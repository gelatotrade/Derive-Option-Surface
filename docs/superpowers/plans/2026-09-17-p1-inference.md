# Paper 1, Plan 3: Inference H1 to H4, Net Edge, Robustness

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test the four pre-registered hypotheses on `markouts.parquet` (wild cluster bootstrap, placebos, difference in differences), compute the net edge per cell, show the robustness across the mark paths, and write all numbers into a numbers sheet that is the only source of numbers for the manuscript.

**Architecture:** One module `derive_surface/inference_p1.py` with tested building blocks (analysis frame, hedge costs, fixed-effects OLS, wild cluster bootstrap with per-cluster sufficient statistics, cluster bootstrap for means and shares, DiD with placebos, cell evaluation, Lorenz curve) and an orchestration that writes to `results/p1/`; CLI `p1 inference`; a script that generates `docs/paper1/NUMBERS.md` from these results.

**Tech Stack:** Python 3.9.6, numpy, pandas; pytest. No new dependencies (no statsmodels, no linearmodels).

**Spec:** `docs/superpowers/specs/2026-09-17-adverse-selection-design.md`; **Pre-registration:** `docs/paper1/PRAEREGISTRIERUNG.md` with addendum 1 and addendum 2, which is added here.

## Global Constraints

- The constraints from plans 1 and 2 continue to apply (Python 3.9, no new dependencies, tests offline, local commits with trailer).
- Every estimate clusters on `taker_wallet`; bootstrap repetitions B = 9 999, seed 20260917, p = (1 + #)/(B + 1), small-sample correction G/(G − 1).
- Fixed effects: instrument × day (one interacted group), implemented as a within transformation.
- Primary horizon 30 min, primary mark path (b) by push time. Every table states horizon, path and unit.
- No number in the manuscript that is not in the numbers sheet; every number in the numbers sheet comes from `results/p1/*.csv`/`*.json`.
- Result files under `results/p1/` are committed (small), `data/p1/` stays untracked.

## Files

| File | Responsibility |
|---|---|
| `docs/paper1/PRAEREGISTRIERUNG.md` | Addendum 2 (H3 date, net-edge decomposition, H1 metric, exclusion without fill IV) |
| `derive_surface/inference_p1.py` | Analysis frame, estimators, bootstraps, DiD, cells, Lorenz, orchestration |
| `derive_surface/p1cli.py` | Subcommand `inference` |
| `scripts/p1_numbers.py` | writes `docs/paper1/NUMBERS.md` from `results/p1/` |
| `tests/test_p1_inference.py` | Offline tests with synthetic panel data |

---

### Task 0: Addendum 2 to the pre-registration

**Files:** Modify `docs/paper1/PRAEREGISTRIERUNG.md`

- [ ] **Step 1: Append the addendum**

```markdown

## Addendum 2 (2026-09-18, before the first inference)

1. **Event date for H3:** HYPE_USDC **options** launched on Deribit on **2026-06-23 09:00 UTC** (official announcement "HYPE Derivatives Launching On Deribit", published 2026-06-16: perp 2026-06-16 09:00 UTC, options and dated futures 2026-06-23 09:00 UTC). The date noted earlier, 2026-06-16, was the perp launch. Deribit's delivery price history covers only 100 days and is not suitable for dating the event.
2. **Net edge, decomposition without double counting:** The half spread is part of the markout. HS = s·(M(t) − P) (markout at horizon 0), adverse selection AS_τ = s·(M(t+τ) − M(t)) and MO_τ = HS + AS_τ. The net edge is therefore NE_τ = MO_τ − maker fee + maker rebate − hedge costs, with the **observed** fees and rebates of the maker row from the tape. Hedge costs = |Δ(t)|·F(t)·(perp taker fee 0.03 % + assumed perp half spread) + |Δ(t)|·F(t)·funding rate per hour·(τ/3600 s); the perp half spread is set at 1 bp and reported with 0 bp and 3 bp as a sensitivity, and the funding rate is the median of the absolute hourly value over the last 30 days per underlying.
3. **H1 metric:** For each taker wallet w, S_w = Σ MO_30min (USDC, path b). L = Σ_{w: S_w < 0} S_w is the maker's aggregate loss. The top-10 share is the sum of the ten smallest (most negative) S_w divided by L. The 90 % interval comes from a cluster bootstrap over wallets (B = 9 999, seed 20260917).
4. **Intervals for means:** For means (H2, cells in H4), the reported interval is the percentile interval of a cluster bootstrap over taker wallets; in addition, the p-value of the wild cluster bootstrap against zero is reported. For regression coefficients (H1, H3), the wild cluster bootstrap applies (restricted residuals, Rademacher).
5. **Exclusion without fill IV:** Fills whose price lies outside the Black-76 arbitrage bounds, and for which therefore no fill IV exists (pilot: 10 745 of 603 940), do not enter the tests in vol points; in USDC and delta-neutral they remain included. The number is reported for each test.
6. **Class "liquidation" is empty:** Liquidations are settled outside the trade tape (27 694 auctions, no match on an option fill). The class analysis runs over the six remaining classes.
```

- [ ] **Step 2: Commit**

```bash
git add docs/paper1/PRAEREGISTRIERUNG.md docs/superpowers/plans/2026-09-17-p1-inference.md
git commit -m "paper1: pre-registration addendum 2 (H3 event date, net-edge decomposition, H1 metric); plan 3

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 1: `inference_p1.py`, estimators and bootstraps

**Files:**
- Create: `derive_surface/inference_p1.py`
- Test: `tests/test_p1_inference.py`

**Interfaces:**
- Consumes: `markouts.parquet` (plan 2), `data/p1/ref/funding_history.parquet`, `data/p1/ref/instrument_fees_*.parquet`.
- Produces:
  - `HORIZON = "30m"`, `B = 9999`, `SEED = 20260917`, `HYPE_EVENT_MS = 1_782_205_200_000` (2026-06-23 09:00 UTC), `MIN_CELL_FILLS = 200`, `PERP_HALF_SPREAD_BP = (0.0, 1.0, 3.0)`
  - `hedge_cost(abs_delta, forward, tau_s, funding_per_hour, taker_fee=3e-4, half_spread_bp=1.0) -> np.ndarray`
  - `analysis_frame(markouts, funding, horizon=HORIZON, half_spread_bp=1.0) -> DataFrame` (columns `y_usd, y_dn, y_vol, hs, as_usd, net_edge, fe_key, cluster, …`)
  - `within(values, groups) -> np.ndarray` (subtract the group means)
  - `ols_fe(y, X, groups) -> (beta, resid, XtX_inv)`
  - `wild_cluster_p(y, X, groups, clusters, test_col, b=B, seed=SEED) -> dict` with `beta, se, t, p, n, clusters`
  - `cluster_mean_ci(values, clusters, b=B, seed=SEED, level=0.95) -> dict` with `mean, lo, hi, p, n, clusters`
  - `top_loss_share(values, wallets, top=10, b=B, seed=SEED, level=0.90) -> dict` with `share, lo, hi, loss_total, wallets`
  - `lorenz(values, wallets) -> DataFrame` (`wallet_share, loss_share`)
  - `did(frame, y_col, event_ms, treated="HYPE", placebos=100, seed=SEED) -> dict`
  - `cell_table(frame, y_col, min_fills=MIN_CELL_FILLS) -> DataFrame`
  - `run_all(root: Path, out_dir: Path, half_spread_bp=1.0) -> dict`

- [ ] **Step 1: Write the failing tests**

`tests/test_p1_inference.py`:

```python
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import inference_p1 as inf


def panel(n_cluster=40, per=25, effect=0.0, seed=0):
    """Panel with cluster-correlated noise and one binary regressor."""
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_cluster):
        shock = rng.normal(0, 1.0)
        for i in range(per):
            x = float((c + i) % 2)
            g = f"inst{i % 5}-day{i % 7}"
            rows.append({"cluster": f"w{c}", "x": x, "fe_key": g,
                         "y": effect * x + shock + rng.normal(0, 0.5)})
    return pd.DataFrame(rows)


