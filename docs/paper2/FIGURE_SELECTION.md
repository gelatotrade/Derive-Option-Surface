# Abbildungen Paper 2: Wahl und Bauanweisung

25.09.2026. Drei unabhängige Entwurfssätze mit je neun Slots (Linsen Mechanismus, Empirie, Praktiker; unter
`docs/paper2/entwuerfe/`, Prototypen unter `data/p2/fig_proto/`), danach zwei Juroren mit verschiedenen Linsen: ein
Referee, der gegen die Daten nachgerechnet hat (`jury_referee.md`), und eine Gestaltungsprüfung, die Breite und
kleinste Schrift nach dem Einsetzen gemessen und alle Prototypen in Graustufen angesehen hat (`jury_gestaltung.md`,
Messung `data/p2/fig_proto/jury/audit_protos.csv`). Diese Datei entscheidet jeden Streitpunkt und ist die
**verbindliche Vorgabe für den Bau** von `derive_surface/figures_p2.py`, `figdata_p2.py`, `scripts/p2_figure_check.py`,
der Social-Karten und des GIF. Wo ein Entwurf oder ein Juror etwas anderes sagt, gilt diese Datei.

Kürzel: M = Mechanismus, E = Empirie, P = Praktiker. Zahlen sind am Pilotschnitt 17.09.2026 nachgerechnet.

**Ergebnisblind.** Die Wahl ist getroffen, ohne die Urteile zu H1 bis H4 zu kennen. Aus `h1.json` bis `h4.json`,
`sens_*.csv`, `sensitivity*.json` und `fig_h*.csv` wurden bei der Synthese nur Schema, Schlüssel und Strukturzahlen
gelesen (n, Tage, Konten, Zellen, zulässige Placebo-Tage, Regeltexte), nie `stat, lo, hi, rejected, p` oder die
Kriterien. Offenlegung: Beim Prüfen der Bin-Struktur von `fig_h2_dist.csv` wurde die Besetzung der beiden offenen
Randklassen der registrierten Variante sichtbar; keine Entscheidung hängt daran, das Fenster [−1; 2] war durch die
Bins der Inferenz vorher festgelegt. Der Referee kannte das Vorzeichen der H4-Schätzung (unmaskierte Felder `se`,
`t`, `fe.beta_direct_solve`); die Wahl für F6 gilt für beide Vorzeichen. Kein Titel, keine Achse und keine
Beschriftung hängt vom Ausgang eines Tests ab.

---

## 1 · Die Wahl in einer Tabelle

| Slot | Frage | Quelle | Grösse (Zoll) | Test |
|---|---|---|---|---|
| T1 | Welches Kapital bindet ein Short an jedem Punkt der Oberfläche, und welche Regel setzt es? | P-T1 a/b ⊕ M-T1 c/d | 7,0 × 4,2 | |
| T2 | Was liefert `get_margin`, und wie bewertet PM2 ein Buch? | P-T2 a/b ⊕ M-T2 c (neu auf dem Referenz-Straddle) | 7,0 × 2,6 | |
| F1 | Was kostet ein Kontrakt je Zelle, und was kosten dieselben Fills unter SM und Legacy-PM? | P-F1 mit den Zahlen von E und der Regime-Aufteilung des Referee | 7,0 × 3,9 | |
| F2 | Ordnet der Kapitalnenner die Karte um? | P-F2 (Karten, Rang gegen Rang) in der Graukodierung der Gestaltung, Urteilsleiste von E, Vorzeichenlinien des Referee | 7,0 × 4,4 | H1 |
| F3 | Was kostet der nächste Kontrakt im Buch eines dominanten Makers? | P-F3 a ⊕ E-F3 b | 3,4 × 4,0 | H2 |
| F4 | Was ist Netting wert? | P-F4 b gebinnt ⊕ E-F4 b | 3,4 × 4,0 | H3 |
| F5 | Wie hat sich die Engine über die Zeit bewegt, und welche Ereignisse tragen H4? | P-F5 ⊕ Statusgrammatik E ⊕ Placebo-Band des Referee | 7,0 × 4,3 | |
| F6 | Folgt der Halbspread dem Preis des Kapitals? | Kombination des Referee: Dosis-Streifen, FWL-Bild E, Placebo mit Prüfliste E, kleiner Forest | 7,0 × 4,2 | H4 |
| A1 | Trifft der Nachbau die Chain? | M-A1 a ⊕ P-A1 b, p95-Marke von E | 7,0 × 2,5 | |
| GIF | Wie bewegt sich die PM2-Kapitalfläche über 15 Monate? | 3D wie T1 (M, P), Takt und Haltebilder M, Ehrlichkeitsregeln E | 1200 × 675 px | |
| Karte 1 | Ein Straddle, drei Engines | M-Karte ⊕ Stufen von P | 1600 × 900 px | |
| Karte 2 | Warum Netting wirkt | P-Karte 2 mit neuem Titel, beide Balken aus demselben Straddle | 1600 × 900 px | |
| Karte 3 | Vier registrierte Urteile | Urteilskarte in der Grammatik von E | 1600 × 900 px | H1 bis H4 |

Neun Abbildungen im PDF: T1, T2, F1 bis F6 im Hauptteil, A1 im Anhang. Einzige 3D-Abbildung ist T1. F3 und F4 bleiben
einspaltige `figure` mit identischem Raster, damit sie nebeneinander oben auf einer Seite stehen; der gemeinsame
`figure*` aus E würde einen Slot verschenken.

---

## 2 · Worin die Juroren übereinstimmten

| Slot | Beide | Warum |
|---|---|---|
| T1 | 3D-Paare PM2 und SM auf einer gemeinsamen `cividis`-Skala, darunter die 2D-Karten „bindende Regel“ aus M | Die Fläche allein sagt nicht, warum sie so aussieht; eine Bodenprojektion im 3D-Achsensystem scheitert an der Tiefensortierung von mplot3d (M hat es ausprobiert). |
| T2 | P a (lineare Balken R und −V) und P b (Hanteln), dazu M c, neu gerechnet auf dem Referenz-Straddle | E a ist ein Dotplot auf log-USDC, dort ist der Markerabstand nicht V. M c ist die einzige Stelle, an der man die Engine ein Buch bewerten sieht. |
| F3 | ECDF aus P, Forest mit Urteilsleiste aus E | Die ECDF liest den Median direkt bei 0,5 ab und passt zu den Bins von `fig_h2_dist.csv` ([−1; 2] mit offenen Rändern); das Histogramm von E verlangt [−2; 3], das die Tabelle nicht hat. |
| F5 | P als Träger, Statusgrammatik aus E, Fehler im HYPE-Streifen beheben, M d entfällt | P trägt die Zahlen, E macht die H4-Auswahl prüfbar; M d zeigt dieselben Zahlen ein zweites Mal. |
| A1 | Streifen je Basiswert × Manager mit Median und n, dazu Fehler gegen Buchbreite (P b) | Enthält alle registrierten Grössen und zeigt, dass der Fehler nicht mit der Buchgrösse wächst. |
| Urteilsgrammatik | E für F2, F3, F4, F6 | Vier Tests, eine Lesart; die Urteilszeile wird aus der Regel neu gebildet und muss `rejected` treffen. |
| Messung | `FS_MIN = 7.0`, Breitentest, kein `bbox tight` | Die Überschreitungen der Prototypen (bis 8,5 Zoll gezeichnet, 5,7 pt im Satz) kommen aus Legendenspalten und langen Zeilenbeschriftungen. |
| GIF | 3D-Fläche nur PM2, wöchentlich mit Haltebildern an Ereignissen, Zeitstreifen, Ehrlichkeitsregeln aus E | Der 2D-Vorschlag von E für X wird verworfen: die bewegte Fläche ist das Wiedererkennungsbild von T1. |
| Karte 1 | M-Karte „One short BTC straddle. Three margin engines.“ | Die drei grossen Zahlen sind die stärkste Einzelaussage aller Karten und brauchen keine Hypothese. |

---

## 3 · Worin sie auseinandergingen, und wie entschieden wurde

**F1: E gegen P.** Der Referee wollte E (BTC-Karten für drei Manager × zwei Seiten, Streifen aller 173 Zellen), weil
die Spezifikation das Kapital *nach Manager* verlangt. Die Gestaltung wollte P (PM2-Karten für alle drei Basiswerte,
Managervergleich als Streifen), weil E gezeichnet 8,54 Zoll breit ist (5,7 pt im Satz) und neun Karten den Vergleich
über Zahlen quer durch das Bild erzwingen. Entschieden: **P als Aufbau mit dem Inhalt von E und der Regime-Aufteilung
des Referee.** Der Managervergleich steht je Zelle als Punkt im Streifen, auf allen drei Basiswerten, die Zahlen in den
Karten haben zwei signifikante Stellen (E). Die Anatomie-Spalte von M entfällt ganz: Sie zeigt einen Kontrakt aus dem
letzten Parameterregime neben Karten, die über vier Regime mitteln, und T2 c trägt den Mechanismus bereits.

**F2: Karten ja oder nein.** Der Referee wollte die Karte des Edge je PM2-Kapital im Bild, weil sie Beitrag 1 der
Spezifikation ist. Die Gestaltung lehnte P-F2 ab, weil die divergierende Skala in Graustufen an beiden Enden gleich grau
wird, Orange und Blau schon den Managern gehören und die Kaufzeile jede gemeinsame Skala sprengt. Entschieden: **Die
Karten bleiben, in der Kodierung der Gestaltung.** Grau nach |Wert| auf logarithmischer Skala *je Zeile* (die
Kaufzeile ist eine Rendite auf die Prämie und bekommt ihre eigene), negative Zellen schraffiert, das Vorzeichen immer als
Zahl. Das Rang-Rang-Bild wird ein einziges gepooltes Panel ohne Basiswertkodierung; die Frage der Gestaltung, ob ein
Teil der Umordnung ein Niveauunterschied zwischen Basiswerten ist, beantworten die explorativen Forest-Zeilen „ρ
innerhalb BTC/ETH/HYPE“ (liegen in `sensitivity.json`, `g_by_ccy`). Die mittleren Rangverschiebungen von E (c/d)
gehen in `fig_f2_shift.csv` und in den Text. Die fünf gerahmten „besten“ Zellen von P entfallen, weil sie nicht vorab
definiert sind. Rangintervalle nur für die zehn grössten |rank_shift| (Gestaltung), nicht 173 Haarlinien.

**F4 Panel a: Histogramm oder Buchbreite.** Der Referee wollte das Histogramm von E (gestapelt ≤ 63 / > 63
Optionen), liess die Buchbreite aber zu, „falls die Gestaltung einen Platz findet“. Die Gestaltung hat ihn gefunden.
Entschieden: **K_SM/K_PM2 gegen Optionsbeine als Median je Bin mit Quartilsband.** Die Grenze von 63 Optionen liegt
dort als echte Achsenposition und nicht als Farbstapel, der kontrafaktische Bereich ist schraffiert und beziffert. Die
Verteilung als solche trägt der Forest (registrierte Zeile, ≤ 63 und > 63 als eigene Zeilen).

**F6 Panel a: Dosiskarten oder Dosis-Streifen.** Die Gestaltung wollte die drei echten BTC-Dosiskarten von M, weil
sie die Variation quer über die Zellen zeigen, die β identifiziert. Der Referee wollte einen Streifen aller 13
Panel-Ereignisse, weil die Karten 3 von 13 Ereignissen zeigen und ihr Kreuz der Vor-Regel (≥ 20 Fills vor dem
Ereignis) statt der Panelregel (je 20 vor und nach) folgt. Entschieden: **Streifen.** Er zeigt die Stütze der
Schätzung vollständig: Median der Dosis über die 475 Paare −0,63 log-%, 11,2 % der Paare positiv (höchstens
+2,2 log-%), 44,4 % mit |Dosis| < 1 log-%, 48,6 % unter −1 log-%. Die Karte vom 20.08.2026 bleibt als Reserve-Social-Karte. Das kleine
Forest-Panel d des Referee bleibt, aber ohne die Zeile „ohne Ausreisserzellen“: Die einzige Zelle über der Schwelle
(HYPE Kauf 00-10/2-7d, Dosis −1,648) liegt nicht im Panel (`rows_dropped_real_panel = 0`), die Zeile wäre mit der
registrierten identisch.

**T1 Iso-Linien.** M und der Referee: 5/8/11/14 % auf den 2D-Karten; P und die Gestaltung: 4/8/12/14 % auf der
3D-Fläche. Entschieden: **4, 8, 12 und 14 % in allen vier Panels und auf dem Farbbalken.** Gleiche Abstände bis 12 %,
dazu 14 % zwischen dem SM-Boden von 13 % und dem Maximum von 15 %, damit der helle Grat der SM-Fläche eine Linie hat.

