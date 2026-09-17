# Design: Wer handelt gegen den Maker? Adverse Selection auf einer Onchain-Options-CLOB (Derive 2024–2026)

Stand: 17.09.2026 · Autor: Gregor Albiez (FHNW) · Ziel: SSRN Working Paper, 15–18 Seiten, Elsevier CAS zweispaltig, wenig Text, viele erklärende Abbildungen · Rolle: wissenschaftliche Vorarbeit des Market-Maker-Bots (liefert das Adverse-Selection-Modell der Quoting-Regel).

**Entscheidungen des Autors (17.09.2026):** Kern BTC/ETH/HYPE, Alts als Anhang · Stichtag 30.09.2026 08:00 UTC · Präregistrierung vor der ersten Markout-Zahl · Derive-Team vorab informieren · Code, Spec, Plan und Manuskript im bestehenden Repo `gelatotrade/Derive-Option-Surface` (Branch `paper1-adverse-selection`), Rohdaten unter `data/p1/` (nicht versioniert). Das Repo ist öffentlich: interne Notizen zur Datenanfrage bleiben ausserhalb (`Derive_Options/docs/`).

Reihenfolge wie bei HIP-4: **erst Pipeline und Zahlenblatt, dann schreiben.** Hypothesen H1–H4 werden vor der ersten Auswertung festgeschrieben (`docs/PRAEREGISTRIERUNG.md`), Erweiterungen danach klar getrennt.

---

## 1 · Fragestellung und Beitrag

**Frage.** Wie gross ist der Verlust eines passiven Makers nach einem Options-Fill auf Derive (Markout über 1 min bis Settlement), aus welchen Gegenparteiklassen stammt er, und in welchen Zellen der Surface (Delta × Tenor × Underlying) bleibt nach Markout, Gebühr, Rebate und Hedge-Kosten ein positiver Netto-Edge?

**Beitrag.**
1. Erste Adverse-Selection-Studie mit **Kontoidentität je Options-Fill**: der öffentliche Derive-Tape trägt wallet, subaccount_id, rfq_id, Gebühr, Rebate und realisiertes P&L. Cartea et al. (toxic flow), Barzykin et al. (adverse selection und price reading) und Albers et al. (fill vs post-fill) sind Theorie oder Perp-Experimente ohne Optionen; Alexander et al. (Deribit) messen Kaufdruck ohne Identität; die Hyperliquid-Identitätsarbeiten betreffen Perps.
2. **Modellfreier Settlement-Markout** als Kontrolle gegen die Zirkularität des Exchange-Marks (der Mark ist ein Backend-SVI, das den Fills folgen kann).
3. **Onchain-Rekonstruktion der Mark-Historie** aus `VolDataUpdated`-Events (SVI-Parameter je Verfall seit 01/2024) als eigener Datenbeitrag.
4. **Netto-Edge-Wasserfall** je Klasse und Zelle: Halbspread − Markout − Gebühr + Rebate − Hedge-Kosten, mit der 12,5-%-Gebührenkappe und den Maker-Tiers.

Nicht Teil des Papers (spätere Paper): Margin-Polytop, Vault-Roll-Ereignisstudie, Maker-Inventarpfade, HYPE-Listungsexperiment als Hauptergebnis. HYPE vor/nach Deribit-Listung erscheint hier nur als Split in H3.

---

## 2 · Daten

