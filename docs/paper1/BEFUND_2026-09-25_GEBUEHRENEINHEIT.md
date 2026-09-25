# Befund 25.09.2026: Einheit von Gebühr und Rabatt im Netto-Edge von Paper 1

Stand: Korrektur am 25.09.2026 umgesetzt (Nachtrag 3 der Präregistrierung, `REVISION_2026-09-25.md`). Bei Abfassung dieses Befunds war an Paper 1 noch nichts geändert. Pilotschnitt 17.09.2026 12:00 UTC, 603 940 Fills, Horizont 30 min.

Rechnung: `scripts/p1_befund_gebuehreneinheit.py` (Kopie der Logik von Paper 1 mit wählbarer Gebühreneinheit),
Aufruf `python3 scripts/p2_heavy.py --wait-max 500 -- python3 scripts/p1_befund_gebuehreneinheit.py`, rund zwei
Minuten; Zwischenstände unter `data/p1/befund_gebuehreneinheit/` (nicht im Git, Neustart überspringt fertige
Schritte). Tests: `tests/test_p1_befund_gebuehreneinheit.py` (15, offline und synthetisch, Teil der Suite).
Zahlen: `results/p1_befund/gebuehreneinheit.csv` (lang, Spalten `section, item, variant, value, lo, hi, …,
p1_reference, matches_p1`), Urteile `results/p1_befund/gebuehreneinheit.json`, korrigierte Zelltabelle
`results/p1_befund/h4_cells_per_contract.csv`.

**Stand der Dateien.** Die erste Fassung lief aus einer Kopie unter `data/p2/p1befund/`, die das `.gitignore`
ausschliesst. Nach dem Audit von Paper 2 (`docs/paper2/AUDIT.md`, A25 bis A27 und A65 bis A68) liegt das Skript
versioniert unter `scripts/`. Ein Neulauf von null reproduziert die committeten Zahlen bitgleich: die ersten 611
Zeilen der CSV (Abschnitte `decomposition` bis `f1_premium_share`), `h4_cells_per_contract.csv`, die Urteile
(`h4`) und alle Reproduktionsprüfungen der JSON sowie alle 25 Zwischendateien. Angehängt sind die Abschnitte
`f5_bp_summary` (A65), `class_clusters` (A66), `decomposition_b9999` und `classes_b9999` (A68), `rfq_booking`
und `rfq_package` (A67). In der JSON ändern sich nur `meta.script` und `meta.note`; neu sind `rfq_booking` und
`h4_rfq_package`.

## Was

`derive_surface/inference_p1.py`, `analysis_frame`, Zeile 232:

    net_edge = mo_usd − fee_maker + rebate_maker − hedge

`mo_usd` und `hedge` gelten je Kontrakt, `fee_maker` und `rebate_maker` (`trade_fee`, `expected_rebate` der
Maker-Zeile) sind Summen je Fill. Richtig ist

    NE = mo_usd − (fee_maker − rebate_maker) / amount − hedge,   Edge des Fills = NE · amount.

Beleg: Die Maker-Gebühr wächst mit der Menge, die Gebühr je Kontrakt nicht. BTC, Median der positiven
Gebühren: 0,11 USDC bei ≤ 0,02 Kontrakten, 19,4 bei > 0,5; je Kontrakt 11,1 bzw. 15,6. HYPE: 0,07 bis 9,1
je Fill, 0,006 bis 0,007 je Kontrakt. Der Rabatt verhält sich gleich. Das Audit bestätigt das am Tape: Die
Maker-Gebühr ist amount · min(Rate · Index, 12,5 % · Mark), die Steigungen von log(Gebühr) und log(Rabatt) auf
log(Menge) liegen nahe 1. Die Menge streut über mehrere Grössenordnungen (Median BTC 0,1, ETH 1, HYPE 125
Kontrakte), deshalb ist der Fehler je Zelle sehr ungleich. Der Test von Paper 1
(`test_analysis_frame_decomposes_the_markout`) nutzt `amount = 1` und konnte ihn nicht finden.

