# Abbildungsentwurf Paper 2, Linse Mechanismus

Stand 25.09.2026 · Entwurf für die Jury (Muster Paper 1: drei Linsen, zwei Juroren) · nichts committet.

Die Abbildungen sollen erklären, **wie** die Engine Kapital bildet (Szenarien, Netting, Static Discount, Long gegen
Short, SM gegen PM2) und **warum** sich die Karte von Paper 1 dadurch verschiebt. Jede Hypothesenabbildung bekommt
deshalb neben dem Befund ein Mechanismus-Panel, das den Befund vorhersagbar macht.

Prototypen (Pilotdaten, Schnitt 17.09.2026) unter `data/p2/fig_proto/mechanismus/`, gebaut mit
`python3 data/p2/fig_proto/mechanismus/proto_mechanismus.py [T1 T2 F1 F2 F5 F6 A1 CARD]`:

| Datei | Slot | Daten |
|---|---|---|
| `t1_proto.png` | T1 | echt: Probe-Gitter BTC 17.09.2026 08:00 UTC, Engine-Nachbau für die bindende Regel |
| `t2_proto.png` | T2 | echt: `results/p2/semantik/faktoren.csv`, Engine-Nachbau (Straddle) |
| `f1_proto.png` | F1 | echt: `capital.parquet` ⋈ `markouts.parquet`, Engine-Nachbau (Anatomie) |
| `f2_proto_synth.png` | F2 | **synthetisch**, Wasserzeichen PROTOTYP |
| `f5_proto.png` | F5 | echt: `manager_oi_share.csv`, `params/`, `events.csv`, `reference_book.csv` |
| `f6_proto_a_real_bc_synth.png` | F6 | Panel a echt (`h4_doses.csv`), Panels b und c **synthetisch** |
| `a1_proto.png` | A1 | echt: `validation.csv` |
| `card_straddle_1600x900.png` | Social-Karte 1 | echt: `reference_book.csv` |

Zu jeder PNG liegt die Zahlentabelle als `fig_*.csv` daneben (im Endbau `results/p2/fig_*.csv`). Keine
Teststatistik wurde berechnet; F3 und F4 sind nur beschrieben, weil ihr Kern die Verteilung der H2- und
H3-Grösse selbst ist. Während der Arbeit sind die Inferenztabellen erschienen (`h1.json` … `h4.json`,
`h1_cells.csv`, `fig_edge_maps.csv`, `fig_capital_by_manager.csv`, `fig_h2_dist.csv`, `fig_h3_series.csv`,
`fig_h4_events.csv`, `h4_placebo.csv`, `sens_*.csv`). Unten sind nur ihre Spalten und Schlüssel verplant; ihre
Werte wurden weder gelesen noch in einen Prototyp übernommen.

---

## 1 · Die Mechanik in fünf Sätzen, und was die Prototypen davon zeigen

1. **Kapital ist `K = Σ p·q − net_IM(q; C = 0)`.** Unter SM zählt eine Long-Option nichts, ein Kauf kostet seine
   Prämie. Ein Short kostet `max(15 % − OTM, 13 %)` des Spots (Put zusätzlich gegen 1,05 × MM geprüft).
2. **PM2 nimmt das schlechteste Szenario des ganzen Buchs** (Spot ±14 % × Vol hoch/unverändert/runter, gedämpfte
   Tails ×0,34 bis ×6, zwei Skew-Szenarien, Basis-Kontingenz), plus Kontingenzen und Static Discount. Der
   Legacy-PM rechnet ähnlich, aber mit IM-Faktor 1,25 und Static Discount 0,95 auf positive Werte.
3. **Für den Einzelkontrakt entscheidet die Seite, nicht der Manager** (F1, echte Daten BTC, PM2-Fenster):
   Käufe binden 0,07 bis 17 % des Nominals unter SM und 0,07 bis 11 % unter PM2, Verkäufe 12,8 bis 15,1 % (SM),
   7,8 bis 17,7 % (PM2) und 8,5 bis 24,3 % (Legacy-PM). Für tief im Geld liegende kurze Verkäufe ist PM2 sogar teurer
   als SM (17 bis 18 % gegen 15 %).
4. **Der grosse PM2-Vorteil entsteht erst im Buch** (T2c, Engine am T1-Block): ein kurzer ATM-Straddle über 30 Tage
   bindet unter PM2 9,7 % des Forwards, dieselben zwei Beine getrennt 23,5 %, unter SM 29,0 %. Das ist die Mechanik
   hinter H2 und H3.
5. **Parameteränderungen verschieben die Karte zellweise** (F6a, echte Dosen): der 23.01.2026 (Tail-Gewichte
   gesenkt) traf fast nur OTM-Verkäufe (|Δ| unter 40 %, am stärksten −14 bis −27 log-% bei 7 bis 90 Tagen), dort,
   wo in T1c die gedämpften Tail-Szenarien binden; der 20.08.2026 (Gitter ±17 → ±14 %) verbilligte jede besetzte
   Verkaufszelle um 21 bis 31 log-%, Käufe kaum. Fast alle Dosen
   sind ≤ 0: das natürliche Experiment besteht im Wesentlichen aus Lockerungen.

