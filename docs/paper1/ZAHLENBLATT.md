# Zahlenblatt Paper 1

Erzeugt 2026-09-25 07:04 UTC aus `results/p1` mit `scripts/p1_zahlenblatt.py`. Pilotdaten bis 17.09.2026 12:00 UTC. Primärer Horizont 30m, Mark-Pfad (b) nach Push-Zeit, Cluster Taker-Wallet, B = 9999, Seed 20260917, Perp-Halbspread 1,0 bp. 603 940 Fills; ohne Fill-IV (nur Vol-Einheit betroffen): 10 745. Gebühr und Rebate gehen je Kontrakt ein (Summe des Fills durch seine Menge, Nachtrag 3 vom 25.09.2026).

## H1 Konzentration der Toxizität

- Top-10-Anteil am aggregierten Maker-Verlust: **90,5 %** (90-%-Intervall 69,8 bis 94,3 %), Verlustsumme -3 240 781 USDC über 11 573 Wallets.
- Grösse über dem 90. Perzentil: Koeffizient -0,765 USDC (t -0,74, p 0,4761).
- Sweep: Koeffizient -0,357 USDC (t -0,10, p 0,9442).
- Urteil: **abgelehnt**.

## H2 Vault-Flow uninformiert

- 30-min-Markout der Vault-Fills: 4,220 USDC (95-%-Intervall 1,644 bis 8,550, p 0,0092, 1 994 Fills, 8 Wallets).
- VRP-bereinigter Settlement-Markout: -6,366 USDC (95-%-Intervall -17,789 bis 5,137).
- Urteil: nicht abgelehnt.

## H3 HYPE vor und nach der Deribit-Listung

- Ereignis 23.06.2026 09:00 UTC, Fenster ±90 Tage, Zielgrösse Vol-Markout.
- DiD-Koeffizient -1,046 Vol-Punkte (t -1,23, p 0,2419, 147 240 Fills, 3879 Wallets).
- Placebo-Daten: 100, davon extremer 46,0 %.
- Urteil: **abgelehnt**.

## H4 Netto-Edge je Zelle

- Besetzte Zellen (≥ 200 Fills): 97; davon mit positivem 90-%-Intervall: **76,3 %**.
- Zellen positiv / negativ / offen: 74 / 0 / 23; mit positivem Mittel und Wild-p ≤ 0,10 (Robustheit, nicht die Regel): 52 (53,6 %).
- ATM-Kurzläufer BTC 40–60 Δ, ≤ 2 d: 24,193 USDC (90-%-Intervall 6,429 bis 46,367, Wild-p 0,104, 8 902 Fills)
- ATM-Kurzläufer ETH 40–60 Δ, ≤ 2 d: 1,053 USDC (90-%-Intervall 0,199 bis 2,098, Wild-p 0,153, 23 718 Fills)
- Urteil: **abgelehnt**.

### Sensitivität des Perp-Halbspreads

| Halbspread (bp) | Zellen | Anteil positiv |
|---|---|---|
| 0,0 | 97 | 78,4 % |
| 1,0 | 97 | 76,3 % |
| 3,0 | 97 | 58,8 % |

## Gegenparteiklassen (30 min, Pfad b)

Alle Beträge in USDC je Kontrakt; Gebühr und Rebate je Kontrakt. Das Intervall gilt dem Markout. Der Netto-Edge der Klasse vault beruht auf 8 Taker-Wallets und wird ohne Intervall berichtet.

