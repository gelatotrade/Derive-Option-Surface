# Figure draft for Paper 2, empirics lens

Status 2026-09-25. Draft for the jury, following the pattern of Paper 1 (`docs/paper1/FIGURE_SELECTION.md`). The lens:
a referee should be able to check each of the four pre-registered verdicts on the figure itself. That takes
estimator, 90 % interval, registered threshold, rejection region, sample size and number of clusters, and it takes them in
the figure itself, not only in the caption.

The prototypes are under `data/p2/fig_proto/empirie/`. The script is `proto_empirie.py`, called as
`python3 data/p2/fig_proto/empirie/proto_empirie.py [T2 F1 F5 A1 F2 F3 F4 F6]`.

| Slot | Prototype | Data |
|---|---|---|
| T2 | `t2_empirie.png`, `fig_t2.csv` | real (`results/p2/semantics/faktoren.csv`) |
| F1 | `f1_empirie.png`, `fig_f1.csv` | real (`capital.parquet` × buckets from `markouts.parquet`) |
| F5 | `f5_empirie.png`, `fig_f5_events.csv` | real (`reference_book.csv`, `manager_oi_share.csv`, `events.csv`, `params/*.json`) |
| A1 | `a1_empirie.png`, `fig_a1.csv` | real (`validation.csv`) |
| F2 | `f2_empirie_SYNTHETIC.png` | real set of cells, **synthetic** edges and bootstrap |
| F3 | `f3_empirie_SYNTHETIC.png` | **synthetic** |
| F4 | `f4_empirie_SYNTHETIC.png` | **synthetic**, only the structural numbers 1,943 and 1,431 come from Addendum 4 |
| F6 | `f6_empirie_SYNTHETIC.png` | **synthetic**, only the list of events comes from `events.csv` |
| T1 | none (existing probe `data/p2/surface/probe_BTC_2026-09-17_pm2_sm.png`) | – |

The synthetic images carry a red watermark “PROTOTYP synthetic placeholder data”. Their numbers are
invented and say nothing about H1 to H4. The prototypes compute no test statistic. The medians, intervals and
ρ in them are placeholders.

---

## 0 · What applies to all figures

**The verdict bar.** The same visual language in F2, F3, F4 and F6, so that a referee reads four verdicts in the same
way:

- Estimator as an open circle, 90 % interval as a thick black bar, registered threshold dashed.
- The rejection region is hatched: for H1 and H2 to the right of the threshold (rejected if the upper bound
  reaches into it), for H3 to the left of it (rejected if the lower bound reaches into it).
- Above it, a line in bold: “registered: 0.18 [0.11, 0.27] → not rejected”. The line applies the registered rule
  to the numbers from `h*.json` and checks whether it matches the field `rejected`. If the two differ,
  the build aborts.
- Right next to it stand n and the number of clusters (UTC days), for H2 and H3 also the number of accounts. This is the
  counterpart of “classes carry their cluster count G” from Paper 1.
- The hatching lies only behind the registered row. An exploratory row that falls into the region is
  not a rejection.

**Registered, sensitivity, exploratory.** In every forest panel the registered row stands at the top, in bold and with a
filled circle. Below it follow the sensitivities named in the addenda (open diamond). Exploratory
splits come last, on a grey background. The pre-registration declares everything except the four tests exploratory
(section “Inference”). The background makes that visible.

**Rules taken over from Paper 1:** CAS widths 3.4 and 7.0 inches, no font below 7 pt (tick labels 7 pt, kept
everywhere in the prototypes), colour always double-coded (managers: PM2 blue, solid, circle; SM orange,
dashed, square; legacy PM green, dotted, triangle; underlying: colour plus marker shape). One number per cell,
cells under 200 fills as an empty cross. No second y axis, no bundles of hairlines. Only T1 is 3D. The
manager palette `#0072B2/#D55E00/#009E73` passed the palette validator (deutan ΔE of the worst
neighbours 11.0). Greyscale was checked on the F5 prototype: after the correction SM is light with dots, legacy PM
medium with hatching and PM2 dark, with a black boundary line in between.