| Datensatz | Quelle | Felder | Umfang / Stand |
|---|---|---|---|
| **Options-Tape** | `public/get_trade_history {instrument_type: option, page_size 1000}` ohne currency (gemischt, paginiert), zusätzlich je Currency als Gegenprobe | trade_id, instrument_name, timestamp (ms), trade_price, trade_amount, mark_price, index_price, direction, liquidity_role, wallet, subaccount_id, rfq_id, quote_id, trade_fee, expected_rebate, realized_pnl, realized_pnl_excl_fees, tx_hash, tx_status, extra_fee | seit 11.01.2024; BTC 309 273, ETH ~800 k, HYPE ~85 k Zeilen (Maker- und Taker-Zeile je Fill); **beide Zeilen behalten**, Paarung über tx_hash + instrument + timestamp + amount + price; Stichtag **30.09.2026 08:00 UTC** |
| Perp-Tape (Hedge-Kosten, Maker-Erkennung) | dito `instrument_type: perp` | wie oben | seit Start |
| **Mark-Pfad (a)** | mark_price späterer Fills desselben Instruments | | im Tape |
| **Mark-Pfad (b)** | Chain: `VolDataUpdated` je Currency-VolFeed (SVI_a, b, ρ, m, σ, fwd, refTau, confidence, timestamp), `ForwardDataUpdated`, `SpotPriceUpdated`; Feed-Adressen aus `v2-core/deployments/957/<CCY>.json` und deren Git-Historie | | `eth_getLogs` auf rpc.derive.xyz, Fenster ≤ 2 000 Blöcke (Limit 10 000 Logs), topic0-Filter; Gegenprobe gegen `get_latest_signed_feeds` |
| **Settlement** | `get_option_settlement_prices {currency}`; `get_option_settlement_history` (P&L je Subaccount) | Verfall, Preis; subaccount_id, amount, settlement_pnl | 944 BTC-Verfälle; 254 986 BTC-Zeilen |
| Externe Referenz | Tardis Deribit `options_chain` am 1. jedes Monats 2024–2026 (kostenlos); DVOL-Historie | mark_iv, bid_iv, ask_iv je Serie | 33 Stichtage; HYPE_USDC prüfen |
| Buch-Mids (Pilot) | Live-Aufzeichnung 03.09.2026 (1,9 h, alle Optionen alle 20 s) und Recorder-Wochen ab Deployment | bid, ask, bid_iv, ask_iv | Pilot; Recorder als Erweiterung |
| **Klassifikation** | Vault-Verträge (help.derive.xyz „Vault Smart Contracts“, `get_vault_statistics`) → Vault-Subaccounts über `AccountCreated`; `get_liquidation_history` (83 Auktionen, tx_hash, bids); `get_maker_program_scores` je Epoche (Wallets im MM-Programm); rfq_id im Tape | | Tabelle wallet/subaccount → Klasse |
| Gebühren, Rebates | trade_fee, expected_rebate je Fill; `get_instrument` (maker_fee_rate, taker_fee_rate, base_fee, mark_price_fee_rate_cap); Institutional-Tiers (help.derive) | | |
| Hedge-Kosten | `get_funding_rate_history` (30 d rollierend, ab jetzt sammeln), Perp-Tape, Recorder-Perp-Buch | | |

Underlyings: **BTC, ETH, HYPE als Kern** (vollständige Surface-Pipeline vorhanden); die neun übrigen (SOL, XRP, ZEC, ADA, XAUT, CC, VVV, LIT, PUMP) nur als deskriptive Anhangstabelle (Fills, RFQ-Anteil, mittlerer Markout), ohne Surface.

Sicherung: Tape und Chain-Logs **sofort** vollständig ziehen und als Parquet mit Manifest (SHA-256, Zeilenzahl, Abrufzeit) ablegen, bevor v3 Felder ändert.

---

### 2a · Befunde der Datenprobe vom 17.09.2026 (gelten vor allem Früheren)