**RFQ-Pakete (A67).** Die Aussage „Summe je Fill“ gilt streng für Orderbuch-Fills. Bei mehrbeinigen RFQ bucht
Derive die Maker-Gebühr des Pakets fast immer auf genau ein Bein: Von 39 366 Paketen mit mehr als einem Bein
(Paket = `rfq_id` und Maker-Wallet) tragen 4 996 eine Maker-Gebühr, bei 4 511 davon liegt sie auf genau einem
Bein, bei 95 auf allen; Rabatte gibt es bei RFQ nicht. Die Bein-Formel trifft im Orderbuch die grosse Mehrheit
der Fills (Audit 84,9 %; eine eigene Grobprüfung mit 3 bp vor und 1 bp ab Februar 2025 ergibt 83,4 %), bei RFQ
fast nie (6,7 % bzw. 0,3 %; die Quote hängt an der angenommenen Rate). `fee_maker / amount` legt die Gebühr des
Pakets also auf das Bein, auf dem sie gebucht ist. Numerisch ist das unerheblich. In der Sensitivität
`per_contract_package` trägt jedes Bein Σ Gebühr / Σ Menge seines Pakets: Mittlere Gebühr über die RFQ-Fills
0,3115 beinweise gegen 0,3177 je Paket, Gebühr im Gesamtmittel −1,0911 gegen −1,0924, Netto-Edge +9,5795 gegen
+9,5782; H4 bleibt bei 74 von 97 positiven Zellen und 0 negativen, kein Zell-Urteil ändert sich, das grösste
Zellmittel verschiebt sich um 0,13 USDC (BTC 75-90 Δ, 2-7 d). Der P1-Nachtrag sollte einen Satz dazu enthalten,
ebenso Nachtrag 2 von Paper 2 (`docs/paper2/PRAEREGISTRIERUNG.md` Z. 111 bis 118; nicht Teil dieses Befunds).

## Reproduktion vor der Korrektur

Die Variante `p1` trifft Paper 1 exakt (alle 67 Vergleiche in der JSON, `reproduced: true`):
`analysis_frame` bitgleich (hs, y_usd, as_usd, hedge, net_edge); alle 97 Zellen aus `results/p1/h4_cells.csv`
mit Mittel, lo, hi, p und Flags identisch (B = 9 999, Seed 20260917 wie registriert); `h4_sensitivity.csv` bei
0, 1 und 3 bp; alle Spalten von `class_means.csv`; T2 = 8,93245 (`ABBILDUNGEN.md`); die Zerlegung im Text
(+15,70, −2,65, −1,56, +0,59, −3,15, +8,93); F5-Textwerte (BTC 9,0 und 28,5 bp, Text „twenty-nine“); die
Quartile von F1c. Der Seed von Paper 1 ist Absicht: nur so sind die alten Intervalle nachprüfbar.

## Zahlen alt und neu

**Zerlegung je Kontrakt** (Mittel, 95-%-Cluster-Bootstrap über Taker-Wallets, **B = 9 999**, Seed 20260917,
also mit so vielen Ziehungen, wie Paper 1 für seine Intervalle angibt; explorativ; CSV `decomposition_b9999`)

| Komponente | alt (Paper 1) | neu (je Kontrakt) |
|---|---|---|
| Halbspread | +15,70 | +15,70 |
| Adverse Selektion | −2,65 | −2,65 |
| Gebühr | −1,56 (−1,96 bis −1,20) | −1,09 (−1,35 bis −0,81) |
| Rabatt | +0,59 (0,46 bis 0,74) | +0,77 (0,65 bis 0,91) |
| Hedge | −3,15 | −3,15 |
| **Netto-Edge** | **+8,93** (1,30 bis 17,32) | **+9,58** (1,56 bis 18,31) |
| Median Netto-Edge | 0,74 | 0,63 |
| mengengewichtet Σ NE·a / Σ a | −70,46 | +0,19 |
| Summe Σ NE·a über alle Fills, USDC | −2 813 Mio. | +7,48 Mio. |

