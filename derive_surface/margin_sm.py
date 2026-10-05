"""Offline replica of the v2-core ``StandardManager`` (SM) margin, one market (base currency) at a time.

Mirrors ``src/risk-managers/StandardManager.sol`` at commit 96796a6 (line numbers below refer to that file) together
with the portfolio layout of ``SRMPortfolioViewer.arrangeSRMPortfolio``:

* options are margined in isolation per strike (``_getIsolatedMargin``, :706-803); a long option has no margin;
* per expiry the better of the summed isolated margins and the max-loss margin is used, the max loss being the
  worst settlement payoff on the grid {0} u {all strikes of the expiry} plus ``unpaired*Scale * F * netCalls`` when
  the expiry is net short calls (:561-593, :811-819); expiries are added up, so SM is not convex;
* the mark-to-market is Black-76 on the forward with discount 1 (:840-858);
* perps: ``-|q| * perpPrice * (im|mm)PerpReq`` plus the unrealised PnL (:442-469, :422-434);
* base collateral: ``+ q * S * marginFactor`` (times ``IMScale`` for IM), MtM ``q * S / stable`` (:519-551);
* IM only: oracle contingencies for perp, option expiry and base when the minimum feed confidence falls below the
  threshold, and the stable-coin depeg penalty on ``|perp| + all shorts`` (:383-394, :412-416, :463-468, :503-512).

``net = cash + V - R`` exactly like ``getMarginAndMarkToMarket`` and ``public/get_margin``; the second return value
is ``mtm = cash + V``. Parameters use the v2-core struct and field names (``IStandardManager``):
``{"OptionMarginParams": {...}, "PerpMarginRequirements": {...}, "BaseMarginParams": {...},
"OracleContingencyParams": {...}, "DepegParams": {...}}`` with values unscaled from 1e18.
"""
from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Tuple

import numpy as np
from scipy.special import ndtr

from .p2types import YEAR, Book, MarketState, OptionLeg

# SRM market ids on Chain 957 (SRM.assetDetails(option).marketId)
MARKET_ID = {"ETH": 1, "BTC": 2, "HYPE": 48}

_MAX_TOTAL_VOL = 24.0  # lyra-utils Black76.MAX_TOTAL_VOL
_WEI = 1e-18


def b76_prices(forward, strike, sigma, sec, discount=1.0) -> Tuple[np.ndarray, np.ndarray]:
    """``lyra-utils`` ``Black76.prices`` in floating point, vectorised: (call, put) per unit.

    ``sec`` is the time to expiry in seconds (annualised with 365 days); zero time or zero vol gives intrinsic value
    on the forward exactly like the contract (total vol and moneyness are floored at one wei, prices capped at the
    discounted forward and strike).
    """
    F, K, sig, s, D = np.broadcast_arrays(*(np.asarray(x, dtype=float)
                                            for x in (forward, strike, sigma, sec, discount)))
    tv = sig * np.sqrt(np.maximum(s, 0.0) / YEAR)
    fD = F * D
    kD = K * D
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        m = np.where(F > 0, K / np.where(F > 0, F, 1.0), 0.0)
        tvs = np.where(tv > 0, tv, _WEI)
        ms = np.where(m > 0, m, _WEI)
        d1 = (0.5 * tvs * tvs - np.log(ms)) / tvs
        d2 = d1 - tvs
        c = ndtr(d1) - ms * ndtr(d2)
    c = np.where(c > 0, c, 0.0)
    c = np.where(tv >= _MAX_TOTAL_VOL, 1.0, c)
    p = np.where(c + m >= 1.0, c + m - 1.0, 0.0)
    call = np.minimum(c * fD, fD)
    put = np.minimum(p * fD, kD)
    call = np.where(K == 0, fD, np.where(F == 0, 0.0, call))
    put = np.where(K == 0, 0.0, np.where(F == 0, kD, put))
    return call, put


