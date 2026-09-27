# Manuscript of Paper 2: outline, word budget and placeholders

Status: 24 September 2026, 23:00 UTC+2. Belongs to `paper2/main.tex` (draft before the first capital figure).

**Addendum 25 September 2026 (pilot cut 17 September 2026):** all placeholders are filled; abstract, results,
discussion and conclusion are written; the captions come from `derive_surface/figs_p2/<slot>.py` (one justified
exception in F2, see `CAPTION_EXCEPTIONS` in `scripts/p2_build.py`). The tables below describe the state before
the results. Check chain: `scripts/p2_wordcount.py` (budget per section), `scripts/p2_number_check.py` (every
number, every date and every time of day is bound in its unit, that is abstract, section, subsection or caption,
via `% src source printed` to exactly one source, one entry per occurrence in the order of the text; rules in the
header of the script; report `docs/paper2/NUMBER_CHECK.md`) and `scripts/p2_build.py` (tectonic, log, overfull
boxes, required parts, dashes, citations, figures, captions, budget, numbers). After the final data run, rerun all
three: a number without a declaration, a declaration without its number and a declared value that is no longer
printed that way each stop the build.

**Addendum 25 September 2026 (audit):** the manuscript is revised according to `docs/paper2/AUDIT.md`; what changed
per finding and what stays open is in section 8. The tables in sections 1 to 4 are historical (state before the
results); the current word counts are in 8.1.

**Title:** What does the edge cost? Capital-adjusted market making under a public portfolio-margin engine.
That capital is measured through hypothetical portfolios of the engine and not through account balances is stated
in the third sentence of the abstract and in the second paragraph of the introduction.

**Build:** `cd paper2 && tectonic main.tex` runs without errors: 7 pages, 0 overfull boxes, no undefined
references. Only one underfull warning from `main.bbl` remains (a long DOI in the bibliography). The figures under
`paper2/figures/{t1,t2,f1,…,f6,a1}.pdf` are **temporary placeholders** (dashed frame with the slot name). The figure
pipeline overwrites them later. `paper2/thumbnails/cas-email.jpeg` is a copy from `paper/thumbnails/`. `cas-dc`
needs the file for the e-mail symbol; without it the build fails.

**Rules for the text:** English, concise, no dashes (em or en dash) in running text, only keys from
`paper2/refs.bib`. Every number comes from `results/p2/` or from the pre-registration (commit `1d13227`);
otherwise a `\PH{…}` stands there. The macro is `\newcommand{\PH}[1]{\textbf{[#1]}}`, so in the PDF the
placeholders appear in bold in square brackets. Before submission, `grep -c '\\PH{' paper2/main.tex` may return
only 1 (the definition).

---

## 1 · Outline and word budget

Counted with the logic of `scripts/p1_wordcount.py`: prose without figures, captions, comments and bibliography,
abstract included. Formulas count. The tolerance is +10 %.

| Section | Label | Content | Budget | now | Remaining |
|---|---|---|---|---|---|
| Abstract | n/a | question, measurement through hypothetical portfolios, four key numbers, pre-registration | 170 | 172 | 0 |
| 1 Introduction | `sec:intro` | capital instead of contracts; why Derive (public deterministic engine, parameters on chain, endpoint without an account); question and link to Paper 1; four contributions of the spec; H1 to H4 in one sentence each; results paragraph | 600 | 564 | ~40 plus `intro-results` |
| 2 The engine and what it returns | `sec:engine` | SM, legacy PM, PM2; net = C + V − R; pre/post; K_p; two engines (off-chain 2 %, on-chain rate feed); why C − net misleads, resolution 11.86 against 1.19; Fig. T1, T2 | 600 | 651 | at the limit (660) |
| 3 Data and measurement | `sec:data` | fills from Paper 1, manager windows; feeds and parameter timelines; capital per fill, cells, formulas; maker books, marginal cost, netting value; dose and regression for H4; inference; validation against `eth_call` | 600 | 643 | at the limit (660) |
| 4 Results | `sec:results` | 4.1 H1 (F1, F2), 4.2 H2 (F3), 4.3 H3 (F4), 4.4 H4 (F5, F6) | 1,400 | 453 | ~950 for the `*-reading` paragraphs and findings |
| 5 Discussion | `sec:discussion` | three paragraphs on meaning (`disc-map`, `disc-book`, `disc-price`), one paragraph on limits (done); Fig. A1 | 400 | 175 | ~225 |
| 6 Conclusion | `sec:conclusion` | two sentences done, `concl-results`, `concl-close` | 200 | 55 | ~145 |
| Back matter | n/a | Data, code and pre-registration (commit `1d13227`); Competing interest; Use of generative tools | n/a | 255 | n/a |
| **Total** | | | **3,970** | **2,968** | |

Like Paper 1, the total of 2,968 counts all sections including the back matter. Without the back matter it is
2,713.

Reserve for cuts if section 2 or 3 grows while being filled: in section 2 the sentence on
`figlewski1984`/`artzner1999` can move to the discussion. In section 3 the regression formula can move into the
caption of F6.

---

## 2 · Figures

