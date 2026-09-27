# Figures for Paper 2: selection and build instructions

2026-09-25. Three independent draft sets of nine slots each (lenses: mechanism, empirics, practitioner; under
`docs/paper2/drafts/`, prototypes under `data/p2/fig_proto/`), then two judges with different lenses: a
referee who recomputed the claims against the data (`jury_referee.md`), and a design review that measured width and
smallest font after placement and looked at every prototype in greyscale (`jury_design.md`,
measurement `data/p2/fig_proto/jury/audit_protos.csv`). This file settles every point of dispute and is the
**binding specification for building** `derive_surface/figures_p2.py`, `figdata_p2.py`, `scripts/p2_figure_check.py`,
the social cards and the GIF. Where a draft or a judge says otherwise, this file applies.

Abbreviations: M = mechanism, E = empirics, P = practitioner. Numbers are recomputed on the pilot cut of 2026-09-17.

**Blind to results.** The selection was made without knowing the verdicts on H1 to H4. From `h1.json` to `h4.json`,
`sens_*.csv`, `sensitivity*.json` and `fig_h*.csv` the synthesis read only schema, keys and structural numbers
(n, days, accounts, cells, admissible placebo days, rule texts), never `stat, lo, hi, rejected, p` or the
criteria. Disclosure: while the bin structure of `fig_h2_dist.csv` was being checked, the counts of the two open
edge classes of the registered variant became visible; no decision depends on them, and the window [−1; 2] had been fixed
beforehand by the bins of the inference. The referee knew the sign of the H4 estimate (unmasked fields `se`,
`t`, `fe.beta_direct_solve`); the choice for F6 holds for either sign. No title, no axis and no
label depends on the outcome of a test.

---

## 1 · The selection in one table

| Slot | Question | Source | Size (in) | Test |
|---|---|---|---|---|
| T1 | What capital does a short bind at each point of the surface, and which rule sets it? | P-T1 a/b ⊕ M-T1 c/d | 7.0 × 4.2 | |
| T2 | What does `get_margin` return, and how does PM2 value a book? | P-T2 a/b ⊕ M-T2 c (redone on the reference straddle) | 7.0 × 2.6 | |
| F1 | What does one contract cost per cell, and what do the same fills cost under SM and legacy PM? | P-F1 with the numbers of E and the referee's regime split | 7.0 × 3.9 | |
| F2 | Does the capital denominator reorder the map? | P-F2 (maps, rank against rank) in the grey coding of the design review, verdict bar from E, sign lines from the referee | 7.0 × 4.4 | H1 |
| F3 | What does the next contract cost in the book of a dominant maker? | P-F3 a ⊕ E-F3 b | 3.4 × 4.0 | H2 |
| F4 | What is netting worth? | P-F4 b binned ⊕ E-F4 b | 3.4 × 4.0 | H3 |
| F5 | How has the engine moved over time, and which events carry H4? | P-F5 ⊕ status grammar E ⊕ placebo band of the referee | 7.0 × 4.3 | |
| F6 | Does the half spread follow the price of capital? | The referee's combination: dose strip, FWL picture E, placebo with checklist E, small forest | 7.0 × 4.2 | H4 |
| A1 | Does the replica match the chain? | M-A1 a ⊕ P-A1 b, p95 mark from E | 7.0 × 2.5 | |
| GIF | How does the PM2 capital surface move over 15 months? | 3D as in T1 (M, P), timing and hold frames M, honesty rules E | 1200 × 675 px | |
| Card 1 | One straddle, three engines | M card ⊕ steps from P | 1600 × 900 px | |
| Card 2 | Why netting works | P card 2 with a new title, both bars from the same straddle | 1600 × 900 px | |
| Card 3 | Four registered verdicts | Verdict card in the grammar of E | 1600 × 900 px | H1 to H4 |

Nine figures in the PDF: T1, T2, F1 to F6 in the main text, A1 in the appendix. The only 3D figure is T1. F3 and F4 stay
single-column `figure` environments with identical grids, so that they stand side by side at the top of a page; the shared
`figure*` from E would waste a slot.

---

## 2 · Where the judges agreed

| Slot | Both | Why |
|---|---|---|
| T1 | 3D pairs PM2 and SM on a common `cividis` scale, below them the 2D maps “binding rule” from M | The surface alone does not say why it looks the way it does; a floor projection inside the 3D axes fails on the depth sorting of mplot3d (M tried it). |
| T2 | P a (linear bars R and −V) and P b (dumbbells), plus M c, recomputed on the reference straddle | E a is a dot plot on log USDC, where the distance between markers is not V. M c is the only place where one sees the engine value a book. |
| F3 | ECDF from P, forest with verdict bar from E | The ECDF reads the median directly at 0.5 and fits the bins of `fig_h2_dist.csv` ([−1; 2] with open edges); the histogram of E needs [−2; 3], which the table does not have. |
| F5 | P as the carrier, status grammar from E, fix the error in the HYPE strip, M d dropped | P carries the numbers, E makes the H4 selection checkable; M d shows the same numbers a second time. |
| A1 | Strips per underlying × manager with median and n, plus error against book width (P b) | Contains all registered quantities and shows that the error does not grow with the size of the book. |
| Verdict grammar | E for F2, F3, F4, F6 | Four tests, one way of reading them; the verdict line is rebuilt from the rule and must match `rejected`. |
| Measurement | `FS_MIN = 7.0`, width test, no `bbox tight` | The overruns of the prototypes (drawn up to 8.5 inches wide, 5.7 pt when typeset) come from legend columns and long row labels. |
| GIF | 3D surface PM2 only, weekly with hold frames at events, time strip, honesty rules from E | E's 2D proposal for X is rejected: the moving surface is the image by which T1 is recognised. |
| Card 1 | M card “One short BTC straddle. Three margin engines.” | The three large numbers are the strongest single statement of all the cards and need no hypothesis. |

---

## 3 · Where they diverged, and how it was decided

**F1: E versus P.** The referee wanted E (BTC maps for three managers × two sides, strips of all 173 cells), because
the specification asks for capital *by manager*. The design review wanted P (PM2 maps for all three underlyings,
manager comparison as strips), because E as drawn is 8.54 inches wide (5.7 pt when typeset) and nine maps force the
comparison through numbers across the whole figure. Decided: **P as the layout, with the content of E and the regime split
of the referee.** The manager comparison is shown per cell as a point in the strip, on all three underlyings, and the numbers in the
maps have two significant digits (E). M's anatomy column is dropped entirely: it shows a contract from the
last parameter regime next to maps that average over four regimes, and T2 c already carries the mechanism.

**F2: maps or no maps.** The referee wanted the map of edge per PM2 capital in the figure, because it is contribution 1 of the
specification. The design review rejected P-F2, because in greyscale the diverging scale turns the same grey at both
ends, orange and blue already belong to the managers, and the buy row breaks any common scale. Decided: **The
maps stay, in the coding of the design review.** Grey by |value| on a logarithmic scale *per row* (the
buy row is a return on the premium and gets a scale of its own), negative cells hatched, the sign always as a
number. The rank-rank picture becomes a single pooled panel without coding of the underlyings; the design review's question whether part
of the reordering is a difference in level between underlyings is answered by the exploratory forest rows “ρ
within BTC/ETH/HYPE” (they are in `sensitivity.json`, `g_by_ccy`). The mean rank shifts of E (c/d)
go into `fig_f2_shift.csv` and into the text. P's five framed “best” cells are dropped, because they were not defined
in advance. Rank intervals only for the ten largest |rank_shift| (design review), not 173 hairlines.

**F4 panel a: histogram or book width.** The referee wanted the histogram of E (stacked ≤ 63 / > 63
options), but allowed book width “if the design review finds a place for it”. The design review found one.
Decided: **K_SM/K_PM2 against option legs as the median per bin with an interquartile band.** The limit of 63 options sits
there as a real position on the axis and not as a colour stack, and the counterfactual range is hatched and labelled with its count. The
distribution as such is carried by the forest (registered row, ≤ 63 and > 63 as rows of their own).

**F6 panel a: dose maps or dose strip.** The design review wanted the three real BTC dose maps of M, because
they show the variation across cells that identifies β. The referee wanted a strip of all 13
panel events, because the maps show 3 of 13 events and their cross follows the pre rule (≥ 20 fills before the
event) instead of the panel rule (20 each before and after). Decided: **strip.** It shows the support of the
estimate in full: median dose over the 475 pairs −0.63 log-%, 11.2 % of the pairs positive (at most
+2.2 log-%), 44.4 % with |dose| < 1 log-%, 48.6 % below −1 log-%. The map of 2026-08-20 stays as a reserve social card. The small
forest panel d of the referee stays, but without the row “without outlier cells”: the only cell above the threshold
(HYPE buy 00-10/2-7d, dose −1.648) is not in the panel (`rows_dropped_real_panel = 0`), so the row would be identical to the
registered one.

**T1 iso-lines.** M and the referee: 5/8/11/14 % on the 2D maps; P and the design review: 4/8/12/14 % on the
3D surface. Decided: **4, 8, 12 and 14 % in all four panels and on the colour bar.** Equal steps up to 12 %,
plus 14 % between the SM floor of 13 % and the maximum of 15 %, so that the bright ridge of the SM surface has a line.

**F5: where the ±14-day windows go.** E and the referee: grey background in panel c. Design review: on the
event rail. Decided: **on the rail**, because c shows BTC only and the windows apply per underlying.

**Unit of the change in capital.** P and the referee write per cent, the design review log-%. Decided: **log-%
(100·Δln K) throughout the paper**, because β is registered in this unit and F5 b, F6 a and F6 b then show the same
number. GIF and cards show simple per cent.

**A1: MM in the books panel.** The referee writes “IM filled, MM hollow” in the selection and “MM only in the
CSV” in the requirements. Decided: **MM only in the CSV**, in both panels.

**Card 2.** Referee: a still of the surface. Design review: P card 2 (straddle against one leg) with a new title. Both
set the same condition on P card 2 (both bars from the same reference straddle, no “almost free”).
Decided: **P card 2 under this condition.** The still becomes the end frame of the GIF and its poster in the README.

**Card 3.** Design review: P card 3 “PM2 discounts the book, not the contract” after H3, otherwise the fingerprint card
of M. Referee: verdict card H1 to H4. Decided: **verdict card.** P card 3 compares a cell median pooled over regimes
with a median over maker-days, that is two populations, and its sentence flips in the last regime (section 4).
The verdict card is designed independently of the outcome. The fingerprint card is the reserve.

