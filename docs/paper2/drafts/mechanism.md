# Figure draft for Paper 2, mechanism lens

Status 2026-09-25 · draft for the jury (pattern of Paper 1: three lenses, two judges) · nothing committed.

The figures are meant to explain **how** the engine forms capital (scenarios, netting, static discount, long against
short, SM against PM2) and **why** this shifts the map of Paper 1. Every hypothesis figure therefore gets
a mechanism panel next to the finding, one that makes the finding predictable.

Prototypes (pilot data, cut of 2026-09-17) under `data/p2/fig_proto/mechanismus/`, built with
`python3 data/p2/fig_proto/mechanismus/proto_mechanismus.py [T1 T2 F1 F2 F5 F6 A1 CARD]`:

| File | Slot | Data |
|---|---|---|
| `t1_proto.png` | T1 | real: probe grid BTC 2026-09-17 08:00 UTC, engine replica for the binding rule |
| `t2_proto.png` | T2 | real: `results/p2/semantics/factors.csv`, engine replica (straddle) |
| `f1_proto.png` | F1 | real: `capital.parquet` ⋈ `markouts.parquet`, engine replica (anatomy) |
| `f2_proto_synth.png` | F2 | **synthetic**, watermark PROTOTYP |
| `f5_proto.png` | F5 | real: `manager_oi_share.csv`, `params/`, `events.csv`, `reference_book.csv` |
| `f6_proto_a_real_bc_synth.png` | F6 | panel a real (`h4_doses.csv`), panels b and c **synthetic** |
| `a1_proto.png` | A1 | real: `validation.csv` |
| `card_straddle_1600x900.png` | social card 1 | real: `reference_book.csv` |

Next to each PNG lies its number table as `fig_*.csv` (in the final build `results/p2/fig_*.csv`). No
test statistic was computed; F3 and F4 are only described, because their core is the distribution of the H2 and
H3 quantity itself. While this work was under way, the inference tables appeared (`h1.json` … `h4.json`,
`h1_cells.csv`, `fig_edge_maps.csv`, `fig_capital_by_manager.csv`, `fig_h2_dist.csv`, `fig_h3_series.csv`,
`fig_h4_events.csv`, `h4_placebo.csv`, `sens_*.csv`). Below, only their columns and keys are planned in; their
values were neither read nor taken into a prototype.

---

## 1 · The mechanics in five sentences, and what the prototypes show of them

1. **Capital is `K = Σ p·q − net_IM(q; C = 0)`.** Under SM a long option counts for nothing, so a buy costs its
   premium. A short costs `max(15 % − OTM, 13 %)` of spot (a put is additionally checked against 1.05 × MM).
2. **PM2 takes the worst scenario of the whole book** (spot ±14 % × vol up/unchanged/down, dampened
   tails ×0.34 to ×6, two skew scenarios, basis contingency), plus contingencies and static discount. The
   legacy PM computes similarly, but with an IM factor of 1.25 and a static discount of 0.95 on positive values.
3. **For the single contract the side decides, not the manager** (F1, real data BTC, PM2 window):
   buys bind 0.07 to 17 % of notional under SM and 0.07 to 11 % under PM2, sells 12.8 to 15.1 % (SM),
   7.8 to 17.7 % (PM2) and 8.5 to 24.3 % (legacy PM). For short sells deep in the money PM2 is even dearer
   than SM (17 to 18 % against 15 %).
4. **The large PM2 advantage arises only in the book** (T2c, engine at the T1 block): a short ATM straddle over 30 days
   binds 9.7 % of the forward under PM2, the same two legs margined separately 23.5 %, and 29.0 % under SM. This is the mechanism
   behind H2 and H3.
5. **Parameter changes shift the map cell by cell** (F6a, real doses): 2026-01-23 (tail weights
   lowered) hit almost only OTM sells (|Δ| below 40 %, most strongly −14 to −27 log-% at 7 to 90 days), exactly
   where the dampened tail scenarios bind in T1c; 2026-08-20 (grid ±17 → ±14 %) made every occupied
   sell cell cheaper by 21 to 31 log-%, and buys barely moved. Almost all doses
   are ≤ 0: the natural experiment consists essentially of loosenings.

