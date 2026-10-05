"""Tests for the offline StandardManager replica (derive_surface.margin_sm).

Reference cases come from v2-core (commit 96796a6, read from data/p2/v2-core) and from
historical eth_calls on Chain 957 (tests/fixtures/p2/sm_chain_cases.json, see gen_a4_chain_fixtures.py).
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
import pytest

from derive_surface import margin_sm
from derive_surface.p2types import YEAR, Book, ExpiryState, MarketState, OptionLeg, capital_from_net

FIX = Path(__file__).parent / "fixtures" / "p2"
# v2-core reference cases (BUSL-1.1) are read in place from the local clone and not copied into the repository;
# without data/p2/v2-core these tests are skipped (the chain fixtures under tests/fixtures/p2 always run).
V2CORE_TESTS = (Path(__file__).resolve().parents[1] / "data" / "p2" / "v2-core" / "test" / "risk-managers"
                / "unit-tests")


def _v2core(rel: str) -> dict:
    path = V2CORE_TESTS / rel
    if not path.exists():
        pytest.skip(f"v2-core reference cases missing: {path}")
    return json.loads(path.read_text())


# Chain fixtures of real accounts (whole balances at a block) identify the account, so they live in
# data/p2/fixtures_private (not tracked, Addendum 1.4, audit A01); without them these tests are skipped.
PRIVATE = Path(__file__).resolve().parents[1] / "data" / "p2" / "fixtures_private"


def _private(name: str) -> dict:
    path = PRIVATE / name
    if not path.exists():
        pytest.skip(f"private chain fixture missing (account-identifying, not in the repository): {path}")
    return json.loads(path.read_text())
E18 = 10 ** 18

# Config.getSRMParams() in v2-core test/config-test.sol plus the overrides of the two test contracts
_OPTION_PARAMS = dict(maxSpotReq=0.15, minSpotReq=0.1, mmCallSpotReq=0.075, mmPutSpotReq=0.075, MMPutMtMReq=0.075,
                      unpairedIMScale=1.2, unpairedMMScale=1.1, mmOffsetScale=1.05)


def _test_params(base_factor: float) -> dict:
    return {
        "OptionMarginParams": dict(_OPTION_PARAMS),
        "PerpMarginRequirements": {"mmPerpReq": 0.05, "imPerpReq": 0.065},
        "BaseMarginParams": {"marginFactor": base_factor, "IMScale": 1.0},
        "OracleContingencyParams": {"perpThreshold": 0.4, "optionThreshold": 0.4, "baseThreshold": 0.4,
                                    "OCFactor": 0.4},
        "DepegParams": {"threshold": 0.98, "depegFactor": 1.2},
    }


class _MockFeed:
    """test/shared/mocks/MockFeeds.sol: vol per (expiry, strike), vol confidence per expiry (last write wins)."""

    def __init__(self, spot: float, spot_conf: float = 1.0):
        self.spot, self.spot_conf = spot, spot_conf
        self.fwd, self.fwd_conf, self.vols, self.vol_conf = {}, {}, {}, {}
        self.perp, self.perp_conf = spot, 1.0

    def set_vol(self, expiry, strike, vol, conf):
        self.vols[(expiry, strike)] = vol
        self.vol_conf[expiry] = conf

    def set_forward(self, expiry, price, conf):
        self.fwd[expiry] = price
        self.fwd_conf[expiry] = conf

    def state(self, ccy: str, ts: int, stable: float) -> MarketState:
        exps = {e: ExpiryState(expiry=e, forward=f, svi=None, vol_conf=self.vol_conf.get(e, 0.0),
                               fwd_conf=self.fwd_conf[e])
                for e, f in self.fwd.items()}
        return MarketState(currency=ccy, ts=ts, spot=self.spot, expiries=exps, perp=self.perp, stable=stable,
                           spot_conf=self.spot_conf, perp_conf=self.perp_conf)


def _market_sum(books, feeds, params, ts, stable, bases, is_initial):
    net = mtm = 0.0
    for ccy, book in books.items():
        n, m = margin_sm.net_margin(book, feeds[ccy].state(ccy, ts, stable), params, is_initial,
                                    vols=feeds[ccy].vols, base=bases.get(ccy, 0.0))
        net += n
        mtm += m
    return net, mtm


# ---------------------------------------------------------------- v2-core test-cases.json (28 cases, 0.1 %)

def _load_cases_json(case: dict):
    s = case["Scenario"]
    ts = 1  # forge default block.timestamp; expiries are relative seconds
    confs = s["SpotPerpConfidences"]
    feeds = {"ETH": _MockFeed(s["ETHSpotPrice"] / E18, confs[0][0] / E18),
             "BTC": _MockFeed(s["BTCSpotPrice"] / E18, confs[1][0] / E18)}
    feeds["ETH"].perp, feeds["ETH"].perp_conf = s["PerpPrice"][0] / E18, confs[0][1] / E18
    feeds["BTC"].perp, feeds["BTC"].perp_conf = s["PerpPrice"][1] / E18, confs[1][1] / E18
    und = s["OptionUnderlying"]
    for i, rel in enumerate(s["FeedExpiries"]):
        ccy = "ETH" if und[i] == "ETH" else "BTC"
        price = s["Forwards"][i] if rel >= 3600 else s[f"SettlementPrice{ccy}"]
        feeds[ccy].set_forward(ts + rel, price / E18, s["ForwardConfidences"][i] / E18)
    books = {"ETH": Book(), "BTC": Book()}
    for i, ccy in enumerate(und):
        expiry = ts + s["OptionExpiries"][i]
        strike = (int(s["OptionStrikes"][i]) // 10 ** 10) * 10 ** 10 / E18
        feeds[ccy].set_vol(expiry, strike, s["OptionVols"][i] / E18, s["OptionVolConfidences"][i] / E18)
        books[ccy].options.append(OptionLeg(expiry, strike, s["OptionIsCall"][i] == 1, s["OptionAmounts"][i] / E18))
    extra_cash = s["Cash"] / E18
    for ccy in ("ETH", "BTC"):
        q = s[f"Perps_{ccy}"] / E18
        books[ccy].perp = q
        if q != 0:
            books[ccy].perp_entry = s[f"LastEntry{ccy}"] / E18
            extra_cash += -q * (s[f"{ccy}GlobalFundingIndex"] - s[f"Account{ccy}FundingIndex"]) / E18
    bases = {"ETH": s["wETH"] / E18, "BTC": s["wBTC"] / E18}
    return books, feeds, bases, s["USDCValue"] / E18, extra_cash, ts


def test_sm_v2core_test_cases_im_mm_mtm():
    cases = _v2core("StandardManager/test-cases.json")
    params = _test_params(0.1)
    assert len(cases) == 28
    worst = 0.0
    for name, case in cases.items():
        books, feeds, bases, stable, cash, ts = _load_cases_json(case)
        r = case["Result"]
        for is_initial, key in ((True, "realIM"), (False, "realMM")):
            net, mtm = _market_sum(books, feeds, params, ts, stable, bases, is_initial)
            net += cash
            exp = r[key] / E18
            rel = abs(net - exp) / max(abs(exp), 1.0)
            worst = max(worst, rel)
            # the Solidity test allows 0.1 %; the float replica meets the Python reference to ~1e-14
            assert rel < 1e-10, (name, key, net, exp)
            if is_initial:
                assert abs(mtm + cash - r["PortfolioMtM"] / E18) / max(abs(r["PortfolioMtM"] / E18), 1.0) < 1e-10, name
    assert worst < 1e-10


# ---------------------------------------------------------------- v2-core test-cases-portfolio.json (42 cases, whole USD)

_EXPIRY_OFFSETS = {"20230104": 3, "20230111": 10, "20230118": 17, "20230227": 57, "20230804": 215, "20230811": 222,
                   "20230818": 229, "20230825": 238}
_FWD_ADD = {"eth": [0.91345, 2.83305, 4.7545, 15.7696, 59.87416, 61.85933, 63.8284, 66.3744],
            "btc": [12.7883, 39.66276, 66.56301, 220.77451, 838.23835, 865.90472, 893.59763, 929.24184]}


def _expiry(date: str, ts: int = 1) -> int:
    return ts + _EXPIRY_OFFSETS[date] * 86400 + 8 * 3600


def _default_feeds():
    feeds = {"ETH": _MockFeed(2000.0), "BTC": _MockFeed(28000.0)}
    for ccy, base in (("ETH", 2000.0), ("BTC", 28000.0)):
        for date, add in zip(_EXPIRY_OFFSETS, _FWD_ADD[ccy.lower()]):
            feeds[ccy].set_forward(_expiry(date), base + add, 1.0)
    feeds["ETH"].perp = 2001.0
    feeds["BTC"].perp = 28020.0
    return feeds


def _env(name, feeds):
    """Per-case feed overrides of TestStandardManager_Portfolio_Cases.t.sol; returns the stable price."""
    e = _expiry("20230118")
    stable = 1.0
    eth = feeds["ETH"]
    if name in ("test_USDC_depeg", "test_long_perp_and_USDC_depeg"):
        stable = 0.1
    elif name == "test_short_call_low_vol_conf":
        eth.set_vol(e, 2000.0, 0.5, 0.1)
    elif name == "test_short_call_low_vol_and_fwd_confidence":
        eth.set_vol(e, 2000.0, 0.5, 0.5)
        eth.set_forward(e, 2004.75, 0.4 - 1e-12)  # 0.4e18 - 1 wei; 1e-18 vanishes in float
    elif name in ("test_short_call_low_spot_vol_fwd_confidence", "test_long_call_low_spot_vol_fwd_confidence"):
        eth.set_vol(e, 2000.0, 0.5, 0.5)
        eth.set_forward(e, 2004.75, 0.4)
        eth.spot_conf = 0.2
    elif name == "test_short_options_two_expiries_low_conf_one_expiry":
        eth.set_vol(e, 2000.0, 0.5, 0.3)
        eth.set_forward(e, 2004.75, 0.4)
        eth.spot_conf = 0.9
    elif name == "test_long_eth_perp_low_perp_confidence":
        eth.perp, eth.perp_conf = 2001.0, 0.1
    elif name == "test_base_asset_low_spot_confidence":
        eth.spot_conf = 0.1
    elif name == "test_general_portfolio":
        stable = 0.97
        eth.set_vol(e, 2000.0, 0.5, 0.5)
        eth.set_forward(e, 2004.75, 0.4 - 1e-12)  # 0.4e18 - 1 wei; 1e-18 vanishes in float
        eth.spot_conf = 0.2
    return stable


def _load_portfolio_case(name: str, case: dict):
    feeds = _default_feeds()
    stable = _env(name, feeds)
    books = {"ETH": Book(), "BTC": Book()}
    for o in case["options"]:
        ccy = o["underlying"].upper()
        e, k = _expiry(o["expiry"]), float(o["strike"])
        if feeds[ccy].vols.get((e, k), 0.0) == 0.0:
            feeds[ccy].set_vol(e, k, 0.5, 1.0)
        books[ccy].options.append(OptionLeg(e, k, o["type"] == "call", o["amount"] / 1e8))
    for p in case["perps"]:
        ccy = p["underlying"].upper()
        books[ccy].perp = p["amount"] / 1e8
        books[ccy].perp_entry = p["entryPrice"] / 1e8
    bases = {}
    for b in case["bases"]:
        bases[b["underlying"].upper()] = bases.get(b["underlying"].upper(), 0.0) + b["amount"] / 1e8
    res = case.get("results", case.get("result"))
    return books, feeds, bases, stable, case["cash"] / 1e8, int(res["im"]), int(res["mm"])


def _sol_trunc(x: float) -> int:
    """``int / 1e18`` in Solidity truncates toward zero; round first so 879.9999999999999 counts as 880."""
    return math.trunc(round(x, 9))


def test_sm_v2core_portfolio_cases_integer_usd():
    cases = _v2core("StandardManager/test-cases-portfolio.json")
    params = _test_params(0.8)
    assert len(cases) == 42
    for name, case in cases.items():
        books, feeds, bases, stable, cash, im_exp, mm_exp = _load_portfolio_case(name, case)
        im, _ = _market_sum(books, feeds, params, 1, stable, bases, True)
        mm, _ = _market_sum(books, feeds, params, 1, stable, bases, False)
        assert _sol_trunc(im + cash) == im_exp, (name, im + cash, im_exp)
        assert _sol_trunc(mm + cash) == mm_exp, (name, mm + cash, mm_exp)


# ---------------------------------------------------------------- hand-computed cases

def _one_leg_state(spot=100.0, forward=101.0, ts=0, expiry=30 * 86400, **kw):
    e = ExpiryState(expiry=expiry, forward=forward, svi=None, vol_conf=kw.pop("vol_conf", 1.0),
                    fwd_conf=kw.pop("fwd_conf", 1.0))
    return MarketState(currency="BTC", ts=ts, spot=spot, expiries={expiry: e}, **kw)


def test_long_option_has_no_margin_and_capital_equals_premium():
    params = _test_params(0.8)
    st = _one_leg_state()
    book = Book(options=[OptionLeg(st.ts + 30 * 86400, 100.0, True, 1.0)])
    net, mtm = margin_sm.net_margin(book, st, params, vols={(30 * 86400, 100.0): 0.5})
    assert net == pytest.approx(0.0, abs=1e-12)
    assert mtm > 0
    # K_p = p q - net: a long option needs exactly its premium, a short one premium plus margin
    assert capital_from_net(7.0 * 1.0, net) == pytest.approx(7.0, abs=1e-12)
    short = Book(options=[OptionLeg(st.ts + 30 * 86400, 100.0, True, -1.0)])
    net_s, mtm_s = margin_sm.net_margin(short, st, params, vols={(30 * 86400, 100.0): 0.5})
    assert net_s == pytest.approx(mtm_s - 0.15 * 100.0, rel=1e-12)  # ATM: maxSpotReq * S
    assert capital_from_net(-7.0, net_s) == pytest.approx(-7.0 - mtm_s + 15.0, rel=1e-12)


def test_short_call_isolated_formula():
    params = _test_params(0.8)
    st = _one_leg_state()
    e = 30 * 86400
    sigma = 0.5
    book = Book(options=[OptionLeg(e, 110.0, True, -1.0)])
    net, mtm = margin_sm.net_margin(book, st, params, vols={(e, 110.0): sigma})
    call, _ = margin_sm.b76_prices(101.0, 110.0, sigma, float(e))
    assert mtm == pytest.approx(-call, rel=1e-12)
    a = max(0.1, 0.15 - 0.10)  # otm ratio (110 - 100) / 100
    assert net == pytest.approx(-a * 100.0 + mtm, rel=1e-12)
    # MM: mmCallSpotReq * S
    net_mm, _ = margin_sm.net_margin(book, st, params, is_initial=False, vols={(e, 110.0): sigma})
    assert net_mm == pytest.approx(-0.075 * 100.0 + mtm, rel=1e-12)


def test_call_spread_uses_max_loss():
    params = _test_params(0.8)
    st = _one_leg_state()
    e = 30 * 86400
    vols = {(e, 100.0): 0.5, (e, 105.0): 0.5}
    book = Book(options=[OptionLeg(e, 100.0, True, -1.0), OptionLeg(e, 105.0, True, 1.0)])
    net, mtm = margin_sm.net_margin(book, st, params, vols=vols)
    # max loss of a 100/105 bear call spread is 5, bounded (net calls = 0)
    assert net == pytest.approx(-5.0, abs=1e-9)


# ---------------------------------------------------------------- single() == net_margin()

def _random_arrays(n, seed=20260924):
    rng = np.random.default_rng(seed)
    spot = rng.uniform(1_000.0, 100_000.0, n)
    fwd = spot * rng.uniform(0.98, 1.05, n)
    tau = rng.choice([0.0, 1 / 365, 7 / 365, 0.25, 1.2], n) * rng.uniform(0.5, 1.0, n)
    tau = np.floor(tau * YEAR) / YEAR
    strike = np.round(fwd * np.exp(rng.normal(0.0, 0.35, n)), 0)
    return {
        "spot": spot, "forward": fwd, "sigma": rng.uniform(0.2, 1.5, n), "tau": tau, "rate": np.zeros(n),
        "strike": strike, "is_call": rng.random(n) < 0.5, "amount": rng.choice([-3.0, -1.0, -0.1, 0.5, 1.0], n),
        "vol_conf": rng.choice([1.0, 0.95, 0.5, 0.2], n), "fwd_conf": rng.choice([1.0, 0.3], n),
        "spot_conf": rng.choice([1.0, 0.9, 0.35], n), "stable": rng.choice([1.0, 1.0, 0.95], n),
    }


def _state_from_row(a, i):
    ts = 1_780_000_000
    expiry = ts + int(round(a["tau"][i] * YEAR))
    e = ExpiryState(expiry=expiry, forward=float(a["forward"][i]), svi=None, vol_conf=float(a["vol_conf"][i]),
                    fwd_conf=float(a["fwd_conf"][i]))
    st = MarketState(currency="BTC", ts=ts, spot=float(a["spot"][i]), expiries={expiry: e},
                     spot_conf=float(a["spot_conf"][i]), stable=float(a["stable"][i]))
    book = Book(options=[OptionLeg(expiry, float(a["strike"][i]), bool(a["is_call"][i]), float(a["amount"][i]))])
    return st, book, {(expiry, float(a["strike"][i])): float(a["sigma"][i])}


@pytest.mark.parametrize("is_initial", [True, False])
def test_single_equals_net_margin(is_initial):
    params = _test_params(0.8)
    a = _random_arrays(200)
    net, mtm = margin_sm.single(a, params, is_initial)
    assert net.shape == (200,) and mtm.shape == (200,)
    for i in range(200):
        st, book, vols = _state_from_row(a, i)
        n_i, m_i = margin_sm.net_margin(book, st, params, is_initial, vols=vols)
        assert net[i] == pytest.approx(n_i, rel=1e-12, abs=1e-9), i
        assert mtm[i] == pytest.approx(m_i, rel=1e-12, abs=1e-9), i


def test_single_is_fast_for_600k_contracts():
    params = _test_params(0.8)
    a = _random_arrays(600_000, seed=1)
    t0 = time.perf_counter()
    net, mtm = margin_sm.single(a, params, True)
    assert time.perf_counter() - t0 < 10.0
    assert np.isfinite(net).all() and np.isfinite(mtm).all()


def test_params_accept_today_schema():
    today = json.loads((FIX / "a4_params_today.json").read_text())["sm"]["BTC"]
    assert set(today) >= {"OptionMarginParams", "PerpMarginRequirements", "BaseMarginParams", "OracleContingencyParams",
                          "DepegParams"}
    st = _one_leg_state(spot=80_000.0, forward=80_100.0)
    e = 30 * 86400
    book = Book(options=[OptionLeg(e, 90_000.0, True, -1.0)])
    net, mtm = margin_sm.net_margin(book, st, today, vols={(e, 90_000.0): 0.45})
    a = max(0.13, 0.15 - 10_000.0 / 80_000.0)
    assert net == pytest.approx(-a * 80_000.0 + mtm, rel=1e-12)


# ---------------------------------------------------------------- Chain 957: eth_call at historical blocks

def _chain_rows():
    doc = json.loads((FIX / "sm_chain_cases.json").read_text())
    return doc["cases"]


def test_sm_chain_isolated_margin_matches_eth_call():
    """SRM.getIsolatedMargin at 12 blocks (BTC, ETH, HYPE; 2024 to 2026), 1 440 positions, IM and MM."""
    cases = _chain_rows()
    assert len(cases) >= 10 and {c["ccy"] for c in cases} == {"BTC", "ETH", "HYPE"}
    n = 0
    for c in cases:
        for r in c["rows"]:
            e = c["expiries"][str(r["expiry"])]
            vol = e["vols"][repr(r["strike"])][0]
            m, v = margin_sm.isolated_margin(c["spot"], e["forward"], vol, (r["expiry"] - c["ts"]) / YEAR, r["strike"],
                                             r["is_call"], r["amount"], c["params"], r["is_initial"])
            assert float(m) == pytest.approx(r["margin"], rel=1e-9, abs=1e-6), (c["ccy"], c["day"], r)
            assert float(v) == pytest.approx(r["mtm"], rel=1e-9, abs=1e-6), (c["ccy"], c["day"], r)
            n += 1
    assert n >= 1000


@pytest.mark.parametrize("is_initial", [True, False])
def test_sm_chain_single_and_net_margin_agree(is_initial):
    """single() on the chain inputs = max(chain isolated margin, max loss) minus the option contingency."""
    for c in _chain_rows():
        rows = [r for r in c["rows"] if r["is_initial"] == is_initial]
        ex = c["expiries"]
        a = {"spot": np.full(len(rows), c["spot"]),
             "forward": np.array([ex[str(r["expiry"])]["forward"] for r in rows]),
             "sigma": np.array([ex[str(r["expiry"])]["vols"][repr(r["strike"])][0] for r in rows]),
             "tau": np.array([(r["expiry"] - c["ts"]) / YEAR for r in rows]), "rate": np.zeros(len(rows)),
             "strike": np.array([r["strike"] for r in rows]), "is_call": np.array([r["is_call"] for r in rows]),
             "amount": np.array([r["amount"] for r in rows]),
             "vol_conf": np.array([ex[str(r["expiry"])]["vol_conf"] for r in rows]),
             "fwd_conf": np.array([ex[str(r["expiry"])]["fwd_conf"] for r in rows]),
             "spot_conf": np.full(len(rows), c["spot_conf"]), "stable": np.full(len(rows), c["stable"])}
        net, mtm = margin_sm.single(a, c["params"], is_initial)
        for i, r in enumerate(rows):
            max_loss = min(r["strike"] * r["amount"], 0.0) if not r["is_call"] else 0.0
            if r["is_call"] and r["amount"] < 0:
                scale = c["params"]["OptionMarginParams"]["unpairedIMScale" if is_initial else "unpairedMMScale"]
                max_loss += scale * a["forward"][i] * r["amount"]
            expected = max(r["margin"], max_loss)  # confidences are all above the thresholds at these blocks
            assert net[i] == pytest.approx(expected, rel=1e-9, abs=1e-6), (c["ccy"], c["day"], r)
            assert mtm[i] == pytest.approx(r["mtm"], rel=1e-9, abs=1e-6)
            st = MarketState(currency=c["ccy"], ts=c["ts"], spot=c["spot"], spot_conf=c["spot_conf"],
                             stable=c["stable"],
                             expiries={r["expiry"]: ExpiryState(expiry=r["expiry"], forward=a["forward"][i], svi=None,
                                                                vol_conf=a["vol_conf"][i], fwd_conf=a["fwd_conf"][i])})
            book = Book(options=[OptionLeg(r["expiry"], r["strike"], r["is_call"], r["amount"])])
            n_i, _ = margin_sm.net_margin(book, st, c["params"], is_initial,
                                          vols={(r["expiry"], r["strike"]): a["sigma"][i]})
            assert n_i == pytest.approx(net[i], rel=1e-12, abs=1e-9)


def test_sm_chain_whole_accounts_match_eth_call():
    """StandardManager.getMarginAndMarkToMarket for 12 real SM accounts (14 to 30 options, up to 8 markets, perps
    with unrealised PnL, base collateral) at six blocks between 2024 and 2026."""
    doc = _private("sm_chain_accounts.json")
    cases = [c for c in doc["cases"] if "skipped" not in c]
    assert len(cases) >= 10
    for c in cases:
        books, states, params, vols, bases = {}, {}, {}, {}, {}
        for mid, m in c["markets"].items():
            exps = {int(e): ExpiryState(expiry=int(e), forward=v["forward"], svi=None, vol_conf=v["vol_conf"],
                                        fwd_conf=v["fwd_conf"]) for e, v in m.get("expiries", {}).items()}
            p = m["perp"]
            q = p["amount"] if p else 0.0
            states[mid] = MarketState(currency=mid, ts=c["ts"], spot=m["spot"], expiries=exps,
                                      perp=p["price"] if p else None, stable=c["stable"], spot_conf=m["spot_conf"],
                                      perp_conf=p["conf"] if p else 1.0)
            # the chain's unsettled perp cash (PnL + funding) enters as an entry price
            entry = p["price"] - p["upnl"] / q if p and q != 0 else None
            books[mid] = Book(options=[OptionLeg(e, k, cl, a) for e, k, cl, a in m["options"]], perp=q,
                              perp_entry=entry)
            params[mid] = m["params"]
            vols[mid] = {(int(k.split("|")[0]), float(k.split("|")[1])): v for k, v in m.get("vols", {}).items()}
            bases[mid] = m["base"]
        for is_initial, key in ((True, "IM"), (False, "MM")):
            net, mtm = margin_sm.net_margin_multi(books, states, params, is_initial, cash=c["cash"], vols=vols,
                                                  bases=bases)
            assert net == pytest.approx(c[key]["net"], rel=1e-9, abs=1e-6), (c["day"], c["account_hash"], key)
            assert mtm == pytest.approx(c[key]["mtm"], rel=1e-9, abs=1e-6), (c["day"], c["account_hash"], key)


def test_requirement_is_mtm_minus_net():
    params = _test_params(0.8)
    st = _one_leg_state()
    e = 30 * 86400
    book = Book(options=[OptionLeg(e, 95.0, False, -2.0)], cash=1_000.0)
    net, mtm = margin_sm.net_margin(book, st, params, vols={(e, 95.0): 0.7})
    assert margin_sm.requirement(book, st, params, vols={(e, 95.0): 0.7}) == pytest.approx(mtm - net)
    assert mtm - net > 0


# ---------------------------------------------------------------- netting per instrument like SubAccounts

@pytest.mark.parametrize("is_initial", [True, False])
def test_legs_of_one_instrument_are_netted_like_subaccounts(is_initial):
    """One balance per subId on chain: +1 and -2 on one call equal -1 (isolated margin, max loss, depeg and option
    contingency count the net short), +1 and -1 equal nothing."""
    params = _test_params(0.8)
    e, e2 = 30 * 86400, 60 * 86400
    st = _one_leg_state(spot=100.0, forward=101.0, vol_conf=0.2, stable=0.9)  # below optionThreshold and depeg
    vols = {(e, 110.0): 0.5, (e, 95.0): 0.6}
    split = Book(options=[OptionLeg(e, 110.0, True, 1.0), OptionLeg(e, 95.0, False, -1.0),
                          OptionLeg(e, 110.0, True, -2.0)])
    merged = Book(options=[OptionLeg(e, 95.0, False, -1.0), OptionLeg(e, 110.0, True, -1.0)])
    n_s, m_s = margin_sm.net_margin(split, st, params, is_initial, vols=vols)
    n_m, m_m = margin_sm.net_margin(merged, st, params, is_initial, vols=vols)
    assert n_s == pytest.approx(n_m, rel=1e-12) and m_s == pytest.approx(m_m, rel=1e-12)
    flat = Book(options=[OptionLeg(e, 110.0, True, 1.0), OptionLeg(e, 110.0, True, -1.0),
                         OptionLeg(e2, 90.0, False, 0.5), OptionLeg(e2, 90.0, False, -0.5)], cash=50.0)
    assert margin_sm.net_margin(flat, st, params, is_initial, vols=vols) == \
        margin_sm.net_margin(Book(cash=50.0), st, params, is_initial, vols=vols)


def test_reviewer_example_btc_call_is_not_doubled():
    """Legs +1 and -2 on BTC 90000 C (net -1) must give the margin of the single leg -1, not twice it."""
    params = json.loads((FIX / "a4_params_today.json").read_text())["sm"]["BTC"]
    e = 30 * 86400
    st = _one_leg_state(spot=80_000.0, forward=80_100.0)
    vols = {(e, 90_000.0): 0.45}
    n2, _ = margin_sm.net_margin(Book(options=[OptionLeg(e, 90_000.0, True, 1.0), OptionLeg(e, 90_000.0, True, -2.0)]),
                                 st, params, vols=vols)
    n1, _ = margin_sm.net_margin(Book(options=[OptionLeg(e, 90_000.0, True, -1.0)]), st, params, vols=vols)
    assert n2 == pytest.approx(n1, rel=1e-12)


def _assert_same_params(chain: dict, timeline: dict, where) -> None:
    """Field-equal comparison of a parameter dict read at the block with the A2 timeline entry."""
    if isinstance(chain, dict):
        assert set(chain) == set(timeline), where
        for k in chain:
            _assert_same_params(chain[k], timeline[k], (where, k))
    elif isinstance(chain, list):
        assert len(chain) == len(timeline), where
        for i, (x, y) in enumerate(zip(chain, timeline)):
            _assert_same_params(x, y, (where, i))
    else:
        assert float(chain) == pytest.approx(float(timeline), rel=1e-15, abs=0.0), where


def test_chain_parameters_equal_a2_timelines():
    """The SM parameters read at the 12 chain blocks equal p2params.Timeline(ccy, "sm").at(ts) field by field."""
    from derive_surface.p2params import Timeline
    n = 0
    for c in _chain_rows():
        path = Timeline.path(c["ccy"], "sm")
        if not path.exists():
            pytest.skip(f"A2 timeline missing: {path}")
        _assert_same_params(c["params"], Timeline(c["ccy"], "sm").at(c["ts"]), (c["ccy"], c["day"]))
        n += 1
    assert n >= 12