| Befund | Folge |
|---|---|
| `get_trade_history` liefert die Zeilen einer Seite **nicht chronologisch** (1000er-Seite unsortiert); Seitenwanderung über grosse Bereiche kann Zeilen auslassen oder doppeln | Download in Zeitfenstern, die auf **eine** Seite passen (rekursive Halbierung je Tag); ein Aufruf je Fenster |
| `from_timestamp` und `to_timestamp` sind **beide inklusiv** (count[a,m−1] + count[m,b] = count[a,b], geprüft) | Fenster [a, b], nächstes ab b+1 |
| Gesamtzahl Options-Zeilen über alle Underlyings rund 1,23 Mio (ohne `currency`-Parameter abrufbar); **erster Fill 06.12.2023 03:13 UTC** (1 402 Zeilen vor dem 01.01.2024) | ein Durchlauf für alle Underlyings ab 01.12.2023; Stichprobe laut Präregistrierung unverändert ab 11.01.2024 |
| Die `count`-Angabe der API ist über lange Bereiche **nicht additiv** (61 Tage: 16 Zeilen weniger als die Summe der Hälften); Tageszahlen stimmen exakt mit den gelieferten Zeilen überein | Integritätsprüfung durch Nachzählen jedes Tages; abweichende Tage werden neu geladen; die CLI schreibt nichts, solange ein Tag abweicht |
| Zeilen können lange nach ihrem Zeitstempel erscheinen: bei RFQ-Fills liegt die Maker-Zeile im Median 3 s, im 99. Perzentil 75 s und maximal 1 689 s (28 min) vor der Taker-Zeile; bei Buch-Fills sind beide gleich | Stichtag muss ≥ 60 min zurückliegen; zwischengespeicherte Fenster werden nur wiederverwendet, wenn sie ≥ 60 min nach Fensterende geladen wurden; finaler Lauf frühestens 30.09.2026 09:00 UTC |
| Maker- und Taker-Zeile tragen dieselbe `trade_id`; bei RFQ-Fills liegt der Maker-Zeitstempel einige Sekunden **vor** dem Taker-Zeitstempel (Quote vs Ausführung) | Fill-Zeit = Taker-Zeitstempel; Maker-Zeit als eigene Spalte |
| Perp-Tape: BTC 2,04 Mio, ETH 3,56 Mio, HYPE 1,47 Mio Zeilen | für Paper 1 **nicht** geladen (Hedge-Kosten aus Gebührenformel, Recorder-Spread, Funding); gehört zu Paper 3 |
| Vol-Feed-Adressen je Underlying über `SVI_fwd` gegen den Live-Forward identifiziert: BTC `0x3883…1b87`, ETH `0xb27c…d160` (beide **unverändert seit 01/2024**; die in R4 vermutete Adressänderung war eine Verwechslung von BTC- und ETH-Feed), HYPE `0x4819…12d1` (aktiv zwischen Block 30,0 Mio und 31,38 Mio, d. h. um den HYPE-Start 10.11.2025); dazu SOL `0x7423`, ZEC `0x52aa`, XAUT `0x665b`, XRP `0xbf2e`, VVV `0x8df0`, ADA `0xe7b5`, CC `0x6a0d`, LIT `0xc9b3`, PUMP `0x0105`, inaktiv `0xd38b` (vermutlich AAVE) | Feed-Tabelle im Code; Kontinuität per Stichprobe geprüft |
| Jeder `VolDataUpdated`-Log trägt `blockTimestamp`; im Beispiel landet die Kurve 45 s nach ihrer Signatur (`feed_ts`) onchain | beide Zeiten werden gespeichert (`feed_ts`, `block_ts`); Präregistrierung spricht von der „onchain gepushten“ Kurve → `block_ts` |
| Eventdichte ~0,5 `VolDataUpdated` je Block für BTC und ETH (2024 anfangs weniger), ~0,35 für HYPE → grob **38 Mio Events** für die drei Kern-Underlyings; RPC-Grenze 10 000 Logs je `eth_getLogs` (Fehler −32005) | adaptive Blockfenster, 50 000-Block-Stücke, wiederaufnehmbar, Hintergrundlauf; volle Auflösung, kompakt gespeichert (Parameter float32, Forward float64); **nur 15 GB frei** |
| `SVI.sol` (lyra-utils): k = ln(K/SVI_fwd), begrenzt auf ±4·√(a + b·σ); w = a + b·(ρ(k−m) + √((k−m)² + σ²)), gedeckelt bei 144; **vol = √(w / SVI_refTau)** mit dem Referenz-Tau des Fits, nicht der laufenden Restlaufzeit | Mark-IV-Rekonstruktion exakt nach dieser Formel; Gegenprobe gegen den Live-Ticker |
| `get_liquidation_history` deckt ohne Zeitfilter nur die **letzten 7 Tage** ab; `count`/`num_pages` sagen nur, ob eine weitere Seite folgt; manche Fenster scheitern reproduzierbar mit HTTP 500 bei Seitengrösse 100, gehen aber mit kleinen Seiten; sehr lange Fenster liefern weniger Auktionen als die Summe kurzer | Tagesfenster, Vereinigung über Seitengrössen 20 und 5, Halbierung bis 1 h bei Totalausfall, verbleibende Lücken werden ausgewiesen; Chain-Events (`DutchAuction`) als Fallback |
| Vault-Wallets: Help-Center-Seite „Vault Smart Contracts“ nennt 202 Adressen (Bridges, Connectors, TSA-Tokens mehrerer Chains); 15 Mainnet-Token auf Derive Chain, davon 10 handelnde Vaults, eins zu eins zu den 10 Vaults aus `get_vault_statistics`; TVL zusammen nur rund 1,6 Mio USD (17.09.2026) | kuratierte Liste `docs/paper1/meta/vault_wallets.csv` mit Quelle je Adresse, Gegenprobe gegen die Wallets im Tape; geringe Teststärke von H2 wird im Datenstand ausgewiesen |
| Maker-Programme (DRV-Scores) gibt es erst ab 20.11.2024 | die Klasse „MM-Programm“ kann vor diesem Datum nicht vergeben werden; im Datenstand ausweisen |
| `get_settlement_history` je Subaccount (BTC 254 986 Zeilen) | für Paper 1 nicht nötig (Settlement-Markout braucht nur den Preis je Verfall) |
| System-Python 3.9.6; das Repo verlangt ≥ 3.10 in `pyproject.toml`, alle 28 Tests laufen aber unter 3.9 | keine Installation, Aufruf per `python3 -m derive_surface` aus dem Repo; neuer Code 3.9-kompatibel (`from __future__ import annotations`, kein `match`) |