This gives the reading line of the figures: T1/T2 explain the rule, F1 the denominator per cell, F2 its effect on
the map (H1), F3/F4 the book (H2/H3), F5/F6 time and dose (H4), A1 the fidelity of the replica.

---

## 2 · Rules for all slots (from Paper 1 plus additions)

- Widths 3.4 and 7.0 inches, typeset 1:1, font ≥ 7 pt everywhere. **Caution:** the code of Paper 1 sets 6.0 and 6.5 pt in F5 and in
  side notes (`figures_p1.py`, `_side_note`, tick labels); do not copy it. For
  Paper 2 `figstyle` should get an `FS_MIN = 7.0`, and a test should check every text instance.
- **Fixed manager coding** in all figures, double-coded: PM2 blue `#0072B2`, solid, circle; SM
  vermilion `#D55E00`, dashed, square; legacy PM green `#009E73`, dotted, diamond (matches
  `p2surface.MANAGER_COLORS/STYLES`). The trio passes the CVD validator (deutan ΔE 11.0, tritan 8.6, normal vision
  18.7), and the line styles carry the distinction in greyscale as well.
- **Fixed side coding:** maker buy ▲, maker sell ▼ (buy = long, sell = short, always name both).
- **Unit of capital:** % of the forward (engine grid) or % of notional (fills). USDC per contract only in the
  CSV tables; it mainly measures the price level (factor 1,599 between BTC and HYPE, Paper 1).
- Maps: one number per cell, cells under 200 fills as an empty cross (for doses: under 20 fills before the event,
  the panel rule of H4). Sequential maps in grey or `cividis`, diverging ones only with the sign printed.
- Mechanism panels from the engine replica name block, contract and parameter state in the figure (footer or
  axis title), so that nobody mistakes a single valuation for a cell mean.
- Every number of the figure as `results/p2/fig_<slot>_<panel>.csv`; hypothesis numbers are only read
  (`h1.json` … `h4.json`), never recomputed in `figures_p2.py`.

---

## 3 · The nine slots at a glance

| Slot | Question | Size (in) | Prototype |
|---|---|---|---|
| T1 | Which rule sets the capital on the surface? | 7.0 × 4.3 | yes, real |
| T2 | What does `get_margin` return, and how does PM2 build R? | 7.0 × 2.75 | yes, real |
| F1 | What does a contract cost per cell and manager, and what does that consist of? | 7.0 × 4.7 | yes, real |
| F2 | Does the capital denominator reorder the map? (H1) | 7.0 × 3.1 | yes, synthetic |
| F3 | What does the next contract in the maker's book cost? (H2) | 3.4 × 3.8 | no (description) |
| F4 | What is netting worth? (H3) | 3.4 × 3.8 | no (description) |
| F5 | How has the engine moved over time? | 7.0 × 5.0 | yes, real |
| F6 | Does the half spread follow the price of capital? (H4) | 7.0 × 4.3 | yes, a real, b/c synthetic |
| A1 | Does the replica match the chain? | 7.0 × 2.7 | yes, real |

---

## 4 · The slots in detail

### T1 · The engine's view of the surface (7.0 × 4.3 in, the only 3D figure)

- **Purpose:** show capital as a surface over the same geometry as the vol surface, and name which rule
  sets it at each point.
- **Data:** `p2surface.capital_grid("BTC", ts, manager ∈ {pm2, sm}, "short")` at the block of the caption
  (pilot: `data/p2/surface/probe_BTC_2026-09-17_grid.csv`, 37 deltas × 20 tenors, columns `delta, tenor_days,
  iv, K_per_forward_bp, strike, forward, spot, is_call, rate, *_conf`). The binding rule per node is new:
  `figdata_p2.binding_rule(grid, params)` via `margin_pm2._span` (index of the worst scenario, basis) and
  the SM branches from `OptionMarginParams`. Parameters `Timeline(ccy, mgr).at(ts)`.
