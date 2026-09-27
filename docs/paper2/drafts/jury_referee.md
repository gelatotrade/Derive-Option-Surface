# Jury Paper 2, Juror Referee (mit Nachrechnung)

Stand 25.09.2026. Grundlage: die drei Entwurfssätze `mechanismus.md`, `empirie.md` und `praktiker.md`, alle
Prototypen unter `data/p2/fig_proto/`, die Spezifikation (Abschnitt 6), die Präregistrierung mit den Nachträgen 1
bis 4, `paper2/main.tex` und die Daten unter `data/p2/derived/` und `results/p2/`. Nichts wurde committet. Das
Urteil des zweiten Jurors (`jury_gestaltung.md`) habe ich absichtlich nicht gelesen, damit beide Urteile
unabhängig bleiben.

**Blindheit gegenüber den Urteilen.** Aus den Inferenzdateien habe ich nur Schema, Schlüssel und Strukturzahlen
gelesen (n, Tage, Konten, Zellen, zulässige Placebo-Tage). Die Felder `stat, lo, hi, rejected, p, p_sided`, die
Kriterien und die Placebo-Perzentile waren maskiert. Eine Offenlegung: In `h4.json` waren `se`, `t` und
`fe.beta_direct_solve` nicht maskiert. Ich kenne deshalb das Vorzeichen der H4-Schätzung. Die Empfehlung zu F6
ist so gefasst, dass sie für beide Vorzeichen gilt. Die übrigen Urteile (H1 bis H3) kenne ich nicht.

Nachgerechnet wurde mit `capital.parquet` ⋈ `markouts.parquet` (336 087 Fills im PM2-Fenster), dem
Probe-Gitter vom 17.09.2026, `faktoren.csv`, `reference_book.csv`, `events.csv`, `params/*.json`,
`h4_doses.csv`, `h4_panel.parquet`, `marginal.parquet`, `maker_days.parquet` und `validation.csv`. Die
Hilfsskripte liegen nur im Scratchpad.

---

## 1 · Urteil in einer Tabelle

| Slot | Wahl | Hauptgrund | Wichtigste Auflage |
|---|---|---|---|
| T1 | **M** (3D a/b und 2D-Streifen c/d mit bindender Regel), dazu Titelzahlen von P, Kopfzeile und Bucketgitter von E | Nur M sagt, *welche* Regel das Kapital setzt, und nur die 2D-Streifen tragen die Iso-Linien lesbar | Block nach vorab festgelegter Regel wählen, Regime (±14-%-Gitter seit 20.08.2026) im Bild nennen |
| T2 | **P a + P b** mit der H3-Schwelle aus M/E, dazu **M c** (Szenario-Profil), neu gerechnet auf dem Referenz-Straddle | P a ist linear und zeigt V als Fläche. E a ist logarithmisch, dort ist der Abstand der Marker nicht V | T2c muss dieselben Zahlen liefern wie F5c (10,0 / 29,6 %), nicht 9,7 / 29,0 % |
| F1 | **E** (BTC-Karten drei Manager × zwei Seiten, zwei signifikante Stellen, Streifen aller 173 Zellen), dazu die gemeinsame Graustufenskala von M und die Streifenordnung von P, **plus Regime-Aufteilung** | Nur E zeigt den Manager-Vergleich je Zelle *und* alle Basiswerte | Die Karte mittelt über vier Parameterstände. Das Vorzeichen von „SM billiger als PM2“ kippt im letzten Regime, das muss im Streifen stehen |
| F2 | **P** (sechs Karten Edge je PM2-Kapital und Rang-Rang-Bild mit Rangbändern) mit der **Urteilsleiste von E** und **neuen Vorzeichen-Hilfslinien** | Die Karte ist Beitrag 1 des Papiers und gehört ins Bild. Die Urteilsleiste zeigt Schätzer, Intervall und Regel | Der H1-Test hat eine strukturelle Untergrenze nahe ρ ≈ 0,73 (Abschnitt 2.1). Das muss sichtbar werden, zusammen mit einer explorativen Zeile „ρ innerhalb Vorzeichen/Seite“ |
| F3 | **P a** (ECDF mit Bändern) und **E b** (Forest mit Urteilsleiste und Sensitivitäten), Konten als explorative Zeilen | ECDF liest den Median direkt bei 0,5 ab und passt zu den Bins von `fig_h2_dist.csv` ([−1; 2] mit offenen Rändern) | Kopfzeile: vier Konten, nur ETH und HYPE (kein BTC), M3 ist das einzige HYPE-Konto |
| F4 | **E** (Histogramm gestapelt ≤ 63 / > 63 Optionen und Forest), Konten als explorative Zeilen aus `sens_h3.csv` | Nur E zeigt Urteil, Intervall und den kontrafaktischen Anteil (1 431 von 1 943 Tagen) zugleich | Kopfzeile sagt 9 Konten, nicht 10. Explorative Regime-Zeilen anfordern |
| F5 | **P** (OI-Streifen, Ereignisleiste mit reinem Parametereffekt, BTC-Referenz-Straddle) mit den **Ereigniszuständen, Timeline-Strichen und ±14-Tage-Fenstern von E** und einem **neuen Band der zulässigen Placebo-Tage** | Ein Bild, das die H4-Auswahl prüfbar macht und die Grösse der Stufen in Zahlen nennt | Fehler von P beheben: der SM-Anteil fehlt im HYPE-Streifen. y-Achse in c ab 0 |
| F6 | **Neu kombiniert:** a Dosis-Streifen aller 13 Panel-Ereignisse, b FWL-Binscatter von E mit Dosis-Rug, c Placebo-Histogramm mit der Prüfliste von E, d kleiner explorativer Forest | Nur die residualisierten Bins haben die Steigung β. Die Dosis-Stütze (Hälfte der Paare unter 1 %) muss sichtbar sein | Solange `inference_p2.py` keine FWL-Bins schreibt, trägt b **keine** β-Gerade |
| A1 | **P** (a Streifen IM mit beschrifteten Schwellen, b Bücher gegen Beinzahl) mit den Medianstrichen von M und der p95-Raute von E | Enthält alle präregistrierten Grössen und zeigt, dass der Fehler nicht mit der Buchgrösse wächst | Ein Revert-Fall (zwei Zeilen IM/MM), nicht „zwei Reverts“. Feed-Alter als Satz, kein eigenes Panel |
| GIF | 3D-PM2-Fläche wöchentlich mit Haltebildern an Ereignissen (M/P), Zeitstreifen mit reinen Parameterstufen (P), die Ehrlichkeitsregeln von E | Einzige Form, in der Markt- und Parameterbewegung getrennt sichtbar sind | Feste Skala, Datum und Block je Bild, `gif_frames.csv`, graue Verfälle bei altem Feed |
| Karten | 1 M „One short BTC straddle. Three margin engines.“ · 2 P-Standbild der Fläche · 3 Urteilskarte H1 bis H4 in der Grammatik von E | Jede Karte trägt genau eine Aussage, die das Papier deckt | P-Karte 3 („discounts the book, not the contract“) entfällt, Begründung in Abschnitt 2.2 |

