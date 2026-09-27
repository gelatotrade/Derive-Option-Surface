# Number check Paper 2

Generated 2026-09-27 11:28 UTC with `scripts/p2_number_check.py` from `paper2/main.tex` against `results/p2` and the list of constants of the pre-registration. Rules in the header of the script.

Checked are the abstract, the prose of all sections and subsections including their titles, and all figure captions; not checked are the title, keywords, cross-references, citations, URLs, display formulas and the bibliography. Every number, date and clock time is bound by `% src source printed` in its unit to exactly one source, in the order of the text; nothing is searched. "Text count": a count word that the sentence itself makes evident (`text:`), without a data source.

## Result

- Numbers, dates and commits in the text: 352
- Result: 251
- Constant: 75
- Commit date: 4
- Text count: 17
- Commit: 5

**Errors: 0** (none)

Text counts (without a data source, for review):

- Introduction: `four` (text:contributions) … nue actually applies. The paper makes four contributions: a capital map, compute …
- caption fig:t2: `30` (text:refbook_target_days) … 2026, on the listed expiry nearest to 30 days (22 days), in per cent of the fo …
- The engine and what it returns: `Two` (text:two_engines) … single contracts on the BTC surface. Two engines implement the managers. The o …
- The engine and what it returns: `two` (text:two_semantics) … e contracts on 25 September 2026, the two semantics differed in   capital by a …
- The engine and what it returns: `two` (text:two_books) … ard to   margin of 11.86 and 1.19 for two books at blocks 44810149 and 45110142 …
- caption fig:f2: `two` (text:denominators) … The map in two denominators ( ). Panel a is net edge …
- caption fig:f2: `ten` (text:largest_moves) … the 90 per cent rank intervals of the ten largest moves. Panel c is the registe …
- Results / A fill in a maker's book (H2): `95th` (text:quantile_level) … nd more than 0.63 of it, and from the 95th percentile on a fill binds about its …
- caption fig:f5: `two` (text:two_events) … May 2026 overlap, so 6527 fills enter two events. Black dashes below each line …
- caption fig:f5: `30` (text:refbook_target_days) … rward on the listed expiry nearest to 30 days, one contract per leg, in per ce …
- caption fig:f6: `ten` (text:reading_aid_pct) … l cheaper. To read the slope: capital ten per cent cheaper is a dose of -0.105 …
- Results / The price of capital (H4): `ten` (text:reading_aid_pct) … s from -41.6 to 29.7, and for capital ten per cent cheaper from a change in the …
- Post hoc and exploratory results: `5th` (text:shuffle_percentile) … up give a of 0.734 on average, with a 5th to 95th percentile from 0.700 to 0.77 …
- Post hoc and exploratory results: `95th` (text:shuffle_percentile) … a of 0.734 on average, with a 5th to 95th percentile from 0.700 to 0.770. Among …
- Post hoc and exploratory results: `ten` (text:top_list) … s would ignore that selection. Of the ten best cells per unit of capital, one i …
- Post hoc and exploratory results: `ten` (text:top_list) … per unit of capital, one is among the ten best per notional; of the best 20, fi …
- Post hoc and exploratory results: `20` (text:top_list) … he ten best per notional; of the best 20, five are. The percentile interval of …

## All numbers