- **Coding:** panels a/b in 3D (height IV in %, colour K in % of the forward, `cividis`, common scale, same
  view elev 24 / azim −128). Below them c/d as **2D strips**: the binding rule as grey areas with hatching
  (PM2: spot +14 % vol up, spot −14 % vol up, tail ×2 dampened, tail ×0.34 dampened; SM: 15 % − OTM,
  13 % floor, put 1.05 × MM) and iso-capital lines 5/8/11/14 % with their own line style and labels, the same
  strokes marked on the colour scale. Greyscale: `cividis` is monotone in lightness, and the strips carry
  hatching and line labels.
- **Core message (5 s):** SM charges 13 to 15 % of spot almost everywhere, under a single rule; PM2 ranges from 3
  to 14 % and is set almost everywhere by one scenario, spot ±14 % with an upward vol shock.
- **Pitfalls:**
  - A floor projection inside the 3D axes was tried and rejected: mplot3d sorts surfaces by depth, so floor and
    iso-lines disappear behind the surface. Hence the 2D strips (allowed, only one 3D figure counts).
  - Height and colour are two surfaces: the z axis is called “implied vol, %”, the colour scale “capital per short contract, % of
    forward”, otherwise one reads IV as capital.
  - The common scale turns SM into an almost single-coloured surface. That is the message, but it must be stated in the
    caption.
  - SM computes in % of spot, the figure in % of the forward: 13 % of spot appears as 12.4 % of the forward at 1 year.
  - Nodes between expiries are interpolated (forward and rate linearly, confidence as the minimum); nodes are OTM (call
    for K ≥ F), axis “call delta (put = Δ − 1)”.
  - The block must not be an event day (check in F5c); after 2026-08-20 the ±14 % grid applies, and the text must
    name the regime.

### T2 · What `get_margin` returns and how PM2 forms R (7.0 × 2.75 in)

- **Purpose:** show the reading `C − net` as a source of error and, in the same place, make visible the rule “worst scenario of the
  book” that explains H2 and H3.
- **Data:** a and b from `results/p2/semantics/factors.csv`, rows where `measurement` starts with `historical`, without
  `H0_`, `case ∈ {A, B}` (exactly four rows: 17 Sep A/B, 24 Sep A/B); columns `SM_R_engine, PM2_R_engine, V_SM,
  V_PM2, F_Cnet, F_R_engine`. c from the replica at the T1 block: reference straddle as in `reference_book` (strike =
  forward, expiry nearest to 30 days), scenario PnL via `margin_pm2._Params/_expiry_factors/_leg_prices/_span`,
  capital via `net_margin` for the straddle, for both legs one by one and for SM.
- **Coding:** a horizontal stacks per manager: R in the manager colour, −V hatched grey, the total `C − net` at the end
  (book B of 24 Sep: SM 211 + 497 = 708, PM2 99 + 497 = 596 thousand USDC). b a dumbbell per book on a log axis, hollow = on
  `C − net`, filled = on R, line at 2 (H3 threshold). c scenario PnL in % of the forward, x categorical by
  spot shock (core ±14 % shaded, tails dampened, not to scale), markers ▲ ● ▼ for vol up/unchanged/
  down, skew as a diamond, the binding scenario circled; three horizontal lines: PM2 capital (9.7 %), PM2 with the legs
  separate (23.5 %, dotted), SM (29.0 %, dashed).
- **Core message (5 s):** `C − net` pushes every factor towards 1, because the same position value sits in both
  numerators; for the straddle PM2 charges only its worst scenario, not the sum of its legs.
