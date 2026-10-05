"""Tests for the capital per fill of Paper 2 (derive_surface.capital, task B2).

K_p(q) = p q - net_IM(q; cash = 0) for the one-contract book q = maker_side (+1 maker buy, -1 maker sell) at the fill
price p, under every manager whose window is open (PRAEREGISTRIERUNG.md, sections Sample and Semantics and capital).
All tests run offline on synthetic feeds; the parameter timelines are the tracked files under results/p2/params.
"""
from __future__ import annotations

import datetime as dt
import json
import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from derive_surface import capital as cap
from derive_surface import margin_pm, margin_pm2, margin_sm
from derive_surface import p2feeds as pf
from derive_surface.p2chain import ts_at_block
from derive_surface.p2params import Timeline
from derive_surface.p2types import YEAR, Book, MarketState, OptionLeg

PM2_START_BTC = int(dt.datetime(2025, 6, 12, 23, 0, tzinfo=dt.timezone.utc).timestamp())
HYPE_START = int(dt.datetime(2025, 11, 11, 0, 0, tzinfo=dt.timezone.utc).timestamp())

# v2-core test config (Config.getSRMParams) as in tests/test_p2_margin_sm.py
SM_PARAMS = {
    "OptionMarginParams": dict(maxSpotReq=0.15, minSpotReq=0.1, mmCallSpotReq=0.075, mmPutSpotReq=0.075,
                               MMPutMtMReq=0.075, unpairedIMScale=1.2, unpairedMMScale=1.1, mmOffsetScale=1.05),
    "PerpMarginRequirements": {"mmPerpReq": 0.05, "imPerpReq": 0.065},
    "BaseMarginParams": {"marginFactor": 0.8, "IMScale": 1.0},
    "OracleContingencyParams": {"perpThreshold": 0.4, "optionThreshold": 0.4, "baseThreshold": 0.4, "OCFactor": 0.4},
    "DepegParams": {"threshold": 0.98, "depegFactor": 1.2},
}


