from __future__ import annotations

import hashlib
import hmac
import json
import re
import subprocess
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from derive_surface import p2ids

REPO = Path(__file__).resolve().parents[1]
SALT_HEX = "00112233445566778899aabbccddeeff" * 2
# synthetic ids, deliberately not in id order (the ranking goes by fill count); the real list stays in data/p2
TOP = [104, 101, 110, 107, 102, 109, 103, 108, 105, 106]
OTHER = 4711  # a synthetic account outside the top ten


def _hmac10(salt_hex: str, x: int) -> str:
    return hmac.new(bytes.fromhex(salt_hex), str(x).encode(), hashlib.sha256).hexdigest()[:10]


@pytest.fixture(autouse=True)
def _fresh_cache():
    p2ids.reset()
    yield
    p2ids.reset()


def _markouts(path: Path) -> Path:
    counts = list(range(40, 30, -1)) + [5, 3]  # ten makers with 40..31 fills, two small ones
    subs = TOP + [OTHER, 99]
    pd.DataFrame({"maker_sub": np.repeat(subs, counts).astype("int64")}).to_parquet(path)
    return path


# --------------------------------------------------------------------------------------------
# Labeler
# --------------------------------------------------------------------------------------------

def test_top_accounts_get_rank_labels():
    lab = p2ids.Labeler(TOP, bytes.fromhex(SALT_HEX))
    assert [lab.label(s) for s in TOP] == [f"M{i}" for i in range(1, 11)]


def test_other_accounts_get_a_salted_hmac_label():
    lab = p2ids.Labeler(TOP, bytes.fromhex(SALT_HEX))
    assert lab.label(OTHER) == "X" + _hmac10(SALT_HEX, OTHER)
    assert lab.label(OTHER)[1:] != hashlib.sha256(str(OTHER).encode()).hexdigest()[:10]
    assert lab.label(np.int64(OTHER)) == lab.label(OTHER) == lab.label(str(OTHER))
    assert p2ids.Labeler(TOP, bytes(32)).label(OTHER) != lab.label(OTHER)
    assert lab.labels([TOP[1], OTHER, TOP[1]]) == ["M2", lab.label(OTHER), "M2"]


def test_only_the_first_ten_ranks_are_m_labels():
    lab = p2ids.Labeler(list(range(1, 13)), bytes.fromhex(SALT_HEX))
    assert lab.label(10) == "M10"
    assert lab.label(11).startswith("X") and lab.label(12).startswith("X")


def test_labeler_rejects_bad_input():
    with pytest.raises(ValueError):
        p2ids.Labeler(TOP, b"short")
    with pytest.raises(ValueError):
        p2ids.Labeler([7, 7], bytes(32))
    lab = p2ids.Labeler(TOP, bytes(32))
    for bad in (-1, 1.5, True, None):
        with pytest.raises((TypeError, ValueError)):
            lab.label(bad)


# --------------------------------------------------------------------------------------------
# Ranking
# --------------------------------------------------------------------------------------------

def test_ranking_by_maker_fills_with_ties_by_id():
    m = pd.DataFrame({"maker_sub": [5] * 3 + [9] * 3 + [2] * 2 + [4] * 4 + [1]})
    assert p2ids.ranking_from_markouts(m, n=3) == [4, 5, 9]


def test_ranking_reads_markouts(tmp_path, monkeypatch):
    monkeypatch.setattr(p2ids, "MARKOUTS", _markouts(tmp_path / "markouts.parquet"))
    monkeypatch.setattr(p2ids, "TOP_MAKERS", tmp_path / "missing.json")
    assert p2ids.top_makers() == TOP


def test_ranking_disagreeing_with_the_books_list_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(p2ids, "MARKOUTS", _markouts(tmp_path / "markouts.parquet"))
    top = tmp_path / "top_makers.json"
    top.write_text(json.dumps({"subaccounts": [TOP[1], TOP[0]] + TOP[2:]}))
    monkeypatch.setattr(p2ids, "TOP_MAKERS", top)
    with pytest.raises(RuntimeError, match="top_makers.json"):
        p2ids.top_makers()
    top.write_text(json.dumps({"subaccounts": TOP}))
    p2ids.reset()
    assert p2ids.top_makers() == TOP


