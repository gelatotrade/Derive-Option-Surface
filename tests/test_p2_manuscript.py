"""Guards for statements of the Paper 2 manuscript that the audit of 25.09.2026 (docs/paper2/AUDIT.md) corrected.

The number chain (scripts/p2_number_check.py) binds every number to its source; these tests bind a few sentences:
wordings the audit found wrong may not come back, and the disclosures it asked for must stay.  Each check is a
pure function of the LaTeX source, so it can be run against an older version of the file as well.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TEX = REPO / "paper2" / "main.tex"

# Wordings the audit showed to be wrong (finding in brackets).
RETRACTED = {
    "every test runs inside it": "A07: H4 also uses the legacy-manager events of 22 February 2025",
    "last pushed before its block": "A46: the replica also takes pushes from the block of the fill",
    "days from any parameter change of the underlying": "A06: the registered placebo rule counts legacy PM and PM2",
    "not an engine only the operator": "A14: soska2021 describes a public margin formula",
    "is public code with": "A14: public are the contracts; the venue trades on an off-chain engine",
    "a narrowing by a fifth is not excluded": "A05: the range is conditional on the event dates",
    "no measurable response": "A05: write 'no detectable response'",
    "leaves open": "A60: the companion paper does not address capital",
    "bound the position in units\n\\citep{ho1981": "A15: Ho and Stoll, Avellaneda and Stoikov penalise",
    "each committed before the step it governs": "A37: Addendum 4 came after doses and the H4 panel",
    "are listed in the same file": "A40: the margin-history probes are not listed there",
    "the one maker under standard margin": "A09: M2 is a subaccount of an operator with PM books",
    "Working~paper,~\\today": "A58: the footer date may not change with every build",
}


def _prose(tex: str) -> str:
    """The document without comment lines, whitespace collapsed to single spaces except in RETRACTED keys."""
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    return tex


def retracted_found(tex: str) -> list:
    text = _prose(tex)
    flat = re.sub(r"\s+", " ", text)
    out = []
    for phrase, why in RETRACTED.items():
        if phrase in text or re.sub(r"\s+", " ", phrase) in flat:
            out.append(f"{phrase!r} ({why})")
    return out


def section(tex: str, title: str) -> str:
    """Prose of one section, from its heading to the next \\section."""
    text = _prose(tex)
    m = re.search(r"\\section\*?\{" + re.escape(title) + r"\}", text)
    if not m:
        return ""
    nxt = re.search(r"\\section\*?\{|\\bibliographystyle", text[m.end():])
    return re.sub(r"\s+", " ", text[m.end():m.end() + (nxt.start() if nxt else len(text))])


def missing_disclosures(tex: str) -> list:
    """Disclosures the audit asked for, each as (finding, where, pattern)."""
    flat = re.sub(r"\s+", " ", _prose(tex))
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", flat)
    back = section(tex, "Data, code and pre-registration")
    data = section(tex, "Data and measurement")
    checks = [
        ("A03 abstract labels the sign reading post hoc", abstract.group(1) if abstract else "", r"post hoc"),
        ("A03 convention exploratory / post hoc", data, r"exploratory, those added after the first results post hoc"),
        ("A03 appendix of post hoc results", flat, r"\\section\{Post hoc and exploratory results\}"),
        ("A02 commit times are local", back, r"local times of the author's machine"),
        ("A02 no public timestamp before the results", back, r"no public timestamp precedes the results"),
        ("A64 German original binding", back, r"German original is binding"),
        ("A64 translation named", back, r"docs/paper2/PREREGISTRATION\.md"),
        ("A37 addendum 4 after doses and panel", back, r"Addendum 4 was written after .*doses and the H4 panel"),
        ("A40 validation fixtures read maker margins", back, r"validation fixtures .* maker accounts"),
        ("A18 correction of the companion paper", data, r"companion paper was corrected on 25 September 2026"),
        ("A18 same unit as the companion paper", data, r"uses the same unit per contract"),
        ("A01 history rewrite disclosed", back, r"history was rewritten to remove account identifiers"),
        ("A01 map of old and new hashes", back, r"HISTORY_REWRITE\.md\} maps the old commit hashes"),
        ("A01 Addendum 5 records the rewrite", back, r"Addendum 5 of 27 September 2026, written after all results"),
        ("A09 wallets of the subaccounts", data, r"share a wallet"),
        ("A05 power of H4", flat, r"The test has little power"),
        ("A05 placebo-calibrated range", flat, r"Calibrated on those placebo statistics"),
        ("A17 primary source of the rules cited", flat, r"\\citep\{derivev2core\}"),
        ("A61 inference cited", data, r"\\citep\{mackinnon2017,roodman2019\}"),
    ]
    return [name for name, where, pattern in checks if not re.search(pattern, where)]


def float_order_problems(tex: str) -> list:
    """A49: every results figure comes out before the conclusion, and A1 sits in the appendix."""
    text = _prose(tex)
    out = []
    barrier = text.find("\\FloatBarrier")
    conclusion = text.find("\\section{Conclusion}")
    appendix = text.find("\\appendix")
    for slot in ("f2", "f3", "f4", "f5", "f6"):
        pos = text.find(f"figures/{slot}.pdf")
        if not (0 <= pos < barrier < conclusion):
            out.append(f"{slot} not before the float barrier ahead of the conclusion")
    if not (0 <= appendix < text.find("figures/a1.pdf")):
        out.append("a1 not in the appendix")
    return out


def metadata_problems(tex: str) -> list:
    """A57: author, subject, keywords and creator are set after \\maketitle."""
    text = _prose(tex)
    after = text[text.find("\\maketitle"):]
    want = [r"\\gdef\\@pdfauthor\{Gregor Albiez\}", r"\\gdef\\@pdfsubject\{Working paper\}", r"pdfkeywords=",
            r"pdfcreator="]
    return [w for w in want if not re.search(w, after)]


@pytest.fixture(scope="module")
def tex() -> str:
    return TEX.read_text()


def test_no_retracted_wording(tex):
    assert retracted_found(tex) == []


def test_disclosures_asked_for_by_the_audit(tex):
    assert missing_disclosures(tex) == []


def test_results_figures_before_the_conclusion(tex):
    assert float_order_problems(tex) == []


def test_pdf_metadata_overwritten(tex):
    assert metadata_problems(tex) == []


def test_checks_catch_the_version_before_the_audit():
    """The checks are not vacuous: the manuscript as audited (commit 1894bad, 3ec74f4 before the history rewrite,
    same blob) fails each of them."""
    import subprocess
    old = subprocess.run(["git", "show", "1894bad:paper2/main.tex"], cwd=REPO, capture_output=True, text=True)
    if old.returncode != 0:
        pytest.skip("commit 1894bad not available")
    assert len(retracted_found(old.stdout)) == len(RETRACTED)
    assert len(missing_disclosures(old.stdout)) >= 10
    assert float_order_problems(old.stdout)
    assert metadata_problems(old.stdout)
