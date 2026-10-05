# Jury for Paper 2, referee judge (with recomputation)

Status 2026-09-25. Basis: the three draft sets `mechanism.md`, `empirics.md` and `practitioner.md`, all
prototypes under `data/p2/fig_proto/`, the specification (section 6), the pre-registration with Addenda 1
to 4, `paper2/main.tex` and the data under `data/p2/derived/` and `results/p2/`. Nothing was committed. I deliberately did not read the
verdict of the second judge (`jury_design.md`), so that both verdicts
stay independent.

**Blindness to the verdicts.** From the inference files I read only schema, keys and structural numbers
(n, days, accounts, cells, admissible placebo days). The fields `stat, lo, hi, rejected, p, p_sided`, the
criteria and the placebo percentiles were masked. One disclosure: in `h4.json` the fields `se`, `t` and
`fe.beta_direct_solve` were not masked. I therefore know the sign of the H4 estimate. The recommendation on F6
is worded so that it holds for either sign. I do not know the other verdicts (H1 to H3).

The recomputation used `capital.parquet` ⋈ `markouts.parquet` (336,087 fills in the PM2 window), the
probe grid of 2026-09-17, `factors.csv`, `reference_book.csv`, `events.csv`, `params/*.json`,
`h4_doses.csv`, `h4_panel.parquet`, `marginal.parquet`, `maker_days.parquet` and `validation.csv`. The
helper scripts are only in the scratchpad.

---

## 1 · Verdict in one table

| Slot | Choice | Main reason | Most important requirement |
|---|---|---|---|
| T1 | **M** (3D a/b and 2D strips c/d with the binding rule), plus title numbers from P, header and bucket grid from E | Only M says *which* rule sets the capital, and only the 2D strips carry the iso-lines legibly | Choose the block by a rule fixed in advance, name the regime (±14 % grid since 2026-08-20) in the figure |
| T2 | **P a + P b** with the H3 threshold from M/E, plus **M c** (scenario profile), recomputed on the reference straddle | P a is linear and shows V as an area. E a is logarithmic, and there the distance between the markers is not V | T2c must give the same numbers as F5c (10.0 / 29.6 %), not 9.7 / 29.0 % |
| F1 | **E** (BTC maps for three managers × two sides, two significant digits, strip of all 173 cells), plus the common greyscale of M and the strip order of P, **plus a regime split** | Only E shows the manager comparison per cell *and* all underlyings | The map averages over four parameter states. The sign of “SM cheaper than PM2” flips in the last regime, and that must be in the strip |
| F2 | **P** (six maps of edge per PM2 capital and a rank-rank picture with rank bands) with the **verdict bar of E** and **new sign guide lines** | The map is contribution 1 of the paper and belongs in the figure. The verdict bar shows estimator, interval and rule | The H1 test has a structural lower bound near ρ ≈ 0.73 (section 2.1). That must become visible, together with an exploratory row “ρ within sign/side” |
| F3 | **P a** (ECDF with bands) and **E b** (forest with verdict bar and sensitivities), accounts as exploratory rows | The ECDF reads the median directly at 0.5 and fits the bins of `fig_h2_dist.csv` ([−1; 2] with open edges) | Header: four accounts, ETH and HYPE only (no BTC), M3 is the only HYPE account |
| F4 | **E** (histogram stacked ≤ 63 / > 63 options, and forest), accounts as exploratory rows from `sens_h3.csv` | Only E shows verdict, interval and the counterfactual share (1,431 of 1,943 days) at once | The header says 9 accounts, not 10. Request exploratory regime rows |
| F5 | **P** (OI strips, event bar with the pure parameter effect, BTC reference straddle) with the **event states, timeline ticks and ±14-day windows of E** and a **new band of admissible placebo days** | One figure that makes the H4 selection checkable and gives the size of the steps in numbers | Fix P's error: the SM share is missing from the HYPE strip. y axis in c from 0 |
| F6 | **Newly combined:** a dose strip of all 13 panel events, b FWL binscatter of E with a dose rug, c placebo histogram with E's checklist, d small exploratory forest | Only the residualised bins have the slope β. The dose support (half of the pairs below 1 %) must be visible | As long as `inference_p2.py` writes no FWL bins, b carries **no** β line |
| A1 | **P** (a strip IM with labelled thresholds, b books against leg count) with M's median bars and E's p95 diamond | Contains all pre-registered quantities and shows that the error does not grow with book size | One revert case (two rows IM/MM), not “two reverts”. Feed age as a sentence, not a panel of its own |
| GIF | 3D PM2 surface weekly with hold frames at events (M/P), time strip with the pure parameter steps (P), E's honesty rules | The only form in which market and parameter movements are visible separately | Fixed scale, date and block per frame, `gif_frames.csv`, grey expiries with an old feed |
| Cards | 1 M “One short BTC straddle. Three margin engines.” · 2 P still of the surface · 3 verdict card H1 to H4 in E's grammar | Each card carries exactly one statement that the paper covers | P card 3 (“discounts the book, not the contract”) is dropped, reason in section 2.2 |

