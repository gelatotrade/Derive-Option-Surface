from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from derive_surface import p2ids

REPO = Path(__file__).resolve().parents[1]
SALT_HEX = "00112233445566778899aabbccddeeff" * 2
TOP = [104, 101, 110, 107, 102, 109, 103, 108, 105, 106]  # synthetic ids (history scrubbed, audit A01)


def _hmac10(salt_hex: str, x: int) -> str:
    return hmac.new(bytes.fromhex(salt_hex), str(x).encode(), hashlib.sha256).hexdigest()[:10]


@pytest.fixture(autouse=True)
def _fresh_cache():
    p2ids.reset()
    yield
    p2ids.reset()


def _markouts(path: Path) -> Path:
    counts = list(range(40, 30, -1)) + [5, 3]  # ten makers with 40..31 fills, two small ones
    subs = TOP + [92718, 99]
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
    assert lab.label(92718) == "X" + _hmac10(SALT_HEX, 92718)
    assert lab.label(92718)[1:] != hashlib.sha256(b"92718").hexdigest()[:10]
    assert lab.label(np.int64(92718)) == lab.label(92718) == lab.label("92718")
    assert p2ids.Labeler(TOP, bytes(32)).label(92718) != lab.label(92718)
    assert lab.labels([101, 92718, 101]) == ["M2", lab.label(92718), "M2"]


def test_only_the_first_ten_ranks_are_m_labels():
    lab = p2ids.Labeler(list(range(1, 13)), bytes.fromhex(SALT_HEX))
    assert lab.label(10) == "M10"
    assert lab.label(11).startswith("X") and lab.label(109).startswith("X")


def test_labeler_rejects_bad_input():
    with pytest.raises(ValueError):
        p2ids.Labeler(TOP, b"short")
    with pytest.raises(ValueError):
        p2ids.Labeler([104, 104], bytes(32))
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
    top.write_text(json.dumps({"subaccounts": [101, 104] + TOP[2:]}))
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
    assert p2ids.label(104) == "M1" and p2ids.label(106) == "M10"
    assert p2ids.label(92718) == "X" + _hmac10(SALT_HEX, 92718)
    assert p2ids.labels(pd.Series([109, 99])) == ["M6", "X" + _hmac10(SALT_HEX, 99)]


def test_module_label_never_creates_a_salt(tmp_path, monkeypatch):
    monkeypatch.setattr(p2ids, "SALT_PATH", tmp_path / "secret_salt.txt")
    monkeypatch.setattr(p2ids, "MARKOUTS", _markouts(tmp_path / "markouts.parquet"))
    monkeypatch.setattr(p2ids, "TOP_MAKERS", tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError):
        p2ids.label(92718)
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
    assert p2ids.main(["label", "101", "92718"]) == 0
    out = capsys.readouterr().out.split()
    assert out[:2] == ["101", "M2"] and out[2] == "92718" and out[3].startswith("X")


# --------------------------------------------------------------------------------------------
# Guard: no unsalted account hashes in results/ and the Paper 2 documents
# --------------------------------------------------------------------------------------------

TEXT_SUFFIXES = {".json", ".jsonl", ".csv", ".md", ".txt", ".tex", ".bib", ".tsv"}


def test_no_unsalted_account_hashes_in_results_or_docs():
    """sha256(str(id))[:10] of a subaccount id is reversible by enumeration; results/ and docs use p2ids labels."""
    tokens = {}
    for root in ("results", "docs/paper2", "paper2"):
        base = REPO / root
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if f.is_file() and f.suffix.lower() in TEXT_SUFFIXES:
                for tok in set(re.findall(r"(?<![0-9a-fA-F])[0-9a-f]{10}(?![0-9a-fA-F])", f.read_text(errors="ignore"))):
                    tokens.setdefault(tok, []).append(str(f.relative_to(REPO)))
    bad = {}
    for i in range(250_000):
        h = hashlib.sha256(str(i).encode()).hexdigest()[:10]
        if h in tokens:
            bad[h] = tokens[h]
    assert not bad, f"unsalted account hashes found (use derive_surface.p2ids.label): {bad}"
