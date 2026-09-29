"""Figures of paper 2: registry of the nine slots, build, checks and the media of the paper (GIF, social cards).

Every slot lives in its own module ``derive_surface/figs_p2/<slot>.py`` (build instruction
``docs/paper2/FIGURE_SELECTION.md``, sections 6 and 7). A slot module has

* ``build(out_dir, results_dir) -> list[Path]``: writes the numbers of the figure as ``results/p2/fig_<slot>*.csv``
  and ``<slot>.pdf`` / ``<slot>.png`` (400 dpi) at print size to ``paper2/figures/`` (laid out at 7.0 or 3.4 in,
  saved at the width main.tex sets it, 6.84 or 3.29 in: ``figs_p2._print``);
* ``CAPTION``: the caption of the manuscript (English, no dashes, result numbers as ``\\PH{key}``);
* ``CHECKS``: the test numbers of the build instruction, the value in the figure table against the file in
  ``results/p2`` it comes from.

The check lists of the slots come in four shapes (the slots were built in parallel); :func:`run_checks` evaluates
any of them and returns one table with the columns ``slot, check, figure, source, ok, instruction, error``.

Command line (``python3 -m derive_surface p2 figures ...``)::

    build [--only t1,f2] [--results results/p2] [--out paper2/figures]
    prepare-t1                    # heavy: capital grids of T1 from the feed history, via scripts/p2_heavy.py
    gif [--weekly|--daily]        # heavy: GIF of the BTC PM2 capital surface, via scripts/p2_heavy.py
    social                        # three social cards 1600 x 900 under paper2/social/
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

SLOTS = ("t1", "t2", "f1", "f2", "f3", "f4", "f5", "f6", "a1")
FIGURES: Dict[str, ModuleType] = {s: importlib.import_module(f"derive_surface.figs_p2.{s}") for s in SLOTS}
CAPTIONS: Dict[str, str] = {s: m.CAPTION for s, m in FIGURES.items()}
# print size of the saved PDF: laid out at 7.0 or 3.4 in, saved at the width main.tex sets it (``figs_p2._print``)
SIZES: Dict[str, tuple] = {"t1": (6.84, 4.2), "t2": (6.84, 2.6), "f1": (6.84, 3.9), "f2": (6.84, 4.4),
                           "f3": (3.29, 4.0), "f4": (3.29, 4.0), "f5": (6.84, 5.15), "f6": (6.84, 4.2), "a1": (6.84, 2.5)}
FS_MIN = 7.0
OUT_DIR = Path("paper2/figures")
RESULTS_DIR = Path("results/p2")


def _slots(only: Optional[Sequence[str]]) -> List[str]:
    if only is None:
        return list(SLOTS)
    if isinstance(only, str):
        only = [s for s in only.split(",")]
    names = [s.strip().lower() for s in only if s.strip()]
    unknown = [s for s in names if s not in FIGURES]
    if unknown:
        raise KeyError(f"unknown figure(s): {', '.join(unknown)}; known: {', '.join(SLOTS)}")
    return names


def build(only: Optional[Sequence[str]] = None, out_dir: Path = OUT_DIR, results_dir: Path = RESULTS_DIR,
          extra: Optional[Mapping[str, Mapping]] = None) -> Dict[str, List[Path]]:
    """Build the slots in ``only`` (all nine by default); ``extra`` passes keyword arguments to single slots (for
    example ``{"f6": {"panel_path": ...}}``). Returns the written paths per slot."""
    extra = extra or {}
    out = {}
    for s in _slots(only):
        paths = list(FIGURES[s].build(Path(out_dir), Path(results_dir), **dict(extra.get(s, {}))))
        gray = Path(out_dir) / "gray" / f"{s}.png"
        if gray not in [Path(p) for p in paths]:
            paths.append(grey_copy(Path(out_dir) / f"{s}.png", gray))
        out[s] = paths
    return out


def grey_copy(png: Path, out: Path) -> Path:
    """Luminance copy of a figure for the greyscale look (section 6.2), Rec. 709 weights as in ``_kit_t2a1``."""
    from PIL import Image

    out.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(png) as im:
        rgb = np.asarray(im.convert("RGB"), dtype=float) / 255.0
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    Image.fromarray(np.clip(np.round(lum * 255.0), 0, 255).astype(np.uint8)).save(out, optimize=True)
    return out


# ---------------------------------------------------------------------------------------------------- checks

def _fmt(v, width: int = 110) -> str:
    """A value of a check as short text for the check table."""
    if v is None:
        return ""
    if isinstance(v, (bool, np.bool_)):
        return "True" if v else "False"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        f = float(v)
        if math.isnan(f):
            return "nan"
        if f == int(f) and abs(f) < 1e15:
            return str(int(f))
        return f"{f:.6g}"
    if isinstance(v, pd.Series):
        v = v.tolist()
    if isinstance(v, pd.DataFrame):
        return f"table {v.shape[0]} x {v.shape[1]}"
    if isinstance(v, np.ndarray):
        v = v.tolist()
    if isinstance(v, Mapping):
        s = "{" + ", ".join(f"{k}: {_fmt(x, width)}" for k, x in v.items()) + "}"
    elif isinstance(v, (list, tuple)):
        s = "[" + ", ".join(_fmt(x, width) for x in v) + "]"
    else:
        s = str(v)
    s = " ".join(s.split())
    return s if len(s) <= width else s[: width - 1] + "…"


def _bool_or_none(v) -> Optional[bool]:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return bool(v)


def run_checks(slot: str, results_dir: Path = RESULTS_DIR, checks: Optional[Sequence] = None) -> pd.DataFrame:
    """Evaluate the check list of ``slot`` against ``results_dir``.

    ``ok`` is figure == source (the check of the build instruction, section 11); ``instruction`` compares the
    figure with the number printed in the build instruction where the slot records one (pilot cut 2026-09-17),
    ``None`` where it does not. ``checks`` replaces the module's list (tests point F6 at a synthetic panel)."""
    mod = FIGURES[slot]
    rd = Path(results_dir)
    rows: List[dict] = []
    if checks is not None or not hasattr(mod, "run_checks"):
        from .figs_p2 import _kit_f5f6 as kit

        res = kit.run_checks(list(checks if checks is not None else mod.CHECKS), rd)
    elif slot in ("t2", "a1"):
        res = mod.run_checks(rd, with_expected=True)
    else:
        res = mod.run_checks(rd)
    if isinstance(res, list):                                             # f3, f4: f34_frame.Check
        for r in res:
            rows.append({"check": r["name"], "figure": f"{r['figure']}: {r['detail']}", "source": r["source"],
                         "ok": bool(r["ok"]), "instruction": None, "error": "" if r["ok"] else r["detail"]})
    elif "agrees_source" in res.columns:                                  # t1
        for r in res.to_dict("records"):
            rows.append({"check": f"{r['id']}: {r['what']}", "figure": r["figure"], "source": r["source"],
                         "ok": bool(r["agrees_source"]), "instruction": _bool_or_none(r["agrees_expected"]),
                         "error": ""})
    elif "agrees" in res.columns:                                         # t2, a1, f5, f6 (kit.check)
        for r in res.to_dict("records"):
            rows.append({"check": f"{r['id']}: {r['what']}", "figure": r["figure"], "source": r["source"],
                         "ok": bool(r["agrees"]), "instruction": _bool_or_none(r["matches_instruction"]),
                         "error": r.get("error", "")})
    else:                                                                 # f1, f2
        for r in res.to_dict("records"):
            rows.append({"check": r["check"], "figure": r["figure"], "source": r["source"], "ok": bool(r["ok"]),
                         "instruction": _bool_or_none(r.get("pilot_ok")), "error": r.get("error", "")})
    out = pd.DataFrame(rows, columns=["check", "figure", "source", "ok", "instruction", "error"])
    out.insert(0, "slot", slot)
    return out


