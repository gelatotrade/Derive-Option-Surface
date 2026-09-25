from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import inference_p1 as inf


def panel(n_cluster=40, per=25, effect=0.0, seed=0):
    """Panel with cluster-correlated noise and one binary regressor."""
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_cluster):
        shock = rng.normal(0, 1.0)
        for i in range(per):
            x = float((c + i) % 2)
            g = f"inst{i % 5}-day{i % 7}"
            rows.append({"cluster": f"w{c}", "x": x, "fe_key": g,
                         "y": effect * x + shock + rng.normal(0, 0.5)})
    return pd.DataFrame(rows)


def test_within_removes_group_means():
    df = pd.DataFrame({"g": ["a", "a", "b"], "v": [1.0, 3.0, 7.0]})
    got = inf.within(df["v"].to_numpy(), df["g"].to_numpy())
    assert got == pytest.approx([-1.0, 1.0, 0.0])


def test_ols_fe_recovers_beta_with_group_offsets():
    rng = np.random.default_rng(1)
    g = np.repeat(["a", "b", "c"], 200)
    x = rng.normal(size=600)
    offsets = {"a": 5.0, "b": -3.0, "c": 0.0}
    y = 2.5 * x + np.array([offsets[k] for k in g]) + rng.normal(0, 0.01, 600)
    beta, resid, _ = inf.ols_fe(y, x.reshape(-1, 1), g)
    assert beta[0] == pytest.approx(2.5, abs=0.01) and abs(resid).max() < 0.1


def test_wild_cluster_p_is_large_without_effect_and_small_with_one():
    zero = panel(effect=0.0, seed=2)
    out0 = inf.wild_cluster_p(zero["y"].to_numpy(), zero[["x"]].to_numpy(), zero["fe_key"].to_numpy(),
                              zero["cluster"].to_numpy(), 0, b=199, seed=inf.SEED)
    assert out0["p"] > 0.2 and out0["clusters"] == 40 and out0["n"] == 1000
    strong = panel(effect=2.0, seed=2)
    out1 = inf.wild_cluster_p(strong["y"].to_numpy(), strong[["x"]].to_numpy(), strong["fe_key"].to_numpy(),
                              strong["cluster"].to_numpy(), 0, b=199, seed=inf.SEED)
    assert out1["p"] < 0.05 and out1["beta"] == pytest.approx(2.0, abs=0.1) and abs(out1["t"]) > 2


def test_wild_cluster_p_is_deterministic():
    df = panel(effect=1.0, seed=3)
    args = (df["y"].to_numpy(), df[["x"]].to_numpy(), df["fe_key"].to_numpy(), df["cluster"].to_numpy(), 0)
    a = inf.wild_cluster_p(*args, b=99, seed=7)
    b = inf.wild_cluster_p(*args, b=99, seed=7)
    assert a == b


def test_cluster_mean_ci_brackets_the_mean_and_flags_a_shift():
    rng = np.random.default_rng(4)
    clusters = np.repeat([f"w{i}" for i in range(30)], 20)
    values = rng.normal(0, 1, 600)
    out = inf.cluster_mean_ci(values, clusters, b=299, seed=inf.SEED)
    assert out["lo"] < out["mean"] < out["hi"] and out["lo"] < 0 < out["hi"] and out["p"] > 0.1
    shifted = inf.cluster_mean_ci(values - 3.0, clusters, b=299, seed=inf.SEED)
    assert shifted["hi"] < 0 and shifted["p"] < 0.05


def test_top_loss_share_and_lorenz():
    wallets = np.array(["a", "b", "c", "d", "e", "f"])
    values = np.array([-40.0, -30.0, -20.0, -5.0, -5.0, 100.0])  # f is profitable for the maker
    out = inf.top_loss_share(values, wallets, top=2, b=199, seed=inf.SEED)
    assert out["loss_total"] == pytest.approx(-100.0) and out["share"] == pytest.approx(0.7)
    assert 0.0 <= out["lo"] <= out["share"] <= out["hi"] <= 1.0 and out["wallets"] == 6
    curve = inf.lorenz(values, wallets)
    assert curve["loss_share"].iloc[-1] == pytest.approx(1.0) and curve["wallet_share"].iloc[-1] == pytest.approx(1.0)
    assert curve["loss_share"].iloc[0] == pytest.approx(0.4)  # the worst wallet alone


