# Numbers for paper 1

Generated 2026-09-25 10:24 UTC from `results/p1` with `scripts/p1_numbers.py`. Pilot data up to 2026-09-17 12:00 UTC. Primary horizon 30m, mark path (b) by push time, clusters by taker wallet, B = 9999, seed 20260917, perp half spread 1.0 bp. 603 940 fills; without a fill IV (only the vol unit is affected): 10 745. Fee and rebate enter per contract (the sum of the fill divided by its amount, addendum 3 of 2026-09-25).

## H1 Concentration of toxicity

- Top-10 share of the aggregate maker loss: **90.5 %** (90 % interval 69.8 to 94.3 %), total loss -3 240 781 USDC over 11 573 wallets.
- Size above the 90th percentile: coefficient -0.765 USDC (t -0.74, p 0.4761).
- Sweep: coefficient -0.357 USDC (t -0.10, p 0.9442).
- Verdict: **rejected**.

## H2 Vault flow is uninformed

- 30 min markout of the vault fills: 4.220 USDC (95 % interval 1.644 to 8.550, p 0.0092, 1 994 fills, 8 wallets).
- VRP-adjusted settlement markout: -6.366 USDC (95 % interval -17.789 to 5.137).
- Verdict: not rejected.

## H3 HYPE before and after the Deribit listing

- Event 2026-06-23 09:00 UTC, window ±90 days, outcome vol markout.
- DiD coefficient -1.046 vol points (t -1.23, p 0.2419, 147 240 fills, 3879 wallets).
- Placebo dates: 100, of which more extreme: 46.0 %.
- Verdict: **rejected**.

## H4 Net edge per cell

- Occupied cells (≥ 200 fills): 97; of these with a positive 90 % interval: **76.3 %**.
- Cells positive / negative / open: 74 / 0 / 23; with a positive mean and wild p ≤ 0.10 (robustness, not the rule): 52 (53.6 %).
- Short-dated ATM BTC 40-60 Δ, ≤ 2 d: 24.193 USDC (90 % interval 6.429 to 46.367, wild p 0.104, 8 902 fills)
- Short-dated ATM ETH 40-60 Δ, ≤ 2 d: 1.053 USDC (90 % interval 0.199 to 2.098, wild p 0.153, 23 718 fills)
- Verdict: **rejected**.

### Sensitivity to the perp half spread

| Half spread (bp) | Cells | Share positive |
|---|---|---|
| 0.0 | 97 | 78.4 % |
| 1.0 | 97 | 76.3 % |
| 3.0 | 97 | 58.8 % |

## Counterparty classes (30 min, path b)

All amounts in USDC per contract; fee and rebate per contract. The interval refers to the markout. The net edge of the class vault rests on 8 taker wallets and is reported without an interval.

| Class | Fills | Half spread | Adverse selection | Markout USDC | 95 % interval | Fee | Rebate | Hedge | Net edge | Share negative |
|---|---|---|---|---|---|---|---|---|---|---|
| dominant_maker | 56 274 | -16.60 | -8.81 | -25.41 | -28.35 to -19.42 | 2.75 | 0.11 | 3.93 | -31.98 | 67.6 % |
| mm_programme | 42 976 | -5.17 | -15.50 | -20.67 | -24.41 to -2.16 | 1.82 | 0.66 | 4.94 | -26.76 | 66.1 % |
| large | 52 200 | 6.40 | -2.51 | 3.89 | -8.73 to 18.70 | 1.35 | 1.02 | 2.76 | 0.79 | 35.7 % |
| vault | 1 994 | 4.32 | -0.10 | 4.22 | 1.64 to 8.55 | 1.13 | 0.02 | 1.02 | 2.09 | 31.6 % |
| rfq | 121 064 | 15.38 | -0.17 | 15.21 | 12.19 to 19.05 | 0.30 | 0.00 | 3.11 | 11.80 | 34.5 % |
| other | 329 432 | 25.60 | -0.87 | 24.73 | 22.05 to 28.02 | 0.96 | 1.14 | 2.87 | 22.04 | 27.0 % |

## Horizons (path b, means)

