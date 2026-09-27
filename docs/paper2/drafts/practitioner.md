# Figure draft for Paper 2, practitioner lens

Status 2026-09-25. Draft for the jury, following the pattern of Paper 1 (`docs/paper1/FIGURE_SELECTION.md`). The lens is
a market maker or bot developer on Derive. They want to know three things: where on the surface capital earns a good
return, what the next contract in their book costs, and how much PM2 saves against SM. Every figure
answers exactly one question that they ask before the next quote.

The prototypes are under `data/p2/fig_proto/praktiker/`. The code is in `proto_praktiker.py` next to them, and every number
of a prototype is also in a `fig_*.csv`. Where H1 to H4 deliver results, the values are **synthetic** (stamp
PROTOTYP, tables with the suffix `_SYNTHETIC`). Hypothesis statistics were not computed. Real numbers come from
the pilot cut of 2026-09-17.

## Overview

| Slot | The practitioner's question | Width × height | Prototype | Data |
|---|---|---|---|---|
| T1 | What does a short bind today, point by point on the surface? | 7.0 × 3.1 in | `t1_praktiker.png` | real |
| T2 | How do I read `get_margin` correctly? | 7.0 × 2.5 in | `t2_praktiker.png` | real |
| F1 | What does a naked contract cost per cell, and is PM2 cheaper for it? | 7.0 × 3.9 in | `f1_praktiker.png` | real |
| F2 | Where does capital earn the best return? (H1) | 7.0 × 3.9 in | `f2_praktiker.png` | synthetic |
| F3 | What does the next contract in my book cost? (H2) | 3.4 × 3.3 in | `f3_praktiker.png` | synthetic |
| F4 | How much does PM2 save on a real book, and from which book size on? (H3) | 3.4 × 4.0 in | `f4_praktiker.png` | synthetic, accounts and leg counts real |
| F5 | How has the price of capital changed? | 7.0 × 4.4 in | `f5_praktiker.png` | real |
| F6 | Does the spread follow the price of capital? (H4) | 7.0 × 2.7 in | `f6_praktiker.png` | synthetic |
| A1 | Can I let the offline replica compute instead of the chain? | 7.0 × 2.6 in | `a1_praktiker.png` | real |

The order gives the practitioner a reading line. T1 and F1 show the price of a contract, F2 the return
on it. F3 and F4 show that the book is cheaper than the sum of its contracts. F5 and F6 show that the price
moves and whether the market reacts to it. A1 answers whether the tool can be trusted.

**Finding from the real data that carries the lens** (exploratory, not a hypothesis): for a single short
PM2 is *not* cheaper than SM. Over the 173 occupied cells of the PM2 window, SM ÷ PM2 for maker sells has a
median of 0.94 (BTC), 0.90 (ETH) and 0.88 (HYPE). In 74 % of the sell cells SM even needs less. The
legacy PM needs 1.38 and 1.35 times as much. On the same morning (2026-09-17, 08:00 UTC) a short ATM call with
22 days binds 11.9 % of the forward under PM2, and the whole short straddle only 10.0 %. Under SM it is 14.3 % and 29.6 %.
So PM2 does not lower the price of the single contract, but that of the book. That is exactly what H2 and H3 test, and the
figures should carry this contrast.

## Rules that apply to all slots

- CAS widths 3.4 and 7.0 inches, no font below 7 pt, colours only from `figstyle.PALETTE`.
- Fixed manager coding, carried out threefold: PM2 blue, solid, circle; SM orange, dashed, square
  or hatched; legacy PM green, dotted, diamond. The palette passes the colour vision test (`validate_palette.js`,
  worst pair deutan ΔE 11.0), but still always carries a line style or symbol.
- Capital in **% of the index or forward** (that is how a maker computes margin), edge in **bp of capital** (as
  pre-registered). A contract is always called “one contract”, never “1 BTC”.
- Maps: one number per cell. Cells under 200 fills get an empty cross. Negatives are additionally hatched.
  Frames only for a highlight defined in advance.
- Every number of the figure also goes into `results/p2/fig_<slot>.csv`. For now the prototypes write them to
  `data/p2/fig_proto/praktiker/fig_*.csv`.
- Distributions never as a coloured point cloud of thousands of points: ECDF, quantile bars or bins.