**Data contract with `inference_p2.py`.** The figures recompute no test statistic. While this draft
was being written, the parallel inference wrote its files under `results/p2/`. The table assigns them to the
slots. Only column names and keys were read for this, no values.

| Slot | reads (available) | still missing |
|---|---|---|
| F1 | `fig_edge_maps.csv` with `map ∈ {sm_pm2win, pm_pm2win, pm2}`: cell size = `sum_K / sum_index` (ratio of sums as in the prototype), `fills`, `occupied`. Alternatively `fig_capital_by_manager.csv` (`window = pm2`, median and p25/p75 of K/index per cell) | Decision: ratio of sums (matches e^K and the H1 denominator) or median (robust against single fills). The prototype takes the sums. Both numbers in one figure would be a second unit and are therefore ruled out |
| F2 | `h1.json` (`stat, lo, hi, rejected, threshold, n, n_days, b, cells_present_min, cells_present_median, cells_by_ccy`), `h1_cells.csv` or `fig_edge_maps.csv` `map = pm2` (`A_bp, B_bp, rank_A, rank_B, rank_shift`, plus rank intervals `rank_*_lo/hi`) | the distribution of the 9,999 ρ replications (a histogram is enough). Without it F2b shows only the bar and the interval. The rank intervals allow error crosses in F2a for the ten largest shifts |
| F3 | `h2.json` (`stat, lo, hi, rejected, threshold, n, n_days, n_sample, n_excluded, share_nonpositive, accounts, fills_by_ccy`), `fig_h2_dist.csv` (`kind = hist/quantile/share_le_0/n` per `variant`), `sens_h2.csv` (forest rows: `ratio_unit, ratio_tape, ratio_mm`, per account, per underlying) | nothing. The overflow counts should be a `kind` of their own in `fig_h2_dist.csv` if the histogram limits do not cover the window [−2, 3] |
| F4 | `h3.json` (`stat, lo, hi, rejected, threshold, n, n_days, n_excluded, n_not_applicable, share_days_over_63_options`), `fig_h3_series.csv` (per maker-day `ratio_sm_pm2`, `over_63_options`: the histogram is descriptive binning in the figure layer), `sens_h3.csv` (`sm_pm2_le63`, `sm_pm2_gt63`, `sm_pm2_mm`, `pm_pm2_be`, per account) | nothing |
| F5 | `events.csv`, `fig_h4_events.csv` (`n_cells, n_pre, n_post, median_dose` per event), `params/*.json`, `reference_book.csv`, `manager_oi_share.csv` | nothing |
| F6 | `h4.json` (`stat, lo, hi, p, p_sided, clusters, fills, events_kept, cell_events, criteria.{beta_positive, p_le_alpha, beta_gt_placebo_p95}, placebo.{p95, share_ge_beta}`), `h4_placebo.csv` (`rep, beta`), `sensitivity_h4.json` (`by_ccy.*`, `no_outlier_cells.*`), `fig_h4_events.csv` (dose terciles `t1..t3` with `y_pre, y_post` per event) | **the residualised FWL bins** (`x_mean, y_mean, n_fills` in 20 bins). Without them F6a becomes the tercile display from `fig_h4_events.csv`: change in the half spread (post − pre) per dose tercile and event. That is honest, but raw and without fixed effects, and the axis must say so. There is no β per event. F6b therefore shows β per underlying and without outlier cells from `sensitivity_h4.json`, on grey as exploratory |
| A1 | `validation.csv`, `validation_summary.json` | optionally the feed age of the test population (from `capital.parquet`, descriptive) |

The key figures of the verdict bars (`stat, lo, hi, threshold, rejected, n, n_days`) have the same names in `h1.json` to
`h4.json`. `figures_p2.py` can therefore use a single function `ruler(ax, h)` for all four tests.
It checks `rejected` against the rule in `rule`, so that figure and numbers sheet do not drift apart.

