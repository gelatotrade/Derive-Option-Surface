# Numbers for Paper 2

Generated 2026-10-05 07:02 UTC from `results/p2` with `scripts/p2_numbers.py`. All headline numbers machine-readable in `results/p2/summary.json` (flat, stable keys).

- **Data status:** Sample from 2024-01-11 00:00 UTC to the last fill at 2026-09-17 11:51:53 UTC. **Pilot state:** the sample ends before the preregistered end (2026-09-30 08:00 UTC); the numbers of the manuscript come from the final data run. Cut-off day 2026-09-17.
- **Inference:** B = 9 999, seed 20260924, 90 % percentile intervals from a cluster bootstrap over UTC days (H1 to H3, Addendum 3). H4: wild cluster bootstrap with Rademacher weights and restricted residuals, cluster UTC day, one-sided p for β > 0, 100 placebo dates.
- **Measurement:** capital under IM (MM as a sensitivity), net edge per contract after Addendum 2: NE = MO_30min − (fee − rebate)/amount − hedge; edge of a fill = NE·amount. Accounts only as labels (M1 to M10).

## Sample

- Fills of the Paper 1 sample: 603 940 (BTC 154 676, ETH 405 250, HYPE 44 014).
- PM2 window from BTC 2025-06-12 23:00 UTC, ETH 2025-06-12 23:00 UTC, HYPE 2025-11-11 00:00 UTC: 336 087 fills (BTC 98 479, ETH 193 600, HYPE 44 008).
- Fills with capital per contract ≤ 0 under IM: SM 10, legacy PM 9, PM2 20 (nothing excluded; exclusions only under the rules of H2 and H3).
- H1: 173 of 210 cells populated (at least 200 fills; BTC 60, ETH 68, HYPE 45), 331 813 fills in populated cells, 463 UTC days from 2025-06-12 to 2026-09-17.
- H2: sample of 20 000 fills of the accounts M3, M5, M8, M10 (ETH 13 594, HYPE 6 405), n = 19 999 after exclusion, 372 UTC days from 2025-09-04 to 2026-09-17.
- H3: 1 968 maker days in the window, of which 1 943 computed (not computed: 24 without options, 1 without snapshot), 462 UTC days from 2025-06-13 to 2026-09-17.
- H4: 18 events, 14 kept, of which 13 with panel cells; panel 91 446 rows from 84 919 fills, 475 cell-event pairs, 141 day clusters.

## Validation of the replica against eth_call

- Threshold of the preregistration per underlying, manager and kind: median |rel| < 0.1 %, 95th percentile < 1 %. Result: 32 of 32 cells (IM and MM) met, **passed**.
- 877 cases at blocks from 2024-01-14 to 2026-09-17; 1 case without a chain answer (revert), not comparable.
- Single contracts under IM: n = 799, median |rel| 8.7·10⁻¹⁰, p95 1.4·10⁻⁸, maximum 8.9·10⁻⁸; largest absolute deviation 0.00033 USD.
- Books under IM: n = 77 (2 to 245 legs), median |rel| 2.2·10⁻⁹, p95 1.3·10⁻⁸, maximum 3.4·10⁻⁸; largest absolute deviation 0.050 USD.
- MM (sensitivity): single contracts median 1.1·10⁻⁹, p95 2.0·10⁻⁸; books median 2.2·10⁻⁹, p95 1.5·10⁻⁸.
- Scenario path against direct call: 6 books, bit-identical: yes.

| Kind | Underlying | Manager | n | missing | Median \|rel\| | p95 \|rel\| | Max \|rel\| | Threshold |
|---|---|---|---:|---:|---:|---:|---:|---|
| single contract | BTC | SM | 100 | 0 | 1.4·10⁻¹⁰ | 6.9·10⁻⁹ | 2.4·10⁻⁸ | met |
| single contract | BTC | legacy PM | 100 | 0 | 2.4·10⁻⁹ | 1.5·10⁻⁸ | 3.1·10⁻⁸ | met |
| single contract | BTC | PM2 | 100 | 0 | 1.8·10⁻¹⁰ | 1.4·10⁻⁸ | 5.0·10⁻⁸ | met |
| single contract | ETH | SM | 100 | 0 | 0 | 9.5·10⁻⁹ | 1.4·10⁻⁸ | met |
| single contract | ETH | legacy PM | 100 | 0 | 3.2·10⁻⁹ | 2.0·10⁻⁸ | 6.5·10⁻⁸ | met |
| single contract | ETH | PM2 | 100 | 0 | 7.4·10⁻¹⁰ | 2.3·10⁻⁸ | 8.9·10⁻⁸ | met |
| single contract | HYPE | SM | 100 | 0 | 9.2·10⁻¹² | 5.6·10⁻⁹ | 1.2·10⁻⁸ | met |
| single contract | HYPE | PM2 | 99 | 1 | 1.7·10⁻⁹ | 1.5·10⁻⁸ | 3.5·10⁻⁸ | met |
| book | BTC | SM | 7 | 0 | 7.1·10⁻¹⁰ | 9.3·10⁻⁹ | 1.2·10⁻⁸ | met |
| book | BTC | legacy PM | 7 | 0 | 1.3·10⁻⁹ | 8.0·10⁻⁹ | 8.1·10⁻⁹ | met |
| book | BTC | PM2 | 7 | 0 | 2.2·10⁻¹⁰ | 9.1·10⁻⁹ | 1.1·10⁻⁸ | met |
| book | ETH | SM | 18 | 0 | 7.5·10⁻¹⁰ | 4.0·10⁻⁹ | 6.8·10⁻⁹ | met |
| book | ETH | legacy PM | 18 | 0 | 3.9·10⁻⁹ | 2.4·10⁻⁸ | 3.4·10⁻⁸ | met |
| book | ETH | PM2 | 18 | 0 | 3.8·10⁻⁹ | 1.3·10⁻⁸ | 2.1·10⁻⁸ | met |
| book | HYPE | SM | 1 | 0 | 2.6·10⁻⁹ | 2.6·10⁻⁹ | 2.6·10⁻⁹ | met |
| book | HYPE | PM2 | 1 | 0 | 4.3·10⁻⁹ | 4.3·10⁻⁹ | 4.3·10⁻⁹ | met |

