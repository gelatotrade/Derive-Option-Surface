"""Inference for paper 2: H1 to H3 of the preregistration (docs/paper2/PRAEREGISTRIERUNG.md, addenda 1 to 4)
plus the exploratory sensitivities and the tables behind the figures.

Net edge (addendum 2). Per contract ``NE = MO_30m - (fee_maker - rebate_maker) / amount - hedge``, with the hedge of
Paper 1 (``inference_p1.hedge_cost``: perp taker fee, 1 bp perp half spread, 30 min of funding at the median
absolute funding rate of the currency). The edge of a fill is ``NE * amount``. Paper 1's form (fee and rebate
subtracted undivided from the per-contract markout) is kept as ``ne_p1`` for the sensitivity.

H1 (rank order). Cells = currency x maker side x |delta| bucket x tenor bucket of Paper 1, occupied with at least 200
fills in the currency's PM2 window. ``A_c = 1e4 * sum(NE a) / sum(index a)`` (bp of notional) and
``B_c = 1e4 * sum(NE a) / sum(K_pm2 a)`` (bp of PM2 capital); the statistic is Spearman's rho between A and B over
the occupied cells. Interval (addendum 3): UTC days are drawn with replacement, both cell quantities are recomputed
from pre-aggregated (cell, day) sums weighted by the multiplicity of each day, rho is taken over the cells with at
least one fill in the replicate; 5th and 95th percentile of B = 9 999 replicates. Rejected if the upper bound is at
least 0.5. No fill is excluded (addendum 4, item 4).

H2 (marginal capital). ``ratio = (dK / amount) / K_pm2,single`` over the drawn sample of 20 000 fills (addendum 4,
item 1); fills with ``K_pm2,single <= 0`` are excluded and counted. Median with a day-cluster interval, every fill of a
drawn day entering with the day's multiplicity. Rejected if the upper bound is at least 0.5. The MM sensitivity takes
one lib per ratio (C5a): ``ratio_mm`` the account's lib in numerator and denominator (``K_single_pm2_mm_acct``, same
market state), ``ratio_mm_std`` the standard lib in both. Override libs differ only in ``mmFactor``, so the IM test is
the same under either lib.

H3 (netting value). ``K_sm / K_pm2`` of the maker days with at least one option position (status ``ok``), both on the
same legs (addendum 4, item 2); days with ``K_pm2 <= 0`` are excluded and counted. Median with a day-cluster
interval. Rejected if the lower bound is at most 2.

Every verdict is a JSON object ``{stat, lo, hi, rejected, rule, n, ...}``. Accounts appear only as ``p2ids`` labels
(the input tables carry them in ``label``); raw subaccount ids never reach ``results/``.

Review round 1 (exploratory, docs/paper2/MANUSKRIPT.md): ``h1_sign`` in ``sensitivity.json`` (the rho that the sign
pattern alone gives when ranks are shuffled within each sign group, rho within sign groups and sides, overlap of the
best cells), H2 and H3 per parameter regime (``regime=R1`` to ``R4``, section 6.6 of ABBILDUNGSWAHL), H3 per manager
of the account (``account_manager=SM/PM/PM2``) and on small books without the SM account, and the size of the H2
population before the draw. None of it changes a registered number.

Audit (docs/paper2/AUDIT.md, exploratory): the groups of ``h1_sign`` chosen by the sign of the estimated edge choose
again in every replicate (A04, ``selection = per replicate``); ``h1_interval`` describes the registered percentile
interval of H1 (share of draws at or above the estimate, reflected and bias-corrected intervals; A28).

CLI: ``python3 -m derive_surface p2 infer run`` (H1 to H3), ``... infer sensitivity`` (exploratory tables and
figure data) and ``... infer extras`` (only the review-round entries, merged into the existing ``sensitivity.json``,
``sens_h2.csv`` and ``sens_h3.csv``), each with ``--root`` (repository root), ``--out``, ``--b``, ``--seed``.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

from .capital import WINDOW_START, in_window
from .inference_p1 import analysis_frame
from .p2events import cell_labels
from .p2types import YEAR

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[1]
B = 9_999
SEED = 20260924
LEVEL = 0.90
MIN_CELL_FILLS = 200
HORIZON = "30m"
HALF_SPREAD_BP = 1.0
H1_MAX_RHO = 0.5
H2_MAX_MEDIAN = 0.5
H3_MIN_MEDIAN = 2.0
SM_MAX_OPTIONS = 63            # options an SM account on v2 can hold (addendum 4, item 2)
SIGN_DRAWS = 4_000             # shuffles of the ranks within the sign groups (h1_sign.sign_floor)
# Parameter regimes of the figures (ABBILDUNGSWAHL section 6.6): the PM2 events of 23.01.2026 04:24:05,
# 24.05.2026 04:05:07 and 20.08.2026 22:09:25 UTC; an object at the event second belongs to the later regime. Fills
# are placed by their time, maker days by the book time 00:00 UTC. Same bounds as figs_p2.f1.REGIME_BOUNDS (tested).
REGIME_BOUNDS = (1769142245, 1779595507, 1787263765)
REGIMES = ("R1", "R2", "R3", "R4")
MANAGERS = ("sm", "pm", "pm2")
CCYS = ("BTC", "ETH", "HYPE")
BTC_ETH = ("BTC", "ETH")

MARKOUT_COLUMNS = ["trade_id", "ts", "currency", "instrument_name", "expiry", "maker_side", "amount", "price",
                   "index_price", "mark_b_t", "delta_t", "fwd_t", "fee_maker", "rebate_maker", "taker_wallet",
                   "mo_usd_30m", "mo_dn_30m", "mo_vol_30m", "delta_bucket", "tenor_bucket"]
CAPITAL_COLUMNS = ["trade_id", "ts", "amount", "sec", "K_sm", "K_pm", "K_pm2", "K_sm_mm", "K_pm_mm", "K_pm2_mm"]
K_COLUMNS = ["K_sm", "K_pm", "K_pm2", "K_sm_mm", "K_pm_mm", "K_pm2_mm"]
CELL_PARTS = ["ccy", "side", "delta_bucket", "tenor_bucket"]
PRIVATE_COLUMNS = {"subaccount", "maker_sub", "taker_sub", "maker_wallet", "taker_wallet", "wallet"}

# H2 variants: (numerator per contract, single-contract capital that is the denominator and the exclusion rule)
H2_VARIANTS: Dict[str, Tuple[str, str]] = {
    "ratio": ("dK_per_contract", "K_single_pm2"),
    "ratio_unit": ("dK_unit", "K_single_pm2"),
    "ratio_tape": ("dK_tape_per_contract", "K_single_pm2"),
    "ratio_mm": ("dK_mm_per_contract", "K_single_pm2_mm_acct"),     # MM, account lib in both (C5a)
    "ratio_mm_std": ("dK_mm_std_per_contract", "K_single_pm2_mm"),  # MM, standard lib in both (C5a)
}
# PM2 lib of (numerator, denominator). Under IM both libs give the same numbers (overrides change only mmFactor;
# books.combine_marginal checks K_single_book_acct == K_single_pm2).
H2_LIBS: Dict[str, Tuple[str, str]] = {
    "ratio": ("account", "standard"),
    "ratio_unit": ("account", "standard"),
    "ratio_tape": ("account", "standard"),
    "ratio_mm": ("account", "account"),
    "ratio_mm_std": ("standard", "standard"),
}
QUANTILES = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
HIST_EDGES = np.concatenate([[-np.inf], np.round(np.arange(-1.0, 2.0 + 1e-9, 0.05), 10), [np.inf]])

H1_RULE = ("rejected if the upper bound of the 90% day-cluster bootstrap percentile interval of Spearman's rho "
           "between edge in bp of notional and edge per PM2 capital over the occupied cells is >= 0.5")
H2_RULE = ("rejected if the upper bound of the 90% day-cluster bootstrap percentile interval of the median of "
           "(dK / amount) / K_pm2_single is >= 0.5; fills with K_pm2_single <= 0 excluded and counted")
H3_RULE = ("rejected if the lower bound of the 90% day-cluster bootstrap percentile interval of the median of "
           "K_sm / K_pm2 over maker days is <= 2; days with K_pm2 <= 0 excluded and counted")


# =====================================================================================================================
# Paths and I/O
# =====================================================================================================================

def paths(root: Path) -> Dict[str, Path]:
    root = Path(root)
    return {"markouts": root / "data" / "p1" / "derived" / "markouts.parquet",
            "funding": root / "data" / "p1" / "ref" / "funding_history.parquet",
            "capital": root / "data" / "p2" / "derived" / "capital.parquet",
            "marginal": root / "data" / "p2" / "derived" / "marginal.parquet",
            "maker_days": root / "data" / "p2" / "derived" / "maker_days.parquet",
            "holding": root / "results" / "p2" / "holding_time.csv",
            "out": root / "results" / "p2"}


def _plain(obj):
    """JSON-safe copy: drops keys starting with ``_``, numpy scalars to Python, NaN/inf to None."""
    if isinstance(obj, Mapping):
        return {str(k): _plain(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [_plain(v) for v in obj.tolist()]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        return f if math.isfinite(f) else None
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return obj


def write_json(obj, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_plain(obj), indent=1, ensure_ascii=False) + "\n")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """CSV under ``results``; refuses columns that could carry raw account ids or wallets."""
    bad = PRIVATE_COLUMNS & set(map(str, df.columns))
    if bad:
        raise ValueError(f"refusing to write account columns {sorted(bad)} to {path}; use p2ids labels")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


# =====================================================================================================================
# Net edge per fill
# =====================================================================================================================

def edge_frame(markouts: pd.DataFrame, funding: pd.DataFrame, capital: pd.DataFrame,
               half_spread_bp: float = HALF_SPREAD_BP) -> pd.DataFrame:
    """One row per fill: cell, UTC day, net edge per contract (addendum 2) and per fill, Paper 1's form, capital per
    contract under every manager, time to expiry in years and the manager windows of the preregistration."""
    a = analysis_frame(markouts, funding, horizon=HORIZON, half_spread_bp=half_spread_bp)
    amount = a["amount"].to_numpy(float)
    mo = a["y_usd"].to_numpy(float)
    fee_net = a["fee_maker"].to_numpy(float) - a["rebate_maker"].to_numpy(float)   # sums per fill
    hedge = a["hedge"].to_numpy(float)                                               # per contract
    edge = mo * amount - fee_net - hedge * amount
    ne_p1 = a["net_edge"].to_numpy(float)                                            # Paper 1: fee, rebate undivided

    cap = capital.drop_duplicates("trade_id").set_index("trade_id")
    if len(cap) != len(capital):
        raise ValueError("capital has duplicate trade_id")
    cap = cap.reindex(a["trade_id"].to_numpy())
    if cap["ts"].isna().any():
        raise ValueError(f"{int(cap['ts'].isna().sum())} fills without a capital row")
    if not np.array_equal(cap["ts"].to_numpy(np.int64), a["ts"].to_numpy(np.int64)):
        raise ValueError("capital and markouts disagree on the taker time")
    if not np.allclose(cap["amount"].to_numpy(float), amount, rtol=1e-12, atol=0.0):
        raise ValueError("capital and markouts disagree on the amount")

    ts = a["ts"].to_numpy(np.int64)
    ccy = a["currency"].to_numpy()
    side = a["maker_side"].to_numpy(float)
    out = pd.DataFrame({
        "trade_id": a["trade_id"].to_numpy(), "ts": ts, "day": a["day"].to_numpy(), "ccy": ccy,
        "side": np.where(side > 0, "buy", "sell"), "delta_bucket": a["delta_bucket"].to_numpy(),
        "tenor_bucket": a["tenor_bucket"].to_numpy(),
        "cell": cell_labels(ccy, side, a["delta_bucket"], a["tenor_bucket"]),
        "amount": amount, "index_price": a["index_price"].to_numpy(float), "mo": mo, "fee_net": fee_net,
        "hedge": hedge, "ne": edge / amount, "edge": edge, "ne_p1": ne_p1, "edge_p1": ne_p1 * amount,
        "tau": cap["sec"].to_numpy(float) / YEAR})
    for k in K_COLUMNS:
        out[k] = cap[k].to_numpy(float)
    ts_s = ts // 1000
    for mgr in MANAGERS:
        flag = np.zeros(len(out), dtype=bool)
        for c in np.unique(ccy):
            m = ccy == c
            flag[m] = in_window(str(c), mgr, ts_s[m])
        out[f"in_{mgr}"] = flag
    return out


def load_edge_frame(root: Path) -> pd.DataFrame:
    p = paths(root)
    t0 = time.time()
    mk = pd.read_parquet(p["markouts"], columns=MARKOUT_COLUMNS)
    fu = pd.read_parquet(p["funding"])
    cap = pd.read_parquet(p["capital"], columns=CAPITAL_COLUMNS)
    fr = edge_frame(mk, fu, cap)
    log.info("edge frame: %d fills in %.1f s", len(fr), time.time() - t0)
    return fr


# =====================================================================================================================
# Bootstrap draws, ranks, medians
# =====================================================================================================================

def day_multiplicities(n_days: int, b: int = B, seed: int = SEED) -> np.ndarray:
    """(b, n_days) matrix: how often each UTC day is drawn in each replicate (n_days draws with replacement).

    All draws come from one ``integers`` call of ``default_rng(seed)``, so the result depends only on the inputs."""
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, n_days, size=(b, n_days))
    flat = (pick + np.arange(b, dtype=np.int64)[:, None] * n_days).ravel()
    return np.bincount(flat, minlength=b * n_days).reshape(b, n_days)


def ranks_desc(x: np.ndarray) -> np.ndarray:
    """Ranks with 1 = largest value, ties averaged."""
    return rankdata(-np.asarray(x, dtype=float), method="average")


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman's rho (Pearson correlation of average ranks) over the pairs where both are finite; NaN below 3 pairs
    or for a constant series."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return float("nan")
    rx, ry = rankdata(x[ok]), rankdata(y[ok])
    rx, ry = rx - rx.mean(), ry - ry.mean()
    den = math.sqrt(float((rx ** 2).sum() * (ry ** 2).sum()))
    return float((rx * ry).sum() / den) if den > 0 else float("nan")


def _pearson_rows(RX: np.ndarray, RY: np.ndarray) -> np.ndarray:
    rx = RX - RX.mean(axis=1, keepdims=True)
    ry = RY - RY.mean(axis=1, keepdims=True)
    den = np.sqrt((rx ** 2).sum(axis=1) * (ry ** 2).sum(axis=1))
    num = (rx * ry).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)


def spearman_rows(X: np.ndarray, Y: np.ndarray, present: np.ndarray) -> np.ndarray:
    """Spearman's rho per row over the columns that are present (and finite) in that row."""
    X, Y = np.asarray(X, dtype=float), np.asarray(Y, dtype=float)
    ok = np.asarray(present, dtype=bool) & np.isfinite(X) & np.isfinite(Y)
    out = np.full(X.shape[0], np.nan)
    full = ok.all(axis=1)
    if full.any() and X.shape[1] >= 3:
        out[full] = _pearson_rows(rankdata(X[full], axis=1), rankdata(Y[full], axis=1))
    for i in np.flatnonzero(~full):
        out[i] = spearman(X[i, ok[i]], Y[i, ok[i]])
    return out


