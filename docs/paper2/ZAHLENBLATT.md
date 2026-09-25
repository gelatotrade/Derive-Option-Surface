# Zahlenblatt Paper 2

Erzeugt 2026-09-25 01:47 UTC aus `results/p2` mit `scripts/p2_zahlenblatt.py`. Alle Kopfzahlen maschinenlesbar in `results/p2/summary.json` (flach, Schlüssel stabil).

- **Datenstand:** Stichprobe vom 11.01.2024 00:00 UTC bis zum letzten Fill am 17.09.2026 11:51:53 UTC. **Pilotstand:** Die Stichprobe endet vor dem präregistrierten Ende (30.09.2026 08:00 UTC); die Zahlen des Manuskripts entstehen mit dem Enddatenlauf. Stichtag 17.09.2026.
- **Inferenz:** B = 9 999, Seed 20260924, 90-%-Perzentilintervalle aus einem Cluster-Bootstrap über UTC-Tage (H1 bis H3, Nachtrag 3). H4: Wild-Cluster-Bootstrap mit Rademacher-Gewichten und restringierten Residuen, Cluster UTC-Tag, einseitiges p für β > 0, 100 Placebo-Termine.
- **Messung:** Kapital unter IM (MM als Sensitivität), Netto-Edge je Kontrakt nach Nachtrag 2: NE = MO_30min − (Gebühr − Rabatt)/Menge − Hedge; Edge eines Fills = NE·Menge. Konten nur als Labels (M1 bis M10).

## Stichprobe

- Fills der Stichprobe von Paper 1: 603 940 (BTC 154 676, ETH 405 250, HYPE 44 014).
- PM2-Fenster ab BTC 12.06.2025 23:00 UTC, ETH 12.06.2025 23:00 UTC, HYPE 11.11.2025 00:00 UTC: 336 087 Fills (BTC 98 479, ETH 193 600, HYPE 44 008).
- Fills mit Kapital je Kontrakt ≤ 0 unter IM: SM 10, Legacy-PM 9, PM2 20 (nichts ausgeschlossen; Ausschlüsse nur nach den Regeln von H2 und H3).
- H1: 173 von 210 Zellen besetzt (mindestens 200 Fills; BTC 60, ETH 68, HYPE 45), 331 813 Fills in besetzten Zellen, 463 UTC-Tage vom 12.06.2025 bis 17.09.2026.
- H2: Stichprobe von 20 000 Fills der Konten M3, M5, M8, M10 (ETH 13 594, HYPE 6 405), n = 19 999 nach Ausschluss, 372 UTC-Tage vom 04.09.2025 bis 17.09.2026.
- H3: 1 968 Maker-Tage im Fenster, davon 1 943 gerechnet (nicht gerechnet: 24 ohne Optionen, 1 ohne Snapshot), 462 UTC-Tage vom 13.06.2025 bis 17.09.2026.
- H4: 18 Ereignisse, 14 behalten, davon 13 mit Panel-Zellen; Panel 91 446 Zeilen aus 84 919 Fills, 475 Zell-Ereignis-Paare, 141 Tages-Cluster.

## Validierung des Nachbaus gegen eth_call

- Schwelle der Präregistrierung je Basiswert, Manager und Art: Median |rel| < 0,1 %, 95. Perzentil < 1 %. Ergebnis: 32 von 32 Zellen (IM und MM) erfüllt, **bestanden**.
- 877 Fälle an Blöcken vom 14.01.2024 bis 17.09.2026; 1 Fall ohne Chain-Antwort (Revert), nicht vergleichbar.
- Einzelkontrakte unter IM: n = 799, Median |rel| 8,7·10⁻¹⁰, p95 1,4·10⁻⁸, Maximum 8,9·10⁻⁸; grösste absolute Abweichung 0,00033 USD.
- Bücher unter IM: n = 77 (2 bis 245 Beine), Median |rel| 2,2·10⁻⁹, p95 1,3·10⁻⁸, Maximum 3,4·10⁻⁸; grösste absolute Abweichung 0,050 USD.
- MM (Sensitivität): Einzelkontrakte Median 1,1·10⁻⁹, p95 2,0·10⁻⁸; Bücher Median 2,2·10⁻⁹, p95 1,5·10⁻⁸.
- Szenario-Weg gegen direkten Aufruf: 6 Bücher, bitgleich: ja.

