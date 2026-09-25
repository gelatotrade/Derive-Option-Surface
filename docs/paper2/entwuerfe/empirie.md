# Abbildungsentwurf Paper 2, Linse Empirie

Stand 25.09.2026. Entwurf für die Jury nach dem Muster von Paper 1 (`docs/paper1/ABBILDUNGSWAHL.md`). Die Linse:
Ein Referee soll jedes der vier präregistrierten Urteile an der Abbildung selbst nachprüfen können. Dazu gehören
Schätzer, 90-%-Intervall, registrierte Schwelle, Ablehnungsbereich, Stichprobengrösse und Clusterzahl, und zwar in
der Abbildung selbst, nicht erst in der Bildunterschrift.

Prototypen liegen unter `data/p2/fig_proto/empirie/`. Das Skript ist `proto_empirie.py`, Aufruf:
`python3 data/p2/fig_proto/empirie/proto_empirie.py [T2 F1 F5 A1 F2 F3 F4 F6]`.

| Slot | Prototyp | Daten |
|---|---|---|
| T2 | `t2_empirie.png`, `fig_t2.csv` | echt (`results/p2/semantik/faktoren.csv`) |
| F1 | `f1_empirie.png`, `fig_f1.csv` | echt (`capital.parquet` × Buckets aus `markouts.parquet`) |
| F5 | `f5_empirie.png`, `fig_f5_events.csv` | echt (`reference_book.csv`, `manager_oi_share.csv`, `events.csv`, `params/*.json`) |
| A1 | `a1_empirie.png`, `fig_a1.csv` | echt (`validation.csv`) |
| F2 | `f2_empirie_SYNTHETIC.png` | echte Zellmenge, **synthetische** Edges und Bootstrap |
| F3 | `f3_empirie_SYNTHETIC.png` | **synthetisch** |
| F4 | `f4_empirie_SYNTHETIC.png` | **synthetisch**, nur die Strukturzahlen 1 943 und 1 431 stammen aus Nachtrag 4 |
| F6 | `f6_empirie_SYNTHETIC.png` | **synthetisch**, nur die Ereignisliste stammt aus `events.csv` |
| T1 | keiner (vorhandene Probe `data/p2/surface/probe_BTC_2026-09-17_pm2_sm.png`) | – |

Die synthetischen Bilder tragen ein rotes Wasserzeichen „PROTOTYP synthetic placeholder data“. Ihre Zahlen sind
erfunden und sagen nichts über H1 bis H4. Die Prototypen berechnen keine Teststatistik. Die Mediane, Intervalle und
ρ darin sind Platzhalter.

---

## 0 · Was für alle Abbildungen gilt

**Die Urteilsleiste.** Dieselbe Bildsprache in F2, F3, F4 und F6, damit ein Referee vier Urteile auf dieselbe Weise
liest:

- Schätzer als offener Kreis, 90-%-Intervall als dicker schwarzer Balken, registrierte Schwelle gestrichelt.
- Der Ablehnungsbereich ist schraffiert: bei H1 und H2 rechts der Schwelle (abgelehnt, wenn die obere Grenze
  hineinreicht), bei H3 links davon (abgelehnt, wenn die untere Grenze hineinreicht).
- Darüber fett eine Zeile: „registered: 0.18 [0.11, 0.27] → not rejected“. Die Zeile wendet die registrierte Regel
  auf die Zahlen aus `h*.json` an und prüft, ob sie zum Feld `rejected` passt. Weichen beide voneinander ab,
  bricht der Bau ab.
- Direkt daneben stehen n und die Zahl der Cluster (UTC-Tage), bei H2 und H3 auch die Zahl der Konten. Das ist das
  Gegenstück zu „Klassen tragen ihre Clusterzahl G“ aus Paper 1.
- Die Schraffur liegt nur hinter der registrierten Zeile. Eine explorative Zeile, die in den Bereich fällt, ist
  keine Ablehnung.

**Registriert, Sensitivität, explorativ.** In jedem Forest-Panel steht die registrierte Zeile oben, fett und mit
gefülltem Kreis. Darunter folgen die Sensitivitäten, die die Nachträge benennen (offene Raute). Explorative
Aufteilungen stehen zuletzt, grau hinterlegt. Die Präregistrierung erklärt alles ausser den vier Tests für explorativ
(Abschnitt „Inferenz“). Die Hinterlegung macht das sichtbar.

**Regeln aus Paper 1, übernommen:** CAS-Breiten 3,4 und 7,0 Zoll, keine Schrift unter 7 pt (Tick-Labels 7 pt, im
Prototyp überall eingehalten), Farbe immer doppelt codiert (Manager: PM2 blau, durchgezogen, Kreis; SM orange,
gestrichelt, Quadrat; Legacy PM grün, gepunktet, Dreieck; Basiswert: Farbe plus Markerform). Eine Zahl je Zelle,
Zellen unter 200 Fills als leeres Kreuz. Keine zweite y-Achse, keine Haarlinienbüschel. Nur T1 ist 3D. Die
Manager-Palette `#0072B2/#D55E00/#009E73` hat den Palettenvalidator bestanden (Deutan-ΔE der schlechtesten
Nachbarn 11,0). Graustufen wurden am Prototyp F5 geprüft: Nach der Korrektur sind SM hell mit Punkten, Legacy PM
mittel mit Schraffur und PM2 dunkel, mit einer schwarzen Grenzlinie dazwischen.