## Data contract with the inference (status of the files 2026-09-25, 01:46)

While this draft was being written, `inference_p2` wrote the tables below. Only column names and
categories were read, no result values. The prototypes stay synthetic. The final figures read:

| Slot | File | Columns the figure needs | Gap |
|---|---|---|---|
| F1 | `fig_capital_by_manager.csv` | `window == "pm2"`, `manager, ccy, side, delta_bucket, tenor_bucket, fills, median_k_over_index` | the ratios SM ÷ PM2 and legacy ÷ PM2 as a ratio of sums on the same fills are missing (`sum_K_sm, sum_K_pm, sum_K_pm2, sum_index`) |
| F2 | `h1.json`, `fig_edge_maps.csv` or `h1_cells.csv` | `stat, lo, hi, rejected, threshold`; per cell `map == "pm2"`, `occupied, A_bp, B_bp, rank_A, rank_B, rank_B_lo, rank_B_hi, fills_k_le_0` | none (A = notional, B = PM2 capital, name them so in the code) |
| F3 | `h2.json`, `fig_h2_dist.csv` | `stat, lo, hi, n, n_excluded, share_nonpositive`; `label ∈ {all, M3, M5, M8, M10}`, `variant == "ratio"`, `kind ∈ {hist, quantile, share_le_0, n}`, bins of 0.05 from −1 to 2 with overflow classes | none: the bin edges include 0, ½ and 1, and the band shares follow exactly from the cumulative histogram. x axis from −1 to 2 instead of −1.5 to 2.5 as in the prototype |
| F4 | `h3.json`, `fig_h3_series.csv` | `stat, lo, hi, days_over_63_options`; per maker-day `label, day, status, n_legs, over_63_options, ratio_sm_pm2, ratio_pm_pm2_be` | none (`_be` = BTC and ETH legs only, label it so) |
| F5 | `manager_oi_share.csv`, `events.csv`, `reference_book.csv`, `fig_h4_events.csv` (column `kept`) | as above | the event of 2025-06-12/13 is missing from `events.csv` |
| F6 | `h4.json`, `h4_placebo.csv`, `fig_h4_events.csv` | `stat, p, placebo.p95, placebo.share_ge_beta, criteria.*`; `beta` of the 100 replications; per event `t{1,2,3}_median_dose, t{k}_y_pre, t{k}_y_post, t{k}_n_*` | panel a needs residuals per cell-event pair after α and γ. `fig_h4_events.csv` delivers only terciles per event with raw means. A workable fallback: 13 events × 3 dose terciles = 39 points, x = tercile median of the dose, y = `y_post − y_pre`. The β line is then comparable only as a direction, because the fixed effects are missing |
| A1 | `validation.csv` | as above | none |

---

## T1: The engine's view of the surface

- **Purpose:** show what capital a single short binds today at every point of the BTC surface, under PM2
  and under SM on the same scale.
- **Data:** `p2surface.capital_grid` at one block (prototype: `data/p2/surface/probe_BTC_2026-09-17_grid.csv`,
  2026-09-17 08:00 UTC). Columns `manager, delta, tenor_days, iv, K_per_forward_bp`, filter `side == short`,
  managers `pm2` and `sm`. Final as `results/p2/fig_t1.csv` with block, grid and K per node (the file
  `surface_t1.json` from `MANUSCRIPT.md` can be folded into it).
- **Coding:** two 3D panels side by side. x = call delta (put = Δ − 1), y = days to expiry (log), z = IV in
  %, colour = capital per short contract in % of the forward on a common scale (cividis, 3 to 15.5 %). Black
  **iso-lines of equal capital** at 4, 6, …, 14 % lie on the surface and are labelled. They carry the
  number in greyscale and make the figure readable without having to compare colours. Panel titles with the
  practitioner's headline number: “PM2: ATM 30 d short = 11.8 % of fwd” and “SM: 14.1 %”. This is the only
  3D figure in the PDF.
- **Size:** 7.0 × 3.1 in.
- **Core message (5 s):** Under SM every short costs almost the same (12 to 15 % of the forward, a flat yellow surface).
  Under PM2 the price depends strongly on the location: short tenors near the money are expensive, long wings cheap
  (3.4 to 13.7 %).