| Art | Basiswert | Manager | n | fehlend | Median \|rel\| | p95 \|rel\| | Max \|rel\| | Schwelle |
|---|---|---|---:|---:|---:|---:|---:|---|
| Einzelkontrakt | BTC | SM | 100 | 0 | 1,4·10⁻¹⁰ | 6,9·10⁻⁹ | 2,4·10⁻⁸ | erfüllt |
| Einzelkontrakt | BTC | Legacy-PM | 100 | 0 | 2,4·10⁻⁹ | 1,5·10⁻⁸ | 3,1·10⁻⁸ | erfüllt |
| Einzelkontrakt | BTC | PM2 | 100 | 0 | 1,8·10⁻¹⁰ | 1,4·10⁻⁸ | 5,0·10⁻⁸ | erfüllt |
| Einzelkontrakt | ETH | SM | 100 | 0 | 0 | 9,5·10⁻⁹ | 1,4·10⁻⁸ | erfüllt |
| Einzelkontrakt | ETH | Legacy-PM | 100 | 0 | 3,2·10⁻⁹ | 2,0·10⁻⁸ | 6,5·10⁻⁸ | erfüllt |
| Einzelkontrakt | ETH | PM2 | 100 | 0 | 7,4·10⁻¹⁰ | 2,3·10⁻⁸ | 8,9·10⁻⁸ | erfüllt |
| Einzelkontrakt | HYPE | SM | 100 | 0 | 9,2·10⁻¹² | 5,6·10⁻⁹ | 1,2·10⁻⁸ | erfüllt |
| Einzelkontrakt | HYPE | PM2 | 99 | 1 | 1,7·10⁻⁹ | 1,5·10⁻⁸ | 3,5·10⁻⁸ | erfüllt |
| Buch | BTC | SM | 7 | 0 | 7,1·10⁻¹⁰ | 9,3·10⁻⁹ | 1,2·10⁻⁸ | erfüllt |
| Buch | BTC | Legacy-PM | 7 | 0 | 1,3·10⁻⁹ | 8,0·10⁻⁹ | 8,1·10⁻⁹ | erfüllt |
| Buch | BTC | PM2 | 7 | 0 | 2,2·10⁻¹⁰ | 9,1·10⁻⁹ | 1,1·10⁻⁸ | erfüllt |
| Buch | ETH | SM | 18 | 0 | 7,5·10⁻¹⁰ | 4,0·10⁻⁹ | 6,8·10⁻⁹ | erfüllt |
| Buch | ETH | Legacy-PM | 18 | 0 | 3,9·10⁻⁹ | 2,4·10⁻⁸ | 3,4·10⁻⁸ | erfüllt |
| Buch | ETH | PM2 | 18 | 0 | 3,8·10⁻⁹ | 1,3·10⁻⁸ | 2,1·10⁻⁸ | erfüllt |
| Buch | HYPE | SM | 1 | 0 | 2,6·10⁻⁹ | 2,6·10⁻⁹ | 2,6·10⁻⁹ | erfüllt |
| Buch | HYPE | PM2 | 1 | 0 | 4,3·10⁻⁹ | 4,3·10⁻⁹ | 4,3·10⁻⁹ | erfüllt |

## H1 Rangfolge (präregistriert)

- Spearman-ρ zwischen Edge in bp des Nominals und Edge je PM2-Kapital über 173 besetzte Zellen im PM2-Fenster: **0,903 [0,881; 0,907]** (90-%-Intervall).
- Regel: abgelehnt, wenn die obere Grenze ≥ 0,5 ist. Urteil: **abgelehnt**.
- Gepoolt über die besetzten Zellen: Edge 3,38 bp des Nominals und 39,9 bp des PM2-Kapitals.
- Rangverschiebung (Rang nach Kapital minus Rang nach Nominal, Rang 1 = höchster Edge): Median |Δ| 14,0, grösste |Δ| 72.
- Bootstrap: jede Replikation enthält mindestens 173 der 173 Zellen; 0 Replikationen ohne ρ.
- 20 Fills mit K_PM2 ≤ 0 bleiben in den Summen (Nachtrag 4); nicht endlich: 0.

| Basiswert | Zellen | Fills | Edge bp Nominal | Edge bp PM2-Kapital | ρ je Basiswert (explorativ) |
|---|---:|---:|---:|---:|---|
| BTC | 60 | 97 370 | 1,50 | 20,1 | 0,892 [0,871; 0,915] |
| ETH | 68 | 193 326 | 2,98 | 37,8 | 0,922 [0,886; 0,925] |
| HYPE | 45 | 41 117 | 13,48 | 90,8 | 0,888 [0,818; 0,911] |

Grösste Rangverschiebungen (negativ: die Zelle rückt unter Kapital nach vorn):

| Zelle | Fills | Edge bp Nominal | Rang | Edge bp Kapital | Rang | Verschiebung |
|---|---:|---:|---:|---:|---:|---:|
| BTC\|buy\|00-10\|2-7d | 2 149 | 2,63 | 76 | 2 270,0 | 4 | −72 |
| ETH\|buy\|00-10\|2-7d | 2 905 | 2,63 | 77 | 1 372,4 | 10 | −67 |
| BTC\|buy\|00-10\|7-30d | 1 933 | 2,85 | 72 | 1 433,8 | 9 | −63 |
| ETH\|buy\|00-10\|7-30d | 2 990 | 2,83 | 73 | 839,8 | 19 | −54 |
| BTC\|buy\|10-25\|2-7d | 3 312 | 1,67 | 84 | 401,1 | 32 | −52 |
| BTC\|buy\|25-40\|<=2d | 2 111 | −2,56 | 127 | −505,0 | 169 | +42 |
| HYPE\|sell\|40-60\|>90d | 474 | 27,27 | 17 | 85,4 | 60 | +43 |
| ETH\|buy\|10-25\|<=2d | 4 689 | −0,41 | 106 | −140,2 | 151 | +45 |
| BTC\|buy\|00-10\|<=2d | 2 057 | −1,68 | 121 | −2 282,1 | 173 | +52 |
| BTC\|buy\|10-25\|<=2d | 2 778 | −0,81 | 111 | −383,1 | 165 | +54 |

## H2 Grenzkosten (präregistriert)

