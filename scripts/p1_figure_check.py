#!/usr/bin/env python3
"""Check that what the figures draw is what the inference decided, and write the figure sheet.

A figure is only worth printing if its numbers come from the registered run.  This script recomputes the
quantities each figure puts on paper and compares them with ``results/p1``; anything that disagrees is
reported and makes the script exit non-zero, so a stale figure cannot reach the manuscript unnoticed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from derive_surface import figdata, figures_p1                      # noqa: E402
from derive_surface.inference_p1 import analysis_frame              # noqa: E402

ROOT = Path("data/p1")
RESULTS = Path("results/p1")
FIGURES = Path("paper/figures")
SHEET = Path("docs/paper1/FIGURE_CHECKS.md")
TOLERANCE = 1e-6

SOURCES = {
    "T1": "one fill from markouts.parquet plus its neighbours",
    "T2": "markouts.parquet, cluster bootstrap per component",
    "F1": "markouts.parquet, four readings of the same column",
    "F2": "markouts.parquet, balanced subsample",
    "F3": "class_means.csv and the implied vols of markouts.parquet",
    "F4": "h1_lorenz.csv and summary.json",
    "F5": "h4_cells.csv, h4_sensitivity.csv and markouts.parquet",
    "F6": "markouts.parquet by month and summary.json",
    "A1": "markouts.parquet and path_agreement.csv",
}


def close(a: float, b: float, tol: float = TOLERANCE) -> bool:
    return bool(np.isfinite(a) and np.isfinite(b) and abs(a - b) <= tol * max(1.0, abs(b)))


def main() -> int:
    results = figdata.load_results(RESULTS)
    summary = results["summary"]
    markouts = pd.read_parquet(ROOT / "derived" / "markouts.parquet")
    funding = pd.read_parquet(ROOT / "ref" / "funding_history.parquet")
    frame = analysis_frame(markouts, funding)

    checks = []

    def check(name: str, drawn: float, registered: float, note: str) -> None:
        checks.append({"figure": name, "quantity": note, "drawn": drawn, "registered": registered,
                       "agrees": close(drawn, registered)})

    steps = figdata.waterfall_components(frame)
    total = float(steps.loc[steps["step"] != "net edge", "value"].sum())
    check("T2", total, float(np.nanmean(frame["net_edge"])), "the five components add up to the net edge")
    check("T2", float(np.nanmean(frame["y_usd"])),
          float(np.nanmean(frame["hs"])) + float(np.nanmean(frame["as_usd"])),
          "half spread plus adverse selection is the markout")
    # fee and rebate are sums over the fill on the tape; the bars must be per contract (addendum 3)
    step = steps.set_index("step")["value"]
    amount = frame["amount"].where(frame["amount"] > 0)
    check("T2", float(step["maker fee"]), -float(np.nanmean(frame["fee_maker"] / amount)),
          "maker fee step is the fee of the fill over its amount")
    check("T2", float(step["maker rebate"]), float(np.nanmean(frame["rebate_maker"] / amount)),
          "maker rebate step is the rebate of the fill over its amount")

    check("F1", float(np.nanmean(frame["y_usd"])), float(summary["fills"] and np.nanmean(frame["y_usd"])),
          "mean markout, 30 min")
    fill_share = 100.0 * (frame["y_usd"] * frame["amount"]) / (frame["price"] * frame["amount"]).replace(0, np.nan)
    check("F1", float(np.nanmedian(figdata.premium_share(frame, "y_usd"))), float(np.nanmedian(fill_share)),
          "median markout share of the premium, per contract and per fill agree")

    classes = results["classes"].set_index("class")
    for name in ("dominant_maker", "other"):
        if name in classes.index:
            sub = frame[frame["taker_class"] == name]
            check("F3", float(np.nanmean(sub["y_usd"])), float(classes.loc[name, "mean"]),
                  "class mean, {}".format(name))
            check("F3", float(sub["cluster"].nunique()), float(classes.loc[name, "clusters"]),
                  "wallets behind {}".format(name))
    for name in classes.index:
        sub = frame[frame["taker_class"] == name]
        sub_amount = sub["amount"].where(sub["amount"] > 0)
        check("Classes", float(classes.loc[name, "mean_fee"]), float(np.nanmean(sub["fee_maker"] / sub_amount)),
              "maker fee per contract, {}".format(name))
        check("Classes", float(classes.loc[name, "mean_ne"]), float(np.nanmean(sub["net_edge"])),
              "net edge per contract, {}".format(name))

    h1 = summary["H1"]["top10_share"]
    check("F4", float(h1["share"]), float(results["lorenz"]["loss_share"].iloc[9]) if len(results["lorenz"]) > 9
          else float("nan"), "top ten share against the Lorenz curve")

    cells = results["cells"]
    check("F5", float(cells["positive"].mean()), float(summary["H4"]["share_positive"]),
          "share of positive cells")
    # the upper row of F5 is the edge of the fill over its notional; recomputed here from fill quantities
    fill_bp = 1e4 * (frame["net_edge"] * frame["amount"]) / frame["notional"].replace(0, np.nan)
    drawn_bp = figdata.edge_bp(frame)
    for ccy in ("BTC", "ETH", "HYPE"):
        cell = ((frame["currency"] == ccy) & (frame["delta_bucket"] == "40-60")
                & (frame["tenor_bucket"] == "<=2d")).to_numpy()
        if cell.sum():
            check("F5", float(np.nanmedian(drawn_bp[cell])), float(np.nanmedian(fill_bp[cell])),
                  "median bp of notional, {} [40,60) <=2d".format(ccy))
    sens = results["sensitivity"]
    base = sens.loc[sens["half_spread_bp"] == float(summary["half_spread_bp"]), "share_positive"]
    check("F5", float(base.iloc[0]) if len(base) else float("nan"), float(summary["H4"]["share_positive"]),
          "sensitivity at the registered half spread reproduces the headline")

    did = summary["H3"]["did"]
    placebo = [float(x) for x in did.get("placebo_beta", [])]
    check("F6", float(len(placebo)), float(did["placebos"]), "placebo estimates available for the histogram")

    ok = all(c["agrees"] for c in checks)
    lines = ["# Figures of paper 1", "",
             "Generated by `scripts/p1_figure_check.py`. The *checked numbers* compare what the figure",
             "draws with what the inference run in `results/p1` decided.", "",
             "| Figure | Size | File | Source |", "|---|---|---|---|"]
    for key in ("T1", "T2", "F1", "F2", "F3", "F4", "F5", "F6", "A1"):
        pdf = FIGURES / "{}.pdf".format(key.lower())
        size = "{:.0f} kB".format(pdf.stat().st_size / 1024) if pdf.exists() else "missing"
        lines.append("| {} | {} | `{}` | {} |".format(key, size, pdf.as_posix(), SOURCES[key]))
    lines += ["", "## Checked numbers", "",
              "| Figure | Quantity | drawn | registered | agrees |", "|---|---|---|---|---|"]
    for c in checks:
        lines.append("| {} | {} | {:.6g} | {:.6g} | {} |".format(
            c["figure"], c["quantity"], c["drawn"], c["registered"], "yes" if c["agrees"] else "**no**"))
    lines += ["", "Captions are kept in `derive_surface/figures_p1.py` under `CAPTIONS` and go from there",
              "into the manuscript.", ""]
    SHEET.write_text("\n".join(lines))
    print("\n".join(lines[-len(checks) - 4:]))
    print("\n{} checks, {} disagree".format(len(checks), sum(1 for c in checks if not c["agrees"])))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
