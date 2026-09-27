# Paper 2 history rewrite

Date: 27 September 2026. Branch `paper2-capital`, local and not pushed. It replaces the local branch
`paper2-kapital` (tip `469cc8e`), which was never pushed. That branch and its backup
`backup/paper2-kapital-vor-integration` still hold the unscrubbed history. Neither may be pushed (no
`git push --all`). They can be deleted once this branch is pushed and its hashes are anchored externally.

Raw account ids and unsalted hashes are deliberately not reproduced here (Addendum 1.4).

## Why

1. **Account identifiers and personal data are removed before publication** (audit A01, pre-registration
   Addendum 1.4). The old commits contained the following:
   - raw ids of dominant maker subaccounts and of PM2 override accounts;
   - unsalted `sha256(str(id))[:10]` hashes, which can be reversed by enumeration;
   - chain fixtures that identify single accounts: whole balances, and a day of events with transaction hashes.
2. **The history now builds on the corrected Paper 1 history.** `main` (`d2a2b43`) holds the corrected, cleaned
   and English Paper 1 history. The old base `0afff2c` corresponds to `01857a4` there. The Paper 2 commits now
   sit on `main`.

## What was done

1. **Replay.** The 20 commits `0afff2c..469cc8e` were replayed onto `main` `d2a2b43`, one new commit per
   original, under these rules:
   - **Paper 1 files keep the `main` version.** This covers `docs/paper1/`, `results/p1*`, `scripts/p1_*`,
     `tests/test_p1_*`, `paper/`, `derive_surface/*p1*`, `figdata` and `figures_social`. The Paper 1 finding
     files of the old history were dropped:
     - `docs/paper1/BEFUND_2026-09-25_GEBUEHRENEINHEIT.md`
     - `results/p1_befund/`
     - `scripts/p1_befund_gebuehreneinheit.py`
     - `tests/test_p1_befund_gebuehreneinheit.py`

     `main` holds them in final English form: `docs/paper1/FINDING_2026-09-25_FEE_UNITS.md`,
     `results/p1_finding/`, `scripts/p1_fee_units_finding.py` and `tests/test_p1_fee_units_finding.py`. The
     commit `955d205` (the Paper 1 finding) became empty and was dropped.
   - **Handover.** `docs/paper2/UEBERGABE.md` is `docs/paper2/HANDOVER.md` on `main`. The two German addenda of
     Paper 2 (24 and 25 September 2026) are appended unchanged to `HANDOVER.md`, to be translated later.
   - **`.gitignore`** is the union of both sides.
   - **OS artefacts.** The removal of `.DS_Store`, `paper/.DS_Store` and `paper/social/.Rhistory` (audit A69) is
     kept, although the last two lie under `paper/`. The guard in `tests/test_p2_ids.py` requires it.
   - No other path conflicted.
2. **Scrub.** `git filter-branch --index-filter` ran over `main..paper2-capital` with
   `scripts/p2_history_scrub.py index`. The script does the following:
   - it removes the six account fixtures from `tests/fixtures/p2`;
   - it replaces unsalted hashes by their p2ids labels;
   - it replaces long top-maker ids in `tests/` by 4242;
   - it replaces the ordered top list in `tests/test_p2_ids.py` by the synthetic list.

   Two extensions covered what the script leaves out:
   - **Override account ids in `tests/`.** Each raw PM2 override account id
     (`data/p2/params/*_pm2_overrides_raw.json`) became a synthetic five-digit placeholder, one per account.
     This also applies where the id was written as a hex literal or as a 32-byte log topic. The affected files
     are `tests/fixtures/p2/params_logs.json`, `tests/test_p2_params.py` and `tests/test_p2_history_scrub.py`.
   - **The checked override account in `docs/paper2/get_margin_semantik.md`.** From the first commit on, its raw
     id became its p2ids label. The file carried that label from Stage B on in any case.

   The scrubbed `results/p2/params/*_pm2_overrides.json` of Stage A to Addendum 4 are byte-identical to the
   labelled files of Stage B.