- Median von ratio = (ΔK/Menge)/K_PM2,Einzel über 19 999 Fills: **0,0345 [0,0307; 0,0386]** (90-%-Intervall).
- Regel: abgelehnt, wenn die obere Grenze ≥ 0,5 ist. Urteil: nicht abgelehnt.
- Anteil ratio ≤ 0: 42,0 %. Ausgeschlossen mit K_PM2,Einzel ≤ 0: 1 von 20 000 gezogenen Fills; nicht endlich 0, Status nicht ok 0.
- Konten (Buch zu Tagesbeginn unter PM2): M3, M5, M8, M10; Fills je Basiswert: ETH 13 594, HYPE 6 405; 372 UTC-Tage.
- Gegenprobe: gespeicherte Spalte ratio gegen Neuberechnung, grösste Abweichung 0.

## H3 Netting-Wert (präregistriert)

- Median von K_SM/K_PM2 über 1 943 Maker-Tage: **4,747 [4,662; 4,824]** (90-%-Intervall).
- Regel: abgelehnt, wenn die untere Grenze ≤ 2,0 ist. Urteil: nicht abgelehnt.
- 1 968 Maker-Tage im Fenster, nicht gerechnet: 24 ohne Optionen, 1 ohne Snapshot; ausgeschlossen mit K_PM2 ≤ 0: 0; 462 UTC-Tage vom 13.06.2025 bis 17.09.2026.
- An 1 431 Tagen (73,6 %) hält das Buch mehr als 63 Optionen; K_SM ist dort kontrafaktisch (Nachtrag 4).
- Maker-Tage je Konto: M1 120, M2 328, M3 303, M4 203, M5 374, M6 119, M7 10, M8 239, M10 247.

## H4 Preis des Kapitals (präregistriert)

- β = **−4,60** bp des Index je Einheit log-Dosis; 90-%-Intervall [−26,04; 16,59] (Wild-Cluster-Bootstrap mit unrestringierten Residuen, beschreibend); Cluster-SE 13,09, t −0,351.
- Einseitiges Wild-Cluster-Bootstrap-p für β > 0: 0,6224 (B = 9 999).
- Placebo: 100 von 100 Replikationen endlich; 95. Perzentil 23,41, Median 1,15, Mittel −7,56, Spanne −101,30 bis 42,38; Anteil der Placebo-β ≥ β: 64 %.
- Kriterien: β > 0 nein; p ≤ 0,05 nein; β über dem Placebo-P95 nein.
- Regel: abgelehnt, wenn β nicht positiv ist mit p ≤ 0,05 oder nicht über dem 95. Perzentil der Placebo-β liegt. Urteil: **abgelehnt**.
- Umfang: n = 91 446 Zeilen, 84 919 Fills, 13 Ereignisse mit Zellen (14 behalten), 475 Zell-Ereignis-Paare, 322 Tag-Basiswert-Gruppen, 141 Tages-Cluster.
- Kontrollen: Herausmitteln in 53 Iterationen, Abweichung zur direkten Lösung 1,1·10⁻¹³; Panel neu gebaut identisch: ja.

## Explorative Sensitivitäten

Nicht präregistriert als Test. „Urteil nach Regel“ ist das Urteil, das die präregistrierte Regel der jeweiligen Hypothese auf diese Variante gäbe.

### (a) Karten unter anderen Managern

| Variante | Grösse | Wert [90-%-Intervall] | n | Urteil nach Regel |
|---|---|---|---:|---|
| PM2, PM2-Fenster (gleich Test H1) | ρ | 0,903 [0,881; 0,907] | 173 | abgelehnt |
| SM, ganzer Zeitraum | ρ | 0,896 [0,872; 0,903] | 177 | abgelehnt |
| Legacy-PM, ganzer Zeitraum | ρ | 0,910 [0,885; 0,914] | 132 | abgelehnt |
| SM auf den Fills des PM2-Fensters | ρ | 0,898 [0,873; 0,902] | 173 | abgelehnt |
| Legacy-PM auf den Fills des PM2-Fensters | ρ | 0,908 [0,885; 0,912] | 128 | abgelehnt |

### (b) MM statt IM

| Variante | Grösse | Wert [90-%-Intervall] | n | Urteil nach Regel |
|---|---|---|---:|---|
| H1 mit MM | ρ | 0,903 [0,880; 0,907] | 173 | abgelehnt |
| Karte SM, ganzer Zeitraum, mit MM | ρ | 0,902 [0,879; 0,910] | 177 | abgelehnt |
| H2 mit MM | Median dK_mm_per_contract/K_single_pm2_mm_acct | 0,0291 [0,0251; 0,0339] | 19 693 | nicht abgelehnt |
| h2_ratio_mm_std | Median dK_mm_std_per_contract/K_single_pm2_mm | 0,0278 [0,0242; 0,0324] | 19 977 | nicht abgelehnt |
| H3 mit MM | Median K_sm_mm/K_pm2_mm | 5,614 [5,471; 5,802] | 1 943 | nicht abgelehnt |

### (c) Netto-Edge in der Form von Paper 1 (Gebühr und Rabatt ungeteilt)

| Variante | Grösse | Wert [90-%-Intervall] | n | Urteil nach Regel |
|---|---|---|---:|---|
| H1 mit Netto-Edge wie Paper 1 | ρ | 0,913 [0,879; 0,915] | 173 | abgelehnt |

### (d) H2-Varianten