Daraus folgt die Leselinie der Abbildungen: T1/T2 erklären die Regel, F1 den Nenner je Zelle, F2 dessen Wirkung auf
die Karte (H1), F3/F4 das Buch (H2/H3), F5/F6 die Zeit und die Dosis (H4), A1 die Treue des Nachbaus.

---

## 2 · Regeln für alle Slots (aus Paper 1 plus Ergänzungen)

- Breiten 3,4 und 7,0 Zoll, Satz 1:1, Schrift ≥ 7 pt überall. **Achtung:** der Code von Paper 1 setzt in F5 und in
  Seitennotizen 6,0 und 6,5 pt (`figures_p1.py`, `_side_note`, Tick-Labels); nicht kopieren. `figstyle` sollte für
  Paper 2 ein `FS_MIN = 7.0` bekommen und ein Test jede Textinstanz prüfen.
- **Feste Manager-Kodierung** in allen Abbildungen, doppelt codiert: PM2 blau `#0072B2`, durchgezogen, Kreis; SM
  zinnober `#D55E00`, gestrichelt, Quadrat; Legacy-PM grün `#009E73`, gepunktet, Raute (entspricht
  `p2surface.MANAGER_COLORS/STYLES`). Das Trio besteht den CVD-Validator (Deutan ΔE 11,0, Tritan 8,6, Normalsicht
  18,7), die Striche tragen die Unterscheidung zusätzlich in Graustufen.
- **Feste Seiten-Kodierung:** Maker-Kauf ▲, Maker-Verkauf ▼ (Kauf = Long, Verkauf = Short, immer beides nennen).
- **Einheit für Kapital:** % des Forwards (Engine-Gitter) oder % des Nominals (Fills). USDC je Kontrakt nur in den
  CSV-Tabellen; es misst vor allem das Preisniveau (Faktor 1 599 zwischen BTC und HYPE, Paper 1).
- Karten: eine Zahl je Zelle, Zellen unter 200 Fills als leeres Kreuz (bei Dosen: unter 20 Fills vor dem Ereignis,
  die Panel-Regel von H4). Sequenzielle Karten grau oder `cividis`, divergierende nur mit gedrucktem Vorzeichen.
- Mechanik-Panels aus dem Engine-Nachbau nennen Block, Kontrakt und Parameterstand im Bild (Fusszeile oder
  Achsentitel), damit niemand eine Einzelbewertung für einen Zellmittelwert hält.
- Jede Zahl der Abbildung als `results/p2/fig_<slot>_<panel>.csv`; Hypothesenzahlen werden nur gelesen
  (`h1.json` … `h4.json`), nie in `figures_p2.py` neu gerechnet.

---

## 3 · Die neun Slots im Überblick

| Slot | Frage | Grösse (Zoll) | Prototyp |
|---|---|---|---|
| T1 | Welche Regel setzt das Kapital auf der Oberfläche? | 7,0 × 4,3 | ja, echt |
| T2 | Was liefert `get_margin`, und wie baut PM2 R? | 7,0 × 2,75 | ja, echt |
| F1 | Was kostet ein Kontrakt je Zelle und Manager, und woraus besteht das? | 7,0 × 4,7 | ja, echt |
| F2 | Ordnet der Kapitalnenner die Karte um? (H1) | 7,0 × 3,1 | ja, synthetisch |
| F3 | Was kostet der nächste Kontrakt im Maker-Buch? (H2) | 3,4 × 3,8 | nein (Beschreibung) |
| F4 | Was ist Netting wert? (H3) | 3,4 × 3,8 | nein (Beschreibung) |
| F5 | Wie hat sich die Engine über die Zeit bewegt? | 7,0 × 5,0 | ja, echt |
| F6 | Folgt der Halbspread dem Preis des Kapitals? (H4) | 7,0 × 4,3 | ja, a echt, b/c synthetisch |
| A1 | Trifft der Nachbau die Chain? | 7,0 × 2,7 | ja, echt |

---

## 4 · Slots im Einzelnen

### T1 · Die Engine-Sicht der Oberfläche (7,0 × 4,3 Zoll, einzige 3D-Abbildung)

- **Zweck:** Kapital als Fläche über derselben Geometrie wie die Vol-Oberfläche zeigen und benennen, welche Regel
  sie an jeder Stelle setzt.
- **Daten:** `p2surface.capital_grid("BTC", ts, manager ∈ {pm2, sm}, "short")` am Block der Bildunterschrift
  (Pilot: `data/p2/surface/probe_BTC_2026-09-17_grid.csv`, 37 Deltas × 20 Laufzeiten, Spalten `delta, tenor_days,
  iv, K_per_forward_bp, strike, forward, spot, is_call, rate, *_conf`). Die bindende Regel je Knoten neu:
  `figdata_p2.binding_rule(grid, params)` über `margin_pm2._span` (Index des schlechtesten Szenarios, Basis) und
  die SM-Zweige aus `OptionMarginParams`. Parameter `Timeline(ccy, mgr).at(ts)`.