Abbreviations: M = mechanism, E = empirics, P = practitioner.

---

## 2 · Findings of the recomputation that decide the choice

### 2.1 H1 has a structural lower bound, and F2 must show it

Of the 173 occupied cells, **74 have a net edge ≤ 0** (buys 26 of 87, sells 48 of 86;
`h1_cells.csv`, column `A_bp`). The capital denominator is positive in every cell (κ = Σ K·a / Σ index·a between
0.07 and 38.7 %). So sign(B) = sign(A) holds in every cell: all 99 positive cells stand in *both* maps
ahead of all 74 non-positive ones. Even if the denominator made the order within both groups completely random,
Spearman's ρ would average **0.73** (simulation with 4,000 draws, 90 % of the values between
0.70 and 0.77). The threshold of the pre-registration is 0.5.

This is a property of the registered statistic, not a question of design, and it does not change the test.
But a referee will find it. The figure must therefore show it, otherwise every ρ above 0.5 looks like an
empirical finding about the reordering. I derived the number without knowing ρ.

- **In the rank-rank picture** there are guide lines at rank 99 and 74 (“edge ≤ 0 below/left”). The points then
  visibly fall into two blocks. The reordering that matters is the dispersion *within* the blocks.
- **In the forest** there are exploratory rows “ρ within edge > 0”, “ρ within edge ≤ 0”, “ρ buys only” and
  “ρ sells only”, on grey. Today `sensitivity.json` has only the split by underlying
  (`g_by_ccy`). `inference_p2.py` still has to write the other rows, marked as exploratory.
- M's log-log display (panel F2a with κ diagonals) is therefore not workable. 43 % of the cells would lie
  at the bottom. The prototype hid this because its synthetic edges were almost all positive.

### 2.2 F1 averages over four parameter states, and the core statement on the single contract flips

E and P carry as their common thread “for a single short PM2 is not cheaper than SM” (SM/PM2 median
0.94 / 0.90 / 0.88, below 1 in 74 % of the sell cells). Pooled over the PM2 window, that holds. Split by regime
(fills ≥ 200 per cell and regime, ratio of sums) it looks different:

| Median SM/PM2, sell cells | to 2026-01-22 | 2026-01-23 to 2026-05-23 | 2026-05-24 to 2026-08-19 | from 2026-08-20 |
|---|---|---|---|---|
| BTC | 0.91 (20 cells) | 0.91 (19) | 0.97 (19) | **1.40** (6) |
| ETH | 0.88 (31) | 0.88 (24) | 0.93 (27) | **1.14** (18) |
| HYPE | – | 0.72 (15) | 1.06 (14) | 1.44 (1) |
| Share of sell fills with K_SM < K_PM2 | 82.5 % | 69.2 % | 54.1 % | **15.4 %** |

T1 therefore visibly contradicts F1: on 2026-09-17 SM is cheaper than PM2 at only 9 of 740 grid nodes (median
SM/PM2 = 1.26), while F1 says “SM cheaper in 74 % of the sell cells”. Both are right. Without the regime, however,
a referee reads it as a contradiction.

Three things follow. **(i)** The strip in F1 shows, per row (underlying × side), filled symbols for the
whole window and hollow ones for “from 2026-08-20”, each with a median bar. Add a table
`fig_f1_regimes.csv`. **(ii)** The sentence “PM2 discounts the book, not the contract” holds only until August 2026.
P card 3 is dropped, and the text must restrict the sentence in time. **(iii)** M's anatomy column in F1
is dropped. It shows a contract from the last regime (11.8 / 14.1 %) next to maps that average over all regimes,
and it only repeats the title numbers of T1.

### 2.3 One object, two numbers: the BTC straddle on 2026-09-17

M T2c computes the straddle at the grid node Δ = 0.50 with 30.4 days (interpolated, strike 77,017) and arrives at
PM2 9.65 %, legs separately 23.45 % and SM 29.02 % of the forward (`fig_t2_proto.csv`: 7,399.89 / 17,980.39 /
22,248.85 USDC at F = 76,668). F5c and the cards show the same straddle from `reference_book.csv` (listed
expiry with 22 days, strike = forward): PM2 **10.03 %**, SM **29.61 %**, legacy **19.68 %**. In the final build
T2c computes on the row of `reference_book.csv` for the same day. The column “legs separately” is added. That way the
paper has only one number per object.

### 2.4 The prototypes are wider than they will be printed

`figstyle` saves with `savefig.bbox = "tight"`. Text outside the axes therefore enlarges the canvas
beyond the CAS width. Set with `\linewidth`, the font shrinks accordingly:

| Prototype | planned | saved | 7 pt become |
|---|---|---|---|
| E F3, E F4 | 3.4 in | 5.46 in | **4.4 pt** |
| P F3, P F4 | 3.4 in | 4.50 in | **5.3 pt** |
| E F1 | 7.0 in | 8.49 in | **5.8 pt** |
| M F5 | 7.0 in | 7.72 in | 6.3 pt |
| M F2 · E F6 · P F5 | 7.0 in | 7.58 · 7.54 · 7.48 in | 6.5 pt |
| E T2 · P F2 · M T2 · E F5 · P F6 | 7.0 in | 7.38 · 7.32 · 7.24 · 7.16 · 7.12 in | 6.6 to 6.9 pt |

`figures_p2.py` needs a test: saved PDF width = 3.4 or 7.0 in ± 0.02, and no text instance
below 7 pt after this scaling. As M rightly notes, `figures_p1.py` itself sets 6.0 and 6.5 pt (lines
70, 143 to 175, 222 to 231). Do not take over this code.

### 2.5 H4: three structural features that no prototype shows in full

- **Overlapping windows.** 91,446 panel rows come from **84,919** fills. 6,527 fills (7.7 %) sit in two
  event windows: BTC 1,457 and ETH 2,861 (2026-01-08/01-23), HYPE 2,209 (2026-05-08/05-24). E noticed
  this. The number belongs in the header of F6 and in the text.
- **Admissible placebo days.** According to `h4.json` (`placebo.admissible_days`) ETH PM2 has only **10** admissible days
  (2025-07-16 to 2025-07-25), BTC PM2 54 (2025-07-16 to 2026-03-21), HYPE PM2 67, the legacy events 363 and 319.
  The ETH placebos of PM2 therefore all come from a single July window. The pre-registration forces this,
  because every row of the timeline counts, collateral changes included. F5 must show this as a band per underlying, and F6c
  gives the day counts per underlying.
- **Dose support.** Over the 475 cell-event pairs the median dose is −0.006. 11.2 % are positive
  (at most +0.022), only 48.6 % lie below −0.01, and the minimum is −0.442. Half of the pairs thus serve
  practically as controls, and β is identified from loosenings. A binscatter with 20 equally populated bins
  puts about ten bins at x ≈ 0. Without a rug or histogram of the dose the reader does not see where the slope
  comes from.

### 2.6 Data contract: what is already there and what is missing

- **F1 needs no new inference column.** `fig_edge_maps.csv` contains `sum_K` and `sum_index` for the maps
  `pm2`, `sm_pm2win` and `pm_pm2win`. 100·`sum_K`/`sum_index` reproduces the cells of the prototypes to
  6 × 10⁻¹⁴, and the ratios SM/PM2 to 6 × 10⁻¹⁵. The fill counts match exactly, and so does the occupancy
  (210 cells, 173 occupied). The data gap that M and P report (`sum_K_sm` missing) therefore does not exist.
- `fig_capital_by_manager.csv` contains the **median per fill as a fraction** (0.11 = 11 %), not the ratio of
  sums. Example BTC sell 00-10/2-7d: median 11.0 %, ratio of sums 9.9 %. The file belongs only in
  the CSV, otherwise two numbers stand for the same cell in the paper.
- `fig_h2_dist.csv` has bins of 0.05 on [−1; 2] with open edges. E's window [−2; 3] therefore cannot
  be displayed; P read this correctly.
- **Missing and needed:** `fig_h4_fwl_bins.csv` (x̄, ȳ, fills per bin, residualised on α and γ, with
  a test that the OLS slope of the bins gives β up to rounding), `h4_placebo_days.csv` (the drawn and
  the admissible days per underlying), the exploratory H1 rows from 2.1, regime rows for H2 and H3 (2.2 and
  gap 3) and `fig_f1_regimes.csv`. **Missing, optional:** `h1_rho_draws.csv` (histogram of the 9,999 ρ). The
  verdict bar carries without it too.

---

## 3 · Recomputed numbers from the drafts

