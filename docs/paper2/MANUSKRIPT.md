# Manuskript Paper 2: Gliederung, Wortbudget und Platzhalter

Stand: 24.09.2026, 23:00 UTC+2. Gehört zu `paper2/main.tex` (Entwurf vor der ersten Kapitalzahl).

**Nachtrag 25.09.2026 (Pilotschnitt 17.09.2026):** Alle Platzhalter sind gefüllt, Abstract, Ergebnisse,
Diskussion und Schluss geschrieben, die Captions stammen aus `derive_surface/figs_p2/<slot>.py` (eine begründete
Abweichung in F2, siehe `CAPTION_EXCEPTIONS` in `scripts/p2_build.py`). Die Tabellen unten beschreiben den
Stand vor den Ergebnissen. Prüfkette: `scripts/p2_wordcount.py` (Budget je Abschnitt), `scripts/p2_number_check.py`
(jede Zahl, jedes Datum und jede Uhrzeit ist in ihrer Einheit, also Abstract, Abschnitt, Unterabschnitt oder
Bildunterschrift, per `% src quelle gedruckt` an genau eine Quelle gebunden, ein Eintrag je Vorkommen in der
Reihenfolge des Texts; Regeln im Kopf des Skripts; Bericht `docs/paper2/ZAHLENPRUEFUNG.md`) und
`scripts/p2_build.py` (tectonic, Log, Overfull, Pflichtteile, Gedankenstriche, Zitate, Abbildungen, Captions,
Budget, Zahlen). Nach dem Enddatenlauf alle drei neu laufen lassen: eine Zahl ohne Erklärung, eine Erklärung ohne
ihre Zahl und ein erklärter Wert, der nicht mehr so gedruckt wird, brechen den Bau ab.

**Nachtrag 25.09.2026 (Audit):** Das Manuskript ist nach `docs/paper2/AUDIT.md` überarbeitet; was sich je Befund
geändert hat und was offen bleibt, steht in Abschnitt 8. Die Tabellen in den Abschnitten 1 bis 4 sind historisch
(Stand vor den Ergebnissen), die aktuellen Wortzahlen stehen in 8.1.

**Titel:** What does the edge cost? Capital-adjusted market making under a public portfolio-margin engine.
Dass Kapital über hypothetische Portfolios der Engine gemessen wird und nicht über Kontosalden, steht im
dritten Satz des Abstracts und im zweiten Absatz der Einleitung.

**Bau:** `cd paper2 && tectonic main.tex` läuft fehlerfrei durch: 7 Seiten, 0 Overfull-Boxen, keine
undefinierten Verweise. Es bleibt nur eine Underfull-Warnung aus `main.bbl` (lange DOI im Literaturverzeichnis).
Die Abbildungen unter `paper2/figures/{t1,t2,f1,…,f6,a1}.pdf` sind **temporäre Platzhalter** (gestrichelter
Rahmen mit Slot-Namen). Die Abbildungspipeline überschreibt sie später. `paper2/thumbnails/cas-email.jpeg` ist eine Kopie aus
`paper/thumbnails/`. `cas-dc` braucht die Datei für das E-Mail-Symbol, ohne sie bricht der Bau ab.

**Regeln für den Text:** Englisch, knapp, keine Gedankenstriche (em/en dash) im Fliesstext, nur Schlüssel
aus `paper2/refs.bib`. Jede Zahl stammt aus `results/p2/` oder aus der Präregistrierung (Commit `1d13227`),
sonst steht dort ein `\PH{…}`. Das Makro ist `\newcommand{\PH}[1]{\textbf{[#1]}}`. Im PDF erscheinen die
Platzhalter also fett in eckigen Klammern. Vor der Einreichung darf `grep -c '\\PH{' paper2/main.tex` nur noch
1 liefern (die Definition).

---

## 1 · Gliederung und Wortbudget

Gezählt mit der Logik von `scripts/p1_wordcount.py`: Prosa ohne Abbildungen, Captions, Kommentare und
Literatur, Abstract eingeschlossen. Formeln zählen mit. Die Toleranz ist +10 %.

| Abschnitt | Label | Inhalt | Budget | jetzt | Rest |
|---|---|---|---|---|---|
| Abstract | – | Frage, Messung über hypothetische Portfolios, vier Kernzahlen, Präregistrierung | 170 | 172 | 0 |
| 1 Introduction | `sec:intro` | Kapital statt Kontrakte; warum Derive (öffentliche deterministische Engine, Parameter on-chain, Endpoint ohne Konto); Frage und Bezug zu Paper 1; vier Beiträge der Spec; H1 bis H4 je ein Satz; Ergebnisabsatz | 600 | 564 | ~40 plus `intro-results` |
| 2 The engine and what it returns | `sec:engine` | SM, Legacy-PM, PM2; net = C + V − R; pre/post; K_p; zwei Engines (off-chain 2 %, on-chain Rate-Feed); warum C − net irreführt, Auflösung 11,86 gegen 1,19; Abb. T1, T2 | 600 | 651 | am Limit (660) |
| 3 Data and measurement | `sec:data` | Fills aus Paper 1, Manager-Fenster; Feeds und Parameter-Zeitlinien; Kapital je Fill, Zellen, Formeln; Maker-Bücher, Grenzkosten, Netting-Wert; Dosis und Regression für H4; Inferenz; Validierung gegen `eth_call` | 600 | 643 | am Limit (660) |
| 4 Results | `sec:results` | 4.1 H1 (F1, F2), 4.2 H2 (F3), 4.3 H3 (F4), 4.4 H4 (F5, F6) | 1 400 | 453 | ~950 für die `*-reading`-Absätze und Befunde |
| 5 Discussion | `sec:discussion` | drei Absätze Bedeutung (`disc-map`, `disc-book`, `disc-price`), ein Absatz Grenzen (fertig); Abb. A1 | 400 | 175 | ~225 |
| 6 Conclusion | `sec:conclusion` | zwei Sätze fertig, `concl-results`, `concl-close` | 200 | 55 | ~145 |
| Back matter | – | Data, code and pre-registration (Commit `1d13227`); Competing interest; Use of generative tools | – | 255 | – |
| **Summe** | | | **3 970** | **2 968** | |

Die Summe von 2 968 zählt wie Paper 1 alle Abschnitte samt Back Matter. Ohne Back Matter sind es 2 713.

Einsparreserve, falls Abschnitt 2 oder 3 beim Füllen wächst: In Abschnitt 2 kann der Satz zu
`figlewski1984`/`artzner1999` in die Diskussion wandern. In Abschnitt 3 lässt sich die Regressionsformel in
die Caption von F6 verschieben.

---

## 2 · Abbildungen

