"""Offline tests for derive_surface/p2api.py (task C5b): explorative API snapshot against the replica at the head block.

No network: the API and the chain are fakes. The replica runs on the committed parameter timelines in results/p2/params.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import pytest

from derive_surface import books, capital, margin_pm2, margin_sm, p2api, p2validate
from derive_surface.markouts import DELTA_EDGES, DELTA_LABELS, TENOR_EDGES_D, TENOR_LABELS
from derive_surface.p2feeds import FEEDS
from derive_surface.p2params import PM2_ADDR, SRM, Timeline
from derive_surface.p2types import YEAR, Book, ExpiryState, MarketState, OptionLeg
from derive_surface.pricing import delta_of

DAY = 86_400
NOW = 1_790_330_400          # 2026-09-25 10:00:00 UTC
E18 = 10 ** 18


# ---------------------------------------------------------------- buckets of Paper 1

def test_buckets_equal_the_paper1_cuts():
    rng = np.random.default_rng(1)
    d = np.concatenate([rng.uniform(0, 100, 500), np.asarray(DELTA_EDGES[:-1]), [99.9999, 100.0]])
    ref = pd.cut(d, DELTA_EDGES, labels=DELTA_LABELS, right=False).astype(str)
    assert [p2api.delta_bucket(x) for x in d] == list(ref)
    t = np.concatenate([rng.uniform(0, 400, 500), [0.0, 2.0, 7.0, 30.0, 90.0, 2.0000001, 90.0000001]])
    ref = pd.cut(t, TENOR_EDGES_D, labels=TENOR_LABELS, right=True, include_lowest=True).astype(str)
    assert [p2api.tenor_bucket(x) for x in t] == list(ref)
    assert p2api.delta_bucket(float("nan")) is None and p2api.tenor_bucket(-0.1) is None


def test_bucket_midpoints():
    assert [p2api.delta_mid(lab) for lab in DELTA_LABELS] == [5.0, 17.5, 32.5, 50.0, 67.5, 82.5, 95.0]
    assert [p2api.tenor_mid(lab, 300.0) for lab in TENOR_LABELS] == [1.0, 4.5, 18.5, 60.0, 195.0]


def test_choose_expiry_takes_the_listed_expiry_nearest_to_the_bucket_mid():
    tenors = {1: 0.9, 2: 1.2, 3: 3.0, 4: 6.9, 5: 20.0, 6: 29.0, 7: 150.0, 8: 300.0, 9: 0.01}
    assert p2api.choose_expiry(tenors, "<=2d") == 1           # |0.9-1| < |1.2-1|
    assert p2api.choose_expiry(tenors, "2-7d") == 3           # |3-4.5| = 1.5 < |6.9-4.5| = 2.4
    assert p2api.choose_expiry(tenors, "7-30d") == 5
    assert p2api.choose_expiry(tenors, "30-90d") is None      # nothing listed in (30, 90]
    assert p2api.choose_expiry(tenors, ">90d") == 7           # mid (90+300)/2 = 195: 150 beats 300
    assert p2api.choose_expiry({1: 0.5, 2: 1.5}, "<=2d") == 1  # tie: the earlier expiry
    assert p2api.choose_expiry({9: 0.01}, "<=2d") is None      # less than 30 min left: not eligible


# ---------------------------------------------------------------- instruments and tickers

def _ticker(mark, delta, fwd=100_500.0, iv=0.5, index=100_000.0, t=NOW * 1000):
    return {"t": t, "A": "1", "a": str(mark + 5), "B": "1", "b": str(mark - 5), "f": None, "I": str(index),
            "M": str(mark), "option_pricing": {"d": str(delta), "i": str(iv), "f": str(fwd), "m": str(mark),
                                               "df": "0.999", "t": "-1", "g": "0", "v": "1", "r": "1"},
            "stats": {"oi": "0"}, "minp": "1", "maxp": "10"}


def _instrument(ccy, expiry, strike, kind, active=True):
    name = books.instrument_name(ccy, expiry, strike, kind == "C")
    return {"instrument_type": "option", "instrument_name": name, "is_active": active,
            "option_details": {"index": f"{ccy}-USD", "expiry": expiry, "strike": str(strike), "option_type": kind,
                               "settlement_price": None}}


def test_ticker_fields_parse_the_slim_ticker():
    f = p2api.ticker_fields(_ticker(1234.5, -0.25, fwd=100_600, iv=0.61, index=100_100, t=1_790_330_400_123))
    assert f == {"mark": 1234.5, "index": 100_100.0, "delta": -0.25, "forward": 100_600.0, "iv": 0.61,
                 "ticker_ts": 1_790_330_400_123}
    g = p2api.ticker_fields({"t": 1, "M": "5", "I": None, "option_pricing": None})
    assert g["mark"] == 5.0 and math.isnan(g["delta"]) and math.isnan(g["index"])


def test_candidates_keep_active_listed_instruments_with_a_ticker():
    e = NOW + 20 * DAY
    insts = [_instrument("BTC", e, 100_000, "C"), _instrument("BTC", e, 110_000, "C", active=False),
             _instrument("BTC", e, 120_000, "C"), _instrument("HYPE", e, 38.75, "P")]
    ticks = {insts[0]["instrument_name"]: _ticker(5000, 0.52), insts[1]["instrument_name"]: _ticker(3000, 0.4),
             insts[3]["instrument_name"]: _ticker(2, -0.3)}
    c = p2api.candidates(insts, ticks)
    assert list(c["instrument"]) == [insts[0]["instrument_name"], insts[3]["instrument_name"]]
    assert list(c["strike"]) == [100_000.0, 38.75] and list(c["is_call"]) == [True, False]
    assert list(c["expiry"]) == [e, e] and list(c["delta"]) == [0.52, -0.3]


def _cands(rows):
    return pd.DataFrame(rows, columns=["instrument", "expiry", "strike", "is_call", "delta", "mark", "index",
                                       "forward", "iv", "ticker_ts"])


def test_choose_instrument_nearest_abs_delta_of_the_type_inside_the_bucket():
    e = NOW + 20 * DAY
    c = _cands([["c1", e, 90_000, True, 0.70, 1, 1, 1, 1, 1], ["c2", e, 100_000, True, 0.52, 1, 1, 1, 1, 1],
                ["c3", e, 110_000, True, 0.33, 1, 1, 1, 1, 1], ["c4", e, 120_000, True, 0.20, 1, 1, 1, 1, 1],
                ["p1", e, 90_000, False, -0.30, 1, 1, 1, 1, 1], ["p2", e, 95_000, False, -0.40, 1, 1, 1, 1, 1],
                ["c5", e, 130_000, True, 0.15, 1, 1, 1, 1, 1], ["c6", e, 125_000, True, 0.20, 1, 1, 1, 1, 1]])
    assert p2api.choose_instrument(c, "40-60", True)["instrument"] == "c2"
    assert p2api.choose_instrument(c, "25-40", True)["instrument"] == "c3"
    assert p2api.choose_instrument(c, "25-40", False)["instrument"] == "p1"   # |0.30-0.325| < |0.40-0.325|
    assert p2api.choose_instrument(c, "10-25", True)["instrument"] == "c4"    # tie 0.20: the smaller strike
    assert p2api.choose_instrument(c, "90-100", True) is None                 # nearest call has |d| 0.70
    assert p2api.choose_instrument(c, "40-60", False)["instrument"] == "p2"   # |d| 0.40 is inside [40, 60)
    assert p2api.choose_instrument(c, "60-75", False) is None
    assert p2api.choose_instrument(c.iloc[:0], "40-60", True) is None


def test_choose_instrument_left_edge_is_inside():
    e = NOW + 20 * DAY
    c = _cands([["p2", e, 95_000, False, -0.40, 1, 1, 1, 1, 1]])
    assert p2api.choose_instrument(c, "40-60", False)["instrument"] == "p2"
    assert p2api.choose_instrument(c, "25-40", False) is None


def test_cell_types_majority_in_the_pm2_window_with_call_fallback():
    pm2_btc_ms = capital.WINDOW_START["pm2"]["BTC"] * 1000
    rows = ([("BTC", 1, "P", "00-10", "<=2d", pm2_btc_ms + 1)] * 3 + [("BTC", 1, "C", "00-10", "<=2d", pm2_btc_ms)] * 2
            + [("BTC", 1, "C", "00-10", "<=2d", pm2_btc_ms - 1)] * 10          # before the window: ignored
            + [("BTC", -1, "C", "00-10", "<=2d", pm2_btc_ms)] + [("BTC", -1, "P", "00-10", "<=2d", pm2_btc_ms)])
    fr = pd.DataFrame(rows, columns=["currency", "maker_side", "option_type", "delta_bucket", "tenor_bucket", "ts"])
    t = p2api.cell_types(fr)
    assert t[("BTC", "buy", "00-10", "<=2d")] == ("P", 0.6, 5)
    assert t[("BTC", "sell", "00-10", "<=2d")] == ("C", 0.5, 2)                 # tie: call
    typ, share, n = p2api.cell_type(t, "BTC", "buy", "10-25", "<=2d")   # no fills in the cell: call
    assert typ == "C" and math.isnan(share) and n == 0
    assert p2api.cell_type(t, "BTC", "buy", "00-10", "<=2d") == ("P", 0.6, 5)


# ---------------------------------------------------------------- API side

def test_margin_request_is_one_contract_long_then_short_with_market_and_no_collateral():
    for mt in ("SM", "PM2"):
        body = p2api.margin_request(mt, "ETH", "ETH-20261030-4000-C")
        assert body == {"margin_type": mt, "market": "ETH",
                        "simulated_positions": [{"instrument_name": "ETH-20261030-4000-C", "amount": "1"}],
                        "simulated_collaterals": [],
                        "simulated_position_changes": [{"instrument_name": "ETH-20261030-4000-C", "amount": "-2"}]}


def test_api_capital_from_pre_and_post():
    res = {"subaccount_id": 0, "pre_initial_margin": "-120.5", "pre_maintenance_margin": "-80",
           "post_initial_margin": "-3000.25", "post_maintenance_margin": "-2000", "is_valid_trade": False}
    nb, ns = p2api.api_nets(res)
    assert (nb, ns) == (-120.5, -3000.25)
    kb, ks = p2api.capital_pair(500.0, nb, ns)
    assert kb == 500.0 + 120.5 and ks == -500.0 + 3000.25


class FakeResp:
    def __init__(self, status, payload):
        self.status_code = status
        self.text = payload if isinstance(payload, str) else json.dumps(payload)


class FakeSession:
    def __init__(self, replies):
        self.headers = {}
        self.replies = list(replies)
        self.posts = []

    def post(self, url, json=None, timeout=None):
        self.posts.append((url, json))
        return self.replies.pop(0)


class FakeClock:
    def __init__(self):
        self.t = 1000.0
        self.sleeps = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


def test_api_client_user_agent_log_retry_and_error(tmp_path):
    clock = FakeClock()
    thr = p2api.Throttle(rate=2.0, clock=clock.now, sleep=clock.sleep)
    sess = FakeSession([FakeResp(429, "slow down"), FakeResp(200, {"result": {"x": 1}, "id": "a"}),
                        FakeResp(200, {"error": {"code": 10015, "message": "bad market"}})])
    log = tmp_path / "C5b.jsonl"
    api = p2api.ApiClient(session=sess, throttle=thr, log_path=log, sleep=clock.sleep)
    assert sess.headers["User-Agent"] == p2api.USER_AGENT and "derive-option-surface" in p2api.USER_AGENT
    assert api.call("get_margin", margin_type="SM") == {"x": 1}
    with pytest.raises(p2api.ApiError):
        api.call("get_margin", margin_type="PM2")
    assert [u for u, _ in sess.posts] == ["https://api.lyra.finance/public/get_margin"] * 3
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert [r["http_status"] for r in rows] == [429, 200, 200]
    assert rows[0]["method"] == "public/get_margin" and rows[0]["params"] == {"margin_type": "SM"}
    assert "bad market" in rows[2]["raw"] and api.n_requests == 3


def test_throttle_is_shared_by_api_and_rpc(tmp_path):
    clock = FakeClock()
    thr = p2api.Throttle(rate=2.0, clock=clock.now, sleep=clock.sleep)
    starts = []

    class Client:
        def call(self, method, params):
            starts.append(clock.t)
            return "0x01"

    class Sess(FakeSession):
        def post(self, url, json=None, timeout=None):
            starts.append(clock.t)
            return FakeResp(200, {"result": 1})

    rpc = p2api.SharedRpc(thr, client=Client(), log_path=tmp_path / "log.jsonl")
    api = p2api.ApiClient(session=Sess([]), throttle=thr, log_path=tmp_path / "log.jsonl", sleep=clock.sleep)
    for _ in range(3):
        rpc.raw("eth_blockNumber", [])
        api.call("get_time")
    gaps = np.diff(starts)
    assert len(starts) == 6 and np.all(gaps >= 0.5 - 1e-12)
    assert rpc.n_requests == 3


# ---------------------------------------------------------------- chain side

def test_selectors_are_keccak_of_the_signatures():
    for name, sig in p2api.SIGNATURES.items():
        assert p2api.SEL[name] == p2validate.keccak256(sig.encode())[:4].hex()
    assert p2api.SEL["getMargin"] == "623bb445" and p2api.SEL["getSpot"] == "2b37269c"
    assert p2api.SEL["getBlockNumber"] == "42cbb15c" and p2api.SEL["getCurrentBlockTimestamp"] == "0f28c97d"


def _words(data: bytes):
    return [int.from_bytes(data[i:i + 32], "big") for i in range(4, len(data), 32)]


def test_chain_calls_read_the_feeds_and_both_managers_for_two_synthetic_accounts():
    e, k = NOW + 20 * DAY, 38.75
    calls, ov = p2api.chain_calls("HYPE", e, k, False)
    f = FEEDS["HYPE"]
    targets = [t.lower() for t, _ in calls]
    assert targets == [books.MULTICALL3.lower(), books.MULTICALL3.lower(), f["spot"], f["forward"], f["vol"],
                       f["rate_pm2"], p2validate.STABLE_FEED, SRM, SRM, PM2_ADDR["HYPE"]["manager"],
                       PM2_ADDR["HYPE"]["manager"]]
    sel = [cd[:4].hex() for _, cd in calls]
    assert sel == [p2api.SEL[n] for n in ("getBlockNumber", "getCurrentBlockTimestamp", "getSpot",
                                          "getForwardPricePortions", "getVol", "getInterestRate", "getSpot",
                                          "getMargin", "getMargin", "getMargin", "getMargin")]
    assert _words(calls[3][1]) == [e] and _words(calls[4][1]) == [p2validate.strike_wei(k), e]
    assert _words(calls[7][1]) == [p2api.ACC_BUY, 1] and _words(calls[8][1]) == [p2api.ACC_SELL, 1]
    assert _words(calls[9][1]) == [p2api.ACC_BUY, 1] and _words(calls[10][1]) == [p2api.ACC_SELL, 1]
    sub = books.encode_option_subid(e, k, False)
    exp = p2validate.state_override({p2api.ACC_BUY: [(p2validate.OPTION_ASSET["HYPE"], sub, E18)],
                                     p2api.ACC_SELL: [(p2validate.OPTION_ASSET["HYPE"], sub, -E18)]})
    assert ov == exp
    assert p2api.ACC_BUY > 2 ** 64 and p2api.ACC_SELL > 2 ** 64 and p2api.ACC_BUY != p2api.ACC_SELL


def _w(x: int) -> bytes:
    return (int(x) % (1 << 256)).to_bytes(32, "big")


def encode_results(results):
    """ABI encoding of Multicall3.aggregate3's return value ``(bool, bytes)[]``."""
    elems = []
    for ok, data in results:
        pad = data + b"\0" * ((-len(data)) % 32)
        elems.append(_w(1 if ok else 0) + _w(0x40) + _w(len(data)) + pad)
    offs, pos = [], 32 * len(elems)
    for el in elems:
        offs.append(pos)
        pos += len(el)
    return _w(0x20) + _w(len(elems)) + b"".join(_w(o) for o in offs) + b"".join(elems)