**Check script** (`scripts/p2_figure_check.py`, pattern of Paper 1): it compares every key figure printed in the figure with
`h*.json`. It counts whether F1 shows exactly as many crosses as the cell table has cells under 200 fills
(including combinations without a single fill). It also checks whether F5 shows filled exactly the events with `kept`
that `events.csv` lists, and whether the verdict line agrees with `rejected`.

---

## T1 · The engine's view of the surface

- **Purpose.** The figure shows that capital is a property of the surface that the engine itself
  sees, computed at the same block with the same feeds.
- **Data source.** `p2surface.capital_grid` for BTC at the block of `results/p2/surface_t1.json` (probe:
  2026-09-17 08:00 UTC, 15 expiries), short side, managers PM2 and SM. The grid comes along as `fig_t1.csv`
  (`manager, delta, tenor_days, iv, K, K_per_forward_bp`, like `probe_BTC_2026-09-17_grid.csv`).
- **Coding.** Two 3D panels side by side. Height is IV in per cent, colour is capital in bp of the
  forward on **one** common scale with `cividis` (monotone in greyscale), plus a colour bar. The
  additions of the empirics lens:
  1. Iso-capital contours projected onto the floor, labelled in 7 pt. The quantity then carries without colour too.
  2. On the floor the bucket edges of Paper 1: call delta 0.10/0.25/0.40/0.60/0.75/0.90 (the |Δ| buckets lie
     symmetrically on the call-delta axis) and tenor 2/7/30/90 days. This way T1 leads straight to F1 and F2.
  3. Grid points outside the quoted strikes (wings beyond `WING_PAD`) turn grey
     (`NA_COLOR`) instead of being extrapolated.
  4. In the header: block, UTC time, number of expiries and, per panel, min/median/max of K. Probe: PM2 342/1,045/1,370 bp,
     SM 1,237/1,298/1,501 bp.
- **Size.** 7.0 × 3.0 inches. The only 3D figure.
- **Core message in 5 s.** Under SM the surface is almost a single colour: a short costs about 13 % of the forward everywhere.
  Under PM2 the price depends on delta and tenor.
- **Pitfalls.** Height is vol and not capital; the z axis label must say so explicitly. The
  back of the surface is hidden, hence the floor contours. The almost single-coloured SM surface easily looks like
  “no information”, but it is the finding. The figure shows only shorts. For maker buys K is essentially
  the premium (under SM there is no credit for longs); that belongs in the caption. A single block is
  a snapshot; time is carried by F5.

## T2 · What `get_margin` returns

- **Purpose.** The figure shows why `C − net` is not a requirement, and that the contradiction 11 against 1.2 arises from
  book and valuation.
- **Data source.** `results/p2/semantics/faktoren.csv`, rows `historisch 17.09.` (`b17_exakt`) and `historisch
  24.09. … (H1_…)` (`b24`), cases A and B. Columns `SM_Cnet, PM2_Cnet, SM_R_engine, PM2_R_engine, V_und_SM,
  V_PM2, F_Cnet, F_R_engine`. The H0 variant stays out (as in `MANUSCRIPT.md` 3a).
- **Coding.** Panel a is a dot plot on a logarithmic USDC axis, one row per book and manager. The
  filled marker stands for R, the open one for `C − net = R − V`, and the grey connection is V. Managers by colour
  and shape. Panel b shows the ratios SM/PM2 per book, filled on R and open on `C − net`, plus the
  H3 threshold 2 dashed. The four number pairs of the caption stand directly at the points.
- **Size.** 7.0 × 2.6 inches.
- **Core message in 5 s.** For the book of 24 Sep (case B), `C − net` under PM2 is six times higher than R, because
  V = −496,859 USDC slips into it. On R all four books lie above 2, on `C − net` two lie below.
- **Pitfalls.** The probe books are constructed and are not maker books; they must not be read as a preview of
  H3. The caption must say that the threshold 2 was derived from these books
  (pre-registration, “data status before this commit”). A log axis is needed, because R lies between 17 k and
  644 k. The prototype says so in the axis label.

## F1 · Capital per contract by manager