def _b76_call(F, K, sigma, sec):
    t = sec / YEAR
    d1 = (math.log(F / K) + 0.5 * sigma * sigma * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return F * norm.cdf(d1) - K * norm.cdf(d2)


def _arrays(n=1, **kw):
    base = {"spot": 100.0, "forward": 101.0, "sigma": 0.5, "tau": 30 * 86400 / YEAR, "rate": 0.0, "strike": 110.0,
            "is_call": True, "amount": -1.0, "vol_conf": 1.0, "fwd_conf": 1.0, "spot_conf": 1.0, "rate_conf": 1.0,
            "fwd_fixed": 0.0, "rate_pm": 0.0, "stable": 1.0}
    base.update(kw)
    return {k: np.full(n, v) if np.ndim(v) == 0 else np.asarray(v) for k, v in base.items()}


# ---------------------------------------------------------------- manager windows (preregistration)

def test_windows_follow_the_preregistration():
    assert cap.WINDOW_START["pm2"]["BTC"] == PM2_START_BTC
    assert cap.WINDOW_START["pm2"]["ETH"] == PM2_START_BTC
    assert cap.WINDOW_START["pm2"]["HYPE"] == HYPE_START
    assert cap.WINDOW_START["sm"]["HYPE"] == HYPE_START
    assert "HYPE" not in cap.WINDOW_START["pm"]
    t = np.array([PM2_START_BTC - 1, PM2_START_BTC])
    assert cap.in_window("BTC", "pm2", t).tolist() == [False, True]
    assert cap.in_window("ETH", "pm2", t).tolist() == [False, True]
    h = np.array([HYPE_START - 1, HYPE_START, HYPE_START + 10 ** 7])
    assert cap.in_window("HYPE", "pm2", h).tolist() == [False, True, True]
    assert cap.in_window("HYPE", "sm", h).tolist() == [False, True, True]
    assert cap.in_window("HYPE", "pm", h).tolist() == [False, False, False]
    first = np.array([1_704_931_200, 1_704_931_231])  # 11.01.2024 00:00 UTC, first ETH fill of Paper 1
    for ccy in ("BTC", "ETH"):
        assert cap.in_window(ccy, "sm", first).all() and cap.in_window(ccy, "pm", first).all()


# ---------------------------------------------------------------- hand-computed capital per manager

def test_sm_short_call_capital_by_hand():
    a = _arrays()
    price = 2.0
    k_im, v = cap.capital_single("sm", a, SM_PARAMS, np.array([price]), is_initial=True)
    k_mm, _ = cap.capital_single("sm", a, SM_PARAMS, np.array([price]), is_initial=False)
    call = _b76_call(101.0, 110.0, 0.5, 30 * 86400)
    # otm ratio (110 - 100) / 100 = 0.1: imMultiplier = max(0.15 - 0.1, minSpotReq 0.1) = 0.1
    # net = -0.1 S + mtm with mtm = -call; the max-loss branch -1.2 F is worse, so isolated margin binds
    assert v[0] == pytest.approx(-call, rel=1e-9)
    assert k_im[0] == pytest.approx(-price + 0.1 * 100.0 + call, rel=1e-9)
    # MM: mmCallSpotReq * S = 7.5
    assert k_mm[0] == pytest.approx(-price + 7.5 + call, rel=1e-9)


def test_sm_short_put_capital_by_hand():
    a = _arrays(forward=100.0, strike=90.0, sigma=0.6, is_call=False)
    price = 1.5
    k_im, v = cap.capital_single("sm", a, SM_PARAMS, np.array([price]), is_initial=True)
    put = _b76_call(100.0, 90.0, 0.6, 30 * 86400) - (100.0 - 90.0)  # put-call parity with D = 1
    assert v[0] == pytest.approx(-put, rel=1e-9)
    # otm 0.1 -> multiplier 0.1: -10 + mtm; the mm branch (-7.5 + mtm) * 1.05 is less binding; max loss -90 not
    assert k_im[0] == pytest.approx(-price + 10.0 + put, rel=1e-9)


def test_sm_long_capital_is_the_premium_exactly():
    rng = np.random.default_rng(3)
    n = 500
    a = _arrays(n, strike=rng.uniform(50, 150, n), is_call=rng.random(n) < 0.5, amount=np.ones(n),
                sigma=rng.uniform(0.2, 2.0, n), tau=rng.uniform(1e-4, 2.0, n), vol_conf=rng.choice([1.0, 0.2], n))
    price = rng.uniform(1e-6, 60.0, n)
    for is_initial in (True, False):
        k, _ = cap.capital_single("sm", a, SM_PARAMS, price, is_initial=is_initial)
        assert np.array_equal(k, price)


def _pm2_params():
    return Timeline("BTC", "pm2").at(PM2_START_BTC + 86400)


def _pm_params():
    return Timeline("BTC", "pm").at(PM2_START_BTC + 86400)


def _state(ts, expiry, *, spot=100_000.0, forward=100_400.0, rate=0.04, rate_conf=1.0, fwd_fixed=0.0,
           vol_conf=1.0, fwd_conf=1.0, spot_conf=1.0):
    es = pf.FeedExpiryState(expiry=expiry, forward=forward, svi=None, rate=rate, vol_conf=vol_conf, fwd_conf=fwd_conf,
                            fwd_fixed=fwd_fixed, rate_conf=rate_conf)
    return MarketState(currency="BTC", ts=ts, spot=spot, expiries={expiry: es}, spot_conf=spot_conf)


@pytest.mark.parametrize("q", [1.0, -1.0])
@pytest.mark.parametrize("is_call", [True, False])
@pytest.mark.parametrize("is_initial", [True, False])
def test_pm2_capital_equals_premium_minus_net_margin_of_the_book(q, is_call, is_initial):
    params = _pm2_params()
    ts = PM2_START_BTC + 86400
    expiry = ts + 40 * 86400
    strike, sigma, price = 104_000.0, 0.55, 3_210.0
    a = _arrays(spot=100_000.0, forward=100_400.0, sigma=sigma, tau=(expiry - ts) / YEAR, rate=0.04, strike=strike,
                is_call=is_call, amount=q, vol_conf=0.97, fwd_conf=0.99, rate_conf=0.98)
    k, v = cap.capital_single("pm2", a, params, np.array([price]), is_initial=is_initial)
    st = _state(ts, expiry, vol_conf=0.97, fwd_conf=0.99, rate_conf=0.98)
    net, mtm = margin_pm2.net_margin(Book(options=[OptionLeg(expiry, strike, is_call, q)]), st, params, is_initial,
                                     vols={(expiry, strike): sigma})
    assert k[0] == pytest.approx(price * q - net, rel=1e-10)
    assert v[0] == pytest.approx(mtm, rel=1e-10)


@pytest.mark.parametrize("q", [1.0, -1.0])
def test_pm_capital_uses_the_legacy_rate_feed_not_the_pm2_feed(q):
    params = _pm_params()
    ts = PM2_START_BTC + 86400
    expiry = ts + 120 * 86400
    strike, sigma, price = 95_000.0, 0.6, 9_000.0
    # the PM2 rate feed says 8 % at confidence 0.1; the legacy manager reads its own static feed (0 at confidence 1)
    a = _arrays(spot=100_000.0, forward=100_400.0, sigma=sigma, tau=(expiry - ts) / YEAR, rate=0.08, rate_conf=0.1,
                rate_pm=0.0, strike=strike, is_call=False, amount=q)
    arr = cap.manager_arrays("pm", a)
    assert np.all(arr["rate_conf"] == 1.0) and np.all(arr["rate_pm"] == 0.0)
    k, _ = cap.capital_single("pm", arr, params, np.array([price]))
    st = _state(ts, expiry, rate=0.08, rate_conf=0.1)
    net, _ = margin_pm.net_margin(Book(options=[OptionLeg(expiry, strike, False, q)]), st, params,
                                  vols={(expiry, strike): sigma})
    assert k[0] == pytest.approx(price * q - net, rel=1e-10)
    # PM2 keeps its own rate and rate confidence
    arr2 = cap.manager_arrays("pm2", a)
    assert np.all(arr2["rate"] == 0.08) and np.all(arr2["rate_conf"] == 0.1)


# ---------------------------------------------------------------- end to end on a synthetic feed history

B0 = 24_866_000                        # 2025-06-12 18:40:15 UTC, a few hours before the BTC PM2 window
E1 = 1_751_011_200                     # 2025-06-27 08:00 UTC
E2 = 1_751_616_000                     # 2025-07-04 08:00 UTC (no SVI curve -> nan)


def _frame(rows, cols=("block", "log_index", "expiry", "value", "confidence", "feed_ts")):
    df = pd.DataFrame(rows, columns=list(cols))
    df.insert(1, "block_ts", [ts_at_block(b) for b in df["block"]])
    return df


def _frames():
    spot = _frame([(B0, 0, 0, 105_000.0, 1.0, ts_at_block(B0) - 1),
                   (B0 + 12_000, 0, 0, 106_000.0, 1.0, ts_at_block(B0 + 12_000) - 2)])
    fwd = _frame([(B0 + 1, 0, E1, 150.0, 1.0, ts_at_block(B0 + 1) - 1),
                  (B0 + 1, 1, E2, 300.0, 1.0, ts_at_block(B0 + 1) - 1),
                  (B0 + 12_001, 0, E1, 180.0, 0.99, ts_at_block(B0 + 12_001) - 1)])
    fwd["fixed"] = 0.0
    rate = _frame([(B0 + 2, 0, E1, 0.037, 1.0, ts_at_block(B0 + 2) - 5),
                   (B0 + 2, 1, E2, 0.038, 1.0, ts_at_block(B0 + 2) - 5)])
    perp = _frame([(B0, 1, 0, 10.0, 1.0, ts_at_block(B0) - 1)])
    rate_pm = _frame([(843_076, 0, 0, 0.0, 1.0, ts_at_block(843_076))])[["block", "block_ts", "log_index", "expiry",
                                                                         "value", "confidence", "feed_ts"]]
    svi = pd.DataFrame({"block": [B0 + 3], "block_ts": [ts_at_block(B0 + 3)], "log_index": [0], "expiry": [E1],
                        "feed_ts": [ts_at_block(B0 + 3) - 4], "svi_a": np.float32([0.004]),
                        "svi_b": np.float32([0.02]), "svi_rho": np.float32([-0.2]), "svi_m": np.float32([0.0]),
                        "svi_sigma": np.float32([0.1]), "svi_fwd": [105_150.0], "svi_ref_tau": np.float32([0.04]),
                        "confidence": np.float32([0.98])})
    return {"spot": spot, "forward": fwd, "rate_pm2": rate, "perp": perp, "rate_pm": rate_pm, "svi": svi}


def _hist(**kw):
    return pf.FeedHistory("BTC", frames=_frames(), **kw)


def _fills():
    t_pre = (PM2_START_BTC - 600) * 1000 + 250           # 22:50 UTC, before the PM2 window
    t_in = PM2_START_BTC * 1000 + 999                     # 23:00:00.999, first second of the window
    t_late = ts_at_block(B0 + 12_000) * 1000 + 1_000      # 13.06. 01:40:16, after the second spot push
    rows = [
        ("a", t_pre, E1, 110_000.0, "C", 900.0, 2.0, 1),
        ("b", t_pre, E1, 100_000.0, "P", 800.0, 1.0, -1),
        ("c", t_in, E1, 110_000.0, "C", 910.0, 0.5, -1),
        ("d", t_in, E1, 98_000.0, "P", 500.0, 3.0, 1),
        ("e", t_late, E1, 112_000.0, "C", 700.0, 1.0, -1),
        ("f", t_late, E2, 112_000.0, "C", 1_000.0, 1.0, -1),   # no SVI curve for E2 -> nan everywhere
    ]
    df = pd.DataFrame(rows, columns=["trade_id", "ts", "expiry", "strike", "option_type", "price", "amount",
                                     "maker_side"])
    df["currency"] = "BTC"
    df["index_price"] = 105_000.0
    return df


def _timelines(ccy="BTC"):
    return cap.load_timelines(ccy)


def test_fill_capital_end_to_end():
    fills = _fills()
    hist = _hist()
    out = cap.capital_for(fills, hist, _timelines(), "BTC")
    assert list(out.columns) == cap.OUT_COLUMNS
    assert out["trade_id"].tolist() == fills["trade_id"].tolist()
    ts_s = fills["ts"].to_numpy() // 1000
    # feeds exactly as FeedHistory.bulk at the taker second
    feed = hist.bulk(ts_s, fills["expiry"].to_numpy(), fills["strike"].to_numpy())
    for c in ("spot", "forward", "sigma", "rate", "vol_conf", "fwd_conf", "spot_age", "fwd_age", "vol_age",
              "rate_age"):
        np.testing.assert_array_equal(out[c].to_numpy(), feed[c].to_numpy(), err_msg=c)
    # time to expiry from the block of the taker second (2 s blocks at odd timestamps)
    block_ts = np.array([ts_at_block(b) for b in out["block"]])
    assert np.all((ts_s - block_ts >= 0) & (ts_s - block_ts <= 1))
    np.testing.assert_array_equal(out["sec"].to_numpy(), fills["expiry"].to_numpy() - block_ts)
    by = out.set_index("trade_id")
    # PM2 window: nan before 12.06.2025 23:00 UTC, set from then on; SM and PM always
    assert np.isnan(by.loc[["a", "b"], ["K_pm2", "K_pm2_mm", "V_pm2"]].to_numpy()).all()
    assert (by.loc[["a", "b"], "reg_pm2"] == -1).all()
    assert np.isfinite(by.loc[["c", "d", "e"], ["K_sm", "K_pm", "K_pm2", "K_sm_mm", "K_pm_mm", "K_pm2_mm"]]
                       .to_numpy()).all()
    assert np.isfinite(by.loc[["a", "b"], ["K_sm", "K_pm", "K_sm_mm", "K_pm_mm"]].to_numpy()).all()
    # SM long = fill price exactly
    for tid in ("a", "d"):
        assert by.loc[tid, "K_sm"] == by.loc[tid, "price"] and by.loc[tid, "K_sm_mm"] == by.loc[tid, "price"]
    # missing SVI curve -> nan under every manager, not an error
    assert np.isnan(by.loc["f", ["K_sm", "K_pm", "K_pm2", "K_sm_mm", "K_pm_mm", "K_pm2_mm"]].to_numpy(float)).all()
    # every value equals p q - net of the one-leg book at the block state with the regime's parameters
    tls = _timelines()
    for tid in ("c", "d", "e"):
        row = by.loc[tid]
        t = ts_at_block(int(row["block"]))
        st = hist.state_at(int(row["ts"]) // 1000, [int(row["expiry"])])
        st = MarketState(currency="BTC", ts=t, spot=st.spot, expiries=st.expiries, perp=st.perp,
                         spot_conf=st.spot_conf, perp_conf=st.perp_conf)
        book = Book(options=[OptionLeg(int(row["expiry"]), float(row["strike"]), row["option_type"] == "C",
                                       float(row["maker_side"]))])
        pq = float(row["price"]) * float(row["maker_side"])
        for mgr, engine in (("sm", margin_sm), ("pm", margin_pm), ("pm2", margin_pm2)):
            params = tls[mgr].at(int(row["ts"]) // 1000)
            assert row[f"reg_{mgr}"] == tls[mgr].entry_at(int(row["ts"]) // 1000)["from_ts"]
            for is_initial, col in ((True, f"K_{mgr}"), (False, f"K_{mgr}_mm")):
                net, mtm = engine.net_margin(book, st, params, is_initial)
                assert row[col] == pytest.approx(pq - net, rel=1e-9, abs=1e-9), (tid, col)
            assert row[f"V_{mgr}"] == pytest.approx(mtm, rel=1e-9, abs=1e-9)


def test_regimes_use_the_parameters_in_force_at_the_fill():
    fills = _fills().iloc[2:5].reset_index(drop=True)
    ts_s = fills["ts"].to_numpy() // 1000
    change = int(ts_s[2])            # the late fill sits exactly on the change: the new state applies
    loose = json.loads(json.dumps(SM_PARAMS))
    tight = json.loads(json.dumps(SM_PARAMS))
    tight["OptionMarginParams"]["maxSpotReq"] = 0.4
    tight["OptionMarginParams"]["minSpotReq"] = 0.3
    tl = Timeline("BTC", "sm", entries=[{"from_block": 1, "from_ts": 1_700_000_000, "params": loose},
                                        {"from_block": 2, "from_ts": change, "params": tight}])
    tls = dict(_timelines(), sm=tl)
    out = cap.capital_for(fills, _hist(), tls, "BTC").set_index("trade_id")
    assert out.loc["c", "reg_sm"] == 1_700_000_000 and out.loc["e", "reg_sm"] == change
    feed = _hist().bulk(ts_s, fills["expiry"].to_numpy(), fills["strike"].to_numpy())
    base = cap.engine_arrays(fills, feed)
    for i, (tid, params) in enumerate((("c", loose), ("d", loose), ("e", tight))):
        one = {k: v[i:i + 1] for k, v in base.items()}
        k, _ = cap.capital_single("sm", one, params, fills["price"].to_numpy()[i:i + 1])
        assert out.loc[tid, "K_sm"] == pytest.approx(k[0], rel=1e-12)
    # a fill before the first entry of a timeline gets nan (no parameters), not an error
    tl_late = Timeline("BTC", "sm", entries=[{"from_block": 2, "from_ts": change, "params": tight}])
    out2 = cap.capital_for(fills, _hist(), dict(_timelines(), sm=tl_late), "BTC").set_index("trade_id")
    assert np.isnan(out2.loc[["c", "d"], "K_sm"]).all() and np.isfinite(out2.loc["e", "K_sm"])
    assert (out2.loc[["c", "d"], "reg_sm"] == -1).all()


def test_hype_windows_end_to_end():
    fills = pd.DataFrame({"trade_id": ["h0", "h1"], "ts": [(HYPE_START - 60) * 1000, (HYPE_START + 60) * 1000],
                          "expiry": [HYPE_START + 7 * 86400] * 2, "strike": [40.0, 40.0], "option_type": ["C", "C"],
                          "price": [1.0, 1.0], "amount": [10.0, 10.0], "maker_side": [-1, -1],
                          "currency": ["HYPE", "HYPE"], "index_price": [40.0, 40.0]})
    E = HYPE_START + 7 * 86400
    b = 31_390_000   # 2025-11-10 19:06:55 UTC
    spot = _frame([(b, 0, 0, 40.0, 1.0, ts_at_block(b) - 1)])
    fwd = _frame([(b, 1, E, 0.1, 1.0, ts_at_block(b) - 1)])
    fwd["fixed"] = 0.0
    svi = pd.DataFrame({"block": [b], "block_ts": [ts_at_block(b)], "log_index": [2], "expiry": [E],
                        "feed_ts": [ts_at_block(b) - 1], "svi_a": np.float32([0.01]), "svi_b": np.float32([0.03]),
                        "svi_rho": np.float32([-0.1]), "svi_m": np.float32([0.0]), "svi_sigma": np.float32([0.1]),
                        "svi_fwd": [40.1], "svi_ref_tau": np.float32([0.02]), "confidence": np.float32([1.0])})
    hist = pf.FeedHistory("HYPE", frames={"spot": spot, "forward": fwd, "svi": svi})
    out = cap.capital_for(fills, hist, cap.load_timelines("HYPE"), "HYPE").set_index("trade_id")
    for col in ("K_sm", "K_pm2", "K_sm_mm", "K_pm2_mm"):
        assert np.isnan(out.loc["h0", col]) and np.isfinite(out.loc["h1", col]), col
    assert np.isnan(out[["K_pm", "K_pm_mm", "V_pm"]].to_numpy(float)).all()
    assert (out["reg_pm"] == -1).all()


# ---------------------------------------------------------------- resumable run over monthly parts

def test_run_writes_monthly_parts_resumes_and_combines(tmp_path):
    fills = _fills()
    later = fills.iloc[[4]].copy()
    later["trade_id"] = "g"
    later["expiry"] = E2
    later["ts"] = (1_751_328_000 + 3600) * 1000        # 2025-07-01 01:00 UTC: a second monthly part
    fills = pd.concat([fills, later], ignore_index=True)
    fills["currency"] = "BTC"
    mk = tmp_path / "markouts.parquet"
    fills.to_parquet(mk)
    parts = tmp_path / "parts"
    calls = []

    def factory(ccy, start_ts, end_ts):
        calls.append((ccy, start_ts, end_ts))
        return pf.FeedHistory(ccy, frames=_frames(), start_ts=start_ts, end_ts=end_ts)

    kw = dict(markouts=mk, parts_dir=parts, history_factory=factory, months_per_window=1)
    r1 = cap.run(["BTC"], max_seconds=0.0, **kw)          # budget exhausted after the first window
    assert r1["done"] is False and r1["written"] == 1 and len(calls) == 1
    r2 = cap.run(["BTC"], **kw)
    assert r2["done"] is True and r2["written"] == 1 and len(calls) == 2
    r3 = cap.run(["BTC"], **kw)
    assert r3["done"] is True and r3["written"] == 0 and len(calls) == 2
    # each window loads exactly the span of its fills
    assert calls[0] == ("BTC", int(fills["ts"].iloc[:6].min() // 1000), int(fills["ts"].iloc[:6].max() // 1000))
    out_path = tmp_path / "capital.parquet"
    df = cap.combine(parts_dir=parts, out=out_path, markouts=mk)
    assert len(df) == len(fills) and set(df["trade_id"]) == set(fills["trade_id"])
    assert list(df.columns) == cap.OUT_COLUMNS
    direct = cap.capital_for(fills, _hist(), _timelines(), "BTC").set_index("trade_id")
    got = df.set_index("trade_id").loc[direct.index]
    np.testing.assert_allclose(got["K_pm2"].to_numpy(float), direct["K_pm2"].to_numpy(float), rtol=1e-12,
                               equal_nan=True)
    assert pd.read_parquet(out_path).shape == df.shape


def test_combine_refuses_missing_fills(tmp_path):
    fills = _fills()
    mk = tmp_path / "markouts.parquet"
    fills.to_parquet(mk)
    parts = tmp_path / "parts"

    def factory(ccy, start_ts, end_ts):
        return pf.FeedHistory(ccy, frames=_frames(), start_ts=start_ts, end_ts=end_ts)

    cap.run(["BTC"], markouts=mk, parts_dir=parts, history_factory=factory)
    extra = pd.concat([fills, fills.iloc[[0]].assign(trade_id="zz", currency="ETH")], ignore_index=True)
    extra.to_parquet(mk)
    with pytest.raises(ValueError, match="missing"):
        cap.combine(parts_dir=parts, out=tmp_path / "c.parquet", markouts=mk)


# ---------------------------------------------------------------- plausibility (no inference)

def test_plausibility_counts_nan_and_nonpositive_capital():
    out = cap.capital_for(_fills(), _hist(), _timelines(), "BTC")
    for tid, k in (("c", -1.0), ("d", 5.0), ("e", 3.0)):   # plant values: one non-positive sell
        out.loc[out["trade_id"] == tid, "K_pm2"] = k
    chk = cap.plausibility(out)
    pm2 = chk["managers"]["BTC"]["pm2"]
    assert pm2["n"] == 6 and pm2["n_in_window"] == 4
    assert pm2["nan_in_window"] == 1 and pm2["share_nan_in_window"] == pytest.approx(0.25)
    assert pm2["share_nan"] == pytest.approx(3 / 6)
    assert pm2["sides"]["sell"]["k_le_0"] == 1 and pm2["sides"]["buy"]["k_le_0"] == 0
    assert pm2["sides"]["sell"]["n"] == 3 and pm2["sides"]["sell"]["n_finite"] == 2   # c, e (f has no feed)
    assert pm2["sides"]["sell"]["share_k_le_0"] == pytest.approx(0.5)
    sm = chk["managers"]["BTC"]["sm"]
    assert sm["n_in_window"] == 6 and sm["nan_in_window"] == 1
    q = sm["sides"]["buy"]["k_over_index"]
    assert set(q) == {"p01", "p05", "p25", "p50", "p75", "p95", "p99", "min", "max", "mean"}
    assert chk["sm_long_exact"] == {"n": 2, "mismatch": 0}
    assert chk["rows"] == 6
    assert "HYPE" not in chk["managers"]
    json.dumps(chk)  # serialisable


def test_plausibility_reports_regimes_and_time_to_expiry():
    out = cap.capital_for(_fills(), _hist(), _timelines(), "BTC")
    chk = cap.plausibility(out)
    reg = chk["regimes"]["BTC"]["pm2"]
    assert sum(reg.values()) == 4 and reg == {"2025-06-12 22:20:01": 4}
    assert sum(chk["regimes"]["BTC"]["sm"].values()) == 6
    assert chk["sec_min"]["BTC"] == int(out["sec"].min())


def test_crosscheck_against_paper1_marks():
    out = cap.capital_for(_fills(), _hist(), _timelines(), "BTC")
    mk = pd.DataFrame({"trade_id": out["trade_id"], "iv_mark_t": out["sigma"].to_numpy(),
                       "mark_b_t": out["V_sm"].to_numpy() / out["maker_side"].to_numpy(),
                       "is_rfq": [True, False, False, False, True, False]})
    mk.loc[1, "iv_mark_t"] *= 1.01                       # one vol differs from Paper 1
    out.loc[out["trade_id"] == "a", "K_pm"] = -3.0       # a non-positive buy, fill price vs mark as a ratio
    x = cap.crosscheck_p1(out, mk)
    assert x["n"] == 6 and x["sigma_equal"] == 4        # f has no vol (nan on both sides counts as unequal)
    assert x["v_sm_minus_mark_bp"]["p50"] == pytest.approx(0.0, abs=1e-9)
    kp = x["k_le_0"]["pm"]
    assert kp["n"] == 1 and kp["n_rfq"] == 1
    assert kp["price_over_mark"]["buy"]["min"] == pytest.approx(900.0 / _mark_of(out, "a"))
    assert kp["price_over_mark"]["sell"]["min"] is None
    json.dumps(x)


def _mark_of(out, tid):
    row = out[out["trade_id"] == tid].iloc[0]
    return float(row["V_sm"] / row["maker_side"])
