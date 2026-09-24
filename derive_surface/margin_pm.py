"""Offline replica of the legacy portfolio margin (v2-core ``PMRM`` + ``PMRMLib``), one base currency per book.

Mirrors ``src/risk-managers/PMRMLib.sol`` (``addPrecomputes``, ``getMarginAndMarkToMarket``) and the portfolio
layout of ``PMRM._arrangePortfolio`` at commit 96796a6:

* per expiry the MtM is Black-76 on the forward with discount 1 (no discounting, no skew scenarios);
* spot shocks move only the variable forward portion ``F_s = var * shock + fixed``, vol shocks scale every option
  vol by ``1 + volRangeUp * (30d / max(sec, dteFloor))^p`` resp. ``max(0, 1 - volRangeDown * (...)^p)`` with
  ``p = shortTermPower`` up to 30 days and ``longTermPower`` beyond;
* a scenario PnL counts a positive shocked expiry value only times the static discount
  ``baseStaticDiscount * exp(-tau * (max(rate, 0) * rateMultScale + rateAddScale))`` (``rate`` = the legacy
  manager's own ``interestRateFeed``, a ``LyraRateFeedStatic`` that holds rate 0 at confidence 1 over the whole
  history: one ``RateUpdated`` at deploy, BTC 0x6fef... block 843076, ETH 0x30a6... block 843060, and no
  ``InterestRateFeedUpdated`` on either PMRM up to block 45131522; the engine therefore uses 0 by default and never
  reads ``ExpiryState.rate``, which carries the PM2 rate);
* ``minSPAN`` starts at the basis contingency ``sum_e min(up - mtm, down - mtm, 0) * (add + mult * tau)`` and takes
  the minimum over the scenarios from ``params["scenarios"]``; then the static contingencies (perp, base and naked
  shorts per strike) are subtracted; IM multiplies by ``imFactor`` (plus the peg-loss add-on) and subtracts the
  confidence contingency; MM uses factor 1.

``net = cash + V - R`` and ``mtm = cash + V`` exactly like ``PMRMLib.getMarginAndMarkToMarket``. Parameters use the
``IPMRMLib`` struct and field names: ``{"MarginParameters": {...}, "VolShockParameters": {...},
"BasisContingencyParameters": {...}, "OtherContingencyParameters": {...}, "scenarios": [{"spotShock": 1.1,
"volShock": 0|1|2}, ...], "maxExpiries": int}`` with values unscaled from 1e18 and ``dteFloor`` in seconds.
"""
from __future__ import annotations

from typing import List, Mapping, Optional, Tuple

import numpy as np

from .margin_sm import b76_prices, merged_options
from .p2types import YEAR, Book, MarketState

_VOL_DIR = {"none": 0, "up": 1, "down": 2}
_DAYS30 = 30.0 * 86400.0


class TooManyExpiries(ValueError):
    """``PMRM_TooManyExpiries``: the book holds more option expiries than ``maxExpiries``; PMRM reverts."""


def scenarios_of(params: Mapping) -> List[Tuple[float, int]]:
    """(spotShock, volShock) pairs; volShock 0 = None, 1 = Up, 2 = Down (``IPMRM.VolShockDirection``)."""
    out = []
    for s in params["scenarios"]:
        if isinstance(s, Mapping):
            shock, vol = s["spotShock"], s["volShock"]
        else:
            shock, vol = s[0], s[1]
        if isinstance(vol, str):
            vol = _VOL_DIR[vol.lower()]
        out.append((float(shock), int(vol)))
    if not out:
        raise ValueError("PMRML_InvalidGetMarginState: no scenarios")
    return out


def _dte_floor(params: Mapping) -> float:
    """``dteFloor`` in seconds (not 1e18-scaled on chain; the setter requires at least 864 s)."""
    d = float(params["VolShockParameters"]["dteFloor"])
    if d < 1.0:
        raise ValueError(f"VolShockParameters.dteFloor must be in seconds, got {d}")
    return d


def vol_shocks(sec, params: Mapping) -> Tuple[np.ndarray, np.ndarray]:
    """``_addVolShocks``: multiplicative (up, down) vol shock per expiry from seconds to expiry."""
    vs = params["VolShockParameters"]
    sec = np.asarray(sec, dtype=float)
    ratio = _DAYS30 / np.maximum(sec, _dte_floor(params))
    power = np.where(sec <= _DAYS30, float(vs["shortTermPower"]), float(vs["longTermPower"]))
    mult = ratio ** power
    up = 1.0 + float(vs["volRangeUp"]) * mult
    down = np.maximum(0.0, 1.0 - float(vs["volRangeDown"]) * mult)
    return up, down


def static_discount(sec, rate, params: Mapping) -> np.ndarray:
    """``_addStaticDiscount``: haircut applied to positive shocked expiry values."""
    mp = params["MarginParameters"]
    tau = np.asarray(sec, dtype=float) / YEAR
    shock_rfr = np.maximum(np.asarray(rate, dtype=float), 0.0) * float(mp["rateMultScale"]) + float(mp["rateAddScale"])
    return float(mp["baseStaticDiscount"]) * np.exp(-tau * shock_rfr)