- **Purpose.** The figure shows what a single contract costs per manager over |Δ| × tenor, and makes the
  statement in the text “SM/PM2 runs from … to …” checkable for all three underlyings.
- **Data source.** `data/p2/derived/capital.parquet` (`K_sm, K_pm, K_pm2, amount, index_price, maker_side, ts`),
  joined on `trade_id` with `delta_bucket, tenor_bucket` from `data/p1/derived/markouts.parquet`. Filter: the
  PM2 window per underlying, so that all managers see the same fills. The cell size is the ratio of sums
  100·Σ K·a / Σ index·a in per cent of the index, like the edge in the paper. Occupied from 200 fills. In the final version the
  figure reads `results/p2/fig_edge_maps.csv` (`sum_K / sum_index` of the maps `sm_pm2win`, `pm_pm2win`, `pm2`), provided
  `sum_K` is quantity-weighted as here. The check script compares with the prototype computation. The prototype writes `fig_f1.csv` (210 rows, all
  underlyings, both sides).
- **Coding.** Panels a and b are heatmaps for BTC: maker buys on top, maker sells below, columns SM, legacy PM
  and PM2. Each cell holds one number with two significant digits. The shading is logarithmic and
  shared within a row, so that managers are comparable within one side. Cells under 200 fills
  show ×. The number of fills is in the y label. Panel c is a strip of all 173 occupied cells
  of all underlyings: x is the ratio on a logarithmic axis, filled SM/PM2, open legacy PM/PM2, triangle
  pointing up for buy and down for sell, colour by underlying. Minimum and maximum stand in the header.
- **Size.** 7.0 × 3.9 inches.
- **Core message in 5 s** (pilot data, descriptive, no test). For a **single** contract PM2 is not
  cheaper than SM. Across 173 occupied cells SM/PM2 lies between 0.75 and 4.67, and below 1 in 86 cells. The
  legacy PM is the dearest for sells (legacy PM/PM2 0.95 to 1.74). The netting advantage of PM2 can therefore
  arise only in the book, and that is exactly what F3 and F4 test.
- **Pitfalls.**
  - For buys K is almost the premium. The upper row is therefore a premium map and not a margin map.
    That must go into the axis title, not only into the caption.
  - ETH and HYPE appear only in the strip and in the CSV. Whoever expects HYPE maps (25 of 70 HYPE cells under
    200 fills) finds them there.
  - The caption in the skeleton says “each panel is shaded on its own scale”. For a comparison of managers that is
    wrong; the scale must be shared within each row.
  - The maximum of 4.67 comes from a single ETH buy cell. Besides min/max the text should also give the median of the
    cell ratios.

## F2 · The map in two denominators (H1)

- **Purpose.** The figure shows the quantity that H1 tests (Spearman ρ of the cell ranks) with its 90 % interval
  against the threshold 0.5, and where the reordering takes place.
- **Data source.** `results/p2/h1.json` and `h1_cells.csv` (cell values under both denominators `A_bp`, `B_bp`, ranks with
  intervals), plus the still missing bootstrap distribution of ρ (see data contract). Set of cells: all occupied cells in the PM2 window (prototype count 173). Ranks and
  mean rank shift are descriptive transformations of the table. The figure may form them from
  `h1_cells.csv`, but not ρ and its interval.
- **Coding.**
  - Panel a: rank-rank scatter, one mark per cell. The x axis is the rank per notional, the y axis the
    rank per PM2 capital, plus the diagonal. Underlying by shape and colour, side by fill (solid = sell).
  - Panel b: the verdict bar for ρ above the grey histogram of the 9,999 replications, with threshold 0.5 and a
    hatched rejection region. The axis line gives the number of cells and the clusters.
  - Panels c and d: mean rank shift (rank PM2 − rank notional) by tenor and by |Δ|, split by
    side. This is the basis for the sentence `h1-reading` (“does the reordering run along tenor, delta or
    side?”).
- **Size.** 7.0 × 3.2 inches.
- **Core message in 5 s.** If the points lie on the diagonal, the denominator reorders nothing. The bar shows
  in bold whether the upper bound reaches 0.5 (H1 rejected) and in which dimension the map shifts.
