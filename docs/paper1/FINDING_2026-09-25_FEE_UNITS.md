# Finding of 25 September 2026: unit of fee and rebate in the net edge of Paper 1

Status: correction implemented on 25 September 2026 (addendum 3 to the pre-registration, `REVISION_2026-09-25.md`). When this finding was written, nothing in Paper 1 had been changed yet. Pilot cut 17 September 2026 12:00 UTC, 603,940 fills, horizon 30 min.

Computation: `scripts/p1_fee_units_finding.py` (a copy of the Paper 1 logic with a selectable fee unit),
invoked as `python3 scripts/p2_heavy.py --wait-max 500 -- python3 scripts/p1_fee_units_finding.py`, about two
minutes; intermediate results under `data/p1/fee_units_finding/` (not in Git, a restart skips finished
steps). Tests: `tests/test_p1_fee_units_finding.py` (15, offline and synthetic, part of the suite).
Numbers: `results/p1_finding/fee_units.csv` (long format, columns `section, item, variant, value, lo, hi, …,
p1_reference, matches_p1`), verdicts `results/p1_finding/fee_units.json`, corrected cell table
`results/p1_finding/h4_cells_per_contract.csv`.

**Status of the files.** The first version ran from a copy under `data/p2/p1befund/`, which `.gitignore`
excludes. Since the audit of Paper 2 (`docs/paper2/AUDIT.md`, A25 to A27 and A65 to A68), the script has been
under version control in `scripts/`. A rerun from scratch reproduces the committed numbers bit for bit: the first
611 rows of the CSV (sections `decomposition` to `f1_premium_share`), `h4_cells_per_contract.csv`, the verdicts
(`h4`) and all reproduction checks in the JSON, as well as all 25 intermediate files. Appended are the sections
`f5_bp_summary` (A65), `class_clusters` (A66), `decomposition_b9999` and `classes_b9999` (A68), `rfq_booking`
and `rfq_package` (A67). In the JSON only `meta.script` and `meta.note` change; `rfq_booking` and
`h4_rfq_package` are new.

## What

`derive_surface/inference_p1.py`, `analysis_frame`, line 232:

    net_edge = mo_usd − fee_maker + rebate_maker − hedge

`mo_usd` and `hedge` are per contract, `fee_maker` and `rebate_maker` (`trade_fee`, `expected_rebate` of the
maker row) are sums per fill. Correct is

    NE = mo_usd − (fee_maker − rebate_maker) / amount − hedge,   edge of the fill = NE · amount.

Evidence: the maker fee grows with the amount, the fee per contract does not. BTC, median of the positive
fees: 0.11 USDC at ≤ 0.02 contracts, 19.4 at > 0.5; per contract 11.1 and 15.6 respectively. HYPE: 0.07 to 9.1
per fill, 0.006 to 0.007 per contract. The rebate behaves the same way. The audit confirms this on the tape: the
maker fee is amount · min(rate · index, 12.5 % · mark), and the slopes of log(fee) and log(rebate) on
log(amount) are close to 1. The amount varies over several orders of magnitude (median BTC 0.1, ETH 1, HYPE 125
contracts), so the error per cell is very uneven. The Paper 1 test
(`test_analysis_frame_decomposes_the_markout`) uses `amount = 1` and could not find it.

**RFQ packages (A67).** The statement "sum per fill" holds strictly for order-book fills. In multi-leg RFQs,
Derive almost always books the maker fee of the package on exactly one leg: of 39,366 packages with more than one
leg (package = `rfq_id` and maker wallet), 4,996 carry a maker fee; for 4,511 of these it sits on exactly one
leg, for 95 on all legs; there are no rebates in RFQ. The leg formula matches the large majority of fills in the
order book (audit 84.9 %; our own rough check with 3 bp before and 1 bp from February 2025 gives 83.4 %), and
almost never in RFQ (6.7 % and 0.3 % respectively; the match rate depends on the assumed rate). `fee_maker /
amount` therefore places the fee of the package on the leg on which it is booked. Numerically this is
immaterial. In the sensitivity `per_contract_package` every leg carries Σ fee / Σ amount of its package: mean
fee over the RFQ fills 0.3115 leg by leg against 0.3177 per package, fee in the overall mean −1.0911 against
−1.0924, net edge +9.5795 against +9.5782; H4 stays at 74 of 97 positive cells and 0 negative, no cell verdict
changes, and the largest cell mean shifts by 0.13 USDC (BTC 75-90 Δ, 2-7 d). The P1 addendum should contain a
sentence on this, as should addendum 2 of Paper 2 (`docs/paper2/PRAEREGISTRIERUNG.md` lines 111 to 118; not
part of this finding).

