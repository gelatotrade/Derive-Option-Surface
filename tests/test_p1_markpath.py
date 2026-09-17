from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import markpath, pricing
from derive_surface.chainfeeds import svi_vol

EXP_A, EXP_B = 1_800_000_000, 1_800_086_400


def svi_rows():
    base = dict(svi_a=0.0001, svi_b=0.01, svi_rho=-0.2, svi_m=-0.005, svi_sigma=0.01, svi_ref_tau=0.01, confidence=0.95)
    return pd.DataFrame([
        {**base, "expiry": EXP_A, "feed_ts": 1_000, "block_ts": 1_010, "block": 1, "log_index": 0, "svi_fwd": 100.0},
        {**base, "expiry": EXP_A, "feed_ts": 2_000, "block_ts": 2_030, "block": 2, "log_index": 0, "svi_fwd": 110.0},
        {**base, "expiry": EXP_B, "feed_ts": 1_500, "block_ts": 1_505, "block": 3, "log_index": 0, "svi_fwd": 500.0},
    ])


def fills():
    return pd.DataFrame({
        "trade_id": ["x", "y", "z", "w"],
        "ts": [2_020_000, 2_040_000, 1_600_000, 900_000],
        "expiry": [EXP_A, EXP_A, EXP_B, EXP_A],
        "strike": [105.0, 105.0, 480.0, 100.0],
        "option_type": ["C", "P", "C", "C"],
    })


def test_attach_svi_uses_latest_curve_of_the_same_expiry_by_push_time():
    out = markpath.attach_svi(fills(), svi_rows(), at_ms="ts", clock="block_ts").set_index("trade_id")
    assert out.loc["x", "svi_fwd"] == 100.0  # the 2 000 curve was signed before but pushed after the fill
    assert out.loc["y", "svi_fwd"] == 110.0
    assert out.loc["z", "svi_fwd"] == 500.0  # never the other expiry's curve
    assert np.isnan(out.loc["w", "svi_fwd"])  # no curve yet
    assert list(out.index) == ["x", "y", "z", "w"]  # input order kept


def test_attach_svi_by_signing_time():
    out = markpath.attach_svi(fills(), svi_rows(), at_ms="ts", clock="feed_ts").set_index("trade_id")
    assert out.loc["x", "svi_fwd"] == 110.0
    assert out.loc["x", "svi_age_s"] == 20


def test_mark_from_svi_matches_black76_with_svi_vol():
    f = markpath.attach_svi(fills(), svi_rows(), at_ms="ts", clock="block_ts")
    got = markpath.mark_from_svi(f, at_ms="ts")
    r = f.iloc[0]
    T = (r.expiry - r.ts / 1000) / pricing.YEAR
    vol = float(svi_vol(r.strike, r.svi_a, r.svi_b, r.svi_rho, r.svi_m, r.svi_sigma, r.svi_fwd, r.svi_ref_tau))
    assert got.iloc[0] == pytest.approx(float(pricing.price(r.svi_fwd, r.strike, T, vol, 1)), rel=1e-12)
    assert got.iloc[1] > 0 and np.isnan(got.iloc[3])


def test_mark_from_svi_with_other_forward():
    f = markpath.attach_svi(fills(), svi_rows(), at_ms="ts", clock="block_ts")
    f["fwd_now"] = 120.0
    a = markpath.mark_from_svi(f, at_ms="ts")
    b = markpath.mark_from_svi(f, at_ms="ts", forward="fwd_now")
    assert b.iloc[0] > a.iloc[0]  # a call gains when the forward rises
