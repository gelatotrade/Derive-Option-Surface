# Abbildungsentwurf Paper 2, Linse Praktiker

Stand 25.09.2026. Entwurf für die Jury nach dem Muster von Paper 1 (`docs/paper1/ABBILDUNGSWAHL.md`). Die Linse ist
ein Market Maker oder Bot-Entwickler auf Derive. Er will drei Dinge wissen: wo auf der Oberfläche sich Kapital gut
verzinst, was der nächste Kontrakt in seinem Buch kostet und wie viel PM2 gegenüber SM spart. Jede Abbildung
beantwortet genau eine Frage, die er vor dem nächsten Quote stellt.

Prototypen liegen unter `data/p2/fig_proto/praktiker/`. Der Code steht in `proto_praktiker.py` daneben, jede Zahl
eines Prototyps auch als `fig_*.csv`. Wo H1 bis H4 Ergebnisse liefern, sind die Werte **synthetisch** (Stempel
PROTOTYP, Tabellen mit Suffix `_SYNTHETIC`). Hypothesenstatistiken wurden nicht berechnet. Echte Zahlen stammen aus
dem Pilotschnitt 17.09.2026.

## Überblick

| Slot | Frage des Praktikers | Breite × Höhe | Prototyp | Daten |
|---|---|---|---|---|
| T1 | Was bindet ein Short heute, Punkt für Punkt auf der Oberfläche? | 7,0 × 3,1 in | `t1_praktiker.png` | echt |
| T2 | Wie lese ich `get_margin` richtig? | 7,0 × 2,5 in | `t2_praktiker.png` | echt |
| F1 | Was kostet ein nackter Kontrakt je Zelle, und ist PM2 dafür billiger? | 7,0 × 3,9 in | `f1_praktiker.png` | echt |
| F2 | Wo verzinst sich Kapital am besten? (H1) | 7,0 × 3,9 in | `f2_praktiker.png` | synthetisch |
| F3 | Was kostet der nächste Kontrakt in meinem Buch? (H2) | 3,4 × 3,3 in | `f3_praktiker.png` | synthetisch |
| F4 | Wie viel spart PM2 an einem echten Buch, und ab welcher Buchgrösse? (H3) | 3,4 × 4,0 in | `f4_praktiker.png` | synthetisch, Konten und Beinzahlen echt |
| F5 | Wie hat sich der Preis des Kapitals verändert? | 7,0 × 4,4 in | `f5_praktiker.png` | echt |
| F6 | Folgt der Spread dem Preis des Kapitals? (H4) | 7,0 × 2,7 in | `f6_praktiker.png` | synthetisch |
| A1 | Kann ich den Offline-Nachbau statt der Chain rechnen lassen? | 7,0 × 2,6 in | `a1_praktiker.png` | echt |

Die Reihenfolge ergibt eine Leselinie für den Praktiker. T1 und F1 zeigen den Preis eines Kontrakts, F2 die Rendite
darauf. F3 und F4 zeigen, dass das Buch billiger ist als die Summe der Kontrakte. F5 und F6 zeigen, dass der Preis
sich bewegt und ob der Markt darauf reagiert. A1 beantwortet, ob man dem Werkzeug trauen darf.

**Befund aus den echten Daten, der die Linse trägt** (explorativ, keine Hypothese): Für einen einzelnen Short ist
PM2 *nicht* billiger als SM. Über die 173 besetzten Zellen des PM2-Fensters liegt SM ÷ PM2 bei Maker-Verkäufen im
Median bei 0,94 (BTC), 0,90 (ETH) und 0,88 (HYPE). In 74 % der Verkaufszellen braucht SM sogar weniger. Der
Legacy-PM braucht das 1,38- bzw. 1,35-Fache. Am selben Morgen (17.09.2026, 08:00 UTC) bindet ein Short-Call ATM mit
22 Tagen unter PM2 11,9 % des Forwards und der ganze Short-Straddle nur 10,0 %. Unter SM sind es 14,3 % und 29,6 %.
PM2 senkt also nicht den Preis des einzelnen Kontrakts, sondern den des Buchs. Genau das testen H2 und H3, und die
Abbildungen sollten diesen Kontrast tragen.

## Regeln, die für alle Slots gelten

- CAS-Breiten 3,4 und 7,0 Zoll, keine Schrift unter 7 pt, Farben nur aus `figstyle.PALETTE`.
- Feste Manager-Kodierung, dreifach ausgeführt: PM2 blau, durchgezogen, Kreis; SM orange, gestrichelt, Quadrat
  bzw. schraffiert; Legacy-PM grün, gepunktet, Raute. Die Palette besteht den Farbsehtest (`validate_palette.js`,
  schlechtestes Paar Deutan ΔE 11,0), trägt aber trotzdem immer Strichart oder Zeichen.
- Kapital in **% des Index bzw. Forwards** (so rechnet ein Maker Margin), Edge in **bp des Kapitals** (wie
  präregistriert). Ein Kontrakt heisst immer „ein Kontrakt“, nie „1 BTC“.
- Karten: eine Zahl je Zelle. Zellen unter 200 Fills bekommen ein leeres Kreuz. Negativ zusätzlich schraffiert.
  Rahmen nur für eine vorab definierte Auszeichnung.
- Jede Zahl der Abbildung auch unter `results/p2/fig_<slot>.csv`. Die Prototypen schreiben sie vorerst nach
  `data/p2/fig_proto/praktiker/fig_*.csv`.
- Verteilungen nie als Punktwolke aus Tausenden Punkten in Farbe: ECDF, Quantilbalken oder Bins.