Abkürzungen: M = Mechanismus, E = Empirie, P = Praktiker.

---

## 2 · Befunde der Nachrechnung, die die Wahl bestimmen

### 2.1 H1 hat eine strukturelle Untergrenze, und F2 muss sie zeigen

Von den 173 besetzten Zellen haben **74 einen Netto-Edge ≤ 0** (Käufe 26 von 87, Verkäufe 48 von 86;
`h1_cells.csv`, Spalte `A_bp`). Der Kapitalnenner ist in jeder Zelle positiv (κ = Σ K·a / Σ Index·a zwischen
0,07 und 38,7 %). Also gilt sign(B) = sign(A) in jeder Zelle: Alle 99 positiven Zellen stehen in *beiden* Karten
vor allen 74 nicht positiven. Selbst wenn der Nenner die Reihenfolge innerhalb beider Gruppen völlig zufällig
machen würde, läge Spearman-ρ im Mittel bei **0,73** (Simulation mit 4 000 Ziehungen, 90 % der Werte zwischen
0,70 und 0,77). Die Schwelle der Präregistrierung ist 0,5.

Das ist eine Eigenschaft der registrierten Statistik, keine Frage der Gestaltung, und sie ändert den Test nicht.
Ein Referee wird sie aber finden. Die Abbildung muss sie deshalb zeigen, sonst wirkt jedes ρ über 0,5 wie ein
empirischer Befund über die Umordnung. Die Zahl habe ich ohne Kenntnis von ρ hergeleitet.

- **Im Rang-Rang-Bild** stehen Hilfslinien bei Rang 99 bzw. 74 („edge ≤ 0 below/left“). Die Punkte fallen dann
  sichtbar in zwei Blöcke. Die Umordnung, um die es geht, ist die Streuung *innerhalb* der Blöcke.
- **Im Forest** stehen explorative Zeilen „ρ innerhalb Edge > 0“, „ρ innerhalb Edge ≤ 0“, „ρ nur Käufe“ und
  „ρ nur Verkäufe“, grau hinterlegt. `sensitivity.json` hat heute nur die Aufteilung nach Basiswert
  (`g_by_ccy`). Die übrigen Zeilen muss `inference_p2.py` noch schreiben, als explorativ gekennzeichnet.
- Die log-log-Darstellung von M (Panel F2a mit κ-Diagonalen) ist damit nicht tragfähig. 43 % der Zellen lägen
  am Boden. Der Prototyp hat das verdeckt, weil seine synthetischen Edges fast alle positiv waren.

### 2.2 F1 mittelt über vier Parameterstände, und die Kernaussage zum Einzelkontrakt kippt

E und P tragen als roten Faden „Für einen einzelnen Short ist PM2 nicht billiger als SM“ (SM/PM2 im Median
0,94 / 0,90 / 0,88, in 74 % der Verkaufszellen unter 1). Gepoolt über das PM2-Fenster stimmt das. Nach Regime
getrennt (Fills ≥ 200 je Zelle und Regime, Verhältnis der Summen) sieht es anders aus:

| Median SM/PM2, Verkaufszellen | bis 22.01.2026 | 23.01. bis 23.05.2026 | 24.05. bis 19.08.2026 | ab 20.08.2026 |
|---|---|---|---|---|
| BTC | 0,91 (20 Zellen) | 0,91 (19) | 0,97 (19) | **1,40** (6) |
| ETH | 0,88 (31) | 0,88 (24) | 0,93 (27) | **1,14** (18) |
| HYPE | – | 0,72 (15) | 1,06 (14) | 1,44 (1) |
| Anteil der Verkaufs-Fills mit K_SM < K_PM2 | 82,5 % | 69,2 % | 54,1 % | **15,4 %** |

T1 widerspricht F1 deshalb sichtbar: Am 17.09.2026 ist SM nur an 9 von 740 Gitterknoten billiger als PM2 (Median
SM/PM2 = 1,26), F1 sagt „SM billiger in 74 % der Verkaufszellen“. Beides ist richtig. Ohne Regime-Angabe liest
ein Referee das aber als Widerspruch.

Daraus folgen drei Dinge. **(i)** Der Streifen in F1 zeigt je Zeile (Basiswert × Seite) gefüllte Zeichen für das
ganze Fenster und hohle für „ab 20.08.2026“, jeweils mit Medianstrich. Dazu kommt eine Tabelle
`fig_f1_regimes.csv`. **(ii)** Der Satz „PM2 discounts the book, not the contract“ gilt nur bis August 2026.
P-Karte 3 entfällt, und der Text muss den Satz zeitlich einschränken. **(iii)** Die Anatomie-Spalte von M in F1
entfällt. Sie zeigt einen Kontrakt aus dem letzten Regime (11,8 / 14,1 %) neben Karten, die über alle Regime
mitteln, und wiederholt nur die Titelzahlen von T1.

### 2.3 Ein Objekt, zwei Zahlen: der BTC-Straddle am 17.09.2026

M T2c rechnet den Straddle am Gitterknoten Δ = 0,50 mit 30,4 Tagen (interpoliert, Strike 77 017) und kommt auf
PM2 9,65 %, getrennte Beine 23,45 % und SM 29,02 % des Forwards (`fig_t2_proto.csv`: 7 399,89 / 17 980,39 /
22 248,85 USDC bei F = 76 668). F5c und die Karten zeigen denselben Straddle aus `reference_book.csv` (gelisteter
Verfall mit 22 Tagen, Strike = Forward): PM2 **10,03 %**, SM **29,61 %**, Legacy **19,68 %**. Im Endbau rechnet
T2c auf der Zeile von `reference_book.csv` desselben Tages. Die Spalte „Beine getrennt“ kommt dazu. So gibt es im
Papier nur eine Zahl je Objekt.