| Variante | Grösse | Wert [90-%-Intervall] | n | Urteil nach Regel |
|---|---|---|---:|---|
| ratio (gleich Test H2) | Median dK_per_contract/K_single_pm2 | 0,0345 [0,0307; 0,0386] | 19 999 | nicht abgelehnt |
| nächster einzelner Kontrakt (ratio_unit) | Median dK_unit/K_single_pm2 | 0,0329 [0,0295; 0,0366] | 19 999 | nicht abgelehnt |
| Buch aus dem Tape | Median dK_tape_per_contract/K_single_pm2 | 0,0340 [0,0305; 0,0382] | 19 999 | nicht abgelehnt |
| MM | Median dK_mm_per_contract/K_single_pm2_mm_acct | 0,0291 [0,0251; 0,0339] | 19 693 | nicht abgelehnt |
| ratio_mm_std | Median dK_mm_std_per_contract/K_single_pm2_mm | 0,0278 [0,0242; 0,0324] | 19 977 | nicht abgelehnt |
| Konto M3 | Median dK_per_contract/K_single_pm2 | 0,0230 [0,0126; 0,0356] | 6 405 | nicht abgelehnt |
| Konto M5 | Median dK_per_contract/K_single_pm2 | 0,0505 [0,0387; 0,0743] | 5 957 | nicht abgelehnt |
| Konto M8 | Median dK_per_contract/K_single_pm2 | 0,0449 [0,0376; 0,0625] | 4 296 | nicht abgelehnt |
| Konto M10 | Median dK_per_contract/K_single_pm2 | 0,0258 [0,0220; 0,0293] | 3 341 | nicht abgelehnt |
| Basiswert ETH | Median dK_per_contract/K_single_pm2 | 0,0378 [0,0342; 0,0421] | 13 594 | nicht abgelehnt |
| Basiswert HYPE | Median dK_per_contract/K_single_pm2 | 0,0230 [0,0126; 0,0356] | 6 405 | nicht abgelehnt |
| Regime R1 | Median dK_per_contract/K_single_pm2 | 0,0503 [0,0411; 0,0693] | 5 137 | nicht abgelehnt |
| Regime R2 | Median dK_per_contract/K_single_pm2 | 0,0372 [0,0305; 0,0466] | 7 906 | nicht abgelehnt |
| Regime R3 | Median dK_per_contract/K_single_pm2 | 0,0117 [−0,0012; 0,0220] | 5 593 | nicht abgelehnt |
| Regime R4 | Median dK_per_contract/K_single_pm2 | 0,0899 [0,0241; 0,1639] | 1 363 | nicht abgelehnt |

### (e) H3-Varianten

| Variante | Grösse | Wert [90-%-Intervall] | n | Urteil nach Regel |
|---|---|---|---:|---|
| K_SM/K_PM2 (gleich Test H3) | Median K_sm/K_pm2 | 4,747 [4,662; 4,824] | 1 943 | nicht abgelehnt |
| K_SM/K_PM2 mit MM | Median K_sm_mm/K_pm2_mm | 5,614 [5,471; 5,802] | 1 943 | nicht abgelehnt |
| K_SM/K_PM, BTC- und ETH-Beine | Median K_sm_be/K_pm_be | 3,245 [3,174; 3,295] | 1 640 | nicht abgelehnt |
| K_PM/K_PM2, BTC- und ETH-Beine | Median K_pm_be/K_pm2_be | 1,545 [1,535; 1,554] | 1 640 | beschreibend |
| K_SM/K_PM2, BTC- und ETH-Beine | Median K_sm_be/K_pm2_be | 4,826 [4,746; 4,926] | 1 640 | nicht abgelehnt |
| Tage mit höchstens 63 Optionen | Median K_sm/K_pm2 | 1,590 [1,532; 1,662] | 512 | abgelehnt |
| Tage mit mehr als 63 Optionen | Median K_sm/K_pm2 | 5,465 [5,345; 5,606] | 1 431 | nicht abgelehnt |
| Konto M1 | Median K_sm/K_pm2 | 5,294 [4,942; 5,472] | 120 | nicht abgelehnt |
| Konto M2 | Median K_sm/K_pm2 | 1,076 [1,049; 1,111] | 328 | abgelehnt |
| Konto M3 | Median K_sm/K_pm2 | 4,357 [4,193; 4,559] | 303 | nicht abgelehnt |
| Konto M4 | Median K_sm/K_pm2 | 8,722 [7,524; 9,296] | 203 | nicht abgelehnt |
| Konto M5 | Median K_sm/K_pm2 | 5,444 [5,216; 5,671] | 374 | nicht abgelehnt |
| Konto M6 | Median K_sm/K_pm2 | 4,239 [3,987; 4,439] | 119 | nicht abgelehnt |
| Konto M7 | Median K_sm/K_pm2 | 6,311 [4,925; 12,243] | 10 | nicht abgelehnt |
| Konto M8 | Median K_sm/K_pm2 | 5,257 [5,134; 5,361] | 239 | nicht abgelehnt |
| Konto M10 | Median K_sm/K_pm2 | 5,663 [5,329; 5,924] | 247 | nicht abgelehnt |
| Regime R1 | Median K_sm/K_pm2 | 4,440 [4,272; 4,592] | 990 | nicht abgelehnt |
| Regime R2 | Median K_sm/K_pm2 | 4,675 [4,496; 4,788] | 590 | nicht abgelehnt |
| Regime R3 | Median K_sm/K_pm2 | 5,720 [5,447; 5,940] | 279 | nicht abgelehnt |
| Regime R4 | Median K_sm/K_pm2 | 6,001 [5,756; 6,620] | 84 | nicht abgelehnt |
| Manager des Kontos PM | Median K_sm/K_pm2 | 5,457 [5,291; 5,719] | 452 | nicht abgelehnt |
| Manager des Kontos PM2 | Median K_sm/K_pm2 | 5,161 [5,068; 5,262] | 1 163 | nicht abgelehnt |
| Manager des Kontos SM | Median K_sm/K_pm2 | 1,076 [1,049; 1,111] | 328 | abgelehnt |
| Tage mit höchstens 63 Optionen ohne SM-Konto | Median K_sm/K_pm2 | 3,780 [3,635; 3,980] | 184 | nicht abgelehnt |

