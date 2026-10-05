# Cleaning the history (audit A01)

> **Commit hashes.** This document was written before the history rewrite of 5 October 2026 (Addendum 7 of the Paper 2 pre-registration, Addendum 4 of the Paper 1 pre-registration). Its hashes refer to the history at the time of writing; `docs/paper2/HISTORY_REWRITE.md` maps every one of them to the current hash. Current hashes: Paper 1 pre-registration `cf1f432`; Paper 2 pre-registration `c9e9162`, Addenda 1 to 6 `b5c905c`, `60896fe`, `2416902`, `a02058a`, `8c066a7`, `6f2436e`, Addendum 7 `7c01e85`.


> **Historical guide.** The cleanup was carried out on 27 September 2026; `docs/paper2/HISTORY_REWRITE.md` records
> it, together with the follow-up steps that are still open. It did not follow section 4 to the letter. The Paper 2
> commits were replayed onto `main` as the new branch `paper2-capital` and scrubbed there with
> `scripts/p2_history_scrub.py` plus two extensions (now part of the script), because a wider scan also found raw
> ids of override accounts, some of them in commits before the pre-registration. Every Paper 2 hash therefore
> changed, the pre-registration included: `1d13227` is now `cc0a29f`, and Addenda 1 to 4 `eb534fe`, `9465210`,
> `bfc34c8` and `c4fcb59` are now `85bb0b7`, `6005d7c`, `8778432` and `e492ba1`. The hash table in section 5 comes
> from a test run and does not apply. The Addendum 5 called for in section 5 is written (27 September 2026). A24
> (section 6) is settled as well: no commit of `main` or `paper2-capital` holds raw wallet addresses in
> `results/p1/h1_lorenz.csv`.
>
> Below, branch names are those of the old history, and each old commit hash is followed by its new one ("old (now
> new)"); in the command block of section 4 a comment gives the mapping. Translated on 27 September 2026; files
> renamed since then appear under their current names, except where a path inside an old commit is meant.

Status 25 September 2026, branch `paper2-kapital` at `d51ede0` (now `1c29ba8`), still without an upstream. This
guide describes how the account identifiers disappear from the history of Paper 2 before the branch is pushed for
the first time. It rewrites nothing itself. The rewrite happens on a **new** branch; `paper2-kapital` stays until
the new branch has been checked. The pre-registration `1d13227` (now `cc0a29f`) and all commits before it stay
unchanged.

Raw ids and unsalted hashes are deliberately not reproduced here (Addendum 1.4).

## 1. What is already fixed in the working tree

These changes are in the working tree and must be committed before the rewrite (commit F):

- `tests/test_p2_ids.py`: `TOP` is a synthetic list (104, 101, 110, ...), and the second account is 4711. New
  guards: no unsalted hashes in `results/`, `docs/paper2/`, `paper2/` **and** `tests/` (now also `.py`), no raw ids
  of the top ten with five or more digits in `tests/` (reads `data/p2/books/top_makers.json`, skipped without the
  file), no `.DS_Store`/`.Rhistory` in the index, no private fixtures in the index.
- The fixtures that identify accounts are now under `data/p2/fixtures_private/` (git-ignored):
  `pm_chain_accounts.json`, `sm_chain_accounts.json`, `books_chain_snapshot.json`, `books_events_day.json`,
  `b1_chain_cases.json` and the generator `gen_b1_fixture.py`. The tests read them there and are skipped when they
  are missing (like the v2-core cases). `gen_a4_chain_fixtures.py` stays in `tests/fixtures/p2`, because it also
  generates the public cases `sm_chain_cases.json` and `pm_chain_cases.json`; it now writes the account cases to
  `data/p2/fixtures_private/`.
- The non-identifying part of `books_chain_snapshot.json` (addresses of the assets, managers and cash asset, and
  the encoder reference for accounts 1 and 2) is public in `tests/fixtures/p2/books_registry.json`, so that the
  registry tests keep running. The decoded balances that `test_p2_books.py` checked as literals (cash balance, one
  leg) are now in the private fixture under `expected`.
- `tests/test_p2_books.py`: the raw id next to the label M3 is replaced by the placeholder 4242.
- `.DS_Store`, `paper/.DS_Store` and `paper/social/.Rhistory` are removed from the index (A69) and listed in
  `.gitignore`.

In a public clone without `data/`, 19 tests are therefore skipped for lack of the private fixtures, and the guard
for raw ids (1 test) for lack of the list; on the author's machine all of them run.

