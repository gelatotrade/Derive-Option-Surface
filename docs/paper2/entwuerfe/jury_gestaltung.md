# Jury Paper 2, Linse Gestaltung

Stand 25.09.2026 · Juror Gestaltung (Muster Paper 1: drei Entwurfssätze, zwei Juroren) · nichts committet.

**Linse.** Lesbarkeit bei 8 pt im zweispaltigen CAS-Satz, gedruckt in Graustufen: Schrift nie unter 7 pt *nach dem
Einsetzen*, Dichte, dieselbe Kodierung in allen neun Abbildungen, 3D nur dort, wo es etwas trägt, und Farbkarten,
die auch in Grau noch funktionieren.

**Was geprüft wurde.**

1. Alle 29 PNG der drei Linsen angesehen, dazu die Probebilder `data/p2/surface/probe_*.png`,
   `proto_btc_iv_colored_by_smcapital.png` und ein Einzelbild des bestehenden GIF.
2. Graustufen: Die farbabhängigen Bilder (T1 M/P, F1 E, F2 E/P, F5 M/P, F6 M, T2 P) wurden nach Luminanz umgerechnet
   und angesehen.
3. **Mechanische Messung.** Das Skript `data/p2/fig_proto/jury/audit_protos.py` ruft jede Prototypfunktion auf, fängt
   `savefig` ab und schreibt keine Datei der Linsen neu. Es misst die gezeichnete Ausdehnung ohne Wasserzeichen
   und die kleinste gesetzte Schrift. Das Ergebnis steht in `data/p2/fig_proto/jury/audit_protos.csv`. Die
   PNG-Grössen selbst taugen dafür nicht, weil die grossen PROTOTYP-Stempel die `bbox tight` aufblähen (Praktiker F3
   liegt als PNG bei 4,5 Zoll, gezeichnet sind 3,29).
4. Von den Inferenzdateien (`h1.json` … `h4.json`, `fig_*.csv`, `sens_*.csv`) wurden nur Spaltennamen und Schlüssel
   gelesen, keine Werte. Von `manager_oi_share.csv` wurden Werte gelesen, weil die Datei deskriptiv ist.

Kürzel: M = Mechanismus, E = Empirie, P = Praktiker. Noten 1 bis 10 nur für die Gestaltung. Über Inhalt und
Nachrechnung urteilt der Referee.

---

## 1 · Urteil in einer Tabelle

| Slot | Wahl | Grösse (Zoll) | Kern der Entscheidung |
|---|---|---|---|
| T1 | **P-T1 a/b ⊕ M-T1 c/d** | 7,0 × 4,2 | P trägt den Wert auf der Fläche (Isolinien, Kopfzahl), M erklärt ihn (bindende Regel als 2D-Karte) |
| T2 | **P-T2 a/b ⊕ M-T2 c** | 7,0 × 2,6 | P ist die sauberste Fassung der Semantik, M-c ist die einzige Stelle, die zeigt, wie PM2 R bildet |
| F1 | **P-F1** | 7,0 × 3,9 | drei Basiswerte, eine Zahl je Zelle, der Managervergleich als Streifen statt neun Karten |
| F2 | **E-F2, a als Kleinvielfache je Basiswert** | 7,0 × 3,4 | einzige Fassung, die das Urteil *und* die Richtung der Umordnung zeigt; P- und M-Karten fallen in Grau durch |
| F3 | **P-F3 a ⊕ E-F3 b** | 3,4 × 3,6 | ECDF liest den Median direkt, der Forest trägt das Urteil |
| F4 | **P-F4 b (gebinnt) ⊕ E-F4 b** | 3,4 × 3,6 | Buchbreite als Mechanismus, Forest als Urteil, dieselbe Grammatik wie F3 |
| F5 | **P-F5 ⊕ Statusgrammatik aus E-F5** | 7,0 × 4,3 | direkte Beschriftung, eine Zahl je Ereignis, keine Legendenspalte |
| F6 | **M-F6 a ⊕ E-F6 a (FWL) ⊕ E-F6 c (Prüfliste)** | 7,0 × 4,2 | echte Dosiskarten zeigen die identifizierende Variation; b und c brauchen die Inferenzgrammatik |
| A1 | **M-A1 a ⊕ P-A1 b** | 7,0 × 2,5 | Streifen mit Median und n, dazu Fehler gegen Buchbreite |
| GIF | P/M-Konzept (3D, nur PM2) mit den Ehrlichkeitsregeln aus E | 1200 × 675 | |
| Karten | 1 = M-Karte ⊕ P-Stufen; 2 = P-Karte 2 (neuer Titel); 3 = P-Karte 3 nach H3, sonst M-Karte 3 | 1600 × 900 | |

Neun Abbildungen: T1, T2, F1 bis F6 und A1. Einzige 3D-Abbildung im PDF ist T1. F3 und F4 bleiben einspaltig, wie im
Gerüst `paper2/main.tex`, und bekommen dasselbe Layout, damit sie oben auf einer Seite nebeneinander stehen können.
Der gemeinsame `figure*`, den E vorschlägt, würde die Zahl auf acht senken und den Slot verschenken.