- **Pitfalls:**
  - `factors.csv` holds several measurements per book (H0 list, live); filter explicitly and test for four rows.
    The numbers in the caption in `main.tex` (11.86/10.76, 1.19/2.14, 2.33/3.19, 1.46/3.61) must come
    from it.
  - Sign: V is negative for shorts; −V is drawn.
  - The PM2 capital line lies below the circled scenario (contingencies, IM factor); that is intended and is
    said in the caption, otherwise it looks like an error.
  - In the prototype the strike is the node at call delta 0.5 (77,017 against F = 76,668); in the final build strike = forward.
  - Three panels in 7 inches: the dumbbell labels (2.14 and 2.33) sit close together; label above and below.

### F1 · What a contract costs, and what that consists of (7.0 × 4.7 in)

- **Purpose:** show the capital denominator per cell, split by side and manager, and decompose on one contract
  what it consists of.
- **Data:** `data/p2/derived/capital.parquet` (`trade_id, currency, ts, maker_side, amount, index_price, K_sm,
  K_pm, K_pm2`) ⋈ `data/p1/derived/markouts.parquet` (`trade_id, delta_bucket, tenor_bucket`); filter:
  PM2 window of the underlying (BTC/ETH from 2025-06-12 23:00 UTC, `ts` in ms), all three managers on the same fills.
  Cell value κ_c = 100·Σ K·a / Σ S·a (% of notional), plus fills per cell. The inference delivers
  `results/p2/fig_capital_by_manager.csv` (`window, manager, ccy, side, delta_bucket, tenor_bucket, fills,
  median_k_over_index, p25_k_over_index, p75_k_over_index, median_k_mm_over_index`), that is **medians per fill**. For
  the mechanics F1 needs the **ratio of sums** (only then does e^K = e^N / κ hold exactly, and only then does F1 match
  `h1_cells.csv`: κ = `sum_K / sum_index`): add columns `sum_K, sum_index` per manager or build them in `figdata_p2`
  from `capital.parquet` (descriptive, no test statistic). The median can stay as a frame style or in the
  CSV. Right column: replica at the T1 block, one
  ATM call of 30 days, `figdata_p2.pm2_anatomy` (valuation convention p·q − V, scenario loss, static discount surcharge,
  contingencies), SM (premium or spot requirement), legacy PM in total.
- **Coding:** 2 rows (maker buy = long, maker sell = short) × 3 maps (SM, legacy PM, PM2), |Δ| × tenor,
  **one** logarithmic grey scale for all six maps, one number per cell, cross under 200 fills. On the right, per
  row, stacked bars (areas with hatching: dots = premium without credit, solid = spot requirement or
  scenario loss, diagonal = static discount, cross = contingencies; legacy PM as a dotted frame) with the
  binding PM2 scenario as a line.
- **Core message (5 s):** A buy costs exactly its premium under SM and hardly less under PM2, a sell 8 to
  18 % of notional; for the single contract PM2 is clearly cheaper than SM only for long-dated OTM sells.
- **Pilot numbers (BTC, PM2 window, 60 of the 70 possible cells with at least 200 fills):** buys SM 0.07 to 16.9 %, PM2 0.07 to 10.9 %;
  sells SM 12.8 to 15.1 %, legacy PM 8.5 to 24.3 %, PM2 7.8 to 17.7 %. Anatomy ATM 30 days in % of the forward:
  buy SM 3.59 (premium), PM2 3.44 (scenario spot ×0.895, vol down), legacy PM 4.44; sell SM 14.08, PM2 11.83
  (11.54 scenario spot ×1.14 vol up, 0.05 static discount, 0.25 contingencies), legacy PM 20.58.