**F5: wo die ±14-Tage-Fenster liegen.** E und Referee: grau hinterlegt in Panel c. Gestaltung: auf der
Ereignisschiene. Entschieden: **auf der Schiene**, weil c nur BTC zeigt und die Fenster je Basiswert gelten.

**Einheit der Kapitaländerung.** P und Referee schreiben Prozent, die Gestaltung log-%. Entschieden: **log-%
(100·Δln K) überall im Papier**, weil β in dieser Einheit registriert ist und F5 b, F6 a und F6 b dann dieselbe Zahl
zeigen. GIF und Karten zeigen einfache Prozent.

**A1: MM im Bücherpanel.** Der Referee schreibt in der Wahl „IM gefüllt, MM hohl“, in den Auflagen „MM nur in der
CSV“. Entschieden: **MM nur in der CSV**, in beiden Panels.

**Karte 2.** Referee: Standbild der Fläche. Gestaltung: P-Karte 2 (Straddle gegen ein Bein) mit neuem Titel. Beide
stellen dieselbe Bedingung an P-Karte 2 (beide Balken aus demselben Referenz-Straddle, kein „almost free“).
Entschieden: **P-Karte 2 unter dieser Bedingung.** Das Standbild wird Endbild und Poster des GIF im README.

**Karte 3.** Gestaltung: P-Karte 3 „PM2 discounts the book, not the contract“ nach H3, sonst die Fingerabdruck-Karte
von M. Referee: Urteilskarte H1 bis H4. Entschieden: **Urteilskarte.** P-Karte 3 vergleicht einen über Regime gepoolten
Zellmedian mit einem Median über Maker-Tage, also zwei Populationen, und ihr Satz kippt im letzten Regime (Abschnitt 4).
Die Urteilskarte ist vom Ausgang unabhängig gestaltet. Die Fingerabdruck-Karte ist Reserve.

**Basiswerte kodieren.** Referee und E kodieren Basiswerte mit Form oder Farbe. Die Gestaltung verbietet beides, weil
Blau und Orange den Managern gehören, ETH und HYPE in Grau zusammenfallen und die Raute schon Legacy-PM ist.
Entschieden: **Basiswerte nur über Panel, Zeile oder Beschriftung**, nie über Farbe oder Markerform.

**Neue Zeichenkonflikte, die kein Juror bemerkt hat.** M-T2 c kodiert Vol-Zustände mit ▲/▼, die für die Seite
reserviert sind, und zeichnet „Beine getrennt“ gepunktet, also in der Strichart von Legacy-PM. E kodiert
Sensitivitätszeilen mit offener Raute und die Gestaltung „behalten ohne Panelzelle“ mit hohler Raute, beides die Form
von Legacy-PM. Aufgelöst in Abschnitt 6.2.

---

## 4 · Die Lücke, die kein Entwurf abgedeckt hat

**Alle Karten und Verteilungen poolen über vier Parameterregime.** Im PM2-Fenster ist das PM2-Kapital des
BTC-Referenz-Straddles von 14,41 auf 10,03 % des Forwards gefallen, allein durch Parameter um 35,0 % (−43,1 log-%).
Kein Entwurf zeigt das in F1 bis F4. Die Gestaltung hat es für F1 und F2 als Lücke benannt, der Referee hat nachgerechnet,
dass die Kernaussage von E und P zum Einzelkontrakt im letzten Regime kippt. Hier nachgerechnet (Verkaufs-Fills,
Verhältnis der Summen, Zellen ab 200 Fills je Regime):

| | bis 23.01.2026 | 23.01. bis 24.05.2026 | 24.05. bis 20.08.2026 | ab 20.08.2026 |
|---|---|---|---|---|
| Anteil der Verkaufs-Fills mit K_SM < K_PM2 | 82,5 % | 69,2 % | 54,1 % | 15,4 % |
| Median SM/PM2 der Verkaufszellen BTC | 0,91 (20 Zellen) | 0,91 (19) | 0,97 (19) | 1,40 (6) |
| dasselbe ETH | 0,88 (31) | 0,88 (24) | 0,93 (27) | 1,14 (18) |
| dasselbe HYPE | keine Zelle | 0,72 (15) | 1,06 (14) | 1,44 (1) |

Käufe liegen für BTC und ETH in allen Regimen bei 1,00 (SM verlangt die Prämie), für HYPE bei 0,87 bis 1,00. Gepoolt
stimmt „für den einzelnen Short ist PM2 nicht billiger als SM“ (Median 0,94 / 0,90 / 0,88); seit dem 20.08.2026
verlangt SM in 84,6 % der Verkaufs-Fills mindestens so viel wie PM2. Auch
H3 steigt dadurch mechanisch, weil derselbe Nenner billiger wurde. Daraus folgen drei Bauvorgaben:

1. **Ein festes Regime-Raster** (Abschnitt 6.6) für alle Aufteilungen: R1 bis R4, getrennt durch die PM2-Ereignisse vom
   23.01.2026, 24.05.2026 und 20.08.2026.
2. **F1:** hohle Zeichen für R4 im Streifen und `fig_f1_regimes.csv` mit allen vier Regimen.
3. **F3 und F4:** explorative Forest-Zeilen R1 bis R4 (die Inferenz muss sie schreiben, Abschnitt 10). F2 nennt das
   Pooling in der Kopfzeile; ob die Rangfolge der F1-Zellen zwischen den Regimen hält, sagt ein Satz im Text aus
   `fig_f1_regimes.csv`.

### Lückencheck

| Anforderung | Wo abgedeckt |
|---|---|
| Spezifikation T1: BTC-Vol-Fläche in 3D, gefärbt mit PM2-Kapital je Short, daneben SM | T1 a/b |
| Spezifikation T2: net = C + V − R, Auflösung 11 gegen 1,2 | T2 a/b |
| Spezifikation F1: Kapital je Kontrakt nach Manager, Kauf und Verkauf | F1 (PM2 als Zahl, SM und Legacy-PM als Quotient je Zelle); absolute SM- und Legacy-Werte in `fig_f1_a.csv` |
| Spezifikation F2: Nominal gegen PM2-Kapital je Basiswert und Seite, mit Rangstreuung | F2 a (Karte je PM2-Kapital), b (Rang gegen Rang mit Rangintervallen); die Nominal-Karte ist die Karte von Paper 1, Verweis in der Caption |
| Spezifikation F3: Verteilung ΔK/K_Einzel, Anteil ≤ 0 | F3 a |
| Spezifikation F4: K_SM/K_PM2 über Maker-Tage, Legacy-PM daneben | F4 a/b; Legacy-PM als registrierte Sensitivitätszeile, nicht als eigene Verteilung |
| Spezifikation F5: OI-Anteile, Ereignisse, Referenzbuch | F5 a/b/c |
| Spezifikation F6: Dosis-Wirkung und Placebo | F6 b/c, dazu a (Stütze) und d |
| Jeder registrierte Test hat Schätzer, Intervall, Schwelle, Regel, n und Cluster im Bild | F2 c, F3 b, F4 b, F6 c/d |
| Kalenderachse | F5, GIF |
| Pooling über Parameterregime | F1 Streifen (R4 hohl), F3 b und F4 b (R1 bis R4), Kopfzeilen F1 und F2 |
| Strukturelle Untergrenze von H1 (Vorzeichen) | F2 b Vorzeichenlinien, F2 c Band „sign pattern alone“ und Zeilen innerhalb Vorzeichen |
| K_SM an 1 431 von 1 943 Maker-Tagen kontrafaktisch | F4 a schraffierter Bereich, F4 b Zeilen ≤ 63 und > 63 |
| H2 ohne BTC, M3 = einziges HYPE-Konto | F3 Kopfzeile, Zeile „M3 (HYPE)“ |
| Stütze von H4 (Dosen fast nur ≤ 0, Hälfte nahe 0) | F6 a |
| Überlappende H4-Fenster (6 527 Fills in zwei Fenstern) | F5 b Fensterbalken, F6 Kopfzeile, Caption |
| Placebo-Stütze (ETH PM2 nur 10 zulässige Tage) | F5 b Placebo-Band, F6 c Zeile |
| Chain- gegen API-Semantik (pauschal 2 %) | Caption T1 und A1 |
| Edge ist ein Fluss je Fill, Kapital ein Bestand | Caption F2, Zeile „per holding time“ im Forest |
| Wer mit leerem Buch startet, zahlt den Preis aus F1 | Caption F3 |
| Höchstens eine 3D-Abbildung | nur T1 (zwei 3D-Achsen in einer Abbildung) |
| Jede Zahl als Tabelle | `results/p2/fig_<slot>_<panel>.csv` (Abschnitt 6.7) |
| Konten nur als Rang-Label | M1 bis M10, nie Adresse oder Hash im Bild |

Bewusst nicht im Bild: MM-Varianten ausser als Forest-Zeile, API-Semantik, ETH- und HYPE-Oberflächen (nur CSV), die
Konten einzeln in F4 (CSV), die Mechanik-Zeilen `hedges_worst` aus M (wären eine neue, nicht registrierte Rechnung).

---

## 5 · Was die Nachrechnung an Entwürfen und Juroren korrigiert hat

| Behauptung | Nachgerechnet | Folge |
|---|---|---|
| Änderung vom 12./13.06.2025 fehlt in `events.csv` (P, Gestaltung) | `MarginParamsUpdated` am 12.06.2025 um 22:20:01 UTC, vor dem Fensterbeginn 23:00 UTC; kein H4-Ereignis (Referee richtig) | erscheint in F5 b nur als grauer Zeitlinienstrich |
| HYPE-SM-Anteil 12 bis 16 % (Gestaltung) gegen 7 bis 49 % (Referee) | beide richtig: 12 bis 16 % von Juni bis September 2026, 7 bis 49 % über 12/2025 bis 09/2026; `pm` ist bei HYPE NaN | `fillna(0)` vor dem Stapeln |
| „−V ist bei beiden Managern gleich“ (P) | −496 914 (SM) gegen −496 859 (PM2) | jede Zeile zeichnet ihr eigenes V |
| Straddle 9,7 / 23,5 / 29,0 % (M T2 c) | anderes Objekt (Gitterknoten Δ 0,50, 30,4 d); Referenz-Straddle 17.09.2026: PM2 10,03, Legacy 19,68, SM 29,61 % | T2 c, F5 c und Karte 1 lesen dieselbe Zeile von `reference_book.csv` |
| Titel 20.08.2026 „Gitter ±17 → ±14 %“ (M) | Paket aus Szenarien, Vol-Schocks, Kontingenzen, Basis, Collateral; Gitter ±18 % bis 24.05.2026, ±17 % bis 20.08.2026, ±14 % seither | Beschriftung „bundle incl. spot grid ±17 % → ±14 %“ |
| Sprung „am Tag nach dem Ereignis“ (M) | nur bei Ereignissen nach 08:00 UTC (22.02.2025, 08.01.2026, 08.05.2026, 20.08.2026); 23.01. und 24.05. springen am selben Tag | Beschriftung immer mit dem Ereignisdatum |
| „zwei Reverts“ (M, E) | ein Fall (HYPE PM2, Einzelkontrakt), zwei Zeilen (IM, MM) | Caption A1 |
| „sechs Grössenordnungen unter der Schwelle“ (M) | Mediane 5 bis 6 Dekaden unter 0,1 %; grösster IM-Einzelwert 8,88e−8, also 5,05 Dekaden unter 1 % und 4,05 unter 0,1 % | keine Dekadenzahl im Bild, die Punkte zeigen es |
| H3 „10 subaccounts“ (E) | 9 Konten mit Maker-Tagen (M9 hat keine) | Kopfzeile F4 |
| H4 „91 446 Fills“ (E, P) | 91 446 Panelzeilen aus 84 919 Fills; 6 527 doppelt (BTC 1 457, ETH 2 861, HYPE 2 209) | Kopfzeile F6 |
| ≤ 63 und > 63 Optionen als registrierte Sensitivität (E) | Nachtrag 4 Ziffer 2 nennt nur Legacy-PM auf BTC- und ETH-Beinen als Sensitivität; der Anteil wird genannt, nicht getestet | Zeilen ≤ 63 / > 63 sind explorativ (grau) |
| „OLS-Steigung der Bins ergibt β“ (Referee) | gilt für gebinnte Mittel nicht exakt | Prüfung auf der Steigung der vollen Residuen (Abschnitt 11) |
| F4-Bins nach Zweierpotenzen | [1; 2) hat 19 Maker-Tage | erster Bin [1; 4) mit 41 |
| „ohne Ausreisserzellen“ als eigene β-Zeile (Referee, E) | 0 Panelzeilen betroffen, β identisch | nur der Placebo-Teil in CSV und Text |
| H2 Konto M5 5 958 Fills (P) | 5 957 nach dem Ausschluss eines Fills mit K_Einzel ≤ 0 | Zeile M5 |