## H1 ranking (preregistered)

- Spearman ρ between edge in bp of notional and edge per PM2 capital over 173 populated cells in the PM2 window: **0.903 [0.881; 0.907]** (90 % interval).
- Rule: rejected if the upper bound is ≥ 0.5. Verdict: **rejected**.
- Pooled over the populated cells: edge 3.38 bp of notional and 39.9 bp of PM2 capital.
- Rank shift (rank by capital minus rank by notional, rank 1 = highest edge): median |Δ| 14.0, largest |Δ| 72.
- Bootstrap: every replication contains at least 173 of the 173 cells; 0 replications without ρ.
- 20 fills with K_PM2 ≤ 0 stay in the sums (Addendum 4); not finite: 0.

| Underlying | Cells | Fills | Edge bp notional | Edge bp PM2 capital | ρ per underlying (exploratory) |
|---|---:|---:|---:|---:|---|
| BTC | 60 | 97 370 | 1.50 | 20.1 | 0.892 [0.871; 0.915] |
| ETH | 68 | 193 326 | 2.98 | 37.8 | 0.922 [0.886; 0.925] |
| HYPE | 45 | 41 117 | 13.48 | 90.8 | 0.888 [0.818; 0.911] |

Largest rank shifts (negative: the cell moves up under capital):

| Cell | Fills | Edge bp notional | Rank | Edge bp capital | Rank | Shift |
|---|---:|---:|---:|---:|---:|---:|
| BTC\|buy\|00-10\|2-7d | 2 149 | 2.63 | 76 | 2 270.0 | 4 | −72 |
| ETH\|buy\|00-10\|2-7d | 2 905 | 2.63 | 77 | 1 372.4 | 10 | −67 |
| BTC\|buy\|00-10\|7-30d | 1 933 | 2.85 | 72 | 1 433.8 | 9 | −63 |
| ETH\|buy\|00-10\|7-30d | 2 990 | 2.83 | 73 | 839.8 | 19 | −54 |
| BTC\|buy\|10-25\|2-7d | 3 312 | 1.67 | 84 | 401.1 | 32 | −52 |
| BTC\|buy\|25-40\|<=2d | 2 111 | −2.56 | 127 | −505.0 | 169 | +42 |
| HYPE\|sell\|40-60\|>90d | 474 | 27.27 | 17 | 85.4 | 60 | +43 |
| ETH\|buy\|10-25\|<=2d | 4 689 | −0.41 | 106 | −140.2 | 151 | +45 |
| BTC\|buy\|00-10\|<=2d | 2 057 | −1.68 | 121 | −2 282.1 | 173 | +52 |
| BTC\|buy\|10-25\|<=2d | 2 778 | −0.81 | 111 | −383.1 | 165 | +54 |

## H2 marginal cost (preregistered)

- Median of ratio = (ΔK/amount)/K_PM2,Einzel over 19 999 fills: **0.0345 [0.0307; 0.0386]** (90 % interval).
- Rule: rejected if the upper bound is ≥ 0.5. Verdict: not rejected.
- Share ratio ≤ 0: 42.0 %. Excluded with K_PM2,Einzel ≤ 0: 1 of 20 000 drawn fills; not finite 0, status not ok 0.
- Accounts (book at the start of the day under PM2): M3, M5, M8, M10; fills per underlying: ETH 13 594, HYPE 6 405; 372 UTC days.
- Cross-check: stored column ratio against recomputation, largest deviation 0.

## H3 netting value (preregistered)

- Median of K_SM/K_PM2 over 1 943 maker days: **4.747 [4.662; 4.824]** (90 % interval).
- Rule: rejected if the lower bound is ≤ 2.0. Verdict: not rejected.
- 1 968 maker days in the window, not computed: 24 without options, 1 without snapshot; excluded with K_PM2 ≤ 0: 0; 462 UTC days from 2025-06-13 to 2026-09-17.
- On 1 431 days (73.6 %) the book holds more than 63 options; K_SM is counterfactual there (Addendum 4).
- Maker days per account: M1 120, M2 328, M3 303, M4 203, M5 374, M6 119, M7 10, M8 239, M10 247.