| Slot | Label | Umgebung | Platzhalter-PDF | Caption-Entwurf | Daten (geplant) |
|---|---|---|---|---|---|
| T1 | `fig:t1` | `figure*` | 7,0 × 3,0 in | Engine-Sicht der BTC-Oberfläche, Farbe = PM2- bzw. SM-Kapital je Short-Kontrakt | `results/p2/surface_t1.json` (Block, Gitter, K je Punkt) aus `p2surface.py` |
| T2 | `fig:t2` | `figure*` | 7,0 × 2,6 in | net = C + V − R; Faktoren auf C − net gegen R für die Probebücher vom 17.09. und 24.09. | `results/p2/semantik/faktoren.csv` (liegt vor) |
| F1 | `fig:f1` | `figure*` | 7,0 × 3,6 in | Kapital je Kontrakt nach Manager über \|Δ\| × Laufzeit, Kauf und Verkauf | `results/p2/capital_cells.csv` |
| F2 | `fig:f2` | `figure*` | 7,0 × 3,2 in | Edge je Nominal gegen Edge je PM2-Kapital, Rangverbindungen, ρ mit Intervall (H1) | `results/p2/h1_cells.csv`, `summary.json` → `H1` |
| F3 | `fig:f3` | `figure` | 3,4 × 2,4 in | Verteilung ΔK / K_single, Schwelle ½, Median mit Intervall (H2) | `results/p2/h2_marginal.csv`, `summary.json` → `H2` |
| F4 | `fig:f4` | `figure` | 3,4 × 2,4 in | K_SM / K_PM2 über Maker-Tage, Legacy daneben, Schwelle 2 (H3) | `results/p2/h3_netting.csv`, `summary.json` → `H3` |
| F5 | `fig:f5` | `figure*` | 7,0 × 3,4 in | OI-Anteile je Manager, Parameterereignisse, Kapital eines festen Referenzbuchs | `results/p2/params/*.json`, `results/p2/oi_shares.csv`, `results/p2/reference_book.csv` |
| F6 | `fig:f6` | `figure*` | 7,0 × 2,6 in | Dosis-Wirkung mit β, Placebo-Verteilung (H4) | `results/p2/h4_panel.csv`, `results/p2/h4_placebo.csv` |
| A1 | `fig:a1` | `figure*` | 7,0 × 2,6 in | Abweichung Nachbau gegen `eth_call`, Einzelkontrakte und Bücher, Schwellen 0,1 % und 1 % | `results/p2/validation.csv` |

Die Dateinamen unter `results/p2/` sind Vorschläge für `inference_p2.py`, `p2validate.py` und
`figdata_p2.py`. Werden sie anders benannt, ist diese Tabelle nachzuziehen. Die Captions sind Entwürfe. Nach
der Jury wie in Paper 1 an die gewählte Gestaltung anpassen, ohne neue Zahlen einzuführen.

---

## 3 · Zahlen, die schon im Text stehen

### 3a · Aus `results/p2/`

| Stelle | Zahl im Text | Quelle |
|---|---|---|
| Abschn. 2, Absatz „Two engines“ | fourteen listed BTC expiries | `results/p2/semantik/box_diskont.json`, Schlüssel `box_2026-09-24T11:27Z`, 14 Zeilen |
| dito | two per cent to within 2.7 × 10⁻⁷ | dito, Feld `r_api`, max \|r_api − 0,02\| = 2,70e−7 |
| dito | 24 September 2026 | dito, `api_ts` |
| dito | 3.64 to 3.82 per cent | dito, Feld `r_chain` min/max (gleich in `v_konvention.json`, Feld `r_feed`) |
| Abschn. 2, Absatz „Reading C − net“, T2-Caption | 11.86 (C − net), 10.76 (R) | `results/p2/semantik/faktoren.csv`, Zeile `historisch 17.09. 10:45:13Z Blk 44810149`, `b17_exakt`, Fall B, Spalten `F_Cnet`, `F_R_engine` |
| dito | 1.19 (C − net), 2.14 (R) | dito, Zeile `historisch 24.09. 09:24:59Z Blk 45110142 (H1_0928-81k_0929-76k-81k)`, `b24`, Fall B |
| dito | block 44 810 149, 17 September 2026; block 45 110 142, „a week later“ | dito, Spalte `messung` |
| dito | PM2 value −496 859 USDC | dito, Zeile 24.09. H1, Fall B, Spalte `V_PM2` = −496 858,84 |
| T2-Caption | 2.33 / 3.19 (17.09., Fall A); 1.46 / 3.61 (24.09., Fall A) | dito, Fall A der beiden historischen Zeilen |
| Abschn. 4.3 | ratios on R ran from 2.14 to 10.76 | dito, Minimum und Maximum von `F_R_engine` über alle Zeilen mit `historisch` |

Hinweis zur Zeile vom 24.09.: `faktoren.csv` hat zwei historische Varianten (`H1_…` und `H0_heutige_Liste`).
Der Text nutzt `H1_…`, weil diese Variante die Originalmessung nachbildet (1,19 entspricht der früheren
Lesung 1,2, siehe `get_margin_semantik.md` Abschnitt 4). Die Variante `H0` ergibt 1,22 und 2,52 und liegt im
Bereich 2,14 bis 10,76.

### 3b · Konstanten aus Präregistrierung und Spezifikation (keine Ergebnisse)

Diese Werte sind Versuchsplan und keine Messung. Sie stehen in `docs/paper2/PRAEREGISTRIERUNG.md`, Commit
`1d13227`:

- Stichprobenbeginn 11 January 2024; Manager-Fenster: SM ganzer Zeitraum (HYPE ab 11 November 2025),
  Legacy-PM BTC/ETH ganzer Zeitraum, PM2 BTC/ETH ab 12 June 2025 23:00 UTC, HYPE ab 11 November 2025.
- Netto-Edge nach „thirty minutes“; Zellen „from 200 fills“; „ten“ dominante Subaccounts; q = ±1; 10⁴ in den
  Formeln (Basispunkte).
- H2 „less than half“, H3 „more than half“ bzw. Schwelle „two“, H1 Schwelle „0.5“, „90 per cent interval“.
- H4: „fourteen days“, Dosisfilter „one per cent“, „20 fills on each side“, „five per cent“, „95th placebo
  percentile“, „100 placebo dates“, „28 days“.
- Inferenz: „9 999 draws“. Validierung: „48 random blocks“, „20 maker-days“, Schwellen „0.1 per cent“ und
  „1 per cent“, „95th percentile“.
- Back Matter: Commit `1d13227`, 24 September 2026, 22:33 UTC+2 (aus `git log`).

Zählwörter ohne Messung: „three managers“, „four hypotheses/contributions“, „two engines“.

---

## 4 · Alle Platzhalter und woraus sie gefüllt werden