Bestätigt (Auswahl): alle Zahlen der Tabelle 3 des Referee, dazu T1 (PM2 3,42 bis 13,70 %, SM 12,37 bis 15,01 % des
Forwards, SM an 9 von 740 Knoten billiger), die vier Faktorpaare aus `faktoren.csv`, F1-Spannen, H1-Vorzeichenstruktur
(74 von 173 Zellen mit Edge ≤ 0, Kapitalnenner in allen 173 Zellen positiv, sign(A) = sign(B) überall), die
Parametersprünge (BTC PM2 +1,60 / −10,49 / −7,84 / −26,05 log-%).

---

## 6 · Regeln für alle Abbildungen

### 6.1 Format und Messung

- Breiten 3,4 und 7,0 Zoll, Satz 1:1 mit `\includegraphics[width=\linewidth]`. `figures_p2.py` setzt für seine
  Abbildungen `savefig.bbox = None` und `savefig.pad_inches = 0`; die Leinwand ist die Druckgrösse. Legenden stehen im
  Panel oder werden durch direkte Beschriftung ersetzt, keine Legendenspalte rechts der Achsen.
- `figstyle` bekommt `FS_MIN = 7.0`. Kein Text unter 7 pt, Panelbuchstaben 8 pt fett, Tick-Beschriftungen schwarz (nicht
  `GREY`). Den Code von `figures_p1.py`, der 6,0 und 6,5 pt setzt, nicht übernehmen.
- Test je Abbildungsfunktion (Muster `data/p2/fig_proto/jury/audit_protos.py`): gespeicherte PDF-Breite = Ziel ± 0,02
  Zoll, `get_tightbbox` jeder Zeichenfläche und jedes Textes innerhalb der Leinwand, keine sichtbare Textinstanz unter
  `FS_MIN`, genau eine Abbildung mit `Axes3D` (T1).
- Ausgabe `paper2/figures/{t1,t2,f1,…,a1}.pdf` und `.png`.

### 6.2 Kodierung

- **Manager** (Farbe gehört den Managern und nichts anderem): PM2 `#0072B2`, durchgezogen, Kreis; SM `#D55E00`,
  gestrichelt, Quadrat; Legacy-PM `#009E73`, gepunktet, Raute. Im Bild heisst er „legacy PM“. Konstanten
  `figstyle.MANAGER = {"pm2": (color, "-", "o"), "sm": (…, "--", "s"), "pm": (…, ":", "D")}`; `p2surface.MANAGER_*`
  liest daraus. Die Strichart Strichpunkt `(0, (3, 1, 1, 1))` ist frei und wird nur für „PM2, Beine einzeln“ in T2 c
  verwendet.
- **Seite:** Maker-Verkauf ▼ gefüllt, Maker-Kauf ▲ hohl, immer „maker sells (short)“ bzw. „maker buys (long)“. In
  Karten steht Verkauf oben. ▲ und ▼ bedeuten nirgends etwas anderes.
- **Basiswert:** nur Panel-, Zeilen- oder Spaltentitel. Keine Farbe, keine Markerform.
- **Statistik** (Schätzer, ECDF, Histogramm, β-Gerade, Forest) schwarz oder grau.
- **Ereignisstatus (F5):** Form = Manager; gefüllt = im H4-Panel; links halb gefüllt (`fillstyle="left"`) = behalten
  ohne Panelzelle (nur HYPE PM2 08.01.2026); hohl = weggefallen (Dosis unter 1 %).
- **Forest-Zeilen:** registriert = gefüllter schwarzer Kreis, Intervall 2 pt schwarz, Beschriftung fett; registrierte
  Sensitivität (in Präregistrierung oder Nachtrag als Sensitivität benannt) = offener schwarzer Kreis, Intervall 1 pt;
  explorativ = offener grauer Kreis (`#666666`), Intervall 1 pt grau, Zeile auf hellgrauem Band `#F0F0F0`.
- **Graustufentest:** jede Abbildung wird im Test zusätzlich nach Luminanz umgerechnet gespeichert
  (`paper2/figures/gray/`) und von Hand gesichtet, bevor sie ins Manuskript geht.

### 6.3 Einheiten, eine je Grösse

| Grösse | Einheit im Bild |
|---|---|
| Kapital aus Fills (F1) | „% of notional“ (Nominal = Menge × Index) |
| Kapital auf dem Gitter und im Referenzbuch (T1, T2 c, F5 c) | „% of forward“ |
| Kapitaländerung (Dosis, Parametersprung) | „log-%“ = 100·Δln K; GIF und Karten: einfache Prozent |
| Edge je Kapital (F2) | „bp of capital“, je Fill |
| Halbspread (F6) | „bp of index“ |
| Beträge eines Buchs | USDC nur in T2 a und in den CSV-Dateien |
| Quotienten (F1 Streifen, F4, T2 b) | logarithmische Achse |

### 6.4 Karten

- Eine Zahl je Zelle, Grau sequenziell nach log-Wert (`Greys` im Bereich 0,08 bis 0,72), Schriftfarbe weiss, wenn die
  Luminanz der Zelle unter 0,45 liegt. Zellen unter 200 Fills: leeres Kreuz „×“ 7 pt `#666666` ohne Füllung.
- Keine divergierenden Farbkarten. Vorzeichenbehaftete Karten: Grau nach |Wert|, negative Zellen zusätzlich mit
  Schraffur `////` in `#666666`, Vorzeichen immer als Zahl.
- Zellraster: 7 |Δ|-Buckets (0–10, 10–25, 25–40, 40–60, 60–75, 75–90, 90–100, oben nach unten) × 5 Laufzeiten
  (≤2, 2–7, 7–30, 30–90, >90 Tage, links nach rechts). Achsentitel „|delta| of the traded option, %“ und „tenor, days“.

### 6.5 Urteilsgrammatik

Eine Funktion `figures_p2.ruler(ax, rows, h, *, side)` baut die Forests von F2 c, F3 b, F4 b und F6 d.

- Kopfzeile fett über dem Panel: `registered: {stat} [{lo}, {hi}] → rejected` bzw. `→ not rejected`. Die Funktion wendet
  die Regel aus `h["rule"]` mit `h["threshold"]` auf `lo`/`hi` neu an und bricht ab, wenn das Ergebnis nicht `h["rejected"]`
  ist. H4 hat eine eigene Prüfliste (F6 c) mit derselben Abbruchregel über `criteria`.
- Schwelle gestrichelt schwarz 0,8 pt. Der Ablehnungsbereich ist schraffiert (`////`, `#BBBBBB`), **nur** in der Höhe der
  registrierten Zeile: H1 und H2 rechts der Schwelle, H3 links davon, H4 bei β ≤ 0.
- Rechts neben jeder Zeile n (Zellen, Fills, Maker-Tage oder Cluster, je nach Test) in 7 pt grau.
- Zeilenbeschriftung höchstens 18 Zeichen. Intervalle, die aus der Achse laufen, enden in einem Pfeil.
- Unter der Kopfzeile eine Zeile mit Stichprobe und Clustern (je Slot unten festgelegt).

### 6.6 Regime-Raster

R1 bis 23.01.2026 04:24:05 UTC, R2 bis 24.05.2026 04:05:07 UTC, R3 bis 20.08.2026 22:09:25 UTC, R4 danach. Grenzen sind
die PM2-Ereignisse, die in BTC und ETH das Referenzbuch um mindestens 3 log-% verändern (BTC −10,5 / −7,8 / −26,0,
ETH −4,9 / −3,4 / −18,3). Zuordnung über den Zeitstempel des Objekts: Fills über `ts`, Maker-Tage über den Buchzeitpunkt
00:00 UTC des Tages. Beschriftung „R1 to 23 Jan“, „R2 to 24 May“, „R3 to 20 Aug“, „R4 since 20 Aug“. Alles, was nach
Regime aufteilt, ist explorativ.

### 6.7 Tabellen

- Eine CSV-Datei je Panel: `results/p2/fig_<slot>_<panel>.csv` (Kleinbuchstaben; Panels mit identischen Daten dürfen eine
  Datei teilen, z. B. `fig_t1_ab.csv`). Jede Zahl, die im Bild steht, steht dort mit voller Genauigkeit, dazu die Spalte
  `printed` mit dem gedruckten Text.
- Die Inferenzdateien (`h1_cells.csv`, `fig_edge_maps.csv`, `fig_h2_dist.csv`, `fig_h3_series.csv`,
  `fig_h4_events.csv`, `h4_placebo.csv`) sind Eingaben. Die Abbildungsschicht rechnet keine Teststatistik nach; erlaubt
  sind Sortieren, Zählen, Binning und Quantile deskriptiver Spalten.

### 6.8 Captions

Englisch, keine Gedankenstriche, jede ergebnisabhängige Zahl als `\PH{key}` (Liste in Abschnitt 12). Captions sagen,
was gezeichnet ist und wie man es liest, nicht was herauskommt.

---

## 7 · Bauanweisungen je Slot

### T1 · Die Engine-Sicht der Oberfläche · 7,0 × 4,2 Zoll

**Warum:** P trägt den Wert auf der Fläche (Iso-Linien, Kopfzahl), M erklärt ihn (bindende Regel). Nur M zeigt, dass
fast überall ein Szenario das PM2-Kapital setzt; das stützt später F6, weil die Senkung der Tail-Gewichte am 23.01.2026
genau die Zellen trifft, in denen die gedämpften Tail-Szenarien binden. Vorlagen: `data/p2/fig_proto/praktiker/t1_praktiker.png`
(a/b), `data/p2/fig_proto/mechanismus/t1_proto.png` (c/d).

**Daten.** `p2surface.capital_grid("BTC", ts=1789632000, manager, side="short")` für `manager ∈ {"pm2", "sm"}` am Block
17.09.2026 08:00:00 UTC (letzter Pilottag, kein Parameterereignis in ±1 Tag, 28 Tage nach dem 20.08.2026). Gitter: 37
Call-Deltas 0,05 bis 0,95 in Schritten von 0,025, 20 Laufzeiten `geomspace(1, 365, 20)` Tage; identisch mit
`data/p2/surface/probe_BTC_2026-09-17_grid.csv`. Parameter `Timeline("BTC", m).at(ts)`. Gelistete Verfälle
`p2surface.live_expiries` (15).

**Berechnung.** K_pct = `K_per_forward_bp` / 100. Bindende Regel je Knoten über `figdata_p2.binding_rule(grid, ccy, ts,
manager)` (Vorlage `_pm2_binding`, `_sm_branch` in `proto_mechanismus.py`): PM2 = Index des schlechtesten Szenarios
aus `margin_pm2` mit (spotShock, volShock, dampeningFactor), abgebildet auf die Klassen „spot +14 %, vol up“, „spot
−14 %, vol up“, „core, other vol“ (Kern, Dämpfung 1, sonstiger Vol-Zustand), „spot ×{s} (dampened)“ für s > 1,
„spot ×{s} (dampened)“ für s < 1, „basis/skew/other“; die Gitterweite ±14 % wird aus den Parametern gelesen, nicht fest
geschrieben. SM = Zweig aus `OptionMarginParams`: „15 % − OTM“, „13 % floor“, „put: 1.05 × MM“. Test: Die Zerlegung
summiert sich an jedem der 1 480 Knoten auf das Gitterkapital (relativ ≤ 1e−9), jede Klasse ist abgedeckt.

**Aufbau.** Kopfzeile, darunter Zeile 1 mit a (PM2) und b (SM) als 3D und dem Farbbalken rechts (Breite 0,10 Zoll),
Zeile 2 mit c (PM2) und d (SM) als 2D-Karten genau unter a und b, darunter eine Legendenzeile für c und d.

- **a, b:** `plot_surface`, x = Call-Delta, y = log10(Tage), z = IV in %; Flächenfarbe `cividis` mit
  `Normalize(3.0, 15.5)` auf K_pct, gemeinsam für beide Panels. Sicht elev 24, azim −128 in beiden, z-Bereich gemeinsam.
  Iso-Linien bei 4, 8, 12, 14 %: `contour` auf dem (Delta, log-Tage)-Gitter von K_pct, auf die Fläche gehoben (z = IV
  bilinear), schwarz 0,7 pt, je Linie eine Beschriftung „8 %“ 7 pt. Achsen: x „call delta (put = Δ − 1)“ mit Ticks 0,1 /
  0,5 / 0,9; y „days to expiry“ mit Ticks 1, 7, 30, 90, 365; z „implied vol, %“.
  Titel: „a  PM2: ATM 30 d short = 11.8 % of forward“, „b  SM: ATM 30 d short = 14.1 % of forward“ (Knoten Δ 0,50,
  30,44 Tage; eine Nachkommastelle, aus dem Gitter gelesen).
