# Figures of Paper 2: check list

Generated 2026-10-06 07:25 UTC with `scripts/p2_figure_check.py` from `results/p2`. Every row compares the value that the figure prints (its table `results/p2/fig_<slot>_*.csv`) with the file in `results/p2` it comes from, never with itself. Column *Build instruction*: the same number against the check number in `docs/paper2/FIGURE_SELECTION.md` (pilot cut 17 September 2026), where the slot has one.

**Result:** 233 of 233 checks yes; build instruction 108 of 108 yes; shape 22 of 22 yes; captions 9 of 9 equal.

## Check numbers

| Slot | Check | Value in figure | Value in results | yes/no | Build instruction |
|---|---|---|---|---|---|
| T1 | ts: block time of the surface | 1789632000 | 1789632000 | yes | yes |
| T1 | n_expiries: live expiries at the block | 15 | 15 | yes | yes |
| T1 | n_nodes_pm2: nodes PM2 | 740 | 740 | yes | yes |
| T1 | n_nodes_sm: nodes SM | 740 | 740 | yes | yes |
| T1 | pm2_min: PM2 K min, % of forward | 3.41803 | 3.41803 | yes | yes |
| T1 | pm2_median: PM2 K median, % of forward | 10.448 | 10.448 | yes | yes |
| T1 | pm2_max: PM2 K max, % of forward | 13.704 | 13.704 | yes | yes |
| T1 | sm_min: SM K min, % of forward | 12.3741 | 12.3741 | yes | yes |
| T1 | sm_median: SM K median, % of forward | 12.979 | 12.979 | yes | yes |
| T1 | sm_max: SM K max, % of forward | 15.0065 | 15.0065 | yes | yes |
| T1 | atm_tenor: ATM 30 d node, tenor in days | 30.4392 | 30.4392 | yes | yes |
| T1 | atm_pm2: PM2 ATM 30 d short, % of forward (title a) | 11.8259 | 11.8259 | yes | yes |
| T1 | atm_sm: SM ATM 30 d short, % of forward (title b) | 14.0803 | 14.0803 | yes | yes |
| T1 | n_sm_below_pm2: nodes where SM < PM2 | 9 | 9 | yes | yes |
| T1 | median_sm_over_pm2: median SM / PM2 over the nodes | 1.26088 | 1.26088 | yes | yes |
| T1 | n_outside_scale: values outside the colour scale [3; 15.5] | 0 | 0 | yes | yes |
| T1 | decomposition_pm2: PM2 rule decomposition = grid capital (max relative gap) | 4.90262e-15 | 4.90262e-15 | yes | yes |
| T1 | decomposition_sm: SM rule decomposition = grid capital (max relative gap) | 3.48163e-15 | 3.48163e-15 | yes | yes |
| T2 | rows: four probe rows in panel b | 4 | 4 | yes | yes |
| T2 | a_sm_R: a: SM requirement R, USDC | 211023 | 211023 | yes | yes |
| T2 | a_sm_minusV: a: SM value term -V, USDC | 496914 | 496914 | yes | yes |
| T2 | a_sm_Cnet: a: SM C - net = R - V, USDC (bar end, printed 708) | 707938 | 707938 | yes | yes |
| T2 | a_pm2_R: a: PM2 requirement R, USDC | 98834.9 | 98834.9 | yes | yes |
| T2 | a_pm2_minusV: a: PM2 value term -V, USDC | 496859 | 496859 | yes | yes |
| T2 | a_pm2_Cnet: a: PM2 C - net = R - V, USDC (bar end, printed 596) | 595694 | 595694 | yes | yes |
| T2 | b_17Sep_short_F_Cnet: b: 17 Sep, short, ratio on C - net | 2.33 | 2.33 | yes | yes |
| T2 | b_17Sep_short_F_R_engine: b: 17 Sep, short, ratio on R | 3.19 | 3.19 | yes | yes |
| T2 | b_17Sep_mixed_F_Cnet: b: 17 Sep, mixed, ratio on C - net | 11.86 | 11.86 | yes | yes |
| T2 | b_17Sep_mixed_F_R_engine: b: 17 Sep, mixed, ratio on R | 10.76 | 10.76 | yes | yes |
| T2 | b_24Sep_short_F_Cnet: b: 24 Sep, short, ratio on C - net | 1.46 | 1.46 | yes | yes |
| T2 | b_24Sep_short_F_R_engine: b: 24 Sep, short, ratio on R | 3.61 | 3.61 | yes | yes |
| T2 | b_24Sep_mixed_F_Cnet: b: 24 Sep, mixed, ratio on C - net | 1.19 | 1.19 | yes | yes |
| T2 | b_24Sep_mixed_F_R_engine: b: 24 Sep, mixed, ratio on R | 2.14 | 2.14 | yes | yes |
| T2 | c_K_pm2: c: PM2 capital of the straddle, % of forward (same value as F5 c and card 1) | 10.0339 | 10.0339 | yes | yes |
| T2 | c_K_sm: c: SM capital of the straddle, % of forward | 29.6109 | 29.6109 | yes | yes |
| T2 | c_ring: c: the ring sits on the argmin of the scenario P&L | 0 | 0 | yes | n/a |
| T2 | c_grid: c: spot grid of the core, half width | 0.14 | 0.14 | yes | yes |
| T2 | c_n_shocks: c: spot shocks on the x axis | 17 | 17 | yes | yes |
| F1 | cells in the grid | 210 | 210 | yes | yes |
| F1 | occupied cells | 173 | 173 | yes | yes |
| F1 | crosses (under 200 fills, incl. empty combinations) | 37 | 37 | yes | yes |
| F1 | crosses by currency | {BTC: 10, ETH: 2, HYPE: 25} | {BTC: 10, ETH: 2, HYPE: 25} | yes | yes |
| F1 | fills per cell = pm2 map | {BTC\|buy\|00-10\|2-7d: 2149, BTC\|buy\|00-10\|30-90d: 994, BTC\|buy\|00-10\|7-30d: 1933, BTC\|buy\|… | {BTC\|buy\|00-10\|2-7d: 2149, BTC\|buy\|00-10\|30-90d: 994, BTC\|buy\|00-10\|7-30d: 1933, BTC\|buy\|… | yes | n/a |
| F1 | fills and contracts equal in pm2, sm_pm2win, pm_pm2win | True | True | yes | n/a |
| F1 | kappa = 100 sum_K / sum_index of h1_cells (max abs gap) | 3.55271e-15 | 0 | yes | yes |
| F1 | printed kappa (two significant digits) and crosses | {BTC\|buy\|00-10\|2-7d: 0.12, BTC\|buy\|00-10\|30-90d: 0.47, BTC\|buy\|00-10\|7-30d: 0.20, BTC\|buy… | {BTC\|buy\|00-10\|2-7d: 0.12, BTC\|buy\|00-10\|30-90d: 0.47, BTC\|buy\|00-10\|7-30d: 0.20, BTC\|buy… | yes | n/a |
| F1 | kappa span of occupied cells by currency and side | {BTC\|buy: [0.0736079, 10.8554], BTC\|sell: [7.79838, 17.6902], ETH\|buy: [0.0802237, 14.525… | {BTC\|buy: [0.0736079, 10.8554], BTC\|sell: [7.79838, 17.6902], ETH\|buy: [0.0802237, 14.525… | yes | yes |
| F1 | q_SM min, max, cells, cells below 1 | [0.752032, 4.6692, 173, 86] | [0.752032, 4.6692, 173, 86] | yes | yes |
| F1 | q_PM min, max, cells, cells below 1 | [0.946187, 1.73585, 128, 2] | [0.946187, 1.73585, 128, 2] | yes | yes |
| F1 | median q_SM of the sell cells by currency | {BTC: 0.943303, ETH: 0.901761, HYPE: 0.875292} | {BTC: 0.943303, ETH: 0.901761, HYPE: 0.875292} | yes | yes |
| F1 | regimes R1 to R4 add up to the maps (relative <= 1e-9) | True | True | yes | n/a |
| F1 | R4 median q_SM of the sell cells by currency | {BTC: 1.39824, ETH: 1.14004, HYPE: 1.44399} | {BTC: 1.39824, ETH: 1.14004, HYPE: 1.44399} | yes | yes |
| F1 | regime bounds = BTC PM2 events | [1769142245, 1779595507, 1787263765] | [1769142245, 1779595507, 1787263765] | yes | n/a |
| F1 | no strip mark outside the x axis | 0 | 0 | yes | n/a |
| F2 | points in panel b | 173 | 173 | yes | yes |
| F2 | points in panel b = occupied cells of h1_cells | 173 | 173 | yes | n/a |
| F2 | cells and crosses in panel a | [210, 37] | [210, 37] | yes | yes |
| F2 | sign line after the cells with A_bp > 0 | 99.5 | 99.5 | yes | yes |
| F2 | cells with A_bp > 0 / <= 0 / all, by side | {buy: [61, 26, 87], sell: [38, 48, 86]} | {buy: [61, 26, 87], sell: [38, 48, 86]} | yes | yes |
| F2 | hatched = B_bp < 0 = A_bp <= 0 (sign(A) = sign(B)) | [BTC\|buy\|00-10\|<=2d, BTC\|buy\|10-25\|<=2d, BTC\|buy\|25-40\|2-7d, BTC\|buy\|25-40\|<=2d, BTC\|buy\|… | [BTC\|buy\|00-10\|<=2d, BTC\|buy\|10-25\|<=2d, BTC\|buy\|25-40\|2-7d, BTC\|buy\|25-40\|<=2d, BTC\|buy\|… | yes | n/a |
| F2 | printed B_bp (sells in bp, buys in per cent) and crosses | {BTC\|buy\|00-10\|2-7d: 23, BTC\|buy\|00-10\|30-90d: 13, BTC\|buy\|00-10\|7-30d: 14, BTC\|buy\|00-10… | {BTC\|buy\|00-10\|2-7d: 23, BTC\|buy\|00-10\|30-90d: 13, BTC\|buy\|00-10\|7-30d: 14, BTC\|buy\|00-10… | yes | n/a |
| F2 | every number in a cell at most four characters | True | True | yes | n/a |
| F2 | B_bp of panel a = h1_cells | 0 | 0 | yes | n/a |
| F2 | ranks and rank intervals of panel b = h1_cells (max abs gap) | 0 | 0 | yes | n/a |
| F2 | ten largest \|rank_shift\| (ties by cell id) | [BTC\|buy\|00-10\|2-7d, BTC\|buy\|00-10\|30-90d, BTC\|buy\|00-10\|7-30d, BTC\|buy\|00-10\|<=2d, BTC\|b… | [BTC\|buy\|00-10\|2-7d, BTC\|buy\|00-10\|30-90d, BTC\|buy\|00-10\|7-30d, BTC\|buy\|00-10\|<=2d, BTC\|b… | yes | n/a |
| F2 | header line = verdict rebuilt from h1.json rule and bounds | registered: 0.90 [0.88, 0.91] → rejected | registered: 0.90 [0.88, 0.91] → rejected | yes | n/a |
| F2 | sample line: cells and day clusters | 173 cells · 463 day clusters | 173 cells · 463 day clusters | yes | yes |
| F2 | forest rows (stat, lo, hi) = h1.json and sensitivity.json | {h1.json: [0.902944, 0.880564, 0.907433], sensitivity.json:a_maps.pm_pm2_window: [0.90764… | {h1.json: [0.902944, 0.880564, 0.907433], sensitivity.json:a_maps.pm_pm2_window: [0.90764… | yes | n/a |
| F2 | fills in occupied cells (panel a) = h1.json n_fills | 331813 | 331813 | yes | yes |
| F2 | cells present in every replicate | 173 | 173 | yes | yes |
| F2 | kappa span of the occupied cells | [0.0736079, 38.7334] | [0.0736079, 38.7334] | yes | yes |
| F3 | verdict line | fig_f3_b.csv header: figure 'registered: 0.035 [0.031, 0.039] → not rejected'; h2.json gi… | h2.json rule, threshold, lo, hi, rejected | yes | n/a |
| F3 | sample line | fig_f3_b.csv header: missing []; fills by ccy sum 19999, n 19999, n_sample 20000 | h2.json accounts, fills_by_ccy, n, n_sample, n_days | yes | n/a |
| F3 | registered row | fig_f3_b.csv registered: figure 0.034540122450644445, [0.03070183757603388, 0.03855716844… | h2.json and sens_h2.csv ratio/all | yes | n/a |
| F3 | other forest rows | fig_f3_b.csv: 11 rows against sens_h2.csv; mismatched [] | sens_h2.csv | yes | n/a |
| F3 | account rows | fig_f3_b.csv label=*: figure accounts ['M10', 'M3', 'M5', 'M8'] with 19999 fills; h2.json… | h2.json accounts and n | yes | n/a |
| F3 | 62 bins, two open, sum n | fig_h2_dist.csv all/ratio: 62 bins sum to 19999.0; h2.json n 19999 | h2.json n | yes | n/a |
| F3 | ECDF steps | fig_f3_a.csv ecdf: 61 steps against the cumulative bins | fig_h2_dist.csv hist | yes | n/a |
| F3 | ECDF at 0 | fig_f3_a.csv ecdf x=0: ECDF(0) 0.41962098104905243; share_le_0 0.41962098104905243; h2.js… | h2.json share_nonpositive, fig_h2_dist.csv share_le_0 | yes | n/a |
| F3 | band shares | fig_f3_a.csv band: free 42 %; cheap 30 %; partial 24 %; full 4 % | fig_h2_dist.csv hist and share_le_0 | yes | n/a |
| F3 | overflows | fig_f3_a.csv overflow and ECDF ends: 15.8 % below −1; 0.0 % above 2 | fig_h2_dist.csv open bins | yes | n/a |
| F3 | median bar | fig_f3_a.csv median: bar 0.03070183757603388 to 0.03855716844133305, circle 0.03454012245… | h2.json stat, lo, hi | yes | n/a |
| F4 | verdict line | fig_f4_b.csv header: figure 'registered: 4.75 [4.66, 4.82] → not rejected'; h3.json gives… | h3.json rule, threshold, lo, hi, rejected | yes | n/a |
| F4 | sample line | fig_f4_b.csv header: missing []; accounts sum 1943, ok rows 1943, h3.json n 1943 | h3.json accounts, n, n_days, status_counts; fig_h3_series.csv | yes | n/a |
| F4 | registered row | fig_f4_b.csv registered: figure 4.7467261022171625, [4.661926808686567, 4.823628547372672… | h3.json and sens_h3.csv sm_pm2/all | yes | n/a |
| F4 | other forest rows | fig_f4_b.csv: 12 rows against sens_h3.csv; mismatched [] | sens_h3.csv | yes | n/a |
| F4 | legacy PM row | fig_f4_b.csv pm_pm2_be: legacy row n 1 640; sens_h3.csv n 1640 | sens_h3.csv pm_pm2_be/all | yes | n/a |
| F4 | maker-days per bin | fig_f4_a.csv bin n: maker-days per bin [41, 29, 57, 170, 215, 431, 909, 91]; series [41, … | fig_h3_series.csv ok rows, h3.json n | yes | n/a |
| F4 | bin quantiles | fig_f4_a.csv median, p25, p75: bins off: [] | fig_h3_series.csv ratio_sm_pm2 | yes | n/a |
| F4 | counterfactual days | fig_f4_a.csv counterfactual: SM counterfactual: 1 431 of 1 943 maker-days; legs >= 64: 14… | h3.json days_over_63_options; fig_h3_series.csv | yes | n/a |
| F4 | threshold line | fig_f4_a.csv threshold: dashed line at 2.0; h3.json 2.0 | h3.json threshold | yes | n/a |
| F5 | f5.b.events: event symbols in b = rows of events.csv | 18 | 18 | yes | yes |
| F5 | f5.b.status_counts: filled / half filled / hollow symbols | {dropped: 4, kept_no_cell: 1, panel: 13} | {dropped: 4, kept_no_cell: 1, panel: 13} | yes | yes |
| F5 | f5.b.status_ids: filled symbols are exactly kept & panel_cells > 0 (events.csv) | {BTC-pm-20240612: dropped, BTC-pm-20250222: panel, BTC-pm2-20251010: dropped, BTC-pm2-202… | {BTC-pm-20240612: dropped, BTC-pm-20250222: panel, BTC-pm2-20251010: dropped, BTC-pm2-202… | yes | n/a |
| F5 | f5.b.panel_cells: panel cells of the filled events = h4.json cell_events | 475 | 475 | yes | yes |
| F5 | f5.b.jumps: effect of the parameters alone, log-% (reference_book.csv) | {BTC-pm-20240612: 0, BTC-pm-20250222: -18.5637, BTC-pm2-20251010: 0, BTC-pm2-20260108: 1.… | {BTC-pm-20240612: 0, BTC-pm-20250222: -18.5637, BTC-pm2-20251010: 0, BTC-pm2-20260108: 1.… | yes | yes |
| F5 | f5.b.printed_jumps: printed numbers = signed whole log-% of reference_book.csv | {BTC-pm-20240612: 0, BTC-pm-20250222: −19, BTC-pm2-20251010: 0, BTC-pm2-20260108: +2, BTC… | {BTC-pm-20240612: 0, BTC-pm-20250222: −19, BTC-pm2-20251010: 0, BTC-pm2-20260108: +2, BTC… | yes | n/a |
| F5 | f5.b.windows: +-14 day windows of the kept events (events.csv) | {BTC-pm-20250222: [1739044357, 1741463557], BTC-pm2-20260108: [1766703049, 1769122249], B… | {BTC-pm-20250222: [1739044357, 1741463557], BTC-pm2-20260108: [1766703049, 1769122249], B… | yes | n/a |
| F5 | f5.b.timeline_rows: grey ticks per rail = rows of params/{CCY}_{m}.json | {BTC PM2: 23, BTC legacy PM: 7, ETH PM2: 22, ETH legacy PM: 6, HYPE PM2: 21} | {BTC PM2: 23, BTC legacy PM: 7, ETH PM2: 22, ETH legacy PM: 6, HYPE PM2: 21} | yes | n/a |
| F5 | f5.b.placebo_days: placebo days per rail (h4.json placebo.admissible_days) | {BTC PM2: 54, BTC legacy PM: 363, ETH PM2: 10, ETH legacy PM: 319, HYPE PM2: 67} | {BTC PM2: 54, BTC legacy PM: 363, ETH PM2: 10, ETH legacy PM: 319, HYPE PM2: 67} | yes | yes |
| F5 | f5.a.shares: stacked shares = manager_oi_share.csv after fillna(0) | [0.781064, 0.218936, 0, 0.460144, 0.539856, 0, 0.318577, 0.681423, 0, 0.260018, 0.739982,… | [0.781064, 0.218936, 0, 0.460144, 0.539856, 0, 0.318577, 0.681423, 0, 0.260018, 0.739982,… | yes | n/a |
| F5 | f5.a.pm2_last_month: PM2 share of option OI in the last month (September 2026) | {BTC: 0.909567, ETH: 0.71894, HYPE: 0.879198} | {BTC: 0.909567, ETH: 0.71894, HYPE: 0.879198} | yes | yes |
| F5 | f5.c.btc_last: BTC reference straddle on the last day, % of forward (SM, legacy PM, PM2) | [29.6109, 19.6794, 10.0339] | [29.6109, 19.6794, 10.0339] | yes | yes |
| F5 | f5.c.eth_last: ETH reference straddle on the last day (CSV only) | [29.7142, 19.4077, 10.9352] | [29.7142, 19.4077, 10.9352] | yes | yes |
| F5 | f5.c.hype_last: HYPE reference straddle on the last day (CSV only) | [59.3634, nan, 20.1865] | [59.3634, nan, 20.1865] | yes | yes |
| F5 | f5.c.last_day: direct labels are the values of 17 Sep 2026 | 2026-09-17 | 2026-09-17 | yes | yes |
| F5 | f5.c.printed: printed direct labels | [SM 29.6 %; legacy PM 19.7 %; PM2 10.0 %] | [SM 29.6 %; legacy PM 19.7 %; PM2 10.0 %] | yes | n/a |
| F6 | f6.a.rows: rows of a = events with panel cells (fig_h4_events.csv n_cells > 0) | 13 | 13 | yes | yes |
| F6 | f6.a.pairs_per_event: symbols per row = n_cells of fig_h4_events.csv | {BTC-pm-20250222: 25, BTC-pm2-20260108: 25, BTC-pm2-20260123: 27, BTC-pm2-20260524: 38, B… | {BTC-pm-20250222: 25, BTC-pm2-20260108: 25, BTC-pm2-20260123: 27, BTC-pm2-20260524: 38, B… | yes | yes |
| F6 | f6.a.pairs_total: symbols in a = h4.json cell_events | 475 | 475 | yes | yes |
| F6 | f6.a.doses: dose of every symbol = h4_doses.csv on the panel pairs, log-% | [0, -3.47239e-06, -0.0584081, 0, -3.57764e-06, -2.50249, -0.097379, 0, -0.000108836, -0.2… | [0, -3.47239e-06, -0.0584081, 0, -3.57764e-06, -2.50249, -0.097379, 0, -0.000108836, -0.2… | yes | n/a |
| F6 | f6.a.dose_stats: median, min, max (log-%); % positive, % below -1, % with \|dose\| < 1 | [-0.633617, -44.2078, 2.20238, 11.1579, 48.6316, 44.4211] | [-0.633617, -44.2078, 2.20238, 11.1579, 48.6316, 44.4211] | yes | yes |
| F6 | f6.a.band: printed share of pairs with \|dose\| < 1 log-% | \|dose\| < 1 log-%: 44.4 % of pairs | \|dose\| < 1 log-%: 44.4 % of pairs | yes | n/a |
| F6 | f6.a.medians: median bar per row = median dose of the event's pairs | [-12.3632, 1.177, 0, -0.946601, -20.7195, -12.2334, 1.17629, 0, -0.00347127, -11.9695, 0,… | [-12.3632, 1.177, 0, -0.946601, -20.7195, -12.2334, 1.17629, 0, -0.00347127, -11.9695, 0,… | yes | n/a |
| F6 | f6.head.panel: header numbers = h4_panel.parquet | {day_ccy_effects: 322, day_clusters: 141, events: 13, fills: 84919, fills_in_two_windows:… | {day_ccy_effects: 322, day_clusters: 141, events: 13, fills: 84919, fills_in_two_windows:… | yes | yes |
| F6 | f6.head.h4: header numbers = h4.json | {day_ccy_effects: 322, day_clusters: 141, events: 13, fills: 84919, fills_in_two_windows:… | {day_ccy_effects: 322, day_clusters: 141, events: 13, fills: 84919, fills_in_two_windows:… | yes | n/a |
| F6 | f6.b.line: slope of the line x 100 = h4.json stat (beta) | -4.59923 | -4.59923 | yes | n/a |
| F6 | f6.b.fwl_slope: fwl_slope of fig_h4_fwl_bins.csv = h4.json stat | -4.59923 | -4.59923 | yes | n/a |
| F6 | f6.b.bins: 20 bins covering all panel rows (h4.json n) | [20, 91446] | [20, 91446] | yes | n/a |
| F6 | f6.b.printed: printed beta and interval = h4.json | β = −4.60 bp per log unit 90 % interval [−26.0, 16.6], descriptive | β = −4.60 bp per log unit 90 % interval [−26.0, 16.6], descriptive | yes | n/a |
| F6 | f6.c.placebo: placebo betas in the histogram = h4_placebo.csv | [-101.296, -89.0711, -81.9797, -71.317, -63.6736, -61.5857, -61.1403, -57.8752, -56.5707,… | [-101.296, -89.0711, -81.9797, -71.317, -63.6736, -61.5857, -61.1403, -57.8752, -56.5707,… | yes | n/a |
| F6 | f6.c.n_placebo: finite placebo betas in the histogram = finite betas of h4_placebo.csv | 100 | 100 | yes | yes |
| F6 | f6.c.p95: P95 line = numpy quantile of h4_placebo.csv = h4.json placebo.p95 | [23.4099, 23.4099] | [23.4099, 23.4099] | yes | n/a |
| F6 | f6.c.estimate: estimate line = h4.json stat | -4.59923 | -4.59923 | yes | n/a |
| F6 | f6.c.criteria: check list = h4.json criteria (p, beta > 0, beta > P95) | [False, False, 0.6224] | [False, False, 0.6224] | yes | n/a |
| F6 | f6.c.verdict: printed verdict = h4.json rejected | H4: rejected | H4: rejected | yes | n/a |
| F6 | f6.c.placebo_days: placebo days per timeline = h4.json placebo.admissible_days | placebo days: BTC 54 · ETH 10 · HYPE 67 · legacy 363 / 319 | placebo days: BTC 54 · ETH 10 · HYPE 67 · legacy 363 / 319 | yes | yes |
| F6 | f6.d.rows: forest rows = h4.json and sensitivity_h4.json by_ccy (stat, lo, hi, clusters) | {BTC only: [-3.41805, -10.5088, 3.56931, 126], ETH only: [-1.89895, -8.36344, 4.67704, 12… | {BTC only: [-3.41805, -10.5088, 3.56931, 126], ETH only: [-1.89895, -8.36344, 4.67704, 12… | yes | n/a |
| F6 | f6.d.hatch: hatching of the registered row ends at max(0, h4.json placebo.p95) | 23.4099 | 23.4099 | yes | n/a |
| A1 | a_n_BTC_sm: a: n printed for BTC SM | 100 | 100 | yes | yes |
| A1 | a_n_BTC_pm: a: n printed for BTC legacy PM | 100 | 100 | yes | yes |
| A1 | a_n_BTC_pm2: a: n printed for BTC PM2 | 100 | 100 | yes | yes |
| A1 | a_n_ETH_sm: a: n printed for ETH SM | 100 | 100 | yes | yes |
| A1 | a_n_ETH_pm: a: n printed for ETH legacy PM | 100 | 100 | yes | yes |
| A1 | a_n_ETH_pm2: a: n printed for ETH PM2 | 100 | 100 | yes | yes |
| A1 | a_n_HYPE_sm: a: n printed for HYPE SM | 100 | 100 | yes | yes |
| A1 | a_n_HYPE_pm2: a: n printed for HYPE PM2 | 99 | 99 | yes | yes |
| A1 | a_zeros_BTC_sm: a: exact zeros in the strip, BTC SM | 45 | 45 | yes | yes |
| A1 | a_zeros_BTC_pm: a: exact zeros in the strip, BTC legacy PM | 0 | 0 | yes | yes |
| A1 | a_zeros_BTC_pm2: a: exact zeros in the strip, BTC PM2 | 19 | 19 | yes | yes |
| A1 | a_zeros_ETH_sm: a: exact zeros in the strip, ETH SM | 53 | 53 | yes | yes |
| A1 | a_zeros_ETH_pm: a: exact zeros in the strip, ETH legacy PM | 0 | 0 | yes | yes |
| A1 | a_zeros_ETH_pm2: a: exact zeros in the strip, ETH PM2 | 15 | 15 | yes | yes |
| A1 | a_zeros_HYPE_sm: a: exact zeros in the strip, HYPE SM | 49 | 49 | yes | yes |
| A1 | a_zeros_HYPE_pm2: a: exact zeros in the strip, HYPE PM2 | 0 | 0 | yes | yes |
| A1 | a_zeros_total: a: exact zeros in the strip, all rows | 181 | 181 | yes | yes |
| A1 | a_median_BTC_sm: a: median tick, BTC SM | 1.44202e-10 | 1.44202e-10 | yes | n/a |
| A1 | a_p95_BTC_sm: a: p95 tick, BTC SM | 6.90937e-09 | 6.90937e-09 | yes | n/a |
| A1 | a_median_BTC_pm: a: median tick, BTC legacy PM | 2.41042e-09 | 2.41042e-09 | yes | n/a |
| A1 | a_p95_BTC_pm: a: p95 tick, BTC legacy PM | 1.48855e-08 | 1.48855e-08 | yes | n/a |
| A1 | a_median_BTC_pm2: a: median tick, BTC PM2 | 1.77912e-10 | 1.77912e-10 | yes | n/a |
| A1 | a_p95_BTC_pm2: a: p95 tick, BTC PM2 | 1.4164e-08 | 1.4164e-08 | yes | n/a |
| A1 | a_median_ETH_sm: a: median tick, ETH SM | 0 | 0 | yes | n/a |
| A1 | a_p95_ETH_sm: a: p95 tick, ETH SM | 9.4887e-09 | 9.4887e-09 | yes | n/a |
| A1 | a_median_ETH_pm: a: median tick, ETH legacy PM | 3.17855e-09 | 3.17855e-09 | yes | n/a |
| A1 | a_p95_ETH_pm: a: p95 tick, ETH legacy PM | 2.01797e-08 | 2.01797e-08 | yes | n/a |
| A1 | a_median_ETH_pm2: a: median tick, ETH PM2 | 7.40067e-10 | 7.40067e-10 | yes | n/a |
| A1 | a_p95_ETH_pm2: a: p95 tick, ETH PM2 | 2.31029e-08 | 2.31029e-08 | yes | n/a |
| A1 | a_median_HYPE_sm: a: median tick, HYPE SM | 9.18132e-12 | 9.18132e-12 | yes | n/a |
| A1 | a_p95_HYPE_sm: a: p95 tick, HYPE SM | 5.58808e-09 | 5.58808e-09 | yes | n/a |
| A1 | a_median_HYPE_pm2: a: median tick, HYPE PM2 | 1.67766e-09 | 1.67766e-09 | yes | n/a |
| A1 | a_p95_HYPE_pm2: a: p95 tick, HYPE PM2 | 1.54843e-08 | 1.54843e-08 | yes | n/a |
| A1 | a_largest_median: a: largest median over the rows (ETH legacy PM) | 3.17855e-09 | 3.17855e-09 | yes | yes |
| A1 | a_largest_single: a: largest single IM deviation drawn | 8.88151e-08 | 8.88151e-08 | yes | yes |
| A1 | a_largest_single_cell: a: the largest single IM deviation is ETH PM2 | ETH pm2 | ETH pm2 | yes | yes |
| A1 | a_threshold_median: median bound (registered) | 0.001 | 0.001 | yes | yes |
| A1 | a_threshold_p95: P95 bound (registered) | 0.01 | 0.01 | yes | yes |
| A1 | a_revert_cases: reverting cases left out (caption) | 1 | 1 | yes | yes |
| A1 | a_revert_rows: reverting rows (IM and MM) | 2 | 2 | yes | yes |
| A1 | b_points: b: IM book points drawn | 77 | 77 | yes | yes |
| A1 | b_legs_min: b: fewest legs | 2 | 2 | yes | yes |
| A1 | b_legs_max: b: most legs | 245 | 245 | yes | yes |
| A1 | b_largest: b: largest book IM deviation (ETH legacy PM) | 3.44957e-08 | 3.44957e-08 | yes | yes |
| A1 | b_largest_miss: b: largest miss, USDC (printed 0.05) | 0.0502857 | 0.0502857 | yes | yes |
| A1 | b_K_max: b: K up to, USDC (printed 19.5 M) | 1.94947e+07 | 1.94947e+07 | yes | yes |
| A1 | b_books: b: books (book x underlying) | 26 | 26 | yes | yes |
| A1 | b_maker_days: b: maker-days | 20 | 20 | yes | yes |
| A1 | b_books_BTC: b: books of BTC | 7 | 7 | yes | yes |
| A1 | b_books_ETH: b: books of ETH | 18 | 18 | yes | yes |
| A1 | b_books_HYPE: b: books of HYPE | 1 | 1 | yes | yes |
| A1 | feed_age: Appendix A: no PM2-window fill uses a feed older than the validation limits | 1 | 1 | yes | yes |
| A1 | spot_stale: Appendix A: PM2-window fills with a spot price older than the spot heartbeat | 17 | 17 | yes | n/a |
| GIF | last frame = T1 a: nodes matched, largest gap of K (USDC) | [740, 1.81899e-12] | [740, 0] | yes | n/a |
| GIF | steps of the straddle in the time strip (simple %) | {BTC-pm2-20260108: +1.6 %, BTC-pm2-20260123: −10 %, BTC-pm2-20260524: −7.5 %, BTC-pm2-202… | {BTC-pm2-20260108: +1.6 %, BTC-pm2-20260123: −10 %, BTC-pm2-20260524: −7.5 %, BTC-pm2-202… | yes | n/a |
| GIF | frames drawn / skipped (no live expiry) | [80, 0] | [80, 0] | yes | n/a |
| GIF | last frame block time = T1 block | 1789632000 | 1789632000 | yes | n/a |
| GIF | colour scale covers every node or ends in arrows (clim, extend) | [3, 19, neither] | [3.4086, 18.8207] | yes | n/a |
| GIF | MP4 next to the GIF (section 8) | docs/media/p2_btc_capital_surface.mp4 | docs/media/p2_btc_capital_surface.mp4 | yes | n/a |
| S1 | card number last_sm (printed 30 %) | 29.6109 | 29.6109 | yes | n/a |
| S1 | card number last_pm (printed 20 %) | 19.6794 | 19.6794 | yes | n/a |
| S1 | card number last_pm2 (printed 10 %) | 10.0339 | 10.0339 | yes | n/a |
| S1 | card number tenor_days (printed 22 d) | 22 | 22 | yes | n/a |
| S1 | card number step_BTC-pm-20250222 (printed −17 %) | -16.9425 | -16.9425 | yes | n/a |
| S1 | card number step_BTC-pm2-20260108 (printed +2 %) | 1.61076 | 1.61076 | yes | n/a |
| S1 | card number step_BTC-pm2-20260123 (printed −10 %) | -9.95623 | -9.95623 | yes | n/a |
| S1 | card number step_BTC-pm2-20260524 (printed −8 %) | -7.54196 | -7.54196 | yes | n/a |
| S1 | card number step_BTC-pm2-20260820 (printed −23 %) | -22.9303 | -22.9303 | yes | n/a |
| S2 | card number K_pm2_call (printed 12.0 %) | 12.0169 | 12.0169 | yes | n/a |
| S2 | card number K_pm2_book (printed 10.0 %) | 10.0339 | 10.0339 | yes | n/a |
| S2 | card number K_sm_call (printed 14.7 %) | 14.6558 | 14.6558 | yes | n/a |
| S2 | card number K_sm (printed 29.6 %) | 29.6109 | 29.6109 | yes | n/a |
| S2 | card number tenor_days (printed 22 days) | 22 | 22 | yes | n/a |
| S3 | card number h1_stat (printed ρ 0.90 [0.88, 0.91]) | 0.902944 | 0.902944 | yes | n/a |
| S3 | card number h1_lo (printed ρ 0.90 [0.88, 0.91]) | 0.880564 | 0.880564 | yes | n/a |
| S3 | card number h1_hi (printed ρ 0.90 [0.88, 0.91]) | 0.907433 | 0.907433 | yes | n/a |
| S3 | card number h1_threshold (printed ρ 0.90 [0.88, 0.91]) | 0.5 | 0.5 | yes | n/a |
| S3 | card number h1_rejected (printed rejected) | 1 | 1 | yes | n/a |
| S3 | card number h2_stat (printed median 0.035 [0.031, 0.039]) | 0.0345401 | 0.0345401 | yes | n/a |
| S3 | card number h2_lo (printed median 0.035 [0.031, 0.039]) | 0.0307018 | 0.0307018 | yes | n/a |
| S3 | card number h2_hi (printed median 0.035 [0.031, 0.039]) | 0.0385572 | 0.0385572 | yes | n/a |
| S3 | card number h2_threshold (printed median 0.035 [0.031, 0.039]) | 0.5 | 0.5 | yes | n/a |
| S3 | card number h2_rejected (printed not rejected) | 0 | 0 | yes | n/a |
| S3 | card number h3_stat (printed median 4.75 [4.66, 4.82]) | 4.74673 | 4.74673 | yes | n/a |
| S3 | card number h3_lo (printed median 4.75 [4.66, 4.82]) | 4.66193 | 4.66193 | yes | n/a |
| S3 | card number h3_hi (printed median 4.75 [4.66, 4.82]) | 4.82363 | 4.82363 | yes | n/a |
| S3 | card number h3_threshold (printed median 4.75 [4.66, 4.82]) | 2 | 2 | yes | n/a |
| S3 | card number h3_rejected (printed not rejected) | 0 | 0 | yes | n/a |
| S3 | card number h4_stat (printed β = −4.6, one-sided p = 0.62, P95 23.4) | -4.59923 | -4.59923 | yes | n/a |
| S3 | card number h4_p (printed β = −4.6, one-sided p = 0.62, P95 23.4) | 0.6224 | 0.6224 | yes | n/a |
| S3 | card number h4_p95 (printed β = −4.6, one-sided p = 0.62, P95 23.4) | 23.4099 | 23.4099 | yes | n/a |
| S3 | card number h4_rejected (printed rejected) | 1 | 1 | yes | n/a |
| F2 | caption "grey band": a row of kind band (h1_sign.sign_floor) | fig_f2_c.csv | drawn | yes | n/a |
| F2 | caption "exploratory rows": rows of kind exploratory | fig_f2_c.csv | drawn | yes | n/a |
| F3 | caption "per subaccount": rows with group label= | fig_f3_b.csv | drawn | yes | n/a |
| F3 | caption "per parameter regime": rows with group regime= | fig_f3_b.csv | drawn | yes | n/a |
| F4 | caption "by the manager of the subaccount": rows with group account_manager= | fig_f4_b.csv | drawn | yes | n/a |
| F4 | caption "by parameter regime": rows with group regime= | fig_f4_b.csv | drawn | yes | n/a |
| F4 | caption "by book size": rows sm_pm2_le63 and sm_pm2_gt63 | fig_f4_b.csv | drawn | yes | n/a |
| F4 | caption "on the same BTC and ETH legs": row sm_pm2_be | fig_f4_b.csv | drawn | yes | n/a |
| F2 | forest: every estimate inside its interval | fig_f2_c.csv: 14 rows | [] | yes | n/a |
| F3 | forest: every estimate inside its interval | fig_f3_b.csv: 12 rows | [] | yes | n/a |
| F4 | forest: every estimate inside its interval | fig_f4_b.csv: 13 rows | [] | yes | n/a |
| F6 | forest: every estimate inside its interval | fig_f6_d.csv: 4 rows | [] | yes | n/a |

## Shape

| File | measured | target | yes/no |
|---|---|---|---|
| `t1.pdf` | 6.840 × 4.200 in | 6.84 × 4.2 in | yes |
| `t2.pdf` | 6.840 × 2.600 in | 6.84 × 2.6 in | yes |
| `f1.pdf` | 6.840 × 3.900 in | 6.84 × 3.9 in | yes |
| `f2.pdf` | 6.840 × 6.200 in | 6.84 × 6.2 in | yes |
| `f3.pdf` | 3.290 × 4.000 in | 3.29 × 4.0 in | yes |
| `f4.pdf` | 3.290 × 4.000 in | 3.29 × 4.0 in | yes |
| `f5.pdf` | 6.840 × 4.470 in | 6.84 × 4.47 in | yes |
| `f6.pdf` | 6.840 × 4.200 in | 6.84 × 4.2 in | yes |
| `a1.pdf` | 6.840 × 2.500 in | 6.84 × 2.5 in | yes |
| `docs/media/p2_btc_capital_surface.gif` | 5.19 MB | ≤ 8 MB | yes |
| `paper2/social/s1_three_engines.png` | 1600 × 900 px | 1600 × 900 px | yes |
| `paper2/social/s2_straddle_vs_call.png` | 1600 × 900 px | 1600 × 900 px | yes |
| `paper2/social/s3_verdicts.png` | 1600 × 900 px | 1600 × 900 px | yes |
| `t1.pdf set in main.tex` | 7.00 pt × 1.0004 = 7.00 pt | ≥ 7 pt | yes |
| `t2.pdf set in main.tex` | 7.00 pt × 1.0004 = 7.00 pt | ≥ 7 pt | yes |
| `f1.pdf set in main.tex` | 7.00 pt × 1.0004 = 7.00 pt | ≥ 7 pt | yes |
| `f2.pdf set in main.tex` | 7.00 pt × 1.0004 = 7.00 pt | ≥ 7 pt | yes |
| `f3.pdf set in main.tex` | 7.00 pt × 1.0020 = 7.01 pt | ≥ 7 pt | yes |
| `f4.pdf set in main.tex` | 7.00 pt × 1.0020 = 7.01 pt | ≥ 7 pt | yes |
| `f5.pdf set in main.tex` | 7.00 pt × 1.0004 = 7.00 pt | ≥ 7 pt | yes |
| `f6.pdf set in main.tex` | 7.00 pt × 1.0004 = 7.00 pt | ≥ 7 pt | yes |
| `a1.pdf set in main.tex` | 7.00 pt × 1.0004 = 7.00 pt | ≥ 7 pt | yes |

## Captions: `paper2/main.tex` against `figures_p2.CAPTIONS`

Reported, not changed. `\PH{key}` of the module caption stands for any text in the manuscript; exceptions from `CAPTION_EXCEPTIONS` in `scripts/p2_build.py`.

| Slot | Status | Note |
|---|---|---|
| T1 | equal |  |
| T2 | equal |  |
| F1 | equal |  |
| F2 | equal with exception | Paper 1 draws its map per notional (its Figure 5) with the net edge per contract over the… |
| F3 | equal |  |
| F4 | equal |  |
| F5 | equal |  |
| F6 | equal |  |
| A1 | equal |  |
