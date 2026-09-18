"""Inference for paper 1: the four pre-registered hypotheses, net edge per cell, robustness.

Everything clusters on the taker wallet.  Regression coefficients are tested with a wild cluster bootstrap
(restricted residuals, Rademacher weights, G/(G-1) correction, p = (1 + #)/(B + 1)); means and cell averages
get a percentile interval from a cluster (pairs) bootstrap plus the wild bootstrap p-value against zero.
Fixed effects are instrument × day, applied as a within transformation.

The bootstrap uses per-cluster sufficient statistics (X'X, X'y-hat, X'u per cluster), so one draw costs
O(G·k²) instead of O(n·k) and B = 9 999 stays cheap on 600 000 fills.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

HORIZON = "30m"
HORIZON_SECONDS = {"1m": 60, "5m": 300, "30m": 1_800, "4h": 14_400, "24h": 86_400}
B = 9_999
SEED = 20260917
HYPE_EVENT_MS = 1_782_205_200_000  # 2026-06-23 09:00 UTC, Deribit HYPE_USDC options
MIN_CELL_FILLS = 200
PERP_HALF_SPREAD_BP = (0.0, 1.0, 3.0)
PERP_TAKER_FEE = 3e-4
CLASSES = ["vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]


def within(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Values minus their group mean."""
    s = pd.Series(np.asarray(values, dtype=float))
    return (s - s.groupby(pd.Series(groups).values).transform("mean")).to_numpy()