def test_ranking_falls_back_to_the_books_list_without_markouts(tmp_path, monkeypatch):
    top = tmp_path / "top_makers.json"
    top.write_text(json.dumps({"subaccounts": TOP}))
    monkeypatch.setattr(p2ids, "MARKOUTS", tmp_path / "missing.parquet")
    monkeypatch.setattr(p2ids, "TOP_MAKERS", top)
    assert p2ids.top_makers() == TOP
    monkeypatch.setattr(p2ids, "TOP_MAKERS", tmp_path / "missing.json")
    p2ids.reset()
    with pytest.raises(FileNotFoundError):
        p2ids.top_makers()


# --------------------------------------------------------------------------------------------
# Salt
# --------------------------------------------------------------------------------------------

def test_salt_is_created_once_and_never_overwritten(tmp_path):
    path = tmp_path / "p2" / "secret_salt.txt"
    assert p2ids.create_salt(path) is True
    text = path.read_text()
    assert re.fullmatch(r"[0-9a-f]{64}\n", text)
    assert (path.stat().st_mode & 0o777) == 0o600
    assert p2ids.create_salt(path) is False
    assert path.read_text() == text
    assert p2ids.load_salt(path) == bytes.fromhex(text.strip())
    other = tmp_path / "other.txt"
    p2ids.create_salt(other)
    assert other.read_text() != text


def test_missing_or_malformed_salt_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="create_salt"):
        p2ids.load_salt(tmp_path / "none.txt")
    bad = tmp_path / "bad.txt"
    bad.write_text("abc\n")
    with pytest.raises(ValueError):
        p2ids.load_salt(bad)


# --------------------------------------------------------------------------------------------
# Module level label() on the repository files
# --------------------------------------------------------------------------------------------

def test_module_label_uses_salt_file_and_markouts(tmp_path, monkeypatch):
    salt = tmp_path / "secret_salt.txt"
    salt.write_text(SALT_HEX + "\n")
    monkeypatch.setattr(p2ids, "SALT_PATH", salt)
    monkeypatch.setattr(p2ids, "MARKOUTS", _markouts(tmp_path / "markouts.parquet"))
    monkeypatch.setattr(p2ids, "TOP_MAKERS", tmp_path / "missing.json")
    assert p2ids.label(TOP[0]) == "M1" and p2ids.label(TOP[9]) == "M10"
    assert p2ids.label(OTHER) == "X" + _hmac10(SALT_HEX, OTHER)
    assert p2ids.labels(pd.Series([TOP[5], 99])) == ["M6", "X" + _hmac10(SALT_HEX, 99)]


def test_module_label_never_creates_a_salt(tmp_path, monkeypatch):
    monkeypatch.setattr(p2ids, "SALT_PATH", tmp_path / "secret_salt.txt")
    monkeypatch.setattr(p2ids, "MARKOUTS", _markouts(tmp_path / "markouts.parquet"))
    monkeypatch.setattr(p2ids, "TOP_MAKERS", tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError):
        p2ids.label(OTHER)
    assert not (tmp_path / "secret_salt.txt").exists()


def test_cli_salt_and_label(tmp_path, monkeypatch, capsys):
    salt = tmp_path / "secret_salt.txt"
    monkeypatch.setattr(p2ids, "SALT_PATH", salt)
    monkeypatch.setattr(p2ids, "MARKOUTS", _markouts(tmp_path / "markouts.parquet"))
    monkeypatch.setattr(p2ids, "TOP_MAKERS", tmp_path / "missing.json")
    assert p2ids.main(["salt"]) == 0
    text = salt.read_text()
    assert p2ids.main(["salt"]) == 0 and salt.read_text() == text
    capsys.readouterr()
    assert p2ids.main(["label", str(TOP[1]), str(OTHER)]) == 0
    out = capsys.readouterr().out.split()
    assert out[:2] == [str(TOP[1]), "M2"] and out[2] == str(OTHER) and out[3].startswith("X")


# --------------------------------------------------------------------------------------------
# Guards: no unsalted account hashes and no raw top-maker ids in tracked text (Addendum 1.4)
# --------------------------------------------------------------------------------------------

TEXT_SUFFIXES = {".json", ".jsonl", ".csv", ".md", ".txt", ".tex", ".bib", ".tsv", ".py"}
GUARDED_ROOTS = ("results", "docs/paper2", "paper2", "tests")


def _guarded_files(roots=GUARDED_ROOTS):
    for root in roots:
        base = REPO / root
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if f.is_file() and f.suffix.lower() in TEXT_SUFFIXES:
                yield f