- **Pitfalls:**
  - The 3D view hides the back. Fix the viewing angle (elev 24, azim −128) and keep it the same in both panels.
    The ATM 30-day node must be visible (hidden in the prototype; in the final version as a label on the iso-line).
  - The node price is the Black-76 mark with D = 1, not a fill price. The label must say “at mark”.
  - Chain semantics. The off-chain API computes PM2 with a flat 2 % discount. For a bot that quotes against the API
    the number deviates by up to 3 % at long tenors (`get_margin_semantics.md`, section 3).
  - The SM surface is almost a single colour. That is the finding, not a display error. Do not fall back on separate scales,
    otherwise exactly the comparison disappears.
  - Between listed expiries the values are interpolated. The tenor axis should show the listed expiries as
    ticks.
  - The date is chosen anew with the final data run. It must be a day without a parameter change within ±1 day.

## T2: What `get_margin` returns

- **Purpose:** show the bot developer that `C − net` is not margin, and resolve the factors 11.86 against 1.19.
- **Data:** `results/p2/semantics/factors.csv`, rows `historical …` without `H0_`, cases A and B. Columns
  `SM_R_engine, PM2_R_engine, V_SM, V_PM2, F_Cnet, F_R_engine`. Prototype table `fig_t2.csv`.
- **Coding:** panel a: one mixed book (24 Sep, case B), one horizontal bar `C − net = R − V` per manager.
  The R part is solid in the manager colour, the −V part hatched. One sees that −V (497,000 USDC) is the same for both
  managers and dwarfs R. Panel b: a dumbbell per probe book (4 rows), open circle = factor on
  `C − net`, filled circle = factor on R, an arrow in between, log x from 1 to 16. Fill instead of colour, and so
  robust in greyscale.
- **Size:** 7.0 × 2.5 in.
- **Core message (5 s):** The position value V sits in `C − net` and pushes the factor SM ÷ PM2 towards 1. On the
  requirement R the books lie between 2.14 and 10.76.
- **Practitioner addition (proposal, a line of its own under panel a or in the caption):** the recipe for the marginal cost
  in one request, `positions = q, changes = Δq, collateral_changes = −p·Δq → ΔK = −(post − pre)`. If the jury
  wants no text in the figure, it goes verbatim into the caption.
- **Pitfalls:**
  - The variant of the book of 24 Sep (`H1_…` against `H0_todays_list`) must be named, otherwise 1.19 does not match
    1.22.
  - The arrow for the book of 17 Sep B points to the left (11.86 → 10.76). That is correct (V > 0), but it looks like an
    error. The caption should say that V is positive there.
  - Do not use ticker marks. `F_R_ticker` exists only for live rows.

## F1: What a contract costs

- **Purpose:** the price list of capital, that is what a single contract binds per cell under PM2, and next to it
  how SM and legacy PM compare on *the same fills*.
- **Data:** `data/p2/derived/capital.parquet` (`K_sm, K_pm, K_pm2, amount, index_price, maker_side, currency`),
  joined on `trade_id` to `data/p1/derived/markouts.parquet` (`delta_bucket, tenor_bucket`). Filter: `K_pm2`
  finite (PM2 window per underlying), 336,087 fills. Per cell the ratio of sums, weighted by quantity:
  `100·Σ K_pm2·a / Σ Index·a` as well as `Σ K_sm·a / Σ K_pm2·a` and `Σ K_pm·a / Σ K_pm2·a` (legacy only on fills with a
  finite `K_pm`). Occupied from 200 fills. Final as `results/p2/capital_cells.csv` or `fig_f1.csv`
  (prototype: 210 cells, 173 occupied). The inference has since written `results/p2/fig_capital_by_manager.csv`
  (`window ∈ {own, pm2}, manager, ccy, side, delta_bucket, tenor_bucket, fills,
  median_k_over_index, p25_…, p75_…`). The file holds **medians per fill**, not the ratio of sums.
  For the number in the cell the median fits (robust, unit % of the index). For the ratios SM ÷ PM2 on
  the same fills one additionally needs `sum_K_<m>` and `sum_index` per cell (an addition, see the data contract below).