### 2.4 Die Prototypen sind breiter, als sie gedruckt werden

`figstyle` speichert mit `savefig.bbox = "tight"`. Text ausserhalb der Achsen vergrössert deshalb die Leinwand
über die CAS-Breite hinaus. Mit `\linewidth` gesetzt, schrumpft die Schrift entsprechend:

| Prototyp | geplant | gespeichert | 7 pt werden zu |
|---|---|---|---|
| E F3, E F4 | 3,4 in | 5,46 in | **4,4 pt** |
| P F3, P F4 | 3,4 in | 4,50 in | **5,3 pt** |
| E F1 | 7,0 in | 8,49 in | **5,8 pt** |
| M F5 | 7,0 in | 7,72 in | 6,3 pt |
| M F2 · E F6 · P F5 | 7,0 in | 7,58 · 7,54 · 7,48 in | 6,5 pt |
| E T2 · P F2 · M T2 · E F5 · P F6 | 7,0 in | 7,38 · 7,32 · 7,24 · 7,16 · 7,12 in | 6,6 bis 6,9 pt |

`figures_p2.py` braucht einen Test: gespeicherte PDF-Breite = 3,4 bzw. 7,0 in ± 0,02, und keine Textinstanz
unter 7 pt nach dieser Skalierung. Wie M richtig bemerkt, setzt `figures_p1.py` selbst 6,0 und 6,5 pt (Zeilen
70, 143 bis 175, 222 bis 231). Diesen Code nicht übernehmen.

### 2.5 H4: drei Strukturmerkmale, die kein Prototyp vollständig zeigt

- **Überlappende Fenster.** 91 446 Panelzeilen stammen aus **84 919** Fills. 6 527 Fills (7,7 %) stehen in zwei
  Ereignisfenstern: BTC 1 457 und ETH 2 861 (08.01./23.01.2026), HYPE 2 209 (08.05./24.05.2026). E hat das
  erkannt. Die Zahl gehört in die Kopfzeile von F6 und in den Text.
- **Zulässige Placebo-Tage.** Laut `h4.json` (`placebo.admissible_days`) hat ETH PM2 nur **10** zulässige Tage
  (16. bis 25.07.2025), BTC PM2 54 (16.07.2025 bis 21.03.2026), HYPE PM2 67, die Legacy-Ereignisse 363 bzw. 319.
  Die ETH-Placebos von PM2 stammen also aus einem einzigen Juli-Fenster. Die Präregistrierung erzwingt das,
  weil jede Zeile der Zeitlinie zählt, auch Collateral-Änderungen. F5 muss das als Band je Basiswert zeigen, F6c
  nennt die Tageszahlen je Basiswert.
- **Dosis-Stütze.** Über die 475 Zell-Ereignis-Paare ist die Dosis im Median −0,006. 11,2 % sind positiv
  (höchstens +0,022), nur 48,6 % liegen unter −0,01, das Minimum ist −0,442. Die Hälfte der Paare dient also
  praktisch als Kontrolle, und β wird aus Lockerungen identifiziert. Ein Binscatter mit 20 gleich besetzten Bins
  legt rund zehn Bins auf x ≈ 0. Ohne Rug oder Histogramm der Dosis sieht der Leser nicht, woher die Steigung
  kommt.

### 2.6 Datenvertrag: was schon da ist und was fehlt

- **F1 braucht keine neue Inferenzspalte.** `fig_edge_maps.csv` enthält `sum_K` und `sum_index` für die Karten
  `pm2`, `sm_pm2win` und `pm_pm2win`. 100·`sum_K`/`sum_index` reproduziert die Zellen der Prototypen auf
  6 × 10⁻¹⁴, und die Quotienten SM/PM2 auf 6 × 10⁻¹⁵. Die Fillzahlen stimmen exakt, und die Besetzung auch
  (210 Zellen, 173 besetzt). Die Datenlücke, die M und P melden (`sum_K_sm` fehlt), existiert also nicht.
- `fig_capital_by_manager.csv` enthält den **Median je Fill als Anteil** (0,11 = 11 %), nicht das Verhältnis der
  Summen. Beispiel BTC-Verkauf 00-10/2-7d: Median 11,0 %, Verhältnis der Summen 9,9 %. Die Datei gehört nur in
  die CSV, sonst stehen zwei Zahlen für dieselbe Zelle im Papier.
- `fig_h2_dist.csv` hat Bins von 0,05 auf [−1; 2] mit offenen Rändern. Das Fenster [−2; 3] von E ist damit
  nicht darstellbar, P hat das richtig gelesen.
- **Fehlt und wird gebraucht:** `fig_h4_fwl_bins.csv` (x̄, ȳ, Fills je Bin nach α und γ residualisiert, mit
  einem Test, dass die OLS-Steigung der Bins auf Rundung β ergibt), `h4_placebo_days.csv` (die gezogenen und
  die zulässigen Tage je Basiswert), die explorativen H1-Zeilen aus 2.1, Regime-Zeilen für H2 und H3 (2.2 und
  Lücke 3) und `fig_f1_regimes.csv`. **Fehlt, optional:** `h1_rho_draws.csv` (Histogramm der 9 999 ρ). Die
  Urteilsleiste trägt auch ohne.

---

## 3 · Nachgerechnete Zahlen der Entwürfe