## 3 · Definitionen

Für jeden Fill zum Zeitpunkt t mit Preis P, Menge q, Maker-Richtung s ∈ {+1 Maker kauft, −1 Maker verkauft}:

- **Markout in USDC je Kontrakt:** MO_τ = s · (M(t+τ) − P), M = Mark-Preis zum Zeitpunkt t+τ aus Pfad (a) oder (b). Horizonte τ ∈ {1 min, 5 min, 30 min, 4 h, 24 h, Settlement}. Negativ = Verlust des Makers.
- **Delta-neutraler Markout:** MO^Δ_τ = MO_τ − s · Δ(t) · (S(t+τ) − S(t)), Δ aus der Mark-IV zum Fill-Zeitpunkt (Black-76 auf dem Forward), S = Index. Nimmt die Spot-Bewegung heraus; Rest ist Vol- und Skew-Bewegung.
- **Markout in Vol-Punkten:** MO^σ_τ = s · (IV_mark(t+τ) − IV_fill(t)), beide per Black-76-Inversion (bestehende Pipeline aus Derive-Option-Surface, bid/ask-IV-Abgleich < 1e-4 verifiziert).
- **Settlement-Markout:** MO_set = s · (Auszahlung bei Verfall − P), modellfrei. **VRP-bereinigt:** MO_set minus Mittelwert von MO_set aller Fills derselben Zelle (Delta-Bucket × Tenor-Bucket × Underlying × Kalendermonat), damit die Prämie, die jede Position der Zelle trägt, herausfällt (Robustheit: DVOL-basierte Erwartung).
- **Effektiver Halbspread:** HS = s_taker · (P − M(t)) mit s_taker = −s (positiv, wenn der Taker schlechter als Mark handelt), in USDC und Vol-Punkten.
- **Netto-Edge des Makers:** NE_τ = HS + MO_τ − fee_maker + rebate_maker − hedge, hedge = Perp-Halbspread + Taker-Fee + erwartetes Funding über τ, je Fill mit Delta gewichtet.
- **Zellen:** Delta-Buckets |Δ| ∈ {0–10, 10–25, 25–40, 40–60 (ATM), 60–75, 75–90, 90–100}; Tenor ∈ {≤ 2 d, 2–7 d, 7–30 d, 30–90 d, > 90 d}; Underlying.
- **Ausschlüsse:** Fills in den letzten 30 min vor Verfall (Settlement-TWAP-Fenster, cockpit `FEED_TWAP_SEC`), `tx_status ≠ settled`, Instrumente ohne Forward.
- **Gegenparteiklassen (Taker-Seite):** Vault · RFQ · Liquidation · Dominanter Maker als Taker (Wallet mit Maker-Anteil ≥ 80 % und ≥ 1 % des Maker-Volumens) · MM-Programm-Wallet · Grosswallet (≥ p99 des Notionals, sonst unklassifiziert) · Retail/Sonstige. Zuordnung je Wallet und Monat, Tabelle wird veröffentlicht (pseudonymisiert).
- **Sweep:** ≥ 5 Fills desselben Takers in ≤ 10 s über ≥ 3 Strikes.

