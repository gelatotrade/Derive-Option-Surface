"""Historical surfaces reconstructed from the trade tape.

Derive keeps no public history of its orderbooks, but it keeps every fill.  A
fill is a point where the book *was*: at ``timestamp`` somebody paid
``trade_price`` for ``instrument_name`` while the index stood at
``index_price``.  Inverting Black-76 on each fill gives an implied vol observed
at a known moneyness and tenor; a time-decayed, size-weighted SVI fit over the
fills of the trailing window gives the surface as the market actually traded it.

This is the closest thing to "historical orderbook data" that exists for Derive,
and it is exact where it matters: every point *is* a crossed quote.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import pricing
from .surface import IV_BOUNDS, MAX_ABS_LOGM, MIN_TENOR_YEARS, Smile, Surface

log = logging.getLogger(__name__)


def load_trades(data_dir: Path, currency: str) -> pd.DataFrame:
    return pd.read_parquet(data_dir / "trades" / f"{currency}_option_trades.parquet")


def load_spot(data_dir: Path, currency: str, resolution: str = "1h") -> pd.Series:
    df = pd.read_parquet(data_dir / "spot" / f"{currency}_{resolution}.parquet")
    return df.set_index("timestamp")["price"].sort_index()


def trade_ivs(trades: pd.DataFrame) -> pd.DataFrame:
    """Implied vol of every fill (forward ~ index; Derive's basis is a few bp)."""
    t = trades.copy()
    t["T"] = (t["expiry"] - t["timestamp"] / 1000.0) / pricing.YEAR
    t["kind"] = np.where(t["option_type"].eq("C"), 1, -1)
    t = t[(t["T"] > MIN_TENOR_YEARS) & (t["index_price"] > 0) & (t["trade_price"] > 0)].copy()
    t["k"] = np.log(t["strike"] / t["index_price"])
    t["iv"] = pricing.implied_vol(t["trade_price"].values, t["index_price"].values, t["strike"].values, t["T"].values, t["kind"].values)
    t["otm"] = (t["kind"] == np.where(t["strike"] >= t["index_price"], 1, -1))
    ok = t["iv"].between(*IV_BOUNDS) & t["k"].abs().le(MAX_ABS_LOGM)
    return t[ok].reset_index(drop=True)


def surface_at(
    fills: pd.DataFrame, spot: pd.Series, ts_ms: int, currency: str, *, window_s: float = 86400, half_life_s: float = 6 * 3600,
    min_strikes: int = 4, otm_only: bool = True
) -> Surface | None:
    """Surface at ``ts_ms`` from the fills of the trailing ``window_s`` seconds."""
    lo = ts_ms - window_s * 1000
    w = fills[(fills["timestamp"] > lo) & (fills["timestamp"] <= ts_ms)]
    if otm_only:
        w = w[w["otm"]]
    F = float(np.interp(ts_ms / 1000, spot.index.values, spot.values))
    smiles = []
    for expiry, g in w.groupby("expiry"):
        T = (expiry - ts_ms / 1000) / pricing.YEAR
        if T <= MIN_TENOR_YEARS or g["strike"].nunique() < min_strikes:
            continue
        age = (ts_ms - g["timestamp"].values) / 1000.0
        weight = g["trade_amount"].values * np.exp(-age * np.log(2) / half_life_s)
        weight = np.maximum(weight, 1e-6)
        # merge repeated strikes into one weighted quote so a busy strike does not dominate the fit
        agg = pd.DataFrame({"k": g["k"].values, "w": weight, "iv": g["iv"].values}).groupby(g["strike"].values)
        k = agg.apply(lambda d: np.average(d["k"], weights=d["w"])).values
        iv = agg.apply(lambda d: np.average(d["iv"], weights=d["w"])).values
        wt = agg["w"].sum().values
        smiles.append(Smile.fit(int(expiry), T, F, 1.0, k, iv, wt))
    if not smiles:
        return None
    return Surface(ts_ms, currency, F, sorted(smiles, key=lambda s: s.T))


def surfaces_over_time(fills: pd.DataFrame, spot: pd.Series, times_ms: np.ndarray, currency: str, **kw) -> list[Surface]:
    out = []
    for ts in times_ms:
        s = surface_at(fills, spot, int(ts), currency, **kw)
        if s is not None and len(s.smiles) >= 2:
            out.append(s)
    log.info("%s: %d/%d timestamps yielded a surface", currency, len(out), len(times_ms))
    return out