56 Vorkommen, 51 verschiedene Schlüssel (`n-fills`, `h1-rho`, `h2-median`, `h3-median` und `n-rejected`
kommen je zweimal vor). Spalte „Quelle“: geplante Datei und Feld. Satzplatzhalter (`*-reading`, `disc-*`,
`concl-*`, `intro-results`) werden erst nach den Tests geschrieben. Jede Zahl darin muss ebenfalls aus
`results/p2/` kommen.

### Abstract

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `n-fills` | Zahl der Fills mit Kapital je Fill (auch Abschn. 3) | `results/p2/summary.json` → `sample.fills` (aus `data/p2/derived/capital.parquet`, Modul `capital.py`) |
| `h1-rho` | Spearman-ρ H1 (auch 4.1) | `summary.json` → `H1.rho` |
| `h2-median` | Median ΔK / K_single H2 (auch 4.2) | `summary.json` → `H2.median` |
| `h3-median` | Median K_SM / K_PM2 H3 (auch 4.3) | `summary.json` → `H3.median` |
| `h4-direction` | Halbsatz: „fell by … basis points …“ oder „did not respond measurably“ | `summary.json` → `H4.beta`, `H4.rejected` |
| `n-rejected` | Zahl abgelehnter Hypothesen, als Wort (auch Schluss) | `summary.json` → Summe `H*.rejected` |

### 1 Introduction

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `intro-results` | Absatz, je Hypothese ein Satz mit Urteil und Kernzahl, Reihenfolge H1 bis H4 | `summary.json` → `H1` bis `H4` |

### 2 The engine and what it returns

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `t1-block` | Block (mit Datum) der Oberfläche in T1 | `results/p2/surface_t1.json` → `block`, `ts` (Modul `p2surface.py`) |

### 3 Data and measurement

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `sample-end` | Ende der Stichprobe (Pilot 17 September 2026 12:00 UTC, final 30 September 2026 08:00 UTC) | `summary.json` → `sample.end` |
| `n-fills` | siehe Abstract | siehe Abstract |
| `val-median` | Median \|ΔK/K\| Nachbau gegen `eth_call`, über alle Basiswerte und Manager | `results/p2/validation.csv`, `summary.json` → `validation.median` (Modul `p2validate.py`) |
| `val-p95` | 95. Perzentil derselben Grösse | dito → `validation.p95` |

Achtung: Der Satz davor steht im Präteritum („were checked“). Verfehlt der Nachbau die Schwelle, muss der Satz
auf den datierten Nachtrag der Präregistrierung verweisen.

### 4.1 H1

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `f1-pattern` | ein bis zwei Sätze: wo sich SM, Legacy-PM und PM2 am stärksten unterscheiden, Kauf gegen Verkauf | `results/p2/capital_cells.csv` |
| `f1-ratio-min` | kleinstes K_SM/K_PM2 eines Short-Kontrakts über besetzte Zellen | dito, Spalte `ratio_sm_pm2`, Seite Verkauf |
| `f1-ratio-max` | grösstes dito | dito |
| `h1-cells` | Zahl besetzter Zellen im PM2-Fenster | `summary.json` → `H1.cells` |
| `h1-rho` | siehe Abstract | `H1.rho` |
| `h1-lo` | untere Grenze 90-%-Intervall | `H1.lo` |
| `h1-hi` | obere Grenze 90-%-Intervall (Ablehnung, wenn ≥ 0,5) | `H1.hi` |
| `h1-verdict` | „rejected“ oder „not rejected“ | `H1.rejected` |
| `h1-reading` | welche Zellen den Rang am stärksten wechseln, entlang Laufzeit, Delta oder Seite | `results/p2/h1_cells.csv` |
| `h1-pooled-sell` | gepoolter Edge je PM2-Kapital, Maker-Verkauf, bp | `H1.pooled_bp.sell` |
| `h1-pooled-buy` | dito, Maker-Kauf | `H1.pooled_bp.buy` |

### 4.2 H2

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `h2-n` | Zahl der getesteten Fills | `summary.json` → `H2.n` |
| `h2-excl` | ausgeschlossene Fills mit K_PM2,single ≤ 0 | `H2.excluded` |
| `h2-sample` | Satz, ob die präregistrierte Zufallsstichprobe (20 000 Fills, Seed 20260924) greift | `H2.sampled`, `H2.n_before_sampling` |
| `h2-median` | siehe Abstract | `H2.median` |
| `h2-lo` | untere Grenze 90-%-Intervall | `H2.lo` |
| `h2-hi` | obere Grenze (Ablehnung, wenn ≥ 0,5) | `H2.hi` |
| `h2-share-nonpos` | Anteil der Fills mit ΔK ≤ 0, in Prozent | `H2.share_nonpos` |
| `h2-verdict` | „rejected“ oder „not rejected“ | `H2.rejected` |
| `h2-reading` | welche Fills am Rand billig (gegen das Buch) und welche teuer (mit dem Buch) sind | `results/p2/h2_marginal.csv` |

### 4.3 H3

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `h3-days` | Zahl der Maker-Tage im Test | `summary.json` → `H3.days` |
| `h3-excl` | ausgeschlossene Maker-Tage mit K_PM2 ≤ 0 | `H3.excluded` |
| `h3-median` | siehe Abstract | `H3.median` |
| `h3-lo` | untere Grenze (Ablehnung, wenn ≤ 2) | `H3.lo` |
| `h3-hi` | obere Grenze | `H3.hi` |
| `h3-verdict` | „rejected“ oder „not rejected“ | `H3.rejected` |
| `h3-legacy-ratio` | Median K_Legacy / K_PM2 derselben Bücher (explorativ) | `results/p2/h3_netting.csv`, `H3.legacy_median` |
| `h3-reading` | Streuung über Maker und Zeit, welche Bücher am wenigsten netten | `results/p2/h3_netting.csv` |

### 4.4 H4

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `h4-events-raw` | Zahl der Parameteränderungen im präregistrierten Satz vor Zusammenfassung und Filter | `results/p2/h4_events.csv` (Modul `p2events.py`) |
| `h4-events` | Ereignisse nach Zusammenfassung je Tag und 1-%-Filter | `summary.json` → `H4.events` |
| `h4-cells` | Zell-Ereignis-Paare mit ≥ 20 Fills je Seite | `H4.cell_events` |
| `h4-doses` | Satz: Spanne und Vorzeichen der Dosen, Verschärfung gegen Lockerung | `results/p2/h4_events.csv`, Spalte `dose` |
| `h4-beta` | β in bp des Index je Einheit log-Kapital | `H4.beta` |
| `h4-p` | einseitiges Wild-Cluster-Bootstrap-p | `H4.p` |
| `h4-placebo-pct` | Perzentil von β unter 100 Placebos | `H4.placebo_pct` (aus `results/p2/h4_placebo.csv`) |
| `h4-verdict` | „rejected“ oder „not rejected“ | `H4.rejected` |
| `h4-reading` | Übersetzung: bp Halbspread je 10 % Kapitaländerung | aus `H4.beta` gerechnet, im Zahlenblatt ausweisen |