**Datenvertrag mit `inference_p2.py`.** Die Abbildungen rechnen keine Teststatistik nach. Während dieser Entwurf
entstand, hat die parallele Inferenz ihre Dateien unter `results/p2/` geschrieben. Die Tabelle ordnet sie den Slots
zu. Gelesen wurden dafür nur Spaltennamen und Schlüssel, keine Werte.

| Slot | liest (vorhanden) | fehlt noch |
|---|---|---|
| F1 | `fig_edge_maps.csv` mit `map ∈ {sm_pm2win, pm_pm2win, pm2}`: Zellgrösse = `sum_K / sum_index` (Verhältnis der Summen wie im Prototyp), `fills`, `occupied`. Alternativ `fig_capital_by_manager.csv` (`window = pm2`, Median und p25/p75 von K/Index je Zelle) | Entscheidung: Verhältnis der Summen (passt zu e^K und zum H1-Nenner) oder Median (robust gegen einzelne Fills). Der Prototyp nimmt die Summen. Beide Zahlen in einer Abbildung wären eine zweite Einheit und sind deshalb ausgeschlossen |
| F2 | `h1.json` (`stat, lo, hi, rejected, threshold, n, n_days, b, cells_present_min, cells_present_median, cells_by_ccy`), `h1_cells.csv` bzw. `fig_edge_maps.csv` `map = pm2` (`A_bp, B_bp, rank_A, rank_B, rank_shift`, dazu Rang-Intervalle `rank_*_lo/hi`) | die Verteilung der 9 999 ρ-Replikationen (Histogramm reicht). Ohne sie zeigt F2b nur Leiste und Intervall. Die Rang-Intervalle erlauben in F2a Fehlerkreuze für die zehn grössten Verschiebungen |
| F3 | `h2.json` (`stat, lo, hi, rejected, threshold, n, n_days, n_sample, n_excluded, share_nonpositive, accounts, fills_by_ccy`), `fig_h2_dist.csv` (`kind = hist/quantile/share_le_0/n` je `variant`), `sens_h2.csv` (Forest-Zeilen: `ratio_unit, ratio_tape, ratio_mm`, je Konto, je Basiswert) | nichts. Die Überlaufzahlen sollten als eigene `kind` in `fig_h2_dist.csv` stehen, falls die Histogrammgrenzen das Fenster [−2, 3] nicht abdecken |
| F4 | `h3.json` (`stat, lo, hi, rejected, threshold, n, n_days, n_excluded, n_not_applicable, share_days_over_63_options`), `fig_h3_series.csv` (je Maker-Tag `ratio_sm_pm2`, `over_63_options`: das Histogramm ist deskriptives Binning in der Abbildungsschicht), `sens_h3.csv` (`sm_pm2_le63`, `sm_pm2_gt63`, `sm_pm2_mm`, `pm_pm2_be`, je Konto) | nichts |
| F5 | `events.csv`, `fig_h4_events.csv` (`n_cells, n_pre, n_post, median_dose` je Ereignis), `params/*.json`, `reference_book.csv`, `manager_oi_share.csv` | nichts |
| F6 | `h4.json` (`stat, lo, hi, p, p_sided, clusters, fills, events_kept, cell_events, criteria.{beta_positive, p_le_alpha, beta_gt_placebo_p95}, placebo.{p95, share_ge_beta}`), `h4_placebo.csv` (`rep, beta`), `sensitivity_h4.json` (`by_ccy.*`, `no_outlier_cells.*`), `fig_h4_events.csv` (Dosis-Terzile `t1..t3` mit `y_pre, y_post` je Ereignis) | **die residualisierten FWL-Bins** (`x_mean, y_mean, n_fills` in 20 Bins). Ohne sie wird F6a zur Terzil-Darstellung aus `fig_h4_events.csv`: Veränderung des Halbspreads (post − pre) je Dosis-Terzil und Ereignis. Das ist ehrlich, aber roh und ohne Fixeffekte, und die Achse muss das sagen. Ein β je Ereignis gibt es nicht. F6b zeigt deshalb β je Basiswert und ohne Ausreisserzellen aus `sensitivity_h4.json`, grau hinterlegt als explorativ |
| A1 | `validation.csv`, `validation_summary.json` | optional das Feed-Alter der Testpopulation (aus `capital.parquet`, deskriptiv) |

Die Kennzahlen der Urteilsleisten (`stat, lo, hi, threshold, rejected, n, n_days`) haben in `h1.json` bis
`h4.json` dieselben Namen. `figures_p2.py` kann also eine einzige Funktion `ruler(ax, h)` für alle vier Tests
verwenden. Sie prüft `rejected` gegen die Regel in `rule`, damit Bild und Zahlenblatt nicht auseinanderlaufen.

**Prüfskript** (`scripts/p2_figure_check.py`, Muster Paper 1): Es vergleicht jede im Bild gedruckte Kennzahl mit
`h*.json`. Es zählt, ob in F1 genau so viele Kreuze stehen, wie die Zelltabelle Zellen unter 200 Fills hat
(einschliesslich Kombinationen ohne einen Fill). Ausserdem prüft es, ob F5 genau die Ereignisse mit `kept` gefüllt
zeigt, die `events.csv` führt, und ob die Urteilszeile mit `rejected` übereinstimmt.

---

## T1 · Die Engine-Sicht der Oberfläche