## Datenvertrag mit der Inferenz (Stand der Dateien 25.09.2026, 01:46)

Während dieses Entwurfs hat `inference_p2` die Tabellen unten geschrieben. Gelesen wurden nur Spaltennamen und
Kategorien, keine Ergebniswerte. Die Prototypen bleiben synthetisch. Die finalen Abbildungen lesen:

| Slot | Datei | Spalten, die die Abbildung braucht | Lücke |
|---|---|---|---|
| F1 | `fig_capital_by_manager.csv` | `window == "pm2"`, `manager, ccy, side, delta_bucket, tenor_bucket, fills, median_k_over_index` | Verhältnis SM ÷ PM2 und Legacy ÷ PM2 als Verhältnis der Summen auf denselben Fills fehlt (`sum_K_sm, sum_K_pm, sum_K_pm2, sum_index`) |
| F2 | `h1.json`, `fig_edge_maps.csv` bzw. `h1_cells.csv` | `stat, lo, hi, rejected, threshold`; je Zelle `map == "pm2"`, `occupied, A_bp, B_bp, rank_A, rank_B, rank_B_lo, rank_B_hi, fills_k_le_0` | keine (A = Nominal, B = PM2-Kapital, im Code so benennen) |
| F3 | `h2.json`, `fig_h2_dist.csv` | `stat, lo, hi, n, n_excluded, share_nonpositive`; `label ∈ {all, M3, M5, M8, M10}`, `variant == "ratio"`, `kind ∈ {hist, quantile, share_le_0, n}`, Bins 0,05 von −1 bis 2 mit Überlaufklassen | keine: Die Bingrenzen enthalten 0, ½ und 1, die Bandanteile folgen exakt aus dem kumulierten Histogramm. x-Achse von −1 bis 2 statt −1,5 bis 2,5 wie im Prototyp |
| F4 | `h3.json`, `fig_h3_series.csv` | `stat, lo, hi, days_over_63_options`; je Maker-Tag `label, day, status, n_legs, over_63_options, ratio_sm_pm2, ratio_pm_pm2_be` | keine (`_be` = nur BTC- und ETH-Beine, so beschriften) |
| F5 | `manager_oi_share.csv`, `events.csv`, `reference_book.csv`, `fig_h4_events.csv` (Spalte `kept`) | wie oben | Ereignis 12./13.06.2025 fehlt in `events.csv` |
| F6 | `h4.json`, `h4_placebo.csv`, `fig_h4_events.csv` | `stat, p, placebo.p95, placebo.share_ge_beta, criteria.*`; `beta` der 100 Replikationen; je Ereignis `t{1,2,3}_median_dose, t{k}_y_pre, t{k}_y_post, t{k}_n_*` | Panel a braucht Residuen je Zell-Ereignis-Paar nach α und γ. `fig_h4_events.csv` liefert nur Terzile je Ereignis mit rohen Mitteln. Tragfähiger Ersatz: 13 Ereignisse × 3 Dosisterzile = 39 Punkte, x = Terzilmedian der Dosis, y = `y_post − y_pre`. Die β-Linie ist dann nur als Richtung vergleichbar, weil die Fixeffekte fehlen |
| A1 | `validation.csv` | wie oben | keine |

---

## T1: Die Engine-Sicht der Oberfläche

- **Zweck:** zeigen, was ein einzelner Short an jedem Punkt der BTC-Oberfläche heute an Kapital bindet, unter PM2
  und unter SM auf derselben Skala.
- **Daten:** `p2surface.capital_grid` an einem Block (Prototyp: `data/p2/surface/probe_BTC_2026-09-17_grid.csv`,
  17.09.2026 08:00 UTC). Spalten `manager, delta, tenor_days, iv, K_per_forward_bp`, Filter `side == short`,
  Manager `pm2` und `sm`. Final als `results/p2/fig_t1.csv` mit Block, Gitter und K je Knoten (die Datei
  `surface_t1.json` aus `MANUSKRIPT.md` kann darin aufgehen).
- **Kodierung:** zwei 3D-Panels nebeneinander. x = Call-Delta (Put = Δ − 1), y = Tage bis Verfall (log), z = IV in
  %, Farbe = Kapital je Short-Kontrakt in % des Forwards auf gemeinsamer Skala (cividis, 3 bis 15,5 %). Schwarze
  **Isolinien gleichen Kapitals** bei 4, 6, …, 14 % liegen auf der Fläche und sind beschriftet. Sie tragen die
  Zahl in Graustufen und machen das Bild lesbar, ohne dass man Farben vergleichen muss. Paneltitel mit der
  Kopfzahl des Praktikers: „PM2: ATM 30 d short = 11,8 % of fwd“ bzw. „SM: 14,1 %“. Das ist die einzige
  3D-Abbildung im PDF.
- **Grösse:** 7,0 × 3,1 in.
- **Kernaussage (5 s):** Unter SM kostet jeder Short fast dasselbe (12 bis 15 % des Forwards, flache gelbe Fläche).
  Unter PM2 hängt der Preis stark vom Ort ab: kurze Laufzeiten nahe am Geld sind teuer, lange Flügel billig
  (3,4 bis 13,7 %).