Mit B = 999 wie die Fehlerbalken von T2 (CSV `decomposition`, Stand der ersten Fassung) lauten die Intervalle
für Gebühr, Rabatt und Netto-Edge alt −1,92 bis −1,18, 0,47 bis 0,73 und 1,25 bis 17,34, neu −1,33 bis −0,80,
0,64 bis 0,91 und 1,46 bis 18,43. Zitiert werden sollten im Text nur die Werte mit B = 9 999 (A68, siehe
Empfehlung 4).

Das Mittel je Fill verschiebt sich nur um +0,65. Jede mengengewichtete Aggregation der alten Form ist dagegen
unbrauchbar, weil die Gebührensumme noch einmal mit der Menge multipliziert wird. Paper 1 berichtet keine
solche Aggregation des Netto-Edge.

**Gegenparteiklassen.** Die Kopfzahlen +24,73 (gewöhnliche Taker) und −25,41 (dominante Maker) sind Markouts
und **ändern sich nicht**, ebenso Halbspread, adverse Selektion und Hedge je Klasse. Es ändern sich Gebühr,
Rabatt und Netto-Edge (Spalten im Zahlenblatt, im Manuskripttext nicht zitiert). G ist die Zahl der
Taker-Wallets hinter der Klasse, also der Cluster des Bootstraps, in Klammern der Anteil des grössten Wallets
an den Fills der Klasse (CSV `class_clusters`). Intervalle mit B = 9 999 (CSV `classes_b9999`; mit B = 999 in
`classes`).

| Klasse | G (grösstes Wallet) | Markout | NE alt | NE neu (95 %, B = 9 999) | Gebühr alt / neu | Rabatt alt / neu |
|---|---|---|---|---|---|---|
| dominant_maker | 17 (82 %) | −25,41 | −30,49 | −31,98 (−35,96 bis −26,95) | 1,23 / 2,75 | 0,08 / 0,11 |
| mm_programme | 33 (83 %) | −20,67 | −25,15 | −26,76 (−30,28 bis −3,58) | 1,13 / 1,82 | 1,59 / 0,66 |
| large | 104 (13 %) | +3,89 | −1,63 | +0,79 (−12,41 bis 15,90) | 4,55 / 1,35 | 1,78 / 1,02 |
| vault | **8** (36 %) | +4,22 | −28,58 | +2,09 (kein belastbares Intervall, G = 8) | 34,21 / 1,13 | 2,44 / 0,02 |
| rfq | 4 512 (3 %) | +15,21 | +11,19 | +11,80 (8,89 bis 15,50) | 0,91 / 0,30 | 0 / 0 |
| other | 10 749 (1 %) | +24,73 | +21,19 | +22,04 (19,43 bis 25,26) | 1,24 / 0,96 | 0,57 / 1,14 |

Der Vault-Netto-Edge wechselt das Vorzeichen, weil die alte Gebühr von 34,21 „je Kontrakt“ eine Summe über
grosse Fills war; je Kontrakt sind es 1,13. Das Vorzeichen folgt aus den Mitteln selbst: Markout +4,22 abzüglich
Gebühr 1,13 und Hedge 1,02, zuzüglich Rabatt 0,02, ergibt +2,09. Ein Intervall trägt diese Aussage nicht (A66):
Der Perzentil-Cluster-Bootstrap läuft über nur G = 8 Taker-Wallets, von denen eines 36 % und zwei zusammen
51 % der 1 994 Vault-Fills tragen, und ist bei so wenigen Clustern zu eng. Rechnerisch ergibt er 1,13 bis 3,49
(B = 9 999; mit B = 999 1,05 bis 3,49, im Audit mit anderem Seed 1,15 bis 3,60). Beim Neuschreiben das
Intervall weglassen oder ausdrücklich mit G = 8 kennzeichnen, wie das Zahlenblatt von Paper 1 es für H2 schon
tut. Abgeschwächt gilt das auch für dominant_maker und mm_programme, in denen je ein Wallet über 80 % der Fills
trägt.