---

## 2 · Die Messung: Breite und kleinste Schrift nach dem Einsetzen

Alle drei Skripte setzen nirgends weniger als 7 pt, und das gilt auch für M (`FS = 7.0`), obwohl `figures_p1.py`
6,0 und 6,5 pt verwendet. Das Problem liegt woanders: Legenden, Seitentexte und lange Zeilenbeschriftungen ragen über
die Figurbreite hinaus. `\includegraphics[width=\linewidth]` skaliert das Bild dann wieder auf 7,0 bzw. 3,4 Zoll,
und damit schrumpft auch die Schrift.

| Prototyp | gezeichnet (Zoll) | Ziel | kleinste Schrift im Satz |
|---|---|---|---|
| E-F1 | 8,54 × 3,69 | 7,0 | **5,7 pt** |
| E-F3 | 3,96 × 3,54 | 3,4 | **6,0 pt** |
| E-F4 | 3,94 × 3,54 | 3,4 | **6,0 pt** |
| M-F5 | 7,69 × 4,73 | 7,0 | **6,4 pt** |
| E-F6 | 7,54 × 2,70 | 7,0 | 6,5 pt |
| M-F2 | 7,47 × 2,83 | 7,0 | 6,6 pt |
| P-F5 | 7,44 × 4,19 | 7,0 | 6,6 pt |
| E-T2 | 7,35 × 2,27 | 7,0 | 6,7 pt |
| P-F2 | 7,30 × 3,87 | 7,0 | 6,7 pt |
| P-F6 | 7,18 × 2,22 | 7,0 | 6,8 pt |
| E-F5 | 7,13 × 4,48 | 7,0 | 6,9 pt |
| alle übrigen (M-T1, M-T2, M-F1, M-F6, M-A1, E-F2, E-A1, P-T1, P-T2, P-F1, P-F3, P-F4, P-A1) | ≤ Ziel | | 7,0 pt |

**Auflage für `figures_p2.py`:** `figstyle` bekommt `FS_MIN = 7.0`. Ein Test ruft jede Abbildungsfunktion auf und prüft
zwei Dinge: Keine sichtbare Textinstanz ist kleiner als `FS_MIN`, und die gezeichnete `tightbbox` ist höchstens so
breit wie das Ziel (3,4 bzw. 7,0 Zoll). Das Skript `jury/audit_protos.py` zeigt, wie das geht. Legenden stehen im
Panel oder werden durch direkte Beschriftung ersetzt, eine Legendenspalte rechts der Achsen gibt es nicht mehr.
Diese Spalte (M-F5, E-F5, P-F5) und zu lange Zeilenbeschriftungen links (E-T2, E-F3, E-F4) sind die häufigsten
Ursachen der Überschreitungen.

---

## 3 · Eine Bildsprache für alle neun Abbildungen

Die Entwürfe widersprechen sich in der Kodierung. Diese Regeln gelten für jede Abbildung und für die Karten:

1. **Farbe gehört den Managern und nichts anderem.** PM2 blau `#0072B2`, durchgezogen, Kreis; SM zinnober `#D55E00`,
   gestrichelt, Quadrat; legacy PM grün `#009E73`, gepunktet, **Raute** (M und P; E nimmt ein Dreieck, das mit der
   Seitenkodierung kollidiert). Die Beschriftung im Bild lautet „legacy PM“, im Gerüst heisst der Manager
   „legacy manager“.
   - **Basiswerte bekommen keine Farbe.** E färbt BTC blau, ETH orange und HYPE rosa (E-F1c, E-F2a, E-F6b). Blau und
     Orange bedeuten aber überall sonst PM2 und SM, und in Grau fallen ETH und HYPE auf denselben Wert (geprüft).
     Basiswerte stehen im Zeilen- oder Paneltitel oder in Kleinvielfachen. P nimmt für HYPE die Raute, die schon
     legacy PM gehört. Deshalb bekommen auch Basiswerte keine eigene Markerform.
   - Nicht-Managerdaten (ECDF, Histogramme, β-Geraden, Schätzer) sind schwarz oder grau. E-F3 (Balken > 0 blau), E-F4
     (≤ 63 Optionen blau), P-F3 (ECDF blau), P-F4 (Kästen blau) und die β-Linien in M/E/P-F6 werden umgefärbt.
2. **Seite:** ▲ = Maker-Kauf (long), ▼ = Maker-Verkauf (short), immer beide Wörter. In Karten steht **Verkauf oben**,
   Kauf unten (wie P-F1 und M-F6; es geht um das Kapital der Shorts, und T1 zeigt Shorts).
3. **Status:** gefüllt = registriert bzw. im H4-Panel, hohl = Sensitivität bzw. weggefallen, Raute hohl = behalten, aber
   ohne Panelzelle. Explorative Zeilen liegen grau hinterlegt (E).
