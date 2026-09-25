from __future__ import annotations

import hashlib
import hmac
import json
import re
import subprocess
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
# Guards: no unsalted account hashes and no raw top-maker ids in tracked text (Nachtrag 1.4)
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
    """The rank key raw id -> M1..M10 stays in data/p2 (Nachtrag 1.4); tests use synthetic ids. Checks the ids with
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