def test_within_removes_group_means():
    df = pd.DataFrame({"g": ["a", "a", "b"], "v": [1.0, 3.0, 7.0]})
    got = inf.within(df["v"].to_numpy(), df["g"].to_numpy())
    assert got == pytest.approx([-1.0, 1.0, 0.0])


def test_ols_fe_recovers_beta_with_group_offsets():
    rng = np.random.default_rng(1)
    g = np.repeat(["a", "b", "c"], 200)
    x = rng.normal(size=600)
    offsets = {"a": 5.0, "b": -3.0, "c": 0.0}
    y = 2.5 * x + np.array([offsets[k] for k in g]) + rng.normal(0, 0.01, 600)
    beta, resid, _ = inf.ols_fe(y, x.reshape(-1, 1), g)
    assert beta[0] == pytest.approx(2.5, abs=0.01) and abs(resid).max() < 0.1


def test_wild_cluster_p_is_large_without_effect_and_small_with_one():
    zero = panel(effect=0.0, seed=2)
    out0 = inf.wild_cluster_p(zero["y"].to_numpy(), zero[["x"]].to_numpy(), zero["fe_key"].to_numpy(),
                              zero["cluster"].to_numpy(), 0, b=199, seed=inf.SEED)
    assert out0["p"] > 0.2 and out0["clusters"] == 40 and out0["n"] == 1000
    strong = panel(effect=2.0, seed=2)
    out1 = inf.wild_cluster_p(strong["y"].to_numpy(), strong[["x"]].to_numpy(), strong["fe_key"].to_numpy(),
                              strong["cluster"].to_numpy(), 0, b=199, seed=inf.SEED)
    assert out1["p"] < 0.05 and out1["beta"] == pytest.approx(2.0, abs=0.1) and abs(out1["t"]) > 2


