from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import figdata
from derive_surface import inference_p1 as inf

WEEK = 7 * 86_400_000
T0 = 1_735_689_600_000  # 2025-01-01 00:00 UTC (a Wednesday)


def frame(n=400, seed=0):
    rng = np.random.default_rng(seed)
    classes = np.array(["other", "rfq", "dominant_maker"])
    rows = pd.DataFrame({
        "ts": T0 + rng.integers(0, 4 * WEEK, n),
        "currency": rng.choice(["BTC", "ETH"], n),
        "taker_class": rng.choice(classes, n),
        "delta_bucket": rng.choice(["25-40", "40-60"], n),
        "tenor_bucket": rng.choice(["<=2d", "7-30d"], n),
        "cluster": rng.choice([f"w{i}" for i in range(12)], n),
        "notional": rng.lognormal(8, 1, n),
        "hs": rng.normal(2.0, 1.0, n),
        "as_usd": rng.normal(-0.5, 1.0, n),
        "net_edge": rng.normal(1.0, 1.0, n),
        "fee_maker": np.abs(rng.normal(0.3, 0.1, n)),
        "rebate_maker": np.abs(rng.normal(0.1, 0.05, n)),
        "hedge": np.abs(rng.normal(0.4, 0.1, n)),
    })
    rows["fee_pc"], rows["rebate_pc"] = rows["fee_maker"], rows["rebate_maker"]     # one contract per fill
    for h in ("1m", "30m", "24h"):
        rows[f"mo_usd_{h}"] = rng.normal(1.5, 2.0, n)
        rows[f"mo_vol_{h}"] = rng.normal(2.0, 3.0, n)
        rows[f"mo_dn_{h}"] = rows[f"mo_usd_{h}"] - rng.normal(0, 0.2, n)
    return rows


def test_horizon_curve_has_one_row_per_class_and_horizon_with_ci():
    out = figdata.horizon_curve(frame(), horizons=("1m", "30m", "24h"), unit="usd", stat="median", b=99, seed=1)
    assert set(out["horizon"]) == {"1m", "30m", "24h"}
    assert set(out["taker_class"]) == {"other", "rfq", "dominant_maker", "all"}
    assert (out["lo"] <= out["value"]).all() and (out["value"] <= out["hi"]).all()
    assert (out["fills"] > 0).all()


def test_horizon_curve_mean_matches_pandas():
    rows = frame()
    out = figdata.horizon_curve(rows, horizons=("30m",), unit="usd", stat="mean", b=49, seed=1)
    got = out[(out["taker_class"] == "all") & (out["horizon"] == "30m")]["value"].iloc[0]
    assert got == pytest.approx(rows["mo_usd_30m"].mean())


def test_cell_matrix_orders_buckets_and_keeps_counts():
    values, counts = figdata.cell_matrix(frame(), value="mo_vol_30m", currency="BTC", stat="median")
    assert list(values.index) == ["<=2d", "7-30d"] and list(values.columns) == ["25-40", "40-60"]
    assert counts.to_numpy().sum() > 0 and values.shape == counts.shape


def test_cell_matrix_masks_thin_cells():
    rows = frame()
    values, counts = figdata.cell_matrix(rows, value="mo_vol_30m", currency="BTC", min_fills=10_000)
    assert values.isna().all().all()


def test_weekly_series_covers_every_week_and_flags_negatives():
    rows = frame()
    out = figdata.weekly_series(rows, horizon="30m")
    assert len(out) >= 4 and {"week", "fills", "median", "share_negative"} <= set(out.columns)
    assert (out["share_negative"].between(0, 1)).all()
    assert out["fills"].sum() == len(rows)


def fills_with_amounts(amounts=(0.1, 5.0, 1.0, 0.1, 5.0, 1.0), fee=0.4, rebate=0.1, index=50_000.0):
    """Tape-like fills: fee and rebate are sums over the fill, markout and hedge are per contract."""
    n = len(amounts)
    amount = np.asarray(amounts, dtype=float)
    return pd.DataFrame({
        "trade_id": ["t{}".format(i) for i in range(n)], "ts": T0 + np.arange(n), "currency": "BTC",
        "instrument_name": "BTC-1-2-C", "taker_wallet": ["0xt{}".format(i % 3) for i in range(n)],
        "taker_class": "other", "delta_bucket": "40-60", "tenor_bucket": "<=2d", "price": 100.0,
        "mark_b_t": 105.0, "delta_t": 0.5, "fwd_t": index, "maker_side": 1, "amount": amount,
        "index_price": index, "notional": amount * index, "fee_maker": fee * amount, "rebate_maker": rebate * amount,
        "mo_usd_30m": 10.0 + np.arange(n), "mo_dn_30m": 9.0, "mo_vol_30m": 5.0,
    })