**H4** (90-%-Cluster-Bootstrap, B = 9 999, Seed 20260917, Regel der Präregistrierung von Paper 1)

| | alt | neu |
|---|---|---|
| positive Zellen, 1 bp | 48 von 97 = **49,5 %** | 74 von 97 = **76,3 %** |
| signifikant negative Zellen | 3 (ETH, niedriges Delta) | 0 |
| positive Zellen je Basiswert BTC / ETH / HYPE | 23 / 13 / 12 | 23 / 26 / 25 |
| Zellen neu positiv / nicht mehr positiv | | 28 / 2 (BTC 60-75 Δ ≤ 2 d, HYPE 75-90 Δ 2-7 d) |
| Sensitivität 0 bp / 3 bp | 57,7 % / 38,1 % | 78,4 % / 58,8 % |
| BTC [40,60) ≤ 2 d | +23,95 (7,24 bis 44,83) | +24,19 (6,43 bis 46,37) |
| ETH [40,60) ≤ 2 d | +0,36 (−0,41 bis 1,34) | **+1,05 (0,20 bis 2,10)** |
| Urteil bei 1 bp | abgelehnt (nur ATM-Zweig) | abgelehnt (beide Zweige) |
| Urteil bei 0 / 1 / 3 bp | abgelehnt / abgelehnt / **nicht abgelehnt** | abgelehnt / abgelehnt / abgelehnt |

Die drei signifikant negativen ETH-Zellen werden signifikant positiv (ETH 00-10 Δ 2-7 d −4,23 wird +0,47,
ETH 00-10 Δ 7-30 d −0,91 wird +0,72, ETH 10-25 Δ 2-7 d −3,05 wird +0,52). Das Urteil bleibt „abgelehnt“, aber
aus einem anderen Grund: die Mehrheitsregel greift jetzt klar und über den ganzen Bereich der Hedge-Annahme.
Die Kernaussage des Manuskripts, der Befund liege so nah an der Schwelle, dass ein unbeobachteter
Hedge-Aufschlag zwischen 0 und 1 bp entscheide, trägt nicht mehr.

**F5-bp-Karte** (Median je Zelle, ≥ 200 Fills). Hier liegt neben der Gebühr ein **zweiter, grösserer
Einheitenfehler**: F5 (`figures_p1.py` Zeile 538) und die Social-Karte S5 (`figures_social.py` Zeile 206)
teilen den Netto-Edge **je Kontrakt** durch `notional = amount · index` **des ganzen Fills**. Das ist nur bei
einem Kontrakt ein bp-Wert. Einheitlich ist NE·a / (a·Index) = NE / Index, wie die Präregistrierung von Paper 2
den Edge in bp definiert.

| Variante (CSV-Schlüssel) | BTC [40,60) ≤ 2 d / 30-90 d | ETH dito | HYPE dito | Zellmedian BTC / ETH / HYPE | Spanne BTC | Spanne ETH | Spanne HYPE |
|---|---|---|---|---|---|---|---|
| alt, wie Paper 1 (`p1\|notional`) | 9,0 / 28,5 | 0,9 / 3,3 | 0,3 / 0,5 | 10,0 / 1,6 / 0,3 | 1,2 bis 78 | −21 bis 12 | 0,0 bis 0,6 |
| nur Gebühr korrigiert (`per_contract\|notional`) | 8,8 / 28,4 | 1,1 / 3,5 | 0,0 / 0,1 | 9,2 / 1,5 / 0,1 | 1,5 bis 78 | −19 bis 12 | 0,0 bis 0,4 |
| nur Nenner korrigiert (`p1\|index`) | 2,8 / 5,7 | 2,9 / 9,2 | 29,0 / 47,7 | 3,5 / 5,5 / 30,0 | 0,6 bis 16 | −81 bis 28 | −0,6 bis 86 |
| **beides korrigiert (`per_contract\|index`)** | **2,8 / 5,8** | **3,8 / 9,8** | **5,0 / 27,2** | **3,3 / 5,7 / 15,1** | 0,9 bis 16 | −83 bis 29 | −6,2 bis 69 |

