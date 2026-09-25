# Zahlenprüfung Paper 2

Erzeugt 2026-09-25 02:03 UTC mit `scripts/p2_number_check.py` aus `paper2/main.tex` gegen `results/p2` (83 Dateien, 342486 Zahlen) und die Konstantenliste der Präregistrierung. Regeln im Kopf des Skripts.

Geprüft sind Abstract, Fliesstext aller Abschnitte samt Zwischentiteln und alle Bildunterschriften; nicht geprüft Titel, Schlüsselwörter, Verweise, Zitate, URLs, abgesetzte Formeln und Literatur. Kennungen mit Ziffern (PM2, H1, M3, UTC+2, Addendum 2) sind keine Zahlen. „Ergebnis (erklärt)“: die Zahl ist im Manuskript per `% src datei:schlüssel` an eine Quelle gebunden und nur gegen sie geprüft. „Ergebnis“: generischer Treffer, zuerst `summary.json`, dann Hypothesen-, Sensitivitäts- und Probedateien, dann alle übrigen Tabellen (dort nur exakt oder mit mindestens drei signifikanten Stellen). Bei kleinen ganzen Zahlen ist die genannte Fundstelle eine von mehreren.

## Ergebnis

- Zahlen, Daten und Commits im Text: 318
- Ergebnis (erklärt): 198
- Konstante: 90
- Datum: 25
- Commit: 5

**Unbelegte Zahlen: 0** (keine)

## Alle Zahlen

