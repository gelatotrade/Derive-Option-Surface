"""Tests for scripts/p2_history_scrub.py (audit A01, docs/paper2/HISTORIE_BEREINIGEN.md).

All ids, hashes and the salt below are synthetic; the "real" top list of these tests is made up.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p2_history_scrub as hs  # noqa: E402

from derive_surface import p2ids  # noqa: E402

REAL = [31, 42, 70001, 20002, 50003, 64, 3005, 50004, 177, 50005]  # stands in for data/p2/books/top_makers.json
SALT = bytes(range(32))


def _sha10(i: int) -> str:
    return hashlib.sha256(str(i).encode()).hexdigest()[:10]


def _scrubber() -> "hs.Scrubber":
    return hs.Scrubber(REAL, SALT)


OLD_IDS_TEST = f'''TOP = [{", ".join(map(str, REAL))}]  # real top-10 of the Paper 1 sample (tests may keep ids)
SALT_HEX = "00112233445566778899aabbccddeeff" * 2


def test_x():
    assert p2ids.label({REAL[0]}) == "M1" and p2ids.label({REAL[9]}) == "M10"
    assert lab.labels([{REAL[1]}, 92718, {REAL[1]}]) == ["M2", lab.label(92718), "M2"]
    with pytest.raises(ValueError):
        p2ids.Labeler([{REAL[0]}, {REAL[0]}], bytes(32))
    assert (path.stat().st_mode & 0o777) == 0o600 and h[:10]
    assert p2ids.main(["label", "{REAL[1]}", "92718"]) == 0
'''


# ---------------------------------------------------------------- hashes

def test_unsalted_hashes_become_labels():
    s = _scrubber()
    lab = p2ids.Labeler(REAL, SALT)
    text = f'{{"account": "{_sha10(REAL[2])}"}} | 3 | {_sha10(123456)} | lib 4e8ea8af, X0123456789, 0x{"ab" * 20}\n'
    new, n = s.scrub("results/p2/params/ETH_pm2_overrides.json", text)
    assert n == {"hashes": 2, "raw_ids": 0}
    assert new == f'{{"account": "M3"}} | 3 | {lab.label(123456)} | lib 4e8ea8af, X0123456789, 0x{"ab" * 20}\n'
    assert s.scrub("results/p2/params/ETH_pm2_overrides.json", new) == (new, {"hashes": 0, "raw_ids": 0})


def test_only_the_paper2_roots_and_text_files_are_touched():
    s = _scrubber()
    text = f"hash {_sha10(REAL[0])}\n"
    for path in ("results/p1/x.csv", "docs/paper1/x.md", "paper/main.tex", "derive_surface/x.py",
                 "results/p2/fig.png"):
        assert s.scrub(path, text) == (text, {"hashes": 0, "raw_ids": 0})
    for path in ("results/p2/a.csv", "docs/paper2/DATENSTAND.md", "paper2/main.tex", "tests/test_x.py"):
        assert s.scrub(path, text)[0] == "hash M1\n"


# ---------------------------------------------------------------- raw ids in tests

def test_real_top_list_in_test_p2_ids_is_mapped_to_synthetic_ids():
    s = _scrubber()
    new, n = s.scrub("tests/test_p2_ids.py", OLD_IDS_TEST)
    syn = hs.SYNTHETIC_TOP
    assert new.splitlines()[0] == f'TOP = [{", ".join(map(str, syn))}]  # synthetic ids (history scrubbed, audit A01)'
    assert f'p2ids.label({syn[0]}) == "M1" and p2ids.label({syn[9]}) == "M10"' in new
    assert f'lab.labels([{syn[1]}, 92718, {syn[1]}])' in new
    assert f'p2ids.Labeler([{syn[0]}, {syn[0]}], bytes(32))' in new
    assert f'p2ids.main(["label", "{syn[1]}", "92718"])' in new
    assert "0o777) == 0o600 and h[:10]" in new  # other numbers stay
    assert not any(str(i) in new for i in REAL if i >= 1000)
    assert n["raw_ids"] > 0
    assert s.scrub("tests/test_p2_ids.py", new) == (new, {"hashes": 0, "raw_ids": 0})  # idempotent


def test_small_numbers_elsewhere_stay_and_long_ids_become_a_placeholder():
    s = _scrubber()
    text = f'rows.append({{"subaccount": {REAL[2]}, "n": 31, "k": 64, "strike": 3005.0}})\n'
    new, n = s.scrub("tests/test_p2_books.py", text)
    assert new == f'rows.append({{"subaccount": {hs.PLACEHOLDER_ID}, "n": 31, "k": 64, "strike": 3005.0}})\n'
    assert n == {"hashes": 0, "raw_ids": 1}
    # without the real top list (a cleaned file) small numbers stay even in test_p2_ids.py: idempotent at the tip
    cleaned = f'TOP = [1, 2]\nassert p2ids.label({REAL[0]}) == "M1"\nx = {REAL[2]}\n'
    assert s.scrub("tests/test_p2_ids.py", cleaned) == (
        f'TOP = [1, 2]\nassert p2ids.label({REAL[0]}) == "M1"\nx = {hs.PLACEHOLDER_ID}\n', {"hashes": 0, "raw_ids": 1})


def test_moved_fixtures_are_the_six_account_files():
    names = {Path(p).name for p in hs.MOVED_FIXTURES}
    assert names == {"pm_chain_accounts.json", "sm_chain_accounts.json", "books_chain_snapshot.json",
                     "books_events_day.json", "b1_chain_cases.json", "gen_b1_fixture.py"}
    assert all(p.startswith("tests/fixtures/p2/") for p in hs.MOVED_FIXTURES)


def test_leaks_counts_without_repeating_ids():
    s = _scrubber()
    bad = f'TOP = [{", ".join(map(str, REAL))}]\nh = "{_sha10(99)}"\n'
    got = s.leaks("tests/test_p2_ids.py", bad)
    assert got == {"hashes": 1, "raw_ids": 5, "top_list": 1}  # five of the ids have five digits
    assert s.leaks("tests/test_p2_ids.py", s.scrub("tests/test_p2_ids.py", bad)[0]) == {
        "hashes": 0, "raw_ids": 0, "top_list": 0}


# ---------------------------------------------------------------- the filter-branch command on a scratch repository

def _git(repo: Path, *args, env=None) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True, env=env).stdout


@pytest.mark.skipif(shutil.which("git") is None, reason="git missing")
def test_filter_branch_rewrites_only_the_new_branch(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@x", GIT_AUTHOR_DATE="2026-09-24T20:00:00+0200",
               GIT_COMMITTER_DATE="2026-09-24T20:00:00+0200", FILTER_BRANCH_SQUELCH_WARNING="1")
    _git(repo, "init", "-q", "-b", "work", env=env)

    def commit(files: dict, msg: str, remove=()):
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text)
        for rel in remove:
            _git(repo, "rm", "-q", rel, env=env)
        _git(repo, "add", "-A", env=env)
        _git(repo, "commit", "-q", "-m", msg, env=env)
        return _git(repo, "rev-parse", "HEAD").strip()

    prereg = commit({"docs/paper2/PRAEREGISTRIERUNG.md": "Praeregistrierung\n"}, "prereg")
    leak = commit({"tests/test_p2_ids.py": OLD_IDS_TEST,
                   "tests/fixtures/p2/pm_chain_accounts.json": json.dumps({"account_hash": _sha10(REAL[1])}),
                   "results/p2/params/ETH_pm2_overrides.json": f'[{{"account": "{_sha10(REAL[3])}"}}]\n'},
                  "stage a")
    addendum = commit({"docs/paper2/PRAEREGISTRIERUNG.md": "Praeregistrierung\nNachtrag 1\n"}, "nachtrag 1")
    fixed = commit({"tests/test_p2_ids.py": "TOP = [104, 101]\n",
                    "results/p2/params/ETH_pm2_overrides.json": '[{"account": "M4"}]\n'},
                   "fix", remove=["tests/fixtures/p2/pm_chain_accounts.json"])
    top = tmp_path / "top_makers.json"
    top.write_text(json.dumps({"subaccounts": REAL}))
    salt = tmp_path / "secret_salt.txt"
    salt.write_text(SALT.hex() + "\n")
    script = Path(hs.__file__).resolve()
    _git(repo, "branch", "work-clean", "work", env=env)
    cmd = f'"{sys.executable}" "{script}" index --top "{top}" --salt "{salt}"'
    _git(repo, "filter-branch", "--index-filter", cmd, "--", f"{leak}^..work-clean", env=env)

    new = _git(repo, "rev-list", "--reverse", "work-clean").split()
    old = _git(repo, "rev-list", "--reverse", "work").split()
    assert new[0] == old[0] == prereg  # the pre-registration keeps its hash
    assert new[1:] != old[1:] and len(new) == len(old) == 4
    assert _git(repo, "rev-parse", "work").strip() == fixed  # the old branch is untouched
    assert _git(repo, "rev-parse", "work-clean^{tree}") == _git(repo, "rev-parse", "work^{tree}")
    for c in new:
        assert "tests/fixtures/p2/pm_chain_accounts.json" not in _git(repo, "ls-tree", "-r", "--name-only", c)
    ids_old = _git(repo, "show", f"{new[1]}:tests/test_p2_ids.py")
    assert str(REAL[2]) not in ids_old and ids_old.startswith(f"TOP = [{hs.SYNTHETIC_TOP[0]}, ")
    assert _git(repo, "show", f"{new[1]}:results/p2/params/ETH_pm2_overrides.json") == '[{"account": "M4"}]\n'
    assert (_git(repo, "show", f"{new[2]}:docs/paper2/PRAEREGISTRIERUNG.md")
            == _git(repo, "show", f"{addendum}:docs/paper2/PRAEREGISTRIERUNG.md"))
    out = subprocess.run([sys.executable, str(script), "check", "work-clean", "--top", str(top)], cwd=repo,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
    out = subprocess.run([sys.executable, str(script), "check", "work", "--top", str(top)], cwd=repo,
                         capture_output=True, text=True)
    assert out.returncode == 1 and "tests/fixtures/p2/pm_chain_accounts.json" in out.stdout
    assert str(REAL[2]) not in out.stdout and _sha10(REAL[1]) not in out.stdout