**Coding the underlyings.** The referee and E code underlyings by shape or colour. The design review forbids both, because
blue and orange belong to the managers, ETH and HYPE merge in grey, and the diamond is already legacy PM.
Decided: **underlyings only through panel, row or label**, never through colour or marker shape.

**New symbol conflicts that no judge noticed.** M-T2 c codes vol states with ▲/▼, which are reserved for the
side, and draws “legs separately” dotted, that is in the line style of legacy PM. E codes
sensitivity rows with an open diamond and the design review codes “kept without panel cell” with a hollow diamond, both the shape
of legacy PM. Resolved in section 6.2.

---

## 4 · The gap that no draft covered

**All maps and distributions pool over four parameter regimes.** In the PM2 window the PM2 capital of the
BTC reference straddle fell from 14.41 to 10.03 % of the forward, by 35.0 % (−43.1 log-%) through parameters alone.
No draft shows this in F1 to F4. The design review named it as a gap for F1 and F2, and the referee recomputed
that the core statement of E and P on the single contract flips in the last regime. Recomputed here (sell fills,
ratio of sums, cells with at least 200 fills per regime):

| | to 2026-01-23 | 2026-01-23 to 2026-05-24 | 2026-05-24 to 2026-08-20 | from 2026-08-20 |
|---|---|---|---|---|
| Share of sell fills with K_SM < K_PM2 | 82.5 % | 69.2 % | 54.1 % | 15.4 % |
| Median SM/PM2 of the BTC sell cells | 0.91 (20 cells) | 0.91 (19) | 0.97 (19) | 1.40 (6) |
| the same for ETH | 0.88 (31) | 0.88 (24) | 0.93 (27) | 1.14 (18) |
| the same for HYPE | no cell | 0.72 (15) | 1.06 (14) | 1.44 (1) |

Buys are at 1.00 for BTC and ETH in all regimes (SM charges the premium), and at 0.87 to 1.00 for HYPE. Pooled,
“for the single short, PM2 is not cheaper than SM” holds (median 0.94 / 0.90 / 0.88); since 2026-08-20
SM has charged at least as much as PM2 on 84.6 % of the sell fills. H3
also rises mechanically as a result, because the same denominator got cheaper. Three build requirements follow:

1. **A fixed regime grid** (section 6.6) for all splits: R1 to R4, separated by the PM2 events of
   2026-01-23, 2026-05-24 and 2026-08-20.
2. **F1:** hollow symbols for R4 in the strip, and `fig_f1_regimes.csv` with all four regimes.
3. **F3 and F4:** exploratory forest rows R1 to R4 (the inference must write them, section 10). F2 names the
   pooling in its header; whether the ranking of the F1 cells holds across regimes is stated in one sentence of the text, taken from
   `fig_f1_regimes.csv`.

### Gap check

| Requirement | Where covered |
|---|---|
| Specification T1: BTC vol surface in 3D, coloured by PM2 capital per short, SM next to it | T1 a/b |
| Specification T2: net = C + V − R, resolution 11 against 1.2 | T2 a/b |
| Specification F1: capital per contract by manager, buy and sell | F1 (PM2 as a number, SM and legacy PM as a ratio per cell); absolute SM and legacy values in `fig_f1_a.csv` |
| Specification F2: notional against PM2 capital per underlying and side, with rank dispersion | F2 a (map per PM2 capital), b (rank against rank with rank intervals); the notional map is the map of Paper 1, referenced in the caption |
| Specification F3: distribution of ΔK/K_single, share ≤ 0 | F3 a |
| Specification F4: K_SM/K_PM2 over maker-days, legacy PM alongside | F4 a/b; legacy PM as a registered sensitivity row, not as a distribution of its own |
| Specification F5: OI shares, events, reference book | F5 a/b/c |
| Specification F6: dose response and placebo | F6 b/c, plus a (support) and d |
| Every registered test shows estimator, interval, threshold, rule, n and clusters in the figure | F2 c, F3 b, F4 b, F6 c/d |
| Calendar axis | F5, GIF |
| Pooling over parameter regimes | F1 strip (R4 hollow), F3 b and F4 b (R1 to R4), headers of F1 and F2 |
| Structural lower bound of H1 (sign) | F2 b sign lines, F2 c band “sign pattern alone” and rows within each sign |
| K_SM counterfactual on 1,431 of 1,943 maker-days | F4 a hatched range, F4 b rows ≤ 63 and > 63 |
| H2 without BTC, M3 = the only HYPE account | F3 header, row “M3 (HYPE)” |
| Support of H4 (doses almost all ≤ 0, half of them near 0) | F6 a |
| Overlapping H4 windows (6,527 fills in two windows) | F5 b window bars, F6 header, caption |
| Placebo support (ETH PM2 only 10 admissible days) | F5 b placebo band, F6 c row |
| Chain against API semantics (flat 2 %) | captions of T1 and A1 |
| Edge is a flow per fill, capital a stock | caption F2, row “per holding time” in the forest |
| Whoever starts with an empty book pays the price from F1 | caption F3 |
| At most one 3D figure | only T1 (two 3D axes in one figure) |
| Every number as a table | `results/p2/fig_<slot>_<panel>.csv` (section 6.7) |
| Accounts only as rank labels | M1 to M10, never an address or hash in the figure |

Deliberately not in the figures: MM variants except as a forest row, API semantics, the ETH and HYPE surfaces (CSV only), the
accounts one by one in F4 (CSV), the mechanics rows `hedges_worst` from M (they would be a new, unregistered computation).

---

## 5 · What the recomputation corrected in the drafts and the judges

| Claim | Recomputed | Consequence |
|---|---|---|
| The change of 2025-06-12/13 is missing from `events.csv` (P, design review) | `MarginParamsUpdated` on 2025-06-12 at 22:20:01 UTC, before the window starts at 23:00 UTC; not an H4 event (the referee is right) | appears in F5 b only as a grey timeline tick |
| HYPE SM share 12 to 16 % (design review) against 7 to 49 % (referee) | both right: 12 to 16 % from June to September 2026, 7 to 49 % over 12/2025 to 09/2026; `pm` is NaN for HYPE | `fillna(0)` before stacking |
| “−V is the same for both managers” (P) | −496,914 (SM) against −496,859 (PM2) | each row draws its own V |
| Straddle 9.7 / 23.5 / 29.0 % (M T2 c) | a different object (grid node Δ 0.50, 30.4 d); reference straddle on 2026-09-17: PM2 10.03, legacy 19.68, SM 29.61 % | T2 c, F5 c and card 1 read the same row of `reference_book.csv` |
| Title for 2026-08-20 “grid ±17 → ±14 %” (M) | a bundle of scenarios, vol shocks, contingencies, basis, collateral; grid ±18 % until 2026-05-24, ±17 % until 2026-08-20, ±14 % since | label “bundle incl. spot grid ±17 % → ±14 %” |
| Jump “on the day after the event” (M) | only for events after 08:00 UTC (2025-02-22, 2026-01-08, 2026-05-08, 2026-08-20); 23 Jan and 24 May jump on the same day | label always carries the event date |
| “two reverts” (M, E) | one case (HYPE PM2, single contract), two rows (IM, MM) | caption A1 |
| “six orders of magnitude below the threshold” (M) | medians 5 to 6 decades below 0.1 %; largest single IM value 8.88e−8, that is 5.05 decades below 1 % and 4.05 below 0.1 % | no decade count in the figure, the points show it |
| H3 “10 subaccounts” (E) | 9 accounts with maker-days (M9 has none) | header F4 |
| H4 “91,446 fills” (E, P) | 91,446 panel rows from 84,919 fills; 6,527 counted twice (BTC 1,457, ETH 2,861, HYPE 2,209) | header F6 |
| ≤ 63 and > 63 options as a registered sensitivity (E) | Addendum 4, item 2, names only legacy PM on BTC and ETH legs as a sensitivity; the share is reported, not tested | rows ≤ 63 / > 63 are exploratory (grey) |
| “the OLS slope of the bins gives β” (referee) | does not hold exactly for binned means | check on the slope of the full residuals (section 11) |
| F4 bins by powers of two | [1; 2) has 19 maker-days | first bin [1; 4) with 41 |
| “without outlier cells” as a β row of its own (referee, E) | 0 panel rows affected, β identical | only the placebo part, in the CSV and the text |
| H2 account M5 with 5,958 fills (P) | 5,957 after excluding one fill with K_single ≤ 0 | row M5 |

Confirmed (a selection): all numbers in table 3 of the referee, plus T1 (PM2 3.42 to 13.70 %, SM 12.37 to 15.01 % of the
forward, SM cheaper at 9 of 740 nodes), the four factor pairs from `factors.csv`, the F1 spans, the H1 sign structure
(74 of 173 cells with edge ≤ 0, capital denominator positive in all 173 cells, sign(A) = sign(B) everywhere), the
parameter jumps (BTC PM2 +1.60 / −10.49 / −7.84 / −26.05 log-%).

---

## 6 · Rules for all figures

### 6.1 Format and measurement

- Widths 3.4 and 7.0 inches, typeset 1:1 with `\includegraphics[width=\linewidth]`. `figures_p2.py` sets for its
  figures `savefig.bbox = None` and `savefig.pad_inches = 0`; the canvas is the print size. Legends sit inside the
  panel or are replaced by direct labels, with no legend column to the right of the axes.
- `figstyle` gets `FS_MIN = 7.0`. No text below 7 pt, panel letters 8 pt bold, tick labels black (not
  `GREY`). Do not take over the code of `figures_p1.py` that sets 6.0 and 6.5 pt.
- Test per figure function (pattern `data/p2/fig_proto/jury/audit_protos.py`): saved PDF width = target ± 0.02
  inches, `get_tightbbox` of every drawing area and every text inside the canvas, no visible text instance below
  `FS_MIN`, exactly one figure with `Axes3D` (T1).
- Output `paper2/figures/{t1,t2,f1,…,a1}.pdf` and `.png`.

### 6.2 Coding

- **Manager** (colour belongs to the managers and to nothing else): PM2 `#0072B2`, solid, circle; SM `#D55E00`,
  dashed, square; legacy PM `#009E73`, dotted, diamond. In the figures it is called “legacy PM”. Constants
  `figstyle.MANAGER = {"pm2": (color, "-", "o"), "sm": (…, "--", "s"), "pm": (…, ":", "D")}`; `p2surface.MANAGER_*`
  reads from them. The dash-dot line style `(0, (3, 1, 1, 1))` is free and is used only for “PM2, legs one by one” in
  T2 c.