- **Kodierung:** Panels a/b 3D (Höhe IV in %, Farbe K in % des Forwards, `cividis`, gemeinsame Skala, gleiche
  Sicht elev 24 / azim −128). Darunter c/d als **2D-Streifen**: bindende Regel als Grauflächen mit Schraffur
  (PM2: Spot +14 % Vol hoch, Spot −14 % Vol hoch, Tail ×2 gedämpft, Tail ×0,34 gedämpft; SM: 15 % − OTM,
  13 %-Boden, Put 1,05 × MM) und Iso-Kapital-Linien 5/8/11/14 % mit eigener Strichart und Beschriftung, dieselben
  Striche auf der Farbskala markiert. Graustufen: `cividis` ist monoton in der Helligkeit, die Streifen tragen
  Schraffur und Linienbeschriftung.
- **Kernaussage (5 s):** SM verlangt fast überall 13 bis 15 % des Spots nach einer einzigen Regel; PM2 reicht von 3
  bis 14 % und wird fast überall von einem Szenario gesetzt, Spot ±14 % mit Vol-Schock nach oben.
- **Fallen:**
  - Bodenprojektion im 3D-Achsensystem ausprobiert und verworfen: mplot3d sortiert Flächen nach Tiefe, Boden und
    Iso-Linien verschwinden hinter der Fläche. Deshalb 2D-Streifen (erlaubt, nur eine 3D-Abbildung zählt).
  - Höhe und Farbe sind zwei Flächen: z-Achse heisst „implied vol, %“, Farbskala „capital per short contract, % of
    forward“, sonst liest man IV als Kapital.
  - Die gemeinsame Skala macht SM zu einer fast einfarbigen Fläche. Das ist die Aussage, muss aber in der
    Unterschrift stehen.
  - SM rechnet in % des Spots, das Bild in % des Forwards: 13 % Spot erscheinen bei 1 Jahr als 12,4 % Forward.
  - Knoten zwischen Verfällen sind interpoliert (Forward, Zins linear, Konfidenz Minimum); Knoten sind OTM (Call
    für K ≥ F), Achse „call delta (put = Δ − 1)“.
  - Der Block darf kein Ereignistag sein (in F5c prüfen); nach dem 20.08.2026 gilt das ±14-%-Gitter, der Text muss
    das Regime nennen.

### T2 · Was `get_margin` liefert und wie PM2 R bildet (7,0 × 2,75 Zoll)

- **Zweck:** Die Lesart `C − net` als Fehlerquelle zeigen und am selben Ort die Regel „schlechtestes Szenario des
  Buchs“ sichtbar machen, die H2 und H3 erklärt.
- **Daten:** a und b aus `results/p2/semantik/faktoren.csv`, Zeilen `messung` beginnt mit „historisch“, ohne
  „H0_“, `fall ∈ {A, B}` (genau vier Zeilen: 17.09. A/B, 24.09. A/B); Spalten `SM_R_engine, PM2_R_engine, V_und_SM,
  V_PM2, F_Cnet, F_R_engine`. c aus dem Nachbau am T1-Block: Referenz-Straddle wie `reference_book` (Strike =
  Forward, Verfall nächst 30 Tagen), Szenario-PnL über `margin_pm2._Params/_expiry_factors/_leg_prices/_span`,
  Kapital über `net_margin` für Straddle, beide Beine einzeln und SM.
- **Kodierung:** a waagerechte Stapel je Manager: R in Managerfarbe, −V schraffiert grau, Summe `C − net` am Ende
  (24.09.-Buch B: SM 211 + 497 = 708, PM2 99 + 497 = 596 Tsd. USDC). b Hantel je Buch auf log-Achse, hohl = auf
  `C − net`, voll = auf R, Linie bei 2 (H3-Schwelle). c Szenario-PnL in % des Forwards, x kategorial nach
  Spot-Schock (Kern ±14 % hinterlegt, Tails gedämpft, nicht massstäblich), Marker ▲ ● ▼ für Vol hoch/unverändert/
  runter, Skew als Raute, das bindende Szenario umkreist; drei Waagerechte: PM2-Kapital (9,7 %), PM2 mit getrennten
  Beinen (23,5 %, gepunktet), SM (29,0 %, gestrichelt).
- **Kernaussage (5 s):** `C − net` drückt jeden Faktor gegen 1, weil derselbe Positionswert in beiden Zählern
  steckt; PM2 verlangt für den Straddle nur sein schlechtestes Szenario, nicht die Summe seiner Beine.
