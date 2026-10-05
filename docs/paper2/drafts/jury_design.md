# Jury for Paper 2, design lens

Status 2026-09-25 · design judge (pattern of Paper 1: three draft sets, two judges) · nothing committed.

**Lens.** Legibility at 8 pt in two-column CAS typesetting, printed in greyscale: font never below 7 pt *after
placement*, density, the same coding in all nine figures, 3D only where it carries something, and colour maps
that still work in grey.

**What was checked.**

1. All 29 PNGs of the three lenses were viewed, plus the probe images `data/p2/surface/probe_*.png`,
   `proto_btc_iv_colored_by_smcapital.png` and a single frame of the existing GIF.
2. Greyscale: the colour-dependent images (T1 M/P, F1 E, F2 E/P, F5 M/P, F6 M, T2 P) were converted to luminance
   and viewed.
3. **Mechanical measurement.** The script `data/p2/fig_proto/jury/audit_protos.py` calls every prototype function, intercepts
   `savefig` and rewrites none of the lenses' files. It measures the drawn extent without watermarks
   and the smallest font set. The result is in `data/p2/fig_proto/jury/audit_protos.csv`. The
   PNG sizes themselves are no use for this, because the large PROTOTYP stamps inflate the `bbox tight` (practitioner F3
   is 4.5 inches as a PNG, while 3.29 are drawn).
4. Of the inference files (`h1.json` … `h4.json`, `fig_*.csv`, `sens_*.csv`) only column names and keys were
   read, no values. Values were read from `manager_oi_share.csv`, because the file is descriptive.

Abbreviations: M = mechanism, E = empirics, P = practitioner. Marks from 1 to 10 for the design only. Content and
recomputation are judged by the referee.

---

## 1 · Verdict in one table

| Slot | Choice | Size (in) | Core of the decision |
|---|---|---|---|
| T1 | **P-T1 a/b ⊕ M-T1 c/d** | 7.0 × 4.2 | P carries the value on the surface (iso-lines, headline number), M explains it (binding rule as a 2D map) |
| T2 | **P-T2 a/b ⊕ M-T2 c** | 7.0 × 2.6 | P is the cleanest version of the semantics, M-c is the only place that shows how PM2 forms R |
| F1 | **P-F1** | 7.0 × 3.9 | three underlyings, one number per cell, the manager comparison as a strip instead of nine maps |
| F2 | **E-F2, with a as small multiples per underlying** | 7.0 × 3.4 | the only version that shows the verdict *and* the direction of the reordering; the P and M maps fail in grey |
| F3 | **P-F3 a ⊕ E-F3 b** | 3.4 × 3.6 | the ECDF reads the median directly, the forest carries the verdict |
| F4 | **P-F4 b (binned) ⊕ E-F4 b** | 3.4 × 3.6 | book width as the mechanism, forest as the verdict, the same grammar as F3 |
| F5 | **P-F5 ⊕ status grammar from E-F5** | 7.0 × 4.3 | direct labels, one number per event, no legend column |
| F6 | **M-F6 a ⊕ E-F6 a (FWL) ⊕ E-F6 c (checklist)** | 7.0 × 4.2 | real dose maps show the identifying variation; b and c need the inference grammar |
| A1 | **M-A1 a ⊕ P-A1 b** | 7.0 × 2.5 | strips with median and n, plus error against book width |
| GIF | P/M concept (3D, PM2 only) with the honesty rules from E | 1200 × 675 | |
| Cards | 1 = M card ⊕ P steps; 2 = P card 2 (new title); 3 = P card 3 after H3, otherwise M card 3 | 1600 × 900 | |

Nine figures: T1, T2, F1 to F6 and A1. The only 3D figure in the PDF is T1. F3 and F4 stay single-column, as in
the skeleton `paper2/main.tex`, and get the same layout, so that they can stand side by side at the top of a page.
The shared `figure*` that E proposes would lower the count to eight and waste the slot.

---

## 2 · The measurement: width and smallest font after placement

None of the three scripts sets anything below 7 pt, and that holds for M as well (`FS = 7.0`), although `figures_p1.py`
uses 6.0 and 6.5 pt. The problem lies elsewhere: legends, side texts and long row labels stick out beyond
the figure width. `\includegraphics[width=\linewidth]` then scales the image back down to 7.0 or 3.4 inches,
and the font shrinks with it.