- **Coding:** rows = maker sells (top) and maker buys (bottom), columns BTC, ETH, HYPE. Per map 7
  |Δ| buckets × 5 tenors, **one number** = PM2 capital in % of the index, grey lightness logarithmic per
  row. On the right, per row, a strip “÷ PM2”: one symbol per occupied cell (SM orange square, legacy green diamond),
  the median as a black bar, a dashed line at 1 and the hint “PM2 cheaper →”.
- **Size:** 7.0 × 3.9 in.
- **Core message (5 s):** A naked short costs 7 to 21 % of the index under PM2 (HYPE 18 to 39 %), and SM is not dearer for
  the same contract (median 0.88 to 0.94). Only the legacy PM charges about 1.4 times as much.
- **Pitfalls:**
  - The map averages over all parameter states of the PM2 window. Within it, the PM2 capital of the reference straddle fell
    from 14.4 to 10.0 % of the forward (F5). For a maker today that is the wrong number. Hence the need for T1
    as the state of one day, or an extra column “last 30 days” in the CSV.
  - For buys SM ÷ PM2 ≈ 1 almost by construction: a long under SM costs exactly its premium. This must not
    be read as “SM and PM2 are equal”. The caption states it as a property of SM.
  - |Δ| is the delta of the traded option. A cell 90–100 on the sell side is a contract sold deep in the
    money, not an OTM premium. Practitioners think in call delta (as in T1), the paper in |Δ| (as in Paper 1). The
    axis label must say “|delta| of the option”.
  - The ratio of sums is carried by large fills. The fill count per cell is in the CSV, not in the
    figure (one number per cell).
  - 20 fills with K_PM2 ≤ 0 (RFQ legs far from the mark) stay in the sums, as laid down for H1 in Addendum 4.

## F2: The map in two denominators (H1)

- **Purpose:** show where a maker earns the most per unit of PM2 capital, and whether the capital denominator
  reorders the cells relative to notional.
- **Data (from the inference):** `results/p2/h1.json` (`stat` = ρ, `lo, hi, rejected, threshold, n`) and
  `results/p2/fig_edge_maps.csv` with `map == "pm2"` or `h1_cells.csv`: per cell `ccy, side, delta_bucket,
  tenor_bucket, fills, occupied, A_bp` (edge per notional), `B_bp` (edge per PM2 capital), `rank_A, rank_B,
  rank_B_lo, rank_B_hi`. The rank bands come from the same replications as ρ. The maps under SM and
  legacy PM (`map ∈ {sm_pm2win, pm_pm2win, …}`) are exploratory and belong in the CSV, not in F2. In the prototype
  the edge values, the ranks and ρ are synthetic. Only the set of cells (173) and the capital shares per cell are
  real (`fig_f2_SYNTHETIC.csv`).
- **Coding:** on the left six maps (sell/buy × BTC/ETH/HYPE), one number = net edge in bp of PM2 capital,
  from 1,000 on as “1.3k”. Diverging scale orange-white-blue with zero in white, negative cells additionally
  hatched (greyscale), the five best cells framed in black. On the right the object of H1: rank by edge per
  notional against rank by edge per PM2 capital, both axes with rank 1 at top right, diagonal dashed. The
  symbol carries the underlying (circle, square, diamond), filled for sell and open for buy. Grey vertical
  lines are the 90 % rank band. A box gives ρ with its interval and the rule “rejected if upper ≥ 0.5”.
- **Size:** 7.0 × 3.9 in.
- **Core message (5 s):** Points far from the diagonal are cells that fare better (top) or worse
  (bottom) per capital than per notional. The framed cells are the ones in which capital earns the best return.
- **Pitfalls:**
  - **Long OTM cells explode.** The capital of a bought OTM contract is its premium, that is 0.07 to 0.6 %
    of the index (F1). Even a small edge then gives thousands of bp per capital, up to 11,400 bp in the prototype. The rank
    (H1) is robust against this, the map is not. Proposal: buy rows with a colour scale of their own, and say in the text
    that edge per capital on buys is a return on the premium. Do not introduce a lower bound on K after the
    fact, because the pre-registration has none.
  - The five “best” cells by point estimate are noisy. Only cells whose
    5 % rank percentile is below 20 should be framed. That needs `rank_capital_p05` from the inference.
  - Edge per capital *per fill* is not a return over time. Capital is a stock and edge a flow. One sentence
    in the caption and the reference to the holding-time sensitivity (`results/p2/holding_time.csv`), otherwise a
    practitioner reads bp per fill as an annual return.
  - A high return does not mean that the cell scales: depth is not part of the paper.