3. **English messages.** The commit messages were translated into English with `git filter-branch --msg-filter`.
   Type prefixes and `Co-Authored-By` trailers are kept verbatim. Each message still describes the original
   commit, for example "463 tests green" in Stage A, and "history not rewritten" and "Paper 1 finding
   reproducible" in the audit fix.
4. **Dates are kept.** Author and committer (name, e-mail, and date with time zone) of every original commit are
   kept, checked pair by pair. As a result, the rewritten commits are dated 24 and 25 September 2026 before their
   new parent `d2a2b43` (25 September 2026, 12:37 +0200). The dates record when the work was first committed.
5. **New commits on top.**
   - `b637822`: Paper 2 on the revised Paper 1 code. `inference_p1.analysis_frame` now divides fee and rebate
     by the amount. `edge_frame` therefore computes the pre-registered sensitivity in Paper 1's former form
     itself, and the result is bit-identical on the 603,940 fills. A test now passes the amount, and
     `roodman2019` in `paper2/refs.bib` equals `paper/refs.bib` again.
   - The commit of this file.

## Pre-registration and addenda

`docs/paper2/PRAEREGISTRIERUNG.md` is byte-identical in every pair (same git blob, same SHA-256). The diff of
each of these five commits against its parent is identical to the original diff: same files, same changes.
For every commit, the author date equals the committer date, and both equal the date of the original.

| Document | Old commit | New commit | Author and committer date | Git blob of PRAEREGISTRIERUNG.md | SHA-256 of PRAEREGISTRIERUNG.md |
|---|---|---|---|---|---|
| Pre-registration | `1d13227b6f0698f29fcd95d18c5828ae6a0bbc5e` | `cc0a29f655b50c7415e01583b25952e9831bbecd` | 2026-09-24 22:33:50 +0200 | `f251a0c5493e81a9dca98b1aecab54d2bde4349b` | `d777206a923e8eca4747043613914b0ba790e6b6f4d54b14244fb54784e46217` |
| Addendum 1 | `eb534fe80dea66e651589e1ea01dfdeec6040c47` | `85bb0b7e17a3d32731a83de40ab88b8e012f3983` | 2026-09-25 00:26:54 +0200 | `83693818948078d9f308e1083541056cd2924ac4` | `7f5f701d014d8fd5f7c401ef93dc622beaad14bd08fbcc66995b29b6fc3781c3` |
| Addendum 2 | `94652106387bc1f6006e0dbe02ac0a7edb13ea67` | `6005d7c53ccf51d3df7d038025f546eb5d07a6ef` | 2026-09-25 00:29:29 +0200 | `461a9af11090c853e2bbf0495c8f1b42c760f434` | `c2e6d5334c85d7dea95035a7d340cc20e41976c5d27e3cc74b3b6b7ffc8c53b6` |
| Addendum 3 | `bfc34c81c507c51a38e83878422b89d072f9ed18` | `8778432b49f01532809517d592acda4727d7aaa8` | 2026-09-25 00:29:56 +0200 | `55ea5cc2868ae7244fa693af5718171aef78673f` | `536a39cbac9a762d97d38e57ce1ac41439f22f676b3432ff31d8d3b9556c7c09` |
| Addendum 4 | `c4fcb59d61b73549aa90cacbd3b997816f36d823` | `e492ba123c4c81ddc478c0c6ef2246867deeeaae` | 2026-09-25 01:29:58 +0200 | `96986c732c85408daa4e704c519601bb531fdc4b` | `eb5e269571df785c0bc65e0b9ebb230dab9380edb95a951b63656eae07bb05f9` |

`PRAEREGISTRIERUNG.md` is not changed after Addendum 4. The tip carries the Addendum 4 version, and the blob
named in `docs/paper2/PREREGISTRATION_EN.md` is unchanged.

