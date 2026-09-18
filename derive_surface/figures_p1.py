"""The figures of paper 1.

One function per slot, all of them fed from the same two sources: the analysis frame built by
``inference_p1.analysis_frame`` and the registered result tables in ``results/p1``.  Nothing is computed a
second time here that the inference already decided, so a figure and the number sheet cannot disagree.

Two rules run through every figure.  Uncertainty belongs in the picture, not in a footnote, which means a
bootstrap interval next to every mean and the wild cluster p-value next to every class.  And every encoding
has to survive grayscale printing, so colour is always doubled by a marker shape, a line style or a hatch.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from . import figdata, figstyle  # noqa: E402
from .inference_p1 import HORIZON_SECONDS, cluster_mean_ci  # noqa: E402
from .markouts import DELTA_LABELS, TENOR_LABELS  # noqa: E402

HORIZONS = list(HORIZON_SECONDS)
PROFESSIONAL = ("dominant_maker", "mm_programme", "large")
AGE_EDGES = [0, 5, 10, 20, 40, 60, 120, 300, np.inf]
AGE_LABELS = ["0-5", "5-10", "10-20", "20-40", "40-60", "60-120", "120-300", ">300"]
BOOTSTRAP = 999                      # figures only draw intervals; the registered ones come from results/p1
SEED = 20260917


# --------------------------------------------------------------------------------------- shared helpers

def _ci(values, clusters, b: int = BOOTSTRAP) -> Dict[str, float]:
    values = np.asarray(values, dtype=float)
    ok = np.isfinite(values)
    if ok.sum() == 0:
        return {"mean": np.nan, "lo": np.nan, "hi": np.nan, "n": 0}
    return cluster_mean_ci(values[ok], np.asarray(clusters)[ok], b=b, seed=SEED)


def _premium(frame: pd.DataFrame) -> pd.Series:
    return (frame["price"] * frame["amount"]).replace(0, np.nan)


def _symlog_core(ax, core: float, axis: str = "x") -> None:
    """Shade the linear core of a symlog axis and say so, so the reader can trust the widths."""
    if axis == "x":
        ax.axvspan(-core, core, color=figstyle.GREY, alpha=0.12, lw=0, zorder=0)
    else:
        ax.axhspan(-core, core, color=figstyle.GREY, alpha=0.12, lw=0, zorder=0)


def _panel_tag(ax, letter: str) -> None:
    """Only the letter. What the panel shows belongs in the caption, not on top of the drawing."""
    ax.set_title(letter, loc="left", fontweight="bold", fontsize=8.0, pad=3)


def _side_note(ax, text: str, y: float, align: str = "left") -> None:
    """A note pinned to the axes frame, so it can never grow the axis or collide with the data."""
    ax.annotate(text, xy=(0.0 if align == "left" else 1.0, y), xycoords="axes fraction",
                ha=align, va="center", fontsize=6.5)


CAPTIONS = {
    "T1": "One fill, three mark paths and three units. Panels a and b stop at the registered 30 minute "
          "horizon; panel c carries every horizon. The shaded band is the interquartile range of the 100 "
          "nearest fills in the same cell, so the example can be read against its neighbours.",
    "T2": "The identity behind the net edge, and who pays the fee. Error bars are 95 percent cluster "
          "bootstrap intervals over taker wallets. The hedge bar is dotted because it is the only modelled "
          "component.",
    "F1": "The same result read four ways. The shaded core of panel a is linear, everything outside it is "
          "logarithmic with equal area per decade.",
    "F2": "How long adverse selection lasts, on the balanced subsample that has every horizon. Bands are "
          "95 percent cluster bootstrap intervals of the median, not dispersion.",
    "F3": "Who takes back which part of the spread. G is the number of taker wallets behind a class and p "
          "is the wild cluster bootstrap p-value against zero; shaded rows carry fewer than 40 wallets.",
    "F4": "The concentration behind H1 and the two coefficients on which H1 fails. The horizontal axis of "
          "panel a is logarithmic because the first ten wallets carry most of the loss.",
    "F5": "Where the edge survives. The upper row is the median net edge per notional, the unit a quoting "
          "decision uses; the lower row is the registered quantity in USDC and its verdict per cell.",
    "F6": "The sample over 33 months and the only event study in the paper. Panel c is the distribution of "
          "the 100 placebo estimates with the estimated effect marked.",
    "A1": "Whether the on-chain mark carries the measurement. A flat line in panel b is the reassurance: "
          "the markout does not move with the age of the curve.",
}


def _class_rows(results: dict) -> pd.DataFrame:
    classes = results["classes"].copy()
    classes["order"] = classes["class"].map({c: i for i, c in enumerate(figstyle.CLASS_ORDER)})
    return classes.sort_values("order")


# ------------------------------------------------------------------------------------------ the figures

def fig_t1(inputs: dict, out_dir: Path) -> List[Path]:
    """T1: one fill, three mark paths, three units -- the definition of everything that follows."""
    frame, svi = inputs["frame"], inputs.get("svi")
    row = figdata.example_fill(frame, taker_class="other", horizon="30m")
    side = float(row["maker_side"])
    x = np.arange(len(HORIZONS) + 1, dtype=float)
    labels = ["fill"] + HORIZONS
    marks = [float(row["mark_b_t"])] + [float(row["mark_b_{}".format(h)]) for h in HORIZONS]
    ivs = [float(row["iv_mark_t"])] + [float(row["iv_b_{}".format(h)]) for h in HORIZONS]
    raw = [0.0] + [side * (m - float(row["price"])) for m in marks[1:]]
    neutral = [0.0] + [float(row["mo_dn_{}".format(h)]) for h in HORIZONS]

    near = frame[(frame["currency"] == row["currency"]) & (frame["delta_bucket"] == row["delta_bucket"])
                 & (frame["tenor_bucket"] == row["tenor_bucket"])]
    near = near.reindex((near["ts"] - row["ts"]).abs().sort_values().index[:100])
    band_lo = [0.0] + [float(np.nanpercentile(near["mo_usd_{}".format(h)], 25)) for h in HORIZONS]
    band_hi = [0.0] + [float(np.nanpercentile(near["mo_usd_{}".format(h)], 75)) for h in HORIZONS]

    fig, axes = figstyle.figure(figstyle.DOUBLE, 2.8, ncols=3, gridspec_kw={"wspace": 0.34})
    a, b, c = axes
    a.step(x, marks, where="post", color=figstyle.PALETTE[0], label="mark, on-chain SVI curve")
    a.axhline(float(row["price"]), color=figstyle.PALETTE[1], ls="--", lw=1.0, label="fill price")
    a.plot([0], [float(row["mark_b_t"])], "o", color=figstyle.PALETTE[0], ms=4)
    if np.isfinite(row.get("mark_a_30m", np.nan)):
        a.plot([3], [float(row["mark_a_30m"])], "s", mfc="none", color=figstyle.GREY, ms=4,
               label="mark of the next fill")
    a.annotate("", xy=(0.12, float(row["mark_b_t"])), xytext=(0.12, float(row["price"])),
               arrowprops=dict(arrowstyle="<->", lw=0.7, color="black"))
    a.text(0.2, 0.5 * (float(row["mark_b_t"]) + float(row["price"])),
           "half spread\n{:+.2f}".format(side * (float(row["mark_b_t"]) - float(row["price"]))), fontsize=7, va="center")
    a.set_ylabel("price, USDC per contract")
    a.legend(loc="best", fontsize=6.5)
    _panel_tag(a, "a  price")

    b.step(x, ivs, where="post", color=figstyle.PALETTE[0])
    b.axhline(float(row["iv_fill"]), color=figstyle.PALETTE[1], ls="--", lw=1.0)
    b.set_ylabel("implied volatility")
    _panel_tag(b, "b  volatility")

    c.fill_between(x, band_lo, band_hi, color=figstyle.GREY, alpha=0.20, lw=0,
                   label="p25-p75 of the 100 nearest fills")
    c.plot(x, raw, "-o", color=figstyle.PALETTE[0], ms=3, label="markout")
    c.plot(x, neutral, "--s", color=figstyle.PALETTE[2], ms=3, mfc="none", label="delta neutral")
    c.fill_between(x, raw, neutral, hatch="///", facecolor="none", edgecolor=figstyle.PALETTE[2], lw=0.0, alpha=0.6)
    c.axhline(0, color="black", lw=0.6)
    c.set_ylabel("markout, USDC per contract")
    c.legend(loc="best", fontsize=6.5)
    _panel_tag(c, "c  markout")

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=6.5)
        ax.set_xlabel("time after the fill")
    fig.text(0.005, 0.5, "maker side, {}".format("sold" if side < 0 else "bought"), rotation=90,
             va="center", fontsize=6.5, color=figstyle.GREY)
    return figstyle.save(fig, "t1", out_dir)


def fig_t2(inputs: dict, out_dir: Path) -> List[Path]:
    """T2: the identity that turns a half spread into a net edge, and where the fee eats the premium."""
    frame = inputs["frame"]
    steps = figdata.waterfall_components(frame)
    cols = {"half spread": "hs", "adverse selection": "as_usd", "maker fee": "fee_maker",
            "maker rebate": "rebate_maker", "hedge cost": "hedge"}
    intervals = {}
    for name, col in cols.items():
        sign = -1.0 if name in ("maker fee", "hedge cost") else 1.0
        ci = _ci(sign * frame[col].to_numpy(float), frame["cluster"].to_numpy())
        intervals[name] = (ci["lo"], ci["hi"])
    markout = _ci(frame["y_usd"].to_numpy(float), frame["cluster"].to_numpy())
    net = _ci(frame["net_edge"].to_numpy(float), frame["cluster"].to_numpy())

    order = ["half spread", "adverse selection", "markout", "maker fee", "maker rebate", "hedge cost", "net edge"]
    values = dict(zip(steps["step"], steps["value"]))
    values["markout"] = markout["mean"]
    intervals["markout"], intervals["net edge"] = (markout["lo"], markout["hi"]), (net["lo"], net["hi"])

    fig = plt.figure(figsize=(figstyle.DOUBLE, 3.0))
    figstyle.use_style()
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.30)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    for ax in (a, b):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    running = 0.0
    for i, name in enumerate(order):
        value = values[name]
        total = name in ("markout", "net edge")
        bottom = 0.0 if total else running
        height = value if total else value
        color = figstyle.GREY if total else (figstyle.PALETTE[0] if value >= 0 else figstyle.PALETTE[1])
        a.bar(i, height, bottom=bottom, color=color, edgecolor="black",
              lw=1.1 if name == "hedge cost" else 0.6,
              ls=":" if name == "hedge cost" else "-",
              hatch="///" if (value < 0 and not total) else None)
        lo, hi = intervals[name]
        top = bottom + height
        a.plot([i, i], [bottom + lo if not total else lo, bottom + hi if not total else hi],
               color="black", lw=0.7) if total else a.plot([i, i], [top - (value - lo), top + (hi - value)],
                                                           color="black", lw=0.7)
        a.text(i, top + (0.9 if value >= 0 else -1.6), "{:+.2f}".format(value), ha="center", fontsize=6.5)
        if not total:
            running += value
    a.axhline(0, color="black", lw=0.6)
    a.set_xticks(range(len(order)))
    a.set_xticklabels([o.replace(" ", "\n") for o in order], fontsize=6.5)
    a.set_ylabel("mean per contract, USDC")
    a.text(0.02, 0.96, "median half spread +{:.2f}, medians are not additive".format(float(frame["hs"].median())),
           transform=a.transAxes, fontsize=6.5, va="top", color=figstyle.GREY)
    a.legend(handles=[Patch(facecolor="white", edgecolor="black", ls=":", label="modelled, not observed")],
             loc="lower left", fontsize=6.5)
    _panel_tag(a, "a  the identity, {:,} fills".format(len(frame)).replace(",", " "))

    premium = _premium(frame)
    grid = np.logspace(-3, 3, 200)
    for label, col, style in (("maker", "fee_maker", "-"), ("taker", "fee_taker", "--")):
        share = (100.0 * frame[col] / premium).to_numpy(float)
        share = share[np.isfinite(share)]
        ecdf = [float(np.mean(share <= g)) for g in grid]
        b.plot(grid, ecdf, style, color=figstyle.PALETTE[0 if label == "maker" else 1], label=label)
        zero = float(np.mean(share <= 0))
        if label == "maker":
            b.text(1.2e-3, zero + 0.03, "{:.0f} % of fills pay no maker fee".format(100 * zero), fontsize=6.5)
        else:
            above = float(np.mean(share > 100))
            b.text(1.5e2, 0.55, "{:.1f} % of fills pay more\nfee than premium".format(100 * above),
                   fontsize=6.5, ha="right")
    b.axvline(12.5, color=figstyle.GREY, lw=0.8, ls=":")
    b.axvline(100, color="black", lw=0.8)
    b.text(12.5, 0.02, " 12.5 %", fontsize=6.5, color=figstyle.GREY)
    b.text(100, 0.02, " premium", fontsize=6.5)
    b.set_xscale("log")
    b.set_xlim(1e-3, 1e3)
    b.set_ylim(0, 1.02)
    b.set_xlabel("fee as a share of the premium, %")
    b.set_ylabel("share of fills at or below")
    b.legend(loc="center left", fontsize=6.5)
    _panel_tag(b, "b  who pays the fee")
    return figstyle.save(fig, "t2", out_dir)


def fig_f1(inputs: dict, out_dir: Path) -> List[Path]:
    """F1: the same finding in four readings, so the headline number cannot be misread."""
    frame = inputs["frame"]
    y = frame["y_usd"].to_numpy(float)
    y = y[np.isfinite(y)]
    trimmed = np.sort(y)
    k = int(0.05 * len(trimmed))
    stats = [("median", float(np.median(y))),
             ("5 % trimmed", float(trimmed[k:len(trimmed) - k].mean()) if len(trimmed) > 2 * k else np.nan),
             ("mean", float(y.mean()))]
    weights = frame.loc[np.isfinite(frame["y_usd"]), "amount"].to_numpy(float)
    contract_weighted = float(np.average(y, weights=weights)) if weights.sum() > 0 else np.nan

    fig, axes = figstyle.figure(figstyle.DOUBLE, 2.6, ncols=3, gridspec_kw={"wspace": 0.33})
    a, b, c = axes

    core = 10.0
    bins = np.concatenate([-np.logspace(3, np.log10(core), 25), np.linspace(-core, core, 21),
                           np.logspace(np.log10(core), 3, 25)])
    a.hist(y, bins=bins, color=figstyle.PALETTE[0], alpha=0.75)
    a.set_xscale("symlog", linthresh=core)
    _symlog_core(a, core)
    for (label, value), style in zip(stats, ["-", "--", ":"]):
        if np.isfinite(value):
            a.axvline(value, color="black", ls=style, lw=1.0)
            a.text(value, a.get_ylim()[1] * (0.95 if label == "median" else 0.82 if label == "mean" else 0.66),
                   " {} {:.2f}".format(label, value), fontsize=6.5)
    a.set_xlabel("markout after 30 min, USDC per contract\n(symlog, shaded core is linear)")
    a.set_ylabel("fills")
    _panel_tag(a, "a  one number, three centres")

    agg = (frame.assign(dollar=frame["y_usd"] * frame["amount"])
                .groupby("currency").agg(dollar=("dollar", "sum"), fills=("y_usd", "size"),
                                         index=("index_price", "mean")).reindex(["BTC", "ETH", "HYPE"]).dropna())
    pos = np.arange(len(agg))
    b.barh(pos, agg["dollar"] / 1e6, color=[figstyle.PALETTE[i] for i in range(len(agg))], edgecolor="black", lw=0.5)
    b.set_yticks(pos)
    b.set_yticklabels(agg.index)
    for i, (name, r) in enumerate(agg.iterrows()):
        b.text(r["dollar"] / 1e6, i, "  {:.2f} m, index {:,.0f}".format(r["dollar"] / 1e6, r["index"]).replace(",", " "),
               va="center", fontsize=6.5)
    b.set_xlim(0, float(agg["dollar"].max()) / 1e6 * 1.9)
    b.set_xlabel("aggregate maker gain, million USDC")
    _panel_tag(b, "b  same dollars, different contracts")

    premium = _premium(frame)
    share = (100.0 * frame["y_usd"] / premium).to_numpy(float)
    share = share[np.isfinite(share)]
    q = np.percentile(share, [25, 50, 75])
    c.hist(share, bins=np.linspace(-100, 150, 60), color=figstyle.PALETTE[2], alpha=0.75)
    for value, label in zip(q, ["q25", "median", "q75"]):
        c.axvline(value, color="black", lw=0.9, ls="--" if label != "median" else "-")
        c.text(value, c.get_ylim()[1] * (0.95 if label == "median" else 0.75),
               " {} {:+.1f} %".format(label, value), fontsize=6.5)
    c.set_xlabel("markout as a share of the premium, %")
    c.set_ylabel("fills")
    _panel_tag(c, "c  what a maker actually books")
    fig.text(0.005, 0.02, "contract weighted mean {:+.3f} USDC per contract".format(contract_weighted),
             fontsize=6.5, color=figstyle.GREY)
    return figstyle.save(fig, "f1", out_dir)


def fig_f2(inputs: dict, out_dir: Path) -> List[Path]:
    """F2: how long adverse selection lasts, on a sample that does not shrink with the horizon."""
    frame = inputs["frame"]
    cols = ["mo_usd_{}".format(h) for h in HORIZONS]
    balanced = frame[np.isfinite(frame[cols]).all(axis=1)]
    professional = balanced["taker_class"].isin(PROFESSIONAL)
    premium = _premium(balanced)
    x = np.arange(len(HORIZONS))

    fig, axes = figstyle.figure(figstyle.DOUBLE, 2.6, ncols=3, gridspec_kw={"wspace": 0.30})
    units = [("USDC per contract", lambda h: balanced["mo_usd_{}".format(h)]),
             ("vol points", lambda h: balanced["mo_vol_{}".format(h)]),
             ("share of premium, %", lambda h: 100.0 * balanced["mo_usd_{}".format(h)] / premium)]
    for ax, (label, getter) in zip(axes, units):
        for name, mask, color, style in (("professional flow", professional, figstyle.PALETTE[1], "--"),
                                         ("other flow", ~professional, figstyle.PALETTE[0], "-")):
            med, lo, hi = [], [], []
            for h in HORIZONS:
                values = getter(h)[mask].to_numpy(float)
                values = values[np.isfinite(values)]
                if len(values) == 0:
                    med.append(np.nan), lo.append(np.nan), hi.append(np.nan)
                    continue
                med.append(float(np.median(values)))
                lo.append(float(np.percentile(values, 25)))
                hi.append(float(np.percentile(values, 75)))
            ax.fill_between(x, lo, hi, color=color, alpha=0.15, lw=0)
            ax.plot(x, med, style, color=color, marker="o", ms=3, label=name)
        full = [float(np.nanmedian(frame["mo_usd_{}".format(h)] if label.startswith("USDC") else
                                   frame["mo_vol_{}".format(h)] if label == "vol points" else
                                   100.0 * frame["mo_usd_{}".format(h)] / _premium(frame))) for h in HORIZONS]
        ax.plot(x, full, "-", color=figstyle.GREY, lw=0.8, label="full sample")
        ax.axhline(0, color="black", lw=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(HORIZONS, fontsize=6.5)
        ax.set_ylabel(label)
        ax.set_xlabel("horizon")
    axes[0].legend(loc="best", fontsize=6.5)
    _panel_tag(axes[0], "a  {:,} fills with every horizon".format(len(balanced)).replace(",", " "))
    _panel_tag(axes[1], "b  poolable unit")
    _panel_tag(axes[2], "c  what it is worth")
    return figstyle.save(fig, "f2", out_dir)


def fig_f3(inputs: dict, out_dir: Path) -> List[Path]:
    """F3: who takes back which part of the spread, and how few wallets that is."""
    frame, results = inputs["frame"], inputs["results"]
    classes = _class_rows(results)
    stats = frame.groupby("taker_class").agg(hs=("hs", "median"), as_usd=("as_usd", "median"),
                                             vol=("y_vol", "median"), mean=("y_usd", "mean"))
    lorenz = results.get("lorenz", pd.DataFrame())
    top10 = set(lorenz.nsmallest(10, "loss")["wallet"]) if {"wallet", "loss"} <= set(lorenz.columns) else set()

    fig = plt.figure(figsize=(figstyle.DOUBLE, 3.4))
    figstyle.use_style()
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.5], height_ratios=[2.2, 1.0], hspace=0.55, wspace=0.28)
    a, b, c = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[:, 1]), fig.add_subplot(gs[1, 0])
    for ax in (a, b, c):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    ladder = classes.sort_values("fills")
    a.barh(np.arange(len(ladder)), ladder["fills"], color=[figstyle.CLASS_COLORS[c] for c in ladder["class"]],
           edgecolor="black", lw=0.4)
    a.set_yticks(np.arange(len(ladder)))
    a.set_yticklabels([figstyle.CLASS_LABELS[c] for c in ladder["class"]], fontsize=6.5)
    a.set_xscale("log")
    a.set_xlabel("fills, log scale")
    _panel_tag(a, "a  the cascade, first match wins")

    pos = np.arange(len(classes))
    for i, (_, r) in enumerate(classes.iterrows()):
        name = r["class"]
        hs = float(stats.loc[name, "hs"]) if name in stats.index else np.nan
        adverse = float(stats.loc[name, "as_usd"]) if name in stats.index else np.nan
        b.barh(i, hs, color=figstyle.CLASS_COLORS[name], edgecolor="black", lw=0.5)
        b.barh(i, adverse, left=hs, color=figstyle.CLASS_COLORS[name], alpha=0.45, hatch="///",
               edgecolor="black", lw=0.5)
        b.plot([float(r["mean"])], [i], "o", mfc="none", color="black", ms=4)
        if int(r["clusters"]) < 40:
            b.axhspan(i - 0.45, i + 0.45, color=figstyle.GREY, alpha=0.12, lw=0, zorder=0)
        b.text(b.get_xlim()[1], i, "  G {:,}   p {:.3f}".format(int(r["clusters"]), float(r["p"])).replace(",", " "),
               va="center", fontsize=6.5)
    b.axvline(0, color="black", lw=0.6)
    b.set_yticks(pos)
    b.set_yticklabels([figstyle.CLASS_LABELS[c] for c in classes["class"]], fontsize=7)
    b.set_xlabel("median half spread and adverse selection, USDC per contract")
    b.legend(handles=[Patch(facecolor=figstyle.GREY, edgecolor="black", label="half spread"),
                      Patch(facecolor=figstyle.GREY, alpha=0.45, hatch="///", edgecolor="black",
                            label="adverse selection"),
                      Line2D([], [], marker="o", mfc="none", color="black", ls="none", label="mean markout")],
             loc="lower right", fontsize=6.5)
    _panel_tag(b, "b  shaded rows carry fewer than 40 wallets")

    if top10:
        shares = []
        for name in ("dominant_maker", "mm_programme"):
            sub = frame[frame["taker_class"] == name]
            shares.append(100.0 * float(sub["taker_wallet"].isin(top10).mean()) if len(sub) else np.nan)
        c.plot(shares, [1, 0], "o", color=figstyle.PALETTE[1], ms=5)
        for value, y in zip(shares, [1, 0]):
            if np.isfinite(value):
                c.text(value, y, "  {:.1f} %".format(value), va="center", fontsize=6.5)
        c.set_yticks([0, 1])
        c.set_yticklabels([figstyle.CLASS_LABELS["mm_programme"], figstyle.CLASS_LABELS["dominant_maker"]],
                          fontsize=6.5)
        c.set_xlim(0, 115)
        c.set_ylim(-0.6, 1.6)
    c.set_xlabel("share of the class' fills from the ten loss wallets, %")
    _panel_tag(c, "c  the same wallets as H1")
    return figstyle.save(fig, "f3", out_dir)


def fig_f4(inputs: dict, out_dir: Path) -> List[Path]:
    """F4: the concentration behind H1, and the two coefficients on which H1 actually fails."""
    results, frame = inputs["results"], inputs["frame"]
    lorenz = results["lorenz"]
    summary = results["summary"]
    h1 = summary["H1"]

    fig = plt.figure(figsize=(figstyle.SINGLE, 4.2))
    figstyle.use_style()
    gs = fig.add_gridspec(3, 1, height_ratios=[2.4, 0.5, 1.5], hspace=0.75)
    a, strip, b = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    for ax in (a, b):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    share, loss = lorenz["wallet_share"].to_numpy(float), lorenz["loss_share"].to_numpy(float)
    a.plot(np.concatenate([[0], share]), np.concatenate([[0], loss]), color=figstyle.PALETTE[0])
    a.plot([0, 1], [0, 1], color=figstyle.GREY, lw=0.7, ls=":")
    a.axhline(0.5, color="black", lw=0.8, ls="--")
    a.text(0.55, 0.52, "H1 rejection threshold, 50 %", fontsize=6.5)
    top_share = float(h1["top10_share"]["share"])
    top_x = 10.0 / max(int(h1["top10_share"]["wallets"]), 1)
    a.plot([top_x], [top_share], "o", color=figstyle.PALETTE[1], ms=5)
    a.annotate("top ten wallets\n{:.1f} % [{:.1f}, {:.1f}]".format(100 * top_share,
                                                                  100 * float(h1["top10_share"]["lo"]),
                                                                  100 * float(h1["top10_share"]["hi"])),
               xy=(top_x, top_share), xytext=(0.25, 0.68), fontsize=6.5,
               arrowprops=dict(arrowstyle="->", lw=0.6))
    a.axhspan(float(h1["top10_share"]["lo"]), float(h1["top10_share"]["hi"]), color=figstyle.PALETTE[1],
              alpha=0.12, lw=0)
    a.set_xlim(0, 1)
    a.set_ylim(0, 1.02)
    a.set_xlabel("share of loss-making taker wallets")
    a.set_ylabel("share of the maker's loss")
    _panel_tag(a, "a  concentration")

    worst = lorenz.nsmallest(10, "loss") if "loss" in lorenz else lorenz.head(10)
    composition = frame[frame["taker_wallet"].isin(set(worst["wallet"]))]["taker_class"].value_counts(normalize=True) \
        if "wallet" in worst else pd.Series(dtype=float)
    left = 0.0
    for name in figstyle.CLASS_ORDER:
        value = float(composition.get(name, 0.0))
        if value <= 0:
            continue
        strip.barh(0, value, left=left, color=figstyle.CLASS_COLORS[name], edgecolor="black", lw=0.4)
        if value > 0.12:
            strip.text(left + value / 2, 0, figstyle.CLASS_LABELS[name], ha="center", va="center", fontsize=6.5)
        left += value
    strip.set_xlim(0, 1)
    strip.set_yticks([])
    strip.set_xticks([])
    for spine in strip.spines.values():
        spine.set_visible(False)
    strip.set_xlabel("what the ten wallets are classified as", fontsize=6.5)

    raw_size = float(frame.loc[frame["size_above_p90"], "y_dn"].mean() - frame.loc[~frame["size_above_p90"], "y_dn"].mean())
    raw_sweep = float(frame.loc[frame["is_sweep"], "y_dn"].mean() - frame.loc[~frame["is_sweep"], "y_dn"].mean())
    pairs = [("size above p90", raw_size, float(h1["size_coefficient"]["beta"]), float(h1["size_coefficient"]["t"])),
             ("sweep", raw_sweep, float(h1["sweep_coefficient"]["beta"]), float(h1["sweep_coefficient"]["t"]))]
    for i, (name, raw, controlled, t) in enumerate(pairs):
        b.plot([raw], [i], "o", mfc="none", color=figstyle.PALETTE[1], ms=5)
        b.plot([controlled], [i], "o", color=figstyle.PALETTE[0], ms=5)
        b.plot([raw, controlled], [i, i], color=figstyle.GREY, lw=0.7)
        b.text(controlled, i + 0.28, "t {:.2f}".format(t), fontsize=6.5, ha="center")
    b.axvline(0, color="black", lw=0.6)
    b.set_yticks(range(len(pairs)))
    b.set_yticklabels([p[0] for p in pairs], fontsize=7)
    b.set_xlabel("difference in markout, USDC per contract")
    b.legend(handles=[Line2D([], [], marker="o", mfc="none", color=figstyle.PALETTE[1], ls="none", label="raw"),
                      Line2D([], [], marker="o", color=figstyle.PALETTE[0], ls="none",
                             label="instrument x day fixed effects")], loc="best", fontsize=6.5)
    _panel_tag(b, "b  why H1 fails")
    fig.text(0.02, 0.005, "wallets can hold several addresses, so the concentration is a lower bound",
             fontsize=6.0, color=figstyle.GREY)
    return figstyle.save(fig, "f4", out_dir)


def fig_f5(inputs: dict, out_dir: Path) -> List[Path]:
    """F5: where the edge survives -- in the unit a bot decides on, and with the registered verdict beside it."""
    frame, results = inputs["frame"], inputs["results"]
    cells = results["cells"]
    currencies = [c for c in ("BTC", "ETH", "HYPE") if (cells["currency"] == c).any()]
    edge_bp = frame.assign(bp=1e4 * frame["net_edge"] / frame["notional"].replace(0, np.nan))

    fig = plt.figure(figsize=(figstyle.DOUBLE, 4.0))
    figstyle.use_style()
    gs = fig.add_gridspec(2, len(currencies) + 1, width_ratios=[1] * len(currencies) + [0.85],
                          hspace=0.55, wspace=0.35)
    for col, ccy in enumerate(currencies):
        values, counts = figdata.cell_matrix(edge_bp[edge_bp["currency"] == ccy], "bp", stat="median")
        ax = fig.add_subplot(gs[0, col])
        ax.imshow(values.to_numpy(float), cmap="Greys", aspect="auto")
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                v = values.to_numpy(float)[i, j]
                if np.isfinite(v):
                    ax.text(j, i, "{:.1f}".format(v), ha="center", va="center", fontsize=6.5,
                            color="white" if v > np.nanpercentile(values.to_numpy(float), 70) else "black")
        ax.set_xticks(range(values.shape[1]))
        ax.set_xticklabels(values.columns, rotation=45, ha="right", fontsize=6)
        ax.set_yticks(range(values.shape[0]))
        ax.set_yticklabels(values.index if col == 0 else [], fontsize=6)
        _panel_tag(ax, ccy)
        if col == 0:
            ax.set_ylabel("tenor")

        sub = cells[cells["currency"] == ccy]
        ax2 = fig.add_subplot(gs[1, col])
        rows = [t for t in TENOR_LABELS if (sub["tenor_bucket"] == t).any()]
        colsb = [d for d in DELTA_LABELS if (sub["delta_bucket"] == d).any()]
        for i, t in enumerate(rows):
            for j, d in enumerate(colsb):
                r = sub[(sub["tenor_bucket"] == t) & (sub["delta_bucket"] == d)]
                if r.empty:
                    ax2.plot(j, i, "x", color=figstyle.GREY, ms=4)
                    continue
                r = r.iloc[0]
                if bool(r["positive"]):
                    ax2.plot(j, i, "^", color=figstyle.PALETTE[0], ms=5)
                elif bool(r["negative"]):
                    ax2.plot(j, i, "v", color=figstyle.PALETTE[1], ms=5)
                else:
                    ax2.plot(j, i, "o", mfc="none", color=figstyle.GREY, ms=4)
        ax2.set_xticks(range(len(colsb)))
        ax2.set_xticklabels(colsb, rotation=45, ha="right", fontsize=6)
        ax2.set_yticks(range(len(rows)))
        ax2.set_yticklabels(rows if col == 0 else [], fontsize=6)
        ax2.set_xlabel("|delta|, %")
        ax2.invert_yaxis()
        ax2.set_ylim(len(rows) - 0.5, -0.5)
        if col == 0:
            ax2.set_ylabel("tenor")

    legend_ax = fig.add_subplot(gs[0, -1])
    legend_ax.axis("off")
    legend_ax.legend(handles=[Line2D([], [], marker="^", color=figstyle.PALETTE[0], ls="none", label="positive"),
                              Line2D([], [], marker="o", mfc="none", color=figstyle.GREY, ls="none",
                                     label="inconclusive"),
                              Line2D([], [], marker="v", color=figstyle.PALETTE[1], ls="none", label="negative"),
                              Line2D([], [], marker="x", color=figstyle.GREY, ls="none", label="under 200 fills")],
                     loc="center", fontsize=6.5, title="registered net edge", title_fontsize=6.5)

    sens = results["sensitivity"]
    ax3 = fig.add_subplot(gs[1, -1])
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)
    ax3.plot(sens["half_spread_bp"], 100 * sens["share_positive"], "-o", color=figstyle.PALETTE[0], ms=4)
    ax3.axhline(50, color="black", lw=0.8, ls="--")
    ax3.text(sens["half_spread_bp"].max(), 51, "H4 threshold", ha="right", fontsize=6.5)
    for _, r in sens.iterrows():
        ax3.text(r["half_spread_bp"], 100 * r["share_positive"] + 2, "{:.1f}".format(100 * r["share_positive"]),
                 ha="center", fontsize=6.5)
    ax3.set_xlabel("assumed perp half spread, bp")
    ax3.set_ylabel("cells positive, %")
    _panel_tag(ax3, "the verdict turns here")
    fig.text(0.005, 0.5, "top: median net edge, bp of notional     bottom: registered net edge, USDC",
             rotation=90, va="center", fontsize=6.0, color=figstyle.GREY)
    return figstyle.save(fig, "f5", out_dir)


def fig_f6(inputs: dict, out_dir: Path) -> List[Path]:
    """F6: is this one market or two, and what does the only event study in the paper show?"""
    frame, results = inputs["frame"], inputs["results"]
    summary = results["summary"]
    month = pd.to_datetime(frame["ts"], unit="ms", utc=True).dt.tz_localize(None).dt.to_period("M")
    f = frame.assign(month=month)
    lorenz = results.get("lorenz", pd.DataFrame())
    top10 = set(lorenz.nsmallest(10, "loss")["wallet"]) if {"wallet", "loss"} <= set(lorenz.columns) else set()

    fig = plt.figure(figsize=(figstyle.DOUBLE, 4.2))
    figstyle.use_style()
    gs = fig.add_gridspec(3, 1, height_ratios=[1.3, 1.1, 1.1], hspace=0.65)
    a, b, c = (fig.add_subplot(gs[i]) for i in range(3))
    for ax in (a, b, c):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    months = sorted(f["month"].unique())
    x = np.arange(len(months))
    index = {m: i for i, m in enumerate(months)}
    for ccy, style in zip(("BTC", "ETH", "HYPE"), ["-", "--", ":"]):
        sub = f[f["currency"] == ccy]
        if sub.empty:
            continue
        series = sub.groupby("month")["y_vol"].median()
        counts = sub.groupby("month")["y_vol"].size()
        xs = [index[m] for m in series.index]
        a.plot(xs, series.to_numpy(float), style, color=figstyle.PALETTE[list("BTC ETH HYPE".split()).index(ccy)],
               marker="o", ms=2.5, label=ccy)
        thin = [i for i, m in zip(xs, series.index) if counts.get(m, 0) < 1000]
        a.plot(thin, series.reindex([months[i] for i in thin]).to_numpy(float), "o", color="white",
               mec=figstyle.GREY, ms=3, zorder=5)
    a.axhline(0, color="black", lw=0.6)
    a.set_ylabel("median markout,\nvol points")
    a.legend(loc="best", fontsize=6.5, ncol=3)
    _panel_tag(a, "a  hollow markers: under 1 000 fills that month")

    composition = (f.groupby(["month", "taker_class"]).size().unstack(fill_value=0))
    composition = composition.div(composition.sum(axis=1), axis=0)
    bottom = np.zeros(len(composition))
    for name in figstyle.CLASS_ORDER:
        if name not in composition:
            continue
        b.fill_between(np.arange(len(composition)), bottom, bottom + composition[name].to_numpy(float),
                       color=figstyle.CLASS_COLORS[name], lw=0, label=figstyle.CLASS_LABELS[name])
        bottom = bottom + composition[name].to_numpy(float)
    if top10:
        top_share = f.assign(top=f["taker_wallet"].isin(top10)).groupby("month")["top"].mean()
        b.plot(np.arange(len(top_share)), top_share.to_numpy(float), color="black", lw=1.0,
               label="ten loss wallets")
    b.set_ylim(0, 1)
    b.set_ylabel("share of fills")
    b.legend(loc="upper left", fontsize=6.0, ncol=4)
    _panel_tag(b, "b  the sample changes composition")

    did = summary["H3"]["did"]
    event = pd.Timestamp(did["event_ms"], unit="ms").to_period("M")
    treated = did.get("treated", "HYPE")
    gap = []
    for m in months:
        sub = f[f["month"] == m]
        t = sub.loc[sub["currency"] == treated, "y_vol"]
        ctrl = sub.loc[sub["currency"] != treated, "y_vol"]
        gap.append(float(t.mean() - ctrl.mean()) if len(t) and len(ctrl) else np.nan)
    gap = np.array(gap)
    pre = gap[[i for i, m in enumerate(months) if m < event]]
    pre = pre[np.isfinite(pre)]
    if len(pre):
        lo, hi = np.percentile(pre, [5, 95])
        c.axhspan(lo, hi, color=figstyle.GREY, alpha=0.18, lw=0, label="placebo spread, pre-event months")
    c.plot(x, gap, "-o", color=figstyle.PALETTE[0], ms=3, label="{} minus controls".format(treated))
    if event in index:
        c.axvline(index[event], color="black", lw=0.9)
        c.text(index[event], c.get_ylim()[1], " event", fontsize=6.5, va="top")
    c.axhline(0, color="black", lw=0.6)
    c.set_ylabel("difference,\nvol points")
    c.text(0.01, 0.06, "difference in differences {:+.3f} vol points, t {:.2f}, p {:.3f}; "
                       "{:.0f} % of {:d} placebos more extreme".format(
                           float(did["beta"]), float(did["t"]), float(did["p"]),
                           100 * float(did["placebo_share_more_extreme"]), int(did["placebos"])),
           transform=c.transAxes, fontsize=6.5)
    c.legend(loc="upper left", fontsize=6.0)
    _panel_tag(c, "c  H3: the estimate sits inside the placebo spread")

    ticks = [i for i in range(0, len(months), max(1, len(months) // 10))]
    for ax in (a, b, c):
        ax.set_xlim(-0.5, len(months) - 0.5)
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(months[i]) for i in ticks], fontsize=6, rotation=45, ha="right")
    return figstyle.save(fig, "f6", out_dir)


def fig_a1(inputs: dict, out_dir: Path) -> List[Path]:
    """A1: is the on-chain mark good enough to carry the measurement?"""
    frame, results = inputs["frame"], inputs["results"]
    fig, axes = figstyle.figure(figstyle.DOUBLE, 3.2, ncols=3, gridspec_kw={"wspace": 0.34})
    a, b, c = axes

    age = frame["svi_age_s_t"].to_numpy(float)
    lag = frame["lag_a_30m_s"].to_numpy(float)
    bins = np.logspace(0, 6, 40)
    a.hist(age[np.isfinite(age) & (age > 0)], bins=bins, color=figstyle.PALETTE[0], alpha=0.65,
           label="age of the curve at the fill")
    a.hist(lag[np.isfinite(lag) & (lag > 0)], bins=bins, color=figstyle.PALETTE[1], alpha=0.55,
           label="distance of the next fill")
    a.axvline(1800, color="black", lw=0.9, ls="--")
    a.text(1800, a.get_ylim()[1] * 0.9, " 30 min", fontsize=6.5)
    a.set_xscale("log")
    a.set_xlabel("seconds, log scale")
    a.set_ylabel("fills")
    a.legend(loc="upper left", fontsize=6.0)
    _panel_tag(a, "a  path (a) is no control at 30 min")

    bucket = pd.cut(frame["svi_age_s_t"], AGE_EDGES, labels=AGE_LABELS, right=False)
    means, los, his, ns = [], [], [], []
    for label in AGE_LABELS:
        sub = frame[bucket == label]
        ci = _ci(sub["y_usd"].to_numpy(float), sub["cluster"].to_numpy()) if len(sub) else {"mean": np.nan,
                                                                                            "lo": np.nan,
                                                                                            "hi": np.nan, "n": 0}
        means.append(ci["mean"]), los.append(ci["lo"]), his.append(ci["hi"]), ns.append(int(ci["n"]))
    pos = np.arange(len(AGE_LABELS))
    b.errorbar(pos, means, yerr=[np.subtract(means, los), np.subtract(his, means)], fmt="o",
               color=figstyle.PALETTE[0], ms=4, lw=0.8, capsize=2)
    for i, n in enumerate(ns):
        b.text(i, b.get_ylim()[0], "{:,}".format(n).replace(",", " "), fontsize=5.5, rotation=90, va="bottom",
               ha="center", color=figstyle.GREY)
    b.set_xticks(pos)
    b.set_xticklabels(AGE_LABELS, rotation=45, ha="right", fontsize=6)
    b.set_xlabel("age of the curve at the fill, s")
    b.set_ylabel("mean markout, USDC per contract")
    _panel_tag(b, "b  a flat line is the reassurance")

    basis = 1e4 * (frame["fwd_t"] / frame["index_price"] - 1.0)
    tenor = basis.groupby(frame["tenor_bucket"]).mean()
    tenor = tenor.reindex([t for t in TENOR_LABELS if t in tenor.index])
    c.barh(np.arange(len(tenor)), tenor.to_numpy(float), color=figstyle.PALETTE[2], edgecolor="black", lw=0.5)
    c.set_yticks(np.arange(len(tenor)))
    c.set_yticklabels(tenor.index, fontsize=6.5)
    c.axvline(0, color="black", lw=0.6)
    c.set_xlabel("curve forward over index, bp")
    _panel_tag(c, "c  the frozen forward")

    paths = results.get("paths", pd.DataFrame())
    if len(paths):
        row = paths[paths["group"] == "lag_a <= 300 s"]
        if len(row):
            fig.text(0.005, 0.01, "paths agree once the comparison is fair: correlation {:.3f} when the next fill is "
                                  "within 300 s, {:.3f} overall".format(
                                      float(row["correlation"].iloc[0]),
                                      float(paths.loc[paths["group"] == "all", "correlation"].iloc[0])),
                     fontsize=6.0, color=figstyle.GREY)
    return figstyle.save(fig, "a1", out_dir)


FIGURES = {"T1": fig_t1, "T2": fig_t2, "F1": fig_f1, "F2": fig_f2, "F3": fig_f3,
           "F4": fig_f4, "F5": fig_f5, "F6": fig_f6, "A1": fig_a1}


# ------------------------------------------------------------------------------------------------ driver

def load_inputs(root, results_dir) -> dict:
    """The analysis frame, the registered results and, if present, the on-chain curves of one month."""
    from .inference_p1 import analysis_frame

    root = Path(root)
    markouts = pd.read_parquet(root / "derived" / "markouts.parquet")
    funding = pd.read_parquet(root / "ref" / "funding_history.parquet")
    frame = analysis_frame(markouts, funding)
    results = figdata.load_results(results_dir)
    svi = pd.DataFrame()
    volfeed = root / "volfeed"
    if volfeed.is_dir():
        newest = sorted(volfeed.glob("BTC_svi_*.parquet"))
        if newest:
            svi = pd.read_parquet(newest[-1])
    return {"frame": frame, "results": results, "svi": svi}


def build(root, results_dir, out_dir, only: Sequence[str] = None) -> Dict[str, List[Path]]:
    """Draw every figure, or the subset named in ``only``, into ``out_dir``."""
    names = list(FIGURES) if only is None else [n.strip() for n in only]
    unknown = [n for n in names if n not in FIGURES]
    if unknown:
        raise KeyError("unknown figure(s): {}; known: {}".format(", ".join(unknown), ", ".join(sorted(FIGURES))))
    inputs = load_inputs(root, results_dir)
    out_dir = Path(out_dir)
    written = {}
    for name in names:
        written[name] = FIGURES[name](inputs, out_dir)
    return written