## F3: The next contract in a maker's book (H2)

- **Purpose:** show how much additional capital a fill binds in the real book of a dominant maker, measured against the
  same contract alone.
- **Data:** `data/p2/derived/marginal.parquet` (`ratio` as the test statistic under Addendum 4, `label`, `day`,
  `K_single_pm2`), filter `status == ok` and `K_single_pm2 > 0`, a sample of 20,000 fills (M3 6,405, M5 5,958,
  M8 4,296, M10 3,341, real numbers). Median and interval from `results/p2/h2.json`
  (`stat, lo, hi, n, n_excluded, share_nonpositive, rejected`). Curve and band shares from
  `results/p2/fig_h2_dist.csv` (`label ∈ {all, M3, M5, M8, M10}`, `variant == "ratio"`, `kind == "hist"` with bins
  of 0.05 and overflow classes, plus `quantile`, `share_le_0`, `n`). The ECDF is built from the cumulative
  histogram. In the prototype the distribution is synthetic.
- **Coding:** panel a as the ECDF of the ratio with four grey bands in practitioner language: “frees capital”
  (< 0), “cheap” (0 to ½), “partial” (½ to 1), “dearer than alone” (> 1), the share of fills above each band.
  The H2 threshold ½ dashed, the median as a point with an interval bar. The x axis is cut to −1 to 2
  (bins of `fig_h2_dist.csv`), and the overflow classes stand as numbers at the edges. Panel b: per
  account the median and p25 to p75 as a bar with n.
  One line, grey bands, no colour coding that one needs.
- **Size:** 3.4 × 3.3 in.
- **Core message (5 s):** The share to the left of ½ is the share of fills that cost less than half in the book.
  The share to the left of 0 even releases capital.
- **Pitfalls:**
  - The statement holds for the book of a dominant maker. Whoever starts with an empty book pays the full price from
    F1. The caption should say so in one sentence, because otherwise a practitioner believes they themselves pay only half.
  - ratio is the ΔK of the whole fill per contract. `ratio_unit` (next single contract) and the tape book are
    sensitivities and do not belong in the same curve.
  - Only four accounts under PM2 (Addendum 1, point 5). M3 carries a third of the sample, hence panel b.
  - The edges: a ratio of −40 is really possible (a fill closes a large position). Without
    cutting, the middle becomes unreadable, hence the overflow counts.

## F4: What netting is worth (H3)

- **Purpose:** show by what factor SM needs more capital than PM2 for *the same real books*, and how the
  factor grows with book size.
- **Data:** `data/p2/derived/maker_days.parquet` (`label, day, n_legs, K_sm, K_pm2, K_pm`, per underlying
  `K_*_<CCY>`), filter `status == ok`, `K_pm2 > 0`, legacy only on BTC/ETH legs (`K_pm_BTC + K_pm_ETH` against
  `K_pm2_BTC + K_pm2_ETH`). Median and interval from `results/p2/h3.json` (`stat, lo, hi, n_excluded,
  days_over_63_options`). Per maker-day from `results/p2/fig_h3_series.csv` (`label, day, status, n_legs,
  over_63_options, ratio_sm_pm2, ratio_pm_pm2_be`). In the prototype the ratios are synthetic. Accounts, days per account and leg counts are real (1,943 maker-days).
- **Coding:** panel a: per account (M1 to M10 without M9, with the number of maker-days below) a quantile bar
  p10/p25/median/p75/p90 of K_SM ÷ K_PM2 on log y, next to it the legacy median as an open diamond. Accounts with fewer
  than 20 days are shaded grey (M7 has 10). The H3 threshold 2 is dashed, with the text “2 = PM2 saves
  half”. Panel b: the same ratio against the number of option legs (log-log), grey points, plus the median curve
  over bins with at least 20 days and the vertical line at 63 options (SM account limit).
- **Size:** 3.4 × 4.0 in.
- **Core message (5 s):** All bars above the line at 2 mean that PM2 saves more than half. Panel b shows
  from how many legs on PM2 pays off.