| Claim | Draft | Recomputed | Verdict |
|---|---|---|---|
| ATM 30-day short PM2 11.8 %, SM 14.1 % of the forward | P, M (F1 anatomy) | 11.83 / 14.08 (grid Δ 0.50, 30.4 d) | ✓ |
| PM2 3.4 to 13.7 %, SM 12.4 to 15.0 % on 2026-09-17 | P, E, M | 342 to 1,370 bp / 1,237 to 1,501 bp | ✓ |
| T2 factors 11.86/10.76, 1.19/2.14, 2.33/3.19, 1.46/3.61; R 211k/99k, −V 497k | all | `factors.csv` rows b17_exact and b24 (H1 variant) | ✓ |
| “For the book of 24 Sep, C − net under PM2 is six times R” | E | 595,694 / 98,835 = 6.03 | ✓ |
| Straddle PM2 9.7 %, legs separately 23.5 %, SM 29.0 % | M (T2c) | arithmetically ✓, but a different object from F5c (10.0 / 29.6 %) | ✗ unify (2.3) |
| BTC buys SM 0.07 to 16.9 %, PM2 0.07 to 10.9 %; sells SM 12.8 to 15.1, legacy 8.5 to 24.3, PM2 7.8 to 17.7 % | M | 0.07–16.85 / 0.07–10.86; 12.83–15.11 / 8.48–24.30 / 7.80–17.69 | ✓ |
| SM/PM2 0.75 to 4.67, < 1 in 86 cells; legacy/PM2 0.95 to 1.74 | E | 0.752–4.669; 86; 0.946–1.736. Maximum: ETH buy 90–100/30–90d (SM 67.8 %, PM2 14.5 %, 234 fills) | ✓, pooled only (2.2) |
| Sells SM/PM2 median 0.94/0.90/0.88, 74 % below 1; legacy 1.38/1.35 | P | 0.943/0.902/0.875; 74.4 %; 1.382/1.355 | ✓, pooled only (2.2) |
| Naked short under PM2 7 to 21 % of the index (HYPE 18 to 39 %) | P | 7.07–21.36 (HYPE 17.50–38.73) | ✓ |
| Reference straddle 2026-09-17: 29.6 / 19.7 / 10.0 % | M, P | 29.61 / 19.68 / 10.03 | ✓ |
| PM2 BTC from 14.4 to 10.0 %; pure steps −10, −8, −23 %; cumulative −35 % (ETH −23, HYPE −47) | P | 14.41 → 10.03; −9.96 / −7.54 / −22.93 %; −35.0 / −22.6 / −47.1 % (including +1.61 % on 8 Jan and −0.35 % on 2025-06-13) | ✓ |
| Log jumps: BTC legacy −18.6; BTC PM2 +1.6 / −10.5 / −7.8 / −26.0; HYPE −37.4 | M | −18.56; +1.60 / −10.49 / −7.84 / −26.05; −37.43 | ✓ |
| “The jump appears on the day after the event” | M | only for events after 08:00 UTC (2025-02-22, 8 Jan, 20 Aug). 23 Jan (04:24) and 24 May (04:05) jump on the same day | ✗ make precise |
| 14 of 18 events are kept, 13 in the panel; 11 of 14 lower the capital | E | 14 kept (HYPE 8 Jan without a panel cell), the three increases are the events of 8 Jan | ✓ |
| The change of 2025-06-12/13 is missing from `events.csv` | P | The change is on 2025-06-12 at 22:20 UTC, that is *before* the window starts at 23:00 UTC. Not an H4 event under the pre-registration. If shown, then as “before the window” | ✗ correct the interpretation |
| 2026-01-23: only OTM sells, −14 to −27 log-% at 7 to 90 d; 20 Aug: all sell cells −21 to −31; 8 Jan: +1 to +2 | M | −14.4 to −27.3 (plus 2–7d −17.4); −20.6 to −30.9; +1.0 to +2.2 | ✓ |
| “Grid ±17 → ±14 %” as the title for 2026-08-20 | M | A bundle: grid ±17 → ±14 %, tail dampening, vol shocks, contingencies, basis, collateral. Until 2026-05-24 the grid was ±18 % | ✗ title “bundle incl. …” |
| Legacy PM IM factor 1.25, static discount 0.95 | M | `BTC_pm.json`: `imFactor` 1.25, `baseStaticDiscount` 0.95 | ✓ |
| H2: M3 6,405, M5 5,958, M8 4,296, M10 3,341; 372 days; ETH 13,595, HYPE 6,405 | P, E | ✓. M3 is the **only** HYPE account. After the exclusion n = 19,999 (ETH 13,594). E's forest writes “n 20 000” | ✓ / correct the label |
| H3: 1,943 maker-days, 1,431 with > 63 options (74 %) | E, P, M | 1,943 / 1,431 = 73.6 %; `over_63_options` ⇔ n_legs ≥ 64 | ✓ |
| H3 “10 subaccounts” | E (header F4) | 9 accounts with maker-days (M9 has none); M7 10 days; every account has exactly one manager, M2 is the only SM account | ✗ |
| H4: 13 events, 475 pairs, 91,446 fills | E, P | 91,446 **rows** from 84,919 fills (2.5) | ✗ unit |
| Validation: medians ≤ 9e−9, maximum 1.9e−7 (MM), 359 exact zeros | E | 8.99e−9; 1.88e−7 (BTC PM2, MM); 359 incl. MM, 181 IM only | ✓ |
| 26 books from 20 maker-days, largest deviation 0.05 USDC at K up to 19.5 million | P | ✓ (0.0503 USDC; 19,494,690 USDC; BTC 7, ETH 18, HYPE 1) | ✓ |
| “two reverts” | M, E | one case (HYPE PM2, single contract), two rows (IM and MM) | ✗ |
| “six orders of magnitude below the threshold” / “at least five decades” | M / P | medians 5 to 6 decades below 0.1 %. Single values (IM) 5.05 decades below 1 %, but only 4.05 below the 0.1 % line | ✗ make precise |
| Feed age of the test population as a panel A1c of its own | E | In the PM2 window no fill has a feed beyond the validation limits (p99 vol 119 s, forward 95 s). Over the whole sample: 448 fills with vol > 20 min, 45 with forward > 1 h | a sentence in the caption is enough |
| OI in September 2026: BTC 91 %, ETH 72 %, HYPE 88 % PM2 | P | 90.96 / 71.89 / 87.92 % | ✓ |