def _ranks_rows_desc(X: np.ndarray, present: np.ndarray) -> np.ndarray:
    """Descending ranks per row among the present columns; NaN elsewhere."""
    ok = np.asarray(present, dtype=bool) & np.isfinite(X)
    out = np.full(X.shape, np.nan)
    full = ok.all(axis=1)
    if full.any():
        out[full] = rankdata(-X[full], axis=1)
    for i in np.flatnonzero(~full):
        out[i, ok[i]] = ranks_desc(X[i, ok[i]])
    return out


def multiset_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Median of the multiset in which ``values[i]`` occurs ``weights[i]`` times (np.median convention)."""
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=np.int64)
    order = np.argsort(v, kind="mergesort")
    v, w = v[order], w[order]
    cum = np.cumsum(w)
    n = int(cum[-1])
    i1 = np.searchsorted(cum, (n - 1) // 2, side="right")
    i2 = np.searchsorted(cum, n // 2, side="right")
    return float((v[i1] + v[i2]) / 2.0)


def _interval(draws: np.ndarray, level: float) -> Tuple[float, float]:
    alpha = (1.0 - level) / 2.0
    d = np.asarray(draws, dtype=float)
    if not np.isfinite(d).any():
        return float("nan"), float("nan")
    return float(np.nanquantile(d, alpha)), float(np.nanquantile(d, 1.0 - alpha))


def median_bootstrap(values: np.ndarray, days, b: int = B, seed: int = SEED, level: float = LEVEL,
                     chunk: int = 250) -> dict:
    """Median with a percentile interval from a UTC-day cluster bootstrap (addendum 3, item 2): every value of a
    drawn day enters the replicate with the day's multiplicity. Non-finite values are dropped first."""
    v = np.asarray(values, dtype=float)
    d = np.asarray(days)
    ok = np.isfinite(v)
    v, d = v[ok], d[ok]
    base = {"b": int(b), "seed": int(seed), "level": float(level), "n": int(len(v))}
    if len(v) == 0:
        return {**base, "stat": float("nan"), "lo": float("nan"), "hi": float("nan"), "n_days": 0,
                "_draws": np.full(b, np.nan)}
    codes, uniq = pd.factorize(pd.Series(d), sort=True)
    order = np.argsort(v, kind="mergesort")
    vs, cs = v[order], codes[order]
    W = day_multiplicities(len(uniq), b=b, seed=seed)
    draws = np.empty(b)
    for r0 in range(0, b, chunk):
        w = W[r0:r0 + chunk][:, cs]
        cum = np.cumsum(w, axis=1)
        n = cum[:, -1]
        i1 = (cum <= ((n - 1) // 2)[:, None]).sum(axis=1)
        i2 = (cum <= (n // 2)[:, None]).sum(axis=1)
        draws[r0:r0 + chunk] = (vs[i1] + vs[i2]) / 2.0
    lo, hi = _interval(draws, level)
    return {**base, "stat": float(np.median(v)), "lo": lo, "hi": hi, "n_days": int(len(uniq)), "_draws": draws}


# =====================================================================================================================
# Cell maps (H1)
# =====================================================================================================================

def _cell_columns(labels: Sequence[str]) -> pd.DataFrame:
    parts = [str(s).split("|") for s in labels]
    if parts and all(len(p) == 4 for p in parts):
        return pd.DataFrame(parts, columns=CELL_PARTS)
    return pd.DataFrame({c: [np.nan] * len(parts) for c in CELL_PARTS})


def edge_map(frame: pd.DataFrame, k_col: str, edge_col: str = "edge", index_col: str = "index_price",
             amount_col: str = "amount", min_fills: int = MIN_CELL_FILLS, b: int = B, seed: int = SEED,
             level: float = LEVEL, tau_col: Optional[str] = None,
             cell_scale: Optional[pd.Series] = None, return_replicates: bool = False) -> Tuple[pd.DataFrame, dict]:
    """Edge per notional (A) and per capital (B) of every cell and the day-cluster bootstrap of Spearman's rho.

    ``frame`` holds one row per fill with ``cell, day``, the fill's edge (``edge_col``, USDC), ``index_col``,
    ``amount_col`` and the capital per contract ``k_col``. ``A = 1e4 sum(edge) / sum(index a)``,
    ``B = 1e4 sum(edge) / sum(K a [tau])`` times ``cell_scale`` (per cell; cells without a finite scale are not
    occupied). Occupied cells have at least ``min_fills`` fills with finite inputs. Replicates draw the UTC days of the
    occupied cells' fills with replacement (addendum 3, item 1) and use the cells with a fill in the replicate.
    ``return_replicates`` adds the (b, occupied cells) matrices ``_A_rep``, ``_B_rep`` and ``_present`` to the result
    (columns in the order of the occupied rows of the returned cells; not written to any file)."""
    cols = ["cell", "day", edge_col, index_col, amount_col, k_col] + ([tau_col] if tau_col else [])
    f = frame[cols]
    amt = f[amount_col].to_numpy(float)
    num = f[edge_col].to_numpy(float)
    idx = f[index_col].to_numpy(float) * amt
    kk = f[k_col].to_numpy(float) * amt
    den = kk * f[tau_col].to_numpy(float) if tau_col else kk
    ok = np.isfinite(num) & np.isfinite(idx) & np.isfinite(den)
    n_nonfinite = int((~ok).sum())
    cell = f["cell"].to_numpy()[ok]
    day = f["day"].to_numpy()[ok]
    num, idx, kk, den, amt = num[ok], idx[ok], kk[ok], den[ok], amt[ok]
    k_nonpos = f[k_col].to_numpy(float)[ok] <= 0

    ccode, clabels = pd.factorize(pd.Series(cell), sort=True)
    nc = len(clabels)
    fills = np.bincount(ccode, minlength=nc)
    s_num = np.bincount(ccode, weights=num, minlength=nc)
    s_idx = np.bincount(ccode, weights=idx, minlength=nc)
    s_k = np.bincount(ccode, weights=kk, minlength=nc)
    s_den = np.bincount(ccode, weights=den, minlength=nc)
    contracts = np.bincount(ccode, weights=amt, minlength=nc)
    nonpos = np.bincount(ccode, weights=k_nonpos.astype(float), minlength=nc).astype(int)
    scale = np.ones(nc) if cell_scale is None else pd.Series(cell_scale, dtype=float).reindex(clabels).to_numpy()
    occupied = (fills >= min_fills) & np.isfinite(scale)
    with np.errstate(invalid="ignore", divide="ignore"):
        A = 1e4 * s_num / s_idx
        Bv = 1e4 * s_num / s_den * scale

    cells = pd.concat([pd.DataFrame({"cell": np.asarray(clabels, dtype=object)}),
                       _cell_columns(list(clabels))], axis=1)
    cells = cells.assign(fills=fills, contracts=contracts, fills_k_le_0=nonpos, sum_edge=s_num, sum_index=s_idx,
                         sum_K=s_k, sum_den=s_den, scale=scale, occupied=occupied, A_bp=A, B_bp=Bv)
    for c in ("rank_A", "rank_B", "rank_shift", "A_lo", "A_hi", "B_lo", "B_hi", "rank_A_lo", "rank_A_hi",
              "rank_B_lo", "rank_B_hi"):
        cells[c] = np.nan

    occ = np.flatnonzero(occupied)
    res = {"b": int(b), "seed": int(seed), "level": float(level), "min_fills": int(min_fills), "n": int(len(occ)),
           "n_fills": int(fills[occ].sum()), "n_contracts": float(contracts[occ].sum()),
           "n_fills_k_le_0": int(nonpos[occ].sum()), "n_fills_nonfinite": n_nonfinite,
           "n_cells_any": int(nc), "stat": float("nan"), "lo": float("nan"), "hi": float("nan"), "n_days": 0,
           "_draws": np.full(b, np.nan)}
    if len(occ) == 0:
        return cells, res
    cells.loc[occ, "rank_A"] = ranks_desc(A[occ])
    cells.loc[occ, "rank_B"] = ranks_desc(Bv[occ])
    cells.loc[occ, "rank_shift"] = cells.loc[occ, "rank_B"] - cells.loc[occ, "rank_A"]
    res["stat"] = spearman(A[occ], Bv[occ])

    # (cell, day) sums of the occupied cells, then replicates as multiplicity-weighted sums
    remap = np.full(nc, -1)
    remap[occ] = np.arange(len(occ))
    sel = remap[ccode] >= 0
    rc = remap[ccode[sel]]
    dcode, dlabels = pd.factorize(pd.Series(day[sel]), sort=True)
    G, C = len(dlabels), len(occ)
    flat = rc * G + dcode

    def mat(w):
        return np.bincount(flat, weights=w, minlength=C * G).reshape(C, G)

    M_num, M_idx, M_den = mat(num[sel]), mat(idx[sel]), mat(den[sel])
    M_cnt = np.bincount(flat, minlength=C * G).reshape(C, G).astype(float)
    W = day_multiplicities(G, b=b, seed=seed).astype(float)
    with np.errstate(all="ignore"):     # numpy 2.0 forwards spurious FP flags from BLAS matmul (see inference_p1)
        S_num, S_idx, S_den = W @ M_num.T, W @ M_idx.T, W @ M_den.T
        n_rep = W @ M_cnt.T
    if not (np.isfinite(S_num).all() and np.isfinite(S_idx).all() and np.isfinite(S_den).all()):
        raise FloatingPointError("non-finite replicate sums")
    present = n_rep > 0.5
    with np.errstate(invalid="ignore", divide="ignore"):
        A_rep = np.where(present, 1e4 * S_num / S_idx, np.nan)
        B_rep = np.where(present, 1e4 * S_num / S_den * scale[occ][None, :], np.nan)
    draws = spearman_rows(A_rep, B_rep, present)
    lo, hi = _interval(draws, level)
    alpha = (1.0 - level) / 2.0
    rank_a = _ranks_rows_desc(A_rep, present)
    rank_b = _ranks_rows_desc(B_rep, present)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for name, mtx in (("A", A_rep), ("B", B_rep), ("rank_A", rank_a), ("rank_B", rank_b)):
            cells.loc[occ, f"{name}_lo"] = np.nanquantile(mtx, alpha, axis=0)
            cells.loc[occ, f"{name}_hi"] = np.nanquantile(mtx, 1.0 - alpha, axis=0)
    n_present = present.sum(axis=1)
    res.update({"lo": lo, "hi": hi, "n_days": int(G), "n_nan_draws": int((~np.isfinite(draws)).sum()),
                "cells_present_min": int(n_present.min()), "cells_present_median": float(np.median(n_present)),
                "first_day": str(dlabels[0]), "last_day": str(dlabels[-1]), "_draws": draws})
    if return_replicates:
        res.update({"_A_rep": A_rep, "_B_rep": B_rep, "_present": present})
    return cells, res


def h1_verdict(res: dict, threshold: float = H1_MAX_RHO, **extra) -> dict:
    hi = res.get("hi", float("nan"))
    rejected = bool(hi >= threshold) if np.isfinite(hi) else None
    out = {"hypothesis": "H1", "claim": f"Spearman rho < {threshold}", "stat": res["stat"], "lo": res["lo"],
           "hi": hi, "rejected": rejected, "rule": H1_RULE, "threshold": threshold}
    out.update({k: v for k, v in res.items() if k not in out})
    out.update(extra)
    return out


# =====================================================================================================================
# H2 and H3
# =====================================================================================================================

def h2_test(marginal: pd.DataFrame, variant: str = "ratio", b: int = B, seed: int = SEED, level: float = LEVEL,
            threshold: float = H2_MAX_MEDIAN) -> dict:
    """Median of the marginal-capital ratio of the drawn H2 sample with a day-cluster interval."""
    num_col, den_col = H2_VARIANTS[variant]
    mg = marginal
    is_ok = (mg["status"] == "ok").to_numpy() if "status" in mg else np.ones(len(mg), dtype=bool)
    den = mg[den_col].to_numpy(float)
    num = mg[num_col].to_numpy(float)
    excl = is_ok & ~(den > 0)
    keep = is_ok & (den > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = num / den
    nan = keep & ~np.isfinite(ratio)
    keep &= np.isfinite(ratio)
    res = median_bootstrap(ratio[keep], mg["day"].to_numpy()[keep], b=b, seed=seed, level=level)
    hi = res["hi"]
    out = {"hypothesis": "H2", "claim": f"median < {threshold}", "variant": variant, "numerator": num_col,
           "denominator": den_col, "stat": res["stat"], "lo": res["lo"], "hi": hi,
           "rejected": bool(hi >= threshold) if np.isfinite(hi) else None, "rule": H2_RULE, "threshold": threshold,
           "n": res["n"], "n_days": res["n_days"], "n_sample": int(len(mg)), "n_not_ok": int((~is_ok).sum()),
           "n_excluded": int(excl.sum()), "n_nonfinite": int(nan.sum()),
           "share_nonpositive": float(np.mean(ratio[keep] <= 0)) if keep.any() else float("nan"),
           "b": res["b"], "seed": res["seed"], "level": res["level"], "_draws": res["_draws"]}
    if "label" in mg:
        out["accounts"] = sorted(map(str, pd.unique(mg.loc[keep, "label"])))
    if "ccy" in mg:
        out["fills_by_ccy"] = {str(k): int(v) for k, v in mg.loc[keep, "ccy"].value_counts().sort_index().items()}
    if keep.any():
        days = pd.to_datetime(mg.loc[keep, "day"])
        out["first_day"], out["last_day"] = str(days.min().date()), str(days.max().date())
    if variant in mg.columns:          # cross-check against the ratio stored by books.marginal (B3)
        stored = mg[variant].to_numpy(float)
        both = keep & np.isfinite(stored)
        out["check_stored_ratio_max_abs"] = float(np.max(np.abs(stored[both] - ratio[both]))) if both.any() else None
        out["check_stored_ratio_nan_mismatch"] = int((np.isfinite(stored) != keep).sum())
    return out


def btc_eth_columns(maker_days: pd.DataFrame) -> pd.DataFrame:
    """K of the BTC and ETH legs only (per-currency columns summed; NaN without BTC or ETH legs), for the legacy-PM
    sensitivity (addendum 4, item 2)."""
    out = pd.DataFrame(index=maker_days.index)
    for m in ("sm", "pm", "pm2", "sm_mm", "pm_mm", "pm2_mm"):
        cols = [f"K_{m}_{c}" for c in BTC_ETH if f"K_{m}_{c}" in maker_days]
        out[f"K_{m}_be"] = maker_days[cols].sum(axis=1, min_count=1) if cols else np.nan
    return out


def h3_test(maker_days: pd.DataFrame, num: str = "K_sm", den: str = "K_pm2", b: int = B, seed: int = SEED,
            level: float = LEVEL, threshold: float = H3_MIN_MEDIAN) -> dict:
    """Median of ``num / den`` over the maker days with an option position (status ok) with a day-cluster interval."""
    md = maker_days
    is_ok = (md["status"] == "ok").to_numpy()
    d = md[den].to_numpy(float)
    n_ = md[num].to_numpy(float)
    applicable = is_ok & np.isfinite(d)
    excl = applicable & ~(d > 0)
    keep = applicable & (d > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = n_ / d
    keep &= np.isfinite(ratio)
    res = median_bootstrap(ratio[keep], md["day"].to_numpy()[keep], b=b, seed=seed, level=level)
    lo = res["lo"]
    out = {"hypothesis": "H3", "claim": f"median > {threshold}", "numerator": num, "denominator": den,
           "stat": res["stat"], "lo": lo, "hi": res["hi"],
           "rejected": bool(lo <= threshold) if np.isfinite(lo) else None, "rule": H3_RULE, "threshold": threshold,
           "n": res["n"], "n_days": res["n_days"], "n_rows": int(len(md)), "n_not_ok": int((~is_ok).sum()),
           "status_counts": {str(k): int(v) for k, v in md["status"].value_counts().sort_index().items()},
           "n_not_applicable": int((is_ok & ~np.isfinite(d)).sum()), "n_excluded": int(excl.sum()),
           "b": res["b"], "seed": res["seed"], "level": res["level"], "_draws": res["_draws"]}
    if "n_legs" in md:
        legs = md.loc[keep, "n_legs"].to_numpy(float)
        out["share_days_over_63_options"] = float(np.mean(legs > SM_MAX_OPTIONS)) if len(legs) else float("nan")
        out["days_over_63_options"] = int((legs > SM_MAX_OPTIONS).sum())
    if "label" in md:
        out["accounts"] = {str(k): int(v) for k, v in md.loc[keep, "label"].value_counts().sort_index().items()}
    if keep.any():
        days = pd.to_datetime(md.loc[keep, "day"])
        out["first_day"], out["last_day"] = str(days.min().date()), str(days.max().date())
    return out


# =====================================================================================================================
# Figure tables
# =====================================================================================================================

def capital_by_manager(frame: pd.DataFrame) -> pd.DataFrame:
    """Median (and quartiles) of K / index per manager x side x |delta| x tenor x currency; ``window = own`` is the
    manager's own window, ``window = pm2`` the PM2 window (the same fills for every manager)."""
    rows = []
    for window in ("own", "pm2"):
        for mgr in MANAGERS:
            flag = frame[f"in_{mgr}"] if window == "own" else frame["in_pm2"] & frame[f"in_{mgr}"]
            f = frame[flag.to_numpy(bool)]
            k = f[f"K_{mgr}"].to_numpy(float) / f["index_price"].to_numpy(float)
            kmm = f[f"K_{mgr}_mm"].to_numpy(float) / f["index_price"].to_numpy(float)
            g = pd.DataFrame({"ccy": f["ccy"].to_numpy(), "side": f["side"].to_numpy(),
                              "delta_bucket": f["delta_bucket"].to_numpy(), "tenor_bucket": f["tenor_bucket"].to_numpy(),
                              "k": k, "kmm": kmm})
            g = g[np.isfinite(g["k"].to_numpy())]
            if g.empty:
                continue
            agg = g.groupby(CELL_PARTS, sort=True).agg(
                fills=("k", "size"), median_k_over_index=("k", "median"),
                p25_k_over_index=("k", lambda x: float(np.quantile(x, 0.25))),
                p75_k_over_index=("k", lambda x: float(np.quantile(x, 0.75))),
                median_k_mm_over_index=("kmm", "median")).reset_index()
            agg.insert(0, "manager", mgr)
            agg.insert(0, "window", window)
            rows.append(agg)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _h2_ratio(mg: pd.DataFrame, variant: str) -> Tuple[np.ndarray, np.ndarray]:
    num_col, den_col = H2_VARIANTS[variant]
    den = mg[den_col].to_numpy(float)
    keep = (den > 0) & ((mg["status"] == "ok").to_numpy() if "status" in mg else True)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = mg[num_col].to_numpy(float) / den
    keep = keep & np.isfinite(r)
    return r, keep


def h2_distribution(marginal: pd.DataFrame) -> pd.DataFrame:
    """Quantiles, histogram (bins of 0.05 on [-1, 2] plus open tails) and share <= 0 of the H2 ratio per account label
    and overall, for every H2 variant."""
    rows = []
    labels = sorted(map(str, pd.unique(marginal["label"]))) + ["all"]
    for variant in H2_VARIANTS:
        r, keep = _h2_ratio(marginal, variant)
        for lab in labels:
            m = keep & ((marginal["label"].astype(str) == lab).to_numpy() if lab != "all" else True)
            v = r[m]
            rows.append({"label": lab, "variant": variant, "kind": "n", "x": np.nan, "x_hi": np.nan,
                         "value": float(len(v))})
            if len(v) == 0:
                continue
            rows.append({"label": lab, "variant": variant, "kind": "share_le_0", "x": 0.0, "x_hi": np.nan,
                         "value": float(np.mean(v <= 0))})
            for q in QUANTILES:
                rows.append({"label": lab, "variant": variant, "kind": "quantile", "x": q, "x_hi": np.nan,
                             "value": float(np.quantile(v, q))})
            counts, _ = np.histogram(v, bins=HIST_EDGES)
            for lo_, hi_, c in zip(HIST_EDGES[:-1], HIST_EDGES[1:], counts):
                rows.append({"label": lab, "variant": variant, "kind": "hist", "x": lo_, "x_hi": hi_,
                             "value": float(c)})
    return pd.DataFrame(rows)


def h3_series(maker_days: pd.DataFrame) -> pd.DataFrame:
    """K under SM, PM2 and legacy PM per maker day (labels only), also on the BTC and ETH legs alone, and the ratios."""
    md = maker_days
    be = btc_eth_columns(md)
    ok = (md["status"] == "ok").to_numpy()

    def ratio(a, b_):
        a, b_ = np.asarray(a, dtype=float), np.asarray(b_, dtype=float)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(ok & (b_ > 0), a / b_, np.nan)

    out = pd.DataFrame({"label": md["label"].astype(str).to_numpy(),
                        "day": pd.to_datetime(md["day"]).dt.strftime("%Y-%m-%d").to_numpy(),
                        "manager": md["manager"].to_numpy() if "manager" in md else np.nan,
                        "status": md["status"].to_numpy(),
                        "n_legs": md["n_legs"].to_numpy(float) if "n_legs" in md else np.nan,
                        "n_legs_pm": md["n_legs_pm"].to_numpy(float) if "n_legs_pm" in md else np.nan})
    out["over_63_options"] = out["n_legs"] > SM_MAX_OPTIONS
    for c in ("K_sm", "K_pm2", "K_pm", "K_sm_mm", "K_pm2_mm", "K_pm_mm"):
        out[c] = md[c].to_numpy(float)
    for c in ("K_sm_be", "K_pm2_be", "K_pm_be"):
        out[c] = be[c].to_numpy(float)
    out["ratio_sm_pm2"] = ratio(md["K_sm"], md["K_pm2"])
    out["ratio_sm_pm2_mm"] = ratio(md["K_sm_mm"], md["K_pm2_mm"])
    out["ratio_sm_pm_be"] = ratio(be["K_sm_be"], be["K_pm_be"])
    out["ratio_pm_pm2_be"] = ratio(be["K_pm_be"], be["K_pm2_be"])
    out["ratio_sm_pm2_be"] = ratio(be["K_sm_be"], be["K_pm2_be"])
    return out.sort_values(["label", "day"], kind="mergesort").reset_index(drop=True)


# =====================================================================================================================
# Review round 1: sign structure of H1, regimes, account managers (exploratory)
# =====================================================================================================================

def regime_of(ts_s) -> np.ndarray:
    """Regime label (R1 to R4) for UNIX seconds; a time at an event second belongs to the later regime."""
    k = np.searchsorted(np.asarray(REGIME_BOUNDS, dtype=np.int64), np.asarray(ts_s, dtype=np.int64), side="right")
    return np.asarray(REGIMES, dtype=object)[k]


def _day_seconds(days) -> np.ndarray:
    return (pd.to_datetime(pd.Series(days)).astype("int64") // 10 ** 9).to_numpy(np.int64)


def fill_regimes(mg: pd.DataFrame) -> np.ndarray:
    """Regime of each H2 fill: by ``ts`` (ms) when present, else by its UTC day."""
    if "ts" in mg:
        return regime_of(mg["ts"].to_numpy(np.int64) // 1000)
    return regime_of(_day_seconds(mg["day"]))


def account_manager(manager) -> np.ndarray:
    """``SM``, ``PM`` or ``PM2`` from a manager label such as ``PM2:ETH``."""
    return np.asarray([str(m).split(":", 1)[0] for m in manager], dtype=object)


def sign_floor(a_bp, draws: int = SIGN_DRAWS, seed: int = SEED) -> dict:
    """Spearman's rho between the ranks of ``a_bp`` and ranks that keep only the sign pattern.

    Capital is positive in every cell, so the cells with positive edge rank first under either denominator. Each
    draw gives the cells with ``a_bp > 0`` a random permutation of the top ranks and the others a random permutation
    of the remaining ranks; the statistic is the correlation of those ranks with the ranks of ``a_bp``."""
    a = np.asarray(a_bp, dtype=float)
    a = a[np.isfinite(a)]
    pos = a > 0
    n, n_pos = int(len(a)), int(pos.sum())
    out = {"draws": int(draws), "seed": int(seed), "n": n, "n_pos": n_pos, "n_nonpos": n - n_pos,
           "rule": "descriptive (no preregistered threshold)", "exploratory": True}
    if n < 3 or draws < 1:
        return {**out, "mean": float("nan"), "median": float("nan"), "p05": float("nan"), "p95": float("nan")}
    ra = ranks_desc(a)
    top = np.arange(1, n_pos + 1, dtype=float)
    rest = np.arange(n_pos + 1, n + 1, dtype=float)
    rng = np.random.default_rng(seed)
    rb = np.empty((draws, n))
    for i in range(draws):
        rb[i, pos] = rng.permutation(top)
        rb[i, ~pos] = rng.permutation(rest)
    rho = _pearson_rows(np.broadcast_to(ra, rb.shape), rb)
    return {**out, "mean": float(np.mean(rho)), "median": float(np.median(rho)),
            "p05": float(np.quantile(rho, 0.05)), "p95": float(np.quantile(rho, 0.95))}


def top_overlap(cells: pd.DataFrame, ks: Sequence[int] = (10, 20)) -> dict:
    """How many of the ``k`` best occupied cells by edge per capital are among the ``k`` best by edge per notional."""
    occ = cells[cells["occupied"].astype(bool)]
    out = {}
    for k in ks:
        a = set(occ.sort_values(["A_bp", "cell"], ascending=[False, True], kind="mergesort")["cell"].head(k))
        b = set(occ.sort_values(["B_bp", "cell"], ascending=[False, True], kind="mergesort")["cell"].head(k))
        out[f"top{k}"] = int(len(a & b))
    return out


H1_SIGN_GROUPS = ("within_pos", "within_nonpos", "within_sell", "within_buy", "within_pos_sell", "within_pos_buy")
# Groups chosen by the sign of the estimated edge: (edge > 0 wanted, maker side or None). Audit A04: the choice depends
# on the result, so every bootstrap replicate chooses again on its own A*; the maker-side groups stay fixed.
H1_SIGN_SELECT: Dict[str, Tuple[bool, Optional[str]]] = {
    "within_pos": (True, None), "within_nonpos": (False, None),
    "within_pos_sell": (True, "sell"), "within_pos_buy": (True, "buy")}
H1_SIDE_GROUPS = {"within_sell": "sell", "within_buy": "buy"}


def _sign_select(a: np.ndarray, side: np.ndarray, positive: bool, want_side: Optional[str]) -> np.ndarray:
    """Cells of a sign group: ``a > 0`` (or ``a <= 0``), optionally of one maker side; NaN (cell absent) is never in."""
    with np.errstate(invalid="ignore"):
        m = (a > 0) if positive else (a <= 0)
    m = np.asarray(m, dtype=bool) & np.isfinite(a)
    return m & (side == want_side) if want_side is not None else m


def h1_sign(frame: pd.DataFrame, cells: pd.DataFrame, k_col: str = "K_pm2", min_fills: int = MIN_CELL_FILLS,
            b: int = B, seed: int = SEED, level: float = LEVEL, draws: int = SIGN_DRAWS,
            full: Optional[Tuple[pd.DataFrame, dict]] = None) -> dict:
    """Sign structure of H1 on the occupied cells of the registered map (``cells``, from ``edge_map``).

    ``sign_floor``: rho from the sign pattern alone (see ``sign_floor``). ``within_*``: rho between edge per notional
    and edge per capital over the occupied cells of one group, with the day-cluster bootstrap of H1.
    ``top_overlap``: overlap of the best cells.

    Groups by the sign of the edge (``within_pos``, ``within_nonpos``, ``within_pos_sell``, ``within_pos_buy``;
    ``selection = per replicate``): the group depends on the estimate, so the statistic is "rho over the cells whose
    estimated edge is > 0 (<= 0)" and every replicate applies that rule to its own A* over all occupied cells present
    in it (the draws of the registered H1 bootstrap, ``full`` = ``edge_map`` of ``frame`` with replicates, computed
    here when not given). With the cells held fixed (the version before audit A04) the replicates lost the cut at
    zero that shapes the estimate, and the estimate could fall outside its own interval. ``switch_share_mean``: share
    of the estimate's cells that a replicate does not choose, mean over replicates. Groups by maker side
    (``within_sell``, ``within_buy``; ``selection = fixed``) do not choose on the result and keep the fixed cells."""
    occ = cells[cells["occupied"].astype(bool)].reset_index(drop=True)
    a_bp, b_bp = occ["A_bp"].to_numpy(float), occ["B_bp"].to_numpy(float)
    side = occ["side"].astype(str).to_numpy()
    out: dict = {"sign_floor": sign_floor(a_bp, draws=draws, seed=seed),
                 "top_overlap": top_overlap(cells),
                 "sign_agree": int((np.sign(a_bp) == np.sign(b_bp)).sum())}
    if full is None:
        full = edge_map(frame, k_col, min_fills=min_fills, b=b, seed=seed, level=level, return_replicates=True)
    fcells, fres = full
    if fcells.loc[fcells["occupied"].astype(bool), "cell"].tolist() != occ["cell"].tolist():
        raise ValueError("h1_sign: the occupied cells of the replicate map differ from the cells given")
    A_rep, B_rep, present = fres["_A_rep"], fres["_B_rep"], fres["_present"]
    for name in H1_SIGN_GROUPS:
        if name in H1_SIDE_GROUPS:
            chosen = set(occ.loc[side == H1_SIDE_GROUPS[name], "cell"])
            sub = frame[frame["cell"].isin(chosen).to_numpy()]
            _, res = edge_map(sub, k_col, min_fills=min_fills, b=b, seed=seed, level=level)
            v = h1_verdict(res)
            v["capital"] = k_col
            out[name] = {**_stats(v, "H1"), "cells": name, "selection": "fixed", "_draws": res["_draws"]}
            continue
        positive, want = H1_SIGN_SELECT[name]
        m0 = _sign_select(a_bp, side, positive, want)
        chosen_rep = present & _sign_select(A_rep, side[None, :], positive, want)
        d = spearman_rows(A_rep, B_rep, chosen_rep)
        lo, hi = _interval(d, level)
        res = {"stat": spearman(a_bp[m0], b_bp[m0]), "lo": lo, "hi": hi, "n": int(m0.sum()),
               "n_days": fres["n_days"], "n_fills": int(occ.loc[m0, "fills"].sum()),
               "n_fills_k_le_0": int(occ.loc[m0, "fills_k_le_0"].sum()), "min_fills": int(min_fills),
               "b": int(b), "seed": int(seed), "level": float(level)}
        v = h1_verdict(res)
        leave = (m0[None, :] & ~chosen_rep).sum(axis=1) / max(int(m0.sum()), 1)
        out[name] = {**_stats(v, "H1"), "cells": name, "selection": "per replicate",
                     "n_rep_median": float(np.median(chosen_rep.sum(axis=1))),
                     "switch_share_mean": float(leave.mean()), "n_nan_draws": int((~np.isfinite(d)).sum()),
                     "_draws": d}
    return out


def h1_interval_shape(draws: np.ndarray, stat: float, level: float = LEVEL, b: Optional[int] = None,
                      seed: Optional[int] = None) -> dict:
    """Shape of the percentile interval of H1 (audit A28, exploratory; the registered verdict uses ``lo, hi``).

    ``lo, hi``: the registered percentile interval of the draws. ``share_ge_stat``: share of draws at or above the
    estimate (0.5 for a centred interval). ``basic_lo, basic_hi``: the reflected interval ``2 stat - (hi, lo)``.
    ``bc_lo, bc_hi``: bias-corrected percentile interval (Efron), quantiles ``Phi(2 z0 -/+ z)`` with
    ``z0 = Phi^-1(share of draws < stat)`` and ``z = Phi^-1(1 - (1 - level) / 2)``."""
    d = np.asarray(draws, dtype=float)
    d = d[np.isfinite(d)]
    alpha = (1.0 - level) / 2.0
    out = {"stat": float(stat), "level": float(level), "n_draws": int(len(d)), "exploratory": True,
           "rule": "descriptive (no preregistered threshold)"}
    if b is not None:
        out["b"] = int(b)
    if seed is not None:
        out["seed"] = int(seed)
    if len(d) == 0 or not np.isfinite(stat):
        return {**out, **{k: float("nan") for k in ("lo", "hi", "mean_draw", "median_draw", "share_ge_stat", "z0",
                                                   "basic_lo", "basic_hi", "bc_lo", "bc_hi")}}
    lo, hi = float(np.quantile(d, alpha)), float(np.quantile(d, 1.0 - alpha))
    z0 = float(norm.ppf(np.mean(d < stat)))
    z = float(norm.ppf(1.0 - alpha))
    if np.isfinite(z0):
        bc_lo, bc_hi = float(np.quantile(d, norm.cdf(2 * z0 - z))), float(np.quantile(d, norm.cdf(2 * z0 + z)))
    else:
        bc_lo = bc_hi = float("nan")
    return {**out, "lo": lo, "hi": hi, "mean_draw": float(d.mean()), "median_draw": float(np.median(d)),
            "share_ge_stat": float(np.mean(d >= stat)), "z0": z0, "basic_lo": 2 * float(stat) - hi,
            "basic_hi": 2 * float(stat) - lo, "bc_lo": bc_lo, "bc_hi": bc_hi}


def h2_regime_rows(mg: pd.DataFrame, **kw) -> Tuple[dict, List[dict]]:
    """H2 statistic per parameter regime (exploratory)."""
    reg = fill_regimes(mg)
    d, rows = {}, []
    for r in REGIMES:
        sub = mg[reg == r]
        if not len(sub):
            continue
        d[r] = _h2_stats(h2_test(sub, variant="ratio", **kw))
        rows.append({"variant": "ratio", "group": f"regime={r}", **d[r]})
    return d, rows


def h3_review_rows(md: pd.DataFrame, **kw) -> Tuple[dict, List[dict]]:
    """H3 per parameter regime, per manager of the account and on books of at most 63 options without the SM
    accounts (exploratory)."""
    e: dict = {"by_regime": {}, "by_account_manager": {}}
    rows: List[dict] = []
    reg = regime_of(_day_seconds(md["day"]))
    for r in REGIMES:
        sub = md[reg == r]
        if (sub["status"] == "ok").any():
            e["by_regime"][r] = _stats(h3_test(sub, **kw), "H3")
            rows.append({"variant": "sm_pm2", "group": f"regime={r}", **e["by_regime"][r]})
    fam = account_manager(md["manager"]) if "manager" in md else np.full(len(md), "", dtype=object)
    for m in ("SM", "PM", "PM2"):
        sub = md[fam == m]
        if (sub["status"] == "ok").any():
            e["by_account_manager"][m] = _stats(h3_test(sub, **kw), "H3")
            rows.append({"variant": "sm_pm2", "group": f"account_manager={m}", **e["by_account_manager"][m]})
    small = md[(md["n_legs"] <= SM_MAX_OPTIONS).to_numpy() & (fam != "SM")]
    if (small["status"] == "ok").any():
        e["sm_pm2_le63_no_sm"] = _stats(h3_test(small, **kw), "H3")
        rows.append({"variant": "sm_pm2_le63_no_sm", "group": "all", **e["sm_pm2_le63_no_sm"]})
    return e, rows


def h2_population(root: Path) -> Optional[dict]:
    """Size of the H2 population before the draw, and whether the preregistered draw from it gives the fills of
    ``marginal.parquet``; None when the book inputs are not there (``books.h2_population``)."""
    from . import books
    root = Path(root)
    need = [root / books.BOOKS_DIR / "top_makers.json", root / books.BOOKS_DIR / "snapshots.parquet",
            root / books.MARKOUTS]
    if not all(p.exists() for p in need):
        return None
    top = json.loads(need[0].read_text())["subaccounts"]
    snaps = pd.read_parquet(need[1])
    m = pd.read_parquet(need[2], columns=books.MARKOUT_B3_COLUMNS)
    m = m[m["maker_sub"].isin(top)].reset_index(drop=True)
    pop = books.h2_population(m, snaps, top)
    sample = books.h2_sample(pop)
    mg = pd.read_parquet(paths(root)["marginal"], columns=["fill_key"])
    same = sorted(map(str, sample["trade_id"])) == sorted(map(str, mg["fill_key"]))
    return {"n": int(len(pop)), "sample": int(len(sample)), "sample_equals_marginal": bool(same),
            "rule": "descriptive (no preregistered threshold)"}


def review_entries(pm2: pd.DataFrame, cells: pd.DataFrame, mg: pd.DataFrame, md: pd.DataFrame,
                   min_fills: int = MIN_CELL_FILLS, **kw) -> Tuple[dict, dict, dict, List[dict], List[dict], dict]:
    """(h1_sign, d_h2 additions, e_h3 additions, sens_h2 rows, sens_h3 rows, h1_interval) of the review round and
    the audit (A04: sign groups chosen again in every replicate; A28: shape of the registered H1 interval). Both H1
    entries use the replicates of the registered map (same draws as ``h1.json``)."""
    full = edge_map(pm2, "K_pm2", min_fills=min_fills, return_replicates=True, **kw)
    sign = h1_sign(pm2, cells, min_fills=min_fills, full=full, **kw)
    interval = h1_interval_shape(full[1]["_draws"], full[1]["stat"], level=kw.get("level", LEVEL),
                                 b=kw.get("b", B), seed=kw.get("seed", SEED))
    d_reg, h2_rows = h2_regime_rows(mg, **kw)
    e_add, h3_rows = h3_review_rows(md, **kw)
    return sign, {"by_regime": d_reg}, e_add, h2_rows, h3_rows, interval


def _merge_rows(old: pd.DataFrame, new: List[dict]) -> pd.DataFrame:
    """Rows of ``old`` whose (variant, group) is not in ``new``, then ``new``."""
    new_df = pd.DataFrame(new)
    if new_df.empty:
        return old
    keys = set(zip(new_df["variant"].astype(str), new_df["group"].astype(str)))
    keep = [(str(v), str(g)) not in keys for v, g in zip(old["variant"], old["group"])]
    return pd.concat([old[keep], new_df], ignore_index=True)


def run_extras(root: Path = REPO, out: Optional[Path] = None, b: int = B, seed: int = SEED, level: float = LEVEL,
               min_fills: int = MIN_CELL_FILLS) -> dict:
    """Only the review-round entries, merged into the existing ``sensitivity.json``, ``sens_h2.csv`` and
    ``sens_h3.csv`` of ``out`` (every other entry is kept as it is)."""
    p = paths(root)
    out = Path(out) if out is not None else p["out"]
    t0 = time.time()
    sens = json.loads((out / "sensitivity.json").read_text())
    fr = load_edge_frame(root)
    pm2 = fr[fr["in_pm2"].to_numpy()]
    cells, _ = edge_map(pm2, "K_pm2", min_fills=min_fills, b=1, seed=seed, level=level)
    mg = pd.read_parquet(p["marginal"])
    md = pd.read_parquet(p["maker_days"])
    kw = dict(b=b, seed=seed, level=level)
    sign, d_add, e_add, h2_rows, h3_rows, interval = review_entries(pm2, cells, mg, md, min_fills=min_fills, **kw)
    sens["h1_sign"] = sign
    sens["h1_interval"] = interval
    sens.setdefault("d_h2", {}).update(d_add)
    pop = h2_population(root)
    if pop is not None:
        sens["d_h2"]["population"] = pop
    sens.setdefault("e_h3", {}).update(e_add)
    write_json(sens, out / "sensitivity.json")
    for name, rows in (("sens_h2.csv", h2_rows), ("sens_h3.csv", h3_rows)):
        old = pd.read_csv(out / name) if (out / name).exists() else pd.DataFrame(columns=["variant", "group"])
        write_csv(_merge_rows(old, rows), out / name)
    log.info("extras done in %.1f s", time.time() - t0)
    return sens


# =====================================================================================================================
# Runs
# =====================================================================================================================

def _summary(v: dict) -> str:
    return (f"{v.get('hypothesis', '')} {v.get('variant', '')} stat={v['stat']:.4f} "
            f"[{v['lo']:.4f}, {v['hi']:.4f}] n={v['n']} rejected={v['rejected']}")


def run(root: Path = REPO, out: Optional[Path] = None, b: int = B, seed: int = SEED, level: float = LEVEL,
        min_fills: int = MIN_CELL_FILLS) -> dict:
    """H1 to H3; writes ``h1_cells.csv``, ``h1.json``, ``h2.json``, ``h3.json``."""
    p = paths(root)
    out = Path(out) if out is not None else p["out"]
    t0 = time.time()
    fr = load_edge_frame(root)
    win = fr[fr["in_pm2"].to_numpy()]
    cells, res = edge_map(win, "K_pm2", min_fills=min_fills, b=b, seed=seed, level=level)
    h1 = h1_verdict(res, map="pm2", window="PM2 window per currency", capital="K_pm2 (IM)",
                    net_edge="addendum 2: MO_30m - (fee - rebate) / amount - hedge (1 bp perp half spread)",
                    n_fills_window=int(len(win)),
                    window_start_utc={c: pd.Timestamp(WINDOW_START["pm2"][c], unit="s", tz="UTC").isoformat()
                                      for c in CCYS},
                    fills_by_ccy={str(k): int(v) for k, v in
                                  cells[cells["occupied"]].groupby("ccy")["fills"].sum().items()},
                    cells_by_ccy={str(k): int(v) for k, v in
                                  cells[cells["occupied"]].groupby("ccy").size().items()})
    write_csv(cells.assign(window="pm2", capital="K_pm2"), out / "h1_cells.csv")
    write_json(h1, out / "h1.json")
    print(_summary(h1))

    mg = pd.read_parquet(p["marginal"])
    h2 = h2_test(mg, b=b, seed=seed, level=level)
    write_json(h2, out / "h2.json")
    print(_summary(h2))

    md = pd.read_parquet(p["maker_days"])
    h3 = h3_test(md, b=b, seed=seed, level=level)
    write_json(h3, out / "h3.json")
    print(_summary(h3))
    log.info("run done in %.1f s", time.time() - t0)
    return {"H1": h1, "H2": h2, "H3": h3}


def _stats(v: dict, rule_key: str) -> dict:
    """Compact exploratory result with the verdict the preregistered rule would give."""
    keep = ("stat", "lo", "hi", "rejected", "n", "n_days", "n_fills", "n_excluded", "n_not_applicable",
            "n_fills_k_le_0", "share_nonpositive", "share_days_over_63_options", "numerator", "denominator",
            "variant", "min_fills", "b", "seed", "level")
    out = {k: v[k] for k in keep if k in v}
    out["rule"] = rule_key
    out["exploratory"] = True
    return out


def _h2_stats(v: dict) -> dict:
    """``_stats`` of an H2 variant plus the PM2 lib of numerator and denominator (``account/account`` etc.)."""
    return {**_stats(v, "H2"), "libs": "/".join(H2_LIBS[v["variant"]])}


def _map_rows(name: str, cells: pd.DataFrame) -> pd.DataFrame:
    c = cells.copy()
    c.insert(0, "map", name)
    return c


def run_sensitivity(root: Path = REPO, out: Optional[Path] = None, b: int = B, seed: int = SEED,
                    level: float = LEVEL, min_fills: int = MIN_CELL_FILLS) -> dict:
    """Exploratory sensitivities (a) to (g) and the figure tables; writes ``sensitivity.json``, ``sens_*.csv`` and
    ``fig_*.csv``."""
    p = paths(root)
    out = Path(out) if out is not None else p["out"]
    t0 = time.time()
    fr = load_edge_frame(root)
    mg = pd.read_parquet(p["marginal"])
    md = pd.read_parquet(p["maker_days"])
    kw = dict(b=b, seed=seed, level=level)
    sens: dict = {"exploratory": True,
                  "note": "exploratory per the preregistration; 'rejected' is the verdict the preregistered rule "
                          "would give on this variant",
                  "b": b, "seed": seed, "level": level}
    maps: List[pd.DataFrame] = []

    def emap(name, frame, k_col, **more):
        cells, res = edge_map(frame, k_col, min_fills=min_fills, **kw, **more)
        maps.append(_map_rows(name, cells))
        v = h1_verdict(res)
        v["capital"] = k_col
        log.info("map %s: rho %.3f [%.3f, %.3f] cells %d", name, v["stat"], v["lo"], v["hi"], v["n"])
        return _stats(v, "H1")

    pm2 = fr[fr["in_pm2"].to_numpy()]
    main_map = emap("pm2", pm2, "K_pm2")

    # (a) maps under SM (whole period) and legacy PM, also on the PM2 window's fills
    sens["a_maps"] = {
        "pm2": main_map,
        "sm_all": emap("sm_all", fr[fr["in_sm"].to_numpy()], "K_sm"),
        "pm_all": emap("pm_all", fr[fr["in_pm"].to_numpy()], "K_pm"),
        "sm_pm2_window": emap("sm_pm2win", pm2, "K_sm"),
        "pm_pm2_window": emap("pm_pm2win", pm2[pm2["in_pm"].to_numpy()], "K_pm"),
    }
    # (b) MM instead of IM
    sens["b_mm"] = {
        "h1_pm2_mm": emap("pm2_mm", pm2, "K_pm2_mm"),
        "h1_sm_all_mm": emap("sm_all_mm", fr[fr["in_sm"].to_numpy()], "K_sm_mm"),
        "h2_ratio_mm": _h2_stats(h2_test(mg, variant="ratio_mm", **kw)),
        "h2_ratio_mm_std": _h2_stats(h2_test(mg, variant="ratio_mm_std", **kw)),
        "h3_mm": _stats(h3_test(md, num="K_sm_mm", den="K_pm2_mm", **kw), "H3"),
    }
    # (c) Paper 1's net edge form (fee and rebate undivided)
    sens["c_p1_net_edge"] = {"h1_pm2": emap("pm2_p1ne", pm2, "K_pm2", edge_col="edge_p1")}

    # (d) H2 variants, per account and per currency
    h2_rows = []
    d: dict = {}
    for variant in H2_VARIANTS:
        v = h2_test(mg, variant=variant, **kw)
        d[variant] = _h2_stats(v)
        h2_rows.append({"variant": variant, "group": "all", **d[variant]})
    for group_col in ("label", "ccy"):
        d[f"by_{group_col}"] = {}
        for g in sorted(map(str, pd.unique(mg[group_col]))):
            v = h2_test(mg[mg[group_col].astype(str) == g], variant="ratio", **kw)
            d[f"by_{group_col}"][g] = _h2_stats(v)
            h2_rows.append({"variant": "ratio", "group": f"{group_col}={g}", **d[f"by_{group_col}"][g]})
    sens["d_h2"] = d

    # (e) H3 with the legacy PM on BTC and ETH legs, per account, share of days over 63 options
    mdx = pd.concat([md, btc_eth_columns(md)], axis=1)
    e: dict = {}
    h3_rows = []
    for name, num, den, frame in (("sm_pm2", "K_sm", "K_pm2", mdx), ("sm_pm2_mm", "K_sm_mm", "K_pm2_mm", mdx),
                                  ("sm_pm_be", "K_sm_be", "K_pm_be", mdx), ("pm_pm2_be", "K_pm_be", "K_pm2_be", mdx),
                                  ("sm_pm2_be", "K_sm_be", "K_pm2_be", mdx),
                                  ("sm_pm2_le63", "K_sm", "K_pm2", mdx[mdx["n_legs"] <= SM_MAX_OPTIONS]),
                                  ("sm_pm2_gt63", "K_sm", "K_pm2", mdx[mdx["n_legs"] > SM_MAX_OPTIONS])):
        v = _stats(h3_test(frame, num=num, den=den, **kw), "H3")
        if not num.startswith("K_sm"):          # legacy PM against PM2 is descriptive, the H3 threshold is for SM
            v.update(rejected=None, rule="descriptive (no preregistered threshold)")
        e[name] = v
        h3_rows.append({"variant": name, "group": "all", **v})
    e["by_label"] = {}
    for g in sorted(map(str, pd.unique(md["label"]))):
        sub = mdx[md["label"].astype(str) == g]
        v = h3_test(sub, **kw)
        e["by_label"][g] = _stats(v, "H3")
        h3_rows.append({"variant": "sm_pm2", "group": f"label={g}", **_stats(v, "H3")})
        if sub["K_pm_be"].notna().any():
            v = h3_test(sub, num="K_sm_be", den="K_pm_be", **kw)
            h3_rows.append({"variant": "sm_pm_be", "group": f"label={g}", **_stats(v, "H3")})
    ok = md["status"] == "ok"
    e["share_days_over_63_options"] = float((md.loc[ok, "n_legs"] > SM_MAX_OPTIONS).mean())
    e["days_over_63_options"] = int((md.loc[ok, "n_legs"] > SM_MAX_OPTIONS).sum())
    e["days_ok"] = int(ok.sum())
    sens["e_h3"] = e

    # (f) time normalisations: to expiry (annualised) and by the empirical holding time per cell
    f_: dict = {"to_expiry": emap("pm2_tau", pm2, "K_pm2", tau_col="tau")}
    f_["to_expiry"]["unit"] = "bp of PM2 capital per year: 1e4 sum(NE a) / sum(K a tau)"
    if p["holding"].exists():
        hold = pd.read_csv(p["holding"])
        hold = hold[hold["window"] == "pm2"]
        keys = cell_labels(hold["ccy"], np.where(hold["side"] == "buy", 1, -1), hold["delta_bucket"],
                           hold["tenor_bucket"])
        for col, name in (("median_days", "holding"), ("median_days_excl_transfer", "holding_excl_transfer")):
            if col not in hold:
                continue
            days_ = pd.Series(hold[col].to_numpy(float), index=keys)
            scale = (365.0 / days_).where(days_ > 0)
            f_[name] = emap(f"pm2_{name}", pm2, "K_pm2", cell_scale=scale)
            f_[name]["unit"] = f"bp of PM2 capital per year: B * 365 / {col} (results/p2/holding_time.csv, pm2)"
    sens["f_time"] = f_

    # (g) rho per currency
    g_: dict = {}
    for c in CCYS:
        sub = pm2[pm2["ccy"].to_numpy() == c]
        if len(sub):
            g_[f"pm2_{c}"] = emap(f"pm2_{c}", sub, "K_pm2")
        sub = fr[fr["in_sm"].to_numpy() & (fr["ccy"].to_numpy() == c)]
        if len(sub):
            g_[f"sm_all_{c}"] = emap(f"sm_all_{c}", sub, "K_sm")
    sens["g_by_ccy"] = g_

    # review round 1: sign structure of H1, regimes, account managers, small books without SM, H2 population
    main_cells = maps[0].drop(columns="map")
    sign, d_add, e_add, more_h2, more_h3, interval = review_entries(pm2, main_cells, mg, md, min_fills=min_fills,
                                                                    **kw)
    sens["h1_sign"] = sign
    sens["h1_interval"] = interval
    sens["d_h2"].update(d_add)
    pop = h2_population(root)
    if pop is not None:
        sens["d_h2"]["population"] = pop
    sens["e_h3"].update(e_add)
    h2_rows += more_h2
    h3_rows += more_h3

    all_maps = pd.concat(maps, ignore_index=True)
    write_csv(all_maps, out / "sens_h1_cells.csv")
    write_csv(pd.DataFrame(h2_rows), out / "sens_h2.csv")
    write_csv(pd.DataFrame(h3_rows), out / "sens_h3.csv")
    write_json(sens, out / "sensitivity.json")

    # figure tables
    fig_maps = all_maps[all_maps["map"].isin(["pm2", "sm_all", "pm_all", "sm_pm2win", "pm_pm2win"])]
    write_csv(fig_maps, out / "fig_edge_maps.csv")
    write_csv(capital_by_manager(fr), out / "fig_capital_by_manager.csv")
    write_csv(h2_distribution(mg), out / "fig_h2_dist.csv")
    write_csv(h3_series(md), out / "fig_h3_series.csv")
    log.info("sensitivity done in %.1f s", time.time() - t0)
    return sens


# =====================================================================================================================
# CLI
# =====================================================================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="derive_surface p2 infer", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run", "sensitivity", "extras"])
    ap.add_argument("--root", type=Path, default=REPO, help="repository root (data/ and results/ below it)")
    ap.add_argument("--out", type=Path, default=None, help="output directory (default <root>/results/p2)")
    ap.add_argument("--b", type=int, default=B)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--min-fills", type=int, default=MIN_CELL_FILLS, help="occupied cell threshold (tests only)")
    a = ap.parse_args(list(sys.argv[1:] if argv is None else argv))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if a.cmd == "run":
        run(a.root, a.out, b=a.b, seed=a.seed, min_fills=a.min_fills)
    elif a.cmd == "extras":
        run_extras(a.root, a.out, b=a.b, seed=a.seed, min_fills=a.min_fills)
    else:
        run_sensitivity(a.root, a.out, b=a.b, seed=a.seed, min_fills=a.min_fills)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