def test_did_finds_a_treatment_effect_and_ranks_placebos():
    rng = np.random.default_rng(5)
    rows = []
    event = 1_000_000_000_000
    day = 86_400_000
    for d in range(-40, 40):
        for ccy in ("BTC", "ETH", "HYPE"):
            for k in range(6):
                post = d >= 0
                treated = ccy == "HYPE"
                rows.append({"ts": event + d * day + k, "currency": ccy, "taker_wallet": f"w{k}",
                             "instrument_name": f"{ccy}-{k}", "day": d,
                             "y_vol": (0.8 if (post and treated) else 0.0) + rng.normal(0, 0.2)})
    frame = pd.DataFrame(rows)
    frame["fe_key"] = frame["instrument_name"] + "|" + frame["day"].astype(str)
    frame["cluster"] = frame["taker_wallet"]
    out = inf.did(frame, "y_vol", event, placebos=20, seed=inf.SEED, b=199)
    assert out["beta"] == pytest.approx(0.8, abs=0.1) and out["p"] < 0.05
    assert out["placebo_share_more_extreme"] <= 0.05 and out["placebos"] == 20


def test_cell_table_respects_the_minimum_and_marks_positive_cells():
    rng = np.random.default_rng(6)
    rows = []
    for cell, (mean, n) in {("BTC", "40-60", "<=2d"): (-1.0, 400), ("BTC", "25-40", "7-30d"): (2.0, 400),
                            ("ETH", "10-25", ">90d"): (5.0, 50)}.items():
        for i in range(n):
            rows.append({"currency": cell[0], "delta_bucket": cell[1], "tenor_bucket": cell[2],
                         "cluster": f"w{i % 20}", "net_edge": mean + rng.normal(0, 0.5)})
    table = inf.cell_table(pd.DataFrame(rows), "net_edge", min_fills=200, b=199, seed=inf.SEED)
    assert len(table) == 2  # the 50-fill cell is dropped
    pos = table.set_index(["currency", "delta_bucket", "tenor_bucket"])
    assert not pos.loc[("BTC", "40-60", "<=2d"), "positive"]
    assert pos.loc[("BTC", "25-40", "7-30d"), "positive"]


def test_hedge_cost_scales_with_delta_and_horizon():
    base = inf.hedge_cost(np.array([0.5]), np.array([100_000.0]), 1_800, np.array([1e-5]), half_spread_bp=1.0)
    twice = inf.hedge_cost(np.array([1.0]), np.array([100_000.0]), 1_800, np.array([1e-5]), half_spread_bp=1.0)
    longer = inf.hedge_cost(np.array([0.5]), np.array([100_000.0]), 86_400, np.array([1e-5]), half_spread_bp=1.0)
    free = inf.hedge_cost(np.array([0.5]), np.array([100_000.0]), 1_800, np.array([0.0]), half_spread_bp=0.0)
    assert twice[0] == pytest.approx(2 * base[0]) and longer[0] > base[0]
    assert free[0] == pytest.approx(0.5 * 100_000 * 3e-4)


def test_analysis_frame_decomposes_the_markout():
    rows = pd.DataFrame([{
        "trade_id": "a", "ts": 1_700_000_000_000, "currency": "BTC", "instrument_name": "BTC-1-2-C",
        "taker_wallet": "0xt", "maker_wallet": "0xm", "taker_class": "other", "delta_bucket": "40-60",
        "tenor_bucket": "7-30d", "is_sweep": False, "size_above_p90": False, "price": 100.0, "mark_b_t": 105.0,
        "mark_b_30m": 110.0, "iv_fill": 0.5, "iv_b_30m": 0.55, "fwd_t": 50_000.0, "fwd_b_30m": 50_500.0,
        "delta_t": 0.5, "maker_side": 1, "fee_maker": 0.4, "rebate_maker": 0.1, "mo_usd_30m": 10.0,
        "mo_dn_30m": 9.0, "mo_vol_30m": 5.0, "mo_set": 3.0, "mo_set_vrp": 1.0, "amount": 1.0,
    }])
    funding = pd.DataFrame({"instrument_name": ["BTC-PERP"], "timestamp": [1], "funding_rate": [1e-5]})
    out = inf.analysis_frame(rows, funding, horizon="30m", half_spread_bp=1.0)
    r = out.iloc[0]
    assert r.hs == pytest.approx(5.0) and r.as_usd == pytest.approx(5.0) and r.y_usd == pytest.approx(10.0)
    assert r.net_edge == pytest.approx(10.0 - 0.4 + 0.1 - r.hedge)
    assert r.fe_key == "BTC-1-2-C|2023-11-14" and r.cluster == "0xt"