- **Pitfalls:**
  - The caption in `main.tex` says USDC and “each map has its own scale”. Both hide the mechanics: USDC
    measures the price level, and with scales of their own the buy and sell maps look alike. Proposal: % of notional,
    one scale. That is exactly the factor that links F2: e^K = e^N / κ.
  - Only BTC fits into the figure; ETH and HYPE go into `fig_f1_cells.csv` and into one sentence of the text.
  - The anatomy is one contract at one block, not a cell mean; label it that way.
  - The static discount is almost invisible for the single contract (0.05 percentage points). Do not sell it as the main mechanism;
    it acts in books with a large |M| and in the regime change of 2026-01-08 (F6a).
  - Legacy PM charges more than the premium for the long (4.44 against 3.59 %): IM factor 1.25 and static discount
    0.95 on positive values. Confirm on an `eth_call` before printing.
  - 20 fills with K_PM2 ≤ 0 stay in the sums (Addendum 4); log scale only on cell values > 0, otherwise a cross with
    its own symbol.

### F2 · The map in two denominators, H1 (7.0 × 3.1 in)

- **Purpose:** show whether and why the ranking of the cells flips when edge is measured per PM2 capital instead of per
  notional.
- **Data:** `results/p2/h1_cells.csv` (`cell, ccy, side, delta_bucket, tenor_bucket, fills, occupied, sum_edge,
  sum_index, sum_K, A_bp, B_bp, rank_A, rank_B, rank_shift, A_lo/A_hi, B_lo/B_hi, rank_*_lo/hi, window, capital`;
  presumably A = per notional and B = per PM2 capital, to be checked against `h1.json` `map`/`capital` and `scale`
  before the build; filter `occupied`), κ = 100·`sum_K/sum_index`; `results/p2/h1.json` (`stat,
  lo, hi, rejected, threshold, n, n_days, cells_by_ccy.*`). Maps with other denominators (SM, legacy PM, MM) from
  `fig_edge_maps.csv` or `sens_h1_cells.csv` (column `map`) only in the CSV. κ must be identical to F1 (test).
- **Coding:** a e^N against e^K on double log axes, plus diagonals of constant κ (0.5 / 2 / 10 %): every cell
  lies on the diagonal of its capital denominator, and reordering is movement across the diagonals. b rank against rank
  with the diagonal and the bootstrap rank intervals (`rank_*_lo/hi`) as fine cross bars; a box with ρ
  and 90 % interval from `h1.json` and the rule “rejected if the upper bound ≥ 0.5”. Markers ▲/▼ for the side, colour `cividis` for the tenor (greyscale: lightness plus shape).
- **Core message (5 s):** Buys and sells lie on different κ diagonals, an order of magnitude apart;
  how far the ranks depart from the diagonal picture is H1.
- **Pitfalls:**
  - Negative edges do not fit on log-log: symlog with a shaded linear core (rule of Paper 1) or a separate
    strip “≤ 0” at the margin, with the count given.
  - The alternative from the specification (lines between the ranks) becomes spaghetti at around 120 cells.
  - Never recompute ρ in the figure, only read it. Ties in the ranks (equal values) as in the inference.
  - The cells come from three underlyings, each in its PM2 window; F1 shows only BTC. Say so in the caption.

### F3 · The next contract in a maker's book, H2 (3.4 × 3.8 in)

- **Purpose:** show the distribution of the marginal cost and explain which fills release capital.
- **Data:** `data/p2/derived/marginal.parquet` (`ratio, status, K_single_pm2, dK_per_contract, manager, ccy, day,
  maker_side, n_legs_before, gross_before, label`) only for the mechanism panel; the distribution itself from
  `results/p2/fig_h2_dist.csv` (`label, variant, kind, x, x_hi, value`: pre-binned, the inference's sample, do not
  draw again) and `results/p2/h2.json` (`stat, lo, hi, rejected, threshold, share_nonpositive, n, n_sample,
  n_excluded, accounts`); variants (unit contract, MM, tape book) from `sens_h2.csv` only in the CSV.
- **Coding:** a histogram of ratio on [−1.5; 1.5] with overflow bars at both ends (counts labelled),
  mass ≤ 0 hatched (“releases capital”), threshold 0.5 dashed, median with 90 % interval as a bar above
  the histogram. b mechanics: ratio split by whether the fill makes a gain or a loss in the binding scenario of the book before the fill
  (new column `hedges_worst` in `books.py`: sign of the fill PnL in `worst` from
  `margin_pm2.margin_details`), two rows as a strip with median; fallback if the column is missing: median and
  interquartile band of ratio over deciles of `n_legs_before`.