| Slot | Label | Environment | Placeholder PDF | Caption draft | Data (planned) |
|---|---|---|---|---|---|
| T1 | `fig:t1` | `figure*` | 7.0 × 3.0 in | engine view of the BTC surface, colour = PM2 or SM capital per short contract | `results/p2/surface_t1.json` (block, grid, K per point) from `p2surface.py` |
| T2 | `fig:t2` | `figure*` | 7.0 × 2.6 in | net = C + V − R; factors on C − net against R for the probe books of 17 and 24 September | `results/p2/semantics/faktoren.csv` (available) |
| F1 | `fig:f1` | `figure*` | 7.0 × 3.6 in | capital per contract by manager over \|Δ\| × tenor, buy and sell | `results/p2/capital_cells.csv` |
| F2 | `fig:f2` | `figure*` | 7.0 × 3.2 in | edge per notional against edge per PM2 capital, rank links, ρ with interval (H1) | `results/p2/h1_cells.csv`, `summary.json` → `H1` |
| F3 | `fig:f3` | `figure` | 3.4 × 2.4 in | distribution of ΔK / K_single, threshold ½, median with interval (H2) | `results/p2/h2_marginal.csv`, `summary.json` → `H2` |
| F4 | `fig:f4` | `figure` | 3.4 × 2.4 in | K_SM / K_PM2 over maker-days, legacy beside it, threshold 2 (H3) | `results/p2/h3_netting.csv`, `summary.json` → `H3` |
| F5 | `fig:f5` | `figure*` | 7.0 × 3.4 in | OI shares by manager, parameter events, capital of a fixed reference book | `results/p2/params/*.json`, `results/p2/oi_shares.csv`, `results/p2/reference_book.csv` |
| F6 | `fig:f6` | `figure*` | 7.0 × 2.6 in | dose response with β, placebo distribution (H4) | `results/p2/h4_panel.csv`, `results/p2/h4_placebo.csv` |
| A1 | `fig:a1` | `figure*` | 7.0 × 2.6 in | deviation of the replica from `eth_call`, single contracts and books, thresholds 0.1 % and 1 % | `results/p2/validation.csv` |

The file names under `results/p2/` are proposals for `inference_p2.py`, `p2validate.py` and `figdata_p2.py`. If
they are named differently, this table has to follow. The captions are drafts. After the jury, as in Paper 1,
adapt them to the chosen design without introducing new numbers.

---

## 3 · Numbers already in the text

### 3a · From `results/p2/`

| Place | Number in the text | Source |
|---|---|---|
| Sec. 2, paragraph "Two engines" | fourteen listed BTC expiries | `results/p2/semantics/box_diskont.json`, key `box_2026-09-24T11:27Z`, 14 rows |
| ditto | two per cent to within 2.7 × 10⁻⁷ | ditto, field `r_api`, max \|r_api − 0.02\| = 2.70e−7 |
| ditto | 24 September 2026 | ditto, `api_ts` |
| ditto | 3.64 to 3.82 per cent | ditto, field `r_chain` min/max (the same in `v_konvention.json`, field `r_feed`) |
| Sec. 2, paragraph "Reading C − net", T2 caption | 11.86 (C − net), 10.76 (R) | `results/p2/semantics/faktoren.csv`, row `historisch 17.09. 10:45:13Z Blk 44810149`, `b17_exakt`, case B, columns `F_Cnet`, `F_R_engine` |
| ditto | 1.19 (C − net), 2.14 (R) | ditto, row `historisch 24.09. 09:24:59Z Blk 45110142 (H1_0928-81k_0929-76k-81k)`, `b24`, case B |
| ditto | block 44 810 149, 17 September 2026; block 45 110 142, "a week later" | ditto, column `messung` |
| ditto | PM2 value −496 859 USDC | ditto, row 24 September H1, case B, column `V_PM2` = −496,858.84 |
| T2 caption | 2.33 / 3.19 (17 September, case A); 1.46 / 3.61 (24 September, case A) | ditto, case A of the two historical rows |
| Sec. 4.3 | ratios on R ran from 2.14 to 10.76 | ditto, minimum and maximum of `F_R_engine` over all rows with `historisch` |

Note on the row of 24 September: `faktoren.csv` has two historical variants (`H1_…` and `H0_heutige_Liste`). The
text uses `H1_…` because this variant reproduces the original measurement (1.19 corresponds to the earlier reading
of 1.2, see `get_margin_semantics.md` section 4). The variant `H0` gives 1.22 and 2.52 and lies within the range
2.14 to 10.76.

### 3b · Constants from the pre-registration and the specification (not results)

These values are the design of the study and not a measurement. They are in `docs/paper2/PRAEREGISTRIERUNG.md`,
commit `1d13227`:

- Start of the sample 11 January 2024; manager windows: SM the whole period (HYPE from 11 November 2025), legacy
  PM BTC/ETH the whole period, PM2 BTC/ETH from 12 June 2025 23:00 UTC, HYPE from 11 November 2025.
- Net edge after "thirty minutes"; cells "from 200 fills"; "ten" dominant subaccounts; q = ±1; 10⁴ in the
  formulas (basis points).
- H2 "less than half", H3 "more than half" and threshold "two", H1 threshold "0.5", "90 per cent interval".
- H4: "fourteen days", dose filter "one per cent", "20 fills on each side", "five per cent", "95th placebo
  percentile", "100 placebo dates", "28 days".
- Inference: "9 999 draws". Validation: "48 random blocks", "20 maker-days", thresholds "0.1 per cent" and
  "1 per cent", "95th percentile".
- Back matter: commit `1d13227`, 24 September 2026, 22:33 UTC+2 (from `git log`).

Counting words without a measurement: "three managers", "four hypotheses/contributions", "two engines".

---

## 4 · All placeholders and what fills them