FEE_PER_CONTRACT, REBATE_PER_CONTRACT = 0.4, 0.1


def fills_with_amounts(amounts=(0.1, 1.0, 5.0)):
    """Fills as the tape books them: markout per contract, maker fee and rebate as sums over the fill.

    The first test of the net edge used one contract per fill, where both readings agree; the fee unit was
    only found on 25.09.2026 (docs/paper1/BEFUND_2026-09-25_GEBUEHRENEINHEIT.md).  Amounts of 0.1 and 5
    make a fee per fill and a fee per contract differ by a factor of ten and five.
    """
    rows = []
    for i, amount in enumerate(amounts):
        rows.append({
            "trade_id": "t{}".format(i), "ts": 1_700_000_000_000 + i, "currency": "BTC",
            "instrument_name": "BTC-1-2-C", "taker_wallet": "0xt{}".format(i), "maker_wallet": "0xm",
            "taker_class": "other", "delta_bucket": "40-60", "tenor_bucket": "7-30d", "price": 100.0,
            "mark_b_t": 105.0, "delta_t": 0.5, "fwd_t": 50_000.0, "maker_side": 1, "amount": amount,
            "index_price": 50_000.0, "notional": amount * 50_000.0,
            "fee_maker": FEE_PER_CONTRACT * amount, "rebate_maker": REBATE_PER_CONTRACT * amount,
            "mo_usd_30m": 10.0, "mo_dn_30m": 9.0, "mo_vol_30m": 5.0,
        })
    return pd.DataFrame(rows)


FUNDING = pd.DataFrame({"instrument_name": ["BTC-PERP"], "timestamp": [1], "funding_rate": [1e-5]})


def test_analysis_frame_takes_fee_and_rebate_per_contract():
    out = inf.analysis_frame(fills_with_amounts(), FUNDING, horizon="30m", half_spread_bp=1.0)
    assert out["fee_pc"].to_numpy() == pytest.approx([FEE_PER_CONTRACT] * 3)
    assert out["rebate_pc"].to_numpy() == pytest.approx([REBATE_PER_CONTRACT] * 3)
    # every fill has the same markout, hedge and fee per contract, so the same net edge per contract
    expected = 10.0 - FEE_PER_CONTRACT + REBATE_PER_CONTRACT - out["hedge"].to_numpy()
    assert out["net_edge"].to_numpy() == pytest.approx(expected)
    # the decomposition holds fill by fill: half spread + adverse selection - fee + rebate - hedge
    parts = out["hs"] + out["as_usd"] - out["fee_pc"] + out["rebate_pc"] - out["hedge"]
    assert parts.to_numpy() == pytest.approx(out["net_edge"].to_numpy())


def test_analysis_frame_gives_no_net_edge_to_a_fill_without_amount():
    out = inf.analysis_frame(fills_with_amounts((0.0, 5.0)), FUNDING, horizon="30m", half_spread_bp=1.0)
    assert np.isnan(out.loc[0, "fee_pc"]) and np.isnan(out.loc[0, "net_edge"])
    assert np.isfinite(out.loc[1, "net_edge"])