| Horizon | Fills | USDC | delta-neutral | Vol points | Path (a) USDC |
|---|---|---|---|---|---|
| 1m | 603 940 | 15.217 | 15.712 | 2.588 | 12.959 |
| 5m | 603 940 | 13.251 | 15.644 | 2.576 | 12.806 |
| 30m | 603 940 | 13.051 | 15.454 | 2.553 | 12.543 |
| 4h | 599 439 | 13.080 | 15.389 | 2.470 | 12.594 |
| 24h | 511 237 | 12.970 | 15.955 | 1.891 | 13.198 |

## Cells with the largest and smallest net edge

| Underlying | Delta | Tenor | Fills | Net edge | 90 % interval |
|---|---|---|---|---|---|
| ETH | 90-100 | >90d | 325 | -30.283 | -77.270 to 9.844 |
| HYPE | 75-90 | <=2d | 472 | -0.034 | -0.105 to 0.093 |
| HYPE | 90-100 | <=2d | 277 | -0.020 | -0.202 to 0.196 |
| HYPE | 10-25 | <=2d | 1 369 | -0.002 | -0.029 to 0.023 |
| HYPE | 60-75 | <=2d | 526 | 0.015 | -0.078 to 0.110 |
| BTC | 90-100 | <=2d | 1 580 | 148.629 | 40.773 to 297.053 |
| BTC | 40-60 | >90d | 1 795 | 199.363 | 108.935 to 324.636 |
| BTC | 10-25 | >90d | 1 529 | 204.207 | 117.522 to 313.830 |
| BTC | 60-75 | >90d | 464 | 300.514 | 75.246 to 583.853 |
| BTC | 25-40 | >90d | 1 607 | 305.765 | 123.954 to 514.743 |

## From the recalculation of the fee unit (revision 2026-09-25)

These numbers are not in `results/p1` but in `results/p1_finding/fee_units.csv` (`scripts/p1_fee_units_finding.py`); the source is given per line.

Decomposition per contract with B = 9 999 (section `decomposition_b9999`, variant `per_contract`; text section 3):

| Quantity | Mean USDC | 95 % interval |
|---|---|---|
| half spread | 15.701 | 9.906 to 22.138 |
| adverse selection | -2.651 | -4.693 to -0.715 |
| markout | 13.051 | 5.592 to 21.247 |
| maker fee | -1.091 | -1.346 to -0.806 |
| maker rebate | 0.769 | 0.648 to 0.913 |
| hedge cost | -3.149 | -3.469 to -2.813 |
| net edge | 9.579 | 1.562 to 18.309 |

- RFQ package (section `rfq_package`, addendum 3 no. 3): fee spread over the package, net edge 9.578 USDC per contract; cells positive / negative at 1 bp 74 / 0.

Robustness of H4 by wild p (positive mean and p ≤ 0.10, not the rule; from the cell tables under `data/p1/fee_units_finding`, text section 5.5):

| Half spread (bp) | Cells | positive (rule) | positive by wild p |
|---|---|---|---|
| 0 | 97 | 76 | 59 (60.8 %) |
| 1 | 97 | 74 | 52 (53.6 %) |
| 3 | 97 | 57 | 44 (45.4 %) |

## Limitations of these numbers

- Pilot state: sample up to 2026-09-17 12:00 UTC. The first version of the manuscript (2026-09-19) and the revision (2026-09-25) rest on this state; the final data run with the registered cut-off 2026-09-30 08:00 UTC is still outstanding.
- The first version subtracted fee and rebate as sums over the fill from the per-contract markout (addendum 3, `docs/paper1/FINDING_2026-09-25_FEE_UNITS.md`); all numbers here are corrected.
- H2 rests on 8 vault wallets; with so few clusters the wild cluster bootstrap is unreliable, so the result is an indication, not proof.
- Path (b) is a mark delayed by minutes (on-chain push per expiry every 60 s at the median, the forward of the curve instead of the live forward). The 1 min and 5 min horizons are affected most; path (a) is shown next to it in the horizon table.
- The vol unit is missing for 10 745 fills without a fill IV (price outside the arbitrage bounds).
- The class "liquidation" is empty: liquidations happen outside the trade tape.