- **Zweck.** Die Abbildung zeigt, dass das Kapital eine Eigenschaft der Oberfläche ist, die die Engine selbst
  sieht, gerechnet am selben Block mit denselben Feeds.
- **Datenquelle.** `p2surface.capital_grid` für BTC am Block von `results/p2/surface_t1.json` (Probe:
  17.09.2026 08:00 UTC, 15 Verfälle), Seite short, Manager PM2 und SM. Das Gitter kommt als `fig_t1.csv` dazu
  (`manager, delta, tenor_days, iv, K, K_per_forward_bp`, wie `probe_BTC_2026-09-17_grid.csv`).
- **Kodierung.** Zwei 3D-Panels nebeneinander. Die Höhe ist die IV in Prozent, die Farbe das Kapital in bp des
  Forwards auf **einer** gemeinsamen Skala mit `cividis` (in Graustufen monoton), dazu ein Farbbalken. Die
  Empirie-Zusätze:
  1. Iso-Kapital-Konturen auf den Boden projiziert, beschriftet mit 7 pt. Damit trägt die Grösse auch ohne Farbe.
  2. Auf dem Boden die Bucketgrenzen von Paper 1: Call-Delta 0,10/0,25/0,40/0,60/0,75/0,90 (die |Δ|-Buckets liegen
     auf der Call-Delta-Achse symmetrisch) und Laufzeit 2/7/30/90 Tage. So führt T1 direkt zu F1 und F2.
  3. Gitterpunkte ausserhalb der quotierten Strikes (Flügel jenseits von `WING_PAD`) werden grau
     (`NA_COLOR`) statt extrapoliert.
  4. Im Kopf Block, UTC-Zeit, Zahl der Verfälle und je Panel min/Median/max von K. Probe: PM2 342/1 045/1 370 bp,
     SM 1 237/1 298/1 501 bp.
- **Grösse.** 7,0 × 3,0 Zoll. Die einzige 3D-Abbildung.
- **Kernaussage in 5 s.** Unter SM ist die Fläche fast einfarbig: Ein Short kostet überall rund 13 % des Forwards.
  Unter PM2 hängt der Preis von Delta und Laufzeit ab.
- **Fallen.** Die Höhe ist Vol und nicht Kapital, das muss die z-Achsenbeschriftung ausdrücklich sagen. Die
  Rückseite der Fläche ist verdeckt, deshalb die Bodenkonturen. Die fast einfarbige SM-Fläche wirkt leicht wie
  „keine Information“, ist aber der Befund. Die Abbildung zeigt nur Shorts. Bei Maker-Käufen ist K im Wesentlichen
  die Prämie (unter SM gibt es keine Gutschrift für Longs), das gehört in die Caption. Ein einzelner Block ist
  eine Momentaufnahme, die Zeit trägt F5.

## T2 · Was `get_margin` liefert

- **Zweck.** Die Abbildung zeigt, warum `C − net` keine Anforderung ist und dass der Widerspruch 11 gegen 1,2 aus
  Buch und Bewertung entsteht.
- **Datenquelle.** `results/p2/semantik/faktoren.csv`, Zeilen `historisch 17.09.` (`b17_exakt`) und `historisch
  24.09. … (H1_…)` (`b24`), Fälle A und B. Spalten `SM_Cnet, PM2_Cnet, SM_R_engine, PM2_R_engine, V_und_SM,
  V_PM2, F_Cnet, F_R_engine`. Die H0-Variante bleibt draussen (wie `MANUSKRIPT.md` 3a).
- **Kodierung.** Panel a ist ein Dotplot auf logarithmischer USDC-Achse, je Buch und Manager eine Zeile. Der
  gefüllte Marker steht für R, der offene für `C − net = R − V`, die graue Verbindung ist V. Manager nach Farbe
  und Form. Panel b zeigt die Quotienten SM/PM2 je Buch, gefüllt auf R und offen auf `C − net`, dazu die
  H3-Schwelle 2 gestrichelt. Die vier Zahlenpaare der Caption stehen direkt an den Punkten.
- **Grösse.** 7,0 × 2,6 Zoll.
- **Kernaussage in 5 s.** Beim Buch vom 24.09. (Fall B) liegt `C − net` unter PM2 sechsmal höher als R, weil
  V = −496 859 USDC hineinrutscht. Auf R liegen alle vier Bücher über 2, auf `C − net` zwei darunter.
- **Fallen.** Die Probebücher sind konstruiert und keine Maker-Bücher; sie dürfen nicht als Vorschau auf H3
  gelesen werden. Die Caption muss sagen, dass die Schwelle 2 aus diesen Büchern abgeleitet wurde
  (Präregistrierung, „Datenstand vor diesem Commit“). Eine Log-Achse ist nötig, weil R zwischen 17 k und 644 k
  liegt. Der Prototyp nennt das in der Achsenbeschriftung.

## F1 · Kapital je Kontrakt nach Manager

- **Zweck.** Die Abbildung zeigt, was ein einzelner Kontrakt je Manager über |Δ| × Laufzeit kostet, und macht die
  Textaussage „SM/PM2 läuft von … bis …“ für alle drei Basiswerte prüfbar.