def test_class_table_and_cells_report_fee_and_rebate_per_contract(tmp_path):
    frame = run_all_frame(n_per_cell=220)
    frame["amount"] = np.resize([0.1, 1.0, 5.0], len(frame))
    frame["fee_maker"] = FEE_PER_CONTRACT * frame["amount"]
    frame["rebate_maker"] = REBATE_PER_CONTRACT * frame["amount"]
    frame["index_price"] = 50_000.0
    frame["notional"] = frame["amount"] * frame["index_price"]
    root = write_inputs(tmp_path, frame)
    out = tmp_path / "results"
    inf.run_all(root, out, half_spread_bp=1.0, b=199, seed=5)
    classes = pd.read_csv(out / "class_means.csv").set_index("class")
    assert classes["mean_fee"].to_numpy() == pytest.approx([FEE_PER_CONTRACT] * len(classes))
    assert classes["mean_rebate"].to_numpy() == pytest.approx([REBATE_PER_CONTRACT] * len(classes))
    ref = inf.analysis_frame(frame, pd.read_parquet(root / "ref" / "funding_history.parquet"))
    expected = ref["y_usd"] - FEE_PER_CONTRACT + REBATE_PER_CONTRACT - ref["hedge"]
    means = expected.groupby(ref["taker_class"]).mean()
    assert classes["mean_ne"].to_numpy() == pytest.approx(means.reindex(classes.index).to_numpy())
    cells = pd.read_csv(out / "h4_cells.csv")
    by_cell = expected.groupby([ref["currency"], ref["delta_bucket"], ref["tenor_bucket"]]).mean()
    for _, r in cells.iterrows():
        assert r["mean"] == pytest.approx(by_cell.loc[(r["currency"], r["delta_bucket"], r["tenor_bucket"])])


def test_path_agreement_reports_correlation_and_sign_agreement():
    rows = pd.DataFrame({
        "mo_usd_30m": [1.0, -2.0, 3.0, -4.0, 5.0, np.nan],
        "mo_usd_a_30m": [1.1, -1.8, -0.5, -4.4, 5.2, 1.0],
        "lag_a_30m_s": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "svi_age_s_t": [5.0, 5.0, 200.0, 200.0, 5.0, 5.0],
        "currency": ["BTC"] * 6,
    })
    out = mk_inf_path(rows)
    assert out.loc[out["group"] == "all", "fills"].iloc[0] == 5
    assert out.loc[out["group"] == "all", "sign_agreement"].iloc[0] == pytest.approx(0.8)
    assert 0.9 < out.loc[out["group"] == "all", "correlation"].iloc[0] <= 1.0
    fresh = out[out["group"] == "svi_age <= 60 s"].iloc[0]
    assert fresh["fills"] == 3 and fresh["sign_agreement"] == pytest.approx(1.0)


def mk_inf_path(rows):
    return inf.path_agreement(rows, horizon="30m")


def run_all_frame(n_per_cell=260, seed=11):
    """A markouts frame with everything run_all touches: two currencies, two cells, five horizons."""
    rng = np.random.default_rng(seed)
    event = inf.HYPE_EVENT_MS
    rows = []
    for ccy in ("BTC", "HYPE"):
        for tenor in ("<=2d", "7-30d"):
            for i in range(n_per_cell):
                ts = int(event + rng.integers(-60, 60) * 86_400_000 + rng.integers(0, 86_400_000))
                rows.append({"ts": ts, "currency": ccy, "instrument_name": "{}-{}".format(ccy, i % 7),
                             "taker_wallet": "0x{}".format(i % 23), "taker_class": ["other", "rfq", "vault"][i % 3],
                             "delta_bucket": "40-60", "tenor_bucket": tenor, "is_sweep": bool(i % 10 == 0),
                             "size_above_p90": bool(i % 12 == 0), "price": 100.0, "mark_b_t": 100.0 + rng.normal(0, 2),
                             "delta_t": float(rng.uniform(-1, 1)), "fwd_t": 50_000.0, "maker_side": int(rng.choice([-1, 1])),
                             "fee_maker": 0.4, "rebate_maker": 0.1, "amount": 1.0,
                             "mo_set": float(rng.normal(1, 5)), "mo_set_vrp": float(rng.normal(0, 5)),
                             "svi_age_s_t": float(abs(rng.normal(30, 10))), "notional": 50_000.0})
    frame = pd.DataFrame(rows)
    for h in inf.HORIZON_SECONDS:
        frame["mo_usd_{}".format(h)] = rng.normal(2.0, 6.0, len(frame))
        frame["mo_dn_{}".format(h)] = frame["mo_usd_{}".format(h)] - rng.normal(0, 0.5, len(frame))
        frame["mo_vol_{}".format(h)] = rng.normal(1.0, 3.0, len(frame))
        frame["mo_usd_a_{}".format(h)] = frame["mo_usd_{}".format(h)] + rng.normal(0, 1.0, len(frame))
        frame["lag_a_{}_s".format(h)] = np.abs(rng.normal(600, 200, len(frame)))
        frame["mark_b_{}".format(h)] = frame["mark_b_t"] + rng.normal(0, 1, len(frame))
        frame["iv_b_{}".format(h)] = np.abs(rng.normal(0.6, 0.05, len(frame)))
        frame["fwd_b_{}".format(h)] = 50_000.0 + rng.normal(0, 50, len(frame))
    return frame