def merged_options(book: Book) -> List[OptionLeg]:
    """One leg per ``(expiry, strike, is_call)`` like ``SubAccounts`` (one balance per subId), sorted; zero balances
    are dropped because the chain does not hold them (they count neither as position nor as expiry)."""
    agg: Dict[Tuple[int, float, bool], float] = {}
    for leg in book.options:
        key = (int(leg.expiry), float(leg.strike), bool(leg.is_call))
        agg[key] = agg.get(key, 0.0) + float(leg.amount)
    return [OptionLeg(e, k, c, q) for (e, k, c), q in sorted(agg.items()) if q != 0.0]


def _prm(params: Mapping, struct: str, field: str) -> float:
    return float(params[struct][field])


def _im_multiplier(otm, params: Mapping):
    """``imMultiplier`` of :756-760 / :795-798: maxSpotReq - otmRatio, floored at minSpotReq."""
    mx = _prm(params, "OptionMarginParams", "maxSpotReq")
    mn = _prm(params, "OptionMarginParams", "minSpotReq")
    return np.where((mx > otm) & (mx - otm > mn), mx - otm, mn)


def isolated_margin(spot, forward, sigma, tau, strike, is_call, amount, params: Mapping, is_initial: bool = True):
    """``StandardManager._getIsolatedMargin`` (vectorised): (margin <= 0, markToMarket) per position.

    ``tau`` in years (365-day), ``amount`` in contracts (negative = short). The margin of a short already contains
    its (negative) mark-to-market; a long position has margin 0.
    """
    spot, forward, sigma, tau, strike, amount = (np.asarray(x, dtype=float) for x in
                                                 (spot, forward, sigma, tau, strike, amount))
    is_call = np.asarray(is_call, dtype=bool)
    call, put = b76_prices(forward, strike, sigma, tau * YEAR)
    mtm = np.where(is_call, call, put) * amount
    om = params["OptionMarginParams"]
    mm_put = np.minimum(float(om["mmPutSpotReq"]) * spot * amount, float(om["MMPutMtMReq"]) * mtm) + mtm
    if is_initial:
        with np.errstate(divide="ignore", invalid="ignore"):
            otm_c = np.where(strike > spot, (strike - spot) / spot, 0.0)
            otm_p = np.where(spot > strike, (spot - strike) / spot, 0.0)
        m_call = _im_multiplier(otm_c, params) * spot * amount + mtm
        m_put = np.minimum(_im_multiplier(otm_p, params) * spot * amount + mtm, mm_put * float(om["mmOffsetScale"]))
    else:
        m_call = mtm + float(om["mmCallSpotReq"]) * spot * amount
        m_put = mm_put
    margin = np.where(amount < 0, np.where(is_call, m_call, m_put), 0.0)
    return margin, mtm


def _depeg_multiplier(stable, params: Mapping, is_initial: bool):
    """``_getDepegMultiplier`` (:387-394): 0 for MM or when the stable price is at or above the threshold."""
    stable = np.asarray(stable, dtype=float)
    if not is_initial:
        return np.zeros_like(stable)
    thr = _prm(params, "DepegParams", "threshold")
    return np.where(stable < thr, (thr - stable) * _prm(params, "DepegParams", "depegFactor"), 0.0)


def _contingency(conf, threshold: float, factor: float):
    """Oracle contingency factor ``(1 - conf) * OCFactor`` when ``threshold != 0`` and ``conf < threshold``."""
    conf = np.asarray(conf, dtype=float)
    if threshold == 0:
        return np.zeros_like(conf)
    return np.where(conf < threshold, (1.0 - conf) * factor, 0.0)


def _settlement_value(strikes: np.ndarray, amounts: np.ndarray, calls: np.ndarray, price: float) -> float:
    diff = price - strikes
    v = np.where(calls & (diff > 0), diff * amounts, np.where(~calls & (diff < 0), -diff * amounts, 0.0))
    return float(v.sum())