def _conf_contingency(conf, amount, spot, params: Mapping):
    """``_getConfidenceContingency``: (1 - conf) * confMargin * amount * spot below ``confThreshold``."""
    oc = params["OtherContingencyParameters"]
    conf = np.asarray(conf, dtype=float)
    return np.where(conf < float(oc["confThreshold"]),
                    (1.0 - conf) * float(oc["confMargin"]) * np.asarray(amount, dtype=float) * spot, 0.0)


def _margin_factor(stable, params: Mapping, is_initial: bool):
    if not is_initial:
        return np.ones_like(np.asarray(stable, dtype=float))
    oc = params["OtherContingencyParameters"]
    stable = np.asarray(stable, dtype=float)
    thr = float(oc["pegLossThreshold"])
    return float(params["MarginParameters"]["imFactor"]) + np.where(stable < thr,
                                                                     (thr - stable) * float(oc["pegLossFactor"]), 0.0)


def _naked_shorts(strikes: np.ndarray, amounts: np.ndarray) -> float:
    """``_getOptionContingency``: calls and puts of one strike net against each other, max(-(c + p), 0)."""
    tot = 0.0
    for k in np.unique(strikes):
        tot += max(-float(amounts[strikes == k].sum()), 0.0)
    return tot


def net_margin(book: Book, state: MarketState, params: Mapping, is_initial: bool = True, *,
               vols: Optional[Mapping[Tuple[int, float], float]] = None, base: float = 0.0,
               rates: Optional[Mapping[int, float]] = None, rate_confs: Optional[Mapping[int, float]] = None,
               fwd_fixed: Optional[Mapping[int, float]] = None,
               strict_expiries: bool = False) -> Tuple[float, float]:
    """(net, mtm) of ``book`` under the legacy PMRM: net = cash + V - R, mtm = cash + V.

    ``vols`` optionally maps ``(expiry, strike)`` to the vol-feed value, otherwise the SVI curve of the expiry is
    used. The legacy rate feed is 0 at confidence 1 over the whole history, so the rate defaults to 0 and
    ``ExpiryState.rate`` (the PM2 rate) is ignored; ``rates`` / ``rate_confs`` override rate and confidence per
    expiry (only for reference cases). ``fwd_fixed`` is the settled forward portion of the last 30 minutes
    (default 0). ``base`` is base-asset collateral in units of the underlying. Legs of one instrument are netted
    first like ``SubAccounts``. ``strict_expiries=True`` raises :class:`TooManyExpiries` when more option expiries
    are held than ``params["maxExpiries"]`` (PMRM reverts); by default the limit is not enforced.
    """
    spot, stable = float(state.spot), float(state.stable)
    options = merged_options(book)
    held = sorted({leg.expiry for leg in options})
    if strict_expiries:
        limit = params.get("maxExpiries")
        if limit is None:
            raise ValueError("strict_expiries needs params['maxExpiries']")
        if len(held) > int(limit):
            raise TooManyExpiries(f"PMRM_TooManyExpiries: {len(held)} expiries held, maxExpiries = {int(limit)}")
    oc = params["OtherContingencyParameters"]
    bc = params["BasisContingencyParameters"]
    min_conf = float(state.spot_conf)
    perp_price = 0.0
    if book.perp != 0:
        perp_price = float(state.perp_price)
        min_conf = min(min_conf, float(state.perp_conf))
    perp_value = 0.0
    if book.perp != 0 and book.perp_entry is not None:
        perp_value = (perp_price - book.perp_entry) * book.perp
    base = float(base)
    if base < 0:
        raise ValueError("base collateral cannot be negative")
    base_value = base * spot / stable
    total_mtm = base_value + perp_value
    static = (abs(book.perp) * float(oc["perpPercent"]) + base * float(oc["basePercent"])) * spot
    conf_cont = float(_conf_contingency(min_conf, abs(book.perp) + base, spot, params))
    basis = 0.0
    expiries = []
    for expiry in held:
        legs = [leg for leg in options if leg.expiry == expiry]
        es = state.expiries[expiry]
        strikes = np.array([leg.strike for leg in legs], dtype=float)
        amounts = np.array([leg.amount for leg in legs], dtype=float)
        calls = np.array([leg.is_call for leg in legs], dtype=bool)
        sig = np.array([vols[(expiry, leg.strike)] if vols is not None and (expiry, leg.strike) in vols
                        else es.vol(leg.strike) for leg in legs], dtype=float)
        fixed = float((fwd_fixed or {}).get(expiry, 0.0))
        var = float(es.forward) - fixed
        rate = float((rates or {}).get(expiry, 0.0))
        rconf = float((rate_confs or {}).get(expiry, 1.0))
        econf = min(min_conf, float(es.fwd_conf), rconf, float(es.vol_conf))
        sec = float(max(expiry - state.ts, 0))

        def value(shock: float, vmult: float, strikes=strikes, amounts=amounts, calls=calls, sig=sig, var=var,
                  fixed=fixed, sec=sec) -> float:
            c, p = b76_prices(var * shock + fixed, strikes, sig * vmult, sec)
            return float((np.where(calls, c, p) * amounts).sum())

        mtm_e = value(1.0, 1.0)
        total_mtm += mtm_e
        up_e = value(float(bc["scenarioSpotUp"]), 1.0)
        dn_e = value(float(bc["scenarioSpotDown"]), 1.0)
        factor = float(bc["basisContAddFactor"]) + float(bc["basisContMultFactor"]) * sec / YEAR
        basis += min(up_e - mtm_e, dn_e - mtm_e, 0.0) * factor
        v_up, v_dn = vol_shocks(sec, params)
        sd = float(static_discount(sec, rate, params))
        static += _naked_shorts(strikes, amounts) * float(oc["optionPercent"]) * spot
        conf_cont += float(_conf_contingency(econf, float(np.abs(amounts).sum()), spot, params))
        expiries.append((value, mtm_e, float(v_up), float(v_dn), sd))
    min_span = basis
    for shock, vdir in scenarios_of(params):
        pnl = 0.0
        for value, mtm_e, v_up, v_dn, sd in expiries:
            shocked = value(shock, v_up if vdir == 1 else v_dn if vdir == 2 else 1.0)
            pnl += (shocked * sd if shocked > 0 else shocked) - mtm_e
        pnl += base * spot * shock / stable + book.perp * (shock - 1.0) * perp_price - base_value
        min_span = min(min_span, pnl)
    min_span -= static
    if is_initial:
        min_span = min_span * float(_margin_factor(stable, params, True)) - conf_cont
    return min_span + total_mtm + book.cash, total_mtm + book.cash