- **Fallen:**
  - Die 3D-Ansicht verdeckt die Rückseite. Blickwinkel fest (elev 24, azim −128) und in beiden Panels gleich.
    Der ATM-30-Tage-Knoten muss sichtbar sein (im Prototyp verdeckt; im Final als Beschriftung auf der Isolinie).
  - Der Knotenpreis ist der Black-76-Mark mit D = 1, nicht ein Fill-Preis. Die Beschriftung muss „at mark“ sagen.
  - Chain-Semantik. Die off-chain API rechnet PM2 mit pauschal 2 % Diskont. Für einen Bot, der gegen die API
    quotet, weicht die Zahl bei langen Laufzeiten um bis zu 3 % ab (`get_margin_semantik.md`, Abschnitt 3).
  - Die SM-Fläche ist fast einfarbig. Das ist der Befund, kein Darstellungsfehler. Nicht auf getrennte Skalen
    ausweichen, sonst verschwindet genau der Vergleich.
  - Zwischen gelisteten Verfällen ist interpoliert. Die Tenor-Achse sollte die gelisteten Verfälle als Striche
    zeigen.
  - Das Datum wird mit dem Enddatenlauf neu gewählt. Es muss ein Tag ohne Parameteränderung in ±1 Tag sein.

## T2: Was `get_margin` liefert

- **Zweck:** dem Bot-Entwickler zeigen, dass `C − net` keine Margin ist, und die Faktoren 11,86 gegen 1,19 auflösen.
- **Daten:** `results/p2/semantik/faktoren.csv`, Zeilen `historisch …` ohne `H0_`, Fälle A und B. Spalten
  `SM_R_engine, PM2_R_engine, V_und_SM, V_PM2, F_Cnet, F_R_engine`. Prototyp-Tabelle `fig_t2.csv`.
- **Kodierung:** Panel a: ein gemischtes Buch (24.09., Fall B), je Manager ein waagerechter Balken `C − net = R − V`.
  Der Teil R ist vollflächig in Managerfarbe, der Teil −V schraffiert. Man sieht, dass −V (497 000 USDC) bei beiden
  Managern gleich ist und R überdeckt. Panel b: Hantel je Probebuch (4 Zeilen), offener Kreis = Faktor auf
  `C − net`, gefüllter Kreis = Faktor auf R, Pfeil dazwischen, log-x von 1 bis 16. Füllung statt Farbe, also
  graustufenfest.
- **Grösse:** 7,0 × 2,5 in.
- **Kernaussage (5 s):** Der Positionswert V steckt in `C − net` und drückt den Faktor SM ÷ PM2 gegen 1. Auf der
  Anforderung R liegen die Bücher zwischen 2,14 und 10,76.
- **Praktiker-Zusatz (Vorschlag, eigene Zeile unter Panel a oder in der Caption):** das Rezept für die Grenzkosten
  in einer Anfrage, `positions = q, changes = Δq, collateral_changes = −p·Δq → ΔK = −(post − pre)`. Wenn die Jury
  keinen Text im Bild will, gehört es wörtlich in die Caption.
- **Fallen:**
  - Die Variante des Buchs vom 24.09. (`H1_…` gegen `H0_heutige_Liste`) muss genannt sein, sonst passt 1,19 nicht zu
    1,22.
  - Der Pfeil beim Buch vom 17.09. B zeigt nach links (11,86 → 10,76). Das ist richtig (V > 0), sieht aber wie ein
    Fehler aus. Die Caption sollte sagen, dass V dort positiv ist.
  - Keine Ticker-Marks verwenden. `F_R_ticker` gibt es nur für Live-Zeilen.

## F1: Was ein Kontrakt kostet

- **Zweck:** die Preisliste des Kapitals, also was ein einzelner Kontrakt je Zelle unter PM2 bindet, und daneben,
  wie SM und Legacy-PM auf *denselben Fills* dazu stehen.
- **Daten:** `data/p2/derived/capital.parquet` (`K_sm, K_pm, K_pm2, amount, index_price, maker_side, currency`),
  gejoint über `trade_id` an `data/p1/derived/markouts.parquet` (`delta_bucket, tenor_bucket`). Filter: `K_pm2`
  endlich (PM2-Fenster je Basiswert), 336 087 Fills. Je Zelle Verhältnis der Summen, mit der Menge gewichtet:
  `100·Σ K_pm2·a / Σ Index·a` sowie `Σ K_sm·a / Σ K_pm2·a` und `Σ K_pm·a / Σ K_pm2·a` (Legacy nur auf Fills mit
  endlichem `K_pm`). Besetzt ab 200 Fills. Final als `results/p2/capital_cells.csv` bzw. `fig_f1.csv`
  (Prototyp: 210 Zellen, 173 besetzt). Die Inferenz hat inzwischen `results/p2/fig_capital_by_manager.csv`
  geschrieben (`window ∈ {own, pm2}, manager, ccy, side, delta_bucket, tenor_bucket, fills,
  median_k_over_index, p25_…, p75_…`). Die Datei enthält **Mediane je Fill**, nicht das Verhältnis der Summen.
  Für die Zahl in der Zelle passt der Median (robust, Einheit % des Index). Für die Verhältnisse SM ÷ PM2 auf
  denselben Fills braucht es zusätzlich `sum_K_<m>` und `sum_index` je Zelle (Ergänzung, siehe Datenvertrag unten).
- **Kodierung:** Zeilen = Maker verkauft (oben) und Maker kauft (unten), Spalten BTC, ETH, HYPE. Je Karte 7
  |Δ|-Buckets × 5 Laufzeiten, **eine Zahl** = PM2-Kapital in % des Index, Graustufenhelligkeit logarithmisch je
  Zeile. Rechts je Zeile ein Streifen „÷ PM2“: je besetzte Zelle ein Zeichen (SM Quadrat orange, Legacy Raute grün),
  der Median als schwarzer Balken, gestrichelte Linie bei 1 und der Hinweis „PM2 cheaper →“.