- **Pitfalls.**
  - The caption in the skeleton describes “lines connect the rank of each cell”. That would be 173 hairlines, which
    Paper 1 explicitly ruled out. The rank-rank scatter shows the same information as an object.
  - ρ mixes three underlyings. Part of the reordering can be a difference in level between the underlyings
    rather than one within an underlying. The shapes must keep that recognisable. An exploratory
    row “ρ within the underlyings” in `h1.json` would be good.
  - In the bootstrap, cells drop out when a replication has no fill. The number of cells per replication
    varies, and the range (`n_cells_min_rep` to `n_cells_max_rep`) belongs in the axis line.
  - 20 fills with K_PM2 ≤ 0 stay in the sums (Addendum 4). A cell with a small total capital can become
    extreme. The rank protects ρ from this, a map in bp does not. That is why F2 shows no bp heatmap;
    the values are in `h1_cells.csv`.

## F3 · The next contract in the book of a dominant maker (H2)

- **Purpose.** The figure shows the distribution of ratio = (ΔK/quantity)/K_PM2,single and the registered verdict
  with its sensitivities.
- **Data source.** `results/p2/h2.json`, `fig_h2_dist.csv`, `sens_h2.csv`. The rows come from
  `data/p2/derived/marginal.parquet` (columns `ratio`, `ratio_unit`, `ratio_mm`, `ratio_tape`, `label`,
  `manager`, `day`). Structure according to the file: 20,000 fills from four accounts (M3, M5, M8, M10) on 372 UTC days, 13,595
  under PM2:ETH and 6,405 under PM2:HYPE.
- **Coding.** Single column with two panels.
  - Panel a: histogram in the window [−2, 3]. The part ≤ 0 (releases capital) is hatched grey, the part > 0
    blue. The threshold 0.5 is dashed, the mark 1 (“as expensive as alone”) dotted, the median a triangle
    at the top edge. The overflows stand as numbers at the edges (“89 beyond 3 →”), the share ≤ 0 at top left.
  - Panel b: forest with the verdict bar. At the top the registered row (IM, whole fill), below it the
    sensitivities from Addendum 4 (next single contract, MM, tape book) and, exploratory, PM2:ETH against
    PM2:HYPE. The header gives accounts, days and exclusions (1 fill with K_single ≤ 0).
- **Size.** 3.4 × 3.7 inches. The skeleton plans 3.4 × 2.4, but without the forest panel the robustness of the
  verdict cannot be seen. Alternative: F3 and F4 as one `figure*` of 7.0 × 2.8 inches, four panels side by side,
  with an identical verdict grammar (the slot count stays at 9 if F4 goes into the same float for it).
- **Core message in 5 s.** What share of the fills releases capital, where the median stands against 0.5, and whether
  any sensitivity flips the verdict.
- **Pitfalls.**
  - The H2 population contains **no BTC**: the four PM2 accounts run under PM2:ETH and PM2:HYPE. That belongs in
    the figure header, otherwise one reads H2 as a statement about all three underlyings.
  - The sample of 20,000 is a random draw (seed 20260924). `sampled` from `h2.json` belongs in the
    header.
  - K_single can be tiny for contracts far out of the money, and then ratio explodes. The window
    [−2, 3] must not swallow anything, hence the overflow counts.
  - Four accounts are few. A single account can carry the median. The split by account belongs at least in
    the CSV, and it goes into the forest if it yields more than one row without making single accounts recognisable.

## F4 · What netting is worth (H3)

- **Purpose.** The figure shows K_SM/K_PM2 over maker-days on a logarithmic axis, with the registered
  verdict (lower bound against 2) and the warning from Addendum 4 that K_SM is counterfactual on most
  days.
- **Data source.** `results/p2/h3.json`, `fig_h3_series.csv`, `sens_h3.csv`. The rows come from
  `data/p2/derived/maker_days.parquet` (`K_sm`, `K_pm2`, `K_pm`, `K_*_mm`, `n_legs`, `manager`, `status`, `label`).
  Structure: 1,943 maker-days, 1,431 of them with more than 63 options (Addendum 4). Accounts under SM, PM:BTC, PM:ETH,
  PM2:ETH and PM2:HYPE.
