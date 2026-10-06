"""Guards for statements of the Paper 2 manuscript that the audit of 25.09.2026 (docs/paper2/AUDIT.md) corrected.

The number chain (scripts/p2_number_check.py) binds every number to its source; these tests bind a few sentences:
wordings the audit found wrong may not come back, and the disclosures it asked for must stay.  Each check is a
pure function of the LaTeX source, so it can be run against an older version of the file as well.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

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


# Wordings and settings that the audit of the rendered PDF (5 October 2026) replaced (finding in brackets).
WITHDRAWN = {
    "hypothetical portfolios, not account balances": "R6: the actual books are not hypothetical",
    "Figures are from a pilot cut": "B3: the numbers are preliminary; give the date of the pilot cut",
    "its contracts can be called at any past block": "R3: code is 'smart contracts', 'contracts' are options",
    "Two of the four are rejected": "R1: name the rejected hypotheses",
    "longnamesfirst": "T12: works of three or more authors cite as et al.",
    "\\sep JEL:": "B11: the JEL codes go into the template's \\JEL",
    "the standard library": "R8/T2: a 'library' is a PM2 parameter set, and 'standard' means SM",
    "Fills against the book's binding scenario": "R18: say that the fill offsets or adds to the worst-scenario loss",
    "between fill price and the SVI mark": "T1: SVI is written out at its first use",
    "Pooled, the net edge is 3.38": "R11: the pooled edge per fill is a flow, not a return per unit of time",
    "the next single contract; Addendum 4 chose": "R17: the H2 estimate comes before the provenance of the measure",
    "of the straddle by 22.9 per cent": "R9: the simple change stands next to the log change of the same step",
    "The top of the capital map rests on": "R12: the H1 verdict comes first; the top cells owe their edge to RFQ legs "
                                           "and the SVI mark (post hoc)",
    "a narrowing of that size": "R19: give the narrowing the test cannot exclude (39 per cent, Section 4.4)",
    "Capital is measured on hypothetical portfolios": "R6: capital is measured on positions",
    "and two are rejected": "R1: name the rejected hypotheses",
    "public contracts with parameters on chain": "R3: the rules are smart contracts",
    "Four dated addenda of 25 September 2026 (UTC+2) follow": "B8/R16: six addenda, the first four of 25 September",
    "its library counts as offsetting risk": "T2/R8: a 'library' is a PM2 parameter set",
    "the account libraries": "T2/R8: a 'library' is a PM2 parameter set",
    "The history uses the on-chain semantics": "R5: capital follows the on-chain engine; no 'history', no 'semantics'",
}

# url.sty's default break characters. Each must stay in \UrlBreaks or \UrlOrds: a character in neither list
# keeps its math code and prints in a wrong glyph (")" came out as "/" in a DOI).
URL_DEFAULT_BREAKS = ".@\\/!_|;>]),?&'+=#"


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


def withdrawn_found(tex: str) -> list:
    flat = re.sub(r"\s+", " ", _prose(tex))
    return [f"{phrase!r} ({why})" for phrase, why in WITHDRAWN.items() if phrase in flat]


def _do_list(pre: str, name: str) -> Optional[str]:
    """The characters of a url.sty list such as \\def\\UrlBreaks{\\do\\.\\do+...}, or None if it is not redefined."""
    m = re.search(r"\\def\\" + name + r"\{(.*)\}\s*$", pre, re.M)
    if not m:
        return None
    return "".join(re.findall(r"\\do\\?(.)", m.group(1)))


def typesetting_problems(tex: str) -> list:
    """Preamble fixes of the PDF audit of 5 October 2026: no URL, path or DOI breaks after a dot or after the colon
    of "https:" and no character lost from url.sty's lists (B4, T7, L5, B6), page 1 numbered in the footer font of
    every page (L6), numbered bookmarks (B10), the JEL codes in the template's \\JEL (B11), no reference that leaves
    a single line in the next column, and a balanced last page (L1)."""
    text = _prose(tex)
    pre = text[:text.find("\\begin{document}")]
    out = []
    breaks, ords = _do_list(pre, "UrlBreaks"), _do_list(pre, "UrlOrds")
    if breaks is None or "." in breaks:
        out.append("B4: url.sty may break after a dot")
    else:
        lost = [c for c in URL_DEFAULT_BREAKS if c not in breaks and c not in (ords or "")]
        if lost:
            out.append("B4: characters in neither \\UrlBreaks nor \\UrlOrds: " + "".join(lost))
    big = _do_list(pre, "UrlBigBreaks")
    if big is None or ":" in big or ":" not in (ords or ""):
        out.append("L5: url.sty may break after the colon of https:")
    if "\\cs_set_eq:NN \\__first_foot: \\__cas_foot:" not in pre:
        out.append("L6: page 1 sets its number outside the footer font")
    if "bookmarksnumbered=true" not in pre:
        out.append("B10: bookmarks without section numbers")
    if "\\JEL{" not in text:
        out.append("B11: JEL codes not in \\JEL")
    # natbib's thebibliography sets both penalties to 4000; only a patch at its end restores the class value.
    if not re.search(r"\\apptocmd\{\\thebibliography\}\{\\clubpenalty\\@M\s*\\widowpenalty\\@M\}", pre):
        out.append("L1: a reference may leave its last line alone in the next column")
    if not re.search(r"\\AddToHook\{shipout/after\}\{.*\\lastpage.*\\balance", pre):
        out.append("L1: the columns of the last page are not balanced")
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
        ("A02 public timestamp after the pilot, before the final run", back,
         r"after the results on the pilot cut, .{0,120}before the final data run"),
        ("A64 German original binding", back, r"German original is binding"),
        ("A64 translation named", back, r"docs/paper2/PREREGISTRATION\.md"),
        ("A37 addendum 4 after doses and panel", back, r"Addendum[ ~]4 was written after .*doses and the H4 panel"),
        ("A40 validation fixtures read maker margins", back, r"validation fixtures .* maker (?:sub)?accounts"),
        ("A18 correction of the companion paper", data, r"companion paper was corrected on 25[ ~]September 2026"),
        ("A18 same unit as the companion paper", data, r"uses the same unit per contract"),
        ("A01 history rewrite disclosed", back, r"history was rewritten twice, the first\s+time to remove account identifiers"),
        ("A01 map of old and new hashes", back, r"Addenda[ ~]5 and[ ~]7 list the old and the new hashes of every registration commit"),
        ("A01 Addenda 5 and 7 record the rewrites", back,
         r"Addendum[ ~]5 of 27[ ~]September 2026 \(\\texttt\{[0-9a-f]{7,40}\}\) and Addendum[ ~]7 of 5[ ~]October 2026 "
         r"\(\\texttt\{[0-9a-f]{7,40}\}\), both\s+written after the results on the pilot cut"),
        ("A09 wallets of the subaccounts", data, r"share a wallet"),
        ("A05 power of H4", flat, r"The test has little power"),
        ("A05 placebo-calibrated range", flat, r"Calibrated on those placebo statistics"),
        ("A17 primary source of the rules cited", flat, r"\\citep\{derivev2core\}"),
        ("A61 inference cited", data, r"\\citep\{mackinnon2017,roodman2019\}"),
        ("C4 Addendum 6 sensitivity reported with the others", flat,
         r"\\subsection\{Sensitivities\}(?:(?!\\section).)*fee of an RFQ package spread over its legs"),
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


def test_no_withdrawn_wording(tex):
    assert withdrawn_found(tex) == []


def test_typesetting_fixes_of_the_pdf_audit(tex):
    assert typesetting_problems(tex) == []


def test_typesetting_check_names_a_character_lost_from_the_url_lists():
    pre = "\\def\\UrlBreaks{\\do\\/\\do\\_}\n\\begin{document}\n"
    lost = [p for p in typesetting_problems(pre) if p.startswith("B4")]
    assert lost and ")" in lost[0] and "." not in lost[0].split(": ")[1]


def test_checks_catch_the_version_before_the_audit():
    """The checks are not vacuous: the manuscript as audited (commit 5e256d8; 1894bad until 5 October and
    3ec74f4 until 27 September 2026, same blob) fails each of them."""
    import subprocess
    old = subprocess.run(["git", "show", "5e256d8:paper2/main.tex"], cwd=REPO, capture_output=True, text=True)
    if old.returncode != 0:
        pytest.skip("commit 5e256d8 not available")
    assert len(retracted_found(old.stdout)) == len(RETRACTED)
    assert len(missing_disclosures(old.stdout)) >= 10
    assert float_order_problems(old.stdout)
    assert metadata_problems(old.stdout)


def test_checks_catch_the_version_before_the_pdf_audit():
    """The manuscript as committed before the fixes of the PDF audit of 5 October 2026 (commit 6e011fb, 4e36d9e until the rewrite of 5 October 2026) holds every
    withdrawn wording and fails every typesetting check."""
    import subprocess
    old = subprocess.run(["git", "show", "6e011fb:paper2/main.tex"], cwd=REPO, capture_output=True, text=True)
    if old.returncode != 0:
        pytest.skip("commit 6e011fb not available")
    assert len(withdrawn_found(old.stdout)) == len(WITHDRAWN)
    assert len(typesetting_problems(old.stdout)) == 7
