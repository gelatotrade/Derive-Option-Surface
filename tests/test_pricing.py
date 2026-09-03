import numpy as np
import pytest

from derive_surface import pricing as p


def fd(fn, x, h):
    return (fn(x + h) - fn(x - h)) / (2 * h)


@pytest.mark.parametrize("kind", [1, -1])
def test_put_call_parity(kind):
    F, K, T, s, df = 78000.0, 80000.0, 30 / 365, 0.55, 0.998
    c = p.price(F, K, T, s, 1, df)
    q = p.price(F, K, T, s, -1, df)
    assert c - q == pytest.approx(df * (F - K), rel=1e-12)


def test_implied_vol_roundtrip():
    rng = np.random.default_rng(0)
    F = 78000.0
    K = F * np.exp(rng.uniform(-0.6, 0.6, 500))
    T = rng.uniform(1 / 365, 1.0, 500)
    s = rng.uniform(0.2, 2.0, 500)
    kind = np.where(rng.random(500) < 0.5, 1, -1)
    V = p.price(F, K, T, s, kind, 0.999)
    iv = p.implied_vol(V, F, K, T, kind, 0.999)
    informative = V - p.intrinsic(F, K, kind, 0.999) > 1e-6 * F  # a quote with no time value carries no vol
    assert informative.sum() > 400
    assert np.allclose(iv[informative], s[informative], atol=1e-9)
    assert np.all(np.isnan(iv[~informative]) | np.isclose(iv[~informative], s[~informative], atol=1e-3))


def test_implied_vol_rejects_arbitrage():
    F, K, T = 100.0, 90.0, 0.1
    assert np.isnan(p.implied_vol(9.0, F, K, T, 1))  # below intrinsic
    assert np.isnan(p.implied_vol(101.0, F, K, T, 1))  # above forward
    assert np.isnan(p.implied_vol(np.nan, F, K, T, 1))


@pytest.mark.parametrize("kind", [1, -1])
@pytest.mark.parametrize("K", [60000.0, 78000.0, 95000.0])
def test_greeks_match_finite_differences(kind, K):
    F, T, s, df = 78000.0, 20 / 365, 0.6, 0.999
    g = p.greeks(F, K, T, s, kind, df)
    h_f, h_s, h_t = F * 1e-4, 1e-4, 1e-6
    # first order
    assert g["delta"] == pytest.approx(fd(lambda x: p.price(x, K, T, s, kind, df), F, h_f), rel=1e-5)
    assert g["vega"] == pytest.approx(fd(lambda x: p.price(F, K, T, x, kind, df), s, h_s), rel=1e-5)
    assert g["theta"] == pytest.approx(-fd(lambda x: p.price(F, K, x, s, kind, df), T, h_t), rel=1e-4)
    # second order
    assert g["gamma"] == pytest.approx(fd(lambda x: p.greeks(x, K, T, s, kind, df)["delta"], F, h_f), rel=1e-4)
    assert g["vanna"] == pytest.approx(fd(lambda x: p.greeks(F, K, T, x, kind, df)["delta"], s, h_s), rel=1e-4)
    assert g["vanna"] == pytest.approx(fd(lambda x: p.greeks(x, K, T, s, kind, df)["vega"], F, h_f), rel=1e-4)
    assert g["volga"] == pytest.approx(fd(lambda x: p.greeks(F, K, T, x, kind, df)["vega"], s, h_s), rel=1e-4)
    assert g["charm"] == pytest.approx(-fd(lambda x: p.greeks(F, K, x, s, kind, df)["delta"], T, h_t), rel=1e-3)
    # third order
    assert g["speed"] == pytest.approx(fd(lambda x: p.greeks(x, K, T, s, kind, df)["gamma"], F, h_f), rel=1e-3)
    assert g["zomma"] == pytest.approx(fd(lambda x: p.greeks(F, K, T, x, kind, df)["gamma"], s, h_s), rel=1e-3)
    assert g["color"] == pytest.approx(-fd(lambda x: p.greeks(F, K, x, s, kind, df)["gamma"], T, h_t), rel=1e-3)
    assert g["ultima"] == pytest.approx(fd(lambda x: p.greeks(F, K, T, x, kind, df)["volga"], s, h_s), rel=1e-3)


def test_strike_for_delta_inverts_delta():
    F, T, s = 3000.0, 45 / 365, 0.8
    for kind, target in [(1, 0.25), (-1, -0.25), (1, 0.5)]:
        K = p.strike_for_delta(target, F, T, s, kind)
        assert p.delta_of(F, K, T, s, kind) == pytest.approx(target, abs=1e-9)