def _expiry_margin(strikes, calls, amounts, vols, spot, forward, sec, conf, params, is_initial) -> Tuple[float, float]:
    """One ``ExpiryHolding``: (max(isolated, max loss) - option contingency, mtm)."""
    strikes = np.asarray(strikes, dtype=float)
    calls = np.asarray(calls, dtype=bool)
    amounts = np.asarray(amounts, dtype=float)
    iso, mtm = isolated_margin(spot, forward, vols, sec / YEAR, strikes, calls, amounts, params, is_initial)
    max_loss = min(_settlement_value(strikes, amounts, calls, 0.0), 0.0)
    for k in strikes:
        max_loss = min(max_loss, min(_settlement_value(strikes, amounts, calls, float(k)), 0.0))
    net_calls = float(amounts[calls].sum())
    if net_calls < 0:
        scale = _prm(params, "OptionMarginParams", "unpairedIMScale" if is_initial else "unpairedMMScale")
        max_loss += scale * forward * net_calls
    margin = max(float(iso.sum()), max_loss)
    if is_initial:
        oc = params["OracleContingencyParams"]
        shorts = float(-amounts[amounts < 0].sum())
        margin -= float(_contingency(conf, float(oc["optionThreshold"]), float(oc["OCFactor"]))) * spot * shorts
    return margin, float(mtm.sum())


def _perp_margin(q: float, perp_price: float, perp_conf: float, spot: float, spot_conf: float, params, is_initial):
    """``_getNetPerpMargin`` (:442-469), always <= 0."""
    if q == 0:
        return 0.0
    req = _prm(params, "PerpMarginRequirements", "imPerpReq" if is_initial else "mmPerpReq")
    margin = -abs(q) * perp_price * req
    if is_initial:
        oc = params["OracleContingencyParams"]
        margin -= float(_contingency(min(perp_conf, spot_conf), float(oc["perpThreshold"]), float(oc["OCFactor"]))) \
            * spot * abs(q)
    return margin


def _base_margin(q: float, spot: float, spot_conf: float, stable: float, params, is_initial) -> Tuple[float, float]:
    """``_getBaseMarginAndMtM`` (:519-551): base collateral counts ``marginFactor`` (x ``IMScale`` for IM)."""
    if q == 0:
        return 0.0, 0.0
    if q < 0:
        raise ValueError("base collateral cannot be negative")
    notional = q * spot
    margin = notional * _prm(params, "BaseMarginParams", "marginFactor")
    mtm = notional / stable
    if not is_initial:
        return margin, mtm
    margin *= _prm(params, "BaseMarginParams", "IMScale")
    if margin == 0:
        return 0.0, mtm
    oc = params["OracleContingencyParams"]
    margin -= float(_contingency(spot_conf, float(oc["baseThreshold"]), float(oc["OCFactor"]))) * notional
    return margin, mtm


def net_margin(book: Book, state: MarketState, params: Mapping, is_initial: bool = True, *,
               vols: Optional[Mapping[Tuple[int, float], float]] = None, base: float = 0.0) -> Tuple[float, float]:
    """(net, mtm) of ``book`` in one SM market: net = cash + V - R, mtm = cash + V.

    ``vols`` optionally maps ``(expiry, strike)`` to the vol-feed value (e.g. read by ``eth_call``); otherwise the
    SVI curve of ``state.expiries[expiry]`` is used. ``base`` is the base-asset collateral (e.g. wrapped BTC) in
    units of the underlying. A perp with ``perp_entry = None`` has no unrealised PnL. Legs of one instrument are
    netted first (:func:`merged_options`), so appending a fill to a book gives the chain's post-trade balance.
    """
    spot, spot_conf = float(state.spot), float(state.spot_conf)
    options = merged_options(book)
    margin = 0.0
    mtm = 0.0
    depeg = float(_depeg_multiplier(state.stable, params, is_initial))
    if depeg != 0.0:
        shorts = sum(-leg.amount for leg in options if leg.amount < 0)
        margin -= (abs(book.perp) + shorts) * depeg * spot
    margin += _perp_margin(book.perp, state.perp_price, state.perp_conf, spot, spot_conf, params, is_initial)
    for expiry in sorted({leg.expiry for leg in options}):
        legs = [leg for leg in options if leg.expiry == expiry]
        es = state.expiries[expiry]
        sigma = []
        for leg in legs:
            key = (leg.expiry, leg.strike)
            sigma.append(vols[key] if vols is not None and key in vols else es.vol(leg.strike))
        conf = min(spot_conf, float(es.fwd_conf), float(es.vol_conf))
        sec = float(max(expiry - state.ts, 0))
        m_e, v_e = _expiry_margin([leg.strike for leg in legs], [leg.is_call for leg in legs],
                                  [leg.amount for leg in legs], np.asarray(sigma, dtype=float), spot,
                                  float(es.forward), sec, conf, params, is_initial)
        margin += m_e
        mtm += v_e
    b_m, b_v = _base_margin(float(base), spot, spot_conf, float(state.stable), params, is_initial)
    upnl = 0.0
    if book.perp != 0 and book.perp_entry is not None:
        upnl = (state.perp_price - book.perp_entry) * book.perp
    margin += b_m + upnl
    mtm += b_v + upnl
    return margin + book.cash, mtm + book.cash