def requirement(book: Book, state: MarketState, params: Mapping, is_initial: bool = True, **kw) -> float:
    """R = mtm - net."""
    net, mtm = net_margin(book, state, params, is_initial, **kw)
    return mtm - net


def single(arrays: Mapping[str, np.ndarray], params: Mapping, is_initial: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """(net, mtm) for many one-option books with cash 0 under the legacy PMRM, vectorised over contracts.

    ``arrays``: equally long 1-D arrays ``spot, forward, sigma, tau, strike, is_call, amount, vol_conf, fwd_conf,
    spot_conf``; optional ``stable`` (1), ``rate_pm`` (the legacy rate feed, default 0), ``rate_conf`` (1) and
    ``fwd_fixed`` (0). A ``rate`` column (the PM2 rate of ``FeedHistory.bulk_state``) is ignored. Identical to
    :func:`net_margin` on the corresponding book.
    """
    a = arrays
    spot = np.asarray(a["spot"], dtype=float)
    n = spot.shape[0]
    one = np.ones(n)
    forward = np.asarray(a["forward"], dtype=float)
    sigma = np.asarray(a["sigma"], dtype=float)
    sec = np.maximum(np.asarray(a["tau"], dtype=float), 0.0) * YEAR  # expired: secToExpiry = 0
    strike = np.asarray(a["strike"], dtype=float)
    is_call = np.asarray(a["is_call"], dtype=bool)
    q = np.asarray(a["amount"], dtype=float)
    fixed = np.asarray(a.get("fwd_fixed", np.zeros(n)), dtype=float)
    var = forward - fixed
    bc = params["BasisContingencyParameters"]
    oc = params["OtherContingencyParameters"]

    def value(shock: float, vmult) -> np.ndarray:
        c, p = b76_prices(var * shock + fixed, strike, sigma * vmult, sec)
        return np.where(is_call, c, p) * q

    mtm = value(1.0, 1.0)
    up = value(float(bc["scenarioSpotUp"]), 1.0)
    dn = value(float(bc["scenarioSpotDown"]), 1.0)
    factor = float(bc["basisContAddFactor"]) + float(bc["basisContMultFactor"]) * sec / YEAR
    min_span = np.minimum(np.minimum(up - mtm, dn - mtm), 0.0) * factor
    v_up, v_dn = vol_shocks(sec, params)
    sd = static_discount(sec, np.asarray(a.get("rate_pm", np.zeros(n)), dtype=float), params)
    for shock, vdir in scenarios_of(params):
        s = value(shock, v_up if vdir == 1 else v_dn if vdir == 2 else 1.0)
        min_span = np.minimum(min_span, np.where(s > 0, s * sd, s) - mtm)
    min_span = min_span - np.maximum(-q, 0.0) * float(oc["optionPercent"]) * spot
    if is_initial:
        conf = np.minimum.reduce([np.asarray(a.get(k, one), dtype=float)
                                  for k in ("spot_conf", "fwd_conf", "rate_conf", "vol_conf")])
        min_span = min_span * _margin_factor(np.asarray(a.get("stable", one), dtype=float), params, True) \
            - _conf_contingency(conf, np.abs(q), spot, params)
    return min_span + mtm, mtm


__all__ = ["TooManyExpiries", "net_margin", "requirement", "scenarios_of", "single", "static_discount",
           "vol_shocks"]