4. **Urteilsgrammatik aus E für F2, F3, F4 und F6.** Die fette Kopfzeile lautet „registered: Schätzer [lo, hi] →
   rejected/not rejected“. Die Schwelle ist gestrichelt, der Ablehnungsbereich schraffiert (nur hinter der
   registrierten Zeile), rechts stehen n und die Clusterzahl. Eine Funktion `ruler(ax, h)` baut das, und der Bau
   bricht ab, wenn die gedruckte Regel nicht zu `rejected` passt.
5. **Karten:** eine Zahl je Zelle; positive Grössen in sequenziellem Grau (log), Schriftfarbe je nach Helligkeit
   schwarz oder weiss; × für Zellen unter 200 Fills (in F6 unter 20 Fills vor dem Ereignis). **Keine divergierenden
   Farbkarten.** P-F2 (Orange–Weiss–Blau) und M-F6 (`PuOr`) haben zwei Fehler: Ihre Enden fallen in Grau auf denselben
   Wert (geprüft: „−3,4k“ und „4,3k“ bzw. „+2“ und „−21“ sind gleich grau), und Orange bzw. Blau sind schon an SM und
   PM2 vergeben. Vorzeichenbehaftete Karten werden deshalb nach |Wert| grau schattiert, die seltenere Vorzeichenseite
   zusätzlich schraffiert, und das Vorzeichen steht immer als Zahl in der Zelle.
6. **Einheiten, eine je Grösse:**
   - Kapital aus Fills: „% of notional“ (Nominal = Menge × Index, wie „bp of notional“ in Paper 1 und die H1-Karte A).
     Das ist dasselbe wie % des Index je Kontrakt, aber nur eine der beiden Wendungen erscheint.
   - Kapital auf dem Engine-Gitter und im Referenzbuch: „% of forward“.
   - Kapitaländerung (Dosis, Parametersprung): **100·Δln K, „log-%“** in allen Abbildungen des Papiers, damit F5, die
     Dosiskarten in F6a und die Achse in F6b dieselbe Zahl zeigen und β direkt passt. Die Karten für X zeigen
     einfache Prozent.
   - USDC nur in T2 (Beträge eines Buchs) und in den CSV-Dateien.
7. **Kapitalskala:** `cividis` in T1, im GIF und im Keyframe, fest über alle Bilder (`fit_limits`). Isolinien
   verwenden dieselben Stufen in 3D, in den 2D-Karten und auf dem Farbbalken.
8. **Satz:** „≤ 2 d“ statt „<=2d“, Halbgeviertstrich in Spannen („2–7 d“), Formelzeichen als Mathtext
   („K_SM / K_PM2“ in E-F4 hat Unterstriche). Tick-Beschriftungen schwarz, nicht grau (P setzt 7-pt-Ticks in
   `GREY`, das ist im Druck zu schwach). Panelbuchstaben 8 pt fett.
9. **Tabellen:** eine CSV-Datei je Panel, `results/p2/fig_<slot>_<panel>.csv`, damit das Prüfskript Panel für Panel
   vergleichen kann (M). Das Prüfskript aus E (`scripts/p2_figure_check.py`: Kreuzzahl, Urteilszeile gegen
   `rejected`, gefüllte Ereignisse gegen `kept`) wird um die Messung aus Abschnitt 2 erweitert.

---

## 4 · Die Slots im Einzelnen

### T1 · Die Engine-Sicht der Oberfläche · P-T1 a/b ⊕ M-T1 c/d · 7,0 × 4,2

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | 7 | Die 2D-Karten „binding PM2 scenario / binding SM rule“ sind das stärkste neue Element aller Entwürfe und in Grau einwandfrei (Grauflächen, Punkte, Schraffur, Isolinien mit eigener Strichart). Die 3D-Panels ohne Isolinien tragen den Wert in Grau nur über Helligkeit. |
| E | – | Kein Prototyp. Die vorgeschlagenen Bodenkonturen hat M ausprobiert: mplot3d sortiert nach Tiefe, Boden und Linien verschwinden hinter der Fläche. |
| P | 8 | Isolinien auf der Fläche tragen die Zahl ohne Farbe (in Grau geprüft), die Kopfzahl „ATM 30 d short = 11,8 % of fwd“ ist die 5-Sekunden-Aussage. Der ATM-30-Tage-Knoten selbst ist verdeckt. |

**Aufbau.** Oben a (PM2) und b (SM) als 3D wie P: gleiche Sicht (elev 24, azim −128), gemeinsame `cividis`-Skala,
Isolinien 4/8/12/14 % inline beschriftet und auf dem Farbbalken markiert, Paneltitel mit Kopfzahl. Unten c und d wie
M als 2D-Karten mit derselben Call-Delta-Achse, bindende Regel als Grau/Punkt/Schraffur, dieselben Isolinien, dazu
die Bucketgrenzen von Paper 1 als dünne weisse Linien (Idee aus E, dort vom unsichtbaren Boden hierher verlegt).

**Auflagen.**

- Den ATM-30-Tage-Knoten als Punkt mit Beschriftung in a und c markieren, damit die Kopfzahl einen Ort hat.
- z-Achse „implied vol, %“, Farbbalken „capital per short contract, % of forward“. Ohne diese Trennung liest man
  die Höhe als Kapital (M, E, P einig).