---

## 4 · Choice per slot

### T1 · The engine's view of the surface

**Choice: M as the carrier.** Panels a/b are 3D (height IV, colour K in % of the forward, `cividis`, one scale). Panels
c/d are 2D strips: the binding PM2 rule and SM rule as grey areas with hatching, plus
iso-capital lines 5/8/11/14 %, which are also marked on the colour bar. Taken over are P's title numbers
(“PM2: ATM 30 d short = 11.8 % of fwd”, “SM: 14.1 %”, both recomputed) and the listed expiries as
ticks on the tenor axis. From E come the header (block, UTC, 15 expiries, parameter state) and the
|Δ|×tenor bucket edges of Paper 1, and **only on the 2D strips**. That way T1 leads straight to F1.

**Why:** Only M answers why the surface looks the way it does (almost everywhere spot ±14 % with an upward vol shock,
tails only in two corners). This later supports F6: the cut in tail weights on 2026-01-23 hits exactly the
OTM sells, that is the cells in which the tail scenarios bind. Iso-lines on the 3D surface (P) are partly
hidden, and so is the ATM 30-day node. A floor projection (E) fails on the depth sorting of mplot3d,
as M checked.

**Requirements:** Fix the block in advance: last pilot day at 08:00 UTC, no parameter event within ±1 day. Name
“grid ±14 % since 20 Aug 2026” in the figure. Test `figdata_p2.binding_rule` against `margin_pm2.margin_details`.
z axis “implied vol, %”, so that nobody reads IV as capital. Into the caption: SM computes in % of spot,
the figure shows % of the forward; the capital is computed in chain semantics (the API computes a flat 2 %). Iso-lines
and the binding rule per node go into `fig_t1.csv`.

### T2 · What `get_margin` returns

**Choice: P a and P b, plus M c.** a: the one book of 24 Sep (case B, block 45,110,142), linear bars, R
solid in the manager colour, −V hatched, the total C − net at the end. b: dumbbells with an arrow from C − net to R,
log 1 to 16, plus the H3 threshold 2 with the addition “threshold set from these probe books”. c: M's
scenario profile, recomputed on the reference straddle (2.3) and with the axis “categorical, not to
scale”.

**Why:** E a is a dot plot on log USDC. There the distance between the markers is log((R − V)/R) and not V, and the
label “gap = value V” therefore says something wrong. P a shows V as an area and so carries the statement
“V sits in both numerators”. M c is the only place where one sees the engine value a book (“the
worst scenario of the book, not the sum of the legs”). That is the bridge from F1 (single contract) to
F3/F4 (book).

**Requirements:** Put the labels in b above and below, so that 2.14 and 2.33 do not collide (M). The
arrow for the book of 17 Sep B points to the left, because V > 0; the caption says so. The H0 variant stays out, and
a test checks exactly the four rows from `factors.csv`.

### F1 · What a contract costs

**Choice: E as the carrier, with changes.** Maps for BTC, three managers × two sides, one number with two
significant digits per cell. M rounds to one decimal and thereby turns 0.07 and 0.11 into the same 0.1.
The shading is **one** logarithmic grey scale for all six maps (M). That shows that the side and
not the manager determines the capital, and the numbers carry the exact values. On the right is the strip of all
173 cells, ordered as in P (rows underlying × side, SM square and legacy diamond, median bar, line
at 1), **with a regime split** (2.2).

**Why:** The specification asks for capital per contract *by manager*. P shows only PM2 and the
ratios; E shows both and checks the statement across all underlyings. M's anatomy column is dropped
(2.2 iii).

**Requirements:** Data from `fig_edge_maps.csv` (2.6). The upper row is called “maker buys: capital
= premium under SM” in the axis title (E, P). The axis says “|delta| of the traded option” (P). Count the crosses against the
cell table (210 cells, 173 occupied). The 20 fills with K_PM2 ≤ 0 stay in the sums (Addendum 4). The caption
in `main.tex` (“USDC”, “each panel on its own scale”) is replaced.