def chain_results(block=45_800_000, block_ts=NOW + 3, spot=100_000.0, fixed=0.0, var=100_500.0, fconf=1.0,
                  vol=0.5, vconf=1.0, rate=0.037, rconf=1.0, stable=1.0, margins=(-10.0, -9000.0, 50.0, -7000.0),
                  fail=()):
    wad = p2validate.wei       # exact 1e18 integer of the decimal value
    rows = [(True, _w(block)), (True, _w(block_ts)), (True, _w(wad(spot)) + _w(E18)),
            (True, _w(wad(fixed)) + _w(wad(var)) + _w(wad(fconf))), (True, _w(wad(vol)) + _w(wad(vconf))),
            (True, _w(wad(rate)) + _w(wad(rconf))), (True, _w(wad(stable)) + _w(E18))]
    rows += [(True, _w(wad(m))) for m in margins]
    return [(False, b"") if i in fail else r for i, r in enumerate(rows)]


def test_decode_chain_values_and_failures():
    res = chain_results(fixed=10.0, var=100_490.0, rate=-0.001, margins=(-1.5, -2.5, 3.5, -4.5))
    d = p2api.decode_chain(p2validate.books.decode_aggregate3(encode_results(res)))
    assert d["block"] == 45_800_000 and d["block_ts"] == NOW + 3
    assert d["spot"] == 100_000.0 and d["forward"] == 100_500.0 and d["fwd_fixed"] == 10.0
    assert d["sigma"] == 0.5 and d["rate"] == pytest.approx(-0.001) and d["stable"] == 1.0
    assert (d["net_sm_buy"], d["net_sm_sell"], d["net_pm2_buy"], d["net_pm2_sell"]) == (-1.5, -2.5, 3.5, -4.5)
    assert d["failed"] == []
    d = p2api.decode_chain(chain_results(fail=(4, 9)))
    assert d["sigma"] is None and d["net_pm2_buy"] is None and d["failed"] == ["getVol", "getMargin:pm2_buy"]