- Die Bucketlinien gelten nur für |Δ| ≤ 60: Das Gitter enthält nur Knoten aus dem Geld, die Zellen 60–100 aus F1
  (Optionen im Geld) haben auf der Fläche kein Gegenstück. Das gehört in einen Satz der Bildunterschrift.
- Höhe von 4,3 auf 4,2 Zoll: Die Legenden von c und d stehen in einer Zeile unter beiden Karten, die
  Prototypfusszeile entfällt.
- M-T1 d bleibt drin, weil es den hellen Grat der SM-Fläche erklärt: Genau dort ist 15 % − OTM grösser als der Boden
  von 13 %.

### T2 · Was `get_margin` liefert und wie PM2 R bildet · P-T2 a/b ⊕ M-T2 c · 7,0 × 2,6

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | 6 | Panel c (Szenario-PnL des Straddles, bindendes Szenario umkreist, drei Kapitallinien) zeigt als einziges Panel den Netting-Mechanismus. In b kollidieren „2.14“ und „2.33“, der Legendenkreis überdeckt „on“, die x-Ticks in c sind um 90° gedreht und zum Teil leer. |
| E | 5 | Alle vier Bücher in USDC, aber die langen Zeilenbeschriftungen nehmen die halbe Breite. Gezeichnet 7,35 Zoll, also 6,7 pt im Satz; „1.19“ sitzt auf der Achslinie. |
| P | 8 | Ein Buch als Stapel R + (−V), rechts die Hanteln mit Pfeil C − net → R. Klar in 5 s. Fehler: „R 99k“ steht weiss auf der Schraffur, und der Pfeil beim 17.09. ist verdeckt. |

**Aufbau.** a (2,0 Zoll) wie P, b (2,1 Zoll) wie P, c (2,9 Zoll) wie M.

**Auflagen.**

- In a steht die R-Zahl ausserhalb des schmalen PM2-Balkens; die Buchvariante (H1-Liste gegen H0) steht im Paneltitel.
- In b ist der Rückwärtspfeil beim 17.09. (V > 0) als eigene Marke erkennbar, oder die Bildunterschrift nennt ihn.
- In c stehen die x-Ticks waagrecht, beschriftet werden nur 0,34 / 0,86 / 1 / 1,14 / 6. Darüber drei Gruppentitel:
  „tail ↓ (dampened)“, „core ±14 %“, „tail ↑“. Die Skew-Rauten werden grösser oder fallen weg.
- In c bleiben die drei Waagerechten direkt beschriftet (9,7 / 23,5 / 29,0). Die Bildunterschrift sagt, dass die
  PM2-Linie unter dem umkreisten Szenario liegt (Kontingenzen, IM-Faktor), sonst sieht es aus wie ein Fehler.
- Die Straddle-Beine kommen aus dem Referenzbuch (Strike = Forward, Verfall nächst 30 Tagen), nicht vom Gitterknoten
  Δ 0,5 (M- und P-Prototyp beide abweichend).

### F1 · Was ein Kontrakt kostet · P-F1 · 7,0 × 3,9

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | 5 | Eine Log-Grauskala für alle sechs Karten macht die Verkaufszeile zu einem schwarzen Block mit weissen Zahlen (Paper-1-Befund zu E3: druckt als schwarzer Block). Die Anatomie-Legende hat sieben Einträge, im Balken sichtbar sind zwei (Static Discount 0,05 pp, Kontingenzen 0,25 pp). |
| E | 4 | Gezeichnet 8,54 Zoll, also 5,7 pt im Satz. Die Basiswertfarben im Streifen c kollidieren mit PM2/SM, und die Dreiecke überlagern sich zu Klumpen. |
| P | 8 | PM2 je Zelle für alle drei Basiswerte, Grau je Zeile, schwarze Zahlen gut lesbar. Rechts der Streifen „÷ PM2“ mit SM-Quadraten, legacy-PM-Rauten und Medianstrich. In Grau einwandfrei. |

**Warum P.** Die Aussage von F1 ist ein Vergleich zwischen Managern. P macht ihn an einer Achse ablesbar, statt über
drei Karten hinweg Zahlen vergleichen zu lassen, und hat trotzdem eine Zahl je Zelle. Als einzige Fassung zeigt P auch
ETH und HYPE.

**Auflagen.**

- Die Kaufzeile heisst im Achsentitel „maker buys (long): capital ≈ premium“ (Falle aus E und P).
- „← PM2 cheaper →“ ist zweideutig. Richtig ist „PM2 cheaper →“ rechts von 1 und „SM cheaper ←“ links davon.
- Einheit nach Regel 6 („% of notional“). Die Kopfzeile über den Karten wird kürzer und nennt Fenster und
  Parameterstand („pooled over the PM2 window“), weil PM2 im Fenster um rund ein Drittel billiger wurde (F5).