### 5 Discussion

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `disc-map` | Absatz: Was die Kapitalkarte gegenüber der Nominalkarte von Paper 1 ändert (H1) | `h1_cells.csv`, `summary.json` → `H1` |
| `disc-book` | Absatz: Was Grenzkosten und Netting-Wert für Grösse und Managerwahl eines Makers heissen (H2, H3) | `summary.json` → `H2`, `H3` |
| `disc-price` | Absatz: Ist Kapital ein Preis, auf den der Halbspread reagiert (H4)? Bezug `comertonforde2010`, `brunnermeier2009` | `summary.json` → `H4` |
| `disc-time` | Halbsatz zu den Zeitnormierungen (bis Verfall, empirische Haltedauer), explorativ | `results/p2/sensitivity_time.csv` |

### 6 Conclusion

| Platzhalter | Bedeutung | Quelle |
|---|---|---|
| `concl-results` | je Hypothese ein Satz in einfachen Worten mit Kernzahl | `summary.json` |
| `n-rejected` | siehe Abstract | siehe Abstract |
| `concl-close` | der eine Satz, den ein Maker mitnehmen soll | – |

---

## 5 · Literatur im Manuskript

Stand nach dem Audit (25.09.2026): alle 30 Schlüssel aus `paper2/refs.bib` werden zitiert (Prüfung je Eintrag in
`docs/paper2/LITERATUR.md`, Gleichheit der mit Paper 1 geteilten Einträge in `tests/test_p2_refs.py`):

| Abschnitt | Schlüssel |
|---|---|
| 1 | brunnermeier2009, garleanu2011, ho1981, avellaneda2008, gueant2013, stoikov2009, garleanu2009, jameson1992, muravyev2016, christoffersen2018, fournier2020, chen2019, albiez2026, santaclara2009, kupiec1996, comertonforde2010, ahn2025 |
| 2 | kupiec1994, duffie2011, cont2014, figlewski1984, artzner1999, derivev2core, qin2021, soska2021, derivegetmargin |
| 3 | albiez2026, cameron2008, mackinnon2017, roodman2019 |
| Back Matter | albiez2026, derivegetmargin, derivev2core, burlig2018 |

`albiez2026` ist `@unpublished` (Working paper, FHNW) ohne DOI und liegt ausserhalb der Crossref-Prüfung. Die
Fassung (19.09.2026, Commit `103c676`, letzte Änderung an `paper/main.tex`) nennt der Text in Abschnitt 3, nicht
der Bib-Eintrag (A18). Die Inferenz-Zitate (`cameron2008`, `mackinnon2017`, `roodman2019`) und `burlig2018` sind
aus `paper/refs.bib` zeichengleich übernommen (A61); der frühere Punkt „Offen“ ist damit erledigt.

---

## 6 · Offene Entscheidungen für den Autor

1. **JEL-Codes** als Vorschlag: G13 (Optionen), G12 (margin-basierte Preisbildung), G24 (Broker, Dealer,
   Market Maker), D47 (Marktdesign). Paper 1 hatte G13, G14, G12, D47.
2. **Competing interest** ist wörtlich aus Paper 1 übernommen, samt Kontakt zum Team wegen Order-Daten.
   Bitte bestätigen, dass das für Paper 2 weiter gilt.
3. **Abstract-Satz zu H4** (`h4-direction`) hängt vom Vorzeichen ab. Bei Ablehnung ist „did not respond
   measurably“ ehrlicher als eine Zahl.