- **Core message (5 s):** In the book of a dominant maker the next contract mostly costs a fraction of its
  stand-alone capital, and fills against the binding scenario release capital.
- **Pitfalls:** ratio is unbounded when K_single is small (show the overflow instead of cutting it off); ratio per
  contract of the fill (Addendum 4, item 1), variants only in the CSV; only four accounts under PM2 carry H2, and the
  account count G = 4 belongs in the figure (Paper 1 rule: shade small G); 3.4 inches leave only two rows for b.

### F4 · What netting is worth, H3 (3.4 × 3.8 in)

- **Purpose:** show K_SM/K_PM2 of the same books and explain why the factor differs so much from book to book.
- **Data:** `results/p2/fig_h3_series.csv` (`label, day, manager, status, n_legs, n_legs_pm, over_63_options,
  K_sm, K_pm2, K_pm, ratio_sm_pm2, ratio_sm_pm_be, ratio_pm_pm2_be, …_mm`), filter as in H3 via `status`;
  `results/p2/h3.json` (`stat, lo, hi, rejected, threshold, n, n_excluded, share_days_over_63_options,
  accounts.M*`); legacy PM and MM from `sens_h3.csv`. `maker_days.parquet` only if `n_expiries_max` is needed for the
  mechanism panel.
- **Coding:** a K_SM/K_PM2 per maker-day on log x, one row per account (rank labels M1 to M10), a median bar per
  row; maker-days with more than 63 options (SM not admissible on v2, 1,431 of 1,943) as hollow markers,
  admissible ones filled; legacy PM/PM2 as diamonds in the same row; threshold 2 dashed; registered median with
  interval at the top. b mechanics: factor against `n_legs` (log-log) with the T2 probe books (2.14 to 10.76) as
  reference marks: netting grows with the breadth of the book.
- **Core message (5 s):** For the same books SM charges a multiple of the PM2 capital, and the factor grows with
  the breadth of the book; most of these books would not even be admissible under SM on v2.
- **Pitfalls:** the counterfactual SM must be visible (hollow), otherwise one reads a real cost comparison;
  K_PM2 ≤ 0 excluded and counted in the figure; a few accounts carry many days (rows per account instead of one cloud);
  the median of the ratios is not the ratio of the sums.

### F5 · The engine over time (7.0 × 5.0 in)

- **Purpose:** show under which manager the positions sit, when parameters change, and that the gap
  between the engines arose in steps on parameter days, not through the market.
- **Data:** `results/p2/manager_oi_share.csv` (`month, ccy, sm, pm, pm2`); `results/p2/params/{CCY}_{mgr}.json`
  (every entry after the first is a change, field `changed`); `results/p2/events.csv` (`ccy, manager,
  event_ts, kept, max_abs_dose, kinds`); `results/p2/reference_book.csv` (`ccy, day, forward, K_sm, K_pm, K_pm2`,
  `*_prev`).
- **Coding:** a three narrow strips (BTC, ETH, HYPE) with monthly shares of OI as stacks, SM solid, legacy PM
  dotted, PM2 hatched. b an event rail per underlying and manager: every parameter change as a grey tick,
  H4 events filled (kept) or hollow (dose under 1 %), marker shape = manager. c BTC reference straddle in %
  of the forward per manager (colour plus line style), kept events as dotted vertical lines. d pure
  parameter effect 100·log(K/K_prev) as stems, shape = underlying.
- **Core message (5 s):** On 2026-09-17 the same BTC straddle costs 29.6 % (SM), 19.7 % (legacy PM) and 10.0 % (PM2)
  of the forward, and the gap arose in jumps on parameter days.