- Die Anatomie aus M kommt in eine Zeile der Bildunterschrift und in `fig_f1_anatomy.csv`, nicht ins Bild.
- Daten aus `fig_edge_maps.csv`, Karten `pm2`, `sm_pm2win`, `pm_pm2win`, Zellwert `sum_K / sum_index`. Ein Test prüft,
  dass `fills` und `contracts` je Zelle in allen drei Karten gleich sind, sonst vergleicht der Streifen verschiedene
  Fills. Die Mediane je Fill aus `fig_capital_by_manager.csv` stehen nur in der CSV.

### F2 · Die Karte in zwei Nennern (H1) · E-F2 mit a als Kleinvielfache · 7,0 × 3,4

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | 4 | Die κ-Diagonalen sind gedanklich elegant, aber nicht in 5 s lesbar. Die Log-log-Achsen sind zu drei Vierteln leer, negative Edges hängen an einem Boden. Die Laufzeit als `cividis` auf 3-pt-Dreiecken ist in Grau nicht zu lesen. |
| E | 7 | Rang gegen Rang, darunter die Urteilsleiste, dazu c/d mit der mittleren Rangverschiebung nach Laufzeit und |Δ| je Seite. Das beantwortet `h1-reading` direkt. Minus: Basiswertfarben; das Histogramm in b braucht Ziehungen, die die Inferenz nicht schreibt. |
| P | 4 | Sechs Karten mit divergierender Skala: Die Kaufzeile explodiert („11.4k“, „−3.4k“), die Verkaufszeile ist fast weiss, beide Enden sind in Grau gleich. 173 graue Rangbänder bilden ein Haarlinienbüschel, und die fünf „besten“ Zellen sind nach der Punktschätzung gerahmt. |

**Aufbau.**

- **a** Rang je Nominal gegen Rang je PM2-Kapital als drei Kleinvielfache (BTC, ETH, HYPE, gemeinsame Achsen, gepoolte
  Ränge), ▲ Kauf hohl, ▼ Verkauf gefüllt, schwarz, Winkelhalbierende. Die Kleinvielfachen ersetzen die Basiswertfarben
  und zeigen sofort, ob ein Teil der Umordnung ein Niveauunterschied zwischen Basiswerten ist (Falle aus E).
- **b** Urteilsleiste für ρ nach Regel 4. Ein graues Histogramm nur dann, wenn die Inferenz die Replikationen schreibt
  (siehe Lücken).
- **c/d** mittlere Rangverschiebung nach Laufzeit bzw. |Δ|, ▲/▼ je Seite. Das ist eine deskriptive Umformung von
  `h1_cells.csv`, ρ wird nicht nachgerechnet.

**Auflagen.**

- Beide Achsen tragen „rank 1 = highest edge“, und die Richtung ist in beiden Achsen dieselbe.
- Rangintervalle nur für die zehn grössten |rank_shift|, als Kreuzbalken; keine 173 Linien.
- Die Karte in bp des Kapitals (P) steht als Tabelle in `fig_f2_cells.csv`. Der Text nennt die besten Zellen mit
  ihren Rangintervallen. P hat selbst gezeigt, warum die Karte nicht trägt: Kauf-OTM-Zellen haben die Prämie als
  Nenner.

### F3 · Der nächste Kontrakt im Buch (H2) · P-F3 a ⊕ E-F3 b · 3,4 × 3,6

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | – | Nur beschrieben. Idee: ratio getrennt danach, ob der Fill das bindende Szenario absichert. |
| E | 7 | Histogramm mit schraffierter Masse ≤ 0 und Überlaufzahlen, darunter der Forest mit Urteilszeile. Gezeichnet 3,96 Zoll, also 6,0 pt; Balken > 0 blau. |
| P | 7 | ECDF mit vier Bändern in Praktikersprache und dem Anteil je Band: eine Linie, graustufenfest, Median bei 0,5 direkt ablesbar. b hat keine x-Tick-Beschriftung, und ein Urteil fehlt. |

**Warum diese Kombination.** H2 testet einen Median. Die ECDF zeigt ihn als Schnitt mit der Höhe 0,5, dazu die
Anteile ≤ 0 und ≤ ½ ohne Balkenzählen. Der Forest aus E trägt das Urteil und die Sensitivitäten.

**Auflagen.**

- a: x-Achse von −1 bis 2, passend zu den Bins in `fig_h2_dist.csv`, Überläufe als Zahl am Rand. Linie schwarz,
  Bänder in drei Grautönen. Die Titelzeile der Bänder ist höchstens zwei Wörter pro Band breit.
- b: Zeilen „registered“, „next contract“, „maintenance margin“, „tape book“, dann grau hinterlegt als explorativ die
  Konten M3/M5/M8/M10 (ersetzt P-b) und, falls `hedges_worst` kommt, die Idee aus M als zwei Zeilen „hedges binding
  scenario / adds to it“. Zeilenbeschriftung höchstens 18 Zeichen, n innerhalb der 3,4 Zoll.
- Kopfzeile: „4 accounts, ETH and HYPE only, 20 000 sampled fills“ (Falle aus E: kein BTC).

