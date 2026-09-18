"""Aggregations behind the figures of paper 1.

Kept apart from the drawing code so that every number in a figure is testable and reproducible, and so
that a figure and the figure sheet can never disagree.  Markouts are heavily skewed (mean 13.05 USDC,
median 0.98 on the pilot), so the default statistic is the median with a cluster bootstrap interval over
taker wallets; ``stat="mean"`` gives the pre-registered quantity.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple

import numpy as np
import pandas as pd

from .chainfeeds import svi_vol
from .inference_p1 import HORIZON_SECONDS, cluster_mean_ci
from .markouts import DELTA_LABELS, TENOR_LABELS

UNIT_COLUMN = {"usd": "mo_usd_{}", "dn": "mo_dn_{}", "vol": "mo_vol_{}", "path_a": "mo_usd_a_{}"}
RESULT_TABLES = {"classes": "class_means.csv", "horizons": "horizon_means.csv", "cells": "h4_cells.csv",
                 "sensitivity": "h4_sensitivity.csv", "lorenz": "h1_lorenz.csv", "paths": "path_agreement.csv"}


def load_results(results_dir) -> Dict[str, object]:
    """The registered results: ``summary`` plus one frame per CSV, empty where a table is absent.

    A figure must never quietly invent a number, so the tables come from the inference run rather than from
    a second computation.  A table that the run did not write yields an empty frame, which lets a figure
    skip its panel instead of crashing halfway through a batch.
    """
    results_dir = Path(results_dir)
    if not results_dir.is_dir():
        raise FileNotFoundError("results directory not found: {}".format(results_dir))
    summary_path = results_dir / "summary.json"
    out: Dict[str, object] = {"summary": json.loads(summary_path.read_text()) if summary_path.exists() else {}}
    for key, name in RESULT_TABLES.items():
        path = results_dir / name
        out[key] = pd.read_csv(path) if path.exists() else pd.DataFrame()
    return out


def cells_matrix(cells: pd.DataFrame, currency: str, value: str = "mean"):
    """Tenor x delta matrix of the registered cell table, its fill counts and which cells exclude zero."""
    g = cells[cells["currency"] == currency]
    values = g.pivot_table(index="tenor_bucket", columns="delta_bucket", values=value, aggfunc="first")
    counts = g.pivot_table(index="tenor_bucket", columns="delta_bucket", values="fills", aggfunc="first")
    lo = g.pivot_table(index="tenor_bucket", columns="delta_bucket", values="lo", aggfunc="first")
    hi = g.pivot_table(index="tenor_bucket", columns="delta_bucket", values="hi", aggfunc="first")
    rows_order = [t for t in TENOR_LABELS if t in values.index]
    cols_order = [d for d in DELTA_LABELS if d in values.columns]
    values, counts = values.loc[rows_order, cols_order], counts.loc[rows_order, cols_order]
    lo, hi = lo.loc[rows_order, cols_order], hi.loc[rows_order, cols_order]
    significant = ((lo > 0) | (hi < 0)).fillna(False)
    return values, counts.fillna(0).astype(int), significant


def _median_ci(values: np.ndarray, clusters: np.ndarray, b: int = 999, seed: int = 20260917,
               level: float = 0.95) -> Tuple[float, float, float]:
    """Cluster bootstrap of the median, exact and fast.

    A draw multiplies every cluster by how often it was drawn, so the pooled median is the weighted median
    over the values sorted once up front: one gather, one cumulative sum and one search per draw instead of
    concatenating thousands of arrays.
    """
    values = np.asarray(values, dtype=float)
    codes = pd.factorize(pd.Series(clusters))[0]
    n_cluster = int(codes.max()) + 1 if len(codes) else 0
    if len(values) == 0:
        return np.nan, np.nan, np.nan
    order = np.argsort(values, kind="stable")
    sorted_values, sorted_codes = values[order], codes[order]
    rng = np.random.default_rng(seed)
    draws = np.empty(b)
    for i in range(b):
        multiplicity = np.bincount(rng.integers(0, n_cluster, n_cluster), minlength=n_cluster).astype(float)
        weights = multiplicity[sorted_codes]
        cumulative = np.cumsum(weights)
        if cumulative[-1] <= 0:
            draws[i] = np.nan
            continue
        draws[i] = sorted_values[min(int(np.searchsorted(cumulative, cumulative[-1] / 2.0)), len(sorted_values) - 1)]
    alpha = (1 - level) / 2
    return (float(np.median(values)), float(np.nanquantile(draws, alpha)), float(np.nanquantile(draws, 1 - alpha)))


def _cluster_stat_ci(values: np.ndarray, clusters: np.ndarray, stat: str, b: int, seed: int,
                     level: float = 0.95) -> Tuple[float, float, float, int]:
    ok = np.isfinite(values)
    values, clusters = values[ok], np.asarray(clusters)[ok]
    if len(values) == 0:
        return np.nan, np.nan, np.nan, 0
    if stat == "mean":
        ci = cluster_mean_ci(values, clusters, b=b, seed=seed, level=level)
        return ci["mean"], ci["lo"], ci["hi"], ci["n"]
    value, lo, hi = _median_ci(values, clusters, b=b, seed=seed, level=level)
    return value, lo, hi, int(len(values))


def horizon_curve(rows: pd.DataFrame, horizons: Sequence[str] = tuple(HORIZON_SECONDS), unit: str = "usd",
                  stat: str = "median", by: str = "taker_class", b: int = 999, seed: int = 20260917) -> pd.DataFrame:
    """One row per class (plus ``all``) and horizon: statistic with a cluster bootstrap interval."""
    out = []
    groups = [("all", rows)] + [(name, g) for name, g in rows.groupby(by, sort=True)]
    for name, g in groups:
        for h in horizons:
            col = UNIT_COLUMN[unit].format(h)
            if col not in g:
                continue
            value, lo, hi, n = _cluster_stat_ci(g[col].to_numpy(float), g["cluster"].to_numpy(), stat, b, seed)
            out.append({by: name, "horizon": h, "seconds": HORIZON_SECONDS[h], "unit": unit, "stat": stat,
                        "value": value, "lo": lo, "hi": hi, "fills": n})
    return pd.DataFrame(out).sort_values([by, "seconds"]).reset_index(drop=True)


def cell_matrix(rows: pd.DataFrame, value: str, currency: str = None, stat: str = "median",
                min_fills: int = 200) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Tenor × delta matrix of a statistic plus the fill counts; thin cells become nan."""
    g = rows if currency is None else rows[rows["currency"] == currency]
    counts = g.pivot_table(index="tenor_bucket", columns="delta_bucket", values=value, aggfunc="count")
    values = g.pivot_table(index="tenor_bucket", columns="delta_bucket", values=value, aggfunc=stat)
    rows_order = [t for t in TENOR_LABELS if t in values.index]
    cols_order = [d for d in DELTA_LABELS if d in values.columns]
    values, counts = values.loc[rows_order, cols_order], counts.loc[rows_order, cols_order]
    return values.where(counts >= min_fills), counts.fillna(0).astype(int)


