# Manuscript of Paper 1

Acceptance record. First version at the end of plan 5 (19 September 2026), revision on 25 September 2026 after
the finding on the fee unit (`FINDING_2026-09-25_FEE_UNITS.md`, addendum 3 to the pre-registration, list of
changes in `REVISION_2026-09-25.md`). The word counter is `scripts/p1_wordcount.py`; the budget applies per
section with a 10 % tolerance.

| Section | First version | Revision | Budget | Status |
|---|---|---|---|---|
| abstract | 156 | 156 | 150 | within budget |
| Introduction | 571 | 571 | 550 | within budget |
| The venue and the tape | 396 | 396 | 450 | within budget |
| What a markout measures | 419 | 484 | 550 | within budget |
| Pre-registration and inference | 239 | 270 | 250 | within budget (limit 275) |
| Results | 1025 | 1198 | 1100 | within budget (limit 1210) |
| What this means for a maker | 353 | 378 | 350 | within budget (limit 385) |
| What this cannot show | 238 | 238 | 250 | within budget |
| Conclusion | 177 | 181 | 180 | within budget |
| **Total** | **3574** | **3872** | **3,830** | |

The revision note on page 1 is a title footnote (`\tnotetext`) placed before `\maketitle` and does not count.

## Build (revision)

| Quantity | Value |
|---|---|
| Pages | 9 |
| Figures | 9, of which 8 span two columns |
| Bibliography entries in total | 24 |
| of which cited | 22 |
| Overfull lines | none |
| Figure check (`scripts/p1_figure_check.py`) | 29 checks, 0 deviating |
| Upload file | `paper/Derive Orderbook Adverse Selection.pdf` = copy of `paper/main.pdf` |

Captions: `derive_surface/figures_p1.py`, `CAPTIONS`, word for word identical to `paper/main.tex` (T2, F1, F2 and
F5 adjusted in the revision). Every bibliography entry was checked against the publisher's page, RePEc or DOI.

## Open

- SSRN: upload the revision, with the abstract field and revision description from `REVISION_2026-09-25.md`.
- Final data run with the registered cutoff 30 September 2026 08:00 UTC; then check every number in the text
  against the new numbers sheet and upload it as a further revision.
- A push or pull request for the public repo is a user decision.