### F4 · Was Netting wert ist (H3) · P-F4 b gebinnt ⊕ E-F4 b · 3,4 × 3,6

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | – | Nur beschrieben: Konto-Zeilen, dazu Faktor gegen Beine als Mechanik. |
| E | 7 | Histogramm gestapelt nach ≤ 63 und > 63 Optionen (kontrafaktisch schraffiert), Forest mit Urteil. Gezeichnet 3,94 Zoll, also 6,0 pt. |
| P | 6 | b (Faktor gegen Beine, Linie bei 63) ist der Mechanismus, aber als Wolke aus 1 943 Punkten, die als grauer Block druckt. P verbietet das in den eigenen Regeln. a mit blauen Kästen je Konto, kein Urteil. |

**Aufbau.**

- **a** K_SM/K_PM2 gegen Optionsbeine (log-log): Median je Bin als Linie mit p25–p75-Band, Bins mit mindestens 20
  Maker-Tagen. Der Bereich rechts von 63 Optionen ist hell schraffiert und direkt beschriftet: „SM counterfactual:
  1 431 of 1 943 maker-days“. Schwelle 2 gestrichelt.
- **b** Forest nach Regel 4, Ablehnungsbereich links von 2. Zeilen: registered, ≤ 63 options, MM, dann grau: legacy
  PM/PM2 (nur BTC- und ETH-Beine, n in der Zeile), Konten unter SM und Konten unter PM2.

**Auflagen.** Die Kästen je Konto aus P stehen in der CSV. Die Kopfzeile nennt „clusters: UTC days“ (Falle aus E).
F3 und F4 haben identische Panelhöhen und Rändermasse.

### F5 · Die Engine über die Zeit · P-F5 ⊕ Statusgrammatik aus E · 7,0 × 4,3

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | 6 | Vier Panels: Die Ereignisschiene mit acht Zeilen auf 0,9 Zoll ist gedrängt, und d braucht ein eigenes Panel für die Handvoll Zahlen, die P als Beschriftung in b unterbringt. Gezeichnet 7,69 Zoll, also 6,4 pt. In Grau lesbar. |
| E | 5 | Sieben Achsen, drei Straddle-Panels mit je einem OI-Streifen. Die Dosis-Beschriftungen in a überlagern sich („0.02“/„0.12“, „1.65“). Als einziger Entwurf zeigt E aber die überlappenden ±14-Tage-Fenster. |
| P | 8 | OI-Streifen mit PM2 unten (Wechsel sofort sichtbar), eine Zahl je Ereignis statt eines eigenen Panels, rechts direkt beschriftete Linien (SM 29,6 %, legacy PM 19,7 %, PM2 10,0 %). In Grau einwandfrei. |

**Auflagen.**

- **Fehler in P-a:** Im HYPE-Streifen fehlt der SM-Anteil (12 bis 16 % von Juni bis September 2026).
  `manager_oi_share.csv` hat für HYPE `pm = NaN`, der Stapel bricht dort ab. `fillna(0)` vor dem Stapeln.
- b nach der Grammatik aus E: ● im H4-Panel, ◇ behalten ohne Panelzelle, ○ weggefallen. Jede Zeile der
  Parameterzeitlinie als kleiner grauer Strich (Placebo-Abstand), die ±14-Tage-Fenster als hellgraue Balken auf der
  Schiene, damit die Überlappungen im Januar und im Mai sichtbar sind, ohne c zu überdecken.
- Zahlen in b in log-% (Regel 6). SM-Zeilen entfallen, die Bildunterschrift nennt die SM-Änderungen als reine
  Perp-Änderungen.
- Legendenspalte rechts streichen: a und b bekommen eine Zeile über dem Panel, c ist direkt beschriftet. Damit
  passen die 7,0 Zoll.
- Das PM2-Ereignis vom 12./13.06.2025 erscheint in b als grauer Strich ohne Status (fehlt in `events.csv`).
- Die Straddle-Reihen für ETH und HYPE stehen in der CSV; ihre Sprünge stehen als Zahlen in b.

### F6 · Der Preis des Kapitals (H4) · M-F6 a ⊕ E-F6 a (FWL) ⊕ E-F6 c · 7,0 × 4,2

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | 7 | Die echten Dosiskarten (drei BTC-Ereignisse mit drei Mechanismen) zeigen die Variation, die β mit Tag-×-Basiswert-Effekten identifiziert: quer über die Zellen eines Ereignisses. Kein anderer Entwurf zeigt sie. b und c sind gestaucht, `PuOr` fällt in Grau zusammen, die y-Ticks des Placebo-Histogramms sind Bruchzahlen (2,5, 7,5). |
| E | 6 | Das FWL-Bild (Gerade mit genau der Steigung β) ist die richtige Form für b, und die Prüfliste über c zeigt beide Kriterien. β je Ereignis in b schätzt die Inferenz aber nicht. Basiswertfarben; gezeichnet 7,54 Zoll. |
| P | 5 | Punktwolke mit Dezilen, deren Steigung ohne Fixeffekte nicht β ist; in b überlagern sich die Datumsbeschriftungen. |

