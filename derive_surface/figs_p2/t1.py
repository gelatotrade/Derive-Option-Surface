"""T1 · The engine's view of the surface (Paper 2, ``docs/paper2/FIGURE_SELECTION.md`` section 7,
slot T1).

Panels a and b: the BTC implied-vol surface of the chain at 17 Sep 2026 08:00 UTC in 3D (height = implied vol), coloured
with the capital that one short contract binds under PM2 and under SM (``cividis`` on one fixed scale, % of forward),
iso-capital lines at 4, 8, 12 and 14 % lifted onto the surface. Panels c and d: the rule that sets the capital at each
node (worst PM2 scenario, SM branch), with the same iso lines, the Paper 1 bucket edges as grid lines and the listed
expiries as ticks on the right axis.

Inputs (all under ``results_dir``):

* ``t1_grid.csv``: :func:`derive_surface.p2surface.capital_grid` for PM2 and SM at the T1 block (37 call deltas x 20
  tenors, one short contract), written by :func:`prepare`. The feed history is heavy, so ``prepare`` runs only through
  ``python3 scripts/p2_heavy.py -- python3 -m derive_surface.figs_p2.t1 prepare``.
* ``t1_grid_meta.json``: ts, block and the live expiries of that block (also from :func:`prepare`).
* ``params/BTC_pm2.json``, ``params/BTC_sm.json``: the parameter timelines (``p2params.Timeline``).

Outputs: ``fig_t1_ab.csv`` (surface and capital per node), ``fig_t1_cd.csv`` (binding rule and its decomposition per
node), ``fig_t1_meta.csv`` (every other number in the figure) under ``results_dir``; ``t1.pdf``, ``t1.png`` (400 dpi)
and ``gray/t1.png`` (luminance, for the greyscale check) under ``out_dir``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import patheffects, transforms  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import ListedColormap, Normalize  # noqa: E402
from matplotlib.patches import Patch, PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402

from .. import figstyle, margin_pm2, margin_sm  # noqa: E402
from ..p2params import Timeline  # noqa: E402
from ..p2types import YEAR  # noqa: E402

SLOT = "t1"
CCY = "BTC"
TS = 1_789_632_000                      # 17 Sep 2026 08:00:00 UTC, last pilot day, no parameter event within +-1 day
DAY = 86_400
MANAGERS = ("pm2", "sm")
WIDTH, HEIGHT = figstyle.DOUBLE, 4.2
FS_MIN = 7.0                            # smallest type on the page (section 6.1)
FS_TAG = 8.0                            # panel titles with their letters
INK = "#000000"
ISO = (4.0, 8.0, 12.0, 14.0)            # iso-capital lines, % of forward (section 3, T1)
CLIM = (3.0, 15.5)                      # colour scale, % of forward
CBAR_TICKS = (4, 6, 8, 10, 12, 14)
ATM_DELTA, ATM_DAYS = 0.5, 30.0         # the node quoted in the titles (nearest grid tenor: 30.44 days)
GRID_FILE = "t1_grid.csv"
META_FILE = "t1_grid_meta.json"
PROBE_GRID = Path("data/p2/surface/probe_BTC_2026-09-17_grid.csv")
VOL_NAMES = {0: "none", 1: "up", 2: "down", 3: "linear skew", 4: "abs skew"}
MANAGER_NAME = {"pm2": "PM2", "sm": "SM"}
REL_TOL = 1e-9                          # decomposition against the grid capital

# fills of the rule maps: (face colour, hatch); the labels come from the parameters (class_labels)
CLASS_STYLE: Dict[str, Dict[str, tuple]] = {
    "pm2": {"up": ("#E0E0E0", ""), "down": ("#A8A8A8", ""), "core": ("#C8C8C8", "--"),
            "tail_up": ("#FFFFFF", "...."), "tail_down": ("#FFFFFF", "\\\\\\\\"), "other": ("#FFFFFF", "xx")},
    "sm": {"otm": ("#FFFFFF", ""), "floor": ("#E0E0E0", "///"), "mm_put": ("#FFFFFF", "...."),
           "max_loss": ("#FFFFFF", "xx")},
}
HATCH_COLOR = "#666666"
MIN_LABEL_VERTICES = 12             # iso-line pieces shorter than this get no label on the 3D surface

CAPTION = (
    "The surface as the engine sees it. BTC implied volatility over call delta and tenor at 08:00 UTC on 17 September "
    "2026, built from the on-chain feeds, with the capital that one short contract binds under PM2 (panel a) and under "
    "standard margin (panel b) as colour on a common scale in per cent of the forward. Height is volatility, colour is "
    "capital, and black lines join points of equal capital. Panels c and d name the rule that sets the capital at each "
    "point: the worst scenario of the PM2 grid, and the branch of the standard margin formula. Their grid lines are "
    "the delta and tenor bucket edges of Figures~\\ref{fig:f1} and~\\ref{fig:f2}, and the ticks on their right "
    "edge mark the listed expiries; the surface holds out-of-the-money options only, so buckets above an absolute "
    "delta of 0.6 have no counterpart here. Standard margin is set in per "
    "cent of spot and shown in per cent of the forward. Capital follows the contracts on chain; the venue's off-chain "
    "engine discounts PM2 at a flat two per cent."
)


# ---------------------------------------------------------------------------------------------------- checks

def _grid(rd: Path) -> pd.DataFrame:
    g = pd.read_csv(Path(rd) / GRID_FILE)
    g["K_pct"] = g["K_per_forward_bp"] / 100.0
    return g


def _atm(g: pd.DataFrame, mgr: str) -> pd.Series:
    d = g[g["manager"] == mgr]
    t = d["tenor_days"].to_numpy()
    tn = t[np.argmin(np.abs(t - ATM_DAYS))]
    return d[np.isclose(d["delta"], ATM_DELTA) & np.isclose(d["tenor_days"], tn)].iloc[0]


def _ratio(g: pd.DataFrame) -> pd.Series:
    p = g[g["manager"] == "pm2"].set_index(["delta", "tenor_days"])["K_pct"]
    s = g[g["manager"] == "sm"].set_index(["delta", "tenor_days"])["K_pct"]
    return (s / p.reindex(s.index)).dropna()


def _max_rel_decomposition(rd: Path, mgr: str) -> float:
    cd = pd.read_csv(Path(rd) / "fig_t1_cd.csv")
    cd = cd[cd["manager"] == mgr]
    g = _grid(rd)
    g = g[g["manager"] == mgr].set_index(["delta", "tenor_days"])["K"]
    parts = cd.set_index(["delta", "tenor_days"])[[c for c in cd.columns if c.startswith("c_")]].sum(axis=1)
    return float((np.abs(parts - g.reindex(parts.index)) / np.abs(g.reindex(parts.index))).max())


def _src_grid(fn):
    return lambda rd: float(fn(_grid(rd)))


def _src_meta(key):
    return lambda rd: float(len(json.loads((Path(rd) / META_FILE).read_text())["expiries"])) if key == "n_expiries" \
        else float(json.loads((Path(rd) / META_FILE).read_text())[key])


def _k(mgr, how):
    return _src_grid(lambda g: getattr(g.loc[g["manager"] == mgr, "K_pct"], how)())


# Check numbers of the build instruction (section 7, T1): the value printed in the figure table against the source file in
# results/p2 (the engine grid and its metadata), never against the figure table itself. ``figure`` = (file, key,
# manager); ``source`` = (file, recomputation); ``expected`` = the number of the build instruction; ``tol`` absolute.
CHECKS: List[dict] = [
    {"id": "ts", "what": "block time of the surface", "figure": ("fig_t1_meta.csv", "ts", ""),
     "source": (META_FILE, _src_meta("ts")), "expected": 1_789_632_000, "tol": 0.0},
    {"id": "n_expiries", "what": "live expiries at the block", "figure": ("fig_t1_meta.csv", "n_expiries", ""),
     "source": (META_FILE, _src_meta("n_expiries")), "expected": 15, "tol": 0.0},
    {"id": "n_nodes_pm2", "what": "nodes PM2", "figure": ("fig_t1_meta.csv", "n_nodes", "pm2"),
     "source": (GRID_FILE, _src_grid(lambda g: (g["manager"] == "pm2").sum())), "expected": 740, "tol": 0.0},
    {"id": "n_nodes_sm", "what": "nodes SM", "figure": ("fig_t1_meta.csv", "n_nodes", "sm"),
     "source": (GRID_FILE, _src_grid(lambda g: (g["manager"] == "sm").sum())), "expected": 740, "tol": 0.0},
    {"id": "pm2_min", "what": "PM2 K min, % of forward", "figure": ("fig_t1_meta.csv", "K_pct_min", "pm2"),
     "source": (GRID_FILE, _k("pm2", "min")), "expected": 3.418, "tol": 5e-4},
    {"id": "pm2_median", "what": "PM2 K median, % of forward", "figure": ("fig_t1_meta.csv", "K_pct_median", "pm2"),
     "source": (GRID_FILE, _k("pm2", "median")), "expected": 10.448, "tol": 5e-4},
    {"id": "pm2_max", "what": "PM2 K max, % of forward", "figure": ("fig_t1_meta.csv", "K_pct_max", "pm2"),
     "source": (GRID_FILE, _k("pm2", "max")), "expected": 13.704, "tol": 5e-4},
    {"id": "sm_min", "what": "SM K min, % of forward", "figure": ("fig_t1_meta.csv", "K_pct_min", "sm"),
     "source": (GRID_FILE, _k("sm", "min")), "expected": 12.374, "tol": 5e-4},
    {"id": "sm_median", "what": "SM K median, % of forward", "figure": ("fig_t1_meta.csv", "K_pct_median", "sm"),
     "source": (GRID_FILE, _k("sm", "median")), "expected": 12.979, "tol": 5e-4},
    {"id": "sm_max", "what": "SM K max, % of forward", "figure": ("fig_t1_meta.csv", "K_pct_max", "sm"),
     "source": (GRID_FILE, _k("sm", "max")), "expected": 15.007, "tol": 5e-4},
    {"id": "atm_tenor", "what": "ATM 30 d node, tenor in days", "figure": ("fig_t1_meta.csv", "atm_tenor_days", ""),
     "source": (GRID_FILE, _src_grid(lambda g: _atm(g, "pm2")["tenor_days"])), "expected": 30.439, "tol": 5e-4},
    {"id": "atm_pm2", "what": "PM2 ATM 30 d short, % of forward (title a)", "figure": ("fig_t1_meta.csv", "atm_K_pct",
                                                                                         "pm2"),
     "source": (GRID_FILE, _src_grid(lambda g: _atm(g, "pm2")["K_pct"])), "expected": 11.826, "tol": 5e-4},
    {"id": "atm_sm", "what": "SM ATM 30 d short, % of forward (title b)", "figure": ("fig_t1_meta.csv", "atm_K_pct",
                                                                                       "sm"),
     "source": (GRID_FILE, _src_grid(lambda g: _atm(g, "sm")["K_pct"])), "expected": 14.080, "tol": 5e-4},
    {"id": "n_sm_below_pm2", "what": "nodes where SM < PM2", "figure": ("fig_t1_meta.csv", "n_sm_below_pm2", ""),
     "source": (GRID_FILE, _src_grid(lambda g: (_ratio(g) < 1.0).sum())), "expected": 9, "tol": 0.0},
    {"id": "median_sm_over_pm2", "what": "median SM / PM2 over the nodes",
     "figure": ("fig_t1_meta.csv", "median_sm_over_pm2", ""),
     "source": (GRID_FILE, _src_grid(lambda g: _ratio(g).median())), "expected": 1.261, "tol": 5e-4},
    {"id": "n_outside_scale", "what": "values outside the colour scale [3; 15.5]",
     "figure": ("fig_t1_meta.csv", "n_outside_scale", ""),
     "source": (GRID_FILE, _src_grid(lambda g: ((g["K_pct"] < CLIM[0]) | (g["K_pct"] > CLIM[1])).sum())),
     "expected": 0, "tol": 0.0},
    {"id": "decomposition_pm2", "what": "PM2 rule decomposition = grid capital (max relative gap)",
     "figure": ("fig_t1_cd.csv", "c_*", "pm2"), "source": (GRID_FILE, lambda rd: _max_rel_decomposition(rd, "pm2")),
     "expected": 0.0, "tol": REL_TOL},
    {"id": "decomposition_sm", "what": "SM rule decomposition = grid capital (max relative gap)",
     "figure": ("fig_t1_cd.csv", "c_*", "sm"), "source": (GRID_FILE, lambda rd: _max_rel_decomposition(rd, "sm")),
     "expected": 0.0, "tol": REL_TOL},
]


def run_checks(results_dir: Path = Path("results/p2")) -> pd.DataFrame:
    """Every check of :data:`CHECKS`: figure value, source value, expected value and the two verdicts."""
    rd = Path(results_dir)
    meta = pd.read_csv(rd / "fig_t1_meta.csv", keep_default_na=False)
    rows = []
    for c in CHECKS:
        fname, key, mgr = c["figure"]
        src = float(c["source"][1](rd))
        if fname == "fig_t1_meta.csv":
            sel = meta[(meta["key"] == key) & (meta["manager"] == mgr)]
            fig_v = float(sel["value"].iloc[0]) if len(sel) == 1 else float("nan")
            agrees_src = bool(np.isfinite(fig_v) and abs(fig_v - src) <= 1e-12 * max(1.0, abs(src)))
        else:                                          # decomposition: the table's parts against the grid capital
            fig_v = src
            agrees_src = bool(src <= REL_TOL)
        rows.append({"id": c["id"], "what": c["what"], "figure": fig_v, "source": src, "expected": c["expected"],
                     "agrees_source": agrees_src,
                     "agrees_expected": bool(abs(fig_v - c["expected"]) <= c["tol"] + 1e-12)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------------- binding rules

def _core_mask(P) -> np.ndarray:
    """Core scenarios of the PM2 grid: undampened, not a skew scenario."""
    return (P.damp == 1.0) & ~P.is_skew


def grid_width(P) -> tuple:
    """(up, down) half widths of the PM2 core spot grid, read from the scenarios (e.g. 0.14, 0.14)."""
    core = _core_mask(P)
    return float(P.shock[core].max() - 1.0), float(1.0 - P.shock[core].min())


def pm2_class_keys(P, worst: np.ndarray, scenario_binds: np.ndarray) -> np.ndarray:
    """Class of the binding PM2 term per node from the index of the worst scenario and whether it beats the basis."""
    worst = np.asarray(worst, dtype=int)
    s, d, damp, skew = P.shock[worst], P.dirs[worst], P.damp[worst], P.is_skew[worst]
    core = _core_mask(P)
    hi, lo = P.shock[core].max(), P.shock[core].min()
    is_core = (damp == 1.0) & ~skew
    out = np.full(len(worst), "other", dtype=object)
    out[is_core] = "core"
    out[is_core & np.isclose(s, hi, rtol=0, atol=1e-12) & (d == 1)] = "up"
    out[is_core & np.isclose(s, lo, rtol=0, atol=1e-12) & (d == 1)] = "down"
    out[~is_core & ~skew & (s > 1.0)] = "tail_up"
    out[~is_core & ~skew & (s < 1.0)] = "tail_down"
    out[~np.asarray(scenario_binds, dtype=bool)] = "other"
    return out


def _pct(x: float) -> str:
    return f"{round(100.0 * x, 6):g}"


def class_labels(mgr: str, P, worst: Optional[np.ndarray] = None, keys: Optional[np.ndarray] = None) -> Dict[str, str]:
    """Legend text per class key; PM2 reads the grid width and the tail shocks from the parameters."""
    if mgr == "sm":
        om = P["OptionMarginParams"]
        return {"otm": f"{_pct(float(om['maxSpotReq']))} % − OTM", "floor": f"{_pct(float(om['minSpotReq']))} % floor",
                "mm_put": f"put: {float(om['mmOffsetScale']):g} × MM", "max_loss": "max loss"}
    up, down = grid_width(P)
    out = {"up": f"spot +{_pct(up)} %, vol up", "down": f"spot −{_pct(down)} %, vol up",
           "core": "core, other vol", "other": "basis/skew/other"}
    for key in ("tail_up", "tail_down"):
        shocks = []
        if worst is not None and keys is not None:
            shocks = sorted({float(P.shock[j]) for j, k in zip(worst, keys) if k == key})
        if not shocks:
            shocks = sorted({float(s) for s, dm, sk in zip(P.shock, P.damp, P.is_skew)
                             if dm != 1.0 and not sk and ((s > 1.0) if key == "tail_up" else (s < 1.0))})
        out[key] = "spot " + "/".join(f"×{s:g}" for s in shocks) + " (dampened)"
    return out


def _arr(g: pd.DataFrame, col: str) -> np.ndarray:
    return g[col].to_numpy(dtype=float)


def _side(g: pd.DataFrame) -> np.ndarray:
    return np.where(g["side"].astype(str).str.lower().isin(["short", "sell"]), -1.0, 1.0) if "side" in g \
        else np.full(len(g), -1.0)


def _pm2_rule(g: pd.DataFrame, params: Mapping) -> pd.DataFrame:
    """Worst PM2 term per node and the split K = (p q - m0) + (-minSPAN * factor) + contingencies (``_single_block``)."""
    P = margin_pm2._Params(params)
    q = _side(g)
    sec = np.round(np.maximum(_arr(g, "tau"), 0.0) * YEAR, 6)
    tau, disc, dpos, dneg, vsu, vsd = margin_pm2._expiry_factors(P, sec, _arr(g, "rate"))
    zero = np.zeros(len(g))
    prices = margin_pm2._leg_prices(P, sec, tau, _arr(g, "forward"), zero, _arr(g, "iv"), _arr(g, "strike"),
                                    g["is_call"].to_numpy(dtype=bool), disc, vsu, vsd)
    m0, basis, ep = margin_pm2._span(P, prices * q[None, :], tau, dpos, dneg)
    worst = np.argmin(ep, axis=0)
    ep_w = ep[worst, np.arange(len(g))]
    scen = ep_w < basis                                   # getMarginAndMarkToMarket: strict <, basis first
    min_span = np.where(scen, ep_w, basis)
    spot = _arr(g, "spot")
    conf = np.minimum.reduce([_arr(g, c) for c in ("spot_conf", "fwd_conf", "rate_conf", "vol_conf")])
    naked = np.maximum(-q, 0.0) * spot
    cont = naked * (P.mm_opt + P.im_opt) + P.conf_cont(conf, np.abs(q) * spot)
    keys = pm2_class_keys(P, worst, scen)
    labels = class_labels("pm2", P, worst, keys)
    return pd.DataFrame({
        "rule_key": keys, "rule": [labels[k] for k in keys],
        "spot_shock": np.where(scen, P.shock[worst], np.nan),
        "vol_shock": np.where(scen, [VOL_NAMES[int(v)] for v in P.dirs[worst]], "basis"),
        "dampening": np.where(scen, P.damp[worst], np.nan),
        "c_convention": _arr(g, "price") * q - m0,
        "c_scenario": -min_span * float(P.factor(True, 1.0)),
        "c_contingency": cont,
    })


def _sm_rule(g: pd.DataFrame, params: Mapping) -> pd.DataFrame:
    """SM branch per node (``StandardManager._getIsolatedMargin``) and K = (p q - mtm) + (mtm - margin) + contingency."""
    om = params["OptionMarginParams"]
    q = _side(g)
    spot, fwd, strike, price = _arr(g, "spot"), _arr(g, "forward"), _arr(g, "strike"), _arr(g, "price")
    is_call = g["is_call"].to_numpy(dtype=bool)
    iso, mtm = margin_sm.isolated_margin(spot, fwd, _arr(g, "iv"), _arr(g, "tau"), strike, is_call, q, params, True)
    with np.errstate(divide="ignore", invalid="ignore"):
        otm = np.where(is_call, np.maximum((strike - spot) / spot, 0.0), np.maximum((spot - strike) / spot, 0.0))
    mx, mn = float(om["maxSpotReq"]), float(om["minSpotReq"])
    mult = margin_sm._im_multiplier(otm, params)
    m_mult = mult * spot * q + mtm
    mm_put = (np.minimum(float(om["mmPutSpotReq"]) * spot * q, float(om["MMPutMtMReq"]) * mtm) + mtm) \
        * float(om["mmOffsetScale"])
    max_loss = np.where(~is_call, np.minimum(strike * q, 0.0), 0.0) \
        + np.where(is_call & (q < 0), float(om["unpairedIMScale"]) * fwd * q, 0.0)
    margin = np.maximum(iso, max_loss)
    keys = np.where((mx > otm) & (mx - otm > mn), "otm", "floor").astype(object)
    keys[~is_call & (mm_put < m_mult)] = "mm_put"
    keys[max_loss > iso] = "max_loss"
    keys[q > 0] = "max_loss"                              # a long has no isolated margin (not drawn in T1)
    short = np.maximum(-q, 0.0)
    conf = np.minimum.reduce([_arr(g, c) for c in ("spot_conf", "fwd_conf", "vol_conf")])
    oc = params["OracleContingencyParams"]
    cont = margin_sm._contingency(conf, float(oc["optionThreshold"]), float(oc["OCFactor"])) * spot * short \
        + margin_sm._depeg_multiplier(np.ones(len(g)), params, True) * short * spot
    labels = class_labels("sm", params)
    return pd.DataFrame({
        "rule_key": keys, "rule": [labels[k] for k in keys],
        "spot_shock": np.nan, "vol_shock": "", "dampening": np.nan,
        "c_convention": price * q - mtm,
        "c_rule": mtm - margin,
        "c_contingency": cont,
    })


def binding_rule(grid: pd.DataFrame, ccy: str = CCY, ts: int = TS, manager: str = "pm2", *,
                 params: Optional[Mapping] = None, root: Optional[Path] = None) -> pd.DataFrame:
    """The rule that sets the capital at every node of ``grid`` (one manager, rows of ``capital_grid``).

    Returns one row per grid row (same order): ``rule_key``, ``rule`` (legend text), ``spot_shock``, ``vol_shock``,
    ``dampening`` (PM2: the worst scenario; NaN when the basis contingency binds) and the parts ``c_*`` whose sum is the
    capital ``K`` of the grid. Raises ``ValueError`` when the parts miss ``K`` by more than 1e-9 relative at any node:
    then the grid was not computed with these parameters.
    """
    mgr = manager.lower()
    g = grid.reset_index(drop=True)
    if params is None:
        params = Timeline(ccy, mgr, root=root).at(int(ts))
    out = _pm2_rule(g, params) if mgr == "pm2" else _sm_rule(g, params) if mgr == "sm" else None
    if out is None:
        raise ValueError(f"binding rules exist for pm2 and sm, not {manager!r}")
    parts = out[[c for c in out.columns if c.startswith("c_")]].sum(axis=1).to_numpy()
    K = _arr(g, "K")
    rel = np.abs(parts - K) / np.maximum(np.abs(K), 1e-12)
    if not np.all(rel <= REL_TOL):
        i = int(np.nanargmax(rel))
        raise ValueError(f"{mgr} decomposition misses the grid capital at node {i}: relative gap {rel[i]:.3e}")
    return out


# ---------------------------------------------------------------------------------------------------- data

def _utc(ts: int) -> dt.datetime:
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc)


def _day(ts: int) -> str:
    d = _utc(ts)
    return f"{d.day} {d.strftime('%b %Y')}"


def grid_since(tl: Timeline, ts: int) -> tuple:
    """(up width, down width, from_ts) of the PM2 core grid in force at ``ts`` and since when it has been in force."""
    entries = [e for e in tl.entries if int(e["from_ts"]) <= int(ts)]
    widths = [grid_width(margin_pm2._Params(e["params"])) for e in entries]
    i = len(entries) - 1
    while i > 0 and np.allclose(widths[i - 1], widths[-1], rtol=0, atol=1e-12):
        i -= 1
    return widths[-1][0], widths[-1][1], int(entries[i]["from_ts"])


def load(results_dir: Path = Path("results/p2")) -> dict:
    """Grid, block metadata, parameters and binding rules of the T1 block."""
    rd = Path(results_dir)
    if not (rd / GRID_FILE).exists():
        raise FileNotFoundError(f"{rd / GRID_FILE} missing: run python3 scripts/p2_heavy.py -- python3 -m "
                                "derive_surface.figs_p2.t1 prepare")
    grid = pd.read_csv(rd / GRID_FILE)
    meta = json.loads((rd / META_FILE).read_text())
    ts, ccy = int(meta["ts"]), str(meta.get("ccy", CCY))
    root = rd / "params"
    tls = {m: Timeline(ccy, m, root=root) for m in MANAGERS}
    params = {m: tls[m].at(ts) for m in MANAGERS}
    grids, rules = {}, {}
    for m in MANAGERS:
        g = grid[grid["manager"] == m].sort_values(["tau", "delta"], kind="mergesort").reset_index(drop=True)
        if g.empty:
            raise ValueError(f"{GRID_FILE} has no rows for {m}")
        g["K_pct"] = g["K_per_forward_bp"] / 100.0
        grids[m] = g
        rules[m] = binding_rule(g, ccy, ts, m, params=params[m])
    up, down, since = grid_since(tls["pm2"], ts)
    return {"ccy": ccy, "ts": ts, "block": meta.get("block"), "expiries": [int(e) for e in meta["expiries"]],
            "grids": grids, "rules": rules, "params": params, "grid_up": up, "grid_down": down, "grid_since": since}


def _atm_row(g: pd.DataFrame) -> pd.Series:
    t = g["tenor_days"].to_numpy()
    tn = t[np.argmin(np.abs(t - ATM_DAYS))]
    return g[np.isclose(g["delta"], ATM_DELTA) & np.isclose(g["tenor_days"], tn)].iloc[0]


def header(data: dict) -> str:
    d = _utc(data["ts"])
    w = data["grid_up"] if np.isclose(data["grid_up"], data["grid_down"]) else None
    grid = f"±{_pct(w)} %" if w is not None else f"+{_pct(data['grid_up'])} %/−{_pct(data['grid_down'])} %"
    return (f"{data['ccy']} · {_day(data['ts'])}, {d.strftime('%H:%M')} UTC · {len(data['expiries'])} live "
            f"expiries · PM2 spot grid {grid} since {_day(data['grid_since'])} · chain semantics")


def title(mgr: str, value: float) -> str:
    return f"{'ab'[MANAGERS.index(mgr)]}  {MANAGER_NAME[mgr]}: ATM 30 d short = {value:.1f} % of forward"


def tables(data: dict) -> Dict[str, pd.DataFrame]:
    """The three figure tables (``fig_t1_ab``, ``fig_t1_cd``, ``fig_t1_meta``) with every number the figure shows."""
    ab, cd, meta = [], [], []

    def m(key, value, printed="", manager="", rule=""):
        meta.append({"key": key, "manager": manager, "rule": rule, "value": value, "printed": printed})

    ts = data["ts"]
    m("header", np.nan, header(data))
    m("ts", ts, f"{_day(ts)}, {_utc(ts).strftime('%H:%M')} UTC")
    m("block", data["block"] if data["block"] is not None else np.nan)
    m("n_expiries", len(data["expiries"]), f"{len(data['expiries'])} live expiries")
    for e in data["expiries"]:
        m("expiry_tenor_days", (e - ts) / DAY, "", rule=str(e))
    m("spot_grid_up_pct", 100 * data["grid_up"], f"±{_pct(data['grid_up'])} %", "pm2")
    m("spot_grid_down_pct", 100 * data["grid_down"], f"±{_pct(data['grid_down'])} %", "pm2")
    m("spot_grid_since_ts", data["grid_since"], _day(data["grid_since"]), "pm2")
    for v in ISO:
        m("iso_level", v, f"{v:g} %")
    for v in CBAR_TICKS:
        m("colorbar_tick", v, f"{v:g}")
    m("colour_scale_min", CLIM[0])
    m("colour_scale_max", CLIM[1])
    atm = {mg: _atm_row(data["grids"][mg]) for mg in MANAGERS}
    m("atm_delta", float(atm["pm2"]["delta"]), "ATM")
    m("atm_tenor_days", float(atm["pm2"]["tenor_days"]), "30 d")
    n_out = 0
    for mg in MANAGERS:
        g, r = data["grids"][mg], data["rules"][mg]
        k = g["K_pct"]
        a = float(atm[mg]["K_pct"])
        m("atm_K_pct", a, f"{a:.1f}", mg)
        m("title", a, title(mg, a), mg)
        m("n_nodes", len(g), "", mg)
        m("K_pct_min", float(k.min()), "", mg)
        m("K_pct_median", float(k.median()), "", mg)
        m("K_pct_max", float(k.max()), "", mg)
        n_out += int(((k < CLIM[0]) | (k > CLIM[1])).sum())
        parts = r[[c for c in r.columns if c.startswith("c_")]].sum(axis=1)
        m("max_rel_decomposition_gap", float((np.abs(parts - g["K"]) / np.abs(g["K"])).max()), "", mg)
        counts = r["rule_key"].value_counts()
        for key in CLASS_STYLE[mg]:
            n = int(counts.get(key, 0))
            lab = r.loc[r["rule_key"] == key, "rule"]
            m("n_class", n, lab.iloc[0] if len(lab) else "", mg, key)
        is_atm = np.isclose(g["delta"], atm[mg]["delta"]) & np.isclose(g["tenor_days"], atm[mg]["tenor_days"])
        ab.append(pd.DataFrame({
            "manager": mg, "delta": g["delta"], "tenor_days": g["tenor_days"], "iv": g["iv"], "strike": g["strike"],
            "forward": g["forward"], "is_call": g["is_call"], "K_usdc": g["K"], "K_pct_forward": k,
            "printed": np.where(is_atm, f"{a:.1f}", "")}))
        cdf = pd.DataFrame({"manager": mg, "delta": g["delta"], "tenor_days": g["tenor_days"]})
        cdf = pd.concat([cdf, r.drop(columns=["rule_key"]).reset_index(drop=True)], axis=1)
        cdf.insert(3, "rule_key", r["rule_key"].to_numpy())
        cdf["K_pct_forward"] = k.to_numpy()
        cdf["printed"] = cdf["rule"]
        cd.append(cdf)
    p = data["grids"]["pm2"].set_index(["delta", "tenor_days"])["K_pct"]
    s = data["grids"]["sm"].set_index(["delta", "tenor_days"])["K_pct"]
    ratio = (s / p.reindex(s.index)).dropna()
    m("n_sm_below_pm2", int((ratio < 1.0).sum()))
    m("median_sm_over_pm2", float(ratio.median()))
    m("n_outside_scale", n_out)
    return {"ab": pd.concat(ab, ignore_index=True), "cd": pd.concat(cd, ignore_index=True),
            "meta": pd.DataFrame(meta)}


# ---------------------------------------------------------------------------------------------------- drawing

def _pivot(g: pd.DataFrame, col: str):
    p = g.pivot(index="tenor_days", columns="delta", values=col)
    return p.columns.to_numpy(float), p.index.to_numpy(float), p.to_numpy()


def _edges(c: np.ndarray, log: bool = False) -> np.ndarray:
    v = np.log(c) if log else c
    mid = 0.5 * (v[1:] + v[:-1])
    e = np.concatenate([[v[0] - (mid[0] - v[0])], mid, [v[-1] + (v[-1] - mid[-1])]])
    return np.exp(e) if log else e


def _cells_path(xe: np.ndarray, ye: np.ndarray, mask: np.ndarray) -> MplPath:
    """One path made of the rectangles of all cells where ``mask`` is true (rows = y, columns = x)."""
    verts, codes = [], []
    for i, j in zip(*np.nonzero(mask)):
        x0, x1, y0, y1 = xe[j], xe[j + 1], ye[i], ye[i + 1]
        verts += [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        codes += [MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO, MplPath.LINETO, MplPath.CLOSEPOLY]
    return MplPath(verts, codes)


def _iso_lines(x, y, C):
    """Contour segments per level on the (x, y) grid (x = delta, y = log10 days)."""
    import contourpy

    gen = contourpy.contour_generator(x, y, np.ma.masked_invalid(C), line_type="Separate")
    return {lev: [s for s in gen.lines(lev) if len(s) >= 2] for lev in ISO}


def _label_vertex(seg: np.ndarray, placed: Sequence[np.ndarray], span: tuple) -> int:
    """Vertex in the middle 60 % of ``seg`` farthest from the labels already placed (the middle one if none)."""
    n = len(seg)
    lo, hi = int(0.2 * (n - 1)), int(np.ceil(0.8 * (n - 1)))
    if not placed or hi <= lo:
        return n // 2
    cand = np.arange(lo, hi + 1)
    p = np.asarray(placed) / np.asarray(span)
    s = seg[cand] / np.asarray(span)
    dist = np.sqrt(((s[:, None, :] - p[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    return int(cand[int(np.argmax(dist))])


def _fig_frac(fig, x0, y0, w, h):
    W, H = fig.get_size_inches()
    return [x0 / W, y0 / H, w / W, h / H]


STROKE = [patheffects.withStroke(linewidth=1.6, foreground="white")]


def _draw_3d(fig, ax, g: pd.DataFrame, mgr: str, norm, zlim) -> None:
    from scipy.interpolate import RegularGridInterpolator

    x, days, Z = _pivot(g, "iv")
    Z = Z * 100.0
    C = _pivot(g, "K_pct")[2]
    ly = np.log10(days)
    X, Y = np.meshgrid(x, ly)
    ax.computed_zorder = False
    ax.set_facecolor("white")
    for a_ in (ax.xaxis, ax.yaxis, ax.zaxis):
        a_.set_pane_color((1, 1, 1, 0))
        a_._axinfo["grid"]["color"] = (0.86, 0.86, 0.86, 1.0)
        a_._axinfo["grid"]["linewidth"] = 0.4
        a_._axinfo["axisline"]["linewidth"] = 0.6
        a_._axinfo["tick"]["outward_factor"] = 0.0
        a_._axinfo["tick"]["inward_factor"] = 0.25
    ax.plot_surface(X, Y, Z, facecolors=figstyle_cmap()(norm(C)), rstride=1, cstride=1, linewidth=0.15,
                    edgecolor=(0, 0, 0, 0.10), shade=False, antialiased=True, zorder=1)
    interp = RegularGridInterpolator((ly, x), Z, bounds_error=False, fill_value=None)
    lift = 0.004 * (zlim[1] - zlim[0])
    placed: List[np.ndarray] = []
    for lev, segs in _iso_lines(x, ly, C).items():
        if not segs:
            continue
        for seg in segs:
            zz = interp(np.column_stack([seg[:, 1], seg[:, 0]])) + lift
            ax.plot(seg[:, 0], seg[:, 1], zz, color=INK, lw=0.7, zorder=3, solid_capstyle="round")
        for seg in segs:                       # one label per line; stubs of a few nodes stay unlabelled
            if len(seg) < MIN_LABEL_VERTICES and seg is not max(segs, key=len):
                continue
            k = _label_vertex(seg, placed, (x.max() - x.min(), ly.max() - ly.min()))
            placed.append(seg[k])
            zz = float(interp([[seg[k, 1], seg[k, 0]]])[0]) + lift
            ax.text(seg[k, 0], seg[k, 1], zz, f"{lev:g} %", fontsize=FS_MIN, color=INK, ha="center", va="bottom",
                    zorder=4, path_effects=STROKE)
    ax.view_init(elev=24, azim=-128)
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(ly.min(), ly.max())
    ax.set_zlim(*zlim)
    ax.set_xticks([0.1, 0.5, 0.9])
    ax.set_xticklabels(["0.1", "0.5", "0.9"])
    ticks = np.array([1, 7, 30, 90, 365])
    ticks = ticks[(ticks >= days.min() * 0.999) & (ticks <= days.max() * 1.001)]
    ax.set_yticks(np.log10(ticks))
    ax.set_yticklabels([f"{t:d}" for t in ticks])
    zt = np.arange(np.ceil(zlim[0] / 10) * 10, zlim[1] + 1e-9, 10)
    ax.set_zticks(zt)
    ax.set_zticklabels([f"{v:.0f}" for v in zt])
    ax.tick_params(axis="both", labelsize=FS_MIN, colors=INK, pad=-2)
    ax.tick_params(axis="z", pad=-1)
    ax.set_xlabel("call delta (put = Δ − 1)", fontsize=FS_MIN, labelpad=-7)
    ax.set_ylabel("days to expiry", fontsize=FS_MIN, labelpad=-7)
    ax.set_zlabel("implied vol, %", fontsize=FS_MIN, labelpad=-8)


def label_missing_levels(ax, x, days, C, labelled) -> List[matplotlib.text.Text]:
    """Label every iso level that ``clabel`` left without a label (pieces too short for an inline label, such as
    the 4 % line at the upper right of panel c): the text sits beside the middle vertex of the level's longest piece
    in the panel, towards the inside of the axes, with the white stroke of the other labels."""
    import contourpy

    gen = contourpy.contour_generator(np.asarray(x, float), np.asarray(days, float), np.ma.masked_invalid(C),
                                      line_type="Separate")
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    added = []
    for lev in ISO:
        text = f"{lev:g} %"
        if text in labelled:
            continue
        segs = [s[(s[:, 0] >= x0) & (s[:, 0] <= x1) & (s[:, 1] >= y0) & (s[:, 1] <= y1)] for s in gen.lines(lev)]
        segs = [s for s in segs if len(s) >= 2]
        if not segs:
            continue
        seg = max(segs, key=lambda s: float(np.abs(np.diff(ax.transData.transform(s), axis=0)).sum()))
        px, py = seg[len(seg) // 2]
        right = px > (x0 + x1) / 2.0
        added.append(ax.annotate(text, (px, py), xytext=(-3 if right else 3, 0), textcoords="offset points",
                                 ha="right" if right else "left", va="center", fontsize=FS_MIN, color=INK, zorder=4,
                                 path_effects=STROKE))
    return added


def figstyle_cmap():
    return matplotlib.colormaps["cividis"]


def _draw_rules(fig, ax, g: pd.DataFrame, r: pd.DataFrame, mgr: str, expiry_days: Sequence[float], atm: pd.Series,
                *, first: bool) -> List[Patch]:
    x, days, C = _pivot(g, "K_pct")
    keys = pd.DataFrame({"delta": g["delta"], "tenor_days": g["tenor_days"], "key": r["rule_key"].to_numpy()}) \
        .pivot(index="tenor_days", columns="delta", values="key").to_numpy()
    xe, ye = _edges(x), _edges(days, log=True)
    handles = []
    for key, (face, hatch) in CLASS_STYLE[mgr].items():
        mask = keys == key
        if not mask.any():
            continue
        vals = np.ma.masked_where(~mask, np.ones(mask.shape))
        ax.pcolormesh(xe, ye, vals, cmap=ListedColormap([face]), vmin=0, vmax=2, shading="flat", linewidth=0.0,
                      antialiased=False, zorder=1)
        if hatch:        # a QuadMesh draws no hatch: one compound patch of the class's cells carries it
            ax.add_patch(PathPatch(_cells_path(xe, ye, mask), facecolor="none", edgecolor=HATCH_COLOR,
                                   linewidth=0.0, hatch=hatch, zorder=1.5))
        label = r.loc[r["rule_key"] == key, "rule"].iloc[0]
        handles.append(Patch(facecolor=face, edgecolor=HATCH_COLOR, hatch=hatch, linewidth=0.5, label=label))
    ax.set_yscale("log")
    ax.set_xlim(0.05, 0.95)
    ax.set_ylim(1.0, 365.0)
    cs = ax.contour(x, days, C, levels=list(ISO), colors=INK, linewidths=0.7, zorder=3)
    if len(cs.levels):
        lbl = ax.clabel(cs, fmt=lambda v: f"{v:g} %", fontsize=FS_MIN, inline=True, inline_spacing=2)
        for t in lbl:
            t.set_path_effects(STROKE)
        label_missing_levels(ax, x, days, C, labelled={t.get_text() for t in lbl})
    ax.set_xticks([0.10, 0.25, 0.40, 0.60, 0.75, 0.90])
    ax.set_xticklabels(["0.10", "0.25", "0.40", "0.60", "0.75", "0.90"])
    ax.set_yticks([1, 2, 7, 30, 90, 365])
    ax.set_yticklabels(["1", "2", "7", "30", "90", "365"] if first else [])
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.tick_params(labelsize=FS_MIN, colors=INK, length=2.5, width=0.6, pad=1.5)
    ax.grid(False)
    for v in (0.10, 0.25, 0.40, 0.60, 0.75, 0.90):
        ax.axvline(v, color="#808080", lw=0.4, zorder=2)
    for v in (2, 7, 30, 90):
        ax.axhline(v, color="#808080", lw=0.4, zorder=2)
    for s in ax.spines.values():
        s.set_linewidth(0.6)
        s.set_zorder(5)
    # listed expiries: short outward ticks on the right axis (0.06 in), so that no iso-line hides among them
    w_in = ax.get_position().width * fig.get_size_inches()[0]
    tr = transforms.blended_transform_factory(ax.transAxes, ax.transData)
    for t in expiry_days:
        if 1.0 <= t <= 365.0:
            ax.plot([1.0, 1.0 + 0.06 / w_in], [t, t], transform=tr, color=INK, lw=0.7, zorder=6, clip_on=False,
                    solid_capstyle="butt")
    ax.plot([float(atm["delta"])], [float(atm["tenor_days"])], "o", ms=3, mfc=INK, mec="white", mew=0.6, zorder=7)
    ax.annotate("ATM 30 d", (float(atm["delta"]), float(atm["tenor_days"])), xytext=(3, 2),
                textcoords="offset points", fontsize=FS_MIN, color=INK, ha="left", va="bottom", zorder=7,
                bbox={"boxstyle": "square,pad=0.08", "facecolor": "white", "edgecolor": "none"})
    ax.set_xlabel("call delta (put = Δ − 1)", fontsize=FS_MIN, labelpad=1)
    if first:
        ax.set_ylabel("days to expiry", fontsize=FS_MIN, labelpad=1)
    return handles


def draw(data: dict, tabs: Dict[str, pd.DataFrame]) -> plt.Figure:
    """The T1 figure at print size (7.0 x 4.2 in): the canvas is the page, nothing is cropped on saving."""
    figstyle.use_style()
    plt.rcParams.update({"savefig.bbox": None, "savefig.pad_inches": 0.0, "hatch.linewidth": 0.5,
                         "xtick.labelsize": FS_MIN, "ytick.labelsize": FS_MIN, "xtick.color": INK,
                         "ytick.color": INK, "font.size": FS_MIN, "axes.labelsize": FS_MIN})
    fig = plt.figure(figsize=(WIDTH, HEIGHT), facecolor="white")
    norm = Normalize(*CLIM)
    iv = np.concatenate([data["grids"][m]["iv"].to_numpy() * 100 for m in MANAGERS])
    zlim = (np.floor(iv.min() / 5.0) * 5.0, np.ceil(iv.max() / 5.0) * 5.0)
    meta = tabs["meta"]

    # header
    fig.text(0.06 / WIDTH, 1 - 0.05 / HEIGHT, meta.loc[meta["key"] == "header", "printed"].iloc[0], fontsize=FS_MIN,
             ha="left", va="top", color=INK)
    # row 1: a, b in 3D, colour bar on the right
    boxes3d = {"pm2": (0.0, 1.84, 3.35, 2.16), "sm": (3.00, 1.84, 3.35, 2.16)}
    tx = {"pm2": 0.10, "sm": 3.40}
    for mg in MANAGERS:
        ax = fig.add_axes(_fig_frac(fig, *boxes3d[mg]), projection="3d")
        _draw_3d(fig, ax, data["grids"][mg], mg, norm, zlim)
        t = meta.loc[(meta["key"] == "title") & (meta["manager"] == mg), "printed"].iloc[0]
        fig.text(tx[mg] / WIDTH, 1 - 0.22 / HEIGHT, t, fontsize=FS_TAG, fontweight="bold", ha="left", va="top",
                 color=INK)
    cax = fig.add_axes(_fig_frac(fig, 6.38, 2.00, 0.10, 1.80))
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=figstyle_cmap()), cax=cax)
    cb.set_ticks(list(CBAR_TICKS))
    cb.ax.tick_params(labelsize=FS_MIN, colors=INK, length=2.0, width=0.6, pad=1.5)
    cb.outline.set_linewidth(0.6)
    for v in ISO:
        cb.ax.plot([0, 1], [v, v], color=INK, lw=0.9, transform=transforms.blended_transform_factory(
            cb.ax.transAxes, cb.ax.transData), solid_capstyle="butt", clip_on=False)
    cb.set_label("capital per short contract,\n% of forward", fontsize=FS_MIN, color=INK, labelpad=3,
                 linespacing=1.1)
    # row 2: c, d under a, b
    boxes2d = {"pm2": (0.45, 0.74, 2.80, 0.84), "sm": (3.50, 0.74, 2.80, 0.84)}
    exp_days = meta.loc[meta["key"] == "expiry_tenor_days", "value"].astype(float).to_list()
    for i, mg in enumerate(MANAGERS):
        ax = fig.add_axes(_fig_frac(fig, *boxes2d[mg]))
        handles = _draw_rules(fig, ax, data["grids"][mg], data["rules"][mg], mg, exp_days,
                              _atm_row(data["grids"][mg]), first=(i == 0))
        ax.set_title("c  binding PM2 scenario" if mg == "pm2" else "d  binding SM rule", loc="left",
                     fontsize=FS_TAG, fontweight="bold", pad=2.5, color=INK)
        x0, _, w, _ = boxes2d[mg]
        leg = fig.legend(handles=handles, loc="upper left", bbox_to_anchor=((x0 - 0.02) / WIDTH, 0.37 / HEIGHT),
                         ncol=2, fontsize=FS_MIN, frameon=False,
                         handlelength=1.6, handleheight=0.9, handletextpad=0.4, columnspacing=0.9, borderaxespad=0.0,
                         borderpad=0.0, labelspacing=0.3)
        leg.set_in_layout(False)
    return fig


def _gray(png: Path, out: Path) -> Path:
    from PIL import Image

    out.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(png) as im:
        im.convert("L").save(out, optimize=True)
    return out


def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2")) -> List[Path]:
    """Write ``fig_t1_ab.csv``, ``fig_t1_cd.csv``, ``fig_t1_meta.csv`` (results) and ``t1.pdf``, ``t1.png`` (figures)."""
    rd, out = Path(results_dir), Path(out_dir)
    data = load(rd)
    tabs = tables(data)
    paths = []
    for name, df in tabs.items():
        p = rd / f"fig_t1_{name}.csv"
        df.to_csv(p, index=False)
        paths.append(p)
    fig = draw(data, tabs)
    from ._print import to_print

    to_print(fig)                                  # the width main.tex sets the figure at
    with matplotlib.rc_context({"savefig.bbox": None, "savefig.pad_inches": 0.0, "savefig.dpi": 400}):
        figs = figstyle.save(fig, SLOT, out)
    paths += figs
    paths.append(_gray(out / f"{SLOT}.png", out / "gray" / f"{SLOT}.png"))
    return paths


# ---------------------------------------------------------------------------------------------------- heavy input

def prepare(results_dir: Path = Path("results/p2"), *, ccy: str = CCY, ts: int = TS,
            probe: Optional[Path] = PROBE_GRID) -> dict:
    """Capital grids of PM2 and SM at the T1 block from the feed history (heavy: run through ``p2_heavy.py``).

    Writes ``t1_grid.csv`` and ``t1_grid_meta.json`` under ``results_dir``; the metadata records the largest gap to
    the probe grid ``data/p2/surface/probe_BTC_2026-09-17_grid.csv`` when that file exists.
    """
    from .. import p2surface
    from ..p2chain import block_at_ts

    rd = Path(results_dir)
    hist = p2surface.load_history(ccy, int(ts) - DAY, int(ts))
    exps = p2surface.live_expiries(hist, int(ts))
    state = hist.state_at(int(ts), exps)
    tenors = p2surface.ANIM_DAYS / 365.0
    grid = pd.concat([p2surface.capital_grid(ccy, int(ts), m, "short", hist=hist, state=state, tenors=tenors)
                      for m in MANAGERS], ignore_index=True)
    meta = {"ccy": ccy, "ts": int(ts), "block": int(block_at_ts(int(ts))), "expiries": [int(e) for e in exps],
            "expiry_tenor_days": [(int(e) - int(ts)) / DAY for e in exps], "tenor_axis_days": list(p2surface.ANIM_DAYS),
            "params_from_ts": {m: int(Timeline(ccy, m).entry_at(int(ts))["from_ts"]) for m in MANAGERS}}
    if probe is not None and Path(probe).exists():
        pg = pd.read_csv(probe)
        key = ["manager", "d_key", "t_key"]

        def keyed(df):
            return df.assign(d_key=df["delta"].round(9), t_key=df["tenor_days"].round(6))

        both = keyed(grid).merge(keyed(pg)[key + ["K_per_forward_bp"]], on=key, suffixes=("", "_probe"))
        meta["probe_rows_matched"] = int(len(both))
        meta["probe_max_abs_diff_bp"] = float(np.abs(both["K_per_forward_bp"] - both["K_per_forward_bp_probe"]).max())
    rd.mkdir(parents=True, exist_ok=True)
    grid.to_csv(rd / GRID_FILE, index=False)
    (rd / META_FILE).write_text(json.dumps(meta, indent=1))
    return meta


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface.figs_p2.t1")
    ap.add_argument("cmd", choices=["prepare", "build", "check"])
    ap.add_argument("--results", default="results/p2")
    ap.add_argument("--out", default="paper2/figures")
    args = ap.parse_args(argv)
    if args.cmd == "prepare":
        print(json.dumps(prepare(Path(args.results)), indent=1))
    elif args.cmd == "build":
        for p in build(Path(args.out), Path(args.results)):
            print(p)
    else:
        res = run_checks(Path(args.results))
        print(res.to_string(index=False))
        return 0 if (res["agrees_source"] & res["agrees_expected"]).all() else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