## All rewritten commits

| Old | New | Author and committer date | Message |
|---|---|---|---|
| `6559b21` | `b2dd70e` | 2026-09-24 22:29:04 +0200 | docs(p2): semantics of get_margin clarified, contradiction 11 vs 1.2 resolved |
| `1d13227` | `cc0a29f` | 2026-09-24 22:33:50 +0200 | prereg(p2): specification and pre-registration before the first capital figure |
| `cccfc01` | `0968031` | 2026-09-24 22:37:01 +0200 | plan(p2): overall plan in seven stages |
| `9b1394f` | `fca1aea` | 2026-09-24 22:38:06 +0200 | feat(p2): throttled chain client with block clock |
| `bd11559` | `d1bdd69` | 2026-09-24 22:59:46 +0200 | docs(p2): literature checked and manuscript skeleton |
| `e7361d2` | `78566f1` | 2026-09-25 00:26:36 +0200 | feat(p2): Stage A - feed history, parameter timelines, SM/PM/PM2 replication, maker holdings |
| `eb534fe` | `85bb0b7` | 2026-09-25 00:26:54 +0200 | prereg(p2): Addendum 1 before the first capital figure (exact on-chain book for H2) |
| `aaec2d3` | `a59f2b9` | 2026-09-25 00:27:22 +0200 | chore(p2): machine-wide lock for memory-heavy jobs |
| `9465210` | `6005d7c` | 2026-09-25 00:29:29 +0200 | prereg(p2): Addendum 2 - fee and rebate are totals per fill |
| `bfc34c8` | `8778432` | 2026-09-25 00:29:56 +0200 | prereg(p2): Addendum 3 - bootstrap and placebo made precise before the inference |
| `c4fcb59` | `e492ba1` | 2026-09-25 01:29:58 +0200 | prereg(p2): Addendum 4 - readings of H2 to H4 before the first test statistic |
| `591d2d5` | `58551d6` | 2026-09-25 01:30:22 +0200 | feat(p2): Stage B - validation, capital per fill, marginal cost, netting, doses, surface |
| `93b42bc` | `f7ba923` | 2026-09-25 02:16:35 +0200 | feat(p2): Stage C - inference H1 to H4 with independent recomputation |
| `955d205` | dropped | 2026-09-25 02:16:35 +0200 | docs(p1): finding on the fee unit (on `main` in final form) |
| `03ee4ca` | `ae90485` | 2026-09-25 02:49:10 +0200 | feat(p2): MM sensitivity H2 with one lib per ratio, API snapshot, CLI |
| `48e4032` | `ae87357` | 2026-09-25 03:49:47 +0200 | feat(p2): Stage D - nine figures, GIF of the capital surface, social cards |
| `3ec74f4` | `1894bad` | 2026-09-25 04:05:41 +0200 | feat(p2): Stage E - manuscript, check chain, referee and numbers round |
| `d51ede0` | `1c29ba8` | 2026-09-25 05:02:45 +0200 | docs(p2): audit of the whole paper (69 findings) |
| `c510913` | `f94bc53` | 2026-09-25 07:40:56 +0200 | fix(p2): audit findings fixed (57 fixed, 9 with a remainder, 3 for the author) |
| `469cc8e` | `fe331b0` | 2026-09-25 07:41:34 +0200 | docs(p2): morning report and handover addendum |

Some commits differ from the original in their own diff, not only in their base:
- `b2dd70e`: `HANDOVER.md` instead of `UEBERGABE.md`, and the label in `get_margin_semantik.md`;
- `78566f1`, `58551d6`, `f7ba923` and `ae90485`: the scrub;
- `f94bc53`: the scrub, and the Paper 1 files dropped;
- `fe331b0`: `HANDOVER.md`.

The other commits have the same diff as their originals.

## Checks