Wie stark der Nenner allein verzerrt, zeigt der Vergleich von „alt“ mit „nur Nenner“ (gleiche Gebühr, A65):
BTC wird um das 3- bis 5-Fache aufgebläht (ATM ≤ 2 d 9,0 gegen 2,8, ATM 30-90 d 28,5 gegen 5,7, Zellmedian
10,0 gegen 3,5), ETH um rund das Dreifache gedrückt (0,9 gegen 2,9; 3,3 gegen 9,2), HYPE durch rund 100 geteilt
(0,3 gegen 29,0; 0,5 gegen 47,7). Die Faktoren sind nicht einfach 1 / Median-Menge, weil der Zellmedian über
Fills sehr unterschiedlicher Menge läuft.

Welcher der beiden Fehler wie viel ausmacht, hängt von der Reihenfolge der Korrekturen ab. Auf dem alten Nenner
verschiebt die Gebührenkorrektur die Karte nur um Zehntel-bp, weil der Nenner HYPE ohnehin gegen null drückt.
Auf dem richtigen Nenner **halbiert sie die HYPE-Karte** (Zellmedian 30,0 gegen 15,1 bp, Maximum 85,5 gegen
68,8, ATM ≤ 2 d 29,0 gegen 5,0): Die alte Form schreibt die Rabattsumme des ganzen Fills je Kontrakt gut, und
in HYPE-Zellen wie ATM ≤ 2 d übersteigt der Rabatt die Gebühr (0,25 gegen 0,03 USDC je Fill bei im Median 100
Kontrakten). BTC bleibt fast gleich, ETH steigt leicht. Die Umkehr der Ordnung zwischen den Basiswerten kommt
vom Nenner: Schon mit alter Gebühr liegt je Nominal HYPE vorn und BTC hinten (Zellmedian 3,5 / 5,5 / 30,0 bp),
korrigiert 3,3 / 5,7 / 15,1 bp. Alle Zellen in der CSV (`section = f5_bp_map`), Zellmediane in
`f5_bp_summary`, Spannen in `f5_bp_range`.

**Nebenbefund F1c und F2c.** Derselbe Einheitenmix: Markout je Kontrakt geteilt durch die Prämie des ganzen
Fills (`price · amount`, `figures_p1._premium`). Quartile alt −1,6 / +1,1 / +21,1 %, je Kontrakt (Markout /
Preis) −3,3 / +3,4 / +13,5 %. F2 Panel c (Median-Markout als Prämienanteil über die Horizonte) nutzt dieselbe
Division und ist ebenso betroffen; der Text von Paper 1 zitiert aus F2c keine Zahl. T2 Panel b (Gebühr des
Fills / Prämie des Fills, für Maker und Taker) ist konsistent und nicht betroffen.

## Betroffene Stellen

**Manuskript `paper/main.tex`**

- Z. 70 bis 72 (Abstract) und Z. 182 bis 190 (Text und Bild T2): Netto-Edge +8,93 wird +9,58, Gebühr −1,56
  wird −1,09, Rabatt +0,59 wird +0,77. Halbspread, adverse Selektion und Markout bleiben.
- Z. 306 bis 313 (H4): 48 positive, 3 negative, 46 offene Zellen werden 74, 0 und 23; 49,5 / 57,7 / 38,1 %
  werden 76,3 / 78,4 / 58,8 %; der Satz über die Hedge-Annahme zwischen 0 und 1 bp entfällt; ETH-ATM ist jetzt
  ebenfalls positiv.
