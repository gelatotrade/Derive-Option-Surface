"""Tests for scripts/p2_history_scrub.py (audit A01, docs/paper2/HISTORY_CLEANUP.md).

All ids, hashes and the salt below are synthetic; the "real" top list of these tests is made up.
"""
from __future__ import annotations

import hashlib
import hmac
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
# stands in for the PM2 override accounts of data/p2/params/*_pm2_overrides_raw.json: two in the top list (one long,
# one short), two long ones outside it and a short one outside it
OVER = [70001, 42, 61234, 88888, 777]


def _sha10(i: int) -> str:
    return hashlib.sha256(str(i).encode()).hexdigest()[:10]


def _scrubber(overrides=()) -> "hs.Scrubber":
    return hs.Scrubber(REAL, SALT, overrides)


def _word(i: int) -> str:
    return format(i, "064x")


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
    for path in ("results/p2/a.csv", "docs/paper2/DATA_STATUS.md", "paper2/main.tex", "tests/test_x.py"):
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


# ---------------------------------------------------------------- override accounts

def test_override_placeholders_are_synthetic_five_digit_ids_fixed_by_the_salt():
    ph = _scrubber(OVER).placeholders()
    assert {i: ph[i] for i in REAL if i >= hs.LONG_ID} == {i: hs.PLACEHOLDER_ID for i in REAL if i >= hs.LONG_ID}
    own = [61234, 88888, 777]  # override accounts outside the top list, short ones included
    assert set(ph) == {i for i in REAL if i >= hs.LONG_ID} | set(own)
    assert all(90_000 <= ph[i] <= 99_999 for i in own) and len({ph[i] for i in own}) == len(own)
    assert not {ph[i] for i in own} & (set(REAL) | set(OVER))
    for i in own:  # 90000 plus the first eight hex digits of the salted HMAC, modulo 10000
        assert ph[i] == 90_000 + int(hmac.new(SALT, str(i).encode(), hashlib.sha256).hexdigest()[:8], 16) % 10_000
    assert hs.Scrubber(REAL, bytes(32), OVER).placeholders() != ph
    with pytest.raises(FileNotFoundError):
        hs.Scrubber(REAL, None, OVER).placeholders()


def test_override_placeholder_never_takes_a_real_or_used_id():
    first = _scrubber(OVER).placeholders()[61234]
    ph = _scrubber(OVER + [first]).placeholders()  # the natural placeholder of 61234 is now a real account
    own = [61234, 88888, 777, first]
    assert ph[61234] != first and len({ph[i] for i in own}) == len(own)
    assert not {ph[i] for i in own} & (set(REAL) | set(OVER) | {first})
    assert all(90_000 <= ph[i] <= 99_999 for i in own)


def test_override_ids_in_tests_become_placeholders_in_every_form():
    s = _scrubber(OVER)
    ph = s.placeholders()
    a, b, short = ph[61234], ph[88888], ph[777]
    text = (f'rows = [{{"account": 61234, "n": 777, "strike": 61234.5}}, {{"subaccount": "88888"}}]\n'
            f'lib = 0x{61234:x}  # also 0x{88888:X}, flag 0x10, small 0x{42:x}, short 0x{777:x}\n'
            f'topic = "0x{_word(88888)}"\n'
            f'data = "0x{_word(5)}{_word(61234)}"\n'
            f'call = "0xa1b2c3d4{_word(70001)}{_word(1)}"\n'
            f'odd = "0x{"0" * 70}{61234:x}"\n'
            f'end = "account 88888."\n')
    new, n = s.scrub("tests/test_p2_params.py", text)
    assert new == (f'rows = [{{"account": {a}, "n": 777, "strike": 61234.5}}, {{"subaccount": "{b}"}}]\n'
                   f'lib = 0x{format(a, "04x")}  # also 0x{format(b, "05X")}, flag 0x10, small 0x{42:x}, '
                   f'short 0x{short:x}\n'
                   f'topic = "0x{_word(b)}"\n'
                   f'data = "0x{_word(5)}{_word(a)}"\n'
                   f'call = "0xa1b2c3d4{_word(hs.PLACEHOLDER_ID)}{_word(1)}"\n'
                   f'odd = "0x{"0" * 70}{61234:x}"\n'  # not a literal, not words: left alone
                   f'end = "account {b}."\n')
    assert n == {"hashes": 0, "raw_ids": 9}
    assert s.scrub("tests/test_p2_params.py", new) == (new, {"hashes": 0, "raw_ids": 0})  # idempotent


def test_override_ids_in_docs_and_results_become_labels():
    s = _scrubber(OVER)
    lab = p2ids.Labeler(REAL, SALT)
    text = "Account 61234 (checked), maker 70001 and 88888. Strike 61234.5, block 610234, lib 0x" + _word(61234) + "\n"
    want = (f"Account {lab.label(61234)} (checked), maker M3 and {lab.label(88888)}. Strike 61234.5, block 610234, "
            f"lib 0x{_word(61234)}\n")
    for path in ("docs/paper2/get_margin_semantics.md", "results/p2/params/ETH_pm2_overrides.json",
                 "paper2/main.tex"):
        new, n = s.scrub(path, text)
        assert (new, n) == (want, {"hashes": 0, "raw_ids": 3}), path
        assert s.scrub(path, new) == (new, {"hashes": 0, "raw_ids": 0})
    for path in ("docs/paper1/x.md", "results/p1/x.csv", "paper/main.tex", "derive_surface/x.py"):
        assert s.scrub(path, text) == (text, {"hashes": 0, "raw_ids": 0}), path


