#!/usr/bin/env python3
"""Check the Paper 2 figures against ``results/p2`` and write ``docs/paper2/ABBILDUNGEN.md``.

* Runs the check list (``CHECKS``) of every slot of ``derive_surface.figures_p2``: the value the figure prints, read
  from its ``results/p2/fig_<slot>*.csv``, against the result file it comes from (never against the figure table
  itself). The column "Bauanweisung" compares with the number printed in ``docs/paper2/ABBILDUNGSWAHL.md`` where
  the slot records one (pilot cut 17.09.2026).
* Checks the print size of every ``paper2/figures/<slot>.pdf`` and, when they exist, the GIF (at most 8 MB) and the
  social cards (1600 x 900).
* Checks that every element a caption announces is drawn (``CAPTION_ELEMENTS``): a phrase of the manuscript caption
  needs its rows in the figure table, so a caption cannot describe a band or a group of rows that the data left out.
* Compares every caption of ``paper2/main.tex`` with ``CAPTIONS`` of ``figures_p2`` (a ``\\PH{key}`` of the module
  caption stands for any text in the manuscript). Differences are reported, never changed; deliberate departures
  listed in ``CAPTION_EXCEPTIONS`` of ``scripts/p2_build.py`` are marked as such.

    python3 scripts/p2_figure_check.py [--results results/p2] [--strict-captions]

Exit status 1 if a check or a size fails; caption differences only with ``--strict-captions``.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import re
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from derive_surface import figures_p2  # noqa: E402

RESULTS = Path("results/p2")
FIGURES = Path("paper2/figures")
TEX = Path("paper2/main.tex")
SHEET = Path("docs/paper2/ABBILDUNGEN.md")
BUILD_SCRIPT = Path("scripts/p2_build.py")
GIF = Path("docs/media/p2_btc_capital_surface.gif")
SOCIAL = Path("paper2/social")
GIF_MAX_BYTES = 8 * 1024 * 1024
SIZE_TOL = 0.02


# ---------------------------------------------------------------------------------------------------- captions

def _balanced(text: str, start: int) -> Tuple[str, int]:
    """Content of the brace group opening at ``text[start] == '{'`` and the index after its closing brace."""
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    raise ValueError("unbalanced braces")


def tex_captions(tex: str) -> Dict[str, str]:
    """Caption per figure file stem of every ``figure``/``figure*`` float (comments removed)."""
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    out = {}
    for m in re.finditer(r"\\begin\{(figure\*?)\}(.*?)\\end\{\1\}", tex, re.S):
        block = m.group(2)
        g = re.search(r"\\includegraphics\s*(?:\[[^\]]*\])?\{([^}]*)\}", block)
        c = block.find("\\caption{")
        if g and c >= 0:
            out[Path(g.group(1)).stem] = _balanced(block, c + len("\\caption"))[0]
    return out


def norm(s: str) -> str:
    """Caption text with the bold title unwrapped and white space collapsed."""
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def caption_exceptions(path: Path = BUILD_SCRIPT) -> List[Tuple[str, str, str, str]]:
    """``CAPTION_EXCEPTIONS`` of the manuscript build (read, not imported); empty when it is not there."""
    try:
        tree = ast.parse(path.read_text())
    except (OSError, SyntaxError):
        return []
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(
            node, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == "CAPTION_EXCEPTIONS" for t in targets) and node.value is not None:
            try:
                return [tuple(x) for x in ast.literal_eval(node.value)]
            except ValueError:
                return []
    return []


def first_difference(a: str, b: str, width: int = 60) -> str:
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return f"module: …{a[max(0, i - 15):i + width]}… | main.tex: …{b[max(0, i - 15):i + width]}…"


def compare_captions(tex: str, captions: Dict[str, str], exceptions: Sequence[Tuple[str, str, str, str]] = ()
                     ) -> pd.DataFrame:
    """One row per slot: ``status`` in {gleich, gleich mit Ausnahme, abweichend, fehlt}, and a note."""
    found = tex_captions(tex)
    rows = []
    for slot, ref in captions.items():
        if slot not in found:
            rows.append({"slot": slot, "status": "fehlt", "note": f"keine Abbildung figures/{slot}.pdf in main.tex"})
            continue
        cap = norm(found[slot])
        status, note = "abweichend", ""
        for candidate, label in ((ref, "gleich"), (_apply(ref, slot, exceptions), "gleich mit Ausnahme")):
            parts = re.split(r"\\PH\{[^}]*\}", norm(candidate))
            if re.fullmatch(r"(?:.+?)".join(re.escape(p) for p in parts), cap, re.S):
                status = label
                break
        if status == "gleich mit Ausnahme":
            note = "; ".join(reason for s, _, _, reason in exceptions if s == slot)
        elif status == "abweichend":
            note = first_difference(norm(ref), cap)
        dashes = [d for d in ("—", "–") if d in found[slot]]
        if dashes:
            note = (note + "; " if note else "") + f"Gedankenstrich in main.tex: {' '.join(dashes)}"
        rows.append({"slot": slot, "status": status, "note": note})
    return pd.DataFrame(rows, columns=["slot", "status", "note"])


def _apply(ref: str, slot: str, exceptions: Sequence[Tuple[str, str, str, str]]) -> str:
    for s, old, new, _ in exceptions:
        if s == slot:
            ref = ref.replace(old, new)
    return ref


# ---------------------------------------------------------------------------------------------------- sizes

def pdf_size(path: Path) -> Tuple[float, float]:
    m = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", Path(path).read_bytes())
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return (x1 - x0) / 72.0, (y1 - y0) / 72.0


def shape_checks(figures: Path = FIGURES, gif: Path = GIF, social: Path = SOCIAL) -> pd.DataFrame:
    rows = []
    for slot, (w, h) in figures_p2.SIZES.items():
        pdf = Path(figures) / f"{slot}.pdf"
        if not pdf.exists():
            rows.append({"what": f"{slot}.pdf", "figure": "fehlt", "target": f"{w} × {h} in", "ok": False})
            continue
        pw, ph = pdf_size(pdf)
        rows.append({"what": f"{slot}.pdf", "figure": f"{pw:.3f} × {ph:.3f} in", "target": f"{w} × {h} in",
                     "ok": abs(pw - w) <= SIZE_TOL and abs(ph - h) <= SIZE_TOL})
    if Path(gif).exists():
        size = Path(gif).stat().st_size
        rows.append({"what": str(gif), "figure": f"{size / 2**20:.2f} MB", "target": "≤ 8 MB",
                     "ok": size <= GIF_MAX_BYTES})
    if Path(social).exists():
        from PIL import Image

        for png in sorted(Path(social).glob("*.png")):
            with Image.open(png) as im:
                rows.append({"what": str(png), "figure": f"{im.size[0]} × {im.size[1]} px", "target": "1600 × 900 px",
                             "ok": im.size == (1600, 900)})
    return pd.DataFrame(rows, columns=["what", "figure", "target", "ok"])


# ---------------------------------------------------------------------------------------------------- media

def _row(slot: str, check: str, figure, source, ok: bool, error: str = "") -> dict:
    return {"slot": slot, "check": check, "figure": figure, "source": source, "ok": bool(ok), "instruction": None,
            "error": error}


def media_checks(results: Path = RESULTS) -> pd.DataFrame:
    """GIF (``gif_meta.json``, ``gif_frames.csv``) and social cards (``fig_s{1,2,3}.csv``) against ``results/p2``;
    nothing when they were not built."""
    import json
    import math

    import numpy as np

    rd = Path(results)
    rows: List[dict] = []
    meta_path = rd / "gif_meta.json"
    if meta_path.exists():
        from derive_surface import gif_p2
        from derive_surface.figs_p2.f5 import pure_jump

        meta = json.loads(meta_path.read_text())
        t1 = pd.read_csv(rd / "t1_grid.csv")
        n_t1 = int((t1["manager"] == "pm2").sum())
        rows.append(_row("gif", "last frame = T1 a: nodes matched, largest gap of K (USDC)",
                         [meta.get("last_frame_nodes_matched_t1"), meta.get("last_frame_max_abs_diff_usdc_t1")],
                         [n_t1, 0.0], meta.get("last_frame_nodes_matched_t1") == n_t1
                         and float(meta.get("last_frame_max_abs_diff_usdc_t1", math.inf)) <= 1e-6))
        ev = gif_p2.kept_events(pd.read_csv(rd / "events.csv"))
        rb = pd.read_csv(rd / "reference_book.csv")
        src = {e.event_id: gif_p2.fmt_step(gif_p2.step_pct(pure_jump(rb, "BTC", "pm2", int(e.event_ts),
                                                                         str(e.event_day))[0]))
               for e in ev.itertuples()}
        rows.append(_row("gif", "steps of the straddle in the time strip (simple %)", meta.get("steps"), src,
                         meta.get("steps") == src))
        frames = pd.read_csv(rd / "gif_frames.csv")
        drawn = frames[frames["frame"] >= 0]
        counted = [int(len(drawn)), int((frames["frame"] < 0).sum())]
        told = [meta.get("frames"), meta.get("skipped")]
        rows.append(_row("gif", "frames drawn / skipped (no live expiry)", told, counted, told == counted))
        last = drawn.iloc[-1]
        rows.append(_row("gif", "last frame block time = T1 block", int(last["ts"]),
                         int(json.loads((rd / "t1_grid_meta.json").read_text())["ts"]),
                         int(last["ts"]) == int(json.loads((rd / "t1_grid_meta.json").read_text())["ts"])))
    summary_path = rd / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
        for i in (1, 2, 3):
            path = rd / f"fig_s{i}.csv"
            if not path.exists():
                continue
            tab = pd.read_csv(path, dtype={"printed": str})
            for r in tab.itertuples():
                if not str(r.source).startswith("summary.json "):
                    continue
                key = str(r.source).split(" ", 1)[1]
                src = summary.get(key)
                ok = src is not None and np.isclose(float(r.value), float(src), rtol=1e-12, atol=0.0)
                rows.append(_row(f"s{i}", f"card number {r.key} (printed {r.printed})", r.value, src, ok))
    return pd.DataFrame(rows, columns=["slot", "check", "figure", "source", "ok", "instruction", "error"])


# ---------------------------------------------------------------------------------------------------- elements

def _group_starts(df: pd.DataFrame, prefix: str) -> bool:
    return "group" in df and df["group"].astype(str).str.startswith(prefix).any()


# (slot, phrase in the manuscript caption, figure table, what must be drawn, test on the table)
CAPTION_ELEMENTS = [
    ("f2", "grey band", "fig_f2_c.csv", "a row of kind band (h1_sign.sign_floor)",
     lambda df: (df["kind"].astype(str) == "band").any()),
    ("f2", "exploratory rows", "fig_f2_c.csv", "rows of kind exploratory",
     lambda df: (df["kind"].astype(str) == "exploratory").any()),
    ("f3", "per account", "fig_f3_b.csv", "rows with group label=", lambda df: _group_starts(df, "label=")),
    ("f3", "per parameter regime", "fig_f3_b.csv", "rows with group regime=", lambda df: _group_starts(df, "regime=")),
    ("f4", "by the manager of the account", "fig_f4_b.csv", "rows with group account_manager=",
     lambda df: _group_starts(df, "account_manager=")),
    ("f4", "by parameter regime", "fig_f4_b.csv", "rows with group regime=", lambda df: _group_starts(df, "regime=")),
    ("f4", "by book size", "fig_f4_b.csv", "rows sm_pm2_le63 and sm_pm2_gt63",
     lambda df: {"sm_pm2_le63", "sm_pm2_gt63"} <= set(df["variant"].astype(str))),
    ("f4", "on the same BTC and ETH legs", "fig_f4_b.csv", "row sm_pm2_be",
     lambda df: "sm_pm2_be" in set(df["variant"].astype(str))),
]


def element_checks(tex: str, results: Path = RESULTS, elements=CAPTION_ELEMENTS) -> pd.DataFrame:
    """Every phrase of ``elements`` that occurs in a manuscript caption needs its rows in the figure table."""
    caps = {k: norm(v) for k, v in tex_captions(tex).items()}
    rows = []
    for slot, phrase, table, what, test in elements:
        if phrase not in caps.get(slot, ""):
            continue
        path = Path(results) / table
        try:
            ok = bool(test(pd.read_csv(path)))
            err = ""
        except Exception as exc:  # noqa: BLE001 - reported, not raised
            ok, err = False, repr(exc)
        rows.append(_row(slot, f"caption \"{phrase}\": {what}", table, "drawn" if ok else "missing", ok, err))
    return pd.DataFrame(rows, columns=["slot", "check", "figure", "source", "ok", "instruction", "error"])


# ---------------------------------------------------------------------------------------------------- sheet

def _cell(v) -> str:
    return figures_p2._fmt(v, 90).replace("|", "\\|").replace("\n", " ")


def _yes(v: Optional[bool]) -> str:
    return "–" if v is None else ("ja" if v else "nein")


def sheet(checks: pd.DataFrame, shapes: pd.DataFrame, captions: pd.DataFrame, results: Path) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n, bad = len(checks), int((~checks["ok"]).sum())
    instr = checks["instruction"].dropna()
    lines = [
        "# Abbildungen Paper 2: Prüfliste", "",
        f"Erzeugt {now} mit `scripts/p2_figure_check.py` aus `{results}`. Jede Zeile vergleicht den Wert, den die "
        "Abbildung druckt (ihre Tabelle `results/p2/fig_<slot>_*.csv`), mit der Datei in `results/p2`, aus der er "
        "stammt, nie mit sich selbst. Spalte *Bauanweisung*: dieselbe Zahl gegen die Prüfzahl in "
        "`docs/paper2/ABBILDUNGSWAHL.md` (Pilotschnitt 17.09.2026), wo der Slot eine hat.", "",
        f"**Ergebnis:** {n - bad} von {n} Prüfungen ja"
        + (f", **{bad} nein**" if bad else "") + f"; Bauanweisung {int(instr.sum())} von {len(instr)} ja; "
        f"Gestalt {int(shapes['ok'].sum())} von {len(shapes)} ja; Captions "
        f"{int(captions['status'].str.startswith('gleich').sum())} von {len(captions)} gleich.", "",
        "## Prüfzahlen", "",
        "| Slot | Prüfung | Wert Abbildung | Wert results | ja/nein | Bauanweisung |",
        "|---|---|---|---|---|---|",
    ]
    for r in checks.to_dict("records"):
        lines.append(f"| {r['slot'].upper()} | {_cell(r['check'])} | {_cell(r['figure'])} | {_cell(r['source'])} | "
                     f"{_yes(r['ok'])} | {_yes(r['instruction'])} |")
    lines += ["", "## Gestalt", "", "| Datei | gemessen | Vorgabe | ja/nein |", "|---|---|---|---|"]
    for r in shapes.to_dict("records"):
        lines.append(f"| `{r['what']}` | {r['figure']} | {r['target']} | {_yes(r['ok'])} |")
    lines += ["", "## Captions: `paper2/main.tex` gegen `figures_p2.CAPTIONS`", "",
              "Gemeldet, nicht geändert. `\\PH{key}` der Modul-Caption steht für beliebigen Text im Manuskript; "
              "Ausnahmen aus `CAPTION_EXCEPTIONS` in `scripts/p2_build.py`.", "",
              "| Slot | Status | Hinweis |", "|---|---|---|"]
    for r in captions.to_dict("records"):
        lines.append(f"| {r['slot'].upper()} | {r['status']} | {_cell(r['note']) if r['note'] else ''} |")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--figures", type=Path, default=FIGURES)
    ap.add_argument("--tex", type=Path, default=TEX)
    ap.add_argument("--sheet", type=Path, default=SHEET)
    ap.add_argument("--strict-captions", action="store_true", help="fail on a caption that differs")
    args = ap.parse_args(argv)
    tex = args.tex.read_text() if args.tex.exists() else ""
    checks = pd.concat([figures_p2.run_all_checks(args.results), media_checks(args.results),
                        element_checks(tex, args.results)], ignore_index=True)
    shapes = shape_checks(args.figures)
    captions = compare_captions(tex, figures_p2.CAPTIONS, caption_exceptions())
    args.sheet.parent.mkdir(parents=True, exist_ok=True)
    args.sheet.write_text(sheet(checks, shapes, captions, args.results))
    for slot, grp in checks.groupby("slot", sort=False):
        print(f"{slot}: {int(grp['ok'].sum())}/{len(grp)} ja")
    for r in checks.loc[~checks["ok"]].to_dict("records"):
        print(f"  NEIN {r['slot']} {r['check']}: {_cell(r['figure'])} gegen {_cell(r['source'])} {r['error']}")
    for r in shapes.loc[~shapes["ok"]].to_dict("records"):
        print(f"  NEIN Gestalt {r['what']}: {r['figure']} (Vorgabe {r['target']})")
    for r in captions.to_dict("records"):
        if r["status"] != "gleich":
            print(f"  Caption {r['slot']}: {r['status']} {r['note'][:160]}")
    print(f"wrote {args.sheet}")
    failed = (~checks["ok"]).any() or (~shapes["ok"]).any()
    if args.strict_captions:
        failed = failed or (~captions["status"].str.startswith("gleich")).any()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
