#!/usr/bin/env python3
"""Count the prose of the Paper 2 manuscript per section and report every section over its budget.

Same counting rule as ``p1_wordcount.py``: figures, tables, captions, comments, labels, references and the
bibliography are not prose and do not count; formulas and the abstract do.  Unlike Paper 1 the budget is a
parameter: ``check`` takes any budget, tolerance and set of hard limits, and the command line can read a
budget from a JSON file.  The default is the budget of ``docs/paper2/MANUSCRIPT.md`` with a tolerance of
ten per cent; the abstract is a hard limit of 200 words without tolerance.

    python3 scripts/p2_wordcount.py [paper2/main.tex] [--budget budget.json] [--tolerance 0.1]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

TEX = Path("paper2/main.tex")

BUDGET: Dict[str, int] = {
    "abstract": 200,
    "Introduction": 600,
    "The engine and what it returns": 600,
    "Data and measurement": 600,
    "Results": 1400,
    "Discussion": 400,
    "Conclusion": 200,
}
TOLERANCE = 0.10
HARD = frozenset({"abstract"})          # limits that the tolerance does not stretch

FIGURE = re.compile(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", re.S)
TABLE = re.compile(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", re.S)
COMMENT = re.compile(r"(?<!\\)%.*")
MACRO_WITH_ARG = re.compile(
    r"\\(label|ref|eqref|cite[a-z]*|includegraphics|bibliography[a-z]*|input|url)\s*(\[[^\]]*\])?\{[^}]*\}")
MACRO = re.compile(r"\\[a-zA-Z]+\*?")
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-.,;:%()]*")


def prose_words(text: str) -> int:
    """Words of prose in a piece of LaTeX, with the rule of Paper 1."""
    text = COMMENT.sub(" ", text)
    text = FIGURE.sub(" ", text)
    text = TABLE.sub(" ", text)
    text = MACRO_WITH_ARG.sub(" ", text)
    text = MACRO.sub(" ", text)
    text = re.sub(r"[{}$&~^_\\]", " ", text)
    return len([w for w in WORD.findall(text) if any(c.isalnum() for c in w)])


def sections(tex: str) -> Dict[str, int]:
    """Words of prose per section, plus the abstract; the bibliography is not a section."""
    tex = COMMENT.sub(" ", tex)
    out: Dict[str, int] = {}
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if abstract:
        out["abstract"] = prose_words(abstract.group(1))
    body = tex[tex.index("\\maketitle"):] if "\\maketitle" in tex else tex
    body = re.split(r"\\bibliographystyle", body)[0]
    parts = re.split(r"\\section\*?\{([^}]*)\}", body)
    for name, content in zip(parts[1::2], parts[2::2]):
        out[name] = out.get(name, 0) + prose_words(content)
    return out


def check(tex: str, budget: Optional[Dict[str, int]] = None, tolerance: float = TOLERANCE,
          hard: Iterable[str] = HARD) -> List[dict]:
    """One row per section: words, budget, allowed words and whether the section runs over.

    A section in ``hard`` may not exceed its budget at all; every other budgeted section may exceed it by
    ``tolerance``.  Sections without a budget are reported and never over.  A budgeted section that is missing
    from the manuscript is reported with ``missing = True``.
    """
    budget = BUDGET if budget is None else budget
    hard = set(hard)
    rows = []
    counted = sections(tex)
    for name, words in counted.items():
        limit = budget.get(name)
        if limit is None:
            allowed = None
        elif name in hard:
            allowed = int(limit)
        else:
            allowed = int(round(limit * (1 + tolerance)))
        rows.append({"section": name, "words": words, "budget": limit, "allowed": allowed,
                     "over": bool(allowed is not None and words > allowed), "missing": False})
    for name, limit in budget.items():
        if name not in counted:
            rows.append({"section": name, "words": 0, "budget": limit, "allowed": None, "over": False,
                         "missing": True})
    return rows


def render(rows: List[dict]) -> str:
    width = max([len(r["section"]) for r in rows] + [10])
    lines = ["{:<{w}}  {:>5}  {:>6}  {:>7}".format("section", "words", "budget", "allowed", w=width)]
    for r in rows:
        mark = "OVER" if r["over"] else ("MISSING" if r["missing"] else "")
        lines.append("{:<{w}}  {:>5}  {:>6}  {:>7}  {}".format(
            r["section"], r["words"], "-" if r["budget"] is None else r["budget"],
            "-" if r["allowed"] is None else r["allowed"], mark, w=width))
    budgeted = [r for r in rows if r["budget"] is not None]
    lines.append("{:<{w}}  {:>5}  {:>6}".format("total (budgeted)", sum(r["words"] for r in budgeted),
                                               sum(r["budget"] for r in budgeted), w=width))
    lines.append("{:<{w}}  {:>5}".format("total (all)", sum(r["words"] for r in rows), w=width))
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tex", nargs="?", default=str(TEX))
    ap.add_argument("--budget", help="JSON file {section: words}; replaces the default budget")
    ap.add_argument("--tolerance", type=float, default=TOLERANCE)
    ap.add_argument("--hard", nargs="*", default=sorted(HARD), help="sections without tolerance")
    args = ap.parse_args(argv)
    budget = json.loads(Path(args.budget).read_text()) if args.budget else BUDGET
    rows = check(Path(args.tex).read_text(), budget, args.tolerance, args.hard)
    print(render(rows))
    over = [r for r in rows if r["over"]]
    missing = [r for r in rows if r["missing"]]
    if over:
        print("\n{} section(s) over budget: {}. Cut them rather than raising the budget.".format(
            len(over), ", ".join(r["section"] for r in over)))
    if missing:
        print("\nbudgeted but not found: {}".format(", ".join(r["section"] for r in missing)))
    return 1 if (over or missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