| Prototype | drawn (in) | target | smallest font when typeset |
|---|---|---|---|
| E-F1 | 8.54 × 3.69 | 7.0 | **5.7 pt** |
| E-F3 | 3.96 × 3.54 | 3.4 | **6.0 pt** |
| E-F4 | 3.94 × 3.54 | 3.4 | **6.0 pt** |
| M-F5 | 7.69 × 4.73 | 7.0 | **6.4 pt** |
| E-F6 | 7.54 × 2.70 | 7.0 | 6.5 pt |
| M-F2 | 7.47 × 2.83 | 7.0 | 6.6 pt |
| P-F5 | 7.44 × 4.19 | 7.0 | 6.6 pt |
| E-T2 | 7.35 × 2.27 | 7.0 | 6.7 pt |
| P-F2 | 7.30 × 3.87 | 7.0 | 6.7 pt |
| P-F6 | 7.18 × 2.22 | 7.0 | 6.8 pt |
| E-F5 | 7.13 × 4.48 | 7.0 | 6.9 pt |
| all others (M-T1, M-T2, M-F1, M-F6, M-A1, E-F2, E-A1, P-T1, P-T2, P-F1, P-F3, P-F4, P-A1) | ≤ target | | 7.0 pt |

**Requirement for `figures_p2.py`:** `figstyle` gets `FS_MIN = 7.0`. A test calls every figure function and checks
two things: no visible text instance is smaller than `FS_MIN`, and the drawn `tightbbox` is at most as
wide as the target (3.4 or 7.0 inches). The script `jury/audit_protos.py` shows how to do it. Legends sit inside the
panel or are replaced by direct labels; there is no longer a legend column to the right of the axes.
This column (M-F5, E-F5, P-F5) and overly long row labels on the left (E-T2, E-F3, E-F4) are the most common
causes of the overruns.

---

## 3 · One visual language for all nine figures

The drafts contradict each other in their coding. These rules apply to every figure and to the cards:

1. **Colour belongs to the managers and to nothing else.** PM2 blue `#0072B2`, solid, circle; SM vermilion `#D55E00`,
   dashed, square; legacy PM green `#009E73`, dotted, **diamond** (M and P; E takes a triangle, which collides with the
   side coding). The label in the figure reads “legacy PM”; in the skeleton the manager is called
   “legacy manager”.
   - **Underlyings get no colour.** E colours BTC blue, ETH orange and HYPE pink (E-F1c, E-F2a, E-F6b). But blue and
     orange mean PM2 and SM everywhere else, and in grey ETH and HYPE fall on the same value (checked).
     Underlyings stand in the row or panel title or in small multiples. P uses the diamond for HYPE, which already
     belongs to legacy PM. That is why underlyings do not get a marker shape of their own either.
   - Non-manager data (ECDF, histograms, β lines, estimators) are black or grey. E-F3 (bars > 0 blue), E-F4
     (≤ 63 options blue), P-F3 (ECDF blue), P-F4 (boxes blue) and the β lines in M/E/P-F6 are recoloured.
2. **Side:** ▲ = maker buy (long), ▼ = maker sell (short), always both words. In maps **sell is on top**,
   buy below (as in P-F1 and M-F6; the subject is the capital of the shorts, and T1 shows shorts).
3. **Status:** filled = registered or in the H4 panel, hollow = sensitivity or dropped, hollow diamond = kept, but
   without a panel cell. Exploratory rows sit on a grey background (E).
4. **Verdict grammar from E for F2, F3, F4 and F6.** The bold header reads “registered: estimator [lo, hi] →
   rejected/not rejected”. The threshold is dashed, the rejection region hatched (only behind the
   registered row), and n and the cluster count stand on the right. A function `ruler(ax, h)` builds this, and the build
   aborts if the printed rule does not match `rejected`.
5. **Maps:** one number per cell; positive quantities in sequential grey (log), font colour black or white
   depending on lightness; × for cells under 200 fills (in F6 under 20 fills before the event). **No diverging
   colour maps.** P-F2 (orange-white-blue) and M-F6 (`PuOr`) have two faults: their ends fall on the same value in grey
   (checked: “−3.4k” and “4.3k”, and “+2” and “−21”, are equally grey), and orange and blue are already taken by SM and
   PM2. Signed maps are therefore shaded grey by |value|, the rarer sign is
   additionally hatched, and the sign always stands as a number in the cell.
