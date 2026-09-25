"""H4 of Paper 2 (price of capital): event regression, wild cluster bootstrap and placebo dates.

Preregistration ``docs/paper2/PRAEREGISTRIERUNG.md`` (H4, Inferenz, Nachtrag 3 points 3 and 4, Nachtrag 4 point 3):

* **Regression** on the panel of :mod:`derive_surface.p2events` (``data/p2/derived/h4_panel.parquet``):
  ``y_i = alpha_{cell, event} + gamma_{day, currency} + beta * post_i * dose_{cell, event} + e_i``. Both fixed effects
  are removed by alternating projections (``demean_two_way``) until the group means of the first set are below
  ``tol`` times the RMS of the column; ``beta`` is the within OLS. Cluster-robust SE by UTC day with the factor
  ``G / (G - 1)``.
* **Wild cluster bootstrap** with restricted residuals (``beta = 0``), Rademacher weights per UTC day, ``B = 9 999``,
  seed 20260924. Every bootstrap sample ``y* = FE_r + w_g u_r`` is refitted with both fixed effects (they are not
  nested in the day clusters): ``M_D(w * u_r) = sum_h w_h M_D(u_r * 1_h)`` is precomputed once per cluster ``h``, so
  a draw costs ``O(G^2)``. One-sided ``p = (1 + #{t* >= t}) / (B + 1)`` for ``beta > 0``. The interval ``lo, hi``
  is the 90 % percentile interval of the same draws with unrestricted residuals (descriptive; the verdict uses ``p``).
* **Placebo** (Nachtrag 3.3): 100 replications. For every kept event a date is drawn uniformly from the admissible
  days of its currency: at least 28 days from every parameter change of the currency (every row of the timelines of
  the H4 managers, also changes that are not events, Nachtrag 4.3), placebo time inside the window of the event's
  manager, ``[t - 14 d, t + 14 d]`` inside the sample. The placebo time keeps the time of day of the real event. The
  date gets the dose vector of a uniformly drawn kept event of the same currency. The panel is built with
  :func:`derive_surface.p2events.build_panel` and ``beta`` is estimated as above.
* **Verdict:** rejected if not (``beta > 0`` and ``p <= 0.05``) or if ``beta`` is not above the 95th percentile
  (numpy, linear) of the finite placebo betas.

Outputs: ``results/p2/h4.json``, ``h4_placebo.csv``, ``fig_h4_events.csv`` and the exploratory
``sensitivity_h4.json`` (per currency; without cells with ``|dose| > 1``; placebo dates at a distance from all
timelines of the currency including SM and account libs). The placebo stage is resumable
(``data/p2/derived/h4_placebo/``)::

    python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface.inference_p2_h4 run --max-seconds 420
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import scipy.sparse as sp

from . import p2events

REPO = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO / "results" / "p2"
PARTS_DIR = REPO / "data" / "p2" / "derived" / "h4_placebo"
PARAMS_DIR = REPO / "results" / "p2" / "params"

B = 9_999
SEED = 20_260_924
LEVEL = 0.90
ALPHA = 0.05
N_PLACEBO = 100
PLACEBO_PERCENTILE = 95.0
GAP_DAYS = 28
WINDOW_DAYS = p2events.WINDOW_DAYS
OUTLIER_ABS_DOSE = 1.0
TOL = 1e-12
DAY = 86_400

RULE = ("rejected if not (beta > 0 and one-sided wild cluster bootstrap p <= 0.05) or if beta is not above the "
        "95th percentile of the placebo betas (100 placebo replications)")
PLACEBO_COLUMNS = ["rep", "beta", "se", "t", "n", "cell_events", "events_with_cells", "clusters", "beta_no_outlier",
                   "n_no_outlier", "draws"]
PART_COLUMNS = PLACEBO_COLUMNS + ["fingerprint"]
FIG_COLUMNS = (["event_id", "ccy", "manager", "event_day", "event_utc", "kinds", "n_cells", "n_pre", "n_post",
                "median_dose"]
               + [f"t{k}_{c}" for k in (1, 2, 3) for c in ("cells", "dose_lo", "dose_hi", "median_dose", "n_pre",
                                                           "n_post", "y_pre", "y_post")])
VARIANTS = {"main": "event", "all_timelines": "all"}
READINGS = [
    "fixed effects alpha per (cell, event) and gamma per (UTC day, currency), removed by alternating projections",
    "cluster-robust SE by UTC day with factor G/(G-1); p = (1 + #{t* >= t}) / (B + 1), one-sided for beta > 0",
    "lo/hi: 90 % percentile interval of the wild cluster bootstrap with unrestricted residuals (same weights)",
    "placebo gap: every row of the parameter timelines of the H4 managers of the currency (legacy PM, PM2 standard "
    "lib), incl. collateral, maxExpiries and dropped events; distance in UTC days >= 28",
    "placebo date inside the window of the replaced event's manager and [t - 14 d, t + 14 d] inside "
    "[2024-01-11 00:00, last fill of the sample]; time of day of the replaced event",
    "placebo dose vector: uniformly drawn kept event of the same currency (the replaced event included)",
    "95th percentile: numpy.quantile (linear) over the finite placebo betas",
]


# =====================================================================================================================
# Two-way within estimator
# =====================================================================================================================

@dataclass
class Design:
    x: np.ndarray             # post * dose
    y: np.ndarray             # y_hs_bp
    codes_a: np.ndarray       # (cell, event)
    codes_b: np.ndarray       # (day, currency)
    clusters: np.ndarray      # UTC day
    n_clusters: int


@dataclass
class Fit:
    beta: float
    se: float
    t: float
    n: int
    n_clusters: int
    xtx: float
    iterations: int
    design: Design
    xd: np.ndarray
    yd: np.ndarray
    resid: np.ndarray


def design(panel: pd.DataFrame) -> Design:
    """Regressor, outcome, fixed-effect groups and day clusters of an H4 panel (``p2events.PANEL_COLUMNS``)."""
    cell_event = panel["cell"].astype(str) + "\x1f" + panel["event_id"].astype(str)
    day_ccy = panel["day"].astype(str) + "\x1f" + panel["ccy"].astype(str)
    codes_a = pd.factorize(cell_event, sort=True)[0]
    codes_b = pd.factorize(day_ccy, sort=True)[0]
    clusters, uniq = pd.factorize(panel["day"].astype(str), sort=True)
    x = panel["post"].to_numpy(bool).astype(float) * panel["dose"].to_numpy(float)
    return Design(x=x, y=panel["y_hs_bp"].to_numpy(float), codes_a=np.asarray(codes_a, dtype=np.int64),
                  codes_b=np.asarray(codes_b, dtype=np.int64), clusters=np.asarray(clusters, dtype=np.int64),
                  n_clusters=int(len(uniq)))


def _indicator(codes: np.ndarray, n_groups: Optional[int] = None) -> sp.csr_matrix:
    n = len(codes)
    k = int(codes.max()) + 1 if n_groups is None else n_groups
    return sp.csr_matrix((np.ones(n), (np.arange(n), codes)), shape=(n, k))


def demean_two_way(V: np.ndarray, codes_a: np.ndarray, codes_b: np.ndarray, tol: float = TOL,
                   max_iter: int = 100_000) -> Tuple[np.ndarray, int]:
    """Residual of every column of ``V`` on the dummies of both groupings, by alternating projections.

    One sweep subtracts the group means of ``codes_a`` and then of ``codes_b``; it stops when every group mean of
    ``codes_a`` is at most ``tol`` times the RMS of the original column (the ``codes_b`` means are then zero)."""
    V = np.array(V, dtype=float, copy=True)
    one_d = V.ndim == 1
    if one_d:
        V = V[:, None]
    if len(V) == 0:
        return (V[:, 0] if one_d else V), 0
    A, Bm = _indicator(codes_a), _indicator(codes_b)
    ca = np.asarray(A.sum(axis=0)).ravel()
    cb = np.asarray(Bm.sum(axis=0)).ravel()
    scale = np.sqrt((V ** 2).mean(axis=0))
    scale[scale == 0] = 1.0
    with np.errstate(all="ignore"):  # numpy 2 reports spurious FP flags from BLAS on these products
        for it in range(1, max_iter + 1):
            V -= A @ ((A.T @ V) / ca[:, None])
            V -= Bm @ ((Bm.T @ V) / cb[:, None])
            worst = np.abs((A.T @ V) / ca[:, None]).max(axis=0)
            if np.all(worst <= tol * scale):
                return (V[:, 0] if one_d else V), it
    raise RuntimeError(f"alternating projections did not converge in {max_iter} sweeps")


def demean_exact(V: np.ndarray, codes_a: np.ndarray, codes_b: np.ndarray) -> np.ndarray:
    """Same residual by a direct least-squares solve on both dummy sets (check of the alternating projections)."""
    D = sp.hstack([_indicator(codes_a), _indicator(codes_b)]).tocsr()
    with np.errstate(all="ignore"):
        P = np.linalg.pinv((D.T @ D).toarray())
        return np.asarray(V, dtype=float) - D @ (P @ (D.T @ np.asarray(V, dtype=float)))


def _nan_fit(d: Design, iterations: int = 0) -> Fit:
    z = np.zeros(len(d.x))
    return Fit(beta=np.nan, se=np.nan, t=np.nan, n=int(len(d.x)), n_clusters=d.n_clusters, xtx=0.0,
               iterations=iterations, design=d, xd=z, yd=z, resid=z)


def fit(panel: pd.DataFrame, tol: float = TOL) -> Fit:
    """Within OLS of ``y_hs_bp`` on ``post * dose`` with both fixed effects; cluster-robust SE by UTC day."""
    d = design(panel)
    if len(d.x) == 0:
        return _nan_fit(d)
    V, iters = demean_two_way(np.column_stack([d.x, d.y]), d.codes_a, d.codes_b, tol=tol)
    xd, yd = V[:, 0], V[:, 1]
    with np.errstate(all="ignore"):  # numpy 2 reports spurious FP flags from BLAS dot products
        xtx = float(np.dot(xd, xd))
        xx = float(np.dot(d.x, d.x))
        xty = float(np.dot(xd, yd))
    if not np.isfinite(xtx) or xtx <= 1e-20 * max(1.0, xx):
        return _nan_fit(d, iters)
    beta = xty / xtx
    resid = yd - xd * beta
    g = d.n_clusters
    scores = np.bincount(d.clusters, weights=xd * resid, minlength=g)
    se = float(np.sqrt(g / max(g - 1, 1) * float((scores ** 2).sum()))) / xtx
    t = beta / se if se > 0 else np.nan
    return Fit(beta=beta, se=se, t=t, n=int(len(d.x)), n_clusters=g, xtx=xtx, iterations=iters, design=d, xd=xd,
               yd=yd, resid=resid)


# =====================================================================================================================
# Wild cluster bootstrap
# =====================================================================================================================

def wcr_prepare(f: Fit, tol: float = TOL) -> dict:
    """Per-cluster statistics of the restricted wild bootstrap (beta = 0, restricted residuals ``u = M_D y``).

    ``C[g, h] = sum_{i in g} xd_i [M_D(u * 1_h)]_i``, ``Q[g] = sum_{i in g} xd_i^2``, ``a[h] = sum_{i in h} xd_i u_i``."""
    d = f.design
    n, g = len(d.x), d.n_clusters
    U = np.zeros((n, g))
    U[np.arange(n), d.clusters] = f.yd
    V, iters = demean_two_way(U, d.codes_a, d.codes_b, tol=tol)
    S = _indicator(d.clusters, g).T.tocsr()
    with np.errstate(all="ignore"):
        C = np.asarray(S @ (f.xd[:, None] * V))
    del U, V
    return {"C": C, "Q": np.bincount(d.clusters, weights=f.xd ** 2, minlength=g),
            "a": np.bincount(d.clusters, weights=f.xd * f.yd, minlength=g), "xtx": f.xtx, "G": g,
            "iterations": iters}


def wcr_draws(prep: Mapping, W: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """``beta*`` and ``t*`` of the refitted bootstrap samples for the weight rows ``W`` (draws x clusters)."""
    W = np.atleast_2d(np.asarray(W, dtype=float))
    xtx, g = prep["xtx"], prep["G"]
    with np.errstate(all="ignore"):
        beta = W @ prep["a"] / xtx
        scores = W @ prep["C"].T - beta[:, None] * prep["Q"][None, :]
        se = np.sqrt(g / max(g - 1, 1) * (scores ** 2).sum(axis=1)) / xtx
        t = np.where(se > 0, beta / np.where(se > 0, se, 1.0), np.nan)
    return beta, t


def wcu_draws(f: Fit, W: np.ndarray) -> np.ndarray:
    """``beta*`` with unrestricted residuals: ``beta + sum_h w_h (xd_h' e_h) / xd'xd``."""
    h = np.bincount(f.design.clusters, weights=f.xd * f.resid, minlength=f.n_clusters)
    with np.errstate(all="ignore"):
        return f.beta + np.atleast_2d(np.asarray(W, dtype=float)) @ h / f.xtx


def wild_cluster_test(f: Fit, b: int = B, seed: int = SEED, level: float = LEVEL) -> dict:
    """One-sided wild cluster bootstrap test of ``beta > 0`` (restricted residuals, Rademacher per day) plus the
    percentile interval of the unrestricted draws."""
    out = {"beta": f.beta, "se": f.se, "t": f.t, "p": np.nan, "lo": np.nan, "hi": np.nan, "n": f.n,
           "clusters": f.n_clusters, "b": int(b), "seed": int(seed), "level": level, "fe_iterations": f.iterations}
    if not np.isfinite(f.t):
        return out
    rng = np.random.default_rng(seed)
    W = rng.choice(np.array([-1.0, 1.0]), size=(b, f.n_clusters))
    prep = wcr_prepare(f)
    _, t_star = wcr_draws(prep, W)
    extreme = int(np.sum(np.isfinite(t_star) & (t_star >= f.t)))
    beta_u = wcu_draws(f, W)
    a = (1.0 - level) / 2.0
    out.update(p=(1 + extreme) / (b + 1), lo=float(np.quantile(beta_u, a)), hi=float(np.quantile(beta_u, 1 - a)),
               bootstrap_fe_iterations=prep["iterations"])
    return out


# =====================================================================================================================
# Placebo calendar
# =====================================================================================================================

def _timeline_files(ccy: str, root: Path, scope: str) -> List[Path]:
    if scope == "event":
        return [root / f"{ccy}_{m}.json" for m in p2events.EVENT_MANAGERS[ccy]]
    if scope == "all":
        return sorted(p for p in root.glob(f"{ccy}_*.json") if not p.name.endswith("_overrides.json"))
    raise ValueError(f"unknown scope {scope!r}")


def change_days(ccy: str, root: Optional[Path] = None, scope: str = "event") -> np.ndarray:
    """UTC day numbers (``ts // 86400``) of every row of the parameter timelines of ``ccy``.

    ``scope="event"``: the timelines of the H4 managers (legacy PM, PM2 standard lib; Nachtrag 4.3).
    ``scope="all"``: every timeline of the currency, also SM and the PM2 account libs (sensitivity)."""
    root = Path(root) if root is not None else PARAMS_DIR
    days = set()
    for path in _timeline_files(ccy, root, scope):
        if not path.exists():
            continue
        for row in json.loads(path.read_text()):
            days.add(int(row["from_ts"]) // DAY)
    return np.array(sorted(days), dtype=np.int64)


def admissible_days(event_ts: int, window: Tuple[int, int], changes: np.ndarray, sample: Tuple[int, int],
                    gap_days: int = GAP_DAYS, window_days: int = WINDOW_DAYS) -> np.ndarray:
    """UTC day numbers ``D`` for a placebo of an event at ``event_ts``: time ``t = D + time of day of the event``
    inside the manager ``window``, ``[t - window_days, t + window_days]`` inside ``sample``, and at least
    ``gap_days`` UTC days from every change day."""
    tod = int(event_ts) % DAY
    lo = max(int(window[0]), int(sample[0]) + window_days * DAY)
    hi = min(int(window[1]), int(sample[1]) - window_days * DAY)
    d0 = -((tod - lo) // DAY)            # ceil((lo - tod) / DAY)
    d1 = (hi - tod) // DAY
    days = np.arange(d0, d1 + 1, dtype=np.int64)
    ch = np.asarray(changes, dtype=np.int64)
    if len(days) and len(ch):
        ch = np.sort(ch)
        i = np.searchsorted(ch, days)
        left = np.abs(days - ch[np.clip(i - 1, 0, len(ch) - 1)])
        right = np.abs(ch[np.clip(i, 0, len(ch) - 1)] - days)
        days = days[np.minimum(left, right) >= gap_days]
    return days


def draw_placebos(kept: pd.DataFrame, days: Mapping[str, np.ndarray], n_rep: int = N_PLACEBO,
                  seed: int = SEED) -> List[List[dict]]:
    """Placebo dates and dose sources. For every replication and every kept event (in the order of ``kept``): a day
    uniformly from ``days[event_id]``, then the source of the dose vector uniformly from the kept events of the same
    currency. The placebo time keeps the time of day of the real event."""
    for ev in kept.itertuples():
        if len(days[ev.event_id]) == 0:
            raise ValueError(f"no admissible placebo day for {ev.event_id}")
    by_ccy: Dict[str, List[str]] = {}
    for ev in kept.itertuples():
        by_ccy.setdefault(ev.ccy, []).append(ev.event_id)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_rep):
        rep = []
        for ev in kept.itertuples():
            dd = days[ev.event_id]
            day = int(dd[rng.integers(len(dd))])
            src = by_ccy[ev.ccy][int(rng.integers(len(by_ccy[ev.ccy])))]
            rep.append({"event_id": ev.event_id, "ccy": ev.ccy, "placebo_ts": day * DAY + int(ev.event_ts) % DAY,
                        "source": src})
        out.append(rep)
    return out


def draws_string(rep: Sequence[Mapping]) -> str:
    return ";".join(f"{d['event_id']}@{pd.Timestamp(int(d['placebo_ts']), unit='s', tz='UTC').strftime('%Y-%m-%d')}"
                    f"@{d['source']}" for d in rep)


def split_frame(frame: pd.DataFrame) -> Dict[str, Tuple[pd.DataFrame, np.ndarray]]:
    """Per currency: fills sorted by taker time (only the columns of ``build_panel``) and their times in ms."""
    cols = ["fill_key", "ts", "ccy", "cell", "y_hs_bp", "day"]
    out = {}
    for ccy, g in frame[cols].groupby("ccy", sort=True):
        g = g.sort_values("ts", kind="mergesort").reset_index(drop=True)
        out[ccy] = (g, g["ts"].to_numpy(np.int64))
    return out


def placebo_panel(frames: Mapping[str, Tuple[pd.DataFrame, np.ndarray]], rep_draws: Sequence[Mapping],
                  vectors: Mapping[str, pd.Series], rep: int) -> pd.DataFrame:
    """Panel of one placebo replication, built with :func:`p2events.build_panel` for every drawn date (the frame is
    cut to the window first, which leaves the result unchanged)."""
    parts = []
    for d in rep_draws:
        fr, ts = frames[d["ccy"]]
        t = int(d["placebo_ts"])
        i0 = np.searchsorted(ts, (t - WINDOW_DAYS * DAY) * 1000, side="left")
        i1 = np.searchsorted(ts, (t + WINDOW_DAYS * DAY) * 1000, side="right")
        parts.append(p2events.build_panel(fr.iloc[i0:i1], d["ccy"], t, vectors.get(d["source"], pd.Series(dtype=float)),
                                          f"P{rep:03d}:{d['event_id']}"))
    parts = [p for p in parts if len(p)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=p2events.PANEL_COLUMNS)


def drop_outlier_cells(panel: pd.DataFrame, max_abs_dose: float = OUTLIER_ABS_DOSE) -> pd.DataFrame:
    """Panel without the cells whose |dose| exceeds ``max_abs_dose``."""
    return panel[panel["dose"].astype(float).abs() <= max_abs_dose].reset_index(drop=True)


# =====================================================================================================================
# Verdict and tables
# =====================================================================================================================

def placebo_summary(betas: Sequence[float], beta: float, percentile: float = PLACEBO_PERCENTILE) -> dict:
    """95th percentile (numpy, linear) of the finite placebo betas and the share at or above ``beta``."""
    b = np.asarray(betas, dtype=float)
    fin = b[np.isfinite(b)]
    if len(fin) == 0:
        return {"n": int(len(b)), "finite": 0, "p95": np.nan, "share_ge_beta": np.nan, "median": np.nan,
                "mean": np.nan, "min": np.nan, "max": np.nan}
    return {"n": int(len(b)), "finite": int(len(fin)), "p95": float(np.quantile(fin, percentile / 100.0)),
            "share_ge_beta": float(np.mean(fin >= beta)) if np.isfinite(beta) else np.nan,
            "median": float(np.median(fin)), "mean": float(fin.mean()), "min": float(fin.min()),
            "max": float(fin.max())}


def verdict(beta: float, p: float, p95: float, alpha: float = ALPHA) -> dict:
    """Preregistered rule: rejected unless beta > 0, p <= alpha and beta above the placebo 95th percentile."""
    crit = {"beta_positive": bool(np.isfinite(beta) and beta > 0),
            "p_le_alpha": bool(np.isfinite(p) and p <= alpha),
            "beta_gt_placebo_p95": bool(np.isfinite(beta) and np.isfinite(p95) and beta > p95)}
    rejected = not (crit["beta_positive"] and crit["p_le_alpha"]) or not crit["beta_gt_placebo_p95"]
    return {"rejected": bool(rejected), "criteria": crit}


def event_figure_table(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Per kept event: date, currency, median dose over its panel cells and the mean ``y`` before and after in the
    dose terciles (cells ranked by dose, ties by cell label; tercile 1 = most negative dose, i.e. the largest
    decrease of capital)."""
    ev = events[events["kept"].astype(bool)] if "kept" in events else events
    rows = []
    for e in ev.itertuples():
        p = panel[panel["event_id"] == e.event_id]
        row = {"event_id": e.event_id, "ccy": e.ccy, "manager": e.manager, "event_day": e.event_day,
               "event_utc": e.event_utc, "kinds": e.kinds, "n_cells": int(p["cell"].nunique()),
               "n_pre": int((~p["post"].astype(bool)).sum()), "n_post": int(p["post"].astype(bool).sum()),
               "median_dose": np.nan}
        if len(p):
            doses = p.groupby("cell")["dose"].first().reset_index().sort_values(["dose", "cell"], kind="mergesort")
            row["median_dose"] = float(doses["dose"].median())
            for k, part in enumerate(np.array_split(np.arange(len(doses)), 3), start=1):
                cells = doses.iloc[part]
                q = p[p["cell"].isin(cells["cell"])]
                post = q["post"].astype(bool)
                row.update({f"t{k}_cells": int(len(cells)),
                            f"t{k}_dose_lo": float(cells["dose"].min()) if len(cells) else np.nan,
                            f"t{k}_dose_hi": float(cells["dose"].max()) if len(cells) else np.nan,
                            f"t{k}_median_dose": float(cells["dose"].median()) if len(cells) else np.nan,
                            f"t{k}_n_pre": int((~post).sum()), f"t{k}_n_post": int(post.sum()),
                            f"t{k}_y_pre": float(q.loc[~post, "y_hs_bp"].mean()) if (~post).any() else np.nan,
                            f"t{k}_y_post": float(q.loc[post, "y_hs_bp"].mean()) if post.any() else np.nan})
        rows.append(row)
    out = pd.DataFrame(rows, columns=FIG_COLUMNS)
    for k in (1, 2, 3):
        out[f"t{k}_cells"] = out[f"t{k}_cells"].fillna(0).astype(int)
    return out


# =====================================================================================================================
# Run (resumable placebo stage) and CLI
# =====================================================================================================================

def _clean(obj):
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return v if np.isfinite(v) else None
    return obj


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(obj), indent=1, sort_keys=False) + "\n")