def _params(ccy):
    return {m: Timeline(ccy, m).entries[-1]["params"] for m in ("sm", "pm2")}


@pytest.mark.parametrize("ccy,strike,is_call", [("BTC", 110_000.0, True), ("BTC", 90_000.0, False),
                                                 ("ETH", 4_000.0, True), ("HYPE", 38.75, False)])
def test_replica_capital_equals_the_book_engines(ccy, strike, is_call):
    scale = {"BTC": 1.0, "ETH": 0.04, "HYPE": 0.0004}[ccy]
    e = NOW + 40 * DAY
    ch = dict(block=45_800_000, block_ts=NOW, spot=100_000.0 * scale, spot_conf=1.0, forward=100_400.0 * scale,
              fwd_fixed=0.0, fwd_conf=1.0, sigma=0.55, vol_conf=1.0, rate=0.037, rate_conf=1.0, stable=1.0)
    params = _params(ccy)
    mark = 2500.0 * scale
    k = p2api.replica_capital(ch, e, strike, is_call, mark, params)
    st = MarketState(currency=ccy, ts=NOW, spot=ch["spot"], stable=1.0, spot_conf=1.0,
                     expiries={e: ExpiryState(e, ch["forward"], None, rate=0.037, vol_conf=1.0, fwd_conf=1.0)})
    vols = {(e, strike): 0.55}
    for mgr, eng in (("sm", margin_sm), ("pm2", margin_pm2)):
        for i, q in enumerate((1.0, -1.0)):
            net, _ = eng.net_margin(Book(options=[OptionLeg(e, strike, is_call, q)]), st, params[mgr], True,
                                    vols=vols)
            assert k[mgr][i] == pytest.approx(mark * q - net, rel=1e-9, abs=1e-9)
    assert k["sm"][0] == pytest.approx(mark, rel=1e-12)          # SM: a long option binds exactly its premium