## H4 price of capital (preregistered)

- β = **−4.60** bp of the index per unit of log dose; 90 % interval [−26.04; 16.59] (wild cluster bootstrap with unrestricted residuals, descriptive); cluster SE 13.09, t −0.351.
- One-sided wild cluster bootstrap p for β > 0: 0.6224 (B = 9 999).
- Placebo: 100 of 100 replications finite; 95th percentile 23.41, median 1.15, mean −7.56, range −101.30 to 42.38; share of placebo β ≥ β: 64 %.
- Criteria: β > 0 no; p ≤ 0.05 no; β above the placebo P95 no.
- Rule: rejected if β is not positive with p ≤ 0.05 or does not lie above the 95th percentile of the placebo β. Verdict: **rejected**.
- Size: n = 91 446 rows, 84 919 fills, 13 events with cells (14 kept), 475 cell-event pairs, 322 day-underlying groups, 141 day clusters.
- Checks: demeaning in 53 iterations, deviation from the direct solution 1.1·10⁻¹³; panel rebuilt identical: yes.

## Exploratory sensitivities

Not preregistered as a test. "Verdict by rule" is the verdict that the preregistered rule of the respective hypothesis would give for this variant.

### (a) Maps under other managers

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| PM2, PM2 window (equal to test H1) | ρ | 0.903 [0.881; 0.907] | 173 | rejected |
| SM, whole period | ρ | 0.896 [0.872; 0.903] | 177 | rejected |
| legacy PM, whole period | ρ | 0.910 [0.885; 0.914] | 132 | rejected |
| SM on the fills of the PM2 window | ρ | 0.898 [0.873; 0.902] | 173 | rejected |
| legacy PM on the fills of the PM2 window | ρ | 0.908 [0.885; 0.912] | 128 | rejected |

### (b) MM instead of IM

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| H1 with MM | ρ | 0.903 [0.880; 0.907] | 173 | rejected |
| map SM, whole period, with MM | ρ | 0.902 [0.879; 0.910] | 177 | rejected |
| H2 with MM | Median dK_mm_per_contract/K_single_pm2_mm_acct | 0.0291 [0.0251; 0.0339] | 19 693 | not rejected |
| h2_ratio_mm_std | Median dK_mm_std_per_contract/K_single_pm2_mm | 0.0278 [0.0242; 0.0324] | 19 977 | not rejected |
| H3 with MM | Median K_sm_mm/K_pm2_mm | 5.614 [5.471; 5.802] | 1 943 | not rejected |

### (c2) Fee of a multi-leg RFQ package spread over its legs (addendum 6)

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| H1 with the RFQ package fee spread over its legs | ρ | 0.904 [0.880; 0.907] | 173 | rejected |

### (c) Net edge in the form of Paper 1 (fee and rebate undivided)

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| H1 with net edge as in Paper 1 | ρ | 0.913 [0.879; 0.915] | 173 | rejected |

### (d) H2 variants

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| ratio (equal to test H2) | Median dK_per_contract/K_single_pm2 | 0.0345 [0.0307; 0.0386] | 19 999 | not rejected |
| next single contract (ratio_unit) | Median dK_unit/K_single_pm2 | 0.0329 [0.0295; 0.0366] | 19 999 | not rejected |
| book from the tape | Median dK_tape_per_contract/K_single_pm2 | 0.0340 [0.0305; 0.0382] | 19 999 | not rejected |
| MM | Median dK_mm_per_contract/K_single_pm2_mm_acct | 0.0291 [0.0251; 0.0339] | 19 693 | not rejected |
| ratio_mm_std | Median dK_mm_std_per_contract/K_single_pm2_mm | 0.0278 [0.0242; 0.0324] | 19 977 | not rejected |
| account M3 | Median dK_per_contract/K_single_pm2 | 0.0230 [0.0126; 0.0356] | 6 405 | not rejected |
| account M5 | Median dK_per_contract/K_single_pm2 | 0.0505 [0.0387; 0.0743] | 5 957 | not rejected |
| account M8 | Median dK_per_contract/K_single_pm2 | 0.0449 [0.0376; 0.0625] | 4 296 | not rejected |
| account M10 | Median dK_per_contract/K_single_pm2 | 0.0258 [0.0220; 0.0293] | 3 341 | not rejected |
| underlying ETH | Median dK_per_contract/K_single_pm2 | 0.0378 [0.0342; 0.0421] | 13 594 | not rejected |
| underlying HYPE | Median dK_per_contract/K_single_pm2 | 0.0230 [0.0126; 0.0356] | 6 405 | not rejected |
| regime R1 | Median dK_per_contract/K_single_pm2 | 0.0503 [0.0411; 0.0693] | 5 137 | not rejected |
| regime R2 | Median dK_per_contract/K_single_pm2 | 0.0372 [0.0305; 0.0466] | 7 906 | not rejected |
| regime R3 | Median dK_per_contract/K_single_pm2 | 0.0117 [−0.0012; 0.0220] | 5 593 | not rejected |
| regime R4 | Median dK_per_contract/K_single_pm2 | 0.0899 [0.0241; 0.1639] | 1 363 | not rejected |
| maker side buy | Median dK_per_contract/K_single_pm2 | −0.1365 [−0.2019; −0.0746] | 9 596 | not rejected |
| maker side sell | Median dK_per_contract/K_single_pm2 | 0.0748 [0.0635; 0.0919] | 10 403 | not rejected |
| ratio of the sums, all | sum(dK) / sum(K_single a) | 0.166 [n/a; n/a] | 19 999 | descriptive |
| ratio of the sums, buy | sum(dK) / sum(K_single a) | −0.397 [n/a; n/a] | 9 596 | descriptive |
| ratio of the sums, sell | sum(dK) / sum(K_single a) | 0.310 [n/a; n/a] | 10 403 | descriptive |