def test_wild_cluster_p_is_deterministic():
    df = panel(effect=1.0, seed=3)
    args = (df["y"].to_numpy(), df[["x"]].to_numpy(), df["fe_key"].to_numpy(), df["cluster"].to_numpy(), 0)
    a = inf.wild_cluster_p(*args, b=99, seed=7)
    b = inf.wild_cluster_p(*args, b=99, seed=7)
    assert a == b


def test_cluster_mean_ci_brackets_the_mean_and_flags_a_shift():
    rng = np.random.default_rng(4)
    clusters = np.repeat([f"w{i}" for i in range(30)], 20)
    values = rng.normal(0, 1, 600)
    out = inf.cluster_mean_ci(values, clusters, b=299, seed=inf.SEED)
    assert out["lo"] < out["mean"] < out["hi"] and out["lo"] < 0 < out["hi"] and out["p"] > 0.1
    shifted = inf.cluster_mean_ci(values - 3.0, clusters, b=299, seed=inf.SEED)
    assert shifted["hi"] < 0 and shifted["p"] < 0.05


def test_top_loss_share_and_lorenz():
    wallets = np.array(["a", "b", "c", "d", "e", "f"])
    values = np.array([-40.0, -30.0, -20.0, -5.0, -5.0, 100.0])  # f is profitable for the maker
    out = inf.top_loss_share(values, wallets, top=2, b=199, seed=inf.SEED)
    assert out["loss_total"] == pytest.approx(-100.0) and out["share"] == pytest.approx(0.7)
    assert 0.0 <= out["lo"] <= out["share"] <= out["hi"] <= 1.0 and out["wallets"] == 6
    curve = inf.lorenz(values, wallets)
    assert curve["loss_share"].iloc[-1] == pytest.approx(1.0) and curve["wallet_share"].iloc[-1] == pytest.approx(1.0)
    assert curve["loss_share"].iloc[0] == pytest.approx(0.4)  # the worst wallet alone


def test_did_finds_a_treatment_effect_and_ranks_placebos():
    rng = np.random.default_rng(5)
    rows = []
    event = 1_000_000_000_000
    day = 86_400_000
    for d in range(-40, 40):
        for ccy in ("BTC", "ETH", "HYPE"):
            for k in range(6):
                post = d >= 0
                treated = ccy == "HYPE"
                rows.append({"ts": event + d * day + k, "currency": ccy, "taker_wallet": f"w{k}",
                             "instrument_name": f"{ccy}-{k}", "day": d,
                             "y_vol": (0.8 if (post and treated) else 0.0) + rng.normal(0, 0.2)})
    frame = pd.DataFrame(rows)
    frame["fe_key"] = frame["instrument_name"] + "|" + frame["day"].astype(str)
    frame["cluster"] = frame["taker_wallet"]
    out = inf.did(frame, "y_vol", event, placebos=20, seed=inf.SEED, b=199)
    assert out["beta"] == pytest.approx(0.8, abs=0.1) and out["p"] < 0.05
    assert out["placebo_share_more_extreme"] <= 0.05 and out["placebos"] == 20


