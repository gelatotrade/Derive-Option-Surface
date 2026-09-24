# Manuskript Paper 2: Gliederung, Wortbudget und Platzhalter

Stand: 24.09.2026, 23:00 UTC+2. Gehört zu `paper2/main.tex` (Entwurf vor der ersten Kapitalzahl).

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

Alle 20 geprüften Schlüssel aus `paper2/refs.bib` werden zitiert, dazu `albiez2026`:

| Abschnitt | Schlüssel |
|---|---|
| 1 | brunnermeier2009, garleanu2011, ho1981, avellaneda2008, gueant2013, stoikov2009, garleanu2009, jameson1992, muravyev2016, christoffersen2018, albiez2026, santaclara2009, kupiec1996, comertonforde2010 |
| 2 | kupiec1994, duffie2011, cont2014, figlewski1984, artzner1999, qin2021, soska2021 |
| 3 und Back Matter | albiez2026 |

`albiez2026` wurde als `@unpublished` (Working paper, FHNW) am Ende von `paper2/refs.bib` ergänzt. Es gibt
keine DOI, der Eintrag liegt deshalb ausserhalb der Crossref-Prüfung. `docs/paper2/LITERATUR.md` nennt noch
20 Einträge und ist nachzuziehen (in diesem Schritt bewusst nicht geändert).

Offen: Für die Inferenz (Cluster- und Wild-Cluster-Bootstrap) zitiert Paper 1 `cameron2008`,
`mackinnon2017` und `roodman2019`. Sollen sie auch hier stehen, sind sie aus `paper/refs.bib` unverändert zu
übernehmen (siehe `LITERATUR.md`, letzter Absatz der Reserve).

---

## 6 · Offene Entscheidungen für den Autor

1. **JEL-Codes** als Vorschlag: G13 (Optionen), G12 (margin-basierte Preisbildung), G24 (Broker, Dealer,
   Market Maker), D47 (Marktdesign). Paper 1 hatte G13, G14, G12, D47.
2. **Competing interest** ist wörtlich aus Paper 1 übernommen, samt Kontakt zum Team wegen Order-Daten.
   Bitte bestätigen, dass das für Paper 2 weiter gilt.
3. **Abstract-Satz zu H4** (`h4-direction`) hängt vom Vorzeichen ab. Bei Ablehnung ist „did not respond
   measurably“ ehrlicher als eine Zahl.
4. **`paper2/main.pdf`** ist Bauausgabe und steht nicht in `.gitignore` (dort nur `paper/main.pdf`). Vor dem
   Commit ergänzen oder die Datei löschen.