- **Farbbalken:** Beschriftung „capital per short contract, % of forward“, Ticks 4, 6, 8, 10, 12, 14; die vier
  Iso-Stufen als schwarze Querstriche über die volle Balkenbreite.
- **c, d:** `pcolormesh` der Klassen; feste Füllungen: „spot +14 %, vol up“ `#E0E0E0`; „spot −14 %, vol up“ `#A8A8A8`;
  „core, other vol“ `#C8C8C8` mit `--`; Tail aufwärts weiss mit `..`; Tail abwärts weiss mit `\\\\`; „basis/skew/other“
  weiss mit `xx`; SM „15 % − OTM“ weiss, „13 % floor“ `#E0E0E0` mit `///`, „put: 1.05 × MM“ weiss mit `..`. Nur
  vorhandene Klassen in der Legende, alle Klassen mit Knotenzahl in der CSV. x 0,05 bis 0,95 mit Ticks bei 0,10, 0,25,
  0,40, 0,60, 0,75, 0,90; y log 1 bis 365 Tage mit Ticks 1, 2, 7, 30, 90, 365. Gitterlinien **nur** an den Ticks 0,10 …
  0,90 und 2, 7, 30, 90 (0,4 pt, `#808080`): das sind die Bucketgrenzen von Paper 1. Iso-Linien wie in a/b, 2D, mit
  Inline-Beschriftung. Die 15 gelisteten Verfälle als kurze Striche (0,06 Zoll, nach innen) an der rechten Achse von c
  und d. Knoten ATM 30 d als schwarzer Punkt 3 pt mit weissem Rand und Beschriftung „ATM 30 d“ in c und d. Titel „c
  binding PM2 scenario“, „d  binding SM rule“. x-Beschriftung „call delta (put = Δ − 1)“, y „days to expiry“ nur in c.
- **Kopfzeile** (7 pt, oben links): „BTC · 17 Sep 2026, 08:00 UTC · 15 live expiries · PM2 spot grid ±14 % since 20 Aug
  2026 · chain semantics“.

**Tabellen.** `fig_t1_ab.csv` (manager, delta, tenor_days, iv, strike, forward, K_usdc, K_pct_forward),
`fig_t1_cd.csv` (manager, delta, tenor_days, rule, spot_shock, vol_shock, dampening, K_pct_forward), `fig_t1_meta.csv`
(ts, block, n_expiries, gelistete Laufzeiten, Iso-Stufen, Knotenwerte ATM 30 d, min/Median/max je Manager, Knotenzahl
je Klasse).

**Caption.**
> **The surface as the engine sees it.** BTC implied volatility over call delta and tenor at 08:00 UTC on 17 September
> 2026, built from the on-chain feeds, with the capital that one short contract binds under PM2 (panel a) and under
> standard margin (panel b) as colour on a common scale in per cent of the forward. Height is volatility, colour is
> capital, and black lines join points of equal capital. Panels c and d name the rule that sets the capital at each
> point: the worst scenario of the PM2 grid, and the branch of the standard margin formula. Their grid lines are the
> delta and tenor bucket edges of Figures~\ref{fig:f1} and~\ref{fig:f2}; the surface holds out-of-the-money options
> only, so buckets above an absolute delta of 0.6 have no counterpart here. Standard margin is set in per cent of spot
> and shown in per cent of the forward. Capital follows the contracts on chain; the venue's off-chain engine discounts
> PM2 at a flat two per cent.

**Prüfzahlen.** 740 Knoten je Manager; 15 Verfälle; ts 1789632000. PM2 K in % des Forwards min 3,418 / Median 10,448 /
max 13,704; SM 12,374 / 12,979 / 15,007. ATM 30 d (Δ 0,50, 30,439 Tage): PM2 11,826, SM 14,080. SM < PM2 an 9 von 740
Knoten, Median SM/PM2 1,261. Alle 1 480 Werte liegen in [3; 15,5]. Zerlegung = Gitterkapital an jedem Knoten.

### T2 · Was `get_margin` liefert, und wie PM2 ein Buch bewertet · 7,0 × 2,6 Zoll

**Warum:** P a zeigt V als Fläche und trägt damit die Aussage „V steckt in C − net, nicht in R“; P b löst die Faktoren auf;
M c ist die Brücke vom Einzelkontrakt (F1) zum Buch (F3, F4). Vorlagen: `praktiker/t2_praktiker.png`,
`mechanismus/t2_proto.png`.

**Daten.** a, b: `results/p2/semantik/faktoren.csv`, Filter `messung` beginnt mit „historisch“, enthält nicht „H0_“,
`fall ∈ {A, B}`; genau vier Zeilen (Test). Spalten `SM_R_engine, PM2_R_engine, V_und_SM, V_PM2, F_Cnet, F_R_engine`.
Zeilennamen: b17_exakt A „17 Sep, short“, B „17 Sep, mixed“; b24 (H1-Liste) A „24 Sep, short“, B „24 Sep, mixed“.
c: Zeile BTC 2026-09-17 von `results/p2/reference_book.csv` (08:00 UTC, gelisteter Verfall mit 22 Tagen, Strike =
Forward = 76 587,73). Szenario-P&L des Buchs (Short-Call + Short-Put am Strike) über `figdata_p2.pm2_scenarios(book,
state, params)` mit `Timeline("BTC", "pm2").at(ts)`; Kapitallinien `K_pm2`, `K_sm` aus derselben Zeile und
`K_pm2_call + K_pm2_put` aus der neuen Erweiterung von `reference_book.csv` (Abschnitt 10).

**Aufbau.** Drei Panels nebeneinander, Breiten einschliesslich Beschriftung 2,0 / 2,1 / 2,9 Zoll.

- **a** Titel „a  mixed book of 24 Sep 2026“. Zwei waagerechte Balken, SM oben, PM2 unten, Höhe 0,55. Segment 1 = R
  (Managerfarbe voll, schwarzer Rand 0,5 pt), Segment 2 = −V des jeweiligen Managers (weiss, Schraffur `////` in
  `#666666`). Beschriftung „R 211“ bzw. „R 99“ über dem linken Balkenende, Summe „708“ bzw. „596“ rechts am Balken.
  x linear 0 bis 800, „C − net = R − V, thousand USDC“. Legende im Panel oben rechts: „R, requirement“ (grau voll),
  „−V, value term“ (schraffiert).
- **b** Vier Zeilen in der Reihenfolge 17 Sep mixed, 24 Sep mixed, 17 Sep short, 24 Sep short. Hohler schwarzer Kreis bei
  `F_Cnet`, gefüllter bei `F_R_engine`, grauer Pfeil (Spitze 3 pt) vom hohlen zum gefüllten. Werte in derselben Zeile auf
  der jeweils äusseren Seite ihres Markers (so kollidieren 2,14 und 2,33 nicht). x log 0,8 bis 20, Ticks 1, 2, 4, 8, 16,
  „SM / PM2 capital ratio (log)“. Senkrechte bei 2 gestrichelt, unten beschriftet „H3 threshold, set from these books“.
  Legendenzeile über dem Panel: „○ on C − net   ● on R“.
- **c** x kategorial über die 17 Spot-Schocks des aktuellen Gitters (0,34; 0,67; 0,86 … 1,14 in Schritten von 0,035;
  1,5; 2; 3; 4; 5; 6). Drei Gruppentitel über der Achse: „tail ↓ (dampened)“, „core ±14 %“ (Kern hinterlegt
  `#F2F2F2`), „tail ↑ (dampened)“. Tick-Beschriftung waagerecht nur bei 0,34 / 0,86 / 1 / 1,14 / 6. y „scenario P&L of
  the book, % of forward“, von −1,15·K_SM/F bis +3. Punkte = PM2-Szenarien als Kreise 3,5 pt mit blauem Rand; Füllung
  vol up blau, vol unchanged weiss, vol down `#BBBBBB`; Kernpunkte je Vol-Zustand mit dünner blauer Linie 0,6 pt
  verbunden, Tails unverbunden, Skew-Szenarien nur in der CSV. Das schlechteste Szenario mit schwarzem Ring 8 pt. Drei
  Waagerechte bei −K/F mit Direktbeschriftung rechts über der Linie: „PM2, book 10.0“ blau durchgezogen 1,2 pt; „PM2,
  legs one by one {x}“ blau Strichpunkt 1,0 pt; „SM 29.6“ zinnober gestrichelt 1,2 pt. Legende der Vol-Zustände als
  Zeile über dem Panel.

**Tabellen.** `fig_t2_a.csv`, `fig_t2_b.csv`, `fig_t2_c.csv` (Szenarien mit spot_shock, vol_shock, dampening, pnl_usdc,
pnl_pct_forward, binding; Kapitallinien).

**Caption.**
> **What \texttt{get\_margin} returns, and how PM2 prices a book.** Panel a splits $C - \mathrm{net}$ into the
> requirement $R$ and the value term $-V$ for the mixed probe book of 24 September 2026 (block 45\,110\,142); $-V$ is
> almost the same under both managers and dwarfs $R$. Panel b sets the ratio of standard to PM2 margin read as
> $C - \mathrm{net}$ (open) against the ratio on $R$ (filled) for the four probe books at their historical blocks. The
> dashed line is the H3 threshold of two, which was set from these books before any maker book was measured. On the
> mixed book of 17 September $V$ is positive, so the ratio falls from 11.86 to 10.76. Panel c is the scenario profit and
> loss of a short BTC straddle struck at the forward on 17 September 2026, on the listed expiry nearest to 30 days
> (22 days), in per cent of the forward. PM2 charges the worst scenario of the whole book plus contingencies (solid
> line), which is less than the sum of the legs margined one by one (dash dot); standard margin is dashed.

**Prüfzahlen.** Vier Zeilen. a: SM R 211 023,47, −V 496 914,28, C − net 707 937,75; PM2 R 98 834,91, −V 496 858,84,
C − net 595 693,75. b (C − net / R): 17 Sep short 2,33 / 3,19; 17 Sep mixed 11,86 / 10,76; 24 Sep short 1,46 / 3,61;
24 Sep mixed 1,19 / 2,14. c: K_PM2/F = 10,03 %, K_SM/F = 29,61 % (identisch mit F5 c und Karte 1); Ring = argmin der
Szenario-P&L; Spot-Gitter ±14 %.

### F1 · Was ein Kontrakt kostet · 7,0 × 3,9 Zoll

**Warum:** Die Aussage von F1 ist ein Managervergleich; P macht ihn an einer Achse ablesbar und zeigt als einzige Fassung
alle drei Basiswerte, bei einer Zahl je Zelle. Vorlage: `praktiker/f1_praktiker.png`.

**Daten.** `results/p2/fig_edge_maps.csv`, Karten `map ∈ {"pm2", "sm_pm2win", "pm_pm2win"}` (dieselben Fills im
PM2-Fenster; `pm_pm2win` nur BTC und ETH). Zellwert κ = 100·`sum_K`/`sum_index` der Karte `pm2`; Quotienten
q_SM = `sum_K`(sm_pm2win)/`sum_K`(pm2), q_PM = `sum_K`(pm_pm2win)/`sum_K`(pm2). Besetzt = `occupied` der Karte `pm2`.
Regime: `results/p2/fig_f1_regimes.csv` aus `figdata_p2.cell_capital_by_regime` (`capital.parquet` ⋈
`data/p1/derived/markouts.parquet` über `trade_id`, Buckets aus Paper 1, Filter `K_pm2` endlich): je Regime und Zelle
fills, contracts, Σ K_sm·a, Σ K_pm·a, Σ K_pm2·a, Σ Index·a, besetzt ab 200 Fills. `fig_capital_by_manager.csv` (Median je
Fill) nicht verwenden: zwei Zellgrössen für dieselbe Zelle.

**Aufbau.** Links sechs Karten (Zeilen: Verkauf oben, Kauf unten; Spalten BTC, ETH, HYPE), rechts je Zeile ein Streifen.

- **Karten:** Raster nach 6.4. Zahl = κ mit zwei signifikanten Stellen (0.07, 0.12, 9.9, 13, 39). Grau log je Zeile,
  gemeinsam über die drei Basiswerte. Zeilentitel links „maker sells (short)“ und „maker buys (long): capital ≈ premium“;
  Spaltentitel BTC, ETH, HYPE; |Δ|-Beschriftung nur links, Laufzeit nur unten.