def run_all_checks(results_dir: Path = RESULTS_DIR, only: Optional[Sequence[str]] = None) -> pd.DataFrame:
    return pd.concat([run_checks(s, results_dir) for s in _slots(only)], ignore_index=True)


# ---------------------------------------------------------------------------------------------------- command line

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="derive_surface p2 figures", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the figures (all nine unless --only)")
    b.add_argument("--only", default=None, help="comma separated slots, e.g. t1,f2")
    b.add_argument("--results", type=Path, default=RESULTS_DIR)
    b.add_argument("--out", type=Path, default=OUT_DIR)
    c = sub.add_parser("check", help="run the check lists of the slots and print the table")
    c.add_argument("--only", default=None)
    c.add_argument("--results", type=Path, default=RESULTS_DIR)
    p = sub.add_parser("prepare-t1", help="heavy: capital grids of T1 (run through scripts/p2_heavy.py)")
    p.add_argument("--results", type=Path, default=RESULTS_DIR)
    g = sub.add_parser("gif", help="heavy: GIF of the BTC PM2 capital surface (run through scripts/p2_heavy.py)")
    g.add_argument("--step", choices=["weekly", "daily"], default="weekly")
    g.add_argument("--start", default=None)
    g.add_argument("--end", default=None)
    g.add_argument("--out", type=Path, default=None)
    g.add_argument("--results", type=Path, default=RESULTS_DIR)
    s = sub.add_parser("social", help="three social cards 1600 x 900")
    s.add_argument("--results", type=Path, default=RESULTS_DIR)
    s.add_argument("--out", type=Path, default=Path("paper2/social"))
    args = ap.parse_args(list(argv) if argv is not None else None)
    if args.cmd == "build":
        for slot, paths in build(args.only, args.out, args.results).items():
            for path in paths:
                print(slot, path)
        return 0
    if args.cmd == "check":
        res = run_all_checks(args.results, None if args.only is None else args.only.split(","))
        with pd.option_context("display.width", 200, "display.max_colwidth", 70, "display.max_rows", 500):
            print(res[["slot", "check", "ok", "instruction"]].to_string(index=False))
        return 0 if res["ok"].all() else 1
    if args.cmd == "prepare-t1":
        print(json.dumps(FIGURES["t1"].prepare(args.results), indent=1))
        return 0
    if args.cmd == "gif":
        from . import gif_p2

        kw = {k: v for k, v in (("start", args.start), ("end", args.end)) if v}
        if args.out is not None:
            kw["out"] = args.out
        print(json.dumps(gif_p2.build(step=args.step, results_dir=args.results, **kw), indent=1, default=str))
        return 0
    if args.cmd == "social":
        from . import social_p2

        for path in social_p2.build(args.results, args.out):
            print(path)
        return 0
    return 2