def test_cell_table_respects_the_minimum_and_marks_positive_cells():
    rng = np.random.default_rng(6)
    rows = []
    for cell, (mean, n) in {("BTC", "40-60", "<=2d"): (-1.0, 400), ("BTC", "25-40", "7-30d"): (2.0, 400),
                            ("ETH", "10-25", ">90d"): (5.0, 50)}.items():
        for i in range(n):
            rows.append({"currency": cell[0], "delta_bucket": cell[1], "tenor_bucket": cell[2],
                         "cluster": f"w{i % 20}", "net_edge": mean + rng.normal(0, 0.5)})
    table = inf.cell_table(pd.DataFrame(rows), "net_edge", min_fills=200, b=199, seed=inf.SEED)
    assert len(table) == 2  # the 50-fill cell is dropped
    pos = table.set_index(["currency", "delta_bucket", "tenor_bucket"])
    assert not pos.loc[("BTC", "40-60", "<=2d"), "positive"]
    assert pos.loc[("BTC", "25-40", "7-30d"), "positive"]


def test_hedge_cost_scales_with_delta_and_horizon():
    base = inf.hedge_cost(np.array([0.5]), np.array([100_000.0]), 1_800, np.array([1e-5]), half_spread_bp=1.0)
    twice = inf.hedge_cost(np.array([1.0]), np.array([100_000.0]), 1_800, np.array([1e-5]), half_spread_bp=1.0)
    longer = inf.hedge_cost(np.array([0.5]), np.array([100_000.0]), 86_400, np.array([1e-5]), half_spread_bp=1.0)
    free = inf.hedge_cost(np.array([0.5]), np.array([100_000.0]), 1_800, np.array([0.0]), half_spread_bp=0.0)
    assert twice[0] == pytest.approx(2 * base[0]) and longer[0] > base[0]
    assert free[0] == pytest.approx(0.5 * 100_000 * 3e-4)


def test_analysis_frame_decomposes_the_markout():
    rows = pd.DataFrame([{
        "trade_id": "a", "ts": 1_700_000_000_000, "currency": "BTC", "instrument_name": "BTC-1-2-C",
        "taker_wallet": "0xt", "maker_wallet": "0xm", "taker_class": "other", "delta_bucket": "40-60",
        "tenor_bucket": "7-30d", "is_sweep": False, "size_above_p90": False, "price": 100.0, "mark_b_t": 105.0,
        "mark_b_30m": 110.0, "iv_fill": 0.5, "iv_b_30m": 0.55, "fwd_t": 50_000.0, "fwd_b_30m": 50_500.0,
        "delta_t": 0.5, "maker_side": 1, "fee_maker": 0.4, "rebate_maker": 0.1, "mo_usd_30m": 10.0,
        "mo_dn_30m": 9.0, "mo_vol_30m": 5.0, "mo_set": 3.0, "mo_set_vrp": 1.0, "amount": 1.0,
    }])
    funding = pd.DataFrame({"instrument_name": ["BTC-PERP"], "timestamp": [1], "funding_rate": [1e-5]})
    out = inf.analysis_frame(rows, funding, horizon="30m", half_spread_bp=1.0)
    r = out.iloc[0]
    assert r.hs == pytest.approx(5.0) and r.as_usd == pytest.approx(5.0) and r.y_usd == pytest.approx(10.0)
    assert r.net_edge == pytest.approx(10.0 - 0.4 + 0.1 - r.hedge)
    assert r.fe_key == "BTC-1-2-C|2023-11-14" and r.cluster == "0xt"