6. **Units, one per quantity:**
   - Capital from fills: “% of notional” (notional = quantity × index, like “bp of notional” in Paper 1 and the H1 map A).
     That is the same as % of the index per contract, but only one of the two phrasings appears.
   - Capital on the engine grid and in the reference book: “% of forward”.
   - Change in capital (dose, parameter jump): **100·Δln K, “log-%”** in all figures of the paper, so that F5, the
     dose maps in F6a and the axis in F6b show the same number and β fits directly. The cards for X show
     simple per cent.
   - USDC only in T2 (amounts of a book) and in the CSV files.
7. **Capital scale:** `cividis` in T1, in the GIF and in the keyframe, fixed over all frames (`fit_limits`). Iso-lines
   use the same levels in 3D, in the 2D maps and on the colour bar.
8. **Typesetting:** “≤ 2 d” instead of “<=2d”, an en dash in ranges (“2–7 d”), symbols as mathtext
   (“K_SM / K_PM2” in E-F4 has underscores). Tick labels black, not grey (P sets 7 pt ticks in
   `GREY`, which is too faint in print). Panel letters 8 pt bold.
9. **Tables:** one CSV file per panel, `results/p2/fig_<slot>_<panel>.csv`, so that the check script can compare panel by
   panel (M). The check script from E (`scripts/p2_figure_check.py`: cross count, verdict line against
   `rejected`, filled events against `kept`) is extended by the measurement from section 2.

---

## 4 · The slots in detail

### T1 · The engine's view of the surface · P-T1 a/b ⊕ M-T1 c/d · 7.0 × 4.2

| Draft | Mark | Design |
|---|---|---|
| M | 7 | The 2D maps “binding PM2 scenario / binding SM rule” are the strongest new element of all drafts and flawless in grey (grey areas, dots, hatching, iso-lines with their own line style). The 3D panels without iso-lines carry the value in grey only through lightness. |
| E | – | No prototype. M tried the proposed floor contours: mplot3d sorts by depth, and floor and lines disappear behind the surface. |
| P | 8 | Iso-lines on the surface carry the number without colour (checked in grey), and the headline number “ATM 30 d short = 11.8 % of fwd” is the 5-second message. The ATM 30-day node itself is hidden. |

**Layout.** At the top a (PM2) and b (SM) in 3D as in P: same view (elev 24, azim −128), common `cividis` scale,
iso-lines 4/8/12/14 % labelled inline and marked on the colour bar, panel titles with the headline number. At the bottom c and d as in
M as 2D maps with the same call-delta axis, the binding rule as grey/dots/hatching, the same iso-lines, plus
the bucket edges of Paper 1 as thin white lines (an idea from E, moved here from the invisible floor).

**Requirements.**

- Mark the ATM 30-day node as a point with a label in a and c, so that the headline number has a location.
- z axis “implied vol, %”, colour bar “capital per short contract, % of forward”. Without this separation one reads
  height as capital (M, E, P agree).
- The bucket lines apply only to |Δ| ≤ 60: the grid holds only out-of-the-money nodes, and the cells 60–100 from F1
  (in-the-money options) have no counterpart on the surface. That belongs in one sentence of the caption.
- Height from 4.3 down to 4.2 inches: the legends of c and d stand in one row below both maps, and the
  prototype footer is dropped.
- M-T1 d stays in, because it explains the bright ridge of the SM surface: exactly there 15 % − OTM is larger than the floor
  of 13 %.

### T2 · What `get_margin` returns and how PM2 forms R · P-T2 a/b ⊕ M-T2 c · 7.0 × 2.6

| Draft | Mark | Design |
|---|---|---|
| M | 6 | Panel c (scenario PnL of the straddle, binding scenario circled, three capital lines) is the only panel that shows the netting mechanism. In b “2.14” and “2.33” collide, the legend circle covers “on”, and the x ticks in c are rotated by 90° and partly empty. |
| E | 5 | All four books in USDC, but the long row labels take half the width. Drawn at 7.35 inches, so 6.7 pt when typeset; “1.19” sits on the axis line. |
| P | 8 | One book as a stack R + (−V), on the right the dumbbells with the arrow C − net → R. Clear in 5 s. Faults: “R 99k” stands in white on the hatching, and the arrow for 17 Sep is hidden. |

**Layout.** a (2.0 inches) as in P, b (2.1 inches) as in P, c (2.9 inches) as in M.

**Requirements.**