- **Streifen** (einer je Zeile, gemeinsame x-Achse): acht Zeilen „SM BTC“, „  R4“, „SM ETH“, „  R4“, „SM HYPE“,
  „  R4“, „legacy BTC“, „legacy ETH“. Je besetzte Zelle ein Zeichen: SM gefülltes zinnober Quadrat 2,5 pt (gepoolt), in der
  R4-Zeile hohles Quadrat (Zellen mit ≥ 200 Fills in R4), Legacy gefüllte grüne Raute; deterministische vertikale
  Streuung ±0,18 Zeilen nach Zellindex. Medianstrich je Zeile schwarz (Höhe 0,5 Zeilen, 1,2 pt; R4 0,6 pt). Anzahl
  Zellen je Zeile rechts in 7 pt grau. x log 0,6 bis 5, Ticks 0,6 / 1 / 2 / 4, Senkrechte bei 1 gestrichelt schwarz;
  Kopf über dem oberen Streifen „← PM2 dearer   PM2 cheaper →“; x-Beschriftung unten „capital ÷ PM2 capital, same fills
  (log)“.
- **Kopfzeile** über den Karten (7 pt): „number = PM2 capital per contract, % of notional, ratio of sums over the PM2
  window, pooled over four parameter regimes · × = under 200 fills“.

**Tabellen.** `fig_f1_a.csv` (ccy, side, delta_bucket, tenor_bucket, fills, contracts, occupied, kappa_pm2, kappa_sm,
kappa_pm, printed), `fig_f1_b.csv` (ccy, side, cell, manager, regime ∈ {pooled, R4}, ratio, row, jitter),
`fig_f1_regimes.csv` (siehe oben).

**Caption.**
> **What one contract costs.** PM2 capital per contract in per cent of notional over the absolute delta of the traded
> option and tenor, for maker sells (upper row) and maker buys (lower row), as a ratio of sums over the fills of the PM2
> window, which spans four parameter regimes. Each row is shaded on one logarithmic grey scale, and an empty cross marks
> a cell with fewer than 200 fills. The strips on the right give, for every occupied cell, the capital of the same fills
> under standard margin (squares) and under the legacy manager (diamonds) divided by PM2 capital, with the median cell
> as a bar; hollow squares use only the fills after the parameter change of 20 August 2026. For a maker buy, standard
> margin charges the premium.

**Prüfzahlen.** 210 Zellen, 173 besetzt, 37 Kreuze (BTC 10 = Kauf 4 + Verkauf 6, ETH 2, HYPE 25). Fills und contracts
je Zelle in allen drei Karten gleich. κ-Spannen (besetzte Zellen): BTC Verkauf 7,80 bis 17,69, Kauf 0,07 bis 10,86; ETH
7,07 bis 21,36 / 0,08 bis 14,53; HYPE 17,50 bis 38,73 / 0,46 bis 15,64. q_SM 0,752 bis 4,669, in 86 Zellen < 1; Median
der Verkaufszellen BTC 0,943, ETH 0,902, HYPE 0,875. q_PM 0,946 bis 1,736 über 128 Zellen. R4-Mediane der
Verkaufszellen 1,398 (BTC, 6 Zellen), 1,140 (ETH, 18), 1,444 (HYPE, 1). κ = 100·`sum_K`/`sum_index` aus `h1_cells.csv`
(Identität, Abweichung 0). Summen über R1 bis R4 = Summen der Karte (relativ ≤ 1e−9).

### F2 · Die Karte in zwei Nennern (H1) · 7,0 × 4,4 Zoll

**Warum:** Die Kapitalkarte ist Beitrag 1 der Spezifikation und gehört ins Bild; die Graukodierung macht sie
druckfest. Das Rang-Rang-Bild zeigt die Grösse, die H1 testet, und die Vorzeichenlinien zeigen die strukturelle
Untergrenze: Weil der Kapitalnenner in jeder Zelle positiv ist, stehen die 99 Zellen mit positivem Edge in beiden
Karten vor den 74 übrigen; selbst eine vollständige Umordnung innerhalb der beiden Gruppen ergäbe ρ um 0,73 (Referee,
4 000 Ziehungen), die Schwelle ist 0,5. Das ändert den Test nicht, muss aber sichtbar sein. Vorlagen:
`praktiker/f2_praktiker.png` (Karten, Rang gegen Rang), `empirie/f2_empirie_SYNTHETIC.png` (Leiste).

**Daten.** `results/p2/h1_cells.csv` (occupied, A_bp, B_bp, rank_A, rank_B, rank_shift, rank_A_lo/hi, rank_B_lo/hi,
fills), `results/p2/h1.json` (stat, lo, hi, rejected, rule, threshold, n, n_days), `results/p2/sensitivity.json` und die
neuen Einträge `sign_floor`, `within_pos`, `within_nonpos` (Abschnitt 10).

**Berechnung.** Nur Zählen und Sortieren: Zahl der Zellen mit A_bp > 0 (Lage der Vorzeichenlinien), zehn grösste
|rank_shift| (Bindungen nach Zell-ID).

**Aufbau.** Links a (Karten, 4,5 Zoll breit, volle Höhe), rechts oben b (Rang gegen Rang, 2,3 × 2,25 Zoll), rechts
unten c (Forest, 2,3 × 1,85 Zoll).

- **a** Sechs Karten wie F1 (Verkauf oben, Kauf unten; BTC, ETH, HYPE). Zahl = B_bp (Edge je PM2-Kapital, bp) mit
  höchstens vier Zeichen: |v| < 10 eine Nachkommastelle („3.4“, „−0.8“), 10 ≤ |v| < 1 000 ganzzahlig („240“, „−35“),
  |v| ≥ 1 000 in ganzen Tausend („3k“, „−12k“). Grau nach log|B| je Zeile (untere Grenze 1 bp), negative Zellen schraffiert,
  Kreuze wie F1. Zeilentitel „maker sells (short)“, „maker buys (long): return on premium“. Kein Farbbalken. Kopfzeile
  „number = net edge per unit of PM2 capital, bp, per fill · hatched = negative · × = under 200 fills · PM2 window,
  pooled over four regimes“.
- **b** x = rank_A („rank by edge per notional“), y = rank_B („rank by edge per PM2 capital“), beide 1 bis 173 mit
  Rang 1 oben rechts (Achsen invertiert), Ticks 1, 50, 100, 150, 173, Zusatz „1 = highest edge“ in beiden
  Achsentiteln. Winkelhalbierende grau gestrichelt 0,6 pt. Vorzeichenlinien bei 99,5 auf beiden Achsen, grau
  durchgezogen 0,6 pt, Beschriftung im unteren linken Block „edge ≤ 0“. Zeichen: Verkauf ▼ gefüllt schwarz 3 pt, Kauf
  ▲ hohl schwarz 3 pt. Für die zehn grössten |rank_shift| Rangintervalle als graues Kreuz (0,6 pt) aus
  rank_A_lo/hi und rank_B_lo/hi.
- **c** Forest nach 6.5, x = Spearman-ρ von −0,2 bis 1,0, Schwelle 0,5, Schraffur ρ ≥ 0,5 hinter der registrierten
  Zeile. Graues Band über alle Zeilen von `sign_floor.p05` bis `sign_floor.p95`, beschriftet „sign pattern alone“.
  Zeilen: „registered“ (h1.json); Sensitivitäten „maintenance margin“ (`b_mm.h1_pm2_mm`), „net edge, Paper 1“
  (`c_p1_net_edge.h1_pm2`); explorativ „per day to expiry“ (`f_time.to_expiry`), „per holding time“ (`f_time.holding`),
  „SM capital“ (`a_maps.sm_pm2_window`), „legacy PM capital“ (`a_maps.pm_pm2_window`), „BTC only“, „ETH only“, „HYPE
  only“ (`g_by_ccy.pm2_*`), „edge > 0 only“, „edge ≤ 0 only“ (neu). n = Zellen. Kopfzeile fett nach 6.5, darunter
  „173 cells · 463 day clusters · rejected if upper bound ≥ 0.5“.

**Tabellen.** `fig_f2_a.csv` (Zellen mit B_bp, printed, hatched), `fig_f2_b.csv` (Ränge, Intervalle, top10),
`fig_f2_c.csv` (label, source_key, kind, stat, lo, hi, n, n_days), `fig_f2_shift.csv` (mittlere Rangverschiebung nach
Laufzeit und |Δ| je Seite, für den Text).

**Caption.**
> **The map in two denominators (H1).** Panel a is net edge per unit of PM2 capital in basis points, per fill, for every
> cell of the PM2 window by underlying and maker side; negative cells are hatched and an empty cross marks fewer than
> 200 fills. For a maker buy the denominator is close to the premium, so the lower row is a return on premium and is
> shaded on its own scale. The map per notional is Figure~\PH{p1-map-fig} of the companion paper. Panel b ranks the
> \PH{h1-cells} occupied cells by edge per notional and by edge per PM2 capital; because capital is positive in every
> cell, the \PH{h1-pos} cells with positive edge come first in both rankings, and the grey lines mark that boundary.
> Crosses give the 90 per cent rank intervals of the ten largest moves. Panel c is the registered test, Spearman's
> $\rho$ with its 90 per cent day-cluster interval against the threshold of 0.5, followed by sensitivities and, on grey,
> exploratory rows; the grey band is the $\rho$ that the sign pattern alone produces when ranks are shuffled within each
> sign group. Edge is a flow per fill and capital a stock, so a cell's value is not a return per unit of time.

**Prüfzahlen.** 173 Punkte; 210 Zellen, 37 Kreuze; 99 Zellen mit A_bp > 0, 74 mit A_bp ≤ 0 (Kauf 26 von 87, Verkauf 48
von 86); sign(A_bp) = sign(B_bp) in allen 173; κ zwischen 0,074 und 38,73 %; `n_days` 463; `cells_present_min` 173;
331 813 Fills in besetzten Zellen von 336 087 im Fenster, 20 Fills mit K_PM2 ≤ 0; zehn Kreuzintervalle. Kopfzeile gegen
h1.json (stat, lo, hi, rejected).

### F3 · Der nächste Kontrakt im Buch (H2) · 3,4 × 4,0 Zoll

**Warum:** H2 testet einen Median; die ECDF zeigt ihn als Schnitt mit der Höhe 0,5 und die Anteile ≤ 0 und ≤ ½ ohne
Balkenzählen. Der Forest trägt Urteil und Robustheit. Vorlagen: `praktiker/f3_praktiker.png` (a),
`empirie/f3_empirie_SYNTHETIC.png` (b).

**Daten.** `results/p2/fig_h2_dist.csv` (`label = all`, `variant = ratio`, `kind ∈ {hist, share_le_0, n}`; 62 Bins:
(−∞; −1), 60 Bins zu 0,05 auf [−1; 2), [2; ∞)), `results/p2/h2.json`, `results/p2/sens_h2.csv` (variant/group) und die
neuen Regime-Zeilen (Abschnitt 10).

**Aufbau.** Kopfzeile, a (1,45 Zoll), b (1,75 Zoll), gemeinsame x-Achse [−1; 2].

- **a** ECDF als Treppe, schwarz 1,0 pt: Wert an jeder rechten Bingrenze = kumulierte Zahl / n. Sie beginnt bei x = −1
  auf der Höhe des linken Überlaufs und endet bei x = 2 auf 1 − rechter Überlauf; beide Überläufe als Text am Rand
  („x % below −1“, „y % above 2“). Bänder hinter der Kurve: ≤ 0 `#BDBDBD`, 0 bis ½ `#D9D9D9`, ½ bis 1 `#EFEFEF`, > 1
  weiss; über jedem Band zwei Zeilen 7 pt: „free“ / „cheap“ / „partial“ / „dearer“ und der Anteil in %. Anteil ≤ 0 aus
  `share_le_0`, die übrigen aus den Bins. Median als waagerechter schwarzer Balken 2 pt von lo bis hi auf y = 0,5 mit
  offenem Kreis bei stat. Senkrechte bei ½ gestrichelt schwarz, bei 1 grau 0,5 pt durchgezogen. y 0 bis 1, Ticks 0 /
  0,25 / 0,5 / 0,75 / 1, „share of fills“.
- **b** Forest nach 6.5, Schraffur x ≥ ½ hinter der registrierten Zeile. Zeilen: „registered“ (h2.json);
  Sensitivitäten „next contract“ (ratio_unit), „maintenance margin“ (ratio_mm), „tape book“ (ratio_tape); explorativ
  „M3 (HYPE)“, „M5“, „M8“, „M10“ (`group = label=…`), „R1 to 23 Jan“, „R2 to 24 May“, „R3 to 20 Aug“, „R4 since 20
  Aug“. n = Fills. x-Beschriftung „ΔK per contract / stand-alone PM2 capital“.
- **Kopfzeile** zweizeilig: fett die Urteilszeile nach 6.5; darunter „4 PM2 accounts, ETH and HYPE only · 19 999 of
  20 000 sampled fills · 372 day clusters“.