- **Coding.**
  - Panel a: histogram on a logarithmic x axis (ticks 0.5 to 64, equal width per doubling), stacked
    by ≤ 63 options (blue) and > 63 options (“SM counterfactual”, hatched grey). Threshold 2 dashed,
    1 dotted, median as a triangle.
  - Panel b: forest with the verdict bar, rejection region to the left of 2. Rows: registered, only days with
    ≤ 63 options, MM, plus, exploratory, legacy PM/PM2 (BTC and ETH legs) and splits by the manager
    of the account.
- **Size.** 3.4 × 3.7 inches (or together with F3, see there).
- **Core message in 5 s.** How much capital PM2 saves against SM on real books, and whether the verdict holds when
  one takes only the days on which an SM account would be allowed to hold the book at all.
- **Pitfalls.**
  - On 74 % of the days the book would not be admissible under SM at all. Without the stacking the referee reads a
    netting factor that is partly an account limit.
  - A ratio needs a log axis, otherwise 0.5 looks closer to 1 than 2 does.
  - Maker-days of the same account are correlated. According to the pre-registration the clusters are UTC days and not
    accounts. That belongs in the header, so that nobody assumes account clusters.
  - The legacy PM row lacks HYPE legs. Its n is therefore smaller, and that must be stated in the row.

## F5 · The engine over time

- **Purpose.** The figure makes the H4 event selection checkable: which parameter changes there were, which ones the
  rules keep (combination per day, dose filter 1 %, 20 fills per side), how large they are for a fixed book
  and whether the changed manager carried any open interest at the time.
- **Data source.** `results/p2/events.csv` (`kept, max_abs_dose, panel_cells, panel_fills_pre/post`),
  `results/p2/params/{CCY}_{pm,pm2}.json` (every row of the timeline, hence the spacing rule of the placebos),
  `results/p2/reference_book.csv` (`K_sm, K_pm, K_pm2, forward`; `K_*_prev` for the pure parameter jump),
  `results/p2/manager_oi_share.csv`.
- **Coding.**
  - Panel a: event tracks, one row each for BTC legacy PM, BTC PM2, ETH legacy PM, ETH PM2 and HYPE PM2.
    ● means “enters the H4 panel”, ◇ “kept, but no cell with 20 fills per side” (HYPE 2026-01-08),
    ○ “dropped, max |dose| below 0.01”. The label is max |dose|. Small grey ticks mark every
    row of the timeline, collateral changes included, because these count for the placebo spacing.
  - Panel b: per underlying the K of the reference book (short straddle at the money, 30 days, 08:00 UTC) in per cent of the forward
    per manager (line style plus colour). Below it a narrow strip with the OI share per manager. The ±14-day
    windows of the H4 events are shaded grey, and overlaps appear darker.
  - One shared calendar axis from 2024-01 to 2026-09.
- **Size.** 7.0 × 4.6 inches (Paper 1 F6 had 4.2).
- **Core message in 5 s** (pilot data). 14 of 18 events are kept, 13 enter the panel. Almost every kept
  change makes capital cheaper. On the reference book 11 of 14 lower the capital; the three exceptions are the
  changes of 2026-01-08 (+1.5 to +1.6 %). The largest jump is PM2 BTC on 2026-08-20 with −23 %, HYPE on
  2026-05-24 with −31 %. The dose therefore varies almost only in one direction.
- **Pitfalls.**
  - **The windows overlap**: 2026-01-08 and 2026-01-23 (BTC, ETH, 15 days apart) as well as 2026-05-08 and 2026-05-24
    (HYPE, 16 days). The post window of the first event is the pre window of the second, and the same fills
    enter two (cell, event) groups. The pre-registration does not forbid this, but the figure must
    show it, and the text should mention it.
  - The reference book is not the dose. The dose is cell-specific; the book only illustrates.
  - The line of the legacy PM runs on until 09/2026, although its OI share is zero from 03/2026. In the final version
    the line should become thin where the manager carries less than 5 % of the OI.
  - In the prototype the labels in the HYPE strip sit too close to the ETH ticks. In the final version the
    track needs more line spacing.

