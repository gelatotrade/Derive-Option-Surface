# Data status of paper 1 (pilot)

Generated 2026-09-17 20:11 UTC with `scripts/p1_data_status.py`. Contains only counts and checks, no markouts (pre-registration). Pilot cut-off 2026-09-17 12:00 UTC; the final cut-off is 2026-09-30 08:00 UTC.

## Options tape

Period 2023-12-01 00:00 UTC to 2026-09-17 12:00 UTC (both inclusive), finished 2026-09-17 14:11 UTC. 1 229 160 rows in 2 010 single-page windows; days with a differing recount: 0. The API reports 1 229 162 rows for the whole period; this number is not additive over long ranges and is for information only.

| Underlying | Rows | SHA-256 (prefix) |
|---|---|---|
| ETH | 811 638 | `0fc5f90969866a67` |
| BTC | 312 536 | `0829120c41723661` |
| HYPE | 88 256 | `0d7d267ec9c51f92` |
| SOL | 6 906 | `983630c6fcab5634` |
| ZEC | 3 988 | `3039578c1ae4ca40` |
| XRP | 2 794 | `b71a29b571f9487b` |
| XAUT | 2 408 | `85645c2af39ec53a` |
| ADA | 588 | `3f501feb2e9b1e17` |
| SNX | 18 | `1e18e29ee4422df6` |
| PUMP | 12 | `3bfd2dcbe2e55c62` |
| LIT | 8 | `6bcf67174ba1a41d` |
| VVV | 6 | `c0cbf7554d114481` |
| AAVE | 2 | `c2f3030f2bcaa986` |

## Fills and counterparty classes (without markouts)

1 229 160 rows give 614 576 fills. Rows without a partner: 8 (8 trade_ids); pairs with a differing price, a differing amount or the same direction: 0; not settled: 0. Liquidation transactions in the match: 43414.

Rows without a partner: BTC-20250826-115000-C taker 2025-08-25 11:56 UTC; BTC-20250826-115000-C taker 2025-08-25 11:56 UTC; BTC-20250826-115000-C taker 2025-08-25 11:57 UTC; BTC-20250826-115000-C taker 2025-08-25 11:57 UTC; BTC-20250826-115000-C taker 2025-08-25 12:04 UTC; BTC-20250826-115000-C taker 2025-08-25 12:04 UTC; BTC-20250826-115000-C taker 2025-08-25 12:04 UTC; BTC-20250829-116000-P taker 2025-08-25 12:20 UTC.

| Taker class | BTC fills | BTC notional (million USD) | ETH fills | ETH notional (million USD) | HYPE fills | HYPE notional (million USD) |
|---|---|---|---|---|---|---|
| liquidation | 0 | 0 | 0 | 0 | 0 | 0 |
| vault | 366 | 78 | 1 628 | 401 | 0 | 0 |
| rfq | 31 568 | 6 509 | 67 367 | 2 930 | 22 262 | 1 694 |
| dominant_maker | 13 990 | 221 | 42 067 | 270 | 382 | 11 |
| mm_programme | 15 506 | 986 | 25 328 | 654 | 2 143 | 23 |
| large | 14 620 | 1 203 | 33 946 | 1 645 | 3 748 | 66 |
| other | 80 214 | 2 085 | 235 483 | 2 952 | 15 593 | 148 |

Flags (core): RFQ 122 511, vault as taker 1 994, vault as maker 360, liquidation 0, taker in the MM programme 96 009.
The class MM programme can only be assigned from 2024-11-20 00:00 UTC on; 112 980 core fills lie before that.
Time gap taker minus maker row, RFQ: median 3.1 s, 99th percentile 75.2 s, maximum 1 689 s.
Time gap taker minus maker row, book: median 0.0 s, 99th percentile 0.0 s, maximum 0 s.

## Vaults

10 vault wallets listed, 8 seen in the tape, 2 354 rows (0.19 % of all rows).