- **Grösse:** 7,0 × 3,9 in.
- **Kernaussage (5 s):** Ein nackter Short kostet unter PM2 7 bis 21 % des Index (HYPE 18 bis 39 %), und SM ist für
  denselben Kontrakt nicht teurer (Median 0,88 bis 0,94). Nur der Legacy-PM verlangt rund das 1,4-Fache.
- **Fallen:**
  - Die Karte mittelt über alle Parameterstände des PM2-Fensters. Das PM2-Kapital des Referenz-Straddles fiel darin
    von 14,4 auf 10,0 % des Forwards (F5). Für einen Maker heute ist das die falsche Zahl. Deshalb braucht es T1
    als Stand eines Tages oder eine Zusatzspalte „letzte 30 Tage“ in der CSV.
  - Bei Käufen ist SM ÷ PM2 ≈ 1 fast per Konstruktion: Ein Long unter SM kostet genau seine Prämie. Das darf nicht
    als „SM und PM2 sind gleich“ gelesen werden. In der Caption steht es als Eigenschaft von SM.
  - |Δ| ist das Delta der gehandelten Option. Eine Zelle 90–100 bei Verkauf ist ein tief im Geld verkaufter
    Kontrakt, keine OTM-Prämie. Praktiker denken in Call-Delta (wie T1), das Papier in |Δ| (wie Paper 1). Die
    Achsenbeschriftung muss „|delta| of the option“ sagen.
  - Das Verhältnis der Summen wird von grossen Fills getragen. Die Fillzahl je Zelle steht in der CSV, nicht im
    Bild (eine Zahl je Zelle).
  - 20 Fills mit K_PM2 ≤ 0 (RFQ-Beine weit vom Mark) bleiben in den Summen, wie in Nachtrag 4 für H1 festgelegt.

## F2: Die Karte in zwei Nennern (H1)

- **Zweck:** zeigen, wo ein Maker je Einheit PM2-Kapital am meisten verdient, und ob der Kapitalnenner die
  Rangfolge der Zellen gegenüber dem Nominal umstellt.
- **Daten (aus der Inferenz):** `results/p2/h1.json` (`stat` = ρ, `lo, hi, rejected, threshold, n`) und
  `results/p2/fig_edge_maps.csv` mit `map == "pm2"` bzw. `h1_cells.csv`: je Zelle `ccy, side, delta_bucket,
  tenor_bucket, fills, occupied, A_bp` (Edge je Nominal), `B_bp` (Edge je PM2-Kapital), `rank_A, rank_B,
  rank_B_lo, rank_B_hi`. Die Rangbänder kommen aus denselben Replikationen wie ρ. Die Karten unter SM und
  Legacy-PM (`map ∈ {sm_pm2win, pm_pm2win, …}`) sind explorativ und gehören in die CSV, nicht in F2. Im Prototyp
  sind die Edge-Werte, die Ränge und ρ synthetisch. Nur die Zellmenge (173) und die Kapitalanteile je Zelle sind
  echt (`fig_f2_SYNTHETIC.csv`).
- **Kodierung:** links sechs Karten (Verkauf/Kauf × BTC/ETH/HYPE), eine Zahl = Netto-Edge in bp des PM2-Kapitals,
  ab 1 000 als „1.3k“. Divergierende Skala orange–weiss–blau mit Null in Weiss, negative Zellen zusätzlich
  schraffiert (Graustufen), die fünf besten Zellen schwarz gerahmt. Rechts das Objekt von H1: Rang nach Edge je
  Nominal gegen Rang nach Edge je PM2-Kapital, beide Achsen mit Rang 1 oben rechts, Diagonale gestrichelt. Das
  Zeichen trägt den Basiswert (Kreis, Quadrat, Raute), gefüllt für Verkauf und offen für Kauf. Graue senkrechte
  Linien sind das 90-%-Rangband. Ein Kasten nennt ρ mit Intervall und die Regel „rejected if upper ≥ 0.5“.
- **Grösse:** 7,0 × 3,9 in.
- **Kernaussage (5 s):** Punkte weit weg von der Diagonale sind Zellen, die je Kapital besser (oben) oder schlechter
  (unten) dastehen als je Nominal. Die gerahmten Zellen sind die, in denen Kapital sich am besten verzinst.
- **Fallen:**
  - **Long-OTM-Zellen explodieren.** Das Kapital eines gekauften OTM-Kontrakts ist seine Prämie, also 0,07 bis 0,6 %
    des Index (F1). Schon ein kleiner Edge gibt dann Tausende bp je Kapital, im Prototyp bis 11 400 bp. Der Rang
    (H1) ist dagegen robust, die Karte aber nicht. Vorschlag: Kaufzeilen mit eigener Farbskala, und im Text sagen,
    dass Edge je Kapital bei Käufen eine Rendite auf die Prämie ist. Keine nachträgliche Untergrenze für K
    einführen, denn die Präregistrierung kennt keine.
  - Die fünf „besten“ Zellen nach Punktschätzung sind verrauscht. Gerahmt werden sollte nur, wessen
    5-%-Rangperzentil unter 20 liegt. Dafür braucht es `rank_capital_p05` aus der Inferenz.
  - Edge je Kapital *je Fill* ist keine Rendite über die Zeit. Kapital ist ein Bestand und Edge ein Fluss. Ein Satz
    in der Caption und der Verweis auf die Haltedauer-Sensitivität (`results/p2/holding_time.csv`), sonst liest ein
    Praktiker bp je Fill als Jahresrendite.
  - Hohe Rendite heisst nicht, dass die Zelle skaliert: Die Tiefe ist nicht Teil des Papiers.