## F6 · The price of capital (H4)

- **Purpose.** The figure shows β in such a way that one can see its slope, and both registered criteria
  (wild p and placebo P95) side by side.
- **Data source.** `results/p2/h4.json`, `h4_placebo.csv`, `sensitivity_h4.json`, `fig_h4_events.csv`, plus the
  still missing FWL bins (see data contract).
  The panel is `data/p2/derived/h4_panel.parquet` (91,446 fills, `dose, post, y_hs_bp, cell, event_id, day`), and the
  doses come from `results/p2/h4_doses.csv`.
- **Coding.**
  - Panel a: partial regression plot (Frisch-Waugh-Lovell). The x axis shows post × dose, the y axis the
    half spread in bp of the index, both residualised on α_{cell,event} and γ_{day,underlying}, in 20 equally
    populated bins. The marker area is proportional to the number of fills. The line has exactly the slope β. This way
    a referee sees whether a single bin carries β. Axis addition: “< 0: capital got cheaper”.
  - Panel b (exploratory, on grey): β per underlying and β without outlier cells from `sensitivity_h4.json`,
    each with 90 % interval and cluster count, the registered estimate as a vertical line. The prototype
    shows β per event. The inference does not estimate that; it would be an additional request.
  - Panel c: histogram of the 100 placebo β, P95 dashed, β as a thick line. Above it the checklist in bold:
    “one-sided wild p = … ≤ 0.05: met / not met”, “β > placebo P95: met / not met”, “H4 rejected / not rejected”.
- **Size.** 7.0 × 3.0 inches.
- **Core message in 5 s.** Whether the half spread falls with the change in capital, and whether both criteria are met.
  H4 needs both, and the checklist shows on which one it fails, if it does.
- **Pitfalls.**
  - Sign: the dose is log(K_after/K_before), negative means cheaper. H4 predicts β > 0 (cheaper capital
    leads to a smaller half spread). Without a hint on the axis one reads it the wrong way round.
  - A raw binscatter of y against the dose without the fixed effects does not have the slope β. Only the
    residualised bins from the inference are admissible. The tercile fallback from `fig_h4_events.csv` must not carry a
    line with slope β (see data contract).
  - Because of F5, almost all doses run in one direction (loosenings). β is identified on the side x < 0; the
    bins show that honestly, and the text should say it.
  - The placebos borrow the dose vectors of real events. A distribution that is not centred on zero is
    a hint of seasonality and not an error of the figure.
  - Under the Paper 1 rule, the p-value stands next to the placebo position. Both belong in panel c, not in the
    caption.

## A1 · Does the replica agree with the chain?

- **Purpose.** The figure shows the pre-registered validation per underlying and manager against the thresholds
  (median < 0.1 %, p95 < 1 %) with all case counts.
- **Data source.** `results/p2/validation.csv` (`kind, ccy, manager, is_initial, rel_err, n_legs, book, status`),
  key figures per cell from `results/p2/validation_summary.json`. 2 cases with `status = revert` stay out and
  are counted.
- **Coding.**
  - Panel a: single contracts, one row per underlying and manager. IM on top (strong), MM below (pale). Bar
    p25 to p75, whiskers min to max, black bar for the median, diamond for p95 (filled IM, open MM). The
    x axis is log |rel| from 1e−13 to 1e−1. Exact zeros lie in a grey strip “exact” at the left edge
    (359 of the single cases are bit-identical). The thresholds are dashed, n stands on the right.
  - Panel b: books. The x axis shows the legs (log), the y axis |rel| (log), shape and colour per manager, IM
    filled, MM open. In the axis label: 20 maker-days, books per underlying BTC 7, ETH 18, HYPE 1.
