"""T2 · What ``get_margin`` returns, and how PM2 prices a book (ABBILDUNGSWAHL.md section 7, T2), 7.0 x 2.6 in.

* a, b: the four historical probe books of ``results/p2/semantik/faktoren.csv`` (``messung`` starts with
  "historisch", no "H0_", ``fall`` A or B). a splits ``C - net`` of the mixed book of 24 Sep 2026 into the requirement
  ``R`` and the value term ``-V`` of each manager; b sets the SM/PM2 ratio read on ``C - net`` against the ratio on
  ``R`` for all four books.
* c: the scenario profit and loss of the BTC reference straddle of 17 Sep 2026, 08:00 UTC (the row of
  ``results/p2/reference_book.csv``; strike = forward, listed expiry nearest to 30 days) under the PM2 parameters in
  force (``Timeline("BTC", "pm2")``), with the capital of the book under PM2, of its legs margined one by one and of
  the book under SM as lines at ``-K/F``.

The engine is rerun on the reference row only after it reproduces ``K_pm2`` and ``K_sm`` of that row (relative
1e-9); otherwise the figure is not built. The capital of the single legs is read from ``K_pm2_call``/``K_pm2_put`` of
the reference book when it carries them (data contract, section 10) and is otherwise computed on the same row with
the same engine and state. The single legs under SM are computed the same way; they are not drawn and serve social
card 2 (``social_p2``). Nothing here needs the feed history.

Command line: ``python3 -m derive_surface.figs_p2.t2`` (writes ``paper2/figures/t2.{pdf,png}`` and
``results/p2/fig_t2_{a,b,c}.csv``, prints the checks).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Mapping, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.transforms as mtransforms  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from .. import margin_pm2, margin_sm  # noqa: E402
from ..p2params import Timeline  # noqa: E402
from ..p2types import Book, ExpiryState, MarketState, OptionLeg  # noqa: E402
from . import _kit_t2a1 as kit  # noqa: E402

SLOT = "t2"
WIDTH, HEIGHT = 7.0, 2.6
FAKTOREN = Path("semantik") / "faktoren.csv"
REFBOOK = Path("reference_book.csv")
REF_CCY, REF_DAY, REF_TS = "BTC", "2026-09-17", 1_789_632_000   # 17 Sep 2026 08:00 UTC
REPRO_REL = 1e-9
ROW_ORDER = ["17 Sep, mixed", "24 Sep, mixed", "17 Sep, short", "24 Sep, short"]
VOL_NAME = {0: "unchanged", 1: "up", 2: "down", 3: "linear skew", 4: "abs skew"}
VOL_FILL = {1: kit.MANAGER["pm2"][0], 0: "white", 2: "#BBBBBB"}
CORE_BG = "#F2F2F2"
LABELLED_SHOCKS = (0.34, 0.86, 1.0, 1.14, 6.0)
XLABEL_C = "spot shock, × spot (in order, not to scale)"   # scenarios at equal steps

CAPTION = (
    r"\textbf{What \texttt{get\_margin} returns, and how PM2 prices a book.} Panel a splits $C - \mathrm{net}$ into "
    r"the requirement $R$ and the value term $-V$ for the mixed probe book of 24 September 2026 (block "
    r"45\,110\,142); $-V$ is almost the same under both managers and dwarfs $R$. Panel b sets the ratio of standard "
    r"to PM2 margin read as $C - \mathrm{net}$ (open) against the ratio on $R$ (filled) for the four probe books at "
    r"their historical blocks. The dashed line is the H3 threshold of two, which was set from these books before any "
    r"maker book was measured. On the mixed book of 17 September $V$ is positive, so the ratio falls from 11.86 to "
    r"10.76. Panel c is the scenario profit and loss of a short BTC straddle struck at the forward on 17 September "
    r"2026, on the listed expiry nearest to 30 days (22 days), in per cent of the forward, over the spot shocks in "
    r"order, not to scale. PM2 charges the worst "
    r"scenario of the whole book plus contingencies (solid line), which is less than the sum of the legs margined one "
    r"by one (dash dot); standard margin is dashed."
)


# ---------------------------------------------------------------------------------------------------- data

def probe_rows(faktoren: pd.DataFrame) -> pd.DataFrame:
    """The four historical probe books (A = short, B = mixed) in drawing order, with label and block."""
    f = faktoren
    sel = f[f["messung"].astype(str).str.startswith("historisch") & ~f["messung"].astype(str).str.contains("H0_")
            & f["fall"].isin(["A", "B"])].copy()
    if len(sel) != 4 or sel[["buch", "fall"]].duplicated().any():
        raise ValueError(f"faktoren.csv: expected exactly four historical probe rows (A/B), found {len(sel)}")
    day = {b: ("17 Sep" if str(b).startswith("b17") else "24 Sep") for b in sel["buch"]}
    sel["label"] = [f"{day[b]}, {'mixed' if c == 'B' else 'short'}" for b, c in zip(sel["buch"], sel["fall"])]
    sel["block"] = [int(re.search(r"Blk\s+(\d+)", str(m)).group(1)) for m in sel["messung"]]
    sel = sel.set_index("label").loc[ROW_ORDER].reset_index()
    return sel


def straddle_inputs(row: pd.Series):
    """Book, market state and leg vols of the reference short straddle from one row of ``reference_book.csv``.

    The state carries confidence 1 everywhere; :func:`load` accepts it only when the engine reproduces the row's
    ``K_pm2`` and ``K_sm`` (so the oracle contingency of the original state was zero, and it is zero for each leg too,
    which reads the same feeds)."""
    e, K, ts = int(row["expiry"]), float(row["strike"]), int(row["ts"])
    state = MarketState(str(row["ccy"]), ts, float(row["spot"]), {e: ExpiryState(e, float(row["forward"]), None,
                                                                                 rate=float(row["rate"]))})
    book = Book(options=[OptionLeg(e, K, True, -1.0), OptionLeg(e, K, False, -1.0)])
    return book, state, {(e, K): float(row["sigma"])}


def pm2_scenarios(book: Book, state: MarketState, params: Mapping, *, vols=None,
                  is_initial: bool = True) -> pd.DataFrame:
    """Scenario P&L of ``book`` under PM2 (dampened, static discount applied, as ``PMRMLib_2``), one row per
    scenario in parameter order: ``scenario, spot_shock, vol_shock, vol_state, dampening, is_skew, pnl_usdc,
    binding`` (binding = the scenario that sets ``minSPAN``; none when the basis contingency binds)."""
    d = margin_pm2.margin_details(book, state, params, is_initial, vols=vols)
    P = margin_pm2._Params(params)
    out = pd.DataFrame({"scenario": np.arange(len(P.shock)), "spot_shock": P.shock, "vol_shock": P.dirs,
                        "vol_state": [VOL_NAME[int(x)] for x in P.dirs], "dampening": P.damp,
                        "is_skew": P.is_skew, "pnl_usdc": np.asarray(d["scenario_pnl"], dtype=float)})
    out["binding"] = out["scenario"] == int(d["worst"])
    out.attrs.update({"basis": float(d["basis"]), "minSPAN": float(d["minSPAN"]), "worst": int(d["worst"])})
    return out


def _book_capital(engine, book: Book, state: MarketState, params: Mapping, vols, premium: float) -> float:
    net, _ = engine.net_margin(book, state, params, True, vols=vols)
    return float(premium - net)


def _reference_row(results_dir: Path) -> pd.Series:
    rb = pd.read_csv(Path(results_dir) / REFBOOK)
    sel = rb[(rb["ccy"] == REF_CCY) & (rb["day"] == REF_DAY)]
    if len(sel) != 1 or int(sel["ts"].iloc[0]) != REF_TS:
        raise ValueError(f"reference_book.csv: no single {REF_CCY} row on {REF_DAY} at ts {REF_TS}")
    return sel.iloc[0]


def load(results_dir: Path = Path("results/p2")) -> dict:
    """Everything T2 draws, from ``results_dir`` (faktoren.csv, reference_book.csv, params/)."""
    rd = Path(results_dir)
    probes = probe_rows(pd.read_csv(rd / FAKTOREN))
    row = _reference_row(rd)
    ts, F = int(row["ts"]), float(row["forward"])
    tl = {m: Timeline(REF_CCY, m, root=rd / "params") for m in ("pm2", "sm")}
    p_pm2, p_sm = tl["pm2"].at(ts), tl["sm"].at(ts)
    book, state, vols = straddle_inputs(row)
    c, p = float(row["price_call"]), float(row["price_put"])
    K_pm2 = _book_capital(margin_pm2, book, state, p_pm2, vols, -(c + p))
    K_sm = _book_capital(margin_sm, book, state, p_sm, vols, -(c + p))
    for name, mine, theirs in (("K_pm2", K_pm2, float(row["K_pm2"])), ("K_sm", K_sm, float(row["K_sm"]))):
        if not abs(mine - theirs) <= REPRO_REL * abs(theirs):
            raise ValueError(f"the engine does not reproduce {name} of the reference row ({mine!r} vs {theirs!r})")
    legs, legs_sm = {}, {}
    for leg, prem in ((book.options[0], -c), (book.options[1], -p)):
        legs["call" if leg.is_call else "put"] = _book_capital(margin_pm2, Book(options=[leg]), state, p_pm2, vols, prem)
        legs_sm["call" if leg.is_call else "put"] = _book_capital(margin_sm, Book(options=[leg]), state, p_sm, vols,
                                                                  prem)
    if {"K_pm2_call", "K_pm2_put"} <= set(row.index) and np.isfinite(row["K_pm2_call"]) \
            and np.isfinite(row["K_pm2_put"]):
        K_call, K_put, source = float(row["K_pm2_call"]), float(row["K_pm2_put"]), "reference_book.csv"
    else:
        K_call, K_put, source = legs["call"], legs["put"], "recomputed on the reference row"
    sc = pm2_scenarios(book, state, p_pm2, vols=vols)
    sc["pnl_pct_forward"] = 100.0 * sc["pnl_usdc"] / F
    core = sc[(sc["dampening"] == 1.0) & ~sc["is_skew"]]
    grid = float(max(core["spot_shock"].max() - 1.0, 1.0 - core["spot_shock"].min()))
    return {"probes": probes, "row": row, "forward": F, "ts": ts, "expiry": int(row["expiry"]),
            "tenor_days": float(row["tenor_days"]), "K_pm2": K_pm2, "K_sm": K_sm, "K_pm2_call": K_call,
            "K_pm2_put": K_put, "K_pm2_legs": K_call + K_put, "legs_source": source,
            "K_sm_call": legs_sm["call"], "K_sm_put": legs_sm["put"],
            "legs_recomputed": legs, "scenarios": sc, "grid": grid, "basis": sc.attrs["basis"],
            "pm2_param_from_ts": int(tl["pm2"].entry_at(ts)["from_ts"])}


# ---------------------------------------------------------------------------------------------------- printed text

def _k(x_usdc: float) -> str:
    return f"{x_usdc / 1e3:.0f}"


def _pct(k: float, F: float) -> str:
    return f"{100.0 * k / F:.1f}"


def line_labels(data: dict) -> Dict[str, str]:
    F = data["forward"]
    return {"K_pm2_book": f"PM2, book {_pct(data['K_pm2'], F)}",
            "K_pm2_legs": f"PM2, legs one by one {_pct(data['K_pm2_legs'], F)}",
            "K_sm": f"SM {_pct(data['K_sm'], F)}"}


def _shock_label(s: float) -> str:
    return f"{s:g}"


# ---------------------------------------------------------------------------------------------------- tables

def tables(data: dict) -> Dict[str, pd.DataFrame]:
    pr = data["probes"]
    a_row = pr[pr["label"] == "24 Sep, mixed"].iloc[0]
    a = []
    for mgr, R, V, C in (("sm", a_row["SM_R_engine"], a_row["V_und_SM"], a_row["SM_Cnet"]),
                         ("pm2", a_row["PM2_R_engine"], a_row["V_PM2"], a_row["PM2_Cnet"])):
        R, V, C = float(R), float(V), float(C)
        for item, value, printed in (("R", R, f"R {_k(R)}"), ("minus_V", -V, ""),
                                     ("C_minus_net", R - V, _k(R - V)), ("C_minus_net_faktoren", C, "")):
            a.append({"manager": mgr, "item": item, "value_usdc": value, "value_drawn_thousand": value / 1e3,
                      "printed": printed, "buch": a_row["buch"], "fall": a_row["fall"], "block": int(a_row["block"])})
    b = pd.DataFrame({"row": np.arange(4), "label": pr["label"], "buch": pr["buch"], "fall": pr["fall"],
                      "block": pr["block"].astype(int), "F_Cnet": pr["F_Cnet"].astype(float),
                      "F_R_engine": pr["F_R_engine"].astype(float),
                      "printed_Cnet": [f"{x:.2f}" for x in pr["F_Cnet"]],
                      "printed_R": [f"{x:.2f}" for x in pr["F_R_engine"]],
                      "SM_Cnet": pr["SM_Cnet"], "PM2_Cnet": pr["PM2_Cnet"], "SM_R_engine": pr["SM_R_engine"],
                      "PM2_R_engine": pr["PM2_R_engine"], "threshold": 2.0,
                      "printed_threshold": "H3 threshold, set from these books"})
    sc = data["scenarios"].copy()
    xs = _positions(sc)
    sc = sc.assign(kind="scenario", item=[f"scenario {i}" for i in sc["scenario"]],
                   x_position=[xs.get(float(s), np.nan) if not k else np.nan
                               for s, k in zip(sc["spot_shock"], sc["is_skew"])],
                   drawn=~sc["is_skew"], printed=[_shock_label(s) if (not k and _labelled(s)) else ""
                                                  for s, k in zip(sc["spot_shock"], sc["is_skew"])])
    F = data["forward"]
    labels = line_labels(data)
    cap = []
    for item, value, drawn in (("K_pm2_book", data["K_pm2"], True), ("K_pm2_legs", data["K_pm2_legs"], True),
                               ("K_pm2_call", data["K_pm2_call"], False), ("K_pm2_put", data["K_pm2_put"], False),
                               ("K_sm", data["K_sm"], True), ("K_sm_call", data["K_sm_call"], False),
                               ("K_sm_put", data["K_sm_put"], False)):
        cap.append({"kind": "capital", "item": item, "pnl_usdc": -value, "pnl_pct_forward": -100.0 * value / F,
                    "value_usdc": value, "value_pct_forward": 100.0 * value / F, "drawn": drawn,
                    "printed": labels.get(item, "")})
    meta = [{"kind": "meta", "item": k, "value_usdc": v, "printed": p} for k, v, p in (
        ("forward", F, ""), ("strike", float(data["row"]["strike"]), ""), ("ts", data["ts"], ""),
        ("expiry", data["expiry"], ""), ("tenor_days", data["tenor_days"], ""),
        ("spot_grid_half_width", data["grid"], f"core ±{data['grid'] * 100:.0f}{kit.THIN}%"),
        ("basis_contingency", data["basis"], ""), ("pm2_param_from_ts", data["pm2_param_from_ts"], ""),
        ("legs_source", np.nan, data["legs_source"]))]
    c = pd.concat([sc, pd.DataFrame(cap), pd.DataFrame(meta)], ignore_index=True)
    cols = ["kind", "item", "scenario", "spot_shock", "vol_shock", "vol_state", "dampening", "is_skew", "pnl_usdc",
            "pnl_pct_forward", "binding", "x_position", "drawn", "value_usdc", "value_pct_forward", "printed"]
    return {"fig_t2_a.csv": pd.DataFrame(a), "fig_t2_b.csv": b, "fig_t2_c.csv": c[cols]}


def _positions(sc: pd.DataFrame) -> Dict[float, int]:
    shocks = sorted({float(s) for s, k in zip(sc["spot_shock"], sc["is_skew"]) if not k})
    return {s: i for i, s in enumerate(shocks)}


def _labelled(s: float) -> bool:
    return any(np.isclose(s, x) for x in LABELLED_SHOCKS)


# ---------------------------------------------------------------------------------------------------- figure

def draw(data: dict):
    fig = kit.new_figure(WIDTH, HEIGHT)
    _panel_a(fig, data)
    _panel_b(fig, data)
    _panel_c(fig, data)
    return fig


def _panel_a(fig, data: dict) -> None:
    kit.letter(fig, 0.02, 0.04, "a")
    kit.fig_text(fig, 0.17, 0.04, "mixed book of 24 Sep 2026", fontsize=8.0)
    ax = kit.axes_at(fig, 0.36, 0.34, 1.46, 1.84)
    t = tables(data)["fig_t2_a.csv"].set_index(["manager", "item"])["value_usdc"]
    for y, mgr, name in ((0, "sm", "SM"), (1, "pm2", "PM2")):
        R, negV = t[(mgr, "R")] / 1e3, t[(mgr, "minus_V")] / 1e3
        ax.barh(y, R, height=0.55, color=kit.MANAGER[mgr][0], edgecolor="black", linewidth=0.5, zorder=2)
        ax.barh(y, negV, left=R, height=0.55, color="white", hatch="////", edgecolor=kit.GREY, linewidth=0.5,
                zorder=2)
        ax.text(0.0, y - 0.31, f"R {R:.0f}", ha="left", va="bottom", fontsize=kit.FS_MIN)
        ax.text(R + negV + 12, y, f"{R + negV:.0f}", ha="left", va="center", fontsize=kit.FS_MIN)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["SM", "PM2"])
    ax.set_ylim(1.45, -1.12)
    ax.set_xlim(0, 800)
    ax.set_xticks([0, 200, 400, 600, 800])
    ax.set_xlabel(f"C {kit.MINUS} net = R {kit.MINUS} V, thousand USDC")
    ax.tick_params(axis="y", length=0)
    ax.legend(handles=[Patch(facecolor="#999999", edgecolor="black", linewidth=0.5, label="R, requirement"),
                       Patch(facecolor="white", hatch="////", edgecolor=kit.GREY, linewidth=0.5,
                             label=f"{kit.MINUS}V, value term")],
              loc="upper right", bbox_to_anchor=(1.0, 1.0), handlelength=1.4, handleheight=0.9,
              handletextpad=0.4, borderaxespad=0.0, borderpad=0.0, labelspacing=0.3, frameon=False)


def _panel_b(fig, data: dict) -> None:
    kit.letter(fig, 2.02, 0.04, "b")
    ax = kit.axes_at(fig, 2.90, 0.34, 0.92, 1.84)
    ax.spines["left"].set_visible(False)
    b = tables(data)["fig_t2_b.csv"]
    for _, r in b.iterrows():
        y, xo, xf = float(r["row"]), float(r["F_Cnet"]), float(r["F_R_engine"])
        ax.annotate("", xy=(xf, y), xytext=(xo, y), zorder=1,
                    arrowprops=dict(arrowstyle="-|>,head_length=0.3,head_width=0.16", color=kit.GREY, lw=0.8,
                                    shrinkA=3.0, shrinkB=3.0, mutation_scale=10))
        ax.plot([xo], [y], "o", ms=4.6, mfc="white", mec="black", mew=0.8, zorder=3)
        ax.plot([xf], [y], "o", ms=4.6, mfc="black", mec="black", mew=0.8, zorder=2)
        lo_x, lo_s = (xo, r["printed_Cnet"]) if xo < xf else (xf, r["printed_R"])
        hi_x, hi_s = (xf, r["printed_R"]) if xo < xf else (xo, r["printed_Cnet"])
        ax.annotate(lo_s, xy=(lo_x, y), xytext=(-4.5, 0), textcoords="offset points", ha="right", va="center",
                    fontsize=kit.FS_MIN)
        ax.annotate(hi_s, xy=(hi_x, y), xytext=(4.5, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=kit.FS_MIN)
    ax.axvline(2.0, color="black", lw=0.8, ls="--", zorder=0)
    ax.text(2.0, 3.55, "H3 threshold,\nset from these books", ha="center", va="top", fontsize=kit.FS_MIN,
            linespacing=1.1, bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))
    ax.set_xscale("log")
    ax.set_xlim(0.8, 20)
    ax.set_xticks([1, 2, 4, 8, 16])
    ax.set_xticklabels(["1", "2", "4", "8", "16"])
    ax.minorticks_off()
    ax.set_yticks(range(4))
    ax.set_yticklabels(list(b["label"]))
    ax.tick_params(axis="y", length=0, pad=17)
    ax.set_ylim(4.3, -0.55)
    ax.grid(axis="x", color="#DDDDDD", lw=0.4, zorder=0)
    ax.set_xlabel("SM / PM2 capital ratio (log)")
    handles = [Line2D([], [], ls="none", marker="o", ms=4.6, mfc="white", mec="black", mew=0.8,
                      label=f"on C {kit.MINUS} net"),
               Line2D([], [], ls="none", marker="o", ms=4.6, mfc="black", mec="black", mew=0.8, label="on R")]
    W, H = fig.get_size_inches()
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(2.2 / W, 1.0 - 0.02 / H), ncol=2,
               handletextpad=0.2, columnspacing=1.2, borderaxespad=0.0, borderpad=0.0, frameon=False,
               handlelength=1.0)


def _panel_c(fig, data: dict) -> None:
    kit.letter(fig, 4.12, 0.04, "c")
    ax = kit.axes_at(fig, 4.66, 0.52, 2.30, 1.66)
    sc = data["scenarios"]
    F = data["forward"]
    pos = _positions(sc)
    draw_sc = sc[~sc["is_skew"]].copy()
    draw_sc["x"] = [pos[float(s)] for s in draw_sc["spot_shock"]]
    core = draw_sc[draw_sc["dampening"] == 1.0]
    lo, hi = core["x"].min(), core["x"].max()
    ax.axvspan(lo - 0.5, hi + 0.5, color=CORE_BG, lw=0, zorder=0)
    blue = kit.MANAGER["pm2"][0]
    for d in (1, 0, 2):
        g = core[core["vol_shock"] == d].sort_values("x")
        ax.plot(g["x"], g["pnl_pct_forward"], color=blue, lw=0.6, zorder=2)
    for _, r in draw_sc.iterrows():
        ax.plot([r["x"]], [r["pnl_pct_forward"]], "o", ms=3.5, mfc=VOL_FILL.get(int(r["vol_shock"]), "white"),
                mec=blue, mew=0.7, zorder=3)
    bind = sc[sc["binding"]]
    if len(bind) and not bool(bind["is_skew"].iloc[0]):
        r = bind.iloc[0]
        ax.plot([pos[float(r["spot_shock"])]], [r["pnl_pct_forward"]], "o", ms=8.0, mfc="none", mec="black",
                mew=0.9, zorder=4)
    n = len(pos)
    labels = line_labels(data)
    lines = (("K_pm2_book", data["K_pm2"], blue, "-", 1.2), ("K_pm2_legs", data["K_pm2_legs"], blue,
                                                           kit.DASHDOT_PM2_LEGS, 1.0),
             ("K_sm", data["K_sm"], kit.MANAGER["sm"][0], kit.MANAGER["sm"][1], 1.2))
    for item, k, color, ls, lw in lines:
        y = -100.0 * k / F
        ax.axhline(y, color=color, ls=ls, lw=lw, zorder=1)
        # the book line sits just under the worst scenario by construction, so its label goes below the line
        below = item == "K_pm2_book"
        ax.annotate(labels[item], xy=(n - 0.5, y), xytext=(-1, -1.5 if below else 1.5), textcoords="offset points",
                    ha="right", va="top" if below else "bottom", fontsize=kit.FS_MIN)
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(-1.15 * 100.0 * data["K_sm"] / F, 3.0)
    shocks = sorted(pos, key=pos.get)
    ax.set_xticks([pos[s] for s in shocks])
    ax.set_xticklabels([_shock_label(s) if _labelled(s) else "" for s in shocks])
    ax.set_xlabel(XLABEL_C)
    ax.set_ylabel("scenario P&L of the book,\n% of forward", linespacing=1.1)
    ax.grid(axis="y", color="#DDDDDD", lw=0.4, zorder=0)
    tr = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    tails_dn = [pos[s] for s in shocks if pos[s] < lo]
    tails_up = [pos[s] for s in shocks if pos[s] > hi]
    grid = f"{data['grid'] * 100:.0f}"
    kw = dict(transform=tr, fontsize=kit.FS_MIN, va="bottom", linespacing=1.1)
    if tails_dn:
        ax.text(min(tails_dn) - 0.5, 1.02, "tail ↓\n(dampened)", ha="left", **kw)
    ax.text((lo + hi) / 2.0, 1.02, f"core\n±{grid}{kit.THIN}%", ha="center", **kw)
    if tails_up:
        ax.text((min(tails_up) + max(tails_up)) / 2.0, 1.02, "tail ↑\n(dampened)", ha="center", **kw)
    handles = [Line2D([], [], ls="none", marker="o", ms=3.5, mfc=VOL_FILL[d], mec=blue, mew=0.7,
                      label=f"vol {VOL_NAME[d]}") for d in (1, 0, 2)]
    handles.append(Line2D([], [], ls="none", marker="o", ms=8.0, mfc="none", mec="black", mew=0.9, label="worst"))
    W, H = fig.get_size_inches()
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(4.3 / W, 1.0 - 0.02 / H), ncol=4,
               handletextpad=0.3, columnspacing=0.9, borderaxespad=0.0, borderpad=0.0, frameon=False,
               handlelength=1.0)


# ---------------------------------------------------------------------------------------------------- build

def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2")) -> List[Path]:
    """Write ``fig_t2_{a,b,c}.csv`` to ``results_dir`` and ``t2.pdf``/``t2.png`` (400 dpi) to ``out_dir``."""
    data = load(results_dir)
    paths = [kit.write_csv(df, results_dir, name) for name, df in tables(data).items()]
    return paths + kit.save(draw(data), SLOT, out_dir)


# ---------------------------------------------------------------------------------------------------- checks

def _fa(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "fig_t2_a.csv").set_index(["manager", "item"])


def _fb(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "fig_t2_b.csv").set_index("label")


def _fc(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "fig_t2_c.csv")


def _src_probe(rd: Path) -> pd.DataFrame:
    return probe_rows(pd.read_csv(rd / FAKTOREN)).set_index("label")


def _src_ref(rd: Path) -> pd.Series:
    return _reference_row(rd)


def _cap(item: str, col: str = "value_pct_forward"):
    return lambda rd: float(_fc(rd).set_index(["kind", "item"]).loc[("capital", item), col])


def _a(mgr: str, item: str):
    return lambda rd: float(_fa(rd).loc[(mgr, item), "value_usdc"])


def _b(label: str, col: str):
    return lambda rd: float(_fb(rd).loc[label, col])


def _src_b(label: str, col: str):
    return lambda rd: float(_src_probe(rd).loc[label, col])


def _ring_is_argmin(rd: Path) -> float:
    s = _fc(rd)
    s = s[s["kind"] == "scenario"]
    ring = s[s["binding"].astype(bool)]
    return float(ring["scenario"].iloc[0]) if len(ring) == 1 else float("nan")


def _src_argmin(rd: Path) -> float:
    s = _fc(rd)
    s = s[s["kind"] == "scenario"]
    return float(s.loc[s["pnl_usdc"].astype(float).idxmin(), "scenario"])


def _src_grid(rd: Path) -> float:
    p = Timeline(REF_CCY, "pm2", root=Path(rd) / "params").at(REF_TS)
    core = [float(s["spotShock"]) for s in p["scenarios"]
            if float(s["dampeningFactor"]) == 1.0 and margin_pm2._vol_dir(s["volShock"]) < 3]
    return max(max(core) - 1.0, 1.0 - min(core))


CHECKS: List[dict] = [
    kit.check("rows", "four probe rows in panel b", lambda rd: float(len(_fb(rd))),
              lambda rd: float(len(_src_probe(rd))), expected=4),
    kit.check("a_sm_R", "a: SM requirement R, USDC", _a("sm", "R"), lambda rd: float(
        _src_probe(rd).loc["24 Sep, mixed", "SM_R_engine"]), expected=211_023.47, expected_tol=0.005),
    kit.check("a_sm_minusV", "a: SM value term -V, USDC", _a("sm", "minus_V"), lambda rd: -float(
        _src_probe(rd).loc["24 Sep, mixed", "V_und_SM"]), expected=496_914.28, expected_tol=0.005),
    kit.check("a_sm_Cnet", "a: SM C - net = R - V, USDC (bar end, printed 708)", _a("sm", "C_minus_net"),
              lambda rd: float(_src_probe(rd).loc["24 Sep, mixed", "SM_Cnet"]), expected=707_937.75,
              expected_tol=0.005, abs_=0.011),
    kit.check("a_pm2_R", "a: PM2 requirement R, USDC", _a("pm2", "R"), lambda rd: float(
        _src_probe(rd).loc["24 Sep, mixed", "PM2_R_engine"]), expected=98_834.91, expected_tol=0.005),
    kit.check("a_pm2_minusV", "a: PM2 value term -V, USDC", _a("pm2", "minus_V"), lambda rd: -float(
        _src_probe(rd).loc["24 Sep, mixed", "V_PM2"]), expected=496_858.84, expected_tol=0.005),
    kit.check("a_pm2_Cnet", "a: PM2 C - net = R - V, USDC (bar end, printed 596)", _a("pm2", "C_minus_net"),
              lambda rd: float(_src_probe(rd).loc["24 Sep, mixed", "PM2_Cnet"]), expected=595_693.75,
              expected_tol=0.005, abs_=0.011),
] + [
    kit.check(f"b_{lab.replace(', ', '_').replace(' ', '')}_{col}", f"b: {lab}, ratio on {what}", _b(lab, col),
              _src_b(lab, col), expected=exp, expected_tol=0.0051)
    for lab, col, what, exp in (
        ("17 Sep, short", "F_Cnet", "C - net", 2.33), ("17 Sep, short", "F_R_engine", "R", 3.19),
        ("17 Sep, mixed", "F_Cnet", "C - net", 11.86), ("17 Sep, mixed", "F_R_engine", "R", 10.76),
        ("24 Sep, short", "F_Cnet", "C - net", 1.46), ("24 Sep, short", "F_R_engine", "R", 3.61),
        ("24 Sep, mixed", "F_Cnet", "C - net", 1.19), ("24 Sep, mixed", "F_R_engine", "R", 2.14))
] + [
    kit.check("c_K_pm2", "c: PM2 capital of the straddle, % of forward (same value as F5 c and card 1)",
              _cap("K_pm2_book"), lambda rd: 100.0 * float(_src_ref(rd)["K_pm2"]) / float(_src_ref(rd)["forward"]),
              expected=10.03, expected_tol=0.005),
    kit.check("c_K_sm", "c: SM capital of the straddle, % of forward", _cap("K_sm"),
              lambda rd: 100.0 * float(_src_ref(rd)["K_sm"]) / float(_src_ref(rd)["forward"]),
              expected=29.61, expected_tol=0.005),
    kit.check("c_ring", "c: the ring sits on the argmin of the scenario P&L", _ring_is_argmin, _src_argmin),
    kit.check("c_grid", "c: spot grid of the core, half width", lambda rd: float(
        _fc(rd).set_index(["kind", "item"]).loc[("meta", "spot_grid_half_width"), "value_usdc"]), _src_grid,
              expected=0.14, expected_tol=1e-12),
    kit.check("c_n_shocks", "c: spot shocks on the x axis", lambda rd: float(
        _fc(rd).query("kind == 'scenario' and drawn")["x_position"].nunique()),
              lambda rd: float(len({float(s["spotShock"]) for s in Timeline(REF_CCY, "pm2", root=Path(rd) / "params")
                                    .at(REF_TS)["scenarios"] if margin_pm2._vol_dir(s["volShock"]) < 3})),
              expected=17),
]


def run_checks(results_dir: Path = Path("results/p2"), with_expected: bool = True) -> pd.DataFrame:
    """Every check of :data:`CHECKS` (figure table against source file, and against the build instruction)."""
    return kit.run_checks(CHECKS, results_dir, with_expected=with_expected)


def main() -> None:  # pragma: no cover - command line
    paths = build()
    for p in paths:
        print("wrote", p)
    out = run_checks()
    print(out[["id", "figure", "source", "agrees", "expected", "matches_instruction", "error"]].to_string())


if __name__ == "__main__":  # pragma: no cover
    main()