FUNDING = pd.DataFrame({"instrument_name": ["BTC-PERP"], "timestamp": [1], "funding_rate": [1e-5]})


def test_waterfall_components_add_up_to_the_mean_net_edge_per_contract():
    """Checked against the net edge of an analysis frame, not against its own last row (that was a tautology)."""
    f = inf.analysis_frame(fills_with_amounts(), FUNDING)
    steps = figdata.waterfall_components(f).set_index("step")["value"]
    assert steps.drop("net edge").sum() == pytest.approx(np.nanmean(f["net_edge"]))
    assert steps["maker fee"] == pytest.approx(-np.nanmean(f["fee_maker"] / f["amount"]))
    assert steps["maker fee"] == pytest.approx(-0.4) and steps["maker rebate"] == pytest.approx(0.1)
    assert list(steps.index)[:2] == ["half spread", "adverse selection"]


def test_waterfall_components_for_one_class():
    rows = frame()
    out = figdata.waterfall_components(rows, taker_class="other")
    total = out.loc[out["step"] != "net edge", "value"].sum()
    assert total == pytest.approx(out.loc[out["step"] == "net edge", "value"].iloc[0], abs=1e-9)
    assert out["fills"].iloc[0] == int((rows["taker_class"] == "other").sum())


def test_edge_bp_is_the_edge_of_the_fill_over_its_notional():
    """F5 and S5 once divided the net edge per contract by the notional of the whole fill."""
    f = inf.analysis_frame(fills_with_amounts(), FUNDING)
    bp = figdata.edge_bp(f).to_numpy()
    fill_edge = f["net_edge"] * f["amount"]
    assert bp == pytest.approx((1e4 * fill_edge / f["notional"]).to_numpy())
    assert bp == pytest.approx((1e4 * f["net_edge"] / 50_000.0).to_numpy())
    # the amount drops out: fills 0 (0.1 contracts) and 3 (0.1) differ from 1 (5) only through the markout
    assert bp[1] - bp[0] == pytest.approx(1e4 * 1.0 / 50_000.0)


def test_premium_share_divides_a_per_contract_markout_by_the_price_per_contract():
    f = inf.analysis_frame(fills_with_amounts(), FUNDING)
    share = figdata.premium_share(f, "y_usd").to_numpy()
    assert share == pytest.approx((100.0 * f["y_usd"] / 100.0).to_numpy())
    assert share[1] == pytest.approx(11.0)            # 11 USDC on a 100 USDC option, five contracts or not


def test_example_fill_picks_a_representative_trade():
    rows = frame()
    rows.loc[0, ["mo_usd_30m", "hs", "as_usd"]] = [3.0, 2.0, 1.0]
    got = figdata.example_fill(rows, taker_class="other")
    assert set(["ts", "hs", "as_usd", "mo_usd_30m"]) <= set(got.index)


def test_example_fill_prefers_earned_spread_then_lost_it():
    rows = frame()
    rows["taker_class"] = "other"
    rows["hs"] = -1.0            # nobody earns the spread ...
    rows["mo_usd_30m"] = 5.0     # ... and nobody loses afterwards
    want = rows["notional"].median()
    rows.loc[7, ["hs", "mo_usd_30m", "notional"]] = [4.0, -9.0, want]
    got = figdata.example_fill(rows, taker_class="other")
    assert got["hs"] > 0 and got["mo_usd_30m"] < 0


def test_example_fill_falls_back_when_no_such_fill_exists():
    rows = frame()
    rows["taker_class"] = "other"
    rows["hs"] = -1.0
    rows["mo_usd_30m"] = 5.0
    got = figdata.example_fill(rows, taker_class="other")
    assert np.isfinite(got["mo_usd_30m"])


def curves():
    """Two SVI pushes for one expiry, the later one at a higher level."""
    return pd.DataFrame({
        "expiry": [1_800_000_000, 1_800_000_000, 1_800_000_000, 1_700_000_000],
        "block_ts": [1_799_000_000, 1_799_000_600, 1_799_001_200, 1_699_000_000],
        "feed_ts": [1_799_000_000, 1_799_000_600, 1_799_001_200, 1_699_000_000],
        "svi_a": [0.0002, 0.0003, 0.0004, 0.0002],
        "svi_b": [0.004, 0.005, 0.006, 0.004],
        "svi_rho": [-0.3, -0.3, -0.3, -0.3],
        "svi_m": [0.002, 0.002, 0.002, 0.002],
        "svi_sigma": [0.02, 0.02, 0.02, 0.02],
        "svi_fwd": [60_000.0, 60_100.0, 60_200.0, 50_000.0],
        "svi_ref_tau": [0.01, 0.01, 0.01, 0.01],
    })


