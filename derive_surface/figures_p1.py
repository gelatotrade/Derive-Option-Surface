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
CASCADE = ["vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]   # classify_fills, first match wins
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
    ax.annotate(text, xy=(0.02 if align == "left" else 0.98, y), xycoords="axes fraction",
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
    frame = inputs["frame"]
    row = figdata.example_fill(frame, taker_class="other", horizon="30m")
    side = float(row["maker_side"])
    price = float(row["price"])
    short = ["1m", "5m", "30m"]                    # panels a and b stop at the registered horizon
    xs = np.arange(len(short) + 1, dtype=float)
    marks = [float(row["mark_b_t"])] + [float(row["mark_b_{}".format(h)]) for h in short]
    ivs = [float(row["iv_mark_t"])] + [float(row["iv_b_{}".format(h)]) for h in short]
    xl = np.arange(len(HORIZONS) + 1, dtype=float)
    raw = [0.0] + [side * (float(row["mark_b_{}".format(h)]) - price) for h in HORIZONS]
    neutral = [0.0] + [float(row["mo_dn_{}".format(h)]) for h in HORIZONS]

    near = frame[(frame["currency"] == row["currency"]) & (frame["delta_bucket"] == row["delta_bucket"])
                 & (frame["tenor_bucket"] == row["tenor_bucket"])]
    near = near.reindex((near["ts"] - row["ts"]).abs().sort_values().index[:100])
    band_lo = [0.0] + [float(np.nanpercentile(near["mo_usd_{}".format(h)], 25)) for h in HORIZONS]
    band_hi = [0.0] + [float(np.nanpercentile(near["mo_usd_{}".format(h)], 75)) for h in HORIZONS]

    fig, axes = figstyle.figure(figstyle.DOUBLE, 2.9, ncols=3, gridspec_kw={"wspace": 0.42})
    fig.subplots_adjust(left=0.085, right=0.985, top=0.88, bottom=0.24)
    a, b, c = axes

    a.plot(xs, marks, "-o", color=figstyle.PALETTE[0], ms=3.5, label="mark, on-chain SVI curve")
    a.axhline(price, color=figstyle.PALETTE[1], ls="--", lw=1.0, label="fill price")
    half = side * (marks[0] - price)
    adverse = side * (marks[3] - marks[0])
    lo, hi = min(min(marks), price), max(max(marks), price)
    pad = 0.18 * (hi - lo if hi > lo else 1.0)
    a.set_ylim(lo - pad, hi + pad)
    xb = len(short) + 0.30                          # two brackets side by side, never stacked on one line
    a.annotate("", xy=(xb, marks[0]), xytext=(xb, price), arrowprops=dict(arrowstyle="<->", lw=0.7, color="black"))
    a.text(xb + 0.10, marks[0] if half > 0 else price, "half spread\n{:+.2f}".format(half), fontsize=6.5,
           va="bottom")
    xc = xb + 1.05
    a.annotate("", xy=(xc, marks[3]), xytext=(xc, marks[0]),
               arrowprops=dict(arrowstyle="<->", lw=0.7, color=figstyle.PALETTE[2]))
    a.text(xc + 0.10, 0.5 * (marks[3] + marks[0]), "adverse selection\n{:+.2f}".format(adverse),
           fontsize=6.5, va="center", color=figstyle.PALETTE[2])
    a.set_xlim(-0.25, xc + 1.45)
    a.set_ylabel("price, USDC per contract")
    a.legend(loc="lower left", fontsize=6.0)
    _panel_tag(a, "a")

    b.plot(xs, ivs, "-o", color=figstyle.PALETTE[0], ms=3.5)
    b.axhline(float(row["iv_fill"]), color=figstyle.PALETTE[1], ls="--", lw=1.0)
    b.set_ylabel("implied volatility")
    _panel_tag(b, "b")

    c.fill_between(xl, band_lo, band_hi, color=figstyle.GREY, alpha=0.20, lw=0, label="p25-p75, 100 nearest fills")
    c.plot(xl, raw, "-o", color=figstyle.PALETTE[0], ms=3, label="markout")
    c.plot(xl, neutral, "--s", color=figstyle.PALETTE[2], ms=3, mfc="none", label="delta neutral")
    c.fill_between(xl, raw, neutral, hatch="///", facecolor="none", edgecolor=figstyle.PALETTE[2], lw=0.0, alpha=0.6)
    c.axhline(0, color="black", lw=0.6)
    c.set_ylabel("markout, USDC per contract")
    c.legend(loc="lower left", fontsize=6.0)
    _panel_tag(c, "c")

    for ax, ticks, names in ((a, xs, ["fill"] + short), (b, xs, ["fill"] + short), (c, xl, ["fill"] + HORIZONS)):
        ax.set_xticks(ticks)
        ax.set_xticklabels(names, fontsize=6.5)
        ax.set_xlabel("time after the fill")
    fig.text(0.5, 0.985, "{}, maker {}, {:,.2f} contracts".format(
        row["instrument_name"], "sold" if side < 0 else "bought", float(row["amount"])).replace(",", " "),
        ha="center", fontsize=6.0, color=figstyle.GREY)
    return figstyle.save(fig, "t1", out_dir)


def fig_t2(inputs: dict, out_dir: Path) -> List[Path]:
    """T2: the identity that turns a half spread into a net edge, and where the fee eats the premium."""
    frame = inputs["frame"]
    steps = figdata.waterfall_components(frame)
    cols = {"half spread": ("hs", 1.0), "adverse selection": ("as_usd", 1.0), "maker fee": ("fee_maker", -1.0),
            "maker rebate": ("rebate_maker", 1.0), "hedge cost": ("hedge", -1.0)}
    intervals = {}
    for name, (col, sign) in cols.items():
        ci = _ci(sign * frame[col].to_numpy(float), frame["cluster"].to_numpy())
        intervals[name] = (ci["mean"] - ci["lo"], ci["hi"] - ci["mean"])
    markout = _ci(frame["y_usd"].to_numpy(float), frame["cluster"].to_numpy())
    net = _ci(frame["net_edge"].to_numpy(float), frame["cluster"].to_numpy())
    intervals["markout"] = (markout["mean"] - markout["lo"], markout["hi"] - markout["mean"])
    intervals["net edge"] = (net["mean"] - net["lo"], net["hi"] - net["mean"])

    order = ["half spread", "adverse selection", "markout", "maker fee", "maker rebate", "hedge cost", "net edge"]
    values = dict(zip(steps["step"], steps["value"]))
    values["markout"], values["net edge"] = markout["mean"], net["mean"]

    fig = plt.figure(figsize=(figstyle.DOUBLE, 3.1))
    figstyle.use_style()
    gs = fig.add_gridspec(1, 2, width_ratios=[1.3, 1.0], wspace=0.26,
                          left=0.075, right=0.985, top=0.90, bottom=0.20)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    for ax in (a, b):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    running, tops = 0.0, []
    for i, name in enumerate(order):
        value = values[name]
        total = name in ("markout", "net edge")
        bottom = 0.0 if total else running
        color = figstyle.GREY if total else (figstyle.PALETTE[0] if value >= 0 else figstyle.PALETTE[1])
        a.bar(i, value, bottom=bottom, color=color, edgecolor="black",
              lw=1.1 if name == "hedge cost" else 0.6, ls=":" if name == "hedge cost" else "-",
              hatch="///" if (value < 0 and not total) else None)
        top = bottom + value
        down, up = intervals[name]
        a.plot([i, i], [top - down, top + up], color="black", lw=0.7)
        a.plot([i - 0.12, i + 0.12], [top - down] * 2, color="black", lw=0.7)
        a.plot([i - 0.12, i + 0.12], [top + up] * 2, color="black", lw=0.7)
        if value >= 0:
            a.text(i, top + up + 0.7, "{:+.2f}".format(value), ha="center", fontsize=6.5)
        else:                                       # a falling step would print its label inside the hatch
            a.text(i, bottom + value - down - 1.5, "{:+.2f}".format(value), ha="center", va="top", fontsize=6.5)
        tops.append(top + up)
        if not total:
            running += value
    a.axhline(0, color="black", lw=0.6)
    a.set_ylim(min(0.0, float(np.min(list(values.values()))) - 2), max(tops) * 1.14)
    a.set_xticks(range(len(order)))
    a.set_xticklabels([o.replace(" ", "\n") for o in order], fontsize=6.5)
    a.set_ylabel("mean per contract, USDC")
    _side_note(a, "median half spread {:+.2f}: medians are not additive".format(float(frame["hs"].median())), 0.04)
    a.legend(handles=[Patch(facecolor="white", edgecolor="black", ls=":", label="modelled, not observed")],
             loc="upper right", fontsize=6.0)
    _panel_tag(a, "a")

    premium = _premium(frame)
    grid = np.logspace(-3, 3, 240)
    for label, col, style, colour in (("maker", "fee_maker", "-", figstyle.PALETTE[0]),
                                      ("taker", "fee_taker", "--", figstyle.PALETTE[1])):
        share = (100.0 * frame[col] / premium).to_numpy(float)
        share = share[np.isfinite(share)]
        b.plot(grid, [float(np.mean(share <= g)) for g in grid], style, color=colour, label=label)
        if label == "maker":
            zero = float(np.mean(share <= 0))
            b.annotate("{:.0f} % of fills pay\nno maker fee".format(100 * zero), xy=(2e-3, zero),
                       xytext=(1.3e-3, min(zero + 0.22, 0.95)), fontsize=6.5,
                       arrowprops=dict(arrowstyle="->", lw=0.5))
        else:
            b.annotate("{:.1f} % pay more fee\nthan premium".format(100 * float(np.mean(share > 100))),
                       xy=(3e2, 0.99), xytext=(6e0, 0.48), fontsize=6.5,
                       arrowprops=dict(arrowstyle="->", lw=0.5))
    b.axvline(12.5, color=figstyle.GREY, lw=0.8, ls=":")
    b.axvline(100, color="black", lw=0.8)
    b.text(12.5, 1.03, "12.5 %", fontsize=6.0, color=figstyle.GREY, ha="right")
    b.text(115, 1.03, "premium", fontsize=6.0, ha="left")
    b.set_xscale("log")
    b.set_xlim(1e-3, 1e3)
    b.set_ylim(0, 1.02)
    b.set_xlabel("fee as a share of the premium, %")
    b.set_ylabel("share of fills at or below")
    b.legend(loc="center left", fontsize=6.5)
    _panel_tag(b, "b")
    return figstyle.save(fig, "t2", out_dir)


def fig_f1(inputs: dict, out_dir: Path) -> List[Path]:
    """F1: the same finding in four readings, so the headline number cannot be misread."""
    frame = inputs["frame"]
    y = frame["y_usd"].to_numpy(float)
    finite = np.isfinite(y)
    y = y[finite]
    trimmed = np.sort(y)
    k = int(0.05 * len(trimmed))
    stats = [("median", float(np.median(y)), "-"),
             ("5 % trimmed", float(trimmed[k:len(trimmed) - k].mean()) if len(trimmed) > 2 * k else np.nan, "--"),
             ("mean", float(y.mean()), ":")]
    weights = frame.loc[finite, "amount"].to_numpy(float)
    contract_weighted = float(np.average(y, weights=weights)) if weights.sum() > 0 else np.nan

    fig, axes = figstyle.figure(figstyle.DOUBLE, 2.7, ncols=3, gridspec_kw={"wspace": 0.42})
    fig.subplots_adjust(left=0.075, right=0.985, top=0.90, bottom=0.26)
    a, b, c = axes

    core = 10.0
    bins = np.concatenate([-np.logspace(3, np.log10(core), 25), np.linspace(-core, core, 21),
                           np.logspace(np.log10(core), 3, 25)])
    a.hist(y, bins=bins, color=figstyle.PALETTE[0], alpha=0.8)
    a.set_xscale("symlog", linthresh=core)
    _symlog_core(a, core)
    for i, (label, value, style) in enumerate(stats):
        if not np.isfinite(value):
            continue
        a.axvline(value, color="black", ls=style, lw=1.0)
        a.annotate("{} {:.2f}".format(label, value), xy=(value, 1.0), xycoords=("data", "axes fraction"),
                   xytext=(3, -9 - 11 * i), textcoords="offset points", fontsize=6.5)
    a.set_xlabel("markout after 30 min, USDC per contract\nsymlog, shaded core linear, equal area per decade")
    a.set_ylabel("fills")
    _side_note(a, "contract weighted {:+.3f}".format(contract_weighted), 0.55, align="right")
    _panel_tag(a, "a")

    agg = (frame.assign(dollar=frame["y_usd"] * frame["amount"])
                .groupby("currency").agg(dollar=("dollar", "sum"), fills=("y_usd", "size"),
                                         index=("index_price", "mean")).reindex(["BTC", "ETH", "HYPE"]).dropna())
    pos = np.arange(len(agg))
    b.barh(pos, agg["dollar"] / 1e6, color=figstyle.PALETTE[0], edgecolor="black", lw=0.5)
    b.set_yticks(pos)
    b.set_yticklabels(agg.index)
    for i, (_, r) in enumerate(agg.iterrows()):
        b.text(r["dollar"] / 1e6 * 1.04, i, "{:.2f} m\nindex {:,.0f}".format(r["dollar"] / 1e6, r["index"])
               .replace(",", " "), va="center", fontsize=6.0)
    b.set_xlim(0, float(agg["dollar"].max()) / 1e6 * 1.75)
    b.set_xlabel("aggregate maker gain,\nmillion USDC")
    _panel_tag(b, "b")

    premium = _premium(frame)
    share = (100.0 * frame["y_usd"] / premium).to_numpy(float)
    share = share[np.isfinite(share)]
    q = np.percentile(share, [25, 50, 75])
    c.hist(share, bins=np.linspace(-100, 150, 60), color=figstyle.PALETTE[2], alpha=0.8)
    for i, (value, label, style) in enumerate(zip(q, ["q25", "median", "q75"], ["--", "-", "--"])):
        c.axvline(value, color="black", lw=0.9, ls=style)
        c.annotate("{} {:+.1f} %".format(label, value), xy=(value, 1.0), xycoords=("data", "axes fraction"),
                   xytext=(3, -9 - 11 * i), textcoords="offset points", fontsize=6.5)
    c.set_xlabel("markout as a share\nof the premium, %")
    c.set_ylabel("fills")
    _panel_tag(c, "c")
    return figstyle.save(fig, "f1", out_dir)


def fig_f2(inputs: dict, out_dir: Path) -> List[Path]:
    """F2: how long adverse selection lasts, on a sample that does not shrink with the horizon."""
    frame = inputs["frame"]
    cols = ["mo_usd_{}".format(h) for h in HORIZONS]
    balanced = frame[np.isfinite(frame[cols]).all(axis=1)]
    professional = balanced["taker_class"].isin(PROFESSIONAL)
    premium = _premium(balanced)
    x = np.arange(len(HORIZONS))
    draws = 249

    fig, axes = figstyle.figure(figstyle.DOUBLE, 2.7, ncols=3, gridspec_kw={"wspace": 0.34})
    fig.subplots_adjust(left=0.075, right=0.985, top=0.90, bottom=0.22)
    units = [("USDC per contract", lambda h, f, prem: f["mo_usd_{}".format(h)]),
             ("vol points", lambda h, f, prem: f["mo_vol_{}".format(h)]),
             ("share of premium, %", lambda h, f, prem: 100.0 * f["mo_usd_{}".format(h)] / prem)]
    for ax, (label, getter) in zip(axes, units):
        for name, mask, color, style in (("professional flow", professional, figstyle.PALETTE[1], "--"),
                                         ("other flow", ~professional, figstyle.PALETTE[0], "-")):
            sub, prem = balanced[mask], premium[mask]
            med, lo, hi = [], [], []
            for h in HORIZONS:
                values = getter(h, sub, prem).to_numpy(float)
                ok = np.isfinite(values)
                if ok.sum() == 0:
                    med.append(np.nan), lo.append(np.nan), hi.append(np.nan)
                    continue
                m, l, u = figdata._median_ci(values[ok], sub["cluster"].to_numpy()[ok], b=draws, seed=SEED)
                med.append(m), lo.append(l), hi.append(u)
            ax.fill_between(x, lo, hi, color=color, alpha=0.22, lw=0)
            ax.plot(x, med, style, color=color, marker="o", ms=3, label=name)
        full = [float(np.nanmedian(getter(h, frame, _premium(frame)))) for h in HORIZONS]
        ax.plot(x, full, "-", color=figstyle.GREY, lw=0.8, label="full sample, median")
        ax.axhline(0, color="black", lw=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(HORIZONS, fontsize=6.5)
        ax.set_ylabel(label)
        ax.set_xlabel("horizon")
    axes[0].legend(loc="center left", fontsize=6.0)
    _side_note(axes[2], "{:,} fills carry every horizon".format(len(balanced)).replace(",", " "), 0.06,
               align="right")
    for ax, letter in zip(axes, "abc"):
        _panel_tag(ax, letter)
    return figstyle.save(fig, "f2", out_dir)


def fig_f3(inputs: dict, out_dir: Path) -> List[Path]:
    """F3: who takes back which part of the spread, and how few wallets that is."""
    frame, results = inputs["frame"], inputs["results"]
    classes = _class_rows(results)
    stats = frame.groupby("taker_class").agg(hs_vol=("hs_vol", "median"), as_vol=("as_vol", "median"),
                                             mean_vol=("y_vol", "mean")) \
        if "hs_vol" in frame else None
    if stats is None:                                   # half spread and adverse selection in vol points
        scale = (frame["y_vol"] / frame["y_usd"].replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        work = frame.assign(hs_vol=frame["hs"] * scale, as_vol=frame["as_usd"] * scale)
        stats = work.groupby("taker_class").agg(hs_vol=("hs_vol", "median"), as_vol=("as_vol", "median"),
                                                mean_vol=("y_vol", "mean"))
    lorenz = results.get("lorenz", pd.DataFrame())
    top10 = set(lorenz.nsmallest(10, "loss")["wallet"]) if {"wallet", "loss"} <= set(lorenz.columns) else set()

    fig = plt.figure(figsize=(figstyle.DOUBLE, 3.3))
    figstyle.use_style()
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.55], height_ratios=[2.0, 1.0], hspace=0.85, wspace=0.42,
                          left=0.115, right=0.845, top=0.92, bottom=0.14)
    a, b, c = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[:, 1]), fig.add_subplot(gs[1, 0])
    for ax in (a, b, c):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    cascade = [c for c in CASCADE if (classes["class"] == c).any()]
    ladder = classes.set_index("class").loc[cascade]
    a.barh(np.arange(len(ladder))[::-1], ladder["fills"], color=[figstyle.CLASS_COLORS[c] for c in cascade],
           edgecolor="black", lw=0.4)
    a.set_yticks(np.arange(len(ladder))[::-1])
    a.set_yticklabels([figstyle.CLASS_LABELS[c] for c in cascade], fontsize=6.5)
    a.set_xscale("log")
    a.set_xlabel("fills, log scale")
    _panel_tag(a, "a")

    for i, (_, r) in enumerate(classes.iterrows()):
        name = r["class"]
        hs = float(stats.loc[name, "hs_vol"]) if name in stats.index else np.nan
        adverse = float(stats.loc[name, "as_vol"]) if name in stats.index else np.nan
        if int(r["clusters"]) < 40:
            b.axhspan(i - 0.45, i + 0.45, color=figstyle.GREY, alpha=0.13, lw=0, zorder=0)
        b.barh(i, hs, color=figstyle.CLASS_COLORS[name], edgecolor="black", lw=0.5)
        b.barh(i, adverse, left=hs, color=figstyle.CLASS_COLORS[name], alpha=0.45, hatch="///",
               edgecolor="black", lw=0.5)
        b.plot([float(r["mean_vol"])], [i], "o", mfc="none", color="black", ms=4)
        b.annotate("G {:,}   p {:.3f}".format(int(r["clusters"]), float(r["p"])).replace(",", " "),
                   xy=(1.02, i), xycoords=("axes fraction", "data"), va="center", fontsize=6.5)
    b.axvline(0, color="black", lw=0.6)
    b.set_yticks(np.arange(len(classes)))
    b.set_yticklabels([figstyle.CLASS_LABELS[c] for c in classes["class"]], fontsize=7)
    b.set_ylim(-0.6, len(classes) - 0.4)
    b.set_xlabel("median half spread and adverse selection, vol points")
    b.legend(handles=[Patch(facecolor=figstyle.GREY, edgecolor="black", label="half spread"),
                      Patch(facecolor=figstyle.GREY, alpha=0.45, hatch="///", edgecolor="black",
                            label="adverse selection"),
                      Line2D([], [], marker="o", mfc="none", color="black", ls="none", label="mean markout")],
             loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, fontsize=6.0)
    _panel_tag(b, "b")

    if top10:
        names = ["dominant_maker", "mm_programme"]
        shares = [100.0 * float(frame.loc[frame["taker_class"] == n, "taker_wallet"].isin(top10).mean())
                  if (frame["taker_class"] == n).any() else np.nan for n in names]
        c.barh([1, 0], shares, color=[figstyle.CLASS_COLORS[n] for n in names], edgecolor="black", lw=0.4)
        for value, y in zip(shares, [1, 0]):
            if np.isfinite(value):
                c.text(value - 3, y, "{:.1f} %".format(value), va="center", ha="right", fontsize=6.5, color="white")
        c.set_yticks([0, 1])
        c.set_yticklabels([figstyle.CLASS_LABELS[n] for n in names[::-1]], fontsize=6.5)
        c.set_xlim(0, 100)
    c.set_xlabel("share of the class' fills\nfrom the ten loss wallets, %", fontsize=6.5)
    _panel_tag(c, "c")
    return figstyle.save(fig, "f3", out_dir)


def fig_f4(inputs: dict, out_dir: Path) -> List[Path]:
    """F4: the concentration behind H1, and the two coefficients on which H1 actually fails."""
    results, frame = inputs["results"], inputs["frame"]
    lorenz, summary = results["lorenz"], results["summary"]
    h1 = summary["H1"]

    fig = plt.figure(figsize=(figstyle.SINGLE, 4.0))
    figstyle.use_style()
    gs = fig.add_gridspec(3, 1, height_ratios=[2.6, 0.32, 1.5], hspace=0.62,
                          left=0.19, right=0.97, top=0.94, bottom=0.11)
    a, strip, b = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    for ax in (a, b):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    share, loss = lorenz["wallet_share"].to_numpy(float), lorenz["loss_share"].to_numpy(float)
    a.plot(share, loss, color=figstyle.PALETTE[0])
    a.set_xscale("log")
    a.axhline(0.5, color="black", lw=0.8, ls="--")
    a.annotate("H1 threshold, 50 %", xy=(0.02, 0.5), xycoords=("axes fraction", "data"),
               xytext=(0, 4), textcoords="offset points", fontsize=6.5)
    n_wallets = max(len(lorenz), 1)
    top_x = 10.0 / n_wallets
    top_share = float(h1["top10_share"]["share"])
    a.plot([top_x], [top_share], "o", color=figstyle.PALETTE[1], ms=5)
    a.plot([top_x, top_x], [float(h1["top10_share"]["lo"]), float(h1["top10_share"]["hi"])],
           color=figstyle.PALETTE[1], lw=1.4)
    a.annotate("ten wallets carry\n{:.1f} % [{:.1f}, {:.1f}]".format(100 * top_share,
                                                                    100 * float(h1["top10_share"]["lo"]),
                                                                    100 * float(h1["top10_share"]["hi"])),
               xy=(top_x, top_share), xytext=(0.36, 0.20), textcoords="axes fraction", fontsize=6.5,
               arrowprops=dict(arrowstyle="->", lw=0.6))
    a.set_xlim(max(top_x / 20, 1e-4), 1.0)
    a.set_ylim(0, 1.03)
    a.set_xlabel("share of loss-making taker wallets, log scale")
    a.set_ylabel("share of the maker's loss")
    _panel_tag(a, "a")

    worst = lorenz.nsmallest(10, "loss") if "loss" in lorenz else lorenz.head(10)
    composition = (frame[frame["taker_wallet"].isin(set(worst["wallet"]))]["taker_class"]
                   .value_counts(normalize=True) if "wallet" in worst else pd.Series(dtype=float))
    left = 0.0
    for name in figstyle.CLASS_ORDER:
        value = float(composition.get(name, 0.0))
        if value <= 0:
            continue
        strip.barh(0, value, left=left, color=figstyle.CLASS_COLORS[name], edgecolor="black", lw=0.4)
        if value > 0.16:
            strip.text(left + value / 2, 0, figstyle.CLASS_LABELS[name], ha="center", va="center", fontsize=6.0,
                       color="white")
        left += value
    strip.set_xlim(0, 1)
    strip.set_yticks([])
    strip.set_xticks([])
    for spine in strip.spines.values():
        spine.set_visible(False)
    strip.set_xlabel("fills of the ten wallets by class", fontsize=6.5, labelpad=2)

    raw_size = float(frame.loc[frame["size_above_p90"], "y_dn"].mean()
                     - frame.loc[~frame["size_above_p90"], "y_dn"].mean())
    raw_sweep = float(frame.loc[frame["is_sweep"], "y_dn"].mean() - frame.loc[~frame["is_sweep"], "y_dn"].mean())
    pairs = [("size above p90", raw_size, float(h1["size_coefficient"]["beta"]), float(h1["size_coefficient"]["t"])),
             ("sweep", raw_sweep, float(h1["sweep_coefficient"]["beta"]), float(h1["sweep_coefficient"]["t"]))]
    for i, (name, raw, controlled, t) in enumerate(pairs):
        b.plot([raw, controlled], [i, i], color=figstyle.GREY, lw=0.8)
        b.plot([raw], [i], "o", mfc="none", color=figstyle.PALETTE[1], ms=5)
        b.plot([controlled], [i], "o", color=figstyle.PALETTE[0], ms=5)
        b.annotate("t {:.2f}".format(t), xy=(1.0, i), xycoords=("axes fraction", "data"),
                   xytext=(-2, 7), textcoords="offset points", ha="right", fontsize=6.5)
    b.axvline(0, color="black", lw=0.6)
    b.set_yticks(range(len(pairs)))
    b.set_yticklabels([p[0] for p in pairs], fontsize=7)
    b.set_ylim(-0.6, len(pairs) - 0.2)
    b.set_xlabel("difference in delta-neutral markout,\nUSDC per contract")
    b.legend(handles=[Line2D([], [], marker="o", mfc="none", color=figstyle.PALETTE[1], ls="none", label="raw"),
                      Line2D([], [], marker="o", color=figstyle.PALETTE[0], ls="none",
                             label="instrument x day fixed effects")],
             loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2, fontsize=6.0)
    _panel_tag(b, "b")
    return figstyle.save(fig, "f4", out_dir)


def fig_f5(inputs: dict, out_dir: Path) -> List[Path]:
    """F5: where the edge survives -- in the unit a bot decides on, and with the registered verdict beside it."""
    frame, results = inputs["frame"], inputs["results"]
    cells = results["cells"]
    currencies = [c for c in ("BTC", "ETH", "HYPE") if (cells["currency"] == c).any()]
    edge_bp = frame.assign(bp=1e4 * frame["net_edge"] / frame["notional"].replace(0, np.nan))

    fig = plt.figure(figsize=(figstyle.DOUBLE, 4.4))
    figstyle.use_style()
    gs = fig.add_gridspec(2, len(currencies) + 1, width_ratios=[1] * len(currencies) + [0.8],
                          hspace=0.42, wspace=0.22, left=0.085, right=0.985, top=0.92, bottom=0.14)
    for col, ccy in enumerate(currencies):
        values, counts = figdata.cell_matrix(edge_bp[edge_bp["currency"] == ccy], "bp", stat="median")
        grid = values.to_numpy(float).T                 # delta on the rows: five columns fit the labels
        ax = fig.add_subplot(gs[0, col])
        ax.imshow(grid, cmap="Greys", aspect="auto")
        cut = np.nanpercentile(grid, 70) if np.isfinite(grid).any() else np.inf
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                v = grid[i, j]
                if np.isfinite(v):
                    ax.text(j, i, "{:.0f}".format(v) if abs(v) >= 10 else "{:.1f}".format(v),
                            ha="center", va="center", fontsize=7, color="white" if v > cut else "black")
        ax.set_xticks(range(grid.shape[1]))
        ax.set_xticklabels(values.index, rotation=45, ha="right", fontsize=6)
        ax.set_yticks(range(grid.shape[0]))
        ax.set_yticklabels(values.columns if col == 0 else [], fontsize=6)
        ax.tick_params(length=0 if col else 2)
        finite = grid[np.isfinite(grid)]
        _panel_tag(ax, "{}  {:.1f} to {:.0f} bp".format(ccy, finite.min(), finite.max()) if finite.size else ccy)
        if col == 0:
            ax.set_ylabel("|delta|, %")

        sub = cells[cells["currency"] == ccy]
        ax2 = fig.add_subplot(gs[1, col])
        rows = [d for d in DELTA_LABELS if (sub["delta_bucket"] == d).any()]
        colsb = [t for t in TENOR_LABELS if (sub["tenor_bucket"] == t).any()]
        for i, d in enumerate(rows):
            for j, t in enumerate(colsb):
                r = sub[(sub["tenor_bucket"] == t) & (sub["delta_bucket"] == d)]
                if r.empty:
                    ax2.plot(j, i, "x", color=figstyle.GREY, ms=4)
                elif bool(r.iloc[0]["positive"]):
                    ax2.plot(j, i, "^", color=figstyle.PALETTE[0], ms=5)
                elif bool(r.iloc[0]["negative"]):
                    ax2.plot(j, i, "v", color=figstyle.PALETTE[1], ms=5)
                else:
                    ax2.plot(j, i, "o", mfc="none", color=figstyle.GREY, ms=4)
        ax2.set_xticks(range(len(colsb)))
        ax2.set_xticklabels(colsb, rotation=45, ha="right", fontsize=6)
        ax2.set_yticks(range(len(rows)))
        ax2.set_yticklabels(rows if col == 0 else [], fontsize=6)
        ax2.set_xlabel("tenor")
        ax2.set_xlim(-0.6, len(colsb) - 0.4)
        ax2.set_ylim(len(rows) - 0.4, -0.6)
        ax2.tick_params(length=0 if col else 2)
        if col == 0:
            ax2.set_ylabel("|delta|, %")

    legend_ax = fig.add_subplot(gs[1, -1])
    legend_ax.axis("off")
    legend_ax.legend(handles=[Line2D([], [], marker="^", color=figstyle.PALETTE[0], ls="none", label="positive"),
                              Line2D([], [], marker="o", mfc="none", color=figstyle.GREY, ls="none",
                                     label="inconclusive"),
                              Line2D([], [], marker="v", color=figstyle.PALETTE[1], ls="none", label="negative"),
                              Line2D([], [], marker="x", color=figstyle.GREY, ls="none", label="under 200 fills")],
                     loc="center", fontsize=6.5, title="registered net edge,\nUSDC per contract",
                     title_fontsize=6.5)

    sens = results["sensitivity"]
    ax3 = fig.add_subplot(gs[0, -1])
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)
    ax3.plot(sens["half_spread_bp"], 100 * sens["share_positive"], "-o", color=figstyle.PALETTE[0], ms=4)
    ax3.axhline(50, color="black", lw=0.8, ls="--")
    last = float(sens["half_spread_bp"].max())
    for _, r in sens.iterrows():
        right = r["half_spread_bp"] < last
        ax3.annotate("{:.1f}".format(100 * r["share_positive"]), xy=(r["half_spread_bp"], 100 * r["share_positive"]),
                     xytext=(5 if right else -5, -9), textcoords="offset points", fontsize=6.5,
                     ha="left" if right else "right")
    ax3.set_xlabel("assumed perp\nhalf spread, bp")
    ax3.set_ylabel("cells positive, %")
    ax3.yaxis.set_label_position("right")
    ax3.yaxis.tick_right()
    _side_note(ax3, "H4 threshold", 0.42)
    _panel_tag(ax3, "sensitivity")
    fig.text(0.5, 0.005, "upper row: median net edge in bp of notional     lower row: verdict on the registered "
                         "net edge in USDC", ha="center", fontsize=6.0, color=figstyle.GREY)
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
    gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.1, 1.1], hspace=0.62,
                          left=0.085, right=0.80, top=0.95, bottom=0.11)
    a, b, c = (fig.add_subplot(gs[i]) for i in range(3))
    for ax in (a, b, c):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    months = sorted(f["month"].unique())
    index = {m: i for i, m in enumerate(months)}
    for k, (ccy, style) in enumerate(zip(("BTC", "ETH", "HYPE"), ["-", "--", ":"])):
        sub = f[f["currency"] == ccy]
        if sub.empty:
            continue
        series, counts = sub.groupby("month")["y_vol"].median(), sub.groupby("month")["y_vol"].size()
        xs = [index[m] for m in series.index]
        a.plot(xs, series.to_numpy(float), style, color=figstyle.PALETTE[k], marker="o", ms=2.5, label=ccy)
        thin = [(index[m], series[m]) for m in series.index if counts.get(m, 0) < 1000]
        if thin:
            a.plot([t[0] for t in thin], [t[1] for t in thin], "o", color="white", mec=figstyle.GREY, ms=3.5,
                   zorder=5)
    a.axhline(0, color="black", lw=0.6)
    a.set_ylabel("median markout,\nvol points")
    a.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=6.0)
    _panel_tag(a, "a")

    composition = f.groupby(["month", "taker_class"]).size().unstack(fill_value=0)
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
    b.legend(loc="center left", bbox_to_anchor=(1.005, 0.5), fontsize=5.8, frameon=False)
    _panel_tag(b, "b")

    did = summary["H3"]["did"]
    placebo = [float(x) for x in did.get("placebo_beta", []) if np.isfinite(x)]
    beta = float(did["beta"])
    if placebo:
        c.hist(placebo, bins=min(20, max(6, len(placebo) // 4)), color=figstyle.GREY, alpha=0.45,
               label="{} placebo windows".format(len(placebo)))
        c.axvline(beta, color=figstyle.PALETTE[1], lw=1.4, label="estimate {:+.3f}".format(beta))
        c.set_xlabel("difference in differences, vol points")
        c.set_ylabel("placebo windows")
        c.legend(loc="upper left", fontsize=6.0)
        _side_note(c, "t {:.2f}, p {:.3f}, {:.0f} % of placebos more extreme".format(
            float(did["t"]), float(did["p"]), 100 * float(did["placebo_share_more_extreme"])), 0.90, align="right")
    else:
        c.text(0.5, 0.5, "placebo estimates not in the results file", transform=c.transAxes, ha="center",
               fontsize=7, color=figstyle.GREY)
    _panel_tag(c, "c")

    ticks = [i for i in range(0, len(months), max(1, len(months) // 10))]
    for ax in (a, b):
        ax.set_xlim(-0.5, len(months) - 0.5)
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(months[i]) for i in ticks] if ax is b else [], fontsize=6, rotation=45, ha="right")
    return figstyle.save(fig, "f6", out_dir)


def fig_a1(inputs: dict, out_dir: Path) -> List[Path]:
    """A1: is the on-chain mark good enough to carry the measurement?"""
    frame, results = inputs["frame"], inputs["results"]
    fig, axes = figstyle.figure(figstyle.DOUBLE, 3.0, ncols=3, gridspec_kw={"wspace": 0.38})
    fig.subplots_adjust(left=0.075, right=0.985, top=0.90, bottom=0.24)
    a, b, c = axes

    age, lag = frame["svi_age_s_t"].to_numpy(float), frame["lag_a_30m_s"].to_numpy(float)
    bins = np.logspace(0, 6, 40)
    a.hist(age[np.isfinite(age) & (age > 0)], bins=bins, color=figstyle.PALETTE[0], alpha=0.7,
           label="age of the curve at the fill")
    a.hist(lag[np.isfinite(lag) & (lag > 0)], bins=bins, color=figstyle.PALETTE[1], alpha=0.55,
           label="distance of the next fill")
    a.axvline(1800, color="black", lw=0.9, ls="--")
    a.annotate("30 min", xy=(1800, 0.0), xycoords=("data", "axes fraction"), xytext=(4, 12),
               textcoords="offset points", fontsize=6.5)
    a.set_xscale("log")
    a.set_xlabel("seconds, log scale")
    a.set_ylabel("fills")
    a.legend(loc="upper left", fontsize=5.8)
    _panel_tag(a, "a")

    bucket = pd.cut(frame["svi_age_s_t"], AGE_EDGES, labels=AGE_LABELS, right=False)
    means, down, up, ns = [], [], [], []
    for label in AGE_LABELS:
        sub = frame[bucket == label]
        ci = _ci(sub["y_usd"].to_numpy(float), sub["cluster"].to_numpy()) if len(sub) else \
            {"mean": np.nan, "lo": np.nan, "hi": np.nan, "n": 0}
        means.append(ci["mean"]), down.append(ci["mean"] - ci["lo"]), up.append(ci["hi"] - ci["mean"])
        ns.append(int(ci["n"]))
    pos = np.arange(len(AGE_LABELS))
    b.errorbar(pos, means, yerr=[down, up], fmt="o", color=figstyle.PALETTE[0], ms=4, lw=0.8, capsize=2)
    b.set_xticks(pos)
    b.set_xticklabels(["{}\n{:,}".format(lbl, n).replace(",", " ") for lbl, n in zip(AGE_LABELS, ns)],
                      rotation=45, ha="right", fontsize=6)
    b.set_xlabel("age of the curve at the fill, s, and fills per class")
    b.set_ylabel("mean markout, USDC per contract")
    _panel_tag(b, "b")

    basis = 1e4 * (frame["fwd_t"] / frame["index_price"] - 1.0)
    tenor = basis.groupby(frame["tenor_bucket"]).mean()
    tenor = tenor.reindex([t for t in TENOR_LABELS if t in tenor.index])
    c.barh(np.arange(len(tenor)), tenor.to_numpy(float), color=figstyle.PALETTE[2], edgecolor="black", lw=0.5)
    c.set_yticks(np.arange(len(tenor)))
    c.set_yticklabels(tenor.index, fontsize=6.5)
    c.axvline(0, color="black", lw=0.6)
    c.set_xlabel("curve forward over index, bp")
    c.set_ylabel("tenor")
    _panel_tag(c, "c")

    paths = results.get("paths", pd.DataFrame())
    if len(paths) and (paths["group"] == "lag_a <= 300 s").any() and (paths["group"] == "all").any():
        _side_note(a, "correlation {:.3f} within 300 s,\n{:.3f} overall".format(
            float(paths.loc[paths["group"] == "lag_a <= 300 s", "correlation"].iloc[0]),
            float(paths.loc[paths["group"] == "all", "correlation"].iloc[0])), 0.55, align="right")
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