- **Side:** maker sell ▼ filled, maker buy ▲ hollow, always “maker sells (short)” or “maker buys (long)”. In
  maps the sell side is on top. ▲ and ▼ mean nothing else anywhere.
- **Underlying:** only panel, row or column titles. No colour, no marker shape.
- **Statistics** (estimator, ECDF, histogram, β line, forest) in black or grey.
- **Event status (F5):** shape = manager; filled = in the H4 panel; left half filled (`fillstyle="left"`) = kept
  without a panel cell (only HYPE PM2 on 2026-01-08); hollow = dropped (dose below 1 %).
- **Forest rows:** registered = filled black circle, interval 2 pt black, label bold; registered
  sensitivity (named as a sensitivity in the pre-registration or an addendum) = open black circle, interval 1 pt;
  exploratory = open grey circle (`#666666`), interval 1 pt grey, row on a light grey band `#F0F0F0`.
- **Greyscale test:** in the test every figure is also saved converted to luminance
  (`paper2/figures/gray/`) and inspected by hand before it goes into the manuscript.

### 6.3 Units, one per quantity

| Quantity | Unit in the figure |
|---|---|
| Capital from fills (F1) | “% of notional” (notional = quantity × index) |
| Capital on the grid and in the reference book (T1, T2 c, F5 c) | “% of forward” |
| Change in capital (dose, parameter jump) | “log-%” = 100·Δln K; GIF and cards: simple per cent |
| Edge per capital (F2) | “bp of capital”, per fill |
| Half spread (F6) | “bp of index” |
| Amounts of a book | USDC only in T2 a and in the CSV files |
| Ratios (F1 strip, F4, T2 b) | logarithmic axis |

### 6.4 Maps

- One number per cell, sequential grey by log value (`Greys` in the range 0.08 to 0.72), font colour white when the
  luminance of the cell is below 0.45. Cells under 200 fills: empty cross “×” 7 pt `#666666` without fill.
- No diverging colour maps. Signed maps: grey by |value|, negative cells additionally with
  hatching `////` in `#666666`, the sign always as a number.
- Cell grid: 7 |Δ| buckets (0–10, 10–25, 25–40, 40–60, 60–75, 75–90, 90–100, top to bottom) × 5 tenors
  (≤2, 2–7, 7–30, 30–90, >90 days, left to right). Axis titles “|delta| of the traded option, %” and “tenor, days”.

### 6.5 Verdict grammar

One function `figures_p2.ruler(ax, rows, h, *, side)` builds the forests of F2 c, F3 b, F4 b and F6 d.

- Bold header above the panel: `registered: {stat} [{lo}, {hi}] → rejected` or `→ not rejected`. The function re-applies
  the rule from `h["rule"]` with `h["threshold"]` to `lo`/`hi` and aborts if the result differs from
  `h["rejected"]`. H4 has its own checklist (F6 c) with the same abort rule over `criteria`.
- Threshold dashed black 0.8 pt. The rejection region is hatched (`////`, `#BBBBBB`), **only** at the height of the
  registered row: H1 and H2 to the right of the threshold, H3 to the left of it, H4 at β ≤ 0.
- To the right of each row its n (cells, fills, maker-days or clusters, depending on the test) in 7 pt grey.
- Row labels at most 18 characters. Intervals that run off the axis end in an arrow.
- Below the header a line with sample and clusters (set per slot below).

### 6.6 Regime grid

R1 until 2026-01-23 04:24:05 UTC, R2 until 2026-05-24 04:05:07 UTC, R3 until 2026-08-20 22:09:25 UTC, R4 thereafter. The boundaries are
the PM2 events that change the reference book in BTC and ETH by at least 3 log-% (BTC −10.5 / −7.8 / −26.0,
ETH −4.9 / −3.4 / −18.3). Assignment by the timestamp of the object: fills by `ts`, maker-days by the book time
00:00 UTC of the day. Labels “R1 to 23 Jan”, “R2 to 24 May”, “R3 to 20 Aug”, “R4 since 20 Aug”. Everything that splits by
regime is exploratory.

### 6.7 Tables

- One CSV file per panel: `results/p2/fig_<slot>_<panel>.csv` (lower case; panels with identical data may
  share a file, e.g. `fig_t1_ab.csv`). Every number printed in the figure is there at full precision, plus the column
  `printed` with the printed text.
- The inference files (`h1_cells.csv`, `fig_edge_maps.csv`, `fig_h2_dist.csv`, `fig_h3_series.csv`,
  `fig_h4_events.csv`, `h4_placebo.csv`) are inputs. The figure layer recomputes no test statistic; allowed
  are sorting, counting, binning and quantiles of descriptive columns.

### 6.8 Captions

English, no dashes as punctuation, every result-dependent number as `\PH{key}` (list in section 12). Captions say
what is drawn and how to read it, not what comes out.

---

## 7 · Build instructions per slot

### T1 · The engine's view of the surface · 7.0 × 4.2 in

**Why:** P carries the value on the surface (iso-lines, headline number), M explains it (binding rule). Only M shows that
almost everywhere a scenario sets the PM2 capital; this later supports F6, because the cut in tail weights on 2026-01-23
hits exactly the cells in which the dampened tail scenarios bind. Templates: `data/p2/fig_proto/praktiker/t1_praktiker.png`
(a/b), `data/p2/fig_proto/mechanismus/t1_proto.png` (c/d).

**Data.** `p2surface.capital_grid("BTC", ts=1789632000, manager, side="short")` for `manager ∈ {"pm2", "sm"}` at the block of
2026-09-17 08:00:00 UTC (last pilot day, no parameter event within ±1 day, 28 days after 2026-08-20). Grid: 37
call deltas 0.05 to 0.95 in steps of 0.025, 20 tenors `geomspace(1, 365, 20)` days; identical to
`data/p2/surface/probe_BTC_2026-09-17_grid.csv`. Parameters `Timeline("BTC", m).at(ts)`. Listed expiries
`p2surface.live_expiries` (15).

**Computation.** K_pct = `K_per_forward_bp` / 100. Binding rule per node via `figdata_p2.binding_rule(grid, ccy, ts,
manager)` (template `_pm2_binding`, `_sm_branch` in `proto_mechanismus.py`): PM2 = index of the worst scenario
from `margin_pm2` with (spotShock, volShock, dampeningFactor), mapped to the classes “spot +14 %, vol up”, “spot
−14 %, vol up”, “core, other vol” (core, dampening 1, any other vol state), “spot ×{s} (dampened)” for s > 1,
“spot ×{s} (dampened)” for s < 1, “basis/skew/other”; the grid width ±14 % is read from the parameters and not fixed
in the code. SM = branch of `OptionMarginParams`: “15 % − OTM”, “13 % floor”, “put: 1.05 × MM”. Test: the decomposition
adds up to the grid capital at each of the 1,480 nodes (relative ≤ 1e−9), and every class is covered.

**Layout.** Header, below it row 1 with a (PM2) and b (SM) in 3D and the colour bar on the right (width 0.10 in),
row 2 with c (PM2) and d (SM) as 2D maps directly below a and b, and below that a legend row for c and d.

- **a, b:** `plot_surface`, x = call delta, y = log10(days), z = IV in %; surface colour `cividis` with
  `Normalize(3.0, 15.5)` on K_pct, shared by both panels. View elev 24, azim −128 in both, shared z range.
  Iso-lines at 4, 8, 12, 14 %: `contour` on the (delta, log days) grid of K_pct, lifted onto the surface (z = IV
  interpolated bilinearly), black 0.7 pt, one label “8 %” 7 pt per line. Axes: x “call delta (put = Δ − 1)” with ticks 0.1 /
  0.5 / 0.9; y “days to expiry” with ticks 1, 7, 30, 90, 365; z “implied vol, %”.
  Titles: “a  PM2: ATM 30 d short = 11.8 % of forward”, “b  SM: ATM 30 d short = 14.1 % of forward” (node Δ 0.50,
  30.44 days; one decimal, read from the grid).
- **Colour bar:** label “capital per short contract, % of forward”, ticks 4, 6, 8, 10, 12, 14; the four
  iso levels as black cross strokes over the full width of the bar.
- **c, d:** `pcolormesh` of the classes; fixed fills: “spot +14 %, vol up” `#E0E0E0`; “spot −14 %, vol up” `#A8A8A8`;
  “core, other vol” `#C8C8C8` with `--`; tail upward white with `..`; tail downward white with `\\\\`; “basis/skew/other”
  white with `xx`; SM “15 % − OTM” white, “13 % floor” `#E0E0E0` with `///`, “put: 1.05 × MM” white with `..`. Only
  classes that occur go into the legend, all classes with their node count into the CSV. x 0.05 to 0.95 with ticks at 0.10, 0.25,
  0.40, 0.60, 0.75, 0.90; y log 1 to 365 days with ticks 1, 2, 7, 30, 90, 365. Grid lines **only** at the ticks 0.10 …
  0.90 and 2, 7, 30, 90 (0.4 pt, `#808080`): these are the bucket edges of Paper 1. Iso-lines as in a/b, in 2D, with
  inline labels. The 15 listed expiries as short ticks (0.06 in, pointing inward) on the right axis of c
  and d. Node ATM 30 d as a black dot 3 pt with a white edge and the label “ATM 30 d” in c and d. Titles “c
  binding PM2 scenario”, “d  binding SM rule”. x label “call delta (put = Δ − 1)”, y label “days to expiry” only in c.
- **Header** (7 pt, top left): “BTC · 17 Sep 2026, 08:00 UTC · 15 live expiries · PM2 spot grid ±14 % since 20 Aug
  2026 · chain semantics”.

**Tables.** `fig_t1_ab.csv` (manager, delta, tenor_days, iv, strike, forward, K_usdc, K_pct_forward),
`fig_t1_cd.csv` (manager, delta, tenor_days, rule, spot_shock, vol_shock, dampening, K_pct_forward), `fig_t1_meta.csv`
(ts, block, n_expiries, listed tenors, iso levels, node values ATM 30 d, min/median/max per manager, node count
per class).