4. **`paper2/main.pdf`** ist Bauausgabe und steht inzwischen in `.gitignore` (erledigt).
5. **Öffentliche Verankerung der Präregistrierung (A02).** Die Zeiten von `1d13227` und der vier Nachträge sind
   lokale Git-Zeiten; kein Commit liegt auf einem Remote. Das Manuskript sagt das jetzt („All commit times are
   local times of the author's machine …“). Empfehlung: erst A01 klären (`docs/paper2/HISTORIE_BEREINIGEN.md`),
   dann den Branch pushen und mit Merge-Commit integrieren (kein Squash, kein Rebase), zusätzlich die
   Commit-Hashes mit OpenTimestamps stempeln oder `PRAEREGISTRIERUNG.md` samt Nachträgen bei OSF hochladen. Ist
   das geschehen, im Abschnitt „Data, code and pre-registration“ das Datum der Veröffentlichung bzw. den
   Zeitstempel nennen (Datum per `% src git:` oder als Konstante erklären).
6. **Historie bereinigen (A01).** Folgt der Autor `docs/paper2/HISTORIE_BEREINIGEN.md`, ändern sich die Hashes
   der Nachträge (Testlauf: `eb534fe` → `1d6b2de`, `9465210` → `3872ed0`, `bfc34c8` → `985ec99`, `c4fcb59` →
   `396e180`; massgeblich ist der echte Lauf; `1d13227` und `103c676` bleiben). Danach in `paper2/main.tex` die
   vier Hashes im Abschnitt „Data, code and pre-registration“ und die Erklärung `% src git:c4fcb59` nachziehen,
   `docs/paper2/ZAHLENPRUEFUNG.md` neu erzeugen und den Abschnitt 7.2 dieser Datei anpassen.

---

## 7 · Review-Runde 1 (25.09.2026)

Eingearbeitet sind alle kritischen und wichtigen Befunde von Referee und Zahlenprüfer, die kleinen fast alle.
Neue Zahlen stehen erst im Text, seit sie in `results/p2` liegen (Zahlenregel). Prüfkette danach grün:
`p2_number_check` (0 unbelegt), `p2_wordcount` (alle Abschnitte im Budget, Abstract 200/200),
`p2_build` (build clean), `p2_figure_check` (alle Prüfungen ja).

### 7.1 Neue Grössen und wo sie entstehen

Alles explorativ oder beschreibend; kein registriertes Urteil und keine registrierte Zahl ändert sich.

| Grösse | Code | Ablage | Wert (Pilot) |
|---|---|---|---|
| ρ nur aus dem Vorzeichenmuster (Ränge innerhalb der Vorzeichengruppen gemischt, 4 000 Ziehungen, Seed 20260924) | `inference_p2.sign_floor` | `sensitivity.json` → `h1_sign.sign_floor`; `summary.json` `h1_sign_floor_*` | Mittel 0,734, P5 0,700, P95 0,770 |
| ρ innerhalb von Gruppen (Tages-Bootstrap von H1, Gruppen nach Vorzeichen wählen ihre Zellen in jeder Replikation neu; A04) | `inference_p2.h1_sign` | `h1_sign.within_{pos,nonpos,sell,buy,pos_sell,pos_buy}` | Edge > 0: 0,634; Verkäufe 0,990; Käufe 0,721; profitable Käufe 0,243 |
| Überlappung der besten Zellen | `inference_p2.top_overlap` | `h1_sign.top_overlap`; `h1_top10_overlap`, `h1_top20_overlap` | 1 von 10, 5 von 20 |
| H2 und H3 je Parameterregime R1 bis R4 (Grenzen wie `figs_p2.f1.REGIME_BOUNDS`, getestet) | `inference_p2.h2_regime_rows`, `h3_review_rows` | `sens_h2.csv`, `sens_h3.csv` (`group = regime=…`); `sensitivity.json` `d_h2.by_regime`, `e_h3.by_regime` | H2 0,0117 bis 0,0899; H3 4,44 bis 6,00 |
| H3 je Manager des Kontos | `inference_p2.h3_review_rows` | `group = account_manager=SM/PM/PM2`; `e_h3.by_account_manager` | SM 1,076; Legacy 5,457; PM2 5,161 |
| H3 höchstens 63 Optionen ohne SM-Konto | dito | `e_h3.sm_pm2_le63_no_sm` | 3,780 [3,635; 3,980], n = 184 |
| H2-Population vor der Ziehung, Ziehung gegen `marginal.parquet` geprüft | `inference_p2.h2_population` | `d_h2.population`; `h2_population` | 100 995, Ziehung identisch |
| H4-Niveau und Lesehilfe (ln 0,9 mal β und Intervallgrenzen) | `inference_p2_h4.review_extras` | `sensitivity_h4.json` → `review.readings`; `h4_review_*` | Halbspread im Mittel 7,93 bp (Median 3,34); −1,75 bis +2,74 bp |
| H4 nur Verkaufs- bzw. Kaufzellen, Dosis mit OI-Anteil des geänderten Managers gewichtet | dito | `review.sells_only`, `buys_only`, `oi_weighted` | −3,81 (p 0,58); 128 (p 0,13); −5,13 (p 0,59); OI-Anteil 54,5 bis 94,9 % |
| API gegen Chain-Semantik, 195 Einzelkontrakte | `p2_zahlenblatt.review_section` aus `api_snapshot.csv` | `api_*` | PM2 Median 0,08 %, p95 0,50 %, Max 2,4 % (> 90 T) |
| Weitere Zähler | dito | `fills_outside_every_window` (6), `h3_accounts_{sm,pm,pm2}` (1/4/4), `h3_accounts_median_above_threshold` (8 von 9), `h3_days_over_validated_legs` (127, bis 317 Beine), `validation_single_blocks_per_cell` (100), `semantik_box_expiries` (14), `event_*_refbook_log_change` | |

CLI: `python3 -m derive_surface p2 infer extras` und `python3 -m derive_surface.inference_p2_h4 extras` schreiben
nur diese Einträge in die bestehenden Dateien; `infer sensitivity` und `inference_p2_h4 run` erzeugen sie beim
nächsten Volllauf mit. Danach `scripts/p2_zahlenblatt.py`. Tests in `tests/test_p2_inference.py` und
`tests/test_p2_inference_h4.py`.

### 7.2 Änderungen an Prüfkette, Abbildungen und Karten

- `p2_number_check.py`: Erklärungen im Abstract gelten nur für das Abstract (so bindet „two are rejected“ nicht
  mehr jede „two“ des Textes an `derived:n_rejected`); Daten und Uhrzeiten lassen sich erklären
  (`% src datei:schlüssel <Datum>`, `const:`, `git:<sha>` für das Autorendatum eines Commits). Damit gehen
  „25 September 2026“ (Nachträge) an `git:c4fcb59`, das Datum der API-Probe an `api_day`, „08:00“ an
  `fig_t1_meta.csv`, „fourteen“ an `semantik_box_expiries`, „−0.105“ an `h4_review_ten_pct_dose`.
- `p2_figure_check.py`: neue Prüfung `CAPTION_ELEMENTS`. Nennt eine Bildunterschrift ein Band oder eine
  Zeilengruppe (F2 „grey band“, F3/F4 „per/by parameter regime“, „by the manager of the account“, „by book size“,
  „on the same BTC and ETH legs“), muss die Figurtabelle diese Zeilen enthalten.
- Captions in den Modulen (F1 „four regimes“ mit den drei Grenzdaten; F2 „edge per unit of premium“; F3 Titel „A
  fill in a dominant maker's book“; F4 Grenze von 63 Optionen als Probe vom September 2026, Zeile „SM / PM2 same
  legs“ erklärt). F2-Zeilentitel „edge per premium“ statt „return on premium“, F3-Band „full“ statt „dearer“;
  F2 und F3 neu gebaut. `docs/paper2/ABBILDUNGSWAHL.md` bleibt als historische Bauanweisung unverändert.
- Social-Karten: s1 „a fill costs … per contract“ statt „the next contract“; s3 nicht mehr „the map … stays the
  same“, sondern Vorzeichenmuster (0,90) und profitable Zellen (0,63); Fusszeile nennt die Präregistrierung
  `1d13227` statt `c4fcb59`.

### 7.3 Abgelehnte oder nur teilweise übernommene Vorschläge

1. **Referee, klein (H1-Intervall unter dem Schätzer):** Der vorgeschlagene Halbsatz „the interval sits below the
   estimate because thin cells are noisier in resampled days“ ist nicht übernommen, weil der Mechanismus nicht
   belegt ist. **Korrektur nach dem Audit (A28):** Die hier zuerst gegebene Begründung war falsch. Die
   Bootstrap-Verteilung des registrierten ρ liegt unter dem Schätzer (Mittel der Ziehungen 0,8946, Median 0,8950,
   nur 15,2 % der Ziehungen auf oder über 0,9029); das Rauschen zieht ρ im registrierten Test nach unten, nicht nach
   oben. Die über dem Schätzer liegenden Gruppenintervalle (Edge ≤ 0: 0,636 bei [0,674; 0,830]) kamen nicht von
   „wenigen, dünn besetzten Zellen“, sondern von der Auswahl der Gruppen über das Vorzeichen des geschätzten Edge
   bei festen Zellen (A04); mit neuer Auswahl je Replikation liegen sie bei [0,460; 0,684]. Das Manuskript nennt
   jetzt die neu gerechneten Intervalle (0,634 [0,572; 0,702], 0,243 [0,207; 0,446]) und in Anhang B, dass das
   Perzentilintervall nicht zentriert ist (bias-korrigiert 0,898 bis 0,920); das Urteil bleibt.
2. **Referee, klein (cameron2008, mackinnon2017, roodman2019 zitieren):** nach dem Audit übernommen (A61); die
   Einträge stehen jetzt in `paper2/refs.bib`.
3. **Referee, wichtig (Aufteilung grosser Bücher auf SM-Subaccounts nach Verfall):** Der zweite Satz des Vorschlags
   ist nicht geprüft und steht deshalb nur als offene Grenze in 4.3 („is not examined“), wie vom Referee für
   diesen Fall vorgesehen.
4. **Referee, wichtig (H2 explorativ nach öffnenden und schliessenden Fills trennen):** nicht gerechnet.
   `marginal.parquet` enthält die Position im Instrument vor dem Fill nicht; sie müsste aus Snapshot und
   `BalanceAdjusted` je Fill neu erhoben werden (Lauf in `books.py`). Übernommen ist die Minimalfassung als Satz
   ohne Zahl: der Median mischt Fills, die das Risiko des Buchs ausgleichen, mit Fills, die es erhöhen. „Many fills
   that release capital close existing positions“ ist ohne diese Messung nicht belegt und steht nicht im Text.
5. **Referee, wichtig (K explorativ für Option plus Perp-Delta rechnen):** nicht gerechnet; die Abweichung zwischen
   gesichertem Netto-Edge und Kapital des ungesicherten Kontrakts steht in Abschnitt 3 und unter den Grenzen.
6. **Referee, klein (Anteil der Maker-Tage mit Nicht-USDC-Collateral):** nicht gerechnet, `maker_days.parquet`
   führt kein Collateral. Nach dem Audit (A44) sagt der Text ohne Zahl, dass die meisten Maker-Tage solches
   Collateral halten (nachgezählt aus `snapshots.parquet`: 1 241 von 1 943) und dass ein PM2-Konto ETH hält, das
   seine Lib als risikomindernd zählt. Eine Zahl im Text braucht einen Schlüssel in `results/p2` (offen, 8.3).
7. **Referee, kritisch (H4 im Abstract „modest narrowing“):** „modest“ ist nicht übernommen. Nach dem Audit (A05)
   ist „a narrowing by a fifth is not excluded“ ersetzt: Die beschreibende Spanne (−1,75 bis +2,74 bp) ist auf die
   Ereignistermine bedingt; an den Placebo-t kalibriert reicht sie von −3,13 bis +4,39 bp, also bis zu 39 % des
   mittleren Halbspreads. Das Abstract sagt weiter nur „no evidence“.
8. **Referee, kritisch (Abstract-Wortlaut H3 mit 73,6 %):** gekürzt auf „mostly books no standard-margin account
   could hold“, weil das Abstract eine harte Grenze von 200 Wörtern hat; 73,6 % stehen in Einleitung und 4.3.
9. **Referee, klein (Kohärenz: PM2 nur praktisch konvex):** wegen des Budgets von Abschnitt 2 (660/660) nur der
   erste Teil übernommen: Der Satz schreibt die Kohärenz nur dem Worst-Loss-Kern der Szenario-Margin zu und nicht
   der ganzen Regel mit Kontingenzen und Static Discount; Figlewski steht jetzt für wahrscheinlichkeitsbasierte
   Margin („probability-based margin“), nicht für Szenario-Engines.
10. **Zahlenprüfer, klein (Deklarationen für alle Zählwörter):** nach dem Audit (A19 bis A21, A33) erledigt. Es gibt
    keine generischen Treffer mehr; jedes Zählwort ist erklärt, als Wert (`fig_f1_regimes.csv:regime~distinct
    four`, `fig_t2_b.csv:row~count four`, `summary.json:validation_single_blocks_per_cell 100`), als Konstante
    (`const:addenda Four`) oder als Textzahl (`text:reading_aid_pct ten`).
11. **Referee, wichtig (Absatz zu den Grenzen um „dose is stand-alone …“ erweitern):** steht statt in der Diskussion
    in 4.4 (Identifikationsabsatz), weil die Diskussion am Budget liegt; die Diskussion nennt die übrigen Grenzen.

### 7.4 Hinweise für den nächsten Lauf

- Nach dem Enddatenlauf: `infer sensitivity`, `inference_p2_h4 run` (beide über `scripts/p2_heavy.py`),
  `p2_zahlenblatt.py`, Abbildungen, `p2_number_check`, `p2_wordcount`, `p2_build`, `p2_figure_check`. Seit dem
  Audit bricht der Bau tatsächlich ab, wenn eine erklärte Zahl ihre Quelle nicht mehr trifft, wenn eine Zahl ohne
  Erklärung dasteht und wenn eine Erklärung kein Vorkommen mehr hat, jeweils je Einheit und Vorkommen. Die Sätze zu
  H1 (0,634 [0,572; 0,702], 0,734), H3 (3,780, 8 von 9) und H4 (kalibrierte Spanne −41,6 bis 29,7, −3,13/+4,39 bp,
  39 %) sind dann neu zu lesen, nicht nur die Ziffern zu tauschen. Für neue Sätze liefert
  `python3 scripts/p2_number_check.py --template` je Einheit die Zahlen in Textreihenfolge mit Kandidaten, die
  inhaltlich zu prüfen sind.
- Die Kaufzellen-Schätzung von H4 (128, p 0,13) beruht auf Dosen nahe null und ist kaum identifiziert; sie steht mit
  den übrigen explorativen H4-Varianten in Anhang B, damit die Verkaufszeile nicht selektiv wirkt.

---

## 8 · Audit-Runde (25.09.2026)

Grundlage: `docs/paper2/AUDIT.md` (69 Befunde). Hier steht, was im Manuskript geändert ist. Kein registriertes
Urteil ändert sich; `results/p2/h1.json` bis `h4.json` sind bitgleich zu `d51ede0`. Wächter für die korrigierten
Formulierungen: `tests/test_p2_manuscript.py` (zurückgenommene Wendungen
dürfen nicht zurückkehren, verlangte Offenlegungen müssen bleiben, Floats vor dem Schluss, PDF-Metadaten; der
Test prüft auch, dass die auditierte Fassung `3ec74f4` an jeder Prüfung scheitert).

### 8.1 Stand der Prüfkette

`p2_number_check` 0 Fehler bei 352 Zahlen (17 Textzahlen), `p2_wordcount` alle Abschnitte im Budget, `p2_build`
„build clean“ (12 Seiten, 0 Overfull, keine Underfull-Box im Fliesstext; die übrigen stammen aus `main.bbl`,
lange URL und DOI), `p2_figure_check` Exit 0.

| Abschnitt | Wörter | erlaubt |
|---|---|---|
| Abstract | 198 | 200 |
| 1 Introduction | 660 | 660 |
| 2 The engine and what it returns | 660 | 660 |
| 3 Data and measurement | 659 | 660 |
| 4 Results | 1 536 | 1 540 |
| 5 Discussion | 438 | 440 |
| 6 Conclusion | 189 | 220 |

Um die Budgets zu halten, stehen die nachträglichen (post hoc) und die registriert explorativen Detailzahlen jetzt
in einem neuen **Anhang B „Post hoc and exploratory results“** (ohne Budget): Vorzeichen-Untergrenze 0,734 mit
Perzentilen, ρ unter Verkäufen und Käufen, Überlappung der besten 10 und 20 Zellen, H1-Intervall nicht zentriert,
explorative Karten (vorher 4.5), H2 je Regime, RFQ-Pakete, Nicht-USDC-Collateral, H4 je Basiswert, nur Verkäufe,
nur Käufe, OI-gewichtet, Placebo über alle Zeitlinien, Placebos mit getrennten Fenstern, Median- und getrimmte
Dosis. Im Ergebnisteil bleiben die registrierten Zahlen, die in Abstract, Einleitung und Schluss zitierten
post-hoc-Werte (0,634 und 0,243 mit Intervall) und die kalibrierte H4-Spanne.

Kennzeichnung (A03): Abschnitt 3 legt fest „Analyses not named in the registration are exploratory, those added
after the first results post hoc“. Post hoc heissen alle Grössen, die erst mit `48e4032` oder später entstanden
(Schlüssel `h1_sign_*`, `sens_h1_sign_*`, `h1_top*`, `*_by_regime_*`, `*_by_account_manager_*`,
`sens_e_h3_sm_pm2_le63_no_sm`, `h4_review_*`, alle Audit-Schlüssel); explorativ die mit den Ergebnissen in
`93b42bc` gerechneten, nicht registrierten Grössen (H2 je Konto, H3 bis 63 Optionen, Placebo über alle
Zeitlinien) und die in der Präregistrierung als explorativ benannten (Karten, je Basiswert, Zeitnormierungen).

### 8.2 Änderungen je Befund

| Befund | Änderung in `paper2/main.tex` |
|---|---|
| A02 | „Data, code and pre-registration“: Commit-Zeiten sind lokale Zeiten des Rechners des Autors, vor den Ergebnissen lag kein Commit auf einem öffentlichen Server; Nachträge mit „(UTC+2)“. Empfehlung OpenTimestamps/OSF in Abschnitt 6, Punkt 5. |
| A03 | Konvention in Abschnitt 3; „post hoc“ bzw. „exploratory“ an jeder betroffenen Zahl; Abstract „post hoc, much of that correlation is the sign of the edge“; „(H1)“ in Diskussion und Schluss nur am registrierten Befund; Detailzahlen in Anhang B. |
| A04 | 0,634 (0,572 to 0,702) und 0,243 (0,207 to 0,446) in Einleitung und 4.1; Caption F2 aus dem Modul („cells are chosen again in every replicate“); Anhang B erklärt die Auswahl je Replikation. |
| A05 | 4.4 neuer Absatz „The test has little power“: sd(t) 1,82 an 100 Placebo-Terminen, kalibrierte 90-%-Spanne −41,6 bis 29,7, für 10 % billigeres Kapital −3,13 bis +4,39 bp, Verengung bis 39 % nicht ausgeschlossen; „by a fifth“ gestrichen; Hinweis auf zu kleine explorative p (Anhang B); Diskussion „or the test lacks the power to detect a narrowing of that size“; Schluss „no detectable response … in a test of little power“; Einleitung „the test cannot exclude a sizeable narrowing“. |
| A06 | Placebo-Regel „at least 28 days from every change of the underlying's legacy-manager and standard PM2 parameters (Addendum 4)“; Variante über alle Zeitlinien (P95 21,57, 88 %) als weitere Lesart von Nachtrag 4 in Anhang B. |
| A07 | „every test runs inside it“ ersetzt durch „only H4 also uses events before it“; 4.4 nennt die Legacy-Ereignisse vom 22.02.2025 (BTC, ETH) mit 75 der 475 Paare (`events.csv:panel_cells@manager=pm,kept=True~sum`). |
| A08 | Abstract und Einleitung: H3-Faktor „on the opening books of nine dominant subaccounts“, vom H2-Satz gelöst; „no standard-margin account could hold“ ersetzt durch „too large for a standard-margin account“. |
| A09 | „subaccount“ statt „maker“, wo Subaccounts gemeint sind; Abschnitt 3 nennt die Wallets („Some share a wallet: M3 and M5, M4 and M10, and M2, the one SM subaccount, with M1, M6 and M8“, nachgerechnet mit `data/p2/audit/inhalt/wallets.py`); 4.3 und Diskussion: M2 hält kleine Bücher, die grossen Bücher seiner Wallet liegen unter Portfolio-Margin; die Aufteilung auf Subaccounts als beobachtete Praxis. |
| A10 | Einleitung und 4.2: „maker buys there mostly release capital and maker sells mostly bind it“ (ohne Zahl, siehe 8.3); Diskussion und Schluss auf „the median fill“ beschränkt. |
| A11 | Erster Diskussionspunkt gilt „from an empty or small book“; in den dominanten PM2-Büchern ordnet das Grenzkapital die Seiten anders. |
| A12 | 4.1: Edge der obersten Kapitalzellen nahe am Abstand von Fill-Preis und SVI-Mark im extrapolierten Flügel, überwiegend RFQ-Beine (post hoc); Diskussion nennt diese Grenze. |
| A13 | 4.1 „a maker buy binds about its premium out of the money and less in the money“; „where a long option binds about its premium“ nur für weit aus dem Geld; Captions F1 und F2 aus den Modulen. |
| A14 | Abstract „the margin rules are public contracts with parameters on chain, and the venue's off-chain engine can be queried for any book“; Abschnitt 2 „The managers' contracts are public \citep{derivev2core} … BitMEX instead margins each position at a percentage of its notional \citep{soska2021}“; Schluss „The rules that set it are public contracts“. Titel unverändert (das Abstract trägt die Einschränkung). |
| A15, A16, A17, A60, A61 | Sätze des Literatur-Agenten übernommen (penalise/bound, fournier2020, chen2019, ahn2025, derivev2core, derivegetmargin, cameron2008, mackinnon2017, roodman2019, burlig2018, „The question extends“, Zellen „a maker side and the absolute delta and tenor buckets of“). |
| A18 | Abschnitt 3: Fassung vom 19.09.2026 (`% src git:103c676`), beide Einheitenfehler (Gebühr und Rabatt je Fill; Karte je Nominal über das Nominal des ganzen Fills), betroffen sind Netto-Edge-Zahlen, Zellzählung der vierten Hypothese und Karte je Nominal, Korrektur angekündigt, Werte je Nominal weichen deshalb ab. |
| A28 | Anhang B: 15 % der Ziehungen auf oder über dem Schätzer, bias-korrigiert 0,898 bis 0,920; 7.3 Nr. 1 korrigiert. |
| A29, A30 | Anhang B: ein Ereignis mehr in den Placebo-Panels (HYPE vom 08.01.2026), überlappende ETH-Fenster aus 10 Tagen, Placebos mit getrennten Fenstern (P95 26,02, 48 %, sd(t) 1,77); Median-Dosis −4,52, getrimmt −4,08. |
| A34 | Referenzbuch „a short straddle at the forward of each underlying (BTC in panel c)“; „11 of the 14 kept events“ (`fig_f5_b.csv:jump_logpct@…~count`), Spanne 3,4 bis 37,4 über die Basiswerte und 7,8 bis 26,0 für BTC mit Zeilenbindung. |
| A35 | 4.1 „on the 6 and 18 sell cells that still reach 200 fills“; der Diskussionssatz zu gepoolt gegen nach dem 20.08. ist gestrichen. |
| A36 | „books of 32 to 63 legs, M2 included, give 3.43“. |
| A37 | Nachträge 1 bis 3 „committed before the step they govern“; Nachtrag 4 „written after capital per fill, marginal costs, netting ratios, the doses and the H4 panel with its half spreads had been computed; it records readings already implemented, but precedes any test statistic“. |
| A38 | 4.2: Nachtrag 4 wählte ratio statt „next single contract“, das der registrierte Wortlaut auch deckt, als beide je Fill vorlagen, vor jedem Median. |
| A39 | 4.5: beide MM-Varianten (0,0291 Konto-Lib, 0,0278 Standard-Lib) und „this variant was set to one library per ratio after the first results“; der erste gemischte Wert (0,0190) liegt nicht in `results/p2` und steht deshalb nicht im Text (8.3). |
| A40 | „before the first capital figure of the registered form, with zero cash“; Stage-A-Fixtures lasen vorher on-chain Margins einzelner Maker-Konten mit Cash; Proben vor der Registrierung einzeln genannt, einschliesslich SM-Karte der BTC-Zellen (aus der sich ρ für SM schon ablesen liess) und Margin-Historien, „which the registration does not list“. |
| A41 | Abschnitt 3: Eröffnungsbuch „priced at the companion paper's mark“. |
| A42 | Anhang A: H2 bewertet Bücher über dem grössten validierten Buch, kein Validierungsfall im Settlement-Fenster. |
| A43 | Abschnitt 2: „whole books were only probed at random, with larger gaps“. |
| A44 | Diskussion „Collateral other than USDC, held on most maker-days“; Anhang B zum risikomindernden ETH eines PM2-Kontos. |
| A45 | Anhang B: jedes Bein eines RFQ-Pakets gegen das Buch vor dem ganzen Paket, ohne die übrigen Beine. |
| A46 | „last pushed up to and including its block“. |
| A47, A50, A51, A53 | Captions A1, F3, F5, T2 aus den Modulen des Abbildungs-Agenten übernommen (samt Erklärungen 17, 180, 5). |
| A49 | Verweis auf F5 in Abschnitt 3 gestrichen; F3 und F4 vor 4.2, F5 und F6 vor 4.4 im Quelltext; `\FloatBarrier` (Paket `placeins`) vor dem Schluss, damit die Diskussion neben den H4-Abbildungen läuft und keine Abbildung hinter den Schluss rutscht; A1 im Anhang. Ergebnis: 12 Seiten, alle Ergebnisabbildungen vor „6. Conclusion“, A1 nach dem Beginn des Anhangs. |
| A55 | „legacy portfolio manager (legacy PM)“ in der Einleitung; M1 bis M10 „by rank“ in Abschnitt 3; R1 bis R4 in Anhang B mit Bezug auf die Grenzdaten von F1. |
| A56 | `\mathit{NE}`; H4-Regression als nummerierte Gleichung mit „post_i marking fills after the event“; Ereigniskapital als $K^{e+}/K^{e-}$. |
| A57 | Nach `\maketitle` Autor, Thema, Schlüsselwörter und Creator gesetzt; Lesezeichen für die Back Matter und die Literatur (`\phantomsection\addcontentsline`). |
| A58 | Fusszeile mit festem Datum „25 September 2026“ statt `\today`; Nachträge mit „(UTC+2)“. |
| A59 | Absatz der Beiträge umformuliert (keine Underfull-Box mehr im Fliesstext). |
| A64 | „The pre-registration is written in German, and its addenda are headed Nachtrag; an English translation made after the analysis is in docs/paper2/PREREGISTRATION_EN.md, and the German original is binding.“ |

### 8.3 Offen für den Autor oder andere Bereiche

- **Zahlen ohne Schlüssel in `results/p2`** (Zahlenregel, deshalb im Text ohne Zahl): Wallets (vier PM2-Subaccounts
  von drei Betreibern, neun H3-Subaccounts von vier Wallets; A09), H2 nach Maker-Seite (Median Verkäufe 0,075,
  Käufe −0,137; Quotient der Summen 0,166; A10), Buchabstand API gegen Chain (A43), Anteil der Maker-Tage mit
  Nicht-USDC-Collateral (1 241 von 1 943) und die Wirkung auf M8 (A44), grösstes H2-Buch (321 Beine), HYPE-Anteil
  und Settlement-Fenster (A42), gepoolter Median auf denselben R4-Zellen (1,031 und 0,991; A35), erste gemischte
  MM-Variante 0,0190 (A39), Edge-Anteil der RFQ-Beine in den obersten Zellen (A12). Wer sie im Text will, legt
  Schlüssel in `summary.json` an (Bereich Grundlagen) und erklärt sie per `% src`.
- **Captions, die nur im Modul geändert werden können** (sonst bricht `caption_drift` den Bau): F4 „standard margin
  account“ statt „standard-margin account“ (A59, `derive_surface/figs_p2/f4.py`); F5 „the reference straddle“
  sollte „the reference straddle of the underlying“ heissen (A34); F1 könnte sagen, dass R4 nur Zellen mit 200
  Fills nach dem 20.08. enthält (A35); F2-Label „net edge, Paper 1“ (A55).
- **A67** (Maker-Gebühr bei mehrbeinigen RFQ auf einem Bein, Nachtrag 2): numerisch unerheblich, im Manuskript
  nicht erwähnt, weil die Zahl (0,001 USDC je Kontrakt) nur in `results/p1_befund` liegt.
- **A02 und A01** siehe Abschnitt 6, Punkte 5 und 6.