| Behauptung | Entwurf | Nachgerechnet | Urteil |
|---|---|---|---|
| ATM-30-Tage-Short PM2 11,8 %, SM 14,1 % des Forwards | P, M (F1-Anatomie) | 11,83 / 14,08 (Gitter Δ 0,50, 30,4 d) | ✓ |
| PM2 3,4 bis 13,7 %, SM 12,4 bis 15,0 % am 17.09.2026 | P, E, M | 342 bis 1 370 bp / 1 237 bis 1 501 bp | ✓ |
| T2-Faktoren 11,86/10,76, 1,19/2,14, 2,33/3,19, 1,46/3,61; R 211k/99k, −V 497k | alle | `faktoren.csv` Zeilen b17_exakt und b24 (H1-Variante) | ✓ |
| „C − net liegt beim 24.09.-Buch unter PM2 sechsmal über R“ | E | 595 694 / 98 835 = 6,03 | ✓ |
| Straddle PM2 9,7 %, Beine getrennt 23,5 %, SM 29,0 % | M (T2c) | arithmetisch ✓, aber anderes Objekt als F5c (10,0 / 29,6 %) | ✗ vereinheitlichen (2.3) |
| BTC Käufe SM 0,07 bis 16,9 %, PM2 0,07 bis 10,9 %; Verkäufe SM 12,8 bis 15,1, Legacy 8,5 bis 24,3, PM2 7,8 bis 17,7 % | M | 0,07–16,85 / 0,07–10,86; 12,83–15,11 / 8,48–24,30 / 7,80–17,69 | ✓ |
| SM/PM2 0,75 bis 4,67, in 86 Zellen < 1; Legacy/PM2 0,95 bis 1,74 | E | 0,752–4,669; 86; 0,946–1,736. Maximum: ETH-Kauf 90–100/30–90d (SM 67,8 %, PM2 14,5 %, 234 Fills) | ✓, nur gepoolt (2.2) |
| Verkäufe SM/PM2 im Median 0,94/0,90/0,88, 74 % unter 1; Legacy 1,38/1,35 | P | 0,943/0,902/0,875; 74,4 %; 1,382/1,355 | ✓, nur gepoolt (2.2) |
| Nackter Short unter PM2 7 bis 21 % des Index (HYPE 18 bis 39 %) | P | 7,07–21,36 (HYPE 17,50–38,73) | ✓ |
| Referenz-Straddle 17.09.2026: 29,6 / 19,7 / 10,0 % | M, P | 29,61 / 19,68 / 10,03 | ✓ |
| PM2 BTC von 14,4 auf 10,0 %; reine Stufen −10, −8, −23 %; kumuliert −35 % (ETH −23, HYPE −47) | P | 14,41 → 10,03; −9,96 / −7,54 / −22,93 %; −35,0 / −22,6 / −47,1 % (einschliesslich +1,61 % am 08.01. und −0,35 % am 13.06.2025) | ✓ |
| Log-Sprünge: BTC Legacy −18,6; BTC PM2 +1,6 / −10,5 / −7,8 / −26,0; HYPE −37,4 | M | −18,56; +1,60 / −10,49 / −7,84 / −26,05; −37,43 | ✓ |
| „Sprung erscheint am Tag nach dem Ereignis“ | M | nur bei Ereignissen nach 08:00 UTC (22.02.2025, 08.01., 20.08.). 23.01. (04:24) und 24.05. (04:05) springen am selben Tag | ✗ präzisieren |
| 14 von 18 Ereignissen bleiben, 13 im Panel; 11 von 14 senken das Kapital | E | 14 behalten (HYPE 08.01. ohne Panelzelle), die drei Anstiege sind die 08.01.-Ereignisse | ✓ |
| Änderung 12./13.06.2025 fehlt in `events.csv` | P | Die Änderung liegt am 12.06.2025 um 22:20 UTC, also *vor* dem Fensterbeginn um 23:00 UTC. Kein H4-Ereignis nach Präregistrierung. Wenn gezeigt, dann als „vor dem Fenster“ | ✗ Deutung korrigieren |
| 23.01.2026: nur OTM-Verkäufe, −14 bis −27 log-% bei 7 bis 90 d; 20.08.: alle Verkaufszellen −21 bis −31; 08.01.: +1 bis +2 | M | −14,4 bis −27,3 (dazu 2–7d −17,4); −20,6 bis −30,9; +1,0 bis +2,2 | ✓ |
| „Gitter ±17 → ±14 %“ als Titel des 20.08.2026 | M | Paket: Gitter ±17 → ±14 %, Tail-Dämpfung, Vol-Schocks, Kontingenzen, Basis, Collateral. Bis 24.05.2026 galt ±18 % | ✗ Titel „bundle incl. …“ |
| Legacy-PM IM-Faktor 1,25, Static Discount 0,95 | M | `BTC_pm.json`: `imFactor` 1,25, `baseStaticDiscount` 0,95 | ✓ |
| H2: M3 6 405, M5 5 958, M8 4 296, M10 3 341; 372 Tage; ETH 13 595, HYPE 6 405 | P, E | ✓. M3 ist das **einzige** HYPE-Konto. Nach dem Ausschluss n = 19 999 (ETH 13 594). Der Forest von E schreibt „n 20 000“ | ✓ / Label korrigieren |
| H3: 1 943 Maker-Tage, 1 431 mit > 63 Optionen (74 %) | E, P, M | 1 943 / 1 431 = 73,6 %; `over_63_options` ⇔ n_legs ≥ 64 | ✓ |
| H3 „10 subaccounts“ | E (Kopfzeile F4) | 9 Konten mit Maker-Tagen (M9 hat keine); M7 10 Tage; jedes Konto hat genau einen Manager, M2 ist das einzige SM-Konto | ✗ |
| H4: 13 Ereignisse, 475 Paare, 91 446 Fills | E, P | 91 446 **Zeilen** aus 84 919 Fills (2.5) | ✗ Einheit |
| Validierung: Mediane ≤ 9e−9, Maximum 1,9e−7 (MM), 359 exakte Nullen | E | 8,99e−9; 1,88e−7 (BTC PM2, MM); 359 inkl. MM, 181 nur IM | ✓ |
| 26 Bücher aus 20 Maker-Tagen, grösste Abweichung 0,05 USDC bei K bis 19,5 Mio. | P | ✓ (0,0503 USDC; 19 494 690 USDC; BTC 7, ETH 18, HYPE 1) | ✓ |
| „zwei Reverts“ | M, E | ein Fall (HYPE PM2, Einzelkontrakt), zwei Zeilen (IM und MM) | ✗ |
| „sechs Grössenordnungen unter der Schwelle“ / „mindestens fünf Dekaden“ | M / P | Mediane 5 bis 6 Dekaden unter 0,1 %. Einzelwerte (IM) 5,05 Dekaden unter 1 %, aber nur 4,05 unter der 0,1-%-Linie | ✗ präzisieren |
| Feed-Alter der Testpopulation als eigenes Panel A1c | E | Im PM2-Fenster hat kein Fill einen Feed jenseits der Validierungsgrenzen (p99 Vol 119 s, Forward 95 s). Über die ganze Stichprobe: 448 Fills mit Vol > 20 min, 45 mit Forward > 1 h | Satz in der Caption genügt |
| OI im September 2026: BTC 91 %, ETH 72 %, HYPE 88 % PM2 | P | 90,96 / 71,89 / 87,92 % | ✓ |