### (e) H3 variants

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| K_SM/K_PM2 (equal to test H3) | Median K_sm/K_pm2 | 4.747 [4.662; 4.824] | 1 943 | not rejected |
| K_SM/K_PM2 with MM | Median K_sm_mm/K_pm2_mm | 5.614 [5.471; 5.802] | 1 943 | not rejected |
| K_SM/K_PM, BTC and ETH legs | Median K_sm_be/K_pm_be | 3.245 [3.174; 3.295] | 1 640 | not rejected |
| K_PM/K_PM2, BTC and ETH legs | Median K_pm_be/K_pm2_be | 1.545 [1.535; 1.554] | 1 640 | descriptive |
| K_SM/K_PM2, BTC and ETH legs | Median K_sm_be/K_pm2_be | 4.826 [4.746; 4.926] | 1 640 | not rejected |
| days with at most 63 options | Median K_sm/K_pm2 | 1.590 [1.532; 1.662] | 512 | rejected |
| days with more than 63 options | Median K_sm/K_pm2 | 5.465 [5.345; 5.606] | 1 431 | not rejected |
| account M1 | Median K_sm/K_pm2 | 5.294 [4.942; 5.472] | 120 | not rejected |
| account M2 | Median K_sm/K_pm2 | 1.076 [1.049; 1.111] | 328 | rejected |
| account M3 | Median K_sm/K_pm2 | 4.357 [4.193; 4.559] | 303 | not rejected |
| account M4 | Median K_sm/K_pm2 | 8.722 [7.524; 9.296] | 203 | not rejected |
| account M5 | Median K_sm/K_pm2 | 5.444 [5.216; 5.671] | 374 | not rejected |
| account M6 | Median K_sm/K_pm2 | 4.239 [3.987; 4.439] | 119 | not rejected |
| account M7 | Median K_sm/K_pm2 | 6.311 [4.925; 12.243] | 10 | not rejected |
| account M8 | Median K_sm/K_pm2 | 5.257 [5.134; 5.361] | 239 | not rejected |
| account M10 | Median K_sm/K_pm2 | 5.663 [5.329; 5.924] | 247 | not rejected |
| regime R1 | Median K_sm/K_pm2 | 4.440 [4.272; 4.592] | 990 | not rejected |
| regime R2 | Median K_sm/K_pm2 | 4.675 [4.496; 4.788] | 590 | not rejected |
| regime R3 | Median K_sm/K_pm2 | 5.720 [5.447; 5.940] | 279 | not rejected |
| regime R4 | Median K_sm/K_pm2 | 6.001 [5.756; 6.620] | 84 | not rejected |
| manager of the account PM | Median K_sm/K_pm2 | 5.457 [5.291; 5.719] | 452 | not rejected |
| manager of the account PM2 | Median K_sm/K_pm2 | 5.161 [5.068; 5.262] | 1 163 | not rejected |
| manager of the account SM | Median K_sm/K_pm2 | 1.076 [1.049; 1.111] | 328 | rejected |
| days with at most 63 options without SM account | Median K_sm/K_pm2 | 3.780 [3.635; 3.980] | 184 | not rejected |

### (f) Time normalisation

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| to expiry, annualised | ρ (edge per capital and year) | 0.806 [0.761; 0.813] | 173 | rejected |
| empirical holding time | ρ (edge per capital and year) | 0.833 [0.795; 0.841] | 173 | rejected |
| holding time without transfers | ρ (edge per capital and year) | 0.822 [0.780; 0.831] | 167 | rejected |

### (g) Values per underlying

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| BTC, PM2 window | ρ | 0.892 [0.871; 0.915] | 60 | rejected |
| BTC, SM, whole period | ρ | 0.911 [0.882; 0.926] | 63 | rejected |
| ETH, PM2 window | ρ | 0.922 [0.886; 0.925] | 68 | rejected |
| ETH, SM, whole period | ρ | 0.890 [0.857; 0.903] | 69 | rejected |
| HYPE, PM2 window | ρ | 0.888 [0.818; 0.911] | 45 | rejected |
| HYPE, SM, whole period | ρ | 0.887 [0.817; 0.910] | 45 | rejected |