def test_replica_capital_is_nan_when_a_feed_reverted():
    ch = dict(block=1, block_ts=NOW, spot=100_000.0, spot_conf=1.0, forward=100_400.0, fwd_fixed=0.0, fwd_conf=1.0,
              sigma=None, vol_conf=None, rate=0.037, rate_conf=1.0, stable=1.0)
    k = p2api.replica_capital(ch, NOW + 40 * DAY, 110_000.0, True, 100.0, _params("BTC"))
    assert all(math.isnan(x) for x in k["sm"] + k["pm2"])


def test_api_semantics_replica_uses_ticker_feeds_and_two_percent():
    e = NOW + 200 * DAY
    params = _params("BTC")
    tick = {"index": 100_000.0, "forward": 101_000.0, "iv": 0.6}
    k = p2api.replica_api_semantics(tick, NOW, e, 120_000.0, True, 4000.0, params)
    arrays = {"spot": np.array([100_000.0] * 2), "forward": np.array([101_000.0] * 2), "sigma": np.array([0.6] * 2),
              "tau": np.array([(e - NOW) / YEAR] * 2), "rate": np.array([0.02] * 2),
              "strike": np.array([120_000.0] * 2), "is_call": np.array([True, True]),
              "amount": np.array([1.0, -1.0]), "vol_conf": np.ones(2), "fwd_conf": np.ones(2), "spot_conf": np.ones(2),
              "rate_conf": np.ones(2), "fwd_fixed": np.zeros(2), "rate_pm": np.zeros(2), "stable": np.ones(2)}
    for mgr in ("sm", "pm2"):
        ref, _ = capital.capital_single(mgr, arrays, params[mgr], np.array([4000.0, 4000.0]))
        assert k[mgr] == pytest.approx(tuple(ref), rel=1e-12)
    assert p2api.API_RATE == 0.02


