# Zahlenblatt Paper 1

Erzeugt 2026-09-17 22:06 UTC aus `results/p1` mit `scripts/p1_zahlenblatt.py`. Pilotdaten bis 17.09.2026 12:00 UTC. Primärer Horizont 30m, Mark-Pfad (b) nach Push-Zeit, Cluster Taker-Wallet, B = 9999, Seed 20260917, Perp-Halbspread 1,0 bp. 603 940 Fills; ohne Fill-IV (nur Vol-Einheit betroffen): 10 745.

## H1 Konzentration der Toxizität

- Top-10-Anteil am aggregierten Maker-Verlust: **90,5 %** (90-%-Intervall 69,8 bis 94,3 %), Verlustsumme -3 240 781 USDC über 11 573 Wallets.
- Grösse über dem 90. Perzentil: Koeffizient -0,765 USDC (t -0,74, p 0,4761).
- Sweep: Koeffizient -0,357 USDC (t -0,10, p 0,9442).
- Urteil: **abgelehnt**.

## H2 Vault-Flow uninformiert

- 30-min-Markout der Vault-Fills: 4,220 USDC (95-%-Intervall 1,644 bis 8,550, p 0,0075, 1 994 Fills, 8 Wallets).
- VRP-bereinigter Settlement-Markout: -6,366 USDC (95-%-Intervall -17,789 bis 5,137).
- Urteil: nicht abgelehnt.

## H3 HYPE vor und nach der Deribit-Listung

- Ereignis 23.06.2026 09:00 UTC, Fenster ±90 Tage, Zielgrösse Vol-Markout.
- DiD-Koeffizient -1,046 Vol-Punkte (t -1,23, p 0,2419, 147 240 Fills, 3879 Wallets).
- Placebo-Daten: 100, davon extremer 46,0 %.
- Urteil: **abgelehnt**.

## H4 Netto-Edge je Zelle

- Besetzte Zellen (≥ 200 Fills): 97; davon mit positivem 90-%-Intervall: **49,5 %**.
- ATM-Kurzläufer BTC 40–60 Δ, ≤ 2 d: 23,955 USDC (90-%-Intervall 7,245 bis 44,828, 8 902 Fills)
- ATM-Kurzläufer ETH 40–60 Δ, ≤ 2 d: 0,361 USDC (90-%-Intervall -0,411 bis 1,338, 23 718 Fills)
- Urteil: **abgelehnt**.

### Sensitivität des Perp-Halbspreads

| Halbspread (bp) | Zellen | Anteil positiv |
|---|---|---|
| 0,0 | 97 | 55,7 % |
| 1,0 | 97 | 50,5 % |
| 3,0 | 97 | 38,1 % |

## Gegenparteiklassen (30 min, Pfad b)

| Klasse | Fills | Markout USDC | 95-%-Intervall | delta-neutral | Vol-Punkte | Netto-Edge |
|---|---|---|---|---|---|---|
| dominant_maker | 56 274 | -25,414 | -28,118 bis -19,874 | -15,985 | -1,273 | -30,491 |
| mm_programme | 42 976 | -20,670 | -24,373 bis -1,903 | -6,736 | -0,832 | -25,150 |
| large | 52 200 | 3,891 | -8,898 bis 19,066 | 6,243 | 1,811 | -1,631 |
| vault | 1 994 | 4,220 | 1,549 bis 8,530 | 4,448 | 1,844 | -28,576 |
| rfq | 121 064 | 15,209 | 12,178 bis 18,955 | 15,189 | 2,971 | 11,187 |
| other | 329 432 | 24,732 | 21,955 bis 28,096 | 25,342 | 3,615 | 21,186 |

## Horizonte (Pfad b, Mittelwerte)

| Horizont | Fills | USDC | delta-neutral | Vol-Punkte | Pfad (a) USDC |
|---|---|---|---|---|---|
| 1m | 603 940 | 15,217 | 15,712 | 2,588 | 12,959 |
| 5m | 603 940 | 13,251 | 15,644 | 2,576 | 12,806 |
| 30m | 603 940 | 13,051 | 15,454 | 2,553 | 12,543 |
| 4h | 599 439 | 13,080 | 15,389 | 2,470 | 12,594 |
| 24h | 511 237 | 12,970 | 15,955 | 1,891 | 13,198 |

## Zellen mit dem grössten und kleinsten Netto-Edge

| Underlying | Delta | Tenor | Fills | Netto-Edge | 90-%-Intervall |
|---|---|---|---|---|---|
| ETH | 90-100 | >90d | 325 | -30,229 | -77,441 bis 9,986 |
| ETH | 00-10 | 2-7d | 21 704 | -4,230 | -7,541 bis -1,633 |
| ETH | 10-25 | 2-7d | 23 054 | -3,046 | -4,798 bis -1,631 |
| HYPE | 25-40 | 30-90d | 2 051 | -2,187 | -6,451 bis 0,125 |
| HYPE | 40-60 | 30-90d | 2 170 | -2,067 | -6,367 bis 0,219 |
| BTC | 90-100 | <=2d | 1 580 | 150,594 | 43,958 bis 297,385 |
| BTC | 40-60 | >90d | 1 795 | 198,146 | 108,601 bis 321,985 |
| BTC | 10-25 | >90d | 1 529 | 204,400 | 117,792 bis 314,044 |
| BTC | 60-75 | >90d | 464 | 302,446 | 77,412 bis 585,305 |
| BTC | 25-40 | >90d | 1 607 | 305,652 | 124,503 bis 514,024 |

## Einschränkungen dieser Zahlen

- Pilotstand: Stichprobe bis 17.09.2026 12:00 UTC. Die Zahlen des Manuskripts entstehen erst mit dem Stichtag 30.09.2026 08:00 UTC.
- H2 beruht auf 8 Vault-Wallets; bei so wenigen Clustern ist der Wild-Cluster-Bootstrap unzuverlässig, das Ergebnis ist ein Hinweis, kein Beweis.
- Pfad (b) ist ein um Minuten verzögerter Mark (onchain-Push je Verfall im Median alle 60 s, Forward der Kurve statt Live-Forward). Die Horizonte 1 min und 5 min sind davon am stärksten betroffen; Pfad (a) steht in der Horizont-Tabelle daneben.
- Die Vol-Einheit fehlt für 10 745 Fills ohne Fill-IV (Preis ausserhalb der Arbitragegrenzen).
- Die Klasse „liquidation“ ist leer: Liquidationen laufen ausserhalb des Trade-Tapes.
