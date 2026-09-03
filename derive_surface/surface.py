"""From one orderbook snapshot to a gridded implied-volatility surface.

Pipeline for a single timestamp:

1. ``quotes_from_snapshot`` — take the top of every book, form the mid, keep
   the out-of-the-money side of each strike (calls above the forward, puts
   below: that is where the liquidity and the vol information live), invert
   Black-76 for the mid/bid/ask implied vols, weight each quote by the
   tightness of its bid/ask *in vol space*.
2. ``Smile.fit`` — per expiry, fit raw-SVI total variance
   ``w(k) = a + b (rho (k - m) + sqrt((k - m)^2 + s^2))`` by weighted least
   squares (quadratic / flat fallbacks when a book is too thin, e.g. HYPE).
3. ``Surface`` — evaluate the smiles on a common moneyness axis (delta or
   log-moneyness) and interpolate total variance linearly across tenor.

The three coordinates of the surface are therefore *(moneyness, tenor,
implied vol)*: the two coordinates that identify an option and the one number
the whole orderbook agrees to price it with.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from . import pricing

MIN_TENOR_YEARS = 1.0 / (365.0 * 24.0)  # ignore expiries inside their final hour
IV_BOUNDS = (0.02, 6.0)
MAX_ABS_LOGM = 1.2  # quotes further out than e^1.2 (3.3x) from the forward carry no vol information
MAX_REL_SPREAD = 0.8  # (ask - bid) / mid; wider books are noise, not price discovery
WING_PAD = 0.05  # cap on how far (in log-moneyness) a smile is followed beyond its last quote before being held flat
DELTA_AXIS = np.linspace(0.05, 0.95, 37)  # call-delta axis (put delta = call delta - 1)
LOGM_AXIS = np.linspace(-0.6, 0.6, 49)


# --------------------------------------------------------------------- quotes
def quotes_from_snapshot(df: pd.DataFrame, ts_ms: int | None = None) -> pd.DataFrame:
    """Turn a top-of-book snapshot (one row per instrument) into OTM vol quotes."""
    d = df.copy()
    ts_ms = ts_ms or int(d["ts"].max())
    d["T"] = (d["expiry"] - ts_ms / 1000.0) / pricing.YEAR
    per_exp = d.groupby("expiry").agg(F=("forward", "median"), df=("discount_factor", "median"))
    d = d.join(per_exp, on="expiry")
    d["F"] = d["F"].fillna(d["index"])  # forward missing -> fall back to the index
    d["df"] = d["df"].fillna(1.0)
    d["kind"] = np.where(d["option_type"].eq("C"), 1, -1)
    d = d[(d["T"] > MIN_TENOR_YEARS) & (d["F"] > 0)]
    otm = np.where(d["strike"] >= d["F"], 1, -1)
    d = d[d["kind"] == otm].copy()
    two_sided = d["bid"].gt(0) & d["ask"].gt(0)
    d["mid"] = np.where(two_sided, 0.5 * (d["bid"] + d["ask"]), np.nan)
    d["k"] = np.log(d["strike"] / d["F"])
    args = (d["F"].values, d["strike"].values, d["T"].values, d["kind"].values, d["df"].values)
    d["iv_mid"] = pricing.implied_vol(d["mid"].values, *args)
    d["iv_bid"] = pricing.implied_vol(d["bid"].where(d["bid"] > 0).values, *args)
    d["iv_ask"] = pricing.implied_vol(d["ask"].where(d["ask"] > 0).values, *args)
    ok = (
        d["iv_mid"].between(*IV_BOUNDS)
        & d["k"].abs().le(MAX_ABS_LOGM)
        & ((d["ask"] - d["bid"]) / d["mid"]).le(MAX_REL_SPREAD)
    )
    d = d[ok].copy()
    width = (d["iv_ask"] - d["iv_bid"]).fillna(0.25).clip(lower=0.005)
    d["weight"] = 1.0 / width
    cols = ["instrument_name", "expiry", "T", "F", "df", "index", "strike", "k", "kind", "bid", "ask", "mid",
            "iv_bid", "iv_mid", "iv_ask", "weight", "delta", "iv"]
    return d[[c for c in cols if c in d.columns]].sort_values(["expiry", "strike"]).reset_index(drop=True)


# ---------------------------------------------------------------------- smile
@dataclass
class Smile:
    """One expiry: fitted total-variance curve plus the quotes it was fitted to."""

    expiry: int
    T: float
    F: float
    df: float
    k: np.ndarray
    iv: np.ndarray
    weight: np.ndarray
    model: str = "flat"
    params: np.ndarray = field(default_factory=lambda: np.zeros(1))

    # raw SVI ----------------------------------------------------------------
    @staticmethod
    def _svi(p: np.ndarray, k: np.ndarray) -> np.ndarray:
        a, b, rho, m, s = p
        return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + s**2))

    @classmethod
    def fit(cls, expiry: int, T: float, F: float, df: float, k: np.ndarray, iv: np.ndarray, weight: np.ndarray) -> "Smile":
        k, iv, weight = (np.asarray(x, float) for x in (k, iv, weight))
        sm = cls(expiry, T, F, df, k, iv, weight)
        w_obs = iv**2 * T
        sw = np.sqrt(weight / weight.max())
        if len(k) >= 5 and np.ptp(k) > 0.02:
            atm = w_obs[np.argmin(np.abs(k))]
            x0 = np.array([0.8 * atm, 0.5 * atm / max(np.ptp(k), 0.1), -0.2, 0.0, 0.1])
            lo = np.array([-1.0, 0.0, -0.999, -2.0, 1e-3])
            hi = np.array([5.0, 20.0, 0.999, 2.0, 3.0])
            res = least_squares(lambda p: sw * (cls._svi(p, k) - w_obs), np.clip(x0, lo, hi), bounds=(lo, hi), loss="soft_l1", f_scale=0.01)
            p = res.x
            probe = np.linspace(k.min() - 0.3, k.max() + 0.3, 101)
            if np.all(cls._svi(p, probe) > 0) and p[1] * (1 + abs(p[2])) <= 4.0:
                sm.model, sm.params = "svi", p
                return sm
        if len(k) >= 3:
            coef = np.polyfit(k, w_obs, 2, w=sw)
            sm.model, sm.params = "quad", coef
            return sm
        sm.model, sm.params = "flat", np.array([np.average(w_obs, weights=weight)])
        return sm

    @property
    def wing_pad(self) -> float:
        """How far past the last quote the fitted curve is trusted: half an ATM standard deviation, at most WING_PAD.

        A 1-day smile quoted to +/-5 % must not be extrapolated 5 % further (that is
        four standard deviations for it); a 90-day smile can be.
        """
        atm = self.iv[np.argmin(np.abs(self.k))] if len(self.k) else 0.5
        return float(min(WING_PAD, 0.5 * atm * np.sqrt(self.T)))

    @property
    def k_range(self) -> tuple[float, float]:
        """Log-moneyness interval actually covered by quotes (used to mask plots to what the book prices)."""
        return float(self.k.min()), float(self.k.max())

    def total_variance(self, k: np.ndarray) -> np.ndarray:
        """Total variance; beyond the quoted range (+ wing_pad) the smile is held flat — we do not invent wings."""
        pad = self.wing_pad
        k = np.clip(np.asarray(k, float), self.k.min() - pad, self.k.max() + pad)
        if self.model == "svi":
            w = self._svi(self.params, k)
        elif self.model == "quad":
            w = np.polyval(self.params, k)
        else:
            w = np.full_like(k, self.params[0])
        return np.clip(w, (IV_BOUNDS[0] ** 2) * self.T, (IV_BOUNDS[1] ** 2) * self.T)

    def __call__(self, k: np.ndarray) -> np.ndarray:
        return np.sqrt(self.total_variance(k) / self.T)

    def strike_for_call_delta(self, delta: np.ndarray, iters: int = 12) -> np.ndarray:
        """Strike whose *smile-consistent* Black-76 call delta equals ``delta`` (fixed-point)."""
        delta = np.asarray(delta, float)
        K = pricing.strike_for_delta(delta, self.F, self.T, self(np.zeros_like(delta)), 1, self.df)
        for _ in range(iters):
            K = pricing.strike_for_delta(delta, self.F, self.T, self(np.log(K / self.F)), 1, self.df)
        return K


# -------------------------------------------------------------------- surface
@dataclass
class Surface:
    ts_ms: int
    currency: str
    spot: float
    smiles: list[Smile]

    @classmethod
    def from_snapshot(cls, df: pd.DataFrame, currency: str, ts_ms: int | None = None, min_quotes: int = 3) -> "Surface":
        ts_ms = ts_ms or int(df["ts"].max())
        q = quotes_from_snapshot(df, ts_ms)
        smiles = []
        for expiry, g in q.groupby("expiry"):
            if len(g) < min_quotes:
                continue
            smiles.append(Smile.fit(int(expiry), g["T"].iloc[0], g["F"].iloc[0], g["df"].iloc[0], g["k"].values, g["iv_mid"].values, g["weight"].values))
        spot = float(df["index"].dropna().median()) if df["index"].notna().any() else float("nan")
        return cls(ts_ms, currency, spot, sorted(smiles, key=lambda s: s.T))

    @property
    def tenors(self) -> np.ndarray:
        return np.array([s.T for s in self.smiles])

    def atm_term_structure(self) -> np.ndarray:
        return np.array([float(s(np.zeros(1))[0]) for s in self.smiles])

    # evaluation ---------------------------------------------------------------
    def iv_at_expiries(self, axis: str = "delta", x: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        """IV of every fitted expiry on the common axis -> (x, iv[expiry, x])."""
        if x is None:
            if axis == "strike":
                raise ValueError("axis='strike' needs an explicit strike grid")
            x = DELTA_AXIS if axis == "delta" else LOGM_AXIS
        x = np.asarray(x, float)
        rows = []
        for s in self.smiles:
            if axis == "delta":
                k = np.log(s.strike_for_call_delta(x) / s.F)
            elif axis == "strike":
                k = np.log(x / s.F)
            else:
                k = x
            rows.append(s(k))
        return x, np.array(rows)

    def grid(self, axis: str = "delta", x: np.ndarray | None = None, tenors: np.ndarray | None = None, n_tenors: int = 24, mask_wings: bool = False):
        """Gridded surface: returns (x, tenor_years, iv[tenor, x]) with total variance linear in T.

        ``mask_wings=True`` (strike / log-moneyness axes) sets nodes outside the
        quoted range of the neighbouring expiries to ``nan`` so a plot shows only
        what the orderbook actually prices.
        """
        x, iv_exp = self.iv_at_expiries(axis, x)
        T_exp = self.tenors
        if tenors is None:
            tenors = np.geomspace(T_exp.min(), T_exp.max(), n_tenors) if len(T_exp) > 1 else T_exp
        w_exp = iv_exp**2 * T_exp[:, None]
        w = np.empty((len(tenors), len(x)))
        for j in range(len(x)):
            w[:, j] = np.interp(tenors, T_exp, w_exp[:, j])
        iv = np.sqrt(np.maximum(w, 1e-10) / tenors[:, None])
        if mask_wings and axis in ("strike", "logm"):
            lo = np.array([s.k_range[0] for s in self.smiles])
            hi = np.array([s.k_range[1] for s in self.smiles])
            lo_t, hi_t = np.interp(tenors, T_exp, lo), np.interp(tenors, T_exp, hi)
            F_t = np.interp(tenors, T_exp, [s.F for s in self.smiles])
            k = np.log(x[None, :] / F_t[:, None]) if axis == "strike" else np.broadcast_to(x[None, :], iv.shape)
            iv = np.where((k >= lo_t[:, None]) & (k <= hi_t[:, None]), iv, np.nan)
        return x, tenors, iv

    def greeks_grid(self, axis: str = "delta", x: np.ndarray | None = None, tenors: np.ndarray | None = None, n_tenors: int = 24) -> dict[str, np.ndarray]:
        """Every greek of the OTM option at each grid node (so the surface can be coloured by any of them)."""
        x, tenors, iv = self.grid(axis, x, tenors, n_tenors)
        F = np.interp(tenors, self.tenors, [s.F for s in self.smiles])
        df = np.interp(tenors, self.tenors, [s.df for s in self.smiles])
        Tm, Fm, dfm = tenors[:, None], F[:, None], df[:, None]
        if axis == "delta":
            K = pricing.strike_for_delta(x[None, :], Fm, Tm, iv, 1, dfm)
        elif axis == "strike":
            K = np.broadcast_to(x[None, :], iv.shape)
        else:
            K = Fm * np.exp(x[None, :])
        kind = np.where(K >= Fm, 1, -1)
        g = pricing.greeks(Fm, K, Tm, iv, kind, dfm)
        g.update(x=x, tenors=tenors, iv=iv, strike=K)
        return g