```

- [ ] **Step 2: Run the tests, confirm the failure**

Run: `python3 -m pytest -q tests/test_p1_inference.py`
Expected: FAIL with `ImportError: cannot import name 'inference_p1'`

- [ ] **Step 3: Implementation**

`derive_surface/inference_p1.py`:

```python
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
    while drawn < b:
        size = min(chunk, b - drawn)
        w = rng.choice(np.array([-1.0, 1.0]), size=(size, n_cluster))
        beta = w @ sums / n                                   # under H0 the residuals are the values themselves
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
    t, p, se = wild_cluster_mean_p(values, clusters, b=min(b, 1999), seed=seed)
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
        ci = cluster_mean_ci(g["y_usd"].to_numpy(), g["cluster"].to_numpy(), b=min(b, 1999), seed=seed)
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
        ci = cluster_mean_ci(sub["y_usd"].to_numpy(), sub["cluster"].to_numpy(), b=min(b, 1999), seed=seed)
        ci.update({"horizon": h, "mean_dn": float(np.nanmean(sub["y_dn"])), "mean_vol": float(np.nanmean(sub["y_vol"])),
                   "mean_path_a": float(np.nanmean(sub[f"mo_usd_a_{h}"])) if f"mo_usd_a_{h}" in sub else np.nan})
        horizons.append(ci)
    pd.DataFrame(horizons).to_csv(out_dir / "horizon_means.csv", index=False)
    sens = []
    for bp in PERP_HALF_SPREAD_BP:
        f2 = analysis_frame(markouts, funding, horizon=HORIZON, half_spread_bp=bp)
        cells2 = cell_table(f2, "net_edge", b=min(b, 1999), seed=seed)
        sens.append({"half_spread_bp": bp, "cells": int(len(cells2)),
                     "share_positive": float(cells2["positive"].mean()) if len(cells2) else np.nan})
    pd.DataFrame(sens).to_csv(out_dir / "h4_sensitivity.csv", index=False)
    summary["missing_vol_unit"] = int((~np.isfinite(frame["y_vol"].to_numpy())).sum())
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    return summary
```

- [ ] **Step 4: Run the tests**

Run: `python3 -m pytest -q tests/test_p1_inference.py`
Expected: `9 passed`

- [ ] **Step 5: Full suite and commit**

```bash
python3 -m pytest -q
git add derive_surface/inference_p1.py tests/test_p1_inference.py
git commit -m "paper1: inference (wild cluster bootstrap, DiD with placebos, net edge per cell)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: CLI `p1 inference` and run

**Files:** Modify `derive_surface/p1cli.py`; Test `tests/test_p1_cli.py`

- [ ] **Step 1: Add the test**

```python
def test_inference_command_is_listed(capsys):
    with pytest.raises(SystemExit):
        main(["p1", "--help"])
    assert "inference" in capsys.readouterr().out
```

- [ ] **Step 2: Add the subcommand**

```python
    s = sub.add_parser("inference", help="pre-registered hypotheses, net edge, robustness")
    s.add_argument("--results", type=Path, default=Path("results/p1"))
    s.add_argument("--half-spread-bp", type=float, default=1.0)
    s.add_argument("--bootstrap", type=int, default=9999)
```

```python
    elif a.cmd == "inference":
        from .inference_p1 import run_all

        summary = run_all(a.root, a.results, half_spread_bp=a.half_spread_bp, b=a.bootstrap)
        print(json.dumps(summary, indent=1, default=str))
```

- [ ] **Step 3: Tests:** `python3 -m pytest -q`

- [ ] **Step 4: Run on the pilot data**

Run: `python3 -m derive_surface p1 inference`
Expected: `results/p1/summary.json`, `h1_lorenz.csv`, `h4_cells.csv`, `h4_sensitivity.csv`, `class_means.csv`, `horizon_means.csv`. Runtime: minutes.

- [ ] **Step 5: Commit**

```bash
git add derive_surface/p1cli.py tests/test_p1_cli.py results/p1
git commit -m "paper1: p1 inference command and pilot results

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Numbers sheet

**Files:** Create `scripts/p1_numbers.py`; Output `docs/paper1/NUMBERS.md`

**Interfaces:** reads `results/p1/summary.json` and the CSVs, writes the numbers sheet with one section per hypothesis (statement, rejection rule, numbers, verdict), a class table and a horizon table, the cell overview and the sensitivity.

- [ ] **Step 1: Write the script**

```python
"""Write docs/paper1/NUMBERS.md from results/p1 (single source of numbers for the manuscript).

Run from the repository root after `p1 inference`:
    python3 scripts/p1_numbers.py
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

RESULTS = Path("results/p1")
OUT = Path("docs/paper1/NUMBERS.md")


def de(x, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "–"
    return f"{x:,.{digits}f}".replace(",", " ").replace(".", ",")


def di(x) -> str:
    """Integer with a thin space as thousands separator."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "–"
    return f"{int(x):,}".replace(",", " ")