- **Pitfalls:**
  - On 1,431 of 1,943 maker-days the book holds more than 63 options. K_SM is counterfactual there, because no
    SM account would be allowed to hold the book (Addendum 4, point 2). The vertical line in panel b and the share in the caption
    are mandatory, otherwise the large factor on the right looks like a saving that does not exist in this form.
  - Days are correlated within an account. The bars show dispersion, not uncertainty. The interval of the pooled
    median from the day bootstrap stands as a number in the caption.
  - No second y axis “% saved”. The translation stands only at the threshold line.
  - A pure long book has K = premium under SM and a little less under PM2. Ratios close to 1 for small books
    are therefore to be expected.

## F5: The engine over time

- **Purpose:** show when makers switched to PM2, when the engine changed its price, and by how much
  a fixed book became cheaper as a result.
- **Data:** `results/p2/manager_oi_share.csv` (`month, ccy, sm, pm, pm2`), `results/p2/events.csv` (`ccy, manager,
  event_ts, kept, event_id`), `results/p2/reference_book.csv` (`ccy, day, forward, K_sm, K_pm, K_pm2, K_*_prev`).
  Pure parameter effect per event = `K_m / K_m_prev − 1` on the first day after the event. Prototype tables
  `fig_f5_events.csv` and `fig_f5_refbook_btc.csv`.
- **Coding:** panel a: three narrow strips (BTC, ETH, HYPE) with monthly OI shares as stacked
  step areas: PM2 solid blue, legacy light green, SM white with orange hatching (in greyscale dark, light,
  hatched). Panel b: an event bar per underlying, circle = PM2, diamond = legacy, filled = in H4, open =
  dropped. Next to each symbol **one number**: the pure effect on the capital of the reference straddle in %.
  Panel c: BTC reference straddle (ATM, about 30 days, one contract each) in % of the forward under SM, legacy PM and
  PM2, direct labels at the right edge, events as dotted vertical lines.
- **Size:** 7.0 × 4.4 in.
- **Core message (5 s):** In 2026 the makers switched almost completely to PM2 (BTC 91 %, ETH 72 %, HYPE 88 % of
  OI in September). PM2 became cheaper in steps, most strongly on 2026-08-20 (BTC −23 %, ETH −17 %, HYPE −18 %).
  The parameter changes alone lowered the capital of the BTC straddle by 35 % (ETH −23 %, HYPE −47 %). SM stayed at
  29.6 %.
- **Pitfalls:**
  - The reference straddle changes expiry (tenor 21 to 36 days). The saw teeth in c are tenor, not
    engine. Take over the proposal from B5: in the final version a synthetic 30-day node via
    `capital_grid(tenors=[30/365])` (exploratory, to be marked as such).
  - The percentages in b hold for this one book. The dose per cell (F6) can have a different sign.
    On 2026-01-08 the engine became dearer (+1.6 %). So do not use “always cheaper” as a title.
  - The change of 2025-06-12/13 (−0.35 %) lies at the edge of the PM2 window and is not in `events.csv`. It
    appears in c, but not in b, and should be added to b as an event without H4 status.
  - OI share is not capital share. The strips show where the positions are margined, not where the capital
    sits.
  - Filling panels b and c with numbers for BTC only would be simpler. But ETH and HYPE belong in them, because HYPE
    has the largest single step with −31 % on 2026-05-24.

## F6: The price of capital (H4)

- **Purpose:** show whether the half spread falls when a parameter change makes the capital of a cell cheaper, in
  a unit that a maker can translate.
- **Data:** `results/p2/h4.json` (`stat` = β, `p, criteria.*, placebo.p95, placebo.share_ge_beta`),
  `results/p2/h4_placebo.csv` (`beta` of the 100 replications) and `results/p2/fig_h4_events.csv` (per event three
  dose terciles with `t{k}_median_dose, t{k}_y_pre, t{k}_y_post`). For panel a in the drawn form, a
  table per cell-event pair with the residuals after α and γ is missing (proposal `fig_f6_pairs.csv` with `event_id, ccy,
  cell, dose, d_hs_resid_bp, n_pre, n_post` from `data/p2/derived/h4_panel.parquet`). Without it panel a carries the
  39 tercile points (see data contract). In the prototype everything is synthetic except the list of events and the
  cell count per event (475 pairs, 13 events with panel cells).