| Token | Vault | Maker rows | Taker rows | RFQ share | Notional (million USD) |
|---|---|---|---|---|---|
| bweETH | weETH Basis Trade | 0 | 0 | n/a | 0.0 |
| weETHC | weETH Covered Call | 142 | 280 | 0 % | 364.7 |
| weETHCS | weETH Covered Call Spread | 0 | 212 | 100 % | 7.8 |
| weETHBULL | weETHPrincipal Protected Bull Call Spread | 0 | 16 | 100 % | 0.0 |
| rswETHC | rswETH Covered Call | 125 | 250 | 0 % | 219.3 |
| rsETHC | rsETH Covered Call | 93 | 150 | 0 % | 98.3 |
| sUSDeBULL | sUSDePrincipal Protected Bull Call Spread | 0 | 720 | 100 % | 37.2 |
| bLBTC | LBTC Basis Trade | 0 | 0 | n/a | 0.0 |
| LBTCCS | LBTC Covered Call Spread | 0 | 80 | 100 % | 29.6 |
| LBTCPS | LBTC Covered Put Spread | 0 | 286 | 100 % | 48.7 |

TVL according to `get_vault_statistics` (20260917): 1.60 million USD in total.

## Reference data

Fetched 2026-09-17 20:05 UTC.

- Settlement prices per underlying: ADA 24, BTC 944, ETH 949, HYPE 282, SOL 119, XAUT 9, XRP 11, ZEC 13.
- Liquidations: 27 694 auctions, 15 733 bids (taken over from the existing files); remaining gaps: 0. The bids are incomplete depending on the page size (2025-10-10: 242 auctions, 34 bids at page size 100, 4 at size 5); complete bids only from the chain events.
  Period of the auctions 2024-01-02 09:31 UTC to 2026-09-16 07:58 UTC. Of 27 694 auctions, not a single option fill carries the transaction (0 matches): liquidations transfer positions outside the trade tape. The class "liquidation" therefore stays empty.
- Maker programmes: 81 epoch programmes, 3390 score rows for option programmes, 38 wallets with a score > 0.
- Instrument fees: 4734 live options; funding history 2183 hourly values (rolling 30 days, extended as it goes).

## SVI history (vol feeds)

| Underlying | Events | first block | last block | first curve | last curve | Expiries | Median push minus signature (s) | Gap between pushes per expiry, median / 90th percentile (s) |
|---|---|---|---|---|---|---|---|---|
| BTC | 17 260 459 | 1 028 885 | 44 812 381 | 2023-12-08 23:49 UTC | 2026-09-17 11:58 UTC | 968 | 27 | 60 / 62 |
| ETH | 17 269 761 | 905 406 | 44 812 371 | 2023-12-06 03:13 UTC | 2026-09-17 11:58 UTC | 967 | 23 | 60 / 62 |
| HYPE | 5 270 725 | 30 639 108 | 44 812 377 | 2025-10-24 09:56 UTC | 2026-09-17 11:58 UTC | 325 | 27 | 60 / 62 |

Events per month:

| Month | BTC | ETH | HYPE |
|---|---|---|---|
| 2023-12 | 2 385 | 1 622 | 0 |
| 2024-01 | 14 850 | 14 873 | 0 |
| 2024-02 | 33 462 | 33 500 | 0 |
| 2024-03 | 61 767 | 61 825 | 0 |
| 2024-04 | 185 746 | 186 269 | 0 |
| 2024-05 | 484 170 | 484 923 | 0 |
| 2024-06 | 464 703 | 466 755 | 0 |
| 2024-07 | 492 600 | 492 260 | 0 |
| 2024-08 | 566 473 | 564 281 | 0 |
| 2024-09 | 534 555 | 533 927 | 0 |
| 2024-10 | 724 010 | 723 904 | 0 |
| 2024-11 | 476 861 | 476 901 | 0 |
| 2024-12 | 580 913 | 580 607 | 0 |
| 2025-01 | 570 304 | 567 469 | 0 |
| 2025-02 | 513 452 | 512 982 | 0 |
| 2025-03 | 521 690 | 521 779 | 0 |
| 2025-04 | 548 834 | 548 887 | 0 |
| 2025-05 | 569 429 | 569 555 | 0 |
| 2025-06 | 503 244 | 503 239 | 0 |
| 2025-07 | 552 953 | 552 975 | 0 |
| 2025-08 | 559 533 | 559 614 | 0 |
| 2025-09 | 527 627 | 529 694 | 0 |
| 2025-10 | 659 841 | 659 560 | 10 912 |
| 2025-11 | 661 695 | 661 991 | 301 485 |
| 2025-12 | 632 905 | 633 808 | 427 680 |
| 2026-01 | 683 703 | 686 172 | 435 168 |
| 2026-02 | 619 919 | 621 508 | 456 593 |
| 2026-03 | 635 128 | 637 715 | 561 789 |
| 2026-04 | 665 649 | 667 949 | 543 427 |
| 2026-05 | 708 921 | 709 037 | 543 310 |
| 2026-06 | 667 209 | 667 916 | 551 072 |
| 2026-07 | 738 218 | 738 343 | 571 241 |
| 2026-08 | 731 716 | 731 837 | 567 424 |
| 2026-09 | 365 994 | 366 084 | 300 624 |