**Caption.**
> **The surface as the engine sees it.** BTC implied volatility over call delta and tenor at 08:00 UTC on 17 September
> 2026, built from the on-chain feeds, with the capital that one short contract binds under PM2 (panel a) and under
> standard margin (panel b) as colour on a common scale in per cent of the forward. Height is volatility, colour is
> capital, and black lines join points of equal capital. Panels c and d name the rule that sets the capital at each
> point: the worst scenario of the PM2 grid, and the branch of the standard margin formula. Their grid lines are the
> delta and tenor bucket edges of Figures~\ref{fig:f1} and~\ref{fig:f2}; the surface holds out-of-the-money options
> only, so buckets above an absolute delta of 0.6 have no counterpart here. Standard margin is set in per cent of spot
> and shown in per cent of the forward. Capital follows the contracts on chain; the venue's off-chain engine discounts
> PM2 at a flat two per cent.

**Check numbers.** 740 nodes per manager; 15 expiries; ts 1789632000. PM2 K in % of the forward min 3.418 / median 10.448 /
max 13.704; SM 12.374 / 12.979 / 15.007. ATM 30 d (Δ 0.50, 30.439 days): PM2 11.826, SM 14.080. SM < PM2 at 9 of 740
nodes, median SM/PM2 1.261. All 1,480 values lie in [3; 15.5]. Decomposition = grid capital at every node.

### T2 · What `get_margin` returns, and how PM2 prices a book · 7.0 × 2.6 in

**Why:** P a shows V as an area and so carries the statement “V sits in C − net, not in R”; P b resolves the factors;
M c is the bridge from the single contract (F1) to the book (F3, F4). Templates: `praktiker/t2_praktiker.png`,
`mechanismus/t2_proto.png`.

**Data.** a, b: `results/p2/semantics/factors.csv`, filter: `measurement` starts with `historical` and does not contain `H0_`,
`case ∈ {A, B}`; exactly four rows (test). Columns `SM_R_engine, PM2_R_engine, V_SM, V_PM2, F_Cnet, F_R_engine`.
Row names: b17_exact A “17 Sep, short”, B “17 Sep, mixed”; b24 (H1 list) A “24 Sep, short”, B “24 Sep, mixed”.
c: row BTC 2026-09-17 of `results/p2/reference_book.csv` (08:00 UTC, listed expiry with 22 days, strike =
forward = 76,587.73). Scenario P&L of the book (short call + short put at the strike) via `figdata_p2.pm2_scenarios(book,
state, params)` with `Timeline("BTC", "pm2").at(ts)`; capital lines `K_pm2`, `K_sm` from the same row and
`K_pm2_call + K_pm2_put` from the new extension of `reference_book.csv` (section 10).

**Layout.** Three panels side by side, widths including labels 2.0 / 2.1 / 2.9 in.

- **a** Title “a  mixed book of 24 Sep 2026”. Two horizontal bars, SM on top, PM2 below, height 0.55. Segment 1 = R
  (manager colour, solid, black edge 0.5 pt), segment 2 = −V of the respective manager (white, hatching `////` in
  `#666666`). Label “R 211” or “R 99” above the left end of the bar, total “708” or “596” to the right of the bar.
  x linear 0 to 800, “C − net = R − V, thousand USDC”. Legend inside the panel at top right: “R, requirement” (solid grey),
  “−V, value term” (hatched).
- **b** Four rows in the order 17 Sep mixed, 24 Sep mixed, 17 Sep short, 24 Sep short. Hollow black circle at
  `F_Cnet`, filled one at `F_R_engine`, grey arrow (head 3 pt) from the hollow to the filled one. Values in the same row, on
  the outer side of their marker (so that 2.14 and 2.33 do not collide). x log 0.8 to 20, ticks 1, 2, 4, 8, 16,
  “SM / PM2 capital ratio (log)”. Vertical line at 2, dashed, labelled at the bottom “H3 threshold, set from these books”.
  Legend row above the panel: “○ on C − net   ● on R”.
- **c** x categorical over the 17 spot shocks of the current grid (0.34; 0.67; 0.86 … 1.14 in steps of 0.035;
  1.5; 2; 3; 4; 5; 6). Three group titles above the axis: “tail ↓ (dampened)”, “core ±14 %” (core shaded
  `#F2F2F2`), “tail ↑ (dampened)”. Horizontal tick labels only at 0.34 / 0.86 / 1 / 1.14 / 6. y “scenario P&L of
  the book, % of forward”, from −1.15·K_SM/F to +3. Points = PM2 scenarios as circles 3.5 pt with a blue edge; fill
  blue for vol up, white for vol unchanged, `#BBBBBB` for vol down; core points of each vol state joined by a thin blue line 0.6 pt,
  tails not joined, skew scenarios only in the CSV. The worst scenario gets a black ring 8 pt. Three
  horizontal lines at −K/F with direct labels on the right above the line: “PM2, book 10.0” blue solid 1.2 pt; “PM2,
  legs one by one {x}” blue dash-dot 1.0 pt; “SM 29.6” vermilion dashed 1.2 pt. Legend of the vol states as a
  row above the panel.

**Tables.** `fig_t2_a.csv`, `fig_t2_b.csv`, `fig_t2_c.csv` (scenarios with spot_shock, vol_shock, dampening, pnl_usdc,
pnl_pct_forward, binding; capital lines).

**Caption.**
> **What \texttt{get\_margin} returns, and how PM2 prices a book.** Panel a splits $C - \mathrm{net}$ into the
> requirement $R$ and the value term $-V$ for the mixed probe book of 24 September 2026 (block 45\,110\,142); $-V$ is
> almost the same under both managers and dwarfs $R$. Panel b sets the ratio of standard to PM2 margin read as
> $C - \mathrm{net}$ (open) against the ratio on $R$ (filled) for the four probe books at their historical blocks. The
> dashed line is the H3 threshold of two, which was set from these books before any maker book was measured. On the
> mixed book of 17 September $V$ is positive, so the ratio falls from 11.86 to 10.76. Panel c is the scenario profit and
> loss of a short BTC straddle struck at the forward on 17 September 2026, on the listed expiry nearest to 30 days
> (22 days), in per cent of the forward. PM2 charges the worst scenario of the whole book plus contingencies (solid
> line), which is less than the sum of the legs margined one by one (dash dot); standard margin is dashed.

**Check numbers.** Four rows. a: SM R 211,023.47, −V 496,914.28, C − net 707,937.75; PM2 R 98,834.91, −V 496,858.84,
C − net 595,693.75. b (C − net / R): 17 Sep short 2.33 / 3.19; 17 Sep mixed 11.86 / 10.76; 24 Sep short 1.46 / 3.61;
24 Sep mixed 1.19 / 2.14. c: K_PM2/F = 10.03 %, K_SM/F = 29.61 % (identical to F5 c and card 1); ring = argmin of the
scenario P&L; spot grid ±14 %.

### F1 · What one contract costs · 7.0 × 3.9 in

**Why:** The statement of F1 is a comparison of managers; P makes it readable on one axis and is the only version that shows
all three underlyings, with one number per cell. Template: `praktiker/f1_praktiker.png`.

**Data.** `results/p2/fig_edge_maps.csv`, maps `map ∈ {"pm2", "sm_pm2win", "pm_pm2win"}` (the same fills in the
PM2 window; `pm_pm2win` BTC and ETH only). Cell value κ = 100·`sum_K`/`sum_index` of the map `pm2`; ratios
q_SM = `sum_K`(sm_pm2win)/`sum_K`(pm2), q_PM = `sum_K`(pm_pm2win)/`sum_K`(pm2). Occupied = `occupied` of the map `pm2`.
Regimes: `results/p2/fig_f1_regimes.csv` from `figdata_p2.cell_capital_by_regime` (`capital.parquet` ⋈
`data/p1/derived/markouts.parquet` on `trade_id`, buckets from Paper 1, filter `K_pm2` finite): per regime and cell
fills, contracts, Σ K_sm·a, Σ K_pm·a, Σ K_pm2·a, Σ index·a, occupied from 200 fills. `fig_capital_by_manager.csv` (median per
fill) is not to be used: it gives two cell sizes for the same cell.

**Layout.** Six maps on the left (rows: sell on top, buy below; columns BTC, ETH, HYPE), one strip per row on the right.

- **Maps:** grid as in 6.4. Number = κ with two significant digits (0.07, 0.12, 9.9, 13, 39). Grey log per row,
  shared across the three underlyings. Row titles on the left “maker sells (short)” and “maker buys (long): capital ≈ premium”;
  column titles BTC, ETH, HYPE; |Δ| labels only on the left, tenor only at the bottom.
- **Strips** (one per row, shared x axis): eight rows “SM BTC”, “  R4”, “SM ETH”, “  R4”, “SM HYPE”,
  “  R4”, “legacy BTC”, “legacy ETH”. One symbol per occupied cell: SM filled vermilion square 2.5 pt (pooled), in the
  R4 row a hollow square (cells with ≥ 200 fills in R4), legacy a filled green diamond; deterministic vertical
  jitter ±0.18 rows by cell index. Median bar per row in black (height 0.5 rows, 1.2 pt; R4 0.6 pt). Number of
  cells per row on the right in 7 pt grey. x log 0.6 to 5, ticks 0.6 / 1 / 2 / 4, vertical line at 1 dashed black;
  header above the top strip “← PM2 dearer   PM2 cheaper →”; x label at the bottom “capital ÷ PM2 capital, same fills
  (log)”.
- **Header** above the maps (7 pt): “number = PM2 capital per contract, % of notional, ratio of sums over the PM2
  window, pooled over four parameter regimes · × = under 200 fills”.

**Tables.** `fig_f1_a.csv` (ccy, side, delta_bucket, tenor_bucket, fills, contracts, occupied, kappa_pm2, kappa_sm,
kappa_pm, printed), `fig_f1_b.csv` (ccy, side, cell, manager, regime ∈ {pooled, R4}, ratio, row, jitter),
`fig_f1_regimes.csv` (see above).

**Caption.**
> **What one contract costs.** PM2 capital per contract in per cent of notional over the absolute delta of the traded
> option and tenor, for maker sells (upper row) and maker buys (lower row), as a ratio of sums over the fills of the PM2
> window, which spans four parameter regimes. Each row is shaded on one logarithmic grey scale, and an empty cross marks
> a cell with fewer than 200 fills. The strips on the right give, for every occupied cell, the capital of the same fills
> under standard margin (squares) and under the legacy manager (diamonds) divided by PM2 capital, with the median cell
> as a bar; hollow squares use only the fills after the parameter change of 20 August 2026. For a maker buy, standard
> margin charges the premium.