def verdict(rejected: bool) -> str:
    return "**rejected**" if rejected else "not rejected"


def main() -> None:
    s = json.loads((RESULTS / "summary.json").read_text())
    cells = pd.read_csv(RESULTS / "h4_cells.csv")
    classes = pd.read_csv(RESULTS / "class_means.csv")
    horizons = pd.read_csv(RESULTS / "horizon_means.csv")
    sens = pd.read_csv(RESULTS / "h4_sensitivity.csv")
    h1, h2, h3, h4 = s["H1"], s["H2"], s["H3"], s["H4"]
    lines = [
        "# Numbers for paper 1", "",
        f"Generated {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M UTC} from `results/p1` with `scripts/p1_numbers.py`. "
        f"Pilot data up to 2026-09-17 12:00 UTC. Primary horizon {s['horizon']}, mark path (b) by push time, "
        f"clusters by taker wallet, B = {s['b']}, seed {s['seed']}, perp half spread {de(s['half_spread_bp'], 1)} bp. "
        f"{di(s['fills'])} fills; without a fill IV (only the vol unit is affected): {di(s['missing_vol_unit'])}.", "",
        "## H1 Concentration of toxicity", "",
        f"- Top-10 share of the aggregate maker loss: **{de(100 * h1['top10_share']['share'], 1)} %** "
        f"(90 % interval {de(100 * h1['top10_share']['lo'], 1)} to {de(100 * h1['top10_share']['hi'], 1)} %), "
        f"total loss {de(h1['top10_share']['loss_total'], 0)} USDC over {di(h1['top10_share']['wallets'])} wallets.",
        f"- Size above the 90th percentile: coefficient {de(h1['size_coefficient']['beta'], 3)} USDC "
        f"(t {de(h1['size_coefficient']['t'], 2)}, p {de(h1['size_coefficient']['p'], 4)}).",
        f"- Sweep: coefficient {de(h1['sweep_coefficient']['beta'], 3)} USDC "
        f"(t {de(h1['sweep_coefficient']['t'], 2)}, p {de(h1['sweep_coefficient']['p'], 4)}).",
        f"- Verdict: {verdict(h1['rejected'])}.", "",
        "## H2 Vault flow is uninformed", "",
        f"- 30 min markout of the vault fills: {de(h2['markout_30m']['mean'], 3)} USDC "
        f"(95 % interval {de(h2['markout_30m']['lo'], 3)} to {de(h2['markout_30m']['hi'], 3)}, p {de(h2['markout_30m']['p'], 4)}, "
        f"{di(h2['markout_30m']['n'])} fills, {h2['markout_30m']['clusters']} wallets).",
        f"- VRP-adjusted settlement markout: {de(h2['settlement_vrp']['mean'], 3)} USDC "
        f"(95 % interval {de(h2['settlement_vrp']['lo'], 3)} to {de(h2['settlement_vrp']['hi'], 3)}).",
        f"- Verdict: {verdict(h2['rejected'])}.", "",
        "## H3 HYPE before and after the Deribit listing", "",
        f"- Event 2026-06-23 09:00 UTC, window ±{h3['did']['window_days']} days, outcome vol markout.",
        f"- DiD coefficient {de(h3['did']['beta'], 3)} vol points (t {de(h3['did']['t'], 2)}, p {de(h3['did']['p'], 4)}, "
        f"{di(h3['did']['n'])} fills, {h3['did']['clusters']} wallets).",
        f"- Placebo dates: {h3['did']['placebos']}, of which more extreme: {de(100 * (h3['did']['placebo_share_more_extreme'] or 0), 1)} %.",
        f"- Verdict: {verdict(h3['rejected'])}.", "",
        "## H4 Net edge per cell", "",
        f"- Occupied cells (≥ 200 fills): {h4['cells']}; of these with a positive 90 % interval: "
        f"**{de(100 * h4['share_positive'], 1)} %**.",
    ]
    for row in h4["atm_short"]:
        lines.append(f"- Short-dated ATM {row['currency']} 40-60 Δ, ≤ 2 d: {de(row['mean'], 3)} USDC "
                     f"(90 % interval {de(row['lo'], 3)} to {de(row['hi'], 3)}, {di(row['fills'])} fills)")
    lines += [f"- Verdict: {verdict(h4['rejected'])}.", "",
              "### Sensitivity to the perp half spread", "",
              "| Half spread (bp) | Cells | Share positive |", "|---|---|---|"]
    for r in sens.itertuples():
        lines.append(f"| {de(r.half_spread_bp, 1)} | {r.cells} | {de(100 * r.share_positive, 1)} % |")
    lines += ["", "## Counterparty classes (30 min, path b)", "",
              "| Class | Fills | Half spread | Adverse selection | Markout USDC | 95 % interval | Fee | Rebate | Hedge | Net edge | Share negative |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in classes.sort_values("mean").iterrows():
        lines.append(f"| {r['class']} | {di(r['fills'])} | {de(r['mean_hs'])} | {de(r['mean_as'])} | {de(r['mean'])} | "
                     f"{de(r['lo'])} to {de(r['hi'])} | {de(r['mean_fee'])} | {de(r['mean_rebate'])} | "
                     f"{de(r['mean_hedge'])} | {de(r['mean_ne'])} | {de(100 * r['share_negative'], 1)} % |")
    lines += ["", "## Horizons (path b, means)", "",
              "| Horizon | Fills | USDC | delta-neutral | Vol points | Path (a) USDC |", "|---|---|---|---|---|---|"]
    for r in horizons.itertuples():
        lines.append(f"| {r.horizon} | {di(r.n)} | {de(r.mean, 3)} | {de(r.mean_dn, 3)} | {de(r.mean_vol, 3)} | "
                     f"{de(r.mean_path_a, 3)} |")
    lines += ["", "## Cells with the largest and smallest net edge", "",
              "| Underlying | Delta | Tenor | Fills | Net edge | 90 % interval |", "|---|---|---|---|---|---|"]
    ranked = cells.sort_values("mean")
    for r in pd.concat([ranked.head(5), ranked.tail(5)]).itertuples():
        lines.append(f"| {r.currency} | {r.delta_bucket} | {r.tenor_bucket} | {di(r.fills)} | {de(r.mean, 3)} | "
                     f"{de(r.lo, 3)} to {de(r.hi, 3)} |")
    lines += ["", "## Limitations of these numbers", "",
              f"- Pilot state: sample up to 2026-09-17 12:00 UTC. The numbers of the manuscript only arise with the "
              f"cut-off 2026-09-30 08:00 UTC.",
              f"- H2 rests on {h2['markout_30m']['clusters']} vault wallets; with so few clusters the "
              f"wild cluster bootstrap is unreliable, so the result is an indication, not proof.",
              f"- Path (b) is a mark delayed by minutes (onchain push per expiry every 60 s at the median, forward of the "
              f"curve instead of the live forward). The horizons 1 min and 5 min are affected most; path (a) is shown "
              f"next to it in the horizon table.",
              f"- The vol unit is missing for {di(s['missing_vol_unit'])} fills without fill IV (price outside the "
              f"arbitrage bounds).",
              "- The class “liquidation” is empty: liquidations run outside the trade tape."]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run and commit**

```bash
python3 scripts/p1_numbers.py
git add scripts/p1_numbers.py docs/paper1/NUMBERS.md
git commit -m "paper1: figure sheet generated from results/p1

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Notes

- The pilot run serves the pipeline; the numbers reported in the paper only arise after the final data state (cut-off 2026-09-30 08:00 UTC, data up to 2026-10-01 09:00 UTC).
- Plan 4 (figures T1, T2, 1 to 5, A) and plan 5 (manuscript, CAS) build on the numbers sheet.
- Open and not pre-registered: path (b') with the live spot from the onchain `SpotPriceUpdated` or `ForwardDataUpdated` events. It would sharpen the USDC markout at 1 and 5 minutes and costs another chain fetch on the order of the vol feed (around 40 million events, two hours, 1.6 GB).