def test_no_unsalted_account_hashes_in_results_docs_or_tests():
    """sha256(str(id))[:10] of a subaccount id is reversible by enumeration; results/, docs and tests use p2ids
    labels or placeholders. Account-identifying chain fixtures live in data/p2/fixtures_private (not tracked)."""
    tokens = {}
    for f in _guarded_files():
        for tok in set(re.findall(r"(?<![0-9a-fA-F])[0-9a-f]{10}(?![0-9a-fA-F])", f.read_text(errors="ignore"))):
            tokens.setdefault(tok, []).append(str(f.relative_to(REPO)))
    bad = {}
    for i in range(250_000):
        h = hashlib.sha256(str(i).encode()).hexdigest()[:10]
        if h in tokens:
            for path in tokens[h]:
                bad[path] = bad.get(path, 0) + 1
    # files and counts only: the failure message must not repeat the hashes
    assert not bad, f"unsalted account hashes found (use derive_surface.p2ids.label): {bad}"


def test_guard_scans_tests_and_python_sources():
    files = {str(f.relative_to(REPO)) for f in _guarded_files()}
    assert "tests/test_p2_ids.py" in files
    assert any(p.startswith("tests/fixtures/") for p in files)


def test_no_raw_top_maker_ids_in_tests():
    """The rank key raw id -> M1..M10 stays in data/p2 (Addendum 1.4); tests use synthetic ids. Checks the ids with
    at least five digits (shorter ones collide with strikes and counts); needs the private list, else skipped."""
    if not p2ids.TOP_MAKERS.exists():
        pytest.skip(f"private list of top makers missing: {p2ids.TOP_MAKERS}")
    ids = [int(x) for x in json.loads(p2ids.TOP_MAKERS.read_text())["subaccounts"]]
    pats = {rank: re.compile(rf"(?<![\d.]){i}(?!\d)") for rank, i in enumerate(ids, start=1) if i >= 10_000}
    assert pats
    hits = {}
    for f in _guarded_files(("tests",)):
        text = f.read_text(errors="ignore")
        ranks = [rank for rank, pat in pats.items() if pat.search(text)]
        if ranks:
            hits[str(f.relative_to(REPO))] = ranks
    # ranks only: the failure message must not repeat the ids
    assert not hits, f"raw top-maker ids (by rank) in tests, use synthetic ids: {hits}"


def _tracked_files(tree: str = None) -> list:
    """Paths in the git index (or in ``tree``); skipped outside a git checkout (e.g. an archive)."""
    if not (REPO / ".git").exists():
        pytest.skip("not a git checkout")
    cmd = ["git", "ls-files"] if tree is None else ["git", "ls-tree", "-r", "--name-only", tree]
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()


def test_no_os_or_editor_artefacts_tracked():
    artefacts = [f for f in _tracked_files() if Path(f).name in {".DS_Store", ".Rhistory"}]
    assert not artefacts, f"remove with git rm --cached: {artefacts}"
    ignored = (REPO / ".gitignore").read_text().split()
    assert ".DS_Store" in ignored and ".Rhistory" in ignored


def test_private_fixtures_are_not_tracked():
    """The account-identifying chain fixtures live in data/p2/fixtures_private, which .gitignore covers."""
    private = [f for f in _tracked_files() if f.startswith("data/p2/")]
    assert not private, private
    moved = {"pm_chain_accounts.json", "sm_chain_accounts.json", "books_chain_snapshot.json", "books_events_day.json",
             "b1_chain_cases.json", "gen_b1_fixture.py"}
    assert not [f for f in _tracked_files() if f.startswith("tests/") and Path(f).name in moved]


# --------------------------------------------------------------------------------------------
# Guard: no raw ids of PM2 override accounts in any tracked file (audit A01, Addendum 1.4)
# --------------------------------------------------------------------------------------------

OVERRIDES_RAW = REPO / "data" / "p2" / "params"  # *_pm2_overrides_raw.json, private (not tracked)
# a whole number: not inside a word (a pseudonym, a hex string), not part of a decimal fraction and not zero-padded
# (PDF offsets); a full stop that ends a sentence may follow
DEC_TOKEN = re.compile(r"(?<![\w.])([1-9]\d*)(?!\w|\.\d)")
HEX_LITERAL = re.compile(r"0[xX]([0-9a-fA-F]{1,63})(?![0-9a-fA-F])")
PDF_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
ACCOUNT_COLUMN = re.compile(r"account|(?:^|_)sub(?:$|_)", re.I)