- In a the R number stands outside the narrow PM2 bar; the book variant (H1 list against H0) stands in the panel title.
- In b the backward arrow for 17 Sep (V > 0) is recognisable as a mark of its own, or the caption names it.
- In c the x ticks are horizontal, and only 0.34 / 0.86 / 1 / 1.14 / 6 are labelled. Above them three group titles:
  “tail ↓ (dampened)”, “core ±14 %”, “tail ↑”. The skew diamonds become larger or are dropped.
- In c the three horizontal lines stay directly labelled (9.7 / 23.5 / 29.0). The caption says that the
  PM2 line lies below the circled scenario (contingencies, IM factor), otherwise it looks like an error.
- The straddle legs come from the reference book (strike = forward, expiry nearest to 30 days), not from the grid node
  Δ 0.5 (the M and P prototypes both deviate).

### F1 · What a contract costs · P-F1 · 7.0 × 3.9

| Draft | Mark | Design |
|---|---|---|
| M | 5 | One log grey scale for all six maps turns the sell row into a black block with white numbers (the Paper 1 finding on E3: prints as a black block). The anatomy legend has seven entries, of which two are visible in the bar (static discount 0.05 pp, contingencies 0.25 pp). |
| E | 4 | Drawn at 8.54 inches, so 5.7 pt when typeset. The underlying colours in strip c collide with PM2/SM, and the triangles overlap into clumps. |
| P | 8 | PM2 per cell for all three underlyings, grey per row, black numbers easy to read. On the right the strip “÷ PM2” with SM squares, legacy PM diamonds and a median bar. Flawless in grey. |

**Why P.** The statement of F1 is a comparison between managers. P makes it readable on one axis, instead of having
numbers compared across three maps, and still has one number per cell. P is also the only version that shows
ETH and HYPE.

**Requirements.**

- The buy row is called “maker buys (long): capital ≈ premium” in the axis title (pitfall from E and P).
- “← PM2 cheaper →” is ambiguous. Correct is “PM2 cheaper →” to the right of 1 and “SM cheaper ←” to the left of it.
- Unit by rule 6 (“% of notional”). The header above the maps becomes shorter and names the window and the
  parameter state (“pooled over the PM2 window”), because PM2 became about a third cheaper within the window (F5).
- The anatomy from M goes into one line of the caption and into `fig_f1_anatomy.csv`, not into the figure.
- Data from `fig_edge_maps.csv`, maps `pm2`, `sm_pm2win`, `pm_pm2win`, cell value `sum_K / sum_index`. A test checks
  that `fills` and `contracts` per cell are equal in all three maps, otherwise the strip compares different
  fills. The medians per fill from `fig_capital_by_manager.csv` appear only in the CSV.

### F2 · The map in two denominators (H1) · E-F2 with a as small multiples · 7.0 × 3.4

| Draft | Mark | Design |
|---|---|---|
| M | 4 | The κ diagonals are conceptually elegant, but not readable in 5 s. The log-log axes are three quarters empty, and negative edges hang on a floor. Tenor as `cividis` on 3 pt triangles cannot be read in grey. |
| E | 7 | Rank against rank, below it the verdict bar, plus c/d with the mean rank shift by tenor and |Δ| per side. That answers `h1-reading` directly. Minus: underlying colours; the histogram in b needs draws that the inference does not write. |
| P | 4 | Six maps with a diverging scale: the buy row explodes (“11.4k”, “−3.4k”), the sell row is almost white, and both ends are the same in grey. 173 grey rank bands form a bundle of hairlines, and the five “best” cells are framed by the point estimate. |

**Layout.**

- **a** Rank per notional against rank per PM2 capital as three small multiples (BTC, ETH, HYPE, shared axes, pooled
  ranks), ▲ buy hollow, ▼ sell filled, black, diagonal. The small multiples replace the underlying colours
  and show at once whether part of the reordering is a difference in level between underlyings (pitfall from E).
- **b** Verdict bar for ρ by rule 4. A grey histogram only if the inference writes the replications
  (see gaps).
- **c/d** mean rank shift by tenor and by |Δ|, ▲/▼ per side. This is a descriptive transformation of
  `h1_cells.csv`; ρ is not recomputed.

**Requirements.**

- Both axes carry “rank 1 = highest edge”, and the direction is the same on both axes.
- Rank intervals only for the ten largest |rank_shift|, as cross bars; not 173 lines.
- The map in bp of capital (P) goes as a table into `fig_f2_cells.csv`. The text names the best cells with
  their rank intervals. P itself showed why the map does not carry: buy OTM cells have the premium as their
  denominator.

