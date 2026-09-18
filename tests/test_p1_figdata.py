from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import figdata

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


def test_waterfall_components_add_up_to_the_net_edge():
    rows = frame()
    out = figdata.waterfall_components(rows, taker_class="other")
    total = out.loc[out["step"] != "net edge", "value"].sum()
    assert total == pytest.approx(out.loc[out["step"] == "net edge", "value"].iloc[0], abs=1e-9)
    assert list(out["step"])[:2] == ["half spread", "adverse selection"]


def test_example_fill_picks_a_representative_trade():
    rows = frame()
    rows.loc[0, ["mo_usd_30m", "hs", "as_usd"]] = [3.0, 2.0, 1.0]
    got = figdata.example_fill(rows, taker_class="other")
    assert set(["ts", "hs", "as_usd", "mo_usd_30m"]) <= set(got.index)
