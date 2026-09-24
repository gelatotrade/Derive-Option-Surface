# Design: Was kostet der Edge? Kapitalbereinigter Edge eines Options-Makers unter einer öffentlichen Risiko-Engine (Derive 2024 bis 2026)

Stand: 24.09.2026 · Autor: Gregor Albiez (FHNW) · Ziel: SSRN Working Paper im Format von Paper 1 (Elsevier CAS
zweispaltig, rund 3 800 Wörter, neun Abbildungen, wenig Text) · Branch `paper2-kapital`.

**Entscheidungen des Autors (24.09.2026):**
- ganzer Zeitraum von Paper 1 mit drei Managern;
- Edge je Kapital je Fill als Hauptgrösse, Zeitnormierung nur als Sensitivität;
- Kapital sowohl im Einzelkontrakt als auch im echten Maker-Buch;
- historisches Kapital über einen Offline-Nachbau mit Stichproben-Validierung gegen `eth_call`;
- Hypothesen H1 bis H4 wie in Abschnitt 4 mit den dortigen Schwellen;
- danach autonom weiterarbeiten, Paper schreiben und am Ende auditieren.

Grundlage: `docs/paper2/get_margin_semantik.md` (Semantik der Engine), `docs/paper2/UEBERGABE.md`, die Daten von
Paper 1 (`data/p1/`) und die Kontextproben unter `data/p2/kontext/`.

---

## 1 · Frage und Beitrag

**Frage.** Wie viel Kapital bindet der Edge eines Options-Makers auf Derive, und ändert sich das Bild aus Paper 1,
wenn man Edge je Kapital statt je Kontrakt misst?

**Beitrag.**
1. **Kapitalkarte.** Edge je Kapital über die Delta-mal-Laufzeit-Karte von Paper 1, gerechnet mit der echten,
   öffentlichen Risiko-Engine und nicht mit einer Modellannahme.
2. **Grenzkosten.** Das Kapital, das ein Fill im tatsächlichen Buch eines dominanten Makers zusätzlich bindet, unter
   dessen tatsächlichem Manager.
3. **Netting-Wert.** Kapital derselben echten Bücher unter Standard-Margin, Legacy-Portfolio-Margin und PM2.
4. **Preis des Kapitals.** Parameteränderungen der Engine als natürliches Experiment: Die kontrafaktische
   Kapitaländerung je Zelle ist exakt berechenbar und dient als Dosis für den Halbspread.

Der Titel nennt, dass Kapital über hypothetische Portfolios der Engine gemessen wird (Möglichkeitsraum), nicht über
beobachtete Kontosalden.

**Nicht Teil des Papiers:** Margin für offene Orders, Buchtiefe, ein Bot-Algorithmus, die API-Semantik (pauschal
2 %) in der Historie, Liquidationen.

---

## 2 · Daten

| Baustein | Quelle | Stand |
|---|---|---|
| Fills mit Netto-Edge | `data/p1/derived/markouts.parquet` und `inference_p1.analysis_frame` (Paper 1) | 603 940 Fills, 11.01.2024 bis 17.09.2026 12:00 UTC (Pilotschnitt) |
| SVI-Kurven je Verfall | `data/p1/volfeed/{CCY}_svi_YYYY-MM.parquet` (on-chain `VolDataUpdated`) | liegt vor |
| Spot, Forward, Zins | on-chain Feed-Events (`SpotPriceUpdated`, `ForwardDataUpdated`, `RateUpdated`) je Basiswert, neu zu laden nach `data/p2/feeds/` | Zeitraum wie Paper 1 |
| Parameter je Manager | on-chain Getter an den Ereignisblöcken, Legacy-PM per Bisektion (keine Events) | `results/p2/params/` |
| Maker-Bücher | `SubAccounts.getAccountBalances` und `manager()` per historischem `eth_call` zu Tagesbeginn für die zehn grössten Maker-Subaccounts, dazu die Fills des Tages aus dem Tape | `data/p2/books/` |
| Manager-Anteile am OI | `OptionAsset.totalPosition` je Manager, monatlich | `data/p2/kontext/margin-historie/oi_legacy.json` |

Verfügbarkeit (aus `data/p2/kontext/margin-historie`):

| | SM | Legacy-PM | PM2 |
|---|---|---|---|
| BTC | ganzer Zeitraum | ganzer Zeitraum (genutzt bis 02/2026) | ab 12.06.2025 23:00 UTC |
| ETH | ganzer Zeitraum | ganzer Zeitraum (genutzt bis 03/2026) | ab 12.06.2025 23:00 UTC |
| HYPE | ab 11.11.2025 | existiert nicht | ab 11.11.2025 |

Blockzeit auf Chain 957: exakt 2 s seit Genesis, Block 2 454 793 = 11.01.2024 00:00:01 UTC. Zeit und Block lassen
sich ohne Anfragen umrechnen.

---

## 3 · Messgrössen