**Tabellen.** `fig_f3_a.csv` (x, ecdf, Bänder mit Anteil, Überläufe), `fig_f3_b.csv`.

**Caption.**
> **The next contract in a dominant maker's book (H2).** Panel a is the cumulative distribution of the marginal capital
> of a fill per contract over its stand-alone PM2 capital, $\Delta K / K_{\text{single}}$, for the \PH{h2-n} tested
> fills of the four PM2 subaccounts, which trade ETH and HYPE only; the numbers above the bands are the shares of fills
> in each band, and the shares beyond the axis are given at both ends. The dashed line is the registered threshold of
> one half, and the bar at height one half is the median with its 90 per cent day-cluster interval. Panel b repeats the
> registered row above the sensitivities and, on grey, exploratory rows per account and per parameter regime. A maker
> who starts from an empty book pays the stand-alone capital of Figure~\ref{fig:f1}.

**Prüfzahlen.** n 19 999, `n_sample` 20 000, `n_excluded` 1, `n_days` 372, Seed 20260924; Konten M3 6 405 (HYPE), M5
5 957, M8 4 296, M10 3 341; ETH 13 594, HYPE 6 405; erster Tag 04.09.2025; 62 Bins, zwei offen; Bandanteile und
Überläufe summieren sich auf 1; ECDF bei 0 = `share_le_0` = `h2.json share_nonpositive`; Kopfzeile gegen h2.json.

### F4 · Was Netting wert ist (H3) · 3,4 × 4,0 Zoll

**Warum:** Die Buchbreite ist der Mechanismus hinter H3 und zeigt die Kontogrenze von 63 Optionen an ihrer echten Stelle;
der Forest trägt Urteil, kontrafaktischen Anteil und Legacy-PM. Gleiches Raster wie F3. Vorlagen:
`praktiker/f4_praktiker.png` (b, hier gebinnt), `empirie/f4_empirie_SYNTHETIC.png` (Forest).

**Daten.** `results/p2/fig_h3_series.csv` (`status == ok`; label, day, manager, n_legs, over_63_options,
ratio_sm_pm2), `results/p2/h3.json`, `results/p2/sens_h3.csv` und die neuen Zeilen nach Kontomanager und Regime.

**Aufbau.** Kopfzeile, a (1,45 Zoll), b (1,75 Zoll); Ränder und Panelhöhen identisch mit F3.

- **a** Bins in Optionsbeinen [1; 4), [4; 8), [8; 16), [16; 32), [32; 64), [64; 128), [128; 256), [256; 512). Je Bin
  Median von ratio_sm_pm2 (schwarze Linie 1,0 pt, Punkt 2,5 pt am geometrischen Bin-Mittel) und p25 bis p75 als Band
  `#CCCCCC`. x log 1 bis 400, Ticks 1, 4, 16, 64, 256, „option legs in the book (log)“; y log, Ticks 1, 2, 4, 8, 16,
  „K_SM / K_PM2 (log)“. Waagerechte bei 2 gestrichelt, „2: PM2 saves half“. Senkrechte bei 63,5 grau 0,6 pt,
  „SM account limit: 63 options“; Bereich rechts davon schraffiert (`\\\\`, `#BBBBBB`), Text „SM counterfactual: 1 431
  of 1 943 maker-days“. Maker-Tage je Bin als Zahl 7 pt grau über der x-Achse.
- **b** Forest nach 6.5, x log (0,5 bis 32, bei Bedarf erweitert), Schwelle 2, Schraffur x ≤ 2 hinter der registrierten
  Zeile. Zeilen: „registered“ (h3.json); Sensitivitäten „maintenance margin“ (sm_pm2_mm), „legacy PM / PM2“ (pm_pm2_be,
  BTC- und ETH-Beine, n 1 640); explorativ „SM / PM2, same legs“ (sm_pm2_be), „≤ 63 options“ (sm_pm2_le63), „> 63
  options“ (sm_pm2_gt63), „SM account (M2)“, „legacy PM accounts“, „PM2 accounts“, „R1 to 23 Jan“ bis „R4 since 20 Aug“.
  n = Maker-Tage. x-Beschriftung „capital ratio to PM2 (log)“.
- **Kopfzeile:** fett die Urteilszeile; darunter „9 accounts · 1 943 maker-days · 462 day clusters (UTC days, not
  accounts)“.

**Tabellen.** `fig_f4_a.csv` (lo, hi, centre, n, median, p25, p75), `fig_f4_b.csv`.

**Caption.**
> **What netting is worth (H3).** Panel a is $K_{\mathrm{SM}}/K_{\mathrm{PM2}}$ for the opening books of \PH{h3-days}
> maker-days against the number of option legs, as the median per bin with the interquartile band. Beyond 63 options no
> standard margin account on the venue may hold the book, so $K_{\mathrm{SM}}$ is counterfactual on \PH{h3-over63}
> maker-days. The dashed line is the registered threshold of two. Panel b is the registered median with its 90 per cent
> interval, the sensitivities including the legacy manager on BTC and ETH legs, and, on grey, exploratory rows by book
> size, by the manager of the account and by parameter regime. Clusters are UTC days, not accounts.

**Prüfzahlen.** 1 943 Maker-Tage `ok` (dazu 24 `no_options`, 1 `no_snapshot`), 462 Cluster, 0 ausgeschlossen, 1 431 mit
mehr als 63 Optionen (73,6 %), `over_63_options` ⇔ n_legs ≥ 64. Neun Konten: M1 120, M2 328, M3 303, M4 203, M5 374, M6
119, M7 10, M8 239, M10 247; Manager M2 SM; M1, M4, M7 PM:ETH, M6 PM:BTC; M3 PM2:HYPE; M5, M8, M10 PM2:ETH. Bins 41,
29, 57, 170, 215, 431, 909, 91. Legacy-Zeilen n 1 640 (303 nicht anwendbar = M3). Kopfzeile gegen h3.json.

### F5 · Die Engine über die Zeit · 7,0 × 4,3 Zoll

**Warum:** P trägt die Zahlen, die der Text vor H4 braucht; die Statusgrammatik von E macht die Ereignisauswahl
prüfbar; das Placebo-Band zeigt, dass ETH PM2 nur zehn zulässige Placebo-Tage hat. Vorlagen:
`praktiker/f5_praktiker.png`, `empirie/f5_empirie.png` (Status, Fenster).

**Daten.** `results/p2/manager_oi_share.csv`; `results/p2/params/{CCY}_{pm,pm2}.json` (jede Zeile, alle Arten, nicht
die Overrides); `results/p2/events.csv`; `results/p2/reference_book.csv`; `h4.json placebo.admissible_days` und
`results/p2/h4_placebo_days.csv` (neu).

**Berechnung.** Reiner Parametereffekt je Ereignis = 100·ln(K_m/K_m_prev) am ersten Referenztag mit
`m_param_ts ≠ m_param_ts_prev` nach dem Ereignis (höchstens ein Tag später); |x| < 0,5 wird „0“.

**Aufbau.** Gemeinsame Kalenderachse 01.01.2024 bis 30.09.2026, Ticks quartalsweise („2024-01“ …), Beschriftung nur unten.

- **a** Drei Streifen BTC, ETH, HYPE (je 0,42 Zoll), Monatsanteile als Treppe (`steps-post`), gestapelt von unten: PM2
  voll `#0072B2`, Legacy-PM voll hellgrün (`#009E73`, 35 % Deckkraft), SM weiss mit Schraffur `////` und Rand `#D55E00`.
  `fillna(0)` vor dem Stapeln. y 0 bis 1, Ticks 0 und 1, „share of option OI“ nur am mittleren Streifen. Legende als eine
  Zeile über a. Streifentitel links fett 8 pt.
- **b** Fünf Schienen: „BTC legacy PM“, „BTC PM2“, „ETH legacy PM“, „ETH PM2“, „HYPE PM2“. Jede Zeile der Zeitlinie
  als grauer Strich (0,08 Zoll, `#999999`). ±14-Tage-Fenster der behaltenen Ereignisse als graue Balken (schwarz, 12 %
  Deckkraft, Höhe 0,5 Zeilen), Überlappungen werden von selbst dunkler. Ereignissymbole nach 6.2 an `event_ts`. Zahl daneben
  (7 pt): reiner Effekt in log-%, ganzzahlig mit Vorzeichen; bei zwei Ereignissen im Abstand unter 30 Tagen steht die Zahl
  des früheren links, die des späteren rechts. Zulässige Placebo-Tage als schwarze Striche 1,2 pt 0,3 Zeilen unter der
  Schiene, rechts „placebo days: 54“. Fensterbeginn PM2 (12.06.2025 23:00 UTC) als kurze Marke „PM2 window“ auf den
  PM2-Schienen von BTC und ETH, HYPE ab 11.11.2025. Titel über b: „parameter changes · number = effect of the parameters
  alone on the reference straddle, log-%“.
- **c** BTC-Referenz-Straddle in % des Forwards je Manager (Farbe und Strichart), y 0 bis 32, Ticks 0 / 10 / 20 / 30,
  Gitterlinien nur hier. Direktbeschriftung am rechten Rand mit den Werten vom 17.09.2026 („SM 29.6 %“, „legacy PM 19.7
  %“, „PM2 10.0 %“). Legacy-Linie 1,2 pt in Monaten mit BTC-Legacy-Anteil ≥ 5 %, sonst 0,5 pt. Behaltene BTC-Ereignisse
  als graue Senkrechte 0,4 pt. PM2-Linie ab 13.06.2025. Titel „BTC reference book: short straddle at the forward, listed
  expiry nearest 30 days, one contract per leg“.

**Tabellen.** `fig_f5_a.csv` (month, ccy, sm, pm, pm2 nach fillna), `fig_f5_b.csv` (ccy, manager, row_ts, kinds,
event_id, status, jump_logpct, window_lo, window_hi, placebo_days), `fig_f5_c.csv` (day, tenor_days, K_sm_pct, K_pm_pct,
K_pm2_pct, legacy_thin).

**Caption.**
> **The engine over time.** Panel a is the monthly share of option open interest per manager and underlying. Panel b
> marks every parameter change of the legacy manager and of PM2 as a grey tick and the registered H4 events as
> symbols: filled when they enter the panel, half filled when kept without a cell of 20 fills on each side, and hollow
> when dropped by the one per cent dose rule. The number is the change that the parameters alone make to the capital of
> the reference straddle, in log per cent. Grey bars are the windows of 14 days on either side of each kept event; the
> windows of January and of May 2026 overlap, so \PH{h4-dup-fills} fills enter two events. Black dashes below each line
> are the days from which placebo dates may be drawn. Panel c is the capital of the BTC reference book, a short straddle
> struck at the forward on the listed expiry nearest to 30 days, one contract per leg, in per cent of the forward; the
> small saw teeth come from rolling between expiries of 21 and 36 days. Parameter changes of standard margin left the
> reference book unchanged.

**Prüfzahlen.** 18 Ereignisse: 14 behalten (13 mit Panelzellen, 1 ohne: HYPE PM2 08.01.2026), 4 weggefallen (BTC und
ETH Legacy 12.06.2024, BTC und ETH PM2 10.10.2025), Panelzellen zusammen 475. Sprünge in log-%: Legacy 22.02.2025 BTC
−18,56, ETH −18,89; PM2 BTC 08.01. +1,60, 23.01. −10,49, 24.05. −7,84, 20.08. −26,05; ETH +1,61, −4,88, −3,36, −18,28;
HYPE 08.01. +1,54, 08.05. −7,43, 24.05. −37,43, 20.08. −20,33; weggefallene 0. Werte am 17.09.2026 (BTC): SM 29,61,
Legacy 19,68, PM2 10,03 % (ETH 29,71 / 19,41 / 10,94; HYPE SM 59,36, PM2 20,19, nur CSV). PM2-Anteil am OI im September
2026: BTC 90,96, ETH 71,89, HYPE 87,92 %. Zulässige Placebo-Tage: BTC PM2 54, ETH PM2 10 (16. bis 25.07.2025), HYPE PM2
67, BTC Legacy 363, ETH Legacy 319. Doppelte Fills 6 527 (BTC 1 457, ETH 2 861, HYPE 2 209). Gefüllte Symbole genau
die Zeilen mit `kept` und `panel_cells > 0`.

### F6 · Der Preis des Kapitals (H4) · 7,0 × 4,2 Zoll

**Warum:** Nur residualisierte Bins haben die Steigung β; eine Gerade über rohe Paare (P) oder rohe Terzile (M) ist
eine unehrliche Kodierung. Der Streifen zeigt, woraus β identifiziert ist; die Prüfliste zeigt beide Kriterien. Vorlagen:
`empirie/f6_empirie_SYNTHETIC.png` (b, c), `mechanismus/f6_proto_a_real_bc_synth.png` (Beschriftung der Mechanismen).