### F2 · The map in two denominators (H1)

**Choice: P as the carrier, with E's verdict bar and the sign lines from 2.1.** On the left six small
maps (sell/buy × BTC/ETH/HYPE), one number per cell = edge in bp of PM2 capital, from 1,000 on as “1.3k”,
negative cells hatched. On the right the rank-rank picture with 90 % rank bands (`rank_B_lo/hi`), underlying as
shape, side as fill. Below it the verdict bar: estimator, 90 % interval, threshold 0.5, hatched
rejection side, “173 cells, 463 day clusters” and in bold the rule with the verdict. Below that the exploratory
forest (grey): MM, net edge in the form of Paper 1, to expiry, holding time, per underlying, SM and
legacy maps (`sensitivity.json`), and newly within sign and within side.

**Why:** The capital map is contribution 1 of the specification. E does not show it at all, and a referee would
ask for it. E also lacks the rank band; M lacks rank band and distribution. P has both, but no
verdict bar, and the five framed “best” cells are not defined in advance.

**Rejected:** M a (log-log, 43 % of the cells ≤ 0), the connecting lines of the specification (173 hairlines,
ruled out in Paper 1) and P's top-5 frames. E's mean rank shifts (c/d) go into the CSV and the text
(`h1-reading`); the maps show this cell by cell.

**Requirements:** Colour as symlog with a shaded linear core on the colour bar (Paper 1 rule), otherwise
the buy cells with values in the thousands carry the whole scale. The caption says that edge per capital on buys is a
return on the premium and applies per fill (a flow over a stock, not an annual return). Map A (per notional)
stays in Paper 1, referenced in the caption. Size 7.0 × 4.0 in.

### F3 · The next contract in the book (H2)

**Choice: P a and E b.** a: ECDF from the cumulative histogram of `fig_h2_dist.csv` (`label = all`,
`variant = ratio`), bands “≤ 0: no extra capital or frees capital” (not just “frees”), 0 to ½, ½ to 1, > 1 with
their shares, plus the overflow shares at both edges. The median with its 90 % interval stands at y = 0.5, and the
threshold ½ is dashed. b: forest with the verdict bar. The registered row is bold. Sensitivities are
`ratio_unit`, `ratio_mm` and `ratio_tape`. Exploratory and on grey follow M3 (= HYPE), M5, M8 and M10 (`sens_h2.csv`).

**Why:** The ECDF reads the registered quantity (median) directly and needs no truncated window.
E's histogram requires [−2; 3], which the table does not have. P's p25 to p75 bars per account show
dispersion, not uncertainty. In the forest the same accounts have intervals. M's mechanism panel
(`hedges_worst`) would be a new, unregistered computation and becomes at most one sentence.

**Requirements:** Header “4 PM2 accounts, ETH and HYPE only (no BTC), 19 999 fills, 372 days, 1 excluded, random
sample of 20 000 (seed 20260924)”. E's ETH/HYPE row is dropped, because HYPE is exactly M3. The caption says
that a maker with an empty book pays the price from F1 (P). Width exactly 3.4 in (2.4).

### F4 · What netting is worth (H3)

**Choice: E as the carrier.** a: histogram on log x, stacked by ≤ 63 options and > 63 options (“SM
counterfactual”, hatched), threshold 2, median. b: forest with the registered row, “≤ 63 only”, “> 63 only”,
MM and legacy/PM2 (BTC and ETH legs only, n in the row). Exploratory and on grey: the nine accounts from `sens_h3.csv`
with their manager (M2 is the only SM account).

**Why:** Only here do the verdict, its interval and the counterfactual share stand in one figure. P's
account bars again show dispersion without the test interval. The breadth mechanism (factor against leg count, M and
P) is correct and vivid, but it finds no room in 3.4 in. It goes into the text as a sentence and into the CSV as a
column. If the design review finds a place for it, then as a binned median with a band and not as a cloud of
1,943 points.

**Requirements:** Header “9 accounts, 1 943 maker-days, 462 day clusters, 0 excluded” (E writes 10). The
caption says that the clusters are UTC days, not accounts. Exploratory rows by parameter regime (gap 3).

### F5 · The engine over time

**Choice: P as the carrier, extended by E and by a new band.**
- a: P's OI strips. Fix the error: the HYPE strip lacks the SM share (7 to 49 % per month), because `pm` is
  NaN for HYPE. Stack with `fillna(0)`.
- b: event bar per underlying with E's symbols: ● in the panel, ◇ kept without a panel cell (HYPE
  2026-01-08), ○ dropped. Grey ticks show every row of the timeline (placebo spacing). The number next to the
  symbol is the pure parameter effect on the reference straddle in % (P, recomputed). **New:** a thin
  band per underlying marks the admissible placebo days (2.5).