## Cross-check: mark at fill time from the on-chain SVI curve

For every core fill (settled, more than 30 min before expiry) the last SVI curve of the same expiry is looked up, by push time (`block_ts`, pre-registered) and by signature time (`feed_ts`). Vol from the curve (exactly as `SVI.sol`), price with Black-76. The comparison is with the `mark_price` of the taker row: as a vol distance (both prices inverted over the same forward `SVI_fwd`) and as a relative price error, once with forward `SVI_fwd`, once with the index of the fill.

| Underlying | Clock | Fills with curve | Median age (s) | Median abs. Δ IV (vp) | Share ≤ 0.5 vp | Share ≤ 2 vp |
|---|---|---|---|---|---|---|
| BTC | block_ts | 155 998 (100.0 %) | 31 | 0.459 | 52.4 % | 84.9 % |
| BTC | feed_ts | 156 000 (100.0 %) | 31 | 0.396 | 56.6 % | 87.2 % |
| ETH | block_ts | 405 107 (100.0 %) | 32 | 0.636 | 43.3 % | 79.1 % |
| ETH | feed_ts | 405 108 (100.0 %) | 31 | 0.565 | 46.5 % | 81.4 % |
| HYPE | block_ts | 43 993 (100.0 %) | 30 | 0.689 | 41.0 % | 77.3 % |
| HYPE | feed_ts | 43 993 (100.0 %) | 30 | 0.540 | 47.8 % | 81.9 % |

Median relative price error by time to expiry (push time):

| Underlying | Time to expiry | Fills | Forward = `SVI_fwd` | Forward = index of the fill |
|---|---|---|---|---|
| BTC | ≤ 3 d | 56 836 | 4.03 % | 2.08 % |
| BTC | 3-30 d | 69 576 | 1.27 % | 2.71 % |
| BTC | > 30 d | 29 586 | 1.13 % | 6.88 % |
| ETH | ≤ 3 d | 144 407 | 3.75 % | 1.43 % |
| ETH | 3-30 d | 183 305 | 1.26 % | 2.09 % |
| ETH | > 30 d | 77 395 | 1.10 % | 4.77 % |
| HYPE | ≤ 3 d | 8 067 | 3.17 % | 1.34 % |
| HYPE | 3-30 d | 24 194 | 1.23 % | 0.92 % |
| HYPE | > 30 d | 11 732 | 0.70 % | 0.93 % |

Median relative price error per quarter (forward = `SVI_fwd`, push time):

| Quarter | BTC | ETH | HYPE |
|---|---|---|---|
| 2023Q4 | 1.61 % | 20.70 % | n/a |
| 2024Q1 | 2.63 % | 2.87 % | n/a |
| 2024Q2 | 1.31 % | 1.40 % | n/a |
| 2024Q3 | 1.18 % | 1.12 % | n/a |
| 2024Q4 | 1.73 % | 1.93 % | n/a |
| 2025Q1 | 1.91 % | 1.95 % | n/a |
| 2025Q2 | 1.53 % | 1.65 % | n/a |
| 2025Q3 | 1.53 % | 1.64 % | n/a |
| 2025Q4 | 1.57 % | 1.53 % | 1.95 % |
| 2026Q1 | 1.80 % | 1.58 % | 1.07 % |
| 2026Q2 | 1.93 % | 1.63 % | 1.25 % |
| 2026Q3 | 2.03 % | 1.72 % | 1.24 % |

Reading: the tape mark uses a current forward (at short maturities the index is closer), the on-chain curve uses its own forward, which can be up to minutes old; on top of that comes the lag of the curve itself. Path (b) is therefore a delayed mark with a fixed forward. The delta-neutral unit and the vol unit are less affected by this than the USDC markout at short horizons.

## Disk usage

```
386M	data/p1/derived
1.8G	data/p1/raw
8.8M	data/p1/ref
 74M	data/p1/tape
1.4G	data/p1/volfeed
```

## Vol feed check

See `docs/paper1/feed_check.md`.