def test_rel_diff():
    assert p2api.rel_diff(110.0, 100.0) == pytest.approx(0.1)
    assert p2api.rel_diff(-90.0, -100.0) == pytest.approx(-0.1)
    assert math.isnan(p2api.rel_diff(1.0, 0.0)) and math.isnan(p2api.rel_diff(float("nan"), 1.0))


# ---------------------------------------------------------------- end to end with fakes

FWD = 100_500.0
EXPIRY_DAYS = [0.9, 5.0, 20.0, 150.0, 300.0]          # nothing in (30, 90]: that tenor bucket stays empty
STRIKES = list(range(40_000, 200_001, 2_500))


def _expiry(days):
    return int(NOW + days * DAY)


class FakeApi:
    def __init__(self, ccy="BTC"):
        self.ccy = ccy
        self.calls = []
        self.n_requests = 0
        self.tickers = {}
        self.insts = []
        for days in EXPIRY_DAYS:
            e = _expiry(days)
            for k in STRIKES:
                for kind in ("C", "P"):
                    inst = _instrument(ccy, e, k, kind)
                    self.insts.append(inst)
                    d = float(delta_of(FWD, k, days / 365.0, 0.5, 1 if kind == "C" else -1))
                    mark = max(1.0, abs(d) * 3000.0)
                    self.tickers.setdefault(e, {})[inst["instrument_name"]] = _ticker(round(mark, 1), round(d, 5))

    def margin(self, body):
        name = body["simulated_positions"][0]["instrument_name"]
        k = books.parse_instrument_name(name)[2]
        base = -k / 100.0 if body["margin_type"] == "SM" else -k / 200.0
        return {"pre_initial_margin": str(base), "post_initial_margin": str(10 * base)}

    def call(self, method, **params):
        self.calls.append((method, params))
        self.n_requests += 1
        if method == "get_instruments":
            return self.insts
        if method == "get_tickers":
            e = [x for x in self.tickers if books.instrument_name("BTC", x, 1, True).split("-")[1]
                 == params["expiry_date"]][0]
            return {"tickers": self.tickers[e]}
        if method == "get_margin":
            return self.margin(params)
        raise AssertionError(method)