- **Coding:** panel a: dose response as a binned scatter, pairs as light grey points, deciles of the dose as
  black squares with 90 % bars, the estimated slope β as a blue line. x axis = dose in log, but with
  ticks labelled as capital change (−50 %, −25 %, 0, +25 %). That is the same axis and not a second one. Panel b:
  per event mean dose against mean spread change, symbol per underlying, legacy open, BTC dates as
  labels. Panel c: histogram of the 100 placebo β, 95th percentile dashed, the estimate as a blue line with a
  label.
- **Size:** 7.0 × 2.7 in.
- **Core message (5 s):** If the blue line in c lies to the right of the 95th percentile and it rises in a, then the
  spread reacts to the price of capital. The caption translates: “capital 10 % cheaper → the half spread changes by
  0.1·β bp of the index.”
- **Pitfalls:**
  - Sign: except for 2026-01-08 the dose is negative (cheaper). A positive slope therefore means that
    the spread falls when capital becomes cheaper. This must go into the caption as the reading direction, otherwise the
    practitioner reads the line the wrong way round.
  - Raw spread changes contain day and cell effects. What must be drawn are the residuals after α and γ,
    otherwise the slope in the figure does not match β.
  - Panel b has 13 points with very unequal cell counts. Point size by fills would be more honest, but it gets in the way in
    greyscale. Hence cell counts in the CSV and points of equal size.
  - The event HYPE 2026-08-20 has a dose of 1.65 from one cell with 6 fills and K close to 0. This cell
    drops out of the panel (fewer than 20 fills per side), but it determines the 1 % rule. It does not belong in a as an
    outlier.
  - No placebo hairlines, only the histogram (rule from Paper 1).

## A1: Does the replica agree with the chain?

- **Purpose:** show that the offline replica of the three managers matches the deployed contracts at rounding level,
  for single contracts and for real books of up to 245 legs.
- **Data:** `results/p2/validation.csv` (`kind, ccy, manager, rel_err, abs_err, K_chain, n_legs, is_initial,
  status`), filter `status == ok`, `is_initial == True` (MM in the CSV). `validation_summary.json` for the
  thresholds. Prototype table `fig_a1.csv`.
- **Coding:** panel a: one row per underlying × manager with jittered symbols (manager symbol and colour),
  |rel. deviation| on log x from 10⁻¹² to 10⁻¹. Exact hits (0) sit in a grey margin strip
  “exact”. The pre-registered bounds 0.1 % (median) and 1 % (p95) are dashed and dotted respectively. Panel b:
  books, deviation against number of legs (log-log), plus in the figure the largest absolute deviation (0.05 USDC at K
  up to 19.5 million USDC).
- **Size:** 7.0 × 2.6 in (appendix).
- **Core message (5 s):** All points lie at least five decades to the left of the bounds, and the deviation does not grow with
  the size of the book.
- **Pitfalls:**
  - The replica matches the *chain*. The exchange admits trades via the off-chain API (flat 2 % discount). A
    bot that uses the replica instead of `get_margin` is exact for liquidation and history, but not for
    admission. That belongs in the caption, otherwise A1 is a false promise for practitioners.
  - Only one HYPE maker-day in the book draw. Do not split panel b by underlying.
  - Exact zeros on a log axis: the margin strip must be labelled, otherwise 45 to 53 SM cases per
    cell disappear.

---

## README and X

### GIF: “The price list moves”

- **Content:** BTC, PM2 capital per short contract as a 3D surface as in T1 (height IV, colour and iso-lines = capital in %
  of the forward). Below it a time strip with the reference straddle under PM2 and SM and a cursor. In the
  GIF SM is only a reference line, so that the surface stays large.
- **Time:** one frame per week (Wednesday 08:00 UTC) from 2025-06-13 to 2026-09-17, about 66 frames. At every event
  with H4 status the frame is held for 6 frames. A banner shows the date and the pure effect, for example
  “20 Aug 2026 · parameter change · straddle −23 %”. The iso-line that moves the most is
  highlighted at that point.
- **Format:** 1200 × 675 (16:9, suits X and the README), 4 fps, colour scale fixed over all frames (`fit_limits`),
  target under 8 MB with a 64-colour palette. The still for the preview is `social_t1_keyframe.png` (1600 × 900).
