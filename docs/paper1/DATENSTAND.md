# Datenstand Paper 1 (Pilot)

Erzeugt 2026-09-17 20:11 UTC mit `scripts/p1_datenstand.py`. Enthält nur Zählungen und Prüfungen, keine Markouts (Präregistrierung). Pilot-Stichtag 2026-09-17 12:00 UTC; der finale Stichtag ist 2026-09-30 08:00 UTC.

## Options-Tape

Zeitraum 2023-12-01 00:00 UTC bis 2026-09-17 12:00 UTC (beide inklusiv), fertig 2026-09-17 14:11 UTC. 1 229 160 Zeilen in 2 010 Einzelseiten-Fenstern; Tage mit abweichender Nachzählung: 0. Die API meldet für den Gesamtzeitraum 1 229 162 Zeilen; diese Zahl ist über lange Bereiche nicht additiv und dient nur zur Information.

| Underlying | Zeilen | SHA-256 (Anfang) |
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

## Fills und Gegenparteiklassen (ohne Markouts)

1 229 160 Zeilen ergeben 614 576 Fills. Zeilen ohne Partner: 8 (8 trade_ids); Paare mit abweichendem Preis, abweichender Menge oder gleicher Richtung: 0; nicht settled: 0. Liquidations-Transaktionen im Abgleich: 43414.

Zeilen ohne Partner: BTC-20250826-115000-C taker 2025-08-25 11:56 UTC; BTC-20250826-115000-C taker 2025-08-25 11:56 UTC; BTC-20250826-115000-C taker 2025-08-25 11:57 UTC; BTC-20250826-115000-C taker 2025-08-25 11:57 UTC; BTC-20250826-115000-C taker 2025-08-25 12:04 UTC; BTC-20250826-115000-C taker 2025-08-25 12:04 UTC; BTC-20250826-115000-C taker 2025-08-25 12:04 UTC; BTC-20250829-116000-P taker 2025-08-25 12:20 UTC.

| Taker-Klasse | BTC Fills | BTC Notional (Mio USD) | ETH Fills | ETH Notional (Mio USD) | HYPE Fills | HYPE Notional (Mio USD) |
|---|---|---|---|---|---|---|
| liquidation | 0 | 0 | 0 | 0 | 0 | 0 |
| vault | 366 | 78 | 1 628 | 401 | 0 | 0 |
| rfq | 31 568 | 6 509 | 67 367 | 2 930 | 22 262 | 1 694 |
| dominant_maker | 13 990 | 221 | 42 067 | 270 | 382 | 11 |
| mm_programme | 15 506 | 986 | 25 328 | 654 | 2 143 | 23 |
| large | 14 620 | 1 203 | 33 946 | 1 645 | 3 748 | 66 |
| other | 80 214 | 2 085 | 235 483 | 2 952 | 15 593 | 148 |

Flags (Kern): RFQ 122 511, Vault als Taker 1 994, Vault als Maker 360, Liquidation 0, Taker im MM-Programm 96 009.
Die Klasse MM-Programm ist erst ab 2024-11-20 00:00 UTC vergebbar; davor liegen 112 980 Kern-Fills.
Zeitabstand Taker- minus Maker-Zeile, RFQ: Median 3,1 s, 99. Perzentil 75,2 s, Maximum 1 689 s.
Zeitabstand Taker- minus Maker-Zeile, Buch: Median 0,0 s, 99. Perzentil 0,0 s, Maximum 0 s.

## Vaults

10 Vault-Wallets gelistet, 8 im Tape gesehen, 2 354 Zeilen (0,19 % aller Zeilen).

| Token | Vault | Maker-Zeilen | Taker-Zeilen | RFQ-Anteil | Notional (Mio USD) |
|---|---|---|---|---|---|
| bweETH | weETH Basis Trade | 0 | 0 | – | 0,0 |
| weETHC | weETH Covered Call | 142 | 280 | 0 % | 364,7 |
| weETHCS | weETH Covered Call Spread | 0 | 212 | 100 % | 7,8 |
| weETHBULL | weETHPrincipal Protected Bull Call Spread | 0 | 16 | 100 % | 0,0 |
| rswETHC | rswETH Covered Call | 125 | 250 | 0 % | 219,3 |
| rsETHC | rsETH Covered Call | 93 | 150 | 0 % | 98,3 |
| sUSDeBULL | sUSDePrincipal Protected Bull Call Spread | 0 | 720 | 100 % | 37,2 |
| bLBTC | LBTC Basis Trade | 0 | 0 | – | 0,0 |
| LBTCCS | LBTC Covered Call Spread | 0 | 80 | 100 % | 29,6 |
| LBTCPS | LBTC Covered Put Spread | 0 | 286 | 100 % | 48,7 |

TVL laut `get_vault_statistics` (20260917): zusammen 1,60 Mio USD.

## Referenzdaten

Abruf 2026-09-17 20:05 UTC.

- Settlement-Preise je Underlying: ADA 24, BTC 944, ETH 949, HYPE 282, SOL 119, XAUT 9, XRP 11, ZEC 13.
- Liquidationen: 27 694 Auktionen, 15 733 Gebote (aus den vorhandenen Dateien übernommen); verbleibende Lücken: 0. Die Gebote sind seitengrössenabhängig unvollständig (10.10.2025: 242 Auktionen, 34 Gebote bei Seitengrösse 100, 4 bei Grösse 5); vollständige Gebote nur aus den Chain-Events.
  Zeitraum der Auktionen 2024-01-02 09:31 UTC bis 2026-09-16 07:58 UTC. Von 27 694 Auktionen trägt kein einziger Options-Fill die Transaktion (0 Treffer): Liquidationen übertragen Positionen ausserhalb des Trade-Tapes. Die Klasse „liquidation“ bleibt daher leer.