**Semantik.** Historisch nur in Chain-Semantik: Parameter und Feeds zum jeweiligen Block, Zins aus dem PM2-Rate-Feed,
Standard-Lib (keine Kontenoverrides ausser im Maker-Buch, wo die Lib des Kontos gilt). Die API-Semantik mit
pauschal 2 % dient nur als heutige Sensitivität. IM ist primär, MM Sensitivität.

**Kapital eines Buchs q zu Preisen p** (aus der Semantik-Notiz):

    K_p(q) = Σ_Optionen p_i·q_i − net_IM(q; cash = 0)

Perps tragen keine Prämie und gehen mit Einstand gleich Perp-Preis ein. Nicht-USDC-Collateral bleibt ausserhalb von
K (Grenze, im Papier genannt).

**Je Fill (Einzelkontrakt).** q = +1 bei Maker-Kauf, −1 bei Maker-Verkauf, p = Fill-Preis, Buch sonst leer, unter
jedem verfügbaren Manager: K_SM, K_PM, K_PM2 je Kontrakt.

**Edge.** Netto-Edge NE nach 30 min aus Paper 1 (USDC je Kontrakt; Halbspread + adverse Selektion − Gebühr + Rabatt
− Hedge).

**Edge je Kapital einer Zelle** = Σ NE_i·a_i / Σ K_i·a_i (Verhältnis der Summen, a = Menge), in bp des Kapitals.
Zellen: Basiswert × Maker-Seite (Kauf, Verkauf) × |Δ|-Bucket × Laufzeit-Bucket aus Paper 1, besetzt ab 200 Fills.
Vergleichsgrösse: Edge in bp des Nominals = Σ NE_i·a_i / Σ Index_i·a_i.

**Grenzkosten je Fill (Maker-Buch).** Buch vor dem Fill = on-chain Bestand zu Tagesbeginn plus die Fills des
Subaccounts seit Tagesbeginn aus dem Tape. ΔK = K(nach) − K(vor), bestehende Positionen zum Mark M_b (Paper 1),
der neue Kontrakt zum Fill-Preis. Verhältnis ΔK / K_Einzel unter dem Manager des Kontos.

**Netting-Wert je Maker-Tag.** K des on-chain Buchs zu Tagesbeginn unter SM, Legacy-PM und PM2, Positionen zum Mark
M_b. Unter PM2 und Legacy-PM je Basiswert getrennt und summiert (kein Netting über Basiswerte).

**Zeitnormierung (Sensitivität).** (i) bis Verfall: NE / (K·Restlaufzeit), annualisiert; (ii) empirische
Haltedauer: Median der Zeit bis zur Glattstellung in den Maker-Büchern je Zelle.

---

## 4 · Hypothesen (präregistriert in `docs/paper2/PRAEREGISTRIERUNG.md`)

| | Aussage | Test und Ablehnungsregel |
|---|---|---|
| H1 Rangfolge | Der Kapitalnenner ordnet die Karte um. | Spearman-ρ zwischen Edge in bp des Nominals und Edge je PM2-Kapital über alle besetzten Zellen im PM2-Fenster. Abgelehnt, wenn die obere Grenze des 90-%-Cluster-Bootstrap-Intervalls (Cluster UTC-Tag) ≥ 0,5 ist. |
| H2 Grenzkosten | Im Buch eines dominanten Makers ist der nächste Kontrakt billig. | Median von ΔK / K_Einzel unter PM2 über die Fills der zehn grössten Maker-Subaccounts im PM2-Fenster. Abgelehnt, wenn die obere Intervallgrenze ≥ 0,5 ist. |
| H3 Netting-Wert | PM2 spart mehr als die Hälfte des Kapitals gegenüber SM. | Median von K_SM / K_PM2 über Maker-Tage im PM2-Fenster. Abgelehnt, wenn die untere Intervallgrenze ≤ 2 ist. |
| H4 Preis des Kapitals | Wird Kapital billiger, sinkt der Halbspread. | Differenz-in-Differenzen um Parameteränderungen mit der kontrafaktischen Kapitaländerung je Zelle als Dosis. Abgelehnt, wenn der Koeffizient nicht positiv ist mit einseitigem Wild-Cluster-Bootstrap-p ≤ 0,05, oder wenn er unter 100 Placebo-Terminen nicht im obersten 5-%-Bereich liegt. |

---

## 5 · Architektur

Neue Module im Paket `derive_surface` mit Präfix `p2` bzw. `margin_`, Tests offline unter `tests/test_p2_*.py`.

