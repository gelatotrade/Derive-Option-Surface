import numpy as np
import pytest

from derive_surface import pricing
from derive_surface.api import OptionName
from derive_surface.surface import Smile, Surface
from tests.test_surface import synthetic_snapshot


def test_fractional_strike_names_parse():
    assert OptionName.parse("HYPE-20260904-77_5-C").strike == 77.5
    assert OptionName.parse("BTC-20260904-110000-P").strike == 110000.0


def test_implied_vol_outside_bracket_is_nan():
    F, K, T = 100.0, 100.0, 1 / 365
    V = pricing.price(F, K, T, 12.0, 1)  # 1200 % vol: outside the [0.001, 8] bracket
    assert np.isnan(pricing.implied_vol(V, F, K, T, 1))


def test_smile_skew_matches_finite_difference():
    df, F = synthetic_snapshot()
    sm = Surface.from_snapshot(df, "X").smiles[2]
    k = np.array([-0.05, 0.0, 0.04])
    fd = (sm(k + 1e-5) - sm(k - 1e-5)) / 2e-5
    assert np.allclose(sm.skew(k), fd, rtol=1e-4)


def test_calendar_pass_makes_total_variance_monotone():
    df, F = synthetic_snapshot()
    s = Surface.from_snapshot(df, "X")
    x, T, iv = s.grid("logm", n_tenors=12)
    w = iv**2 * T[:, None]
    assert np.all(np.diff(w, axis=0) >= -1e-12)


def test_std_axis_roundtrip():
    df, F = synthetic_snapshot()
    s = Surface.from_snapshot(df, "X")
    x, iv = s.iv_at_expiries("std", np.array([0.0]))
    assert np.allclose(iv[:, 0], s.atm_term_structure())


def test_mvdelta_sign_under_sticky_delta():
    df, F = synthetic_snapshot()
    g = Surface.from_snapshot(df, "X").greeks_grid("delta", n_tenors=4, ssr=0.0)
    # negative skew + sticky-delta: rising spot lowers every fixed-strike vol -> MV delta below BS delta
    assert np.nanmedian(g["skew"]) < 0 and np.nanmedian(g["mvdelta"]) > 0