### (h) Sign structure of H1 (review round 1; groups by the sign of the edge choose their cells anew in every replication, audit A04)

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| only cells with edge > 0 | ρ | 0.634 [0.572; 0.702] | 99 | rejected |
| only cells with edge ≤ 0 | ρ | 0.636 [0.460; 0.684] | 74 | rejected |
| only maker sells | ρ | 0.990 [0.985; 0.992] | 86 | rejected |
| only maker buys | ρ | 0.721 [0.689; 0.784] | 87 | rejected |
| maker sells with edge > 0 | ρ | 0.940 [0.924; 0.968] | 38 | rejected |
| maker buys with edge > 0 | ρ | 0.243 [0.207; 0.446] | 61 | not rejected |

### (i) RFQ fills and the top of the capital map (audit A12)

| Variant | Quantity | Value [90 % interval] | n | Verdict by rule |
|---|---|---|---:|---|
| H1 without RFQ fills | ρ | 0.900 [0.889; 0.913] | 153 | rejected |
| ten best cells per unit of PM2 capital | RFQ share of the edge | 0.896 [n/a; n/a] | 13 637 | descriptive |
| ten best cells per unit of PM2 capital | RFQ share of the fills | 0.394 [n/a; n/a] | 13 637 | descriptive |

### (h) H4 variants

| Variant | β | 90 % interval | p | n | Placebo P95 | Share placebo β ≥ β | Verdict by rule |
|---|---:|---|---:|---:|---:|---:|---|
| only BTC (5 events) | −3.42 | [−10.51; 3.57] | 0.7497 | 24 598 | n/a | n/a | n/a |
| only ETH (5 events) | −1.90 | [−8.36; 4.68] | 0.6690 | 53 378 | n/a | n/a | n/a |
| only HYPE (3 events) | −10.12 | [−85.84; 64.68] | 0.5778 | 13 470 | n/a | n/a | n/a |
| without cells with \|d\| > 1 | −4.60 | [−26.04; 16.59] | 0.6224 | 91 446 | 23.41 | 65 % | rejected |
| placebo distance to all timelines | −4.60 | [−26.04; 16.59] | 0.6224 | 91 446 | 21.57 | 88 % | rejected |
| placebos only for events with cells, windows separate | −4.60 | [−26.04; 16.59] | 0.6224 | 91 446 | 26.02 | 48 % | rejected |
| dose as the median of the log ratios | −4.52 | [−26.50; 17.29] | 0.6161 | 91 446 | n/a | n/a | n/a |
| dose without fills with \|log ratio\| > 1 | −4.08 | [−25.66; 17.26] | 0.6070 | 91 446 | n/a | n/a | n/a |

- Cells with \|d\| > 1: HYPE-pm2-20260820 HYPE|buy|00-10|2-7d (d = −1.648). In the real panel 0 rows drop out; otherwise the variant acts only in the placebo panels.
- Distance to all timelines: placebo dates keep 28 days away from every parameter change of the underlying under SM, legacy PM, the PM2 standard lib and the account libs.
- Placebos only for events with cells in the real panel, placebo windows of an underlying without overlap (audit A29): 8 to 10 events per replication (median 9); sd(t) of the placebos 1.77.

## Reference book effects of the events

Reference book: short straddle ATM (strike = forward) of the expiry near 30 days, 1 contract per leg, daily at 08:00 UTC; K before computes the same book in the same market state with the parameters of 24 h earlier (pure parameter effect, `results/p2/reference_book.csv`). One row per event from `results/p2/events.csv`; the reference book day is the first day whose parameter state stems from the event. K in bp of the forward.