- **Build:** `p2surface.animate(managers=("pm2",), …)` with three additions: iso-lines (code in
  `proto_praktiker.t1_engine_surface`), hold frames with a banner at events, and the unit % instead of bp. The
  feed history loads by quarter and must run through `scripts/p2_heavy.py` (machine lock).
- **Pitfall:** the surface also changes through the market and vol. Without a banner a viewer takes every movement for a
  parameter change. That is why the time strip shows the pure parameter effect as a step (K against K_prev).

### Social cards 1600 × 900

| Card | File | Data | Title | Core message |
|---|---|---|---|---|
| 1 | `social_1_engine_cheaper.png` | real | “Parameter changes alone cut PM2 capital by 35%” | Reference straddle BTC: PM2 from 14.4 to 10.0 % of the forward, pure parameter steps −10, −8, −23 %; SM flat at 29.6 % |
| 2 | `social_2_straddle_vs_leg.png` | real | “Sell the put too: under PM2 it is almost free” | 2026-09-17, 22 days ATM: PM2 one short call 11.9 %, straddle 10.0 %; SM 14.3 % against 29.6 % |
| 3 | `social_3_contract_vs_book.png` | mixed, PROTOTYP | “PM2 discounts the book, not the contract” | naked short SM ÷ PM2 = 0.90 (real, median of the sell cells) against the book [H3 median, synthetic 4.1] |

Card 2 is the strongest practitioner card. It needs no hypothesis and shows the mechanism in two bars.
Its flaw: the single leg comes from the grid node Δ 0.50 with 22.3 days, the straddle from the listed
expiry with 22 days and strike = forward. For publication, compute both legs of the reference straddle one by one
(columns `K_<m>_call`, `K_<m>_put` in `reference_book_series`, exploratory). Card 3 is filled only after
H3. If H3 comes out differently, the title stays correct as long as the book factor is above 1. If it is below,
the card is dropped. A fourth card “The next contract is cheap” (ECDF from F3) is possible, but only if H2
is not rejected.

Style as in `derive_surface/figures_social.py`: title 25 pt bold, axes 16 pt, core message in the title, fixed image size
without `bbox tight`.

---

## What from this lens should go to the jury

1. **The contrast of contract against book as the common thread.** F1 (real) shows that PM2 does not make a single short
   cheaper. F3 and F4 show that the book becomes cheaper. Without F1 in this form a practitioner reads T1 as
   “PM2 is cheaper everywhere”.
2. **F2 needs a decision on the buy side** before anything is drawn. The return on the premium of an
   OTM long is real, but it dominates any common colour scale.
3. **F5 carries real numbers that need no hypothesis** (−35 % BTC, −23 % ETH, −47 % HYPE pure
   parameter effect). They belong as a sentence in the results section before H4, because they make the dose tangible.
4. **Units:** capital in % of the index/forward, edge in bp of capital. A maker understands the number “11.8 % of forward”
   at once, “1,182 bp” not.

## Files

- Prototype code: `data/p2/fig_proto/praktiker/proto_praktiker.py` (called from the repo root, arguments T1, T2,
  F1 … A1, SOCIAL, KEYFRAME).
- Images: `t1_praktiker.png`, `t2_praktiker.png`, `f1_praktiker.png`, `f5_praktiker.png`, `a1_praktiker.png`
  (real); `f2_praktiker.png`, `f3_praktiker.png`, `f4_praktiker.png`, `f6_praktiker.png` (PROTOTYP); cards
  `social_1_engine_cheaper.png`, `social_2_straddle_vs_leg.png` (real), `social_3_contract_vs_book.png`
  (PROTOTYP), `social_t1_keyframe.png` (real, GIF still).
- Tables: `fig_t1.csv`, `fig_t1_markers.csv`, `fig_t2.csv`, `fig_f1.csv`, `fig_f5_events.csv`,
  `fig_f5_refbook_btc.csv`, `fig_a1.csv`, `fig_social_1.csv`, `fig_social_2.csv` (real);
  `fig_f2_SYNTHETIC.csv`, `fig_f3_SYNTHETIC.csv`, `fig_f4_SYNTHETIC.csv`, `fig_f6_SYNTHETIC.csv`.