- **Fallen:**
  - `faktoren.csv` enthält je Buch mehrere Messungen (H0-Liste, live); Filter explizit und Test auf vier Zeilen.
    Die Zahlen der Bildunterschrift in `main.tex` (11,86/10,76, 1,19/2,14, 2,33/3,19, 1,46/3,61) müssen daraus
    kommen.
  - Vorzeichen: V ist für Shorts negativ; gezeichnet wird −V.
  - Die PM2-Kapitallinie liegt unter dem umkreisten Szenario (Kontingenzen, IM-Faktor); das ist gewollt und wird
    in der Unterschrift gesagt, sonst wirkt es wie ein Fehler.
  - Im Prototyp ist der Strike der Knoten Call-Delta 0,5 (77 017 gegen F = 76 668); im Endbau Strike = Forward.
  - Drei Panels in 7 Zoll: Hantel-Beschriftungen (2,14 und 2,33) liegen eng; Beschriftung ober- und unterhalb.

### F1 · Was ein Kontrakt kostet, und woraus (7,0 × 4,7 Zoll)

- **Zweck:** Den Kapitalnenner je Zelle zeigen, getrennt nach Seite und Manager, und an einem Kontrakt zerlegen,
  woraus er besteht.
- **Daten:** `data/p2/derived/capital.parquet` (`trade_id, currency, ts, maker_side, amount, index_price, K_sm,
  K_pm, K_pm2`) ⋈ `data/p1/derived/markouts.parquet` (`trade_id, delta_bucket, tenor_bucket`); Filter:
  PM2-Fenster des Basiswerts (BTC/ETH ab 12.06.2025 23:00 UTC, `ts` in ms), alle drei Manager auf denselben Fills.
  Zellwert κ_c = 100·Σ K·a / Σ S·a (% des Nominals), dazu Fills je Zelle. Die Inferenz liefert
  `results/p2/fig_capital_by_manager.csv` (`window, manager, ccy, side, delta_bucket, tenor_bucket, fills,
  median_k_over_index, p25_k_over_index, p75_k_over_index, median_k_mm_over_index`), also **Mediane je Fill**. Für
  die Mechanik braucht F1 das **Verhältnis der Summen** (nur damit gilt e^K = e^N / κ exakt, und nur so passt F1 zu
  `h1_cells.csv`: κ = `sum_K / sum_index`): Spalten `sum_K, sum_index` je Manager ergänzen oder in `figdata_p2`
  aus `capital.parquet` bilden (beschreibend, keine Teststatistik). Der Median kann als Rahmenstil oder in der CSV
  bleiben. Rechte Spalte: Nachbau am T1-Block, ein
  ATM-Call 30 Tage, `figdata_p2.pm2_anatomy` (Bewertungskonvention p·q − V, Szenarioverlust, Static-Discount-Zuschlag,
  Kontingenzen), SM (Prämie bzw. Spot-Anforderung), Legacy-PM gesamt.
- **Kodierung:** 2 Zeilen (Maker-Kauf = Long, Maker-Verkauf = Short) × 3 Karten (SM, Legacy-PM, PM2), |Δ| × Laufzeit,
  **eine** logarithmische Grauskala für alle sechs Karten, eine Zahl je Zelle, Kreuz unter 200 Fills. Rechts je
  Zeile gestapelte Balken (Flächen mit Schraffur: Punkte = Prämie ohne Gutschrift, voll = Spot-Anforderung bzw.
  Szenarioverlust, Diagonale = Static Discount, Kreuz = Kontingenzen; Legacy-PM als gepunkteter Rahmen) mit dem
  bindenden PM2-Szenario als Zeile.
- **Kernaussage (5 s):** Ein Kauf kostet unter SM genau seine Prämie und unter PM2 kaum weniger, ein Verkauf 8 bis
  18 % des Nominals; beim einzelnen Kontrakt ist PM2 nur für OTM-Verkäufe langer Laufzeit deutlich billiger als SM.
- **Pilotzahlen (BTC, PM2-Fenster, 60 der 70 möglichen Zellen mit mindestens 200 Fills):** Käufe SM 0,07 bis 16,9 %, PM2 0,07 bis 10,9 %;
  Verkäufe SM 12,8 bis 15,1 %, Legacy-PM 8,5 bis 24,3 %, PM2 7,8 bis 17,7 %. Anatomie ATM 30 Tage in % des Forwards:
  Kauf SM 3,59 (Prämie), PM2 3,44 (Szenario Spot ×0,895, Vol runter), Legacy-PM 4,44; Verkauf SM 14,08, PM2 11,83
  (11,54 Szenario Spot ×1,14 Vol hoch, 0,05 Static Discount, 0,25 Kontingenzen), Legacy-PM 20,58.