class FakeRpc:
    def __init__(self):
        self.calls = []
        self.n_requests = 0

    def raw(self, method, params):
        self.calls.append((method, params))
        self.n_requests += 1
        assert method == "eth_call" and params[1] == "latest"
        return "0x" + encode_results(chain_results()).hex()


def _types():
    t = {}
    for side in ("buy", "sell"):
        for d in DELTA_LABELS:
            for ten in TENOR_LABELS:
                t[("BTC", side, d, ten)] = ("P" if (side == "sell" and d in ("00-10", "10-25")) else "C", 0.7, 300)
    return t


def test_snapshot_end_to_end_with_fakes(tmp_path):
    api, rpc = FakeApi(), FakeRpc()
    params = _params("BTC")
    rows = p2api.snapshot_ccy("BTC", api, rpc, _types(), lambda ccy, mgr, ts: (params[mgr], "2026-09-04 22:51:37"),
                              clock=lambda: float(NOW))
    df = p2api.to_frame(rows)
    assert len(df) == 2 * 7 * 5
    assert set(df.loc[df["tenor_bucket"] == "30-90d", "status"]) == {"no_expiry"}
    ok = df[df["status"] == "ok"]
    assert len(ok) > 0 and set(df["status"]) <= {"ok", "no_expiry", "no_strike"}
    # the instrument sits in its cells: type, |delta| and tenor
    for r in ok.itertuples():
        assert p2api.delta_bucket(abs(r.delta) * 100) == r.delta_bucket
        assert p2api.tenor_bucket(r.tenor_days) == r.tenor_bucket
        assert r.option_type == ("P" if (r.side == "sell" and r.delta_bucket in ("00-10", "10-25")) else "C")
        assert r.instrument.endswith("-" + r.option_type)
    # K_api = p q - net, with net(+1) = pre and net(-1) = post of one request
    for r in ok.itertuples():
        q = 1.0 if r.side == "buy" else -1.0
        base_sm, base_pm2 = -r.strike / 100.0, -r.strike / 200.0
        net_sm = base_sm if q > 0 else 10 * base_sm
        net_pm2 = base_pm2 if q > 0 else 10 * base_pm2
        assert r.K_api_sm == pytest.approx(r.mark * q - net_sm)
        assert r.K_api_pm2 == pytest.approx(r.mark * q - net_pm2)
        m = (-10.0, -9000.0, 50.0, -7000.0)
        assert r.K_oracle_sm == pytest.approx(r.mark * q - (m[0] if q > 0 else m[1]))
        assert r.K_oracle_pm2 == pytest.approx(r.mark * q - (m[2] if q > 0 else m[3]))
        assert r.rel_diff_sm == pytest.approx(r.K_api_sm / r.K_chain_sm - 1)
        assert r.rel_diff_pm2 == pytest.approx(r.K_api_pm2 / r.K_chain_pm2 - 1)
        assert r.block == 45_800_000
    # the chain replica of one row, recomputed
    r = ok.iloc[0]
    e = _expiry(float([d for d in EXPIRY_DAYS if p2api.tenor_bucket(d) == r["tenor_bucket"]][0]))
    ch = p2api.decode_chain(books.decode_aggregate3(encode_results(chain_results())))
    k = p2api.replica_capital(ch, e, r["strike"], r["option_type"] == "C", r["mark"], params)
    i = 0 if r["side"] == "buy" else 1
    assert r["K_chain_sm"] == pytest.approx(k["sm"][i]) and r["K_chain_pm2"] == pytest.approx(k["pm2"][i])
    # one get_margin per instrument and manager (both sides in one request), one eth_call per instrument,
    # one get_tickers per chosen expiry, the instrument list once
    n_inst = ok["instrument"].nunique()
    methods = [m for m, _ in api.calls]
    assert methods.count("get_margin") == 2 * n_inst and len(rpc.calls) == n_inst
    assert methods.count("get_tickers") == 4 and methods.count("get_instruments") == 1
    assert all(p.get("market") == "BTC" for m, p in api.calls if m == "get_margin")
    assert {p["margin_type"] for m, p in api.calls if m == "get_margin"} == {"SM", "PM2"}
    # the override of every eth_call holds the two synthetic accounts in SubAccounts
    for _, params_ in rpc.calls:
        assert list(params_[2]) == [books.SUBACCOUNTS.lower()]
    assert list(df.columns[:len(p2api.KEY_COLUMNS)]) == p2api.KEY_COLUMNS