def ols_fe(y: np.ndarray, X: np.ndarray, groups: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """OLS after removing group means from y and every column of X."""
    yd = within(y, groups)
    Xd = np.column_stack([within(X[:, j], groups) for j in range(X.shape[1])])
    with np.errstate(all="ignore"):  # numpy 2 forwards spurious BLAS flags on small matrices
        XtX_inv = np.linalg.pinv(Xd.T @ Xd)
        beta = XtX_inv @ (Xd.T @ yd)
        resid = yd - Xd @ beta
    return beta, resid, XtX_inv


def _cluster_index(clusters: np.ndarray) -> Tuple[np.ndarray, int]:
    codes, uniques = pd.factorize(pd.Series(clusters), sort=True)
    return codes, len(uniques)


def _cluster_stats(Xd: np.ndarray, resid: np.ndarray, codes: np.ndarray, n_cluster: int) -> np.ndarray:
    """Per-cluster score vectors X_g' u_g."""
    k = Xd.shape[1]
    scores = np.zeros((n_cluster, k))
    for j in range(k):
        scores[:, j] = np.bincount(codes, weights=Xd[:, j] * resid, minlength=n_cluster)
    return scores


def _cluster_robust_var(XtX_inv: np.ndarray, scores: np.ndarray, n_cluster: int) -> np.ndarray:
    with np.errstate(all="ignore"):                           # numpy 2.0 reports spurious FP errors from BLAS matmul
        meat = scores.T @ scores * (n_cluster / max(n_cluster - 1, 1))
        return XtX_inv @ meat @ XtX_inv


def wild_cluster_p(y: np.ndarray, X: np.ndarray, groups: np.ndarray, clusters: np.ndarray, test_col: int,
                   b: int = B, seed: int = SEED) -> dict:
    """Wild cluster bootstrap for H0: beta[test_col] = 0 (restricted residuals, Rademacher weights)."""
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    beta, resid, XtX_inv = ols_fe(y, X, groups)
    codes, n_cluster = _cluster_index(clusters)
    Xd = np.column_stack([within(X[:, j], groups) for j in range(X.shape[1])])
    yd = within(y, groups)
    scores = _cluster_stats(Xd, resid, codes, n_cluster)
    var = _cluster_robust_var(XtX_inv, scores, n_cluster)
    se = float(np.sqrt(max(var[test_col, test_col], 0.0)))
    t = float(beta[test_col] / se) if se > 0 else np.nan
    keep = [j for j in range(X.shape[1]) if j != test_col]
    if keep:
        Xr = Xd[:, keep]
        with np.errstate(all="ignore"):
            beta_r = np.linalg.pinv(Xr.T @ Xr) @ (Xr.T @ yd)
            fitted_r = Xr @ beta_r
    else:
        fitted_r = np.zeros_like(yd)
    resid_r = yd - fitted_r
    # per-cluster statistics of the restricted fit
    k = Xd.shape[1]
    Q = np.zeros((n_cluster, k, k))
    for i in range(k):
        for j in range(k):
            Q[:, i, j] = np.bincount(codes, weights=Xd[:, i] * Xd[:, j], minlength=n_cluster)
    R = np.zeros((n_cluster, k))
    S = np.zeros((n_cluster, k))
    for j in range(k):
        R[:, j] = np.bincount(codes, weights=Xd[:, j] * fitted_r, minlength=n_cluster)
        S[:, j] = np.bincount(codes, weights=Xd[:, j] * resid_r, minlength=n_cluster)
    A = S @ XtX_inv.T  # contribution of each cluster to beta*
    beta_r_full = XtX_inv @ R.sum(axis=0)
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(b):
        w = rng.choice(np.array([-1.0, 1.0]), size=n_cluster)
        beta_star = beta_r_full + A.T @ w
        m = R + w[:, None] * S - np.einsum("gij,j->gi", Q, beta_star)
        var_star = _cluster_robust_var(XtX_inv, m, n_cluster)
        se_star = np.sqrt(max(var_star[test_col, test_col], 0.0))
        t_star = beta_star[test_col] / se_star if se_star > 0 else np.nan
        if np.isfinite(t_star) and abs(t_star) >= abs(t):
            extreme += 1
    return {"beta": float(beta[test_col]), "se": se, "t": t, "p": (1 + extreme) / (b + 1),
            "n": int(len(y)), "clusters": int(n_cluster), "b": int(b)}


def wild_cluster_mean_p(values: np.ndarray, clusters: np.ndarray, b: int = B, seed: int = SEED,
                        chunk: int = 500) -> Tuple[float, float, float]:
    """Wild cluster bootstrap for H0: mean = 0 (no fixed effects); returns (t, p, se)."""
    codes, n_cluster = _cluster_index(clusters)
    n = len(values)
    correction = n_cluster / max(n_cluster - 1, 1)
    sums = np.bincount(codes, weights=values, minlength=n_cluster)
    counts = np.bincount(codes, minlength=n_cluster).astype(float)
    mean = values.sum() / n
    scores = sums - counts * mean
    se = float(np.sqrt((scores ** 2).sum() * correction) / n)
    t = mean / se if se > 0 else np.nan
    rng = np.random.default_rng(seed)
    extreme, drawn = 0, 0
    with np.errstate(all="ignore"):                           # numpy 2.0 reports spurious FP errors from BLAS matmul
        while drawn < b:
            size = min(chunk, b - drawn)
            w = rng.choice(np.array([-1.0, 1.0]), size=(size, n_cluster))
            beta = w @ sums / n                               # under H0 the residuals are the values themselves
            score = w * sums - counts[None, :] * beta[:, None]
            se_star = np.sqrt((score ** 2).sum(axis=1) * correction) / n
            t_star = np.where(se_star > 0, beta / np.where(se_star > 0, se_star, 1.0), np.nan)
            extreme += int(np.nansum(np.abs(t_star) >= abs(t)))
            drawn += size
    return t, (1 + extreme) / (b + 1), se


def cluster_mean_ci(values: np.ndarray, clusters: np.ndarray, b: int = B, seed: int = SEED,
                    level: float = 0.95, chunk: int = 500) -> dict:
    """Percentile interval of the mean from a cluster (pairs) bootstrap plus the wild bootstrap p-value."""
    values = np.asarray(values, dtype=float)
    ok = np.isfinite(values)
    values, clusters = values[ok], np.asarray(clusters)[ok]
    if len(values) == 0:
        return {"mean": np.nan, "lo": np.nan, "hi": np.nan, "p": np.nan, "t": np.nan, "se": np.nan,
                "n": 0, "clusters": 0, "level": level}
    codes, n_cluster = _cluster_index(clusters)
    sums = np.bincount(codes, weights=values, minlength=n_cluster)
    counts = np.bincount(codes, minlength=n_cluster).astype(float)
    rng = np.random.default_rng(seed)
    draws = np.empty(b)
    drawn = 0
    while drawn < b:
        size = min(chunk, b - drawn)
        pick = rng.integers(0, n_cluster, (size, n_cluster))
        draws[drawn:drawn + size] = sums[pick].sum(axis=1) / np.maximum(counts[pick].sum(axis=1), 1e-12)
        drawn += size
    alpha = (1 - level) / 2
    t, p, se = wild_cluster_mean_p(values, clusters, b=b, seed=seed)
    return {"mean": float(values.mean()), "lo": float(np.quantile(draws, alpha)), "hi": float(np.quantile(draws, 1 - alpha)),
            "p": p, "t": t, "se": se, "n": int(len(values)), "clusters": int(n_cluster), "level": level}


def top_loss_share(values: np.ndarray, wallets: np.ndarray, top: int = 10, b: int = B, seed: int = SEED,
                   level: float = 0.90) -> dict:
    """Share of the maker's aggregate loss that the `top` worst taker wallets account for."""
    df = pd.DataFrame({"w": np.asarray(wallets), "v": np.asarray(values, dtype=float)}).dropna()
    per = df.groupby("w")["v"].sum().to_numpy()

    def share_of(vals: np.ndarray) -> float:
        losses = vals[vals < 0]
        total = losses.sum()
        if total == 0 or len(losses) == 0:
            return np.nan
        k = min(top, len(losses))
        worst = np.partition(losses, k - 1)[:k].sum() if k < len(losses) else losses.sum()
        return float(worst / total)

    rng = np.random.default_rng(seed)
    draws = np.empty(b)
    for i in range(b):
        draws[i] = share_of(per[rng.integers(0, len(per), len(per))])
    alpha = (1 - level) / 2
    return {"share": share_of(per), "lo": float(np.nanquantile(draws, alpha)), "hi": float(np.nanquantile(draws, 1 - alpha)),
            "loss_total": float(per[per < 0].sum()), "wallets": int(len(per)), "top": int(top), "level": level}


def lorenz(values: np.ndarray, wallets: np.ndarray) -> pd.DataFrame:
    """Cumulative share of the maker's loss against the cumulative share of taker wallets (worst first)."""
    per = pd.DataFrame({"w": np.asarray(wallets), "v": np.asarray(values, dtype=float)}).dropna().groupby("w")["v"].sum()
    losses = per[per < 0].sort_values()
    total = losses.sum()
    out = pd.DataFrame({"wallet": losses.index, "loss": losses.to_numpy()})
    out["wallet_share"] = (np.arange(len(out)) + 1) / len(out)
    out["loss_share"] = out["loss"].cumsum() / total
    return out


def hedge_cost(abs_delta: np.ndarray, forward: np.ndarray, tau_s: float, funding_per_hour: np.ndarray,
               taker_fee: float = PERP_TAKER_FEE, half_spread_bp: float = 1.0) -> np.ndarray:
    """Cost of delta-hedging one contract in the perp: fee + half spread now, funding over the horizon."""
    notional = np.abs(np.asarray(abs_delta, dtype=float)) * np.asarray(forward, dtype=float)
    return notional * (taker_fee + half_spread_bp / 10_000.0) + notional * np.asarray(funding_per_hour, dtype=float) * (tau_s / 3600.0)


def analysis_frame(markouts: pd.DataFrame, funding: pd.DataFrame, horizon: str = HORIZON,
                   half_spread_bp: float = 1.0) -> pd.DataFrame:
    """Analysis columns for one horizon: markout units, half spread, adverse selection, net edge, FE key, cluster."""
    tau = HORIZON_SECONDS[horizon]
    f = markouts.copy()
    rates = (funding.assign(ccy=funding["instrument_name"].str.split("-").str[0])
                    .groupby("ccy")["funding_rate"].apply(lambda x: float(np.median(np.abs(x)))))
    f["funding_per_hour"] = f["currency"].map(rates).fillna(float(np.median(np.abs(funding["funding_rate"]))) if len(funding) else 0.0)
    side = f["maker_side"].to_numpy(float)
    f["hs"] = side * (f["mark_b_t"].to_numpy() - f["price"].to_numpy())
    f["y_usd"] = f[f"mo_usd_{horizon}"].to_numpy()
    f["as_usd"] = f["y_usd"] - f["hs"]
    f["y_dn"] = f[f"mo_dn_{horizon}"].to_numpy()
    f["y_vol"] = f[f"mo_vol_{horizon}"].to_numpy()
    f["hedge"] = hedge_cost(f["delta_t"].to_numpy(), f["fwd_t"].to_numpy(), tau, f["funding_per_hour"].to_numpy(),
                            half_spread_bp=half_spread_bp)
    f["net_edge"] = f["y_usd"] - f["fee_maker"].to_numpy() + f["rebate_maker"].to_numpy() - f["hedge"].to_numpy()
    day = pd.to_datetime(f["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    f["day"] = day
    f["fe_key"] = f["instrument_name"] + "|" + day
    f["cluster"] = f["taker_wallet"]
    f["horizon"] = horizon
    return f


def did(frame: pd.DataFrame, y_col: str, event_ms: int = HYPE_EVENT_MS, treated: str = "HYPE",
        placebos: int = 100, seed: int = SEED, b: int = B, window_days: int = 90) -> dict:
    """Difference in differences around the listing of the treated underlying, with placebo event dates."""
    day = 86_400_000
    win = frame[(frame["ts"] >= event_ms - window_days * day) & (frame["ts"] <= event_ms + window_days * day)]
    win = win[np.isfinite(win[y_col].to_numpy())]
    is_treated = (win["currency"] == treated).to_numpy(float)
    post = (win["ts"] >= event_ms).to_numpy(float)
    X = np.column_stack([is_treated * post, is_treated])
    out = wild_cluster_p(win[y_col].to_numpy(), X, win["day"].to_numpy(), win["cluster"].to_numpy(), 0, b=b, seed=seed)
    pre = frame[(frame["ts"] < event_ms) & (frame["ts"] >= event_ms - 2 * window_days * day)]
    pre = pre[np.isfinite(pre[y_col].to_numpy())]
    rng = np.random.default_rng(seed)
    placebo_t = []
    if len(pre) and placebos:
        lo, hi = int(pre["ts"].min()) + 10 * day, int(pre["ts"].max()) - 10 * day
        fakes = rng.integers(lo, hi, placebos) if hi > lo else np.array([], dtype="int64")
        for fake in fakes:
            sub = pre[(pre["ts"] >= fake - window_days * day) & (pre["ts"] <= fake + window_days * day)]
            if sub["currency"].nunique() < 2 or len(sub) < 100:
                continue
            tr = (sub["currency"] == treated).to_numpy(float)
            po = (sub["ts"] >= fake).to_numpy(float)
            res = wild_cluster_p(sub[y_col].to_numpy(), np.column_stack([tr * po, tr]), sub["day"].to_numpy(),
                                 sub["cluster"].to_numpy(), 0, b=99, seed=seed)
            if np.isfinite(res["t"]):
                placebo_t.append(abs(res["t"]))
    share = float(np.mean([pt >= abs(out["t"]) for pt in placebo_t])) if placebo_t else np.nan
    out.update({"event_ms": int(event_ms), "treated": treated, "y": y_col, "window_days": window_days,
                "placebos": len(placebo_t), "placebo_share_more_extreme": share})
    return out


def cell_table(frame: pd.DataFrame, y_col: str, min_fills: int = MIN_CELL_FILLS, b: int = B,
               seed: int = SEED, level: float = 0.90) -> pd.DataFrame:
    """Mean of ``y_col`` per (currency, delta bucket, tenor bucket) with a cluster bootstrap interval."""
    rows = []
    for (ccy, delta, tenor), g in frame.groupby(["currency", "delta_bucket", "tenor_bucket"], sort=True):
        vals = g[y_col].to_numpy(float)
        ok = np.isfinite(vals)
        if ok.sum() < min_fills:
            continue
        ci = cluster_mean_ci(vals[ok], g["cluster"].to_numpy()[ok], b=b, seed=seed, level=level)
        rows.append({"currency": ccy, "delta_bucket": delta, "tenor_bucket": tenor, "fills": int(ok.sum()),
                     "mean": ci["mean"], "lo": ci["lo"], "hi": ci["hi"], "p": ci["p"],
                     "positive": bool(ci["lo"] > 0), "negative": bool(ci["hi"] < 0)})
    return pd.DataFrame(rows)


def path_agreement(rows: pd.DataFrame, horizon: str = HORIZON) -> pd.DataFrame:
    """How well the two mark paths agree: correlation, sign agreement and median gap, overall and by curve age.

    Path (b) is the last on-chain SVI curve, path (a) the mark of the next fill of the same instrument.  A
    stale curve should show up as weaker agreement, so the table splits on the age of the curve at the fill.
    """
    b_col, a_col = f"mo_usd_{horizon}", f"mo_usd_a_{horizon}"
    frame = rows[[b_col, a_col, "lag_a_{}_s".format(horizon), "svi_age_s_t"]].copy()
    frame = frame[np.isfinite(frame[b_col]) & np.isfinite(frame[a_col])]
    lag_col = "lag_a_{}_s".format(horizon)
    groups = [("all", frame),
              ("lag_a <= 300 s", frame[frame[lag_col] <= 300]),
              ("lag_a <= 3600 s", frame[frame[lag_col] <= 3600])]
    if "svi_age_s_t" in frame:
        groups.append(("svi_age <= 60 s", frame[frame["svi_age_s_t"] <= 60]))
        groups.append(("svi_age > 60 s", frame[frame["svi_age_s_t"] > 60]))
    out = []
    for name, g in groups:
        if len(g) < 2:
            out.append({"group": name, "fills": int(len(g)), "correlation": np.nan, "sign_agreement": np.nan,
                        "median_gap": np.nan, "median_lag_a_s": np.nan})
            continue
        sign = np.mean(np.sign(g[b_col].to_numpy()) == np.sign(g[a_col].to_numpy()))
        out.append({"group": name, "fills": int(len(g)),
                    "correlation": float(np.corrcoef(g[b_col], g[a_col])[0, 1]),
                    "sign_agreement": float(sign),
                    "median_gap": float(np.median(g[a_col] - g[b_col])),
                    "median_lag_a_s": float(np.median(g["lag_a_{}_s".format(horizon)]))})
    return pd.DataFrame(out)


def run_all(root: Path, out_dir: Path, half_spread_bp: float = 1.0, b: int = B, seed: int = SEED) -> dict:
    """All four hypotheses plus net edge, class means and robustness; writes CSV/JSON to ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    markouts = pd.read_parquet(root / "derived" / "markouts.parquet")
    funding = pd.read_parquet(root / "ref" / "funding_history.parquet")
    frame = analysis_frame(markouts, funding, horizon=HORIZON, half_spread_bp=half_spread_bp)
    summary: Dict[str, dict] = {"horizon": HORIZON, "fills": int(len(frame)), "half_spread_bp": half_spread_bp,
                                "seed": seed, "b": b}

    # H1: concentration and the size/sweep coefficients
    h1_share = top_loss_share(frame["y_usd"].to_numpy(), frame["cluster"].to_numpy(), top=10, b=b, seed=seed)
    dummies = pd.get_dummies(frame["delta_bucket"], prefix="d", drop_first=True).to_numpy(float)
    X = np.column_stack([frame["size_above_p90"].to_numpy(float), frame["is_sweep"].to_numpy(float), dummies])
    h1_size = wild_cluster_p(frame["y_dn"].to_numpy(), X, frame["fe_key"].to_numpy(), frame["cluster"].to_numpy(), 0, b=b, seed=seed)
    h1_sweep = wild_cluster_p(frame["y_dn"].to_numpy(), X, frame["fe_key"].to_numpy(), frame["cluster"].to_numpy(), 1, b=b, seed=seed)
    summary["H1"] = {"top10_share": h1_share, "size_coefficient": h1_size, "sweep_coefficient": h1_sweep,
                     "rejected": bool(h1_share["hi"] < 0.5 or not (h1_size["beta"] < 0 and abs(h1_size["t"]) >= 1.96)
                                      or not (h1_sweep["beta"] < 0 and abs(h1_sweep["t"]) >= 1.96))}
    lorenz(frame["y_usd"].to_numpy(), frame["cluster"].to_numpy()).to_csv(out_dir / "h1_lorenz.csv", index=False)

    # H2: vault flow
    vault = frame[frame["taker_class"] == "vault"]
    h2_usd = cluster_mean_ci(vault["y_usd"].to_numpy(), vault["cluster"].to_numpy(), b=b, seed=seed)
    h2_set = cluster_mean_ci(vault["mo_set_vrp"].to_numpy(), vault["cluster"].to_numpy(), b=b, seed=seed)
    summary["H2"] = {"markout_30m": h2_usd, "settlement_vrp": h2_set, "rejected": bool(h2_usd["hi"] < 0)}

    # H3: HYPE before and after the Deribit listing
    h3 = did(frame, "y_vol", HYPE_EVENT_MS, placebos=100, seed=seed, b=b)
    summary["H3"] = {"did": h3, "rejected": bool(not (h3["beta"] > 0 and abs(h3["t"]) >= 1.96)
                                                 or (np.isfinite(h3["placebo_share_more_extreme"])
                                                     and h3["placebo_share_more_extreme"] > 0.05))}

    # H4: net edge per cell
    cells = cell_table(frame, "net_edge", b=b, seed=seed)
    cells.to_csv(out_dir / "h4_cells.csv", index=False)
    atm = cells[(cells["currency"].isin(["BTC", "ETH"])) & (cells["delta_bucket"] == "40-60") & (cells["tenor_bucket"] == "<=2d")]
    share_positive = float(cells["positive"].mean()) if len(cells) else np.nan
    summary["H4"] = {"cells": int(len(cells)), "share_positive": share_positive,
                     "atm_short": atm.to_dict("records"),
                     "rejected": bool(share_positive >= 0.5 or bool(atm["positive"].any()))}

    # descriptives and robustness (no hypothesis attached)
    classes = []
    for name, g in frame.groupby("taker_class"):
        ci = cluster_mean_ci(g["y_usd"].to_numpy(), g["cluster"].to_numpy(), b=b, seed=seed)
        ci.update({"class": name, "fills": int(len(g)), "mean_dn": float(np.nanmean(g["y_dn"])),
                   "mean_vol": float(np.nanmean(g["y_vol"])), "mean_ne": float(np.nanmean(g["net_edge"])),
                   "mean_hs": float(np.nanmean(g["hs"])), "mean_as": float(np.nanmean(g["as_usd"])),
                   "mean_hedge": float(np.nanmean(g["hedge"])), "mean_fee": float(np.nanmean(g["fee_maker"])),
                   "mean_rebate": float(np.nanmean(g["rebate_maker"])), "mean_notional": float(np.nanmean(g["notional"])),
                   "share_negative": float(np.nanmean(g["y_usd"] < 0))})
        classes.append(ci)
    pd.DataFrame(classes).to_csv(out_dir / "class_means.csv", index=False)
    horizons = []
    for h in HORIZON_SECONDS:
        col = f"mo_usd_{h}"
        if col not in markouts:
            continue
        sub = analysis_frame(markouts, funding, horizon=h, half_spread_bp=half_spread_bp)
        ci = cluster_mean_ci(sub["y_usd"].to_numpy(), sub["cluster"].to_numpy(), b=b, seed=seed)
        ci.update({"horizon": h, "mean_dn": float(np.nanmean(sub["y_dn"])), "mean_vol": float(np.nanmean(sub["y_vol"])),
                   "mean_path_a": float(np.nanmean(sub[f"mo_usd_a_{h}"])) if f"mo_usd_a_{h}" in sub else np.nan})
        horizons.append(ci)
    pd.DataFrame(horizons).to_csv(out_dir / "horizon_means.csv", index=False)
    sens = []
    for bp in PERP_HALF_SPREAD_BP:
        f2 = analysis_frame(markouts, funding, horizon=HORIZON, half_spread_bp=bp)
        cells2 = cell_table(f2, "net_edge", b=b, seed=seed)
        sens.append({"half_spread_bp": bp, "cells": int(len(cells2)),
                     "share_positive": float(cells2["positive"].mean()) if len(cells2) else np.nan})
    pd.DataFrame(sens).to_csv(out_dir / "h4_sensitivity.csv", index=False)
    paths = path_agreement(markouts, horizon=HORIZON)
    paths.to_csv(out_dir / "path_agreement.csv", index=False)
    summary["path_agreement"] = paths.to_dict("records")
    summary["missing_vol_unit"] = int((~np.isfinite(frame["y_vol"].to_numpy())).sum())
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    return summary