**Aufbau.** Links a als 2 × 3 Karten wie M (Verkauf oben), rechts übereinander b und c.

- **a** Dosis je Zelle in log-%, Grau nach |Dosis|, positive Dosen (nur 08.01.2026) schraffiert, Vorzeichen in jeder
  Zelle, × unter 20 Fills. Die Spaltentitel nennen den Mechanismus (M).
- **b** Das FWL-Bild aus E: 20 gleich besetzte Bins der residualisierten Grössen, Gerade mit Steigung β, schwarz,
  Achsenzusatz „< 0: capital got cheaper“. **Nur mit den Bins aus der Inferenz.** Ohne sie zeigt b die Terzile aus
  `fig_h4_events.csv` *ohne* β-Gerade (E), und die Achse sagt „raw, no fixed effects“.
- **c** Placebo-Histogramm mit ganzzahligen Ticks, P95 gestrichelt, β durchgezogen schwarz, darüber die Prüfliste
  aus E in zwei kurzen Zeilen plus Urteil.

Die Fussnote, dass β fast nur aus Lockerungen identifiziert ist, steht in der Bildunterschrift; a macht es sichtbar.

### A1 · Trifft der Nachbau die Chain? · M-A1 a ⊕ P-A1 b · 7,0 × 2,5

| Entwurf | Note | Gestaltung |
|---|---|---|
| M | 8 | Streifen je Basiswert × Manager, Medianstrich, n je Zeile, exakte Nullen am Rand. |
| E | 5 | IM und MM als Doppelbalken verdoppeln die Tinte. Die Fusszeile überlagert die x-Beschriftung von b, die abgeschnitten ist. |
| P | 7 | b (Abweichung gegen Beine mit „largest miss 0.05 USDC on K up to 19.5 M USDC“) ist die beste Buchdarstellung. In a fehlt der Median, obwohl die registrierte Schwelle am Median hängt. |

**Auflagen.** Der Randstreifen „exact“ ist beschriftet (P), die Schwellen sind direkt an der Linie beschriftet
(„median bound 0.1 %“, „p95 bound 1 %“), MM steht nur in der CSV. Die Bildunterschrift trägt den Satz aus P:
Der Nachbau trifft die Chain, die off-chain API rechnet PM2 mit pauschal 2 % Diskont.

---

## 5 · README und X

### GIF der Kapitalfläche

Das bestehende GIF (`BTC_capital_short_2026-08-14_2026-08-27.gif`) zeigt die Probleme: 960 × 540, Ticks etwa 9 px,
beide Flächen klein, Einheit bp, und der Farbbalken hat sichtbare Stufen (GIF-Quantisierung von `cividis`).

**Wahl.** Das Konzept aus P und M: eine grosse 3D-Fläche, nur PM2, im Aussehen von T1. SM erscheint nur als Zahl in
der Ecke, weil seine Fläche einfarbig ist (M). Darunter der Referenz-Straddle mit Cursor. Die Ehrlichkeitsregeln
kommen aus E: feste Skala, graue Verfälle bei altem Feed statt Interpolation, Plakette „stale feed“,
`results/p2/gif_frames.csv`, statisches Endbild als PNG. E schlägt für X eine 2D-Karte vor. Das lehne ich ab: Die
bewegte Fläche ist das Wiedererkennungsbild von T1, und was man auf 600 px lesen muss, steht ohnehin im Banner.

- Takt wie M: wöchentlich, dazu an jedem behaltenen BTC-Ereignis drei Tagesbilder mit 1,5 s Halt und Banner
  („20 Aug 2026 · parameter change · grid ±17 % → ±14 % · straddle −23 %“). 4 fps. Tägliche Bilder mit 12 fps (E)
  flackern, weil der Markt die Fläche jeden Tag bewegt.
- 1200 × 675 als ein Master für README und X. Banner und Datum mindestens 32 px, Achsen mindestens 22 px.
- Höchstens zwei Isolinien (8 % und 12 %), weil Konturen zwischen Wochenbildern springen.
- Globale 256-Farben-Palette statt 64 (P), gegen die Stufen. Für X zusätzlich MP4 (M: `write_mp4`), weil X GIFs
  ohnehin umkodiert.

### Social-Karten 1600 × 900

1. **„One short BTC straddle. Three margin engines.“** Die M-Karte als Träger: die drei grossen Zahlen 30/20/10 %
   mit Strichmuster darunter sind die stärkste Einzelaussage aller Karten. Dazu die Stufenbeschriftungen aus P an
   der PM2-Linie (−10 %, −8 %, −23 %) und die Zeile „capital for a hypothetical book, not a balance“ (M).
   Die P-Karte 1 entfällt: Der Titel „cut PM2 capital by 35%“ ist rechts abgeschnitten, und 35 % lässt sich im Bild
   nicht nachprüfen, weil die Linie von 14,4 auf 10,0 fällt, also um 31 %.
