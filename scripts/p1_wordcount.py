#!/usr/bin/env python3
"""Count the manuscript's prose per section and report every section over its budget.

The paper is meant to be small, so the budget is a constraint and not a wish: a section that runs over is
cut, never granted more room.  Figures, captions, labels and the bibliography are not prose and do not
count; the abstract does.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

BUDGET = {
    "abstract": 150,
    "Introduction": 550,
    "The venue and the tape": 450,
    "What a markout measures": 550,
    "Pre-registration and inference": 250,
    "Results": 1100,
    "What this means for a maker": 350,
    "What this cannot show": 250,
    "Conclusion": 180,
}
TOLERANCE = 0.10

FIGURE = re.compile(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", re.S)
TABLE = re.compile(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", re.S)
COMMENT = re.compile(r"(?<!\\)%.*")
MACRO_WITH_ARG = re.compile(r"\\(label|ref|cite[a-z]*|includegraphics|bibliography[a-z]*|input)\s*(\[[^\]]*\])?\{[^}]*\}")
MACRO = re.compile(r"\\[a-zA-Z]+\*?")


def _prose(text: str) -> int:
    text = FIGURE.sub(" ", text)
    text = TABLE.sub(" ", text)
    text = COMMENT.sub(" ", text)
    text = MACRO_WITH_ARG.sub(" ", text)
    text = MACRO.sub(" ", text)
    text = re.sub(r"[{}$&~^_\\]", " ", text)
    return len([w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-.,;:%()]*", text) if any(c.isalnum() for c in w)])


def sections(tex: str) -> Dict[str, int]:
    """Words of prose per section, plus the abstract; the bibliography is not a section."""
    out: Dict[str, int] = {}
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if abstract:
        out["abstract"] = _prose(abstract.group(1))
    body = tex[tex.index("\\maketitle"):] if "\\maketitle" in tex else tex
    body = re.split(r"\\bibliographystyle", body)[0]
    parts = re.split(r"\\section\*?\{([^}]*)\}", body)
    for name, content in zip(parts[1::2], parts[2::2]):
        out[name] = out.get(name, 0) + _prose(content)
    return out


def check(tex: str, budget: Optional[Dict[str, int]] = None, tolerance: float = TOLERANCE) -> List[dict]:
    """One row per section: words, budget and whether it runs over by more than the tolerance."""
    budget = BUDGET if budget is None else budget
    rows = []
    for name, words in sections(tex).items():
        limit = budget.get(name)
        allowed = None if limit is None else int(round(limit * (1 + tolerance)))
        rows.append({"section": name, "words": words, "budget": limit, "allowed": allowed,
                     "over": bool(allowed is not None and words > allowed)})
    return rows


def main(argv: List[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else Path("paper/main.tex")
    rows = check(path.read_text())
    total = sum(r["words"] for r in rows)
    width = max(len(r["section"]) for r in rows) if rows else 10
    for r in rows:
        mark = "OVER" if r["over"] else ""
        print("{:<{w}}  {:>5}  {:>5}  {}".format(r["section"], r["words"],
                                                 r["budget"] if r["budget"] is not None else "-", mark, w=width))
    print("{:<{w}}  {:>5}  {:>5}".format("total", total, sum(v for v in BUDGET.values()), w=width))
    over = [r for r in rows if r["over"]]
    if over:
        print("\n{} section(s) over budget; cut them rather than raising the budget.".format(len(over)))
    return 1 if over else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