| Stelle | Text | Beleg | Quelle | Wert |
|---|---|---|---|---|
| abstract | `0.903` | Ergebnis (erklärt) | summary.json:h1_stat; auch summary.json:sens_b_mm_h1_pm2_mm_stat | ≈ 0.902944 |
| abstract | `3.5` | Ergebnis (erklärt) | summary.json:h2_stat | ≈ 0.0345401 ×100 |
| abstract | `4.75` | Ergebnis (erklärt) | summary.json:h3_stat | ≈ 4.74673 |
| abstract | `three` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Stichprobe (Manager-Fenster)) | drei Manager: SM, Legacy-PM, PM2 |
| abstract | `two` | Ergebnis (erklärt) | derived:n_rejected | = 2 |
| abstract | `four` | Ergebnis (erklärt) | summary.json:h2_n_accounts; auch derived:n_hypotheses | = 4 |
| abstract | `Four` | Ergebnis (erklärt) | summary.json:h2_n_accounts; auch derived:n_hypotheses | = 4 |
| abstract | `two` | Ergebnis (erklärt) | derived:n_rejected | = 2 |
| Introduction | `0.903` | Ergebnis (erklärt) | summary.json:h1_stat; auch summary.json:sens_b_mm_h1_pm2_mm_stat | ≈ 0.902944 |
| Introduction | `0.881` | Ergebnis (erklärt) | summary.json:h1_lo | ≈ 0.880564 |
| Introduction | `0.907` | Ergebnis (erklärt) | summary.json:h1_hi | ≈ 0.907433 |
| Introduction | `0.5` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | Schwelle H1 (obere Grenze ≥ 0,5) und H2 (Median < 0,5) |
| Introduction | `0.634` | Ergebnis (erklärt) | summary.json:sens_h1_sign_within_pos_stat | ≈ 0.634125 |
| Introduction | `3.5` | Ergebnis (erklärt) | summary.json:h2_stat | ≈ 0.0345401 ×100 |
| Introduction | `4.75` | Ergebnis (erklärt) | summary.json:h3_stat | ≈ 4.74673 |
| Introduction | `0.62` | Ergebnis (erklärt) | summary.json:h4_p | ≈ 0.6224 |
| Introduction | `three` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Stichprobe (Manager-Fenster)) | drei Manager: SM, Legacy-PM, PM2 |
| Introduction | `Four` | Ergebnis (erklärt) | derived:n_hypotheses; auch summary.json:h2_n_accounts | = 4 |
| Introduction | `Four` | Ergebnis (erklärt) | derived:n_hypotheses; auch summary.json:h2_n_accounts | = 4 |
| Introduction | `Two` | Ergebnis (erklärt) | derived:n_rejected | = 2 |
| Introduction | `four` | Ergebnis (erklärt) | derived:n_hypotheses; auch summary.json:h2_n_accounts | = 4 |
| Introduction | `four` | Ergebnis (erklärt) | derived:n_hypotheses; auch summary.json:h2_n_accounts | = 4 |
| caption fig:t1 | `17 September 2026` | Datum | summary.json:cutoff_day | 2026-09-17 |
| caption fig:t1 | `08:00` | Ergebnis (erklärt) | fig_t1_meta.csv:ts | 08:00 |
| caption fig:t1 | `0.6` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital (Buckets aus Paper 1)) | \|Δ\|-Bucketgrenze 60 % als Delta 0,6 |
| caption fig:t1 | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| caption fig:t2 | `24 September 2026` | Ergebnis (erklärt) | semantik/box_diskont.json:box_*.api_ts | 2026-09-24 |
| caption fig:t2 | `17 September 2026` | Datum | summary.json:cutoff_day | 2026-09-17 |
| caption fig:t2 | `17 September` | Datum | summary.json:cutoff_day | 2026-09-17 |
| caption fig:t2 | `45110142` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 24.09. 09:24:59Z Blk 45110142 (H1_0928-81k_0929-76k-81k)].messung; auch semantik/faktoren.csv[historisch 24.09. 09:24:59Z Blk 45110142 (H0_heutige_Liste)].messung | = 4.51101e+07 |
| caption fig:t2 | `11.86` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 17.09. 10:45:13Z Blk 44810149].F_Cnet | = 11.86 |
| caption fig:t2 | `10.76` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 17.09. 10:45:13Z Blk 44810149].F_R_engine | = 10.76 |
| caption fig:t2 | `30` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital) | Netto-Edge nach 30 Minuten; Laufzeit-Bucketgrenze 30 Tage (Paper 1); Referenzbuch nahe 30 Tagen |
| caption fig:t2 | `22` | Ergebnis (erklärt) | reference_book.csv[BTC].tenor_days | = 22 |
| caption fig:t2 | `four` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | vier Hypothesen H1 bis H4 |
| caption fig:t2 | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| The engine and what it returns | `24 September 2026` | Ergebnis (erklärt) | semantik/box_diskont.json:box_*.api_ts | 2026-09-24 |
| The engine and what it returns | `25 September 2026` | Ergebnis (erklärt) | summary.json:api_day | 2026-09-25 |
| The engine and what it returns | `2.0000` | Ergebnis (erklärt) | semantik/box_diskont.json:box_2026-09-24T11:27Z.13.r_api; auch semantik/box_diskont.json:box_2026-09-24T11:27Z.12.r_api; semantik/box_diskont.json:box_2026-09-24T11:27Z.11.r_api | ≈ 0.02 ×100 |
| The engine and what it returns | `3.64` | Ergebnis (erklärt) | semantik/box_diskont.json:box_2026-09-24T11:27Z.0.r_chain; auch semantik/box_diskont.json:box_2026-09-24T11:27Z.1.r_chain; semantik/box_diskont.json:box_2026-09-24T11:27Z.2.r_chain | = 0.0364 ×100 |
| The engine and what it returns | `3.82` | Ergebnis (erklärt) | semantik/box_diskont.json:box_2026-09-24T11:27Z.13.r_chain | = 0.0382 ×100 |
| The engine and what it returns | `195` | Ergebnis (erklärt) | summary.json:api_n | = 195 |
| The engine and what it returns | `0.08` | Ergebnis (erklärt) | summary.json:api_pm2_median_abs_rel | ≈ 0.000802662 ×100 |
| The engine and what it returns | `2.4` | Ergebnis (erklärt) | summary.json:api_pm2_max_abs_rel | ≈ 0.0241262 ×100 |
| The engine and what it returns | `11.86` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 17.09. 10:45:13Z Blk 44810149].F_Cnet | = 11.86 |
| The engine and what it returns | `1.19` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 24.09. 09:24:59Z Blk 45110142 (H1_0928-81k_0929-76k-81k)].F_Cnet; auch semantik/faktoren.csv[live live_result.json Blk 45114302].F_Cnet | = 1.19 |
| The engine and what it returns | `44810149` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 17.09. 10:45:13Z Blk 44810149].messung | = 4.48101e+07 |
| The engine and what it returns | `45110142` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 24.09. 09:24:59Z Blk 45110142 (H1_0928-81k_0929-76k-81k)].messung; auch semantik/faktoren.csv[historisch 24.09. 09:24:59Z Blk 45110142 (H0_heutige_Liste)].messung | = 4.51101e+07 |
| The engine and what it returns | `10.76` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 17.09. 10:45:13Z Blk 44810149].F_R_engine | = 10.76 |
| The engine and what it returns | `2.14` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 24.09. 09:24:59Z Blk 45110142 (H1_0928-81k_0929-76k-81k)].F_R_engine | = 2.14 |
| The engine and what it returns | `-496859` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 24.09. 09:24:59Z Blk 45110142 (H1_0928-81k_0929-76k-81k)].V_PM2 | ≈ -496859 |
| The engine and what it returns | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| The engine and what it returns | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| The engine and what it returns | `Two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| The engine and what it returns | `fourteen` | Ergebnis (erklärt) | summary.json:semantik_box_expiries | = 14 |
| The engine and what it returns | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| The engine and what it returns | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| caption fig:f1 | `20 August 2026` | Datum | summary.json: | 2026-08-20 |
| caption fig:f1 | `20 August 2026` | Datum | summary.json: | 2026-08-20 |
| caption fig:f1 | `23 January` | Datum | summary.json: | 2026-01-23 |
| caption fig:f1 | `24 May` | Datum | summary.json: | 2026-05-24 |
| caption fig:f1 | `200` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital) | Zelle besetzt ab 200 Fills |
| caption fig:f1 | `four` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | vier Hypothesen H1 bis H4 |
| Data and measurement | `11 January 2024` | Datum | summary.json:sample_start_utc | 2024-01-11 |
| Data and measurement | `17 September 2026` | Datum | summary.json:cutoff_day | 2026-09-17 |
| Data and measurement | `30 September 2026` | Datum | summary.json:sample_prereg_end_utc | 2026-09-30 |
| Data and measurement | `11 November 2025` | Datum | summary.json:pm2_window_start_hype | 2025-11-11 |
| Data and measurement | `12 June 2025` | Datum | summary.json:h1_first_day | 2025-06-12 |
| Data and measurement | `11 November 2025` | Datum | summary.json:pm2_window_start_hype | 2025-11-11 |
| Data and measurement | `23:00` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Stichprobe (Manager-Fenster)) | PM2-Fenster ab 23:00 UTC |
| Data and measurement | `603940` | Ergebnis (erklärt) | summary.json:fills_total | = 603940 |
| Data and measurement | `+1` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital; Hypothesen, H4; Validierung vor der Messung) | q = +1 bei Maker-Kauf; Dosisfilter 1 %; Schwelle 95. Perzentil 1 % |
| Data and measurement | `-1` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital) | q = −1 bei Maker-Verkauf |
| Data and measurement | `200` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital) | Zelle besetzt ab 200 Fills |
| Data and measurement | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| Data and measurement | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| Data and measurement | `9999` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Inferenz) | B = 9 999 Bootstrap-Ziehungen |
| Data and measurement | `100` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | 100 Placebo-Termine |
| Data and measurement | `28` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | Placebo-Termine mindestens 28 Tage von jedem Ereignis |
| Data and measurement | `100` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | 100 Placebo-Termine |
| Data and measurement | `48` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Validierung vor der Messung) | mindestens 48 Zufallsblöcke je Basiswert und Manager |
| Data and measurement | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| Data and measurement | `32` | Ergebnis (erklärt) | summary.json:validation_cells | = 32 |
| Data and measurement | `thirty` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital) | Netto-Edge nach 30 Minuten; Laufzeit-Bucketgrenze 30 Tage (Paper 1); Referenzbuch nahe 30 Tagen |
| Data and measurement | `six` | Ergebnis (erklärt) | summary.json:fills_outside_every_window | = 6 |
| Data and measurement | `ten` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Maker-Bücher; Semantik) | die zehn dominanten Maker-Subaccounts; \|Δ\|-Bucketgrenze 10 % (Paper 1) |
| Data and measurement | `fourteen` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | Dosisfenster [e − 14 Tage, e) und Regressionsfenster ± 14 Tage |
| Data and measurement | `fourteen` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | Dosisfenster [e − 14 Tage, e) und Regressionsfenster ± 14 Tage |
| caption fig:f2 | `200` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital) | Zelle besetzt ab 200 Fills |
| caption fig:f2 | `173` | Ergebnis (erklärt) | summary.json:h1_n_cells | = 173 |
| caption fig:f2 | `99` | Ergebnis (erklärt) | derived:h1_cells_pos | = 99 |
| caption fig:f2 | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| caption fig:f2 | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| caption fig:f2 | `0.5` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | Schwelle H1 (obere Grenze ≥ 0,5) und H2 (Median < 0,5) |
| caption fig:f2 | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| caption fig:f2 | `ten` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Maker-Bücher; Semantik) | die zehn dominanten Maker-Subaccounts; \|Δ\|-Bucketgrenze 10 % (Paper 1) |
| caption fig:f3 | `19999` | Ergebnis (erklärt) | summary.json:h2_n | = 19999 |
| caption fig:f3 | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| caption fig:f3 | `four` | Ergebnis (erklärt) | summary.json:h2_n_accounts; auch summary.json:h3_accounts_pm2; summary.json:h3_accounts_pm | = 4 |
| caption fig:f4 | `September 2026` | Datum | summary.json:api_day | 2026-09 |
| caption fig:f4 | `1943` | Ergebnis (erklärt) | summary.json:h3_n | = 1943 |
| caption fig:f4 | `63` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Nachtrag 4, Ziffer 2) | 63 Optionen, die ein SM-Konto auf v2 halten kann |
| caption fig:f4 | `1431` | Ergebnis (erklärt) | summary.json:h3_days_over_63_options | = 1431 |
| caption fig:f4 | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| caption fig:f4 | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| caption fig:f5 | `May 2026` | Datum | summary.json: | 2026-05 |
| caption fig:f5 | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| caption fig:f5 | `14` | Ergebnis (erklärt) | summary.json:h1_rank_shift_median_abs; auch summary.json:events_kept | = 14 |
| caption fig:f5 | `6527` | Ergebnis (erklärt) | fig_f6_head.csv[fills_in_two_windows].value | = 6527 |
| caption fig:f5 | `30` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital) | Netto-Edge nach 30 Minuten; Laufzeit-Bucketgrenze 30 Tage (Paper 1); Referenzbuch nahe 30 Tagen |
| caption fig:f5 | `21` | Ergebnis (erklärt) | reference_book.csv[BTC].tenor_days; auch reference_book.csv[ETH].tenor_days; reference_book.csv[HYPE].tenor_days | = 21 |
| caption fig:f5 | `36` | Ergebnis (erklärt) | reference_book.csv[BTC].tenor_days; auch reference_book.csv[ETH].tenor_days; reference_book.csv[HYPE].tenor_days | = 36 |
| caption fig:f5 | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| caption fig:f6 | `475` | Ergebnis (erklärt) | summary.json:h4_cell_events | = 475 |
| caption fig:f6 | `13` | Ergebnis (erklärt) | summary.json:events_with_cells | = 13 |
| caption fig:f6 | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| caption fig:f6 | `100` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | 100 Placebo-Termine |
| caption fig:f6 | `-0.105` | Ergebnis (erklärt) | summary.json:h4_review_ten_pct_dose | ≈ -0.105361 |
| caption fig:f6 | `-0.105` | Ergebnis (erklärt) | summary.json:h4_review_ten_pct_dose | ≈ -0.105361 |
| caption fig:f6 | `ten` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Maker-Bücher; Semantik) | die zehn dominanten Maker-Subaccounts; \|Δ\|-Bucketgrenze 10 % (Paper 1) |
| Results | `20 August 2026` | Datum | summary.json: | 2026-08-20 |
| Results | `20 August 2026` | Datum | summary.json: | 2026-08-20 |
| Results | `8 January 2026` | Datum | summary.json: | 2026-01-08 |
| Results | `25 July 2025` | Datum | h4.json:placebo.admissible_days.ETH-pm-20250222.last | 2025-07-25 |
| Results | `September 2026` | Datum | summary.json:api_day | 2026-09 |
| Results | `16 July` | Datum | h4.json:placebo.admissible_days.BTC-pm2-20260108.first | 2025-07-16 |
| Results | `7.8` | Ergebnis (erklärt) | fig_f1_a.csv[BTC].kappa_pm2 | ≈ 7.79838 |
| Results | `17.7` | Ergebnis (erklärt) | fig_f1_a.csv[BTC].kappa_pm2; auch fig_f1_a.csv[ETH].kappa_pm2 | ≈ 17.6902 |
| Results | `7.1` | Ergebnis (erklärt) | fig_f1_a.csv[ETH].kappa_pm2 | ≈ 7.06574 |
| Results | `21.4` | Ergebnis (erklärt) | fig_f1_a.csv[ETH].kappa_pm2 | ≈ 21.3819 |
| Results | `17.5` | Ergebnis (erklärt) | fig_f1_a.csv[HYPE].kappa_pm2; auch fig_f1_a.csv[ETH].kappa_pm2 | ≈ 17.5 |
| Results | `38.7` | Ergebnis (erklärt) | fig_f1_a.csv[HYPE].kappa_pm2 | ≈ 38.7334 |
| Results | `0.943` | Ergebnis (erklärt) | fig_f1_b.csv[BTC].row_median | ≈ 0.943303 |
| Results | `0.902` | Ergebnis (erklärt) | fig_f1_b.csv[ETH].row_median | ≈ 0.901761 |
| Results | `0.875` | Ergebnis (erklärt) | fig_f1_b.csv[HYPE].row_median | ≈ 0.875292 |
| Results | `1.398` | Ergebnis (erklärt) | fig_f1_b.csv[BTC].row_median | ≈ 1.39824 |
| Results | `1.140` | Ergebnis (erklärt) | fig_f1_b.csv[ETH].row_median | ≈ 1.14004 |
| Results | `1.382` | Ergebnis (erklärt) | fig_f1_b.csv[BTC].row_median | ≈ 1.38242 |
| Results | `1.355` | Ergebnis (erklärt) | fig_f1_b.csv[ETH].row_median | ≈ 1.35481 |
| Results | `173` | Ergebnis (erklärt) | summary.json:h1_n_cells | = 173 |
| Results | `200` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital) | Zelle besetzt ab 200 Fills |
| Results | `210` | Ergebnis (erklärt) | summary.json:h1_n_cells_any | = 210 |
| Results | `0.903` | Ergebnis (erklärt) | summary.json:h1_stat; auch summary.json:sens_b_mm_h1_pm2_mm_stat | ≈ 0.902944 |
| Results | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| Results | `0.881` | Ergebnis (erklärt) | summary.json:h1_lo | ≈ 0.880564 |
| Results | `0.907` | Ergebnis (erklärt) | summary.json:h1_hi | ≈ 0.907433 |
| Results | `0.5` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | Schwelle H1 (obere Grenze ≥ 0,5) und H2 (Median < 0,5) |
| Results | `99` | Ergebnis (erklärt) | derived:h1_cells_pos | = 99 |
| Results | `0.734` | Ergebnis (erklärt) | summary.json:h1_sign_floor_mean | ≈ 0.734164 |
| Results | `5th` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | einseitiges p ≤ 0,05 (fünf Prozent) |
| Results | `95th` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | 95. Perzentil (Placebo-β, Validierung) |
| Results | `0.700` | Ergebnis (erklärt) | summary.json:h1_sign_floor_p05 | ≈ 0.699743 |
| Results | `0.770` | Ergebnis (erklärt) | summary.json:h1_sign_floor_p95 | ≈ 0.769757 |
| Results | `0.634` | Ergebnis (erklärt) | summary.json:sens_h1_sign_within_pos_stat | ≈ 0.634125 |
| Results | `0.5` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | Schwelle H1 (obere Grenze ≥ 0,5) und H2 (Median < 0,5) |
| Results | `0.990` | Ergebnis (erklärt) | summary.json:sens_h1_sign_within_sell_stat | ≈ 0.989867 |
| Results | `0.721` | Ergebnis (erklärt) | summary.json:sens_h1_sign_within_buy_stat | ≈ 0.72104 |
| Results | `0.243` | Ergebnis (erklärt) | summary.json:sens_h1_sign_within_pos_buy_stat | ≈ 0.24294 |
| Results | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| Results | `3.38` | Ergebnis (erklärt) | summary.json:h1_pooled_edge_bp_notional | ≈ 3.38247 |
| Results | `39.9` | Ergebnis (erklärt) | summary.json:h1_pooled_edge_bp_capital | ≈ 39.9456 |
| Results | `14` | Ergebnis (erklärt) | summary.json:h1_rank_shift_median_abs; auch summary.json:events_kept | = 14 |
| Results | `76` | Ergebnis (erklärt) | h1_cells.csv[BTC\|buy\|00-10\|2-7d].rank_A | = 76 |
| Results | `4` | Ergebnis (erklärt) | h1_cells.csv[BTC\|buy\|00-10\|2-7d].rank_B | = 4 |
| Results | `121` | Ergebnis (erklärt) | h1_cells.csv[BTC\|buy\|00-10\|<=2d].rank_A | = 121 |
| Results | `173` | Ergebnis (erklärt) | summary.json:h1_n_cells | = 173 |
| Results | `53rd` | Ergebnis (erklärt) | h1_cells.csv[ETH\|sell\|10-25\|>90d].rank_B | = 53 |
| Results | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| Results | `100995` | Ergebnis (erklärt) | summary.json:h2_population | = 100995 |
| Results | `20000` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H2) | einfache Zufallsstichprobe von 20 000 Fills (H2) |
| Results | `20000` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H2) | einfache Zufallsstichprobe von 20 000 Fills (H2) |
| Results | `19999` | Ergebnis (erklärt) | summary.json:h2_n | = 19999 |
| Results | `372` | Ergebnis (erklärt) | summary.json:h2_n_days | = 372 |
| Results | `0.0345` | Ergebnis (erklärt) | summary.json:h2_stat | ≈ 0.0345401 |
| Results | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| Results | `0.0307` | Ergebnis (erklärt) | summary.json:h2_lo | ≈ 0.0307018 |
| Results | `0.0386` | Ergebnis (erklärt) | summary.json:h2_hi | ≈ 0.0385572 |
| Results | `42.0` | Ergebnis (erklärt) | summary.json:h2_share_nonpositive | ≈ 0.419621 ×100 |
| Results | `3.5` | Ergebnis (erklärt) | summary.json:h2_stat | ≈ 0.0345401 ×100 |
| Results | `0.28` | Ergebnis (erklärt) | fig_h2_dist.csv[all].value | ≈ -0.279558 Betrag |
| Results | `0.63` | Ergebnis (erklärt) | fig_h2_dist.csv[all].value | ≈ 0.630583 |
| Results | `95th` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | 95. Perzentil (Placebo-β, Validierung) |
| Results | `0.0230` | Ergebnis (erklärt) | summary.json:sens_d_h2_by_label_m3_stat | ≈ 0.0229804 |
| Results | `0.0505` | Ergebnis (erklärt) | summary.json:sens_d_h2_by_label_m5_stat | ≈ 0.050472 |
| Results | `0.0117` | Ergebnis (erklärt) | summary.json:sens_d_h2_by_regime_r3_stat | ≈ 0.0117382 |
| Results | `0.0899` | Ergebnis (erklärt) | summary.json:sens_d_h2_by_regime_r4_stat | ≈ 0.0898755 |
| Results | `1943` | Ergebnis (erklärt) | summary.json:h3_n | = 1943 |
| Results | `4.747` | Ergebnis (erklärt) | summary.json:h3_stat | ≈ 4.74673 |
| Results | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| Results | `4.662` | Ergebnis (erklärt) | summary.json:h3_lo | ≈ 4.66193 |
| Results | `4.824` | Ergebnis (erklärt) | summary.json:h3_hi | ≈ 4.82363 |
| Results | `2.14` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 24.09. 09:24:59Z Blk 45110142 (H1_0928-81k_0929-76k-81k)].F_R_engine | = 2.14 |
| Results | `10.76` | Ergebnis (erklärt) | semantik/faktoren.csv[historisch 17.09. 10:45:13Z Blk 44810149].F_R_engine | = 10.76 |
| Results | `1.545` | Ergebnis (erklärt) | summary.json:sens_e_h3_pm_pm2_be_stat | ≈ 1.54511 |
| Results | `3.245` | Ergebnis (erklärt) | summary.json:sens_e_h3_sm_pm_be_stat | ≈ 3.24539 |
| Results | `1431` | Ergebnis (erklärt) | summary.json:h3_days_over_63_options | = 1431 |
| Results | `73.6` | Ergebnis (erklärt) | summary.json:h3_share_days_over_63_options | ≈ 0.73649 ×100 |
| Results | `63` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Nachtrag 4, Ziffer 2) | 63 Optionen, die ein SM-Konto auf v2 halten kann |
| Results | `5.465` | Ergebnis (erklärt) | summary.json:sens_e_h3_sm_pm2_gt63_stat | ≈ 5.46541 |
| Results | `512` | Ergebnis (erklärt) | summary.json:sens_e_h3_sm_pm2_le63_n | = 512 |
| Results | `63` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Nachtrag 4, Ziffer 2) | 63 Optionen, die ein SM-Konto auf v2 halten kann |
| Results | `1.590` | Ergebnis (erklärt) | summary.json:sens_e_h3_sm_pm2_le63_stat | ≈ 1.58987 |
| Results | `1.532` | Ergebnis (erklärt) | summary.json:sens_e_h3_sm_pm2_le63_lo | ≈ 1.53175 |
| Results | `1.662` | Ergebnis (erklärt) | summary.json:sens_e_h3_sm_pm2_le63_hi | ≈ 1.66154 |
| Results | `328` | Ergebnis (erklärt) | summary.json:sens_e_h3_by_label_m2_n | = 328 |
| Results | `1.076` | Ergebnis (erklärt) | summary.json:sens_e_h3_by_label_m2_stat | ≈ 1.07571 |
| Results | `3.780` | Ergebnis (erklärt) | summary.json:sens_e_h3_sm_pm2_le63_no_sm_stat | ≈ 3.77975 |
| Results | `32` | Ergebnis (erklärt) | fig_f4_a.csv[bin].lo | = 32 |
| Results | `63` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Nachtrag 4, Ziffer 2) | 63 Optionen, die ein SM-Konto auf v2 halten kann |
| Results | `3.43` | Ergebnis (erklärt) | fig_f4_a.csv[bin].median | ≈ 3.42506 |
| Results | `18` | Ergebnis (erklärt) | summary.json:events_total | = 18 |
| Results | `14` | Ergebnis (erklärt) | summary.json:h1_rank_shift_median_abs; auch summary.json:events_kept | = 14 |
| Results | `13` | Ergebnis (erklärt) | summary.json:events_with_cells | = 13 |
| Results | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| Results | `475` | Ergebnis (erklärt) | summary.json:h4_cell_events | = 475 |
| Results | `3.4` | Ergebnis (erklärt) | summary.json:event_eth_pm2_20260524_refbook_log_change | ≈ -0.0335989 ×100 Betrag |
| Results | `37.4` | Ergebnis (erklärt) | summary.json:event_hype_pm2_20260524_refbook_log_change | ≈ -0.374322 ×100 Betrag |
| Results | `22.9` | Ergebnis (erklärt) | summary.json:event_btc_pm2_20260820_refbook_change | ≈ -0.229303 ×100 Betrag |
| Results | `26.0` | Ergebnis (erklärt) | summary.json:event_btc_pm2_20260820_refbook_log_change | ≈ -0.26046 ×100 Betrag |
| Results | `1.6` | Ergebnis (erklärt) | summary.json:event_btc_pm2_20260108_refbook_log_change; auch summary.json:event_eth_pm2_20260108_refbook_log_change | ≈ 0.0159792 ×100 |
| Results | `54.5` | Ergebnis (erklärt) | summary.json:h4_review_oi_share_min | ≈ 0.54478 ×100 |
| Results | `94.9` | Ergebnis (erklärt) | summary.json:h4_review_oi_share_max | ≈ 0.948867 ×100 |
| Results | `-4.60` | Ergebnis (erklärt) | summary.json:h4_stat | ≈ -4.59923 |
| Results | `0.6224` | Ergebnis (erklärt) | summary.json:h4_p | = 0.6224 |
| Results | `64` | Ergebnis (erklärt) | summary.json:h4_placebo_share_ge_beta | = 0.64 ×100 |
| Results | `100` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | 100 Placebo-Termine |
| Results | `0.05` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4) | einseitiges p ≤ 0,05 |
| Results | `95th` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | 95. Perzentil (Placebo-β, Validierung) |
| Results | `23.41` | Ergebnis (erklärt) | summary.json:h4_placebo_p95 | ≈ 23.4099 |
| Results | `13.09` | Ergebnis (erklärt) | summary.json:h4_se | ≈ 13.0949 |
| Results | `90` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | 90-%-Intervall |
| Results | `-1.75` | Ergebnis (erklärt) | summary.json:h4_review_ten_pct_change_lo | ≈ -1.74801 |
| Results | `+2.74` | Ergebnis (erklärt) | summary.json:h4_review_ten_pct_change_hi | ≈ 2.7436 |
| Results | `7.93` | Ergebnis (erklärt) | summary.json:h4_review_y_mean | ≈ 7.93122 |
| Results | `-3.42` | Ergebnis (erklärt) | summary.json:sens_h4_by_ccy_btc_beta | ≈ -3.41805 |
| Results | `-1.90` | Ergebnis (erklärt) | summary.json:sens_h4_by_ccy_eth_beta | ≈ -1.89895 |
| Results | `-10.12` | Ergebnis (erklärt) | summary.json:sens_h4_by_ccy_hype_beta | ≈ -10.1236 |
| Results | `-3.81` | Ergebnis (erklärt) | summary.json:h4_review_sells_only_beta | ≈ -3.80969 |
| Results | `-5.13` | Ergebnis (erklärt) | summary.json:h4_review_oi_weighted_beta | ≈ -5.12936 |
| Results | `0.5` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | Schwelle H1 (obere Grenze ≥ 0,5) und H2 (Median < 0,5) |
| Results | `128` | Ergebnis (erklärt) | summary.json:h4_review_buys_only_beta | ≈ 127.98 |
| Results | `0.13` | Ergebnis (erklärt) | summary.json:h4_review_buys_only_p | ≈ 0.1303 |
| Results | `141` | Ergebnis (erklärt) | summary.json:h4_clusters | = 141 |
| Results | `10` | Ergebnis (erklärt) | h4.json:placebo.admissible_days.ETH-pm2-20260108.days; auch h4.json:placebo.admissible_days.ETH-pm2-20260123.days; h4.json:placebo.admissible_days.ETH-pm2-20260524.days | = 10 |
| Results | `0.903` | Ergebnis (erklärt) | summary.json:h1_stat; auch summary.json:sens_b_mm_h1_pm2_mm_stat | ≈ 0.902944 |
| Results | `5.614` | Ergebnis (erklärt) | summary.json:sens_b_mm_h3_mm_stat | ≈ 5.61428 |
| Results | `0.0291` | Ergebnis (erklärt) | summary.json:sens_b_mm_h2_ratio_mm_stat | ≈ 0.02906 |
| Results | `19693` | Ergebnis (erklärt) | summary.json:sens_b_mm_h2_ratio_mm_n | = 19693 |
| Results | `0.913` | Ergebnis (erklärt) | summary.json:sens_c_p1_net_edge_h1_pm2_stat | ≈ 0.912609 |
| Results | `0.0340` | Ergebnis (erklärt) | summary.json:sens_d_h2_ratio_tape_stat | ≈ 0.0340328 |
| Results | `0.0329` | Ergebnis (erklärt) | summary.json:sens_d_h2_ratio_unit_stat | ≈ 0.0329119 |
| Results | `0.888` | Ergebnis (erklärt) | summary.json:sens_g_by_ccy_pm2_hype_stat | ≈ 0.888406 |
| Results | `0.922` | Ergebnis (erklärt) | summary.json:sens_g_by_ccy_pm2_eth_stat | ≈ 0.921632 |
| Results | `0.806` | Ergebnis (erklärt) | summary.json:sens_f_time_to_expiry_stat | ≈ 0.805874 |
| Results | `0.833` | Ergebnis (erklärt) | summary.json:sens_f_time_holding_stat | ≈ 0.833378 |
| Results | `ten` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Maker-Bücher; Semantik) | die zehn dominanten Maker-Subaccounts; \|Δ\|-Bucketgrenze 10 % (Paper 1) |
| Results | `ten` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Maker-Bücher; Semantik) | die zehn dominanten Maker-Subaccounts; \|Δ\|-Bucketgrenze 10 % (Paper 1) |
| Results | `five` | Ergebnis (erklärt) | summary.json:h1_top20_overlap | = 5 |
| Results | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| Results | `seven` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital (Buckets aus Paper 1)) | Laufzeit-Bucketgrenze 7 Tage |
| Results | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| Results | `ten` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Maker-Bücher; Semantik) | die zehn dominanten Maker-Subaccounts; \|Δ\|-Bucketgrenze 10 % (Paper 1) |
| Results | `four` | Ergebnis (erklärt) | summary.json:h2_n_accounts; auch summary.json:h3_accounts_pm2; summary.json:h3_accounts_pm | = 4 |
| Results | `nine` | Ergebnis (erklärt) | summary.json:h3_n_accounts; auch summary.json:h3_accounts_median_n | = 9 |
| Results | `four` | Ergebnis (erklärt) | summary.json:h2_n_accounts; auch summary.json:h3_accounts_pm2; summary.json:h3_accounts_pm | = 4 |
| Results | `four` | Ergebnis (erklärt) | summary.json:h2_n_accounts; auch summary.json:h3_accounts_pm2; summary.json:h3_accounts_pm | = 4 |
| Results | `eight` | Ergebnis (erklärt) | summary.json:h3_accounts_median_above_threshold | = 8 |
| Results | `nine` | Ergebnis (erklärt) | summary.json:h3_n_accounts; auch summary.json:h3_accounts_median_n | = 9 |
| Results | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| Results | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| Results | `ten` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Maker-Bücher; Semantik) | die zehn dominanten Maker-Subaccounts; \|Δ\|-Bucketgrenze 10 % (Paper 1) |
| caption fig:a1 | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| caption fig:a1 | `1e-13` | Ergebnis (erklärt) | fig_a1_meta.csv[x_lo].value | = 1e-13 |
| caption fig:a1 | `95th` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | 95. Perzentil (Placebo-β, Validierung) |
| caption fig:a1 | `0.1` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Validierung vor der Messung) | Schwelle Median der absoluten relativen Abweichung 0,1 % |
| caption fig:a1 | `95th` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | 95. Perzentil (Placebo-β, Validierung) |
| caption fig:a1 | `1` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Semantik und Kapital; Hypothesen, H4; Validierung vor der Messung) | q = +1 bei Maker-Kauf; Dosisfilter 1 %; Schwelle 95. Perzentil 1 % |
| caption fig:a1 | `two` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln; Inferenz; Semantik) | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage |
| Discussion | `20 August 2026` | Datum | summary.json: | 2026-08-20 |
| Discussion | `17 September 2026` | Datum | summary.json:cutoff_day | 2026-09-17 |
| Discussion | `3.5` | Ergebnis (erklärt) | summary.json:h2_stat | ≈ 0.0345401 ×100 |
| Discussion | `22.9` | Ergebnis (erklärt) | summary.json:event_btc_pm2_20260820_refbook_change | ≈ -0.229303 ×100 Betrag |
| Discussion | `13` | Ergebnis (erklärt) | summary.json:events_with_cells | = 13 |
| Discussion | `four` | Ergebnis (erklärt) | summary.json:h2_n_accounts | = 4 |
| Discussion | `four` | Ergebnis (erklärt) | summary.json:h2_n_accounts | = 4 |
| Conclusion | `0.903` | Ergebnis (erklärt) | summary.json:h1_stat; auch summary.json:sens_b_mm_h1_pm2_mm_stat | ≈ 0.902944 |
| Conclusion | `3.5` | Ergebnis (erklärt) | summary.json:h2_stat | ≈ 0.0345401 ×100 |
| Conclusion | `4.75` | Ergebnis (erklärt) | summary.json:h3_stat | ≈ 4.74673 |
| Conclusion | `Four` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | vier Hypothesen H1 bis H4 |
| Conclusion | `two` | Ergebnis (erklärt) | derived:n_rejected | = 2 |
| Data, code and pre-registration | `1d13227` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `eb534fe` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `9465210` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `bfc34c8` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `c4fcb59` | Commit | git: Commit vorhanden |  |
| Data, code and pre-registration | `24 September 2026` | Ergebnis (erklärt) | git:1d13227 | 2026-09-24 |
| Data, code and pre-registration | `25 September 2026` | Ergebnis (erklärt) | git:c4fcb59 | 2026-09-25 |
| Data, code and pre-registration | `22:33` | Ergebnis (erklärt) | git:1d13227 | 22:33 |
| Data, code and pre-registration | `three` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Stichprobe (Manager-Fenster)) | drei Manager: SM, Legacy-PM, PM2 |
| Data, code and pre-registration | `four` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | vier Hypothesen H1 bis H4 |
| Data, code and pre-registration | `Four` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen und Ablehnungsregeln) | vier Hypothesen H1 bis H4 |
| Validation of the replica | `14 January 2024` | Datum | summary.json:validation_first_day | 2024-01-14 |
| Validation of the replica | `17 September 2026` | Datum | summary.json:cutoff_day | 2026-09-17 |
| Validation of the replica | `877` | Ergebnis (erklärt) | summary.json:validation_cases | = 877 |
| Validation of the replica | `32` | Ergebnis (erklärt) | summary.json:validation_cells | = 32 |
| Validation of the replica | `8.7e-10` | Ergebnis (erklärt) | summary.json:validation_single_median_rel | = 8.66716e-10 |
| Validation of the replica | `95th` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | 95. Perzentil (Placebo-β, Validierung) |
| Validation of the replica | `1.4e-8` | Ergebnis (erklärt) | summary.json:validation_single_p95_rel | = 1.3969e-08 |
| Validation of the replica | `799` | Ergebnis (erklärt) | summary.json:validation_single_n | = 799 |
| Validation of the replica | `8.9e-8` | Ergebnis (erklärt) | summary.json:validation_single_max_rel | = 8.88151e-08 |
| Validation of the replica | `77` | Ergebnis (erklärt) | summary.json:validation_book_n | = 77 |
| Validation of the replica | `20` | Konstante | docs/paper2/PRAEREGISTRIERUNG.md (Hypothesen, H4; Validierung vor der Messung) | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) |
| Validation of the replica | `2` | Ergebnis (erklärt) | summary.json:validation_book_legs_min | = 2 |
| Validation of the replica | `245` | Ergebnis (erklärt) | summary.json:validation_book_legs_max | = 245 |
| Validation of the replica | `2.2e-9` | Ergebnis (erklärt) | summary.json:validation_book_median_rel | = 2.19474e-09 |
| Validation of the replica | `0.050` | Ergebnis (erklärt) | summary.json:validation_book_max_abs_usd | ≈ 0.0502857 |
| Validation of the replica | `127` | Ergebnis (erklärt) | summary.json:h3_days_over_validated_legs | = 127 |
| Validation of the replica | `317` | Ergebnis (erklärt) | summary.json:h3_legs_max | = 317 |

## Konstanten der Präregistrierung

Quelle: `docs/paper2/PRAEREGISTRIERUNG.md` (Commit `1d13227`) mit den Nachträgen 1 bis 4 vom 25.09.2026.

| Wert | Bedeutung | Abschnitt |
|---|---|---|
| 0 | cash = 0 in K_p(q) = Σ p·q − net_IM(q; cash = 0) | Semantik und Kapital |
| 1 | q = +1 bei Maker-Kauf; Dosisfilter 1 %; Schwelle 95. Perzentil 1 % | Semantik und Kapital; Hypothesen, H4; Validierung vor der Messung |
| -1 | q = −1 bei Maker-Verkauf | Semantik und Kapital |
| 30 | Netto-Edge nach 30 Minuten; Laufzeit-Bucketgrenze 30 Tage (Paper 1); Referenzbuch nahe 30 Tagen | Semantik und Kapital |
| 200 | Zelle besetzt ab 200 Fills | Semantik und Kapital |
| 10 000 | 10⁴ in den Zellgrössen (Basispunkte) | Semantik und Kapital |
| 10 | die zehn dominanten Maker-Subaccounts; \|Δ\|-Bucketgrenze 10 % (Paper 1) | Maker-Bücher; Semantik |
| 3 | drei Manager: SM, Legacy-PM, PM2 | Stichprobe (Manager-Fenster) |
| 4 | vier Hypothesen H1 bis H4 | Hypothesen und Ablehnungsregeln |
| 0.5 | Schwelle H1 (obere Grenze ≥ 0,5) und H2 (Median < 0,5) | Hypothesen und Ablehnungsregeln |
| 2 | Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage | Hypothesen und Ablehnungsregeln; Inferenz; Semantik |
| 90 | 90-%-Intervall | Hypothesen und Ablehnungsregeln |
| 20 000 | einfache Zufallsstichprobe von 20 000 Fills (H2) | Hypothesen, H2 |
| 20 260 924 | Seed 20260924 | Hypothesen, H2; Inferenz |
| 14 | Dosisfenster [e − 14 Tage, e) und Regressionsfenster ± 14 Tage | Hypothesen, H4 |
| 20 | mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung) | Hypothesen, H4; Validierung vor der Messung |
| 5 | einseitiges p ≤ 0,05 (fünf Prozent) | Hypothesen, H4 |
| 0.05 | einseitiges p ≤ 0,05 | Hypothesen, H4 |
| 95 | 95. Perzentil (Placebo-β, Validierung) | Hypothesen, H4; Validierung vor der Messung |
| 100 | 100 Placebo-Termine | Hypothesen, H4 |
| 28 | Placebo-Termine mindestens 28 Tage von jedem Ereignis | Hypothesen, H4 |
| 9 999 | B = 9 999 Bootstrap-Ziehungen | Inferenz |
| 48 | mindestens 48 Zufallsblöcke je Basiswert und Manager | Validierung vor der Messung |
| 0.1 | Schwelle Median der absoluten relativen Abweichung 0,1 % | Validierung vor der Messung |
| 63 | 63 Optionen, die ein SM-Konto auf v2 halten kann | Nachtrag 4, Ziffer 2 |
| 25 | \|Δ\|-Bucketgrenze 25 % | Semantik und Kapital (Buckets aus Paper 1) |
| 40 | \|Δ\|-Bucketgrenze 40 % | Semantik und Kapital (Buckets aus Paper 1) |
| 60 | \|Δ\|-Bucketgrenze 60 % | Semantik und Kapital (Buckets aus Paper 1) |
| 0.6 | \|Δ\|-Bucketgrenze 60 % als Delta 0,6 | Semantik und Kapital (Buckets aus Paper 1) |
| 75 | \|Δ\|-Bucketgrenze 75 % | Semantik und Kapital (Buckets aus Paper 1) |
| 7 | Laufzeit-Bucketgrenze 7 Tage | Semantik und Kapital (Buckets aus Paper 1) |
| 2024-01-11 | Stichprobenbeginn 11.01.2024 00:00 UTC | Stichprobe |
| 2026-09-30 | präregistriertes Stichprobenende 30.09.2026 08:00 UTC | Stichprobe |
| 2026-09-17 | Pilotschnitt 17.09.2026 12:00 UTC | Stichprobe |
| 2025-06-12 | PM2-Fenster BTC und ETH ab 12.06.2025 23:00 UTC | Stichprobe (Manager-Fenster) |
| 2025-11-11 | SM und PM2 für HYPE ab 11.11.2025 | Stichprobe (Manager-Fenster) |
| 2024-06-12 | Legacy-PM-Ereignis 12.06.2024 | Hypothesen, H4 |
| 2025-02-22 | Legacy-PM-Ereignis 22.02.2025 | Hypothesen, H4 |
| 2026-09-24 | Präregistrierung, Commit 1d13227 (git log) | Kopf der Präregistrierung |
| 2026-09-25 | Nachträge 1 bis 4, datiert 25.09.2026 | Nachträge 1 bis 4 |
| 00:00 | Stichprobenbeginn und HYPE-Fenster 00:00 UTC | Stichprobe |
| 08:00 | Stichprobenende 08:00 UTC | Stichprobe |
| 12:00 | Pilotschnitt 12:00 UTC | Stichprobe |
| 23:00 | PM2-Fenster ab 23:00 UTC | Stichprobe (Manager-Fenster) |
| 22:33 | Commit 1d13227 um 22:33 UTC+2 (git log) | Kopf der Präregistrierung |

Rechenidentitäten (keine Ergebnisse, nur Lesehilfen):

- -0.1054: ln 0,9: Dosis, wenn Kapital zehn Prozent billiger wird (Lesehilfe zu β, Abbildung F6)
