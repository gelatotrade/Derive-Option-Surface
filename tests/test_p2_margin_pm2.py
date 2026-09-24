"""Tests for the offline PMRMLib_2 replica (``derive_surface.margin_pm2``).

Three layers:
* the 139 v2-core portfolio cases (``data/p2/v2-core/.../PMRM_2/portfolio_cases``, read in place, skipped when absent),
* real chain cases (``tests/fixtures/p2/pm2_chain_cases.json``: feeds, parameters and the ``eth_call`` result of
  ``PMRMLib_2.addPrecomputes`` + ``getMarginAndMarkToMarket`` at the same block),
* the vectorised single-contract path against the book path, plus hand-checked pieces.

The parameter dicts follow the A2 schema (Solidity struct and field names, values as floats, ``dteFloor`` in
seconds). The adapters below build that schema from raw chain snapshots and from the v2-core case files; they are
test helpers only.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

from derive_surface import margin_pm2 as pm2
from derive_surface.p2types import YEAR, Book, ExpiryState, MarketState, OptionLeg

ROOT = Path(__file__).resolve().parents[1]
CHAIN_FIXTURE = ROOT / "tests" / "fixtures" / "p2" / "pm2_chain_cases.json"
V2CORE_CASES = ROOT / "data" / "p2" / "v2-core" / "test" / "risk-managers" / "unit-tests" / "PMRM_2" / "portfolio_cases"
E18 = 10 ** 18
REF_TIME = 1_630_000_000  # TestPMRM_2_PortfolioCasesNEW.t.sol: vm.warp(REF_TIME)
DAY = 86_400


@dataclass(frozen=True)
class _Expiry(ExpiryState):
    """ExpiryState plus the optional feed fields that margin_pm2 reads when present."""

    fwd_fixed: float = 0.0
    rate_conf: float = 1.0


# ----------------------------------------------------------------------------------------------------------------
# Adapter: raw chain snapshot -> A2 parameter schema (test helper, not production code)
# ----------------------------------------------------------------------------------------------------------------
MARGIN_FIELDS = ["imFactor", "mmFactor", "shortRateMultScale", "longRateMultScale", "shortRateAddScale",
                 "longRateAddScale", "shortBaseStaticDiscount", "longBaseStaticDiscount"]
VOL_FIELDS = ["volRangeUp", "volRangeDown", "shortTermPower", "longTermPower", "dteFloor", "minVolUpShock"]
BASIS_FIELDS = ["scenarioSpotUp", "scenarioSpotDown", "basisContAddFactor", "basisContMultFactor"]
OTHER_FIELDS = ["pegLossThreshold", "pegLossFactor", "confThreshold", "confMargin", "MMPerpPercent", "IMPerpPercent",
                "MMOptionPercent", "IMOptionPercent"]
SKEW_FIELDS = ["linearBaseCap", "absBaseCap", "linearCBase", "absCBase", "minKStar", "widthScale", "volParamStatic",
               "volParamScale"]


def _d(x) -> float:
    return int(x) / E18


def params_from_snapshot(snap: dict) -> dict:
    """Getter tuples of PMRMLib_2 / PMRM_2 (raw uint/int strings) -> A2 schema."""
    vol = {k: _d(v) for k, v in zip(VOL_FIELDS, snap["volShock"])}
    vol["dteFloor"] = float(int(snap["volShock"][4]))  # seconds, not 1e18-scaled
    return {
        "MarginParameters": {k: _d(v) for k, v in zip(MARGIN_FIELDS, snap["margin"])},
        "VolShockParameters": vol,
        "BasisContingencyParameters": {k: _d(v) for k, v in zip(BASIS_FIELDS, snap["basis"])},
        "OtherContingencyParameters": {k: _d(v) for k, v in zip(OTHER_FIELDS, snap["other"])},
        "SkewShockParameters": {k: _d(v) for k, v in zip(SKEW_FIELDS, snap["skew"])},
        "scenarios": [{"spotShock": _d(s[0]), "volShock": int(s[1]), "dampeningFactor": _d(s[2])}
                      for s in snap["scenarios"]],
        "maxExpiries": int(snap["maxExpiries"]),
    }


def state_from_snapshot(snap: dict):
    """MarketState and per-strike chain vols of a snapshot."""
    expiries, vols = {}, {}
    for e, d in snap["expiries"].items():
        e = int(e)
        confs = {_d(v[1]) for v in d["vols"].values()}
        assert len(confs) == 1, "LyraVolFeed confidence is per expiry"
        fixed, var = _d(d["fixed"]), _d(d["var"])
        expiries[e] = _Expiry(expiry=e, forward=fixed + var, svi=None, rate=_d(d["rate"]), vol_conf=confs.pop(),
                              fwd_conf=_d(d["fconf"]), fwd_fixed=fixed, rate_conf=_d(d["rconf"]))
        for k_raw, (v, _c) in d["vols"].items():
            vols[(e, _d(k_raw))] = _d(v)
    state = MarketState(currency=snap["ccy"], ts=int(snap["timestamp"]), spot=_d(snap["spot"][0]), expiries=expiries,
                        perp=_d(snap["perp"][0]), stable=_d(snap["stable"][0]), spot_conf=_d(snap["spot"][1]),
                        perp_conf=_d(snap["perp"][1]))
    return state, vols


def book_from_case(case: dict) -> Book:
    legs = [OptionLeg(int(e), _d(k), bool(c), _d(a)) for e, k, c, a in case["legs"]]
    entry = case.get("perp_entry")
    return Book(options=legs, perp=_d(case.get("perp", "0")), perp_entry=None if entry is None else _d(entry),
                cash=_d(case.get("cash", "0")))


def _chain():
    return json.loads(CHAIN_FIXTURE.read_text())


CHAIN = _chain()


# ----------------------------------------------------------------------------------------------------------------
# Adapter: v2-core portfolio case -> A2 schema, Book, MarketState (test helper)
# ----------------------------------------------------------------------------------------------------------------
V2_DIR = {"None": 0, "Up": 1, "Down": 2, "LINEAR": 3, "ABS": 4}


def params_from_v2core(J: dict) -> dict:
    p = J["Parameters"]
    M, V, B, O, S = p["Margin"], p["VolShock"], p["BasisContingency"], p["OtherContingency"], p["SkewShock"]
    f = float
    return {
        "MarginParameters": {"imFactor": f(M["IM_LOSS_FACTOR"]), "mmFactor": f(M["MM_LOSS_FACTOR"]),
                             "shortRateMultScale": f(M["SHORT_RATE_MULTSCALE"]),
                             "longRateMultScale": f(M["LONG_RATE_MULTSCALE"]),
                             "shortRateAddScale": f(M["SHORT_RATE_ADDSCALE"]),
                             "longRateAddScale": f(M["LONG_RATE_ADDSCALE"]),
                             "shortBaseStaticDiscount": f(M["BASE_STATIC_DISCOUNT_NEG"]),
                             "longBaseStaticDiscount": f(M["BASE_STATIC_DISCOUNT"])},
        "VolShockParameters": {"volRangeUp": f(V["VOLRANGEUP"]), "volRangeDown": f(V["VOLRANGEDOWN"]),
                               "shortTermPower": f(V["SHORTTERMPOWER"]), "longTermPower": f(V["LONGTERMPOWER"]),
                               "dteFloor": f(V["DTE_FLOOR"]) * DAY,  # harness: DTE_FLOOR * 1 days / 1e18
                               "minVolUpShock": f(V["MIN_VOL_EVAL_SHOCKED"])},
        "BasisContingencyParameters": {"scenarioSpotUp": f(B["SCENARIO_SPOT_UP"]),
                                       "scenarioSpotDown": f(B["SCENARIO_SPOT_DOWN"]),
                                       "basisContAddFactor": f(B["BASIS_CONT_ADD_FACTOR"]),
                                       "basisContMultFactor": f(B["BASIS_CONT_MULT_FACTOR"])},
        "OtherContingencyParameters": {"pegLossThreshold": f(O["PEG_LOSS_THRESHOLD"]),
                                       "pegLossFactor": f(O["PEG_LOSS_FACTOR"]),
                                       "confThreshold": f(O["CONF_THRESHOLD"]), "confMargin": f(O["CONF_MARGIN"]),
                                       "MMPerpPercent": f(O["MM_PERP_PERCENT"]),
                                       "IMPerpPercent": f(O["IM_PERP_PERCENT"]),
                                       "MMOptionPercent": f(O["MM_OPTION_PERCENT"]),
                                       "IMOptionPercent": f(O["IM_OPTION_PERCENT"])},
        "SkewShockParameters": {"linearBaseCap": f(S["LINEAR_SCALE_CAP"]), "absBaseCap": f(S["ABS_SCALE_CAP"]),
                                "linearCBase": f(S["LINEAR_CBASE"]), "absCBase": f(S["ABS_CBASE"]),
                                "minKStar": f(S["MIN_K_STAR"]), "widthScale": f(S["MIN_WIDTH_SCALE"]),
                                "volParamStatic": f(S["VOL_PARAM_STATIC"]), "volParamScale": f(S["VOL_PARAM_SCALE"])},
        "scenarios": [{"spotShock": f(s["SpotShock"]), "volShock": V2_DIR[s["VolShockDirection"]],
                       "dampeningFactor": f(s["DampeningFactor"])} for s in p["Scenarios"]],
        "maxExpiries": 16,
    }


def portfolio_from_v2core(J: dict):
    """Book, MarketState, vols and collaterals exactly as the Solidity harness arranges them."""
    s = J["Scenario"]
    f = float
    expiries = {}
    for fd in s["OptionFeeds"]:
        sec = int(fd["FeedExpiry"])
        F = f(fd["Forward"])
        # harness: inside the 30 min settlement window the forward is split into fixed and variable portions
        fixed = F * (1800 - sec) / 1800 if sec < 1800 else 0.0
        expiries[REF_TIME + sec] = _Expiry(expiry=REF_TIME + sec, forward=F, svi=None, rate=f(fd["Rate"]),
                                           vol_conf=f(fd["OptionVolConfidences"]),
                                           fwd_conf=f(fd["ForwardConfidence"]), fwd_fixed=fixed,
                                           rate_conf=f(fd["RateConfidence"]))
    legs, vols = [], {}
    for o in s["Options"]:
        e = REF_TIME + int(o["Expiry"])
        K = f(o["Strike"])
        legs.append(OptionLeg(e, K, bool(int(o["IsCall"])), f(o["Amount"])))
        vols[(e, K)] = f(o["MarkVol"])
    q = f(s["NumPerps"])
    P = f(s["PerpPrice"])
    pv = f(s["UnrealisedPerpPNL"]) + f(s["UnrealisedFunding"])
    # perpValue = q (P - entry)  <=>  entry = P - perpValue / q (perpValue only exists when a perp is held)
    entry = (P - pv / q) if q != 0 else None
    book = Book(options=legs, perp=q, perp_entry=entry, cash=f(s["Cash"]))
    state = MarketState(currency="ETH", ts=REF_TIME, spot=f(s["SpotPrice"]), expiries=expiries, perp=P,
                        stable=f(s["StablePrice"]), spot_conf=f(s["SpotConfidence"]), perp_conf=f(s["PerpConfidence"]))
    colls = [pm2.Collateral(amount=f(c["Amount"]), price=f(c["Price"]), confidence=f(c["Confidence"]),
                            is_risk_cancelling=bool(c["IsRiskCancelling"]), MMHaircut=f(c["MMHaircut"]),
                            IMHaircut=f(c["IMHaircut"])) for c in s.get("Collaterals", [])]
    return book, state, vols, colls


V2_FILES = sorted(V2CORE_CASES.glob("*.json")) if V2CORE_CASES.exists() else []
# Note: the Solidity harness skips test_67 because PMRM_2.setScenarios rejects its skew scenario with a spot shock
# (PMRM_2.sol:168-175). The lib ignores the spot shock of skew scenarios, and so does the replica, so it matches too.


def _rel(x: float, ref: float) -> float:
    return abs(x - ref) / max(1.0, abs(ref))


@pytest.mark.skipif(not V2_FILES, reason="v2-core reference cases not present under data/p2/v2-core")
def test_v2core_reference_case_count():
    assert len(V2_FILES) == 139


@pytest.mark.parametrize("path", V2_FILES, ids=[p.stem for p in V2_FILES])
def test_v2core_reference_cases(path):
    J = json.loads(path.read_text())
    params = params_from_v2core(J)
    book, state, vols, colls = portfolio_from_v2core(J)
    im, _ = pm2.net_margin(book, state, params, True, vols=vols, collaterals=colls)
    mm, _ = pm2.net_margin(book, state, params, False, vols=vols, collaterals=colls)
    assert _rel(im, float(J["Result"]["IM"])) <= 1e-9
    assert _rel(mm, float(J["Result"]["MM"])) <= 1e-9


# ----------------------------------------------------------------------------------------------------------------
# Chain cases
# ----------------------------------------------------------------------------------------------------------------
def test_chain_fixture_has_enough_cases():
    assert len(CHAIN["cases"]) >= 10
    assert {c["snapshot"].split("_")[0] for c in CHAIN["cases"]} >= {"BTC", "ETH", "HYPE"}


@pytest.mark.parametrize("case", CHAIN["cases"], ids=[c["name"] for c in CHAIN["cases"]])
def test_chain_cases(case):
    snap = CHAIN["snapshots"][case["snapshot"]]
    params = params_from_snapshot(snap)
    state, vols = state_from_snapshot(snap)
    book = book_from_case(case)
    for key, initial in (("IM", True), ("MM", False)):
        d = pm2.margin_details(book, state, params, initial, vols=vols)
        want = case["chain"][key]
        assert d["net"] == pytest.approx(_d(want["net"]), abs=1e-6)
        assert d["mtm"] == pytest.approx(_d(want["mtm"]), abs=1e-6)
        assert d["worst"] == int(want["worst"])
        net, mtm = pm2.net_margin(book, state, params, initial, vols=vols)
        assert (net, mtm) == (d["net"], d["mtm"])
        assert pm2.requirement(book, state, params, initial, vols=vols) == pytest.approx(mtm - net, abs=1e-9)


# ----------------------------------------------------------------------------------------------------------------
# single() against net_margin()
# ----------------------------------------------------------------------------------------------------------------
def _random_contracts(n: int, seed: int):
    rng = np.random.default_rng(seed)
    snaps = sorted(CHAIN["snapshots"])
    param_sets = [params_from_snapshot(CHAIN["snapshots"][k]) for k in snaps]
    out = []
    ts = 1_780_000_000
    for i in range(n):
        params = param_sets[i % len(param_sets)]
        spot = float(rng.choice([35.0, 2_500.0, 90_000.0]))
        kind = rng.integers(0, 6)
        if kind == 0:
            sec = int(rng.choice([0, 600, 1_799, 3_600, 30 * DAY, 30 * DAY + 1, 30 * DAY - 1, DAY - 1]))
        else:
            sec = int(rng.integers(60, 400 * DAY))
        fwd = spot * float(np.exp(rng.normal(0.0, 0.02)))
        fixed = float(rng.uniform(0, fwd)) if sec < 1_800 and rng.random() < 0.5 else 0.0
        strike = float(fwd * np.exp(rng.normal(0.0, 0.35)))
        c = dict(
            params=params, ts=ts, expiry=ts + sec, spot=spot, forward=fwd, fwd_fixed=fixed,
            sigma=float(rng.uniform(0.05, 2.5)), rate=float(rng.uniform(-0.03, 0.12)), strike=strike,
            is_call=bool(rng.random() < 0.5), amount=float(rng.choice([-1.0, 1.0]) * rng.choice([1.0, 0.37, 25.0])),
            vol_conf=float(rng.choice([1.0, 0.95, 0.5, 0.2])), fwd_conf=float(rng.choice([1.0, 0.97, 0.4])),
            rate_conf=float(rng.choice([1.0, 0.3])), spot_conf=float(rng.choice([1.0, 0.99, 0.5])),
            stable=float(rng.choice([1.0, 0.9999, 0.97])), cash=float(rng.choice([0.0, 1234.5])),
        )
        out.append(c)
    return out


def _as_book(c):
    e = _Expiry(expiry=c["expiry"], forward=c["forward"], svi=None, rate=c["rate"], vol_conf=c["vol_conf"],
                fwd_conf=c["fwd_conf"], fwd_fixed=c["fwd_fixed"], rate_conf=c["rate_conf"])
    state = MarketState(currency="BTC", ts=c["ts"], spot=c["spot"], expiries={e.expiry: e}, stable=c["stable"],
                        spot_conf=c["spot_conf"])
    book = Book(options=[OptionLeg(c["expiry"], c["strike"], c["is_call"], c["amount"])], cash=c["cash"])
    return book, state, {(c["expiry"], c["strike"]): c["sigma"]}


def _as_arrays(cs):
    keys = ["spot", "forward", "sigma", "rate", "strike", "is_call", "amount", "vol_conf", "fwd_conf", "spot_conf",
            "stable", "rate_conf", "fwd_fixed", "cash"]
    arr = {k: np.array([c[k] for c in cs]) for k in keys}
    arr["tau"] = np.array([(c["expiry"] - c["ts"]) / YEAR for c in cs])
    return arr


@pytest.mark.parametrize("initial", [True, False])
def test_single_matches_net_margin_on_random_contracts(initial):
    cs = _random_contracts(200, seed=20260924)
    by_params = {}
    for c in cs:
        by_params.setdefault(id(c["params"]), []).append(c)
    n_checked = 0
    for group in by_params.values():
        net, mtm = pm2.single(_as_arrays(group), group[0]["params"], initial)
        for i, c in enumerate(group):
            book, state, vols = _as_book(c)
            want_net, want_mtm = pm2.net_margin(book, state, c["params"], initial, vols=vols)
            assert net[i] == pytest.approx(want_net, rel=1e-10, abs=1e-8)
            assert mtm[i] == pytest.approx(want_mtm, rel=1e-10, abs=1e-8)
            n_checked += 1
    assert n_checked == 200


def test_single_accepts_scalar_broadcast_and_defaults():
    params = params_from_snapshot(CHAIN["snapshots"][sorted(CHAIN["snapshots"])[0]])
    base = dict(spot=90_000.0, forward=np.array([90_100.0, 90_100.0]), sigma=0.5, tau=30 / 365, rate=0.04,
                strike=np.array([95_000.0, 85_000.0]), is_call=np.array([True, False]), amount=-1.0,
                vol_conf=1.0, fwd_conf=1.0, spot_conf=1.0)
    net, mtm = pm2.single(base, params)
    assert net.shape == mtm.shape == (2,)
    full = {k: np.broadcast_to(np.asarray(v), (2,)).copy() for k, v in base.items()}
    net2, mtm2 = pm2.single(full, params)
    np.testing.assert_array_equal(net, net2)
    np.testing.assert_array_equal(mtm, mtm2)


def test_single_is_fast_enough_for_600k_contracts():
    params = params_from_snapshot(CHAIN["snapshots"][sorted(CHAIN["snapshots"])[0]])
    n = 600_000
    rng = np.random.default_rng(1)
    fwd = 90_000.0 * np.exp(rng.normal(0, 0.01, n))
    arrays = dict(spot=np.full(n, 90_000.0), forward=fwd, sigma=rng.uniform(0.2, 1.5, n),
                  tau=rng.uniform(0, 1.2, n), rate=rng.uniform(0, 0.08, n), strike=fwd * np.exp(rng.normal(0, 0.3, n)),
                  is_call=rng.random(n) < 0.5, amount=np.where(rng.random(n) < 0.5, -1.0, 1.0),
                  vol_conf=np.ones(n), fwd_conf=np.ones(n), spot_conf=np.ones(n))
    t0 = time.perf_counter()
    net, mtm = pm2.single(arrays, params)
    elapsed = time.perf_counter() - t0
    assert np.isfinite(net).all() and np.isfinite(mtm).all()
    assert elapsed < 120.0


# ----------------------------------------------------------------------------------------------------------------
# Hand-checked pieces
# ----------------------------------------------------------------------------------------------------------------
def _today():
    snap = CHAIN["snapshots"][sorted(k for k in CHAIN["snapshots"] if k.startswith("BTC"))[-1]]
    return params_from_snapshot(snap)


def _state(expiries, ts=1_780_000_000, **kw):
    exps = {e.expiry: e for e in expiries}
    return MarketState(currency="BTC", ts=ts, spot=kw.pop("spot", 80_000.0), expiries=exps, **kw)


def test_perp_value_scenario_and_contingency_by_hand():
    params = _today()
    O = params["OtherContingencyParameters"]
    M = params["MarginParameters"]
    S, P, q, entry = 80_000.0, 80_150.0, -2.5, 79_000.0
    state = _state([], spot=S, perp=P)
    book = Book(perp=q, perp_entry=entry)
    pnl = [q * (s["spotShock"] - 1.0) * P * s["dampeningFactor"] for s in params["scenarios"]]
    min_span = min(0.0, min(pnl))
    value = q * (P - entry)
    im_req = -min_span * M["imFactor"] + abs(q) * S * (O["MMPerpPercent"] + O["IMPerpPercent"])
    mm_req = -min_span * M["mmFactor"] + abs(q) * S * O["MMPerpPercent"]
    im, mtm = pm2.net_margin(book, state, params, True)
    mm, _ = pm2.net_margin(book, state, params, False)
    assert mtm == pytest.approx(value, abs=1e-9)
    assert im == pytest.approx(value - im_req, rel=1e-12)
    assert mm == pytest.approx(value - mm_req, rel=1e-12)
    # entry None = entry at the engine's perp price: no unrealised PnL
    assert pm2.net_margin(Book(perp=q), state, params, True)[1] == 0.0


def test_oracle_contingency_uses_min_confidence_of_held_expiry():
    params = _today()
    O = params["OtherContingencyParameters"]
    ts = 1_780_000_000
    e1 = _Expiry(expiry=ts + 10 * DAY, forward=80_100.0, svi=None, rate=0.04)
    e2 = _Expiry(expiry=ts + 40 * DAY, forward=80_300.0, svi=None, rate=0.04)
    legs = [OptionLeg(e1.expiry, 85_000.0, True, -1.5), OptionLeg(e1.expiry, 75_000.0, False, 0.5),
            OptionLeg(e2.expiry, 80_000.0, True, 2.0)]
    vols = {(e1.expiry, 85_000.0): 0.45, (e1.expiry, 75_000.0): 0.55, (e2.expiry, 80_000.0): 0.5}
    book = Book(options=legs)
    base_im, _ = pm2.net_margin(book, _state([e1, e2]), params, True, vols=vols)
    base_mm, _ = pm2.net_margin(book, _state([e1, e2]), params, False, vols=vols)
    low = _Expiry(expiry=e1.expiry, forward=e1.forward, svi=None, rate=0.04, vol_conf=0.5)
    im, _ = pm2.net_margin(book, _state([low, e2]), params, True, vols=vols)
    mm, _ = pm2.net_margin(book, _state([low, e2]), params, False, vols=vols)
    expected = (1 - 0.5) * O["confMargin"] * (1.5 + 0.5) * 80_000.0
    assert 0.5 < O["confThreshold"]
    assert base_im - im == pytest.approx(expected, rel=1e-12)
    assert mm == pytest.approx(base_mm, rel=1e-15)
    # a zero-amount leg is not held on chain: its expiry's low confidence must not matter
    ghost = _Expiry(expiry=ts + 5 * DAY, forward=80_050.0, svi=None, rate=0.04, vol_conf=0.1)
    book2 = Book(options=legs + [OptionLeg(ghost.expiry, 80_000.0, True, 0.0)])
    im2, _ = pm2.net_margin(book2, _state([e1, e2, ghost]), params, True, vols={**vols, (ghost.expiry, 80_000.0): 0.5})
    assert im2 == pytest.approx(base_im, rel=1e-15)
    # a perp with low confidence lowers the confidence of every held expiry (portfolio.minConfidence)
    st = _state([e1, e2], perp=80_000.0, perp_conf=0.3)
    im3, _ = pm2.net_margin(Book(options=legs, perp=0.1), st, params, True, vols=vols)
    im4, _ = pm2.net_margin(Book(options=legs, perp=0.1), _state([e1, e2], perp=80_000.0), params, True, vols=vols)
    cc = (1 - 0.3) * O["confMargin"] * (2.0 + 2.0 + 0.1) * 80_000.0
    assert im4 - im3 == pytest.approx(cc, rel=1e-12)


def test_discount_uses_non_negative_feed_rate():
    params = _today()
    ts = 1_780_000_000
    sec = 90 * DAY
    leg = OptionLeg(ts + sec, 90_000.0, True, 1.0)
    vols = {(ts + sec, 90_000.0): 0.6}
    out = {}
    for r in (-0.05, 0.0, 0.04):
        e = _Expiry(expiry=ts + sec, forward=80_500.0, svi=None, rate=r)
        out[r] = pm2.net_margin(Book(options=[leg]), _state([e]), params, True, vols=vols)
    assert out[-0.05] == out[0.0]
    from derive_surface.pricing import price
    tau = sec / YEAR
    assert out[0.04][1] == pytest.approx(math.exp(-0.04 * tau) * float(price(80_500.0, 90_000.0, tau, 0.6, 1)),
                                         rel=1e-12)


def test_duplicate_legs_are_merged_and_margin_is_homogeneous():
    params = _today()
    ts = 1_780_000_000
    e = _Expiry(expiry=ts + 20 * DAY, forward=80_200.0, svi=None, rate=0.03)
    vols = {(e.expiry, 85_000.0): 0.5, (e.expiry, 70_000.0): 0.7}
    one = Book(options=[OptionLeg(e.expiry, 85_000.0, True, -1.0), OptionLeg(e.expiry, 70_000.0, False, 0.4)])
    split = Book(options=[OptionLeg(e.expiry, 85_000.0, True, -0.25), OptionLeg(e.expiry, 70_000.0, False, 0.4),
                          OptionLeg(e.expiry, 85_000.0, True, -0.75)])
    st = _state([e])
    assert pm2.net_margin(split, st, params, True, vols=vols) == pytest.approx(
        pm2.net_margin(one, st, params, True, vols=vols), rel=1e-14)
    big = Book(options=[OptionLeg(l.expiry, l.strike, l.is_call, 3.7 * l.amount) for l in one.options])
    net1, mtm1 = pm2.net_margin(one, st, params, True, vols=vols)
    net2, mtm2 = pm2.net_margin(big, st, params, True, vols=vols)
    assert net2 == pytest.approx(3.7 * net1, rel=1e-12)
    assert mtm2 == pytest.approx(3.7 * mtm1, rel=1e-12)


def test_vols_default_to_the_svi_curve_of_the_expiry():
    params = _today()
    ts = 1_780_000_000
    svi = (0.01, 0.05, -0.2, 0.0, 0.2, 0.1)
    e = _Expiry(expiry=ts + 30 * DAY, forward=80_000.0, svi=svi, rate=0.03)
    book = Book(options=[OptionLeg(e.expiry, 84_000.0, True, -1.0)])
    got = pm2.net_margin(book, _state([e]), params, True)
    want = pm2.net_margin(book, _state([e]), params, True, vols={(e.expiry, 84_000.0): e.vol(84_000.0)})
    assert got == want


def test_parameter_schema_checks():
    params = _today()
    bad = json.loads(json.dumps(params))
    bad["VolShockParameters"]["dteFloor"] = 86_400 / 1e18  # dteFloor wrongly 1e18-scaled
    with pytest.raises(ValueError):
        pm2.net_margin(Book(), _state([]), bad, True)
    named = json.loads(json.dumps(params))
    for s in named["scenarios"]:
        s["volShock"] = ["None", "Up", "Down", "Linear", "Abs"][s["volShock"]]
    ts = 1_780_000_000
    e = _Expiry(expiry=ts + 30 * DAY, forward=80_000.0, svi=None, rate=0.03)
    book = Book(options=[OptionLeg(e.expiry, 84_000.0, True, -1.0)])
    vols = {(e.expiry, 84_000.0): 0.5}
    assert pm2.net_margin(book, _state([e]), named, True, vols=vols) == pm2.net_margin(
        book, _state([e]), params, True, vols=vols)


def test_empty_book_is_cash():
    params = _today()
    assert pm2.net_margin(Book(cash=250.0), _state([]), params, True) == (250.0, 250.0)
