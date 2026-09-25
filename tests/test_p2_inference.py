"""Tests for derive_surface.inference_p2: H1 to H3 of the Paper 2 preregistration and the exploratory tables.

All tests are offline and use synthetic data with known solutions: hand-computed cell ratios, rank correlations
with a known value, bootstrap replicates re-computed by brute force from the fill-level data, medians of the
explicitly replicated multiset.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from derive_surface import inference_p2 as ip

DAY_MS = 86_400_000
T0 = 1_760_000_000_000  # 2025-10-09, inside the PM2 window of BTC and ETH, before HYPE's


def _utc_ms(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp() * 1000)


# ------------------------------------------------------------------------------------------------ synthetic data

def _markouts(n: int = 4, **over) -> pd.DataFrame:
    base = {
        "trade_id": [f"t{i}" for i in range(n)],
        "ts": [T0 + i * 1000 for i in range(n)],
        "currency": ["BTC"] * n,
        "instrument_name": ["BTC-20251031-100000-C"] * n,
        "expiry": [1_761_897_600] * n,
        "maker_side": [1] * n,
        "amount": [2.0] * n,
        "price": [1_000.0] * n,
        "index_price": [100_000.0] * n,
        "mark_b_t": [1_010.0] * n,
        "delta_t": [-0.5] * n,
        "fwd_t": [100_000.0] * n,
        "fee_maker": [4.0] * n,
        "rebate_maker": [1.0] * n,
        "taker_wallet": ["w"] * n,
        "mo_usd_30m": [10.0] * n,
        "mo_dn_30m": [0.0] * n,
        "mo_vol_30m": [0.0] * n,
        "delta_bucket": ["40-60"] * n,
        "tenor_bucket": ["7-30d"] * n,
        "tenor_days": [20.0] * n,
    }
    base.update(over)
    return pd.DataFrame(base)


def _funding(rate: float = 1e-5) -> pd.DataFrame:
    return pd.DataFrame({"instrument_name": ["BTC-PERP", "ETH-PERP", "HYPE-PERP"] * 2,
                         "funding_rate": [rate, rate, rate, -rate, -rate, -rate]})


def _capital(mk: pd.DataFrame, k: float = 5_000.0) -> pd.DataFrame:
    n = len(mk)
    return pd.DataFrame({"trade_id": mk["trade_id"], "ts": mk["ts"], "amount": mk["amount"],
                         "sec": np.full(n, 20 * 86_400), "K_sm": np.full(n, k), "K_pm": np.full(n, k),
                         "K_pm2": np.full(n, k), "K_sm_mm": np.full(n, k / 2), "K_pm_mm": np.full(n, k / 2),
                         "K_pm2_mm": np.full(n, k / 2)})


def _fill_frame(rows) -> pd.DataFrame:
    """Minimal edge frame: rows of (cell, day, edge, index_notional, k_notional, amount)."""
    df = pd.DataFrame(rows, columns=["cell", "day", "edge", "idx", "kk", "amount"])
    df["index_price"] = df["idx"] / df["amount"]
    df["K"] = df["kk"] / df["amount"]
    return df


# ------------------------------------------------------------------------------------------------ net edge

def test_net_edge_divides_fee_and_rebate_by_amount_addendum_2():
    mk = _markouts(n=2, amount=[2.0, 0.5], fee_maker=[4.0, 1.0], rebate_maker=[1.0, 0.25])
    fr = edge = ip.edge_frame(mk, _funding(1e-5), _capital(mk))
    notional = 0.5 * 100_000.0
    hedge = notional * (3e-4 + 1e-4) + notional * 1e-5 * 0.5   # fee + 1 bp half spread, 30 min of funding
    np.testing.assert_allclose(fr["hedge"], hedge)
    ne = 10.0 - np.array([3.0 / 2.0, 0.75 / 0.5]) - hedge
    np.testing.assert_allclose(fr["ne"], ne)
    np.testing.assert_allclose(edge["edge"], ne * np.array([2.0, 0.5]))
    ne_p1 = 10.0 - np.array([3.0, 0.75]) - hedge                  # Paper 1 form: sums per fill undivided
    np.testing.assert_allclose(fr["ne_p1"], ne_p1)
    np.testing.assert_allclose(fr["edge_p1"], ne_p1 * np.array([2.0, 0.5]))


def test_edge_frame_cells_windows_and_tau():
    mk = _markouts(n=4, currency=["BTC", "BTC", "HYPE", "HYPE"],
                   instrument_name=["BTC-X", "BTC-X", "HYPE-X", "HYPE-X"],
                   ts=[_utc_ms("2025-06-12 22:59:59"), _utc_ms("2025-06-12 23:00:00"),
                       _utc_ms("2025-11-10 23:59:59"), _utc_ms("2025-11-11 00:00:00")],
                   maker_side=[1, -1, 1, -1])
    fr = ip.edge_frame(mk, _funding(), _capital(mk))
    assert fr["in_pm2"].tolist() == [False, True, False, True]
    assert fr["in_sm"].tolist() == [True, True, False, True]
    assert fr["in_pm"].tolist() == [True, True, False, False]
    assert fr["side"].tolist() == ["buy", "sell", "buy", "sell"]
    assert fr["cell"].iloc[1] == "BTC|sell|40-60|7-30d"
    assert fr["day"].tolist() == ["2025-06-12", "2025-06-12", "2025-11-10", "2025-11-11"]
    np.testing.assert_allclose(fr["tau"], 20 / 365.0)


def test_edge_frame_rejects_mismatched_capital():
    mk = _markouts(n=2)
    cap = _capital(mk)
    cap.loc[1, "amount"] = 3.0
    with pytest.raises(ValueError):
        ip.edge_frame(mk, _funding(), cap)


# ------------------------------------------------------------------------------------------------ ranks

def test_spearman_matches_scipy_with_ties():
    rng = np.random.default_rng(1)
    x = rng.integers(0, 5, 40).astype(float)
    y = x + rng.normal(0, 2, 40)
    assert ip.spearman(x, y) == pytest.approx(stats.spearmanr(x, y).correlation, abs=1e-12)
    assert np.isnan(ip.spearman(np.ones(5), np.arange(5.0)))


def test_spearman_rows_uses_only_present_cells():
    X = np.array([[1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0], [1.0, 2.0, 9.0, 3.0]])
    Y = np.array([[1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0], [1.0, 2.0, -5.0, 3.0]])
    present = np.array([[True] * 4, [True] * 4, [True, True, False, True]])
    got = ip.spearman_rows(X, Y, present)
    np.testing.assert_allclose(got, [1.0, -1.0, 1.0])


def test_ranks_descending_with_average_ties():
    np.testing.assert_allclose(ip.ranks_desc(np.array([5.0, 1.0, 5.0, 3.0])), [1.5, 4.0, 1.5, 3.0])


# ------------------------------------------------------------------------------------------------ bootstrap draws

def test_day_multiplicities_shape_sum_and_seed():
    W = ip.day_multiplicities(7, b=50, seed=3)
    assert W.shape == (50, 7)
    assert (W.sum(axis=1) == 7).all()
    np.testing.assert_array_equal(W, ip.day_multiplicities(7, b=50, seed=3))
    assert not np.array_equal(W, ip.day_multiplicities(7, b=50, seed=4))


# ------------------------------------------------------------------------------------------------ cell maps (H1)

def test_cell_ratios_are_ratios_of_sums():
    fr = _fill_frame([("c1", "d1", 10.0, 1_000.0, 100.0, 1.0), ("c1", "d2", -4.0, 3_000.0, 50.0, 2.0),
                      ("c2", "d1", 1.0, 500.0, 10.0, 1.0), ("c2", "d1", 2.0, 500.0, 20.0, 1.0),
                      ("c3", "d2", 5.0, 100.0, 5.0, 1.0)])
    cells, res = ip.edge_map(fr, k_col="K", edge_col="edge", min_fills=2, b=20)
    cells = cells.set_index("cell")
    assert set(cells.index[cells["occupied"]]) == {"c1", "c2"}
    assert cells.loc["c1", "fills"] == 2
    assert cells.loc["c1", "A_bp"] == pytest.approx(1e4 * 6.0 / 4_000.0)
    assert cells.loc["c1", "B_bp"] == pytest.approx(1e4 * 6.0 / 150.0)
    assert cells.loc["c2", "A_bp"] == pytest.approx(1e4 * 3.0 / 1_000.0)
    assert cells.loc["c2", "B_bp"] == pytest.approx(1e4 * 3.0 / 30.0)
    assert cells.loc["c1", "sum_edge"] == pytest.approx(6.0)
    assert cells.loc["c1", "sum_K"] == pytest.approx(150.0)
    assert cells.loc["c1", "sum_index"] == pytest.approx(4_000.0)
    assert np.isnan(cells.loc["c3", "A_bp"]) or not cells.loc["c3", "occupied"]
    assert res["n"] == 2


def _structured_cells(A: np.ndarray, Bv: np.ndarray, days: int = 12, fills_per_day: int = 3) -> pd.DataFrame:
    """Every day repeats the same per-cell structure, so every bootstrap replicate has the same cell ratios."""
    rows = []
    for c, (a, bb) in enumerate(zip(A, Bv)):
        for d in range(days):
            for _ in range(fills_per_day):
                edge = 1.0
                rows.append((f"c{c:02d}", f"2025-10-{d + 1:02d}", edge, 1e4 * edge / a, 1e4 * edge / bb, 1.0))
    return _fill_frame(rows)


def test_rho_bootstrap_known_rho_collapses_interval():
    A = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    perm = np.array([2, 1, 4, 3, 6, 5, 8, 7], dtype=float)       # adjacent swaps: sum d^2 = 8
    known = 1 - 6 * 8 / (8 * (64 - 1))
    fr = _structured_cells(A, perm)
    cells, res = ip.edge_map(fr, k_col="K", edge_col="edge", min_fills=10, b=200, seed=5)
    np.testing.assert_allclose(cells.sort_values("cell")["A_bp"], A)
    np.testing.assert_allclose(cells.sort_values("cell")["B_bp"], perm)
    assert res["stat"] == pytest.approx(known)
    assert res["lo"] == pytest.approx(known) and res["hi"] == pytest.approx(known)
    assert res["n_days"] == 12 and res["n"] == 8


def test_rho_bootstrap_matches_bruteforce_resampling():
    rng = np.random.default_rng(11)
    rows = []
    for c in range(6):
        for d in range(9):
            for _ in range(rng.integers(0, 3)):              # some cells have no fill on some days
                a = float(rng.uniform(0.5, 3))
                rows.append((f"c{c}", f"d{d}", float(rng.normal(1, 3)) * a, 1_000.0 * a,
                             float(rng.uniform(50, 150)) * a, a))
    fr = _fill_frame(rows)
    b = 60
    cells, res = ip.edge_map(fr, k_col="K", edge_col="edge", min_fills=1, b=b, seed=9)
    occ = sorted(cells.loc[cells["occupied"], "cell"])
    days = np.array(sorted(fr["day"].unique()))
    W = ip.day_multiplicities(len(days), b=b, seed=9)
    brute = []
    for w in W:
        parts = [fr[fr["day"] == day] for day, m in zip(days, w) for _ in range(m)]
        rep = pd.concat(parts)
        rep = rep[rep["cell"].isin(occ)]
        g = rep.groupby("cell")
        A = 1e4 * g["edge"].sum() / g["idx"].sum()
        Bv = 1e4 * g["edge"].sum() / g["kk"].sum()
        brute.append(stats.spearmanr(A, Bv).correlation if len(A) >= 3 else np.nan)
    np.testing.assert_allclose(res["_draws"], brute, atol=1e-12)
    assert res["lo"] == pytest.approx(np.nanquantile(brute, 0.05))
    assert res["hi"] == pytest.approx(np.nanquantile(brute, 0.95))


def test_rho_bootstrap_spread_matches_sampling_spread():
    """The day bootstrap must reproduce the sampling variability of rho: its spread from one data set is compared with
    the spread of rho over independently regenerated data sets (same cells, new daily noise)."""
    rng = np.random.default_rng(2)
    n_cells, n_days, per_day = 25, 40, 2
    level_a = 20 + 2 * rng.normal(0, 1, n_cells)
    level_b = 20 + 2 * (0.4 * (level_a - 20) / 2 + rng.normal(0, 1, n_cells))

    def draw():
        ea = level_a[:, None, None] + rng.normal(0, 3, (n_cells, n_days, per_day))
        eb = level_b[:, None, None] + rng.normal(0, 3, (n_cells, n_days, per_day))
        return 1e4 / ea, 1e4 / eb                   # index and capital notional per fill with edge 1

    mc = []
    for _ in range(150):
        idx, kk = draw()
        A = 1e4 * n_days * per_day / idx.sum(axis=(1, 2))
        Bv = 1e4 * n_days * per_day / kk.sum(axis=(1, 2))
        mc.append(ip.spearman(A, Bv))
    idx, kk = draw()
    rows = [(f"c{c:02d}", f"d{d:03d}", 1.0, idx[c, d, j], kk[c, d, j], 1.0)
            for c in range(n_cells) for d in range(n_days) for j in range(per_day)]
    _, res = ip.edge_map(_fill_frame(rows), k_col="K", edge_col="edge", min_fills=10, b=600, seed=1)
    sd_boot, sd_mc = float(np.std(res["_draws"])), float(np.std(mc))
    assert 0.6 < sd_boot / sd_mc < 1.6
    assert res["lo"] <= res["stat"] <= res["hi"]
    assert res["hi"] - res["lo"] == pytest.approx(2 * 1.645 * sd_mc, rel=0.4)


def test_edge_map_cell_scale_and_tau_denominator():
    fr = _fill_frame([("c1", "d1", 10.0, 1_000.0, 100.0, 1.0), ("c1", "d2", 10.0, 1_000.0, 100.0, 1.0),
                      ("c2", "d1", 5.0, 1_000.0, 100.0, 1.0), ("c2", "d2", 5.0, 1_000.0, 100.0, 1.0),
                      ("c3", "d1", 1.0, 1_000.0, 100.0, 1.0), ("c3", "d2", 1.0, 1_000.0, 100.0, 1.0)])
    fr["tau"] = np.where(fr["cell"] == "c1", 0.5, 0.1)
    cells, _ = ip.edge_map(fr, k_col="K", edge_col="edge", min_fills=2, b=10, tau_col="tau")
    c = cells.set_index("cell")
    assert c.loc["c1", "B_bp"] == pytest.approx(1e4 * 20.0 / (200.0 * 0.5))
    assert c.loc["c2", "B_bp"] == pytest.approx(1e4 * 10.0 / (200.0 * 0.1))
    scale = pd.Series({"c1": 2.0, "c2": 4.0, "c3": np.nan})
    cells, res = ip.edge_map(fr, k_col="K", edge_col="edge", min_fills=2, b=10, cell_scale=scale)
    c = cells.set_index("cell")
    assert c.loc["c1", "B_bp"] == pytest.approx(1e4 * 20.0 / 200.0 * 2.0)
    assert not c.loc["c3", "occupied"]
    assert res["n"] == 2


def test_edge_map_cell_scale_enters_every_replicate():
    A = np.arange(1.0, 9.0)
    fr = _structured_cells(A, A)                      # B = A per cell, rho = +1 without a scale
    labels = sorted(fr["cell"].unique())
    scale = pd.Series(1.0 / A ** 2, index=labels)     # B * scale = 1 / A reverses the order
    cells, res = ip.edge_map(fr, k_col="K", edge_col="edge", min_fills=10, b=30, cell_scale=scale)
    assert res["stat"] == pytest.approx(-1.0)
    assert res["lo"] == pytest.approx(-1.0) and res["hi"] == pytest.approx(-1.0)
    np.testing.assert_allclose(cells.sort_values("cell")["B_hi"], 1.0 / A)


def test_h1_verdict_rule_and_keys():
    A = np.arange(1.0, 9.0)
    same = ip.h1_verdict(ip.edge_map(_structured_cells(A, A), k_col="K", edge_col="edge", min_fills=10, b=50)[1])
    assert same["stat"] == pytest.approx(1.0) and same["rejected"] is True
    rev = ip.h1_verdict(ip.edge_map(_structured_cells(A, A[::-1]), k_col="K", edge_col="edge", min_fills=10,
                                    b=50)[1])
    assert rev["stat"] == pytest.approx(-1.0) and rev["rejected"] is False
    for key in ("stat", "lo", "hi", "rejected", "rule", "n", "n_days", "b", "seed", "level"):
        assert key in same


# ------------------------------------------------------------------------------------------------ medians (H2, H3)

def test_multiset_median_equals_numpy_on_repeated_values():
    rng = np.random.default_rng(4)
    for _ in range(50):
        v = np.sort(rng.normal(size=rng.integers(1, 12)))
        w = rng.integers(0, 4, len(v))
        if w.sum() == 0:
            w[0] = 1
        assert ip.multiset_median(v, w) == pytest.approx(np.median(np.repeat(v, w)))


def test_median_bootstrap_matches_bruteforce():
    rng = np.random.default_rng(8)
    days = rng.choice([f"d{i}" for i in range(7)], 40)
    vals = rng.normal(0.3, 1, 40)
    res = ip.median_bootstrap(vals, days, b=40, seed=6, level=0.9)
    uniq = np.array(sorted(set(days)))
    W = ip.day_multiplicities(len(uniq), b=40, seed=6)
    code = np.searchsorted(uniq, days)
    brute = [np.median(np.repeat(vals, w[code])) for w in W]
    np.testing.assert_allclose(res["_draws"], brute)
    assert res["stat"] == pytest.approx(np.median(vals))
    assert res["lo"] == pytest.approx(np.quantile(brute, 0.05))
    assert res["hi"] == pytest.approx(np.quantile(brute, 0.95))
    assert res["n"] == 40 and res["n_days"] == 7


def _marginal(n: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ks = rng.uniform(100, 200, n)
    ks[:3] = [0.0, -5.0, 150.0]
    dk = ks * rng.uniform(-0.2, 0.6, n)
    return pd.DataFrame({"fill_key": [f"f{i}" for i in range(n)], "subaccount": 123456, "label": ["M3", "M5"] * (n // 2),
                         "day": pd.to_datetime("2025-10-01") + pd.to_timedelta(rng.integers(0, 10, n), unit="D"),
                         "ccy": "ETH", "status": "ok", "amount": 2.0, "dK_per_contract": dk,
                         "dK_unit": dk * 1.1, "dK_tape_per_contract": dk * 0.9, "dK_mm_per_contract": dk * 0.8,
                         "dK_mm_std_per_contract": dk * 0.7, "K_single_pm2": ks, "K_single_pm2_mm": ks * 0.8,
                         "K_single_pm2_mm_acct": ks * 0.6})


def test_h2_excludes_nonpositive_single_capital_and_counts():
    mg = _marginal()
    v = ip.h2_test(mg, b=99)
    keep = mg["K_single_pm2"] > 0
    assert v["n_excluded"] == 2 and v["n"] == int(keep.sum())
    assert v["stat"] == pytest.approx(np.median(mg.loc[keep, "dK_per_contract"] / mg.loc[keep, "K_single_pm2"]))
    assert v["rejected"] is bool(v["hi"] >= 0.5)
    for key in ("stat", "lo", "hi", "rejected", "rule", "n"):
        assert key in v


def test_h2_variants_use_their_numerator_and_denominator():
    mg = _marginal()
    v = ip.h2_test(mg, variant="ratio_mm", b=19)
    keep = mg["K_single_pm2_mm_acct"] > 0
    assert v["stat"] == pytest.approx(np.median(mg.loc[keep, "dK_mm_per_contract"]
                                                / mg.loc[keep, "K_single_pm2_mm_acct"]))
    v = ip.h2_test(mg, variant="ratio_mm_std", b=19)
    keep = mg["K_single_pm2_mm"] > 0
    assert v["stat"] == pytest.approx(np.median(mg.loc[keep, "dK_mm_std_per_contract"] / mg.loc[keep, "K_single_pm2_mm"]))
    v = ip.h2_test(mg, variant="ratio_unit", b=19)
    keep = mg["K_single_pm2"] > 0
    assert v["stat"] == pytest.approx(np.median(mg.loc[keep, "dK_unit"] / mg.loc[keep, "K_single_pm2"]))


def test_h2_mm_variants_take_one_lib_in_numerator_and_denominator():
    """C5a: the MM sensitivity never divides an account-lib dK_mm by a standard-lib K_single_mm."""
    num, den = ip.H2_VARIANTS["ratio_mm"]
    assert (num, den) == ("dK_mm_per_contract", "K_single_pm2_mm_acct")
    assert ip.H2_LIBS["ratio_mm"] == ("account", "account")
    num, den = ip.H2_VARIANTS["ratio_mm_std"]
    assert (num, den) == ("dK_mm_std_per_contract", "K_single_pm2_mm")
    assert ip.H2_LIBS["ratio_mm_std"] == ("standard", "standard")
    assert set(ip.H2_LIBS) == set(ip.H2_VARIANTS)


def test_h2_preregistered_result_does_not_depend_on_mm_columns():
    mg = _marginal()
    full = ip.h2_test(mg, b=49)
    lean = ip.h2_test(mg.drop(columns=["dK_mm_per_contract", "dK_mm_std_per_contract", "K_single_pm2_mm",
                                       "K_single_pm2_mm_acct"]), b=49)
    np.testing.assert_array_equal(full.pop("_draws"), lean.pop("_draws"))
    assert full == lean


def test_h2_rule_rejects_when_upper_bound_reaches_threshold():
    mg = _marginal()
    mg["dK_per_contract"] = mg["K_single_pm2"] * 0.1
    assert ip.h2_test(mg, b=49)["rejected"] is False
    mg["dK_per_contract"] = mg["K_single_pm2"] * 0.8
    assert ip.h2_test(mg, b=49)["rejected"] is True


def _maker_days(n: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(3)
    k2 = rng.uniform(1e5, 2e5, n)
    k2[0] = -1.0
    ksm = k2 * rng.uniform(2.5, 4.0, n)
    df = pd.DataFrame({"subaccount": 7, "label": ["M1", "M2"] * (n // 2),
                       "day": pd.to_datetime("2025-07-01") + pd.to_timedelta(rng.integers(0, 15, n), unit="D"),
                       "status": ["ok"] * (n - 2) + ["no_options", "no_snapshot"], "n_legs": rng.integers(1, 200, n),
                       "manager": "PM2:ETH", "K_sm": ksm, "K_pm2": k2, "K_pm": k2 * 1.5, "K_sm_mm": ksm * 0.8,
                       "K_pm2_mm": k2 * 0.8, "K_pm_mm": k2 * 1.2})
    for c in ("BTC", "ETH", "HYPE"):
        share = {"BTC": 0.25, "ETH": 0.75, "HYPE": 0.0}[c]
        for m in ("sm", "pm2", "pm"):
            if m == "pm" and c == "HYPE":
                continue
            df[f"K_{m}_{c}"] = df[f"K_{m}"] * share if share else np.nan
    return df


def test_h3_filters_status_excludes_nonpositive_and_counts():
    md = _maker_days()
    v = ip.h3_test(md, b=99)
    ok = (md["status"] == "ok") & (md["K_pm2"] > 0)
    assert v["n"] == int(ok.sum()) and v["n_excluded"] == 1 and v["n_not_ok"] == 2
    assert v["stat"] == pytest.approx(np.median(md.loc[ok, "K_sm"] / md.loc[ok, "K_pm2"]))
    assert v["rejected"] is bool(v["lo"] <= 2.0)
    md["K_sm"] = md["K_pm2"] * 1.5
    assert ip.h3_test(md, b=49)["rejected"] is True


def test_h3_legacy_pm_on_btc_eth_legs_only():
    md = _maker_days()
    md.loc[5, "K_pm2_HYPE"] = 1e9                  # a HYPE leg must not enter the BTC/ETH comparison
    be = ip.btc_eth_columns(md)
    np.testing.assert_allclose(be["K_pm_be"], md["K_pm"])
    np.testing.assert_allclose(be["K_pm2_be"], md["K_pm2"])
    only_hype = md.copy()
    for m in ("sm", "pm2", "pm"):
        only_hype[f"K_{m}_BTC"] = np.nan
        only_hype[f"K_{m}_ETH"] = np.nan
    assert ip.btc_eth_columns(only_hype)["K_pm_be"].isna().all()


# ------------------------------------------------------------------------------------------------ figure tables

def test_capital_by_manager_medians_per_cell():
    fr = pd.DataFrame({"ccy": "BTC", "side": ["sell"] * 3 + ["buy"], "delta_bucket": "40-60",
                       "tenor_bucket": "7-30d", "index_price": 100.0, "in_sm": True, "in_pm": True,
                       "in_pm2": [True, True, False, True],
                       "K_sm": [10.0, 20.0, 30.0, 1.0], "K_pm": [5.0, 6.0, 7.0, 1.0], "K_pm2": [3.0, 4.0, np.nan, 1.0],
                       "K_sm_mm": 1.0, "K_pm_mm": 1.0, "K_pm2_mm": 1.0})
    t = ip.capital_by_manager(fr)
    row = t[(t["window"] == "own") & (t["manager"] == "sm") & (t["side"] == "sell")].iloc[0]
    assert row["fills"] == 3 and row["median_k_over_index"] == pytest.approx(0.2)
    row = t[(t["window"] == "own") & (t["manager"] == "pm2") & (t["side"] == "sell")].iloc[0]
    assert row["fills"] == 2 and row["median_k_over_index"] == pytest.approx(0.035)
    row = t[(t["window"] == "pm2") & (t["manager"] == "sm") & (t["side"] == "sell")].iloc[0]
    assert row["fills"] == 2 and row["median_k_over_index"] == pytest.approx(0.15)


def test_h2_distribution_and_h3_series_carry_labels_only():
    dist = ip.h2_distribution(_marginal())
    assert {"label", "variant", "kind"} <= set(dist.columns)
    assert "subaccount" not in dist.columns and set(dist["label"]) == {"M3", "M5", "all"}
    q = dist[(dist["label"] == "all") & (dist["variant"] == "ratio") & (dist["kind"] == "quantile")]
    mg = _marginal()
    keep = mg["K_single_pm2"] > 0
    med = q.loc[q["x"] == 0.5, "value"].iloc[0]
    assert med == pytest.approx(np.median(mg.loc[keep, "dK_per_contract"] / mg.loc[keep, "K_single_pm2"]))
    hist = dist[(dist["label"] == "all") & (dist["variant"] == "ratio") & (dist["kind"] == "hist")]
    assert hist["value"].sum() == int(keep.sum())
    series = ip.h3_series(_maker_days())
    assert "subaccount" not in series.columns
    assert {"label", "day", "K_sm", "K_pm2", "K_pm", "ratio_sm_pm2"} <= set(series.columns)


def test_no_raw_account_ids_in_written_tables(tmp_path):
    ip.write_csv(ip.h3_series(_maker_days()), tmp_path / "x.csv")
    assert "123456" not in (tmp_path / "x.csv").read_text() and "subaccount" not in (tmp_path / "x.csv").read_text()
    with pytest.raises(ValueError):
        ip.write_csv(pd.DataFrame({"subaccount": [1]}), tmp_path / "y.csv")


def test_json_writer_replaces_nan_and_drops_private_keys(tmp_path):
    ip.write_json({"stat": np.nan, "_draws": np.arange(3), "n": np.int64(3), "ok": np.bool_(True)}, tmp_path / "a.json")
    back = json.loads((tmp_path / "a.json").read_text())
    assert back == {"stat": None, "n": 3, "ok": True}


# ------------------------------------------------------------------------------------------------ CLI on a synthetic root

def _synthetic_root(tmp_path: Path) -> Path:
    rng = np.random.default_rng(0)
    n = 1_500
    ccy = rng.choice(["BTC", "ETH", "HYPE"], n)
    side = rng.choice([1, -1], n)
    ts = _utc_ms("2025-11-12") + rng.integers(0, 20 * DAY_MS, n)
    ts[:200] = _utc_ms("2025-01-10") + rng.integers(0, 20 * DAY_MS, 200)    # outside the PM2 window
    mk = _markouts(n=n, ts=ts, currency=ccy, instrument_name=[f"{c}-X" for c in ccy], maker_side=side,
                   amount=rng.uniform(0.1, 3, n), index_price=np.where(ccy == "HYPE", 40.0, 3_000.0),
                   mo_usd_30m=rng.normal(2, 5, n), delta_bucket=rng.choice(["00-10", "40-60"], n),
                   tenor_bucket=rng.choice(["<=2d", "7-30d"], n), maker_sub=rng.choice([7, 8], n))
    mk.loc[mk["currency"] == "HYPE", "ts"] = np.maximum(mk.loc[mk["currency"] == "HYPE", "ts"],
                                                        _utc_ms("2025-11-11"))
    cap = _capital(mk)
    cap["K_pm2"] = np.where(side < 0, 400.0, 30.0) * rng.uniform(0.5, 1.5, n)
    cap["K_sm"] = cap["K_pm2"] * 1.3
    cap.loc[mk["currency"] == "HYPE", ["K_pm", "K_pm_mm"]] = np.nan
    cap.loc[mk["ts"] < _utc_ms("2025-06-12 23:00"), ["K_pm2", "K_pm2_mm"]] = np.nan
    (tmp_path / "data/p1/derived").mkdir(parents=True)
    (tmp_path / "data/p1/ref").mkdir(parents=True)
    (tmp_path / "data/p2/derived").mkdir(parents=True)
    (tmp_path / "results/p2").mkdir(parents=True)
    mk.to_parquet(tmp_path / "data/p1/derived/markouts.parquet")
    _funding().to_parquet(tmp_path / "data/p1/ref/funding_history.parquet")
    cap.to_parquet(tmp_path / "data/p2/derived/capital.parquet")
    _marginal(200).to_parquet(tmp_path / "data/p2/derived/marginal.parquet")
    _maker_days(60).to_parquet(tmp_path / "data/p2/derived/maker_days.parquet")
    hold = pd.DataFrame([{"window": "pm2", "ccy": c, "side": s, "delta_bucket": d, "tenor_bucket": t,
                          "n_fills": 300, "median_days": 2.0}
                         for c in ("BTC", "ETH", "HYPE") for s in ("buy", "sell") for d in ("00-10", "40-60")
                         for t in ("<=2d", "7-30d")])
    hold.to_csv(tmp_path / "results/p2/holding_time.csv", index=False)
    return tmp_path


def test_main_run_and_sensitivity_write_all_outputs(tmp_path):
    root = _synthetic_root(tmp_path)
    out = root / "results" / "p2"
    assert ip.main(["run", "--root", str(root), "--b", "49", "--min-fills", "20"]) == 0
    for name in ("h1_cells.csv", "h1.json", "h2.json", "h3.json"):
        assert (out / name).exists(), name
    for name in ("h1.json", "h2.json", "h3.json"):
        v = json.loads((out / name).read_text())
        assert {"stat", "lo", "hi", "rejected", "rule", "n"} <= set(v), name
        assert v["b"] == 49 and v["seed"] == ip.SEED
    cells = pd.read_csv(out / "h1_cells.csv")
    assert {"cell", "fills", "A_bp", "B_bp", "sum_K", "rank_A", "rank_B", "occupied"} <= set(cells.columns)
    assert ip.main(["sensitivity", "--root", str(root), "--b", "19", "--min-fills", "20"]) == 0
    sens = json.loads((out / "sensitivity.json").read_text())
    assert sens["exploratory"] is True
    for key in ("a_maps", "b_mm", "c_p1_net_edge", "d_h2", "e_h3", "f_time", "g_by_ccy"):
        assert key in sens, key
    assert sens["e_h3"]["sm_pm_be"]["rejected"] in (True, False)
    assert sens["e_h3"]["pm_pm2_be"]["rejected"] is None      # legacy PM vs PM2: no preregistered threshold
    assert "holding" in sens["f_time"] and "to_expiry" in sens["f_time"]
    hi = sens["h1_interval"]                                   # A28: shape of the registered interval (same draws)
    assert (hi["stat"], hi["lo"], hi["hi"]) == pytest.approx(
        (sens["a_maps"]["pm2"]["stat"], sens["a_maps"]["pm2"]["lo"], sens["a_maps"]["pm2"]["hi"]))
    assert hi["exploratory"] is True and hi["b"] == 19
    mg = pd.read_parquet(root / "data/p2/derived/marginal.parquet")
    for sec, key, variant in (("d_h2", "ratio_mm", "ratio_mm"), ("d_h2", "ratio_mm_std", "ratio_mm_std"),
                              ("b_mm", "h2_ratio_mm", "ratio_mm"), ("b_mm", "h2_ratio_mm_std", "ratio_mm_std")):
        v = sens[sec][key]
        num, den = ip.H2_VARIANTS[variant]
        assert (v["numerator"], v["denominator"]) == (num, den), (sec, key)
        assert v["libs"] == "/".join(ip.H2_LIBS[variant]), (sec, key)
        keep = mg[den] > 0
        assert v["stat"] == pytest.approx(np.median(mg.loc[keep, num] / mg.loc[keep, den])), (sec, key)
    sh2 = pd.read_csv(out / "sens_h2.csv")
    both = sh2[sh2["group"] == "all"].set_index("variant")
    assert {"ratio_mm", "ratio_mm_std"} <= set(both.index)
    assert both.loc["ratio_mm", "denominator"] == "K_single_pm2_mm_acct"
    assert both.loc["ratio_mm_std", "numerator"] == "dK_mm_std_per_contract"
    assert both.loc["ratio_mm", "libs"] == "account/account" and both.loc["ratio_mm_std", "libs"] == "standard/standard"
    for name in ("fig_capital_by_manager.csv", "fig_edge_maps.csv", "fig_h2_dist.csv", "fig_h3_series.csv",
                 "sens_h1_cells.csv", "sens_h2.csv", "sens_h3.csv"):
        assert (out / name).exists(), name
        assert "subaccount" not in (out / name).read_text()


# ------------------------------------------------------------------------------------------------ review round 1

def test_regime_bounds_match_the_figures_and_event_second_is_later_regime():
    from derive_surface.figs_p2 import f1
    assert ip.REGIME_BOUNDS == f1.REGIME_BOUNDS and ip.REGIMES == f1.REGIMES
    b = ip.REGIME_BOUNDS
    got = ip.regime_of([b[0] - 1, b[0], b[1], b[2] - 1, b[2] + 10])
    assert list(got) == ["R1", "R2", "R3", "R3", "R4"]
    np.testing.assert_array_equal(ip.fill_regimes(pd.DataFrame({"ts": [b[1] * 1000 - 1, b[1] * 1000]})),
                                  ["R2", "R3"])


def test_sign_floor_one_cell_per_group_is_exact_and_all_positive_is_near_zero():
    v = ip.sign_floor([5.0, -1.0], draws=10)
    assert v["n_pos"] == 1 and v["n_nonpos"] == 1
    # two cells: ranks are fixed by the sign pattern, rho is one
    assert ip.sign_floor([5.0, 3.0, -1.0], draws=50)["p05"] < 1.0
    three = ip.sign_floor([5.0, -1.0, -2.0, -3.0], draws=200, seed=1)
    assert -1.0 <= three["p05"] <= three["mean"] <= three["p95"] <= 1.0
    flat = ip.sign_floor(np.arange(1.0, 201.0), draws=500, seed=2)
    assert abs(flat["mean"]) < 0.02 and flat["n_nonpos"] == 0
    split = ip.sign_floor(np.r_[np.arange(1.0, 101.0), -np.arange(1.0, 101.0)], draws=500, seed=3)
    # two equal groups shuffled inside: rho = 0.75 in expectation (between-group variance share)
    assert split["mean"] == pytest.approx(0.75, abs=0.02)
    again = ip.sign_floor(np.r_[np.arange(1.0, 101.0), -np.arange(1.0, 101.0)], draws=500, seed=3)
    assert again == split


def test_top_overlap_counts_cells_best_under_both_denominators():
    cells = pd.DataFrame({"cell": list("abcdef"), "occupied": [True] * 5 + [False],
                          "A_bp": [6.0, 5.0, 4.0, 3.0, 2.0, 99.0], "B_bp": [1.0, 50.0, 40.0, 3.0, 2.0, 99.0]})
    assert ip.top_overlap(cells, ks=(1, 2, 3)) == {"top1": 0, "top2": 1, "top3": 2}


def test_h1_sign_groups_reuse_the_h1_bootstrap_on_their_cells():
    rng = np.random.default_rng(5)
    rows = []
    for c in range(8):
        side = "sell" if c < 4 else "buy"
        cell = f"BTC|{side}|d{c}|t"
        for d in range(6):
            for _ in range(5):
                edge = (c - 3.5) * 10 + rng.normal(0, 1)
                rows.append((cell, f"2025-10-0{d + 1}", edge, 1e5, 1e3 * (c + 1), 1.0))
    fr = _fill_frame(rows)
    fr["side"] = fr["cell"].str.split("|").str[1]
    cells, res = ip.edge_map(fr, "K", min_fills=10, b=9)
    out = ip.h1_sign(fr, cells, k_col="K", min_fills=10, b=9, draws=20)
    assert set(ip.H1_SIGN_GROUPS) <= set(out)
    assert out["sign_floor"]["n"] == 8 and out["sign_floor"]["draws"] == 20
    occ = cells[cells["occupied"]]
    pos = occ[occ["A_bp"] > 0]
    assert out["within_pos"]["n"] == len(pos)
    assert out["within_pos"]["stat"] == pytest.approx(ip.spearman(pos["A_bp"], pos["B_bp"]))
    assert out["within_sell"]["n"] == 4 and out["within_buy"]["n"] == 4
    assert out["sign_agree"] == 8
    assert out["within_pos"]["b"] == 9 and out["within_pos"]["rule"] == "H1"


def _near_zero_frame(seed: int, n_cells: int = 60, n_days: int = 80, per: int = 3, sd: float = 6.0) -> pd.DataFrame:
    """Many cells with true edge near zero, capital independent of the edge (the design of the audit's
    synthetic_sign_groups.py, A04); the cells and their capital are fixed, ``seed`` draws the fills."""
    mu = np.linspace(-1.5, 1.5, n_cells)
    kcap = np.exp(np.random.default_rng(1).normal(4, 1.5, n_cells))
    rng = np.random.default_rng(seed)
    n = n_days * per
    fr = pd.DataFrame({"cell": np.repeat([f"BTC|{'sell' if c % 2 else 'buy'}|c{c:02d}|t" for c in range(n_cells)], n),
                       "day": np.tile(np.repeat([f"d{d:03d}" for d in range(n_days)], per), n_cells),
                       "edge": (mu[:, None, None] + rng.normal(0, sd, (n_cells, n_days, per))).ravel(),
                       "index_price": 1e4, "amount": 1.0, "K": np.repeat(kcap, n)})
    fr["side"] = fr["cell"].str.split("|").str[1]
    return fr


def test_h1_sign_groups_by_edge_sign_choose_again_and_mostly_cover_their_estimate():
    """A04: the sign groups are chosen by the estimated edge, so every replicate chooses again on its own A*. Over 30
    data sets of the audit's design the estimate lies inside its interval in 95 % of the group intervals (with the
    cells held fixed, as before the audit: 77 %); single data sets can still miss (percentile interval of a
    non-smooth statistic)."""
    inside = []
    for s in range(30):
        fr = _near_zero_frame(100 + s)
        cells, _ = ip.edge_map(fr, "K", min_fills=10, b=1)
        out = ip.h1_sign(fr, cells, k_col="K", min_fills=10, b=199, draws=2)
        for name in ("within_pos", "within_nonpos"):
            v = out[name]
            inside.append(v["lo"] <= v["stat"] <= v["hi"])
            assert v["selection"] == "per replicate", name
            assert 0.0 < v["switch_share_mean"] < 1.0, name
        for name in ("within_sell", "within_buy"):          # chosen by the maker side, not by the result
            assert out[name]["selection"] == "fixed", name
        assert out["within_pos_sell"]["selection"] == out["within_pos_buy"]["selection"] == "per replicate"
    assert np.mean(inside) >= 0.9


def test_h1_sign_reselected_draws_match_bruteforce_resampling():
    rng = np.random.default_rng(3)
    rows = []
    for c in range(8):
        side = "sell" if c < 4 else "buy"
        for d in range(10):
            for _ in range(int(rng.integers(1, 4))):
                rows.append((f"BTC|{side}|d{c}|t", f"d{d}", float(rng.normal((c - 3.5) * 0.3, 2.0)), 1e4,
                             float(rng.uniform(50, 150)) * (c + 1), 1.0))
    fr = _fill_frame(rows)
    b = 40
    cells, _ = ip.edge_map(fr, "K", min_fills=5, b=1)
    out = ip.h1_sign(fr, cells, k_col="K", min_fills=5, b=b, seed=4, draws=5)
    occ = sorted(cells.loc[cells["occupied"], "cell"])
    days = np.array(sorted(fr["day"].unique()))
    W = ip.day_multiplicities(len(days), b=b, seed=4)
    want = {"within_pos": [], "within_nonpos": [], "within_pos_buy": []}
    for w in W:
        rep = pd.concat([fr[fr["day"] == day] for day, m in zip(days, w) for _ in range(m)])
        g = rep[rep["cell"].isin(occ)].groupby("cell")
        A = 1e4 * g["edge"].sum() / g["idx"].sum()
        Bv = 1e4 * g["edge"].sum() / g["kk"].sum()
        buy = A.index.str.split("|").str[1] == "buy"
        for name, m in (("within_pos", A > 0), ("within_nonpos", A <= 0), ("within_pos_buy", (A > 0) & buy)):
            want[name].append(stats.spearmanr(A[m], Bv[m]).correlation if m.sum() >= 3 else np.nan)
    for name, brute in want.items():
        np.testing.assert_allclose(out[name]["_draws"], brute, atol=1e-12, err_msg=name)
        assert out[name]["lo"] == pytest.approx(np.nanquantile(brute, 0.05)), name
        assert out[name]["hi"] == pytest.approx(np.nanquantile(brute, 0.95)), name


def test_h1_interval_shape_percentile_basic_and_bias_corrected():
    """A28: exploratory description of the registered percentile interval (not centred on the estimate)."""
    rng = np.random.default_rng(0)
    draws = rng.normal(0.0, 1.0, 20_000)
    sym = ip.h1_interval_shape(draws, 0.0)
    assert sym["lo"] == pytest.approx(np.quantile(draws, 0.05)) and sym["hi"] == pytest.approx(np.quantile(draws, 0.95))
    assert sym["share_ge_stat"] == pytest.approx(np.mean(draws >= 0.0))
    assert sym["bc_lo"] == pytest.approx(sym["lo"], abs=0.03) and sym["bc_hi"] == pytest.approx(sym["hi"], abs=0.03)
    shifted = ip.h1_interval_shape(draws, 1.0)            # estimate at the 84th percentile of its draws
    assert shifted["basic_lo"] == pytest.approx(2.0 - shifted["hi"])
    assert shifted["basic_hi"] == pytest.approx(2.0 - shifted["lo"])
    z0 = stats.norm.ppf(np.mean(draws < 1.0))
    assert shifted["z0"] == pytest.approx(z0)
    z = stats.norm.ppf(0.95)
    assert shifted["bc_lo"] == pytest.approx(np.quantile(draws, stats.norm.cdf(2 * z0 - z)))
    assert shifted["bc_hi"] == pytest.approx(np.quantile(draws, stats.norm.cdf(2 * z0 + z)))
    assert shifted["mean_draw"] == pytest.approx(draws.mean()) and shifted["exploratory"] is True


def test_h3_review_rows_by_regime_manager_and_small_books_without_sm():
    md = _maker_days(40)
    md["manager"] = ["SM", "PM:ETH", "PM2:ETH", "PM2:HYPE"] * 10
    md["day"] = pd.to_datetime(["2026-01-10", "2026-03-01", "2026-06-01", "2026-09-01"] * 10)
    md["n_legs"] = [10, 100] * 20
    e, rows = ip.h3_review_rows(md, b=19)
    assert set(e["by_regime"]) == {"R1", "R2", "R3", "R4"} and set(e["by_account_manager"]) == {"SM", "PM", "PM2"}
    ok = (md["status"] == "ok") & (md["K_pm2"] > 0)
    small = ok & (md["n_legs"] <= 63) & (md["manager"] != "SM")
    assert e["sm_pm2_le63_no_sm"]["n"] == int(small.sum())
    assert e["sm_pm2_le63_no_sm"]["stat"] == pytest.approx(np.median(md.loc[small, "K_sm"] / md.loc[small, "K_pm2"]))
    pm2 = ok & md["manager"].str.startswith("PM2")
    assert e["by_account_manager"]["PM2"]["n"] == int(pm2.sum())
    groups = {(r["variant"], r["group"]) for r in rows}
    assert ("sm_pm2", "regime=R4") in groups and ("sm_pm2", "account_manager=SM") in groups
    assert ("sm_pm2_le63_no_sm", "all") in groups


def test_merge_rows_replaces_same_variant_and_group():
    old = pd.DataFrame({"variant": ["ratio", "ratio"], "group": ["all", "regime=R1"], "stat": [1.0, 2.0]})
    new = [{"variant": "ratio", "group": "regime=R1", "stat": 3.0}, {"variant": "ratio", "group": "regime=R2",
                                                                    "stat": 4.0}]
    got = ip._merge_rows(old, new)
    assert list(zip(got["group"], got["stat"])) == [("all", 1.0), ("regime=R1", 3.0), ("regime=R2", 4.0)]


def test_main_extras_adds_review_entries_and_keeps_the_rest(tmp_path):
    root = _synthetic_root(tmp_path)
    out = root / "results" / "p2"
    assert ip.main(["sensitivity", "--root", str(root), "--b", "19", "--min-fills", "20"]) == 0
    sens = json.loads((out / "sensitivity.json").read_text())
    assert {"sign_floor", "top_overlap", "within_pos", "within_nonpos"} <= set(sens["h1_sign"])
    assert "by_regime" in sens["d_h2"] and "by_account_manager" in sens["e_h3"]
    before = {k: v for k, v in sens.items() if k not in ("h1_sign", "h1_interval")}
    (out / "sensitivity.json").write_text(json.dumps(before))
    sh3 = pd.read_csv(out / "sens_h3.csv")
    n_before = len(sh3)
    assert ip.main(["extras", "--root", str(root), "--b", "19", "--min-fills", "20"]) == 0
    again = json.loads((out / "sensitivity.json").read_text())
    assert again["h1_sign"] == sens["h1_sign"]
    assert again["h1_interval"] == sens["h1_interval"]
    assert again["a_maps"] == sens["a_maps"]
    assert len(pd.read_csv(out / "sens_h3.csv")) == n_before     # replaced, not appended twice