def net_margin_multi(books: Mapping[str, Book], states: Mapping[str, MarketState], params: Mapping[str, Mapping],
                     is_initial: bool = True, *, cash: float = 0.0,
                     vols: Optional[Mapping[str, Mapping[Tuple[int, float], float]]] = None,
                     bases: Optional[Mapping[str, float]] = None) -> Tuple[float, float]:
    """(net, mtm) of an SM account holding several markets: the markets add up, cash counts once.

    ``params`` maps currency to that market's parameter dict; ``book.cash`` of the per-market books is ignored.
    """
    net = mtm = float(cash)
    for ccy, book in books.items():
        b = Book(options=book.options, perp=book.perp, perp_entry=book.perp_entry, cash=0.0)
        n, m = net_margin(b, states[ccy], params[ccy], is_initial, vols=(vols or {}).get(ccy),
                          base=(bases or {}).get(ccy, 0.0))
        net += n
        mtm += m
    return net, mtm


def requirement(book: Book, state: MarketState, params: Mapping, is_initial: bool = True, **kw) -> float:
    """R = mtm - net (>= 0 for option books; perp PnL and base collateral enter V and R as in the contract)."""
    net, mtm = net_margin(book, state, params, is_initial, **kw)
    return mtm - net


def single(arrays: Mapping[str, np.ndarray], params: Mapping, is_initial: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """(net, mtm) for many one-option books with cash 0, vectorised.

    ``arrays`` holds equally long 1-D arrays ``spot, forward, sigma, tau, rate, strike, is_call, amount, vol_conf,
    fwd_conf, spot_conf`` (``rate`` is unused by SM; optional ``stable``, default 1). Identical to
    :func:`net_margin` on the corresponding book.
    """
    a = arrays
    spot = np.asarray(a["spot"], dtype=float)
    n = spot.shape[0]
    one = np.ones(n)
    forward = np.asarray(a["forward"], dtype=float)
    strike = np.asarray(a["strike"], dtype=float)
    is_call = np.asarray(a["is_call"], dtype=bool)
    amount = np.asarray(a["amount"], dtype=float)
    iso, mtm = isolated_margin(spot, forward, a["sigma"], a["tau"], strike, is_call, amount, params, is_initial)
    # max loss on the grid {0, K}: a put pays K*q at 0, a call nothing; unpaired short calls add scale*F*q
    max_loss = np.where(~is_call, np.minimum(strike * amount, 0.0), 0.0)
    scale = _prm(params, "OptionMarginParams", "unpairedIMScale" if is_initial else "unpairedMMScale")
    max_loss = max_loss + np.where(is_call & (amount < 0), scale * forward * amount, 0.0)
    net = np.maximum(iso, max_loss)
    if is_initial:
        short = np.maximum(-amount, 0.0)
        conf = np.minimum(np.minimum(np.asarray(a.get("spot_conf", one), dtype=float),
                                     np.asarray(a.get("fwd_conf", one), dtype=float)),
                          np.asarray(a.get("vol_conf", one), dtype=float))
        oc = params["OracleContingencyParams"]
        net = net - _contingency(conf, float(oc["optionThreshold"]), float(oc["OCFactor"])) * spot * short
        net = net - _depeg_multiplier(np.asarray(a.get("stable", one), dtype=float), params, True) * short * spot
    return net, mtm


__all__ = ["MARKET_ID", "b76_prices", "isolated_margin", "merged_options", "net_margin", "net_margin_multi",
           "requirement", "single"]
