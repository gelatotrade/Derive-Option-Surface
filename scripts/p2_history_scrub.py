#!/usr/bin/env python3
"""Scrub account identifiers from the Paper 2 history on a NEW branch (audit A01, Addendum 1.4).

Guide: docs/paper2/HISTORY_CLEANUP.md. The run of 27 September 2026 (docs/paper2/HISTORY_REWRITE.md) replayed the
Paper 2 commits onto main as the new branch paper2-capital and scrubbed them there:

    FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch \\
        --index-filter 'python3 "<repo>/scripts/p2_history_scrub.py" index' -- main..paper2-capital
    python3 scripts/p2_history_scrub.py check main..paper2-capital

``index`` works on the index of one commit (as git filter-branch --index-filter calls it):

1. it removes the account-identifying chain fixtures (``MOVED_FIXTURES``, now in data/p2/fixtures_private);
2. in text files under results/p2, docs/paper2, paper2 and tests it replaces every unsalted ``sha256(str(id))[:10]``
   (reversed by enumeration of the ids below ``LIMIT``) by the p2ids label of the id (M1..M10 or salted X label);
3. in tests/ it replaces raw top-maker ids with at least five digits by ``PLACEHOLDER_ID`` and, in a
   tests/test_p2_ids.py whose ``TOP`` line is the real ranked list, every top-maker id by ``SYNTHETIC_TOP``;
4. it covers the raw ids of the PM2 override accounts (``data/p2/params/*_pm2_overrides_raw.json``) and the long
   top-maker ids in every form the history held them:
   * tests/: a decimal id with at least five digits becomes a synthetic placeholder (``PLACEHOLDER_ID`` for a top
     maker, one five-digit id from ``PLACEHOLDER_BASE`` on per override account, fixed by the salt and never a real
     id); a hex literal of at most 32 bytes, or a 32-byte word of ABI data, a log topic or calldata, whose value is
     such an id becomes the placeholder in the same width and case;
   * docs/paper2, results/p2, paper2: a decimal id with at least five digits becomes the p2ids label of the account
     (M1..M10, or X and the salted HMAC).

``check`` scans every commit of a revision range and prints counts per file (never ids or hashes); exit code 1 if
anything is left. The script holds no ids: the ranked list, the override lists and the salt are read from data/p2
of this checkout (``--top``, ``--overrides``, ``--salt``). Files outside the Paper 2 roots (Paper 1) are never
changed.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
TOP_PATH = REPO / "data" / "p2" / "books" / "top_makers.json"
SALT_PATH = REPO / "data" / "p2" / "secret_salt.txt"
OVERRIDES_DIR = REPO / "data" / "p2" / "params"
OVERRIDES_GLOB = "*_pm2_overrides_raw.json"

MOVED_FIXTURES = tuple(f"tests/fixtures/p2/{name}" for name in (
    "pm_chain_accounts.json", "sm_chain_accounts.json", "books_chain_snapshot.json", "books_events_day.json",
    "b1_chain_cases.json", "gen_b1_fixture.py"))
SCRUB_ROOTS = ("results/p2/", "docs/paper2/", "paper2/", "tests/")
LABEL_ROOTS = ("results/p2/", "docs/paper2/", "paper2/")  # raw ids become labels here, placeholders in tests/
TEXT_SUFFIXES = (".json", ".jsonl", ".csv", ".md", ".txt", ".tex", ".bib", ".tsv", ".py")
SYNTHETIC_TOP = [104, 101, 110, 107, 102, 109, 103, 108, 105, 106]  # as in tests/test_p2_ids.py
PLACEHOLDER_ID = 4242
PLACEHOLDER_BASE = 90_000  # placeholders of the override accounts: 90000 to 99999
LONG_ID = 10_000  # shorter ids collide with strikes and counts
MIN_HEX_ID = 100  # smaller hex values collide with flags and constants
LIMIT = 250_000  # enumeration bound, as in the guard of tests/test_p2_ids.py
IDS_TEST = "tests/test_p2_ids.py"

HASH_TOKEN = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{10}(?![0-9a-fA-F])")
# a whole number: not inside a word or a decimal fraction; a full stop that ends a sentence may follow
INT_TOKEN = re.compile(r"(?<![\w.])(\d+)(?!\w|\.\d)")
TOP_LINE = re.compile(r"^TOP = \[([\d,\s]*)\][^\n]*$", re.M)
HEX_TOKEN = re.compile(r"0x([0-9a-fA-F]+)")

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


def hex_fields(digits: str) -> List[Tuple[int, int, int]]:
    """(start, end, value) of the fields of a hex literal (digits without ``0x``) that can hold an id: the whole
    literal up to 32 bytes; beyond that its 32-byte words, when the literal is ABI data or a log topic list (a
    multiple of 64 digits) or calldata (a 4-byte selector, then 32-byte words); nothing otherwise."""
    if len(digits) <= 64:
        return [(0, len(digits), int(digits, 16))]
    first = len(digits) % 64
    if first not in (0, 8):
        return []
    return [(k, k + 64, int(digits[k:k + 64], 16)) for k in range(first, len(digits), 64)]


class Scrubber:
    def __init__(self, top: Sequence[int], salt: Optional[bytes], overrides: Sequence[int] = ()):
        self.top = [int(x) for x in top]
        self.salt = salt
        self.overrides = sorted({int(x) for x in overrides})
        self._labeler = None
        self._placeholders: Optional[Dict[int, int]] = None
        self.long_ids = {i: PLACEHOLDER_ID for i in self.top if i >= LONG_ID}
        self.all_ids = dict(zip(self.top, SYNTHETIC_TOP))
        own = set(self.overrides) - set(self.top)  # override accounts outside the top ten get their own placeholder
        self.long_accounts = {i for i in set(self.top) | own if i >= LONG_ID}  # decimal: tests/ and the label roots
        self.hex_accounts = {i for i in set(self.long_ids) | own if i >= MIN_HEX_ID}  # hex: tests/
        self._top_seq = re.compile(r"(?<![\w.])" + r"\s*,\s*".join(map(str, self.top)) + r"(?![\w.])")

    def _hmac(self, i: int) -> str:
        if self.salt is None:
            raise FileNotFoundError("salt needed for the placeholders of the override accounts")
        return hmac.new(self.salt, str(i).encode(), hashlib.sha256).hexdigest()

    def placeholders(self) -> Dict[int, int]:
        """Replacement id in tests/ per account: ``PLACEHOLDER_ID`` for a long top-maker id; for every override
        account outside the top ten a five-digit id from ``PLACEHOLDER_BASE`` on, fixed by the salt, one per account
        and never one of the real ids."""
        if self._placeholders is None:
            ph = dict(self.long_ids)
            own = sorted(set(self.overrides) - set(self.top), key=self._hmac)
            used = set(ph.values()) | set(self.top) | set(self.overrides)
            for i in own:
                n = PLACEHOLDER_BASE + int(self._hmac(i)[:8], 16) % 10_000
                while n in used:
                    n = PLACEHOLDER_BASE + (n + 1 - PLACEHOLDER_BASE) % 10_000
                ph[i] = n
                used.add(n)
            self._placeholders = ph
        return self._placeholders

    def label(self, i: int) -> str:
        if self._labeler is None:
            sys.path.insert(0, str(REPO))
            from derive_surface.p2ids import Labeler  # lazy: pandas is imported only when a label is needed
            if self.salt is None:
                raise FileNotFoundError("salt needed to label an account")
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
                if i in mapping:
                    new = mapping[i]
                elif i in self.long_accounts:
                    new = self.placeholders()[i]
                else:
                    return m.group(0)
                counts["raw_ids"] += 1
                return str(new)

            text = INT_TOKEN.sub(sub_id, text)
            text = HEX_TOKEN.sub(lambda m: self._sub_hex(m, counts), text)
        elif path.startswith(LABEL_ROOTS):
            def sub_label(m):
                i = int(m.group(1))
                if i not in self.long_accounts:
                    return m.group(0)
                counts["raw_ids"] += 1
                return self.label(i)

            text = INT_TOKEN.sub(sub_label, text)
        return text, counts

    def _sub_hex(self, m, counts: Dict[str, int]) -> str:
        """A hex literal with every id field replaced by the placeholder of its account (same width and case)."""
        digits = m.group(1)
        upper = any(c in "ABCDEF" for c in digits) and not any(c in "abcdef" for c in digits)
        out = digits
        for start, end, value in reversed(hex_fields(digits)):
            if value in self.hex_accounts:
                new = format(self.placeholders()[value], f"0{end - start}x")
                out = out[:start] + (new.upper() if upper else new) + out[end:]
                counts["raw_ids"] += 1
        return "0x" + out

    def _raw_ids(self, path: str, text: str) -> set:
        """The distinct raw ids that ``scrub`` would replace in ``path`` (decimal, hex literal or 32-byte word)."""
        if not (_is_text(path) and _in_roots(path)):
            return set()
        found = {int(t) for t in INT_TOKEN.findall(text)} & self.long_accounts
        if path.startswith("tests/"):
            found |= {v for m in HEX_TOKEN.finditer(text) for _, _, v in hex_fields(m.group(1))} & self.hex_accounts
        return found

    def leaks(self, path: str, text: str) -> Dict[str, int]:
        """Counts only: distinct unsalted hashes; distinct raw ids of top makers and override accounts that
        ``scrub`` replaces (decimal in tests/ and the label roots, hex literal or 32-byte word in tests/); the
        ordered top list."""
        table = unsalted_table()
        hashes = len({t for t in HASH_TOKEN.findall(text) if t in table}) if _is_text(path) else 0
        raw = len(self._raw_ids(path, text))
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


def load_overrides(directory: Path) -> List[int]:
    """Raw ids of the PM2 override accounts in ``directory/*_pm2_overrides_raw.json``; an error if there is none."""
    files = sorted(Path(directory).glob(OVERRIDES_GLOB))
    if not files:
        raise FileNotFoundError(f"no {OVERRIDES_GLOB} in {directory}")
    return sorted({int(e["account"]) for f in files for e in json.loads(f.read_text())})


def _load(top_path: Path, salt_path: Optional[Path], overrides_dir: Optional[Path] = None) -> Scrubber:
    top = [int(x) for x in json.loads(Path(top_path).read_text())["subaccounts"]]
    salt = bytes.fromhex(Path(salt_path).read_text().strip()) if salt_path and Path(salt_path).exists() else None
    overrides = load_overrides(overrides_dir) if overrides_dir is not None else []
    return Scrubber(top, salt, overrides)


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
    a.add_argument("--overrides", type=Path, default=OVERRIDES_DIR, help=f"directory with {OVERRIDES_GLOB}")
    b = sub.add_parser("check", help="scan a revision range, counts only")
    b.add_argument("rev")
    b.add_argument("--top", type=Path, default=TOP_PATH)
    b.add_argument("--overrides", type=Path, default=OVERRIDES_DIR, help=f"directory with {OVERRIDES_GLOB}")
    args = ap.parse_args(argv)
    if args.cmd == "index":
        stats = run_index(_load(args.top, args.salt, args.overrides))
        if any(stats.values()):
            print(f"p2_history_scrub: {stats}", file=sys.stderr)
        return 0
    return run_check(_load(args.top, None, args.overrides), args.rev)


if __name__ == "__main__":
    sys.exit(main())