- **Datenquelle.** `data/p2/derived/capital.parquet` (`K_sm, K_pm, K_pm2, amount, index_price, maker_side, ts`),
  verbunden über `trade_id` mit `delta_bucket, tenor_bucket` aus `data/p1/derived/markouts.parquet`. Filter: das
  PM2-Fenster je Basiswert, damit alle Manager dieselben Fills sehen. Zellgrösse ist das Verhältnis der Summen
  100·Σ K·a / Σ Index·a in Prozent des Index, wie der Edge im Papier. Besetzt ab 200 Fills. Im Finale liest die
  Abbildung `results/p2/fig_edge_maps.csv` (`sum_K / sum_index` der Karten `sm_pm2win`, `pm_pm2win`, `pm2`), sofern
  `sum_K` wie hier mengengewichtet ist. Das Prüfskript vergleicht mit der Prototyp-Rechnung. Der Prototyp schreibt `fig_f1.csv` (210 Zeilen, alle
  Basiswerte, beide Seiten).
- **Kodierung.** Panels a und b sind Heatmaps für BTC: Maker-Käufe oben, Maker-Verkäufe unten, Spalten SM, Legacy PM
  und PM2. In jeder Zelle steht eine Zahl mit zwei signifikanten Stellen. Die Schattierung ist logarithmisch und
  gilt gemeinsam für eine Zeile, sodass Manager innerhalb einer Seite vergleichbar sind. Zellen unter 200 Fills
  zeigen ×. Die Zahl der Fills steht in der y-Beschriftung. Panel c ist ein Streifen aller 173 besetzten Zellen
  aller Basiswerte: x ist der Quotient auf logarithmischer Achse, gefüllt SM/PM2, offen Legacy PM/PM2, Dreieck
  nach oben für Kauf und nach unten für Verkauf, Farbe nach Basiswert. Minimum und Maximum stehen im Kopf.
- **Grösse.** 7,0 × 3,9 Zoll.
- **Kernaussage in 5 s** (Pilotdaten, deskriptiv, kein Test). Für einen **einzelnen** Kontrakt ist PM2 nicht
  billiger als SM. SM/PM2 liegt über 173 besetzte Zellen zwischen 0,75 und 4,67 und in 86 Zellen unter 1. Der
  Legacy PM ist bei Verkäufen am teuersten (Legacy PM/PM2 0,95 bis 1,74). Der Netting-Vorteil von PM2 kann also
  erst im Buch entstehen, und genau das prüfen F3 und F4.
- **Fallen.**
  - Bei Käufen ist K fast die Prämie. Die obere Zeile ist deshalb eine Prämienkarte und keine Margin-Karte.
    Das muss in den Achsentitel, nicht nur in die Caption.
  - ETH und HYPE stehen nur im Streifen und in der CSV. Wer HYPE-Karten erwartet (25 von 70 HYPE-Zellen unter
    200 Fills), findet sie dort.
  - Die Caption im Gerüst sagt „each panel is shaded on its own scale“. Für einen Manager-Vergleich ist das
    falsch, die Skala muss je Zeile gemeinsam gelten.
  - Das Maximum 4,67 kommt aus einer einzelnen ETH-Kaufzelle. Der Text sollte neben min/max auch den Median der
    Zellquotienten nennen.

## F2 · Die Karte in zwei Nennern (H1)

- **Zweck.** Die Abbildung zeigt die Grösse, die H1 testet (Spearman-ρ der Zellränge), mit ihrem 90-%-Intervall
  gegen die Schwelle 0,5, und wo die Umordnung stattfindet.
- **Datenquelle.** `results/p2/h1.json` und `h1_cells.csv` (Zellwerte beider Nenner `A_bp`, `B_bp`, Ränge mit
  Intervallen), dazu die noch fehlende Bootstrap-Verteilung von ρ (siehe Datenvertrag). Zellmenge: alle besetzten Zellen im PM2-Fenster (Prototyp-Zählung 173). Ränge und
  mittlere Rangverschiebung sind deskriptive Umformungen der Tabelle. Die Abbildung darf sie aus `h1_cells.csv`
  bilden, ρ und das Intervall aber nicht.
- **Kodierung.**
  - Panel a: Rang-Rang-Streudiagramm, eine Marke je Zelle. Die x-Achse ist der Rang je Nominal, die y-Achse der
    Rang je PM2-Kapital, dazu die Diagonale. Basiswert nach Form und Farbe, Seite nach Füllung (voll = Verkauf).
  - Panel b: die Urteilsleiste für ρ über dem grauen Histogramm der 9 999 Replikationen, mit Schwelle 0,5 und
    schraffiertem Ablehnungsbereich. Die Achsenzeile nennt die Zahl der Zellen und die Cluster.
  - Panels c und d: mittlere Rangverschiebung (Rang PM2 − Rang Nominal) nach Laufzeit bzw. |Δ|, getrennt nach
    Seite. Das ist die Grundlage für den Satz `h1-reading` („läuft die Umordnung entlang Laufzeit, Delta oder
    Seite?“).
- **Grösse.** 7,0 × 3,2 Zoll.
- **Kernaussage in 5 s.** Liegen die Punkte auf der Diagonalen, ordnet der Nenner nichts um. Die Leiste zeigt
  fett, ob die obere Grenze 0,5 erreicht (H1 abgelehnt) und in welcher Dimension sich die Karte verschiebt.