56 occurrences, 51 distinct keys (`n-fills`, `h1-rho`, `h2-median`, `h3-median` and `n-rejected` occur twice
each). Column "Source": planned file and field. Sentence placeholders (`*-reading`, `disc-*`, `concl-*`,
`intro-results`) are written only after the tests. Every number in them must also come from `results/p2/`.

### Abstract

| Placeholder | Meaning | Source |
|---|---|---|
| `n-fills` | number of fills with capital per fill (also sec. 3) | `results/p2/summary.json` → `sample.fills` (from `data/p2/derived/capital.parquet`, module `capital.py`) |
| `h1-rho` | Spearman ρ of H1 (also 4.1) | `summary.json` → `H1.rho` |
| `h2-median` | median ΔK / K_single of H2 (also 4.2) | `summary.json` → `H2.median` |
| `h3-median` | median K_SM / K_PM2 of H3 (also 4.3) | `summary.json` → `H3.median` |
| `h4-direction` | half-sentence: "fell by … basis points …" or "did not respond measurably" | `summary.json` → `H4.beta`, `H4.rejected` |
| `n-rejected` | number of rejected hypotheses, as a word (also conclusion) | `summary.json` → sum of `H*.rejected` |

### 1 Introduction

| Placeholder | Meaning | Source |
|---|---|---|
| `intro-results` | paragraph, one sentence per hypothesis with verdict and key number, order H1 to H4 | `summary.json` → `H1` to `H4` |

### 2 The engine and what it returns

| Placeholder | Meaning | Source |
|---|---|---|
| `t1-block` | block (with date) of the surface in T1 | `results/p2/surface_t1.json` → `block`, `ts` (module `p2surface.py`) |

### 3 Data and measurement

| Placeholder | Meaning | Source |
|---|---|---|
| `sample-end` | end of the sample (pilot 17 September 2026 12:00 UTC, final 30 September 2026 08:00 UTC) | `summary.json` → `sample.end` |
| `n-fills` | see abstract | see abstract |
| `val-median` | median \|ΔK/K\| of the replica against `eth_call`, over all underlyings and managers | `results/p2/validation.csv`, `summary.json` → `validation.median` (module `p2validate.py`) |
| `val-p95` | 95th percentile of the same quantity | ditto → `validation.p95` |

Caution: the sentence before it is in the past tense ("were checked"). If the replica misses the threshold, the
sentence must refer to the dated addendum of the pre-registration.

### 4.1 H1

| Placeholder | Meaning | Source |
|---|---|---|
| `f1-pattern` | one or two sentences: where SM, legacy PM and PM2 differ most, buy against sell | `results/p2/capital_cells.csv` |
| `f1-ratio-min` | smallest K_SM/K_PM2 of a short contract over populated cells | ditto, column `ratio_sm_pm2`, sell side |
| `f1-ratio-max` | largest, ditto | ditto |
| `h1-cells` | number of populated cells in the PM2 window | `summary.json` → `H1.cells` |
| `h1-rho` | see abstract | `H1.rho` |
| `h1-lo` | lower bound of the 90 % interval | `H1.lo` |
| `h1-hi` | upper bound of the 90 % interval (rejection if ≥ 0.5) | `H1.hi` |
| `h1-verdict` | "rejected" or "not rejected" | `H1.rejected` |
| `h1-reading` | which cells change rank most, along tenor, delta or side | `results/p2/h1_cells.csv` |
| `h1-pooled-sell` | pooled edge per PM2 capital, maker sell, bp | `H1.pooled_bp.sell` |
| `h1-pooled-buy` | ditto, maker buy | `H1.pooled_bp.buy` |

### 4.2 H2

| Placeholder | Meaning | Source |
|---|---|---|
| `h2-n` | number of fills tested | `summary.json` → `H2.n` |
| `h2-excl` | excluded fills with K_PM2,single ≤ 0 | `H2.excluded` |
| `h2-sample` | sentence on whether the pre-registered random sample (20,000 fills, seed 20260924) applies | `H2.sampled`, `H2.n_before_sampling` |
| `h2-median` | see abstract | `H2.median` |
| `h2-lo` | lower bound of the 90 % interval | `H2.lo` |
| `h2-hi` | upper bound (rejection if ≥ 0.5) | `H2.hi` |
| `h2-share-nonpos` | share of fills with ΔK ≤ 0, in per cent | `H2.share_nonpos` |
| `h2-verdict` | "rejected" or "not rejected" | `H2.rejected` |
| `h2-reading` | which fills are cheap at the margin (against the book) and which are dear (with the book) | `results/p2/h2_marginal.csv` |

### 4.3 H3

| Placeholder | Meaning | Source |
|---|---|---|
| `h3-days` | number of maker-days in the test | `summary.json` → `H3.days` |
| `h3-excl` | excluded maker-days with K_PM2 ≤ 0 | `H3.excluded` |
| `h3-median` | see abstract | `H3.median` |
| `h3-lo` | lower bound (rejection if ≤ 2) | `H3.lo` |
| `h3-hi` | upper bound | `H3.hi` |
| `h3-verdict` | "rejected" or "not rejected" | `H3.rejected` |
| `h3-legacy-ratio` | median K_Legacy / K_PM2 of the same books (exploratory) | `results/p2/h3_netting.csv`, `H3.legacy_median` |
| `h3-reading` | spread over makers and time, which books net least | `results/p2/h3_netting.csv` |

### 4.4 H4