**Daten.** `data/p2/derived/h4_panel.parquet` (Paare `event_id, cell`) ⋈ `results/p2/h4_doses.csv`;
`results/p2/fig_h4_events.csv`; `results/p2/h4.json`; `results/p2/h4_placebo.csv`; `results/p2/sensitivity_h4.json`;
`results/p2/fig_h4_fwl_bins.csv` (neu, Abschnitt 10).

**Aufbau.** Linke Spalte 3,3 Zoll: a (2,55 Zoll hoch), darunter d (1,1 Zoll). Rechte Spalte 3,5 Zoll: b (1,95 Zoll), darunter
c (1,7 Zoll). Kopfzeile über allem: „13 events · 475 cell-event pairs · 91 446 rows from 84 919 fills (6 527 in two
windows) · 141 day clusters · 322 day × underlying effects“.

- **a** 13 Zeilen nach Ereignisdatum, Beschriftung „2025-02-22 BTC legacy“ usw. Je Paar ein Zeichen bei x = 100·Dosis:
  Verkauf ▼ gefüllt 0,15 Zeilen über der Linie, Kauf ▲ hohl 0,15 darunter, 2,5 pt. Median je Zeile schwarzer Strich.
  Graues Band |x| < 1 über alle Zeilen, oben beschriftet „|dose| < 1 log-%: {Anteil} of pairs“. n Paare rechts. x
  linear −46 bis +4, Ticks −40, −30, −20, −10, 0, „dose: change in log capital of the cell, log-% (< 0: capital got
  cheaper)“.
- **b** Mit `fig_h4_fwl_bins.csv`: x = residualisiertes post × Dosis in log-%, y = residualisierter Halbspread in bp des
  Index, 20 gleich besetzte Bins als schwarze Kreise mit Fläche proportional zu den Fills; Gerade durch den Ursprung mit
  Steigung β/100 schwarz 1,0 pt; Text im Panel „β = {stat} bp per log unit · 90 % interval [{lo}, {hi}], descriptive“;
  unter der x-Achse ein Streifen 0,15 Zoll mit dem Histogramm der residualisierten x (40 Bins, grau). Achsen
  „post × dose, residualised, log-%“ und „half spread, residualised, bp of index“.
  **Ersatz, nur falls die Inferenz die Bins nicht liefert:** Kontraste innerhalb des Ereignisses aus
  `fig_h4_events.csv`, je Ereignis und Terzil k x = 100·(t_k_median_dose − Mittel der drei Terzile), y = (t_k_y_post −
  t_k_y_pre) − Mittel der drei Terzile, 39 hohle graue Kreise, **keine Gerade**; y-Achse „within-event contrast, bp of
  index (no day effects)“, Text „no fitted line: binned residuals not available“.
- **c** Histogramm der 100 Placebo-β (grau, 20 Bins über die Spanne einschliesslich β), ganzzahlige y-Ticks, P95
  gestrichelt schwarz „placebo P95“, β durchgezogen schwarz 1,5 pt „estimate“. Prüfliste über dem Panel, 7 pt: „β > 0
  and one-sided wild p = {p} ≤ 0.05: met / not met“, „β above placebo P95 ({p95}): met / not met“, fett „H4: rejected / not
  rejected“. Die Zeile wird aus `criteria` gebildet und muss `rejected` treffen. Unten im Panel „placebo days: BTC 54 · ETH
  10 · HYPE 67 · legacy 363 / 319“.
- **d** Forest nach 6.5: „registered“ (β aus h4.json, Intervall als „descriptive“ gekennzeichnet), explorativ „BTC
  only“, „ETH only“, „HYPE only“ (`sensitivity_h4.json by_ccy`), n = Cluster. Senkrechte bei 0 gestrichelt, Schraffur β
  ≤ 0 hinter der registrierten Zeile. x „β, bp of index per log unit of capital“.

**Tabellen.** `fig_f6_a.csv` (event_id, ccy, manager, cell, side, dose_logpct, n_pre, n_post), `fig_f6_b.csv` (Bins
oder Ersatz, mit Spalte `mode`), `fig_f6_c.csv` (rep, beta; dazu p95, β, p, criteria), `fig_f6_d.csv`.

**Caption.**
> **The price of capital (H4).** Panel a shows the dose, the change in log capital that a parameter change makes to a
> cell, for each of the \PH{h4-pairs} cell and event pairs of the \PH{h4-events} events in the panel, sells above and
> buys below each line, with the median as a bar. Panel b is the half spread against the post-event dose after removing
> the cell by event and the day by underlying effects, in 20 bins of equal size; the line has the slope $\beta$, whose
> interval is descriptive because the registered p-value comes from restricted residuals. Panel c places $\beta$ among
> the estimates at 100 placebo dates and lists both registered criteria. Panel d gives $\beta$ per underlying, for
> exploration. Most doses are close to zero or negative, so $\beta$ is identified from parameter changes that made
> capital cheaper. To read the slope: capital ten per cent cheaper is a dose of $-0.105$, which predicts a change in the
> half spread of $-0.105\,\beta$ basis points of the index.

**Prüfzahlen.** 13 Zeilen; Paare je Ereignis 25, 25, 27, 38, 43, 50, 37, 40, 54, 52, 29, 35, 20 (Summe 475, gleich
`fig_h4_events.csv n_cells`); Dosis über die Paare: Median −0,634 log-%, Minimum −44,21, Maximum +2,20, 11,2 % positiv,
48,6 % unter −1 log-%, 44,4 % mit |Dosis| < 1 log-%; 91 446 Zeilen, 84 919 Fills, 141 Cluster, 322 Tag × Basiswert; 100 endliche Placebo-β. β, lo, hi,
p, p95 und `criteria` gegen h4.json; Steigung der Geraden = β.

### A1 · Trifft der Nachbau die Chain? · 7,0 × 2,5 Zoll (Anhang)

**Warum:** Die registrierte Schwelle hängt am Median; M zeigt ihn je Zeile mit n, P b zeigt, dass der Fehler nicht mit
der Buchgrösse wächst. Vorlagen: `mechanismus/a1_proto.png` (a), `praktiker/a1_praktiker.png` (b).

**Daten.** `results/p2/validation.csv`, Filter `status == "ok"` und `is_initial == True`; Schwellen aus
`validation_summary.json` (`thresholds.median = 0.001`, `thresholds.p95 = 0.01`).

**Aufbau.** a 4,2 Zoll breit, b 2,6 Zoll.

- **a** Acht Zeilen (`kind == "single"`): BTC SM, BTC legacy PM, BTC PM2, ETH SM, ETH legacy PM, ETH PM2, HYPE SM,
  HYPE PM2. x = |rel_err| log 1e−13 bis 1e−1; exakte Nullen in einem grauen Randstreifen links bei 3e−13, beschriftet
  „exact“. Zeichen nach Manager 2 pt, vertikale Streuung ±0,2. Median als schwarzer Strich 1,2 pt über 0,6 Zeilen, p95
  als schwarzer Strich 0,6 pt. Schwellen senkrecht: 1e−3 schwarz gestrichelt „median bound 0.1 %“, 1e−2 schwarz
  Strichpunkt „p95 bound 1 %“, direkt beschriftet. n rechts.
- **b** Bücher (`kind == "book"`): x = n_legs log 2 bis 300, y = |rel_err| log 1e−13 bis 1e−1 mit Randstreifen „exact“
  unten, Zeichen nach Manager, Schwellen waagerecht wie in a. Text im Panel: „largest miss 0.05 USDC on K up to 19.5 M
  USDC“ und „26 books from 20 maker-days (BTC 7, ETH 18, HYPE 1)“. MM nur in der CSV.

**Tabellen.** `fig_a1_a.csv`, `fig_a1_b.csv` (mit MM-Zeilen und Spalte `drawn`).

**Caption.**
> **Does the replica match the chain?** Absolute relative deviation of initial-margin capital between each offline
> replica and \texttt{eth\_call} on the deployed contracts, for single contracts per underlying and manager (panel a)
> and for the opening books of 20 maker-days against their number of legs (panel b). Exact matches sit in the strip on
> the left of panel a and at the bottom of panel b. The lines are the registered bounds for the median (0.1 per cent)
> and the 95th percentile (1 per cent). One single HYPE contract under PM2 hit a reverting call and is left out. In the
> PM2 window no fill uses a feed older than the limits of the validation blocks. The replica follows the contracts on
> chain; the venue's off-chain engine discounts PM2 at a flat two per cent.

**Prüfzahlen.** n je Zeile 100, HYPE PM2 99; exakte Nullen (IM, Einzel) BTC PM2 19, BTC SM 45, ETH PM2 15, ETH SM 53,
HYPE SM 49, Summe 181; grösster IM-Einzelwert 8,88e−8 (ETH PM2); grösster Median 3,18e−9 (ETH legacy PM); Bücher 77
IM-Zeilen, 2 bis 245 Beine, grösster Wert 3,45e−8 (ETH legacy PM), grösste absolute Abweichung 0,0503 USDC, K_chain bis
19 494 690 USDC; 1 Revert-Fall (2 Zeilen). Der Satz zum Feed-Alter wird im Bau gegen `capital.parquet` geprüft (Referee:
im PM2-Fenster p99 Vol 119 s, Forward 95 s); trifft er nicht zu, entfällt er.

---

## 8 · GIF der Kapitalfläche

**Inhalt.** BTC, Seite short, nur PM2, als 3D-Fläche im Aussehen von T1 (Höhe IV, Farbe `cividis` = Kapital in % des
Forwards, Iso-Linien 8 und 12 % mit Beschriftung). In der Ecke oben rechts „SM, same ATM 30 d short: {x} %“ aus dem
SM-Gitter desselben Bildes. Darunter ein Zeitstreifen mit dem BTC-Referenz-Straddle je Manager (Farbe und Strichart
wie F5 c), laufendem Cursor und den behaltenen PM2-Ereignissen als Senkrechte mit Stufenzahl in einfachen Prozent.

**Bilder.** Jeden Mittwoch 08:00 UTC vom 18.06.2025 bis 16.09.2026 (66 Bilder), dazu der T1-Block 17.09.2026 08:00 UTC als
letztes Bild. Für jedes behaltene BTC-PM2-Ereignis (08.01., 23.01., 24.05., 20.08.2026) drei Tagesbilder: letzter
08:00-Block vor dem Ereignis, erster danach und der folgende Tag; das erste Bild danach wird 6 Bilder lang gehalten
(1,5 s) und trägt ein Banner. 4 fps, rund 25 s. Bannertexte aus `events.csv` und `reference_book.csv`, einfache Prozent:
„8 Jan 2026 · margin parameters · straddle +1.6 %“, „23 Jan 2026 · scenario weights · straddle −10 %“, „24 May 2026 ·
vol shocks, contingencies, scenarios · straddle −7.5 %“, „20 Aug 2026 · parameter bundle incl. spot grid ±17 % → ±14 %
· straddle −23 %“ (zweizeilig, wenn nötig).

**Ehrlichkeit.** Feste Farbskala über alle Bilder (`p2surface.fit_limits`), auf dem Farbbalken gedruckt. Jedes Bild zeigt
Datum, Uhrzeit und Block. Verfälle ohne frischen Feed (älter als `LIVE_MAX_AGE`) fallen weg, Knoten ausserhalb der
lebenden Verfälle in `NA_COLOR` statt extrapoliert; eine Plakette „{k} expiries without fresh feed left out“, wenn
k > 0. Ein Wochenbild ohne lebenden Verfall wird übersprungen und in der Tabelle vermerkt. Hervorgehoben werden nur die
festen Iso-Linien, keine nachträglich gewählte.

**Format.** Master 1200 × 675 px für README und X; Banner und Datum mindestens 32 px, Achsen und Ticks mindestens 22 px.
GIF mit globaler 256-Farben-Palette unter 8 MB; MP4 1280 × 720 über `animate.write_mp4`; statisches Endbild als PNG
(zugleich Poster im README). Dateien `docs/media/BTC_p2_capital_pm2.gif`, `.mp4`, `_end.png`; Tabelle
`results/p2/gif_frames.csv` (Bild, Datum, ts, Block, Haltedauer, Verfälle, weggelassene Verfälle, K min/Median/max,
Banner). Bau über `p2surface.animate(managers=("pm2",), …)` mit den Ergänzungen Iso-Linien, Haltebilder mit Banner,
Einheit %, Ecke SM; Lauf nur über `scripts/p2_heavy.py` (Maschinensperre, Feed-Historie quartalsweise).

**Prüfzahlen.** 67 reguläre Bilder plus 12 Ereignisbilder; letztes Bild identisch mit T1 a (gleiche K-Werte je Knoten);
Stufen im Zeitstreifen = exp(Sprung aus F5) − 1: +1,6 %, −10,0 %, −7,5 %, −22,9 %.