## F3: Der nächste Kontrakt im Buch eines Makers (H2)

- **Zweck:** zeigen, was ein Fill im echten Buch eines dominanten Makers an Kapital zusätzlich bindet, gemessen am
  selben Kontrakt allein.
- **Daten:** `data/p2/derived/marginal.parquet` (`ratio` als Teststatistik nach Nachtrag 4, `label`, `day`,
  `K_single_pm2`), Filter `status == ok` und `K_single_pm2 > 0`, Stichprobe von 20 000 Fills (M3 6 405, M5 5 958,
  M8 4 296, M10 3 341, echte Zahlen). Median und Intervall aus `results/p2/h2.json`
  (`stat, lo, hi, n, n_excluded, share_nonpositive, rejected`). Kurve und Bandanteile aus
  `results/p2/fig_h2_dist.csv` (`label ∈ {all, M3, M5, M8, M10}`, `variant == "ratio"`, `kind == "hist"` mit Bins
  von 0,05 und Überlaufklassen, dazu `quantile`, `share_le_0`, `n`). Die ECDF entsteht aus dem kumulierten
  Histogramm. Im Prototyp ist die Verteilung synthetisch.
- **Kodierung:** Panel a als ECDF des Verhältnisses mit vier grauen Bändern in Praktikersprache: „frees capital“
  (< 0), „cheap“ (0 bis ½), „partial“ (½ bis 1), „dearer than alone“ (> 1), über jedem Band der Anteil der Fills.
  Die H2-Schwelle ½ gestrichelt, der Median als Punkt mit Intervallbalken. Die x-Achse ist auf −1 bis 2
  beschnitten (Bins von `fig_h2_dist.csv`), die Überlaufklassen stehen als Zahl an den Rändern. Panel b: je
  Konto Median und p25–p75 als Balken mit n.
  Eine Linie, Graustufenbänder, keine Farbcodierung, die man braucht.
- **Grösse:** 3,4 × 3,3 in.
- **Kernaussage (5 s):** Der Anteil links von ½ ist der Anteil der Fills, die im Buch weniger als die Hälfte kosten.
  Der Anteil links von 0 setzt sogar Kapital frei.
- **Fallen:**
  - Die Aussage gilt für das Buch eines dominanten Makers. Wer mit leerem Buch startet, zahlt den vollen Preis aus
    F1. Die Caption sollte das in einem Satz sagen, weil ein Praktiker sonst glaubt, er selbst zahle nur die Hälfte.
  - ratio ist ΔK des ganzen Fills je Kontrakt. `ratio_unit` (nächster einzelner Kontrakt) und das Tape-Buch sind
    Sensitivitäten und gehören nicht in dieselbe Kurve.
  - Nur vier Konten unter PM2 (Nachtrag 1, Punkt 5). M3 trägt ein Drittel der Stichprobe, deshalb Panel b.
  - Die Ränder: Ein Verhältnis von −40 ist real möglich (ein Fill schliesst eine grosse Position). Ohne
    Beschneidung wird die Mitte unlesbar, deshalb die Überlaufzahlen.

## F4: Was Netting wert ist (H3)

- **Zweck:** zeigen, um welchen Faktor SM mehr Kapital als PM2 für *dieselben echten Bücher* braucht und wie der
  Faktor mit der Buchgrösse wächst.
- **Daten:** `data/p2/derived/maker_days.parquet` (`label, day, n_legs, K_sm, K_pm2, K_pm`, je Basiswert
  `K_*_<CCY>`), Filter `status == ok`, `K_pm2 > 0`, Legacy nur auf BTC/ETH-Beinen (`K_pm_BTC + K_pm_ETH` gegen
  `K_pm2_BTC + K_pm2_ETH`). Median und Intervall aus `results/p2/h3.json` (`stat, lo, hi, n_excluded,
  days_over_63_options`). Je Maker-Tag aus `results/p2/fig_h3_series.csv` (`label, day, status, n_legs,
  over_63_options, ratio_sm_pm2, ratio_pm_pm2_be`). Im Prototyp sind die Verhältnisse synthetisch. Konten, Tage je Konto und Beinzahlen sind echt (1 943 Maker-Tage).
- **Kodierung:** Panel a: je Konto (M1 bis M10 ohne M9, darunter die Zahl der Maker-Tage) ein Quantilbalken
  p10/p25/Median/p75/p90 von K_SM ÷ K_PM2 auf log-y, daneben der Legacy-Median als offene Raute. Konten mit weniger
  als 20 Tagen sind grau hinterlegt (M7 hat 10). Die H3-Schwelle 2 steht gestrichelt mit dem Text „2 = PM2 saves
  half“. Panel b: dasselbe Verhältnis gegen die Zahl der Optionsbeine (log-log), graue Punkte, dazu die Mediankurve
  über Bins mit mindestens 20 Tagen und die Senkrechte bei 63 Optionen (SM-Kontogrenze).
- **Grösse:** 3,4 × 4,0 in.
- **Kernaussage (5 s):** Alle Balken über der Linie bei 2 heissen: PM2 spart mehr als die Hälfte. Panel b zeigt,
  ab wie vielen Beinen sich PM2 lohnt.