### (f) Zeitnormierung

| Variante | Grösse | Wert [90-%-Intervall] | n | Urteil nach Regel |
|---|---|---|---:|---|
| bis zum Verfall, annualisiert | ρ (Edge je Kapital und Jahr) | 0,806 [0,761; 0,813] | 173 | abgelehnt |
| empirische Haltedauer | ρ (Edge je Kapital und Jahr) | 0,833 [0,795; 0,841] | 173 | abgelehnt |
| Haltedauer ohne Transfers | ρ (Edge je Kapital und Jahr) | 0,822 [0,780; 0,831] | 167 | abgelehnt |

### (g) Werte je Basiswert

| Variante | Grösse | Wert [90-%-Intervall] | n | Urteil nach Regel |
|---|---|---|---:|---|
| BTC, PM2-Fenster | ρ | 0,892 [0,871; 0,915] | 60 | abgelehnt |
| BTC, SM, ganzer Zeitraum | ρ | 0,911 [0,882; 0,926] | 63 | abgelehnt |
| ETH, PM2-Fenster | ρ | 0,922 [0,886; 0,925] | 68 | abgelehnt |
| ETH, SM, ganzer Zeitraum | ρ | 0,890 [0,857; 0,903] | 69 | abgelehnt |
| HYPE, PM2-Fenster | ρ | 0,888 [0,818; 0,911] | 45 | abgelehnt |
| HYPE, SM, ganzer Zeitraum | ρ | 0,887 [0,817; 0,910] | 45 | abgelehnt |

### (h) Vorzeichenstruktur von H1 (Review-Runde 1)

| Variante | Grösse | Wert [90-%-Intervall] | n | Urteil nach Regel |
|---|---|---|---:|---|
| nur Zellen mit Edge > 0 | ρ | 0,634 [0,623; 0,737] | 99 | abgelehnt |
| nur Zellen mit Edge ≤ 0 | ρ | 0,636 [0,674; 0,830] | 74 | abgelehnt |
| nur Maker-Verkäufe | ρ | 0,990 [0,985; 0,992] | 86 | abgelehnt |
| nur Maker-Käufe | ρ | 0,721 [0,689; 0,784] | 87 | abgelehnt |
| Maker-Verkäufe mit Edge > 0 | ρ | 0,940 [0,937; 0,978] | 38 | abgelehnt |
| Maker-Käufe mit Edge > 0 | ρ | 0,243 [0,231; 0,476] | 61 | nicht abgelehnt |

### (h) H4-Varianten

| Variante | β | 90-%-Intervall | p | n | Placebo-P95 | Anteil Placebo-β ≥ β | Urteil nach Regel |
|---|---:|---|---:|---:|---:|---:|---|
| nur BTC (5 Ereignisse) | −3,42 | [−10,51; 3,57] | 0,7497 | 24 598 | – | – | – |
| nur ETH (5 Ereignisse) | −1,90 | [−8,36; 4,68] | 0,6690 | 53 378 | – | – | – |
| nur HYPE (3 Ereignisse) | −10,12 | [−85,84; 64,68] | 0,5778 | 13 470 | – | – | – |
| ohne Zellen mit \|d\| > 1 | −4,60 | [−26,04; 16,59] | 0,6224 | 91 446 | 23,41 | 65 % | abgelehnt |
| Placebo-Abstand zu allen Zeitlinien | −4,60 | [−26,04; 16,59] | 0,6224 | 91 446 | 21,57 | 88 % | abgelehnt |

- Zellen mit \|d\| > 1: HYPE-pm2-20260820 HYPE|buy|00-10|2-7d (d = −1,648). Im echten Panel fallen 0 Zeilen weg; die Variante wirkt sonst nur in den Placebo-Panels.
- Abstand zu allen Zeitlinien: Placebo-Termine halten 28 Tage Abstand zu jeder Parameteränderung des Basiswerts unter SM, Legacy-PM, PM2-Standard-Lib und den Konto-Libs.

## Referenzbuch-Effekte der Ereignisse

Referenzbuch: Short-Straddle ATM (Strike = Forward) des Verfalls nahe 30 Tagen, 1 Kontrakt je Bein, täglich 08:00 UTC; K_vorher rechnet dasselbe Buch im selben Marktzustand mit den Parametern von 24 h früher (reiner Parametereffekt, `results/p2/reference_book.csv`). Zeile je Ereignis aus `results/p2/events.csv`; der Referenzbuch-Tag ist der erste Tag, dessen Parameterstand aus dem Ereignis stammt. K in bp des Forwards.

