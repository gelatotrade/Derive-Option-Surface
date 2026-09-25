from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import markouts as mk
from derive_surface import pricing

T0 = 1_780_000_000_000                 # ms
EXP = 1_780_000_000 + 6 * 86_400 + 43_200   # s, 6.5 days later (away from bucket edges)
TAU = 0.02


def flat_curve(ts_s, vol, fwd, expiry=EXP, block=1):
    """SVI with b = 0: total variance a everywhere, vol = sqrt(a / refTau)."""
    return {"expiry": expiry, "feed_ts": ts_s, "block_ts": ts_s, "block": block, "log_index": 0,
            "svi_a": vol * vol * TAU, "svi_b": 0.0, "svi_rho": 0.0, "svi_m": 0.0, "svi_sigma": 0.1,
            "svi_fwd": fwd, "svi_ref_tau": TAU, "confidence": 0.95}


def fill_row(tid, ts, price, taker_side, strike=100.0, kind="C", currency="BTC", expiry=EXP, **kw):
    row = {"trade_id": tid, "ts": ts, "ts_maker": ts, "instrument_name": f"{currency}-X-{strike}-{kind}", "currency": currency,
           "expiry": expiry, "strike": strike, "option_type": kind, "price": price, "amount": 1.0, "mark_price": price,
           "index_price": 100.0, "taker_side": taker_side, "taker_wallet": "0xt", "maker_wallet": "0xm", "tx_status": "settled",
           "pair_ok": True, "notional": 100.0, "tx_hash": f"0x{tid}", "rfq_id": None, "taker_class": "other"}
    row.update(kw)
    return row


def bs(F, K, T_s, vol, kind=1):
    return float(pricing.price(F, K, T_s / pricing.YEAR, vol, kind))


def test_sample_fills_applies_every_exclusion_in_order():
    rows = [fill_row("ok", mk.SAMPLE_START_MS + 1, 5.0, 1),
            fill_row("alt", mk.SAMPLE_START_MS + 1, 5.0, 1, currency="SOL"),
            fill_row("early", mk.SAMPLE_START_MS - 1, 5.0, 1),
            fill_row("pending", mk.SAMPLE_START_MS + 1, 5.0, 1, tx_status="pending"),
            fill_row("badpair", mk.SAMPLE_START_MS + 1, 5.0, 1, pair_ok=False),
            fill_row("late", (EXP * 1000) - 10 * 60_000, 5.0, 1)]
    rows[-1]["ts"] = rows[-1]["expiry"] * 1000 - 10 * 60_000
    rows[-1]["expiry"] = rows[-1]["ts"] // 1000 + 600
    sample, steps = mk.sample_fills(pd.DataFrame(rows), cutoff_ms=mk.FINAL_CUTOFF_MS * 2)
    assert list(sample["trade_id"]) == ["ok"]
    assert steps == [("input", 6), ("core", 5), ("window", 4), ("settled", 3), ("pair_ok", 2), ("not_last_30min", 1)]