- **A01, the script's check.** `scripts/p2_history_scrub.py check main..paper2-capital` reports 0 files. It
  reported 12 files over the old range.
- **A01, a wider scan.** A second scan covered every file of every tree in `main..paper2-capital`, not only the
  Paper 2 roots. It looked for:
  - unsalted hashes of all ids below 250,000;
  - sha256, sha1 and md5 prefixes of the ids of the top ten and of the override accounts;
  - five-digit ids of these accounts, whether written as a decimal token, as a hex literal or as a 32-byte word
    (also in inflated PDF streams);
  - the ordered top list;
  - the six fixture paths.

  None of these categories has a match. Over the old range, the same scan flagged 17 files. Top-ten ids with
  one to four digits cannot be told apart from ordinary numbers. The scan therefore also looks for such a number
  right after an account-like key. It finds three test files, `tests/test_p2_books.py`,
  `tests/test_p2_inference.py` and `tests/test_p2_params.py`, and the matches are synthetic test values (for
  example accounts 5 and 7 in `tests/test_p2_params.py`).
- **End state.** `git diff paper2-kapital paper2-capital` shows differences only in these places:
  - Paper 1 files and other files in their `main` version (`derive_surface/animate.py`,
    `derive_surface/markouts.py`, `docs/derive_api_notes.md`, `docs/superpowers/*p1*`, `tests/conftest.py`);
  - `HANDOVER.md` and `UEBERGABE.md`;
  - the three scrubbed test files;
  - `b637822`;
  - this file.

  The private fixtures were already absent from the tip of `paper2-kapital`.
- **Tests and build.** `python3 -m pytest -q` gives 1004 passed, with the private fixtures under
  `data/p2/fixtures_private`. `python3 scripts/p2_build.py` gives "build clean" (12 pages, 352 numbers checked)
  in a checkout whose repository still holds the old commits.

## Consequences and open points

- **Old hashes are still cited.** The manuscript and several files name the old hashes:
  - `paper2/main.tex` names `1d13227`, `eb534fe`, `9465210`, `bfc34c8` and `c4fcb59`, and also `103c676` of
    Paper 1, which is `81d89dc` on `main`;
  - `derive_surface/social_p2.py` and the social cards name `1d13227` in the footer;
  - so do `docs/paper2/MANUSKRIPT.md`, `ZAHLENPRUEFUNG.md`, `ABBILDUNGSWAHL.md`, `VALIDIERUNG.md`,
    `PREREGISTRATION_EN.md` and `tests/test_p2_number_check.py`.

  In a clone that holds only this branch, the old commits do not exist. There `scripts/p2_build.py` fails with
  nine numbers without source, all of them commit references.

  Still to do:
  1. Write a dated Addendum 5 to `PRAEREGISTRIERUNG.md` with the mapping above and its translation in
     `PREREGISTRATION_EN.md`, including the new blob hash.
  2. Then put the new hashes into `main.tex`, the social cards and the files listed above.
  3. Regenerate `ZAHLENPRUEFUNG.md`.

  `AUDIT.md`, `HISTORIE_BEREINIGEN.md` and `BERICHT_2026-09-25.md` are dated reports about the old history and
  stay as they are.
- **Missing fixtures in rewritten commits.** The rewritten intermediate commits lack the six account fixtures.
  Their tests that need them do not run in those commits.
- **Limits of the pseudonyms.** The limits in `HISTORIE_BEREINIGEN.md`, section 6, still hold:
  - the ranks M1 to M10 can be recomputed from the public tape;
  - the X labels of override accounts can be matched through the public `LibOverrideUpdated` events.
    `tests/fixtures/p2/params_logs.json` keeps the transaction hash of the event whose account topic was
    replaced.

  The rewrite removes the raw ids and the reversible hashes, not these routes.
- **Before the push.** Push only `paper2-capital`. Integrate it with a merge commit (A02), and anchor the new
  hashes externally (OpenTimestamps or OSF).