- **Pilot numbers panel d (log-%):** BTC legacy PM 2025-02-22 −18.6; BTC PM2 2026-01-08 +1.6, 2026-01-23 −10.5,
  2026-05-24 −7.8, 2026-08-20 −26.0; HYPE PM2 2026-05-24 −37.4.
- **Pitfalls:**
  - `K_prev` computes with the parameters of 24 h earlier; the jump appears on the day after the event (22 Feb →
    23 Feb). Label with the event date.
  - SM changes affect only perps (no option effect); show the ticks, but name them as such.
  - HYPE has no legacy PM; OI shares are monthly, everything else daily.
  - The straddle rolls to the expiry nearest to 30 days; small saw teeth are rolls, not parameters.
  - Four panels in 5 inches: only c gets grid lines, a and b do not.

### F6 · The price of capital, H4 (7.0 × 4.3 in)

- **Purpose:** show the dose as the fingerprint of the parameter change on the map, and then whether the half spread
  follows it.
- **Data:** a `results/p2/h4_doses.csv` (`event_id, cell, dose, n_fills`), three BTC PM2 events with
  different mechanisms: 2026-01-08 (static discount adjusted), 2026-01-23 (tail weights), 2026-08-20 (grid
  ±14 %). b `results/p2/fig_h4_events.csv` (per event the dose terciles `t1…t3` with `*_dose_lo/hi, *_median_dose,
  *_n_pre/post, *_y_pre/post`): per tercile the difference y_post − y_pre against the mean dose, one point per
  event and tercile (shape = underlying), plus β from `h4.json` (`stat, lo, hi, p, p_sided, criteria.*,
  events_kept, cell_events`). c `results/p2/h4_placebo.csv` (`rep, beta`) with `h4.json` `placebo.p95,
  placebo.share_ge_beta`.
- **Coding:** a 2 × 3 maps (rows sell/buy, columns events), 100·dose with sign as a number, `PuOr`
  diverging around 0, cross under 20 fills. b dose response in classes with intervals and the line β. c
  histogram of the 100 placebo β with the 95th percentile and the estimate.
- **Core message (5 s):** Every parameter change leaves its own imprint on the map (tail weights almost only
  OTM sells, the grid all sells by −21 to −31 log-%, the static discount +1 to +2 log-% on sells); b and c
  say whether the half spread follows this imprint.
- **Pitfalls:**
  - Almost all doses are ≤ 0 (only 2026-01-08 makes capital dearer); β is essentially identified from loosenings.
    This belongs in the caption.
  - Diverging colour alone does not carry in greyscale; the sign stands as a number in every cell.
  - Only BTC in a; ETH and HYPE in the CSV. Changes combined per day: e = first change (Addendum 4).
  - β in bp of the index per log unit of capital; the text converts to 10 % of capital.
  - Do not draw raw half-spread time series around the event (the noise tempts reading by eye).

### A1 · Does the replica match the chain? (7.0 × 2.7 in, appendix)

- **Purpose:** show the validation against `eth_call` as a distribution, with the registered thresholds.
- **Data:** `results/p2/validation.csv` (`kind, ccy, manager, is_initial, status, rel_err, n_legs`), IM primary
  (`is_initial == True`), `status == ok`; `validation_summary.json` for thresholds, reverts and the
  single scenario check.
- **Coding:** a single contracts, b books; rows underlying × manager, x = log10 |rel|, exact zeros at the margin
  “≤ 1e−12”, median as a bar, thresholds 0.1 % and 1 % dashed, n per row. Mechanism variant for b: rel against
  `n_legs` (2 to 245), so that one sees that the error does not grow with the breadth of the book.
- **Core message (5 s):** The replica matches the chain to about 1e−9 to 1e−8, six orders of magnitude below the
  threshold, for single contracts as for books.
- **Pitfalls:** zeros on a log axis (almost half of the SM cases are exactly 0); name the two reverts; HYPE books
  n = 1; IM and MM stand as duplicate rows in the CSV.