---

## 4 · Wahl je Slot

### T1 · Die Engine-Sicht der Oberfläche

**Wahl: M als Träger.** Die Panels a/b sind 3D (Höhe IV, Farbe K in % des Forwards, `cividis`, eine Skala). Die
Panels c/d sind 2D-Streifen: die bindende PM2-Regel bzw. SM-Regel als Graufläche mit Schraffur, dazu
Iso-Kapital-Linien 5/8/11/14 %, die auch auf dem Farbbalken markiert sind. Übernommen werden die Titelzahlen von P
(„PM2: ATM 30 d short = 11.8 % of fwd“, „SM: 14.1 %“, beide nachgerechnet) und die gelisteten Verfälle als
Striche auf der Laufzeitachse. Von E kommen die Kopfzeile (Block, UTC, 15 Verfälle, Parameterstand) und die
|Δ|×Laufzeit-Bucketgrenzen von Paper 1, und zwar **nur auf den 2D-Streifen**. So führt T1 direkt zu F1.

**Warum:** Nur M beantwortet, warum die Fläche so aussieht (fast überall Spot ±14 % mit Vol-Schock nach oben,
Tails nur in zwei Ecken). Das stützt später F6: Die Senkung der Tail-Gewichte am 23.01.2026 trifft genau
OTM-Verkäufe, also die Zellen, in denen die Tail-Szenarien binden. Iso-Linien auf der 3D-Fläche (P) sind teilweise
verdeckt, der ATM-30-Tage-Knoten auch. Eine Bodenprojektion (E) scheitert an der Tiefensortierung von mplot3d,
wie M geprüft hat.

**Auflagen:** Den Block vorab festlegen: letzter Pilottag um 08:00 UTC, kein Parameterereignis in ±1 Tag. Im
Bild „grid ±14 % since 20 Aug 2026“ nennen. `figdata_p2.binding_rule` gegen `margin_pm2.margin_details` testen.
z-Achse „implied vol, %“, damit niemand IV als Kapital liest. In die Caption: SM rechnet in % des Spots,
gezeigt wird % des Forwards; das Kapital ist in Chain-Semantik gerechnet (API rechnet pauschal 2 %). Iso-Linien
und bindende Regel je Knoten gehen in `fig_t1.csv`.

### T2 · Was `get_margin` liefert

**Wahl: P a und P b, dazu M c.** a: das eine Buch vom 24.09. (Fall B, Block 45 110 142), lineare Balken, R
vollflächig in Managerfarbe, −V schraffiert, Summe C − net am Ende. b: Hanteln mit Pfeil von C − net nach R,
log 1 bis 16, dazu die H3-Schwelle 2 mit dem Zusatz „threshold set from these probe books“. c: das
Szenario-Profil von M, neu gerechnet auf dem Referenz-Straddle (2.3) und mit der Achse „categorical, not to
scale“.

**Warum:** E a ist ein Dotplot auf log-USDC. Dort ist der Markerabstand log((R − V)/R) und nicht V, und die
Beschriftung „gap = value V“ sagt deshalb etwas Falsches. P a zeigt V als Fläche und trägt damit die Aussage
„V steckt in beiden Zählern“. M c ist die einzige Stelle, an der man die Engine ein Buch bewerten sieht („das
schlechteste Szenario des Buchs, nicht die Summe der Beine“). Das ist die Brücke von F1 (Einzelkontrakt) zu
F3/F4 (Buch).

**Auflagen:** Beschriftungen in b oberhalb und unterhalb setzen, damit 2,14 und 2,33 nicht kollidieren (M). Der
Pfeil beim Buch 17.09. B zeigt nach links, weil V > 0; das sagt die Caption. Die H0-Variante bleibt draussen, und
ein Test prüft genau die vier Zeilen aus `faktoren.csv`.

### F1 · Was ein Kontrakt kostet

**Wahl: E als Träger, mit Änderungen.** Karten für BTC, drei Manager × zwei Seiten, eine Zahl mit zwei
signifikanten Stellen je Zelle. M rundet auf eine Nachkommastelle und macht so aus 0,07 und 0,11 dieselbe 0,1.
Die Schattierung ist **eine** logarithmische Grauskala für alle sechs Karten (M). Das zeigt, dass die Seite und
nicht der Manager das Kapital bestimmt, und die Zahlen tragen die genauen Werte. Rechts steht der Streifen aller
173 Zellen, geordnet wie bei P (Zeilen Basiswert × Seite, SM-Quadrat und Legacy-Raute, Medianstrich, Linie
bei 1), **mit Regime-Aufteilung** (2.2).

**Warum:** Die Spezifikation fragt nach dem Kapital je Kontrakt *nach Manager*. P zeigt nur PM2 und die
Quotienten, E zeigt beides und prüft die Aussage über alle Basiswerte. Die Anatomie-Spalte von M entfällt
(2.2 iii).

**Auflagen:** Daten aus `fig_edge_maps.csv` (2.6). Die obere Zeile heisst im Achsentitel „maker buys: capital
= premium under SM“ (E, P). Die Achse sagt „|delta| of the traded option“ (P). Kreuze zählen gegen die
Zelltabelle (210 Zellen, 173 besetzt). Die 20 Fills mit K_PM2 ≤ 0 bleiben in den Summen (Nachtrag 4). Die Caption
von `main.tex` („USDC“, „each panel on its own scale“) wird ersetzt.

### F2 · Die Karte in zwei Nennern (H1)