## 2. Affected commits and files

Checked with `python3 scripts/p2_history_scrub.py check 1d13227^..paper2-kapital` (counts only, names no ids;
`1d13227` is now `cc0a29f`):

| File | Finding | Commits |
|---|---|---|
| `tests/fixtures/p2/pm_chain_accounts.json` | whole balances, 3 unsalted hashes | `e7361d2` (now `78566f1`) to `d51ede0` (now `1c29ba8`; 13) |
| `tests/fixtures/p2/sm_chain_accounts.json` | whole balances, 11 unsalted hashes | `e7361d2` (now `78566f1`) to `d51ede0` (now `1c29ba8`; 13) |
| `tests/fixtures/p2/books_chain_snapshot.json` | Multicall response of a top-ten account, 1 hash | `e7361d2` (now `78566f1`) to `d51ede0` (now `1c29ba8`; 13) |
| `tests/fixtures/p2/books_events_day.json` | a day's events with 109 transaction hashes and the `tx_hash` of the fill, 1 hash | `e7361d2` (now `78566f1`) to `d51ede0` (now `1c29ba8`; 13) |
| `tests/fixtures/p2/b1_chain_cases.json` | books of M2 and M3 on one day each | `591d2d5` (now `58551d6`) to `d51ede0` (now `1c29ba8`; 7) |
| `tests/fixtures/p2/gen_b1_fixture.py` | two raw ids that appear in the fixture with their label | `591d2d5` (now `58551d6`) to `d51ede0` (now `1c29ba8`; 7) |
| `tests/test_p2_ids.py` | ordered top-ten list, i.e. the key from raw id to M1..M10 | `591d2d5` (now `58551d6`) to `d51ede0` (now `1c29ba8`; 7) |
| `tests/test_p2_books.py` | a raw id next to the label M3 | `03ee4ca` (now `ae90485`) to `d51ede0` (now `1c29ba8`; 4) |
| `results/p2/params/BTC_pm2_overrides.json` | 15 unsalted hashes | `e7361d2` (now `78566f1`) to `c4fcb59` (now `e492ba1`; 6) |
| `results/p2/params/ETH_pm2_overrides.json` | 16 unsalted hashes | `e7361d2` (now `78566f1`) to `c4fcb59` (now `e492ba1`; 6) |
| `results/p2/params/HYPE_pm2_overrides.json` | 10 unsalted hashes | `e7361d2` (now `78566f1`) to `c4fcb59` (now `e492ba1`; 6) |
| `docs/paper2/DATENSTAND.md` (now `DATA_STATUS.md`) | hashes of all ten dominant accounts | `e7361d2` (now `78566f1`) to `c4fcb59` (now `e492ba1`; 6) |

Not affected: the commit messages and all commits before `e7361d2` (now `78566f1`), hence also `1d13227` (now `cc0a29f`), `cccfc01` (now `0968031`), `9b1394f` (now `fca1aea`) and
`bd11559` (now `d1bdd69`; check over all 82 commits of the branch). The points A24 and A69 lie before `1d13227` (now `cc0a29f`) and are not cleaned
here (section 6).

## 3. Tool

`scripts/p2_history_scrub.py` (tests: `tests/test_p2_history_scrub.py`, including a run of `git filter-branch` on a
throwaway repository). The script contains no ids; it reads the list and the salt from `data/p2` of the checkout it
is started from.

- `index` edits the index of a commit as `git filter-branch --index-filter` passes it: it removes the six fixture
  files from `tests/fixtures/p2`; in text files under `results/p2/`, `docs/paper2/`, `paper2/` and `tests/` it
  replaces every unsalted hash (reversed by enumeration up to 250,000) with the p2ids label (M1..M10, or X with
  salt, i.e. the same labels as from `591d2d5` (now `58551d6`) on); in `tests/` it replaces raw ids of the top ten with five or
  more digits by 4242, and in a `tests/test_p2_ids.py` with the real `TOP` list it replaces all ten ids with the
  synthetic list. It does not touch Paper 1 files. On an already cleaned state it changes nothing.
- `check <range>` searches every commit and prints only counts per file; exit code 1 if anything is left.

## 4. Procedure

Prerequisites: all audit fixes committed on `paper2-kapital`, suite green, working tree without changes to tracked
files, `data/p2/secret_salt.txt` and `data/p2/books/top_makers.json` present. From the root directory of the
repository, in zsh or bash:

```sh
# old hashes of this block: e7361d2 (now 78566f1), 1d13227 (now cc0a29f)
# 1. new branch; only this one is rewritten, from Stage A (e7361d2) on
git status --short --untracked-files=no            # must be empty
git branch paper2-kapital-clean paper2-kapital
export P2_SCRUB="$PWD/scripts/p2_history_scrub.py"
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch \
  --index-filter 'python3 "$P2_SCRUB" index' \
  -- e7361d2^..paper2-kapital-clean

# 2. check
python3 scripts/p2_history_scrub.py check 1d13227^..paper2-kapital-clean   # 0 files, exit 0
git diff --stat paper2-kapital paper2-kapital-clean                        # empty: same end state
git merge-base --is-ancestor 1d13227 paper2-kapital-clean && echo "1d13227 unchanged"
git rev-list --reverse e7361d2^..paper2-kapital > data/p2/p2_old.txt
git rev-list --reverse e7361d2^..paper2-kapital-clean > data/p2/p2_new.txt
paste -d' ' data/p2/p2_old.txt data/p2/p2_new.txt | while read old new; do
  p=$(git diff --quiet "$old:docs/paper2/PRAEREGISTRIERUNG.md" "$new:docs/paper2/PRAEREGISTRIERUNG.md" && echo same || echo DIFFERS)
  d=$([ "$(git log -1 --format='%an %ad %cn %cd %s' "$old")" = "$(git log -1 --format='%an %ad %cn %cd %s' "$new")" ] && echo same || echo DIFFERS)
  echo "$(git rev-parse --short "$old") -> $(git rev-parse --short "$new")  pre-registration $p, metadata $d  $(git log -1 --format=%s "$old")"
done

# 3. swap the branches, remove the backup of filter-branch
git branch -m paper2-kapital paper2-kapital-unclean   # local only, never push
git branch -m paper2-kapital-clean paper2-kapital
git checkout -q paper2-kapital
git update-ref -d refs/original/refs/heads/paper2-kapital-clean
```

If step 1 stops with "A previous backup already exists", a backup of an earlier run is still present; then delete
the new branch, create it again and use `filter-branch -f`. Step 2 must show "same" in every line, and
`git diff --stat` must be empty.

**Test run.** On 25 September 2026 this sequence ran in three fresh clones of this repository
(`git clone --no-local`), the last time verbatim from the block above as it then stood, with German comments and
output labels; the changes from section 1 were simulated there as commit F: 14 commits rewritten in about 6 s,
`check` afterwards 0 files (12 before), end state identical, `PRAEREGISTRIERUNG.md` as well as author, committer,
date and message the same in every pair, and the labels in the rewritten `*_pm2_overrides.json` byte-identical with
those from `591d2d5` (now `58551d6`) on. All runs gave the same new hashes. The six fixtures are missing in the rewritten commits;
the tests of that time in these commits do not run there without them, and the end state is not affected.

## 5. Consequences for the cited hashes

`1d13227` (now `cc0a29f`; pre-registration) and all commits before it keep their hash. All commits from `e7361d2`
(now `78566f1`) on get new hashes; the content of `PRAEREGISTRIERUNG.md` and the timestamps stay the same per commit. The test run gave:

| old (now new) | test run | Commit |
|---|---|---|
| `e7361d2` (now `78566f1`) | `a2aa7c5` | Stage A |
| `eb534fe` (now `85bb0b7`) | `1d6b2de` | Addendum 1 |
| `9465210` (now `6005d7c`) | `3872ed0` | Addendum 2 |
| `bfc34c8` (now `8778432`) | `985ec99` | Addendum 3 |
| `c4fcb59` (now `e492ba1`) | `396e180` | Addendum 4 |
| `591d2d5` (now `58551d6`) | `f459643` | Stage B |
| `93b42bc` (now `f7ba923`) | `defbb03` | Stage C |
| `03ee4ca` (now `ae90485`) | `7634832` | MM sensitivity H2 |

The values hold only if script, salt and list are unchanged; what counts is the output of step 2 of the real run.
To be updated afterwards (on the cleaned branch, as a new commit):

- `paper2/main.tex` lines 669 to 671 (`eb534fe` (now `85bb0b7`), `9465210` (now `6005d7c`), `bfc34c8` (now `8778432`), `c4fcb59` (now `e492ba1`)) and the comment
  `% src git:c4fcb59` (now `git:e492ba1`) in line 679. `1d13227` (now `cc0a29f`) in lines 666 and 678 stays.