| Ereignis | Zeitpunkt | Geänderte Strukturen | max. \|Dosis\| | behalten | Panel-Zellen | Referenzbuch-Tag | K vorher | K nachher | Änderung |
|---|---|---|---:|---|---:|---|---:|---:|---:|
| BTC-pm-20240612 | 12.06.2024 00:01 UTC | Basis | 0,06 % | nein | 0 | 12.06.2024 | 2 331 | 2 331 | 0,00 % |
| ETH-pm-20240612 | 12.06.2024 00:01 UTC | Basis | 0,06 % | nein | 0 | 12.06.2024 | 2 412 | 2 412 | 0,00 % |
| BTC-pm-20250222 | 22.02.2025 19:52 UTC | Basis, Kontingenzen, Vol-Schock, Szenarien | 28,26 % | ja | 25 | 23.02.2025 | 2 303 | 1 913 | −16,94 % |
| ETH-pm-20250222 | 22.02.2025 19:52 UTC | Basis, Kontingenzen, Vol-Schock, Szenarien | 27,83 % | ja | 50 | 23.02.2025 | 2 458 | 2 035 | −17,21 % |
| BTC-pm2-20251010 | 10.10.2025 22:55 UTC | Kontingenzen | 0,00 % | nein | 0 | 11.10.2025 | 1 435 | 1 435 | 0,00 % |
| ETH-pm2-20251010 | 10.10.2025 22:55 UTC | Kontingenzen | 0,00 % | nein | 0 | 11.10.2025 | 1 419 | 1 419 | 0,00 % |
| BTC-pm2-20260108 | 08.01.2026 22:50 UTC | Margin | 3,60 % | ja | 25 | 09.01.2026 | 1 440 | 1 463 | +1,61 % |
| ETH-pm2-20260108 | 08.01.2026 22:50 UTC | Margin | 5,35 % | ja | 37 | 09.01.2026 | 1 431 | 1 454 | +1,62 % |
| HYPE-pm2-20260108 | 08.01.2026 22:50 UTC | Margin | 2,09 % | ja | 0 | 09.01.2026 | 4 102 | 4 165 | +1,55 % |
| BTC-pm2-20260123 | 23.01.2026 04:24 UTC | Szenarien | 27,33 % | ja | 27 | 23.01.2026 | 1 458 | 1 313 | −9,96 % |
| ETH-pm2-20260123 | 23.01.2026 04:24 UTC | Szenarien | 27,14 % | ja | 40 | 23.01.2026 | 1 445 | 1 377 | −4,76 % |
| HYPE-pm2-20260508 | 08.05.2026 12:24 UTC | Basis, Kontingenzen | 11,66 % | ja | 29 | 09.05.2026 | 4 193 | 3 893 | −7,16 % |
| BTC-pm2-20260524 | 24.05.2026 04:05 UTC | Basis, Kontingenzen, Vol-Schock, Szenarien | 8,22 % | ja | 38 | 24.05.2026 | 1 319 | 1 219 | −7,54 % |
| ETH-pm2-20260524 | 24.05.2026 04:05 UTC | Kontingenzen, Vol-Schock | 5,45 % | ja | 54 | 24.05.2026 | 1 340 | 1 296 | −3,30 % |
| HYPE-pm2-20260524 | 24.05.2026 04:05 UTC | Basis, Margin, Kontingenzen, Vol-Schock, Szenarien | 44,21 % | ja | 35 | 24.05.2026 | 3 836 | 2 638 | −31,22 % |
| BTC-pm2-20260820 | 20.08.2026 22:09 UTC | Basis, Kontingenzen, Vol-Schock, Szenarien | 67,47 % | ja | 43 | 21.08.2026 | 1 213 | 935 | −22,93 % |
| ETH-pm2-20260820 | 20.08.2026 22:09 UTC | Basis, Kontingenzen, Vol-Schock, Szenarien | 51,51 % | ja | 52 | 21.08.2026 | 1 307 | 1 089 | −16,71 % |
| HYPE-pm2-20260820 | 20.08.2026 22:09 UTC | Margin, Kontingenzen, Vol-Schock, Szenarien | 164,82 % | ja | 20 | 21.08.2026 | 2 514 | 2 051 | −18,39 % |

Parametereffekte im Referenzbuch ohne Ereigniszeile (ausserhalb des Manager-Fensters oder nicht in der Ereignisliste):

- PM2 BTC 13.06.2025: −0,35 %, Parameterstand vom 12.06.2025 22:20 UTC.
- PM2 ETH 13.06.2025: −0,69 %, Parameterstand vom 12.06.2025 22:20 UTC.

Niveau des Referenzbuchs (K in bp des Forwards über die Tage im Manager-Fenster):

| Basiswert | Manager | Tage | Minimum | Median | Maximum |
|---|---|---:|---:|---:|---:|
| BTC | SM | 981 | 2 724 | 2 945 | 3 000 |
| BTC | Legacy-PM | 981 | 1 888 | 1 950 | 2 700 |
| BTC | PM2 | 462 | 933 | 1 369 | 1 464 |
| ETH | SM | 981 | 2 726 | 2 956 | 3 000 |
| ETH | Legacy-PM | 981 | 1 909 | 2 101 | 2 727 |
| ETH | PM2 | 462 | 1 078 | 1 422 | 1 589 |
| HYPE | SM | 311 | 5 750 | 5 990 | 6 000 |
| HYPE | PM2 | 311 | 1 997 | 4 062 | 4 375 |

## Manager-Anteile am Options-OI

Anteil von `OptionAsset.totalPosition` je Manager an der Summe über die Manager, jeweils am Monatsersten (`results/p2/manager_oi_share.csv`).