| Klasse | Fills | Halbspread | Adverse Selection | Markout USDC | 95-%-Intervall | Gebühr | Rebate | Hedge | Netto-Edge | Anteil negativ |
|---|---|---|---|---|---|---|---|---|---|---|
| dominant_maker | 56 274 | -16,60 | -8,81 | -25,41 | -28,35 bis -19,42 | 2,75 | 0,11 | 3,93 | -31,98 | 67,6 % |
| mm_programme | 42 976 | -5,17 | -15,50 | -20,67 | -24,41 bis -2,16 | 1,82 | 0,66 | 4,94 | -26,76 | 66,1 % |
| large | 52 200 | 6,40 | -2,51 | 3,89 | -8,73 bis 18,70 | 1,35 | 1,02 | 2,76 | 0,79 | 35,7 % |
| vault | 1 994 | 4,32 | -0,10 | 4,22 | 1,64 bis 8,55 | 1,13 | 0,02 | 1,02 | 2,09 | 31,6 % |
| rfq | 121 064 | 15,38 | -0,17 | 15,21 | 12,19 bis 19,05 | 0,30 | 0,00 | 3,11 | 11,80 | 34,5 % |
| other | 329 432 | 25,60 | -0,87 | 24,73 | 22,05 bis 28,02 | 0,96 | 1,14 | 2,87 | 22,04 | 27,0 % |

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
| ETH | 90-100 | >90d | 325 | -30,283 | -77,270 bis 9,844 |
| HYPE | 75-90 | <=2d | 472 | -0,034 | -0,105 bis 0,093 |
| HYPE | 90-100 | <=2d | 277 | -0,020 | -0,202 bis 0,196 |
| HYPE | 10-25 | <=2d | 1 369 | -0,002 | -0,029 bis 0,023 |
| HYPE | 60-75 | <=2d | 526 | 0,015 | -0,078 bis 0,110 |
| BTC | 90-100 | <=2d | 1 580 | 148,629 | 40,773 bis 297,053 |
| BTC | 40-60 | >90d | 1 795 | 199,363 | 108,935 bis 324,636 |
| BTC | 10-25 | >90d | 1 529 | 204,207 | 117,522 bis 313,830 |
| BTC | 60-75 | >90d | 464 | 300,514 | 75,246 bis 583,853 |
| BTC | 25-40 | >90d | 1 607 | 305,765 | 123,954 bis 514,743 |

## Aus der Nachrechnung der Gebühreneinheit (Revision 25.09.2026)

Diese Zahlen stehen nicht in `results/p1`, sondern in `results/p1_befund/gebuehreneinheit.csv` (`scripts/p1_befund_gebuehreneinheit.py`); Quelle je Zeile.

Zerlegung je Kontrakt mit B = 9 999 (Abschnitt `decomposition_b9999`, Variante `per_contract`; Text Abschnitt 3):

| Grösse | Mittel USDC | 95-%-Intervall |
|---|---|---|
| half spread | 15,701 | 9,906 bis 22,138 |
| adverse selection | -2,651 | -4,693 bis -0,715 |
| markout | 13,051 | 5,592 bis 21,247 |
| maker fee | -1,091 | -1,346 bis -0,806 |
| maker rebate | 0,769 | 0,648 bis 0,913 |
| hedge cost | -3,149 | -3,469 bis -2,813 |
| net edge | 9,579 | 1,562 bis 18,309 |

- RFQ-Paket (Abschnitt `rfq_package`, Nachtrag 3 Nr. 3): Gebühr über das Paket verteilt, Netto-Edge 9,578 USDC je Kontrakt; Zellen positiv / negativ bei 1 bp 74 / 0.

Robustheit von H4 nach Wild-p (positives Mittel und p ≤ 0,10, nicht die Regel; aus den Zelltabellen unter `data/p1/befund_gebuehreneinheit`, Text Abschnitt 5.5):

| Halbspread (bp) | Zellen | positiv (Regel) | positiv nach Wild-p |
|---|---|---|---|
| 0 | 97 | 76 | 59 (60,8 %) |
| 1 | 97 | 74 | 52 (53,6 %) |
| 3 | 97 | 57 | 44 (45,4 %) |

## Einschränkungen dieser Zahlen

- Pilotstand: Stichprobe bis 17.09.2026 12:00 UTC. Auf diesem Stand beruhen die Erstfassung des Manuskripts (19.09.2026) und die Revision (25.09.2026); der Enddatenlauf mit dem registrierten Stichtag 30.09.2026 08:00 UTC steht aus.
- Die Erstfassung zog Gebühr und Rebate als Summen des Fills vom Markout je Kontrakt ab (Nachtrag 3, `docs/paper1/BEFUND_2026-09-25_GEBUEHRENEINHEIT.md`); alle Zahlen hier sind korrigiert.
- H2 beruht auf 8 Vault-Wallets; bei so wenigen Clustern ist der Wild-Cluster-Bootstrap unzuverlässig, das Ergebnis ist ein Hinweis, kein Beweis.
- Pfad (b) ist ein um Minuten verzögerter Mark (onchain-Push je Verfall im Median alle 60 s, Forward der Kurve statt Live-Forward). Die Horizonte 1 min und 5 min sind davon am stärksten betroffen; Pfad (a) steht in der Horizont-Tabelle daneben.
- Die Vol-Einheit fehlt für 10 745 Fills ohne Fill-IV (Preis ausserhalb der Arbitragegrenzen).
- Die Klasse „liquidation“ ist leer: Liquidationen laufen ausserhalb des Trade-Tapes.
