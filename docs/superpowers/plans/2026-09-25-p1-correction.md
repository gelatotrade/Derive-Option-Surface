# Paper 1: Correcting the Fee Unit (Revision for SSRN) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct paper 1 so that the fee, the rebate and the map per notional actually adhere to the registered unit "USDC per contract", carry the correction through all affected numbers, figures and passages, and build a revised PDF for SSRN.

**Architecture:** Branch `paper1-korrektur` from `paper1-adverse-selection`. Smallest possible code correction at the source (`inference_p1.analysis_frame` and the places that read raw fee or notional columns), test-driven with fills of quantity ≠ 1. Then a rerun of the inference and figures on the pilot data (cut 2026-09-17 12:00 UTC), an independent recalculation against `scripts/p1_fee_units_finding.py`, a text revision with a revision note, an audit, the build.

**Tech Stack:** Python 3.9.6, pandas, numpy, matplotlib, pytest, tectonic.

**Finding:** `docs/paper1/FINDING_2026-09-25_FEE_UNITS.md` (cause, numbers old and new, affected places, code recommendation).

## Global Constraints

- Change only paper 1 files (`derive_surface/*p1*`, `figdata.py`, `figures_p1.py`, `figures_social.py`, `classify.py` only if needed, `scripts/p1_*`, `tests/test_p1_*`, `results/p1/`, `docs/paper1/`, `paper/`). Do not touch anything under `data/p2/` or `paper2/`.
- The pre-registration is not overwritten: only a dated addendum 3 at the end of `docs/paper1/PRAEREGISTRIERUNG.md`. The pre-registration commit `3fd9caa` remains the reference in the manuscript.
- Hypotheses, thresholds and sample remain unchanged; the only change is the unit in which the registered definition is implemented.
- Agents do not commit; the orchestrator commits with selected paths (never `git add -A`, because `data/p2/` and `paper2/` are not ignored here).
- Paper in English, documentation in German, no em or en dashes in running text, keep to the word budgets of paper 1.

## Tasks

### K1: Addendum 3 to the pre-registration
- [ ] Dated addendum: fee and rebate in the tape are sums per fill; NE per contract = MO − (fee − rebate)/quantity − hedge; the map per notional divides the sum of the edge by the sum of the notional (or NE per contract by index per contract); cause, discovery on 2026-09-25, no change to hypotheses or thresholds.

### K2: Code correction (test-driven)
- [ ] Failing tests with fills of quantity 0.1 and 5: NE per contract, waterfall identity (HS + AS − fee + rebate − hedge = NE), class table, bp map per notional.
- [ ] `inference_p1.analysis_frame`: columns `fee_pc`, `rebate_pc` per contract; `net_edge` computed from them.
- [ ] Waterfall, T2 error bars and class table (`figdata.py`, `inference_p1.py`) read the per-contract columns.
- [ ] F5 (`figures_p1.py`) and S5 (`figures_social.py`): bp per notional made consistent (NE per contract divided by index per contract).
- [ ] F1c/F2c: premium share and markout units per contract.
- [ ] Suite green.

### K3: Rerun on the pilot data
- [ ] Inference (`python3 -m derive_surface p1 …`), figures, numbers sheet, figure check.

### K4: Independent recalculation
- [ ] All changed headline numbers against `results/p1_finding/fee_units.csv` (generated with `scripts/p1_fee_units_finding.py`); resolve any discrepancies.

### K5: Manuscript and accompanying material
- [ ] All affected passages according to the finding (abstract, decomposition, classes including the sign change of the vault class, H4 section, map per notional, conclusion), revision note on page 1 (date of the first version 2026-09-19, revision 2026-09-25, what was corrected).
- [ ] `docs/paper1/NUMBERS.md`, `FIGURE_FINDINGS.md`, `MANUSCRIPT.md`, `paper/social/x_article.md` and the cards S1/S5; new text for the SSRN abstract field and a short correction note for X in `docs/paper1/REVISION_2026-09-25.md`.
- [ ] Build with `python3 scripts/p1_build.py`, word budget, figure check; replace the upload file `paper/Derive Orderbook Adverse Selection.pdf`.

### K6: Audit of the revision
- [ ] Numbers (text against results), content (referee: does every statement hold after the correction, is the revision note fairly worded), form (layout, figures, dashes); fix the findings; final build.
