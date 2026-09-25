"""Mark price of an option at any time from the on-chain SVI history (mark path (b) of paper 1).

``attach_svi`` joins to every row the last SVI curve of the same expiry whose clock (``block_ts`` = pushed
on chain, or ``feed_ts`` = signed) is at or before the row's time.  ``mark_from_svi`` prices the option with
Black-76 on that curve: vol from ``chainfeeds.svi_vol`` (reference tau of the fit), time to expiry from the
row's time, forward ``SVI_fwd`` unless another forward column is given, discount factor 1.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from . import pricing
from .chainfeeds import svi_vol

SVI_COLUMNS = ["svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_fwd", "svi_ref_tau", "confidence"]


def attach_svi(rows: pd.DataFrame, svi: pd.DataFrame, *, at_ms: str = "ts", clock: str = "block_ts") -> pd.DataFrame:
    """``rows`` (columns ``expiry`` in s and ``at_ms`` in ms) plus the latest curve with ``clock`` <= time."""
    left = rows.assign(_row=np.arange(len(rows)), _t=rows[at_ms].astype("int64"))
    right = svi[svi[clock] > 0][["expiry", clock, "block"] + SVI_COLUMNS].rename(columns={"block": "svi_block"})
    right = right.assign(_t=right[clock].astype("int64") * 1000, svi_clock=right[clock].astype("int64")).drop(columns=[clock])
    merged = pd.merge_asof(left.sort_values("_t"), right.sort_values("_t"), on="_t", by="expiry", direction="backward")
    merged = merged.sort_values("_row").drop(columns=["_row", "_t"]).reset_index(drop=True)
    merged["svi_age_s"] = merged[at_ms] / 1000 - merged["svi_clock"]
    return merged


def mark_from_svi(rows: pd.DataFrame, *, at_ms: str = "ts", forward: Optional[str] = None) -> pd.Series:
    """Black-76 mark price per row from the attached SVI curve; nan without a curve or at/after expiry."""
    F = (rows[forward] if forward else rows["svi_fwd"]).to_numpy(float)
    K = rows["strike"].to_numpy(float)
    T = (rows["expiry"].to_numpy(float) - rows[at_ms].to_numpy(float) / 1000.0) / pricing.YEAR
    vol = svi_vol(K, *(rows[c].to_numpy(float) for c in ["svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_fwd", "svi_ref_tau"]))
    kind = np.where(rows["option_type"].to_numpy() == "C", 1, -1)
    with np.errstate(invalid="ignore"):
        price = pricing.price(F, K, T, vol, kind, 1.0)
    return pd.Series(np.where((T > 0) & np.isfinite(vol), price, np.nan), index=rows.index)