- c: BTC reference straddle per manager with direct labels at the right edge. The ±14-day windows are shaded
  grey, overlaps darker (E). The y axis starts at 0, so that the ratio 3 : 2 : 1 of the engines
  is honest (P starts at 5, M at 9). The legacy line becomes thin where the OI share is below 5 % (E).

**Why:** P carries the numbers that the text needs (−35 / −23 / −47 %). E makes the H4 selection checkable. M d
(stems in log-%) shows the same numbers a second time and is dropped in favour of the labels. M's SM rows
(perps only) are dropped as well. E's reference book panels for ETH and HYPE are replaced by the labels of the
bar.

**Requirements:** Label the event with its date, not with the day of the jump (2.3). The caption explains the saw teeth
(tenor 21 to 36 days). The caption names the overlapping windows (6,527 fills in two
windows). The change of 2025-06-12 at 22:20 UTC appears at most as “before PM2 window”.

### F6 · The price of capital (H4)

**Choice: a new combination of E, P and M.**
- a: **dose strip of all 13 panel events.** One row per event, one tick per panel pair (▼ sell,
  ▲ buy), plus the median. Source: `h4_doses.csv`, filtered to the pairs in `h4_panel.parquet`. The strip
  replaces M's three selected BTC dose maps. These are real and beautiful, but they show 3 of 13 events,
  and their cross follows only the pre rule (≥ 20 fills before the event) instead of the panel rule (20 each before and after).
  One of these maps becomes the reserve for X.
- b: **FWL binscatter** as in E, with point area by fills, the line β and a rug or histogram of the
  dose below the x axis (2.5). The axis explains the signs (“< 0: capital got cheaper”). The ticks may be
  labelled in % change in capital as in P, because it is the same axis.
- c: placebo histogram with P95 and β, above it E's checklist (one-sided wild p ≤ 0.05 met/not met, β >
  P95 met/not met, verdict). Below it the admissible placebo days per underlying.
- d (small, grey): β per underlying, without outlier cells, placebo over all timelines (`sensitivity_h4.json`),
  each with its cluster count.

**Why:** Only the residualised bins have the slope β. P a draws β over raw pairs, M b over raw
terciles. Neither line has the slope of the regression; that is a dishonest encoding. E b shows β per
event, which the inference does not estimate.

**Requirements:** The header gives 13 events, 475 pairs, 91,446 rows from 84,919 fills, 141 day clusters
and 322 day-by-underlying effects. In the figure the 90 % interval of β is called “descriptive”, because `h4.json` forms it from
unrestricted residuals. The wild p of the rule comes from restricted residuals. **Without
`fig_h4_fwl_bins.csv`** b shows the tercile contrasts within an event (Δy of the tercile minus the mean Δy
of the event, against dose minus its mean) and no β line. The conversion in the caption reads “10 % cheaper
= dose −0.105, predicted change −0.105·β bp” and not 0.1·β. The recommendation holds for either sign
of β.

### A1 · Does the replica match the chain?

**Choice: P as the carrier, plus M's median bars and n per row and E's p95 diamond.** a:
single contracts IM, rows underlying × manager, log |rel|, exact zeros in a labelled margin strip,
lines “median limit 0.1 %” and “p95 limit 1 %” labelled directly. b: books, |rel| against leg count (log-log),
IM filled, MM hollow, in the figure the largest absolute deviation (0.05 USDC at K up to 19.5 million USDC).

**Why:** P b shows the referee's point that the error does not grow with book size (2 to 245 legs). M b
splits the books by underlying, although HYPE has only one book. E a with double bars IM/MM is overloaded, and
E's footer overlaps the axis label.

**Requirements:** MM only in the CSV. The caption names one revert case (HYPE PM2, two rows) and the feed age
as a sentence: in the PM2 window no fill has a feed beyond the validation limits; over the whole sample
there are 448 and 45 respectively. The Addendum 1 number “1,165 of 1,165 account-days exact” can stand as a side line in b.

---

## 5 · README and X

**GIF.** 3D surface of PM2 for BTC, short, weekly from 2025-06-13 to 2026-09-17, plus, at every kept
BTC event, the day before, the day itself and the day after as hold frames with a banner (M, P). At the bottom a time strip with the
reference straddle per manager and the pure parameter steps (K against K_prev), so that market and
parameter movements stay separate (P). From E come the honesty rules: fixed scale over all frames
(`fit_limits`), date and block per frame, skipped days visible, expiries with an old feed grey instead of
interpolated, `results/p2/gif_frames.csv` with date, block, expiries and K min/median/max, a static
end frame. Format 1200 × 675, font at least 14 px at this size. The existing GIF has about 10 px.
One fixed iso-line (10 %) is highlighted, not “the one that moves the most”, because that would be a
selection after the fact.

