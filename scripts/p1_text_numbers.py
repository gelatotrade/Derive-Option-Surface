#!/usr/bin/env python3
"""Write ``results/p1/text_numbers.json``: the numbers the Paper 1 manuscript prints that no other file under
``results/p1`` holds (counts of the sample, quantities the figures draw, sensitivities named in the text).

The manuscript binds every number to one source with a ``% src`` declaration, and
``scripts/p2_number_check.py --paper 1`` checks each binding, so a run on new data names every sentence whose number
has changed.  Each quantity is computed the way its figure computes it (``figures_p1``, ``figdata``): the same
analysis frame, the same cells, the same draws and seeds; intervals quoted in the text that no figure draws use the
registered B = 9 999 of ``inference_p1``.

Run from the repository root after ``python3 -m derive_surface p1 inference``:

    python3 scripts/p1_text_numbers.py [--root data/p1] [--results results/p1]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from derive_surface import figdata, figures_p1                                   # noqa: E402
from derive_surface.inference_p1 import (B, NEAR_LAG_S, SEED, analysis_frame,     # noqa: E402
                                         cell_table, cluster_mean_ci, load_salt, wallet_pseudonym)

ROOT = Path("data/p1")
RESULTS = Path("results/p1")
OUT_NAME = "text_numbers.json"
HIGH_DELTA = ("60-75", "75-90", "90-100")          # rows with an absolute delta of 60 per cent or more
SHORT_TENORS = ("<=2d", "2-7d")                     # options of up to seven days
LOW_DELTA = ("00-10", "10-25", "25-40", "40-60")    # absolute delta below 60 per cent
BELOW_75 = LOW_DELTA + ("60-75",)                   # every delta row below 75 per cent
ATM = "40-60"
PROFESSIONAL_SHARE_CLASSES = ("dominant_maker", "mm_programme")
TRIM = 0.05                                         # Figure 1: trimmed from each tail
INTERVAL_LEVEL = 0.95                               # interval of the mean net edge in section 3
P_ALTERNATIVE = 0.10                                # section 5.5: cells counted by a positive mean and p below this
TENOR_KEY = {"<=2d": "le2d", "2-7d": "2to7d", "7-30d": "7to30d", "30-90d": "30to90d", ">90d": "gt90d"}


def _month(ms) -> str:
    return pd.Timestamp(int(ms), unit="ms", tz="UTC").strftime("%Y-%m-%d")


def sample_numbers(frame: pd.DataFrame) -> Dict[str, object]:
    """Counts of the sample (section 2) and the calendar of the panel (Figure 6)."""
    out: Dict[str, object] = {
        "fills": int(len(frame)),
        "instruments": int(frame["instrument_name"].nunique()),
        "taker_wallets": int(frame["taker_wallet"].nunique()),
        "maker_wallets": int(frame["maker_wallet"].nunique()),
        "first_fill_day": _month(frame["ts"].min()),
        "last_fill_day": _month(frame["ts"].max()),
        "rfq_share_pct": float(100.0 * frame["is_rfq"].astype(bool).mean()),
        "curve_age_median_s": float(np.nanmedian(frame["svi_age_s_t"].to_numpy(float))),
        "curve_age_p90_s": float(np.nanpercentile(frame["svi_age_s_t"].to_numpy(float), 90)),
    }
    for ccy in ("BTC", "ETH", "HYPE"):
        out[f"fills_{ccy}"] = int((frame["currency"] == ccy).sum())
    month = pd.to_datetime(frame["ts"], unit="ms", utc=True).dt.strftime("%Y-%m")
    out["months"] = int(month.nunique())
    out["hype_first_day"] = _month(frame.loc[frame["currency"] == "HYPE", "ts"].min())
    mm = frame.loc[frame["taker_class"] == "mm_programme", "ts"]
    out["mm_programme_first_day"] = _month(mm.min()) if len(mm) else None
    return out


def markout_numbers(frame: pd.DataFrame, b: int, seed: int) -> Dict[str, object]:
    """The decomposition of the net edge (section 3, Figure 2) and the readings of the average (Figure 1)."""
    y = frame["y_usd"].to_numpy(float)
    ok = np.isfinite(y)
    out: Dict[str, object] = {
        "mean_markout": float(np.mean(y[ok])),
        "median_markout": float(np.median(y[ok])),
        "mean_half_spread": float(np.nanmean(frame["hs"])),
        "mean_adverse_selection": float(np.nanmean(frame["as_usd"])),
        "mean_fee": float(np.nanmean(frame["fee_pc"])),
        "mean_rebate": float(np.nanmean(frame["rebate_pc"])),
        "mean_hedge": float(np.nanmean(frame["hedge"])),
        "mean_net_edge": float(np.nanmean(frame["net_edge"])),
    }
    out["mean_over_median"] = out["mean_markout"] / out["median_markout"]
    # exploratory: the same net edge on the delta-neutral markout (the registered one charges the hedge to the USDC
    # markout, which still carries the move of the underlying)
    out["mean_net_edge_delta_neutral"] = float(np.nanmean(frame["y_dn"] - frame["fee_pc"] + frame["rebate_pc"]
                                                          - frame["hedge"]))
    out["mean_adverse_selection_delta_neutral"] = float(np.nanmean(frame["y_dn"] - frame["hs"]))
    split = figures_p1.class_vol_split(frame)
    for name, r in split.iterrows():
        out[f"class_hs_vol_median_{name}"] = float(r["hs_vol"])
        out[f"class_as_vol_median_{name}"] = float(r["as_vol"])
    ne = frame["net_edge"].to_numpy(float)
    fine = np.isfinite(ne)
    ci = cluster_mean_ci(ne[fine], frame["cluster"].to_numpy()[fine], b=b, seed=seed, level=INTERVAL_LEVEL)
    out["net_edge_lo95"], out["net_edge_hi95"] = float(ci["lo"]), float(ci["hi"])
    out["net_edge_interval_pct"] = 100.0 * INTERVAL_LEVEL

    # Figure 1: contract weighted, trimmed, aggregate dollar amount per underlying, share of the premium
    out["contract_weighted_mean"] = float(np.average(y[ok], weights=frame.loc[ok, "amount"].to_numpy(float)))
    s = np.sort(y[ok])
    k = int(TRIM * len(s))
    out["trimmed_mean_5pct"] = float(s[k:len(s) - k].mean())
    out["trim_pct"] = 100.0 * TRIM
    agg = (frame.assign(dollar=frame["y_usd"] * frame["amount"])
                .groupby("currency").agg(dollar=("dollar", "sum"), index=("index_price", "mean")))
    for ccy in ("BTC", "ETH", "HYPE"):
        if ccy in agg.index:
            out[f"dollar_gain_musd_{ccy}"] = float(agg.loc[ccy, "dollar"] / 1e6)
            out[f"mean_index_{ccy}"] = float(agg.loc[ccy, "index"])
    idx = agg["index"].reindex(["BTC", "ETH", "HYPE"]).dropna()
    out["index_ratio_max_min"] = float(idx.max() / idx.min())
    out["index_ratio_log10"] = float(np.log10(idx.max() / idx.min()))
    share = figdata.premium_share(frame, "y_usd").to_numpy(float)
    share = share[np.isfinite(share)]
    for q, name in ((25, "q25"), (50, "median"), (75, "q75")):
        out[f"premium_share_{name}_pct"] = float(np.percentile(share, q))
    return out


def package_fee_net_edge(frame: pd.DataFrame) -> pd.Series:
    """Net edge with the maker fee of a multi-leg RFQ spread over its package (Addendum 3, point 3): every leg of a
    package (same ``rfq_id`` and maker wallet) carries (sum of fees - sum of rebates) / sum of amounts; order book
    fills are unchanged."""
    f = frame
    amount = f["amount"].astype(float)
    rfq = f["rfq_id"].notna() & (f["rfq_id"].astype(str) != "")
    key = f["rfq_id"].astype(str) + "|" + f["maker_wallet"].astype(str)
    sums = f[rfq].assign(_net=f["fee_maker"].astype(float) - f["rebate_maker"].astype(float), _a=amount)\
        .groupby(key[rfq])[["_net", "_a"]].sum()
    per_contract = (sums["_net"] / sums["_a"]).reindex(key[rfq]).to_numpy()
    own = f["fee_pc"] - f["rebate_pc"]
    spread = own.copy()
    spread.loc[rfq] = per_contract
    return f["y_usd"] - spread - f["hedge"]


def horizon_numbers(frame: pd.DataFrame) -> Dict[str, object]:
    """Section 5.2 and Figure 2: the fills that carry every horizon, and the mean across the five horizons."""
    cols = ["mo_usd_{}".format(h) for h in figures_p1.HORIZONS]
    balanced = frame[np.isfinite(frame[cols]).all(axis=1)]
    out: Dict[str, object] = {"balanced_fills": int(len(balanced))}
    hs_vol = 100.0 * balanced["maker_side"] * (balanced["iv_mark_t"] - balanced["iv_fill"])
    out["balanced_mean_half_spread"] = float(np.nanmean(balanced["hs"]))
    for h in figures_p1.HORIZONS:
        out[f"balanced_mean_usd_{h}"] = float(np.nanmean(balanced[f"mo_usd_{h}"]))
        out[f"balanced_mean_vol_{h}"] = float(np.nanmean(balanced[f"mo_vol_{h}"]))
        out[f"balanced_median_usd_{h}"] = float(np.nanmedian(balanced[f"mo_usd_{h}"]))
        out[f"balanced_median_vol_{h}"] = float(np.nanmedian(balanced[f"mo_vol_{h}"]))
        out[f"balanced_median_premium_{h}"] = float(np.nanmedian(figdata.premium_share(balanced, f"mo_usd_{h}")))
        # adverse selection = markout - half spread, in USDC, delta-neutral and vol points
        out[f"balanced_mean_as_usd_{h}"] = float(np.nanmean(balanced[f"mo_usd_{h}"] - balanced["hs"]))
        out[f"balanced_mean_as_dn_{h}"] = float(np.nanmean(balanced[f"mo_dn_{h}"] - balanced["hs"]))
        out[f"balanced_mean_as_vol_{h}"] = float(np.nanmean(balanced[f"mo_vol_{h}"] - hs_vol))
    last, first = figures_p1.HORIZONS[-1], figures_p1.HORIZONS[0]
    out["balanced_as_usd_share_after_first_pct"] = float(
        100.0 * (out[f"balanced_mean_as_usd_{last}"] - out[f"balanced_mean_as_usd_{first}"]) / out[f"balanced_mean_as_usd_{last}"])
    return out


def settlement_numbers(frame: pd.DataFrame, b: int, seed: int) -> Dict[str, object]:
    """Section 3: the registered settlement horizon (robustness path c) over the fills settled inside the loaded data
    (a fill whose expiry has no settlement price has no settlement markout), with a cluster pairs bootstrap interval
    over taker wallets."""
    y = frame["mo_set"].to_numpy(float)
    ok = np.isfinite(y)
    ci = cluster_mean_ci(y[ok], frame["cluster"].to_numpy()[ok], b=b, seed=seed, level=INTERVAL_LEVEL)
    return {"settlement_fills": int(ok.sum()), "settlement_mean": float(y[ok].mean()),
            "settlement_lo95": float(ci["lo"]), "settlement_hi95": float(ci["hi"]),
            "settlement_interval_pct": 100.0 * INTERVAL_LEVEL}


def concentration_numbers(frame: pd.DataFrame, lorenz: pd.DataFrame) -> Dict[str, object]:
    """Figure 3c and section 5.4: the ten loss wallets in the professional classes, the single largest wallet and
    the raw differences of size and sweep (Figure 4b)."""
    out: Dict[str, object] = {"loss_wallets": int(len(lorenz))}
    worst = lorenz.nsmallest(10, "loss")
    out["top1_loss_share_pct"] = float(100.0 * lorenz["loss"].min() / lorenz["loss"].sum())
    top10 = set(worst["wallet"])
    if top10 and all(str(w).startswith("W") for w in top10):
        member = pd.Series(wallet_pseudonym(frame["taker_wallet"], load_salt()), index=frame.index).isin(top10)
    else:
        member = frame["taker_wallet"].isin(top10)
    for name in PROFESSIONAL_SHARE_CLASSES:
        sel = frame["taker_class"] == name
        out[f"top10_share_of_{name}_fills_pct"] = float(100.0 * member[sel].mean()) if sel.any() else None
    # the ten loss wallets that ever trade in the two professional classes, and their share of the loss
    wallets = (pd.Series(wallet_pseudonym(frame["taker_wallet"], load_salt()), index=frame.index)
               if top10 and all(str(w).startswith("W") for w in top10) else frame["taker_wallet"])
    professional = set(wallets[frame["taker_class"].isin(PROFESSIONAL_SHARE_CLASSES)]) & top10
    out["top10_in_professional_classes"] = int(len(professional))
    out["top10_professional_loss_share_pct"] = float(
        100.0 * worst.loc[worst["wallet"].isin(professional), "loss"].sum() / lorenz["loss"].sum())
    out["raw_size_difference_dn"] = float(frame.loc[frame["size_above_p90"], "y_dn"].mean()
                                          - frame.loc[~frame["size_above_p90"], "y_dn"].mean())
    out["raw_sweep_difference_dn"] = float(frame.loc[frame["is_sweep"], "y_dn"].mean()
                                           - frame.loc[~frame["is_sweep"], "y_dn"].mean())
    return out


def cell_numbers(frame: pd.DataFrame, cells: pd.DataFrame, markouts: pd.DataFrame, funding: pd.DataFrame,
                 b: int, seed: int) -> Dict[str, object]:
    """Section 5.5 and section 6: verdicts per cell, the alternative count by p-value, and the map per notional."""
    out: Dict[str, object] = {"cells": int(len(cells)), "cells_positive": int(cells["positive"].sum()),
                              "cells_negative": int(cells["negative"].sum())}
    inconclusive = cells[~cells["positive"] & ~cells["negative"]]
    out["cells_inconclusive"] = int(len(inconclusive))
    out["cells_inconclusive_high_delta"] = int(inconclusive["delta_bucket"].isin(HIGH_DELTA).sum())
    out["high_delta_fill_share_pct"] = float(100.0 * frame["delta_bucket"].isin(HIGH_DELTA).mean())

    def by_p(table: pd.DataFrame) -> int:
        return int(((table["mean"] > 0) & (table["p"] < P_ALTERNATIVE)).sum())

    out["alternative_p_threshold"] = P_ALTERNATIVE
    out["cells_positive_p10_1bp"] = by_p(cells)
    out["cells_positive_p10_1bp_pct"] = 100.0 * by_p(cells) / len(cells)
    f3 = analysis_frame(markouts, funding, half_spread_bp=3.0)
    cells3 = cell_table(f3, "net_edge", b=b, seed=seed)
    out["cells_3bp"] = int(len(cells3))
    atm3 = cells3[cells3["currency"].isin(["BTC", "ETH"]) & (cells3["delta_bucket"] == ATM)
                  & (cells3["tenor_bucket"] == "<=2d")]
    out["atm_short_cells_positive_3bp"] = int(atm3["positive"].sum())
    out["atm_short_cells_excluding_zero_3bp"] = int((atm3["positive"] | atm3["negative"]).sum())
    out["cells_positive_p10_3bp"] = by_p(cells3)
    out["cells_positive_p10_3bp_pct"] = 100.0 * by_p(cells3) / len(cells3)

    # the RFQ fee spread over the package: mean net edge and the cell verdicts it would change
    pkg = frame.assign(net_edge=package_fee_net_edge(frame))
    out["net_edge_package_fee"] = float(np.nanmean(pkg["net_edge"]))
    cells_pkg = cell_table(pkg, "net_edge", b=b, seed=seed)
    merged = cells.merge(cells_pkg, on=["currency", "delta_bucket", "tenor_bucket"], how="outer",
                         suffixes=("", "_pkg"), indicator=True)
    changed = (merged["_merge"] != "both") | (merged["positive"] != merged["positive_pkg"]) | \
              (merged["negative"] != merged["negative_pkg"])
    out["cells_verdict_changed_package_fee"] = int(changed.sum())

    # Figure 5, upper row: median net edge in basis points of notional per cell (cells of at least 200 fills)
    bp = frame.assign(bp=figdata.edge_bp(frame))
    ratios = []
    for ccy in ("BTC", "ETH", "HYPE"):
        values, _ = figdata.cell_matrix(bp[bp["currency"] == ccy], "bp", stat="median")
        grid = values.to_numpy(float)
        if not np.isfinite(grid).any():
            continue
        out[f"bp_median_over_cells_{ccy}"] = float(np.nanmedian(grid))
        for tenor in values.index:
            if ATM in values.columns and np.isfinite(values.loc[tenor, ATM]):
                out[f"bp_atm_{TENOR_KEY[tenor]}_{ccy}"] = float(values.loc[tenor, ATM])
        short = values.loc[[t for t in SHORT_TENORS if t in values.index],
                           [d for d in LOW_DELTA if d in values.columns]].to_numpy(float)
        if np.isfinite(short).any():
            out[f"bp_short_low_delta_min_{ccy}"] = float(np.nanmin(short))
            out[f"bp_short_low_delta_max_{ccy}"] = float(np.nanmax(short))
        if "<=2d" in values.index and ">90d" in values.index:
            for d in [d for d in BELOW_75 if d in values.columns]:
                lo, hi = values.loc["<=2d", d], values.loc[">90d", d]
                if np.isfinite(lo) and np.isfinite(hi) and lo > 0:
                    ratios.append(hi / lo)
    out["bp_ratio_pairs"] = len(ratios)
    if ratios:
        out["bp_ratio_90d_over_2d_min"] = float(min(ratios))
        out["bp_ratio_90d_over_2d_max"] = float(max(ratios))
    core = frame[frame["currency"].isin(["BTC", "ETH"])]
    out["short_low_delta_share_btc_eth_pct"] = float(
        100.0 * (core["tenor_bucket"].isin(SHORT_TENORS) & core["delta_bucket"].isin(LOW_DELTA)).mean())
    return out


def curve_age_numbers(frame: pd.DataFrame) -> Dict[str, object]:
    """Figure A1b: the mean markout per class of curve age."""
    bucket = pd.cut(frame["svi_age_s_t"], figures_p1.AGE_EDGES, labels=figures_p1.AGE_LABELS, right=False)
    means = [float(np.nanmean(frame.loc[bucket == label, "y_usd"])) for label in figures_p1.AGE_LABELS
             if (bucket == label).any()]
    return {"curve_age_classes": len(means), "curve_age_class_mean_min": float(min(means)),
            "curve_age_class_mean_max": float(max(means))}


def figure_constants() -> Dict[str, object]:
    """Constants of the figures that their captions print (draws, levels, thresholds of the drawing)."""
    import inspect
    level = inspect.signature(cluster_mean_ci).parameters["level"].default
    level_f2 = inspect.signature(figdata._median_ci).parameters["level"].default
    return {"figure_draws": figures_p1.BOOTSTRAP, "figure_interval_pct": 100.0 * level,
            "f2_interval_pct": 100.0 * level_f2,
            "t1_neighbours": figures_p1.NEIGHBOURS, "f3_few_wallets": figures_p1.FEW_WALLETS,
            "f5_shade_lo_pct": figures_p1.SHADE_PERCENTILES[0], "f5_shade_hi_pct": figures_p1.SHADE_PERCENTILES[1],
            "f6_thin_month_fills": figures_p1.THIN_MONTH_FILLS, "path_a_near_s": NEAR_LAG_S}


def build(root: Path, results: Path, b: int = B, seed: int = SEED) -> Dict[str, object]:
    markouts = pd.read_parquet(root / "derived" / "markouts.parquet")
    funding = pd.read_parquet(root / "ref" / "funding_history.parquet")
    frame = analysis_frame(markouts, funding)
    lorenz = pd.read_csv(results / "h1_lorenz.csv")
    cells = pd.read_csv(results / "h4_cells.csv")
    out: Dict[str, object] = {"b": b, "seed": seed}
    out.update(sample_numbers(frame))
    out.update(markout_numbers(frame, b, seed))
    out.update(horizon_numbers(frame))
    out.update(settlement_numbers(frame, b, seed))
    out.update(concentration_numbers(frame, lorenz))
    out.update(cell_numbers(frame, cells, markouts, funding, b, seed))
    out.update(curve_age_numbers(frame))
    out.update(figure_constants())
    summary = json.loads((results / "summary.json").read_text())
    beta = np.asarray(summary["H3"]["did"].get("placebo_beta", []), dtype=float)
    out["h3_placebo_beta_sd"] = float(np.std(beta, ddof=1)) if len(beta) > 1 else None
    # the placebo estimates are not centred on zero: their centre, how many lie below zero, and the span of their dates
    out["h3_placebo_beta_mean"] = float(np.mean(beta)) if len(beta) else None
    out["h3_placebo_negative"] = int((beta < 0).sum())
    did = summary["H3"]["did"]
    for key, name in (("placebo_first_ms", "h3_placebo_first_day"), ("placebo_last_ms", "h3_placebo_last_day")):
        out[name] = pd.Timestamp(did[key], unit="ms", tz="UTC").strftime("%Y-%m-%d") if did.get(key) else None
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--out", type=Path, default=None, help="default <results>/text_numbers.json")
    ap.add_argument("--b", type=int, default=B)
    args = ap.parse_args(argv)
    values = build(args.root, args.results, b=args.b)
    out = args.out or args.results / OUT_NAME
    out.write_text(json.dumps(values, indent=1, sort_keys=True) + "\n")
    print(json.dumps(values, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
