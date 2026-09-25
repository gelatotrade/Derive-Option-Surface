"""Markouts of paper 1, exactly as pre-registered (docs/paper1/PRAEREGISTRIERUNG.md, incl. addendum 1;
English translation in docs/paper1/PREREGISTRATION.md).

Maker side s = −taker_side.  MO_τ = s·(M(t+τ) − P) per contract in USDC; delta-neutral
MO^Δ_τ = MO_τ − s·Δ(t)·(F(t+τ) − F(t)) with F the forward of the valid SVI curve at both ends; vol-point
markout 100·s·(IV_b(t+τ) − IV_fill(t)).  Path (b) = last on-chain SVI curve of the expiry by push time.
Path (a) = mark_price of the first fill of the same instrument at or after t+τ.  Path (c) = settlement.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from . import pricing
from .chainfeeds import load_feed, svi_vol
from .markpath import SVI_COLUMNS, attach_svi, mark_from_svi

log = logging.getLogger(__name__)

CORE = ("BTC", "ETH", "HYPE")
SAMPLE_START_MS = 1_704_931_200_000   # 2024-01-11 00:00 UTC
FINAL_CUTOFF_MS = 1_790_755_200_000   # 2026-09-30 08:00 UTC
PILOT_CUTOFF_MS = 1_789_646_400_000   # 2026-09-17 12:00 UTC
EXPIRY_BUFFER_MS = 30 * 60_000
HORIZONS_S: Dict[str, int] = {"1m": 60, "5m": 300, "30m": 1_800, "4h": 14_400, "24h": 86_400}
DELTA_EDGES = [0.0, 10.0, 25.0, 40.0, 60.0, 75.0, 90.0, 100.0 + 1e-9]
DELTA_LABELS = ["00-10", "10-25", "25-40", "40-60", "60-75", "75-90", "90-100"]
TENOR_EDGES_D = [0.0, 2.0, 7.0, 30.0, 90.0, np.inf]
TENOR_LABELS = ["<=2d", "2-7d", "7-30d", "30-90d", ">90d"]
SVI_EXTRA = ["svi_block", "svi_clock", "svi_age_s"]


def sample_fills(fills: pd.DataFrame, start_ms: int = SAMPLE_START_MS, cutoff_ms: int = FINAL_CUTOFF_MS,
                 currencies=CORE) -> Tuple[pd.DataFrame, List[Tuple[str, int]]]:
    steps = [("input", len(fills))]
    f = fills[fills["currency"].isin(currencies)]
    steps.append(("core", len(f)))
    f = f[(f["ts"] >= start_ms) & (f["ts"] <= cutoff_ms)]
    steps.append(("window", len(f)))
    f = f[f["tx_status"] == "settled"]
    steps.append(("settled", len(f)))
    f = f[f["pair_ok"].astype(bool)]
    steps.append(("pair_ok", len(f)))
    f = f[f["expiry"] * 1000 - f["ts"] > EXPIRY_BUFFER_MS]
    steps.append(("not_last_30min", len(f)))
    return f.reset_index(drop=True), steps


def flag_sweeps(fills: pd.DataFrame, window_ms: int = 10_000, min_fills: int = 5, min_strikes: int = 3) -> pd.Series:
    """True for fills inside a 10-s window (starting at a fill of the same taker and underlying) holding ≥ 5 fills over ≥ 3 strikes."""
    flags = pd.Series(False, index=fills.index)
    for _, g in fills.groupby(["taker_wallet", "currency"], sort=False):
        if len(g) < min_fills:
            continue
        g = g.sort_values("ts")
        ts = g["ts"].to_numpy()
        strikes = g["strike"].to_numpy()
        ends = np.searchsorted(ts, ts + window_ms, side="right")
        hit = np.zeros(len(g), dtype=bool)
        for i in np.flatnonzero(ends - np.arange(len(g)) >= min_fills):
            if len(np.unique(strikes[i:ends[i]])) >= min_strikes:
                hit[i:ends[i]] = True
        flags.loc[g.index[hit]] = True
    return flags


def _tenor_T(rows: pd.DataFrame, at_ms: str) -> np.ndarray:
    return (rows["expiry"].to_numpy(float) - rows[at_ms].to_numpy(float) / 1000.0) / pricing.YEAR


def _svi_args(rows: pd.DataFrame):
    return [rows[c].to_numpy(float) for c in ["svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_fwd", "svi_ref_tau"]]


def state_at_fill(rows: pd.DataFrame, svi: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    s = attach_svi(rows, svi, at_ms="ts", clock="block_ts")
    have = s["svi_fwd"].notna()
    missing = int((~have).sum())
    s = s[have].reset_index(drop=True)
    kind = np.where(s["option_type"].to_numpy() == "C", 1, -1)
    T = _tenor_T(s, "ts")
    K = s["strike"].to_numpy(float)
    F = s["svi_fwd"].to_numpy(float)
    vol = svi_vol(K, *_svi_args(s))
    s["maker_side"] = -s["taker_side"].astype(int)
    s["fwd_t"] = F
    s["iv_mark_t"] = vol
    s["iv_fill"] = pricing.implied_vol(s["price"].to_numpy(float), F, K, T, kind)
    s["mark_b_t"] = mark_from_svi(s, at_ms="ts").to_numpy()
    s["delta_t"] = pricing.delta_of(F, K, T, vol, kind)
    s["abs_delta_pct"] = np.abs(s["delta_t"]) * 100
    s["delta_bucket"] = pd.cut(s["abs_delta_pct"], DELTA_EDGES, labels=DELTA_LABELS, right=False).astype(str)
    s["tenor_days"] = T * 365.0
    s["tenor_bucket"] = pd.cut(s["tenor_days"], TENOR_EDGES_D, labels=TENOR_LABELS, right=True, include_lowest=True).astype(str)
    s = s.rename(columns={"svi_age_s": "svi_age_s_t"}).drop(columns=SVI_COLUMNS + ["svi_block", "svi_clock"])
    return s, missing


def marks_b(state: pd.DataFrame, svi: pd.DataFrame, horizons: Dict[str, int] = HORIZONS_S) -> pd.DataFrame:
    out = pd.DataFrame(index=state.index)
    base = state[["expiry", "strike", "option_type", "ts"]]
    for name, sec in horizons.items():
        q = base.assign(tq=base["ts"] + sec * 1000)
        m = attach_svi(q, svi, at_ms="tq", clock="block_ts")
        live = (m["tq"].to_numpy() < m["expiry"].to_numpy() * 1000) & m["svi_fwd"].notna().to_numpy()
        vol = svi_vol(m["strike"].to_numpy(float), *_svi_args(m))
        out[f"mark_b_{name}"] = np.where(live, mark_from_svi(m, at_ms="tq").to_numpy(), np.nan)
        out[f"iv_b_{name}"] = np.where(live, vol, np.nan)
        out[f"fwd_b_{name}"] = np.where(live, m["svi_fwd"].to_numpy(float), np.nan)
    return out


def add_markouts(state: pd.DataFrame, marks: pd.DataFrame, horizons: Dict[str, int] = HORIZONS_S) -> pd.DataFrame:
    out = pd.concat([state, marks], axis=1)
    s = out["maker_side"].to_numpy(float)
    for name in horizons:
        mo = s * (out[f"mark_b_{name}"].to_numpy() - out["price"].to_numpy(float))
        out[f"mo_usd_{name}"] = mo
        out[f"mo_dn_{name}"] = mo - s * out["delta_t"].to_numpy() * (out[f"fwd_b_{name}"].to_numpy() - out["fwd_t"].to_numpy())
        out[f"mo_vol_{name}"] = 100.0 * s * (out[f"iv_b_{name}"].to_numpy() - out["iv_fill"].to_numpy())
    return out


def add_path_a(state: pd.DataFrame, fills: pd.DataFrame, horizons: Dict[str, int] = HORIZONS_S) -> pd.DataFrame:
    out = state.copy()
    ref = (fills[["instrument_name", "ts", "mark_price"]].dropna()
           .rename(columns={"ts": "tq", "mark_price": "mark_a"}).sort_values("tq"))
    ref = ref.assign(ts_a=ref["tq"])
    for name, sec in horizons.items():
        q = out[["instrument_name", "ts"]].assign(tq=out["ts"] + sec * 1000, _row=np.arange(len(out)))
        m = pd.merge_asof(q.sort_values("tq"), ref, on="tq", by="instrument_name", direction="forward").sort_values("_row")
        out[f"mark_a_{name}"] = m["mark_a"].to_numpy()
        out[f"lag_a_{name}_s"] = (m["ts_a"].to_numpy() - m["tq"].to_numpy()) / 1000.0
        out[f"mo_usd_a_{name}"] = out["maker_side"].to_numpy(float) * (out[f"mark_a_{name}"].to_numpy() - out["price"].to_numpy(float))
    return out


def add_settlement(state: pd.DataFrame, settle: pd.DataFrame) -> pd.DataFrame:
    prices = settle[["currency", "expiry", "settlement_price"]].astype({"expiry": "int64", "settlement_price": "float64"})
    out = state.merge(prices, on=["currency", "expiry"], how="left")
    kind = np.where(out["option_type"].to_numpy() == "C", 1.0, -1.0)
    out["payoff"] = np.maximum(kind * (out["settlement_price"].to_numpy() - out["strike"].to_numpy(float)), 0.0)
    out["mo_set"] = out["maker_side"].to_numpy(float) * (out["payoff"] - out["price"].to_numpy(float))
    month = pd.to_datetime(out["ts"], unit="ms", utc=True).dt.strftime("%Y-%m")
    cell_mean = out.groupby([out["currency"], out["delta_bucket"], out["tenor_bucket"], month])["mo_set"].transform("mean")
    out["mo_set_vrp"] = out["mo_set"] - cell_mean
    return out


def add_size_flag(state: pd.DataFrame, q: float = 0.9) -> pd.DataFrame:
    out = state.copy()
    threshold = out.groupby("currency")["notional"].transform(lambda x: x.quantile(q))
    out["size_above_p90"] = out["notional"] > threshold
    return out


def build_markouts(root: Path, cutoff_ms: int, out_path: Path) -> dict:
    fills = pd.read_parquet(root / "derived" / "fills.parquet")
    fills["is_sweep"] = flag_sweeps(fills).to_numpy()
    sample, steps = sample_fills(fills, cutoff_ms=cutoff_ms)
    settle = pd.read_parquet(root / "ref" / "settlement_prices.parquet")
    parts, missing = [], {}
    for ccy in CORE:
        rows = sample[sample["currency"] == ccy]
        if rows.empty:
            continue
        svi = load_feed(root / "raw" / "volfeed", ccy)
        state, missing[ccy] = state_at_fill(rows, svi)
        parts.append(add_markouts(state, marks_b(state, svi)))
        log.info("%s: %d fills with markouts, %d without a curve", ccy, len(state), missing[ccy])
    res = pd.concat(parts, ignore_index=True)
    res = add_path_a(res, fills)
    res = add_settlement(res, settle)
    res = add_size_flag(res)
    res.to_parquet(out_path, index=False, compression="zstd")
    coverage = {col: int(res[col].notna().sum()) for col in res.columns if col.startswith(("mo_usd_", "mo_dn_", "mo_vol_", "mo_set"))}
    summary = {"cutoff_ms": cutoff_ms, "steps": steps, "without_curve": missing, "rows": int(len(res)), "coverage": coverage,
               "sweep_fills": int(res["is_sweep"].sum()), "size_above_p90": int(res["size_above_p90"].sum())}
    out_path.with_name("markouts_summary.json").write_text(json.dumps(summary, indent=1))
    return summary