def _fingerprint(frame: pd.DataFrame, kept: pd.DataFrame, doses: pd.DataFrame, seed: int,
                 sample: Tuple[int, int]) -> str:
    d = doses[np.isfinite(doses["dose"].astype(float))].sort_values(["event_id", "cell"])
    payload = {"frame_n": int(len(frame)), "frame_ts_max": int(frame["ts"].max()) if len(frame) else 0,
               "frame_y_sum": round(float(np.nansum(frame["y_hs_bp"].to_numpy(float))), 6),
               "kept": [f"{e.event_id}:{int(e.event_ts)}" for e in kept.itertuples()],
               "doses": [f"{r.event_id}|{r.cell}|{float(r.dose):.15e}" for r in d.itertuples()],
               "seed": int(seed), "sample": [int(sample[0]), int(sample[1])]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _load_parts(path: Path, fingerprint: str, draws: Sequence[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=PART_COLUMNS)
    parts = pd.read_csv(path, dtype={"fingerprint": str, "draws": str})
    if len(parts) and (parts["fingerprint"] != fingerprint).any():
        raise RuntimeError(f"stale placebo parts in {path} (data or events changed); delete {path.parent} and rerun")
    parts = parts.drop_duplicates("rep", keep="last")
    for r in parts.itertuples():
        if int(r.rep) >= len(draws) or r.draws != draws[int(r.rep)]:
            raise RuntimeError(f"stale placebo parts in {path} (draw of rep {int(r.rep)} differs); delete and rerun")
    return parts


def _placebo_row(frames, rep_draws, vectors, rep: int) -> dict:
    panel = placebo_panel(frames, rep_draws, vectors, rep)
    f = fit(panel)
    q = drop_outlier_cells(panel)
    fq = fit(q) if len(q) < len(panel) else f
    return {"rep": rep, "beta": f.beta, "se": f.se, "t": f.t, "n": f.n,
            "cell_events": int(panel.groupby(["cell", "event_id"]).ngroups) if len(panel) else 0,
            "events_with_cells": int(panel["event_id"].nunique()) if len(panel) else 0, "clusters": f.n_clusters,
            "beta_no_outlier": fq.beta, "n_no_outlier": fq.n, "draws": draws_string(rep_draws)}


def _panel_check(stored: pd.DataFrame, frame: pd.DataFrame, kept: pd.DataFrame,
                 vectors: Mapping[str, pd.Series]) -> dict:
    """Rebuild the panel of the real events with ``build_panel`` and compare it with the stored panel."""
    parts = [p2events.build_panel(frame, e.ccy, int(e.event_ts), vectors.get(e.event_id, pd.Series(dtype=float)),
                                  e.event_id) for e in kept.itertuples()]
    parts = [p for p in parts if len(p)]
    rebuilt = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=p2events.PANEL_COLUMNS)
    key = ["event_id", "fill_key"]
    a = stored.sort_values(key, kind="mergesort").reset_index(drop=True)
    b = rebuilt.sort_values(key, kind="mergesort").reset_index(drop=True)
    same = len(a) == len(b)
    diff_y = diff_d = np.nan
    if same and len(a):
        same = bool((a[["event_id", "fill_key", "cell", "day", "ccy"]].astype(str).to_numpy()
                     == b[["event_id", "fill_key", "cell", "day", "ccy"]].astype(str).to_numpy()).all()
                    and (a["post"].astype(bool).to_numpy() == b["post"].astype(bool).to_numpy()).all())
        diff_y = float(np.max(np.abs(a["y_hs_bp"].to_numpy(float) - b["y_hs_bp"].to_numpy(float))))
        diff_d = float(np.max(np.abs(a["dose"].to_numpy(float) - b["dose"].to_numpy(float))))
        same = same and diff_y <= 1e-9 and diff_d <= 1e-12
    return {"equal": bool(same), "rows_stored": int(len(a)), "rows_rebuilt": int(len(b)), "max_abs_diff_y": diff_y,
            "max_abs_diff_dose": diff_d}


def run(b: int = B, n_placebo: int = N_PLACEBO, seed: int = SEED, max_seconds: Optional[float] = None,
        frame: Optional[pd.DataFrame] = None, events: Optional[pd.DataFrame] = None,
        doses: Optional[pd.DataFrame] = None, panel: Optional[pd.DataFrame] = None,
        params_root: Optional[Path] = None, out_dir: Path = RESULTS_DIR, parts_dir: Path = PARTS_DIR,
        dose_dir: Path = p2events.DOSE_DIR, panel_path: Path = p2events.PANEL_PATH) -> dict:
    """H4 with placebo and sensitivities. The placebo stage is resumable; the outputs are written once all
    replications of every variant are done (``status`` DONE, else PARTIAL)."""
    t0 = time.monotonic()
    if events is None or doses is None:
        ev_list = p2events.event_list(root=params_root)
        doses = p2events.load_doses(ev_list, dose_dir) if doses is None else doses
        events = p2events.flag_events(ev_list, doses) if events is None else events
    if panel is None:
        panel = pd.read_parquet(panel_path)
    if frame is None:
        frame = p2events.load_frame()
    kept = (events[events["kept"].astype(bool)].sort_values(["ccy", "event_ts"], kind="mergesort")
            .reset_index(drop=True))
    vectors = p2events.dose_vectors(doses)
    sample = (p2events.SAMPLE_START_TS, min(p2events.SAMPLE_END_TS, int(frame["ts"].max()) // 1000))
    fp = _fingerprint(frame, kept, doses, seed, sample)
    frames = split_frame(frame)

    parts_dir.mkdir(parents=True, exist_ok=True)
    placebo: Dict[str, pd.DataFrame] = {}
    days_info: Dict[str, dict] = {}
    new = 0
    complete = True
    for variant, scope in VARIANTS.items():
        changes = {c: change_days(c, root=params_root, scope=scope) for c in sorted(set(kept["ccy"]))}
        days = {e.event_id: admissible_days(int(e.event_ts), p2events.manager_window(e.ccy, e.manager),
                                            changes[e.ccy], sample) for e in kept.itertuples()}
        days_info[variant] = {k: {"days": int(len(v)),
                                  "first": pd.Timestamp(int(v.min()) * DAY, unit="s").strftime("%Y-%m-%d")
                                  if len(v) else None,
                                  "last": pd.Timestamp(int(v.max()) * DAY, unit="s").strftime("%Y-%m-%d")
                                  if len(v) else None} for k, v in days.items()}
        draws = draw_placebos(kept, days, n_placebo, seed)
        dstr = [draws_string(r) for r in draws]
        path = parts_dir / f"{variant}.csv"
        parts = _load_parts(path, fp, dstr)
        done = set(int(r) for r in parts["rep"])
        for rep in range(n_placebo):
            if rep in done:
                continue
            if max_seconds is not None and new > 0 and time.monotonic() - t0 > max_seconds:
                complete = False
                break
            row = _placebo_row(frames, draws[rep], vectors, rep)
            row["fingerprint"] = fp
            pd.DataFrame([row], columns=PART_COLUMNS).to_csv(path, mode="a", header=not path.exists(), index=False)
            new += 1
        parts = _load_parts(path, fp, dstr)
        parts = parts[parts["rep"].astype(int) < n_placebo].sort_values("rep").reset_index(drop=True)
        if len(parts) < n_placebo:
            complete = False
        placebo[variant] = parts
        if not complete:
            break
    if not complete:
        return {"status": "PARTIAL", "placebo_new": new,
                "placebo_done": {k: int(len(v)) for k, v in placebo.items()}, "seconds": time.monotonic() - t0}

    # ---- main estimate on the stored panel
    f = fit(panel)
    test = wild_cluster_test(f, b=b, seed=seed)
    exact = demean_exact(np.column_stack([f.design.x, f.design.y]), f.design.codes_a, f.design.codes_b)
    xe, ye = exact[:, 0], exact[:, 1]
    with np.errstate(all="ignore"):
        xex = float(np.dot(xe, xe))
        beta_exact = float(np.dot(xe, ye)) / xex if xex > 0 else np.nan
    main_pl = placebo["main"]
    ps = placebo_summary(main_pl["beta"].to_numpy(float), f.beta)
    v = verdict(f.beta, test["p"], ps["p95"])
    ps.update({"timelines": "legacy PM and PM2 standard lib of the currency, every row", "gap_days": GAP_DAYS,
               "seed": seed, "admissible_days": days_info["main"]})
    h4 = {"hypothesis": "H4", "stat": f.beta, "lo": test["lo"], "hi": test["hi"], "rejected": v["rejected"],
          "rule": RULE, "n": f.n, "se": f.se, "t": f.t, "p": test["p"], "p_sided": "one-sided, beta > 0",
          "b": b, "seed": seed, "level": LEVEL,
          "interval": "90 % percentile interval, wild cluster bootstrap with unrestricted residuals (descriptive)",
          "clusters": f.n_clusters, "fills": int(panel["fill_key"].nunique()),
          "events": int(panel["event_id"].nunique()), "events_kept": int(len(kept)),
          "cell_events": int(panel.groupby(["cell", "event_id"]).ngroups),
          "day_ccy": int(panel.groupby(["day", "ccy"]).ngroups),
          "criteria": v["criteria"], "placebo": ps,
          "fe": {"method": "alternating projections", "tol": TOL, "iterations": f.iterations,
                 "bootstrap_iterations": test.get("bootstrap_fe_iterations"),
                 "beta_direct_solve": beta_exact, "abs_diff_beta_direct_solve": abs(beta_exact - f.beta)},
          "panel_check": _panel_check(panel, frame, kept, vectors),
          "sample": [pd.Timestamp(sample[0], unit="s", tz="UTC").isoformat(),
                     pd.Timestamp(sample[1], unit="s", tz="UTC").isoformat()],
          "readings": READINGS}

    # ---- exploratory
    by_ccy = {}
    for ccy in sorted(panel["ccy"].unique()):
        sub = panel[panel["ccy"] == ccy].reset_index(drop=True)
        by_ccy[ccy] = wild_cluster_test(fit(sub), b=b, seed=seed)
        by_ccy[ccy].update(events=int(sub["event_id"].nunique()), cell_events=int(sub.groupby(["cell", "event_id"]).ngroups))
    trimmed = drop_outlier_cells(panel)
    t_trim = test if len(trimmed) == len(panel) else wild_cluster_test(fit(trimmed), b=b, seed=seed)
    ps_trim = placebo_summary(main_pl["beta_no_outlier"].to_numpy(float), t_trim["beta"])
    big = doses[np.abs(doses["dose"].astype(float)) > OUTLIER_ABS_DOSE]
    big = big[big["event_id"].isin(kept["event_id"])]
    all_pl = placebo["all_timelines"]
    ps_all = placebo_summary(all_pl["beta"].to_numpy(float), f.beta)
    sens = {"exploratory": True, "hypothesis": "H4", "b": b, "seed": seed,
            "by_ccy": by_ccy,
            "no_outlier_cells": {"max_abs_dose": OUTLIER_ABS_DOSE,
                                 "dose_cells_above": [{"event_id": r.event_id, "cell": r.cell, "dose": float(r.dose)}
                                                      for r in big.itertuples()],
                                 "rows_dropped_real_panel": int(len(panel) - len(trimmed)), "h4": t_trim,
                                 "placebo": ps_trim, "placebo_betas": main_pl["beta_no_outlier"].tolist(),
                                 **verdict(t_trim["beta"], t_trim["p"], ps_trim["p95"])},
            "placebo_all_timelines": {"timelines": "every timeline of the currency (SM, legacy PM, PM2 standard "
                                                   "lib and account libs), every row",
                                      "placebo": ps_all, "admissible_days": days_info["all_timelines"],
                                      "placebo_betas": all_pl["beta"].tolist(),
                                      **verdict(f.beta, test["p"], ps_all["p95"])}}

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "h4.json", h4)
    main_pl[PLACEBO_COLUMNS].to_csv(out_dir / "h4_placebo.csv", index=False)
    event_figure_table(panel, kept).to_csv(out_dir / "fig_h4_events.csv", index=False)
    _write_json(out_dir / "sensitivity_h4.json", sens)
    return {"status": "DONE", "placebo_new": new, "beta": f.beta, "p": test["p"], "placebo_p95": ps["p95"],
            "rejected": v["rejected"], "seconds": time.monotonic() - t0}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface.inference_p2_h4")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="H4: regression, wild cluster bootstrap, placebo, sensitivities (resumable)")
    r.add_argument("--b", type=int, default=B)
    r.add_argument("--placebos", type=int, default=N_PLACEBO)
    r.add_argument("--seed", type=int, default=SEED)
    r.add_argument("--max-seconds", type=float, default=420.0)
    a = ap.parse_args(argv)
    res = run(b=a.b, n_placebo=a.placebos, seed=a.seed, max_seconds=a.max_seconds)
    print(json.dumps(_clean(res)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