| Placeholder | Meaning | Source |
|---|---|---|
| `h4-events-raw` | number of parameter changes in the pre-registered set before merging and filtering | `results/p2/h4_events.csv` (module `p2events.py`) |
| `h4-events` | events after merging per day and the 1 % filter | `summary.json` → `H4.events` |
| `h4-cells` | cell-event pairs with ≥ 20 fills per side | `H4.cell_events` |
| `h4-doses` | sentence: range and sign of the doses, tightening against loosening | `results/p2/h4_events.csv`, column `dose` |
| `h4-beta` | β in bp of the index per unit of log capital | `H4.beta` |
| `h4-p` | one-sided wild cluster bootstrap p | `H4.p` |
| `h4-placebo-pct` | percentile of β among 100 placebos | `H4.placebo_pct` (from `results/p2/h4_placebo.csv`) |
| `h4-verdict` | "rejected" or "not rejected" | `H4.rejected` |
| `h4-reading` | translation: bp of half spread per 10 % change in capital | computed from `H4.beta`, to be shown in the numbers sheet |

### 5 Discussion

| Placeholder | Meaning | Source |
|---|---|---|
| `disc-map` | paragraph: what the capital map changes compared with the notional map of Paper 1 (H1) | `h1_cells.csv`, `summary.json` → `H1` |
| `disc-book` | paragraph: what marginal cost and netting value mean for a maker's size and choice of manager (H2, H3) | `summary.json` → `H2`, `H3` |
| `disc-price` | paragraph: is capital a price that the half spread responds to (H4)? Reference to `comertonforde2010`, `brunnermeier2009` | `summary.json` → `H4` |
| `disc-time` | half-sentence on the time normalisations (to expiry, empirical holding time), exploratory | `results/p2/sensitivity_time.csv` |

### 6 Conclusion

| Placeholder | Meaning | Source |
|---|---|---|
| `concl-results` | one sentence per hypothesis in plain words with its key number | `summary.json` |
| `n-rejected` | see abstract | see abstract |
| `concl-close` | the one sentence a maker should take away | n/a |

---

## 5 · References in the manuscript

State after the audit (25 September 2026): all 30 keys from `paper2/refs.bib` are cited (check per entry in
`docs/paper2/LITERATURE.md`, equality of the entries shared with Paper 1 in `tests/test_p2_refs.py`):

| Section | Keys |
|---|---|
| 1 | brunnermeier2009, garleanu2011, ho1981, avellaneda2008, gueant2013, stoikov2009, garleanu2009, jameson1992, muravyev2016, christoffersen2018, fournier2020, chen2019, albiez2026, santaclara2009, kupiec1996, comertonforde2010, ahn2025 |
| 2 | kupiec1994, duffie2011, cont2014, figlewski1984, artzner1999, derivev2core, qin2021, soska2021, derivegetmargin |
| 3 | albiez2026, cameron2008, mackinnon2017, roodman2019 |
| Back matter | albiez2026, derivegetmargin, derivev2core, burlig2018 |

`albiez2026` is `@unpublished` (working paper, FHNW) without a DOI and lies outside the Crossref check. The
version (19 September 2026, commit `103c676`, last change to `paper/main.tex`) is named by the text in section 3,
not by the bib entry (A18). The inference citations (`cameron2008`, `mackinnon2017`, `roodman2019`) and
`burlig2018` are taken over character for character from `paper/refs.bib` (A61); the earlier "open" item is thus
done.

---

## 6 · Open decisions for the author

1. **JEL codes** as a proposal: G13 (options), G12 (margin-based pricing), G24 (brokers, dealers, market makers),
   D47 (market design). Paper 1 had G13, G14, G12, D47.
2. **Competing interest** is taken over word for word from Paper 1, including the contact with the team about
   order data. Please confirm that this still holds for Paper 2.
3. **Abstract sentence on H4** (`h4-direction`) depends on the sign. On rejection, "did not respond measurably" is
   more honest than a number.