### F3 · The next contract in the book (H2) · P-F3 a ⊕ E-F3 b · 3.4 × 3.6

| Draft | Mark | Design |
|---|---|---|
| M | – | Only described. Idea: ratio split by whether the fill hedges the binding scenario. |
| E | 7 | Histogram with the mass ≤ 0 hatched and overflow counts, below it the forest with the verdict line. Drawn at 3.96 inches, so 6.0 pt; bars > 0 blue. |
| P | 7 | ECDF with four bands in practitioner language and the share per band: one line, robust in greyscale, the median at 0.5 directly readable. b has no x tick labels, and a verdict is missing. |

**Why this combination.** H2 tests a median. The ECDF shows it as the crossing with height 0.5, plus the
shares ≤ 0 and ≤ ½ without counting bars. The forest from E carries the verdict and the sensitivities.

**Requirements.**

- a: x axis from −1 to 2, matching the bins in `fig_h2_dist.csv`, overflows as numbers at the edge. Line black,
  bands in three shades of grey. The title line of the bands is at most two words wide per band.
- b: rows “registered”, “next contract”, “maintenance margin”, “tape book”, then on grey as exploratory the
  accounts M3/M5/M8/M10 (replaces P-b) and, if `hedges_worst` arrives, the idea from M as two rows “hedges binding
  scenario / adds to it”. Row labels at most 18 characters, n within the 3.4 inches.
- Header: “4 accounts, ETH and HYPE only, 20 000 sampled fills” (pitfall from E: no BTC).

### F4 · What netting is worth (H3) · P-F4 b binned ⊕ E-F4 b · 3.4 × 3.6

| Draft | Mark | Design |
|---|---|---|
| M | – | Only described: account rows, plus factor against legs as the mechanism. |
| E | 7 | Histogram stacked by ≤ 63 and > 63 options (counterfactual hatched), forest with the verdict. Drawn at 3.94 inches, so 6.0 pt. |
| P | 6 | b (factor against legs, line at 63) is the mechanism, but as a cloud of 1,943 points that prints as a grey block. P forbids this in its own rules. a with blue boxes per account, no verdict. |

**Layout.**

- **a** K_SM/K_PM2 against option legs (log-log): median per bin as a line with a p25 to p75 band, bins with at least 20
  maker-days. The region to the right of 63 options is lightly hatched and directly labelled: “SM counterfactual:
  1 431 of 1 943 maker-days”. Threshold 2 dashed.
- **b** Forest by rule 4, rejection region to the left of 2. Rows: registered, ≤ 63 options, MM, then on grey: legacy
  PM/PM2 (BTC and ETH legs only, n in the row), accounts under SM and accounts under PM2.

**Requirements.** P's boxes per account go into the CSV. The header names “clusters: UTC days” (pitfall from E).
F3 and F4 have identical panel heights and margins.

### F5 · The engine over time · P-F5 ⊕ status grammar from E · 7.0 × 4.3

| Draft | Mark | Design |
|---|---|---|
| M | 6 | Four panels: the event rail with eight rows on 0.9 inches is cramped, and d needs a panel of its own for the handful of numbers that P fits into b as labels. Drawn at 7.69 inches, so 6.4 pt. Readable in grey. |
| E | 5 | Seven axes, three straddle panels each with an OI strip. The dose labels in a overlap (“0.02”/“0.12”, “1.65”). But E is the only draft that shows the overlapping ±14-day windows. |
| P | 8 | OI strips with PM2 at the bottom (the switch is visible at once), one number per event instead of a panel of its own, directly labelled lines on the right (SM 29.6 %, legacy PM 19.7 %, PM2 10.0 %). Flawless in grey. |

**Requirements.**

- **Error in P-a:** the HYPE strip lacks the SM share (12 to 16 % from June to September 2026).
  `manager_oi_share.csv` has `pm = NaN` for HYPE, and the stack breaks off there. `fillna(0)` before stacking.
- b in the grammar from E: ● in the H4 panel, ◇ kept without a panel cell, ○ dropped. Every row of the
  parameter timeline as a small grey tick (placebo spacing), the ±14-day windows as light grey bars on the
  rail, so that the overlaps in January and in May are visible without covering c.