- Regenerate `docs/paper2/NUMBER_CHECK.md` (`scripts/p2_number_check.py`). The check resolves hashes with
  `git cat-file -e`; as long as the old branch is present locally it still finds the old hashes, in a fresh clone
  it no longer does.
- `docs/paper2/MANUSCRIPT.md` lines 305 and 316, `docs/paper2/FIGURE_SELECTION.md` line 813 and
  `tests/test_p2_number_check.py` (examples with `c4fcb59` (now `e492ba1`), only for consistency; the tests resolve hashes through a
  stub). `derive_surface/social_p2.py` names only `1d13227` (now `cc0a29f`) and stays.
- `docs/paper2/AUDIT.md` is a dated report on the old state and stays; a sentence pointing to this file is enough.
- A dated **Addendum 5** at the end of `PRAEREGISTRIERUNG.md`: the reason (A01), the mapping from old to new for the
  four addenda, the statement that text and timestamps are unchanged, and that no registered verdict is affected.
  Write it only after the run, because only then are the new hashes fixed. The manuscript then names the new hashes
  and refers to Addendum 5 (see A02). Translate Addendum 5 into `docs/paper2/PREREGISTRATION.md` as well and update
  the blob hash in its header; otherwise `tests/test_p2_prereg_en.py` fails. The translation itself names only
  `1d13227` (now `cc0a29f`) and the blob hash of the original, which stays the same in the rewrite.

## 6. Not part of this cleanup

- **A24, an open decision of the author on Paper 1.** `results/p1/h1_lorenz.csv` contains 1,388 wallet addresses
  (commit `a26a59d` (now `b7ed5bc`), in both local branches). `a26a59d` (now `b7ed5bc`) is an ancestor of `1d13227` (now `cc0a29f`). Taking the addresses out of
  the history would mean rewriting from `a26a59d` (now `b7ed5bc`) on; then `1d13227` (now `cc0a29f`), all hashes of Paper 2 and the late hashes of
  Paper 1 change (the pre-registration of Paper 1, `3fd9caa`, `7f67eaf`, `837595c`, lies before it). The script
  does not touch `results/p1`, and `check` does not search for addresses. Nothing is changed in the working tree.
- **A69.** `.DS_Store` (`fdb8014`, now `fcdfde3`), `paper/.DS_Store` and `paper/social/.Rhistory` (`0afff2c`, now `01857a4`) also lie before
  `1d13227` (now `cc0a29f`) and stay in the history; they are only removed from the index. `.DS_Store` can contain file names of
  the local folder.
- **Remaining weak features.** The old versions of `tests/test_p2_books.py` (`e7361d2` (now `78566f1`) to `d51ede0` (now `1c29ba8`)) contain
  decoded values of a top-ten account at one block (cash balance, one option leg), but no id and no label. Anyone
  who queries all accounts at this block with `eth_call` would find the account; the script leaves these literals
  in place.
- **Limits of the pseudonyms.** The public trade history (`get_trade_history`) gives the `subaccount_id` of every
  fill. Anyone who loads the tape can therefore recompute the ranking M1 to M10 (Addendum 1.4: most maker fills in
  the Paper 1 sample). The X labels of the override accounts can also be matched through the public
  `LibOverrideUpdated` events and the block numbers in `results/p2/params/*_overrides.json`. The pseudonyms protect
  against casual matching, not against targeted matching. The cleanup establishes the state that Addendum 1.4
  describes; the paper should not claim any further protection.

## 7. Recommendation

1. Clean up now, while the branch is local: commit the fixes, carry out section 4, write Addendum 5, update the
   citations, build the paper, run `scripts/p2_number_check.py` and the suite. The cost is four new addendum
   hashes, with unchanged text and an unchanged pre-registration.
2. Push only the cleaned branch (`git push -u origin paper2-kapital`), never `paper2-kapital-unclean` and never
   `git push --all`. Use a merge commit when integrating, neither squash nor rebase (A02). Then anchor the new
   hashes externally (OpenTimestamps or OSF, A02).
3. Keep `paper2-kapital-unclean` locally until push and anchoring are done; only then delete it
   (`git branch -D paper2-kapital-unclean`). The old objects stay in the local repository until `git gc` and
   are not pushed.
4. Decide A24 separately. Align the sentence about the pseudonyms in the section "Data, code and pre-registration"
   with section 6.