---

## 4 · Hypothesen (Präregistrierung vor der ersten Auswertung)

| | Hypothese | Ablehnung, wenn |
|---|---|---|
| H1 | Toxizität ist konzentriert: die 10 Taker-Wallets mit dem grössten Maker-Verlust tragen > 50 % des aggregierten negativen Markouts (30 min); Fills > p90 der Grösse und Sweeps haben signifikant negativeren Markout als kleine Fills | Bootstrap-90-%-Band des Top-10-Anteils schliesst 50 % aus nach unten; oder der Grösseneffekt hat cluster-robust (Wallet) |t| < 1,96 |
| H2 | Vault-Rolls sind uninformierter Flow: VRP-bereinigter Settlement-Markout und 30-min-Markout der Vault-Fills ≥ 0 für den Maker | 95-%-Intervall des Vault-Markouts liegt vollständig unter 0 |
| H3 | HYPE war vor der Deribit-Listung (16.06.2026, Datum verifizieren) toxischer als danach und als BTC/ETH (Vol-Markout) | Differenz vor/nach (DiD gegen BTC/ETH, Placebo-Daten) nicht signifikant oder mit falschem Vorzeichen |
| H4 | Netto-Edge ist zellenabhängig: bei 30 min ist NE in weniger als der Hälfte der besetzten Zellen positiv; ATM-Kurzläufer BTC/ETH negativ, Flügel und lange Tenors positiv | Anteil positiver Zellen ≥ 50 % oder ATM-Kurzläufer positiv (Bootstrap je Zelle) |

Nebenbefunde ohne Präregistrierung (klar als explorativ): Markout nach Tageszeit, nach Buch-vs-RFQ, VPIN als Vergleichsmass, Inventar-konditionierter Markout der dominanten Maker (Placebo-Permutation), Fill-Finalität (Anteil reverted, Match→Settlement-Zeit).

---

## 5 · Methodik

1. **Panel-Regression:** MO_τ (drei Einheiten) auf Klasse × Grössenklasse × Delta-Bucket, Fixed Effects Instrument × Tag, Cluster auf Taker-Wallet; Wild-Cluster-Bootstrap wie in HIP-4 (`inference.py`-Muster, Clusterkorrektur G/(G−1)).
2. **Varianzzerlegung** within/between Wallet; **Lorenz-Kurve** der Toxizität (kumulierter Anteil der Taker-Wallets vs kumulierter Maker-Verlust).
3. **Placebo:** Klassen zufällig permutiert (1 000 Züge) → Verteilung des Klasseneffekts unter der Null.
4. **Robustheit des Mark-Pfads:** (a) spätere Fill-Marks, (b) onchain-SVI, (c) Settlement, (d) Deribit-Stichtage: Ergebnisse müssen in Vorzeichen und Grössenordnung übereinstimmen; Tabelle im Anhang.
5. **Mehrfach-Wallets:** Sensitivität, wenn Wallets mit identischem Zeit-/Instrumentmuster zusammengelegt werden (Konzentration als Untergrenze ausweisen).
6. **Netto-Edge:** je Zelle mit Bootstrap-Band; Gebühr aus trade_fee (Kappe als Treppe sichtbar), Rebate aus expected_rebate, Tier-Szenarien (Standard, Tier 4, Tier 1).