| Event | Time | Changed structures | max. \|dose\| | kept | Panel cells | Reference book day | K before | K after | Change |
|---|---|---|---:|---|---:|---|---:|---:|---:|
| BTC-pm-20240612 | 2024-06-12 00:01 UTC | basis | 0.06 % | no | 0 | 2024-06-12 | 2 331 | 2 331 | 0.00 % |
| ETH-pm-20240612 | 2024-06-12 00:01 UTC | basis | 0.06 % | no | 0 | 2024-06-12 | 2 412 | 2 412 | 0.00 % |
| BTC-pm-20250222 | 2025-02-22 19:52 UTC | basis, contingencies, vol shock, scenarios | 28.26 % | yes | 25 | 2025-02-23 | 2 303 | 1 913 | −16.94 % |
| ETH-pm-20250222 | 2025-02-22 19:52 UTC | basis, contingencies, vol shock, scenarios | 27.83 % | yes | 50 | 2025-02-23 | 2 458 | 2 035 | −17.21 % |
| BTC-pm2-20251010 | 2025-10-10 22:55 UTC | contingencies | 0.00 % | no | 0 | 2025-10-11 | 1 435 | 1 435 | 0.00 % |
| ETH-pm2-20251010 | 2025-10-10 22:55 UTC | contingencies | 0.00 % | no | 0 | 2025-10-11 | 1 419 | 1 419 | 0.00 % |
| BTC-pm2-20260108 | 2026-01-08 22:50 UTC | margin | 3.60 % | yes | 25 | 2026-01-09 | 1 440 | 1 463 | +1.61 % |
| ETH-pm2-20260108 | 2026-01-08 22:50 UTC | margin | 5.35 % | yes | 37 | 2026-01-09 | 1 431 | 1 454 | +1.62 % |
| HYPE-pm2-20260108 | 2026-01-08 22:50 UTC | margin | 2.09 % | yes | 0 | 2026-01-09 | 4 102 | 4 165 | +1.55 % |
| BTC-pm2-20260123 | 2026-01-23 04:24 UTC | scenarios | 27.33 % | yes | 27 | 2026-01-23 | 1 458 | 1 313 | −9.96 % |
| ETH-pm2-20260123 | 2026-01-23 04:24 UTC | scenarios | 27.14 % | yes | 40 | 2026-01-23 | 1 445 | 1 377 | −4.76 % |
| HYPE-pm2-20260508 | 2026-05-08 12:24 UTC | basis, contingencies | 11.66 % | yes | 29 | 2026-05-09 | 4 193 | 3 893 | −7.16 % |
| BTC-pm2-20260524 | 2026-05-24 04:05 UTC | basis, contingencies, vol shock, scenarios | 8.22 % | yes | 38 | 2026-05-24 | 1 319 | 1 219 | −7.54 % |
| ETH-pm2-20260524 | 2026-05-24 04:05 UTC | contingencies, vol shock | 5.45 % | yes | 54 | 2026-05-24 | 1 340 | 1 296 | −3.30 % |
| HYPE-pm2-20260524 | 2026-05-24 04:05 UTC | basis, margin, contingencies, vol shock, scenarios | 44.21 % | yes | 35 | 2026-05-24 | 3 836 | 2 638 | −31.22 % |
| BTC-pm2-20260820 | 2026-08-20 22:09 UTC | basis, contingencies, vol shock, scenarios | 67.47 % | yes | 43 | 2026-08-21 | 1 213 | 935 | −22.93 % |
| ETH-pm2-20260820 | 2026-08-20 22:09 UTC | basis, contingencies, vol shock, scenarios | 51.51 % | yes | 52 | 2026-08-21 | 1 307 | 1 089 | −16.71 % |
| HYPE-pm2-20260820 | 2026-08-20 22:09 UTC | margin, contingencies, vol shock, scenarios | 164.82 % | yes | 20 | 2026-08-21 | 2 514 | 2 051 | −18.39 % |

Parameter effects in the reference book without an event row (outside the manager window or not in the event list):

- PM2 BTC 2025-06-13: −0.35 %, parameter state of 2025-06-12 22:20 UTC.
- PM2 ETH 2025-06-13: −0.69 %, parameter state of 2025-06-12 22:20 UTC.

Level of the reference book (K in bp of the forward over the days in the manager window):

| Underlying | Manager | Days | Minimum | Median | Maximum |
|---|---|---:|---:|---:|---:|
| BTC | SM | 981 | 2 724 | 2 945 | 3 000 |
| BTC | legacy PM | 981 | 1 888 | 1 950 | 2 700 |
| BTC | PM2 | 462 | 933 | 1 369 | 1 464 |
| ETH | SM | 981 | 2 726 | 2 956 | 3 000 |
| ETH | legacy PM | 981 | 1 909 | 2 101 | 2 727 |
| ETH | PM2 | 462 | 1 078 | 1 422 | 1 589 |
| HYPE | SM | 311 | 5 750 | 5 990 | 6 000 |
| HYPE | PM2 | 311 | 1 997 | 4 062 | 4 375 |

## Manager shares of the options OI

Share of `OptionAsset.totalPosition` per manager in the sum over the managers, each on the first day of the month (`results/p2/manager_oi_share.csv`).

- BTC: data from 2024-01; PM2 first in 2025-07 (17.2 %); at most 95.3 % (2026-07); legacy PM below 1 % from 2026-02; last (2026-09) SM 9.0 %, legacy PM 0.0 %, PM2 91.0 %.
- ETH: data from 2024-02; PM2 first in 2025-07 (12.0 %); at most 80.6 % (2026-08); legacy PM below 1 % from 2026-02; last (2026-09) SM 28.1 %, legacy PM 0.0 %, PM2 71.9 %.
- HYPE: data from 2025-12; PM2 first in 2025-12 (51.4 %); at most 93.0 % (2026-04); last (2026-09) SM 12.1 %, PM2 87.9 %.

