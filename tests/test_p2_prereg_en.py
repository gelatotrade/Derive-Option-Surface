"""The English translation of the pre-registration (audit A64) follows the binding German original.

If docs/paper2/PRAEREGISTRIERUNG.md gains a dated addendum, the translation must be extended and the blob hash in
its header updated (``git hash-object docs/paper2/PRAEREGISTRIERUNG.md``).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DE = REPO / "docs" / "paper2" / "PRAEREGISTRIERUNG.md"
EN = REPO / "docs" / "paper2" / "PREREGISTRATION.md"


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _sections(text: str):
    """Heading -> number of numbered items (``1.`` at line start) below it."""
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = [line[3:], 0]
            out.append(cur)
        elif cur is not None and re.match(r"\d+\. ", line):
            cur[1] += 1
    return out


def test_translation_names_the_translated_version_of_the_original():
    m = re.search(r"git blob[\s>]+`([0-9a-f]{40})`", EN.read_text())  # may wrap inside the quote block
    assert m, "the translation must name the git blob of the German original it translates"
    assert m.group(1) == _git_blob(DE.read_bytes()), (
        "docs/paper2/PRAEREGISTRIERUNG.md changed: extend docs/paper2/PREREGISTRATION.md and update the blob")


def test_translation_is_dated_later_and_names_the_original_as_binding():
    head = EN.read_text().split("\n\n## ")[0]
    assert "Translation, not part of the registration" in head
    assert "25 September 2026" in head and "after all" in head
    assert "German" in head and "original is binding" in head
    assert "`cc0a29f`" in head and "`1d13227`" in head  # registration commit, and its hash before the rewrite


def test_every_section_addendum_and_item_is_translated():
    de = _sections(DE.read_text())
    en = _sections(EN.read_text())
    assert len(en) == len(de) == 13  # seven sections, six addenda
    assert [n for _, n in en] == [n for _, n in de]
    # the headings of the binding German original, matched verbatim ("Nachtrag 1 (25.09.2026, ...")
    de_add = [re.match(r"Nachtrag (\d+) \((\d+)\.(\d+)\.(\d{4})", h).groups() for h, _ in de if h.startswith("Nachtrag")]
    en_add = [re.match(r"Addendum (\d+) \((\d+) September (\d{4})", h).groups() for h, _ in en
              if h.startswith("Addendum")]
    assert [a[0] for a in en_add] == [a[0] for a in de_add] == ["1", "2", "3", "4", "5", "6"]
    assert all((d[1], d[3]) == (e[1], e[2]) and d[2] == "09" for d, e in zip(de_add, en_add))
    for h in ("**H1 ranking:**", "**H2 marginal cost:**", "**H3 netting value:**", "**H4 price of capital:**"):
        assert h in EN.read_text()