- **Fallen:**
  - Die Bildunterschrift in `main.tex` sagt USDC und „jede Karte eigene Skala“. Beides verdeckt die Mechanik: USDC
    misst Preisniveau, und mit eigenen Skalen sehen Kauf- und Verkaufskarten gleich aus. Vorschlag: % des Nominals,
    eine Skala. Das ist genau der Faktor, der F2 verbindet: e^K = e^N / κ.
  - Nur BTC passt in das Bild; ETH und HYPE in `fig_f1_cells.csv` und im Text mit einem Satz.
  - Die Anatomie ist ein Kontrakt an einem Block, kein Zellmittel; so beschriften.
  - Der Static Discount ist beim Einzelkontrakt fast unsichtbar (0,05 Prozentpunkte). Nicht als Hauptmechanismus
    verkaufen; er wirkt in Büchern mit grossem |M| und im Regimewechsel vom 08.01.2026 (F6a).
  - Legacy-PM verlangt für den Long mehr als die Prämie (4,44 gegen 3,59 %): IM-Faktor 1,25 und Static Discount
    0,95 auf positive Werte. Vor dem Druck an einem `eth_call` bestätigen.
  - 20 Fills mit K_PM2 ≤ 0 bleiben in den Summen (Nachtrag 4); Log-Skala nur auf Zellwerten > 0, sonst Kreuz mit
    eigenem Zeichen.

### F2 · Die Karte in zwei Nennern, H1 (7,0 × 3,1 Zoll)

- **Zweck:** Zeigen, ob und warum die Rangfolge der Zellen kippt, wenn Edge je PM2-Kapital statt je Nominal
  gemessen wird.
- **Daten:** `results/p2/h1_cells.csv` (`cell, ccy, side, delta_bucket, tenor_bucket, fills, occupied, sum_edge,
  sum_index, sum_K, A_bp, B_bp, rank_A, rank_B, rank_shift, A_lo/A_hi, B_lo/B_hi, rank_*_lo/hi, window, capital`;
  vermutlich A = je Nominal und B = je PM2-Kapital, vor dem Bau an `h1.json` `map`/`capital` und `scale`
  prüfen; Filter `occupied`), κ = 100·`sum_K/sum_index`; `results/p2/h1.json` (`stat,
  lo, hi, rejected, threshold, n, n_days, cells_by_ccy.*`). Karten anderer Nenner (SM, Legacy-PM, MM) aus
  `fig_edge_maps.csv` bzw. `sens_h1_cells.csv` (Spalte `map`) nur in der CSV. κ muss identisch mit F1 sein (Test).
- **Kodierung:** a e^N gegen e^K doppelt logarithmisch, dazu Diagonalen konstanter κ (0,5 / 2 / 10 %): jede Zelle
  liegt auf der Diagonalen ihres Kapitalnenners, Umordnung ist Bewegung quer zu den Diagonalen. b Rang gegen Rang
  mit Winkelhalbierender und den Bootstrap-Rangintervallen (`rank_*_lo/hi`) als feine Kreuzbalken; Kasten mit ρ
  und 90-%-Intervall aus `h1.json` und der Regel „abgelehnt, wenn obere Grenze ≥ 0,5“. Marker ▲/▼ für die Seite, Farbe `cividis` für die Laufzeit (Graustufen: Helligkeit plus Form).
- **Kernaussage (5 s):** Käufe und Verkäufe liegen auf verschiedenen κ-Diagonalen, eine Grössenordnung auseinander;
  wie weit die Ränge vom Diagonalbild abweichen, ist H1.
- **Fallen:**
  - Negative Edges passen nicht auf log-log: Symlog mit hinterlegtem linearem Kern (Regel Paper 1) oder eigener
    Streifen „≤ 0“ am Rand, Anzahl nennen.
  - Die Alternative aus der Spezifikation (Linien zwischen den Rängen) wird bei rund 120 Zellen zu Spaghetti.
  - ρ nie in der Abbildung nachrechnen, nur lesen. Bindungen in den Rängen (gleiche Werte) wie in der Inferenz.
  - Die Zellen stammen aus drei Basiswerten im jeweiligen PM2-Fenster; F1 zeigt nur BTC. In der Unterschrift sagen.

### F3 · Der nächste Kontrakt im Buch eines Makers, H2 (3,4 × 3,8 Zoll)

- **Zweck:** Die Verteilung der Grenzkosten zeigen und erklären, welche Fills Kapital freisetzen.
- **Daten:** `data/p2/derived/marginal.parquet` (`ratio, status, K_single_pm2, dK_per_contract, manager, ccy, day,
  maker_side, n_legs_before, gross_before, label`) nur für das Mechanik-Panel; die Verteilung selbst aus
  `results/p2/fig_h2_dist.csv` (`label, variant, kind, x, x_hi, value`: vorgebinnt, Stichprobe der Inferenz, nicht
  neu ziehen) und `results/p2/h2.json` (`stat, lo, hi, rejected, threshold, share_nonpositive, n, n_sample,
  n_excluded, accounts`); Varianten (Einheitskontrakt, MM, Tape-Buch) aus `sens_h2.csv` nur in der CSV.
- **Kodierung:** a Histogramm von ratio auf [−1,5; 1,5] mit Überlaufbalken an beiden Enden (Anzahl beschriftet),
  Masse ≤ 0 schraffiert („setzt Kapital frei“), Schwelle 0,5 gestrichelt, Median mit 90-%-Intervall als Balken über
  dem Histogramm. b Mechanik: ratio getrennt danach, ob der Fill im bindenden Szenario des Buchs vor dem Fill Gewinn
  oder Verlust macht (neue Spalte `hedges_worst` in `books.py`: Vorzeichen des Fill-PnL in `worst` aus
  `margin_pm2.margin_details`), zwei Zeilen als Strip mit Median; Ersatz, falls die Spalte fehlt: Median und
  Quartilsband von ratio über Dezile von `n_legs_before`.