**Cards (1600 × 900).**
1. **M “One short BTC straddle. Three margin engines.”** The numbers 30 / 20 / 10 % are recomputed. Correct the
   subtitle: “nearest listed expiry to 30 days (22 d on 17 Sep 2026)” instead of “about 30 days”.
   Add the line “capital for a hypothetical book, not a balance”. The vertical lines are called “parameter
   changes kept for H4”.
2. **Still of the surface** (P `social_t1_keyframe.png`) with M's sentence: “Almost everywhere one scenario sets
   the capital: spot ±14 % with vol up.” Fix the cut-off colour bar label.
3. **Verdict card H1 to H4** in E's grammar: per test estimator, interval, threshold and “pre-registered ·
   rejected/not rejected”. With placeholders until the final data run.

Reserve: P card 1 (−35 %). The number is right, but it is the same series as card 1, and title and subtitle
are cut off on the right. P card 2 only if both legs come from the same reference straddle and the title
does not say “almost free”, because capital is not risk. The card even shows less capital *with* the put
(10.0 against 11.9 %). M card 3 (fingerprint of 2026-08-20) only with the title “bundle”.

**Rejected:** P card 3. It compares a cell median pooled over regimes (0.90; from 2026-08-20 BTC 1.40,
ETH 1.14) with the median over maker-days, that is two different populations. And it draws ratios as
linear bars from 0.

---

## 6 · Gaps that a referee would ask about

1. **Structural lower bound of H1** (2.1). Sign lines in F2 and exploratory ρ within sign and
   within side. The text gives the lower bound as a way of reading the result, without changing the test.
2. **Regime dependence of the single contract** (2.2). Regime split in the F1 strip and in
   `fig_f1_regimes.csv`; restrict the sentence “book, not contract” in time.
3. **H2 and H3 over time.** No draft shows whether the medians are carried by the parameter regime. PM2 became
   35 % cheaper, so K_SM/K_PM2 rises mechanically. Exploratory rows per regime in `sens_h2.csv` and
   `sens_h3.csv`, grey in the forest. Alternatively a monthly median in the CSV (`fig_h3_series.csv` has `day`).
4. **Placebo support of H4** (2.5). ETH PM2 has 10 admissible days. Show this as a band in F5, give the day counts in F6c,
   request `h4_placebo_days.csv`.
5. **Overlapping H4 windows**: 6,527 of 84,919 fills counted twice. This belongs in F5, F6 and the text.
6. **Dose support of H4**: half of the pairs below 1 %, 11 % positive. Dose strip F6a and rug in F6b.
7. **Missing inference tables:** `fig_h4_fwl_bins.csv` (needed for F6b), the exploratory H1 rows, the
   regime rows for H2 and H3, `h4_placebo_days.csv`; optionally `h1_rho_draws.csv`. The figure layer computes
   none of these itself.
8. **Sample flow as a table, not as a slot:** 336,087 fills in the PM2 window → 331,813 in 173 occupied
   cells (H1). H2: 19,999 fills, 4 accounts, ETH and HYPE only, from 2025-09-04. H3: 1,943 maker-days, 9 accounts
   (25 days without options or snapshot). H4: 13 events, 475 pairs, 91,446 rows, 84,919 fills.
9. **Print size and font** (2.4). The check script must test the width and the smallest font after scaling,
   and for Paper 2 `savefig.bbox = "tight"` should not apply.
10. **One number per object**: T2c, F5c and card 1 show the same straddle from the same row of
    `reference_book.csv` (2.3).
11. **Event titles**: 2026-08-20 is a bundle. The grid was ±18 % until 2026-05-24, then ±17 %, and from 20 Aug
    ±14 %. The sentence “PM2 takes spot ±14 %” holds only for the last regime.
12. **Two cell sizes for F1**: do not put `fig_capital_by_manager.csv` (median per fill, as a fraction) next to
    `fig_edge_maps.csv` (ratio of sums) in the figure.

## 7 · For the check script `scripts/p2_figure_check.py`

- Every printed number against its source: T2 against `factors.csv` (exactly four rows), F1 against `fig_edge_maps.csv`,
  F5 against `reference_book.csv` and `events.csv`, A1 against `validation.csv`, all verdict bars against
  `h*.json`. The verdict line is rebuilt from `rule` and the bounds and must match `rejected`.
- Counts: crosses in F1 = cells under 200 fills (BTC: 10 per manager, 70 − 60 over both sides; all
  underlyings: 37 per manager), 173 points in F2 and in the F1 strip, symbols
  in F5 = 14 kept + 4 dropped, 13 rows and 475 ticks in F6a.
- Identity: κ in F1 = 100·`sum_K`/`sum_index` of `h1_cells.csv`. T2c, F5c and card 1 show the same
  straddle value.
- Form: PDF width 3.4 or 7.0 in ± 0.02, no font below 7 pt, exactly one 3D axis in the PDF (T1).