## Reproduction before the correction

The variant `p1` matches Paper 1 exactly (all 67 comparisons in the JSON, `reproduced: true`):
`analysis_frame` bit-identical (hs, y_usd, as_usd, hedge, net_edge); all 97 cells from `results/p1/h4_cells.csv`
identical in mean, lo, hi, p and flags (B = 9,999, seed 20260917 as registered); `h4_sensitivity.csv` at
0, 1 and 3 bp; all columns of `class_means.csv`; T2 = 8.93245 (`FIGURE_CHECKS.md`); the decomposition in the text
(+15.70, −2.65, −1.56, +0.59, −3.15, +8.93); the F5 text values (BTC 9.0 and 28.5 bp, text "twenty-nine"); the
quartiles of F1c. The Paper 1 seed is deliberate: only with it can the old intervals be checked.

## Numbers old and new

**Decomposition per contract** (mean, 95 % cluster bootstrap over taker wallets, **B = 9,999**, seed 20260917,
that is, with as many draws as Paper 1 states for its intervals; exploratory; CSV `decomposition_b9999`)

| Component | old (Paper 1) | new (per contract) |
|---|---|---|
| Half spread | +15.70 | +15.70 |
| Adverse selection | −2.65 | −2.65 |
| Fee | −1.56 (−1.96 to −1.20) | −1.09 (−1.35 to −0.81) |
| Rebate | +0.59 (0.46 to 0.74) | +0.77 (0.65 to 0.91) |
| Hedge | −3.15 | −3.15 |
| **Net edge** | **+8.93** (1.30 to 17.32) | **+9.58** (1.56 to 18.31) |
| Median net edge | 0.74 | 0.63 |
| amount-weighted Σ NE·a / Σ a | −70.46 | +0.19 |
| Sum Σ NE·a over all fills, USDC | −2,813 million | +7.48 million |

With B = 999, as for the error bars of T2 (CSV `decomposition`, state of the first version), the intervals for
fee, rebate and net edge are, old, −1.92 to −1.18, 0.47 to 0.73 and 1.25 to 17.34, and, new, −1.33 to −0.80,
0.64 to 0.91 and 1.46 to 18.43. Only the values with B = 9,999 should be cited in the text (A68, see
recommendation 4).

The mean per fill shifts by only +0.65. Any amount-weighted aggregation of the old form, by contrast, is
unusable, because the fee sum is multiplied by the amount a second time. Paper 1 reports no such aggregation of
the net edge.

**Counterparty classes.** The headline numbers +24.73 (ordinary takers) and −25.41 (dominant makers) are
markouts and **do not change**, nor do half spread, adverse selection and hedge per class. Fee, rebate and net
edge change (columns in the numbers sheet, not cited in the manuscript text). G is the number of taker wallets
behind the class, that is, the clusters of the bootstrap; in parentheses, the share of the largest wallet in the
fills of the class (CSV `class_clusters`). Intervals with B = 9,999 (CSV `classes_b9999`; with B = 999 in
`classes`).

| Class | G (largest wallet) | Markout | NE old | NE new (95 %, B = 9,999) | Fee old / new | Rebate old / new |
|---|---|---|---|---|---|---|
| dominant_maker | 17 (82 %) | −25.41 | −30.49 | −31.98 (−35.96 to −26.95) | 1.23 / 2.75 | 0.08 / 0.11 |
| mm_programme | 33 (83 %) | −20.67 | −25.15 | −26.76 (−30.28 to −3.58) | 1.13 / 1.82 | 1.59 / 0.66 |
| large | 104 (13 %) | +3.89 | −1.63 | +0.79 (−12.41 to 15.90) | 4.55 / 1.35 | 1.78 / 1.02 |
| vault | **8** (36 %) | +4.22 | −28.58 | +2.09 (no reliable interval, G = 8) | 34.21 / 1.13 | 2.44 / 0.02 |
| rfq | 4,512 (3 %) | +15.21 | +11.19 | +11.80 (8.89 to 15.50) | 0.91 / 0.30 | 0 / 0 |
| other | 10,749 (1 %) | +24.73 | +21.19 | +22.04 (19.43 to 25.26) | 1.24 / 0.96 | 0.57 / 1.14 |

