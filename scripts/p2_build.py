#!/usr/bin/env python3
"""Build the Paper 2 manuscript and refuse to call a flawed run a success.

tectonic keeps going after a recoverable LaTeX error and still writes a PDF, so a missing section can hide
behind a clean-looking console.  This builds ``paper2/main.tex`` with the full log kept, then fails on any of:

* an error in the log or a non-zero exit of tectonic;
* an overfull box, an undefined reference or citation, a missing file, or ``??`` in the PDF text;
* a required part missing from the PDF (sections, back matter, references, JEL codes, the abstract);
* a placeholder ``\\PH{...}`` left in the text, or a dash (em or en dash, ``--``, a spaced hyphen) in the prose;
* a citation key that is not in ``paper2/refs.bib`` or not among the checked sources of
  ``docs/paper2/LITERATURE.md``;
* a figure slot missing, a figure file missing, or a figure never referenced in the text;
* a caption that differs from the ``CAPTION`` of ``derive_surface/figs_p2/<slot>.py`` where that module has one
  (a ``\\PH{key}`` in the module caption stands for any number in the manuscript; deliberate departures are
  listed with their reason in ``CAPTION_EXCEPTIONS`` and printed on every build);
* a section over its word budget (``p2_wordcount.py``);
* a number, date or clock time in the text that ``p2_number_check.py`` finds without its declaration or
  that its declared source no longer covers, and a declaration that binds no number of its unit (every
  number is declared in its unit, one entry per occurrence, in the order of the text);
* a figure that prints more than one page away from its first callout in the running text, or a page that
  holds figures and no running text (layout, read from the PDF).  A figure one page before its first callout
  is printed as a note: in Section 4 every page carries a figure, and no order of the floats avoids it.

    python3 scripts/p2_build.py [--allow-caption-drift] [--no-numbers]

Exit status 0 only if nothing of the above was found.  The PDF is written to ``paper2/main.pdf``.
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2_number_check as nc  # noqa: E402
import p2_wordcount as wc  # noqa: E402

PAPER = Path("paper2")
BIB = PAPER / "refs.bib"
LITERATURE = Path("docs/paper2/LITERATURE.md")
FIGS = Path("derive_surface/figs_p2")
RESULTS = Path("results/p2")
SLOTS = ["t1", "t2", "f1", "f2", "f3", "f4", "f5", "f6", "a1"]
MUST_CONTAIN = ["A B S T R A C T", "Introduction", "The engine and what it returns", "Data and measurement",
                "Results", "Discussion", "Conclusion", "Data, code and pre-registration", "Competing interest",
                "Use of generative tools", "References", "G13"]

COMMENT = re.compile(r"(?<!\\)%.*")


# ---------------------------------------------------------------------------------------------------------------
# Compile
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class Compiled:
    returncode: int
    console: str
    log: str
    pdf: Optional[Path]


def compile_pdf(paper: Path = PAPER, runner: Callable = subprocess.run) -> Compiled:
    """tectonic with the log kept; the PDF is copied to ``paper/main.pdf``."""
    with tempfile.TemporaryDirectory() as tmp:
        run = runner(["tectonic", "--keep-logs", "--outdir", tmp, "main.tex"], cwd=str(paper),
                     capture_output=True, text=True)
        log_path = Path(tmp) / "main.log"
        log = log_path.read_text(errors="replace") if log_path.exists() else ""
        pdf = None
        if (Path(tmp) / "main.pdf").exists():
            pdf = paper / "main.pdf"
            shutil.copyfile(Path(tmp) / "main.pdf", pdf)
        return Compiled(run.returncode, (run.stdout or "") + (run.stderr or ""), log, pdf)


def log_problems(log: str, console: str = "") -> Dict[str, List[str]]:
    """Errors, overfull boxes, undefined references and citations, and missing files in a TeX log."""
    lines = log.splitlines()
    out = {
        "errors": [l for l in lines if l.startswith("! ")] +
                  [l for l in console.splitlines() if l.lower().startswith("error")],
        "overfull": [l for l in lines if re.search(r"Overfull \\[hv]box", l)],
        "undefined references": [l for l in lines if re.search(r"Reference `[^']*' on page \S+ undefined", l)],
        "undefined citations": [l for l in lines if re.search(r"Citation `[^']*' on page \S+ undefined", l)],
        "missing files": [l for l in lines if re.search(r"File `[^']*' not found|LaTeX Error: File", l)],
    }
    if "There were undefined references" in log and not out["undefined references"]:
        out["undefined references"].append("There were undefined references.")
    return out


def pdf_text(pdf: Path) -> Tuple[int, str]:
    import pypdf
    reader = pypdf.PdfReader(str(pdf))
    return len(reader.pages), " ".join((page.extract_text() or "") for page in reader.pages)


def pdf_problems(text: str, must: Sequence[str] = MUST_CONTAIN) -> Dict[str, List[str]]:
    return {"missing parts": [m for m in must if m not in text],
            "unresolved ?? in PDF": ["??"] if "??" in text else []}


# Running text is set in STIX (cas-dc), captions in Latin Modern Sans and the labels inside the figures in DejaVu
# Sans (matplotlib), so the font tells a callout in the text from one in a caption or a figure.
BODY_FONT = re.compile(r"STIX|Charis")
CAPTION_LABEL = re.compile(r"^\s*Figure (\d+):")
CALLOUT = re.compile(r"Figures?\s+(\d+)((?:\s*(?:,|and)\s*\d+)*)")
MARGIN_PT = 50          # header and footer lie within this distance of the top and bottom edge of the page
MIN_BODY_CHARS = 100    # less running text than this on a page with figures: a page of figures only


@dataclass
class PageLayout:
    figures: List[int]      # numbers of the figures whose caption is on the page
    callouts: List[int]     # figures cited in the running text of the page
    body_chars: int         # characters of running text, header and footer left out


def pdf_layout(pdf: Path) -> List[PageLayout]:
    """Per page: the figures printed on it, the figures its running text cites and the amount of running text."""
    import pypdf
    pages = []
    for page in pypdf.PdfReader(str(pdf)).pages:
        height = float(page.mediabox.height)
        body: List[str] = []
        figures: List[int] = []

        def visit(text, cm, tm, font, size):
            if not text.strip():
                return
            name = str(font.get("/BaseFont", "")) if font else ""
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            if BODY_FONT.search(name):
                if MARGIN_PT < y < height - MARGIN_PT:
                    body.append(text)
            else:
                m = CAPTION_LABEL.match(text)
                if m:
                    figures.append(int(m.group(1)))

        page.extract_text(visitor_text=visit)
        joined = " ".join(body)
        callouts = []
        for m in CALLOUT.finditer(joined):
            callouts += [int(m.group(1))] + [int(n) for n in re.findall(r"\d+", m.group(2))]
        pages.append(PageLayout(figures, sorted(set(callouts)), len(re.sub(r"\s", "", joined))))
    return pages


def layout_problems(pages: Sequence[PageLayout]) -> Tuple[Dict[str, List[str]], List[str]]:
    """Problems of the float placement (PDF audit L2) and notes on figures one page before their first callout."""
    first: Dict[int, int] = {}
    for no, page in enumerate(pages, 1):
        for n in page.callouts:
            first.setdefault(n, no)
    far, alone, notes = [], [], []
    for no, page in enumerate(pages, 1):
        for n in page.figures:
            if n not in first:
                continue
            gap = no - first[n]
            where = "Figure {} on page {}, first cited in the text on page {}".format(n, no, first[n])
            if gap > 1 or gap < -1:
                far.append(where)
            elif gap == -1:
                notes.append(where)
        if page.figures and page.body_chars < MIN_BODY_CHARS:
            alone.append("page {}: Figure {}".format(no, ", ".join(str(n) for n in page.figures)))
    return {"figure far from its first callout": far, "page of figures only": alone}, notes


# ---------------------------------------------------------------------------------------------------------------
# Source checks
# ---------------------------------------------------------------------------------------------------------------
def body(tex: str) -> str:
    """The document from \\begin{document} on, without comments."""
    tex = COMMENT.sub("", tex)
    return tex[tex.index("\\begin{document}"):] if "\\begin{document}" in tex else tex


MATH = re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}.*?\\end\{\1\}|\\\[.*?\\\]|"
                  r"(?<!\\)\$.*?(?<!\\)\$", re.S)
ARGS = re.compile(r"\\(url|href|label|ref|eqref|cite[a-z]*|includegraphics|texttt)\s*(\[[^\]]*\])?\{[^}]*\}")
DASHES = [("--", re.compile(r"--")), ("en or em dash", re.compile("[\u2013\u2014]")),
          ("spaced hyphen", re.compile(r"(?<=[A-Za-z0-9,.;)])\s+-\s+(?=[A-Za-z0-9(])"))]


def placeholders(tex: str) -> List[str]:
    return re.findall(r"\\PH\{[^}]*\}", body(tex))


def dashes(tex: str) -> List[str]:
    """Dashes in the prose, outside math, URLs, labels and code; with some context."""
    text = ARGS.sub(" ", MATH.sub(" ", body(tex)))
    out = []
    for name, pattern in DASHES:
        for m in pattern.finditer(text):
            ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 30):m.end() + 30])
            out.append("{}: ...{}...".format(name, ctx))
    return out


def bib_keys(bib: str) -> List[str]:
    return re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib)


def cited(tex: str) -> List[str]:
    keys: List[str] = []
    for m in re.finditer(r"\\cite[a-z]*\s*(?:\[[^\]]*\])*\{([^}]*)\}", body(tex)):
        keys += [k.strip() for k in m.group(1).split(",") if k.strip()]
    return keys


def citation_problems(tex: str, bib: str, literature: str) -> Dict[str, List[str]]:
    known = set(bib_keys(bib))
    keys = sorted(set(cited(tex)))
    return {"citations not in refs.bib": [k for k in keys if k not in known],
            "citations not in LITERATURE.md": [k for k in keys if not re.search(r"\b" + re.escape(k) + r"\b",
                                                                                 literature)]}


def figure_problems(tex: str, paper: Path, slots: Sequence[str] = SLOTS) -> Dict[str, List[str]]:
    text = body(tex)
    graphics = re.findall(r"\\includegraphics\s*(?:\[[^\]]*\])?\{([^}]*)\}", text)
    missing_files = [g for g in graphics if not (paper / g).exists() and not (paper / (g + ".pdf")).exists()]
    included = {Path(g).stem for g in graphics}
    floats = FIGURE.findall(text)
    labels = [m for _, block in floats for m in re.findall(r"\\label\{([^}]*)\}", block)]
    outside = FIGURE.sub(" ", text)
    unreferenced = [l for l in labels if not re.search(r"\\ref\{" + re.escape(l) + r"\}", outside)]
    return {"figure slots missing": [s for s in slots if s not in included],
            "figure files missing": missing_files,
            "figures never referenced": unreferenced}


FIGURE = re.compile(r"\\begin\{(figure\*?)\}(.*?)\\end\{\1\}", re.S)


def tex_captions(tex: str) -> Dict[str, str]:
    """Caption text per figure file stem, with the bold title unwrapped."""
    out = {}
    for _, block in FIGURE.findall(body(tex)):
        g = re.search(r"\\includegraphics\s*(?:\[[^\]]*\])?\{([^}]*)\}", block)
        caps = nc.captions(block)
        if g and caps:
            out[Path(g.group(1)).stem] = caps[0]
    return out


def _evaluate(node: ast.AST, names: Dict[str, ast.AST], depth: int = 0) -> Optional[str]:
    """String value of a module-level expression built from literals, names, ``+`` and ``" ".join([...])``."""
    if depth > 20:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in names:
        return _evaluate(names[node.id], names, depth + 1)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _evaluate(node.left, names, depth + 1), _evaluate(node.right, names, depth + 1)
        return None if left is None or right is None else left + right
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "join"
            and len(node.args) == 1 and isinstance(node.args[0], (ast.List, ast.Tuple))):
        sep = _evaluate(node.func.value, names, depth + 1)
        parts = [_evaluate(e, names, depth + 1) for e in node.args[0].elts]
        return None if sep is None or any(p is None for p in parts) else sep.join(parts)
    return None


def module_caption(path: Path) -> Optional[str]:
    """The string assigned to ``CAPTION`` at module level, evaluated without importing the module."""
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, OSError):
        return None
    names: Dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names[t.id] = node.value
    return _evaluate(names["CAPTION"], names) if "CAPTION" in names else None


def _norm(s: str) -> str:
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


# Deliberate departures from a module caption: (slot, text in the module caption, text in the manuscript, reason).
CAPTION_EXCEPTIONS: List[Tuple[str, str, str, str]] = [
    ("f2", r"The map per notional is Figure~\PH{p1-map-fig} of the companion paper.",
     r"The map per notional is not drawn; its ranks enter panel b.",
     "Paper 1 draws its map per notional (its Figure 5) with the net edge per contract over the notional of the "
     "whole fill; the finding of 25 September 2026 (docs/paper1/FINDING_2026-09-25_FEE_UNITS.md) revises it, so "
     "the manuscript does not point to it."),
]


def caption_drift(tex: str, figs: Path = FIGS,
                  exceptions: Sequence[Tuple[str, str, str, str]] = CAPTION_EXCEPTIONS) -> List[str]:
    """Slots whose manuscript caption differs from the CAPTION of ``figs/<slot>.py``, after the exceptions."""
    out = []
    caps = tex_captions(tex)
    for slot, cap in sorted(caps.items()):
        module = figs / (slot + ".py")
        if not module.exists():
            continue
        ref = module_caption(module)
        if ref is None:
            continue
        for ex_slot, old, new, _ in exceptions:
            if ex_slot == slot:
                ref = ref.replace(old, new)
        parts = re.split(r"\\PH\{[^}]*\}", _norm(ref))
        pattern = r"(?:.+?)".join(re.escape(p) for p in parts)
        if not re.fullmatch(pattern, _norm(cap)):
            out.append(slot)
    return out


# ---------------------------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class Report:
    problems: Dict[str, List[str]] = field(default_factory=dict)
    pages: int = 0
    words: int = 0
    budget_rows: List[dict] = field(default_factory=list)
    numbers: int = 0
    layout_notes: List[str] = field(default_factory=list)

    def failed(self) -> List[str]:
        return [k for k, v in self.problems.items() if v]


def check_sources(tex: str, paper: Path = PAPER, bib: str = "", literature: str = "", figs: Path = FIGS,
                  results: Path = RESULTS, numbers: bool = True, allow_caption_drift: bool = False,
                  resolve_commit: Optional[Callable[[str], bool]] = None,
                  budget: Optional[Dict[str, int]] = None, slots: Sequence[str] = SLOTS) -> Report:
    """Everything that can be checked without compiling."""
    rep = Report()
    rep.problems["placeholders"] = placeholders(tex)
    rep.problems["dashes in prose"] = dashes(tex)
    rep.problems.update(citation_problems(tex, bib, literature))
    rep.problems.update(figure_problems(tex, paper, slots))
    drift = caption_drift(tex, figs)
    rep.problems["caption differs from figs_p2 CAPTION"] = [] if allow_caption_drift else drift
    rows = wc.check(tex, budget)
    rep.budget_rows = rows
    rep.words = sum(r["words"] for r in rows)
    rep.problems["over word budget"] = ["{} ({} > {})".format(r["section"], r["words"], r["allowed"])
                                        for r in rows if r["over"]]
    rep.problems["budgeted section missing"] = [r["section"] for r in rows if r["missing"]]
    if numbers:
        verdicts = nc.check(tex, results, resolve_commit=resolve_commit)
        rep.numbers = sum(1 for v in verdicts if v.how != "decl")
        rep.problems["numbers without source"] = ["{}: {} ({})".format(v.unit, v.token.rel + v.token.raw, v.detail)
                                                  for v in verdicts if not v.ok and v.how != "decl"]
        rep.problems["number declarations unused or invalid"] = [
            "{}: {} (line {}: {})".format(v.unit, v.token.raw, v.line, v.detail) for v in verdicts if v.how == "decl"]
    return rep


def build(paper: Path = PAPER, runner: Callable = subprocess.run, numbers: bool = True,
          allow_caption_drift: bool = False, read_pdf: Callable[[Path], Tuple[int, str]] = pdf_text,
          read_layout: Callable[[Path], Sequence[PageLayout]] = pdf_layout,
          resolve_commit: Optional[Callable[[str], bool]] = None, results: Path = RESULTS,
          literature_path: Path = LITERATURE, figs: Path = FIGS, budget: Optional[Dict[str, int]] = None,
          slots: Sequence[str] = SLOTS, must: Sequence[str] = MUST_CONTAIN) -> Report:
    """Source checks, then tectonic, then the log and the PDF; every argument can be replaced in a test."""
    tex = (paper / "main.tex").read_text()
    bib = (paper / "refs.bib").read_text() if (paper / "refs.bib").exists() else ""
    literature = literature_path.read_text() if literature_path.exists() else ""
    rep = check_sources(tex, paper, bib, literature, figs, results, numbers, allow_caption_drift, resolve_commit,
                        budget, slots)
    compiled = compile_pdf(paper, runner)
    logp = log_problems(compiled.log, compiled.console)
    if compiled.returncode != 0:
        logp["errors"] = logp["errors"] + ["tectonic exited with {}".format(compiled.returncode)]
    if not compiled.log:
        logp["errors"] = logp["errors"] + ["no log written"]
    rep.problems.update(logp)
    if compiled.pdf is None:
        rep.problems["missing parts"] = ["no PDF written"]
        return rep
    rep.pages, text = read_pdf(compiled.pdf)
    rep.problems.update(pdf_problems(text, must))
    layout, rep.layout_notes = layout_problems(read_layout(compiled.pdf))
    rep.problems.update(layout)
    return rep


def render(rep: Report) -> str:
    lines = ["pages           {}".format(rep.pages),
             "words           {}".format(rep.words),
             "numbers checked {}".format(rep.numbers)]
    for key, items in rep.problems.items():
        lines.append("{:<40}{}".format(key, len(items) if items else "none"))
    for key in rep.failed():
        lines.append("")
        lines.append(key + ":")
        lines += ["  " + str(i) for i in rep.problems[key][:12]]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--allow-caption-drift", action="store_true",
                    help="report captions that differ from derive_surface/figs_p2 without failing")
    ap.add_argument("--no-numbers", action="store_true", help="skip the number check")
    args = ap.parse_args(argv)
    rep = build(numbers=not args.no_numbers, allow_caption_drift=args.allow_caption_drift)
    print(render(rep))
    for slot, _, new, reason in CAPTION_EXCEPTIONS:
        print("\ncaption {} departs from its module on purpose: \"{}\" ({})".format(slot, new, reason))
    for note in rep.layout_notes:
        print("\nlayout note: {} (one page before its first callout)".format(note))
    if args.allow_caption_drift:
        drift = caption_drift((PAPER / "main.tex").read_text())
        if drift:
            print("\ncaption drift (allowed): {}".format(", ".join(drift)))
    if rep.failed():
        print("\nBUILD NOT CLEAN: {}".format(", ".join(rep.failed())))
        return 1
    print("\nbuild clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