**Wahl: P als Träger, mit der Urteilsleiste von E und den Vorzeichenlinien aus 2.1.** Links sechs kleine
Karten (Verkauf/Kauf × BTC/ETH/HYPE), eine Zahl je Zelle = Edge in bp des PM2-Kapitals, ab 1 000 als „1.3k“,
negative Zellen schraffiert. Rechts das Rang-Rang-Bild mit 90-%-Rangbändern (`rank_B_lo/hi`), Basiswert als
Form, Seite als Füllung. Darunter die Urteilsleiste: Schätzer, 90-%-Intervall, Schwelle 0,5, schraffierte
Ablehnungsseite, „173 cells, 463 day clusters“ und fett die Regel mit dem Urteil. Darunter der explorative
Forest (grau): MM, Netto-Edge in der Form von Paper 1, bis Verfall, Haltedauer, je Basiswert, SM- und
Legacy-Karten (`sensitivity.json`), neu dazu innerhalb Vorzeichen und innerhalb Seite.

**Warum:** Die Kapitalkarte ist Beitrag 1 der Spezifikation. E zeigt sie gar nicht, und ein Referee würde sie
verlangen. E fehlt ausserdem das Rangband, M fehlen Rangband und Verteilung. P hat beides, aber keine
Urteilsleiste, und die fünf gerahmten „besten“ Zellen sind nicht vorab definiert.

**Verworfen:** M a (log-log, 43 % der Zellen ≤ 0), die Verbindungslinien der Spezifikation (173 Haarlinien, in
Paper 1 verboten) und die Top-5-Rahmen von P. Die mittleren Rangverschiebungen von E (c/d) gehen in CSV und Text
(`h1-reading`); die Karten zeigen das zellweise.

**Auflagen:** Farbe als Symlog mit hinterlegtem linearem Kern auf dem Farbbalken (Paper-1-Regel), sonst tragen
die Kaufzellen mit Werten in k-Grösse die ganze Skala. Die Caption sagt, dass Edge je Kapital bei Käufen eine
Rendite auf die Prämie ist und je Fill gilt (Fluss durch Bestand, keine Jahresrendite). Die Karte A (je Nominal)
bleibt Paper 1, Verweis in der Caption. Grösse 7,0 × 4,0 in.

### F3 · Der nächste Kontrakt im Buch (H2)

**Wahl: P a und E b.** a: ECDF aus dem kumulierten Histogramm von `fig_h2_dist.csv` (`label = all`,
`variant = ratio`), Bänder „≤ 0: no extra capital or frees capital“ (nicht nur „frees“), 0 bis ½, ½ bis 1, > 1 mit
den Anteilen, dazu die Überlaufanteile an beiden Rändern. Der Median steht mit 90-%-Intervall bei y = 0,5, die
Schwelle ½ ist gestrichelt. b: Forest mit Urteilsleiste. Die registrierte Zeile ist fett. Sensitivitäten sind
`ratio_unit`, `ratio_mm` und `ratio_tape`. Explorativ und grau folgen M3 (= HYPE), M5, M8 und M10 (`sens_h2.csv`).

**Warum:** Die ECDF liest die registrierte Grösse (Median) direkt ab und kommt ohne abgeschnittenes Fenster aus.
Das Histogramm von E verlangt [−2; 3], das die Tabelle nicht hat. Die p25–p75-Balken je Konto von P zeigen
Streuung, nicht Unsicherheit. Im Forest haben dieselben Konten Intervalle. Das Mechanik-Panel von M
(`hedges_worst`) wäre eine neue, nicht registrierte Rechnung und wird höchstens ein Satz.

**Auflagen:** Kopfzeile „4 PM2 accounts, ETH and HYPE only (no BTC), 19 999 fills, 372 days, 1 excluded, random
sample of 20 000 (seed 20260924)“. Die ETH/HYPE-Zeile von E entfällt, weil HYPE genau M3 ist. Die Caption sagt,
dass ein Maker mit leerem Buch den Preis aus F1 zahlt (P). Breite genau 3,4 in (2.4).

### F4 · Was Netting wert ist (H3)

**Wahl: E als Träger.** a: Histogramm auf log-x, gestapelt nach ≤ 63 Optionen und > 63 Optionen („SM
counterfactual“, schraffiert), Schwelle 2, Median. b: Forest mit registrierter Zeile, „≤ 63 only“, „> 63 only“,
MM und Legacy/PM2 (nur BTC- und ETH-Beine, n in der Zeile). Explorativ und grau: die neun Konten aus `sens_h3.csv`
mit ihrem Manager (M2 ist das einzige SM-Konto).

**Warum:** Nur hier stehen das Urteil, sein Intervall und der kontrafaktische Anteil in einem Bild. Die
Kontobalken von P zeigen wieder Streuung ohne das Testintervall. Die Breitenmechanik (Faktor gegen Beinzahl, M und
P) ist richtig und anschaulich, bekommt aber in 3,4 in keinen Platz. Sie geht als Satz in den Text und als Spalte
in die CSV. Falls die Gestaltung einen Platz findet, dann als Binned-Median mit Band und nicht als Wolke aus
1 943 Punkten.

**Auflagen:** Kopfzeile „9 accounts, 1 943 maker-days, 462 day clusters, 0 excluded“ (E schreibt 10). Die
Caption sagt, dass Cluster UTC-Tage sind, nicht Konten. Explorative Zeilen nach Parameterregime (Lücke 3).

### F5 · Die Engine über die Zeit

**Wahl: P als Träger, ergänzt um E und um ein neues Band.**
- a: OI-Streifen von P. Fehler beheben: Im HYPE-Streifen fehlt der SM-Anteil (7 bis 49 % je Monat), weil `pm` bei HYPE
  NaN ist. Mit `fillna(0)` stapeln.
- b: Ereignisleiste je Basiswert mit den Zeichen von E: ● im Panel, ◇ behalten ohne Panelzelle (HYPE
  08.01.2026), ○ weggefallen. Graue Striche zeigen jede Zeile der Zeitlinie (Placebo-Abstand). Die Zahl neben dem
  Zeichen ist der reine Parametereffekt auf den Referenz-Straddle in % (P, nachgerechnet). **Neu:** Ein dünnes
  Band je Basiswert markiert die zulässigen Placebo-Tage (2.5).
- c: BTC-Referenz-Straddle je Manager mit Direktbeschriftung am rechten Rand. Die ±14-Tage-Fenster sind grau
  hinterlegt, Überlappungen dunkler (E). Die y-Achse beginnt bei 0, damit das Verhältnis 3 : 2 : 1 der Engines
  ehrlich ist (P beginnt bei 5, M bei 9). Die Legacy-Linie wird dünn, wo der OI-Anteil unter 5 % liegt (E).