| Modul | Aufgabe |
|---|---|
| `p2types.py` | gemeinsame Typen `MarketState`, `ExpiryState`, `Book`, `OptionLeg`, `capital_from_net` (liegt vor) |
| `p2feeds.py` | Laden der Feed-Events (Spot, Forward, Zins, Perp) je Basiswert; `state_at(ccy, ts, expiries)` baut einen `MarketState` aus Feeds und SVI |
| `p2params.py` | Parameter je Basiswert, Manager und Zeitpunkt aus `results/p2/params/*.json`; Laden per `eth_call` an Ereignisblöcken |
| `margin_sm.py` | Nachbau `StandardManager` (isoliert, Max-Loss je Verfall, Perp, Basis), einzeln und vektorisiert |
| `margin_pm.py` | Nachbau Legacy-`PMRMLib` (ohne Diskont, ohne Skew, eigene Szenarien) |
| `margin_pm2.py` | Nachbau `PMRMLib_2` (Port von `data/p2/semantik_20260924/verify-konvex/pm2v.py`), vektorisiert |
| `p2validate.py` | Vergleich Nachbau gegen `eth_call` an Zufallsblöcken je Basiswert und Manager |
| `capital.py` | Kapital je Fill (Einzelkontrakt) unter allen verfügbaren Managern → `data/p2/derived/capital.parquet` |
| `books.py` | on-chain Bestände der Maker-Subaccounts zu Tagesbeginn, Dekodierung der Options-SubIds, Grenzkosten je Fill, Netting-Wert je Maker-Tag |
| `p2events.py` | Ereignisliste, Dosis je Zelle und Ereignis, Panel für H4 |
| `inference_p2.py` | Tests H1 bis H4, Sensitivitäten, `results/p2/*.csv|json` |
| `p2surface.py` | Adapter SVI-Kurve → `Surface`, Kapitalfläche auf dem Delta-mal-Laufzeit-Gitter, Animation |
| `figures_p2.py`, `figdata_p2.py` | Abbildungen über Registry wie Paper 1, Stil aus `figstyle.py` |
| `p2cli.py` | Unterbefehle `feeds`, `params`, `validate`, `capital`, `books`, `events`, `infer`, `figures`, `surface` |
| `scripts/p2_*.py` | Bau, Wortzählung, Zahlenblatt, Abbildungsprüfung (Muster Paper 1, ohne tautologische Vergleiche) |
| `paper2/` | Manuskript `main.tex`, `refs.bib`, `figures/` |

Die RPC-Last bleibt ≤ 2 Anfragen/s je Prozess. Alle Downloads sind wiederaufnehmbar und schreiben stückweise.
Maker-Subaccounts und Wallets erscheinen in Ergebnisdateien nur als Hash (SHA-256, erste 10 Zeichen).

---

## 6 · Abbildungen (Entwurf, finale Wahl wie in Paper 1 über Entwurf und Jury)

| Slot | Inhalt |
|---|---|
| T1 | Die Engine-Sicht der Oberfläche: BTC-Vol-Surface in 3D (Höhe IV), gefärbt mit dem PM2-Kapital je Short-Kontrakt, daneben SM. |
| T2 | Was `get_margin` liefert: net = C + V − R und die Auflösung 11 gegen 1,2 (Balken C − net gegen R). |
| F1 | Kapital je Kontrakt nach Manager über |Δ| × Laufzeit, Kauf und Verkauf. |
| F2 | Die Karte: Edge in bp des Nominals gegen Edge je PM2-Kapital je Basiswert und Seite, mit Rangstreuung (H1). |
| F3 | Grenzkosten im Maker-Buch: Verteilung ΔK / K_Einzel, Anteil ≤ 0 (H2). |
| F4 | Netting-Wert: K_SM / K_PM2 über Maker-Tage, Legacy-PM daneben (H3). |
| F5 | Zeitachse: Manager-Anteile am OI, Parameterereignisse je Basiswert, Kapital eines festen Referenzbuchs. |
| F6 | Preis des Kapitals: Dosis-Wirkung und Placebo-Verteilung (H4). |
| A1 | Validierung des Nachbaus gegen `eth_call`. |

Dazu für README und X: GIF der Kapitalfläche über die Zeit mit den Parameterereignissen, Social-Karten 1600×900.

Regeln aus Paper 1: CAS-Breiten 3,4 und 7,0 Zoll, keine Schrift unter 7 pt, lesbar in Graustufen, eine Zahl je
Zelle, Zellen unter 200 Fills als leeres Kreuz, jede Zahl der Abbildung auch als Tabelle unter `results/p2/`.

---

## 7 · Manuskript

Englisch, keine Gedankenstriche im Fliesstext, Wortbudget je Abschnitt (Einleitung 600, Engine und Semantik 600,
Daten und Messung 600, Ergebnisse 1 400, Diskussion 400, Schluss 200). Jede Zahl im Text muss in `results/p2/`
nachweisbar sein (Prüfskript). Literatur nur mit geprüfter DOI oder Verlagsseite, höchstens ein Web-Agent
gleichzeitig.

---

## 8 · Reihenfolge

1. Spezifikation und Präregistrierung committen (dieser Schritt).
2. Feeds, Parameter, drei Engines mit Tests; Maker-Bestände laden.
3. Validierung gegen `eth_call`; erst danach Kapital je Fill, Maker-Bücher, Dosen.
4. Inferenz H1 bis H4, Zahlenblatt.
5. Abbildungen mit Jury, Oberfläche und Animation.
6. Manuskript, Literaturprüfung, Bau.
7. Audit über das gesamte Paper.

Pilotzahlen mit Schnitt 17.09.2026 12:00 UTC, der Enddatenlauf folgt mit Paper 1 nach dem 01.10.2026.