- **Kernaussage (5 s):** Im Buch eines dominanten Makers kostet der nächste Kontrakt meist einen Bruchteil seines
  Einzelkapitals, und Fills gegen das bindende Szenario setzen Kapital frei.
- **Fallen:** ratio ist unbeschränkt, wenn K_single klein ist (Überlauf zeigen statt abschneiden); ratio je
  Kontrakt des Fills (Nachtrag 4 Ziffer 1), Varianten nur in der CSV; nur vier Konten unter PM2 tragen H2, die
  Kontenzahl G = 4 gehört ins Bild (Paper-1-Regel: kleine G hinterlegen); 3,4 Zoll lassen für b nur zwei Zeilen.

### F4 · Was Netting wert ist, H3 (3,4 × 3,8 Zoll)

- **Zweck:** K_SM/K_PM2 derselben Bücher zeigen und erklären, warum der Faktor von Buch zu Buch so verschieden ist.
- **Daten:** `results/p2/fig_h3_series.csv` (`label, day, manager, status, n_legs, n_legs_pm, over_63_options,
  K_sm, K_pm2, K_pm, ratio_sm_pm2, ratio_sm_pm_be, ratio_pm_pm2_be, …_mm`), Filter wie H3 über `status`;
  `results/p2/h3.json` (`stat, lo, hi, rejected, threshold, n, n_excluded, share_days_over_63_options,
  accounts.M*`); Legacy-PM und MM aus `sens_h3.csv`. `maker_days.parquet` nur, falls `n_expiries_max` für das
  Mechanik-Panel gebraucht wird.
- **Kodierung:** a K_SM/K_PM2 je Maker-Tag auf log-x, eine Zeile je Konto (Rang-Label M1 bis M10), Median-Strich je
  Zeile; Maker-Tage mit mehr als 63 Optionen (SM auf v2 nicht zulässig, 1 431 von 1 943) als hohle Marker,
  zulässige gefüllt; Legacy-PM/PM2 als Rauten in derselben Zeile; Schwelle 2 gestrichelt; registrierter Median mit
  Intervall oben. b Mechanik: Faktor gegen `n_legs` (log-log) mit den T2-Probebüchern (2,14 bis 10,76) als
  Referenzmarken: Netting wächst mit der Breite des Buchs.
- **Kernaussage (5 s):** SM verlangt für dieselben Bücher ein Vielfaches des PM2-Kapitals, und der Faktor wächst mit
  der Breite des Buchs; die meisten dieser Bücher wären unter SM auf v2 gar nicht zulässig.
- **Fallen:** das kontrafaktische SM muss sichtbar sein (hohl), sonst liest man einen realen Kostenvergleich;
  K_PM2 ≤ 0 ausgeschlossen und im Bild gezählt; wenige Konten tragen viele Tage (Zeilen je Konto statt einer Wolke);
  Median der Quotienten ist nicht Quotient der Summen.

### F5 · Die Engine über die Zeit (7,0 × 5,0 Zoll)

- **Zweck:** Zeigen, unter welchem Manager die Positionen liegen, wann Parameter sich ändern, und dass der Abstand
  zwischen den Engines in Stufen an Parametertagen entstanden ist, nicht durch den Markt.
- **Daten:** `results/p2/manager_oi_share.csv` (`month, ccy, sm, pm, pm2`); `results/p2/params/{CCY}_{mgr}.json`
  (jeder Eintrag nach dem ersten ist eine Änderung, Feld `changed`); `results/p2/events.csv` (`ccy, manager,
  event_ts, kept, max_abs_dose, kinds`); `results/p2/reference_book.csv` (`ccy, day, forward, K_sm, K_pm, K_pm2`,
  `*_prev`).
- **Kodierung:** a drei schmale Streifen (BTC, ETH, HYPE) mit Monatsanteilen am OI als Stapel, SM voll, Legacy-PM
  gepunktet, PM2 schraffiert. b Ereignisschiene je Basiswert und Manager: jede Parameteränderung als grauer Strich,
  H4-Ereignisse gefüllt (behalten) oder hohl (unter 1 % Dosis), Markerform = Manager. c Referenz-Straddle BTC in %
  des Forwards je Manager (Farbe plus Strichart), behaltene Ereignisse als gepunktete Senkrechte. d reiner
  Parametereffekt 100·log(K/K_prev) als Stiele, Form = Basiswert.
- **Kernaussage (5 s):** Derselbe BTC-Straddle kostet am 17.09.2026 29,6 % (SM), 19,7 % (Legacy-PM) und 10,0 % (PM2)
  des Forwards, und der Abstand ist in Sprüngen an Parametertagen entstanden.