**Warum:** P trägt die Zahlen, die der Text braucht (−35 / −23 / −47 %). E macht die H4-Auswahl prüfbar. M d
(Stiele in log-%) zeigt dieselben Zahlen ein zweites Mal und entfällt zugunsten der Beschriftung. Die SM-Zeilen
von M (nur Perps) entfallen ebenso. Die Referenzbuch-Panels für ETH und HYPE von E ersetzt die Beschriftung der
Leiste.

**Auflagen:** Das Ereignis mit seinem Datum beschriften, nicht mit dem Tag des Sprungs (2.3). Die Sägezähne
erklärt die Caption (Laufzeit 21 bis 36 Tage). Die Caption nennt die überlappenden Fenster (6 527 Fills in zwei
Fenstern). Die Änderung vom 12.06.2025 um 22:20 UTC erscheint höchstens als „before PM2 window“.

### F6 · Der Preis des Kapitals (H4)

**Wahl: eine neue Kombination aus E, P und M.**
- a: **Dosis-Streifen aller 13 Panel-Ereignisse.** Je Ereignis eine Zeile, je Panelpaar ein Strich (▼ Verkauf,
  ▲ Kauf), dazu der Median. Quelle: `h4_doses.csv`, gefiltert auf die Paare in `h4_panel.parquet`. Der Streifen
  ersetzt die drei ausgewählten BTC-Dosiskarten von M. Diese sind echt und schön, zeigen aber 3 von 13 Ereignissen,
  und ihr Kreuz folgt nur der Vor-Regel (≥ 20 Fills vor dem Ereignis) statt der Panelregel (je 20 vor und nach).
  Eine Karte davon wird Reserve für X.
- b: **FWL-Binscatter** wie bei E, mit Punktfläche nach Fills, der Geraden β und einem Rug bzw. Histogramm der
  Dosis unter der x-Achse (2.5). Die Achse erklärt die Vorzeichen („< 0: capital got cheaper“). Die Ticks dürfen
  wie bei P in % Kapitaländerung beschriftet sein, weil es dieselbe Achse ist.
- c: Placebo-Histogramm mit P95 und β, darüber die Prüfliste von E (einseitiges Wild-p ≤ 0,05 met/not met, β >
  P95 met/not met, Urteil). Darunter die zulässigen Placebo-Tage je Basiswert.
- d (klein, grau): β je Basiswert, ohne Ausreisserzellen, Placebo über alle Zeitlinien (`sensitivity_h4.json`),
  jeweils mit Clusterzahl.

**Warum:** Nur die residualisierten Bins haben die Steigung β. P a zeichnet β über rohe Paare, M b über rohe
Terzile. Beide Geraden haben nicht die Steigung der Regression, das ist eine unehrliche Kodierung. E b zeigt β je
Ereignis, das die Inferenz nicht schätzt.

**Auflagen:** Die Kopfzeile nennt 13 Ereignisse, 475 Paare, 91 446 Zeilen aus 84 919 Fills, 141 Tagescluster
und 322 Tag-Basiswert-Effekte. Das 90-%-Intervall von β heisst im Bild „descriptive“, weil `h4.json` es aus
unrestringierten Residuen bildet. Das Wild-p der Regel kommt aus restringierten Residuen. **Ohne
`fig_h4_fwl_bins.csv`** zeigt b die Terzil-Kontraste innerhalb eines Ereignisses (Δy des Terzils minus Δy-Mittel
des Ereignisses gegen Dosis minus Mittel) und keine β-Gerade. Die Umrechnung in der Caption lautet „10 % billiger
= Dosis −0,105, vorhergesagte Änderung −0,105·β bp“ und nicht 0,1·β. Die Empfehlung gilt für beide Vorzeichen
von β.

### A1 · Trifft der Nachbau die Chain?

**Wahl: P als Träger, dazu die Medianstriche und das n je Zeile von M und die p95-Raute von E.** a:
Einzelkontrakte IM, Zeilen Basiswert × Manager, log |rel|, exakte Nullen in einem beschrifteten Randstreifen,
Linien „median limit 0.1 %“ und „p95 limit 1 %“ direkt beschriftet. b: Bücher, |rel| gegen Beinzahl (log-log),
IM gefüllt, MM hohl, im Bild die grösste absolute Abweichung (0,05 USDC bei K bis 19,5 Mio. USDC).

**Warum:** P b zeigt den Referee-Punkt, dass der Fehler nicht mit der Buchgrösse wächst (2 bis 245 Beine). M b
teilt die Bücher nach Basiswert auf, obwohl HYPE nur ein Buch hat. E a mit Doppelbalken IM/MM ist überladen, und
die Fusszeile von E überlappt die Achsenbeschriftung.

**Auflagen:** MM nur in der CSV. Die Caption nennt einen Revert-Fall (HYPE PM2, zwei Zeilen) und das Feed-Alter
als Satz: Im PM2-Fenster hat kein Fill einen Feed jenseits der Validierungsgrenzen, über die ganze Stichprobe
sind es 448 bzw. 45. Die Nachtrag-1-Zahl „1 165 von 1 165 Konto-Tagen exakt“ kann als Nebenzeile in b stehen.

---

## 5 · README und X

**GIF.** 3D-Fläche von PM2 für BTC, Short, wöchentlich vom 13.06.2025 bis 17.09.2026, dazu an jedem behaltenen
BTC-Ereignis Vortag, Tag und Folgetag als Haltebilder mit Banner (M, P). Unten ein Zeitstreifen mit dem
Referenz-Straddle je Manager und den reinen Parameterstufen (K gegen K_prev), damit Markt- und
Parameterbewegung getrennt bleiben (P). Von E kommen die Ehrlichkeitsregeln: feste Skala über alle Bilder
(`fit_limits`), Datum und Block je Bild, übersprungene Tage sichtbar, Verfälle mit altem Feed grau statt
interpoliert, `results/p2/gif_frames.csv` mit Datum, Block, Verfällen und K min/Median/max, ein statischer
Endframe. Format 1200 × 675, Schrift mindestens 14 px bei dieser Grösse. Das bestehende GIF hat etwa 10 px.
Hervorgehoben wird eine feste Iso-Linie (10 %), nicht „die, die am meisten wandert“, denn das wäre eine
nachträgliche Auswahl.