- **Fallen.**
  - Die Caption im Gerüst beschreibt „lines connect the rank of each cell“. Das wären 173 Haarlinien, die
    Paper 1 ausdrücklich verboten hat. Das Rang-Rang-Streudiagramm zeigt dieselbe Information als Objekt.
  - ρ vermischt drei Basiswerte. Ein Teil der Umordnung kann ein Niveauunterschied zwischen den Basiswerten sein
    und keiner innerhalb eines Basiswerts. Die Formen müssen das erkennbar lassen. Gut wäre eine explorative
    Zeile „ρ innerhalb der Basiswerte“ in `h1.json`.
  - Im Bootstrap fallen Zellen weg, wenn eine Replikation keinen Fill hat. Die Zahl der Zellen je Replikation
    schwankt, und die Spanne (`n_cells_min_rep` bis `n_cells_max_rep`) gehört in die Achsenzeile.
  - 20 Fills mit K_PM2 ≤ 0 bleiben in den Summen (Nachtrag 4). Eine Zelle mit kleinem Summenkapital kann
    extrem werden. Der Rang schützt ρ davor, eine Karte in bp dagegen nicht. Deshalb zeigt F2 keine bp-Heatmap,
    die Werte stehen in `h1_cells.csv`.

## F3 · Der nächste Kontrakt im Buch eines dominanten Makers (H2)

- **Zweck.** Die Abbildung zeigt die Verteilung von ratio = (ΔK/Menge)/K_PM2,Einzel und das registrierte Urteil
  mit seinen Sensitivitäten.
- **Datenquelle.** `results/p2/h2.json`, `fig_h2_dist.csv`, `sens_h2.csv`. Die Zeilen kommen aus
  `data/p2/derived/marginal.parquet` (Spalten `ratio`, `ratio_unit`, `ratio_mm`, `ratio_tape`, `label`,
  `manager`, `day`). Struktur laut Datei: 20 000 Fills aus vier Konten (M3, M5, M8, M10) an 372 UTC-Tagen, 13 595
  unter PM2:ETH und 6 405 unter PM2:HYPE.
- **Kodierung.** Einspaltig mit zwei Panels.
  - Panel a: Histogramm im Fenster [−2, 3]. Der Teil ≤ 0 (gibt Kapital frei) ist grau schraffiert, der Teil > 0
    blau. Die Schwelle 0,5 ist gestrichelt, die Marke 1 („so teuer wie allein“) gepunktet, der Median als Dreieck
    am oberen Rand. Die Überläufe stehen als Zahl an den Rändern („89 beyond 3 →“), der Anteil ≤ 0 oben links.
  - Panel b: Forest mit der Urteilsleiste. Oben die registrierte Zeile (IM, ganzer Fill), darunter die
    Sensitivitäten aus Nachtrag 4 (nächster einzelner Kontrakt, MM, Tape-Buch) und explorativ PM2:ETH gegen
    PM2:HYPE. Der Kopf nennt Konten, Tage und Ausschlüsse (1 Fill mit K_Einzel ≤ 0).
- **Grösse.** 3,4 × 3,7 Zoll. Das Gerüst plant 3,4 × 2,4, aber ohne das Forest-Panel ist die Robustheit des
  Urteils nicht zu sehen. Alternative: F3 und F4 als ein `figure*` mit 7,0 × 2,8 Zoll, vier Panels nebeneinander,
  mit identischer Urteilsgrammatik (die Slotzahl bleibt 9, wenn F4 dafür in denselben Float geht).
- **Kernaussage in 5 s.** Welcher Anteil der Fills Kapital freigibt, wo der Median gegen 0,5 steht und ob
  irgendeine Sensitivität das Urteil kippt.
- **Fallen.**
  - Die H2-Population enthält **kein BTC**: Die vier PM2-Konten laufen unter PM2:ETH und PM2:HYPE. Das gehört in
    den Abbildungskopf, sonst liest man H2 als Aussage über alle drei Basiswerte.
  - Die Stichprobe von 20 000 ist eine Zufallsauswahl (Seed 20260924). `sampled` aus `h2.json` gehört in die
    Kopfzeile.
  - K_Einzel kann bei weit aus dem Geld liegenden Kontrakten winzig sein, dann explodiert ratio. Das Fenster
    [−2, 3] darf nichts verschlucken, deshalb die Überlaufzahlen.
  - Vier Konten sind wenig. Ein Konto kann den Median tragen. Die Aufteilung nach Konto gehört mindestens in
    die CSV und steht im Forest, falls sie mehr als eine Zeile hergibt, ohne einzelne Konten erkennbar zu machen.

## F4 · Was Netting wert ist (H3)

- **Zweck.** Die Abbildung zeigt K_SM/K_PM2 über Maker-Tage auf logarithmischer Achse, mit dem registrierten
  Urteil (untere Grenze gegen 2) und der Warnung aus Nachtrag 4, dass K_SM an den meisten Tagen kontrafaktisch
  ist.
- **Datenquelle.** `results/p2/h3.json`, `fig_h3_series.csv`, `sens_h3.csv`. Die Zeilen kommen aus
  `data/p2/derived/maker_days.parquet` (`K_sm`, `K_pm2`, `K_pm`, `K_*_mm`, `n_legs`, `manager`, `status`, `label`).
  Struktur: 1 943 Maker-Tage, davon 1 431 mit mehr als 63 Optionen (Nachtrag 4). Konten unter SM, PM:BTC, PM:ETH,
  PM2:ETH und PM2:HYPE.