def test_api_error_is_recorded_not_raised():
    class ErrApi(FakeApi):
        def margin(self, body):
            if body["margin_type"] == "PM2":
                raise p2api.ApiError("get_margin", {"code": 10015, "message": "x"})
            return super().margin(body)

    params = _params("BTC")
    rows = p2api.snapshot_ccy("BTC", ErrApi(), FakeRpc(), _types(), lambda c, m, ts: (params[m], "x"),
                              clock=lambda: float(NOW))
    df = p2api.to_frame(rows)
    got = df[df["status"] == "api_error"]
    assert len(got) > 0 and got["K_api_pm2"].isna().all() and got["K_api_sm"].notna().all()
    assert got["K_chain_pm2"].notna().all()


def test_run_writes_csv_meta_and_doc(tmp_path):
    params = _params("BTC")
    out = p2api.run(ccys=("BTC",), csv_path=tmp_path / "api_snapshot.csv", meta_path=tmp_path / "meta.json",
                    doc_path=tmp_path / "C5b.md", api=FakeApi(), rpc=FakeRpc(), types=_types(),
                    params_at=lambda c, m, ts: (params[m], "2026-09-04 22:51:37"), clock=lambda: float(NOW))
    df = pd.read_csv(tmp_path / "api_snapshot.csv")
    for col in ("ccy", "side", "delta_bucket", "tenor_bucket", "instrument", "K_api_sm", "K_chain_sm", "K_api_pm2",
                "K_chain_pm2", "rel_diff_sm", "rel_diff_pm2", "ts"):
        assert col in df.columns
    assert len(df) == len(out) == 70
    assert df["ts"].dropna().astype("int64").min() > 10 ** 12          # milliseconds
    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["requests"]["api"] > 0 and meta["requests"]["rpc"] > 0 and meta["rate_per_s"] == 2.0
    doc = (tmp_path / "C5b.md").read_text()
    assert doc.startswith("## C5b") and "Exploratory" in doc and "API semantics with 2 %" in doc
    assert "K_api" in doc and "| BTC |" in doc
    assert "Largest deviations" in doc and " 1 cells" not in doc
    # every markdown table keeps its column count (a "|" inside a cell must be escaped)
    import re
    tables, cur = [], []
    for line in doc.splitlines() + [""]:
        if line.startswith("|"):
            cur.append(len(re.findall(r"(?<!\\)\|", line)))
        elif cur:
            tables.append(cur)
            cur = []
    assert len(tables) >= 4 and all(len(set(t)) == 1 for t in tables), tables
    # report re-renders the same document from the files alone
    (tmp_path / "C5b.md").unlink()
    assert p2api.main(["report", "--csv", str(tmp_path / "api_snapshot.csv"), "--meta", str(tmp_path / "meta.json"),
                       "--doc", str(tmp_path / "C5b.md")]) == 0
    assert (tmp_path / "C5b.md").read_text() == doc