---

## 5 · README and X

### GIF: “The map breathes with the market and jumps with the parameters”

- **Content:** PM2 capital per short contract as a 3D surface (height IV, colour K in % of the forward, fixed scale over
  all frames), below it the reference straddle per manager as a band with a running cursor and event flags. SM only
  as a number in the corner (“SM: 29 %”), because its surface is a single colour.
- **Frames:** weekly from 2025-06-13 to 2026-09-17 (about 66) plus three daily frames per kept BTC event
  (the day before, the day itself with the banner “parameter change: tail weights lowered”, the day after), held for 1.5 s; 4 fps, about 25 s.
  In the event frame, overlay the cells with |dose| > 5 % from F6a as outlines on the band.
- **Technique:** `p2surface.animate` with the `ANIM_DAYS` axis, `fit_limits` over all frames; run only through
  `scripts/p2_heavy.py` (feed history per quarter). 960 × 540 for the README, 1280 × 720 as MP4 for X
  (`write_mp4`), GIF under 8 MB.
- **Pitfalls:** The existing GIF (`data/p2/surface/BTC_capital_short_2026-08-14_2026-08-27.gif`) has tick fonts
  of about 10 px; on X anything under 14 px is unreadable. Days without a live expiry are skipped, and the date in the frame
  must show it. Check the colour quantisation of the GIF with `cividis`.

### Social cards 1600 × 900

1. **“One short BTC straddle. Three margin engines.”** (prototype built, real data): time series from F5c, on the right
   three large numbers 30 % / 20 % / 10 % of the forward on 2026-09-17, line style per manager. Pitfall: add “capital for a
   hypothetical book, not a balance” as a line; PM2 starts only in June 2025 (window), do not label it
   as “introduced”.
2. **“Where the capital comes from”:** T1a as a single surface plus the sentence “Almost everywhere one scenario sets the
   capital: spot ±14 % with vol up.” and the strip T1c below it.
3. **“One parameter change, one fingerprint”:** F6a for 2026-08-20 (sell side) with “Every short got 21 to 31 %
   cheaper overnight. Buys barely moved.” After the inference, a fourth card with the four verdicts H1 to H4.

---

## 6 · What the lens changes relative to the specification (for the jury)

| Slot | Specification | Mechanism proposal | Reason |
|---|---|---|---|
| T1 | 3D PM2 and SM | plus 2D strips “binding rule” with iso-lines | The surface alone does not say why; a floor projection in 3D fails |
| T2 | two panels | plus panel c, scenario profile of the straddle | the only place where one sees how PM2 forms R and why netting works |
| F1 | USDC, own scales | % of notional, one log scale, anatomy column | denominator of F2; side dominates manager |
| F2 | rank lines | κ diagonals plus rank dispersion | reordering readable as movement across the denominator |
| F3, F4 | distribution only | one mechanism panel each (binding scenario, book breadth) | the finding becomes predictable |
| F5 | three panels | plus d, pure parameter effect from `K_prev` | separates market from parameters |
| F6 | dose response, placebo | plus a, real dose maps | makes the experiment visible, links to T1c |

Open requirements on the code: `figdata_p2.binding_rule` (T1c/d), `figdata_p2.pm2_anatomy` (F1, T2c),
`figdata_p2.cell_capital_ratio` (F1 as a ratio of sums per manager, matching `h1_cells.csv`), column
`hedges_worst` in `books.py` (F3b). The inference tables cover F2, F3a, F4a, F6b/c; F6b reads the terciles from
`fig_h4_events.csv`, so a bin table of its own is not needed. The prototype code
`data/p2/fig_proto/mechanismus/proto_mechanismus.py` contains the engine decompositions (`pm2_scenarios`,
`pm2_anatomy`, `_pm2_binding`, `_sm_branch`) as a template; at the T1 node the PM2 decomposition adds up exactly to
the capital of the grid (9,066.71 USDC for the short, 2,636.54 for the long).