**Check numbers.** 210 cells, 173 occupied, 37 crosses (BTC 10 = buy 4 + sell 6, ETH 2, HYPE 25). Fills and contracts
per cell are equal in all three maps. κ spans (occupied cells): BTC sell 7.80 to 17.69, buy 0.07 to 10.86; ETH
7.07 to 21.36 / 0.08 to 14.53; HYPE 17.50 to 38.73 / 0.46 to 15.64. q_SM 0.752 to 4.669, below 1 in 86 cells; median
of the sell cells BTC 0.943, ETH 0.902, HYPE 0.875. q_PM 0.946 to 1.736 over 128 cells. R4 medians of the
sell cells 1.398 (BTC, 6 cells), 1.140 (ETH, 18), 1.444 (HYPE, 1). κ = 100·`sum_K`/`sum_index` from `h1_cells.csv`
(identity, deviation 0). Sums over R1 to R4 = sums of the map (relative ≤ 1e−9).

### F2 · The map in two denominators (H1) · 7.0 × 4.4 in

**Why:** The capital map is contribution 1 of the specification and belongs in the figure; the grey coding makes it
print-proof. The rank-rank picture shows the quantity that H1 tests, and the sign lines show the structural
lower bound: because the capital denominator is positive in every cell, the 99 cells with positive edge come first in both
maps, ahead of the 74 others; even a complete reordering within the two groups would give a ρ of about 0.73 (referee,
4,000 draws), and the threshold is 0.5. This does not change the test, but it must be visible. Templates:
`praktiker/f2_praktiker.png` (maps, rank against rank), `empirie/f2_empirie_SYNTHETIC.png` (verdict bar).

**Data.** `results/p2/h1_cells.csv` (occupied, A_bp, B_bp, rank_A, rank_B, rank_shift, rank_A_lo/hi, rank_B_lo/hi,
fills), `results/p2/h1.json` (stat, lo, hi, rejected, rule, threshold, n, n_days), `results/p2/sensitivity.json` and the
new entries `sign_floor`, `within_pos`, `within_nonpos` (section 10).

**Computation.** Only counting and sorting: number of cells with A_bp > 0 (position of the sign lines), the ten largest
|rank_shift| (ties broken by cell ID).

**Layout.** On the left a (maps, 4.5 in wide, full height), at top right b (rank against rank, 2.3 × 2.25 in), at
bottom right c (forest, 2.3 × 1.85 in).

- **a** Six maps as in F1 (sell on top, buy below; BTC, ETH, HYPE). Number = B_bp (edge per PM2 capital, bp) with
  at most four characters: |v| < 10 with one decimal (“3.4”, “−0.8”), 10 ≤ |v| < 1,000 as an integer (“240”, “−35”),
  |v| ≥ 1,000 in whole thousands (“3k”, “−12k”). Grey by log|B| per row (lower bound 1 bp), negative cells hatched,
  crosses as in F1. Row titles “maker sells (short)”, “maker buys (long): return on premium”. No colour bar. Header
  “number = net edge per unit of PM2 capital, bp, per fill · hatched = negative · × = under 200 fills · PM2 window,
  pooled over four regimes”.
- **b** x = rank_A (“rank by edge per notional”), y = rank_B (“rank by edge per PM2 capital”), both 1 to 173 with
  rank 1 at top right (axes inverted), ticks 1, 50, 100, 150, 173, and the addition “1 = highest edge” in both
  axis titles. Diagonal grey dashed 0.6 pt. Sign lines at 99.5 on both axes, grey
  solid 0.6 pt, labelled “edge ≤ 0” in the lower left block. Symbols: sell ▼ filled black 3 pt, buy
  ▲ hollow black 3 pt. For the ten largest |rank_shift| the rank intervals as a grey cross (0.6 pt) from
  rank_A_lo/hi and rank_B_lo/hi.
- **c** Forest as in 6.5, x = Spearman ρ from −0.2 to 1.0, threshold 0.5, hatching ρ ≥ 0.5 behind the registered
  row. Grey band across all rows from `sign_floor.p05` to `sign_floor.p95`, labelled “sign pattern alone”.
  Rows: “registered” (h1.json); sensitivities “maintenance margin” (`b_mm.h1_pm2_mm`), “net edge, Paper 1”
  (`c_p1_net_edge.h1_pm2`); exploratory “per day to expiry” (`f_time.to_expiry`), “per holding time” (`f_time.holding`),
  “SM capital” (`a_maps.sm_pm2_window`), “legacy PM capital” (`a_maps.pm_pm2_window`), “BTC only”, “ETH only”, “HYPE
  only” (`g_by_ccy.pm2_*`), “edge > 0 only”, “edge ≤ 0 only” (new). n = cells. Bold header as in 6.5, below it
  “173 cells · 463 day clusters · rejected if upper bound ≥ 0.5”.

**Tables.** `fig_f2_a.csv` (cells with B_bp, printed, hatched), `fig_f2_b.csv` (ranks, intervals, top10),
`fig_f2_c.csv` (label, source_key, kind, stat, lo, hi, n, n_days), `fig_f2_shift.csv` (mean rank shift by
tenor and |Δ| per side, for the text).

**Caption.**
> **The map in two denominators (H1).** Panel a is net edge per unit of PM2 capital in basis points, per fill, for every
> cell of the PM2 window by underlying and maker side; negative cells are hatched and an empty cross marks fewer than
> 200 fills. For a maker buy the denominator is close to the premium, so the lower row is a return on premium and is
> shaded on its own scale. The map per notional is Figure~\PH{p1-map-fig} of the companion paper. Panel b ranks the
> \PH{h1-cells} occupied cells by edge per notional and by edge per PM2 capital; because capital is positive in every
> cell, the \PH{h1-pos} cells with positive edge come first in both rankings, and the grey lines mark that boundary.
> Crosses give the 90 per cent rank intervals of the ten largest moves. Panel c is the registered test, Spearman's
> $\rho$ with its 90 per cent day-cluster interval against the threshold of 0.5, followed by sensitivities and, on grey,
> exploratory rows; the grey band is the $\rho$ that the sign pattern alone produces when ranks are shuffled within each
> sign group. Edge is a flow per fill and capital a stock, so a cell's value is not a return per unit of time.

**Check numbers.** 173 points; 210 cells, 37 crosses; 99 cells with A_bp > 0, 74 with A_bp ≤ 0 (buy 26 of 87, sell 48
of 86); sign(A_bp) = sign(B_bp) in all 173; κ between 0.074 and 38.73 %; `n_days` 463; `cells_present_min` 173;
331,813 fills in occupied cells out of 336,087 in the window, 20 fills with K_PM2 ≤ 0; ten cross intervals. Header checked against
h1.json (stat, lo, hi, rejected).

### F3 · The next contract in the book (H2) · 3.4 × 4.0 in

**Why:** H2 tests a median; the ECDF shows it as the crossing with height 0.5, and the shares ≤ 0 and ≤ ½ without
counting bars. The forest carries verdict and robustness. Templates: `praktiker/f3_praktiker.png` (a),
`empirie/f3_empirie_SYNTHETIC.png` (b).

**Data.** `results/p2/fig_h2_dist.csv` (`label = all`, `variant = ratio`, `kind ∈ {hist, share_le_0, n}`; 62 bins:
(−∞; −1), 60 bins of 0.05 on [−1; 2), [2; ∞)), `results/p2/h2.json`, `results/p2/sens_h2.csv` (variant/group) and the
new regime rows (section 10).

**Layout.** Header, a (1.45 in), b (1.75 in), shared x axis [−1; 2].

- **a** ECDF as a step line, black 1.0 pt: value at each right bin edge = cumulative count / n. It starts at x = −1
  at the height of the left overflow and ends at x = 2 at 1 − right overflow; both overflows as text at the margin
  (“x % below −1”, “y % above 2”). Bands behind the curve: ≤ 0 `#BDBDBD`, 0 to ½ `#D9D9D9`, ½ to 1 `#EFEFEF`, > 1
  white; above each band two lines in 7 pt: “free” / “cheap” / “partial” / “dearer” and the share in %. Share ≤ 0 from
  `share_le_0`, the others from the bins. Median as a horizontal black bar 2 pt from lo to hi at y = 0.5 with an
  open circle at stat. Vertical line at ½ dashed black, at 1 grey 0.5 pt solid. y 0 to 1, ticks 0 /
  0.25 / 0.5 / 0.75 / 1, “share of fills”.
- **b** Forest as in 6.5, hatching x ≥ ½ behind the registered row. Rows: “registered” (h2.json);
  sensitivities “next contract” (ratio_unit), “maintenance margin” (ratio_mm), “tape book” (ratio_tape); exploratory
  “M3 (HYPE)”, “M5”, “M8”, “M10” (`group = label=…`), “R1 to 23 Jan”, “R2 to 24 May”, “R3 to 20 Aug”, “R4 since 20
  Aug”. n = fills. x label “ΔK per contract / stand-alone PM2 capital”.
- **Header** on two lines: in bold the verdict line as in 6.5; below it “4 PM2 accounts, ETH and HYPE only · 19 999 of
  20 000 sampled fills · 372 day clusters”.

**Tables.** `fig_f3_a.csv` (x, ecdf, bands with share, overflows), `fig_f3_b.csv`.

**Caption.**
> **The next contract in a dominant maker's book (H2).** Panel a is the cumulative distribution of the marginal capital
> of a fill per contract over its stand-alone PM2 capital, $\Delta K / K_{\text{single}}$, for the \PH{h2-n} tested
> fills of the four PM2 subaccounts, which trade ETH and HYPE only; the numbers above the bands are the shares of fills
> in each band, and the shares beyond the axis are given at both ends. The dashed line is the registered threshold of
> one half, and the bar at height one half is the median with its 90 per cent day-cluster interval. Panel b repeats the
> registered row above the sensitivities and, on grey, exploratory rows per account and per parameter regime. A maker
> who starts from an empty book pays the stand-alone capital of Figure~\ref{fig:f1}.

**Check numbers.** n 19,999, `n_sample` 20,000, `n_excluded` 1, `n_days` 372, seed 20260924; accounts M3 6,405 (HYPE), M5
5,957, M8 4,296, M10 3,341; ETH 13,594, HYPE 6,405; first day 2025-09-04; 62 bins, two of them open; band shares and
overflows add up to 1; ECDF at 0 = `share_le_0` = `h2.json share_nonpositive`; header checked against h2.json.

### F4 · What netting is worth (H3) · 3.4 × 4.0 in

**Why:** Book width is the mechanism behind H3 and shows the account limit of 63 options at its real position;
the forest carries the verdict, the counterfactual share and legacy PM. Same grid as F3. Templates:
`praktiker/f4_praktiker.png` (b, binned here), `empirie/f4_empirie_SYNTHETIC.png` (forest).