- BTC: Daten ab 01.2024; PM2 erstmals 07.2025 (17,2 %); höchstens 95,3 % (07.2026); Legacy-PM unter 1 % ab 02.2026; zuletzt (09.2026) SM 9,0 %, Legacy-PM 0,0 %, PM2 91,0 %.
- ETH: Daten ab 02.2024; PM2 erstmals 07.2025 (12,0 %); höchstens 80,6 % (08.2026); Legacy-PM unter 1 % ab 02.2026; zuletzt (09.2026) SM 28,1 %, Legacy-PM 0,0 %, PM2 71,9 %.
- HYPE: Daten ab 12.2025; PM2 erstmals 12.2025 (51,4 %); höchstens 93,0 % (04.2026); zuletzt (09.2026) SM 12,1 %, PM2 87,9 %.

| Monat | BTC SM | BTC Legacy-PM | BTC PM2 | ETH SM | ETH Legacy-PM | ETH PM2 | HYPE SM | HYPE PM2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024-01 | 78,1 % | 21,9 % | 0,0 % | – | – | – | – | – |
| 2024-02 | 46,0 % | 54,0 % | 0,0 % | 47,4 % | 52,6 % | 0,0 % | – | – |
| 2024-03 | 31,9 % | 68,1 % | 0,0 % | 33,5 % | 66,5 % | 0,0 % | – | – |
| 2024-04 | 26,0 % | 74,0 % | 0,0 % | 29,0 % | 71,0 % | 0,0 % | – | – |
| 2024-05 | 34,8 % | 65,2 % | 0,0 % | 30,0 % | 70,0 % | 0,0 % | – | – |
| 2024-06 | 13,3 % | 86,7 % | 0,0 % | 32,8 % | 67,2 % | 0,0 % | – | – |
| 2024-07 | 20,5 % | 79,5 % | 0,0 % | 42,3 % | 57,7 % | 0,0 % | – | – |
| 2024-08 | 31,0 % | 69,0 % | 0,0 % | 38,9 % | 61,1 % | 0,0 % | – | – |
| 2024-09 | 36,7 % | 63,3 % | 0,0 % | 42,9 % | 57,1 % | 0,0 % | – | – |
| 2024-10 | 47,0 % | 53,0 % | 0,0 % | 40,2 % | 59,8 % | 0,0 % | – | – |
| 2024-11 | 48,7 % | 51,3 % | 0,0 % | 36,1 % | 63,9 % | 0,0 % | – | – |
| 2024-12 | 46,5 % | 53,5 % | 0,0 % | 46,7 % | 53,3 % | 0,0 % | – | – |
| 2025-01 | 47,1 % | 52,9 % | 0,0 % | 48,6 % | 51,4 % | 0,0 % | – | – |
| 2025-02 | 44,1 % | 55,9 % | 0,0 % | 45,5 % | 54,5 % | 0,0 % | – | – |
| 2025-03 | 46,1 % | 53,9 % | 0,0 % | 43,8 % | 56,2 % | 0,0 % | – | – |
| 2025-04 | 47,9 % | 52,1 % | 0,0 % | 51,0 % | 49,0 % | 0,0 % | – | – |
| 2025-05 | 46,7 % | 53,3 % | 0,0 % | 49,6 % | 50,4 % | 0,0 % | – | – |
| 2025-06 | 45,5 % | 54,5 % | 0,0 % | 48,7 % | 51,3 % | 0,0 % | – | – |
| 2025-07 | 42,2 % | 40,6 % | 17,2 % | 50,6 % | 37,4 % | 12,0 % | – | – |
| 2025-08 | 45,6 % | 33,7 % | 20,7 % | 47,0 % | 38,9 % | 14,1 % | – | – |
| 2025-09 | 41,4 % | 39,8 % | 18,8 % | 42,8 % | 44,1 % | 13,1 % | – | – |
| 2025-10 | 37,5 % | 32,0 % | 30,5 % | 41,2 % | 37,5 % | 21,3 % | – | – |
| 2025-11 | 38,5 % | 17,1 % | 44,3 % | 37,9 % | 12,1 % | 50,0 % | – | – |
| 2025-12 | 37,8 % | 22,7 % | 39,5 % | 40,0 % | 13,1 % | 46,8 % | 48,6 % | 51,4 % |
| 2026-01 | 38,4 % | 4,1 % | 57,5 % | 27,8 % | 8,8 % | 63,4 % | 28,7 % | 71,3 % |
| 2026-02 | 28,7 % | 0,0 % | 71,3 % | 38,4 % | 0,2 % | 61,4 % | 46,1 % | 53,9 % |
| 2026-03 | 14,0 % | 0,0 % | 86,0 % | 29,6 % | 0,0 % | 70,4 % | 26,2 % | 73,8 % |
| 2026-04 | 6,1 % | 0,0 % | 93,9 % | 28,1 % | 0,0 % | 71,9 % | 7,0 % | 93,0 % |
| 2026-05 | 7,4 % | 0,0 % | 92,6 % | 30,8 % | 0,0 % | 69,2 % | 13,9 % | 86,1 % |
| 2026-06 | 16,4 % | 0,0 % | 83,6 % | 39,4 % | 0,0 % | 60,6 % | 16,4 % | 83,6 % |
| 2026-07 | 4,7 % | 0,0 % | 95,3 % | 30,1 % | 0,0 % | 69,9 % | 15,9 % | 84,1 % |
| 2026-08 | 5,1 % | 0,0 % | 94,9 % | 19,4 % | 0,0 % | 80,6 % | 12,8 % | 87,2 % |
| 2026-09 | 9,0 % | 0,0 % | 91,0 % | 28,1 % | 0,0 % | 71,9 % | 12,1 % | 87,9 % |