- **Size.** 7.0 × 2.8 inches.
- **Core message in 5 s** (real). The medians per cell are at most 9e−9, the largest single deviation
  1.9e−7 (MM), so at least four decades below the thresholds. The error does not grow with the size of the book (2 to 245 legs).
- **Pitfalls.**
  - The validation blocks require fresh feeds (vol push at most 20 min, forward at most 1 h old,
    `VALIDATION.md`), the test population does not. A1 vouches for the engine, not for the feed assignment with old feeds.
    Proposal: a panel c with the distribution of feed age (`vol_age` in `capital.parquet`) of the
    test population next to the validation selection, or a sentence in the caption.
  - For HYPE the books row rests on **one** book. The n must be in the figure (it is in the axis label).
  - A log axis over twelve decades makes 1e−8 and 1e−2 look close. The thresholds need a
    label directly at the line.

---

## README and X

### GIF: the capital surface over time

- **Content.** BTC, short side, PM2. The capital surface as a **2D heatmap** over call delta × tenor (log), not
  in 3D: on X the GIF is shrunk to about 600 px, and a 3D surface with occlusion is not readable there.
  The 3D version (like `data/p2/surface/BTC_capital_short_2026-08-14_2026-08-27.gif`) stays for the README.
- **Time.** Daily frames at 08:00 UTC from 2025-06-13 to 2026-09-17, every third day (about 155 frames), 12 fps.
  At every H4 event the animation pauses for one second, with the overlay “Parameter change 20 Aug 2026: grid ±17 %
  → ±14 % · reference book −23 %” from `events.csv` and `reference_book.csv`.
- **Lower strip.** The time series of the reference book (PM2 solid, SM dashed) with a cursor and
  event marks in the style of F5 (● in the panel, ◇, ○). That is `p2surface._draw_series`.
- **Honesty.** One fixed colour scale over all frames (`p2surface.fit_limits`). Every frame shows date and
  block. Expiries without a fresh feed appear grey (`NA_COLOR`) and are not interpolated. A badge
  “stale feed” appears when a feed is older than one day. The values of all frames are in
  `results/p2/gif_frames.csv` (date, block, number of expiries, K min/median/max).
- **Format.** 1200 × 675 px, under 8 MB (X allows 15 MB, GitHub renders large GIFs slowly), plus a
  static end frame as PNG for readers without animation.

### Social cards (1600 × 900 px)

Shared rules: one message per card, one large number with interval and n, font at least 28 px (still 10 px at
600 px width), source and pre-registration commit in the footer, colour double-coded as in the
paper. Numbers only from `results/p2/`. While the tests are running, the cards on H1 to H4 carry placeholders.

1. **“One contract, three price tags”** (from F1, real data). The BTC short heatmap under PM2, next to it the
   ratio strip. Large number: the range of SM/PM2 over the occupied cells. Subline: “for a single
   contract PM2 is not cheaper than SM, netting is where it pays”. The subline holds only if F3 and F4
   carry it; otherwise it is dropped.
2. **“What the next contract costs”** (H2 and H3). Two verdict bars one above the other, the median of ΔK/K_single and
   the median of K_SM/K_PM2, each with interval, threshold and “pre-registered · rejected/not rejected”.
3. **“The engine got cheaper, did spreads follow?”** (F5 and F6). On the left the reference book line BTC PM2 with the
   jumps (−23 % on 2026-08-20), on the right β with the placebo distribution and the checklist. This card comes only
   once H4 has been evaluated.

---

## Open questions to the jury and to the inference

1. Should F2 get the rank-rank display (empirics) instead of the connecting lines from the skeleton? I recommend
   yes, because of the hairline rule from Paper 1.
2. F3 and F4 as one shared `figure*` (7.0 × 2.8) or two single-column ones (3.4 × 3.7)? The shared float
   makes the verdict grammar comparable and saves a float position.
3. Can `inference_p2.py` still write the FWL bins for F6a and the replication distribution of ρ for F2b? Without
   them F6a falls back on the raw dose terciles and F2b on the bare bar, and the figure layer must not recompute
   either.
4. The overlapping H4 windows (January, May) must be mentioned in the text. The figure already shows them.