def weekly_series(rows: pd.DataFrame, horizon: str = "30m", unit: str = "usd") -> pd.DataFrame:
    """Weekly median markout, share of losing fills and volume, for the time-series figure."""
    col = UNIT_COLUMN[unit].format(horizon)
    week = pd.to_datetime(rows["ts"], unit="ms", utc=True).dt.tz_localize(None).dt.to_period("W").dt.start_time
    g = rows.assign(week=week).groupby("week")
    out = g.agg(fills=(col, "size"), median=(col, "median"), mean=(col, "mean"),
                notional=("notional", "sum")).reset_index()
    out["share_negative"] = g[col].apply(lambda x: float(np.mean(x.to_numpy() < 0))).to_numpy()
    return out


def waterfall_components(rows: pd.DataFrame, taker_class: str = None) -> pd.DataFrame:
    """Half spread, adverse selection, fee, rebate and hedge that add up to the net edge."""
    g = rows if taker_class is None else rows[rows["taker_class"] == taker_class]
    steps = [("half spread", float(np.nanmean(g["hs"]))),
             ("adverse selection", float(np.nanmean(g["as_usd"]))),
             ("maker fee", -float(np.nanmean(g["fee_maker"]))),
             ("maker rebate", float(np.nanmean(g["rebate_maker"]))),
             ("hedge cost", -float(np.nanmean(g["hedge"])))]
    total = sum(v for _, v in steps)
    steps.append(("net edge", total))
    return pd.DataFrame(steps, columns=["step", "value"]).assign(fills=int(len(g)), taker_class=taker_class or "all")


def example_fill(rows: pd.DataFrame, taker_class: str = "other", horizon: str = "30m") -> pd.Series:
    """A median-sized fill that earned the half spread and then lost it: the schematic's example.

    The schematic only teaches the decomposition if the example shows both parts with the sign the paper
    argues about, so the search is narrowed to fills with ``hs > 0`` and a negative markout before the
    median-size rule picks one.  Without such a fill the narrowing is dropped rather than returning nothing.
    """
    col = UNIT_COLUMN["usd"].format(horizon)
    g = rows[(rows["taker_class"] == taker_class) & np.isfinite(rows[col])]
    if g.empty:
        g = rows[np.isfinite(rows[col])]
    teaching = g[(g["hs"] > 0) & (g[col] < -g["hs"])] if "hs" in g else g.iloc[:0]
    if not teaching.empty:
        g = teaching
    target = g["notional"].median()
    order = (g["notional"] - target).abs()
    return g.loc[order.sort_values().index[0]]


def curve_at(svi: pd.DataFrame, expiry: int, at_s: float, points: int = 96,
             span: Tuple[float, float] = (0.6, 1.6)) -> Dict[str, object]:
    """The last on-chain SVI curve pushed for one expiry at or before ``at_s``, on a strike grid.

    Derive's mark is this curve, so a figure that wants to show what the maker was quoting against has to
    take the curve as of the fill, not the freshest one.  ``None`` when nothing had been pushed yet.
    """
    pushed = svi[(svi["expiry"] == expiry) & (svi["block_ts"] <= at_s)]
    if pushed.empty:
        return None
    c = pushed.sort_values("block_ts").iloc[-1]
    strike = np.linspace(span[0], span[1], points) * float(c["svi_fwd"])
    vol = svi_vol(strike, c["svi_a"], c["svi_b"], c["svi_rho"], c["svi_m"], c["svi_sigma"],
                  c["svi_fwd"], c["svi_ref_tau"])
    return {"strike": strike, "k": np.log(strike / float(c["svi_fwd"])), "vol": vol,
            "forward": float(c["svi_fwd"]), "block_ts": int(c["block_ts"]),
            "age_s": float(at_s - float(c["block_ts"])), "ref_tau": float(c["svi_ref_tau"])}