**Data.** `results/p2/fig_h3_series.csv` (`status == ok`; label, day, manager, n_legs, over_63_options,
ratio_sm_pm2), `results/p2/h3.json`, `results/p2/sens_h3.csv` and the new rows by account manager and regime.

**Layout.** Header, a (1.45 in), b (1.75 in); margins and panel heights identical to F3.

- **a** Bins in option legs [1; 4), [4; 8), [8; 16), [16; 32), [32; 64), [64; 128), [128; 256), [256; 512). Per bin
  the median of ratio_sm_pm2 (black line 1.0 pt, dot 2.5 pt at the geometric bin centre) and p25 to p75 as a band
  `#CCCCCC`. x log 1 to 400, ticks 1, 4, 16, 64, 256, “option legs in the book (log)”; y log, ticks 1, 2, 4, 8, 16,
  “K_SM / K_PM2 (log)”. Horizontal line at 2 dashed, “2: PM2 saves half”. Vertical line at 63.5 grey 0.6 pt,
  “SM account limit: 63 options”; the region to its right hatched (`\\\\`, `#BBBBBB`), text “SM counterfactual: 1 431
  of 1 943 maker-days”. Maker-days per bin as a number in 7 pt grey above the x axis.
- **b** Forest as in 6.5, x log (0.5 to 32, extended if needed), threshold 2, hatching x ≤ 2 behind the registered
  row. Rows: “registered” (h3.json); sensitivities “maintenance margin” (sm_pm2_mm), “legacy PM / PM2” (pm_pm2_be,
  BTC and ETH legs, n 1,640); exploratory “SM / PM2, same legs” (sm_pm2_be), “≤ 63 options” (sm_pm2_le63), “> 63
  options” (sm_pm2_gt63), “SM account (M2)”, “legacy PM accounts”, “PM2 accounts”, “R1 to 23 Jan” to “R4 since 20 Aug”.
  n = maker-days. x label “capital ratio to PM2 (log)”.
- **Header:** in bold the verdict line; below it “9 accounts · 1 943 maker-days · 462 day clusters (UTC days, not
  accounts)”.

**Tables.** `fig_f4_a.csv` (lo, hi, centre, n, median, p25, p75), `fig_f4_b.csv`.

**Caption.**
> **What netting is worth (H3).** Panel a is $K_{\mathrm{SM}}/K_{\mathrm{PM2}}$ for the opening books of \PH{h3-days}
> maker-days against the number of option legs, as the median per bin with the interquartile band. Beyond 63 options no
> standard margin account on the venue may hold the book, so $K_{\mathrm{SM}}$ is counterfactual on \PH{h3-over63}
> maker-days. The dashed line is the registered threshold of two. Panel b is the registered median with its 90 per cent
> interval, the sensitivities including the legacy manager on BTC and ETH legs, and, on grey, exploratory rows by book
> size, by the manager of the account and by parameter regime. Clusters are UTC days, not accounts.

**Check numbers.** 1,943 maker-days `ok` (plus 24 `no_options`, 1 `no_snapshot`), 462 clusters, 0 excluded, 1,431 with
more than 63 options (73.6 %), `over_63_options` ⇔ n_legs ≥ 64. Nine accounts: M1 120, M2 328, M3 303, M4 203, M5 374, M6
119, M7 10, M8 239, M10 247; managers M2 SM; M1, M4, M7 PM:ETH, M6 PM:BTC; M3 PM2:HYPE; M5, M8, M10 PM2:ETH. Bins 41,
29, 57, 170, 215, 431, 909, 91. Legacy rows n 1,640 (303 not applicable = M3). Header checked against h3.json.

### F5 · The engine over time · 7.0 × 4.3 in

**Why:** P carries the numbers that the text needs before H4; the status grammar of E makes the event selection
checkable; the placebo band shows that ETH PM2 has only ten admissible placebo days. Templates:
`praktiker/f5_praktiker.png`, `empirie/f5_empirie.png` (status, windows).

**Data.** `results/p2/manager_oi_share.csv`; `results/p2/params/{CCY}_{pm,pm2}.json` (every row, all kinds, not
the overrides); `results/p2/events.csv`; `results/p2/reference_book.csv`; `h4.json placebo.admissible_days` and
`results/p2/h4_placebo_days.csv` (new).

**Computation.** Pure parameter effect per event = 100·ln(K_m/K_m_prev) on the first reference day with
`m_param_ts ≠ m_param_ts_prev` after the event (at most one day later); |x| < 0.5 becomes “0”.

**Layout.** Shared calendar axis 2024-01-01 to 2026-09-30, quarterly ticks (“2024-01” …), labels only at the bottom.

- **a** Three strips BTC, ETH, HYPE (0.42 in each), monthly shares as steps (`steps-post`), stacked from the bottom: PM2
  solid `#0072B2`, legacy PM solid light green (`#009E73`, 35 % opacity), SM white with hatching `////` and edge `#D55E00`.
  `fillna(0)` before stacking. y 0 to 1, ticks 0 and 1, “share of option OI” only on the middle strip. Legend as a single
  row above a. Strip titles on the left, bold 8 pt.
- **b** Five rails: “BTC legacy PM”, “BTC PM2”, “ETH legacy PM”, “ETH PM2”, “HYPE PM2”. Every row of the timeline
  as a grey tick (0.08 in, `#999999`). ±14-day windows of the kept events as grey bars (black, 12 %
  opacity, height 0.5 rows), so that overlaps turn darker by themselves. Event symbols as in 6.2 at `event_ts`. Number next to each
  (7 pt): pure effect in log-%, an integer with sign; for two events less than 30 days apart the number of the
  earlier one stands on the left, that of the later one on the right. Admissible placebo days as black dashes 1.2 pt, 0.3 rows below the
  rail, on the right “placebo days: 54”. Start of the PM2 window (2025-06-12 23:00 UTC) as a short mark “PM2 window” on the
  PM2 rails of BTC and ETH, for HYPE from 2025-11-11. Title above b: “parameter changes · number = effect of the parameters
  alone on the reference straddle, log-%”.
- **c** BTC reference straddle in % of the forward per manager (colour and line style), y 0 to 32, ticks 0 / 10 / 20 / 30,
  grid lines only here. Direct labels at the right edge with the values of 2026-09-17 (“SM 29.6 %”, “legacy PM 19.7
  %”, “PM2 10.0 %”). Legacy line 1.2 pt in months with a BTC legacy share ≥ 5 %, otherwise 0.5 pt. Kept BTC events
  as grey vertical lines 0.4 pt. PM2 line from 2025-06-13. Title “BTC reference book: short straddle at the forward, listed
  expiry nearest 30 days, one contract per leg”.

**Tables.** `fig_f5_a.csv` (month, ccy, sm, pm, pm2 after fillna), `fig_f5_b.csv` (ccy, manager, row_ts, kinds,
event_id, status, jump_logpct, window_lo, window_hi, placebo_days), `fig_f5_c.csv` (day, tenor_days, K_sm_pct, K_pm_pct,
K_pm2_pct, legacy_thin).

**Caption.**
> **The engine over time.** Panel a is the monthly share of option open interest per manager and underlying. Panel b
> marks every parameter change of the legacy manager and of PM2 as a grey tick and the registered H4 events as
> symbols: filled when they enter the panel, half filled when kept without a cell of 20 fills on each side, and hollow
> when dropped by the one per cent dose rule. The number is the change that the parameters alone make to the capital of
> the reference straddle, in log per cent. Grey bars are the windows of 14 days on either side of each kept event; the
> windows of January and of May 2026 overlap, so \PH{h4-dup-fills} fills enter two events. Black dashes below each line
> are the days from which placebo dates may be drawn. Panel c is the capital of the BTC reference book, a short straddle
> struck at the forward on the listed expiry nearest to 30 days, one contract per leg, in per cent of the forward; the
> small saw teeth come from rolling between expiries of 21 and 36 days. Parameter changes of standard margin left the
> reference book unchanged.

**Check numbers.** 18 events: 14 kept (13 with panel cells, 1 without: HYPE PM2 2026-01-08), 4 dropped (BTC and
ETH legacy 2024-06-12, BTC and ETH PM2 2025-10-10), panel cells together 475. Jumps in log-%: legacy 2025-02-22 BTC
−18.56, ETH −18.89; PM2 BTC 8 Jan +1.60, 23 Jan −10.49, 24 May −7.84, 20 Aug −26.05; ETH +1.61, −4.88, −3.36, −18.28;
HYPE 8 Jan +1.54, 8 May −7.43, 24 May −37.43, 20 Aug −20.33; dropped events 0. Values on 2026-09-17 (BTC): SM 29.61,
legacy 19.68, PM2 10.03 % (ETH 29.71 / 19.41 / 10.94; HYPE SM 59.36, PM2 20.19, CSV only). PM2 share of OI in September
2026: BTC 90.96, ETH 71.89, HYPE 87.92 %. Admissible placebo days: BTC PM2 54, ETH PM2 10 (2025-07-16 to 2025-07-25), HYPE PM2
67, BTC legacy 363, ETH legacy 319. Duplicate fills 6,527 (BTC 1,457, ETH 2,861, HYPE 2,209). Filled symbols are exactly
the rows with `kept` and `panel_cells > 0`.

### F6 · The price of capital (H4) · 7.0 × 4.2 in

**Why:** Only residualised bins have the slope β; a line through raw pairs (P) or raw terciles (M) is
a dishonest encoding. The strip shows what β is identified from; the checklist shows both criteria. Templates:
`empirie/f6_empirie_SYNTHETIC.png` (b, c), `mechanismus/f6_proto_a_real_bc_synth.png` (labelling of the mechanisms).

**Data.** `data/p2/derived/h4_panel.parquet` (pairs `event_id, cell`) ⋈ `results/p2/h4_doses.csv`;
`results/p2/fig_h4_events.csv`; `results/p2/h4.json`; `results/p2/h4_placebo.csv`; `results/p2/sensitivity_h4.json`;
`results/p2/fig_h4_fwl_bins.csv` (new, section 10).

**Layout.** Left column 3.3 in: a (2.55 in high), below it d (1.1 in). Right column 3.5 in: b (1.95 in), below it
c (1.7 in). Header above everything: “13 events · 475 cell-event pairs · 91 446 rows from 84 919 fills (6 527 in two
windows) · 141 day clusters · 322 day × underlying effects”.

