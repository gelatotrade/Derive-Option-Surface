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
timelines of the currency including SM and account libs; ``placebo_matched``: placebos only for the events with cells
in the real panel and with disjoint windows per currency; ``audit``: see below). The placebo stage is resumable
(``data/p2/derived/h4_placebo/``)::

    python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface.inference_p2_h4 run --max-seconds 420

Descriptive figure tables (ABBILDUNGSWAHL section 10; no registered number changes): ``fig_h4_fwl_bins.csv``, the
residualised regressor and outcome in 20 equal-count bins with their histogram and the slope ``beta``, and
``h4_placebo_days.csv``, the candidate placebo days of every kept event with the gap rule and the number of draws.
``run`` writes both; ``figtables`` rebuilds them from the stored panel and results without the placebo stage::

    python3 -m derive_surface.inference_p2_h4 figtables

Audit entries (docs/paper2/AUDIT.md; exploratory, no registered number changes), ``sensitivity_h4.json`` ``audit``:
``placebo_calibration`` (A05): the day-cluster SE and the wild bootstrap measure the noise at one given date, not the
spread from date to date; the placebo t give the reference distribution, their spread (``t_sd``) and the span
``beta - (t_p95, t_p05) * se`` with its reading for capital ten per cent cheaper. ``placebo_composition`` (A29): how
the placebo panels differ from the real one (an event without cells, overlapping windows). ``dose_robust`` (A30):
beta with the median log ratio per cell and with the mean without fills with ``|log ratio| > 1``
(``data/p2/derived/h4_doses/*_fills.parquet``). ``extras`` rebuilds ``review`` and ``audit`` from stored results.
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
from scipy.stats import norm

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
VARIANTS = {"main": "event", "all_timelines": "all", "matched": "event"}
SEP_DAYS = 2 * WINDOW_DAYS + 1          # placebo days of one currency this far apart have disjoint windows (A29)
TRIM_ABS_LOG_RATIO = 1.0                # dose sensitivity: fills with |log(K_after / K_before)| above left out (A30)
MEDIAN_DIFF = 0.05                      # dose sensitivity: pairs counted whose median and mean log ratio differ more
FWL_BINS = 20
FWL_HIST_BINS = 40
FWL_COLUMNS = ["kind", "bin", "x_mean", "y_mean", "n_rows", "n_fills", "x", "x_hi", "count", "fwl_slope"]
PLACEBO_DAY_COLUMNS = ["timeline", "ccy", "manager", "day", "admissible", "drawn_count"]
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


def draw_placebos_apart(kept: pd.DataFrame, days: Mapping[str, np.ndarray], n_rep: int = N_PLACEBO,
                        seed: int = SEED, sep_days: int = SEP_DAYS) -> List[List[dict]]:
    """Placebos with disjoint windows per currency (audit A29, exploratory; the registered draw is
    :func:`draw_placebos`). ``kept`` are the events to replace (in ``run``: those with cells in the real panel). Per
    replication the events are visited in a random order; each takes a day uniformly from its admissible days that
    are at least ``sep_days`` from the days already drawn for its currency in this replication (so no fill enters two
    placebo windows), or is left out when none is left; the dose vector comes uniformly from ``kept`` of the same
    currency. The list of a replication follows the order of ``kept``."""
    for ev in kept.itertuples():
        if len(days[ev.event_id]) == 0:
            raise ValueError(f"no admissible placebo day for {ev.event_id}")
    by_ccy: Dict[str, List[str]] = {}
    for ev in kept.itertuples():
        by_ccy.setdefault(ev.ccy, []).append(ev.event_id)
    evs = list(kept.itertuples())
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_rep):
        chosen: Dict[int, dict] = {}
        taken: Dict[str, List[int]] = {}
        for i in rng.permutation(len(evs)):
            ev = evs[int(i)]
            dd = np.asarray(days[ev.event_id], dtype=np.int64)
            prev = taken.get(ev.ccy)
            if prev:
                dd = dd[np.all(np.abs(dd[:, None] - np.asarray(prev, dtype=np.int64)[None, :]) >= sep_days, axis=1)]
            if len(dd) == 0:
                continue
            day = int(dd[rng.integers(len(dd))])
            src = by_ccy[ev.ccy][int(rng.integers(len(by_ccy[ev.ccy])))]
            taken.setdefault(ev.ccy, []).append(day)
            chosen[int(i)] = {"event_id": ev.event_id, "ccy": ev.ccy,
                              "placebo_ts": day * DAY + int(ev.event_ts) % DAY, "source": src}
        out.append([chosen[i] for i in sorted(chosen)])
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


def fwl_bins(panel: pd.DataFrame, n_bins: int = FWL_BINS, n_hist: int = FWL_HIST_BINS,
             f: Optional[Fit] = None) -> pd.DataFrame:
    """Descriptive picture of ``beta`` (Frisch-Waugh-Lovell, ABBILDUNGSWAHL section 10).

    ``post * dose`` and ``y`` after removing both fixed effects, x in log-% (100 times the residualised regressor).
    ``kind = bin``: ``n_bins`` equal-count bins of the rows sorted by residualised x (stable), with the means of x and
    y, the rows and the distinct fills. ``kind = hist``: ``n_hist`` equal-width bins of the residualised x over its
    range. ``fwl_slope`` = sum x~ y~ / sum x~^2 in bp per log unit, which is ``beta``."""
    f = fit(panel) if f is None else f
    x = 100.0 * np.asarray(f.xd, dtype=float)
    y = np.asarray(f.yd, dtype=float)
    keys = panel["fill_key"].astype(str).to_numpy()
    with np.errstate(all="ignore"):
        slope = float(np.dot(f.xd, f.yd) / np.dot(f.xd, f.xd)) if len(x) else np.nan
    rows = []
    order = np.argsort(x, kind="mergesort")
    for k, idx in enumerate(np.array_split(order, n_bins)):
        if len(idx) == 0:
            continue
        rows.append({"kind": "bin", "bin": k, "x_mean": float(x[idx].mean()), "y_mean": float(y[idx].mean()),
                     "n_rows": int(len(idx)), "n_fills": int(len(set(keys[idx])))})
    if len(x):
        counts, edges = np.histogram(x, bins=n_hist)
        for k, c in enumerate(counts):
            rows.append({"kind": "hist", "bin": k, "x": float(edges[k]), "x_hi": float(edges[k + 1]),
                         "count": int(c)})
    out = pd.DataFrame(rows, columns=FWL_COLUMNS)
    for c in ("bin", "n_rows", "n_fills", "count"):
        out[c] = out[c].astype("Int64")
    out["fwl_slope"] = slope
    return out


def drawn_counts(draws: Sequence[Sequence[Mapping]]) -> Dict[Tuple[str, int], int]:
    """Number of placebo replications that drew each (event_id, UTC day number)."""
    out: Dict[Tuple[str, int], int] = {}
    for rep in draws:
        for d in rep:
            key = (str(d["event_id"]), int(d["placebo_ts"]) // DAY)
            out[key] = out.get(key, 0) + 1
    return out


def drawn_counts_from_strings(strings: Sequence[str]) -> Dict[Tuple[str, int], int]:
    """Same counts from the ``draws`` column of ``h4_placebo.csv`` (``event_id@YYYY-MM-DD@source;...``)."""
    out: Dict[Tuple[str, int], int] = {}
    for s in strings:
        for part in str(s).split(";"):
            eid, day, _ = part.split("@")
            key = (eid, int(pd.Timestamp(day, tz="UTC").timestamp()) // DAY)
            out[key] = out.get(key, 0) + 1
    return out


def placebo_day_table(kept: pd.DataFrame, changes: Mapping[str, np.ndarray], sample: Tuple[int, int],
                      drawn: Mapping[Tuple[str, int], int]) -> pd.DataFrame:
    """Candidate placebo days of every kept event (manager window and sample, before the gap rule), whether the gap
    rule admits them and how often the placebo stage drew them. ``timeline`` is the event id, as in
    ``h4.json placebo.admissible_days``."""
    empty = np.array([], dtype=np.int64)
    rows = []
    for e in kept.itertuples():
        window = p2events.manager_window(e.ccy, e.manager)
        cand = admissible_days(int(e.event_ts), window, empty, sample)
        ok = set(admissible_days(int(e.event_ts), window, changes[e.ccy], sample).tolist())
        for d in cand.tolist():
            rows.append({"timeline": e.event_id, "ccy": e.ccy, "manager": e.manager,
                         "day": pd.Timestamp(d * DAY, unit="s").strftime("%Y-%m-%d"), "admissible": d in ok,
                         "drawn_count": int(drawn.get((e.event_id, d), 0))})
    return pd.DataFrame(rows, columns=PLACEBO_DAY_COLUMNS)


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
        if variant == "matched":        # A29: events with cells in the real panel, disjoint windows per currency
            matched = kept[kept["event_id"].isin(set(panel["event_id"].astype(str)))].reset_index(drop=True)
            if matched.empty:
                placebo[variant] = pd.DataFrame(columns=PART_COLUMNS)
                continue
            draws = draw_placebos_apart(matched, days, n_placebo, seed)
        else:
            draws = draw_placebos(kept, days, n_placebo, seed)
        if variant == "main":
            day_table = placebo_day_table(kept, changes, sample, drawn_counts(draws))
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

    mt = placebo["matched"]
    ps_m = placebo_summary(mt["beta"].to_numpy(float), f.beta)
    ps_m.update(t_spread(mt["t"].to_numpy(float)))
    drawn = np.array([len(_parse_draws(x)) for x in mt["draws"].astype(str)], dtype=float)
    sens["placebo_matched"] = {
        "design": "placebos only for the kept events with cells in the real panel; per replication the placebo days "
                  f"of one currency are at least {SEP_DAYS} days apart (disjoint windows), events that do not fit "
                  "are left out (audit A29)",
        "placebo": ps_m, "events_drawn": _min_med_max(drawn),
        "events_with_cells": _min_med_max(mt["events_with_cells"].to_numpy(float)),
        "placebo_betas": mt["beta"].tolist(), **verdict(f.beta, test["p"], ps_m["p95"])}

    oi_path = out_dir / "manager_oi_share.csv"
    sens["review"] = review_extras(panel, h4, kept, pd.read_csv(oi_path) if oi_path.exists() else None, b=b,
                                   seed=seed)
    fills = load_fill_doses(sorted(map(str, panel["event_id"].unique())), dose_dir)
    sens["audit"] = audit_extras(panel, h4, kept, main_pl, fills, b=b, seed=seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "h4.json", h4)
    main_pl[PLACEBO_COLUMNS].to_csv(out_dir / "h4_placebo.csv", index=False)
    event_figure_table(panel, kept).to_csv(out_dir / "fig_h4_events.csv", index=False)
    fwl_bins(panel, f=f).to_csv(out_dir / "fig_h4_fwl_bins.csv", index=False)
    day_table.to_csv(out_dir / "h4_placebo_days.csv", index=False)
    _write_json(out_dir / "sensitivity_h4.json", sens)
    return {"status": "DONE", "placebo_new": new, "beta": f.beta, "p": test["p"], "placebo_p95": ps["p95"],
            "rejected": v["rejected"], "seconds": time.monotonic() - t0}


TEN_PCT_DOSE = float(np.log(0.9))    # dose of capital ten per cent cheaper (reading aid of Figure F6)


def event_oi_share(events: pd.DataFrame, oi: pd.DataFrame) -> Dict[str, float]:
    """Share of the currency's option open interest held under the changed manager in the month of each event
    (``manager_oi_share.csv``: month, ccy, sm, pm, pm2)."""
    out = {}
    for e in events.itertuples():
        month = pd.Timestamp(int(e.event_ts), unit="s").strftime("%Y-%m")
        hit = oi[(oi["month"].astype(str) == month) & (oi["ccy"].astype(str) == str(e.ccy))]
        out[str(e.event_id)] = float(hit[str(e.manager)].iloc[0]) if len(hit) else float("nan")
    return out


def review_extras(panel: pd.DataFrame, h4: Mapping, events: pd.DataFrame, oi: Optional[pd.DataFrame] = None,
                  b: int = B, seed: int = SEED) -> dict:
    """Review round 1, exploratory (docs/paper2/MANUSKRIPT.md); no registered number changes.

    ``readings``: level of the outcome in the panel (rows and distinct fills) and the change in the half spread that
    ``beta`` and its descriptive interval imply for capital ten per cent cheaper (dose ``ln 0.9``). ``sells_only`` and
    ``buys_only``: the estimate on the cells of one maker side. ``oi_weighted``: the dose times the share of open
    interest under the changed manager in the event month, the dose that the average contract of the currency saw."""
    y = panel["y_hs_bp"].to_numpy(float)
    fills = panel.drop_duplicates("fill_key")["y_hs_bp"].to_numpy(float)
    beta, lo, hi = float(h4["stat"]), float(h4["lo"]), float(h4["hi"])
    changes = sorted([TEN_PCT_DOSE * lo, TEN_PCT_DOSE * hi])
    out: dict = {"exploratory": True, "b": int(b), "seed": int(seed),
                 "readings": {"y_mean": float(np.mean(y)), "y_median": float(np.median(y)), "n_rows": int(len(y)),
                              "y_mean_fills": float(np.mean(fills)), "y_median_fills": float(np.median(fills)),
                              "n_fills": int(len(fills)), "ten_pct_dose": TEN_PCT_DOSE,
                              "ten_pct_change_beta": TEN_PCT_DOSE * beta, "ten_pct_change_lo": changes[0],
                              "ten_pct_change_hi": changes[1],
                              "note": "change in the half spread (bp of the index) for capital ten per cent cheaper: "
                                      "ln(0.9) times beta and times the bounds of the descriptive interval"}}
    side = panel["cell"].astype(str).str.split("|").str[1]
    for name, s in (("sells_only", "sell"), ("buys_only", "buy")):
        sub = panel[(side == s).to_numpy()].reset_index(drop=True)
        t = wild_cluster_test(fit(sub), b=b, seed=seed)
        t.update(events=int(sub["event_id"].nunique()), cell_events=int(sub.groupby(["cell", "event_id"]).ngroups))
        out[name] = t
    if oi is not None:
        share = event_oi_share(events, oi)
        w = panel["event_id"].astype(str).map(share).to_numpy(float)
        weighted = panel.assign(dose=panel["dose"].to_numpy(float) * w)
        t = wild_cluster_test(fit(weighted), b=b, seed=seed)
        kept = sorted(set(panel["event_id"].astype(str)))
        t.update(share_min=float(np.nanmin([share[k] for k in kept])),
                 share_max=float(np.nanmax([share[k] for k in kept])), shares={k: share[k] for k in kept})
        out["oi_weighted"] = t
    return out


def _ten_pct(lo: float, hi: float) -> List[float]:
    """Change in the half spread (bp) for capital ten per cent cheaper at the bounds ``lo, hi`` of beta, sorted."""
    return sorted([TEN_PCT_DOSE * float(lo), TEN_PCT_DOSE * float(hi)])


def t_spread(t: Sequence[float], level: float = LEVEL) -> dict:
    """Spread of placebo t statistics: sample sd, MAD-based sd, percentiles and the shares beyond the normal
    critical value of ``level`` (nominal: ``1 - level`` two-sided, ``(1 - level) / 2`` one-sided)."""
    x = np.asarray(t, dtype=float)
    x = x[np.isfinite(x)]
    alpha = (1.0 - level) / 2.0
    crit = float(norm.ppf(1.0 - alpha))
    if len(x) < 2:
        return {"n": int(len(x)), "crit": crit, "t_sd": np.nan, "t_mad_sd": np.nan, "t_mean": np.nan,
                "t_median": np.nan, "t_p05": np.nan, "t_p95": np.nan, "share_t_gt_crit": np.nan,
                "share_abs_t_gt_crit": np.nan}
    med = float(np.median(x))
    return {"n": int(len(x)), "crit": crit, "t_sd": float(np.std(x, ddof=1)),
            "t_mad_sd": float(np.median(np.abs(x - med)) / norm.ppf(0.75)), "t_mean": float(x.mean()),
            "t_median": med, "t_p05": float(np.quantile(x, alpha)), "t_p95": float(np.quantile(x, 1.0 - alpha)),
            "share_t_gt_crit": float(np.mean(x > crit)), "share_abs_t_gt_crit": float(np.mean(np.abs(x) > crit))}


def placebo_calibration(placebo: pd.DataFrame, res: Mapping, y_mean: float, level: float = LEVEL) -> dict:
    """Span of beta calibrated on the placebo distribution of t (audit A05, exploratory).

    The day-cluster SE and the wild cluster bootstrap measure the noise of ``beta`` at the given dates; at random
    dates (the placebos, each with its own day-cluster SE) t spreads wider, because the cells do not move in parallel
    from date to date. Taking the placebo t as the reference distribution of ``(beta_hat - beta) / se``:
    ``lo, hi = beta - (t_p95, t_p05) * se`` (percentiles at ``level``); ``sd_scaled_lo, sd_scaled_hi`` =
    ``beta -/+ z * se * t_sd`` (normal, SE scaled by the sd of the placebo t); ``p_placebo_t`` = one-sided
    ``(1 + #{t_placebo >= t}) / (n + 1)``. ``ten_pct_*``: change in the half spread for capital ten per cent cheaper
    (``ln 0.9`` times the bounds); ``ten_pct_narrowing_share*``: the largest narrowing inside the span as a share of
    ``y_mean``, the mean half spread of the panel (negative: no narrowing inside the span). The registered verdict and
    ``h4.json`` stay as they are."""
    beta, se, t0 = float(res["stat"]), float(res["se"]), float(res["t"])
    sp_ = t_spread(placebo["t"].to_numpy(float), level)
    fin = np.isfinite(placebo["t"].to_numpy(float))
    betas = placebo["beta"].to_numpy(float)[fin]
    ses = placebo["se"].to_numpy(float)
    ses = ses[np.isfinite(ses)]
    lo, hi = beta - sp_["t_p95"] * se, beta - sp_["t_p05"] * se
    k = sp_["crit"] * se * sp_["t_sd"]
    ch, ch_sd, ch_d = _ten_pct(lo, hi), _ten_pct(beta - k, beta + k), _ten_pct(res["lo"], res["hi"])
    n = sp_["n"]
    return {"exploratory": True, "level": float(level), **sp_,
            "beta": beta, "se": se, "t": t0,
            "beta_sd": float(np.std(betas, ddof=1)) if len(betas) > 1 else np.nan,
            "se_median": float(np.median(ses)) if len(ses) else np.nan,
            "p_placebo_t": (1 + int(np.sum(placebo["t"].to_numpy(float)[fin] >= t0))) / (n + 1) if n else np.nan,
            "lo": lo, "hi": hi, "sd_scaled_lo": beta - k, "sd_scaled_hi": beta + k,
            "y_mean": float(y_mean), "ten_pct_dose": TEN_PCT_DOSE,
            "ten_pct_change_lo": ch[0], "ten_pct_change_hi": ch[1],
            "ten_pct_change_sd_scaled_lo": ch_sd[0], "ten_pct_change_sd_scaled_hi": ch_sd[1],
            "ten_pct_narrowing_share": -ch[0] / float(y_mean),
            "ten_pct_narrowing_share_sd_scaled": -ch_sd[0] / float(y_mean),
            "ten_pct_narrowing_share_descriptive": -ch_d[0] / float(y_mean),
            "note": "span of beta calibrated on the placebo t (percentiles); the descriptive interval of h4.json and "
                    "the wild bootstrap p condition on the given dates. The placebo panels contain an event without "
                    "cells in the real panel and overlapping windows (placebo_composition, placebo_matched)."}


def _min_med_max(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return {"min": None, "median": None, "max": None}
    return {"min": int(x.min()), "median": float(np.median(x)), "max": int(x.max())}


def _parse_draws(s: str) -> List[Tuple[str, int]]:
    """(event_id, UTC day number) of a ``draws`` string of ``h4_placebo.csv``."""
    out = []
    for part in str(s).split(";"):
        if part:
            eid, day, _ = part.split("@")
            out.append((eid, int(pd.Timestamp(day, tz="UTC").timestamp()) // DAY))
    return out


def _overlap_pairs(days_by_ccy: Mapping[str, List[int]], sep_days: int = SEP_DAYS) -> int:
    return int(sum(abs(a - b) < sep_days for dd in days_by_ccy.values() for i, a in enumerate(dd) for b in dd[i + 1:]))


def placebo_composition(placebo: pd.DataFrame, panel: pd.DataFrame, kept: pd.DataFrame) -> dict:
    """How the placebo panels are built compared with the real panel (audit A29, descriptive): events with cells,
    rows, day clusters, pairs of dates of one currency whose windows overlap (days less than ``SEP_DAYS`` apart) and
    days drawn twice for one currency in a replication."""
    ccy_of = dict(zip(kept["event_id"].astype(str), kept["ccy"].astype(str)))
    real = set(panel["event_id"].astype(str))
    ids = [str(e) for e in kept["event_id"]]
    real_days: Dict[str, List[int]] = {}
    for e, ts in zip(ids, kept["event_ts"]):
        if e in real:
            real_days.setdefault(ccy_of[e], []).append(int(ts) // DAY)
    overlaps, same = [], []
    for s in placebo["draws"]:
        by: Dict[str, List[int]] = {}
        for eid, day in _parse_draws(s):
            by.setdefault(ccy_of.get(eid, eid.split("-")[0]), []).append(day)
        overlaps.append(_overlap_pairs(by))
        same.append(sum(len(v) - len(set(v)) for v in by.values()))
    ev_pl = placebo["events_with_cells"].to_numpy(float)
    rows = placebo["n"].to_numpy(float)
    return {"exploratory": True, "events_kept": int(len(ids)), "events_with_cells_real": int(len(real)),
            "events_without_cells_real": [e for e in ids if e not in real],
            "events_with_cells_placebo_min": int(ev_pl.min()),
            "events_with_cells_placebo_median": float(np.median(ev_pl)),
            "events_with_cells_placebo_max": int(ev_pl.max()), "rows_real": int(len(panel)),
            "rows_per_fill_real": float(len(panel) / max(panel["fill_key"].nunique(), 1)),
            "rows_placebo_min": int(rows.min()), "rows_placebo_median": float(np.median(rows)),
            "rows_placebo_max": int(rows.max()),
            "clusters_real": int(panel["day"].nunique()),
            "clusters_placebo_median": float(np.median(placebo["clusters"].to_numpy(float))),
            "overlap_pairs_real": _overlap_pairs(real_days), "overlap_pairs_placebo_mean": float(np.mean(overlaps)),
            "same_day_draws_placebo_mean": float(np.mean(same)), "sep_days": SEP_DAYS}


def load_fill_doses(event_ids: Sequence[str], dose_dir: Path = p2events.DOSE_DIR) -> Optional[pd.DataFrame]:
    """Per-fill log ratios (``<event_id>_fills.parquet`` of ``p2events``) of the given events with an ``event_id``
    column; None when no file is there."""
    parts = []
    for eid in event_ids:
        path = Path(dose_dir) / f"{eid}_fills.parquet"
        if path.exists():
            d = pd.read_parquet(path)
            d.insert(0, "event_id", str(eid))
            parts.append(d)
    return pd.concat(parts, ignore_index=True) if parts else None


def robust_doses(fills: pd.DataFrame, trim: float = TRIM_ABS_LOG_RATIO) -> pd.DataFrame:
    """Per (event, cell): the registered dose (mean log ratio over the fills with one), the median, the mean without
    fills with ``|log ratio| > trim`` (NaN when none is left), the fills with a log ratio and those above ``trim``."""
    f = fills[np.isfinite(fills["log_ratio"].to_numpy(float))]
    key = [f["event_id"].astype(str), f["cell"].astype(str)]
    g = f["log_ratio"].astype(float).groupby(key)
    large = f["log_ratio"].abs() > trim
    out = pd.DataFrame({"dose_mean": g.mean(), "dose_median": g.median(), "n_valid": g.size(),
                        "n_large": large.groupby(key).sum().astype(int)})
    small = f[~large.to_numpy()]
    out["dose_trimmed"] = small["log_ratio"].astype(float).groupby(
        [small["event_id"].astype(str), small["cell"].astype(str)]).mean().reindex(out.index)
    out.index.names = ["event_id", "cell"]
    return out.reset_index()


def dose_robust(panel: pd.DataFrame, fills: Optional[pd.DataFrame], b: int = B, seed: int = SEED,
                trim: float = TRIM_ABS_LOG_RATIO, median_diff: float = MEDIAN_DIFF) -> Optional[dict]:
    """beta with robust doses (audit A30, exploratory; the registered dose is the mean log ratio). A few fills near
    zero capital (maker buys at the minimum price) give log ratios of -6 and move the mean. ``median``: the median
    log ratio per (event, cell); ``trimmed``: the mean without fills with ``|log ratio| > trim``; rows of cells
    without a dose are dropped. ``check_mean_max_abs_diff``: the stored panel dose against the mean of the fills."""
    if fills is None or len(fills) == 0:
        return None
    t = robust_doses(fills, trim).set_index(["event_id", "cell"])
    key = pd.MultiIndex.from_arrays([panel["event_id"].astype(str), panel["cell"].astype(str)])
    tab = t.reindex(key)
    pairs = t.reindex(pd.MultiIndex.from_frame(panel[["event_id", "cell"]].astype(str).drop_duplicates()))
    diff = np.abs(tab["dose_mean"].to_numpy(float) - panel["dose"].to_numpy(float))
    out: dict = {"exploratory": True, "trim_abs_log_ratio": float(trim), "median_diff": float(median_diff),
                 "pairs": int(len(pairs)), "pairs_without_fills": int(pairs["dose_mean"].isna().sum()),
                 "pairs_with_large_log_ratio": int((pairs["n_large"] > 0).sum()),
                 "fills_with_large_log_ratio": int(np.nansum(pairs["n_large"].to_numpy(float))),
                 "pairs_median_differs": int((np.abs(pairs["dose_median"] - pairs["dose_mean"]) > median_diff).sum()),
                 "check_mean_max_abs_diff": float(np.nanmax(diff)) if np.isfinite(diff).any() else np.nan}
    for name, col in (("median", "dose_median"), ("trimmed", "dose_trimmed")):
        d = tab[col].to_numpy(float)
        keep = np.isfinite(d)
        alt = panel.assign(dose=d)[keep].reset_index(drop=True)
        r = wild_cluster_test(fit(alt), b=b, seed=seed)
        r.update(exploratory=True, rows_dropped=int((~keep).sum()),
                 cell_events=int(alt.groupby(["cell", "event_id"]).ngroups) if len(alt) else 0,
                 events=int(alt["event_id"].nunique()))
        out[name] = r
    return out


def audit_extras(panel: pd.DataFrame, res: Mapping, kept: pd.DataFrame, placebo: pd.DataFrame,
                 fills: Optional[pd.DataFrame], b: int = B, seed: int = SEED) -> dict:
    """Audit entries of ``sensitivity_h4.json`` (A05, A29, A30; exploratory): ``placebo_calibration``,
    ``placebo_composition``, ``dose_robust`` (None without per-fill doses)."""
    return {"exploratory": True, "b": int(b), "seed": int(seed),
            "placebo_calibration": placebo_calibration(placebo, res, float(np.mean(panel["y_hs_bp"].to_numpy(float)))),
            "placebo_composition": placebo_composition(placebo, panel, kept),
            "dose_robust": dose_robust(panel, fills, b=b, seed=seed)}


def _sorted_kept(events: pd.DataFrame) -> pd.DataFrame:
    return (events[events["kept"].astype(bool)].sort_values(["ccy", "event_ts"], kind="mergesort")
            .reset_index(drop=True))


def run_extras(results_dir: Path = RESULTS_DIR, panel_path: Path = p2events.PANEL_PATH, b: int = B,
               seed: int = SEED, dose_dir: Path = p2events.DOSE_DIR) -> dict:
    """``review_extras`` and ``audit_extras`` on the stored panel and results (``h4_placebo.csv``, per-fill doses),
    merged into ``sensitivity_h4.json`` as ``review`` and ``audit``."""
    results_dir = Path(results_dir)
    h4 = json.loads((results_dir / "h4.json").read_text())
    sens = json.loads((results_dir / "sensitivity_h4.json").read_text())
    events = pd.read_csv(results_dir / "events.csv")
    oi_path = results_dir / "manager_oi_share.csv"
    oi = pd.read_csv(oi_path) if oi_path.exists() else None
    panel = pd.read_parquet(panel_path)
    if abs(fit(panel).beta - float(h4["stat"])) > 1e-8 * max(1.0, abs(float(h4["stat"]))):
        raise RuntimeError("stored panel does not reproduce h4.json stat")
    sens["review"] = review_extras(panel, h4, events[events["kept"].astype(bool)], oi, b=b, seed=seed)
    placebo = pd.read_csv(results_dir / "h4_placebo.csv", dtype={"draws": str})
    fills = load_fill_doses(sorted(map(str, panel["event_id"].unique())), dose_dir)
    sens["audit"] = audit_extras(panel, h4, _sorted_kept(events), placebo, fills, b=b, seed=seed)
    _write_json(results_dir / "sensitivity_h4.json", sens)
    r = sens["review"]
    return {"status": "DONE", "y_mean": r["readings"]["y_mean"], "sells_beta": r["sells_only"]["beta"],
            "buys_beta": r["buys_only"]["beta"],
            "oi_beta": r.get("oi_weighted", {}).get("beta")}


def fig_tables(results_dir: Path = RESULTS_DIR, panel: Optional[pd.DataFrame] = None,
               events: Optional[pd.DataFrame] = None, params_root: Optional[Path] = None,
               panel_path: Path = p2events.PANEL_PATH) -> dict:
    """Rebuild ``fig_h4_fwl_bins.csv`` and ``h4_placebo_days.csv`` from the stored panel, ``events.csv``, ``h4.json``
    and ``h4_placebo.csv`` (no placebo stage, no bootstrap). Refuses when the slope differs from ``h4.json stat`` or
    the admissible days differ from ``h4.json placebo.admissible_days``."""
    results_dir = Path(results_dir)
    res = json.loads((results_dir / "h4.json").read_text())
    if events is None:
        events = pd.read_csv(results_dir / "events.csv")
    if panel is None:
        panel = pd.read_parquet(panel_path)
    kept = (events[events["kept"].astype(bool)].sort_values(["ccy", "event_ts"], kind="mergesort")
            .reset_index(drop=True))
    sample = tuple(int(pd.Timestamp(s).timestamp()) for s in res["sample"])
    f = fit(panel)
    bins = fwl_bins(panel, f=f)
    slope = float(bins["fwl_slope"].iloc[0])
    if not abs(slope - float(res["stat"])) <= 1e-8 * max(1.0, abs(float(res["stat"]))):
        raise RuntimeError(f"FWL slope {slope} differs from h4.json stat {res['stat']}")
    changes = {c: change_days(c, root=params_root, scope="event") for c in sorted(set(kept["ccy"]))}
    placebo = pd.read_csv(results_dir / "h4_placebo.csv", dtype={"draws": str})
    table = placebo_day_table(kept, changes, sample, drawn_counts_from_strings(placebo["draws"].tolist()))
    adm = table[table["admissible"]].groupby("timeline").size()
    for eid, info in res["placebo"]["admissible_days"].items():
        if int(adm.get(eid, 0)) != int(info["days"]):
            raise RuntimeError(f"admissible days of {eid}: {int(adm.get(eid, 0))} here, {info['days']} in h4.json")
    bins.to_csv(results_dir / "fig_h4_fwl_bins.csv", index=False)
    table.to_csv(results_dir / "h4_placebo_days.csv", index=False)
    return {"status": "DONE", "fwl_slope": slope, "beta": float(res["stat"]),
            "admissible_days": {k: int(v) for k, v in adm.items()}, "drawn": int(table["drawn_count"].sum())}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface.inference_p2_h4")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="H4: regression, wild cluster bootstrap, placebo, sensitivities (resumable)")
    r.add_argument("--b", type=int, default=B)
    r.add_argument("--placebos", type=int, default=N_PLACEBO)
    r.add_argument("--seed", type=int, default=SEED)
    r.add_argument("--max-seconds", type=float, default=420.0)
    sub.add_parser("figtables", help="rebuild fig_h4_fwl_bins.csv and h4_placebo_days.csv from stored results")
    x = sub.add_parser("extras", help="review-round readings, side splits and audit entries into "
                                      "sensitivity_h4.json (review, audit) from stored results")
    x.add_argument("--b", type=int, default=B)
    x.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    if a.cmd == "figtables":
        print(json.dumps(_clean(fig_tables())), flush=True)
        return 0
    if a.cmd == "extras":
        print(json.dumps(_clean(run_extras(b=a.b, seed=a.seed))), flush=True)
        return 0
    res = run(b=a.b, n_placebo=a.placebos, seed=a.seed, max_seconds=a.max_seconds)
    print(json.dumps(_clean(res)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