- Z. 194 bis 197, 314 bis 316, Bildunterschrift Z. 321 und Abschnitt 6 Z. 343 bis 351: alle bp-Aussagen (BTC
  „nine“ bis „twenty-nine“, ETH „one and three“, HYPE „between zero and one“, „nothing at all“, „two of the
  three underlyings do not pay“, „rises monotonically“) stammen aus dem Nenner-Fehler und sind neu zu schreiben.
- Z. 398 bis 400 (Schluss): „net edge sits so close to the registered threshold that an unobserved hedging
  cost decides it“ gilt nicht mehr.
- Z. 233 bis 235 (F1c): Quartile des Prämienanteils, siehe Nebenbefund.
- Z. 217 bis 223 (Inferenz): „Every interval reported in this paper was drawn the same number of times as the
  headline it belongs to“, bei B = 9 999. Die Intervalle von Zerlegung und Klassen in der ersten Fassung dieses
  Befunds sind mit B = 999 gezogen; siehe Empfehlung 4.
- Nebenbeobachtung Z. 214 bis 215: Das Manuskript formuliert H4 umgekehrt zur Präregistrierung („holds that a
  net edge survives in a majority … rejected otherwise“), und Z. 313 („fires either way“) passt zu den alten
  Zahlen nicht, dort griff nur der ATM-Zweig. Beim Neuschreiben mitkorrigieren.

**Committete PDF und Abbildungen**

- `paper/Derive Orderbook Adverse Selection.pdf` (Commit 0afff2c): umbenannte Kopie des Manuskripts, die das
  `.gitignore` für `paper/main.pdf` umgeht. Sie enthält alle oben genannten alten Aussagen (Textextraktion:
  „leave a net edge of +8.93“, T2-Beschriftung „−1.56 +0.59 … +8.93“, „sits just under it at 49.5 per cent“,
  „57.7 49.5 38.1“ im F5-Panel, „about nine basis points … twenty-nine“, „nothing at all“, „−1.6 … +21.1 per
  cent“). Aus dem Repo nehmen oder ausdrücklich als überholt kennzeichnen und nach der Korrektur neu erzeugen.
- `paper/figures/t2.pdf` (Balken und Fehlerbalken von Gebühr, Rabatt, Netto-Edge), `f5.pdf` (bp-Zeile und
  Sensitivitätspanel), `f1.pdf` (Panel c, Quartile), `f2.pdf` (Panel c): neu bauen.

**Social-Texte und Karten**

- `paper/social/x_article.md`, Artikel: Z. 37 bis 38 (8.93), Z. 83 bis 87 („rises … in all three underlyings,
  and BTC is in a different league“, „HYPE sits between 0.1 and 0.6 basis points … nothing at all“), Z. 96 bis
  98 (49.5 % und Hedge-Kosten zwischen null und einem bp).
- `paper/social/x_article.md`, Thread: Tweet 3 Z. 136 bis 137 (+8.93 USDC per contract) und Tweet 7 Z. 176 bis
  178 („BTC is in a different league“, „HYPE pays 0.1 to 0.6 bp … After hedging, nothing“). Die Vorbemerkung
  Z. 4 bis 5 („will move slightly“) trifft für H4 und die Karte nicht zu.
- Karten `paper/social/s1_decomposition.png` (Gebühr, Rabatt und NET EDGE aus `figdata.waterfall_components`)
  und `paper/social/s5_map.png` (bp-Karte; Untertitel „HYPE pays almost nothing anywhere.“ aus
  `derive_surface/figures_social.py` Z. 210 bis 211).

**Dokumentation**

- `docs/paper1/ZAHLENBLATT.md`: H4 Z. 27 bis 30, Sensitivität Z. 36 bis 38, Klassentabelle Z. 44 bis 49
  (Gebühr, Rebate, Netto-Edge), Zellen mit grösstem und kleinstem Netto-Edge Z. 63 bis 74 (die drei
  ETH-Zellen mit niedrigem Delta stehen dort als die negativsten und sind neu signifikant positiv).