**Karten (1600 × 900).**
1. **M „One short BTC straddle. Three margin engines.“** Die Zahlen 30 / 20 / 10 % sind nachgerechnet. Den
   Untertitel korrigieren: „nearest listed expiry to 30 days (22 d on 17 Sep 2026)“ statt „about 30 days“.
   Die Zeile „capital for a hypothetical book, not a balance“ ergänzen. Die Senkrechten heissen „parameter
   changes kept for H4“.
2. **Standbild der Fläche** (P `social_t1_keyframe.png`) mit dem Satz von M: „Almost everywhere one scenario sets
   the capital: spot ±14 % with vol up.“ Die abgeschnittene Farbbalken-Beschriftung beheben.
3. **Urteilskarte H1 bis H4** in der Grammatik von E: je Test Schätzer, Intervall, Schwelle und „pre-registered ·
   rejected/not rejected“. Bis zum Enddatenlauf mit Platzhalter.

Reserve: P-Karte 1 (−35 %). Die Zahl stimmt, aber es ist dieselbe Reihe wie Karte 1, und Titel und Untertitel
sind rechts abgeschnitten. P-Karte 2 nur, wenn beide Beine aus demselben Referenz-Straddle kommen und der Titel
nicht „almost free“ sagt, denn Kapital ist nicht Risiko. Die Karte zeigt sogar weniger Kapital *mit* dem Put
(10,0 gegen 11,9 %). M-Karte 3 (Fingerabdruck 20.08.2026) nur mit Titel „bundle“.

**Verworfen:** P-Karte 3. Sie vergleicht einen über Regime gepoolten Zellmedian (0,90; ab 20.08.2026 BTC 1,40,
ETH 1,14) mit dem Median über Maker-Tage, also zwei verschiedene Populationen. Und sie zeichnet Quotienten als
lineare Balken ab 0.

---

## 6 · Lücken, die ein Referee verlangen würde

1. **Strukturelle Untergrenze von H1** (2.1). Vorzeichenlinien in F2 und explorative ρ innerhalb Vorzeichen und
   innerhalb Seite. Der Text nennt die Untergrenze als Lesart, ohne den Test zu ändern.
2. **Regime-Abhängigkeit des Einzelkontrakts** (2.2). Regime-Aufteilung im F1-Streifen und in
   `fig_f1_regimes.csv`, den Satz „book, not contract“ zeitlich einschränken.
3. **H2 und H3 über die Zeit.** Kein Entwurf zeigt, ob die Mediane vom Parameterregime getragen werden. PM2 wurde
   um 35 % billiger, K_SM/K_PM2 steigt also mechanisch. Explorative Zeilen je Regime in `sens_h2.csv` und
   `sens_h3.csv`, im Forest grau. Alternativ ein Monatsmedian in der CSV (`fig_h3_series.csv` hat `day`).
4. **Placebo-Stütze von H4** (2.5). ETH PM2 hat 10 zulässige Tage. Als Band in F5 zeigen, Tageszahlen in F6c
   nennen, `h4_placebo_days.csv` anfordern.
5. **Überlappende H4-Fenster**: 6 527 von 84 919 Fills doppelt. Das gehört in F5, F6 und den Text.
6. **Dosis-Stütze von H4**: die Hälfte der Paare unter 1 %, 11 % positiv. Dosis-Streifen F6a und Rug in F6b.
7. **Fehlende Inferenztabellen:** `fig_h4_fwl_bins.csv` (für F6b nötig), die explorativen H1-Zeilen, die
   Regime-Zeilen für H2 und H3, `h4_placebo_days.csv`; optional `h1_rho_draws.csv`. Die Abbildungsschicht rechnet
   nichts davon selbst.
8. **Stichproben-Fluss als Tabelle, nicht als Slot:** 336 087 Fills im PM2-Fenster → 331 813 in 173 besetzten
   Zellen (H1). H2: 19 999 Fills, 4 Konten, nur ETH und HYPE, ab 04.09.2025. H3: 1 943 Maker-Tage, 9 Konten
   (25 Tage ohne Optionen oder Snapshot). H4: 13 Ereignisse, 475 Paare, 91 446 Zeilen, 84 919 Fills.
9. **Druckgrösse und Schrift** (2.4). Das Prüfskript muss die Breite und die kleinste Schrift nach Skalierung
   testen, und für Paper 2 sollte `savefig.bbox = "tight"` nicht gelten.
10. **Eine Zahl je Objekt**: T2c, F5c und Karte 1 zeigen denselben Straddle aus derselben Zeile von
    `reference_book.csv` (2.3).
11. **Ereignistitel**: 20.08.2026 ist ein Paket. Das Gitter war bis 24.05.2026 ±18 %, danach ±17 %, ab 20.08.
    ±14 %. Der Satz „PM2 nimmt Spot ±14 %“ gilt nur für das letzte Regime.
12. **Zwei Zellgrössen für F1**: `fig_capital_by_manager.csv` (Median je Fill, als Anteil) nicht neben
    `fig_edge_maps.csv` (Verhältnis der Summen) ins Bild setzen.

## 7 · Für das Prüfskript `scripts/p2_figure_check.py`

- Jede gedruckte Zahl gegen ihre Quelle: T2 gegen `faktoren.csv` (genau vier Zeilen), F1 gegen `fig_edge_maps.csv`,
  F5 gegen `reference_book.csv` und `events.csv`, A1 gegen `validation.csv`, alle Urteilsleisten gegen
  `h*.json`. Die Urteilszeile wird aus `rule` und den Grenzen neu gebildet und muss `rejected` treffen.
- Zählungen: Kreuze in F1 = Zellen unter 200 Fills (BTC: 10 je Manager, 70 − 60 über beide Seiten; alle
  Basiswerte: 37 je Manager), 173 Punkte in F2 und im F1-Streifen, Zeichen
  in F5 = 14 behalten + 4 weggefallen, 13 Zeilen und 475 Striche in F6a.
- Identität: κ in F1 = 100·`sum_K`/`sum_index` von `h1_cells.csv`. T2c, F5c und Karte 1 zeigen denselben
  Straddle-Wert.
- Gestalt: PDF-Breite 3,4 bzw. 7,0 in ± 0,02, keine Schrift unter 7 pt, genau eine 3D-Achse im PDF (T1).