def test_number_format():
    assert p2api.fmt_num(1234567.891, 1) == "1,234,567.9"
    assert p2api.fmt_pct(0.001234, 2) == "+0.12 %" and p2api.fmt_pct(-0.05, 1) == "−5.0 %"
    assert p2api.fmt_num(float("nan"), 2) == "n/a"
    assert p2api.fmt_sci(1.8e-15) == "1.8·10⁻¹⁵"


def test_cli_help_lists_run_and_report(capsys):
    with pytest.raises(SystemExit) as exc:
        p2api.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "run" in out and "report" in out


def test_throttle_oversleep_does_not_shorten_the_next_gap():
    clock = FakeClock()

    def late_sleep(s):             # the OS wakes us 10 ms late
        clock.sleep(s + 0.01)

    thr = p2api.Throttle(rate=2.0, clock=clock.now, sleep=late_sleep)
    starts = []
    for _ in range(6):
        thr.wait()
        starts.append(clock.t)
    gaps = np.diff(starts)
    assert np.all(gaps >= 0.5) and all(starts[i + 2] - starts[i] > 1.0 for i in range(4))


def test_shared_rpc_logs_the_start_of_the_request(tmp_path, monkeypatch):
    stamps = iter(["start", "end", "later"])
    monkeypatch.setattr(p2api, "_utc_now", lambda: next(stamps))

    class Client:
        def call(self, method, params):
            p2api._utc_now()           # time passes while the node answers
            return "0x01"

    rpc = p2api.SharedRpc(p2api.Throttle(rate=1e6), client=Client(), log_path=tmp_path / "log.jsonl")
    rpc.raw("eth_blockNumber", [])
    row = json.loads((tmp_path / "log.jsonl").read_text())
    assert row["ts"] == "start" and row["host"] == p2api.RPC_URL


def test_max_starts_in_one_second_from_the_log(tmp_path):
    log = tmp_path / "log.jsonl"
    ts = ["2026-09-25T00:00:00.000+00:00", "2026-09-25T00:00:00.600+00:00", "2026-09-25T00:00:01.200+00:00",
          "2026-09-25T00:00:01.800+00:00", "2026-09-25T00:00:09.000+00:00"]
    log.write_text("".join(json.dumps({"ts": t, "method": "x"}) + "\n" for t in ts))
    assert p2api.max_starts_per_second(log, "2026-09-25T00:00:00+00:00", "2026-09-25T00:00:05+00:00") == 2
    assert p2api.max_starts_per_second(log, "2026-09-25T00:00:00+00:00", "2026-09-25T00:00:10+00:00") == 2
    log.write_text(log.read_text() + json.dumps({"ts": "2026-09-25T00:00:00.900+00:00"}) + "\n")
    assert p2api.max_starts_per_second(log, "2026-09-25T00:00:00+00:00", "2026-09-25T00:00:05+00:00") == 3
    assert p2api.max_starts_per_second(tmp_path / "missing.jsonl", "2026-09-25T00:00:00+00:00",
                                       "2026-09-25T00:00:05+00:00") is None