The vault net edge changes sign because the old fee of 34.21 "per contract" was a sum over large fills; per
contract it is 1.13. The sign follows from the means themselves: markout +4.22 minus fee 1.13 and hedge 1.02,
plus rebate 0.02, gives +2.09. An interval does not support this statement (A66): the percentile cluster
bootstrap runs over only G = 8 taker wallets, one of which carries 36 % and two of which together carry 51 % of
the 1,994 vault fills, and it is too narrow with so few clusters. Numerically it gives 1.13 to 3.49 (B = 9,999;
with B = 999 1.05 to 3.49, in the audit with a different seed 1.15 to 3.60). When rewriting, omit the interval
or label it explicitly with G = 8, as the Paper 1 numbers sheet already does for H2. In weaker form this also
applies to dominant_maker and mm_programme, in each of which a single wallet carries over 80 % of the fills.

**H4** (90 % cluster bootstrap, B = 9,999, seed 20260917, rule of the Paper 1 pre-registration)

| | old | new |
|---|---|---|
| positive cells, 1 bp | 48 of 97 = **49.5 %** | 74 of 97 = **76.3 %** |
| significantly negative cells | 3 (ETH, low delta) | 0 |
| positive cells per underlying BTC / ETH / HYPE | 23 / 13 / 12 | 23 / 26 / 25 |
| cells newly positive / no longer positive | | 28 / 2 (BTC 60-75 Δ ≤ 2 d, HYPE 75-90 Δ 2-7 d) |
| sensitivity 0 bp / 3 bp | 57.7 % / 38.1 % | 78.4 % / 58.8 % |
| BTC [40,60) ≤ 2 d | +23.95 (7.24 to 44.83) | +24.19 (6.43 to 46.37) |
| ETH [40,60) ≤ 2 d | +0.36 (−0.41 to 1.34) | **+1.05 (0.20 to 2.10)** |
| verdict at 1 bp | rejected (ATM branch only) | rejected (both branches) |
| verdict at 0 / 1 / 3 bp | rejected / rejected / **not rejected** | rejected / rejected / rejected |

The three significantly negative ETH cells become significantly positive (ETH 00-10 Δ 2-7 d −4.23 becomes +0.47,
ETH 00-10 Δ 7-30 d −0.91 becomes +0.72, ETH 10-25 Δ 2-7 d −3.05 becomes +0.52). The verdict remains "rejected",
but for a different reason: the majority rule now applies clearly and across the whole range of the hedge
assumption. The core statement of the manuscript, that the result lies so close to the threshold that an
unobserved hedging premium between 0 and 1 bp decides it, no longer holds.

**F5 bp map** (median per cell, ≥ 200 fills). Here, besides the fee, there is a **second, larger unit
error**: F5 (`figures_p1.py` line 538) and the social card S5 (`figures_social.py` line 206) divide the net edge
**per contract** by `notional = amount · index` **of the whole fill**. That is a bp value only for one
contract. Consistent is NE·a / (a·index) = NE / index, the way the Paper 2 pre-registration defines the edge in
bp.

| Variant (CSV key) | BTC [40,60) ≤ 2 d / 30-90 d | ETH ditto | HYPE ditto | Cell median BTC / ETH / HYPE | Range BTC | Range ETH | Range HYPE |
|---|---|---|---|---|---|---|---|
| old, as in Paper 1 (`p1\|notional`) | 9.0 / 28.5 | 0.9 / 3.3 | 0.3 / 0.5 | 10.0 / 1.6 / 0.3 | 1.2 to 78 | −21 to 12 | 0.0 to 0.6 |
| fee corrected only (`per_contract\|notional`) | 8.8 / 28.4 | 1.1 / 3.5 | 0.0 / 0.1 | 9.2 / 1.5 / 0.1 | 1.5 to 78 | −19 to 12 | 0.0 to 0.4 |
| denominator corrected only (`p1\|index`) | 2.8 / 5.7 | 2.9 / 9.2 | 29.0 / 47.7 | 3.5 / 5.5 / 30.0 | 0.6 to 16 | −81 to 28 | −0.6 to 86 |
| **both corrected (`per_contract\|index`)** | **2.8 / 5.8** | **3.8 / 9.8** | **5.0 / 27.2** | **3.3 / 5.7 / 15.1** | 0.9 to 16 | −83 to 29 | −6.2 to 69 |