- `docs/paper1/ABBILDUNGEN.md` Z. 22: T2-Prüfwert 8,93245.
- `docs/paper1/ABBILDUNGS_BEFUNDE.md` §2 Z. 13 bis 28: alte bp-Tabelle (BTC 9,0 / 28,5 / 73,8, ETH 0,9 / 3,3 /
  4,8, HYPE 0,3 / 0,5 / 0,1), „Die Ordnung ist in allen drei Basiswerten dieselbe“, „rund eine
  Grössenordnung“ zwischen den Basiswerten, „HYPE … praktisch nichts“. §1 bleibt inhaltlich (die BTC-Zellen in
  USDC ändern sich um höchstens 3,1 USDC, Median der Zellen ≤ 2 d 23,95 gegen 24,19, > 90 d 204,4 gegen 204,2).
- `docs/paper1/ABBILDUNGSWAHL.md` Z. 59: Die Nachrechnung ersetzte die Quartile eines Entwurfs, −3,3 / +3,4 /
  +13,5 %, durch −1,6 / +1,1 / +21,1 %. Die Werte des Entwurfs waren die einheitliche Form je Kontrakt; die
  „Korrektur“ führte den Einheitenmix ein. Ausserdem Z. 50 (Sensitivität 57,7 %).
- `docs/paper2/UEBERGABE.md` Z. 26 bis 27 (Zerlegung mit −1,56 / +0,59 / +8,93).
- Nur zur Kenntnis, als Protokoll nicht umzuschreiben: `docs/superpowers/plans/2026-09-18-p1-abbildungen.md`
  Z. 254 bis 255 und 334.

**Nicht betroffen:** H1 (90,5 %, Grösse, Sweeps), H2, H3, alle Markouts inklusive +24,73 und −25,41,
Horizonte, Pfadvergleich, T2 Panel b, Abbildungen T1, F3, F4, F6, A1 und die Karten S2 bis S4.

## Empfehlung für den Enddatenlauf

1. **Nachtrag.** Vor dem Lauf einen datierten Nachtrag in `docs/paper1/PRAEREGISTRIERUNG.md`: Gebühr und Rabatt
   der Maker-Zeile sind Summen je Fill und werden durch die Menge geteilt (wie Nachtrag 2 von Paper 2); bei
   mehrbeinigen RFQ ist die Gebühr eine Summe je Paket und auf einem Bein gebucht, die Verteilung über das Paket
   wird als Sensitivität berichtet. Offen benennen, dass der Fehler nach dem Pilotlauf gefunden wurde. Die alte
   Form als Sensitivität berichten.