| Month | BTC SM | BTC legacy PM | BTC PM2 | ETH SM | ETH legacy PM | ETH PM2 | HYPE SM | HYPE PM2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024-01 | 78.1 % | 21.9 % | 0.0 % | n/a | n/a | n/a | n/a | n/a |
| 2024-02 | 46.0 % | 54.0 % | 0.0 % | 47.4 % | 52.6 % | 0.0 % | n/a | n/a |
| 2024-03 | 31.9 % | 68.1 % | 0.0 % | 33.5 % | 66.5 % | 0.0 % | n/a | n/a |
| 2024-04 | 26.0 % | 74.0 % | 0.0 % | 29.0 % | 71.0 % | 0.0 % | n/a | n/a |
| 2024-05 | 34.8 % | 65.2 % | 0.0 % | 30.0 % | 70.0 % | 0.0 % | n/a | n/a |
| 2024-06 | 13.3 % | 86.7 % | 0.0 % | 32.8 % | 67.2 % | 0.0 % | n/a | n/a |
| 2024-07 | 20.5 % | 79.5 % | 0.0 % | 42.3 % | 57.7 % | 0.0 % | n/a | n/a |
| 2024-08 | 31.0 % | 69.0 % | 0.0 % | 38.9 % | 61.1 % | 0.0 % | n/a | n/a |
| 2024-09 | 36.7 % | 63.3 % | 0.0 % | 42.9 % | 57.1 % | 0.0 % | n/a | n/a |
| 2024-10 | 47.0 % | 53.0 % | 0.0 % | 40.2 % | 59.8 % | 0.0 % | n/a | n/a |
| 2024-11 | 48.7 % | 51.3 % | 0.0 % | 36.1 % | 63.9 % | 0.0 % | n/a | n/a |
| 2024-12 | 46.5 % | 53.5 % | 0.0 % | 46.7 % | 53.3 % | 0.0 % | n/a | n/a |
| 2025-01 | 47.1 % | 52.9 % | 0.0 % | 48.6 % | 51.4 % | 0.0 % | n/a | n/a |
| 2025-02 | 44.1 % | 55.9 % | 0.0 % | 45.5 % | 54.5 % | 0.0 % | n/a | n/a |
| 2025-03 | 46.1 % | 53.9 % | 0.0 % | 43.8 % | 56.2 % | 0.0 % | n/a | n/a |
| 2025-04 | 47.9 % | 52.1 % | 0.0 % | 51.0 % | 49.0 % | 0.0 % | n/a | n/a |
| 2025-05 | 46.7 % | 53.3 % | 0.0 % | 49.6 % | 50.4 % | 0.0 % | n/a | n/a |
| 2025-06 | 45.5 % | 54.5 % | 0.0 % | 48.7 % | 51.3 % | 0.0 % | n/a | n/a |
| 2025-07 | 42.2 % | 40.6 % | 17.2 % | 50.6 % | 37.4 % | 12.0 % | n/a | n/a |
| 2025-08 | 45.6 % | 33.7 % | 20.7 % | 47.0 % | 38.9 % | 14.1 % | n/a | n/a |
| 2025-09 | 41.4 % | 39.8 % | 18.8 % | 42.8 % | 44.1 % | 13.1 % | n/a | n/a |
| 2025-10 | 37.5 % | 32.0 % | 30.5 % | 41.2 % | 37.5 % | 21.3 % | n/a | n/a |
| 2025-11 | 38.5 % | 17.1 % | 44.3 % | 37.9 % | 12.1 % | 50.0 % | n/a | n/a |
| 2025-12 | 37.8 % | 22.7 % | 39.5 % | 40.0 % | 13.1 % | 46.8 % | 48.6 % | 51.4 % |
| 2026-01 | 38.4 % | 4.1 % | 57.5 % | 27.8 % | 8.8 % | 63.4 % | 28.7 % | 71.3 % |
| 2026-02 | 28.7 % | 0.0 % | 71.3 % | 38.4 % | 0.2 % | 61.4 % | 46.1 % | 53.9 % |
| 2026-03 | 14.0 % | 0.0 % | 86.0 % | 29.6 % | 0.0 % | 70.4 % | 26.2 % | 73.8 % |
| 2026-04 | 6.1 % | 0.0 % | 93.9 % | 28.1 % | 0.0 % | 71.9 % | 7.0 % | 93.0 % |
| 2026-05 | 7.4 % | 0.0 % | 92.6 % | 30.8 % | 0.0 % | 69.2 % | 13.9 % | 86.1 % |
| 2026-06 | 16.4 % | 0.0 % | 83.6 % | 39.4 % | 0.0 % | 60.6 % | 16.4 % | 83.6 % |
| 2026-07 | 4.7 % | 0.0 % | 95.3 % | 30.1 % | 0.0 % | 69.9 % | 15.9 % | 84.1 % |
| 2026-08 | 5.1 % | 0.0 % | 94.9 % | 19.4 % | 0.0 % | 80.6 % | 12.8 % | 87.2 % |
| 2026-09 | 9.0 % | 0.0 % | 91.0 % | 28.1 % | 0.0 % | 71.9 % | 12.1 % | 87.9 % |

## Review round 1 (exploratory or descriptive)

- H1, sign only: shuffling the ranks within the 99 cells with edge > 0 and within the 74 others (4 000 draws) gives ρ 0.734 on average (5th to 95th percentile 0.700 to 0.770).
- H1 within groups: edge > 0 0.634 (n = 99), edge ≤ 0 0.636 (n = 74), sells 0.990, buys 0.721, buys with edge > 0 0.243 (n = 61).
- Best cells: the ten best per capital and the ten best per notional share 1 cells, the best 20 share 5; same sign in 173 cells.
- H2: population before the draw 100 995 fills; the preregistered draw gives exactly the fills of marginal.parquet: yes.
- H3 accounts by manager: PM 4, PM2 4, SM 1.
- H3: 8 of 9 account medians above the threshold 2; at most 63 options without SM account 3.780 [3.635; 3.980] (n = 184).
- H3: 127 maker days with more legs than the largest validated book (245 legs).
- Fills outside every manager window (without capital): 6.
- API against chain semantics (195 single contracts on 2026-09-25): PM2 median |rel| 0.08 %, p95 0.50 %, maximum 2.41 % (tenor >90d); SM median 0.00 %, maximum 0.30 %.
- H4 level: half spread in the panel 7.93 bp of the index on average (median 3.34); capital ten per cent cheaper (dose −0.105): change of the half spread +0.48 bp, interval −1.75 to +2.74 bp.
- H4 only sell cells: β −3.81, p 0.5766; OI-weighted dose (share 54.5 % to 94.9 %): β −5.13, p 0.5926.