## Review-Runde 1 (explorativ oder beschreibend)

- H1, nur Vorzeichen: Mischt man die Ränge innerhalb der 99 Zellen mit Edge > 0 und der 74 übrigen (4 000 Ziehungen), ist ρ im Mittel 0,734 (5. bis 95. Perzentil 0,700 bis 0,770).
- H1 innerhalb von Gruppen: Edge > 0 0,634 (n = 99), Edge ≤ 0 0,636 (n = 74), Verkäufe 0,990, Käufe 0,721, Käufe mit Edge > 0 0,243 (n = 61).
- Beste Zellen: von den zehn besten je Kapital 1 unter den zehn besten je Nominal, von den besten 20 5; gleiches Vorzeichen in 173 Zellen.
- H2: Population vor der Ziehung 100 995 Fills; die präregistrierte Ziehung ergibt genau die Fills von marginal.parquet: ja.
- H3-Konten nach Manager: PM 4, PM2 4, SM 1.
- H3: 8 von 9 Kontomedianen über der Schwelle 2; höchstens 63 Optionen ohne SM-Konto 3,780 [3,635; 3,980] (n = 184).
- H3: 127 Maker-Tage mit mehr Beinen als das grösste validierte Buch (245 Beine).
- Fills ausserhalb jedes Manager-Fensters (ohne Kapital): 6.
- API gegen Chain-Semantik (195 Einzelkontrakte am 25.09.2026): PM2 Median |rel| 0,08 %, p95 0,50 %, Maximum 2,41 % (Laufzeit >90d); SM Median 0,00 %, Maximum 0,30 %.
- H4 Niveau: Halbspread im Panel im Mittel 7,93 bp des Index (Median 3,34); Kapital zehn Prozent billiger (Dosis −0,105): Änderung des Halbspreads +0,48 bp, Intervall −1,75 bis +2,74 bp.
- H4 nur Verkaufszellen: β −3,81, p 0,5766; OI-gewichtete Dosis (Anteil 54,5 % bis 94,9 %): β −5,13, p 0,5926.

## Konsistenzprüfungen

15 von 15 Prüfungen erfüllt. Die Prüfungen rechnen die Urteile aus den Zahlen und Regeln nach und gleichen die Dateien untereinander ab.

- Stichtag einheitlich: erfüllt (letzter Tag von H1, H3 und Referenzbuch gleich dem Tag des letzten Fills (17.09.2026), H2 endet am 17.09.2026).
- B, Seed und Niveau in allen Dateien gleich: erfüllt (B = 9 999, Seed 20260924, Niveau 90 %).
- Fills je Basiswert ergeben die Stichprobe: erfüllt (154 676 + 405 250 + 44 014 = 603 940).
- PM2-Fenster: Kapitaldatei und H1 zählen gleich: erfüllt (336 087 gegen 336 087).
- Validierung: alle Zellen unter der Schwelle: erfüllt (32 von 32 Zellen).
- H1: ρ aus h1_cells.csv gleich h1.json: erfüllt (0,902944 gegen 0,902944).
- H1: besetzte Zellen und Fills gleich h1.json: erfüllt (173 Zellen, 331 813 Fills).
- H1: Urteil folgt aus der Regel (obere Grenze ≥ Schwelle): erfüllt (obere Grenze 0,907, Schwelle 0,5).
- H2: Urteil folgt aus der Regel (obere Grenze ≥ Schwelle): erfüllt (obere Grenze 0,0386, Schwelle 0,5).
- H2: gespeicherte ratio gleich Neuberechnung: erfüllt (grösste Abweichung 0).
- H3: Urteil folgt aus der Regel (untere Grenze ≤ Schwelle): erfüllt (untere Grenze 4,662, Schwelle 2,0).
- H4: Kriterien und Urteil folgen aus β, p und Placebo-P95: erfüllt (β −4,60, p 0,6224, P95 23,41).
- H4: Herausmitteln gleich direkter Lösung, Panel reproduziert: erfüllt (Abweichung 1,1·10⁻¹³, Panel neu gebaut identisch: ja).
- H4: behaltene Ereignisse in events.csv gleich h4.json: erfüllt (14 gegen 14).
- Sensitivitäten: Grundvariante gleich dem Test: erfüllt (3 von 3 gleich).

## Einschränkungen dieser Zahlen

- Pilotstand: Die Stichprobe endet am 17.09.2026 11:51:53 UTC, vor dem präregistrierten Ende (30.09.2026 08:00 UTC). Die Zahlen des Manuskripts entstehen mit dem Enddatenlauf.
- H3: An 73,6 % der Maker-Tage hält das Buch mehr Optionen, als ein SM-Konto auf v2 halten kann; K_SM ist dort kontrafaktisch.
- H1: 20 Fills mit K_PM2 ≤ 0 (weit vom Mark bepreiste RFQ-Beine) bleiben in den Summen.
- H2 beruht auf 4 Konten unter PM2; die Verteilung je Konto steht unter (d).
- H4: Das Intervall für β ist beschreibend; das Urteil folgt aus dem einseitigen p und dem Placebo-P95. 141 Tages-Cluster, 13 Ereignisse mit Zellen.
- Kapital je Fill ist das Kapital eines leeren Buchs mit genau diesem Kontrakt (Einzelkontrakt); Nicht-USDC-Collateral bleibt ausserhalb von K.