2. **Code, vollständig.** Die Korrektur in `analysis_frame` allein genügt nicht: Wasserfall, T2-Fehlerbalken
   und Klassentabelle lesen die rohen Spalten weiter. Nur `net_edge` zu korrigieren, liesse T2 Gebühr −1,56
   und Rabatt +0,59 neben einem NE-Balken von +9,58 zeigen, S1 behielte +8,93, und `class_means.csv` behielte
   die alten Gebühren. Alle Stellen:

   a. `derive_surface/inference_p1.py`, `analysis_frame` (Z. 232): Spalten je Kontrakt bilden und nur sie
      verwenden.

          amount = f["amount"].to_numpy(float)
          amount = np.where(amount > 0, amount, np.nan)
          f["fee_pc"] = f["fee_maker"].to_numpy(float) / amount
          f["rebate_pc"] = f["rebate_maker"].to_numpy(float) / amount
          f["net_edge"] = f["y_usd"] - f["fee_pc"] + f["rebate_pc"] - f["hedge"].to_numpy()

      H4-Zellen und `h4_sensitivity.csv` (`cell_table` auf `net_edge`) folgen damit von selbst.
   b. `derive_surface/inference_p1.py`, Klassentabelle (Z. 371 bis 372): `mean_fee` aus `fee_pc`,
      `mean_rebate` aus `rebate_pc`. `scripts/p1_zahlenblatt.py` liest diese Spalten.
   c. `derive_surface/figdata.py`, `waterfall_components` (Z. 145 bis 146): `fee_pc` und `rebate_pc` statt
      `fee_maker` und `rebate_maker`. Das korrigiert T2 (`figures_p1.py` Z. 182), die Karte S1
      (`figures_social.py` Z. 89) und die T2-Prüfung in `scripts/p1_figure_check.py` Z. 58 bis 60.
   d. `derive_surface/figures_p1.py`, `fig_t2` Panel a (Z. 183 bis 184): Intervalle aus `fee_pc` und
      `rebate_pc`. Panel b (Z. 238 bis 242) bleibt bei `fee_maker / (price · amount)` und
      `fee_taker / (price · amount)`: Summe des Fills durch Prämie des Fills ist einheitlich.
   e. F5 und S5 (`figures_p1.py` Z. 538, `figures_social.py` Z. 206): `bp = 1e4 · net_edge / index_price`
      (gleich NE·a / (a·Index)), oder als Zellquotient Σ NE·a / Σ Index·a wie in Paper 2. Den Untertitel von S5
      (`figures_social.py` Z. 210 bis 211, „HYPE pays almost nothing anywhere“) neu schreiben.
   f. F1c (`figures_p1.py` Z. 317 bis 318) und F2c (Z. 338, 346 und 362): Markout je Kontrakt durch `price`,
      nicht durch `_premium(...) = price · amount`. `_premium` (Z. 50 bis 51) bleibt nur für T2 Panel b.
   g. `scripts/p1_figure_check.py`: Die T2-Prüfung (Z. 58 bis 60) vergleicht dann wieder echt; zusätzlich prüfen,
      dass der Gebührenschritt gleich −mean(`fee_pc`) ist und die F5-Textwerte aus NE / Index stammen.
   h. Tests mit `amount ≠ 1`. `test_analysis_frame_decomposes_the_markout` (`tests/test_p1_inference.py`) mit
      Mengen wie 0,5 und 4 erweitern. `test_waterfall_components_add_up_to_the_net_edge`
      (`tests/test_p1_figdata.py`) ist tautologisch, weil die Zeile „net edge“ selbst die Summe der Schritte
      ist; er muss gegen das Mittel von `net_edge` eines `analysis_frame` prüfen:

          f = inf.analysis_frame(rows_with_amounts([0.5, 4.0]), funding)
          steps = figdata.waterfall_components(f).set_index("step")["value"]
          assert steps.drop("net edge").sum() == pytest.approx(np.nanmean(f["net_edge"]))
          assert steps["maker fee"] == pytest.approx(-np.nanmean(f["fee_maker"] / f["amount"]))

      Dazu je ein Test für Klassentabelle (Gebühr je Kontrakt), F5 (bp = NE / Index) und F1c/F2c (Markout /
      Preis). Vorlage: `tests/test_p1_befund_gebuehreneinheit.py`.

3. **Danach** Zahlenblatt, `p1_figure_check.py`, Abbildungen, Social-Karten, `x_article.md`, die committete PDF
   und die oben genannten Textstellen neu; H4-Absatz, Abschnitt 6 und Schluss inhaltlich neu schreiben, nicht nur
   Zahlen tauschen.

4. **Intervalle (A68).** Werden Intervalle der Zerlegung oder der Klassen im Text zitiert, die mit B = 9 999
   (`decomposition_b9999`, `classes_b9999`), damit der Satz in `paper/main.tex` Z. 222 bis 223 stimmt. Die
   Fehlerbalken der Abbildungen sind mit B = 999 gezogen (`figures_p1.py` Z. 36); dann den Satz auf die Intervalle
   im Text einschränken oder die Abbildungen ebenfalls mit 9 999 Ziehungen rechnen. Das Vault-Intervall nur mit
   G = 8 oder gar nicht angeben (A66).

5. Paper 2 rechnet bereits je Kontrakt; nach der Korrektur sind beide Papiere konsistent.
