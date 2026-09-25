# Zahlenprüfung Paper 2

Erzeugt 2026-09-25 04:54 UTC mit `scripts/p2_number_check.py` aus `paper2/main.tex` gegen `results/p2` und die Konstantenliste der Präregistrierung. Regeln im Kopf des Skripts.

Geprüft sind Abstract, Fliesstext aller Abschnitte und Unterabschnitte samt Zwischentiteln und alle Bildunterschriften; nicht geprüft Titel, Schlüsselwörter, Verweise, Zitate, URLs, abgesetzte Formeln und Literatur. Jede Zahl, jedes Datum und jede Uhrzeit ist per `% src quelle gedruckt` in ihrer Einheit an genau eine Quelle gebunden, in der Reihenfolge des Texts; gesucht wird nichts. „Textzahl“: ein Zählwort, das der Satz selbst belegt (`text:`), ohne Datenquelle.

## Ergebnis

- Zahlen, Daten und Commits im Text: 352
- Ergebnis: 251
- Konstante: 75
- Commit-Datum: 4
- Textzahl: 17
- Commit: 5

**Fehler: 0** (keine)

Textzahlen (ohne Datenquelle, zur Durchsicht):

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

## Alle Zahlen

| Stelle | Text | Beleg | Quelle | Wert |
|---|---|---|---|---|
| abstract | `three` | Konstante | const:managers | drei Manager: SM, Legacy-PM, PM2 (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| abstract | `0.903` | Ergebnis | summary.json:h1_stat | = 0.902944 |
| abstract | `four` | Ergebnis | summary.json:h2_n_accounts | = 4 |
| abstract | `3.5` | Ergebnis | summary.json:h2_stat~pct | = 3.45401 |
| abstract | `nine` | Ergebnis | summary.json:h3_n_accounts | = 9 |
| abstract | `4.75` | Ergebnis | summary.json:h3_stat | = 4.74673 |
| abstract | `Four` | Ergebnis | derived:n_hypotheses | = 4 |
| abstract | `two` | Ergebnis | derived:n_rejected | = 2 |
| Introduction | `three` | Konstante | const:managers | drei Manager: SM, Legacy-PM, PM2 (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Introduction | `four` | Textzahl | text:contributions | Zählwort aus dem Satz |
| Introduction | `Four` | Ergebnis | derived:n_hypotheses | = 4 |
| Introduction | `Two` | Ergebnis | derived:n_rejected | = 2 |
| Introduction | `four` | Ergebnis | derived:n_hypotheses | = 4 |
| Introduction | `0.903` | Ergebnis | summary.json:h1_stat | = 0.902944 |
| Introduction | `0.881` | Ergebnis | summary.json:h1_lo | = 0.880564 |
| Introduction | `0.907` | Ergebnis | summary.json:h1_hi | = 0.907433 |
| Introduction | `0.5` | Konstante | const:h1_threshold | H1 abgelehnt, wenn die obere Grenze ≥ 0,5 ist (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Introduction | `0.634` | Ergebnis | summary.json:sens_h1_sign_within_pos_stat | = 0.634125 |
| Introduction | `0.572` | Ergebnis | summary.json:sens_h1_sign_within_pos_lo | = 0.572071 |
| Introduction | `0.702` | Ergebnis | summary.json:sens_h1_sign_within_pos_hi | = 0.701746 |
| Introduction | `four` | Ergebnis | summary.json:h2_n_accounts | = 4 |
| Introduction | `3.5` | Ergebnis | summary.json:h2_stat~pct | = 3.45401 |
| Introduction | `4.75` | Ergebnis | summary.json:h3_stat | = 4.74673 |
| Introduction | `nine` | Ergebnis | summary.json:h3_n_accounts | = 9 |
| Introduction | `0.62` | Ergebnis | summary.json:h4_p | = 0.6224 |
| caption fig:t1 | `08:00` | Ergebnis | fig_t1_meta.csv:value@key=ts | = 08:00 |
| caption fig:t1 | `17 September 2026` | Ergebnis | fig_t1_meta.csv:value@key=ts | = 2026-09-17 |
| caption fig:t1 | `0.6` | Konstante | const:delta_edge_60_delta | \|Δ\|-Bucketgrenze 60 % als Delta 0,6 (docs/paper1/PRAEREGISTRIERUNG.md, Zellen und Klassen) |
| caption fig:t1 | `two` | Konstante | const:api_discount_pct | API-Semantik mit 2 % (explorativ) (docs/paper2/PRAEREGISTRIERUNG.md, Inferenz) |
| caption fig:t2 | `24 September 2026` | Ergebnis | semantik/box_diskont.json:box_*.api_ts~all | alle: 2026-09-24, 2026-09-24, 2026-09-24, 2026-09-24 … |
| caption fig:t2 | `45110142` | Ergebnis | fig_t2_b.csv:block@row=1 | = 4.51101e+07 |
| caption fig:t2 | `four` | Ergebnis | fig_t2_b.csv:row~count | = 4 |
| caption fig:t2 | `two` | Konstante | const:h3_threshold | H3: Median von K_SM / K_PM2 grösser als 2 (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:t2 | `17 September` | Ergebnis | semantik/faktoren.csv:messung@buch=b17_exakt,fall=B,F_Cnet=11.86 | = --09-17 |
| caption fig:t2 | `11.86` | Ergebnis | fig_t2_b.csv:F_Cnet@row=0 | = 11.86 |
| caption fig:t2 | `10.76` | Ergebnis | fig_t2_b.csv:F_R_engine@row=0 | = 10.76 |
| caption fig:t2 | `17 September 2026` | Ergebnis | fig_t1_meta.csv:value@key=ts | = 2026-09-17 |
| caption fig:t2 | `30` | Textzahl | text:refbook_target_days | Zählwort aus dem Satz |
| caption fig:t2 | `22` | Ergebnis | reference_book.csv:tenor_days@ccy=BTC,day=2026-09-17 | = 22 |
| The engine and what it returns | `Two` | Textzahl | text:two_engines | Zählwort aus dem Satz |
| The engine and what it returns | `fourteen` | Ergebnis | summary.json:semantik_box_expiries | = 14 |
| The engine and what it returns | `24 September 2026` | Ergebnis | semantik/box_diskont.json:box_*.api_ts~all | alle: 2026-09-24, 2026-09-24, 2026-09-24, 2026-09-24 … |
| The engine and what it returns | `2.0000` | Ergebnis | semantik/box_diskont.json:box_*.r_api~pct~all | alle: 1.99997, 1.99999, 1.99999, 1.99999 … |
| The engine and what it returns | `3.64` | Ergebnis | semantik/box_diskont.json:box_*.r_chain~min~pct | = 3.64 |
| The engine and what it returns | `3.82` | Ergebnis | semantik/box_diskont.json:box_*.r_chain~max~pct | = 3.82 |
| The engine and what it returns | `195` | Ergebnis | summary.json:api_n | = 195 |
| The engine and what it returns | `25 September 2026` | Ergebnis | summary.json:api_day | = 2026-09-25 |
| The engine and what it returns | `two` | Textzahl | text:two_semantics | Zählwort aus dem Satz |
| The engine and what it returns | `0.08` | Ergebnis | summary.json:api_pm2_median_abs_rel~pct | = 0.0802662 |
| The engine and what it returns | `2.4` | Ergebnis | summary.json:api_pm2_max_abs_rel~pct | = 2.41262 |
| The engine and what it returns | `11.86` | Ergebnis | fig_t2_b.csv:F_Cnet@row=0 | = 11.86 |
| The engine and what it returns | `1.19` | Ergebnis | fig_t2_b.csv:F_Cnet@row=1 | = 1.19 |
| The engine and what it returns | `two` | Textzahl | text:two_books | Zählwort aus dem Satz |
| The engine and what it returns | `44810149` | Ergebnis | fig_t2_b.csv:block@row=0 | = 4.48101e+07 |
| The engine and what it returns | `45110142` | Ergebnis | fig_t2_b.csv:block@row=1 | = 4.51101e+07 |
| The engine and what it returns | `10.76` | Ergebnis | fig_t2_b.csv:F_R_engine@row=0 | = 10.76 |
| The engine and what it returns | `2.14` | Ergebnis | fig_t2_b.csv:F_R_engine@row=1 | = 2.14 |
| The engine and what it returns | `-496859` | Ergebnis | fig_t2_a.csv:value_usdc@manager=pm2,item=minus_V~neg | = -496859 |
| caption fig:f1 | `23 January` | Ergebnis | events.csv:event_day@event_id=BTC-pm2-20260123 | = --01-23 |
| caption fig:f1 | `24 May` | Ergebnis | events.csv:event_day@event_id=BTC-pm2-20260524 | = --05-24 |
| caption fig:f1 | `20 August 2026` | Ergebnis | events.csv:event_day@event_id=BTC-pm2-20260820 | = 2026-08-20 |
| caption fig:f1 | `four` | Ergebnis | fig_f1_regimes.csv:regime~distinct | = 4 |
| caption fig:f1 | `200` | Konstante | const:cell_min_fills | Zelle besetzt ab 200 Fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantik und Kapital) |
| caption fig:f1 | `20 August 2026` | Ergebnis | events.csv:event_day@event_id=BTC-pm2-20260820 | = 2026-08-20 |
| Data and measurement | `11 January 2024` | Konstante | const:sample_start | Stichprobenbeginn 11.01.2024 00:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Data and measurement | `17 September 2026` | Konstante | const:pilot_cut | Pilotschnitt 17.09.2026 12:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Data and measurement | `603940` | Ergebnis | summary.json:fills_total | = 603940 |
| Data and measurement | `thirty` | Konstante | const:markout_minutes | Netto-Edge nach 30 Minuten (docs/paper2/PRAEREGISTRIERUNG.md, Semantik und Kapital) |
| Data and measurement | `19 September 2026` | Commit-Datum | git:103c676 | = 2026-09-19 |
| Data and measurement | `11 November 2025` | Konstante | const:window_hype | SM und PM2 für HYPE ab 11.11.2025 00:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Data and measurement | `six` | Ergebnis | summary.json:fills_outside_every_window | = 6 |
| Data and measurement | `12 June 2025` | Konstante | const:pm2_window_btc_eth | PM2-Fenster BTC und ETH ab 12.06.2025 23:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Data and measurement | `23:00` | Konstante | const:pm2_window_btc_eth | PM2-Fenster BTC und ETH ab 12.06.2025 23:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Data and measurement | `11 November 2025` | Konstante | const:window_hype | SM und PM2 für HYPE ab 11.11.2025 00:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Data and measurement | `+1` | Konstante | const:q_buy | q = +1 bei Maker-Kauf (docs/paper2/PRAEREGISTRIERUNG.md, Semantik und Kapital) |
| Data and measurement | `-1` | Konstante | const:q_sell | q = −1 bei Maker-Verkauf (docs/paper2/PRAEREGISTRIERUNG.md, Semantik und Kapital) |
| Data and measurement | `200` | Konstante | const:cell_min_fills | Zelle besetzt ab 200 Fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantik und Kapital) |
| Data and measurement | `ten` | Konstante | const:dominant_makers | die zehn dominanten Maker-Subaccounts (docs/paper2/PRAEREGISTRIERUNG.md, Maker-Bücher) |
| Data and measurement | `fourteen` | Konstante | const:dose_window_days | Dosisfenster [e − 14 Tage, e) (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Data and measurement | `fourteen` | Konstante | const:regression_window_days | Regressionsfenster [e − 14 Tage, e + 14 Tage] (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Data and measurement | `20` | Konstante | const:h4_min_fills_side | Zellen brauchen mindestens 20 Fills vor und 20 nach dem Ereignis (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Data and measurement | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Data and measurement | `9999` | Konstante | const:bootstrap_draws | B = 9 999 Bootstrap-Ziehungen (docs/paper2/PRAEREGISTRIERUNG.md, Inferenz) |
| Data and measurement | `100` | Konstante | const:placebo_dates | 100 Placebo-Termine (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Data and measurement | `28` | Konstante | const:placebo_gap_days | Placebo-Termine mindestens 28 Tage von jedem Ereignis (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f2 | `two` | Textzahl | text:denominators | Zählwort aus dem Satz |
| caption fig:f2 | `200` | Konstante | const:cell_min_fills | Zelle besetzt ab 200 Fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantik und Kapital) |
| caption fig:f2 | `173` | Ergebnis | summary.json:h1_n_cells | = 173 |
| caption fig:f2 | `99` | Ergebnis | derived:h1_cells_pos | = 99 |
| caption fig:f2 | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f2 | `ten` | Textzahl | text:largest_moves | Zählwort aus dem Satz |
| caption fig:f2 | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f2 | `0.5` | Konstante | const:h1_threshold | H1 abgelehnt, wenn die obere Grenze ≥ 0,5 ist (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f3 | `19999` | Ergebnis | summary.json:h2_n | = 19999 |
| caption fig:f3 | `four` | Ergebnis | summary.json:h2_n_accounts | = 4 |
| caption fig:f3 | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f4 | `1943` | Ergebnis | summary.json:h3_n | = 1943 |
| caption fig:f4 | `63` | Konstante | const:sm_max_options | 63 Optionen, die ein SM-Konto auf v2 halten kann (docs/paper2/PRAEREGISTRIERUNG.md, Nachtrag 4) |
| caption fig:f4 | `September 2026` | Konstante | const:addenda_day | Nachträge 1 bis 4, datiert 25.09.2026 (docs/paper2/PRAEREGISTRIERUNG.md, Nachtrag 1) |
| caption fig:f4 | `1431` | Ergebnis | summary.json:h3_days_over_63_options | = 1431 |
| caption fig:f4 | `two` | Konstante | const:h3_threshold | H3: Median von K_SM / K_PM2 grösser als 2 (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f4 | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The capital denominator and the map (H1) | `7.8` | Ergebnis | fig_f1_a.csv:kappa_pm2@ccy=BTC,side=sell,occupied=True~min | = 7.79838 |
| Results / The capital denominator and the map (H1) | `17.7` | Ergebnis | fig_f1_a.csv:kappa_pm2@ccy=BTC,side=sell,occupied=True~max | = 17.6902 |
| Results / The capital denominator and the map (H1) | `7.1` | Ergebnis | fig_f1_a.csv:kappa_pm2@ccy=ETH,side=sell,occupied=True~min | = 7.06574 |
| Results / The capital denominator and the map (H1) | `21.4` | Ergebnis | fig_f1_a.csv:kappa_pm2@ccy=ETH,side=sell,occupied=True~max | = 21.3641 |
| Results / The capital denominator and the map (H1) | `17.5` | Ergebnis | fig_f1_a.csv:kappa_pm2@ccy=HYPE,side=sell,occupied=True~min | = 17.5 |
| Results / The capital denominator and the map (H1) | `38.7` | Ergebnis | fig_f1_a.csv:kappa_pm2@ccy=HYPE,side=sell,occupied=True~max | = 38.7334 |
| Results / The capital denominator and the map (H1) | `0.943` | Ergebnis | fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=sm,regime=pooled | = 0.943303 |
| Results / The capital denominator and the map (H1) | `0.902` | Ergebnis | fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=sm,regime=pooled | = 0.901761 |
| Results / The capital denominator and the map (H1) | `0.875` | Ergebnis | fig_f1_b.csv:row_median@ccy=HYPE,side=sell,manager=sm,regime=pooled | = 0.875292 |
| Results / The capital denominator and the map (H1) | `20 August 2026` | Ergebnis | events.csv:event_day@event_id=BTC-pm2-20260820 | = 2026-08-20 |
| Results / The capital denominator and the map (H1) | `1.398` | Ergebnis | fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=sm,regime=R4 | = 1.39824 |
| Results / The capital denominator and the map (H1) | `1.140` | Ergebnis | fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=sm,regime=R4 | = 1.14004 |
| Results / The capital denominator and the map (H1) | `6` | Ergebnis | fig_f1_b.csv:row_n@ccy=BTC,side=sell,manager=sm,regime=R4 | = 6 |
| Results / The capital denominator and the map (H1) | `18` | Ergebnis | fig_f1_b.csv:row_n@ccy=ETH,side=sell,manager=sm,regime=R4 | = 18 |
| Results / The capital denominator and the map (H1) | `200` | Konstante | const:cell_min_fills | Zelle besetzt ab 200 Fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantik und Kapital) |
| Results / The capital denominator and the map (H1) | `1.382` | Ergebnis | fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=pm,regime=pooled | = 1.38242 |
| Results / The capital denominator and the map (H1) | `1.355` | Ergebnis | fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=pm,regime=pooled | = 1.35481 |
| Results / The capital denominator and the map (H1) | `173` | Ergebnis | summary.json:h1_n_cells | = 173 |
| Results / The capital denominator and the map (H1) | `200` | Konstante | const:cell_min_fills | Zelle besetzt ab 200 Fills (docs/paper2/PRAEREGISTRIERUNG.md, Semantik und Kapital) |
| Results / The capital denominator and the map (H1) | `210` | Ergebnis | summary.json:h1_n_cells_any | = 210 |
| Results / The capital denominator and the map (H1) | `0.903` | Ergebnis | summary.json:h1_stat | = 0.902944 |
| Results / The capital denominator and the map (H1) | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The capital denominator and the map (H1) | `0.881` | Ergebnis | summary.json:h1_lo | = 0.880564 |
| Results / The capital denominator and the map (H1) | `0.907` | Ergebnis | summary.json:h1_hi | = 0.907433 |
| Results / The capital denominator and the map (H1) | `0.5` | Konstante | const:h1_threshold | H1 abgelehnt, wenn die obere Grenze ≥ 0,5 ist (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The capital denominator and the map (H1) | `99` | Ergebnis | derived:h1_cells_pos | = 99 |
| Results / The capital denominator and the map (H1) | `0.634` | Ergebnis | summary.json:sens_h1_sign_within_pos_stat | = 0.634125 |
| Results / The capital denominator and the map (H1) | `0.572` | Ergebnis | summary.json:sens_h1_sign_within_pos_lo | = 0.572071 |
| Results / The capital denominator and the map (H1) | `0.702` | Ergebnis | summary.json:sens_h1_sign_within_pos_hi | = 0.701746 |
| Results / The capital denominator and the map (H1) | `0.243` | Ergebnis | summary.json:sens_h1_sign_within_pos_buy_stat | = 0.24294 |
| Results / The capital denominator and the map (H1) | `0.207` | Ergebnis | summary.json:sens_h1_sign_within_pos_buy_lo | = 0.206961 |
| Results / The capital denominator and the map (H1) | `0.446` | Ergebnis | summary.json:sens_h1_sign_within_pos_buy_hi | = 0.446156 |
| Results / The capital denominator and the map (H1) | `3.38` | Ergebnis | summary.json:h1_pooled_edge_bp_notional | = 3.38247 |
| Results / The capital denominator and the map (H1) | `39.9` | Ergebnis | summary.json:h1_pooled_edge_bp_capital | = 39.9456 |
| Results / The capital denominator and the map (H1) | `14` | Ergebnis | summary.json:h1_rank_shift_median_abs | = 14 |
| Results / The capital denominator and the map (H1) | `two` | Konstante | const:tenor_edge_2d | Laufzeit-Bucketgrenze 2 Tage (docs/paper1/PRAEREGISTRIERUNG.md, Zellen und Klassen) |
| Results / The capital denominator and the map (H1) | `seven` | Konstante | const:tenor_edge_7d | Laufzeit-Bucketgrenze 7 Tage (docs/paper1/PRAEREGISTRIERUNG.md, Zellen und Klassen) |
| Results / The capital denominator and the map (H1) | `76` | Ergebnis | h1_cells.csv:rank_A@BTC\|buy\|00-10\|2-7d | = 76 |
| Results / The capital denominator and the map (H1) | `4` | Ergebnis | h1_cells.csv:rank_B@BTC\|buy\|00-10\|2-7d | = 4 |
| Results / The capital denominator and the map (H1) | `two` | Konstante | const:tenor_edge_2d | Laufzeit-Bucketgrenze 2 Tage (docs/paper1/PRAEREGISTRIERUNG.md, Zellen und Klassen) |
| Results / The capital denominator and the map (H1) | `121` | Ergebnis | h1_cells.csv:rank_A@BTC\|buy\|00-10\|<=2d | = 121 |
| Results / The capital denominator and the map (H1) | `173` | Ergebnis | h1_cells.csv:rank_B@BTC\|buy\|00-10\|<=2d | = 173 |
| Results / The capital denominator and the map (H1) | `53rd` | Ergebnis | h1_cells.csv:rank_B@side=sell,occupied=True~min | = 53 |
| Results / The capital denominator and the map (H1) | `20` | Ergebnis | summary.json:h1_n_fills_k_le_0 | = 20 |
| Results / A fill in a maker's book (H2) | `ten` | Konstante | const:dominant_makers | die zehn dominanten Maker-Subaccounts (docs/paper2/PRAEREGISTRIERUNG.md, Maker-Bücher) |
| Results / A fill in a maker's book (H2) | `four` | Ergebnis | summary.json:h2_n_accounts | = 4 |
| Results / A fill in a maker's book (H2) | `100995` | Ergebnis | summary.json:h2_population | = 100995 |
| Results / A fill in a maker's book (H2) | `20000` | Konstante | const:h2_sample | einfache Zufallsstichprobe von 20 000 Fills (H2) (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / A fill in a maker's book (H2) | `20000` | Konstante | const:h2_sample | einfache Zufallsstichprobe von 20 000 Fills (H2) (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / A fill in a maker's book (H2) | `19999` | Ergebnis | summary.json:h2_n | = 19999 |
| Results / A fill in a maker's book (H2) | `372` | Ergebnis | summary.json:h2_n_days | = 372 |
| Results / A fill in a maker's book (H2) | `0.0345` | Ergebnis | summary.json:h2_stat | = 0.0345401 |
| Results / A fill in a maker's book (H2) | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / A fill in a maker's book (H2) | `0.0307` | Ergebnis | summary.json:h2_lo | = 0.0307018 |
| Results / A fill in a maker's book (H2) | `0.0386` | Ergebnis | summary.json:h2_hi | = 0.0385572 |
| Results / A fill in a maker's book (H2) | `42.0` | Ergebnis | summary.json:h2_share_nonpositive~pct | = 41.9621 |
| Results / A fill in a maker's book (H2) | `3.5` | Ergebnis | summary.json:h2_stat~pct | = 3.45401 |
| Results / A fill in a maker's book (H2) | `0.28` | Ergebnis | fig_h2_dist.csv:value@label=all,variant=ratio,kind=quantile,x=0.25~neg | = 0.276364 |
| Results / A fill in a maker's book (H2) | `0.63` | Ergebnis | fig_h2_dist.csv:value@label=all,variant=ratio,kind=quantile,x=0.75 | = 0.630583 |
| Results / A fill in a maker's book (H2) | `95th` | Textzahl | text:quantile_level | Zählwort aus dem Satz |
| Results / A fill in a maker's book (H2) | `0.0230` | Ergebnis | summary.json:sens_d_h2_by_label_m3_stat,sens_d_h2_by_label_m5_stat,sens_d_h2_by_label_m8_stat,sens_d_h2_by_label_m10_stat~min | = 0.0229804 |
| Results / A fill in a maker's book (H2) | `0.0505` | Ergebnis | summary.json:sens_d_h2_by_label_m3_stat,sens_d_h2_by_label_m5_stat,sens_d_h2_by_label_m8_stat,sens_d_h2_by_label_m10_stat~max | = 0.050472 |
| caption fig:f5 | `20` | Konstante | const:h4_min_fills_side | Zellen brauchen mindestens 20 Fills vor und 20 nach dem Ereignis (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f5 | `14` | Konstante | const:regression_window_days | Regressionsfenster [e − 14 Tage, e + 14 Tage] (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f5 | `May 2026` | Ergebnis | events.csv:event_day@event_id=BTC-pm2-20260524 | = 2026-05 |
| caption fig:f5 | `6527` | Ergebnis | fig_f6_head.csv:value@key=fills_in_two_windows | = 6527 |
| caption fig:f5 | `two` | Textzahl | text:two_events | Zählwort aus dem Satz |
| caption fig:f5 | `30` | Textzahl | text:refbook_target_days | Zählwort aus dem Satz |
| caption fig:f5 | `21` | Ergebnis | reference_book.csv:tenor_days@ccy=BTC~min | = 21 |
| caption fig:f5 | `36` | Ergebnis | reference_book.csv:tenor_days@ccy=BTC~max | = 36 |
| caption fig:f5 | `5` | Ergebnis | fig_f5_c.csv:legacy_thin_below~max~pct | = 5 |
| caption fig:f6 | `475` | Ergebnis | summary.json:h4_cell_events | = 475 |
| caption fig:f6 | `13` | Ergebnis | summary.json:events_with_cells | = 13 |
| caption fig:f6 | `20` | Ergebnis | fig_f6_b.csv:bin@mode=bins,kind=bin~count | = 20 |
| caption fig:f6 | `100` | Konstante | const:placebo_dates | 100 Placebo-Termine (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| caption fig:f6 | `ten` | Textzahl | text:reading_aid_pct | Zählwort aus dem Satz |
| caption fig:f6 | `-0.105` | Ergebnis | summary.json:h4_review_ten_pct_dose | = -0.105361 |
| caption fig:f6 | `-0.105` | Ergebnis | summary.json:h4_review_ten_pct_dose | = -0.105361 |
| Results / What netting is worth (H3) | `1943` | Ergebnis | summary.json:h3_n | = 1943 |
| Results / What netting is worth (H3) | `nine` | Ergebnis | summary.json:h3_n_accounts | = 9 |
| Results / What netting is worth (H3) | `four` | Ergebnis | summary.json:h3_accounts_pm2 | = 4 |
| Results / What netting is worth (H3) | `four` | Ergebnis | summary.json:h3_accounts_pm | = 4 |
| Results / What netting is worth (H3) | `4.747` | Ergebnis | summary.json:h3_stat | = 4.74673 |
| Results / What netting is worth (H3) | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / What netting is worth (H3) | `4.662` | Ergebnis | summary.json:h3_lo | = 4.66193 |
| Results / What netting is worth (H3) | `4.824` | Ergebnis | summary.json:h3_hi | = 4.82363 |
| Results / What netting is worth (H3) | `eight` | Ergebnis | summary.json:h3_accounts_median_above_threshold | = 8 |
| Results / What netting is worth (H3) | `nine` | Ergebnis | summary.json:h3_accounts_median_n | = 9 |
| Results / What netting is worth (H3) | `two` | Konstante | const:h3_threshold | H3: Median von K_SM / K_PM2 grösser als 2 (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / What netting is worth (H3) | `two` | Konstante | const:h3_threshold | H3: Median von K_SM / K_PM2 grösser als 2 (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / What netting is worth (H3) | `2.14` | Ergebnis | fig_t2_b.csv:F_R_engine~min | = 2.14 |
| Results / What netting is worth (H3) | `10.76` | Ergebnis | fig_t2_b.csv:F_R_engine~max | = 10.76 |
| Results / What netting is worth (H3) | `1.545` | Ergebnis | summary.json:sens_e_h3_pm_pm2_be_stat | = 1.54511 |
| Results / What netting is worth (H3) | `3.245` | Ergebnis | summary.json:sens_e_h3_sm_pm_be_stat | = 3.24539 |
| Results / What netting is worth (H3) | `1431` | Ergebnis | summary.json:h3_days_over_63_options | = 1431 |
| Results / What netting is worth (H3) | `73.6` | Ergebnis | summary.json:h3_share_days_over_63_options~pct | = 73.649 |
| Results / What netting is worth (H3) | `63` | Konstante | const:sm_max_options | 63 Optionen, die ein SM-Konto auf v2 halten kann (docs/paper2/PRAEREGISTRIERUNG.md, Nachtrag 4) |
| Results / What netting is worth (H3) | `September 2026` | Konstante | const:addenda_day | Nachträge 1 bis 4, datiert 25.09.2026 (docs/paper2/PRAEREGISTRIERUNG.md, Nachtrag 1) |
| Results / What netting is worth (H3) | `5.465` | Ergebnis | summary.json:sens_e_h3_sm_pm2_gt63_stat | = 5.46541 |
| Results / What netting is worth (H3) | `512` | Ergebnis | summary.json:sens_e_h3_sm_pm2_le63_n | = 512 |
| Results / What netting is worth (H3) | `63` | Konstante | const:sm_max_options | 63 Optionen, die ein SM-Konto auf v2 halten kann (docs/paper2/PRAEREGISTRIERUNG.md, Nachtrag 4) |
| Results / What netting is worth (H3) | `1.590` | Ergebnis | summary.json:sens_e_h3_sm_pm2_le63_stat | = 1.58987 |
| Results / What netting is worth (H3) | `1.532` | Ergebnis | summary.json:sens_e_h3_sm_pm2_le63_lo | = 1.53175 |
| Results / What netting is worth (H3) | `1.662` | Ergebnis | summary.json:sens_e_h3_sm_pm2_le63_hi | = 1.66154 |
| Results / What netting is worth (H3) | `328` | Ergebnis | summary.json:sens_e_h3_by_label_m2_n | = 328 |
| Results / What netting is worth (H3) | `1.076` | Ergebnis | summary.json:sens_e_h3_by_label_m2_stat | = 1.07571 |
| Results / What netting is worth (H3) | `3.780` | Ergebnis | summary.json:sens_e_h3_sm_pm2_le63_no_sm_stat | = 3.77975 |
| Results / What netting is worth (H3) | `32` | Ergebnis | fig_f4_a.csv:lo@kind=bin,hi=64 | = 32 |
| Results / What netting is worth (H3) | `63` | Konstante | const:sm_max_options | 63 Optionen, die ein SM-Konto auf v2 halten kann (docs/paper2/PRAEREGISTRIERUNG.md, Nachtrag 4) |
| Results / What netting is worth (H3) | `3.43` | Ergebnis | fig_f4_a.csv:median@kind=bin,hi=64 | = 3.42506 |
| Results / The price of capital (H4) | `18` | Ergebnis | summary.json:events_total | = 18 |
| Results / The price of capital (H4) | `14` | Ergebnis | summary.json:events_kept | = 14 |
| Results / The price of capital (H4) | `13` | Ergebnis | summary.json:events_with_cells | = 13 |
| Results / The price of capital (H4) | `20` | Konstante | const:h4_min_fills_side | Zellen brauchen mindestens 20 Fills vor und 20 nach dem Ereignis (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The price of capital (H4) | `475` | Ergebnis | summary.json:h4_cell_events | = 475 |
| Results / The price of capital (H4) | `22 February 2025` | Konstante | const:legacy_event_2025 | Legacy-PM-Ereignis 22.02.2025 (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The price of capital (H4) | `75` | Ergebnis | events.csv:panel_cells@manager=pm,kept=True~sum | = 75 |
| Results / The price of capital (H4) | `14` | Ergebnis | summary.json:events_kept | = 14 |
| Results / The price of capital (H4) | `11` | Ergebnis | fig_f5_b.csv:jump_logpct@mark=event,status!=dropped,jump_logpct<0~count | = 11 |
| Results / The price of capital (H4) | `3.4` | Ergebnis | summary.json:event_eth_pm2_20260524_refbook_log_change~neg~pct | = 3.35989 |
| Results / The price of capital (H4) | `37.4` | Ergebnis | summary.json:event_hype_pm2_20260524_refbook_log_change~neg~pct | = 37.4322 |
| Results / The price of capital (H4) | `7.8` | Ergebnis | fig_f5_b.csv:jump_logpct@mark=event,ccy=BTC,jump_logpct<0~max~neg | = 7.84153 |
| Results / The price of capital (H4) | `26.0` | Ergebnis | fig_f5_b.csv:jump_logpct@mark=event,ccy=BTC,jump_logpct<0~min~neg | = 26.046 |
| Results / The price of capital (H4) | `20 August 2026` | Ergebnis | events.csv:event_day@event_id=BTC-pm2-20260820 | = 2026-08-20 |
| Results / The price of capital (H4) | `22.9` | Ergebnis | summary.json:event_btc_pm2_20260820_refbook_change~neg~pct | = 22.9303 |
| Results / The price of capital (H4) | `8 January 2026` | Ergebnis | events.csv:event_day@event_id=BTC-pm2-20260108 | = 2026-01-08 |
| Results / The price of capital (H4) | `1.6` | Ergebnis | summary.json:event_btc_pm2_20260108_refbook_log_change,event_eth_pm2_20260108_refbook_log_change,event_hype_pm2_20260108_refbook_log_change~pct~median | = 1.59792 |
| Results / The price of capital (H4) | `54.5` | Ergebnis | summary.json:h4_review_oi_share_min~pct | = 54.478 |
| Results / The price of capital (H4) | `94.9` | Ergebnis | summary.json:h4_review_oi_share_max~pct | = 94.8867 |
| Results / The price of capital (H4) | `-4.60` | Ergebnis | summary.json:h4_stat | = -4.59923 |
| Results / The price of capital (H4) | `0.6224` | Ergebnis | summary.json:h4_p | = 0.6224 |
| Results / The price of capital (H4) | `64` | Ergebnis | summary.json:h4_placebo_share_ge_beta~pct | = 64 |
| Results / The price of capital (H4) | `100` | Konstante | const:placebo_dates | 100 Placebo-Termine (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The price of capital (H4) | `0.05` | Konstante | const:h4_alpha | einseitiges p ≤ 0,05 (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The price of capital (H4) | `95th` | Konstante | const:placebo_percentile | β über dem 95. Perzentil der Placebo-β (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The price of capital (H4) | `23.41` | Ergebnis | summary.json:h4_placebo_p95 | = 23.4099 |
| Results / The price of capital (H4) | `13.09` | Ergebnis | summary.json:h4_se | = 13.0949 |
| Results / The price of capital (H4) | `100` | Ergebnis | summary.json:h4_cal_n | = 100 |
| Results / The price of capital (H4) | `1.82` | Ergebnis | summary.json:h4_cal_t_sd | = 1.81756 |
| Results / The price of capital (H4) | `90` | Konstante | const:interval_pct | 90-%-Intervall (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Results / The price of capital (H4) | `-41.6` | Ergebnis | summary.json:h4_cal_lo | = -41.6364 |
| Results / The price of capital (H4) | `29.7` | Ergebnis | summary.json:h4_cal_hi | = 29.6968 |
| Results / The price of capital (H4) | `ten` | Textzahl | text:reading_aid_pct | Zählwort aus dem Satz |
| Results / The price of capital (H4) | `-3.13` | Ergebnis | summary.json:h4_cal_ten_pct_change_lo | = -3.12887 |
| Results / The price of capital (H4) | `+4.39` | Ergebnis | summary.json:h4_cal_ten_pct_change_hi | = 4.38683 |
| Results / The price of capital (H4) | `7.93` | Ergebnis | summary.json:h4_cal_y_mean | = 7.93122 |
| Results / The price of capital (H4) | `39` | Ergebnis | summary.json:h4_cal_ten_pct_narrowing_share~pct | = 39.4501 |
| Results / The price of capital (H4) | `141` | Ergebnis | summary.json:h4_clusters | = 141 |
| Results / Sensitivities | `0.903` | Ergebnis | summary.json:sens_b_mm_h1_pm2_mm_stat | = 0.902559 |
| Results / Sensitivities | `5.614` | Ergebnis | summary.json:sens_b_mm_h3_mm_stat | = 5.61428 |
| Results / Sensitivities | `0.0291` | Ergebnis | summary.json:sens_b_mm_h2_ratio_mm_stat | = 0.02906 |
| Results / Sensitivities | `19693` | Ergebnis | summary.json:sens_b_mm_h2_ratio_mm_n | = 19693 |
| Results / Sensitivities | `0.0278` | Ergebnis | summary.json:sens_b_mm_h2_ratio_mm_std_stat | = 0.0277626 |
| Results / Sensitivities | `0.913` | Ergebnis | summary.json:sens_c_p1_net_edge_h1_pm2_stat | = 0.912609 |
| Results / Sensitivities | `0.0340` | Ergebnis | summary.json:sens_d_h2_ratio_tape_stat | = 0.0340328 |
| Results / Sensitivities | `0.0329` | Ergebnis | summary.json:sens_d_h2_ratio_unit_stat | = 0.0329119 |
| Discussion | `four` | Ergebnis | summary.json:h2_n_accounts | = 4 |
| Discussion | `3.5` | Ergebnis | summary.json:h2_stat~pct | = 3.45401 |
| Discussion | `22.9` | Ergebnis | summary.json:event_btc_pm2_20260820_refbook_change~neg~pct | = 22.9303 |
| Discussion | `four` | Ergebnis | summary.json:h2_n_accounts | = 4 |
| Discussion | `13` | Ergebnis | summary.json:events_with_cells | = 13 |
| Discussion | `17 September 2026` | Konstante | const:pilot_cut | Pilotschnitt 17.09.2026 12:00 UTC (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Conclusion | `0.903` | Ergebnis | summary.json:h1_stat | = 0.902944 |
| Conclusion | `3.5` | Ergebnis | summary.json:h2_stat~pct | = 3.45401 |
| Conclusion | `4.75` | Ergebnis | summary.json:h3_stat | = 4.74673 |
| Conclusion | `Four` | Ergebnis | derived:n_hypotheses | = 4 |
| Conclusion | `two` | Ergebnis | derived:n_rejected | = 2 |
| Data, code and pre-registration | `three` | Konstante | const:managers | drei Manager: SM, Legacy-PM, PM2 (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Data, code and pre-registration | `four` | Ergebnis | derived:n_hypotheses | = 4 |
| Data, code and pre-registration | `24 September 2026` | Commit-Datum | git:1d13227 | = 2026-09-24 |
| Data, code and pre-registration | `22:33` | Commit-Datum | git:1d13227 | = 22:33 |
| Data, code and pre-registration | `Four` | Konstante | const:addenda | vier datierte Nachträge (docs/paper2/PRAEREGISTRIERUNG.md, Nachtrag 4) |
| Data, code and pre-registration | `25 September 2026` | Commit-Datum | git:c4fcb59 | = 2026-09-25 |
| Data, code and pre-registration | `three` | Konstante | const:managers | drei Manager: SM, Legacy-PM, PM2 (docs/paper2/PRAEREGISTRIERUNG.md, Stichprobe) |
| Data, code and pre-registration | `1d13227` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `eb534fe` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `9465210` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `bfc34c8` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `c4fcb59` | Commit | git: Commit vorhanden |  |
| caption fig:a1 | `20` | Ergebnis | validation.csv:book@kind=book~distinct | = 20 |
| caption fig:a1 | `1e-13` | Ergebnis | fig_a1_meta.csv:value@key=x_lo | = 1e-13 |
| caption fig:a1 | `95th` | Konstante | const:validation_percentile | 95. Perzentil der absoluten relativen Abweichung (docs/paper2/PRAEREGISTRIERUNG.md, Validierung vor der Messung) |
| caption fig:a1 | `0.1` | Konstante | const:validation_median_pct | Median der absoluten relativen Abweichung unter 0,1 % (docs/paper2/PRAEREGISTRIERUNG.md, Validierung vor der Messung) |
| caption fig:a1 | `95th` | Konstante | const:validation_percentile | 95. Perzentil der absoluten relativen Abweichung (docs/paper2/PRAEREGISTRIERUNG.md, Validierung vor der Messung) |
| caption fig:a1 | `1` | Konstante | const:validation_p95_pct | 95. Perzentil unter 1 % (docs/paper2/PRAEREGISTRIERUNG.md, Validierung vor der Messung) |
| caption fig:a1 | `17` | Ergebnis | fig_a1_meta.csv:value@key=spot_stale_fills | = 17 |
| caption fig:a1 | `180` | Ergebnis | fig_a1_meta.csv:value@key=spot_limit_s | = 180 |
| caption fig:a1 | `two` | Konstante | const:api_discount_pct | API-Semantik mit 2 % (explorativ) (docs/paper2/PRAEREGISTRIERUNG.md, Inferenz) |
| Validation of the replica | `100` | Ergebnis | summary.json:validation_single_blocks_per_cell | = 100 |
| Validation of the replica | `48` | Konstante | const:validation_min_blocks | mindestens 48 Zufallsblöcke je Basiswert und Manager (docs/paper2/PRAEREGISTRIERUNG.md, Validierung vor der Messung) |
| Validation of the replica | `20` | Ergebnis | validation.csv:book@kind=book~distinct | = 20 |
| Validation of the replica | `877` | Ergebnis | summary.json:validation_cases | = 877 |
| Validation of the replica | `14 January 2024` | Ergebnis | summary.json:validation_first_day | = 2024-01-14 |
| Validation of the replica | `17 September 2026` | Ergebnis | summary.json:validation_last_day | = 2026-09-17 |
| Validation of the replica | `32` | Ergebnis | summary.json:validation_cells_passed | = 32 |
| Validation of the replica | `8.7e-10` | Ergebnis | summary.json:validation_single_median_rel | = 8.66716e-10 |
| Validation of the replica | `95th` | Konstante | const:validation_percentile | 95. Perzentil der absoluten relativen Abweichung (docs/paper2/PRAEREGISTRIERUNG.md, Validierung vor der Messung) |
| Validation of the replica | `1.4e-8` | Ergebnis | summary.json:validation_single_p95_rel | = 1.3969e-08 |
| Validation of the replica | `799` | Ergebnis | summary.json:validation_single_n | = 799 |
| Validation of the replica | `8.9e-8` | Ergebnis | summary.json:validation_single_max_rel | = 8.88151e-08 |
| Validation of the replica | `77` | Ergebnis | summary.json:validation_book_n | = 77 |
| Validation of the replica | `20` | Ergebnis | validation.csv:book@kind=book~distinct | = 20 |
| Validation of the replica | `2` | Ergebnis | summary.json:validation_book_legs_min | = 2 |
| Validation of the replica | `245` | Ergebnis | summary.json:validation_book_legs_max | = 245 |
| Validation of the replica | `2.2e-9` | Ergebnis | summary.json:validation_book_median_rel | = 2.19474e-09 |
| Validation of the replica | `0.050` | Ergebnis | summary.json:validation_book_max_abs_usd | = 0.0502857 |
| Validation of the replica | `127` | Ergebnis | summary.json:h3_days_over_validated_legs | = 127 |
| Validation of the replica | `317` | Ergebnis | summary.json:h3_legs_max | = 317 |
| Post hoc and exploratory results | `0.734` | Ergebnis | summary.json:h1_sign_floor_mean | = 0.734164 |
| Post hoc and exploratory results | `5th` | Textzahl | text:shuffle_percentile | Zählwort aus dem Satz |
| Post hoc and exploratory results | `95th` | Textzahl | text:shuffle_percentile | Zählwort aus dem Satz |
| Post hoc and exploratory results | `0.700` | Ergebnis | summary.json:h1_sign_floor_p05 | = 0.699743 |
| Post hoc and exploratory results | `0.770` | Ergebnis | summary.json:h1_sign_floor_p95 | = 0.769757 |
| Post hoc and exploratory results | `0.990` | Ergebnis | summary.json:sens_h1_sign_within_sell_stat | = 0.989867 |
| Post hoc and exploratory results | `0.721` | Ergebnis | summary.json:sens_h1_sign_within_buy_stat | = 0.72104 |
| Post hoc and exploratory results | `ten` | Textzahl | text:top_list | Zählwort aus dem Satz |
| Post hoc and exploratory results | `ten` | Textzahl | text:top_list | Zählwort aus dem Satz |
| Post hoc and exploratory results | `20` | Textzahl | text:top_list | Zählwort aus dem Satz |
| Post hoc and exploratory results | `five` | Ergebnis | summary.json:h1_top20_overlap | = 5 |
| Post hoc and exploratory results | `15` | Ergebnis | summary.json:h1_interval_share_ge_stat~pct | = 15.2315 |
| Post hoc and exploratory results | `0.898` | Ergebnis | summary.json:h1_interval_bc_lo | = 0.898267 |
| Post hoc and exploratory results | `0.920` | Ergebnis | summary.json:h1_interval_bc_hi | = 0.919643 |
| Post hoc and exploratory results | `0.888` | Ergebnis | summary.json:sens_a_maps_sm_pm2_window_stat,sens_a_maps_pm_pm2_window_stat,sens_g_by_ccy_pm2_btc_stat,sens_g_by_ccy_pm2_eth_stat,sens_g_by_ccy_pm2_hype_stat~min | = 0.888406 |
| Post hoc and exploratory results | `0.922` | Ergebnis | summary.json:sens_a_maps_sm_pm2_window_stat,sens_a_maps_pm_pm2_window_stat,sens_g_by_ccy_pm2_btc_stat,sens_g_by_ccy_pm2_eth_stat,sens_g_by_ccy_pm2_hype_stat~max | = 0.921632 |
| Post hoc and exploratory results | `0.806` | Ergebnis | summary.json:sens_f_time_to_expiry_stat | = 0.805874 |
| Post hoc and exploratory results | `0.833` | Ergebnis | summary.json:sens_f_time_holding_stat | = 0.833378 |
| Post hoc and exploratory results | `0.0117` | Ergebnis | summary.json:sens_d_h2_by_regime_r1_stat,sens_d_h2_by_regime_r2_stat,sens_d_h2_by_regime_r3_stat,sens_d_h2_by_regime_r4_stat~min | = 0.0117382 |
| Post hoc and exploratory results | `0.0899` | Ergebnis | summary.json:sens_d_h2_by_regime_r1_stat,sens_d_h2_by_regime_r2_stat,sens_d_h2_by_regime_r3_stat,sens_d_h2_by_regime_r4_stat~max | = 0.0898755 |
| Post hoc and exploratory results | `-3.42` | Ergebnis | summary.json:sens_h4_by_ccy_btc_beta | = -3.41805 |
| Post hoc and exploratory results | `-1.90` | Ergebnis | summary.json:sens_h4_by_ccy_eth_beta | = -1.89895 |
| Post hoc and exploratory results | `-10.12` | Ergebnis | summary.json:sens_h4_by_ccy_hype_beta | = -10.1236 |
| Post hoc and exploratory results | `-3.81` | Ergebnis | summary.json:h4_review_sells_only_beta | = -3.80969 |
| Post hoc and exploratory results | `-5.13` | Ergebnis | summary.json:h4_review_oi_weighted_beta | = -5.12936 |
| Post hoc and exploratory results | `0.5` | Ergebnis | summary.json:sens_h4_by_ccy_btc_p,sens_h4_by_ccy_eth_p,sens_h4_by_ccy_hype_p,h4_review_sells_only_p,h4_review_oi_weighted_p~min | = 0.5766 |
| Post hoc and exploratory results | `128` | Ergebnis | summary.json:h4_review_buys_only_beta | = 127.98 |
| Post hoc and exploratory results | `0.13` | Ergebnis | summary.json:h4_review_buys_only_p | = 0.1303 |
| Post hoc and exploratory results | `28` | Konstante | const:placebo_gap_days | Placebo-Termine mindestens 28 Tage von jedem Ereignis (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Post hoc and exploratory results | `95th` | Konstante | const:placebo_percentile | β über dem 95. Perzentil der Placebo-β (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Post hoc and exploratory results | `21.57` | Ergebnis | summary.json:sens_h4_all_timelines_placebo_p95 | = 21.5691 |
| Post hoc and exploratory results | `88` | Ergebnis | summary.json:sens_h4_all_timelines_placebo_share_ge_beta~pct | = 88 |
| Post hoc and exploratory results | `8 January 2026` | Ergebnis | events.csv:event_day@event_id=HYPE-pm2-20260108 | = 2026-01-08 |
| Post hoc and exploratory results | `10` | Ergebnis | h4.json:placebo.admissible_days.ETH-pm2-*.days | = 10 |
| Post hoc and exploratory results | `16 July` | Ergebnis | h4.json:placebo.admissible_days.ETH-pm2-*.first | = --07-16 |
| Post hoc and exploratory results | `25 July 2025` | Ergebnis | h4.json:placebo.admissible_days.ETH-pm2-*.last | = 2025-07-25 |
| Post hoc and exploratory results | `95th` | Konstante | const:placebo_percentile | β über dem 95. Perzentil der Placebo-β (docs/paper2/PRAEREGISTRIERUNG.md, Hypothesen und Ablehnungsregeln) |
| Post hoc and exploratory results | `26.02` | Ergebnis | summary.json:sens_h4_matched_placebo_p95 | = 26.0166 |
| Post hoc and exploratory results | `48` | Ergebnis | summary.json:sens_h4_matched_placebo_share_ge_beta~pct | = 48 |
| Post hoc and exploratory results | `1.77` | Ergebnis | summary.json:sens_h4_matched_placebo_t_sd | = 1.77216 |
| Post hoc and exploratory results | `-4.52` | Ergebnis | summary.json:sens_h4_dose_median_beta | = -4.51808 |
| Post hoc and exploratory results | `-4.08` | Ergebnis | summary.json:sens_h4_dose_trimmed_beta | = -4.07647 |

## Konstanten der Präregistrierung

Quelle: `docs/paper2/PRAEREGISTRIERUNG.md` (Commit `1d13227`) mit den Nachträgen 1 bis 4 vom 25.09.2026; die Bucketgrenzen aus `docs/paper1/PRAEREGISTRIERUNG.md`. Im Manuskript als `const:name`.

| Name | Wert | Bedeutung | Abschnitt |
|---|---|---|---|
| `prereg_day` | 2026-09-24 | Präregistrierung festgelegt am 24.09.2026 | Kopf |
| `sample_start` | 2024-01-11 00:00 | Stichprobenbeginn 11.01.2024 00:00 UTC | Stichprobe |
| `sample_end` | 2026-09-30 08:00 | präregistriertes Stichprobenende 30.09.2026 08:00 UTC | Stichprobe |
| `pilot_cut` | 2026-09-17 12:00 | Pilotschnitt 17.09.2026 12:00 UTC | Stichprobe |
| `pm2_window_btc_eth` | 2025-06-12 23:00 | PM2-Fenster BTC und ETH ab 12.06.2025 23:00 UTC | Stichprobe |
| `window_hype` | 2025-11-11 00:00 | SM und PM2 für HYPE ab 11.11.2025 00:00 UTC | Stichprobe |
| `managers` | 3 | drei Manager: SM, Legacy-PM, PM2 | Stichprobe |
| `cash_zero` | 0 | cash = 0 in K_p(q) = Σ p·q − net_IM(q; cash = 0) | Semantik und Kapital |
| `q_buy` | 1 | q = +1 bei Maker-Kauf | Semantik und Kapital |
| `q_sell` | -1 | q = −1 bei Maker-Verkauf | Semantik und Kapital |
| `markout_minutes` | 30 | Netto-Edge nach 30 Minuten | Semantik und Kapital |
| `cell_min_fills` | 200 | Zelle besetzt ab 200 Fills | Semantik und Kapital |
| `bp_factor` | 10 000 | 10⁴ in den Zellgrössen (Basispunkte) | Semantik und Kapital |
| `dominant_makers` | 10 | die zehn dominanten Maker-Subaccounts | Maker-Bücher |
| `hypotheses` | 4 | vier Hypothesen H1 bis H4 | Hypothesen und Ablehnungsregeln |
| `h1_threshold` | 0.5 | H1 abgelehnt, wenn die obere Grenze ≥ 0,5 ist | Hypothesen und Ablehnungsregeln |
| `h2_threshold` | 0.5 | H2: Median von ΔK / K_PM2,Einzel kleiner als 0,5 | Hypothesen und Ablehnungsregeln |
| `h3_threshold` | 2 | H3: Median von K_SM / K_PM2 grösser als 2 | Hypothesen und Ablehnungsregeln |
| `interval_pct` | 90 | 90-%-Intervall | Hypothesen und Ablehnungsregeln |
| `h2_sample` | 20 000 | einfache Zufallsstichprobe von 20 000 Fills (H2) | Hypothesen und Ablehnungsregeln |
| `seed` | 20 260 924 | Seed 20260924 | Hypothesen und Ablehnungsregeln |
| `legacy_event_2024` | 2024-06-12 | Legacy-PM-Ereignis 12.06.2024 | Hypothesen und Ablehnungsregeln |
| `legacy_event_2025` | 2025-02-22 | Legacy-PM-Ereignis 22.02.2025 | Hypothesen und Ablehnungsregeln |
| `dose_filter_pct` | 1 | Ereignisse mit grösster absoluter Dosis unter 1 % fallen weg | Hypothesen und Ablehnungsregeln |
| `dose_window_days` | 14 | Dosisfenster [e − 14 Tage, e) | Hypothesen und Ablehnungsregeln |
| `regression_window_days` | 14 | Regressionsfenster [e − 14 Tage, e + 14 Tage] | Hypothesen und Ablehnungsregeln |
| `h4_min_fills_side` | 20 | Zellen brauchen mindestens 20 Fills vor und 20 nach dem Ereignis | Hypothesen und Ablehnungsregeln |
| `h4_alpha` | 0.05 | einseitiges p ≤ 0,05 | Hypothesen und Ablehnungsregeln |
| `placebo_dates` | 100 | 100 Placebo-Termine | Hypothesen und Ablehnungsregeln |
| `placebo_percentile` | 95 | β über dem 95. Perzentil der Placebo-β | Hypothesen und Ablehnungsregeln |
| `placebo_gap_days` | 28 | Placebo-Termine mindestens 28 Tage von jedem Ereignis | Hypothesen und Ablehnungsregeln |
| `bootstrap_draws` | 9 999 | B = 9 999 Bootstrap-Ziehungen | Inferenz |
| `api_discount_pct` | 2 | API-Semantik mit 2 % (explorativ) | Inferenz |
| `validation_min_blocks` | 48 | mindestens 48 Zufallsblöcke je Basiswert und Manager | Validierung vor der Messung |
| `validation_min_maker_days` | 20 | Maker-Bücher an mindestens 20 Maker-Tagen | Validierung vor der Messung |
| `validation_median_pct` | 0.1 | Median der absoluten relativen Abweichung unter 0,1 % | Validierung vor der Messung |
| `validation_percentile` | 95 | 95. Perzentil der absoluten relativen Abweichung | Validierung vor der Messung |
| `validation_p95_pct` | 1 | 95. Perzentil unter 1 % | Validierung vor der Messung |
| `addenda_day` | 2026-09-25 | Nachträge 1 bis 4, datiert 25.09.2026 | Nachtrag 1 |
| `interval_lower_percentile` | 5 | Intervall vom 5. Perzentil der Replikationen | Nachtrag 3 |
| `interval_upper_percentile` | 95 | bis zum 95. Perzentil der Replikationen | Nachtrag 3 |
| `addenda` | 4 | vier datierte Nachträge | Nachtrag 4 |
| `sm_max_options` | 63 | 63 Optionen, die ein SM-Konto auf v2 halten kann | Nachtrag 4 |
| `delta_edge_10` | 10 | \|Δ\|-Bucketgrenze 10 % | Zellen und Klassen (Paper 1) |
| `delta_edge_25` | 25 | \|Δ\|-Bucketgrenze 25 % | Zellen und Klassen (Paper 1) |
| `delta_edge_40` | 40 | \|Δ\|-Bucketgrenze 40 % | Zellen und Klassen (Paper 1) |
| `delta_edge_60` | 60 | \|Δ\|-Bucketgrenze 60 % | Zellen und Klassen (Paper 1) |
| `delta_edge_60_delta` | 0.6 | \|Δ\|-Bucketgrenze 60 % als Delta 0,6 | Zellen und Klassen (Paper 1) |
| `delta_edge_75` | 75 | \|Δ\|-Bucketgrenze 75 % | Zellen und Klassen (Paper 1) |
| `delta_edge_90` | 90 | \|Δ\|-Bucketgrenze 90 % | Zellen und Klassen (Paper 1) |
| `tenor_edge_2d` | 2 | Laufzeit-Bucketgrenze 2 Tage | Zellen und Klassen (Paper 1) |
| `tenor_edge_7d` | 7 | Laufzeit-Bucketgrenze 7 Tage | Zellen und Klassen (Paper 1) |
| `tenor_edge_30d` | 30 | Laufzeit-Bucketgrenze 30 Tage | Zellen und Klassen (Paper 1) |
| `tenor_edge_90d` | 90 | Laufzeit-Bucketgrenze 90 Tage | Zellen und Klassen (Paper 1) |

Rechenidentitäten (keine Ergebnisse, nur Lesehilfen; im Manuskript als `ident:name`):

- `ln_0_9` = -0.1054: ln 0,9: Dosis, wenn Kapital zehn Prozent billiger wird (Lesehilfe zu β, Abbildung F6)
