from __future__ import annotations

import math

import pytest

from derive_surface.p2types import Book, ExpiryState, MarketState, OptionLeg, capital_from_net


def _state():
    e = ExpiryState(expiry=1_790_000_000, forward=101.0, svi=(0.01, 0.05, -0.2, 0.0, 0.2, 0.1), rate=0.04)
    return MarketState(currency="BTC", ts=1_780_000_000, spot=100.0, expiries={e.expiry: e})


def test_expiry_state_tau_in_years():
    st = _state()
    e = st.expiries[1_790_000_000]
    assert st.tau(e.expiry) == pytest.approx(10_000_000 / (365.0 * 86400.0))


def test_expiry_state_vol_uses_svi_on_log_moneyness():
    st = _state()
    e = st.expiries[1_790_000_000]
    a, b, rho, m, sig, ref_tau = e.svi
    k = math.log(120.0 / e.forward)
    w = a + b * (rho * (k - m) + math.sqrt((k - m) ** 2 + sig ** 2))
    assert e.vol(120.0) == pytest.approx(math.sqrt(w / ref_tau))


def test_book_legs_and_premium():
    book = Book(options=[OptionLeg(1_790_000_000, 100.0, True, -2.0), OptionLeg(1_790_000_000, 90.0, False, 1.0)])
    assert book.expiries() == [1_790_000_000]
    assert book.premium({(1_790_000_000, 100.0, True): 5.0, (1_790_000_000, 90.0, False): 2.0}) == pytest.approx(-8.0)


def test_capital_from_net_is_premium_minus_net():
    # K_p(q) = sum p q - net(q; C = 0)
    assert capital_from_net(premium=-8.0, net_zero_cash=-20.0) == pytest.approx(12.0)