How strongly the denominator alone distorts is shown by comparing "old" with "denominator only" (same fee, A65):
BTC is inflated 3- to 5-fold (ATM ≤ 2 d 9.0 against 2.8, ATM 30-90 d 28.5 against 5.7, cell median
10.0 against 3.5), ETH is depressed by about a factor of three (0.9 against 2.9; 3.3 against 9.2), and HYPE is
divided by about 100 (0.3 against 29.0; 0.5 against 47.7). The factors are not simply 1 / median amount, because
the cell median runs over fills of very different amounts.

Which of the two errors accounts for how much depends on the order of the corrections. On the old denominator,
the fee correction moves the map by only tenths of a bp, because the denominator pushes HYPE towards zero anyway.
On the correct denominator **it halves the HYPE map** (cell median 30.0 against 15.1 bp, maximum 85.5 against
68.8, ATM ≤ 2 d 29.0 against 5.0): the old form credits the rebate sum of the whole fill per contract, and in HYPE
cells such as ATM ≤ 2 d the rebate exceeds the fee (0.25 against 0.03 USDC per fill at a median of 100
contracts). BTC stays almost the same, ETH rises slightly. The reversal of the ranking between the underlyings
comes from the denominator: even with the old fee, per unit of notional HYPE leads and BTC trails (cell median
3.5 / 5.5 / 30.0 bp), corrected 3.3 / 5.7 / 15.1 bp. All cells in the CSV (`section = f5_bp_map`), cell medians
in `f5_bp_summary`, ranges in `f5_bp_range`.

**Side finding F1c and F2c.** The same unit mix: markout per contract divided by the premium of the whole
fill (`price · amount`, `figures_p1._premium`). Quartiles old −1.6 / +1.1 / +21.1 %, per contract (markout /
price) −3.3 / +3.4 / +13.5 %. F2 panel c (median markout as a share of the premium across the horizons) uses the
same division and is affected in the same way; the text of Paper 1 cites no number from F2c. T2 panel b (fee of
the fill / premium of the fill, for maker and taker) is consistent and not affected.

## Affected places

**Manuscript `paper/main.tex`**

- Lines 70 to 72 (abstract) and lines 182 to 190 (text and figure T2): net edge +8.93 becomes +9.58, fee −1.56
  becomes −1.09, rebate +0.59 becomes +0.77. Half spread, adverse selection and markout stay.
- Lines 306 to 313 (H4): 48 positive, 3 negative, 46 open cells become 74, 0 and 23; 49.5 / 57.7 / 38.1 %
  become 76.3 / 78.4 / 58.8 %; the sentence about the hedge assumption between 0 and 1 bp is dropped; ETH ATM is
  now positive as well.