- **a** 13 rows by event date, labels “2025-02-22 BTC legacy” and so on. One symbol per pair at x = 100·dose:
  sell ▼ filled 0.15 rows above the line, buy ▲ hollow 0.15 below it, 2.5 pt. Median per row as a black bar.
  Grey band |x| < 1 across all rows, labelled at the top “|dose| < 1 log-%: {share} of pairs”. n pairs on the right. x
  linear −46 to +4, ticks −40, −30, −20, −10, 0, “dose: change in log capital of the cell, log-% (< 0: capital got
  cheaper)”.
- **b** With `fig_h4_fwl_bins.csv`: x = residualised post × dose in log-%, y = residualised half spread in bp of the
  index, 20 equally populated bins as black circles with area proportional to the fills; line through the origin with
  slope β/100 black 1.0 pt; text in the panel “β = {stat} bp per log unit · 90 % interval [{lo}, {hi}], descriptive”;
  below the x axis a strip of 0.15 in with the histogram of the residualised x (40 bins, grey). Axes
  “post × dose, residualised, log-%” and “half spread, residualised, bp of index”.
  **Fallback, only if the inference does not deliver the bins:** within-event contrasts from
  `fig_h4_events.csv`, per event and tercile k x = 100·(t_k_median_dose − mean of the three terciles), y = (t_k_y_post −
  t_k_y_pre) − mean of the three terciles, 39 hollow grey circles, **no line**; y axis “within-event contrast, bp of
  index (no day effects)”, text “no fitted line: binned residuals not available”.
- **c** Histogram of the 100 placebo β (grey, 20 bins over the range including β), integer y ticks, P95
  dashed black “placebo P95”, β solid black 1.5 pt “estimate”. Checklist above the panel, 7 pt: “β > 0
  and one-sided wild p = {p} ≤ 0.05: met / not met”, “β above placebo P95 ({p95}): met / not met”, in bold “H4: rejected / not
  rejected”. The line is built from `criteria` and must match `rejected`. At the bottom of the panel “placebo days: BTC 54 · ETH
  10 · HYPE 67 · legacy 363 / 319”.
- **d** Forest as in 6.5: “registered” (β from h4.json, interval marked as “descriptive”), exploratory “BTC
  only”, “ETH only”, “HYPE only” (`sensitivity_h4.json by_ccy`), n = clusters. Vertical line at 0 dashed, hatching β
  ≤ 0 behind the registered row. x “β, bp of index per log unit of capital”.

**Tables.** `fig_f6_a.csv` (event_id, ccy, manager, cell, side, dose_logpct, n_pre, n_post), `fig_f6_b.csv` (bins
or fallback, with column `mode`), `fig_f6_c.csv` (rep, beta; plus p95, β, p, criteria), `fig_f6_d.csv`.

**Caption.**
> **The price of capital (H4).** Panel a shows the dose, the change in log capital that a parameter change makes to a
> cell, for each of the \PH{h4-pairs} cell and event pairs of the \PH{h4-events} events in the panel, sells above and
> buys below each line, with the median as a bar. Panel b is the half spread against the post-event dose after removing
> the cell by event and the day by underlying effects, in 20 bins of equal size; the line has the slope $\beta$, whose
> interval is descriptive because the registered p-value comes from restricted residuals. Panel c places $\beta$ among
> the estimates at 100 placebo dates and lists both registered criteria. Panel d gives $\beta$ per underlying, for
> exploration. Most doses are close to zero or negative, so $\beta$ is identified from parameter changes that made
> capital cheaper. To read the slope: capital ten per cent cheaper is a dose of $-0.105$, which predicts a change in the
> half spread of $-0.105\,\beta$ basis points of the index.

**Check numbers.** 13 rows; pairs per event 25, 25, 27, 38, 43, 50, 37, 40, 54, 52, 29, 35, 20 (sum 475, equal to
`fig_h4_events.csv n_cells`); dose over the pairs: median −0.634 log-%, minimum −44.21, maximum +2.20, 11.2 % positive,
48.6 % below −1 log-%, 44.4 % with |dose| < 1 log-%; 91,446 rows, 84,919 fills, 141 clusters, 322 day × underlying; 100 finite placebo β. β, lo, hi,
p, p95 and `criteria` checked against h4.json; slope of the line = β.

### A1 · Does the replica match the chain? · 7.0 × 2.5 in (appendix)

**Why:** The registered threshold is on the median; M shows it per row with n, and P b shows that the error does not grow with
the size of the book. Templates: `mechanismus/a1_proto.png` (a), `praktiker/a1_praktiker.png` (b).

**Data.** `results/p2/validation.csv`, filter `status == "ok"` and `is_initial == True`; thresholds from
`validation_summary.json` (`thresholds.median = 0.001`, `thresholds.p95 = 0.01`).

**Layout.** a 4.2 in wide, b 2.6 in.

- **a** Eight rows (`kind == "single"`): BTC SM, BTC legacy PM, BTC PM2, ETH SM, ETH legacy PM, ETH PM2, HYPE SM,
  HYPE PM2. x = |rel_err| log 1e−13 to 1e−1; exact zeros in a grey margin strip on the left at 3e−13, labelled
  “exact”. Symbols by manager 2 pt, vertical jitter ±0.2. Median as a black bar 1.2 pt over 0.6 rows, p95
  as a black bar 0.6 pt. Thresholds as vertical lines: 1e−3 black dashed “median bound 0.1 %”, 1e−2 black
  dash-dot “p95 bound 1 %”, labelled directly. n on the right.
- **b** Books (`kind == "book"`): x = n_legs log 2 to 300, y = |rel_err| log 1e−13 to 1e−1 with the margin strip “exact”
  at the bottom, symbols by manager, thresholds as horizontal lines as in a. Text in the panel: “largest miss 0.05 USDC on K up to 19.5 M
  USDC” and “26 books from 20 maker-days (BTC 7, ETH 18, HYPE 1)”. MM only in the CSV.

**Tables.** `fig_a1_a.csv`, `fig_a1_b.csv` (with the MM rows and a column `drawn`).

**Caption.**
> **Does the replica match the chain?** Absolute relative deviation of initial-margin capital between each offline
> replica and \texttt{eth\_call} on the deployed contracts, for single contracts per underlying and manager (panel a)
> and for the opening books of 20 maker-days against their number of legs (panel b). Exact matches sit in the strip on
> the left of panel a and at the bottom of panel b. The lines are the registered bounds for the median (0.1 per cent)
> and the 95th percentile (1 per cent). One single HYPE contract under PM2 hit a reverting call and is left out. In the
> PM2 window no fill uses a feed older than the limits of the validation blocks. The replica follows the contracts on
> chain; the venue's off-chain engine discounts PM2 at a flat two per cent.

**Check numbers.** n per row 100, HYPE PM2 99; exact zeros (IM, single) BTC PM2 19, BTC SM 45, ETH PM2 15, ETH SM 53,
HYPE SM 49, total 181; largest single IM value 8.88e−8 (ETH PM2); largest median 3.18e−9 (ETH legacy PM); books 77
IM rows, 2 to 245 legs, largest value 3.45e−8 (ETH legacy PM), largest absolute deviation 0.0503 USDC, K_chain up to
19,494,690 USDC; 1 revert case (2 rows). The sentence on feed age is checked against `capital.parquet` in the build (referee:
in the PM2 window p99 vol 119 s, forward 95 s); if it does not hold, it is dropped.

---

## 8 · GIF of the capital surface

**Content.** BTC, short side, PM2 only, as a 3D surface in the look of T1 (height IV, colour `cividis` = capital in % of the
forward, iso-lines 8 and 12 % with labels). In the top right corner “SM, same ATM 30 d short: {x} %” from the
SM grid of the same frame. Below it a time strip with the BTC reference straddle per manager (colour and line style
as in F5 c), a running cursor and the kept PM2 events as vertical lines with the step in simple per cent.

**Frames.** Every Wednesday at 08:00 UTC from 2025-06-18 to 2026-09-16 (66 frames), plus the T1 block of 2026-09-17 08:00 UTC as the
last frame. For each kept BTC PM2 event (8 Jan, 23 Jan, 24 May, 20 Aug 2026) three daily frames: the last
08:00 block before the event, the first one after it and the following day; the first frame after the event is held for 6 frames
(1.5 s) and carries a banner. 4 fps, about 25 s. Banner texts from `events.csv` and `reference_book.csv`, simple per cent:
“8 Jan 2026 · margin parameters · straddle +1.6 %”, “23 Jan 2026 · scenario weights · straddle −10 %”, “24 May 2026 ·
vol shocks, contingencies, scenarios · straddle −7.5 %”, “20 Aug 2026 · parameter bundle incl. spot grid ±17 % → ±14 %
· straddle −23 %” (on two lines if needed).

**Honesty.** A fixed colour scale over all frames (`p2surface.fit_limits`), printed on the colour bar. Every frame shows
date, time and block. Expiries without a fresh feed (older than `LIVE_MAX_AGE`) are left out, and nodes outside the
live expiries are drawn in `NA_COLOR` instead of being extrapolated; a badge “{k} expiries without fresh feed left out” when
k > 0. A weekly frame without a live expiry is skipped and noted in the table. Only the
fixed iso-lines are highlighted, none chosen after the fact.

**Format.** Master 1200 × 675 px for the README and X; banner and date at least 32 px, axes and ticks at least 22 px.
GIF with a global 256-colour palette under 8 MB; MP4 1280 × 720 via `animate.write_mp4`; static end frame as PNG
(also the poster in the README). Files `docs/media/BTC_p2_capital_pm2.gif`, `.mp4`, `_end.png`; table
`results/p2/gif_frames.csv` (frame, date, ts, block, hold duration, expiries, left-out expiries, K min/median/max,
banner). Built via `p2surface.animate(managers=("pm2",), …)` with the additions iso-lines, hold frames with banner,
unit %, SM corner; run only through `scripts/p2_heavy.py` (machine lock, feed history by quarter).

**Check numbers.** 67 regular frames plus 12 event frames; last frame identical to T1 a (same K values per node);
steps in the time strip = exp(jump from F5) − 1: +1.6 %, −10.0 %, −7.5 %, −22.9 %.

---

## 9 · Social cards 1600 × 900

