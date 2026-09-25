# Vol feed check

Run 2026-09-17 14:48 UTC, head block 44,817,461.

## Continuity

177 samples of 200 blocks each from block 800,000 on, spaced 250,000 apart; 14 distinct emitters.

| Feed | Samples with events | first | last | Gaps after the start | Forward first → last |
|---|---|---|---|---|---|
| BTC | 166 | 2,050,000 | 44,800,000 | 6: 2,300,000, 2,550,000, 2,800,000, 3,300,000, 3,550,000, 4,800,000 | 42,943.40 → 76,648.13 |
| ETH | 166 | 2,050,000 | 44,800,000 | 6: 2,300,000, 2,550,000, 2,800,000, 3,300,000, 3,550,000, 4,800,000 | 2,317.43 → 2,446.14 |
| HYPE | 57 | 30,800,000 | 44,800,000 | none | 47.61 → 79.34 |

### Possible replacement feeds (unknown address, forward within ±15% of the last core forward)

| Block | Core feed | Candidate | Forward | Events |
|---|---|---|---|---|
| 4,550,000 | BTC (last 59,473.14) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 56,564.28 | 2 |
| 5,050,000 | BTC (last 68,791.35) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 68,003.50 | 1 |
| 5,300,000 | BTC (last 67,817.62) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 67,402.02 | 1 |
| 5,550,000 | BTC (last 64,213.20) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 63,807.27 | 1 |
| 5,800,000 | BTC (last 71,024.44) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 70,343.02 | 2 |
| 6,050,000 | BTC (last 66,545.80) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 66,142.01 | 1 |
| 6,300,000 | BTC (last 72,341.64) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 71,698.72 | 2 |
| 6,550,000 | BTC (last 64,379.25) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 64,204.52 | 1 |
| 6,800,000 | BTC (last 64,003.11) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 63,943.73 | 2 |
| 7,050,000 | BTC (last 64,492.04) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 64,371.20 | 6 |
| 40,300,000 | HYPE (last 64.06) | 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 70.32 | 7 |
| 40,550,000 | HYPE (last 53.87) | 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 61.63 | 7 |
| 40,800,000 | HYPE (last 73.85) | 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 73.27 | 6 |
| 41,050,000 | HYPE (last 67.53) | 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 75.41 | 7 |

### Unknown emitters (neither core feeds nor known other feeds)

| Address | Samples | first | last | Forward (median) |
|---|---|---|---|---|
| 0x533acdac4ac1155a0946d0e1890712d98984de1e | 16 | 4,550,000 | 8,550,000 | 6.388e+04 |
| 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 70 | 24,800,000 | 42,300,000 | 165.8 |

## Formula: latest signed curve against the live mark IV

Checks `svi_vol` (reference tau, SVI forward) without a time lag. Δ IV in vol units (0.01 = 1 vol point).

| Underlying | Expiry | Options | Age of the signed curve (s) | max. abs. Δ IV | Median abs. Δ IV |
|---|---|---|---|---|---|
| BTC | 20260918 | 76 | 19 | 0.00001 | 0.00001 |
| BTC | 20260919 | 34 | 19 | 0.00001 | 0.00000 |
| BTC | 20260920 | 34 | 19 | 0.00001 | 0.00000 |
| ETH | 20260918 | 62 | 20 | 0.00001 | 0.00000 |
| ETH | 20260919 | 54 | 20 | 0.00001 | 0.00001 |
| ETH | 20260920 | 58 | 20 | 0.00001 | 0.00000 |
| HYPE | 20260918 | 60 | 22 | 0.00001 | 0.00001 |
| HYPE | 20260919 | 38 | 22 | 0.00001 | 0.00001 |

## Cross-check: last curve pushed on chain against the live mark IV

The on-chain curve lags the backend mark by the time shown; the deviation measures this lag, not the formula.

| Underlying | Expiry | Options | max. abs. Δ IV | Median abs. Δ IV | Age of the SVI (s) |
|---|---|---|---|---|---|
| BTC | 20260918 | 76 | 0.01839 | 0.00531 | 184 |
| BTC | 20260919 | 34 | 0.00223 | 0.00165 | 184 |
| BTC | 20260920 | 34 | 0.02075 | 0.00607 | 184 |
| ETH | 20260918 | 62 | 0.01622 | 0.01148 | 206 |
| ETH | 20260919 | 54 | 0.00589 | 0.00210 | 206 |
| ETH | 20260920 | 58 | 0.00583 | 0.00450 | 206 |
| HYPE | 20260918 | 60 | 0.05320 | 0.04070 | 188 |
| HYPE | 20260919 | 38 | 0.03274 | 0.01326 | 188 |
| HYPE | 20260920 | 0 | n/a | n/a | 188 |
