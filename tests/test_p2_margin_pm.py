"""Tests for the offline legacy portfolio-margin replica (derive_surface.margin_pm, v2-core PMRM + PMRMLib).

Reference cases come from v2-core (commit 96796a6, read from data/p2/v2-core), from historical eth_calls of the
deployed PMRMLib on Chain 957 (tests/fixtures/p2/pm_chain_cases.json) and from PMRM.getMargin on whole legacy-PM
maker accounts (data/p2/fixtures_private/pm_chain_accounts.json, not tracked); see gen_a4_chain_fixtures.py.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
import pytest

from derive_surface import margin_pm
from derive_surface.p2types import YEAR, Book, ExpiryState, MarketState, OptionLeg

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
T0 = 1_640_995_200  # PMRMTestBase warps to 1 Jan 2022


def _default_scenarios():
    """Config.getDefaultScenarios(): spot 1.15 .. 0.85 in 5 % steps, each with vol Up, None, Down."""
    out = []
    for shock in (1.15, 1.1, 1.05, 1.0, 0.95, 0.9, 0.85):
        for vol in (1, 0, 2):
            out.append({"spotShock": shock, "volShock": vol})
    return out


def _config_params(over=None) -> dict:
    """Config.getPMRMParams() of v2-core test/config-test.sol."""
    p = {
        "BasisContingencyParameters": {"scenarioSpotUp": 1.05, "scenarioSpotDown": 0.95, "basisContAddFactor": 0.25,
                                       "basisContMultFactor": 0.01},
        "OtherContingencyParameters": {"pegLossThreshold": 0.98, "pegLossFactor": 2.0, "confThreshold": 0.6,
                                       "confMargin": 0.5, "basePercent": 0.02, "perpPercent": 0.02,
                                       "optionPercent": 0.01},
        "MarginParameters": {"imFactor": 1.3, "baseStaticDiscount": 0.95, "rateMultScale": 4.0, "rateAddScale": 0.05},
        "VolShockParameters": {"volRangeUp": 0.45, "volRangeDown": 0.3, "shortTermPower": 0.3, "longTermPower": 0.13,
                               "dteFloor": 86400.0},
        "scenarios": _default_scenarios(),
        "maxExpiries": 11,
    }
    for (struct, field), value in (over or {}).items():
        p[struct][field] = value
    return p


class _MockFeed:
    """MockFeeds.sol: forward portions and rate per expiry, vol per (expiry, strike), vol confidence per expiry."""

    def __init__(self, spot, spot_conf=1.0):
        self.spot, self.spot_conf = spot, spot_conf
        self.fixed, self.var, self.fwd_conf, self.rate, self.rate_conf = {}, {}, {}, {}, {}
        self.vols, self.vol_conf = {}, {}
        self.perp, self.perp_conf, self.stable = spot, 1.0, 1.0

    def set_vol(self, expiry, strike, vol, conf):
        self.vols[(expiry, strike)] = vol
        self.vol_conf[expiry] = conf

    def set_forward(self, expiry, price, conf, fixed=0.0):
        self.fixed[expiry], self.var[expiry], self.fwd_conf[expiry] = fixed, price, conf

    def set_rate(self, expiry, rate, conf):
        self.rate[expiry], self.rate_conf[expiry] = rate, conf

    def state(self, ts):
        exps = {e: ExpiryState(expiry=e, forward=self.var[e] + self.fixed[e], svi=None, rate=self.rate.get(e, 0.0),
                               vol_conf=self.vol_conf.get(e, 0.0), fwd_conf=self.fwd_conf[e]) for e in self.var}
        return MarketState(currency="ETH", ts=ts, spot=self.spot, expiries=exps, perp=self.perp, stable=self.stable,
                           spot_conf=self.spot_conf, perp_conf=self.perp_conf)

    def kwargs(self):
        # the legacy engine ignores ExpiryState.rate (PM2 rate); the mock rate feed goes in explicitly
        return {"vols": self.vols, "fwd_fixed": self.fixed, "rates": self.rate, "rate_confs": self.rate_conf}


# ---------------------------------------------------------------- testAndVerifyScenarios.json (21 cases, 1e-10 USD)

def _load_verify(case: dict):
    s = case["Scenario"]
    f = _MockFeed(s["SpotPrice"] / E18, s["SpotConfidence"] / E18)
    for i, rel in enumerate(s["FeedExpiries"]):
        e = T0 + rel
        f.set_forward(e, s["ForwardsVariable"][i] / E18, s["ForwardConfidences"][i] / E18, s["ForwardsFixed"][i] / E18)
        f.set_rate(e, s["Rates"][i] / E18, s["RateConfidences"][i] / E18)
    f.stable = s["StablePrice"] / E18
    f.perp, f.perp_conf = s["PerpPrice"] / E18, s["PerpConfidence"] / E18
    book = Book()
    for i, rel in enumerate(s["OptionExpiries"]):
        e, k = T0 + rel, s["OptionStrikes"][i] / E18
        f.set_vol(e, k, s["OptionVols"][i] / E18, s["OptionVolConfidences"][i] / E18)
        book.options.append(OptionLeg(e, k, s["OptionIsCall"][i] == 1, s["OptionAmounts"][i] / E18))
    book.perp = s["Perps"] / E18
    # perpValue = unrealised PnL + funding enters totalMtM additively, exactly like cash
    book.cash = (s["Cash"] + (s["UnrealisedPerpPNL"] + s["UnrealisedFunding"] if s["Perps"] != 0 else 0)) / E18
    return book, f, s["Base"] / E18


def test_pm_v2core_verify_scenarios():
    cases = _v2core("PMRM/testAndVerifyScenarios.json")
    params = _config_params()
    assert len(cases) == 21
    for name, case in cases.items():
        book, feed, base = _load_verify(case)
        r = case["Result"]
        st = feed.state(T0)
        im, mtm = margin_pm.net_margin(book, st, params, True, base=base, **feed.kwargs())
        mm, _ = margin_pm.net_margin(book, st, params, False, base=base, **feed.kwargs())
        exp_im, exp_mm = r["InitialMarginHand"] / E18, r["MaintenanceMarginHand"] / E18
        # TestPMRM_Scenarios asserts 1e8 wei = 1e-10 USD; the float replica stays within 1e-9 relative
        assert im == pytest.approx(exp_im, rel=1e-9, abs=1e-6), (name, im, exp_im)
        assert mm == pytest.approx(exp_mm, rel=1e-9, abs=1e-6), (name, mm, exp_mm)
        assert mtm == pytest.approx(r["PortfolioMTM"] / E18, rel=1e-9, abs=1e-6), name


# ---------------------------------------------------------------- test-cases-portfolio-pm.json (44 cases, integer USD)

_EXPIRY_OFFSETS = {"20230104": 3, "20230111": 10, "20230118": 17, "20230227": 57, "20230804": 215, "20230811": 222,
                   "20230818": 229, "20230825": 238}
_ETH_FWD_ADD = [0.91345, 2.83305, 4.7545, 15.7696, 59.87416, 61.85933, 63.8284, 66.3744]


def _expiry(date: str) -> int:
    return 1 + _EXPIRY_OFFSETS[date] * 86400 + 8 * 3600  # TestCaseExpiries at block.timestamp = 1


def _portfolio_feed(name: str) -> _MockFeed:
    f = _MockFeed(2000.0)
    for date, add in zip(_EXPIRY_OFFSETS, _ETH_FWD_ADD):
        f.set_forward(_expiry(date), 2000.0 + add, 1.0)
        f.set_rate(_expiry(date), 0.02, 1.0)
    f.perp, f.perp_conf = 2001.0, 1.0
    e = _expiry("20230118")
    if name == "test_depeg_contingency_pm":
        f.stable = 0.2
    elif name in ("test_oracle_cont_long_call_pm", "test_oracle_cont_short_call_pm"):
        f.spot_conf = 0.1
        f.set_vol(e, 1700.0, 0.5, 0.3 if name == "test_oracle_cont_long_call_pm" else 0.1)
        f.set_forward(e, 2004.75, 0.4)
    elif name == "test_oracle_cont_base_asset_pm":
        f.spot_conf = 0.1
        f.set_vol(e, 1700.0, 0.01, 0.1)
        f.set_forward(e, 2004.75, 0.02)
    elif name == "test_oracle_cont_long_perp_asset_pm":
        f.spot_conf = 0.3
        f.set_vol(e, 1700.0, 0.5, 0.1)
        f.set_forward(e, 2004.75, 0.02)
        f.perp, f.perp_conf = 2001.0, 0.1
    elif name == "test_general_portfolio_pm":
        f.spot, f.spot_conf = 2004.0, 0.3
        f.set_vol(e, 1700.0, 0.15, 0.1)
        f.set_vol(e, 2100.0, 1.01, 0.1)
        f.set_vol(e, 1000.0, 0.33, 0.1)
        f.set_forward(_expiry("20230227"), 2014.7545, 0.2)
        f.perp, f.perp_conf = 2017.0, 0.3
    return f


def _sol_trunc(x: float) -> int:
    return math.trunc(round(x, 9))


def test_pm_v2core_portfolio_cases_integer_usd():
    cases = _v2core("PMRM/test-cases-portfolio-pm.json")
    params = _config_params({("MarginParameters", "rateAddScale"): 0.12,
                               ("OtherContingencyParameters", "confMargin"): 0.4,
                               ("OtherContingencyParameters", "basePercent"): 0.025,
                               ("OtherContingencyParameters", "perpPercent"): 0.025})
    assert len(cases) == 44
    for name, case in cases.items():
        f = _portfolio_feed(name)
        book = Book()
        for o in case["options"]:
            e, k = _expiry(o["expiry"]), float(o["strike"])
            if f.vols.get((e, k), 0.0) == 0.0:
                f.set_vol(e, k, 0.5, 1.0)
            book.options.append(OptionLeg(e, k, o["type"] == "call", o["amount"] / 1e8))
        for p in case["perps"]:
            book.perp, book.perp_entry = p["amount"] / 1e8, p["entryPrice"] / 1e8
        base = sum(b["amount"] / 1e8 for b in case["bases"])
        book.cash = case["cash"] / 1e8
        st = f.state(1)
        im, _ = margin_pm.net_margin(book, st, params, True, base=base, **f.kwargs())
        mm, _ = margin_pm.net_margin(book, st, params, False, base=base, **f.kwargs())
        res = case.get("results", case.get("result"))
        assert _sol_trunc(im) == int(res["im"]), (name, im, res["im"])
        assert _sol_trunc(mm) == int(res["mm"]), (name, mm, res["mm"])


# ---------------------------------------------------------------- hand-computed and structural cases

def test_long_call_needs_only_scenario_loss():
    """A long option loses at most its value; with no contingency R = imFactor * worst scenario loss."""
    params = _config_params()
    e = 30 * 86400
    st = MarketState(currency="BTC", ts=0, spot=100.0,
                     expiries={e: ExpiryState(expiry=e, forward=100.0, svi=None, rate=0.0)})
    book = Book(options=[OptionLeg(e, 100.0, True, 1.0)])
    im, mtm = margin_pm.net_margin(book, st, params, True, vols={(e, 100.0): 0.5})
    mm, _ = margin_pm.net_margin(book, st, params, False, vols={(e, 100.0): 0.5})
    assert mtm > 0
    assert (mtm - im) == pytest.approx(1.3 * (mtm - mm), rel=1e-12)  # imFactor scales the MM loss
    assert 0 < mtm - mm <= mtm + 1e-12


def test_legacy_pm_mtm_is_undiscounted():
    params = _config_params()
    e = 365 * 86400
    st = MarketState(currency="BTC", ts=0, spot=100.0,
                     expiries={e: ExpiryState(expiry=e, forward=105.0, svi=None, rate=0.05)})
    book = Book(options=[OptionLeg(e, 100.0, False, -2.0)])
    _, mtm = margin_pm.net_margin(book, st, params, True, vols={(e, 100.0): 0.6})
    from derive_surface.margin_sm import b76_prices
    _, put = b76_prices(105.0, 100.0, 0.6, float(e))
    assert mtm == pytest.approx(-2.0 * float(put), rel=1e-12)


# ---------------------------------------------------------------- single() == net_margin()

def _random_arrays(n, seed=20260924):
    rng = np.random.default_rng(seed)
    spot = rng.uniform(1_000.0, 100_000.0, n)
    fwd = spot * rng.uniform(0.98, 1.05, n)
    tau = rng.choice([0.0, 1 / 365, 7 / 365, 45 / 365, 1.2], n) * rng.uniform(0.5, 1.0, n)
    tau = np.floor(tau * YEAR) / YEAR
    return {
        "spot": spot, "forward": fwd, "sigma": rng.uniform(0.2, 1.5, n), "tau": tau,
        "rate": np.full(n, 0.042),  # PM2 rate column of FeedHistory.bulk_state: must be ignored
        "rate_pm": rng.choice([0.0, 0.0, 0.03, -0.01], n),
        "strike": np.round(fwd * np.exp(rng.normal(0.0, 0.35, n)), 0),
        "is_call": rng.random(n) < 0.5, "amount": rng.choice([-3.0, -1.0, -0.1, 0.5, 1.0], n),
        "vol_conf": rng.choice([1.0, 0.95, 0.5, 0.2], n), "fwd_conf": rng.choice([1.0, 0.3], n),
        "spot_conf": rng.choice([1.0, 0.9, 0.35], n), "stable": rng.choice([1.0, 1.0, 0.95], n),
    }


@pytest.mark.parametrize("is_initial", [True, False])
def test_single_equals_net_margin(is_initial):
    params = json.loads((FIX / "a4_params_today.json").read_text())["pm"]["BTC"]
    a = _random_arrays(200)
    net, mtm = margin_pm.single(a, params, is_initial)
    assert net.shape == (200,) and mtm.shape == (200,)
    ts = 1_780_000_000
    for i in range(200):
        expiry = ts + int(round(a["tau"][i] * YEAR))
        es = ExpiryState(expiry=expiry, forward=float(a["forward"][i]), svi=None, rate=float(a["rate"][i]),
                         vol_conf=float(a["vol_conf"][i]), fwd_conf=float(a["fwd_conf"][i]))
        rates = {expiry: float(a["rate_pm"][i])}
        st = MarketState(currency="BTC", ts=ts, spot=float(a["spot"][i]), expiries={expiry: es},
                         spot_conf=float(a["spot_conf"][i]), stable=float(a["stable"][i]))
        k = float(a["strike"][i])
        book = Book(options=[OptionLeg(expiry, k, bool(a["is_call"][i]), float(a["amount"][i]))])
        n_i, m_i = margin_pm.net_margin(book, st, params, is_initial, vols={(expiry, k): float(a["sigma"][i])},
                                        rates=rates)
        assert net[i] == pytest.approx(n_i, rel=1e-12, abs=1e-9), i
        assert mtm[i] == pytest.approx(m_i, rel=1e-12, abs=1e-9), i


def test_single_is_fast_for_600k_contracts():
    params = json.loads((FIX / "a4_params_today.json").read_text())["pm"]["BTC"]
    a = _random_arrays(600_000, seed=1)
    t0 = time.perf_counter()
    net, mtm = margin_pm.single(a, params, True)
    assert time.perf_counter() - t0 < 10.0
    assert np.isfinite(net).all() and np.isfinite(mtm).all()


# ---------------------------------------------------------------- Chain 957: deployed PMRMLib per eth_call

def _chain_state(c, legs):
    vconf = {}
    for e, k, _, _ in legs:
        vconf[e] = min(vconf.get(e, 1.0), c["expiries"][str(e)]["vols"][repr(k)][1])
    exps = {int(e): ExpiryState(expiry=int(e), forward=v["fixed"] + v["var"], svi=None,
                                vol_conf=vconf.get(int(e), 1.0), fwd_conf=v["fwd_conf"])
            for e, v in c["expiries"].items()}
    st = MarketState(currency=c["ccy"], ts=c["ts"], spot=c["spot"], expiries=exps, perp=c["perp_price"],
                     stable=c["stable"], spot_conf=c["spot_conf"], perp_conf=c["perp_conf"])
    kw = {"vols": {(e, k): c["expiries"][str(e)]["vols"][repr(k)][0] for e, k, _, _ in legs},
          "rates": {int(e): v["rate"] for e, v in c["expiries"].items()},
          "rate_confs": {int(e): v["rate_conf"] for e, v in c["expiries"].items()},
          "fwd_fixed": {int(e): v["fixed"] for e, v in c["expiries"].items()}}
    return st, kw


def test_pm_chain_books_match_deployed_lib():
    """Legacy PMRMLib at 8 blocks (BTC, ETH; 2024 to 2026, all three parameter regimes), 5 books each, IM and MM."""
    doc = json.loads((FIX / "pm_chain_cases.json").read_text())
    assert len(doc["cases"]) >= 8
    n = 0
    for c in doc["cases"]:
        for b in c["books"]:
            st, kw = _chain_state(c, b["legs"])
            book = Book(options=[OptionLeg(e, k, cl, q) for e, k, cl, q in b["legs"]], perp=b["perp"])
            for is_initial, key in ((True, "IM"), (False, "MM")):
                net, mtm = margin_pm.net_margin(book, st, c["params"], is_initial, base=b["base"], **kw)
                assert net == pytest.approx(b[key]["net"], rel=1e-9, abs=1e-6), (c["ccy"], c["day"], b["name"], key)
                assert mtm == pytest.approx(b[key]["mtm"], rel=1e-9, abs=1e-6), (c["ccy"], c["day"], b["name"], key)
                n += 1
    assert n >= 80


@pytest.mark.parametrize("is_initial", [True, False])
def test_pm_chain_single_leg_books_via_single(is_initial):
    doc = json.loads((FIX / "pm_chain_cases.json").read_text())
    key = "IM" if is_initial else "MM"
    for c in doc["cases"]:
        books = [b for b in c["books"] if len(b["legs"]) == 1 and b["perp"] == 0 and b["base"] == 0]
        assert books
        rows = [b["legs"][0] for b in books]
        ex = c["expiries"]
        a = {"spot": np.full(len(rows), c["spot"]),
             "forward": np.array([ex[str(e)]["fixed"] + ex[str(e)]["var"] for e, _, _, _ in rows]),
             "fwd_fixed": np.array([ex[str(e)]["fixed"] for e, _, _, _ in rows]),
             "sigma": np.array([ex[str(e)]["vols"][repr(k)][0] for e, k, _, _ in rows]),
             "tau": np.array([max(e - c["ts"], 0) / YEAR for e, _, _, _ in rows]),
             "rate_pm": np.array([ex[str(e)]["rate"] for e, _, _, _ in rows]),
             "rate_conf": np.array([ex[str(e)]["rate_conf"] for e, _, _, _ in rows]),
             "strike": np.array([k for _, k, _, _ in rows]), "is_call": np.array([cl for _, _, cl, _ in rows]),
             "amount": np.array([q for _, _, _, q in rows]),
             "vol_conf": np.array([ex[str(e)]["vols"][repr(k)][1] for e, k, _, _ in rows]),
             "fwd_conf": np.array([ex[str(e)]["fwd_conf"] for e, _, _, _ in rows]),
             "spot_conf": np.full(len(rows), c["spot_conf"]), "stable": np.full(len(rows), c["stable"])}
        net, mtm = margin_pm.single(a, c["params"], is_initial)
        for i, b in enumerate(books):
            assert net[i] == pytest.approx(b[key]["net"], rel=1e-9, abs=1e-6), (c["ccy"], c["day"], b["name"])
            assert mtm[i] == pytest.approx(b[key]["mtm"], rel=1e-9, abs=1e-6)


def test_requirement_is_mtm_minus_net_and_cash_is_additive():
    params = json.loads((FIX / "a4_params_today.json").read_text())["pm"]["BTC"]
    e = 20 * 86400
    st = MarketState(currency="BTC", ts=0, spot=80_000.0,
                     expiries={e: ExpiryState(expiry=e, forward=80_100.0, svi=None, rate=0.0)})
    legs = [OptionLeg(e, 85_000.0, True, -1.0), OptionLeg(e, 75_000.0, False, -1.0)]
    vols = {(e, 85_000.0): 0.45, (e, 75_000.0): 0.5}
    n0, m0 = margin_pm.net_margin(Book(options=legs), st, params, vols=vols)
    n1, m1 = margin_pm.net_margin(Book(options=legs, cash=5_000.0), st, params, vols=vols)
    assert n1 - n0 == pytest.approx(5_000.0) and m1 - m0 == pytest.approx(5_000.0)
    assert margin_pm.requirement(Book(options=legs), st, params, vols=vols) == pytest.approx(m0 - n0)


# ---------------------------------------------------------------- legacy rate feed, netting per instrument, maxExpiries

def _today():
    return json.loads((FIX / "a4_params_today.json").read_text())["pm"]["BTC"]


def test_legacy_pm_ignores_expiry_state_rate():
    """The legacy StaticRate feeds (BTC 0x6fef..., ETH 0x30a6...) hold rate 0 at confidence 1 over the whole history;
    ExpiryState.rate carries the PM2 rate (about 4.2 %) and must not leak into the legacy static discount."""
    params = _today()
    e = 180 * 86400
    vols = {(e, 80_000.0): 0.5}
    book = Book(options=[OptionLeg(e, 80_000.0, True, 1.0)])

    def state(rate):
        return MarketState(currency="BTC", ts=0, spot=80_000.0,
                           expiries={e: ExpiryState(expiry=e, forward=80_500.0, svi=None, rate=rate)})

    for is_initial in (True, False):
        assert margin_pm.net_margin(book, state(0.042), params, is_initial, vols=vols) == \
            margin_pm.net_margin(book, state(0.0), params, is_initial, vols=vols)
    # an explicit legacy rate still works as override and lowers the discounted upside of a long option
    n0, _ = margin_pm.net_margin(book, state(0.0), params, vols=vols)
    n1, _ = margin_pm.net_margin(book, state(0.0), params, vols=vols, rates={e: 0.042})
    assert n1 < n0


def test_single_ignores_rate_column_and_reads_rate_pm():
    params = _today()
    a = _random_arrays(300, seed=7)
    a["rate_pm"] = np.zeros(300)
    b = dict(a, rate=np.zeros(300))
    n_a, m_a = margin_pm.single(a, params)
    n_b, m_b = margin_pm.single(b, params)
    np.testing.assert_array_equal(n_a, n_b)
    np.testing.assert_array_equal(m_a, m_b)
    del b["rate"]
    n_c, _ = margin_pm.single(b, params)  # neither rate nor rate_pm: legacy rate 0
    np.testing.assert_array_equal(n_a, n_c)
    d = dict(a, rate_pm=np.full(300, 0.042))
    n_d, _ = margin_pm.single(d, params)
    assert (n_d <= n_a + 1e-12).all() and (n_d < n_a - 1e-9).any()


@pytest.mark.parametrize("is_initial", [True, False])
def test_legs_of_one_instrument_are_netted_like_subaccounts(is_initial):
    """SubAccounts hold one balance per subId: +1 and -2 on one call equal -1, +1 and -1 equal nothing (confidence
    below confThreshold, so netOptions = sum |balance| enters the IM)."""
    params = _today()
    e, e2 = 30 * 86400, 60 * 86400
    st = MarketState(currency="BTC", ts=0, spot=80_000.0, spot_conf=0.5,
                     expiries={e: ExpiryState(expiry=e, forward=80_100.0, svi=None, vol_conf=0.3)})
    vols = {(e, 90_000.0): 0.45, (e, 70_000.0): 0.5}
    split = Book(options=[OptionLeg(e, 90_000.0, True, 1.0), OptionLeg(e, 70_000.0, False, -1.0),
                          OptionLeg(e, 90_000.0, True, -2.0)])
    merged = Book(options=[OptionLeg(e, 70_000.0, False, -1.0), OptionLeg(e, 90_000.0, True, -1.0)])
    n_s, m_s = margin_pm.net_margin(split, st, params, is_initial, vols=vols)
    n_m, m_m = margin_pm.net_margin(merged, st, params, is_initial, vols=vols)
    assert n_s == pytest.approx(n_m, rel=1e-12) and m_s == pytest.approx(m_m, rel=1e-12)
    # a closed position (also on an expiry without feed state) is not held at all
    flat = Book(options=[OptionLeg(e, 90_000.0, True, 1.0), OptionLeg(e, 90_000.0, True, -1.0),
                         OptionLeg(e2, 85_000.0, False, 0.5), OptionLeg(e2, 85_000.0, False, -0.5)], cash=100.0)
    assert margin_pm.net_margin(flat, st, params, is_initial, vols=vols) == \
        margin_pm.net_margin(Book(cash=100.0), st, params, is_initial, vols=vols)


def test_strict_expiries_mirrors_pmrm_too_many_expiries():
    """PMRM._countExpiriesAndOptions reverts (PMRM_TooManyExpiries) at the (maxExpiries + 1)-th expiry held."""
    params = dict(_today(), maxExpiries=2)
    days = (7, 14, 30)
    exps = {d * 86400: ExpiryState(expiry=d * 86400, forward=80_100.0, svi=None) for d in days}
    st = MarketState(currency="BTC", ts=0, spot=80_000.0, expiries=exps)
    vols = {(d * 86400, 80_000.0): 0.5 for d in days}
    three = Book(options=[OptionLeg(d * 86400, 80_000.0, True, -1.0) for d in days])
    net, _ = margin_pm.net_margin(three, st, params, vols=vols)  # default: not enforced
    assert math.isfinite(net)
    with pytest.raises(margin_pm.TooManyExpiries):
        margin_pm.net_margin(three, st, params, vols=vols, strict_expiries=True)
    assert issubclass(margin_pm.TooManyExpiries, ValueError)
    # a closed third expiry is not held and does not count
    two = Book(options=three.options[:2] + [OptionLeg(30 * 86400, 80_000.0, True, 1.0),
                                            OptionLeg(30 * 86400, 80_000.0, True, -1.0)])
    n2, _ = margin_pm.net_margin(two, st, params, vols=vols, strict_expiries=True)
    assert n2 == margin_pm.net_margin(Book(options=three.options[:2]), st, params, vols=vols)[0]


def test_pm_chain_whole_accounts_match_get_margin():
    """PMRM.getMargin(account, isInitial) for real legacy-PM maker accounts (options over several expiries, perp with
    unsettled cash, cash) at blocks in all three parameter regimes, every feed value read at the same block. Checks
    the portfolio arrangement (``PMRM._arrangePortfolio``) independently of the library cases above. The legacy rate
    is not passed: the engine's default 0 must reproduce the chain."""
    doc = _private("pm_chain_accounts.json")
    cases = [c for c in doc["cases"] if "skipped" not in c]
    assert len(cases) >= 3 and {c["ccy"] for c in cases} == {"BTC", "ETH"}
    for c in cases:
        assert all(v["rate"] == 0.0 and v["rate_conf"] == 1.0 for v in c["expiries"].values())
        vols, vconf = {}, {}
        for key, (v, vc) in c["vols"].items():
            e, k = int(key.split("|")[0]), float(key.split("|")[1])
            vols[(e, k)] = v
            vconf[e] = min(vconf.get(e, 1.0), vc)
        exps = {int(e): ExpiryState(expiry=int(e), forward=v["fixed"] + v["var"], svi=None, rate=0.042,
                                    vol_conf=vconf.get(int(e), 1.0), fwd_conf=v["fwd_conf"])
                for e, v in c["expiries"].items()}
        p = c["perp"]
        q = p["amount"] if p else 0.0
        st = MarketState(currency=c["ccy"], ts=c["ts"], spot=c["spot"], expiries=exps,
                         perp=p["price"] if p else None, stable=c["stable"], spot_conf=c["spot_conf"],
                         perp_conf=p["conf"] if p else 1.0)
        # unsettled perp cash (PnL + funding) enters as an entry price
        entry = p["price"] - p["upnl"] / q if p and q != 0 else None
        book = Book(options=[OptionLeg(e, k, cl, a) for e, k, cl, a in c["options"]], perp=q, perp_entry=entry,
                    cash=c["cash"])
        kw = {"vols": vols, "base": c["base"], "strict_expiries": True,
              "fwd_fixed": {int(e): v["fixed"] for e, v in c["expiries"].items()}}
        for is_initial, key in ((True, "IM"), (False, "MM")):
            net, mtm = margin_pm.net_margin(book, st, c["params"], is_initial, **kw)
            assert net == pytest.approx(c[key], rel=1e-9, abs=1e-6), (c["ccy"], c["day"], c["account_hash"], key)
            assert mtm == pytest.approx(c["mtm"], rel=1e-9, abs=1e-6), (c["ccy"], c["day"], c["account_hash"])


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
    """The parameters read at the 13 legacy-PM chain blocks equal p2params.Timeline(ccy, "pm").at(ts) field by field
    (all three regimes: basis 1.0/1.2 until 12.06.2024, maxExpiries 11 -> 18 on 25.09.2024, volRangeUp,
    optionPercent and scenarios on 22.02.2025). The 5 account blocks come from the private fixture; without it the
    8 library blocks are checked."""
    from derive_surface.p2params import Timeline
    docs = {"pm_chain_cases.json": json.loads((FIX / "pm_chain_cases.json").read_text())}
    if (PRIVATE / "pm_chain_accounts.json").exists():
        docs["pm_chain_accounts.json"] = _private("pm_chain_accounts.json")
    n = 0
    for name, doc in docs.items():
        for c in doc["cases"]:
            if "skipped" in c:
                continue
            path = Timeline.path(c["ccy"], "pm")
            if not path.exists():
                pytest.skip(f"A2 timeline missing: {path}")
            _assert_same_params(c["params"], Timeline(c["ccy"], "pm").at(c["ts"]), (name, c["ccy"], c["day"]))
            n += 1
    assert n >= (13 if len(docs) == 2 else 8)