---

## 6 · Abbildungen (Theorie zuerst, dann Empirie)

| # | Abbildung | Zeigt |
|---|---|---|
| T1 | Mechanik des Markouts: ein Fill, drei Mark-Pfade (Fill-Marks, onchain-SVI, Settlement), drei Einheiten (USDC, delta-neutral, Vol) | Definition ohne Formeln |
| T2 | Netto-Edge-Zerlegung als Wasserfall-Schema mit Gebührenkappe 12,5 % und Tier-Rebates | warum Flügel und ATM verschieden rechnen |
| 1 | Markout-Fan über den Horizont (1 min … Settlement), Buch vs RFQ, BTC/ETH/HYPE, drei Einheiten übereinander | Hauptbefund und Vol-vs-Spot-Zerlegung |
| 2 | Heatmap Delta × Tenor des mittleren 30-min-Markouts in Vol-Punkten, daneben in bp Notional | wo der Maker verliert |
| 3 | Lorenz-Kurve der Toxizität, Segmente Vault / RFQ / Liquidation / Grosswallet / Sonstige eingefärbt | H1, H2 |
| 4 | Netto-Edge-Wasserfall je Klasse (Halbspread, Markout, Gebühr, Rebate, Hedge) | H4 |
| 5 | Tages-Toxizität 2024–2026 mit Ereignissen: FalconX 10/2025, HYPE-Listung 06/2026, Rekordmonat 03/2026, Vault-Roll-Tage | H3, Zeitstruktur |
| A | Anhang: Robustheit der vier Mark-Pfade; Klassentabelle; Alt-Underlyings | |

---

## 7 · Pipeline und Ablage

Alles im Repo `Derive-Option-Surface` (lokal unter `~/Documents/Papers/Working Papers/Derive_Options/Derive-Option-Surface`), Branch `paper1-adverse-selection`:

```
derive_surface/
  fulltape.py      Options-Tape mit allen 20 Feldern, beide Zeilen je Fill, Einzelseiten-Fenster, Manifest   (Plan 1)
  chainfeeds.py    VolDataUpdated je Feed, adaptive Blockfenster, Dekodierung, SVI-Vol nach SVI.sol          (Plan 1)
  refdata.py       Settlement-Preise, Liquidationen, Maker-Programme und Scores, Vaults, Gebühren, Funding   (Plan 1)
  classify.py      Paarung Maker/Taker, Wallet-Monats-Kennzahlen, Gegenparteiklassen                         (Plan 1)
  p1cli.py         python3 -m derive_surface p1 tape|volfeed|compact|ref|fills                                (Plan 1)
  markouts.py      Mark-Pfade a/b/c/d, drei Einheiten, Zellen, Ausschlüsse                                    (Plan 2)
  inference_p1.py  Regressionen, Wild-Cluster-Bootstrap, Placebo, Lorenz, Netto-Edge                         (Plan 2)
  figures_p1.py    T1, T2, 1–5, A                                                                              (Plan 3)
scripts/p1_check_feeds.py   Feed-Kontinuität und Gegenprobe SVI vs Live-Mark                                   (Plan 1)
docs/paper1/     PRAEREGISTRIERUNG.md, DATENSTAND.md, ZAHLENBLATT.md, meta/vault_wallets.csv
paper/           CAS-Manuskript (Plan 4)
data/p1/         raw/, tape/, volfeed/, ref/, derived/  (git-ignoriert)
tests/           offline; test_p1_*.py
```