def write_inputs(tmp_path, frame):
    root = tmp_path / "data"
    (root / "derived").mkdir(parents=True)
    (root / "ref").mkdir(parents=True)
    frame.to_parquet(root / "derived" / "markouts.parquet", index=False)
    pd.DataFrame({"instrument_name": ["BTC-PERP", "HYPE-PERP"], "timestamp": [1, 2],
                  "funding_rate": [1e-5, 2e-5]}).to_parquet(root / "ref" / "funding_history.parquet", index=False)
    return root


def test_run_all_writes_every_registered_table(tmp_path):
    root = write_inputs(tmp_path, run_all_frame())
    out = tmp_path / "results"
    summary = inf.run_all(root, out, half_spread_bp=1.0, b=199, seed=5)
    for name in ("h1_lorenz.csv", "h4_cells.csv", "h4_sensitivity.csv", "class_means.csv",
                 "horizon_means.csv", "path_agreement.csv", "summary.json"):
        assert (out / name).exists(), name
    assert set(summary) >= {"H1", "H2", "H3", "H4", "path_agreement", "missing_vol_unit"}
    assert summary["fills"] == 4 * 260


def test_every_reported_number_uses_the_same_bootstrap_size(tmp_path, monkeypatch):
    """A sensitivity row that varies around the registered case must be that case, not a cheaper approximation.

    The pilot run showed why: the headline drew 9 999 times and the sensitivity 1 999, one cell flipped, and
    the two reported shares of positive cells straddled the rejection threshold of H4 (49,5 % against 50,5 %).
    Comparing the numbers cannot catch this reliably, because whether a cell flips depends on the data, so
    the guard is on the mechanism: every interval in one run is drawn the same number of times.
    """
    sizes = []
    real_ci, real_cells = inf.cluster_mean_ci, inf.cell_table

    def spy_ci(values, clusters, b=inf.B, **kw):
        sizes.append(b)
        return real_ci(values, clusters, b=b, **kw)

    def spy_cells(frame, y_col, min_fills=inf.MIN_CELL_FILLS, b=inf.B, **kw):
        sizes.append(b)
        return real_cells(frame, y_col, min_fills=min_fills, b=b, **kw)

    monkeypatch.setattr(inf, "cluster_mean_ci", spy_ci)
    monkeypatch.setattr(inf, "cell_table", spy_cells)
    root = write_inputs(tmp_path, run_all_frame())
    summary = inf.run_all(root, tmp_path / "results", half_spread_bp=1.0, b=2999, seed=5)
    assert sizes, "run_all computed no interval at all"
    assert set(sizes) == {2999}, "bootstrap sizes differ within one run: {}".format(sorted(set(sizes)))
    sens = pd.read_csv(tmp_path / "results" / "h4_sensitivity.csv")
    base = float(sens[sens["half_spread_bp"] == 1.0]["share_positive"].iloc[0])
    assert base == pytest.approx(summary["H4"]["share_positive"], abs=1e-12)
    assert int(sens[sens["half_spread_bp"] == 1.0]["cells"].iloc[0]) == summary["H4"]["cells"]


def test_did_keeps_the_placebo_estimates_not_just_their_count():
    """The event study figure has to draw the placebo distribution, so the estimates must survive the run."""
    rng = np.random.default_rng(7)
    n = 4_000
    event = 1_700_000_000_000
    day = 86_400_000
    frame = pd.DataFrame({
        "ts": event + rng.integers(-150 * day, 80 * day, n),
        "currency": rng.choice(["HYPE", "BTC"], n),
        "cluster": rng.choice(["w{}".format(i) for i in range(40)], n),
    })
    frame["day"] = pd.to_datetime(frame["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    frame["y_vol"] = rng.normal(0, 1, n) + (frame["currency"] == "HYPE") * (frame["ts"] >= event) * 0.4
    out = inf.did(frame, "y_vol", event_ms=event, treated="HYPE", placebos=6, seed=3, b=99, window_days=45)
    assert len(out["placebo_beta"]) == out["placebos"] == len(out["placebo_t"])
    assert all(np.isfinite(b) for b in out["placebo_beta"])