def test_state_signs_iv_and_buckets():
    svi = pd.DataFrame([flat_curve(T0 // 1000 - 10, 0.5, 100.0)])
    p = bs(100.0, 100.0, EXP - T0 / 1000, 0.5)
    rows = pd.DataFrame([fill_row("a", T0, p, -1), fill_row("b", T0 - 60_000, p, 1)])  # b: before any curve
    state, missing = mk.state_at_fill(rows, svi)
    assert missing == 1 and list(state["trade_id"]) == ["a"]
    r = state.iloc[0]
    assert r.maker_side == 1 and r.iv_fill == pytest.approx(0.5, abs=1e-6) and r.iv_mark_t == pytest.approx(0.5)
    assert r.mark_b_t == pytest.approx(p, rel=1e-9)
    assert r.delta_bucket == "40-60" and r.tenor_bucket == "2-7d" and r.tenor_days == pytest.approx(6.5, abs=1e-6)


def test_markouts_in_three_units():
    t1 = T0 // 1000 + 1800
    svi = pd.DataFrame([flat_curve(T0 // 1000 - 10, 0.5, 100.0, block=1), flat_curve(t1 - 5, 0.6, 102.0, block=2)])
    p = bs(100.0, 100.0, EXP - T0 / 1000, 0.5)
    rows = pd.DataFrame([fill_row("maker_buys", T0, p, -1), fill_row("maker_sells", T0, p, 1)])
    state, _ = mk.state_at_fill(rows, svi)
    marks = mk.marks_b(state, svi, {"30m": 1800})
    out = mk.add_markouts(state, marks, {"30m": 1800})
    m30 = bs(102.0, 100.0, EXP - (T0 / 1000 + 1800), 0.6)
    assert out.loc[0, "mo_usd_30m"] == pytest.approx(m30 - p, rel=1e-9)
    assert out.loc[1, "mo_usd_30m"] == pytest.approx(p - m30, rel=1e-9)
    assert out.loc[0, "mo_vol_30m"] == pytest.approx(10.0, abs=1e-4)
    delta = out.loc[0, "delta_t"]
    assert out.loc[0, "mo_dn_30m"] == pytest.approx((m30 - p) - delta * 2.0, rel=1e-9)
    assert abs(out.loc[0, "mo_dn_30m"]) < abs(out.loc[0, "mo_usd_30m"])


def test_horizon_at_or_after_expiry_is_nan():
    expiry = T0 // 1000 + 3000
    svi = pd.DataFrame([flat_curve(T0 // 1000 - 10, 0.5, 100.0, expiry=expiry)])
    p = bs(100.0, 100.0, expiry - T0 / 1000, 0.5)
    state, _ = mk.state_at_fill(pd.DataFrame([fill_row("a", T0, p, -1, expiry=expiry)]), svi)
    marks = mk.marks_b(state, svi, {"30m": 1800, "4h": 14_400})
    assert np.isfinite(marks.loc[0, "mark_b_30m"]) and np.isnan(marks.loc[0, "mark_b_4h"]) and np.isnan(marks.loc[0, "fwd_b_4h"])


def test_path_a_uses_first_fill_at_or_after_target():
    svi = pd.DataFrame([flat_curve(T0 // 1000 - 10, 0.5, 100.0)])
    rows = pd.DataFrame([fill_row("a", T0, 5.0, -1)])
    state, _ = mk.state_at_fill(rows, svi)
    later = pd.DataFrame([fill_row("x", T0 + 100_000, 1.0, 1, mark_price=6.0),
                          fill_row("y", T0 + 400_000, 1.0, 1, mark_price=7.0),
                          fill_row("z", T0 + 400_000, 1.0, 1, mark_price=9.0, instrument_name="OTHER")])
    out = mk.add_path_a(state, pd.concat([rows, later]), {"5m": 300})
    assert out.loc[0, "mark_a_5m"] == 7.0 and out.loc[0, "lag_a_5m_s"] == pytest.approx(100.0)
    assert out.loc[0, "mo_usd_a_5m"] == pytest.approx(2.0)


def test_settlement_payoff_and_vrp_adjustment():
    svi = pd.DataFrame([flat_curve(T0 // 1000 - 10, 0.5, 100.0)])
    rows = pd.DataFrame([fill_row("a", T0, 5.0, -1), fill_row("b", T0 + 1, 4.0, -1),
                         fill_row("p", T0 + 2, 25.0, 1, strike=130.0, kind="P")])  # deep ITM put: its own delta cell
    state, _ = mk.state_at_fill(rows, svi)
    settle = pd.DataFrame([{"currency": "BTC", "expiry": EXP, "expiry_date": "x", "settlement_price": 108.0}])
    out = mk.add_settlement(state, settle).set_index("trade_id")
    assert out.loc["a", "payoff"] == pytest.approx(8.0) and out.loc["a", "mo_set"] == pytest.approx(3.0)
    assert out.loc["p", "payoff"] == pytest.approx(22.0) and out.loc["p", "mo_set"] == pytest.approx(3.0)  # maker sold it at 25
    cell = out.loc[["a", "b"]]
    assert cell["mo_set_vrp"].sum() == pytest.approx(0.0) and out.loc["a", "mo_set_vrp"] == pytest.approx(-0.5)


def test_settlement_missing_for_live_expiry():
    svi = pd.DataFrame([flat_curve(T0 // 1000 - 10, 0.5, 100.0)])
    state, _ = mk.state_at_fill(pd.DataFrame([fill_row("a", T0, 5.0, -1)]), svi)
    out = mk.add_settlement(state, pd.DataFrame(columns=["currency", "expiry", "expiry_date", "settlement_price"]))
    assert np.isnan(out.loc[0, "mo_set"]) and np.isnan(out.loc[0, "mo_set_vrp"])


def test_flag_sweeps():
    def f(tid, ts, strike, wallet="0xs", currency="BTC"):
        return fill_row(tid, ts, 1.0, 1, strike=strike, taker_wallet=wallet, currency=currency)
    rows = [f(f"s{i}", T0 + 2_000 * i, 100.0 + 10 * (i % 3)) for i in range(5)]                  # 5 fills, 8 s, 3 strikes
    rows += [f(f"t{i}", T0 + 2_000 * i, 100.0 + 10 * (i % 2), wallet="0xtwo") for i in range(5)]  # only 2 strikes
    rows += [f(f"u{i}", T0 + 2_000 * i, 100.0 + 10 * i, wallet="0xfour") for i in range(4)]       # only 4 fills
    rows += [f(f"v{i}", T0 + 8_000 * i, 100.0 + 10 * i, wallet="0xslow") for i in range(5)]       # 32 s apart overall
    df = pd.DataFrame(rows)
    flags = mk.flag_sweeps(df)
    assert flags[df.taker_wallet == "0xs"].all()
    assert not flags[df.taker_wallet != "0xs"].any()


def test_size_flag_per_currency():
    rows = [fill_row(f"b{i}", T0, 1.0, 1, notional=float(i)) for i in range(10)]
    rows += [fill_row(f"e{i}", T0, 1.0, 1, currency="ETH", notional=float(100 * i)) for i in range(10)]
    out = mk.add_size_flag(pd.DataFrame(rows))
    assert list(out.loc[out.currency == "BTC", "size_above_p90"]) == [False] * 9 + [True]
    assert out["size_above_p90"].sum() == 2
