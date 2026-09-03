import numpy as np
import pandas as pd
import pytest

from derive_surface import pricing
from derive_surface.shock import StickyStrikeSmile, repriced_ladder, shocked_surface
from derive_surface.surface import Smile, Surface
from derive_surface.tape import surface_at, trade_ivs
from derive_surface.animate import Frame


def make_smile(F=100.0, T=30 / 365):
    k = np.linspace(-0.3, 0.3, 13)
    iv = 0.5 + 0.4 * k**2 - 0.2 * k  # a skewed smile
    return Smile.fit(1, T, F, 1.0, k, iv, np.ones_like(k))


def test_sticky_strike_keeps_iv_per_strike_and_sticky_delta_keeps_iv_per_moneyness():
    base = make_smile()
    surf = Surface(0, "X", 100.0, [base])
    K = 95.0
    up = shocked_surface(surf, 0.05, "sticky_delta").smiles[0]
    ss = shocked_surface(surf, 0.05, "sticky_strike").smiles[0]
    assert up.F == pytest.approx(105.0) and isinstance(ss, StickyStrikeSmile)
    # sticky strike: same strike -> same vol as before the move
    assert ss(np.array([np.log(K / ss.F)]))[0] == pytest.approx(base(np.array([np.log(K / base.F)]))[0], abs=1e-9)
    # sticky delta: same moneyness -> same vol; same strike -> vol has moved along the skew
    assert up(np.array([-0.05]))[0] == pytest.approx(base(np.array([-0.05]))[0], abs=1e-9)
    assert up(np.array([np.log(K / up.F)]))[0] != pytest.approx(base(np.array([np.log(K / base.F)]))[0], abs=1e-4)


def test_repriced_ladder_respects_put_call_parity_and_widths():
    base = make_smile()
    surf = Surface(0, "X", 100.0, [base])
    strikes = np.array([90.0, 100.0, 110.0])
    lad = pd.DataFrame(dict(strike=strikes, call_bid=[10.0, 4.0, 1.0], call_ask=[11.0, 5.0, 1.6], put_bid=[0.8, 3.9, 10.5], put_ask=[1.2, 4.9, 11.5]))
    frame = Frame(0, surf, lad, 1, 100.0)
    new, F = repriced_ladder(frame, shocked_surface(surf, 0.03, "sticky_delta"))
    assert F == pytest.approx(103.0)
    assert np.allclose(new["call_mid"] - new["put_mid"], F - strikes, atol=1e-9)  # Black-76 parity, df = 1
    assert np.allclose(new["call_ask"] - new["call_bid"], lad["call_ask"] - lad["call_bid"])


def test_trade_ivs_and_surface_from_fills():
    rng = np.random.default_rng(1)
    F, ts = 3000.0, 1_788_000_000_000
    expiry = int(ts / 1000 + 10 * 86400)
    T = (expiry - ts / 1000) / pricing.YEAR
    rows = []
    for _ in range(300):
        k = rng.uniform(-0.15, 0.15)
        K = F * np.exp(k)
        kind = 1 if K >= F else -1
        iv = 0.7 + 0.5 * k**2
        rows.append(dict(trade_id=str(len(rows)), timestamp=ts - int(rng.uniform(0, 6 * 3600) * 1000), instrument_name="X", expiry=expiry,
                         strike=K, option_type="C" if kind == 1 else "P", direction="buy", trade_price=pricing.price(F, K, T, iv, kind),
                         trade_amount=1.0, mark_price=np.nan, index_price=F, liquidity_role="taker", tx_status="settled"))
    fills = trade_ivs(pd.DataFrame(rows))
    assert len(fills) == 300 and fills["otm"].all()
    spot = pd.Series([F, F], index=[ts / 1000 - 86400, ts / 1000 + 86400])
    s = surface_at(fills, spot, ts, "X")
    assert s is not None and len(s.smiles) == 1
    sm = s.smiles[0]
    assert sm(np.array([0.0]))[0] == pytest.approx(0.7, abs=0.01)
    assert sm(np.array([0.1]))[0] == pytest.approx(0.705, abs=0.01)