- Numbers in b in log-% (rule 6). SM rows are dropped; the caption names the SM changes as pure
  perp changes.
- Delete the legend column on the right: a and b get a line above the panel, and c is labelled directly. Then
  the 7.0 inches fit.
- The PM2 event of 2025-06-12/13 appears in b as a grey tick without status (it is missing from `events.csv`).
- The straddle series for ETH and HYPE go into the CSV; their jumps stand as numbers in b.

### F6 · The price of capital (H4) · M-F6 a ⊕ E-F6 a (FWL) ⊕ E-F6 c · 7.0 × 4.2

| Draft | Mark | Design |
|---|---|---|
| M | 7 | The real dose maps (three BTC events with three mechanisms) show the variation that identifies β with day-by-underlying effects: across the cells of one event. No other draft shows it. b and c are squashed, `PuOr` collapses in grey, and the y ticks of the placebo histogram are fractions (2.5, 7.5). |
| E | 6 | The FWL picture (a line with exactly the slope β) is the right form for b, and the checklist above c shows both criteria. But the inference does not estimate β per event in b. Underlying colours; drawn at 7.54 inches. |
| P | 5 | A point cloud with deciles whose slope is not β without the fixed effects; in b the date labels overlap. |

**Layout.** On the left a as 2 × 3 maps as in M (sell on top), on the right b above c.

- **a** Dose per cell in log-%, grey by |dose|, positive doses (only 2026-01-08) hatched, the sign in every
  cell, × under 20 fills. The column titles name the mechanism (M).
- **b** The FWL picture from E: 20 equally populated bins of the residualised quantities, a line with slope β, black,
  axis addition “< 0: capital got cheaper”. **Only with the bins from the inference.** Without them b shows the terciles from
  `fig_h4_events.csv` *without* a β line (E), and the axis says “raw, no fixed effects”.
- **c** Placebo histogram with integer ticks, P95 dashed, β solid black, above it the checklist
  from E in two short lines plus the verdict.

The footnote that β is identified almost only from loosenings stands in the caption; a makes it visible.

### A1 · Does the replica match the chain? · M-A1 a ⊕ P-A1 b · 7.0 × 2.5

| Draft | Mark | Design |
|---|---|---|
| M | 8 | Strips per underlying × manager, median bar, n per row, exact zeros at the margin. |
| E | 5 | IM and MM as double bars double the ink. The footer overlaps the x label of b, which is cut off. |
| P | 7 | b (deviation against legs with “largest miss 0.05 USDC on K up to 19.5 M USDC”) is the best display of the books. In a the median is missing, although the registered threshold is on the median. |

**Requirements.** The margin strip “exact” is labelled (P), the thresholds are labelled directly at the line
(“median bound 0.1 %”, “p95 bound 1 %”), and MM appears only in the CSV. The caption carries the sentence from P:
the replica matches the chain, while the off-chain API computes PM2 with a flat 2 % discount.

---

## 5 · README and X

### GIF of the capital surface

The existing GIF (`BTC_capital_short_2026-08-14_2026-08-27.gif`) shows the problems: 960 × 540, ticks about 9 px,
both surfaces small, unit bp, and the colour bar has visible steps (GIF quantisation of `cividis`).

**Choice.** The concept from P and M: one large 3D surface, PM2 only, in the look of T1. SM appears only as a number in
the corner, because its surface is a single colour (M). Below it the reference straddle with a cursor. The honesty rules
come from E: fixed scale, grey expiries with an old feed instead of interpolation, the badge “stale feed”,
`results/p2/gif_frames.csv`, a static end frame as PNG. For X, E proposes a 2D map. I reject that: the
moving surface is the image by which T1 is recognised, and whatever has to be read at 600 px is in the banner anyway.

- Timing as in M: weekly, plus three daily frames at every kept BTC event with a 1.5 s hold and a banner
  (“20 Aug 2026 · parameter change · grid ±17 % → ±14 % · straddle −23 %”). 4 fps. Daily frames at 12 fps (E)
  flicker, because the market moves the surface every day.
- 1200 × 675 as one master for README and X. Banner and date at least 32 px, axes at least 22 px.
- At most two iso-lines (8 % and 12 %), because contours jump between weekly frames.
- A global 256-colour palette instead of 64 (P), against the steps. For X additionally an MP4 (M: `write_mp4`), because X
  re-encodes GIFs anyway.

### Social cards 1600 × 900