def test_curve_at_takes_the_last_push_before_the_moment():
    got = figdata.curve_at(curves(), expiry=1_800_000_000, at_s=1_799_000_900)
    assert got["block_ts"] == 1_799_000_600
    assert got["age_s"] == pytest.approx(300.0)
    assert got["forward"] == pytest.approx(60_100.0)
    assert np.isfinite(got["vol"]).all() and (got["vol"] > 0).all()
    assert got["strike"][0] < got["forward"] < got["strike"][-1]
    assert got["k"] == pytest.approx(np.log(got["strike"] / got["forward"]))


def test_curve_at_ignores_other_expiries_and_later_pushes():
    got = figdata.curve_at(curves(), expiry=1_800_000_000, at_s=1_799_000_000)
    assert got["block_ts"] == 1_799_000_000 and got["forward"] == pytest.approx(60_000.0)


def test_curve_at_returns_none_when_nothing_was_pushed_yet():
    assert figdata.curve_at(curves(), expiry=1_800_000_000, at_s=1_798_000_000) is None


def test_median_cluster_bootstrap_matches_brute_force():
    rng = np.random.default_rng(3)
    clusters = np.repeat([f"w{i}" for i in range(15)], 20)
    values = rng.normal(0, 1, 300)
    fast = figdata._median_ci(values, clusters, b=400, seed=5)
    # brute force: resample clusters, pool their values, take the median
    codes, uniq = pd.factorize(pd.Series(clusters))
    by = [values[codes == g] for g in range(len(uniq))]
    r = np.random.default_rng(5)
    draws = [np.median(np.concatenate([by[j] for j in r.integers(0, len(by), len(by))])) for _ in range(400)]
    assert fast[0] == pytest.approx(float(np.median(values)))
    assert fast[1] == pytest.approx(float(np.quantile(draws, 0.025)), abs=0.12)
    assert fast[2] == pytest.approx(float(np.quantile(draws, 0.975)), abs=0.12)


def test_median_cluster_bootstrap_is_fast_on_many_rows():
    import time
    rng = np.random.default_rng(4)
    n = 200_000
    clusters = rng.integers(0, 4_000, n).astype(str)
    values = rng.normal(0, 1, n)
    t0 = time.time()
    figdata._median_ci(values, clusters, b=199, seed=1)
    assert time.time() - t0 < 20


def test_load_results_reads_every_table_and_the_summary(tmp_path):
    (tmp_path / "summary.json").write_text('{"fills": 7, "H4": {"cells": 97}}')
    pd.DataFrame({"class": ["other"], "mean": [1.0]}).to_csv(tmp_path / "class_means.csv", index=False)
    pd.DataFrame({"horizon": ["30m"], "mean": [2.0]}).to_csv(tmp_path / "horizon_means.csv", index=False)
    got = figdata.load_results(tmp_path)
    assert got["summary"]["fills"] == 7 and got["summary"]["H4"]["cells"] == 97
    assert got["classes"]["mean"].iloc[0] == 1.0 and got["horizons"]["mean"].iloc[0] == 2.0
    assert got["cells"].empty and got["lorenz"].empty      # missing files are empty, never missing keys
    assert set(figdata.RESULT_TABLES) <= set(got)


def test_load_results_complains_about_a_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        figdata.load_results(tmp_path / "nope")


def test_cells_matrix_pivots_the_registered_cell_table():
    cells = pd.DataFrame({
        "currency": ["BTC", "BTC", "BTC", "ETH"],
        "delta_bucket": ["40-60", "25-40", "40-60", "40-60"],
        "tenor_bucket": ["<=2d", "<=2d", "7-30d", "<=2d"],
        "fills": [8902, 3000, 500, 23718],
        "mean": [23.95, -2.0, 4.0, 0.36],
        "lo": [7.24, -5.0, -1.0, -0.41],
        "hi": [44.83, 1.0, 9.0, 1.34],
    })
    values, counts, sig = figdata.cells_matrix(cells, "BTC")
    assert list(values.columns) == ["25-40", "40-60"] and list(values.index) == ["<=2d", "7-30d"]
    assert values.loc["<=2d", "40-60"] == pytest.approx(23.95)
    assert np.isnan(values.loc["7-30d", "25-40"])         # a cell the run never produced stays empty
    assert counts.loc["<=2d", "40-60"] == 8902
    assert bool(sig.loc["<=2d", "40-60"]) and not bool(sig.loc["<=2d", "25-40"])