## Audit (exploratory)

Exploratory or descriptive (docs/paper2/AUDIT.md); no registered verdict changes.

- H1 in sign groups (A04, selection anew in each replication: every replication chooses the cells by its own edge): edge > 0 0.634 [0.572; 0.702], edge ≤ 0 0.636 [0.460; 0.684], sells with edge > 0 0.940 [0.924; 0.968], buys with edge > 0 0.243 [0.207; 0.446]; on average 9.2 % (edge > 0) and 19.2 % (edge ≤ 0) of the cells leave their group per replication. Groups by side stay fixed.
- H1 interval (A28): 15.2 % of the 9 999 draws lie on or above the estimate 0.9029 (mean 0.8946, median 0.8950); the percentile interval [0.881; 0.907] is not centred. Reflected [0.898; 0.925], bias-corrected [0.898; 0.920].
- H4, placebo t (A05): sd(t) 1.82 (MAD sd 2.13), 5th/95th percentile −2.62/2.83; share t > 1.645 21 %, |t| > 1.645 43 %; sd of the placebo β 28.7 at a median SE of 8.8.
- H4, range for β calibrated to the placebo t: [−41.6; 29.7] (SE times sd(t): [−43.7; 34.5]); p against the placebo t 0.62. Capital ten per cent cheaper: −3.13 to +4.39 bp (SE times sd(t): −3.64 to +4.61 bp); largest narrowing in the range 39 % of the mean half spread 7.93 bp (descriptive interval: 22 %; SE times sd(t): 46 %).
- H4, construction of the placebo panels (A29): always 14 events with cells per replication, in the real panel 13 of 14 (without cells: HYPE-pm2-20260108); rows at the median 97 997 against 91 446 (1.08 per fill), day clusters at the median 189 against 141; pairs of overlapping windows of one underlying per replication on average 11.6 against 3 in the real panel, days drawn twice on average 0.82.
- H4, dose (A30): 4 of 475 cell-event pairs contain fills with |log ratio| > 1 (6 fills), in 6 pairs the median departs from the mean by more than 0.05. β with the median dose −4.52 (p 0.6161), without these fills −4.08 (p 0.6070); registered −4.60.

## Consistency checks

15 of 15 checks met. The checks recompute the verdicts from the numbers and rules and reconcile the files with one another.

- Cut-off day consistent: met (last day of H1, H3 and the reference book equal to the day of the last fill (2026-09-17), H2 ends on 2026-09-17).
- B, seed and level equal in all files: met (B = 9 999, seed 20260924, level 90 %).
- Fills per underlying add up to the sample: met (154 676 + 405 250 + 44 014 = 603 940).
- PM2 window: capital file and H1 count the same: met (336 087 against 336 087).
- Validation: all cells below the threshold: met (32 of 32 cells).
- H1: ρ from h1_cells.csv equal to h1.json: met (0.902944 against 0.902944).
- H1: populated cells and fills equal to h1.json: met (173 cells, 331 813 fills).
- H1: verdict follows from the rule (upper bound ≥ threshold): met (upper bound 0.907, threshold 0.5).
- H2: verdict follows from the rule (upper bound ≥ threshold): met (upper bound 0.0386, threshold 0.5).
- H2: stored ratio equal to recomputation: met (largest deviation 0).
- H3: verdict follows from the rule (lower bound ≤ threshold): met (lower bound 4.662, threshold 2.0).
- H4: criteria and verdict follow from β, p and the placebo P95: met (β −4.60, p 0.6224, P95 23.41).
- H4: demeaning equal to the direct solution, panel reproduced: met (deviation 1.1·10⁻¹³, panel rebuilt identical: yes).
- H4: kept events in events.csv equal to h4.json: met (14 against 14).
- Sensitivities: base variant equal to the test: met (3 of 3 equal).

## Limitations of these numbers

- Pilot state: the sample ends at 2026-09-17 11:51:53 UTC, before the preregistered end (2026-09-30 08:00 UTC). The numbers of the manuscript come from the final data run.
- H3: on 73.6 % of the maker days the book holds more options than an SM account on v2 can hold; K_SM is counterfactual there.
- H1: 20 fills with K_PM2 ≤ 0 (RFQ legs priced far from the mark) stay in the sums.
- H2 rests on 4 accounts under PM2; the distribution per account is under (d).
- H4: the interval for β is descriptive and conditional on the event dates; the verdict follows from the one-sided p and the placebo P95. 141 day clusters, 13 events with cells. At placebo dates t scatters with sd 1.82 instead of 1; the range calibrated to the placebo t is under Audit.
- Capital per fill is the capital of an empty book holding exactly this contract (single contract); non-USDC collateral stays outside K.