1. **“One short BTC straddle. Three margin engines.”** The M card as the carrier: the three large numbers 30/20/10 %
   with the line pattern below them are the strongest single statement of all the cards. Add the step labels from P at
   the PM2 line (−10 %, −8 %, −23 %) and the line “capital for a hypothetical book, not a balance” (M).
   P card 1 is dropped: the title “cut PM2 capital by 35%” is cut off on the right, and 35 % cannot be checked in the image,
   because the line falls from 14.4 to 10.0, that is by 31 %.
2. **P card 2 (straddle against one leg)** with a more precise title. “Almost free” understates, because the second
   leg lowers the capital. Proposal: “Under PM2 a short straddle needs less capital than one short call.” Both
   bars come from the same reference straddle (legs computed one by one), not from a mix of a grid node and a listed
   expiry.
3. **After H3: P card 3 “PM2 discounts the book, not the contract”**, both bars grey or hatched black,
   because both are ratios and neither is a manager; with interval and n. If H3 does not carry the title, the
   M card 3 replaces it (“One parameter change, one fingerprint”, dose map 2026-08-20 sell side). This card needs
   no hypothesis.

For all cards: font at least 24 px (9 px at 600 px width). Title and axis labels lie
inside 1600 × 900. P card 1 and the keyframe (`social_t1_keyframe.png`, colour bar title) are cut off on the
right. Every number in the title can be read off the image itself.

---

## 6 · Gaps

**The gap that no draft closes: time in F1 and F2.** Both maps pool over the whole PM2 window,
in which the PM2 capital of the reference book fell from 14.4 to 10.0 % (F5). The denominator of H1 thus mixes
parameter regimes. No draft shows this in the figure; only P names it as a pitfall. At the least the header of F1
and F2 names the window. Better would be a column “last 30 days” in `fig_f1_*.csv`, plus a sentence on whether the ranking
of the F1 cells holds across the regimes (descriptive, no new test statistic).

Further gaps, by urgency:

1. **FWL bins for F6b are missing from the inference** (`fig_h4_events.csv` has only terciles with raw means). Without them
   F6 has no line with slope β.
2. **No replication distribution of ρ** (`h1.json` has `stat, lo, hi`, no draws). F2b manages without it,
   but a histogram would be the only form in which one sees the skew of the interval.
3. **Engine helpers are missing from the package:** `figdata_p2.binding_rule` (T1 c/d) and `pm2_scenarios` (T2 c) exist only in the
   prototype `proto_mechanismus.py`. They must move over with a test on the sum (the decomposition matches the
   grid capital exactly at the T1 node).
4. **Single legs of the reference straddle** (`K_<m>_call`, `K_<m>_put`) for T2 c and card 2.
5. **`hedges_worst` in `books.py`** for the mechanism rows in F3 (optional, exploratory).
6. **`figstyle` for Paper 2:** `FS_MIN`, the manager markers (diamond for legacy PM) and the side symbols as constants,
   plus the width and font test from section 2. Today every lens defines its own markers.
7. **The decision on units** “% of notional” and “log-%” (rule 6) must also apply in the text of `main.tex`. The
   caption of F1 in the skeleton still says “USDC” and “each panel on its own scale”, and that of F2 still “lines
   connect the rank of each cell”. Both are replaced.
8. **The event of 2025-06-12/13** is missing from `events.csv` (F5 b).
9. **HYPE in T1, the F1 anatomy and F6a** exists only as CSV. That is intended, but every caption must say so.

---

## 7 · Where I expect a dispute with the referee

- **F2:** The referee might want the practitioner map (bp of capital per cell) in the figure, because it says *where*
  capital earns a return. My answer: not in this colour map. At most a grey map of only the
  sell row is conceivable. The buy row has the premium as its denominator and breaks any scale.
- **F6:** Without FWL bins I would rather leave b empty (only a bar for β with its interval) than lay a line over raw
  terciles.
- **Unit of the dose:** the practitioner will want per cent instead of log-%. In the paper I consider log-% right, because β
  is registered in this unit. The cards show per cent.
- **T1 height of 4.2 inches** is a lot for a figure ahead of the results. Whoever wants to shorten it cuts d, not c.

## Files

- This verdict: `docs/paper2/drafts/jury_design.md`
- Measurement: `data/p2/fig_proto/jury/audit_protos.py`, `data/p2/fig_proto/jury/audit_protos.csv`