- **Pilotzahlen Panel d (log-%):** BTC Legacy-PM 22.02.2025 −18,6; BTC PM2 08.01.2026 +1,6, 23.01.2026 −10,5,
  24.05.2026 −7,8, 20.08.2026 −26,0; HYPE PM2 24.05.2026 −37,4.
- **Fallen:**
  - `K_prev` rechnet mit den Parametern von vor 24 h; der Sprung erscheint am Tag nach dem Ereignis (22.02. →
    23.02.). Beschriften mit dem Ereignisdatum.
  - SM-Änderungen betreffen nur Perps (kein Optionseffekt); Striche zeigen, aber so benennen.
  - HYPE hat keinen Legacy-PM; OI-Anteile sind monatlich, alles andere täglich.
  - Der Straddle rollt auf den Verfall nächst 30 Tagen; kleine Sägezähne sind Rollen, keine Parameter.
  - Vier Panels auf 5 Zoll: nur c bekommt Gitterlinien, a und b nicht.

### F6 · Der Preis des Kapitals, H4 (7,0 × 4,3 Zoll)

- **Zweck:** Die Dosis als Fingerabdruck der Parameteränderung auf der Karte zeigen und dann, ob der Halbspread ihr
  folgt.
- **Daten:** a `results/p2/h4_doses.csv` (`event_id, cell, dose, n_fills`), drei BTC-PM2-Ereignisse mit
  verschiedenen Mechanismen: 08.01.2026 (Static Discount gedreht), 23.01.2026 (Tail-Gewichte), 20.08.2026 (Gitter
  ±14 %). b `results/p2/fig_h4_events.csv` (je Ereignis Dosis-Terzile `t1…t3` mit `*_dose_lo/hi, *_median_dose,
  *_n_pre/post, *_y_pre/post`): je Terzil die Differenz y_post − y_pre gegen die mittlere Dosis, ein Punkt je
  Ereignis und Terzil (Form = Basiswert), dazu β aus `h4.json` (`stat, lo, hi, p, p_sided, criteria.*,
  events_kept, cell_events`). c `results/p2/h4_placebo.csv` (`rep, beta`) mit `h4.json` `placebo.p95,
  placebo.share_ge_beta`.
- **Kodierung:** a 2 × 3 Karten (Zeilen Verkauf/Kauf, Spalten Ereignisse), 100·Dosis mit Vorzeichen als Zahl, `PuOr`
  divergierend um 0, Kreuz unter 20 Fills. b Dosis-Wirkung in Klassen mit Intervallen und der Geraden β. c
  Histogramm der 100 Placebo-β mit 95. Perzentil und Schätzer.
- **Kernaussage (5 s):** Jede Parameteränderung hat einen eigenen Abdruck auf der Karte (Tail-Gewichte fast nur
  OTM-Verkäufe, Gitter alle Verkäufe um −21 bis −31 log-%, Static Discount +1 bis +2 log-% auf Verkäufe); b und c
  sagen, ob der Halbspread diesem Abdruck folgt.
- **Fallen:**
  - Fast alle Dosen sind ≤ 0 (nur der 08.01.2026 verteuert); β ist im Wesentlichen aus Lockerungen identifiziert.
    Gehört in die Unterschrift.
  - Divergierende Farbe allein trägt nicht in Graustufen; das Vorzeichen steht als Zahl in jeder Zelle.
  - Nur BTC in a; ETH und HYPE in der CSV. Zusammengefasste Tagesänderungen: e = erste Änderung (Nachtrag 4).
  - β in bp des Index je log-Einheit Kapital; der Text rechnet auf 10 % Kapital um.
  - Keine rohen Halbspread-Zeitreihen um das Ereignis zeichnen (Rauschen verführt zur Augenlesung).

### A1 · Trifft der Nachbau die Chain? (7,0 × 2,7 Zoll, Anhang)

- **Zweck:** Die Validierung gegen `eth_call` als Verteilung zeigen, mit den registrierten Schwellen.
- **Daten:** `results/p2/validation.csv` (`kind, ccy, manager, is_initial, status, rel_err, n_legs`), IM primär
  (`is_initial == True`), `status == ok`; `validation_summary.json` für Schwellen, Reverts und die
  Szenario-Einzelprüfung.
- **Kodierung:** a Einzelkontrakte, b Bücher; Zeilen Basiswert × Manager, x = log10 |rel|, exakte Nullen am Rand
  „≤ 1e−12“, Median als Strich, Schwellen 0,1 % und 1 % gestrichelt, n je Zeile. Mechanik-Variante für b: rel gegen
  `n_legs` (2 bis 245), damit sichtbar ist, dass der Fehler nicht mit der Breite des Buchs wächst.
- **Kernaussage (5 s):** Der Nachbau trifft die Chain auf etwa 1e−9 bis 1e−8, sechs Grössenordnungen unter der
  Schwelle, für Einzelkontrakte wie für Bücher.
- **Fallen:** Nullen auf log-Achse (fast die Hälfte der SM-Fälle ist exakt 0); zwei Reverts nennen; HYPE-Bücher
  n = 1; IM und MM stehen als doppelte Zeilen in der CSV.