Shared: `figures_social` style (fixed size without `bbox tight`), font at least 28 px, everything inside the frame
(test on `tightbbox`), every number in the title readable in the image, colour double-coded as in the paper, simple per cent.
Footer “Derive, chain 957 · replica of the deployed margin contracts · pre-registration commit c4fcb59”
(`c4fcb59` is now `e492ba1`; since review round 1 the footer names the pre-registration commit itself, now
`cc0a29f`, see `docs/paper2/MANUSCRIPT.md` section 7.2). Output `paper2/social/s1_three_engines.png`,
`s2_straddle_vs_call.png`, `s3_verdicts.png`, tables `results/p2/fig_s{1,2,3}.csv`.

1. **“One short BTC straddle. Three margin engines.”** Left two thirds: time series from F5 c (2024-01 to 2026-09,
   lines 4 px, line style per manager), at the PM2 line the steps “+2 %”, “−10 %”, “−8 %”, “−23 %”, vertical lines
   “parameter changes kept for H4”. On the right three large numbers “30 %”, “20 %”, “10 %” with line pattern and name below.
   Subtitle “Capital for one short straddle at the forward, listed expiry nearest to 30 days (22 d on 17 Sep 2026), %
   of forward. Capital for a hypothetical book, not a balance.” Template `mechanismus/card_straddle_1600x900.png`.
   Check numbers 29.61 / 19.68 / 10.03 %.
2. **“Under PM2 a short straddle needs less capital than one short call.”** Two groups (PM2, SM), two bars each from 0:
   “one short call” (outline in the manager colour, white fill) and “short straddle” (solid in the manager colour; SM with
   hatching), values above the bars. Both from the same row of `reference_book.csv` (2026-09-17, strike = forward,
   22 days), single legs from the extension (section 10). Subtitle “BTC, 17 Sep 2026, 08:00 UTC, strike at the
   forward, 22 days, % of forward. Capital, not risk.” **Title rule:** the title holds only if K_PM2(straddle) <
   K_PM2(call); otherwise it reads “Under PM2 the second leg of a straddle adds little capital”, provided K_PM2(straddle) −
   K_PM2(call) < 0.25·K_PM2(call); otherwise the card is dropped and the reserve moves up. Template
   `praktiker/social_2_straddle_vs_leg.png` (its legs come from different objects, do not take that over).
3. **“Four pre-registered tests. Four verdicts.”** Four rows H1 to H4, each with the statement in plain words on the left
   (“The capital denominator reorders the map”, “The next contract in a big book is cheap”, “PM2 needs less than half of
   SM's capital”, “Cheaper capital, tighter spreads”), a verdict bar in the middle (estimator, interval, threshold,
   hatched rejection side; H4: β with the placebo P95 as a mark and “one-sided p = …”), and on the right the verdict “rejected”
   or “not rejected”. Numbers only from `h1.json` to `h4.json`; verdicts by the same rules as `ruler`. Title and
   layout do not depend on the outcome.

**Reserve:** “One parameter bundle, one fingerprint”: dose map BTC PM2 2026-08-20, sell side, simple per cent per
cell, cross by the panel rule; the numbers in the title are built from the map. Template
`mechanismus/f6_proto_a_real_bc_synth.png` panel a, without `PuOr` (grey by |value|).

**Rejected:** P card 1 (the same series as card 1, title cut off, the 35 % not readable in the image), P card 3
(two populations, flips in the last regime), keyframe as a card (it becomes the end frame of the GIF).

---

## 10 · Data contract: what must be delivered before the build

Everything here is exploratory or descriptive and is labelled as such; no registered number changes.

| Delivery | Who | For | Content | Fallback if it is missing |
|---|---|---|---|---|
| `results/p2/fig_h4_fwl_bins.csv` | `inference_p2_h4.py` | F6 b | `kind = bin`: bin, x_mean, y_mean, n_rows, n_fills (20 equally populated bins of post·dose, residualised on α and γ, and of y likewise, x in log-%); `kind = hist`: x, x_hi, count (40 bins); plus `fwl_slope` = Σx̃ỹ/Σx̃² over all rows | within-event contrasts without a line (F6 b) |
| `results/p2/h4_placebo_days.csv` | `inference_p2_h4.py` | F5 b | timeline (event_id key as in `admissible_days`), day, admissible, drawn_count | band dropped, only the number of days stands at the rail |
| `sensitivity.json`: `h1_sign.within_pos`, `h1_sign.within_nonpos`, `h1_sign.sign_floor` | `inference_p2.py` | F2 c | ρ within edge > 0 and within edge ≤ 0 with interval (same bootstrap); ρ under a random ordering within the sign groups, 4,000 draws, seed 20260924: mean, p05, p95 | rows and band dropped; a sentence in the text citing the referee is **not** allowed, the number must come from `results/p2` |
| `sens_h2.csv`, `sens_h3.csv`: `group = regime=R1…R4` | `inference_p2.py` | F3 b, F4 b | median with interval per regime as in 6.6 | rows dropped |
| `sens_h3.csv`: `group = account_manager=SM/PM/PM2` | `inference_p2.py` | F4 b | median with interval over the accounts per account manager | rows dropped, accounts one by one only in the CSV |
| `reference_book.csv`: `K_<m>_call`, `K_<m>_put` | `p2surface.reference_book_series` | T2 c, card 2 | capital per leg as a one-leg book at the same block, all managers | T2 c without the dash-dot line, card 2 dropped |
| `figdata_p2.binding_rule` | `figdata_p2.py` | T1 c/d | section 7 T1, with the sum test | no fallback, T1 waits |
| `figdata_p2.pm2_scenarios` | `figdata_p2.py` | T2 c | scenario P&L per (spotShock, volShock, dampening) of a book | no fallback |
| `figdata_p2.cell_capital_by_regime` → `fig_f1_regimes.csv` | `figdata_p2.py` | F1, text | section 7 F1 | hollow symbols dropped |
| `figstyle.FS_MIN`, `figstyle.MANAGER`, `figstyle.SIDE`, P2 rc without `bbox tight` | `figstyle.py` | all | section 6 | no fallback |

Not requested: `h1_rho_draws.csv` (F2 shows no histogram of ρ), `hedges_worst` in `books.py`.

---

## 11 · Check script `scripts/p2_figure_check.py` and tests

Pattern `scripts/p1_figure_check.py`, without tautological comparisons: the script reads the printed values from
`fig_<slot>_<panel>.csv` (column `printed` and the full values) and compares them with the sources, not with themselves.
It writes `docs/paper2/FIGURE_CHECKS.md` and exits with a status ≠ 0 on any deviation.

- **Sources:** T2 against `factors.csv` (exactly four rows); T1 against `probe_BTC_2026-09-17_summary.json` and the grid; F1
  against `fig_edge_maps.csv`; F2 against `h1_cells.csv` and `h1.json`; F3 against `fig_h2_dist.csv`, `h2.json`, `sens_h2.csv`;
  F4 against `fig_h3_series.csv`, `h3.json`, `sens_h3.csv`; F5 against `reference_book.csv`, `events.csv`,
  `manager_oi_share.csv`, `h4.json`; F6 against `h4_doses.csv`, `h4_panel.parquet`, `fig_h4_events.csv`, `h4.json`,
  `h4_placebo.csv`, `sensitivity_h4.json`; A1 against `validation.csv` and `validation_summary.json`.
- **Verdicts:** every verdict line (F2 c, F3 b, F4 b, F6 c, card 3) is rebuilt from the rule and the bounds and must
  match `rejected`; H4 from `criteria`.
- **Counts:** crosses in F1 and F2 37 each (cells under 200 fills, including combinations without any fill); 173 points in F2
  b; F1 strips 173 SM points and 128 legacy points; F5 b 14 filled or half-filled and 4 hollow symbols, filled ones
  exactly `kept & panel_cells > 0`; F6 a 13 rows and 475 symbols; F4 a eight bins with at least 20 maker-days each; A1
  n per row.
- **Identities:** κ in F1 = 100·`sum_K`/`sum_index` in `h1_cells.csv`; T2 c, F5 c and card 1 show the same
  straddle value (10.03 / 29.61 %); last GIF frame = T1 a; F6 b line = β and `fwl_slope` = β (relative ≤ 1e−8);
  sums of the regimes = pooled sums (F1).
- **Form** (also as a test in `tests/test_p2_figures.py`): PDF width 3.4 or 7.0 inches ± 0.02; no font below
  7 pt; all texts inside the canvas; exactly one figure with `Axes3D` (T1); no colour other than the manager colours,
  grey and black in F2 to F6 and A1 (check the palette of the artists); ▲/▼ only as side symbols; cards 1600 × 900 px;
  GIF under 8 MB.
- **Captions:** no dash (“—”, “–” as punctuation) in the captions of `paper2/main.tex`; every `\PH{key}`
  of the captions is in the numbers sheet.

---

## 12 · Changes to `paper2/main.tex`

- All nine captions are replaced by the drafts above. In particular, T1 drops “capital in USDC”, F1 drops
  “capital per contract in USDC” and “each panel is shaded on its own scale”, F2 drops “lines connect the rank of each
  cell”, F5 drops “recomputed at every parameter change” (the series is computed daily at 08:00 UTC), and F6 drops the
  two-panel description.
- New placeholders for `docs/paper2/MANUSCRIPT.md` and the numbers sheet: `p1-map-fig` (number of the notional map in Paper 1),
  `h1-pos` (cells with positive edge), `h3-over63` (maker-days with more than 63 options), `h4-pairs`, `h4-dup-fills`;
  the existing keys `h1-cells`, `h2-n`, `h3-days`, `h4-events` stay in use.
- Order of the floats as in the skeleton: T1 and T2 in the section on the engine, F1 in data and measurement, F2 to F6 in the
  results, A1 in the appendix. F3 and F4 as `figure[t]` with identical height.

---

## 13 · Files

- This specification: `docs/paper2/FIGURE_SELECTION.md`
- Drafts and jury: `docs/paper2/drafts/{mechanism,empirics,practitioner,jury_referee,jury_design}.md`
- Prototypes and measurement: `data/p2/fig_proto/{mechanismus,empirie,praktiker,jury}/`
- To build: `derive_surface/figures_p2.py`, `derive_surface/figdata_p2.py`, additions to `figstyle.py`,
  `p2surface.py`, `inference_p2.py`, `inference_p2_h4.py`; `scripts/p2_figure_check.py`; `tests/test_p2_figures.py`;
  outputs `paper2/figures/`, `paper2/social/`, `docs/media/BTC_p2_capital_pm2.*`, `results/p2/fig_<slot>_<panel>.csv`,
  `results/p2/gif_frames.csv`, `docs/paper2/FIGURE_CHECKS.md`.
