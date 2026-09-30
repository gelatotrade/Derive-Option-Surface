"""Offline checks on the Paper 2 bibliography (paper2/refs.bib) and its record docs/paper2/LITERATURE.md.

Every entry is recorded in LITERATURE.md, entries shared with Paper 1 are identical character for character,
published works carry the DOI that was checked against Crossref, and the primary sources of the margin rules
(contract code and API documentation) are cited with commit and access date (audit A16, A17, A61).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
BIB2 = ROOT / "paper2" / "refs.bib"
BIB1 = ROOT / "paper" / "refs.bib"
LITERATURE = ROOT / "docs" / "paper2" / "LITERATURE.md"

ENTRY = re.compile(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,.*?^\}", re.S | re.M)

# Checked against api.crossref.org and doi.org on 25 September 2026 (docs/paper2/LITERATURE.md).
VERIFIED_DOI = {
    "fournier2020": "10.1017/S0022109019000462",
    "chen2019": "10.1093/rfs/hhy004",
    "ahn2025": "10.1093/rof/rfae039",
    "cameron2008": "10.1162/rest.90.3.414",
    "mackinnon2017": "10.1002/jae.2508",
    "roodman2019": "10.1177/1536867X19830877",
    "burlig2018": "10.1016/j.econlet.2018.03.036",
}
DOI_EXEMPT: set = set()
SHARED_WITH_PAPER1 = {"garleanu2009", "muravyev2016", "christoffersen2018",
                      "cameron2008", "mackinnon2017", "roodman2019", "burlig2018"}


def entries(text: str) -> Dict[str, Tuple[str, str]]:
    """Key -> (entry type in lower case, full entry text)."""
    return {m.group(2): (m.group(1).lower(), m.group(0)) for m in ENTRY.finditer(text)}


def field(entry: str, name: str) -> str:
    m = re.search(r"^\s*" + name + r"\s*=\s*\{(.*)\}\s*,?\s*$", entry, re.M)
    return m.group(1) if m else ""


def text(entry: str, name: str) -> str:
    """A field as printed: the braces that protect capitals from the style removed."""
    return re.sub(r"(?<!\\)[{}]", "", field(entry, name))


def test_every_entry_is_a_row_of_literature():
    lit = LITERATURE.read_text(encoding="utf-8")
    keys = entries(BIB2.read_text(encoding="utf-8"))
    assert [k for k in keys if not re.search(r"^\| " + re.escape(k) + r" \|", lit, re.M)] == []


def test_literature_states_the_number_of_entries():
    lit = LITERATURE.read_text(encoding="utf-8")
    stated = re.search(r"`paper2/refs\.bib` \((\d+) entries\)", lit)
    assert stated and int(stated.group(1)) == len(entries(BIB2.read_text(encoding="utf-8")))


def test_entries_shared_with_paper1_are_identical():
    p1 = entries(BIB1.read_text(encoding="utf-8"))
    p2 = entries(BIB2.read_text(encoding="utf-8"))
    shared = set(p1) & set(p2)
    assert SHARED_WITH_PAPER1 <= shared
    assert sorted(k for k in shared if p1[k][1] != p2[k][1]) == []


def test_published_entries_carry_the_verified_doi():
    e = entries(BIB2.read_text(encoding="utf-8"))
    assert {k: field(e[k][1], "doi") for k in VERIFIED_DOI if k in e} == VERIFIED_DOI
    no_doi = [k for k, (typ, body) in e.items()
              if typ in {"article", "inproceedings"} and not field(body, "doi") and k not in DOI_EXEMPT]
    assert no_doi == []


def test_primary_sources_of_the_rules_are_cited_with_commit_and_access_date():
    e = entries(BIB2.read_text(encoding="utf-8"))
    typ, code = e["derivev2core"]
    assert typ == "misc"
    assert field(code, "url") == "https://github.com/derivexyz/v2-core/tree/96796a6"
    assert text(code, "note").startswith("Commit 96796a6") and "accessed 24 September 2026" in text(code, "note")
    typ, api = e["derivegetmargin"]
    assert typ == "misc"
    assert field(api, "url") == "https://docs.derive.xyz/api-reference/subaccounts/publicget_margin"
    assert text(api, "title") == "public/get\\_margin"
    assert text(api, "note") == "Accessed 24 September 2026"
    # the style lower-cases a note that follows the URL unless its first letter is braced
    assert field(code, "note").startswith("{C}") and field(api, "note").startswith("{A}")