- **Kodierung.**
  - Panel a: Histogramm auf logarithmischer x-Achse (Ticks 0,5 bis 64, gleiche Breite je Verdopplung), gestapelt
    nach ≤ 63 Optionen (blau) und > 63 Optionen („SM counterfactual“, grau schraffiert). Schwelle 2 gestrichelt,
    1 gepunktet, Median als Dreieck.
  - Panel b: Forest mit der Urteilsleiste, Ablehnungsbereich links von 2. Zeilen: registriert, nur Tage mit
    ≤ 63 Optionen, MM, dazu explorativ Legacy PM/PM2 (BTC- und ETH-Beine) sowie Aufteilungen nach dem Manager
    des Kontos.
- **Grösse.** 3,4 × 3,7 Zoll (oder zusammen mit F3, siehe dort).
- **Kernaussage in 5 s.** Wie viel Kapital PM2 gegenüber SM auf echten Büchern spart und ob das Urteil trägt, wenn
  man nur die Tage nimmt, an denen ein SM-Konto das Buch überhaupt halten dürfte.
- **Fallen.**
  - An 74 % der Tage wäre das Buch unter SM gar nicht zulässig. Ohne die Stapelung liest der Referee einen
    Netting-Faktor, der zum Teil eine Kontogrenze ist.
  - Ein Quotient braucht eine Log-Achse, sonst wirkt 0,5 näher an 1 als 2.
  - Maker-Tage desselben Kontos hängen zusammen. Die Cluster sind laut Präregistrierung UTC-Tage und nicht
    Konten. Das gehört in die Kopfzeile, damit niemand Konten-Cluster unterstellt.
  - In der Legacy-PM-Zeile fehlen HYPE-Beine. Ihr n ist deshalb kleiner, und das muss in der Zeile stehen.

## F5 · Die Engine über die Zeit

- **Zweck.** Die Abbildung macht die H4-Ereignisauswahl nachprüfbar: welche Parameteränderungen es gab, welche die
  Regeln behalten (Zusammenfassung je Tag, Dosisfilter 1 %, 20 Fills je Seite), wie gross sie für ein festes Buch
  sind und ob der geänderte Manager damals überhaupt Open Interest trug.
- **Datenquelle.** `results/p2/events.csv` (`kept, max_abs_dose, panel_cells, panel_fills_pre/post`),
  `results/p2/params/{CCY}_{pm,pm2}.json` (jede Zeile der Zeitlinie, also die Abstandsregel der Placebos),
  `results/p2/reference_book.csv` (`K_sm, K_pm, K_pm2, forward`; `K_*_prev` für den reinen Parametersprung),
  `results/p2/manager_oi_share.csv`.
- **Kodierung.**
  - Panel a: Ereignisspuren, je eine Zeile für BTC Legacy PM, BTC PM2, ETH Legacy PM, ETH PM2 und HYPE PM2.
    ● bedeutet „geht ins H4-Panel“, ◇ „behalten, aber keine Zelle mit 20 Fills je Seite“ (HYPE 08.01.2026),
    ○ „weggefallen, max |Dosis| unter 0,01“. Die Beschriftung ist max |Dosis|. Kleine graue Striche markieren jede
    Zeile der Zeitlinie, auch Collateral-Änderungen, weil diese für den Placebo-Abstand zählen.
  - Panel b: je Basiswert K des Referenzbuchs (Short-Straddle am Geld, 30 Tage, 08:00 UTC) in Prozent des Forwards
    je Manager (Linienart plus Farbe). Darunter ein schmaler Streifen mit dem OI-Anteil je Manager. Die ±14-Tage-
    Fenster der H4-Ereignisse sind grau hinterlegt, Überlappungen erscheinen dunkler.
  - Eine gemeinsame Kalenderachse von 2024-01 bis 2026-09.
- **Grösse.** 7,0 × 4,6 Zoll (Paper 1 F6 hatte 4,2).
- **Kernaussage in 5 s** (Pilotdaten). 14 von 18 Ereignissen bleiben, 13 gehen ins Panel. Fast jede behaltene
  Änderung verbilligt das Kapital. Am Referenzbuch senken 11 von 14 das Kapital, die drei Ausnahmen sind die
  Änderungen vom 08.01.2026 (+1,5 bis +1,6 %). Der grösste Sprung ist PM2 BTC am 20.08.2026 mit −23 %, HYPE am
  24.05.2026 mit −31 %. Die Dosis variiert also fast nur in eine Richtung.
- **Fallen.**
  - **Die Fenster überlappen**: 08.01. und 23.01.2026 (BTC, ETH, 15 Tage Abstand) sowie 08.05. und 24.05.2026
    (HYPE, 16 Tage). Das Nach-Fenster des ersten Ereignisses ist das Vor-Fenster des zweiten, dieselben Fills
    gehen in zwei (Zelle, Ereignis)-Gruppen ein. Die Präregistrierung verbietet das nicht, aber das Bild muss es
    zeigen, und der Text sollte es nennen.
  - Das Referenzbuch ist nicht die Dosis. Die Dosis ist zellspezifisch, das Buch veranschaulicht nur.
  - Die Linie des Legacy PM läuft bis 09/2026 weiter, obwohl sein OI-Anteil ab 03/2026 bei null liegt. Im Finale
    sollte die Linie dünn werden, wo der Manager weniger als 5 % des OI trägt.
  - Die Beschriftungen im HYPE-Streifen liegen im Prototyp zu dicht an den ETH-Strichen. Im Finale braucht die
    Spur mehr Zeilenabstand.