- Maker-Programme: 81 Epochen-Programme, 3390 Score-Zeilen für Options-Programme, 38 Wallets mit Score > 0.
- Instrument-Gebühren: 4734 lebende Optionen; Funding-Historie 2183 Stundenwerte (rollierend 30 Tage, wird fortgeschrieben).

## SVI-Historie (Vol-Feeds)

| Underlying | Events | erster Block | letzter Block | erste Kurve | letzte Kurve | Verfälle | Median Push minus Signatur (s) | Abstand zwischen Pushes je Verfall, Median / 90. Perzentil (s) |
|---|---|---|---|---|---|---|---|---|
| BTC | 17 260 459 | 1 028 885 | 44 812 381 | 2023-12-08 23:49 UTC | 2026-09-17 11:58 UTC | 968 | 27 | 60 / 62 |
| ETH | 17 269 761 | 905 406 | 44 812 371 | 2023-12-06 03:13 UTC | 2026-09-17 11:58 UTC | 967 | 23 | 60 / 62 |
| HYPE | 5 270 725 | 30 639 108 | 44 812 377 | 2025-10-24 09:56 UTC | 2026-09-17 11:58 UTC | 325 | 27 | 60 / 62 |

Events je Monat:

| Monat | BTC | ETH | HYPE |
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

## Gegenprobe: Mark zum Fill-Zeitpunkt aus der onchain SVI-Kurve

Für jeden Kern-Fill (settled, mehr als 30 min vor Verfall) wird die letzte SVI-Kurve desselben Verfalls gesucht, nach Push-Zeit (`block_ts`, präregistriert) und nach Signaturzeit (`feed_ts`). Vol aus der Kurve (exakt wie `SVI.sol`), Preis mit Black-76. Verglichen wird mit dem `mark_price` der Taker-Zeile: als Vol-Abstand (beide Preise über denselben Forward `SVI_fwd` invertiert) und als relativer Preisfehler, einmal mit Forward `SVI_fwd`, einmal mit dem Index des Fills.

| Underlying | Uhr | Fills mit Kurve | Median Alter (s) | Median abs. Δ IV (vp) | Anteil ≤ 0,5 vp | Anteil ≤ 2 vp |
|---|---|---|---|---|---|---|
| BTC | block_ts | 155 998 (100,0 %) | 31 | 0,459 | 52,4 % | 84,9 % |
| BTC | feed_ts | 156 000 (100,0 %) | 31 | 0,396 | 56,6 % | 87,2 % |
| ETH | block_ts | 405 107 (100,0 %) | 32 | 0,636 | 43,3 % | 79,1 % |
| ETH | feed_ts | 405 108 (100,0 %) | 31 | 0,565 | 46,5 % | 81,4 % |
| HYPE | block_ts | 43 993 (100,0 %) | 30 | 0,689 | 41,0 % | 77,3 % |
| HYPE | feed_ts | 43 993 (100,0 %) | 30 | 0,540 | 47,8 % | 81,9 % |

Median relativer Preisfehler nach Restlaufzeit (Push-Zeit):

| Underlying | Restlaufzeit | Fills | Forward = `SVI_fwd` | Forward = Index des Fills |
|---|---|---|---|---|
| BTC | ≤ 3 d | 56 836 | 4,03 % | 2,08 % |
| BTC | 3–30 d | 69 576 | 1,27 % | 2,71 % |
| BTC | > 30 d | 29 586 | 1,13 % | 6,88 % |
| ETH | ≤ 3 d | 144 407 | 3,75 % | 1,43 % |
| ETH | 3–30 d | 183 305 | 1,26 % | 2,09 % |
| ETH | > 30 d | 77 395 | 1,10 % | 4,77 % |
| HYPE | ≤ 3 d | 8 067 | 3,17 % | 1,34 % |
| HYPE | 3–30 d | 24 194 | 1,23 % | 0,92 % |
| HYPE | > 30 d | 11 732 | 0,70 % | 0,93 % |

Median relativer Preisfehler je Quartal (Forward = `SVI_fwd`, Push-Zeit):

| Quartal | BTC | ETH | HYPE |
|---|---|---|---|
| 2023Q4 | 1,61 % | 20,70 % | – |
| 2024Q1 | 2,63 % | 2,87 % | – |
| 2024Q2 | 1,31 % | 1,40 % | – |
| 2024Q3 | 1,18 % | 1,12 % | – |
| 2024Q4 | 1,73 % | 1,93 % | – |
| 2025Q1 | 1,91 % | 1,95 % | – |
| 2025Q2 | 1,53 % | 1,65 % | – |
| 2025Q3 | 1,53 % | 1,64 % | – |
| 2025Q4 | 1,57 % | 1,53 % | 1,95 % |
| 2026Q1 | 1,80 % | 1,58 % | 1,07 % |
| 2026Q2 | 1,93 % | 1,63 % | 1,25 % |
| 2026Q3 | 2,03 % | 1,72 % | 1,24 % |

Lesart: Der Tape-Mark rechnet mit einem aktuellen Forward (bei kurzen Laufzeiten liegt der Index näher), die onchain Kurve mit ihrem eigenen, bis zu Minuten alten Forward; dazu kommt der Verzug der Kurve selbst. Pfad (b) ist deshalb ein verzögerter, forward-fixierter Mark. Die delta-neutrale und die Vol-Einheit sind davon weniger betroffen als der USDC-Markout auf kurzen Horizonten.

## Plattenbedarf

```
386M	data/p1/derived
1,8G	data/p1/raw
8,8M	data/p1/ref
 74M	data/p1/tape
1,4G	data/p1/volfeed
```

## Vol-Feed-Prüfung

Siehe `docs/paper1/feed_check.md`.
