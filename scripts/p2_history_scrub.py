#!/usr/bin/env python3
"""Scrub account identifiers from the Paper 2 history on a NEW branch (audit A01, Nachtrag 1.4).

Guide with the full command sequence: docs/paper2/HISTORIE_BEREINIGEN.md. Short form:

    git branch paper2-kapital-bereinigt paper2-kapital
    FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch \\
        --index-filter 'python3 "<repo>/scripts/p2_history_scrub.py" index' -- e7361d2^..paper2-kapital-bereinigt
    python3 scripts/p2_history_scrub.py check 1d13227^..paper2-kapital-bereinigt

``index`` works on the index of one commit (as git filter-branch --index-filter calls it):

1. it removes the account-identifying chain fixtures (``MOVED_FIXTURES``, now in data/p2/fixtures_private);
2. in text files under results/p2, docs/paper2, paper2 and tests it replaces every unsalted ``sha256(str(id))[:10]``
   (reversed by enumeration of the ids below ``LIMIT``) by the p2ids label of the id (M1..M10 or salted X label);
3. in tests/ it replaces raw top-maker ids with at least five digits by ``PLACEHOLDER_ID`` and, in a
   tests/test_p2_ids.py whose ``TOP`` line is the real ranked list, every top-maker id by ``SYNTHETIC_TOP``.

``check`` scans every commit of a revision range and prints counts per file (never ids or hashes); exit code 1 if
anything is left. The script holds no ids: the ranked list and the salt are read from data/p2 of this checkout
(``--top``, ``--salt``). Files outside the Paper 2 roots (Paper 1) are never changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
TOP_PATH = REPO / "data" / "p2" / "books" / "top_makers.json"
SALT_PATH = REPO / "data" / "p2" / "secret_salt.txt"

MOVED_FIXTURES = tuple(f"tests/fixtures/p2/{name}" for name in (
    "pm_chain_accounts.json", "sm_chain_accounts.json", "books_chain_snapshot.json", "books_events_day.json",
    "b1_chain_cases.json", "gen_b1_fixture.py"))
SCRUB_ROOTS = ("results/p2/", "docs/paper2/", "paper2/", "tests/")
TEXT_SUFFIXES = (".json", ".jsonl", ".csv", ".md", ".txt", ".tex", ".bib", ".tsv", ".py")
SYNTHETIC_TOP = [104, 101, 110, 107, 102, 109, 103, 108, 105, 106]  # as in tests/test_p2_ids.py
PLACEHOLDER_ID = 4242
LONG_ID = 10_000  # shorter ids collide with strikes and counts
LIMIT = 250_000  # enumeration bound, as in the guard of tests/test_p2_ids.py
IDS_TEST = "tests/test_p2_ids.py"

HASH_TOKEN = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{10}(?![0-9a-fA-F])")
INT_TOKEN = re.compile(r"(?<![\w.])(\d+)(?![\w.])")
TOP_LINE = re.compile(r"^TOP = \[([\d,\s]*)\][^\n]*$", re.M)

_TABLE: Optional[Dict[str, int]] = None


def unsalted_table() -> Dict[str, int]:
    global _TABLE
    if _TABLE is None:
        _TABLE = {hashlib.sha256(str(i).encode()).hexdigest()[:10]: i for i in range(LIMIT)}
    return _TABLE


def _is_text(path: str) -> bool:
    return path.endswith(TEXT_SUFFIXES)


def _in_roots(path: str) -> bool:
    return path.startswith(SCRUB_ROOTS)


class Scrubber:
    def __init__(self, top: Sequence[int], salt: Optional[bytes]):
        self.top = [int(x) for x in top]
        self.salt = salt
        self._labeler = None
        self.long_ids = {i: PLACEHOLDER_ID for i in self.top if i >= LONG_ID}
        self.all_ids = dict(zip(self.top, SYNTHETIC_TOP))
        self._top_seq = re.compile(r"(?<![\w.])" + r"\s*,\s*".join(map(str, self.top)) + r"(?![\w.])")

    def label(self, i: int) -> str:
        if self._labeler is None:
            sys.path.insert(0, str(REPO))
            from derive_surface.p2ids import Labeler  # lazy: pandas is imported only when a hash is found
            if self.salt is None:
                raise FileNotFoundError("salt needed to label an unsalted hash")
            self._labeler = Labeler(self.top, self.salt)
        return self._labeler.label(i)

    def _real_top_line(self, text: str) -> bool:
        m = TOP_LINE.search(text)
        return bool(m) and [int(x) for x in re.findall(r"\d+", m.group(1))] == self.top

    def scrub(self, path: str, text: str) -> Tuple[str, Dict[str, int]]:
        counts = {"hashes": 0, "raw_ids": 0}
        if not (_is_text(path) and _in_roots(path)):
            return text, counts
        table = unsalted_table()

        def sub_hash(m):
            i = table.get(m.group(0))
            if i is None:
                return m.group(0)
            counts["hashes"] += 1
            return self.label(i)

        text = HASH_TOKEN.sub(sub_hash, text)
        if path.startswith("tests/"):
            mapping = self.long_ids
            if path == IDS_TEST and self._real_top_line(text):
                mapping = self.all_ids
                text = TOP_LINE.sub("TOP = [" + ", ".join(map(str, SYNTHETIC_TOP))
                                    + "]  # synthetic ids (history scrubbed, audit A01)", text, count=1)
                counts["raw_ids"] += 1

            def sub_id(m):
                i = int(m.group(1))
                if i not in mapping:
                    return m.group(0)
                counts["raw_ids"] += 1
                return str(mapping[i])

            text = INT_TOKEN.sub(sub_id, text)
        return text, counts

    def leaks(self, path: str, text: str) -> Dict[str, int]:
        """Counts only: distinct unsalted hashes, distinct long top ids in tests/, the ordered top list."""
        table = unsalted_table()
        hashes = len({t for t in HASH_TOKEN.findall(text) if t in table}) if _is_text(path) else 0
        raw = 0
        if path.startswith("tests/") and _is_text(path):
            found = {int(t) for t in INT_TOKEN.findall(text)}
            raw = len(found & set(self.long_ids))
        top_list = 1 if _is_text(path) and self._top_seq.search(text) else 0
        return {"hashes": hashes, "raw_ids": raw, "top_list": top_list}


# ---------------------------------------------------------------- git plumbing

def _git(*args: str, input: Optional[bytes] = None) -> bytes:
    return subprocess.run(["git", *args], input=input, capture_output=True, check=True).stdout


def _read_blobs(shas: List[str]) -> Dict[str, bytes]:
    if not shas:
        return {}
    out = _git("cat-file", "--batch", input="".join(s + "\n" for s in shas).encode())
    blobs, pos = {}, 0
    for sha in shas:
        nl = out.index(b"\n", pos)
        _, typ, size = out[pos:nl].split()
        size = int(size)
        blobs[sha] = out[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1
    return blobs


def _load(top_path: Path, salt_path: Optional[Path]) -> Scrubber:
    top = [int(x) for x in json.loads(Path(top_path).read_text())["subaccounts"]]
    salt = bytes.fromhex(Path(salt_path).read_text().strip()) if salt_path and Path(salt_path).exists() else None
    return Scrubber(top, salt)


def run_index(scrubber: Scrubber) -> Dict[str, int]:
    entries = []
    for rec in _git("ls-files", "-s", "-z").split(b"\0"):
        if rec:
            meta, path = rec.decode().split("\t", 1)
            mode, sha, _stage = meta.split()
            entries.append((mode, sha, path))
    remove = [p for _, _, p in entries if p in MOVED_FIXTURES]
    if remove:
        _git("rm", "--cached", "-q", "--ignore-unmatch", "--", *remove)
    cands = [(m, s, p) for m, s, p in entries if p not in remove and _is_text(p) and _in_roots(p)]
    blobs = _read_blobs(sorted({s for _, s, _ in cands}))
    updates, stats = [], {"removed": len(remove), "files": 0, "hashes": 0, "raw_ids": 0}
    for mode, sha, path in cands:
        text = blobs[sha].decode("utf-8", errors="surrogateescape")
        new, counts = scrubber.scrub(path, text)
        if new != text:
            new_sha = _git("hash-object", "-w", "--stdin", input=new.encode("utf-8", errors="surrogateescape"))
            updates.append(f"{mode} {new_sha.decode().strip()}\t{path}\n")
            stats["files"] += 1
            stats["hashes"] += counts["hashes"]
            stats["raw_ids"] += counts["raw_ids"]
    if updates:
        _git("update-index", "--index-info", input="".join(updates).encode())
    return stats


def run_check(scrubber: Scrubber, rev: str) -> int:
    texts: Dict[str, str] = {}
    found_in: Dict[Tuple[str, str], Dict[str, int]] = {}
    report: Dict[str, List[str]] = {}
    commits = _git("rev-list", rev).decode().split()
    for c in commits:
        entries = []
        for line in _git("ls-tree", "-r", c).decode().splitlines():
            meta, path = line.split("\t", 1)
            _, typ, sha = meta.split()
            if typ == "blob":
                entries.append((sha, path))
        todo = sorted({s for s, p in entries if _is_text(p) and s not in texts})
        for sha, blob in _read_blobs(todo).items():
            texts[sha] = blob.decode("utf-8", errors="ignore")
        for sha, path in entries:
            found = []
            if path in MOVED_FIXTURES:
                found.append("account fixture")
            if _is_text(path):
                if (path, sha) not in found_in:  # the rules depend on the path
                    found_in[(path, sha)] = scrubber.leaks(path, texts[sha])
                found += [f"{k} {v}" for k, v in found_in[(path, sha)].items() if v]
            if found:
                report.setdefault(path, []).append(c[:7] + " (" + ", ".join(found) + ")")
    for path in sorted(report):
        print(f"{path}: {len(report[path])} of {len(commits)} commits, e.g. {report[path][0]}")
    print(f"checked {len(commits)} commits: {len(report)} files with account identifiers")
    return 1 if report else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("index", help="scrub the current index (git filter-branch --index-filter)")
    a.add_argument("--top", type=Path, default=TOP_PATH)
    a.add_argument("--salt", type=Path, default=SALT_PATH)
    b = sub.add_parser("check", help="scan a revision range, counts only")
    b.add_argument("rev")
    b.add_argument("--top", type=Path, default=TOP_PATH)
    args = ap.parse_args(argv)
    if args.cmd == "index":
        stats = run_index(_load(args.top, args.salt))
        if any(stats.values()):
            print(f"p2_history_scrub: {stats}", file=sys.stderr)
        return 0
    return run_check(_load(args.top, None), args.rev)


if __name__ == "__main__":
    sys.exit(main())