---

## 9 · Social-Karten 1600 × 900

Gemeinsam: `figures_social`-Stil (feste Grösse ohne `bbox tight`), Schrift mindestens 28 px, alles innerhalb des Rahmens
(Test auf `tightbbox`), jede Zahl im Titel im Bild ablesbar, Farbe doppelt codiert wie im Papier, einfache Prozent.
Fusszeile „Derive, chain 957 · replica of the deployed margin contracts · pre-registration commit c4fcb59“. Ausgabe
`paper2/social/s1_three_engines.png`, `s2_straddle_vs_call.png`, `s3_verdicts.png`, Tabellen `results/p2/fig_s{1,2,3}.csv`.

1. **„One short BTC straddle. Three margin engines.“** Links zwei Drittel: Zeitreihe aus F5 c (2024-01 bis 2026-09,
   Linien 4 px, Strichart je Manager), an der PM2-Linie die Stufen „+2 %“, „−10 %“, „−8 %“, „−23 %“, Senkrechte
   „parameter changes kept for H4“. Rechts drei grosse Zahlen „30 %“, „20 %“, „10 %“ mit Strichmuster und Namen darunter.
   Untertitel „Capital for one short straddle at the forward, listed expiry nearest to 30 days (22 d on 17 Sep 2026), %
   of forward. Capital for a hypothetical book, not a balance.“ Vorlage `mechanismus/card_straddle_1600x900.png`.
   Prüfzahlen 29,61 / 19,68 / 10,03 %.
2. **„Under PM2 a short straddle needs less capital than one short call.“** Zwei Gruppen (PM2, SM), je zwei Balken ab 0:
   „one short call“ (Umriss in Managerfarbe, Füllung weiss) und „short straddle“ (voll in Managerfarbe; SM mit
   Schraffur), Werte über den Balken. Beide aus derselben Zeile von `reference_book.csv` (17.09.2026, Strike = Forward,
   22 Tage), Einzelbeine aus der Erweiterung (Abschnitt 10). Untertitel „BTC, 17 Sep 2026, 08:00 UTC, strike at the
   forward, 22 days, % of forward. Capital, not risk.“ **Titelregel:** Der Titel gilt nur, wenn K_PM2(Straddle) <
   K_PM2(Call); sonst lautet er „Under PM2 the second leg of a straddle adds little capital“, sofern K_PM2(Straddle) −
   K_PM2(Call) < 0,25·K_PM2(Call); sonst entfällt die Karte und die Reserve rückt nach. Vorlage
   `praktiker/social_2_straddle_vs_leg.png` (dort Beine aus verschiedenen Objekten, nicht übernehmen).
3. **„Four pre-registered tests. Four verdicts.“** Vier Zeilen H1 bis H4, je Zeile links die Aussage in Klartext
   („The capital denominator reorders the map“, „The next contract in a big book is cheap“, „PM2 needs less than half of
   SM's capital“, „Cheaper capital, tighter spreads“), in der Mitte eine Urteilsleiste (Schätzer, Intervall, Schwelle,
   schraffierte Ablehnungsseite; H4: β mit Placebo-P95 als Marke und „one-sided p = …“), rechts das Urteil „rejected“
   oder „not rejected“. Zahlen nur aus `h1.json` bis `h4.json`; Urteile nach denselben Regeln wie `ruler`. Titel und
   Aufbau hängen nicht vom Ausgang ab.

**Reserve:** „One parameter bundle, one fingerprint“: Dosiskarte BTC PM2 20.08.2026, Verkaufsseite, einfache Prozent je
Zelle, Kreuz nach der Panelregel; Titelzahlen werden aus der Karte gebildet. Vorlage
`mechanismus/f6_proto_a_real_bc_synth.png` Panel a, ohne `PuOr` (Grau nach |Wert|).

**Verworfen:** P-Karte 1 (dieselbe Reihe wie Karte 1, Titel abgeschnitten, 35 % nicht im Bild ablesbar), P-Karte 3
(zwei Populationen, kippt im letzten Regime), Keyframe als Karte (wird Endbild des GIF).

---

## 10 · Datenvertrag: was vor dem Bau geliefert werden muss

Alles hier ist explorativ oder deskriptiv und wird so gekennzeichnet; keine registrierte Zahl ändert sich.

| Lieferung | Wer | Für | Inhalt | Ersatz, falls sie fehlt |
|---|---|---|---|---|
| `results/p2/fig_h4_fwl_bins.csv` | `inference_p2_h4.py` | F6 b | `kind = bin`: bin, x_mean, y_mean, n_rows, n_fills (20 gleich besetzte Bins der nach α und γ residualisierten post·Dosis bzw. y, x in log-%); `kind = hist`: x, x_hi, count (40 Bins); dazu `fwl_slope` = Σx̃ỹ/Σx̃² über alle Zeilen | Kontraste innerhalb des Ereignisses ohne Gerade (F6 b) |
| `results/p2/h4_placebo_days.csv` | `inference_p2_h4.py` | F5 b | timeline (event_id-Schlüssel wie `admissible_days`), day, admissible, drawn_count | Band entfällt, nur die Tageszahl steht an der Schiene |
| `sensitivity.json`: `h1_sign.within_pos`, `h1_sign.within_nonpos`, `h1_sign.sign_floor` | `inference_p2.py` | F2 c | ρ innerhalb Edge > 0 und ≤ 0 mit Intervall (gleicher Bootstrap); ρ bei zufälliger Rangfolge innerhalb der Vorzeichengruppen, 4 000 Ziehungen, Seed 20260924: mean, p05, p95 | Zeilen und Band entfallen; Satz im Text mit Verweis auf den Referee ist **nicht** zulässig, die Zahl muss aus `results/p2` kommen |
| `sens_h2.csv`, `sens_h3.csv`: `group = regime=R1…R4` | `inference_p2.py` | F3 b, F4 b | Median mit Intervall je Regime nach 6.6 | Zeilen entfallen |
| `sens_h3.csv`: `group = account_manager=SM/PM/PM2` | `inference_p2.py` | F4 b | Median mit Intervall über die Konten je Kontomanager | Zeilen entfallen, Konten einzeln nur in der CSV |
| `reference_book.csv`: `K_<m>_call`, `K_<m>_put` | `p2surface.reference_book_series` | T2 c, Karte 2 | Kapital je Bein als Ein-Bein-Buch am selben Block, alle Manager | T2 c ohne Strichpunktlinie, Karte 2 entfällt |
| `figdata_p2.binding_rule` | `figdata_p2.py` | T1 c/d | Abschnitt 7 T1, mit Summentest | kein Ersatz, T1 wartet |
| `figdata_p2.pm2_scenarios` | `figdata_p2.py` | T2 c | Szenario-P&L je (spotShock, volShock, dampening) eines Buchs | kein Ersatz |
| `figdata_p2.cell_capital_by_regime` → `fig_f1_regimes.csv` | `figdata_p2.py` | F1, Text | Abschnitt 7 F1 | hohle Zeichen entfallen |
| `figstyle.FS_MIN`, `figstyle.MANAGER`, `figstyle.SIDE`, P2-rc ohne `bbox tight` | `figstyle.py` | alle | Abschnitt 6 | kein Ersatz |

Nicht angefordert: `h1_rho_draws.csv` (F2 zeigt kein Histogramm von ρ), `hedges_worst` in `books.py`.

---

## 11 · Prüfskript `scripts/p2_figure_check.py` und Tests

Muster `scripts/p1_figure_check.py`, ohne tautologische Vergleiche: Das Skript liest die gedruckten Werte aus
`fig_<slot>_<panel>.csv` (Spalte `printed` und volle Werte) und vergleicht sie mit den Quellen, nicht mit sich selbst.
Es schreibt `docs/paper2/ABBILDUNGEN.md` und endet mit Status ≠ 0 bei jeder Abweichung.

- **Quelle:** T2 gegen `faktoren.csv` (genau vier Zeilen); T1 gegen `probe_BTC_2026-09-17_summary.json` und das Gitter; F1
  gegen `fig_edge_maps.csv`; F2 gegen `h1_cells.csv` und `h1.json`; F3 gegen `fig_h2_dist.csv`, `h2.json`, `sens_h2.csv`;
  F4 gegen `fig_h3_series.csv`, `h3.json`, `sens_h3.csv`; F5 gegen `reference_book.csv`, `events.csv`,
  `manager_oi_share.csv`, `h4.json`; F6 gegen `h4_doses.csv`, `h4_panel.parquet`, `fig_h4_events.csv`, `h4.json`,
  `h4_placebo.csv`, `sensitivity_h4.json`; A1 gegen `validation.csv` und `validation_summary.json`.
- **Urteile:** jede Urteilszeile (F2 c, F3 b, F4 b, F6 c, Karte 3) wird aus Regel und Grenzen neu gebildet und muss
  `rejected` treffen; H4 aus `criteria`.
- **Zählungen:** Kreuze F1 und F2 je 37 (Zellen unter 200 Fills einschliesslich Kombinationen ohne Fill); 173 Punkte in F2
  b; F1-Streifen 173 SM-Punkte und 128 Legacy-Punkte; F5 b 14 gefüllte oder halb gefüllte und 4 hohle Symbole, gefüllt
  genau `kept & panel_cells > 0`; F6 a 13 Zeilen und 475 Zeichen; F4 a acht Bins mit je mindestens 20 Maker-Tagen; A1
  n je Zeile.
- **Identitäten:** κ in F1 = 100·`sum_K`/`sum_index` in `h1_cells.csv`; T2 c, F5 c und Karte 1 zeigen denselben
  Straddle-Wert (10,03 / 29,61 %); letztes GIF-Bild = T1 a; F6 b Gerade = β und `fwl_slope` = β (relativ ≤ 1e−8);
  Summen der Regime = gepoolte Summen (F1).
- **Gestalt** (auch als Test in `tests/test_p2_figures.py`): PDF-Breite 3,4 bzw. 7,0 Zoll ± 0,02; keine Schrift unter
  7 pt; alle Texte innerhalb der Leinwand; genau eine Abbildung mit `Axes3D` (T1); keine Farbe ausser Managerfarben,
  Grau und Schwarz in F2 bis F6 und A1 (Palette der Artists prüfen); ▲/▼ nur als Seitenzeichen; Karten 1600 × 900 px;
  GIF unter 8 MB.
- **Captions:** kein Gedankenstrich („—“, „–“ als Satzzeichen) in den Captions von `paper2/main.tex`; jedes `\PH{key}`
  der Captions steht im Zahlenblatt.

---

## 12 · Änderungen an `paper2/main.tex`

- Alle neun Captions werden durch die Entwürfe oben ersetzt. Insbesondere entfallen in T1 „capital in USDC“, in F1
  „capital per contract in USDC“ und „each panel is shaded on its own scale“, in F2 „lines connect the rank of each
  cell“, in F5 „recomputed at every parameter change“ (die Reihe ist täglich um 08:00 UTC gerechnet), in F6 die
  Zweipanel-Beschreibung.
- Neue Platzhalter für `docs/paper2/MANUSKRIPT.md` und das Zahlenblatt: `p1-map-fig` (Nummer der Nominal-Karte in Paper 1),
  `h1-pos` (Zellen mit positivem Edge), `h3-over63` (Maker-Tage mit mehr als 63 Optionen), `h4-pairs`, `h4-dup-fills`;
  vorhandene Schlüssel `h1-cells`, `h2-n`, `h3-days`, `h4-events` werden weiterverwendet.
- Reihenfolge der Floats wie im Gerüst: T1 und T2 im Abschnitt Engine, F1 in Daten und Messung, F2 bis F6 in den
  Ergebnissen, A1 im Anhang. F3 und F4 als `figure[t]` mit identischer Höhe.

---

## 13 · Dateien

- Diese Vorgabe: `docs/paper2/ABBILDUNGSWAHL.md`
- Entwürfe und Jury: `docs/paper2/entwuerfe/{mechanismus,empirie,praktiker,jury_referee,jury_gestaltung}.md`
- Prototypen und Messung: `data/p2/fig_proto/{mechanismus,empirie,praktiker,jury}/`
- Zu bauen: `derive_surface/figures_p2.py`, `derive_surface/figdata_p2.py`, Ergänzungen in `figstyle.py`,
  `p2surface.py`, `inference_p2.py`, `inference_p2_h4.py`; `scripts/p2_figure_check.py`; `tests/test_p2_figures.py`;
  Ausgaben `paper2/figures/`, `paper2/social/`, `docs/media/BTC_p2_capital_pm2.*`, `results/p2/fig_<slot>_<panel>.csv`,
  `results/p2/gif_frames.csv`, `docs/paper2/ABBILDUNGEN.md`.