- **Fallen:**
  - An 1 431 von 1 943 Maker-Tagen hält das Buch mehr als 63 Optionen. K_SM ist dort kontrafaktisch, weil kein
    SM-Konto das Buch halten dürfte (Nachtrag 4, Punkt 2). Die Senkrechte in Panel b und der Anteil in der Caption
    sind Pflicht, sonst wirkt der grosse Faktor rechts wie ein Sparpotenzial, das es so nicht gibt.
  - Tage sind je Konto korreliert. Die Balken zeigen Streuung, nicht Unsicherheit. Das Intervall des gepoolten
    Medians aus dem Tages-Bootstrap steht als Zahl in der Caption.
  - Keine zweite y-Achse „% gespart“. Die Übersetzung steht nur an der Schwellenlinie.
  - Ein reines Long-Buch hat unter SM K = Prämie, unter PM2 etwas weniger. Verhältnisse nahe 1 bei kleinen Büchern
    sind deshalb erwartbar.

## F5: Die Engine über die Zeit

- **Zweck:** zeigen, wann Maker nach PM2 gewechselt sind, wann die Engine ihren Preis geändert hat und um wie viel
  ein festes Buch dadurch billiger wurde.
- **Daten:** `results/p2/manager_oi_share.csv` (`month, ccy, sm, pm, pm2`), `results/p2/events.csv` (`ccy, manager,
  event_ts, kept, event_id`), `results/p2/reference_book.csv` (`ccy, day, forward, K_sm, K_pm, K_pm2, K_*_prev`).
  Reiner Parametereffekt je Ereignis = `K_m / K_m_prev − 1` am ersten Tag nach dem Ereignis. Prototyp-Tabellen
  `fig_f5_events.csv` und `fig_f5_refbook_btc.csv`.
- **Kodierung:** Panel a: drei schmale Streifen (BTC, ETH, HYPE) mit monatlichen OI-Anteilen als gestapelte
  Treppenflächen: PM2 blau vollflächig, Legacy hellgrün, SM weiss mit oranger Schraffur (in Graustufen dunkel, hell,
  schraffiert). Panel b: Ereignisleiste je Basiswert, Kreis = PM2, Raute = Legacy, gefüllt = in H4, offen =
  weggefallen. Neben jedem Zeichen **eine Zahl**: der reine Effekt auf das Kapital des Referenz-Straddles in %.
  Panel c: BTC-Referenz-Straddle (ATM, etwa 30 Tage, je ein Kontrakt) in % des Forwards unter SM, Legacy-PM und
  PM2, Direktbeschriftung am rechten Rand, Ereignisse als gepunktete Senkrechte.
- **Grösse:** 7,0 × 4,4 in.
- **Kernaussage (5 s):** Die Maker sind 2026 fast vollständig zu PM2 gewechselt (BTC 91 %, ETH 72 %, HYPE 88 % des
  OI im September). PM2 wurde in Stufen billiger, am stärksten am 20.08.2026 (BTC −23 %, ETH −17 %, HYPE −18 %).
  Allein die Parameteränderungen senkten das Kapital des BTC-Straddles um 35 % (ETH −23 %, HYPE −47 %). SM blieb bei
  29,6 %.
- **Fallen:**
  - Der Referenz-Straddle wechselt den Verfall (Laufzeit 21 bis 36 Tage). Die Sägezähne in c sind Laufzeit, nicht
    Engine. Vorschlag aus B5 übernehmen: im Final einen synthetischen 30-Tage-Knoten über
    `capital_grid(tenors=[30/365])` (explorativ, so zu kennzeichnen).
  - Die Prozentzahlen in b gelten für dieses eine Buch. Die Dosis je Zelle (F6) kann ein anderes Vorzeichen haben.
    Am 08.01.2026 wurde die Engine teurer (+1,6 %). Deshalb nicht „immer billiger“ titeln.
  - Die Änderung vom 12./13.06.2025 (−0,35 %) liegt am Rand des PM2-Fensters und steht nicht in `events.csv`. Sie
    erscheint in c, aber nicht in b, und sollte in b als Ereignis ohne H4-Status ergänzt werden.
  - OI-Anteil ist nicht Kapitalanteil. Die Streifen zeigen, wo die Positionen margined sind, nicht wo das Kapital
    liegt.
  - Die Panels b und c nur für BTC mit Zahlen zu füllen wäre einfacher. ETH und HYPE gehören aber hinein, weil HYPE
    mit −31 % am 24.05.2026 den grössten Einzelschritt hat.

## F6: Der Preis des Kapitals (H4)

- **Zweck:** zeigen, ob der Halbspread sinkt, wenn eine Parameteränderung das Kapital einer Zelle billiger macht, in
  einer Einheit, die ein Maker übersetzen kann.
- **Daten:** `results/p2/h4.json` (`stat` = β, `p, criteria.*, placebo.p95, placebo.share_ge_beta`),
  `results/p2/h4_placebo.csv` (`beta` der 100 Replikationen) und `results/p2/fig_h4_events.csv` (je Ereignis drei
  Dosisterzile mit `t{k}_median_dose, t{k}_y_pre, t{k}_y_post`). Für Panel a in der gezeichneten Form fehlt eine
  Tabelle je Zell-Ereignis-Paar mit den Residuen nach α und γ (Vorschlag `fig_f6_pairs.csv` mit `event_id, ccy,
  cell, dose, d_hs_resid_bp, n_pre, n_post` aus `data/p2/derived/h4_panel.parquet`). Ohne sie trägt Panel a die
  39 Terzilpunkte (siehe Datenvertrag). Im Prototyp ist alles synthetisch bis auf die Ereignisliste und die
  Zellzahl je Ereignis (475 Paare, 13 Ereignisse mit Panelzellen).