def test_leaks_count_override_ids_in_every_form():
    s = _scrubber(OVER)
    text = f'x = 61234\ntopic = "0x{_word(88888)}"\ny = 0x{777:x}\nz = "0x{_word(1)}{_word(61234)}"\n'
    assert s.leaks("tests/test_p2_params.py", text) == {"hashes": 0, "raw_ids": 3, "top_list": 0}
    assert s.leaks("tests/test_p2_params.py", s.scrub("tests/test_p2_params.py", text)[0])["raw_ids"] == 0
    assert s.leaks("docs/paper2/x.md", "accounts 61234, 88888 and 777\n")["raw_ids"] == 2  # short ids collide
    assert s.leaks("docs/paper1/x.md", "accounts 61234, 88888\n")["raw_ids"] == 0
    # without the override lists only the top list counts
    assert _scrubber().leaks("tests/test_p2_params.py", text)["raw_ids"] == 0


def test_load_reads_every_override_list(tmp_path):
    top = tmp_path / "top_makers.json"
    top.write_text(json.dumps({"subaccounts": REAL}))
    params = tmp_path / "params"
    params.mkdir()
    (params / "BTC_pm2_overrides_raw.json").write_text(json.dumps([{"account": 61234, "lib": "0x1"},
                                                                     {"account": 70001, "lib": "0x2"}]))
    (params / "HYPE_pm2_overrides_raw.json").write_text(json.dumps([{"account": "88888", "lib": "0x3"}]))
    (params / "BTC_pm2_overrides.json").write_text(json.dumps([{"account": 99}]))  # labelled file: not read
    s = hs._load(top, None, params)
    assert s.overrides == [61234, 70001, 88888] and s.top == REAL
    assert hs._load(top, None).overrides == []
    with pytest.raises(FileNotFoundError):
        hs._load(top, None, tmp_path / "empty")


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

    prereg = commit({"docs/paper2/PRAEREGISTRIERUNG.md": "pre-registration\n"}, "prereg")
    leak = commit({"tests/test_p2_ids.py": OLD_IDS_TEST,
                   "tests/fixtures/p2/pm_chain_accounts.json": json.dumps({"account_hash": _sha10(REAL[1])}),
                   "tests/fixtures/p2/params_logs.json": json.dumps({"topics": ["0x" + _word(61234)]}),
                   "docs/paper2/get_margin_semantics.md": "checked account 88888\n",
                   "results/p2/params/ETH_pm2_overrides.json": f'[{{"account": "{_sha10(REAL[3])}"}}]\n'},
                  "stage a")
    addendum = commit({"docs/paper2/PRAEREGISTRIERUNG.md": "pre-registration\naddendum 1\n"}, "addendum 1")
    lab = p2ids.Labeler(REAL, SALT)
    ph = _scrubber(OVER).placeholders()
    fixed = commit({"tests/test_p2_ids.py": "TOP = [104, 101]\n",
                    "tests/fixtures/p2/params_logs.json": json.dumps({"topics": ["0x" + _word(ph[61234])]}),
                    "docs/paper2/get_margin_semantics.md": f"checked account {lab.label(88888)}\n",
                    "results/p2/params/ETH_pm2_overrides.json": '[{"account": "M4"}]\n'},
                   "fix", remove=["tests/fixtures/p2/pm_chain_accounts.json"])
    top = tmp_path / "top_makers.json"
    top.write_text(json.dumps({"subaccounts": REAL}))
    salt = tmp_path / "secret_salt.txt"
    salt.write_text(SALT.hex() + "\n")
    params = tmp_path / "params"
    params.mkdir()
    (params / "ETH_pm2_overrides_raw.json").write_text(json.dumps([{"account": i} for i in OVER]))
    script = Path(hs.__file__).resolve()
    _git(repo, "branch", "work-clean", "work", env=env)
    cmd = f'"{sys.executable}" "{script}" index --top "{top}" --salt "{salt}" --overrides "{params}"'
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
    assert _git(repo, "show", f"{new[1]}:tests/fixtures/p2/params_logs.json") == json.dumps(
        {"topics": ["0x" + _word(ph[61234])]})
    assert (_git(repo, "show", f"{new[1]}:docs/paper2/get_margin_semantics.md")
            == f"checked account {lab.label(88888)}\n")
    assert (_git(repo, "show", f"{new[2]}:docs/paper2/PRAEREGISTRIERUNG.md")
            == _git(repo, "show", f"{addendum}:docs/paper2/PRAEREGISTRIERUNG.md"))
    check = [sys.executable, str(script), "check", "--top", str(top), "--overrides", str(params)]
    out = subprocess.run(check + ["work-clean"], cwd=repo, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
    out = subprocess.run(check + ["work"], cwd=repo, capture_output=True, text=True)
    assert out.returncode == 1 and "tests/fixtures/p2/pm_chain_accounts.json" in out.stdout
    assert "tests/fixtures/p2/params_logs.json" in out.stdout and "docs/paper2/get_margin_semantics.md" in out.stdout
    assert str(REAL[2]) not in out.stdout and _sha10(REAL[1]) not in out.stdout
    assert "61234" not in out.stdout and "88888" not in out.stdout