def _override_accounts(params: Path = OVERRIDES_RAW) -> set:
    ids = set()
    for f in sorted(Path(params).glob("*_pm2_overrides_raw.json")):
        ids |= {int(e["account"]) for e in json.loads(f.read_text())}
    return ids


def _id_hits(text: str, ids) -> int:
    """Occurrences of ``ids`` in ``text``: as a decimal token, as a hex literal shorter than 32 bytes, and as a
    32-byte word anywhere (log topic, ABI data, calldata; with or without 0x, any case)."""
    dec = {str(i) for i in ids}
    n = sum(1 for m in DEC_TOKEN.finditer(text) if m.group(1) in dec)
    n += sum(1 for m in HEX_LITERAL.finditer(text) if int(m.group(1), 16) in ids)
    low = text.lower()
    return n + sum(low.count(format(i, "064x")) for i in ids)


def _file_hits(path: Path, ids) -> int:
    """``_id_hits`` over the bytes of a file (latin-1, so binary files are scanned too), the inflated streams of a
    PDF, and the account columns of a parquet file."""
    data = path.read_bytes()
    parts = [data]
    if path.suffix.lower() == ".pdf":
        for m in PDF_STREAM.finditer(data):
            try:
                parts.append(zlib.decompress(m.group(1)))
            except zlib.error:
                pass
    n = sum(_id_hits(part.decode("latin-1"), ids) for part in parts)
    if path.suffix.lower() == ".parquet":
        import pyarrow.parquet as pq

        cols = [c for c in pq.read_schema(path).names if ACCOUNT_COLUMN.search(c)]
        if cols:
            df = pd.read_parquet(path, columns=cols)
            n += sum(int(pd.to_numeric(df[c], errors="coerce").isin(list(ids)).sum()) for c in cols)
    return n


def test_override_guard_finds_every_form_and_nothing_else(tmp_path):
    ids = {61234, 88888}  # synthetic
    word = format(61234, "064x")
    for text in ('{"account": 61234}', '"subaccount": "61234"', "account 61234.", f"lib 0x{61234:x}",
                 f"lib 0X{61234:X}", f'topics: ["0x{word}"]', f"0x{'0' * 64}{word}", f"0xa1b2c3d4{word}",
                 word.upper()):
        assert _id_hits(text, ids) == 1, text
    # not an account: a float, a pseudonym, a zero-padded PDF offset, a longer number, a fraction, a longer literal
    assert _id_hits(f"61234.5 -61234.75 W9f61234 0000061234 00000 n 612345 1.61234 0x{61234:x}0", ids) == 0
    params = tmp_path / "params"
    params.mkdir()
    (params / "BTC_pm2_overrides_raw.json").write_text(json.dumps([{"account": 61234, "lib": "0x1"}]))
    (params / "ETH_pm2_overrides_raw.json").write_text(json.dumps([{"account": "88888", "lib": "0x2"}]))
    (params / "ETH_pm2_overrides.json").write_text(json.dumps([{"account": "X0123456789"}]))
    assert _override_accounts(params) == ids and _override_accounts(tmp_path / "missing") == set()
    pdf = tmp_path / "f.pdf"
    pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<</Filter /FlateDecode>>\nstream\n" + zlib.compress(b"BT (maker 88888) Tj ET")
                    + b"\nendstream\nendobj\n")
    assert _file_hits(pdf, ids) == 1
    parquet = tmp_path / "m.parquet"
    pd.DataFrame({"maker_sub": [61234, 5], "strike": [61234.0, 88888.0]}).to_parquet(parquet)
    assert _file_hits(parquet, ids) == 1  # the account column only, not the strike


def test_no_raw_override_account_ids_in_tracked_files():
    """The raw ids of the PM2 override accounts stay in data/p2/params (Addendum 1.4): tests use synthetic ids, the
    results and documents p2ids labels. Scans every tracked file in every form an id took in the old history
    (decimal, hex literal, 32-byte word; inflated PDF streams, account columns of parquet files). Needs the private
    override lists, else skipped."""
    ids = _override_accounts()
    if not ids:
        pytest.skip(f"private override lists missing: {OVERRIDES_RAW}/*_pm2_overrides_raw.json")
    hits = {}
    for rel in _tracked_files():
        f = REPO / rel
        if f.is_file():
            n = _file_hits(f, ids)
            if n:
                hits[rel] = n
    # files and counts only: the failure message must not repeat the ids
    assert not hits, f"raw override account ids in tracked files (use p2ids labels or synthetic ids): {hits}"