- **Kodierung:** Panel a: Dosis-Wirkung als Binned Scatter, Paare als hellgraue Punkte, Dezile der Dosis als
  schwarze Quadrate mit 90-%-Balken, die geschätzte Steigung β als blaue Linie. x-Achse = Dosis in log, aber mit
  Ticks als Kapitaländerung beschriftet (−50 %, −25 %, 0, +25 %). Das ist dieselbe Achse und keine zweite. Panel b:
  je Ereignis mittlere Dosis gegen mittlere Spreadänderung, Zeichen je Basiswert, Legacy offen, BTC-Daten als
  Beschriftung. Panel c: Histogramm der 100 Placebo-β, 95. Perzentil gestrichelt, Schätzung als blaue Linie mit
  Beschriftung.
- **Grösse:** 7,0 × 2,7 in.
- **Kernaussage (5 s):** Liegt die blaue Linie in c rechts vom 95. Perzentil und steigt sie in a, dann reagiert der
  Spread auf den Preis des Kapitals. Die Caption übersetzt: „Kapital 10 % billiger → Halbspread ändert sich um
  0,1·β bp des Index.“
- **Fallen:**
  - Vorzeichen: Die Dosis ist bis auf den 08.01.2026 negativ (billiger). Eine positive Steigung heisst also, dass
    der Spread sinkt, wenn das Kapital billiger wird. Das muss als Leserichtung in die Caption, sonst liest der
    Praktiker die Linie verkehrt.
  - Rohe Spreadänderungen enthalten Tag- und Zelleffekte. Gezeichnet werden müssen die Residuen nach α und γ,
    sonst passt die Steigung im Bild nicht zu β.
  - Panel b hat 13 Punkte mit sehr ungleicher Zellzahl. Punktgrösse nach Fills wäre ehrlicher, stört aber in
    Graustufen. Deshalb Zellzahl in der CSV und Punkte gleich gross.
  - Das Ereignis HYPE 20.08.2026 hat eine Dosis von 1,65 aus einer Zelle mit 6 Fills und K nahe 0. Diese Zelle
    fällt im Panel weg (weniger als 20 Fills je Seite), bestimmt aber die 1-%-Regel. Sie gehört nicht als Ausreisser
    in a.
  - Keine Placebo-Haarlinien, nur das Histogramm (Regel aus Paper 1).

## A1: Stimmt der Nachbau mit der Chain?

- **Zweck:** zeigen, dass der Offline-Nachbau der drei Manager die deployten Verträge auf Rundungsniveau trifft,
  für Einzelkontrakte und für echte Bücher bis 245 Beine.
- **Daten:** `results/p2/validation.csv` (`kind, ccy, manager, rel_err, abs_err, K_chain, n_legs, is_initial,
  status`), Filter `status == ok`, `is_initial == True` (MM in der CSV). `validation_summary.json` für die
  Schwellen. Prototyp-Tabelle `fig_a1.csv`.
- **Kodierung:** Panel a: je Basiswert × Manager eine Zeile mit gestreuten Zeichen (Manager-Zeichen und -Farbe),
  |rel. Abweichung| auf log-x von 10⁻¹² bis 10⁻¹. Exakte Treffer (0) sitzen in einem grauen Randstreifen
  „exact“. Die präregistrierten Grenzen 0,1 % (Median) und 1 % (p95) sind gestrichelt bzw. gepunktet. Panel b:
  Bücher, Abweichung gegen Zahl der Beine (log-log), dazu im Bild die grösste absolute Abweichung (0,05 USDC bei K
  bis 19,5 Mio. USDC).
- **Grösse:** 7,0 × 2,6 in (Anhang).
- **Kernaussage (5 s):** Alle Punkte liegen mindestens fünf Dekaden links der Grenzen, und die Abweichung wächst nicht mit
  der Buchgrösse.
- **Fallen:**
  - Der Nachbau trifft die *Chain*. Die Börse lässt Trades über die off-chain API zu (pauschal 2 % Diskont). Ein
    Bot, der den Nachbau statt `get_margin` nutzt, ist exakt für Liquidation und Historie, aber nicht für die
    Zulassung. Das gehört in die Caption, sonst ist A1 für Praktiker ein falsches Versprechen.
  - Nur ein HYPE-Maker-Tag in der Buchziehung. Panel b nicht nach Basiswert aufteilen.
  - Exakte Nullen auf log-Achse: Der Randstreifen muss beschriftet sein, sonst verschwinden 45 bis 53 SM-Fälle je
    Zelle.

---

## README und X

### GIF: „Die Preisliste bewegt sich“

- **Inhalt:** BTC, PM2-Kapital je Short-Kontrakt als 3D-Fläche wie T1 (Höhe IV, Farbe und Isolinien = Kapital in %
  des Forwards). Darunter ein Zeitstreifen mit dem Referenz-Straddle unter PM2 und SM und einem Cursor. SM ist im
  GIF nur Referenzlinie, damit die Fläche gross bleibt.
- **Zeit:** ein Bild je Woche (Mittwoch 08:00 UTC) vom 13.06.2025 bis 17.09.2026, etwa 66 Bilder. An jedem Ereignis
  mit H4-Status wird das Bild 6 Frames gehalten. Ein Banner zeigt Datum und reinen Effekt, zum Beispiel
  „20 Aug 2026 · parameter change · straddle −23 %“. Die Isolinie, die am meisten wandert, wird dabei
  hervorgehoben.