| Place | Text | Evidence | Source | Value |
|---|---|---|---|---|
| abstract | `three` | Constant | const:managers | three managers: SM, legacy PM, PM2 (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| abstract | `0.903` | Result | summary.json:h1_stat | = 0.902944 |
| abstract | `four` | Result | summary.json:h2_n_accounts | = 4 |
| abstract | `3.5` | Result | summary.json:h2_stat~pct | = 3.45401 |
| abstract | `nine` | Result | summary.json:h3_n_accounts | = 9 |
| abstract | `4.75` | Result | summary.json:h3_stat | = 4.74673 |
| abstract | `Four` | Result | derived:n_hypotheses | = 4 |
| abstract | `two` | Result | derived:n_rejected | = 2 |
| Introduction | `three` | Constant | const:managers | three managers: SM, legacy PM, PM2 (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Introduction | `four` | Text count | text:contributions | count word from the sentence |
| Introduction | `Four` | Result | derived:n_hypotheses | = 4 |
| Introduction | `Two` | Result | derived:n_rejected | = 2 |
| Introduction | `four` | Result | derived:n_hypotheses | = 4 |
| Introduction | `0.903` | Result | summary.json:h1_stat | = 0.902944 |
| Introduction | `0.881` | Result | summary.json:h1_lo | = 0.880564 |
| Introduction | `0.907` | Result | summary.json:h1_hi | = 0.907433 |
| Introduction | `0.5` | Constant | const:h1_threshold | H1 rejected if the upper bound is ≥ 0.5 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Introduction | `0.634` | Result | summary.json:sens_h1_sign_within_pos_stat | = 0.634125 |
| Introduction | `0.572` | Result | summary.json:sens_h1_sign_within_pos_lo | = 0.572071 |
| Introduction | `0.702` | Result | summary.json:sens_h1_sign_within_pos_hi | = 0.701746 |
| Introduction | `four` | Result | summary.json:h2_n_accounts | = 4 |
| Introduction | `3.5` | Result | summary.json:h2_stat~pct | = 3.45401 |
| Introduction | `4.75` | Result | summary.json:h3_stat | = 4.74673 |
| Introduction | `nine` | Result | summary.json:h3_n_accounts | = 9 |
| Introduction | `0.62` | Result | summary.json:h4_p | = 0.6224 |
| caption fig:t1 | `08:00` | Result | fig_t1_meta.csv:value@key=ts | = 08:00 |
| caption fig:t1 | `17 September 2026` | Result | fig_t1_meta.csv:value@key=ts | = 2026-09-17 |
| caption fig:t1 | `0.6` | Constant | const:delta_edge_60_delta | \|Δ\| bucket edge 60 % as delta 0.6 (docs/paper1/PRAEREGISTRIERUNG.md, Cells and classes) |
| caption fig:t1 | `two` | Constant | const:api_discount_pct | API semantics with 2 % (exploratory) (docs/paper2/PRAEREGISTRIERUNG.md, Inference) |
| caption fig:t2 | `24 September 2026` | Result | semantics/box_diskont.json:box_*.api_ts~all | all: 2026-09-24, 2026-09-24, 2026-09-24, 2026-09-24 … |
| caption fig:t2 | `45110142` | Result | fig_t2_b.csv:block@row=1 | = 4.51101e+07 |
| caption fig:t2 | `four` | Result | fig_t2_b.csv:row~count | = 4 |
| caption fig:t2 | `two` | Constant | const:h3_threshold | H3: median of K_SM / K_PM2 greater than 2 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:t2 | `17 September` | Result | semantics/faktoren.csv:messung@buch=b17_exakt,fall=B,F_Cnet=11.86 | = --09-17 |
| caption fig:t2 | `11.86` | Result | fig_t2_b.csv:F_Cnet@row=0 | = 11.86 |
| caption fig:t2 | `10.76` | Result | fig_t2_b.csv:F_R_engine@row=0 | = 10.76 |
| caption fig:t2 | `17 September 2026` | Result | fig_t1_meta.csv:value@key=ts | = 2026-09-17 |
| caption fig:t2 | `30` | Text count | text:refbook_target_days | count word from the sentence |
| caption fig:t2 | `22` | Result | reference_book.csv:tenor_days@ccy=BTC,day=2026-09-17 | = 22 |
| The engine and what it returns | `Two` | Text count | text:two_engines | count word from the sentence |
| The engine and what it returns | `fourteen` | Result | summary.json:semantics_box_expiries | = 14 |
| The engine and what it returns | `24 September 2026` | Result | semantics/box_diskont.json:box_*.api_ts~all | all: 2026-09-24, 2026-09-24, 2026-09-24, 2026-09-24 … |
| The engine and what it returns | `2.0000` | Result | semantics/box_diskont.json:box_*.r_api~pct~all | all: 1.99997, 1.99999, 1.99999, 1.99999 … |
| The engine and what it returns | `3.64` | Result | semantics/box_diskont.json:box_*.r_chain~min~pct | = 3.64 |
| The engine and what it returns | `3.82` | Result | semantics/box_diskont.json:box_*.r_chain~max~pct | = 3.82 |
| The engine and what it returns | `195` | Result | summary.json:api_n | = 195 |
| The engine and what it returns | `25 September 2026` | Result | summary.json:api_day | = 2026-09-25 |
| The engine and what it returns | `two` | Text count | text:two_semantics | count word from the sentence |
| The engine and what it returns | `0.08` | Result | summary.json:api_pm2_median_abs_rel~pct | = 0.0802662 |
| The engine and what it returns | `2.4` | Result | summary.json:api_pm2_max_abs_rel~pct | = 2.41262 |
| The engine and what it returns | `11.86` | Result | fig_t2_b.csv:F_Cnet@row=0 | = 11.86 |
| The engine and what it returns | `1.19` | Result | fig_t2_b.csv:F_Cnet@row=1 | = 1.19 |
| The engine and what it returns | `two` | Text count | text:two_books | count word from the sentence |
| The engine and what it returns | `44810149` | Result | fig_t2_b.csv:block@row=0 | = 4.48101e+07 |
| The engine and what it returns | `45110142` | Result | fig_t2_b.csv:block@row=1 | = 4.51101e+07 |
| The engine and what it returns | `10.76` | Result | fig_t2_b.csv:F_R_engine@row=0 | = 10.76 |
| The engine and what it returns | `2.14` | Result | fig_t2_b.csv:F_R_engine@row=1 | = 2.14 |
| The engine and what it returns | `-496859` | Result | fig_t2_a.csv:value_usdc@manager=pm2,item=minus_V~neg | = -496859 |
| caption fig:f1 | `23 January` | Result | events.csv:event_day@event_id=BTC-pm2-20260123 | = --01-23 |
| caption fig:f1 | `24 May` | Result | events.csv:event_day@event_id=BTC-pm2-20260524 | = --05-24 |
| caption fig:f1 | `20 August 2026` | Result | events.csv:event_day@event_id=BTC-pm2-20260820 | = 2026-08-20 |
| caption fig:f1 | `four` | Result | fig_f1_regimes.csv:regime~distinct | = 4 |
| caption fig:f1 | `200` | Constant | const:cell_min_fills | cell populated from 200 fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantics and capital) |
| caption fig:f1 | `20 August 2026` | Result | events.csv:event_day@event_id=BTC-pm2-20260820 | = 2026-08-20 |
| Data and measurement | `11 January 2024` | Constant | const:sample_start | start of the sample 11 January 2024 00:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Data and measurement | `17 September 2026` | Constant | const:pilot_cut | pilot cut 17 September 2026 12:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Data and measurement | `603940` | Result | summary.json:fills_total | = 603940 |
| Data and measurement | `thirty` | Constant | const:markout_minutes | net edge after 30 minutes (docs/paper2/PRAEREGISTRIERUNG.md, Semantics and capital) |
| Data and measurement | `25 September 2026` | Commit date | git:faf6cea | = 2026-09-25 |
| Data and measurement | `11 November 2025` | Constant | const:window_hype | SM and PM2 for HYPE from 11 November 2025 00:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Data and measurement | `six` | Result | summary.json:fills_outside_every_window | = 6 |
| Data and measurement | `12 June 2025` | Constant | const:pm2_window_btc_eth | PM2 window for BTC and ETH from 12 June 2025 23:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Data and measurement | `23:00` | Constant | const:pm2_window_btc_eth | PM2 window for BTC and ETH from 12 June 2025 23:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Data and measurement | `11 November 2025` | Constant | const:window_hype | SM and PM2 for HYPE from 11 November 2025 00:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Data and measurement | `+1` | Constant | const:q_buy | q = +1 for a maker buy (docs/paper2/PRAEREGISTRIERUNG.md, Semantics and capital) |
| Data and measurement | `-1` | Constant | const:q_sell | q = −1 for a maker sell (docs/paper2/PRAEREGISTRIERUNG.md, Semantics and capital) |
| Data and measurement | `200` | Constant | const:cell_min_fills | cell populated from 200 fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantics and capital) |
| Data and measurement | `ten` | Constant | const:dominant_makers | the ten dominant maker subaccounts (docs/paper2/PRAEREGISTRIERUNG.md, Maker books) |
| Data and measurement | `fourteen` | Constant | const:dose_window_days | dose window [e − 14 days, e) (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Data and measurement | `fourteen` | Constant | const:regression_window_days | regression window [e − 14 days, e + 14 days] (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Data and measurement | `20` | Constant | const:h4_min_fills_side | cells need at least 20 fills before and 20 after the event (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Data and measurement | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Data and measurement | `9999` | Constant | const:bootstrap_draws | B = 9 999 bootstrap draws (docs/paper2/PRAEREGISTRIERUNG.md, Inference) |
| Data and measurement | `100` | Constant | const:placebo_dates | 100 placebo dates (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Data and measurement | `28` | Constant | const:placebo_gap_days | placebo dates at least 28 days from every event (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f2 | `two` | Text count | text:denominators | count word from the sentence |
| caption fig:f2 | `200` | Constant | const:cell_min_fills | cell populated from 200 fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantics and capital) |
| caption fig:f2 | `173` | Result | summary.json:h1_n_cells | = 173 |
| caption fig:f2 | `99` | Result | derived:h1_cells_pos | = 99 |
| caption fig:f2 | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f2 | `ten` | Text count | text:largest_moves | count word from the sentence |
| caption fig:f2 | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f2 | `0.5` | Constant | const:h1_threshold | H1 rejected if the upper bound is ≥ 0.5 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f3 | `19999` | Result | summary.json:h2_n | = 19999 |
| caption fig:f3 | `four` | Result | summary.json:h2_n_accounts | = 4 |
| caption fig:f3 | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f4 | `1943` | Result | summary.json:h3_n | = 1943 |
| caption fig:f4 | `63` | Constant | const:sm_max_options | 63 options that an SM account on v2 can hold (docs/paper2/PRAEREGISTRIERUNG.md, Addendum 4) |
| caption fig:f4 | `September 2026` | Constant | const:addenda_day | Addenda 1 to 4, dated 25 September 2026 (docs/paper2/PRAEREGISTRIERUNG.md, Addendum 1) |
| caption fig:f4 | `1431` | Result | summary.json:h3_days_over_63_options | = 1431 |
| caption fig:f4 | `two` | Constant | const:h3_threshold | H3: median of K_SM / K_PM2 greater than 2 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f4 | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The capital denominator and the map (H1) | `7.8` | Result | fig_f1_a.csv:kappa_pm2@ccy=BTC,side=sell,occupied=True~min | = 7.79838 |
| Results / The capital denominator and the map (H1) | `17.7` | Result | fig_f1_a.csv:kappa_pm2@ccy=BTC,side=sell,occupied=True~max | = 17.6902 |
| Results / The capital denominator and the map (H1) | `7.1` | Result | fig_f1_a.csv:kappa_pm2@ccy=ETH,side=sell,occupied=True~min | = 7.06574 |
| Results / The capital denominator and the map (H1) | `21.4` | Result | fig_f1_a.csv:kappa_pm2@ccy=ETH,side=sell,occupied=True~max | = 21.3641 |
| Results / The capital denominator and the map (H1) | `17.5` | Result | fig_f1_a.csv:kappa_pm2@ccy=HYPE,side=sell,occupied=True~min | = 17.5 |
| Results / The capital denominator and the map (H1) | `38.7` | Result | fig_f1_a.csv:kappa_pm2@ccy=HYPE,side=sell,occupied=True~max | = 38.7334 |
| Results / The capital denominator and the map (H1) | `0.943` | Result | fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=sm,regime=pooled | = 0.943303 |
| Results / The capital denominator and the map (H1) | `0.902` | Result | fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=sm,regime=pooled | = 0.901761 |
| Results / The capital denominator and the map (H1) | `0.875` | Result | fig_f1_b.csv:row_median@ccy=HYPE,side=sell,manager=sm,regime=pooled | = 0.875292 |
| Results / The capital denominator and the map (H1) | `20 August 2026` | Result | events.csv:event_day@event_id=BTC-pm2-20260820 | = 2026-08-20 |
| Results / The capital denominator and the map (H1) | `1.398` | Result | fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=sm,regime=R4 | = 1.39824 |
| Results / The capital denominator and the map (H1) | `1.140` | Result | fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=sm,regime=R4 | = 1.14004 |
| Results / The capital denominator and the map (H1) | `6` | Result | fig_f1_b.csv:row_n@ccy=BTC,side=sell,manager=sm,regime=R4 | = 6 |
| Results / The capital denominator and the map (H1) | `18` | Result | fig_f1_b.csv:row_n@ccy=ETH,side=sell,manager=sm,regime=R4 | = 18 |
| Results / The capital denominator and the map (H1) | `200` | Constant | const:cell_min_fills | cell populated from 200 fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantics and capital) |
| Results / The capital denominator and the map (H1) | `1.382` | Result | fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=pm,regime=pooled | = 1.38242 |
| Results / The capital denominator and the map (H1) | `1.355` | Result | fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=pm,regime=pooled | = 1.35481 |
| Results / The capital denominator and the map (H1) | `173` | Result | summary.json:h1_n_cells | = 173 |
| Results / The capital denominator and the map (H1) | `200` | Constant | const:cell_min_fills | cell populated from 200 fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantics and capital) |
| Results / The capital denominator and the map (H1) | `210` | Result | summary.json:h1_n_cells_any | = 210 |
| Results / The capital denominator and the map (H1) | `0.903` | Result | summary.json:h1_stat | = 0.902944 |
| Results / The capital denominator and the map (H1) | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The capital denominator and the map (H1) | `0.881` | Result | summary.json:h1_lo | = 0.880564 |
| Results / The capital denominator and the map (H1) | `0.907` | Result | summary.json:h1_hi | = 0.907433 |
| Results / The capital denominator and the map (H1) | `0.5` | Constant | const:h1_threshold | H1 rejected if the upper bound is ≥ 0.5 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The capital denominator and the map (H1) | `99` | Result | derived:h1_cells_pos | = 99 |
| Results / The capital denominator and the map (H1) | `0.634` | Result | summary.json:sens_h1_sign_within_pos_stat | = 0.634125 |
| Results / The capital denominator and the map (H1) | `0.572` | Result | summary.json:sens_h1_sign_within_pos_lo | = 0.572071 |
| Results / The capital denominator and the map (H1) | `0.702` | Result | summary.json:sens_h1_sign_within_pos_hi | = 0.701746 |
| Results / The capital denominator and the map (H1) | `0.243` | Result | summary.json:sens_h1_sign_within_pos_buy_stat | = 0.24294 |
| Results / The capital denominator and the map (H1) | `0.207` | Result | summary.json:sens_h1_sign_within_pos_buy_lo | = 0.206961 |
| Results / The capital denominator and the map (H1) | `0.446` | Result | summary.json:sens_h1_sign_within_pos_buy_hi | = 0.446156 |
| Results / The capital denominator and the map (H1) | `3.38` | Result | summary.json:h1_pooled_edge_bp_notional | = 3.38247 |
| Results / The capital denominator and the map (H1) | `39.9` | Result | summary.json:h1_pooled_edge_bp_capital | = 39.9456 |
| Results / The capital denominator and the map (H1) | `14` | Result | summary.json:h1_rank_shift_median_abs | = 14 |
| Results / The capital denominator and the map (H1) | `two` | Constant | const:tenor_edge_2d | tenor bucket edge 2 days (docs/paper1/PRAEREGISTRIERUNG.md, Cells and classes) |
| Results / The capital denominator and the map (H1) | `seven` | Constant | const:tenor_edge_7d | tenor bucket edge 7 days (docs/paper1/PRAEREGISTRIERUNG.md, Cells and classes) |
| Results / The capital denominator and the map (H1) | `76` | Result | h1_cells.csv:rank_A@BTC\|buy\|00-10\|2-7d | = 76 |
| Results / The capital denominator and the map (H1) | `4` | Result | h1_cells.csv:rank_B@BTC\|buy\|00-10\|2-7d | = 4 |
| Results / The capital denominator and the map (H1) | `two` | Constant | const:tenor_edge_2d | tenor bucket edge 2 days (docs/paper1/PRAEREGISTRIERUNG.md, Cells and classes) |
| Results / The capital denominator and the map (H1) | `121` | Result | h1_cells.csv:rank_A@BTC\|buy\|00-10\|<=2d | = 121 |
| Results / The capital denominator and the map (H1) | `173` | Result | h1_cells.csv:rank_B@BTC\|buy\|00-10\|<=2d | = 173 |
| Results / The capital denominator and the map (H1) | `53rd` | Result | h1_cells.csv:rank_B@side=sell,occupied=True~min | = 53 |
| Results / The capital denominator and the map (H1) | `20` | Result | summary.json:h1_n_fills_k_le_0 | = 20 |
| Results / A fill in a maker's book (H2) | `ten` | Constant | const:dominant_makers | the ten dominant maker subaccounts (docs/paper2/PRAEREGISTRIERUNG.md, Maker books) |
| Results / A fill in a maker's book (H2) | `four` | Result | summary.json:h2_n_accounts | = 4 |
| Results / A fill in a maker's book (H2) | `100995` | Result | summary.json:h2_population | = 100995 |
| Results / A fill in a maker's book (H2) | `20000` | Constant | const:h2_sample | simple random sample of 20 000 fills (H2) (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / A fill in a maker's book (H2) | `20000` | Constant | const:h2_sample | simple random sample of 20 000 fills (H2) (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / A fill in a maker's book (H2) | `19999` | Result | summary.json:h2_n | = 19999 |
| Results / A fill in a maker's book (H2) | `372` | Result | summary.json:h2_n_days | = 372 |
| Results / A fill in a maker's book (H2) | `0.0345` | Result | summary.json:h2_stat | = 0.0345401 |
| Results / A fill in a maker's book (H2) | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / A fill in a maker's book (H2) | `0.0307` | Result | summary.json:h2_lo | = 0.0307018 |
| Results / A fill in a maker's book (H2) | `0.0386` | Result | summary.json:h2_hi | = 0.0385572 |
| Results / A fill in a maker's book (H2) | `42.0` | Result | summary.json:h2_share_nonpositive~pct | = 41.9621 |
| Results / A fill in a maker's book (H2) | `3.5` | Result | summary.json:h2_stat~pct | = 3.45401 |
| Results / A fill in a maker's book (H2) | `0.28` | Result | fig_h2_dist.csv:value@label=all,variant=ratio,kind=quantile,x=0.25~neg | = 0.276364 |
| Results / A fill in a maker's book (H2) | `0.63` | Result | fig_h2_dist.csv:value@label=all,variant=ratio,kind=quantile,x=0.75 | = 0.630583 |
| Results / A fill in a maker's book (H2) | `95th` | Text count | text:quantile_level | count word from the sentence |
| Results / A fill in a maker's book (H2) | `0.0230` | Result | summary.json:sens_d_h2_by_label_m3_stat,sens_d_h2_by_label_m5_stat,sens_d_h2_by_label_m8_stat,sens_d_h2_by_label_m10_stat~min | = 0.0229804 |
| Results / A fill in a maker's book (H2) | `0.0505` | Result | summary.json:sens_d_h2_by_label_m3_stat,sens_d_h2_by_label_m5_stat,sens_d_h2_by_label_m8_stat,sens_d_h2_by_label_m10_stat~max | = 0.050472 |
| caption fig:f5 | `20` | Constant | const:h4_min_fills_side | cells need at least 20 fills before and 20 after the event (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f5 | `14` | Constant | const:regression_window_days | regression window [e − 14 days, e + 14 days] (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f5 | `May 2026` | Result | events.csv:event_day@event_id=BTC-pm2-20260524 | = 2026-05 |
| caption fig:f5 | `6527` | Result | fig_f6_head.csv:value@key=fills_in_two_windows | = 6527 |
| caption fig:f5 | `two` | Text count | text:two_events | count word from the sentence |
| caption fig:f5 | `30` | Text count | text:refbook_target_days | count word from the sentence |
| caption fig:f5 | `21` | Result | reference_book.csv:tenor_days@ccy=BTC~min | = 21 |
| caption fig:f5 | `36` | Result | reference_book.csv:tenor_days@ccy=BTC~max | = 36 |
| caption fig:f5 | `5` | Result | fig_f5_c.csv:legacy_thin_below~max~pct | = 5 |
| caption fig:f6 | `475` | Result | summary.json:h4_cell_events | = 475 |
| caption fig:f6 | `13` | Result | summary.json:events_with_cells | = 13 |
| caption fig:f6 | `20` | Result | fig_f6_b.csv:bin@mode=bins,kind=bin~count | = 20 |
| caption fig:f6 | `100` | Constant | const:placebo_dates | 100 placebo dates (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| caption fig:f6 | `ten` | Text count | text:reading_aid_pct | count word from the sentence |
| caption fig:f6 | `-0.105` | Result | summary.json:h4_review_ten_pct_dose | = -0.105361 |
| caption fig:f6 | `-0.105` | Result | summary.json:h4_review_ten_pct_dose | = -0.105361 |
| Results / What netting is worth (H3) | `1943` | Result | summary.json:h3_n | = 1943 |
| Results / What netting is worth (H3) | `nine` | Result | summary.json:h3_n_accounts | = 9 |
| Results / What netting is worth (H3) | `four` | Result | summary.json:h3_accounts_pm2 | = 4 |
| Results / What netting is worth (H3) | `four` | Result | summary.json:h3_accounts_pm | = 4 |
| Results / What netting is worth (H3) | `4.747` | Result | summary.json:h3_stat | = 4.74673 |
| Results / What netting is worth (H3) | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / What netting is worth (H3) | `4.662` | Result | summary.json:h3_lo | = 4.66193 |
| Results / What netting is worth (H3) | `4.824` | Result | summary.json:h3_hi | = 4.82363 |
| Results / What netting is worth (H3) | `eight` | Result | summary.json:h3_accounts_median_above_threshold | = 8 |
| Results / What netting is worth (H3) | `nine` | Result | summary.json:h3_accounts_median_n | = 9 |
| Results / What netting is worth (H3) | `two` | Constant | const:h3_threshold | H3: median of K_SM / K_PM2 greater than 2 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / What netting is worth (H3) | `two` | Constant | const:h3_threshold | H3: median of K_SM / K_PM2 greater than 2 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / What netting is worth (H3) | `2.14` | Result | fig_t2_b.csv:F_R_engine~min | = 2.14 |
| Results / What netting is worth (H3) | `10.76` | Result | fig_t2_b.csv:F_R_engine~max | = 10.76 |
| Results / What netting is worth (H3) | `1.545` | Result | summary.json:sens_e_h3_pm_pm2_be_stat | = 1.54511 |
| Results / What netting is worth (H3) | `3.245` | Result | summary.json:sens_e_h3_sm_pm_be_stat | = 3.24539 |
| Results / What netting is worth (H3) | `1431` | Result | summary.json:h3_days_over_63_options | = 1431 |
| Results / What netting is worth (H3) | `73.6` | Result | summary.json:h3_share_days_over_63_options~pct | = 73.649 |
| Results / What netting is worth (H3) | `63` | Constant | const:sm_max_options | 63 options that an SM account on v2 can hold (docs/paper2/PRAEREGISTRIERUNG.md, Addendum 4) |
| Results / What netting is worth (H3) | `September 2026` | Constant | const:addenda_day | Addenda 1 to 4, dated 25 September 2026 (docs/paper2/PRAEREGISTRIERUNG.md, Addendum 1) |
| Results / What netting is worth (H3) | `5.465` | Result | summary.json:sens_e_h3_sm_pm2_gt63_stat | = 5.46541 |
| Results / What netting is worth (H3) | `512` | Result | summary.json:sens_e_h3_sm_pm2_le63_n | = 512 |
| Results / What netting is worth (H3) | `63` | Constant | const:sm_max_options | 63 options that an SM account on v2 can hold (docs/paper2/PRAEREGISTRIERUNG.md, Addendum 4) |
| Results / What netting is worth (H3) | `1.590` | Result | summary.json:sens_e_h3_sm_pm2_le63_stat | = 1.58987 |
| Results / What netting is worth (H3) | `1.532` | Result | summary.json:sens_e_h3_sm_pm2_le63_lo | = 1.53175 |
| Results / What netting is worth (H3) | `1.662` | Result | summary.json:sens_e_h3_sm_pm2_le63_hi | = 1.66154 |
| Results / What netting is worth (H3) | `328` | Result | summary.json:sens_e_h3_by_label_m2_n | = 328 |
| Results / What netting is worth (H3) | `1.076` | Result | summary.json:sens_e_h3_by_label_m2_stat | = 1.07571 |
| Results / What netting is worth (H3) | `3.780` | Result | summary.json:sens_e_h3_sm_pm2_le63_no_sm_stat | = 3.77975 |
| Results / What netting is worth (H3) | `32` | Result | fig_f4_a.csv:lo@kind=bin,hi=64 | = 32 |
| Results / What netting is worth (H3) | `63` | Constant | const:sm_max_options | 63 options that an SM account on v2 can hold (docs/paper2/PRAEREGISTRIERUNG.md, Addendum 4) |
| Results / What netting is worth (H3) | `3.43` | Result | fig_f4_a.csv:median@kind=bin,hi=64 | = 3.42506 |
| Results / The price of capital (H4) | `18` | Result | summary.json:events_total | = 18 |
| Results / The price of capital (H4) | `14` | Result | summary.json:events_kept | = 14 |
| Results / The price of capital (H4) | `13` | Result | summary.json:events_with_cells | = 13 |
| Results / The price of capital (H4) | `20` | Constant | const:h4_min_fills_side | cells need at least 20 fills before and 20 after the event (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The price of capital (H4) | `475` | Result | summary.json:h4_cell_events | = 475 |
| Results / The price of capital (H4) | `22 February 2025` | Constant | const:legacy_event_2025 | legacy PM event 22 February 2025 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The price of capital (H4) | `75` | Result | events.csv:panel_cells@manager=pm,kept=True~sum | = 75 |
| Results / The price of capital (H4) | `14` | Result | summary.json:events_kept | = 14 |
| Results / The price of capital (H4) | `11` | Result | fig_f5_b.csv:jump_logpct@mark=event,status!=dropped,jump_logpct<0~count | = 11 |
| Results / The price of capital (H4) | `3.4` | Result | summary.json:event_eth_pm2_20260524_refbook_log_change~neg~pct | = 3.35989 |
| Results / The price of capital (H4) | `37.4` | Result | summary.json:event_hype_pm2_20260524_refbook_log_change~neg~pct | = 37.4322 |
| Results / The price of capital (H4) | `7.8` | Result | fig_f5_b.csv:jump_logpct@mark=event,ccy=BTC,jump_logpct<0~max~neg | = 7.84153 |
| Results / The price of capital (H4) | `26.0` | Result | fig_f5_b.csv:jump_logpct@mark=event,ccy=BTC,jump_logpct<0~min~neg | = 26.046 |
| Results / The price of capital (H4) | `20 August 2026` | Result | events.csv:event_day@event_id=BTC-pm2-20260820 | = 2026-08-20 |
| Results / The price of capital (H4) | `22.9` | Result | summary.json:event_btc_pm2_20260820_refbook_change~neg~pct | = 22.9303 |
| Results / The price of capital (H4) | `8 January 2026` | Result | events.csv:event_day@event_id=BTC-pm2-20260108 | = 2026-01-08 |
| Results / The price of capital (H4) | `1.6` | Result | summary.json:event_btc_pm2_20260108_refbook_log_change,event_eth_pm2_20260108_refbook_log_change,event_hype_pm2_20260108_refbook_log_change~pct~median | = 1.59792 |
| Results / The price of capital (H4) | `54.5` | Result | summary.json:h4_review_oi_share_min~pct | = 54.478 |
| Results / The price of capital (H4) | `94.9` | Result | summary.json:h4_review_oi_share_max~pct | = 94.8867 |
| Results / The price of capital (H4) | `-4.60` | Result | summary.json:h4_stat | = -4.59923 |
| Results / The price of capital (H4) | `0.6224` | Result | summary.json:h4_p | = 0.6224 |
| Results / The price of capital (H4) | `64` | Result | summary.json:h4_placebo_share_ge_beta~pct | = 64 |
| Results / The price of capital (H4) | `100` | Constant | const:placebo_dates | 100 placebo dates (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The price of capital (H4) | `0.05` | Constant | const:h4_alpha | one-sided p ≤ 0.05 (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The price of capital (H4) | `95th` | Constant | const:placebo_percentile | β above the 95th percentile of the placebo β (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The price of capital (H4) | `23.41` | Result | summary.json:h4_placebo_p95 | = 23.4099 |
| Results / The price of capital (H4) | `13.09` | Result | summary.json:h4_se | = 13.0949 |
| Results / The price of capital (H4) | `100` | Result | summary.json:h4_cal_n | = 100 |
| Results / The price of capital (H4) | `1.82` | Result | summary.json:h4_cal_t_sd | = 1.81756 |
| Results / The price of capital (H4) | `90` | Constant | const:interval_pct | 90 % interval (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Results / The price of capital (H4) | `-41.6` | Result | summary.json:h4_cal_lo | = -41.6364 |
| Results / The price of capital (H4) | `29.7` | Result | summary.json:h4_cal_hi | = 29.6968 |
| Results / The price of capital (H4) | `ten` | Text count | text:reading_aid_pct | count word from the sentence |
| Results / The price of capital (H4) | `-3.13` | Result | summary.json:h4_cal_ten_pct_change_lo | = -3.12887 |
| Results / The price of capital (H4) | `+4.39` | Result | summary.json:h4_cal_ten_pct_change_hi | = 4.38683 |
| Results / The price of capital (H4) | `7.93` | Result | summary.json:h4_cal_y_mean | = 7.93122 |
| Results / The price of capital (H4) | `39` | Result | summary.json:h4_cal_ten_pct_narrowing_share~pct | = 39.4501 |
| Results / The price of capital (H4) | `141` | Result | summary.json:h4_clusters | = 141 |
| Results / Sensitivities | `0.903` | Result | summary.json:sens_b_mm_h1_pm2_mm_stat | = 0.902559 |
| Results / Sensitivities | `5.614` | Result | summary.json:sens_b_mm_h3_mm_stat | = 5.61428 |
| Results / Sensitivities | `0.0291` | Result | summary.json:sens_b_mm_h2_ratio_mm_stat | = 0.02906 |
| Results / Sensitivities | `19693` | Result | summary.json:sens_b_mm_h2_ratio_mm_n | = 19693 |
| Results / Sensitivities | `0.0278` | Result | summary.json:sens_b_mm_h2_ratio_mm_std_stat | = 0.0277626 |
| Results / Sensitivities | `0.913` | Result | summary.json:sens_c_p1_net_edge_h1_pm2_stat | = 0.912609 |
| Results / Sensitivities | `0.0340` | Result | summary.json:sens_d_h2_ratio_tape_stat | = 0.0340328 |
| Results / Sensitivities | `0.0329` | Result | summary.json:sens_d_h2_ratio_unit_stat | = 0.0329119 |
| Discussion | `four` | Result | summary.json:h2_n_accounts | = 4 |
| Discussion | `3.5` | Result | summary.json:h2_stat~pct | = 3.45401 |
| Discussion | `22.9` | Result | summary.json:event_btc_pm2_20260820_refbook_change~neg~pct | = 22.9303 |
| Discussion | `four` | Result | summary.json:h2_n_accounts | = 4 |
| Discussion | `13` | Result | summary.json:events_with_cells | = 13 |
| Discussion | `17 September 2026` | Constant | const:pilot_cut | pilot cut 17 September 2026 12:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Conclusion | `0.903` | Result | summary.json:h1_stat | = 0.902944 |
| Conclusion | `3.5` | Result | summary.json:h2_stat~pct | = 3.45401 |
| Conclusion | `4.75` | Result | summary.json:h3_stat | = 4.74673 |
| Conclusion | `Four` | Result | derived:n_hypotheses | = 4 |
| Conclusion | `two` | Result | derived:n_rejected | = 2 |
| Data, code and pre-registration | `three` | Constant | const:managers | three managers: SM, legacy PM, PM2 (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Data, code and pre-registration | `four` | Result | derived:n_hypotheses | = 4 |
| Data, code and pre-registration | `24 September 2026` | Commit date | git:cc0a29f | = 2026-09-24 |
| Data, code and pre-registration | `22:33` | Commit date | git:cc0a29f | = 22:33 |
| Data, code and pre-registration | `Four` | Constant | const:addenda | four dated addenda (docs/paper2/PRAEREGISTRIERUNG.md, Addendum 4) |
| Data, code and pre-registration | `25 September 2026` | Commit date | git:e492ba1 | = 2026-09-25 |
| Data, code and pre-registration | `three` | Constant | const:managers | three managers: SM, legacy PM, PM2 (docs/paper2/PRAEREGISTRIERUNG.md, Sample) |
| Data, code and pre-registration | `cc0a29f` | Commit | git: commit present |  |
| Data, code and pre-registration | `85bb0b7` | Commit | git: commit present |  |
| Data, code and pre-registration | `6005d7c` | Commit | git: commit present |  |
| Data, code and pre-registration | `8778432` | Commit | git: commit present |  |
| Data, code and pre-registration | `e492ba1` | Commit | git: commit present |  |
| caption fig:a1 | `20` | Result | validation.csv:book@kind=book~distinct | = 20 |
| caption fig:a1 | `1e-13` | Result | fig_a1_meta.csv:value@key=x_lo | = 1e-13 |
| caption fig:a1 | `95th` | Constant | const:validation_percentile | 95th percentile of the absolute relative deviation (docs/paper2/PRAEREGISTRIERUNG.md, Validation before measurement) |
| caption fig:a1 | `0.1` | Constant | const:validation_median_pct | median of the absolute relative deviation below 0.1 % (docs/paper2/PRAEREGISTRIERUNG.md, Validation before measurement) |
| caption fig:a1 | `95th` | Constant | const:validation_percentile | 95th percentile of the absolute relative deviation (docs/paper2/PRAEREGISTRIERUNG.md, Validation before measurement) |
| caption fig:a1 | `1` | Constant | const:validation_p95_pct | 95th percentile below 1 % (docs/paper2/PRAEREGISTRIERUNG.md, Validation before measurement) |
| caption fig:a1 | `17` | Result | fig_a1_meta.csv:value@key=spot_stale_fills | = 17 |
| caption fig:a1 | `180` | Result | fig_a1_meta.csv:value@key=spot_limit_s | = 180 |
| caption fig:a1 | `two` | Constant | const:api_discount_pct | API semantics with 2 % (exploratory) (docs/paper2/PRAEREGISTRIERUNG.md, Inference) |
| Validation of the replica | `100` | Result | summary.json:validation_single_blocks_per_cell | = 100 |
| Validation of the replica | `48` | Constant | const:validation_min_blocks | at least 48 random blocks per underlying and manager (docs/paper2/PRAEREGISTRIERUNG.md, Validation before measurement) |
| Validation of the replica | `20` | Result | validation.csv:book@kind=book~distinct | = 20 |
| Validation of the replica | `877` | Result | summary.json:validation_cases | = 877 |
| Validation of the replica | `14 January 2024` | Result | summary.json:validation_first_day | = 2024-01-14 |
| Validation of the replica | `17 September 2026` | Result | summary.json:validation_last_day | = 2026-09-17 |
| Validation of the replica | `32` | Result | summary.json:validation_cells_passed | = 32 |
| Validation of the replica | `8.7e-10` | Result | summary.json:validation_single_median_rel | = 8.66716e-10 |
| Validation of the replica | `95th` | Constant | const:validation_percentile | 95th percentile of the absolute relative deviation (docs/paper2/PRAEREGISTRIERUNG.md, Validation before measurement) |
| Validation of the replica | `1.4e-8` | Result | summary.json:validation_single_p95_rel | = 1.3969e-08 |
| Validation of the replica | `799` | Result | summary.json:validation_single_n | = 799 |
| Validation of the replica | `8.9e-8` | Result | summary.json:validation_single_max_rel | = 8.88151e-08 |
| Validation of the replica | `77` | Result | summary.json:validation_book_n | = 77 |
| Validation of the replica | `20` | Result | validation.csv:book@kind=book~distinct | = 20 |
| Validation of the replica | `2` | Result | summary.json:validation_book_legs_min | = 2 |
| Validation of the replica | `245` | Result | summary.json:validation_book_legs_max | = 245 |
| Validation of the replica | `2.2e-9` | Result | summary.json:validation_book_median_rel | = 2.19474e-09 |
| Validation of the replica | `0.050` | Result | summary.json:validation_book_max_abs_usd | = 0.0502857 |
| Validation of the replica | `127` | Result | summary.json:h3_days_over_validated_legs | = 127 |
| Validation of the replica | `317` | Result | summary.json:h3_legs_max | = 317 |
| Post hoc and exploratory results | `0.734` | Result | summary.json:h1_sign_floor_mean | = 0.734164 |
| Post hoc and exploratory results | `5th` | Text count | text:shuffle_percentile | count word from the sentence |
| Post hoc and exploratory results | `95th` | Text count | text:shuffle_percentile | count word from the sentence |
| Post hoc and exploratory results | `0.700` | Result | summary.json:h1_sign_floor_p05 | = 0.699743 |
| Post hoc and exploratory results | `0.770` | Result | summary.json:h1_sign_floor_p95 | = 0.769757 |
| Post hoc and exploratory results | `0.990` | Result | summary.json:sens_h1_sign_within_sell_stat | = 0.989867 |
| Post hoc and exploratory results | `0.721` | Result | summary.json:sens_h1_sign_within_buy_stat | = 0.72104 |
| Post hoc and exploratory results | `ten` | Text count | text:top_list | count word from the sentence |
| Post hoc and exploratory results | `ten` | Text count | text:top_list | count word from the sentence |
| Post hoc and exploratory results | `20` | Text count | text:top_list | count word from the sentence |
| Post hoc and exploratory results | `five` | Result | summary.json:h1_top20_overlap | = 5 |
| Post hoc and exploratory results | `15` | Result | summary.json:h1_interval_share_ge_stat~pct | = 15.2315 |
| Post hoc and exploratory results | `0.898` | Result | summary.json:h1_interval_bc_lo | = 0.898267 |
| Post hoc and exploratory results | `0.920` | Result | summary.json:h1_interval_bc_hi | = 0.919643 |
| Post hoc and exploratory results | `0.888` | Result | summary.json:sens_a_maps_sm_pm2_window_stat,sens_a_maps_pm_pm2_window_stat,sens_g_by_ccy_pm2_btc_stat,sens_g_by_ccy_pm2_eth_stat,sens_g_by_ccy_pm2_hype_stat~min | = 0.888406 |
| Post hoc and exploratory results | `0.922` | Result | summary.json:sens_a_maps_sm_pm2_window_stat,sens_a_maps_pm_pm2_window_stat,sens_g_by_ccy_pm2_btc_stat,sens_g_by_ccy_pm2_eth_stat,sens_g_by_ccy_pm2_hype_stat~max | = 0.921632 |
| Post hoc and exploratory results | `0.806` | Result | summary.json:sens_f_time_to_expiry_stat | = 0.805874 |
| Post hoc and exploratory results | `0.833` | Result | summary.json:sens_f_time_holding_stat | = 0.833378 |
| Post hoc and exploratory results | `0.0117` | Result | summary.json:sens_d_h2_by_regime_r1_stat,sens_d_h2_by_regime_r2_stat,sens_d_h2_by_regime_r3_stat,sens_d_h2_by_regime_r4_stat~min | = 0.0117382 |
| Post hoc and exploratory results | `0.0899` | Result | summary.json:sens_d_h2_by_regime_r1_stat,sens_d_h2_by_regime_r2_stat,sens_d_h2_by_regime_r3_stat,sens_d_h2_by_regime_r4_stat~max | = 0.0898755 |
| Post hoc and exploratory results | `-3.42` | Result | summary.json:sens_h4_by_ccy_btc_beta | = -3.41805 |
| Post hoc and exploratory results | `-1.90` | Result | summary.json:sens_h4_by_ccy_eth_beta | = -1.89895 |
| Post hoc and exploratory results | `-10.12` | Result | summary.json:sens_h4_by_ccy_hype_beta | = -10.1236 |
| Post hoc and exploratory results | `-3.81` | Result | summary.json:h4_review_sells_only_beta | = -3.80969 |
| Post hoc and exploratory results | `-5.13` | Result | summary.json:h4_review_oi_weighted_beta | = -5.12936 |
| Post hoc and exploratory results | `0.5` | Result | summary.json:sens_h4_by_ccy_btc_p,sens_h4_by_ccy_eth_p,sens_h4_by_ccy_hype_p,h4_review_sells_only_p,h4_review_oi_weighted_p~min | = 0.5766 |
| Post hoc and exploratory results | `128` | Result | summary.json:h4_review_buys_only_beta | = 127.98 |
| Post hoc and exploratory results | `0.13` | Result | summary.json:h4_review_buys_only_p | = 0.1303 |
| Post hoc and exploratory results | `28` | Constant | const:placebo_gap_days | placebo dates at least 28 days from every event (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Post hoc and exploratory results | `95th` | Constant | const:placebo_percentile | β above the 95th percentile of the placebo β (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Post hoc and exploratory results | `21.57` | Result | summary.json:sens_h4_all_timelines_placebo_p95 | = 21.5691 |
| Post hoc and exploratory results | `88` | Result | summary.json:sens_h4_all_timelines_placebo_share_ge_beta~pct | = 88 |
| Post hoc and exploratory results | `8 January 2026` | Result | events.csv:event_day@event_id=HYPE-pm2-20260108 | = 2026-01-08 |
| Post hoc and exploratory results | `10` | Result | h4.json:placebo.admissible_days.ETH-pm2-*.days | = 10 |
| Post hoc and exploratory results | `16 July` | Result | h4.json:placebo.admissible_days.ETH-pm2-*.first | = --07-16 |
| Post hoc and exploratory results | `25 July 2025` | Result | h4.json:placebo.admissible_days.ETH-pm2-*.last | = 2025-07-25 |
| Post hoc and exploratory results | `95th` | Constant | const:placebo_percentile | β above the 95th percentile of the placebo β (docs/paper2/PRAEREGISTRIERUNG.md, Hypotheses and rejection rules) |
| Post hoc and exploratory results | `26.02` | Result | summary.json:sens_h4_matched_placebo_p95 | = 26.0166 |
| Post hoc and exploratory results | `48` | Result | summary.json:sens_h4_matched_placebo_share_ge_beta~pct | = 48 |
| Post hoc and exploratory results | `1.77` | Result | summary.json:sens_h4_matched_placebo_t_sd | = 1.77216 |
| Post hoc and exploratory results | `-4.52` | Result | summary.json:sens_h4_dose_median_beta | = -4.51808 |
| Post hoc and exploratory results | `-4.08` | Result | summary.json:sens_h4_dose_trimmed_beta | = -4.07647 |

## Constants of the pre-registration

Source: `docs/paper2/PRAEREGISTRIERUNG.md` (commit `cc0a29f`) with Addenda 1 to 4 of 25 September 2026; the bucket edges from `docs/paper1/PRAEREGISTRIERUNG.md`. In the manuscript as `const:name`. Sections are named as in the English translations, with the heading of the binding German original in quotation marks.

| Name | Value | Meaning | Section |
|---|---|---|---|
| `prereg_day` | 2026-09-24 | pre-registration fixed on 24 September 2026 | Header |
| `sample_start` | 2024-01-11 00:00 | start of the sample 11 January 2024 00:00 UTC | Sample ("Stichprobe") |
| `sample_end` | 2026-09-30 08:00 | preregistered end of the sample 30 September 2026 08:00 UTC | Sample ("Stichprobe") |
| `pilot_cut` | 2026-09-17 12:00 | pilot cut 17 September 2026 12:00 UTC | Sample ("Stichprobe") |
| `pm2_window_btc_eth` | 2025-06-12 23:00 | PM2 window for BTC and ETH from 12 June 2025 23:00 UTC | Sample ("Stichprobe") |
| `window_hype` | 2025-11-11 00:00 | SM and PM2 for HYPE from 11 November 2025 00:00 UTC | Sample ("Stichprobe") |
| `managers` | 3 | three managers: SM, legacy PM, PM2 | Sample ("Stichprobe") |
| `cash_zero` | 0 | cash = 0 in K_p(q) = Σ p·q − net_IM(q; cash = 0) | Semantics and capital ("Semantik und Kapital") |
| `q_buy` | 1 | q = +1 for a maker buy | Semantics and capital ("Semantik und Kapital") |
| `q_sell` | -1 | q = −1 for a maker sell | Semantics and capital ("Semantik und Kapital") |
| `markout_minutes` | 30 | net edge after 30 minutes | Semantics and capital ("Semantik und Kapital") |
| `cell_min_fills` | 200 | cell populated from 200 fills | Semantics and capital ("Semantik und Kapital") |
| `bp_factor` | 10 000 | 10⁴ in the cell quantities (basis points) | Semantics and capital ("Semantik und Kapital") |
| `dominant_makers` | 10 | the ten dominant maker subaccounts | Maker books ("Maker-Bücher") |
| `hypotheses` | 4 | four hypotheses H1 to H4 | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `h1_threshold` | 0.5 | H1 rejected if the upper bound is ≥ 0.5 | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `h2_threshold` | 0.5 | H2: median of ΔK / K_PM2,Einzel smaller than 0.5 | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `h3_threshold` | 2 | H3: median of K_SM / K_PM2 greater than 2 | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `interval_pct` | 90 | 90 % interval | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `h2_sample` | 20 000 | simple random sample of 20 000 fills (H2) | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `seed` | 20 260 924 | seed 20260924 | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `legacy_event_2024` | 2024-06-12 | legacy PM event 12 June 2024 | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `legacy_event_2025` | 2025-02-22 | legacy PM event 22 February 2025 | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `dose_filter_pct` | 1 | events whose largest absolute dose is below 1 % are dropped | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `dose_window_days` | 14 | dose window [e − 14 days, e) | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `regression_window_days` | 14 | regression window [e − 14 days, e + 14 days] | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `h4_min_fills_side` | 20 | cells need at least 20 fills before and 20 after the event | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `h4_alpha` | 0.05 | one-sided p ≤ 0.05 | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `placebo_dates` | 100 | 100 placebo dates | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `placebo_percentile` | 95 | β above the 95th percentile of the placebo β | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `placebo_gap_days` | 28 | placebo dates at least 28 days from every event | Hypotheses and rejection rules ("Hypothesen und Ablehnungsregeln") |
| `bootstrap_draws` | 9 999 | B = 9 999 bootstrap draws | Inference ("Inferenz") |
| `api_discount_pct` | 2 | API semantics with 2 % (exploratory) | Inference ("Inferenz") |
| `validation_min_blocks` | 48 | at least 48 random blocks per underlying and manager | Validation before measurement ("Validierung vor der Messung") |
| `validation_min_maker_days` | 20 | maker books on at least 20 maker days | Validation before measurement ("Validierung vor der Messung") |
| `validation_median_pct` | 0.1 | median of the absolute relative deviation below 0.1 % | Validation before measurement ("Validierung vor der Messung") |
| `validation_percentile` | 95 | 95th percentile of the absolute relative deviation | Validation before measurement ("Validierung vor der Messung") |
| `validation_p95_pct` | 1 | 95th percentile below 1 % | Validation before measurement ("Validierung vor der Messung") |
| `addenda_day` | 2026-09-25 | Addenda 1 to 4, dated 25 September 2026 | Addendum 1 ("Nachtrag 1") |
| `interval_lower_percentile` | 5 | interval from the 5th percentile of the replications | Addendum 3 ("Nachtrag 3") |
| `interval_upper_percentile` | 95 | to the 95th percentile of the replications | Addendum 3 ("Nachtrag 3") |
| `addenda` | 4 | four dated addenda | Addendum 4 ("Nachtrag 4") |
| `sm_max_options` | 63 | 63 options that an SM account on v2 can hold | Addendum 4 ("Nachtrag 4") |
| `delta_edge_10` | 10 | \|Δ\| bucket edge 10 % | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `delta_edge_25` | 25 | \|Δ\| bucket edge 25 % | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `delta_edge_40` | 40 | \|Δ\| bucket edge 40 % | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `delta_edge_60` | 60 | \|Δ\| bucket edge 60 % | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `delta_edge_60_delta` | 0.6 | \|Δ\| bucket edge 60 % as delta 0.6 | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `delta_edge_75` | 75 | \|Δ\| bucket edge 75 % | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `delta_edge_90` | 90 | \|Δ\| bucket edge 90 % | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `tenor_edge_2d` | 2 | tenor bucket edge 2 days | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `tenor_edge_7d` | 7 | tenor bucket edge 7 days | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `tenor_edge_30d` | 30 | tenor bucket edge 30 days | Cells and classes ("Zellen und Klassen") (Paper 1) |
| `tenor_edge_90d` | 90 | tenor bucket edge 90 days | Cells and classes ("Zellen und Klassen") (Paper 1) |

Arithmetic identities (no results, only reading aids; in the manuscript as `ident:name`):

- `ln_0_9` = -0.1054: ln 0.9: the dose when capital becomes ten per cent cheaper (reading aid for β, Figure F6)