- Pricing (Black-76, IV-Inversion, Forward-Delta) aus `derive_surface.pricing` direkt nutzen.
- Jede Auswertung als Skript, jede Zahl im Zahlenblatt mit Skript und Datum (Lehre aus HIP-4: Dominanz-Code ging dreimal verloren).
- Langläufe (Chain-Logs, Tape) wiederaufnehmbar, mit `caffeinate` am Netzteil oder auf dem VPS.

---

## 8 · Zeitplan (5–6 Wochen)

| Woche | Schritt | Ergebnis |
|---|---|---|
| 1 | Options-Tape + Chain-Feeds + Referenzdaten sichern; Klassentabelle; Präregistrierung H1–H4 (Perps entfallen, s. §2a) | Manifest, Klassen-Statistik, `PRAEREGISTRIERUNG.md` |
| 2 | Markouts in drei Einheiten, vier Mark-Pfade; Deskriptiva; Theorie-Abbildungen T1/T2 | Zahlenblatt v1, Abb. T1, T2, 1, 2 |
| 3 | Inferenz (Regressionen, Bootstrap, Placebo), Netto-Edge, Robustheit, Alt-Anhang | Zahlenblatt v2, Abb. 3–5, A |
| 4 | Schreiben (CAS, harte Grössenziele je Abschnitt, ≤ 18 Seiten), refs.bib nur verifizierte Quellen | Manuskript v1 |
| 5 | Zwei unabhängige Prüfer (Zahlen, Text), Einarbeitung, Team informieren, SSRN-Blatt | Upload-Fassung |

---

## 9 · Risiken und Grenzen

- **Mark-Zirkularität:** Backend-SVI kann den eigenen Fills folgen → Settlement-Markout und Deribit-Stichtage als unabhängige Pfade; Ergebnisse nur berichten, wo die Pfade übereinstimmen.
- **Mehrfach-Wallets:** Konzentration ist eine Untergrenze; Sensitivität mit Zusammenlegung.
- **Klassen heuristisch:** Vault und RFQ hart (Verträge, rfq_id), Institution/Retail weich; Team-Klassentabelle würde ersetzen, ist aber nicht nötig.
- **Rebate-Tier je Wallet unbekannt:** expected_rebate je Fill ist beobachtet, Tier-Szenarien für den Netto-Edge.
- **v3-Migration:** Felder und Events können sich ändern → Daten jetzt sichern, Stichtag 30.09.2026.
- **Ethik:** Wallets sind öffentlich, im Paper nur pseudonyme Cluster („Taker-A“); Derive-Team vor Veröffentlichung informieren; Deribit-Stichtage nur aggregiert (ToS „personal use“).
- **Statistische Kraft:** BTC/ETH reichlich (> 1 Mio Zeilen); HYPE dünn, H3 nur mit Placebo-Daten und DiD.

---

## 10 · Entscheidungen (17.09.2026 vom Autor bestätigt)

1. Kern BTC/ETH/HYPE, Rest als Anhang.
2. Stichtag 30.09.2026 08:00 UTC; bis dahin Pilotdaten bis 17.09.2026 12:00 UTC nur zum Bau der Pipeline, **keine Markouts**.
3. Präregistrierung H1–H4 (`docs/paper1/PRAEREGISTRIERUNG.md`) wird committet, bevor eine Markout-Zahl existiert.
4. Derive-Team wird vorab informiert (Formular).
5. Bestehendes Repo `gelatotrade/Derive-Option-Surface`, soweit möglich.

Umsetzung in Plänen: Plan 1 Datenbasis und Klassen (`docs/superpowers/plans/2026-09-17-p1-datenbasis.md`), Plan 2 Markouts und Inferenz, Plan 3 Abbildungen, Plan 4 Manuskript.
