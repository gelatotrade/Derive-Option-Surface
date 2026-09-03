import numpy as np
import pandas as pd
import pytest

from derive_surface import pricing
from derive_surface.surface import DELTA_AXIS, Smile, Surface, quotes_from_snapshot


def synthetic_snapshot(F=78000.0, ts_ms=1_788_000_000_000, days=(1, 7, 30, 90), spread_vol=0.01):
    """A fake top-of-book built from a known SVI surface, quoted as bid/ask premiums."""
    rows = []
    for d in days:
        T = d / 365
        expiry = int(ts_ms / 1000 + d * 86400)
        params = np.array([0.02 * T, 0.4 * T, -0.3, 0.0, 0.2])  # raw SVI total variance
        strikes = F * np.exp(np.linspace(-0.35, 0.35, 15) * np.sqrt(T) * 3 + 0.0)
        for K in strikes:
            k = np.log(K / F)
            w = params[0] + params[1] * (params[2] * (k - params[3]) + np.sqrt((k - params[3]) ** 2 + params[4] ** 2))
            iv = np.sqrt(w / T)
            for kind, ot in ((1, "C"), (-1, "P")):
                bid = pricing.price(F, K, T, iv - spread_vol, kind)
                ask = pricing.price(F, K, T, iv + spread_vol, kind)
                rows.append(dict(ts=ts_ms, instrument_name=f"X-{d}-{K:.0f}-{ot}", expiry=expiry, strike=K, option_type=ot,
                                 bid=bid, ask=ask, bid_amount=1.0, ask_amount=1.0, mark=np.nan, index=F, forward=F,
                                 iv=iv, bid_iv=iv - spread_vol, ask_iv=iv + spread_vol, delta=np.nan, gamma=np.nan,
                                 vega=np.nan, theta=np.nan, rho=np.nan, discount_factor=1.0, open_interest=0.0))
    return pd.DataFrame(rows), F


def test_quotes_keep_only_otm_and_recover_iv():
    df, F = synthetic_snapshot()
    q = quotes_from_snapshot(df)
    assert ((q["kind"] == 1) == (q["strike"] >= F)).all()
    # mid of two symmetric-in-vol quotes is (to first order) the centre vol
    assert np.allclose(q["iv_mid"], q["iv"], atol=2e-3)
    assert (q["iv_bid"] < q["iv_mid"]).all() and (q["iv_ask"] > q["iv_mid"]).all()


def test_svi_fit_recovers_surface_within_spread():
    df, F = synthetic_snapshot()
    s = Surface.from_snapshot(df, "X")
    assert len(s.smiles) == 4 and all(sm.model == "svi" for sm in s.smiles)
    for sm in s.smiles:
        assert np.max(np.abs(sm(sm.k) - sm.iv)) < 0.01  # inside the 1-vol-point half spread


def test_grid_shapes_and_monotone_tenor_interpolation():
    df, F = synthetic_snapshot()
    s = Surface.from_snapshot(df, "X")
    x, T, iv = s.grid("delta", n_tenors=10)
    assert iv.shape == (10, len(DELTA_AXIS)) and np.all(np.isfinite(iv))
    assert T[0] == pytest.approx(s.tenors[0]) and T[-1] == pytest.approx(s.tenors[-1])
    x, T, iv = s.grid("logm", n_tenors=5)
    assert iv.shape == (5, 49)


def test_delta_axis_is_self_consistent():
    df, F = synthetic_snapshot()
    s = Surface.from_snapshot(df, "X")
    sm = s.smiles[2]
    K = sm.strike_for_call_delta(DELTA_AXIS)
    d = pricing.delta_of(sm.F, K, sm.T, sm(np.log(K / sm.F)), 1, sm.df)
    assert np.allclose(d, DELTA_AXIS, atol=1e-6)


def test_greeks_grid_contains_all_orders():
    df, F = synthetic_snapshot()
    g = Surface.from_snapshot(df, "X").greeks_grid("delta", n_tenors=6)
    for name in ("delta", "vega", "theta", "gamma", "vanna", "volga", "charm", "speed", "zomma", "color", "ultima"):
        assert g[name].shape == g["iv"].shape and np.all(np.isfinite(g[name]))
    assert (g["gamma"] > 0).all() and (g["vega"] > 0).all()


def test_thin_book_falls_back_gracefully():
    sm = Smile.fit(0, 0.1, 100.0, 1.0, np.array([-0.1, 0.0, 0.1]), np.array([0.6, 0.5, 0.55]), np.ones(3))
    assert sm.model == "quad"
    flat = Smile.fit(0, 0.1, 100.0, 1.0, np.array([0.0, 0.05]), np.array([0.5, 0.5]), np.ones(2))
    assert flat.model == "flat" and flat(np.array([0.3]))[0] == pytest.approx(0.5)
    # wings are held flat beyond the quoted range, never extrapolated into nonsense
    assert sm(np.array([2.0]))[0] == pytest.approx(sm(np.array([0.1 + sm.wing_pad]))[0])
    assert 0 < sm.wing_pad <= 0.05