---

## 5 · README und X

### GIF: „Die Karte atmet mit dem Markt und springt mit den Parametern“

- **Inhalt:** PM2-Kapital je Short-Kontrakt als 3D-Fläche (Höhe IV, Farbe K in % des Forwards, feste Skala über
  alle Frames), darunter der Referenz-Straddle je Manager als Band mit laufendem Cursor und Ereignisflaggen. SM nur
  als Zahl in der Ecke („SM: 29 %“), weil seine Fläche einfarbig ist.
- **Frames:** wöchentlich vom 13.06.2025 bis 17.09.2026 (rund 66) plus je behaltenem BTC-Ereignis drei Tagesframes
  (Vortag, Tag mit Banner „parameter change: tail weights lowered“, Folgetag), 1,5 s gehalten; 4 fps, rund 25 s.
  Beim Ereignisframe die Zellen mit |Dosis| > 5 % aus F6a als Umriss auf dem Band einblenden.
- **Technik:** `p2surface.animate` mit `ANIM_DAYS`-Achse, `fit_limits` über alle Frames; Lauf nur über
  `scripts/p2_heavy.py` (Feed-Historie je Quartal). 960 × 540 für das README, 1280 × 720 als MP4 für X
  (`write_mp4`), GIF unter 8 MB.
- **Fallen:** Das bestehende GIF (`data/p2/surface/BTC_capital_short_2026-08-14_2026-08-27.gif`) hat Tick-Schrift
  von etwa 10 px; auf X unter 14 px nicht lesbar. Tage ohne Live-Verfall werden übersprungen, das Datum im Frame
  muss das zeigen. Farbquantisierung des GIF bei `cividis` prüfen.

### Social-Karten 1600 × 900

1. **„One short BTC straddle. Three margin engines.“** (Prototyp gebaut, echte Daten): Zeitreihe aus F5c, rechts
   drei grosse Zahlen 30 % / 20 % / 10 % des Forwards am 17.09.2026, Strichart je Manager. Falle: „capital for a
   hypothetical book, not a balance“ als Zeile ergänzen; PM2 beginnt erst im Juni 2025 (Fenster), nicht beschriften
   als „eingeführt“.
2. **„Where the capital comes from“:** T1a als Einzelfläche plus der Satz „Almost everywhere one scenario sets the
   capital: spot ±14 % with vol up.“ und der Streifen T1c darunter.
3. **„One parameter change, one fingerprint“:** F6a für den 20.08.2026 (Verkaufsseite) mit „Every short got 21 to 31 %
   cheaper overnight. Buys barely moved.“ Nach der Inferenz eine vierte Karte mit den vier Urteilen H1 bis H4.

---

## 6 · Was die Linse gegenüber der Spezifikation ändert (für die Jury)

| Slot | Spezifikation | Vorschlag Mechanismus | Grund |
|---|---|---|---|
| T1 | 3D PM2 und SM | plus 2D-Streifen „bindende Regel“ mit Iso-Linien | Die Fläche allein sagt nicht, warum; Bodenprojektion in 3D scheitert |
| T2 | zwei Panels | plus Panel c Szenario-Profil des Straddles | einzige Stelle, an der man sieht, wie PM2 R bildet und warum Netting wirkt |
| F1 | USDC, eigene Skalen | % des Nominals, eine Log-Skala, Anatomie-Spalte | Nenner von F2; Seite dominiert Manager |
| F2 | Rang-Linien | κ-Diagonalen plus Rang-Streuung | Umordnung als Bewegung quer zum Nenner lesbar |
| F3, F4 | nur Verteilung | je ein Mechanik-Panel (bindendes Szenario, Buchbreite) | Befund wird vorhersagbar |
| F5 | drei Panels | plus d reiner Parametereffekt aus `K_prev` | trennt Markt von Parameter |
| F6 | Dosis-Wirkung, Placebo | plus a echte Dosiskarten | macht das Experiment sichtbar, verbindet mit T1c |

Offene Anforderungen an den Code: `figdata_p2.binding_rule` (T1c/d), `figdata_p2.pm2_anatomy` (F1, T2c),
`figdata_p2.cell_capital_ratio` (F1 als Verhältnis der Summen je Manager, passend zu `h1_cells.csv`), Spalte
`hedges_worst` in `books.py` (F3b). Die Inferenztabellen decken F2, F3a, F4a, F6b/c ab; F6b liest die Terzile aus
`fig_h4_events.csv`, eine eigene Bin-Tabelle ist nicht nötig. Der Prototyp-Code
`data/p2/fig_proto/mechanismus/proto_mechanismus.py` enthält die Engine-Zerlegungen (`pm2_scenarios`,
`pm2_anatomy`, `_pm2_binding`, `_sm_branch`) als Vorlage; die PM2-Zerlegung summiert sich am T1-Knoten exakt auf
das Kapital des Gitters (9 066,71 USDC für den Short, 2 636,54 für den Long).