## F6 · Der Preis des Kapitals (H4)

- **Zweck.** Die Abbildung zeigt β so, dass man seine Steigung sehen kann, und beide registrierten Kriterien
  (Wild-p und Placebo-P95) nebeneinander.
- **Datenquelle.** `results/p2/h4.json`, `h4_placebo.csv`, `sensitivity_h4.json`, `fig_h4_events.csv`, dazu die
  noch fehlenden FWL-Bins (siehe Datenvertrag).
  Das Panel ist `data/p2/derived/h4_panel.parquet` (91 446 Fills, `dose, post, y_hs_bp, cell, event_id, day`), die
  Dosen stammen aus `results/p2/h4_doses.csv`.
- **Kodierung.**
  - Panel a: Partialregressionsbild (Frisch-Waugh-Lovell). Die x-Achse zeigt post × Dosis, die y-Achse den
    Halbspread in bp des Index, beide nach α_{Zelle,Ereignis} und γ_{Tag,Basiswert} residualisiert, in 20 gleich
    besetzten Bins. Die Markerfläche ist proportional zur Zahl der Fills. Die Gerade hat genau die Steigung β. So
    sieht ein Referee, ob ein einzelner Bin β trägt. Achsenzusatz: „< 0: capital got cheaper“.
  - Panel b (explorativ, grau hinterlegt): β je Basiswert und β ohne Ausreisserzellen aus `sensitivity_h4.json`,
    jeweils mit 90-%-Intervall und Clusterzahl, die registrierte Schätzung als senkrechte Linie. Der Prototyp
    zeigt β je Ereignis. Das schätzt die Inferenz nicht, es wäre ein Zusatzwunsch.
  - Panel c: Histogramm der 100 Placebo-β, P95 gestrichelt, β als dicke Linie. Darüber die Prüfliste in fett:
    „one-sided wild p = … ≤ 0.05: met / not met“, „β > placebo P95: met / not met“, „H4 rejected / not rejected“.
- **Grösse.** 7,0 × 3,0 Zoll.
- **Kernaussage in 5 s.** Ob der Halbspread mit der Kapitaländerung sinkt, und ob beide Kriterien erfüllt sind.
  H4 braucht beide, und die Prüfliste zeigt, an welchem es gegebenenfalls scheitert.
- **Fallen.**
  - Vorzeichen: Die Dosis ist log(K_nach/K_vor), negativ heisst billiger. H4 sagt β > 0 voraus (billigeres Kapital
    führt zu kleinerem Halbspread). Ohne Achsenhinweis liest man es verkehrt herum.
  - Ein roher Binscatter von y gegen die Dosis ohne die Fixeffekte hat nicht die Steigung β. Nur die
    residualisierten Bins aus der Inferenz sind zulässig. Der Terzil-Ersatz aus `fig_h4_events.csv` darf keine
    Gerade mit Steigung β tragen (siehe Datenvertrag).
  - Wegen F5 laufen fast alle Dosen in eine Richtung (Lockerungen). β wird auf der Seite x < 0 identifiziert, die
    Bins zeigen das ehrlich, der Text sollte es sagen.
  - Die Placebos leihen sich die Dosisvektoren echter Ereignisse. Eine Verteilung, die nicht um null liegt, ist
    ein Hinweis auf Saisonalität und kein Fehler der Abbildung.
  - Nach Paper-1-Regel steht neben der Placebo-Position auch der p-Wert. Beide gehören in Panel c, nicht in die
    Caption.

## A1 · Stimmt der Nachbau mit der Chain überein?

- **Zweck.** Die Abbildung zeigt die präregistrierte Validierung je Basiswert und Manager gegen die Schwellen
  (Median < 0,1 %, p95 < 1 %) mit allen Fallzahlen.
- **Datenquelle.** `results/p2/validation.csv` (`kind, ccy, manager, is_initial, rel_err, n_legs, book, status`),
  Kennzahlen je Zelle aus `results/p2/validation_summary.json`. 2 Fälle mit `status = revert` bleiben draussen und
  werden gezählt.
- **Kodierung.**
  - Panel a: Einzelkontrakte, je Basiswert und Manager eine Zeile. Oben IM (kräftig), unten MM (blass). Balken
    p25 bis p75, Whisker min bis max, schwarzer Strich für den Median, Raute für p95 (gefüllt IM, offen MM). Die
    x-Achse ist log |rel| von 1e−13 bis 1e−1. Exakte Nullen liegen in einem grauen Streifen „exact“ am linken Rand
    (359 der Einzelfälle sind bitgleich). Die Schwellen sind gestrichelt, n steht rechts.
  - Panel b: Bücher. Die x-Achse zeigt die Beine (log), die y-Achse |rel| (log), Form und Farbe je Manager, IM
    gefüllt, MM offen. In der Achsenbeschriftung: 20 Maker-Tage, Bücher je Basiswert BTC 7, ETH 18, HYPE 1.
- **Grösse.** 7,0 × 2,8 Zoll.
- **Kernaussage in 5 s** (echt). Die Mediane je Zelle liegen höchstens bei 9e−9, die grösste Einzelabweichung
  bei 1,9e−7 (MM), also mindestens vier Dekaden unter den Schwellen. Der Fehler wächst nicht mit der Buchgrösse (2 bis 245 Beine).
