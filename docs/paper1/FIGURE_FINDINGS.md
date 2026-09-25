# Findings that arose while building the figures

Status: 2026-09-18, section 2 revised on 2026-09-25. Pilot sample with cut-off 2026-09-17 12:00 UTC,
603,940 fills.
None of this changes the pre-registration; these are descriptive supplementary quantities for the figures.

## 1. The registered net edge in USDC is not a map but a price level

The registered H4 quantity is the net edge in USDC per contract. Computed across the cells, it rises
almost monotonically with tenor, for BTC from about 10 USDC at <= 2 days to 200 to 300 USDC beyond
90 days. Above all, this measures that long-dated options are expensive. For the question of where a market maker
should quote, the edge per unit of risk taken on is the right quantity.

## 2. Relative to notional, the margin is thinnest where the flow is

Revised on 2026-09-25 (Addendum 3 to the pre-registration, finding `FINDING_2026-09-25_FEE_UNITS.md`). The
first version of this section divided the net edge per contract by the notional of the whole fill and subtracted
fee and rebate as totals of the fill. Its table (BTC 9.0 / 28.5 / 73.8, ETH 0.9 / 3.3 / 4.8, HYPE
0.3 / 0.5 / 0.1) and the statements based on it (same ordering in all underlyings, an order of magnitude between the
underlyings, HYPE practically zero) came from this unit error. The correct quantity is the edge of the fill divided by
its notional, i.e. 10^4 x NE per contract / index.

Median net edge in basis points of notional, cells with at least 200 fills:

| Underlying | ATM, <= 2 d | ATM, 30 to 90 d | deep in the money, <= 2 d | Median across the cells | Range of the cells |
|---|---|---|---|---|---|
| BTC | 2.8 | 5.8 | 15.5 | 3.3 | 0.9 to 15.6 |
| ETH | 3.8 | 9.8 | 15.5 | 5.7 | -82.8 to 28.8 |
| HYPE | 5.0 | 27.2 | 11.8 | 15.1 | -6.2 to 68.8 |

- In every underlying and every delta row below 75, the edge beyond 90 days is 2.5 to 10 times
  the value at <= 2 days. The map is not strictly monotonic: up to 75 delta, ETH also rises with delta,
  while BTC and HYPE scatter more. The deep in-the-money rows with few fills break the pattern (ETH 90-100 beyond
  90 days -82.8 bp with 325 fills, HYPE 75-90 <= 2 d -6.2 bp).
- The ordering of the underlyings reverses relative to USDC per contract: BTC pays the most per contract and the
  least per notional, HYPE the most per notional.
- Where the flow is, the margin is thin: options up to 7 days with |delta| below 60 carry about 46 % of the BTC
  and ETH fills and earn 1.0 to 2.8 bp (BTC) and 1.6 to 3.8 bp (ETH) respectively.

The figure for the practitioner map therefore shows both units: USDC per contract as the registered
quantity, and basis points of notional as the quantity a bot decides by.

## 3. The example fill for the mechanism figure is real

T1 shows ETH-20250110-3600-C, 2025-01-04 12:38 UTC, taker of class other, no RFQ. The maker buys
1.00 contract at 125.00 against a curve that says 125.41, and so earns 0.41 USDC of half spread. Thirty
minutes later the curve stands at 121.69: adverse selection -3.72, markout -3.31 USDC. The curve at the fill
was 23 seconds old. The fill is chosen by `figdata.example_fill`: class other, positive half spread,
markout below minus the half spread, notional closest to the median.

Status 2026-09-25: an earlier version of this section named BTC-20260807-64000-C (2026-08-01, maker
sells at 496.68 against 473.98, markout -172.78 USDC, two-legged RFQ). This fill no longer appears in any
figure.

## 4. The two mark paths agree once the comparison is fair

| Group | Fills | Correlation | Same sign | Median difference |
|---|---|---|---|---|
| all | 540,531 | 0.390 | 69.1 % | 0.022 |
| next fill <= 300 s later | 26,885 | 0.896 | 91.3 % | -0.005 |
| next fill <= 3,600 s later | 135,971 | 0.939 | 83.5 % | 0.007 |
| curve <= 60 s old | 501,384 | 0.397 | 68.8 % | 0.023 |

The weak overall correlation comes from the median distance to the next fill of 15,026 seconds, not from
the curve: with a fresh curve almost nothing changes, and with a comparison fill close in time the correlation rises
to 0.94.