- **Format:** 1200 × 675 (16:9, passt für X und README), 4 fps, Farbskala über alle Frames fest (`fit_limits`),
  Ziel unter 8 MB mit 64-Farben-Palette. Standbild für die Vorschau ist `social_t1_keyframe.png` (1600 × 900).
- **Bau:** `p2surface.animate(managers=("pm2",), …)` mit drei Ergänzungen: Isolinien (Code in
  `proto_praktiker.t1_engine_surface`), Haltebilder mit Banner an Ereignissen und Einheit % statt bp. Die
  Feed-Historie lädt quartalsweise und muss über `scripts/p2_heavy.py` laufen (Maschinensperre).
- **Falle:** Die Fläche ändert sich auch durch Markt und Vol. Ohne Banner sieht ein Zuschauer jede Bewegung als
  Parameteränderung. Deshalb zeigt der Zeitstreifen den reinen Parametereffekt als Stufe (K gegen K_prev).

### Social-Karten 1600 × 900

| Karte | Datei | Daten | Titel | Kernaussage |
|---|---|---|---|---|
| 1 | `social_1_engine_cheaper.png` | echt | „Parameter changes alone cut PM2 capital by 35%“ | Referenz-Straddle BTC: PM2 von 14,4 auf 10,0 % des Forwards, reine Parameterstufen −10, −8, −23 %; SM flach bei 29,6 % |
| 2 | `social_2_straddle_vs_leg.png` | echt | „Sell the put too: under PM2 it is almost free“ | 17.09.2026, 22 Tage ATM: PM2 ein Short-Call 11,9 %, Straddle 10,0 %; SM 14,3 % gegen 29,6 % |
| 3 | `social_3_contract_vs_book.png` | gemischt, PROTOTYP | „PM2 discounts the book, not the contract“ | nackter Short SM ÷ PM2 = 0,90 (echt, Median der Verkaufszellen) gegen Buch [H3-Median, synthetisch 4,1] |

Karte 2 ist die stärkste Praktiker-Karte. Sie braucht keine Hypothese und zeigt den Mechanismus in zwei Balken.
Ihr Schönheitsfehler: Das Einzelbein kommt vom Gitterknoten Δ 0,50 mit 22,3 Tagen, der Straddle vom gelisteten
Verfall mit 22 Tagen und Strike = Forward. Für die Veröffentlichung beide Beine des Referenz-Straddles einzeln
rechnen (Spalten `K_<m>_call`, `K_<m>_put` in `reference_book_series`, explorativ). Karte 3 wird erst nach H3
gefüllt. Fällt H3 anders aus, bleibt der Titel richtig, solange der Buchfaktor über 1 liegt. Liegt er darunter,
fällt die Karte weg. Eine vierte Karte „The next contract is cheap“ (ECDF aus F3) ist möglich, aber nur, wenn H2
nicht abgelehnt wird.

Stil wie `derive_surface/figures_social.py`: Titel 25 pt fett, Achsen 16 pt, Kernaussage im Titel, feste Bildgrösse
ohne `bbox tight`.

---

## Was aus dieser Linse in die Jury gehen sollte

1. **Den Kontrast Kontrakt gegen Buch als roten Faden.** F1 (echt) zeigt, dass PM2 einen einzelnen Short nicht
   verbilligt. F3 und F4 zeigen, dass das Buch billiger wird. Ohne F1 in dieser Form liest ein Praktiker T1 als
   „PM2 ist überall billiger“.
2. **F2 braucht eine Entscheidung zur Kaufseite**, bevor gezeichnet wird. Die Rendite auf die Prämie eines
   OTM-Longs ist real, dominiert aber jede gemeinsame Farbskala.
3. **F5 trägt reale Zahlen, die keine Hypothese brauchen** (−35 % BTC, −23 % ETH, −47 % HYPE reiner
   Parametereffekt). Sie gehören als Satz in den Ergebnisteil vor H4, weil sie die Dosis greifbar machen.
4. **Einheiten:** Kapital in % des Index/Forwards, Edge in bp des Kapitals. Die Zahl „11,8 % of forward“ versteht ein
   Maker sofort, „1 182 bp“ nicht.

## Dateien

- Prototyp-Code: `data/p2/fig_proto/praktiker/proto_praktiker.py` (Aufruf aus dem Repo-Stamm, Argumente T1, T2,
  F1 … A1, SOCIAL, KEYFRAME).
- Bilder: `t1_praktiker.png`, `t2_praktiker.png`, `f1_praktiker.png`, `f5_praktiker.png`, `a1_praktiker.png`
  (echt); `f2_praktiker.png`, `f3_praktiker.png`, `f4_praktiker.png`, `f6_praktiker.png` (PROTOTYP); Karten
  `social_1_engine_cheaper.png`, `social_2_straddle_vs_leg.png` (echt), `social_3_contract_vs_book.png`
  (PROTOTYP), `social_t1_keyframe.png` (echt, GIF-Standbild).
- Tabellen: `fig_t1.csv`, `fig_t1_markers.csv`, `fig_t2.csv`, `fig_f1.csv`, `fig_f5_events.csv`,
  `fig_f5_refbook_btc.csv`, `fig_a1.csv`, `fig_social_1.csv`, `fig_social_2.csv` (echt);
  `fig_f2_SYNTHETIC.csv`, `fig_f3_SYNTHETIC.csv`, `fig_f4_SYNTHETIC.csv`, `fig_f6_SYNTHETIC.csv`.