2. **P-Karte 2 (Straddle gegen ein Bein)** mit einem genaueren Titel. „Almost free“ untertreibt, denn das zweite
   Bein senkt das Kapital. Vorschlag: „Under PM2 a short straddle needs less capital than one short call.“ Beide
   Balken kommen aus demselben Referenz-Straddle (Beine einzeln gerechnet), nicht aus Gitterknoten und gelistetem
   Verfall gemischt.
3. **Nach H3: P-Karte 3 „PM2 discounts the book, not the contract“**, beide Balken grau bzw. schwarz schraffiert,
   weil beide Quotienten sind und keiner ein Manager; mit Intervall und n. Trägt H3 den Titel nicht, ersetzt die
   M-Karte 3 sie („One parameter change, one fingerprint“, Dosiskarte 20.08.2026 Verkaufsseite). Diese Karte braucht
   keine Hypothese.

Für alle Karten gilt: Schrift mindestens 24 px (auf 600 px Breite 9 px). Titel und Achsenbeschriftung liegen
innerhalb von 1600 × 900. P-Karte 1 und der Keyframe (`social_t1_keyframe.png`, Farbbalkentitel) sind rechts
abgeschnitten. Jede Zahl im Titel lässt sich im Bild selbst ablesen.

---

## 6 · Lücken

**Die Lücke, die kein Entwurf schliesst: die Zeit in F1 und F2.** Beide Karten poolen über das ganze PM2-Fenster,
in dem das PM2-Kapital des Referenzbuchs von 14,4 auf 10,0 % gefallen ist (F5). Der Nenner von H1 mischt damit
Parameterregime. Kein Entwurf zeigt das im Bild, nur P nennt es als Falle. Mindestens nennt die Kopfzeile von F1
und F2 das Fenster. Besser wäre eine Spalte „letzte 30 Tage“ in `fig_f1_*.csv`, dazu ein Satz, ob sich die Rangfolge
der F1-Zellen zwischen den Regimen hält (deskriptiv, keine neue Teststatistik).

Weitere Lücken, nach Dringlichkeit:

1. **FWL-Bins für F6b fehlen in der Inferenz** (`fig_h4_events.csv` hat nur Terzile mit rohen Mitteln). Ohne sie
   hat F6 keine Gerade mit Steigung β.
2. **Keine Replikationsverteilung von ρ** (`h1.json` hat `stat, lo, hi`, keine Ziehungen). F2b kommt ohne sie aus,
   ein Histogramm wäre aber die einzige Form, in der man die Schiefe des Intervalls sieht.
3. **Engine-Hilfen fehlen im Paket:** `figdata_p2.binding_rule` (T1 c/d) und `pm2_scenarios` (T2 c) stehen nur im
   Prototyp `proto_mechanismus.py`. Sie müssen mit einem Test auf die Summe umziehen (die Zerlegung trifft am
   T1-Knoten das Gitterkapital exakt).
4. **Einzelbeine des Referenz-Straddles** (`K_<m>_call`, `K_<m>_put`) für T2 c und Karte 2.
5. **`hedges_worst` in `books.py`** für die Mechanik-Zeilen in F3 (optional, explorativ).
6. **`figstyle` für Paper 2:** `FS_MIN`, die Manager-Marker (Raute für legacy PM) und die Seitenzeichen als Konstanten,
   dazu der Breiten- und Schrifttest aus Abschnitt 2. Heute definiert jede Linse ihre eigenen Marker.
7. **Einheitenentscheid** „% of notional“ und „log-%“ (Regel 6) muss auch im Text von `main.tex` gelten. Die
   Bildunterschrift von F1 im Gerüst sagt noch „USDC“ und „each panel on its own scale“, die von F2 noch „lines
   connect the rank of each cell“. Beides wird ersetzt.
8. **Ereignis 12./13.06.2025** fehlt in `events.csv` (F5 b).
9. **HYPE in T1, F1-Anatomie und F6a** gibt es nur als CSV. Das ist gewollt, aber jede Bildunterschrift muss es sagen.

---

## 7 · Wo ich mit dem Referee Streit erwarte

- **F2:** Der Referee könnte die Praktiker-Karte (bp des Kapitals je Zelle) im Bild wollen, weil sie sagt, *wo*
  Kapital sich verzinst. Meine Antwort: nicht in dieser Farbkarte. Denkbar ist höchstens eine graue Karte nur der
  Verkaufszeile. Die Kaufzeile hat die Prämie als Nenner und sprengt jede Skala.
- **F6:** Ohne FWL-Bins würde ich b lieber leer lassen (nur Leiste für β mit Intervall) als eine Gerade über rohe
  Terzile zu legen.
- **Einheit der Dosis:** Der Praktiker wird Prozent statt log-% wollen. Im Papier halte ich log-% für richtig, weil β
  in dieser Einheit registriert ist. Die Karten zeigen Prozent.
- **T1-Höhe 4,2 Zoll** ist viel für eine Abbildung vor den Ergebnissen. Wer kürzen will, streicht d, nicht c.

## Dateien

- Dieses Urteil: `docs/paper2/entwuerfe/jury_gestaltung.md`
- Messung: `data/p2/fig_proto/jury/audit_protos.py`, `data/p2/fig_proto/jury/audit_protos.csv`
