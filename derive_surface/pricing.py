"""Black-76 pricing on the forward, implied-vol inversion and greeks to third order.

Everything is vectorised over numpy arrays.  Conventions (they matter when
comparing against the exchange):

* ``F`` forward, ``K`` strike, ``T`` year fraction to expiry, ``sigma`` annual
  vol, ``df`` discount factor (Derive quotes options in USDC on the forward and
  reports ``df`` explicitly, usually 0.998–1.0).
* ``kind`` is ``+1`` for calls, ``-1`` for puts.
* Greeks are derivatives with respect to the **forward** (Derive's ``delta``
  is also w.r.t. the forward), per 1.0 of vol (not per 1 %), per year.
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr  # standard normal CDF, vectorised and fast

SQRT_2PI = np.sqrt(2.0 * np.pi)
YEAR = 365.0 * 86400.0  # seconds; tenors are expressed in calendar years


def npdf(x):
    return np.exp(-0.5 * np.square(x)) / SQRT_2PI


def _prep(F, K, T, sigma, kind, df):
    F, K, T, sigma, kind, df = np.broadcast_arrays(*(np.asarray(a, dtype=float) for a in (F, K, T, sigma, kind, df)))
    T = np.maximum(T, 1e-12)
    sig_t = np.maximum(sigma, 1e-12) * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sig_t**2) / sig_t
    d2 = d1 - sig_t
    return F, K, T, sigma, kind, df, sig_t, d1, d2


def price(F, K, T, sigma, kind=1, df=1.0):
    """Black-76 premium in quote currency per unit of underlying."""
    F, K, T, sigma, kind, df, sig_t, d1, d2 = _prep(F, K, T, sigma, kind, df)
    return df * kind * (F * ndtr(kind * d1) - K * ndtr(kind * d2))


def intrinsic(F, K, kind=1, df=1.0):
    return df * np.maximum(kind * (np.asarray(F, float) - np.asarray(K, float)), 0.0)


def implied_vol(V, F, K, T, kind=1, df=1.0, *, lo=1e-3, hi=8.0, iters=64):
    """Vectorised bisection for Black-76 implied vol.

    Bisection is chosen over Newton on purpose: the premium is monotone in vol,
    so 64 halvings of [lo, hi] converge unconditionally to ~1e-18 relative
    precision without any of Newton's flat-vega pathologies for deep OTM
    quotes.  Prices at or below intrinsic (or above the no-arbitrage cap) give
    ``nan``.
    """
    V, F, K, T, kind, df = np.broadcast_arrays(*(np.asarray(a, dtype=float) for a in (V, F, K, T, kind, df)))
    lower = intrinsic(F, K, kind, df)
    upper = df * np.where(kind > 0, F, K)
    ok = np.isfinite(V) & (V > lower + 1e-12) & (V < upper) & (T > 0) & (F > 0) & (K > 0)
    a = np.full(V.shape, lo)
    b = np.full(V.shape, hi)
    for _ in range(iters):
        m = 0.5 * (a + b)
        too_high = price(F, K, T, m, kind, df) > V
        b = np.where(too_high, m, b)
        a = np.where(too_high, a, m)
    iv = 0.5 * (a + b)
    ok &= (iv > lo * (1 + 1e-6)) & (iv < hi * (1 - 1e-6))  # a root outside the bracket is not a root
    return np.where(ok, iv, np.nan)


def greeks(F, K, T, sigma, kind=1, df=1.0) -> dict[str, np.ndarray]:
    """First-, second- and third-order greeks under Black-76 (forward measure).

    First order:  delta, vega, theta (per year, calendar decay), rho (w.r.t. the
    flat rate implied by ``df``, i.e. ``-T * V``; Derive reports the opposite sign).
    All are exact derivatives of the *discounted* premium; for the undiscounted
    forward delta used on the delta axis see ``delta_of``.
    Second order: gamma, vanna (d delta / d sigma = d vega / dF), volga (d vega /
    d sigma), charm (d delta / dt).
    Third order:  speed (d gamma / dF), zomma (d gamma / d sigma), color (d gamma
    / dt), ultima (d volga / d sigma).
    """
    F, K, T, sigma, kind, df, sig_t, d1, d2 = _prep(F, K, T, sigma, kind, df)
    sigma = np.maximum(sigma, 1e-12)
    sqrt_t = np.sqrt(T)
    phi = npdf(d1)
    V = df * kind * (F * ndtr(kind * d1) - K * ndtr(kind * d2))
    vega = df * F * phi * sqrt_t
    gamma = df * phi / (F * sig_t)
    out = {
        "price": V,
        # ---- first order
        "delta": df * (ndtr(d1) - np.where(kind > 0, 0.0, 1.0)),
        "vega": vega,
        "theta": -df * F * phi * sigma / (2.0 * sqrt_t),
        "rho": -T * V,
        # ---- second order
        "gamma": gamma,
        "vanna": -df * phi * d2 / sigma,
        "volga": vega * d1 * d2 / sigma,
        "charm": df * phi * d2 / (2.0 * T),
        # ---- third order
        "speed": -gamma / F * (1.0 + d1 / sig_t),
        "zomma": gamma * (d1 * d2 - 1.0) / sigma,
        "color": df * phi / (2.0 * F * T * sig_t) * (1.0 - d1 * d2),
        "ultima": -vega / sigma**2 * (d1 * d2 * (1.0 - d1 * d2) + d1**2 + d2**2),
    }
    return out


def delta_of(F, K, T, sigma, kind=1, df=1.0):
    """*Forward delta* N(d1) (minus 1 for puts): the undiscounted market convention that Derive
    reports and that the delta axis uses.  ``greeks()['delta']`` is the exact derivative of the
    discounted premium and differs by the factor ``df``."""
    F, K, T, sigma, kind, df, sig_t, d1, d2 = _prep(F, K, T, sigma, kind, df)
    return ndtr(d1) - np.where(kind > 0, 0.0, 1.0)


def strike_for_delta(delta, F, T, sigma, kind=1, df=1.0):
    """Invert the forward delta N(d1) (see ``delta_of``) for the strike."""
    delta, F, T, sigma, kind, df = np.broadcast_arrays(*(np.asarray(a, dtype=float) for a in (delta, F, T, sigma, kind, df)))
    from scipy.special import ndtri

    n = delta + np.where(kind > 0, 0.0, 1.0)
    d1 = ndtri(np.clip(n, 1e-9, 1 - 1e-9))
    sig_t = sigma * np.sqrt(T)
    return F * np.exp(-(d1 * sig_t) + 0.5 * sig_t**2)