- **Fallen.**
  - Die Validierungsblöcke verlangen frische Feeds (Vol-Push höchstens 20 min, Forward höchstens 1 h alt,
    `VALIDIERUNG.md`), die Testpopulation nicht. A1 belegt die Engine, nicht die Feed-Zuordnung bei alten Feeds.
    Vorschlag: ein Panel c mit der Verteilung des Feed-Alters (`vol_age` in `capital.parquet`) der
    Testpopulation neben der Validierungsauswahl, oder ein Satz in der Caption.
  - Für HYPE steht die Bücherzeile auf **einem** Buch. Das n muss im Bild stehen (steht in der Achsenbeschriftung).
  - Eine Log-Achse über zwölf Dekaden lässt 1e−8 und 1e−2 optisch nah wirken. Die Schwellen brauchen eine
    Beschriftung direkt an der Linie.

---

## README und X

### GIF: die Kapitalfläche über die Zeit

- **Inhalt.** BTC, Seite short, PM2. Die Kapitalfläche als **2D-Heatmap** über Call-Delta × Laufzeit (log), nicht
  in 3D: Auf X wird das GIF auf rund 600 px verkleinert, und eine 3D-Fläche mit Verdeckung ist dort nicht lesbar.
  Die 3D-Fassung (wie `data/p2/surface/BTC_capital_short_2026-08-14_2026-08-27.gif`) bleibt für die README.
- **Zeit.** Tägliche Frames um 08:00 UTC vom 13.06.2025 bis 17.09.2026, jeder dritte Tag (rund 155 Frames), 12 fps.
  An jedem H4-Ereignis hält die Animation eine Sekunde an, mit Einblendung „Parameter change 20 Aug 2026: grid ±17 %
  → ±14 % · reference book −23 %“ aus `events.csv` und `reference_book.csv`.
- **Unterer Streifen.** Die Zeitreihe des Referenzbuchs (PM2 durchgezogen, SM gestrichelt) mit Cursor und
  Ereignismarken im Stil von F5 (● im Panel, ◇, ○). Das ist `p2surface._draw_series`.
- **Ehrlichkeit.** Eine feste Farbskala über alle Frames (`p2surface.fit_limits`). Jeder Frame zeigt Datum und
  Block. Verfälle ohne frischen Feed erscheinen grau (`NA_COLOR`) und werden nicht interpoliert. Eine Plakette
  „stale feed“ erscheint, wenn ein Feed älter als ein Tag ist. Die Werte aller Frames stehen in
  `results/p2/gif_frames.csv` (Datum, Block, Zahl der Verfälle, K min/Median/max).
- **Format.** 1200 × 675 px, unter 8 MB (X erlaubt 15 MB, GitHub rendert grosse GIFs langsam), dazu ein
  statischer Endframe als PNG für Leser ohne Animation.

### Social-Karten (1600 × 900 px)

Gemeinsame Regeln: eine Botschaft je Karte, eine grosse Zahl mit Intervall und n, Schrift mindestens 28 px (auf
600 px Breite noch 10 px), Quelle und Präregistrierungs-Commit in der Fusszeile, Farbe doppelt codiert wie im
Papier. Zahlen nur aus `results/p2/`. Solange die Tests laufen, tragen die Karten zu H1 bis H4 Platzhalter.

1. **„One contract, three price tags“** (aus F1, echte Daten). Die BTC-Short-Heatmap unter PM2, daneben der
   Quotientenstreifen. Grosse Zahl: die Spanne SM/PM2 über die besetzten Zellen. Unterzeile: „for a single
   contract PM2 is not cheaper than SM, netting is where it pays“. Die Unterzeile gilt nur, wenn F3 und F4 das
   tragen, sonst entfällt sie.
2. **„What the next contract costs“** (H2 und H3). Zwei Urteilsleisten übereinander, der Median von ΔK/K_Einzel und
   der Median von K_SM/K_PM2, jeweils mit Intervall, Schwelle und „pre-registered · rejected/not rejected“.
3. **„The engine got cheaper, did spreads follow?“** (F5 und F6). Links die Referenzbuch-Linie BTC PM2 mit den
   Sprüngen (−23 % am 20.08.2026), rechts β mit der Placebo-Verteilung und der Prüfliste. Diese Karte kommt erst,
   wenn H4 ausgewertet ist.

---

## Offene Fragen an die Jury und an die Inferenz

1. Soll F2 die Rang-Rang-Darstellung bekommen (Empirie) statt der Verbindungslinien aus dem Gerüst? Ich empfehle
   ja, wegen der Haarlinien-Regel aus Paper 1.
2. F3 und F4 als ein gemeinsamer `figure*` (7,0 × 2,8) oder zwei einspaltige (3,4 × 3,7)? Der gemeinsame Float
   macht die Urteilsgrammatik vergleichbar und spart eine Fliesstelle.
3. Kann `inference_p2.py` noch die FWL-Bins für F6a und die Replikationsverteilung von ρ für F2b schreiben? Ohne
   sie fällt F6a auf die rohen Dosis-Terzile zurück, F2b auf die blosse Leiste, und die Abbildungsschicht darf
   beides nicht nachrechnen.
4. Die überlappenden H4-Fenster (Januar, Mai) müssen im Text erwähnt werden. Die Abbildung zeigt sie bereits.
