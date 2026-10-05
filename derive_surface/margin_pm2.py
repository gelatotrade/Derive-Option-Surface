"""Offline replica of Derive's portfolio margin engine PM2 (``PMRMLib_2`` + ``PMRM_2._arrangePortfolio``).

Reference: v2-core commit 96796a6, ``src/risk-managers/PMRMLib_2.sol`` and ``PMRM_2.sol`` (line numbers below refer
to these files). The engine returns net margin ``net = cash + V - R`` and ``mtm = cash + V`` exactly like
``PMRMLib_2.getMarginAndMarkToMarket``; the requirement is ``R = mtm - net``.

Mechanics (all in floating point; the contract works in 1e18 fixed point, the difference is ~1e-15 relative):

* Each held expiry e has a mark-to-market ``M_e = sum_i q_i * B76(F_e, K_i, sigma_i, tau_e, D_e)`` with the discount
  ``D_e = exp(-max(r_e, 0) * tau_e)`` from the rate feed and ``sigma_i`` the vol feed value at the strike.
* A scenario (spot shock s, vol direction, dampening d) re-prices every expiry: the variable forward portion is
  shocked (``F = F_var * s + F_fixed``), vol shocks and the skew shock act multiplicatively on ``sigma_i``. The shocked
  expiry value is scaled by the static discount (``staticDiscountPos`` if >= 0, else ``staticDiscountNeg``) and its
  PnL against ``M_e`` is dampened; skew scenarios use ``-|PnL|`` per expiry. Perps add ``q (s - 1) P d``.
* ``minSPAN = min(basis contingency, min over scenarios)``; ``R = -minSPAN * factor + MM contingencies
  (+ IM contingencies for IM)``, with the peg-loss add-on to the IM factor.
* Contingencies: perps ``|q| S pct``, naked shorts per strike ``max(-(c_K + p_K), 0) S pct``, the oracle
  contingency ``(1 - c) confMargin notional`` when the minimum confidence c of a held expiry (forward, rate, vol of
  the held strikes, spot, perp if held) is below ``confThreshold``, and collateral haircuts.

Parameters use the A2 schema: Solidity struct names and field names of ``IPMRMLib_2`` as keys, values as floats
(1e18 scaling removed; ``VolShockParameters.dteFloor`` in seconds), plus ``scenarios`` (list of dicts with
``spotShock``, ``volShock`` in 0..4 or ``None|Up|Down|Linear|Abs``, ``dampeningFactor``) and ``maxExpiries``
(not enforced here; the chain reverts beyond it).

Optional feed fields read from each :class:`~derive_surface.p2types.ExpiryState` when present: ``fwd_fixed`` (the
fixed forward portion inside the 30 min settlement window, default 0) and ``rate_conf`` (rate feed confidence,
default 1).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
from scipy.special import ndtr

from .p2types import YEAR, Book, MarketState

DAY = 86_400.0
THIRTY_DAYS = 30.0 * DAY
MAX_TOTAL_VOL = 24.0      # Black76.sol: above sigma sqrt(tau) = 24 the standard call price is 1
CHUNK = 32_768            # rows per block in single(); bounds memory at ~36 x CHUNK floats per temporary

VOL_SHOCK = {"none": 0, "up": 1, "down": 2, "linear": 3, "abs": 4}   # IPMRM_2.VolShockDirection

SINGLE_KEYS = ("spot", "forward", "sigma", "tau", "rate", "strike", "is_call", "amount", "vol_conf", "fwd_conf",
               "spot_conf")
SINGLE_DEFAULTS = {"stable": 1.0, "rate_conf": 1.0, "fwd_fixed": 0.0, "cash": 0.0}


@dataclass(frozen=True)
class Collateral:
    """Non-cash collateral held in a PM2 account (``IPMRM_2.CollateralHoldings`` plus its lib parameters)."""

    amount: float
    price: float
    confidence: float = 1.0
    is_risk_cancelling: bool = False
    MMHaircut: float = 0.0
    IMHaircut: float = 0.0


class _Params:
    """Parameter dict (A2 schema) flattened into floats and numpy arrays."""

    def __init__(self, params: Mapping):
        m = params["MarginParameters"]
        v = params["VolShockParameters"]
        b = params["BasisContingencyParameters"]
        o = params["OtherContingencyParameters"]
        k = params["SkewShockParameters"]
        self.im, self.mm = float(m["imFactor"]), float(m["mmFactor"])
        self.s_mult, self.l_mult = float(m["shortRateMultScale"]), float(m["longRateMultScale"])
        self.s_add, self.l_add = float(m["shortRateAddScale"]), float(m["longRateAddScale"])
        self.s_base, self.l_base = float(m["shortBaseStaticDiscount"]), float(m["longBaseStaticDiscount"])
        self.v_up, self.v_down = float(v["volRangeUp"]), float(v["volRangeDown"])
        self.st_pow, self.lt_pow = float(v["shortTermPower"]), float(v["longTermPower"])
        self.dte_floor = float(v["dteFloor"])
        if 0.0 < self.dte_floor < 1.0:
            raise ValueError(f"VolShockParameters.dteFloor must be in seconds (got {self.dte_floor!r}; 1e18-scaled?)")
        self.min_vol_up = float(v["minVolUpShock"])
        self.b_up, self.b_down = float(b["scenarioSpotUp"]), float(b["scenarioSpotDown"])
        self.b_add, self.b_mult = float(b["basisContAddFactor"]), float(b["basisContMultFactor"])
        self.peg_thr, self.peg_fac = float(o["pegLossThreshold"]), float(o["pegLossFactor"])
        self.conf_thr, self.conf_margin = float(o["confThreshold"]), float(o["confMargin"])
        self.mm_perp, self.im_perp = float(o["MMPerpPercent"]), float(o["IMPerpPercent"])
        self.mm_opt, self.im_opt = float(o["MMOptionPercent"]), float(o["IMOptionPercent"])
        self.lin_cap, self.abs_cap = float(k["linearBaseCap"]), float(k["absBaseCap"])
        self.lin_c, self.abs_c = float(k["linearCBase"]), float(k["absCBase"])
        self.min_kstar, self.width = float(k["minKStar"]), float(k["widthScale"])
        self.vol_static, self.vol_scale = float(k["volParamStatic"]), float(k["volParamScale"])
        scen = list(params["scenarios"])
        if not scen:
            raise ValueError("PMRMLib_2 needs at least one scenario (PMRML2_InvalidGetMarginState)")
        self.shock = np.array([float(s["spotShock"]) for s in scen])
        self.dirs = np.array([_vol_dir(s["volShock"]) for s in scen], dtype=int)
        self.damp = np.array([float(s["dampeningFactor"]) for s in scen])
        self.is_skew = self.dirs >= 3
        # pricing rows: 0 = unshocked mtm, 1/2 = basis contingency up/down, 3.. = margin scenarios
        self.row_shock = np.concatenate([[1.0, self.b_up, self.b_down], self.shock])
        self.row_dir = np.concatenate([[0, 0, 0], self.dirs]).astype(int)

    def factor(self, is_initial: bool, stable) -> np.ndarray:
        """PMRMLib_2.sol:148-154: IM/MM factor plus the peg-loss add-on for IM."""
        stable = np.asarray(stable, float)
        if not is_initial:
            return np.full(stable.shape, self.mm)
        return self.im + np.where(stable < self.peg_thr, (self.peg_thr - stable) * self.peg_fac, 0.0)

    def conf_cont(self, conf, notional) -> np.ndarray:
        """PMRMLib_2.sol:444-449."""
        conf = np.asarray(conf, float)
        return np.where(conf < self.conf_thr, (1.0 - conf) * self.conf_margin * np.asarray(notional, float), 0.0)


def _vol_dir(x) -> int:
    if isinstance(x, str):
        return VOL_SHOCK[x.strip().lower()]
    i = int(x)
    if not 0 <= i <= 4:
        raise ValueError(f"volShock must be 0..4, got {x!r}")
    return i


# --------------------------------------------------------------------------------------------------------------
# Pricing
# --------------------------------------------------------------------------------------------------------------
def _b76(sec, vol, fwd, strike, disc, is_call) -> np.ndarray:
    """lyra-utils ``Black76.prices`` (Black76.sol:63-101, 131-172), vectorised with broadcasting."""
    tv = vol * np.sqrt(sec / YEAR)
    fd = fwd * disc
    kd = strike * disc
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        m = strike / fwd
        tvs = np.where(tv > 0.0, tv, 1e-18)                      # totalVol == 0 -> 1 wei
        k = np.log(np.maximum(m, 1e-18))                          # moneyness == 0 -> 1 wei
        d1 = (0.5 * tvs * tvs - k) / tvs
        c = ndtr(d1) - m * ndtr(d1 - tvs)
        c = np.where(tv >= MAX_TOTAL_VOL, 1.0, np.maximum(c, 0.0))
        p = np.maximum(c + m - 1.0, 0.0)                          # _standardPutFromCall
        call = np.minimum(c * fd, fd)
        put = np.minimum(p * fd, kd)
    call = np.where(strike == 0.0, fd, np.where(fwd == 0.0, 0.0, call))
    put = np.where(strike == 0.0, 0.0, np.where(fwd == 0.0, kd, put))
    return np.where(is_call, call, put)


def _expiry_factors(P: _Params, sec, rate):
    """Discount, static discounts (PMRMLib_2.sol:395-411) and vol shock multipliers (:413-422) per expiry."""
    r = np.maximum(rate, 0.0)                                     # PMRM_2.sol:356-357 (rate >= 0)
    tau = sec / YEAR
    disc = np.exp(-r * tau)                                       # PMRM_2.sol:376
    dpos = P.l_base * np.exp(-tau * (r * P.l_mult + P.l_add))
    dneg = np.minimum(1.0 / disc, P.s_base / np.exp(-tau * (r * P.s_mult + P.s_add)))
    with np.errstate(divide="ignore"):
        t30 = THIRTY_DAYS / np.maximum(sec, P.dte_floor)
    ms = t30 ** np.where(sec <= THIRTY_DAYS, P.st_pow, P.lt_pow)
    vs_up = 1.0 + P.v_up * ms
    vs_down = np.maximum(0.0, 1.0 - P.v_down * ms)
    return tau, disc, dpos, dneg, vs_up, vs_down


def _leg_prices(P: _Params, sec, tau, f_var, f_fix, sigma, strike, is_call, disc, vs_up, vs_down) -> np.ndarray:
    """Option values (rows x legs) for the unshocked, basis and scenario rows; leg inputs are 1-D arrays."""
    # vol per direction (None, Up, Down, Linear, Abs); shocks act on the vol at the strike
    vol_up = np.maximum(P.min_vol_up, sigma * vs_up)             # :246-248, :260
    vol_down = np.maximum(0.0, sigma * vs_down)                   # :249-250, :260 (minVol = 0)
    f_now = f_var + f_fix
    st = np.sqrt(tau)                                             # :296
    kstar = np.maximum(P.min_kstar, st * P.width * (P.vol_static + st * P.vol_scale))   # :278-282
    with np.errstate(divide="ignore", invalid="ignore"):
        k = np.log(strike / f_now)                                # :316

        def skew_vol(kk, cap):
            mult = 1.0 + np.where(kk >= 0.0, np.minimum(cap, kk * cap / kstar), np.maximum(-cap, kk * cap / kstar))
            return sigma * np.maximum(mult, 0.0)                  # :319-326

        vol_lin = skew_vol(k, P.lin_c * st + P.lin_cap)           # :298-300
        vol_abs = skew_vol(np.abs(k), P.abs_c * st + P.abs_cap)
    vols = np.stack([sigma, vol_up, vol_down, vol_lin, vol_abs])  # (5, L)
    vol = vols[P.row_dir]                                         # (R, L)
    skew_row = (P.row_dir >= 3)[:, None]
    fwd = np.where(skew_row, f_now[None, :], f_var[None, :] * P.row_shock[:, None] + f_fix[None, :])  # :254-255, :294
    return _b76(sec[None, :], vol, fwd, strike[None, :], disc[None, :], is_call[None, :])


def _span(P: _Params, M: np.ndarray, tau, dpos, dneg):
    """Per expiry: unshocked MtM, basis contingency (:428-442) and scenario PnL (:178-219) from expiry values M."""
    m0, m_up, m_dn, ms = M[0], M[1], M[2], M[3:]
    basis = np.minimum(np.minimum(m_up - m0, m_dn - m0), 0.0) * (P.b_add + P.b_mult * tau)
    shocked = np.where(ms >= 0.0, ms * dpos, ms * dneg)           # :205-207
    ep = (shocked - m0) * P.damp[:, None]                          # :209
    ep = np.where(P.is_skew[:, None], -np.abs(ep), ep)            # :213-218
    return m0, basis, ep


# --------------------------------------------------------------------------------------------------------------
# Books
# --------------------------------------------------------------------------------------------------------------
def _merged_legs(book: Book) -> List[Tuple[int, float, bool, float]]:
    """One balance per (expiry, strike, is_call) like SubAccounts, sorted; zero balances are not held."""
    agg: Dict[Tuple[int, float, bool], float] = {}
    for leg in book.options:
        key = (int(leg.expiry), float(leg.strike), bool(leg.is_call))
        agg[key] = agg.get(key, 0.0) + float(leg.amount)
    return [(e, k, c, a) for (e, k, c), a in sorted(agg.items()) if a != 0.0]


def margin_details(book: Book, state: MarketState, params: Mapping, is_initial: bool = True, *,
                   vols: Optional[Mapping[Tuple[int, float], float]] = None,
                   collaterals: Sequence[Collateral] = ()) -> dict:
    """Full PM2 evaluation of one book (one currency). ``vols`` overrides the SVI vol per (expiry, strike)."""
    P = _Params(params)
    legs = _merged_legs(book)
    spot = float(state.spot)
    qp = float(book.perp)
    perp_price = float(state.perp_price) if qp != 0.0 else 0.0
    min_conf = float(state.spot_conf) if qp == 0.0 else min(float(state.spot_conf), float(state.perp_conf))
    perp_value = 0.0
    if qp != 0.0 and book.perp_entry is not None:
        perp_value = qp * (perp_price - float(book.perp_entry))

    # perps (PMRMLib_2.sol:350-356)
    pn = abs(qp) * spot
    mm_c = pn * P.mm_perp
    im_c = pn * P.im_perp + float(P.conf_cont(min_conf, pn))
    total_mtm = perp_value
    pnl = qp * (P.shock - 1.0) * perp_price * P.damp            # :173-175, :336-342
    basis_total = 0.0
    expiry_mtm: Dict[int, float] = {}

    if legs:
        exps = sorted({e for e, _, _, _ in legs})
        eidx = {e: i for i, e in enumerate(exps)}
        est = [state.expiries[e] for e in exps]
        sec_e = np.array([max(e - int(state.ts), 0) for e in exps], dtype=float)
        rate_e = np.array([float(s.rate) for s in est])
        tau_e, disc_e, dpos_e, dneg_e, vsu_e, vsd_e = _expiry_factors(P, sec_e, rate_e)
        fwd_e = np.array([float(s.forward) for s in est])
        fix_e = np.array([float(getattr(s, "fwd_fixed", 0.0) or 0.0) for s in est])
        g = np.array([eidx[e] for e, _, _, _ in legs])
        strike = np.array([k for _, k, _, _ in legs], dtype=float)
        is_call = np.array([c for _, _, c, _ in legs], dtype=bool)
        q = np.array([a for _, _, _, a in legs], dtype=float)
        sigma = np.array([_leg_vol(state, vols, e, k) for e, k, _, _ in legs], dtype=float)
        prices = _leg_prices(P, sec_e[g], tau_e[g], fwd_e[g] - fix_e[g], fix_e[g], sigma, strike, is_call,
                             disc_e[g], vsu_e[g], vsd_e[g])
        starts = np.flatnonzero(np.r_[True, g[1:] != g[:-1]])    # legs are sorted by expiry
        M = np.add.reduceat(prices * q[None, :], starts, axis=1)  # (rows, expiries)
        m0, basis, ep = _span(P, M, tau_e, dpos_e, dneg_e)
        total_mtm += float(m0.sum())                              # :364-365
        basis_total = float(basis.sum())
        pnl = pnl + ep.sum(axis=1)
        expiry_mtm = {e: float(m0[i]) for i, e in enumerate(exps)}

        # naked shorts per strike (:451-495) and oracle contingency per expiry (:361, :373-374, PMRM_2.sol:364, :409)
        per_strike: Dict[Tuple[int, float], float] = {}
        net_opts = np.zeros(len(exps))
        for (e, k, _c, a) in legs:
            per_strike[(e, k)] = per_strike.get((e, k), 0.0) + a
            net_opts[eidx[e]] += abs(a)
        naked = sum(max(-v, 0.0) for v in per_strike.values())
        mm_c += naked * spot * P.mm_opt
        im_c += naked * spot * P.im_opt
        for i, s in enumerate(est):
            conf = min(min_conf, float(s.fwd_conf), float(getattr(s, "rate_conf", 1.0)), float(s.vol_conf))
            im_c += float(P.conf_cont(conf, net_opts[i] * spot))

    # collaterals (PMRM_2.sol:423-429, PMRMLib_2.sol:377-388, :222-233)
    stable = float(state.stable)
    for c in collaterals:
        value = float(c.amount) * float(c.price) / stable
        total_mtm += value
        mm_c += value * float(c.MMHaircut)
        im_c += value * float(c.IMHaircut) + float(P.conf_cont(min(float(c.confidence), float(state.spot_conf)), value))
        if c.is_risk_cancelling:
            pnl = pnl + value * (P.shock - 1.0) * P.damp

    # getMarginAndMarkToMarket (:127-164): minSPAN starts at the basis contingency, strict < keeps the first minimum
    min_span, worst = basis_total, len(pnl)
    if np.isnan(pnl).any() or np.isnan(min_span):
        min_span, worst = float("nan"), -1
    else:
        j = int(np.argmin(pnl))
        if pnl[j] < min_span:
            min_span, worst = float(pnl[j]), j
    factor = float(P.factor(is_initial, stable))
    req = -min_span * factor + mm_c + (im_c if is_initial else 0.0)
    mtm = total_mtm + float(book.cash)
    return {"net": mtm - req, "mtm": mtm, "requirement": req, "V": total_mtm, "minSPAN": min_span, "worst": worst,
            "basis": basis_total, "MMContingency": mm_c, "IMContingency": im_c, "factor": factor,
            "scenario_pnl": pnl, "expiry_mtm": expiry_mtm}


def _leg_vol(state: MarketState, vols, expiry: int, strike: float) -> float:
    if vols is not None:
        v = vols.get((expiry, strike))
        if v is not None:
            return float(v)
    return state.expiries[expiry].vol(strike)


def net_margin(book: Book, state: MarketState, params: Mapping, is_initial: bool = True, *,
               vols: Optional[Mapping[Tuple[int, float], float]] = None,
               collaterals: Sequence[Collateral] = ()) -> Tuple[float, float]:
    """(net, mtm) with net = cash + V - R and mtm = cash + V, as ``PMRMLib_2.getMarginAndMarkToMarket``."""
    d = margin_details(book, state, params, is_initial, vols=vols, collaterals=collaterals)
    return d["net"], d["mtm"]


def requirement(book: Book, state: MarketState, params: Mapping, is_initial: bool = True, *,
                vols: Optional[Mapping[Tuple[int, float], float]] = None,
                collaterals: Sequence[Collateral] = ()) -> float:
    """R = mtm - net."""
    return margin_details(book, state, params, is_initial, vols=vols, collaterals=collaterals)["requirement"]


# --------------------------------------------------------------------------------------------------------------
# Many single-contract books at once
# --------------------------------------------------------------------------------------------------------------
def single(arrays: Mapping, params: Mapping, is_initial: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """(net, mtm) for many one-leg books, each with its own market state; no perp, no collateral.

    ``arrays`` holds equally long 1-D arrays (scalars broadcast) with the keys ``spot, forward, sigma, tau, rate,
    strike, is_call, amount, vol_conf, fwd_conf, spot_conf``; optional ``stable, rate_conf, fwd_fixed, cash``
    (defaults 1, 1, 0, 0). ``tau`` is in years (seconds / (365 * 86400)), ``sigma`` the vol feed value at the
    strike, ``rate`` the raw feed rate (clipped at 0 like PMRM_2), ``amount`` in contracts (positive = long).
    """
    missing = [k for k in SINGLE_KEYS if k not in arrays]
    if missing:
        raise KeyError(f"single(): missing keys {missing}")
    P = _Params(params)
    cols = {k: arrays[k] for k in SINGLE_KEYS}
    for k, v in SINGLE_DEFAULTS.items():
        cols[k] = arrays.get(k, v)
    names = list(cols)
    bc = np.broadcast_arrays(*(np.asarray(cols[k]) for k in names))
    cols = {k: np.ravel(v) for k, v in zip(names, bc)}
    n = cols["spot"].shape[0]
    net = np.empty(n)
    mtm = np.empty(n)
    for lo in range(0, n, CHUNK):
        sl = slice(lo, min(lo + CHUNK, n))
        net[sl], mtm[sl] = _single_block(P, {k: v[sl] for k, v in cols.items()}, is_initial)
    return net, mtm


def _single_block(P: _Params, c: Mapping[str, np.ndarray], is_initial: bool):
    f = lambda k: np.asarray(c[k], dtype=float)  # noqa: E731
    spot, q = f("spot"), f("amount")
    # integer seconds as on chain; rounding removes the float noise of tau * YEAR at the 30-day switch
    sec = np.round(np.maximum(f("tau"), 0.0) * YEAR, 6)
    tau, disc, dpos, dneg, vs_up, vs_down = _expiry_factors(P, sec, f("rate"))
    f_fix = f("fwd_fixed")
    prices = _leg_prices(P, sec, tau, f("forward") - f_fix, f_fix, f("sigma"), f("strike"),
                         np.asarray(c["is_call"], dtype=bool), disc, vs_up, vs_down)
    m0, basis, ep = _span(P, prices * q[None, :], tau, dpos, dneg)
    min_span = np.minimum(basis, ep.min(axis=0))
    notional = np.abs(q) * spot
    naked = np.maximum(-q, 0.0) * spot
    conf = np.minimum.reduce([f("spot_conf"), f("fwd_conf"), f("rate_conf"), f("vol_conf")])
    mm_c = naked * P.mm_opt
    req = -min_span * P.factor(is_initial, f("stable")) + mm_c
    if is_initial:
        req = req + naked * P.im_opt + P.conf_cont(conf, notional)
    mtm = f("cash") + m0
    return mtm - req, mtm