4. **`paper2/main.pdf`** is build output and is now in `.gitignore` (done).
5. **Public anchoring of the pre-registration (A02).** The times of `1d13227` and the four addenda are local git
   times; no commit is on a remote. The manuscript now says so ("All commit times are local times of the author's
   machine …"). Recommendation: first settle A01 (`docs/paper2/HISTORY_CLEANUP.md`), then push the branch and
   integrate it with a merge commit (no squash, no rebase), and in addition stamp the commit hashes with
   OpenTimestamps or upload `PRAEREGISTRIERUNG.md` with its addenda to OSF. Once that is done, give the date of
   publication or the timestamp in the section "Data, code and pre-registration" (date declared via `% src git:`
   or as a constant).
6. **Clean up the history (A01).** If the author follows `docs/paper2/HISTORY_CLEANUP.md`, the hashes of the
   addenda change (test run: `eb534fe` → `1d6b2de`, `9465210` → `3872ed0`, `bfc34c8` → `985ec99`, `c4fcb59` →
   `396e180`; the real run is what counts; `1d13227` and `103c676` stay). Afterwards update in `paper2/main.tex` the
   four hashes in the section "Data, code and pre-registration" and the declaration `% src git:c4fcb59`, regenerate
   `docs/paper2/NUMBER_CHECK.md` and adjust section 7.2 of this file.

---

## 7 · Review round 1 (25 September 2026)

All critical and important findings of the referee and the number checker are incorporated, and almost all of the
minor ones. New numbers entered the text only once they were in `results/p2` (number rule). Check chain green
afterwards: `p2_number_check` (0 unsupported), `p2_wordcount` (all sections within budget, abstract 200/200),
`p2_build` (build clean), `p2_figure_check` (all checks yes).

### 7.1 New quantities and where they are produced

All exploratory or descriptive; no registered verdict and no registered number changes.

| Quantity | Code | Stored in | Value (pilot) |
|---|---|---|---|
| ρ from the sign pattern alone (ranks shuffled within the sign groups, 4,000 draws, seed 20260924) | `inference_p2.sign_floor` | `sensitivity.json` → `h1_sign.sign_floor`; `summary.json` `h1_sign_floor_*` | mean 0.734, P5 0.700, P95 0.770 |
| ρ within groups (day bootstrap of H1, groups by sign choose their cells anew in every replicate; A04) | `inference_p2.h1_sign` | `h1_sign.within_{pos,nonpos,sell,buy,pos_sell,pos_buy}` | edge > 0: 0.634; sells 0.990; buys 0.721; profitable buys 0.243 |
| overlap of the best cells | `inference_p2.top_overlap` | `h1_sign.top_overlap`; `h1_top10_overlap`, `h1_top20_overlap` | 1 of 10, 5 of 20 |
| H2 and H3 per parameter regime R1 to R4 (bounds as in `figs_p2.f1.REGIME_BOUNDS`, tested) | `inference_p2.h2_regime_rows`, `h3_review_rows` | `sens_h2.csv`, `sens_h3.csv` (`group = regime=…`); `sensitivity.json` `d_h2.by_regime`, `e_h3.by_regime` | H2 0.0117 to 0.0899; H3 4.44 to 6.00 |
| H3 by the account's manager | `inference_p2.h3_review_rows` | `group = account_manager=SM/PM/PM2`; `e_h3.by_account_manager` | SM 1.076; legacy 5.457; PM2 5.161 |
| H3 at most 63 options without the SM account | ditto | `e_h3.sm_pm2_le63_no_sm` | 3.780 [3.635, 3.980], n = 184 |
| H2 population before the draw, draw checked against `marginal.parquet` | `inference_p2.h2_population` | `d_h2.population`; `h2_population` | 100,995, draw identical |
| H4 level and reading aid (ln 0.9 times β and the interval bounds) | `inference_p2_h4.review_extras` | `sensitivity_h4.json` → `review.readings`; `h4_review_*` | half spread on average 7.93 bp (median 3.34); −1.75 to +2.74 bp |
| H4 sell cells only or buy cells only, dose weighted by the OI share of the changed manager | ditto | `review.sells_only`, `buys_only`, `oi_weighted` | −3.81 (p 0.58); 128 (p 0.13); −5.13 (p 0.59); OI share 54.5 to 94.9 % |
| API against chain semantics, 195 single contracts | `p2_numbers.review_section` from `api_snapshot.csv` | `api_*` | PM2 median 0.08 %, p95 0.50 %, max 2.4 % (> 90 d) |
| further counts | ditto | `fills_outside_every_window` (6), `h3_accounts_{sm,pm,pm2}` (1/4/4), `h3_accounts_median_above_threshold` (8 of 9), `h3_days_over_validated_legs` (127, up to 317 legs), `validation_single_blocks_per_cell` (100), `semantics_box_expiries` (14), `event_*_refbook_log_change` | |

CLI: `python3 -m derive_surface p2 infer extras` and `python3 -m derive_surface.inference_p2_h4 extras` write only
these entries into the existing files; `infer sensitivity` and `inference_p2_h4 run` produce them with the next
full run. Then `scripts/p2_numbers.py`. Tests in `tests/test_p2_inference.py` and
`tests/test_p2_inference_h4.py`.

### 7.2 Changes to the check chain, figures and cards

- `p2_number_check.py`: declarations in the abstract apply only to the abstract (so "two are rejected" no longer
  binds every "two" of the text to `derived:n_rejected`); dates and times of day can be declared
  (`% src file:key <date>`, `const:`, `git:<sha>` for the author date of a commit). With this, "25 September 2026"
  (addenda) goes to `git:c4fcb59`, the date of the API probe to `api_day`, "08:00" to `fig_t1_meta.csv`,
  "fourteen" to `semantics_box_expiries`, "−0.105" to `h4_review_ten_pct_dose`.
- `p2_figure_check.py`: new check `CAPTION_ELEMENTS`. If a caption names a band or a group of rows (F2 "grey band",
  F3/F4 "per/by parameter regime", "by the manager of the account", "by book size", "on the same BTC and ETH legs"),
  the figure table must contain these rows.
- Captions in the modules (F1 "four regimes" with the three boundary dates; F2 "edge per unit of premium"; F3 title
  "A fill in a dominant maker's book"; F4 limit of 63 options as a probe of September 2026, row "SM / PM2 same
  legs" explained). F2 row title "edge per premium" instead of "return on premium", F3 band "full" instead of
  "dearer"; F2 and F3 rebuilt. `docs/paper2/FIGURE_SELECTION.md` stays unchanged as the historical build
  instruction.
- Social cards: s1 "a fill costs … per contract" instead of "the next contract"; s3 no longer "the map … stays the
  same" but the sign pattern (0.90) and the profitable cells (0.63); the footer names the pre-registration
  `1d13227` instead of `c4fcb59`.

### 7.3 Proposals rejected or only partly adopted

1. **Referee, minor (H1 interval below the estimate):** the proposed half-sentence "the interval sits below the
   estimate because thin cells are noisier in resampled days" is not adopted, because the mechanism is not
   established. **Correction after the audit (A28):** the reason first given here was wrong. The bootstrap
   distribution of the registered ρ lies below the estimate (mean of the draws 0.8946, median 0.8950, only 15.2 %
   of the draws at or above 0.9029); in the registered test the noise pulls ρ down, not up. The group intervals
   lying above the estimate (edge ≤ 0: 0.636 at [0.674, 0.830]) did not come from "few, thinly populated cells" but
   from choosing the groups by the sign of the estimated edge with fixed cells (A04); with a new choice per
   replicate they are [0.460, 0.684]. The manuscript now gives the recomputed intervals (0.634 [0.572, 0.702],
   0.243 [0.207, 0.446]) and states in appendix B that the percentile interval is not centred (bias-corrected
   0.898 to 0.920); the verdict stands.
2. **Referee, minor (cite cameron2008, mackinnon2017, roodman2019):** adopted after the audit (A61); the entries are
   now in `paper2/refs.bib`.
3. **Referee, important (splitting large books over SM subaccounts by expiry):** the second sentence of the
   proposal is not checked and therefore appears only as an open limit in 4.3 ("is not examined"), as the referee
   intended for this case.
4. **Referee, important (split H2 exploratively into opening and closing fills):** not computed.
   `marginal.parquet` does not contain the position in the instrument before the fill; it would have to be
   collected anew from the snapshot and `BalanceAdjusted` per fill (a run in `books.py`). Adopted is the minimal
   version as a sentence without a number: the median mixes fills that offset the book's risk with fills that
   raise it. "Many fills that release capital close existing positions" is not established without this
   measurement and is not in the text.
5. **Referee, important (compute K exploratively for option plus perp delta):** not computed; the gap between the
   hedged net edge and the capital of the unhedged contract is stated in section 3 and among the limits.
6. **Referee, minor (share of maker-days with non-USDC collateral):** not computed; `maker_days.parquet` does not
   record collateral. After the audit (A44) the text says without a number that most maker-days hold such
   collateral (counted from `snapshots.parquet`: 1,241 of 1,943) and that one PM2 account holds ETH that its lib
   counts as risk-reducing. A number in the text needs a key in `results/p2` (open, 8.3).
7. **Referee, critical (H4 in the abstract "modest narrowing"):** "modest" is not adopted. After the audit (A05),
   "a narrowing by a fifth is not excluded" is replaced: the descriptive range (−1.75 to +2.74 bp) is conditional on
   the event dates; calibrated at the placebo t it runs from −3.13 to +4.39 bp, that is up to 39 % of the mean half
   spread. The abstract still says only "no evidence".
8. **Referee, critical (abstract wording of H3 with 73.6 %):** shortened to "mostly books no standard-margin
   account could hold", because the abstract has a hard limit of 200 words; 73.6 % is given in the introduction
   and in 4.3.
9. **Referee, minor (coherence: PM2 only practically convex):** because of the budget of section 2 (660/660) only
   the first part is adopted: the sentence attributes coherence only to the worst-loss core of the scenario margin
   and not to the whole rule with contingencies and static discount; Figlewski now stands for probability-based
   margin, not for scenario engines.
10. **Number checker, minor (declarations for all counting words):** done after the audit (A19 to A21, A33). There
    are no generic matches any more; every counting word is declared, as a value (`fig_f1_regimes.csv:regime~distinct
    four`, `fig_t2_b.csv:row~count four`, `summary.json:validation_single_blocks_per_cell 100`), as a constant
    (`const:addenda Four`) or as a text number (`text:reading_aid_pct ten`).
11. **Referee, important (extend the paragraph on limits with "dose is stand-alone …"):** placed in 4.4
    (identification paragraph) instead of the discussion, because the discussion is at its budget; the discussion
    names the other limits.

### 7.4 Notes for the next run

- After the final data run: `infer sensitivity`, `inference_p2_h4 run` (both via `scripts/p2_heavy.py`),
  `p2_numbers.py`, figures, `p2_number_check`, `p2_wordcount`, `p2_build`, `p2_figure_check`. Since the audit the
  build really stops when a declared number no longer matches its source, when a number stands without a
  declaration and when a declaration no longer has an occurrence, each per unit and occurrence. The sentences on H1
  (0.634 [0.572, 0.702], 0.734), H3 (3.780, 8 of 9) and H4 (calibrated range −41.6 to 29.7, −3.13/+4.39 bp, 39 %)
  then have to be read anew, not just their digits swapped. For new sentences,
  `python3 scripts/p2_number_check.py --template` lists per unit the numbers in text order with candidates whose
  content has to be checked.
- The buy-cell estimate of H4 (128, p 0.13) rests on doses near zero and is barely identified; it stands with the
  other exploratory H4 variants in appendix B, so that the sell row does not look selective.

---

## 8 · Audit round (25 September 2026)

Basis: `docs/paper2/AUDIT.md` (69 findings). This section records what changed in the manuscript. No registered
verdict changes; `results/p2/h1.json` to `h4.json` are bit-identical to `d51ede0`. Guard for the corrected
wording: `tests/test_p2_manuscript.py` (withdrawn phrases must not return, required disclosures must stay, floats
before the conclusion, PDF metadata; the test also checks that the audited version `3ec74f4` fails every check).

### 8.1 State of the check chain

`p2_number_check` 0 errors for 352 numbers (17 text numbers), `p2_wordcount` all sections within budget, `p2_build`
"build clean" (12 pages, 0 overfull, no underfull box in running text; the others come from `main.bbl`, a long URL
and DOI), `p2_figure_check` exit 0.

| Section | Words | allowed |
|---|---|---|
| Abstract | 198 | 200 |
| 1 Introduction | 660 | 660 |
| 2 The engine and what it returns | 660 | 660 |
| 3 Data and measurement | 659 | 660 |
| 4 Results | 1,536 | 1,540 |
| 5 Discussion | 438 | 440 |
| 6 Conclusion | 189 | 220 |

To keep the budgets, the post hoc and the registered exploratory detail numbers are now in a new **appendix B
"Post hoc and exploratory results"** (without a budget): sign floor 0.734 with percentiles, ρ among sells and buys,
overlap of the best 10 and 20 cells, H1 interval not centred, exploratory maps (formerly 4.5), H2 per regime, RFQ
packages, non-USDC collateral, H4 per underlying, sells only, buys only, OI-weighted, placebo over all timelines,
placebos with separate windows, median and trimmed dose. The results section keeps the registered numbers, the post
hoc values cited in the abstract, introduction and conclusion (0.634 and 0.243 with interval) and the calibrated H4
range.

Labelling (A03): section 3 sets out "Analyses not named in the registration are exploratory, those added after the
first results post hoc". Post hoc are all quantities that arose only with `48e4032` or later (keys `h1_sign_*`,
`sens_h1_sign_*`, `h1_top*`, `*_by_regime_*`, `*_by_account_manager_*`, `sens_e_h3_sm_pm2_le63_no_sm`,
`h4_review_*`, all audit keys); exploratory are the unregistered quantities computed with the results in `93b42bc`
(H2 per account, H3 up to 63 options, placebo over all timelines) and those the pre-registration names as
exploratory (maps, per underlying, time normalisations).

### 8.2 Changes per finding

| Finding | Change in `paper2/main.tex` |
|---|---|
| A02 | "Data, code and pre-registration": commit times are local times of the author's machine, before the results no commit was on a public server; addenda with "(UTC+2)". Recommendation OpenTimestamps/OSF in section 6, point 5. |
| A03 | Convention in section 3; "post hoc" or "exploratory" at every affected number; abstract "post hoc, much of that correlation is the sign of the edge"; "(H1)" in discussion and conclusion only at the registered finding; detail numbers in appendix B. |
| A04 | 0.634 (0.572 to 0.702) and 0.243 (0.207 to 0.446) in the introduction and 4.1; F2 caption from the module ("cells are chosen again in every replicate"); appendix B explains the choice per replicate. |
| A05 | 4.4 new paragraph "The test has little power": sd(t) 1.82 at 100 placebo dates, calibrated 90 % range −41.6 to 29.7, for 10 % cheaper capital −3.13 to +4.39 bp, a narrowing of up to 39 % not excluded; "by a fifth" deleted; note on exploratory p that are too small (appendix B); discussion "or the test lacks the power to detect a narrowing of that size"; conclusion "no detectable response … in a test of little power"; introduction "the test cannot exclude a sizeable narrowing". |
| A06 | Placebo rule "at least 28 days from every change of the underlying's legacy-manager and standard PM2 parameters (Addendum 4)"; variant over all timelines (P95 21.57, 88 %) as a further reading of addendum 4 in appendix B. |
| A07 | "every test runs inside it" replaced by "only H4 also uses events before it"; 4.4 names the legacy events of 22 February 2025 (BTC, ETH) with 75 of the 475 pairs (`events.csv:panel_cells@manager=pm,kept=True~sum`). |
| A08 | Abstract and introduction: H3 factor "on the opening books of nine dominant subaccounts", detached from the H2 sentence; "no standard-margin account could hold" replaced by "too large for a standard-margin account". |
| A09 | "subaccount" instead of "maker" where subaccounts are meant; section 3 names the wallets ("Some share a wallet: M3 and M5, M4 and M10, and M2, the one SM subaccount, with M1, M6 and M8", recomputed with `data/p2/audit/inhalt/wallets.py`); 4.3 and discussion: M2 holds small books, the large books of its wallet sit under portfolio margin; the split over subaccounts as observed practice. |
| A10 | Introduction and 4.2: "maker buys there mostly release capital and maker sells mostly bind it" (without a number, see 8.3); discussion and conclusion restricted to "the median fill". |
| A11 | The first point of the discussion holds "from an empty or small book"; in the dominant PM2 books the marginal capital orders the sides differently. |
| A12 | 4.1: edge of the top capital cells close to the gap between fill price and SVI mark in the extrapolated wing, mostly RFQ legs (post hoc); the discussion names this limit. |
| A13 | 4.1 "a maker buy binds about its premium out of the money and less in the money"; "where a long option binds about its premium" only for far out of the money; captions F1 and F2 from the modules. |
| A14 | Abstract "the margin rules are public contracts with parameters on chain, and the venue's off-chain engine can be queried for any book"; section 2 "The managers' contracts are public \citep{derivev2core} … BitMEX instead margins each position at a percentage of its notional \citep{soska2021}"; conclusion "The rules that set it are public contracts". Title unchanged (the abstract carries the qualification). |
| A15, A16, A17, A60, A61 | Sentences of the literature agent adopted (penalise/bound, fournier2020, chen2019, ahn2025, derivev2core, derivegetmargin, cameron2008, mackinnon2017, roodman2019, burlig2018, "The question extends", cells "a maker side and the absolute delta and tenor buckets of"). |
| A18 | Section 3: version of 19 September 2026 (`% src git:103c676`), both unit errors (fee and rebate per fill; map per notional over the notional of the whole fill), the affected items are net edge numbers, the cell count of the fourth hypothesis and the map per notional, correction announced, values per notional therefore differ. |
| A28 | Appendix B: 15 % of the draws at or above the estimate, bias-corrected 0.898 to 0.920; 7.3 no. 1 corrected. |
| A29, A30 | Appendix B: one event more in the placebo panels (HYPE of 8 January 2026), overlapping ETH windows of 10 days, placebos with separate windows (P95 26.02, 48 %, sd(t) 1.77); median dose −4.52, trimmed −4.08. |
| A34 | Reference book "a short straddle at the forward of each underlying (BTC in panel c)"; "11 of the 14 kept events" (`fig_f5_b.csv:jump_logpct@…~count`), range 3.4 to 37.4 over the underlyings and 7.8 to 26.0 for BTC with row binding. |
| A35 | 4.1 "on the 6 and 18 sell cells that still reach 200 fills"; the discussion sentence on pooled against after 20 August is deleted. |
| A36 | "books of 32 to 63 legs, M2 included, give 3.43". |
| A37 | Addenda 1 to 3 "committed before the step they govern"; addendum 4 "written after capital per fill, marginal costs, netting ratios, the doses and the H4 panel with its half spreads had been computed; it records readings already implemented, but precedes any test statistic". |
| A38 | 4.2: addendum 4 chose ratio instead of the "next single contract", which the registered wording also covers, when both were available per fill, before any median. |
| A39 | 4.5: both MM variants (0.0291 account lib, 0.0278 standard lib) and "this variant was set to one library per ratio after the first results"; the first mixed value (0.0190) is not in `results/p2` and is therefore not in the text (8.3). |
| A40 | "before the first capital figure of the registered form, with zero cash"; stage A fixtures previously read on-chain margins of single maker accounts with cash; probes before the registration named one by one, including the SM map of the BTC cells (from which ρ for SM could already be read) and margin histories, "which the registration does not list". |
| A41 | Section 3: opening book "priced at the companion paper's mark". |
| A42 | Appendix A: H2 values books above the largest validated book, no validation case in the settlement window. |
| A43 | Section 2: "whole books were only probed at random, with larger gaps". |
| A44 | Discussion "Collateral other than USDC, held on most maker-days"; appendix B on the risk-reducing ETH of a PM2 account. |
| A45 | Appendix B: each leg of an RFQ package against the book before the whole package, without the other legs. |
| A46 | "last pushed up to and including its block". |
| A47, A50, A51, A53 | Captions A1, F3, F5, T2 taken over from the modules of the figure agent (with declarations 17, 180, 5). |
| A49 | Reference to F5 in section 3 deleted; F3 and F4 before 4.2, F5 and F6 before 4.4 in the source; `\FloatBarrier` (package `placeins`) before the conclusion, so that the discussion runs beside the H4 figures and no figure slips behind the conclusion; A1 in the appendix. Result: 12 pages, all result figures before "6. Conclusion", A1 after the start of the appendix. |
| A55 | "legacy portfolio manager (legacy PM)" in the introduction; M1 to M10 "by rank" in section 3; R1 to R4 in appendix B with reference to the boundary dates of F1. |
| A56 | `\mathit{NE}`; H4 regression as a numbered equation with "post_i marking fills after the event"; event capital as $K^{e+}/K^{e-}$. |
| A57 | Author, subject, keywords and creator set after `\maketitle`; bookmarks for the back matter and the bibliography (`\phantomsection\addcontentsline`). |
| A58 | Footer with the fixed date "25 September 2026" instead of `\today`; addenda with "(UTC+2)". |
| A59 | Paragraph of the contributions reworded (no underfull box in running text any more). |
| A64 | "The pre-registration is written in German, and its addenda are headed Nachtrag; an English translation made after the analysis is in docs/paper2/PREREGISTRATION.md, and the German original is binding." |

### 8.3 Open for the author or other areas

- **Numbers without a key in `results/p2`** (number rule, hence in the text without a number): wallets (four PM2
  subaccounts of three operators, nine H3 subaccounts of four wallets; A09), H2 by maker side (median sells 0.075,
  buys −0.137; ratio of the sums 0.166; A10), book gap API against chain (A43), share of maker-days with non-USDC
  collateral (1,241 of 1,943) and the effect on M8 (A44), largest H2 book (321 legs), HYPE share and settlement
  window (A42), pooled median on the same R4 cells (1.031 and 0.991; A35), first mixed MM variant 0.0190 (A39),
  edge share of the RFQ legs in the top cells (A12). Whoever wants them in the text creates keys in `summary.json`
  (foundations area) and declares them via `% src`.
- **Captions that can only be changed in the module** (otherwise `caption_drift` stops the build): F4 "standard
  margin account" instead of "standard-margin account" (A59, `derive_surface/figs_p2/f4.py`); F5 "the reference
  straddle" should read "the reference straddle of the underlying" (A34); F1 could say that R4 contains only cells
  with 200 fills after 20 August (A35); F2 label "net edge, Paper 1" (A55).
- **A67** (maker fee on one leg for multi-leg RFQs, addendum 2): numerically negligible, not mentioned in the
  manuscript, because the number (0.001 USDC per contract) is only in `results/p1_finding`.
- **A02 and A01** see section 6, points 5 and 6.