- Lines 194 to 197, 314 to 316, caption line 321 and section 6 lines 343 to 351: all bp statements (BTC
  "nine" to "twenty-nine", ETH "one and three", HYPE "between zero and one", "nothing at all", "two of the
  three underlyings do not pay", "rises monotonically") stem from the denominator error and must be rewritten.
- Lines 398 to 400 (conclusion): "net edge sits so close to the registered threshold that an unobserved hedging
  cost decides it" no longer holds.
- Lines 233 to 235 (F1c): quartiles of the premium share, see side finding.
- Lines 217 to 223 (inference): "Every interval reported in this paper was drawn the same number of times as the
  headline it belongs to", at B = 9,999. The intervals of the decomposition and the classes in the first version
  of this finding are drawn with B = 999; see recommendation 4.
- Side observation, lines 214 to 215: the manuscript states H4 the reverse way round from the pre-registration
  ("holds that a net edge survives in a majority … rejected otherwise"), and line 313 ("fires either way") does
  not fit the old numbers, where only the ATM branch applied. Correct this as well when rewriting.

**Committed PDF and figures**

- `paper/Derive Orderbook Adverse Selection.pdf` (commit 0afff2c): renamed copy of the manuscript that gets
  around the `.gitignore` for `paper/main.pdf`. It contains all the old statements listed above (text extraction:
  "leave a net edge of +8.93", T2 label "−1.56 +0.59 … +8.93", "sits just under it at 49.5 per cent",
  "57.7 49.5 38.1" in the F5 panel, "about nine basis points … twenty-nine", "nothing at all", "−1.6 … +21.1 per
  cent"). Remove it from the repo or mark it explicitly as superseded, and generate it again after the correction.
- `paper/figures/t2.pdf` (bars and error bars of fee, rebate, net edge), `f5.pdf` (bp row and sensitivity
  panel), `f1.pdf` (panel c, quartiles), `f2.pdf` (panel c): rebuild.

**Social texts and cards**

- `paper/social/x_article.md`, article: lines 37 to 38 (8.93), lines 83 to 87 ("rises … in all three
  underlyings, and BTC is in a different league", "HYPE sits between 0.1 and 0.6 basis points … nothing at all"),
  lines 96 to 98 (49.5 % and hedging costs between zero and one bp).
- `paper/social/x_article.md`, thread: tweet 3 lines 136 to 137 (+8.93 USDC per contract) and tweet 7 lines 176
  to 178 ("BTC is in a different league", "HYPE pays 0.1 to 0.6 bp … After hedging, nothing"). The preliminary
  remark in lines 4 to 5 ("will move slightly") does not hold for H4 and the map.
- Cards `paper/social/s1_decomposition.png` (fee, rebate and NET EDGE from `figdata.waterfall_components`)
  and `paper/social/s5_map.png` (bp map; subtitle "HYPE pays almost nothing anywhere." from
  `derive_surface/figures_social.py` lines 210 to 211).

**Documentation**

- `docs/paper1/NUMBERS.md`: H4 lines 27 to 30, sensitivity lines 36 to 38, class table lines 44 to 49
  (fee, rebate, net edge), cells with the largest and smallest net edge lines 63 to 74 (the three
  ETH cells with low delta appear there as the most negative and are now significantly positive).
- `docs/paper1/FIGURE_CHECKS.md` line 22: T2 check value 8.93245.
- `docs/paper1/FIGURE_FINDINGS.md` §2 lines 13 to 28: old bp table (BTC 9.0 / 28.5 / 73.8, ETH 0.9 / 3.3 /
  4.8, HYPE 0.3 / 0.5 / 0.1), "the ranking is the same in all three underlyings", "about one order of
  magnitude" between the underlyings, "HYPE … practically nothing". §1 stays as it is in substance (the BTC cells
  in USDC change by at most 3.1 USDC, median of the cells ≤ 2 d 23.95 against 24.19, > 90 d 204.4 against 204.2).
- `docs/paper1/FIGURE_SELECTION.md` line 59: the recomputation replaced the quartiles of a draft, −3.3 / +3.4 /
  +13.5 %, with −1.6 / +1.1 / +21.1 %. The values of the draft were the consistent form per contract; the
  "correction" introduced the unit mix. Also line 50 (sensitivity 57.7 %).
- `docs/paper2/HANDOVER.md` lines 26 to 27 (decomposition with −1.56 / +0.59 / +8.93).
- For information only, not to be rewritten because it is a record: `docs/superpowers/plans/2026-09-18-p1-figures.md`
  lines 254 to 255 and 334.

**Not affected:** H1 (90.5 %, size, sweeps), H2, H3, all markouts including +24.73 and −25.41,
horizons, path comparison, T2 panel b, figures T1, F3, F4, F6, A1 and the cards S2 to S4.

## Recommendation for the final data run

1. **Addendum.** Before the run, a dated addendum in `docs/paper1/PRAEREGISTRIERUNG.md` (English translation:
   `docs/paper1/PREREGISTRATION.md`): fee and rebate of the maker row are sums per fill and are divided by the
   amount (as in addendum 2 of Paper 2); in multi-leg RFQs the fee is a sum per package and booked on one leg, and
   the distribution across the package is reported as a sensitivity. State openly that the error was found after
   the pilot run. Report the old form as a sensitivity.

2. **Code, complete.** The correction in `analysis_frame` alone is not enough: the waterfall, the T2 error bars
   and the class table keep reading the raw columns. Correcting only `net_edge` would leave T2 showing a fee of
   −1.56 and a rebate of +0.59 next to an NE bar of +9.58, S1 would keep +8.93, and `class_means.csv` would keep
   the old fees. All places:

   a. `derive_surface/inference_p1.py`, `analysis_frame` (line 232): form columns per contract and use only
      them.

          amount = f["amount"].to_numpy(float)
          amount = np.where(amount > 0, amount, np.nan)
          f["fee_pc"] = f["fee_maker"].to_numpy(float) / amount
          f["rebate_pc"] = f["rebate_maker"].to_numpy(float) / amount
          f["net_edge"] = f["y_usd"] - f["fee_pc"] + f["rebate_pc"] - f["hedge"].to_numpy()

      The H4 cells and `h4_sensitivity.csv` (`cell_table` on `net_edge`) then follow automatically.
   b. `derive_surface/inference_p1.py`, class table (lines 371 to 372): `mean_fee` from `fee_pc`,
      `mean_rebate` from `rebate_pc`. `scripts/p1_numbers.py` reads these columns.
   c. `derive_surface/figdata.py`, `waterfall_components` (lines 145 to 146): `fee_pc` and `rebate_pc` instead of
      `fee_maker` and `rebate_maker`. This corrects T2 (`figures_p1.py` line 182), the card S1
      (`figures_social.py` line 89) and the T2 check in `scripts/p1_figure_check.py` lines 58 to 60.
   d. `derive_surface/figures_p1.py`, `fig_t2` panel a (lines 183 to 184): intervals from `fee_pc` and
      `rebate_pc`. Panel b (lines 238 to 242) stays with `fee_maker / (price · amount)` and
      `fee_taker / (price · amount)`: the sum of the fill divided by the premium of the fill is consistent.
   e. F5 and S5 (`figures_p1.py` line 538, `figures_social.py` line 206): `bp = 1e4 · net_edge / index_price`
      (equal to NE·a / (a·index)), or as a cell ratio Σ NE·a / Σ index·a as in Paper 2. Rewrite the subtitle of S5
      (`figures_social.py` lines 210 to 211, "HYPE pays almost nothing anywhere").
   f. F1c (`figures_p1.py` lines 317 to 318) and F2c (lines 338, 346 and 362): markout per contract divided by
      `price`, not by `_premium(...) = price · amount`. `_premium` (lines 50 to 51) stays only for T2 panel b.
   g. `scripts/p1_figure_check.py`: the T2 check (lines 58 to 60) then makes a real comparison again; in
      addition, check that the fee step equals −mean(`fee_pc`) and that the F5 text values come from NE / index.
   h. Tests with `amount ≠ 1`. Extend `test_analysis_frame_decomposes_the_markout` (`tests/test_p1_inference.py`)
      with amounts such as 0.5 and 4. `test_waterfall_components_add_up_to_the_net_edge`
      (`tests/test_p1_figdata.py`) is tautological, because the row "net edge" is itself the sum of the steps;
      it has to check against the mean of `net_edge` of an `analysis_frame`:

          f = inf.analysis_frame(rows_with_amounts([0.5, 4.0]), funding)
          steps = figdata.waterfall_components(f).set_index("step")["value"]
          assert steps.drop("net edge").sum() == pytest.approx(np.nanmean(f["net_edge"]))
          assert steps["maker fee"] == pytest.approx(-np.nanmean(f["fee_maker"] / f["amount"]))

      In addition, one test each for the class table (fee per contract), F5 (bp = NE / index) and F1c/F2c
      (markout / price). Template: `tests/test_p1_fee_units_finding.py`.

3. **Afterwards**, produce the numbers sheet, `p1_figure_check.py`, the figures, the social cards,
   `x_article.md`, the committed PDF and the text passages named above anew; rewrite the H4 paragraph, section 6
   and the conclusion in substance, not just swap the numbers.

4. **Intervals (A68).** If intervals of the decomposition or of the classes are cited in the text, use those with
   B = 9,999 (`decomposition_b9999`, `classes_b9999`), so that the sentence in `paper/main.tex` lines 222 to 223
   holds. The error bars of the figures are drawn with B = 999 (`figures_p1.py` line 36); in that case either
   restrict the sentence to the intervals in the text or compute the figures with 9,999 draws as well. Give the
   vault interval only with G = 8, or not at all (A66).

5. Paper 2 already computes per contract; after the correction, both papers are consistent.
