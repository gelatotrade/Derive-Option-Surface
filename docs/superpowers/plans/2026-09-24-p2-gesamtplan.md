# Paper 2: Gesamtplan (Kapitalbereinigter Edge) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aus den Fills von Paper 1 und einem Offline-Nachbau der drei Derive-Margin-Manager das Kapital je Fill, die Grenzkosten in echten Maker-Büchern, den Netting-Wert und die Dosis von Parameteränderungen berechnen, H1 bis H4 testen, neun Abbildungen bauen und das Manuskript schreiben.

**Architecture:** Neue fokussierte Module im Paket `derive_surface` (Präfix `p2`/`margin_`), die über die Typen aus `derive_surface/p2types.py` (liegt vor) sprechen. Daten unter `data/p2/` (git-ignoriert), Ergebnisse unter `results/p2/`, Manuskript unter `paper2/`. Die Ausführung läuft in Stufen A bis G; innerhalb einer Stufe arbeiten Agenten parallel an disjunkten Dateien, der Orchestrator committet nach jeder Stufe.

**Tech Stack:** Python 3.9.6 (System), numpy, pandas, pyarrow, requests, scipy, matplotlib; pytest; tectonic für LaTeX. Keine neuen Abhängigkeiten.

**Spec:** `docs/superpowers/specs/2026-09-24-p2-kapital-design.md` · **Präregistrierung:** `docs/paper2/PRAEREGISTRIERUNG.md` (Commit `1d13227`) · **Semantik:** `docs/paper2/get_margin_semantik.md`.

## Global Constraints

- Python 3.9.6: jede neue Datei beginnt mit `from __future__ import annotations`; kein `match`, keine `X | Y`-Typen ausserhalb von Annotationen.
- Keine neuen Abhängigkeiten. Tests offline, kein Netzwerk; `python3 -m pytest -q` muss nach jeder Stufe grün sein (Stand: 154 Tests).
- Aufrufe aus dem Repo-Wurzelverzeichnis `~/Documents/Papers/Finished Papers/Derive_Options/Derive-Option-Surface`.
- Daten nur unter `data/p2/` (git-ignoriert). Ergebnisse (klein) unter `results/p2/`. Nichts löschen, was nicht in dieser Sitzung erzeugt wurde.
- RPC `https://rpc.lyra.finance` (Chain 957) höchstens 2 Anfragen/s je Prozess; API `https://api.lyra.finance` höchstens 2 Anfragen/s, User-Agent setzen. Jede Anfrage mit Zeitstempel in ein JSONL-Log unter `data/p2/logs/`.
- Blockzeit: `block = 2_454_793 + (ts − 1_704_931_201) // 2` (exakt 2 s je Block; Block 2 454 793 = 2024-01-11 00:00:01 UTC). Gegenprobe gegen `volfeed` (`block`, `block_ts`).
- Code, Kommentare, Commit-Nachrichten englisch; Dokumente unter `docs/paper2/` deutsch mit Umlauten, keine Gedankenstriche im Fliesstext.
- Agenten committen nicht; der Orchestrator committet nach jeder Stufe.
- Maker-Subaccounts und Wallets in `results/` nur als `sha256(str(id))[:10]`.
- Referenzquellen: v2-core unter `data/p2/v2-core/` (Commit `96796a6`), Prototypen unter `data/p2/semantik_20260924/` und `data/p2/kontext/`, Adressen in `data/p2/kontext/margin-historie/deploy.json` und `addresses_head.json`.
- Kein Wert aus der Präregistrierung wird geändert. Abweichungen nur als datierter Nachtrag in `docs/paper2/PRAEREGISTRIERUNG.md`.

## Dateien

| Datei | Verantwortung | Stufe |
|---|---|---|
| `derive_surface/p2types.py` | Typen (liegt vor) | – |
| `derive_surface/p2chain.py` | RPC-Client (eth_call, getLogs adaptiv, Log), Blockzeit | A1 |
| `derive_surface/p2feeds.py` | Feed-Events laden und verdichten; `FeedHistory` mit `state_at` und `bulk_state` | A1 |
| `derive_surface/p2params.py` | Parameter-Zeitlinien je Basiswert und Manager | A2 |
| `derive_surface/margin_pm2.py` | Nachbau `PMRMLib_2` | A3 |
| `derive_surface/margin_sm.py`, `derive_surface/margin_pm.py` | Nachbau `StandardManager`, Legacy-`PMRMLib` | A4 |
| `derive_surface/books.py` | Bestände der Maker-Subaccounts, Dekodierung, Buch vor dem Fill | A5, B3 |
| `derive_surface/p2validate.py` | Nachbau gegen `eth_call` | B1 |
| `derive_surface/capital.py` | Kapital je Fill | B2 |
| `derive_surface/p2events.py` | Ereignisse, Dosen, H4-Panel | B4 |
| `derive_surface/p2surface.py` | SVI → Surface, Kapitalfläche, Animation | B5 |
| `derive_surface/inference_p2.py` | H1 bis H4, Sensitivitäten | C |
| `derive_surface/figdata_p2.py`, `derive_surface/figures_p2.py` | Abbildungen | D |
| `derive_surface/p2cli.py`, `derive_surface/__main__.py` | CLI `python3 -m derive_surface p2 …` | Orchestrator nach A |
| `scripts/p2_build.py`, `scripts/p2_wordcount.py`, `scripts/p2_zahlenblatt.py`, `scripts/p2_figure_check.py`, `scripts/p2_number_check.py` | Prüfkette | C, D, E |
| `paper2/main.tex`, `paper2/refs.bib`, `paper2/figures/` | Manuskript | E |
| `docs/paper2/ZAHLENBLATT.md`, `ABBILDUNGEN.md`, `VALIDIERUNG.md`, `DATENSTAND.md`, `AUDIT.md` | Dokumentation | B–F |

---

## Stufe A: Grundlagen (parallel, disjunkte Dateien)

### Task A1: Chain-Client und Feed-Historie

**Files:** Create `derive_surface/p2chain.py`, `derive_surface/p2feeds.py`, `tests/test_p2_chain.py`, `tests/test_p2_feeds.py`, `tests/fixtures/p2/` (echte Logs als JSON).

**Interfaces:**
- Consumes: `derive_surface.p2types.MarketState`, `ExpiryState`; `derive_surface.chainfeeds.svi_vol`, `load_feed`-Muster; SVI-Historie `data/p1/volfeed/{CCY}_svi_YYYY-MM.parquet` (Spalten `block, block_ts, log_index, expiry, feed_ts, svi_a, svi_b, svi_rho, svi_m, svi_sigma, svi_fwd, svi_ref_tau, confidence`).
- Produces:
  - `p2chain.block_at_ts(ts: int) -> int`, `p2chain.ts_at_block(block: int) -> int` (Formel aus Global Constraints).
  - `p2chain.Rpc(url=..., rate=2.0, log_path=...)` mit `.call(to, data, block) -> bytes`, `.logs(address, topic0, lo, hi) -> list[dict]` (adaptive Fenster, Limit 10 000 Logs).
  - `p2feeds.FEEDS[ccy]` = dict mit Adressen `spot`, `forward`, `vol`, `rate_pm2`, `rate_pm`, `perp` (aus `deploy.json`/`addresses_head.json`; HYPE-Adressen aus der Chain).
  - `p2feeds.sync(ccy, kind, to_block)` lädt `SpotPriceUpdated`, `ForwardDataUpdated`, `RateUpdated` (PM2-Rate-Feed) und den Perp-Preis-Feed stückweise nach `data/p2/feeds/raw/{ccy}/{kind}/`, `p2feeds.compact(ccy, kind)` schreibt `data/p2/feeds/{ccy}_{kind}.parquet` mit Spalten `block, block_ts, log_index, expiry, value, confidence, feed_ts` (spot/perp: `expiry = 0`, `value` = Preis; forward: `value` = `fwdSpotDifference`; rate: `value` = Zins als float).
  - `p2feeds.FeedHistory(ccy)` mit `.state_at(ts: int, expiries: list[int]) -> MarketState` (je Feed der letzte Wert mit `block_ts ≤ ts`; Forward = Spot + `fwdSpotDifference` exakt wie `LyraForwardFeed.getForwardPricePortions`; SVI aus `volfeed`; Zins aus `rate_pm2`, 0 wenn kein Wert) und `.bulk(ts: np.ndarray, expiry: np.ndarray, strike: np.ndarray) -> pd.DataFrame` mit Spalten `spot, forward, sigma, rate, svi_fwd, vol_conf, fwd_conf, spot_age, fwd_age, vol_age, rate_age` (vektorisiert über `np.searchsorted` je Verfall).

- [ ] **Step 1:** Ereignis-ABIs aus `data/p2/v2-core/src/interfaces/ILyraSpotFeed.sol:17`, `ILyraForwardFeed.sol:26`, `ILyraRateFeed.sol:17` und dem Perp-Feed lesen; Topics per keccak der Signaturen berechnen und im Code als Konstanten mit Kommentar ablegen. Echte Beispiel-Logs je Art mit einem einzelnen `eth_getLogs` holen und als Fixture speichern.
- [ ] **Step 2: Failing tests:** Dekodierung jedes Fixture-Logs auf die erwarteten Felder; `block_at_ts(1_704_931_201) == 2_454_793`; `state_at` auf einer synthetischen Mini-Historie (drei Spot-Werte, zwei Forward-Werte, eine SVI-Kurve) liefert den jeweils letzten Wert ≤ ts und Forward = Spot + Differenz; `bulk` stimmt Zeile für Zeile mit `state_at` überein.
- [ ] **Step 3:** Implementieren, Tests grün.
- [ ] **Step 4: Daten laden** für BTC, ETH, HYPE von Block 843 000 (BTC/ETH) bzw. dem HYPE-Deploy bis Block 44 812 000 (17.09.2026 12:00 UTC + Puffer): spot, forward, rate_pm2 (ab PM2-Deploy), perp. Wiederaufnehmbar. Ergebnis und Zeilenzahlen in `docs/paper2/DATENSTAND.md` (Abschnitt Feeds).
- [ ] **Step 5: Gegenprobe:** an 10 Zufallsblöcken je Basiswert `getSpot`/`getForwardPrice`/`getInterestRate` per `eth_call` gegen `state_at` (Abweichung 0 erwartet); Ergebnis in `DATENSTAND.md`.

### Task A2: Parameter-Zeitlinien

**Files:** Create `derive_surface/p2params.py`, `tests/test_p2_params.py`, `results/p2/params/{ccy}_{mgr}.json` (mgr ∈ `sm`, `pm`, `pm2`).

**Interfaces:**
- Consumes: `p2chain.Rpc` (Task A1; bis dahin eigener Minimal-Client erlaubt, danach umstellen), Ereignislisten `data/p2/kontext/margin-historie/events.json`, `data/p2/semantik_20260924/code-pm2/param_timeline_btc.json`, Getter-Signaturen aus v2-core (`IPMRMLib_2`, `IPMRMLib`, `IStandardManager`, `PMRM_2`, `PMRM`).
- Produces: JSON-Liste `[{"from_block": int, "from_ts": int, "source": str, "params": {...}}]` je (Basiswert, Manager), aufsteigend. **Schlüssel = Solidity-Strukturnamen und Feldnamen exakt wie in v2-core**, Werte als float (1e18-skaliert zurückgerechnet), z. B. PM2: `{"VolShockParameters": {...}, "MarginParameters": {...}, "BasisContingencyParameters": {...}, "OtherContingencyParameters": {...}, "SkewShockParameters": {...}, "CollateralParameters": {...}, "scenarios": [{"spotShock": .., "volShock": 0|1|2, "dampeningFactor": ..}, ...], "maxExpiries": int}`; SM (Markt-ID je Basiswert: BTC 2, ETH 1, HYPE 48): `{"OptionMarginParams": {...}, "PerpMarginRequirements": {...}, "BaseMarginParams": {...}, "OracleContingencyParams": {...}, "DepegParams": {...}}`; Legacy-PM wie `IPMRMLib`-Strukturen plus `scenarios`. `p2params.Timeline(ccy, mgr).at(ts) -> dict` und `.changes() -> list[int]`.

- [ ] **Step 1: Failing tests:** `Timeline.at` wählt den letzten Eintrag mit `from_ts ≤ ts`; vor dem ersten Eintrag `KeyError`; JSON-Rundreise erhält alle Schlüssel.
- [ ] **Step 2:** Implementieren, Tests grün.
- [ ] **Step 3: Laden:** je Ereignisblock (PM2: alle `*ParamsUpdated`, `ScenariosUpdated`, `MaxExpiriesUpdated` der Standard-Lib und des Managers; SM: `OptionMarginParamsSet` usw. je Markt; Legacy-PM: Monatsproben der Getter plus Bisektion wie in `data/p2/kontext/margin-historie/oi_legacy.py`) alle Getter per historischem `eth_call` am Ereignisblock lesen. Achtung: Beim SM-Event `OptionMarginParamsSet` sind unpairedIM/MM im Event vertauscht, deshalb immer den Getter lesen, nie das Event.
- [ ] **Step 4:** Tabelle der Änderungen je Basiswert und Manager in `docs/paper2/DATENSTAND.md` (Abschnitt Parameter), dazu die monatlichen Manager-Anteile am OI aus `oi_legacy.json` nach `results/p2/manager_oi_share.csv` (Spalten `month, ccy, sm, pm, pm2`).

### Task A3: Nachbau PM2

**Files:** Create `derive_surface/margin_pm2.py`, `tests/test_p2_margin_pm2.py`, `tests/fixtures/p2/pm2_chain_cases.json`.

**Interfaces:**
- Consumes: `p2types.Book`, `MarketState`; Parameter-Dict im Schema aus Task A2; Referenz-Implementierungen `data/p2/semantik_20260924/verify-konvex/pm2v.py` (vektorisiert, chain-exakt) und `code-pm2/pm2_replica.py`; Solidity `data/p2/v2-core/src/risk-managers/PMRMLib_2.sol`, `PMRM_2.sol`.
- Produces:
  - `margin_pm2.net_margin(book, state, params, is_initial=True) -> tuple[float, float]` = (net, mtm), net = cash + V − R, mtm = cash + V.
  - `margin_pm2.single(arrays: dict, params, is_initial=True) -> tuple[np.ndarray, np.ndarray]` für viele Einzelkontrakt-Bücher; `arrays` hat die Schlüssel `spot, forward, sigma, tau, rate, strike, is_call, amount, vol_conf, fwd_conf, spot_conf` (gleich lange 1-D-Arrays). Vol-Schocks wirken multiplikativ auf `sigma` am Strike.
  - `margin_pm2.requirement(book, state, params, is_initial=True) -> float` = mtm − net.

- [ ] **Step 1: Failing tests:** alle 139 Referenzfälle `data/p2/v2-core/test/risk-managers/unit-tests/PMRM_2/portfolio_cases/*.json` (Relativfehler ≤ 1e-9 gegen die im Fall erwarteten IM/MM; Einlese-Logik wie in `pm2_replica.py`); mindestens 10 Chain-Fälle mit echten Feeds, Parametern und `eth_call`-Ergebnis als Fixture (aus `data/p2/semantik_20260924/verify-konvex/rep_vs_chain.json` bzw. neu erzeugt), Toleranz 1e-6 USD; `single` gleich `net_margin` für 200 Zufallskontrakte.
- [ ] **Step 2:** Port von `pm2v.py` in das Schema der Parameter-Dicts; Tests grün.

### Task A4: Nachbau SM und Legacy-PM

**Files:** Create `derive_surface/margin_sm.py`, `derive_surface/margin_pm.py`, `tests/test_p2_margin_sm.py`, `tests/test_p2_margin_pm.py`, Fixtures unter `tests/fixtures/p2/`.

**Interfaces:**
- Consumes: wie A3; Referenzen `data/p2/semantik_20260924/verify-widerspruch/engine.py`, `code-sm/sm_model.py`, Solidity `StandardManager.sol`, `PMRMLib.sol`, `PMRM.sol`; Referenzfälle `data/p2/v2-core/test/risk-managers/unit-tests/StandardManager/test-cases.json`, `test-cases-portfolio.json`, `.../PMRM/test-cases-portfolio-pm.json`, `.../PMRM/utils/*.json`.
- Produces: `margin_sm.net_margin(book, state, params, is_initial=True)`, `margin_sm.single(arrays, params, is_initial=True)`, `margin_pm.net_margin(...)`, `margin_pm.single(...)` mit derselben Signatur wie A3. SM rechnet den Options-MtM undiskontiert (Black-76, D = 1); Legacy-PM ebenfalls ohne Diskont.

- [ ] **Step 1: Failing tests:** SM-Referenzfälle aus v2-core (IM und MM), Legacy-PM-Referenzfälle, je mindestens 10 Chain-Fälle mit `eth_call` (`SRM.getIsolatedMargin`, `getMarginAndMarkToMarket` des Legacy-PM mit Lib-Aufruf wie in `data/p2/semantik_20260924/code-pm2/oracle_legacy.py`), `single` gleich `net_margin`.
- [ ] **Step 2:** Implementieren, Tests grün. SM: isoliert, Max-Loss je Verfall am Gitter {0} ∪ Strikes plus unpaired-Calls, `max(I_e, L_e)`, Perp, Basis; Legacy-PM: Szenarien ±Spot × Vol, Kontingenzen, `imFactor` auf minSPAN.

### Task A5: Maker-Bestände

**Files:** Create `derive_surface/books.py` (Teil 1), `tests/test_p2_books.py`, `data/p2/books/snapshots.parquet`.

**Interfaces:**
- Consumes: `p2chain.Rpc` (bis A1 fertig eigener Minimal-Client), `data/p1/derived/markouts.parquet` (Spalten `maker_sub`, `ts`, …), `data/p1/tape/{CCY}_options_full.parquet`, v2-core `SubAccounts.sol` (`getAccountBalances`, `manager`), `OptionEncoding.sol` (SubId-Dekodierung).
- Produces:
  - `books.top_maker_subaccounts(n=10) -> list[int]` (meiste Maker-Fills in der Stichprobe von Paper 1).
  - `books.decode_option_subid(sub_id: int) -> tuple[int, float, bool]` (expiry, strike, is_call) exakt wie `OptionEncoding`.
  - `books.snapshot(rpc, subaccount: int, block: int) -> list[dict]` mit `asset, sub_id, balance, kind ∈ {option, perp, cash, base}, ccy, expiry, strike, is_call` sowie `manager`.
  - `data/p2/books/snapshots.parquet` mit Spalten `subaccount, day, block, manager, asset, sub_id, kind, ccy, expiry, strike, is_call, amount` für die zehn Subaccounts, jeden UTC-Tag vom 11.01.2024 bis 17.09.2026 (erster Block des Tages).
  - `books.book_at(snapshot_rows, tape_rows, ts) -> dict[ccy, Book]` (Tagesbeginn plus Fills des Tages vor ts, verfallene Optionen entfernt, Perps mit Einstand = None).

- [ ] **Step 1: Failing tests:** SubId-Dekodierung an drei echten Instrumenten (aus dem Tape: Instrumentname ↔ `sub_id` der Positions-API oder Chain); `book_at` auf synthetischen Daten (Tagesbestand + zwei Fills, einer davon Taker-Zeile, ein verfallener Leg).
- [ ] **Step 2:** Implementieren, Tests grün.
- [ ] **Step 3: Laden** der Snapshots (etwa 10 × 980 Tage = 9 800 Aufrufe plus `manager`), wiederaufnehmbar; Konten ohne Bestand an einem Tag erzeugen keine Zeilen, der Manager wird trotzdem gespeichert (`kind = "none"`).
- [ ] **Step 4:** Abgleich an 20 Zufalls-Maker-Tagen: Bestand Tagesbeginn + Fills des Tages = Bestand des nächsten Tages (Abweichungen = Transfers, Liquidationen, Settlement) als Quote in `DATENSTAND.md`.

**Orchestrator nach Stufe A:** CLI `p2` mit Unterbefehlen verdrahten, Suite grün, Commit.

---

## Stufe B: Messung (erst nach bestandener Validierung B1)

### Task B1: Validierung gegen eth_call

**Files:** Create `derive_surface/p2validate.py`, `tests/test_p2_validate.py`, `results/p2/validation.csv`, `docs/paper2/VALIDIERUNG.md`.

**Interfaces:** Consumes A1 bis A5. Produces `validation.csv` mit `ccy, manager, kind ∈ {single, book}, block, ts, K_replica, K_chain, abs_err, rel_err, is_initial`.

- [ ] Je Basiswert und verfügbarem Manager mindestens 48 Zufallsblöcke im jeweiligen Fenster (Seed 20260924), je Block ein Zufallskontrakt aus den aktiven Verfällen mit Vol-Push in den letzten 20 min (Strike aus dem Tape des Tages), Seite zufällig; Kapital K per Nachbau (`FeedHistory.state_at` + Parameter) gegen `eth_call` an der Lib bzw. am Manager mit denselben Positionen (Chain-Orakel wie `data/p2/semantik_20260924/code-pm2/oracle.py`, SM über `getIsolatedMargin`, Legacy-PM wie `oracle_legacy.py`). Dazu 20 Maker-Tage (Bücher) unter PM2.
- [ ] Schwelle aus der Präregistrierung prüfen (Median |rel| < 0,1 %, p95 < 1 %). Ergebnis in `VALIDIERUNG.md`. Bei Verfehlen Ursache suchen und beheben; wenn nicht behebbar, datierten Nachtrag in der Präregistrierung schreiben, bevor B2 startet.

### Task B2: Kapital je Fill

**Files:** Create `derive_surface/capital.py`, `tests/test_p2_capital.py`, `data/p2/derived/capital.parquet`.

**Interfaces:** Consumes `markouts.parquet` (Spalten `trade_id` bzw. Fill-Schlüssel, `ts`, `currency`, `expiry`, `strike`, `option_type`, `price`, `amount`, `maker_side`, `index_price`, `delta_bucket`, `tenor_bucket`, `abs_delta_pct`), `FeedHistory.bulk`, `Timeline.at`, `margin_*.single`. Produces `capital.parquet` mit Fill-Schlüssel und `K_sm, K_pm, K_pm2, K_sm_mm, K_pm_mm, K_pm2_mm` (NaN ausserhalb des Manager-Fensters), `spot, forward, sigma, rate, vol_age, fwd_age`.

- [ ] Failing tests: K = p·q − net für drei handgerechnete Fälle je Manager (SM-Short-Call, SM-Long = Prämie, PM2 gegen `net_margin`); Fenstergrenzen (PM2 NaN vor 12.06.2025 23:00 UTC, HYPE-SM NaN vor 11.11.2025, HYPE-PM immer NaN).
- [ ] Implementieren (gruppiert nach Basiswert und Parameterregime, vektorisiert), Lauf über alle 603 940 Fills, Zeilenzahl und NaN-Anteile in `DATENSTAND.md`.

### Task B3: Grenzkosten und Netting-Wert

**Files:** Modify `derive_surface/books.py` (Teil 2), `tests/test_p2_books.py`; Create `data/p2/derived/marginal.parquet`, `data/p2/derived/maker_days.parquet`.

**Interfaces:** Consumes A1 bis A5 und B2. Produces `marginal.parquet` (`fill_key, subaccount_hash, ts, ccy, manager, dK, K_single_pm2, ratio`) für die präregistrierte Stichprobe (Konto unter PM2 zu Tagesbeginn, PM2-Fenster, Zufallsauswahl 20 000, Seed 20260924) und `maker_days.parquet` (`subaccount_hash, day, K_sm, K_pm, K_pm2, K_*_mm, n_legs, gross_contracts, manager`).

- [ ] Failing tests: ΔK = p·q_neu + net(vor) − net(nach) auf synthetischem Buch; Maker-Tag mit zwei Basiswerten rechnet PM2 je Basiswert getrennt; Beine ohne offenes PM2-Fenster fallen weg.
- [ ] Zusätzlich (Sensitivität Zeitnormierung): empirische Haltedauer je Zelle aus den Tagesbeständen (FIFO-Glattstellung der Maker-Fills der zehn Subaccounts, Median je Zelle) nach `results/p2/holding_time.csv`.
- [ ] Implementieren und laufen lassen.

### Task B4: Ereignisse und Dosen (H4)

**Files:** Create `derive_surface/p2events.py`, `tests/test_p2_events.py`, `results/p2/events.csv`, `data/p2/derived/h4_panel.parquet`.

**Interfaces:** Consumes `Timeline.changes`, `capital.parquet`, `markouts.parquet` (Halbspread `hs` bzw. aus `inference_p1.analysis_frame`), `FeedHistory`, `margin_*.single`. Produces `events.csv` (`ccy, manager, event_ts, kinds, max_abs_dose, kept`) und das Panel (`fill_key, ccy, cell, event_id, post, dose, y_hs_bp, day`).

- [ ] Failing tests: Zusammenfassen gleicher Tage; Dosis log(K_nach/K_vor) auf synthetischem Beispiel; Fensterlogik ohne Ereignistag; Ausschluss max |Dosis| < 1 %.
- [ ] Implementieren und laufen lassen.

### Task B5: Oberfläche und Kapitalfläche

**Files:** Create `derive_surface/p2surface.py`, `tests/test_p2_surface.py`.

**Interfaces:** Consumes `surface.py` (`Surface`, `greeks_grid`), `animate.py` (`Renderer`), `FeedHistory.state_at`, `margin_*.single`, Prototyp `data/p2/kontext/oberflaeche/proto_chain_surface.py`. Produces `p2surface.chain_surface(ccy, ts) -> Surface` (SVI-Kurven eines Zeitpunkts, Adapter wie `ChainSmile`), `p2surface.capital_grid(ccy, ts, manager, side) -> pd.DataFrame` (call-Δ × Laufzeit-Gitter mit `iv, strike, K_per_forward_bp`), `p2surface.render_frame(...)` und `p2surface.animate(ccy, days, out)` (GIF/MP4 wie `docs/media`, Palette aus `figstyle`).

- [ ] Failing tests: `chain_surface` gibt an den Knoten die `svi_vol`-Werte zurück; `capital_grid` Kapital SM-Short = a·S nach Formel; Delta-Selbstkonsistenz.
- [ ] `p2surface.reference_book_series(ccy) -> pd.DataFrame`: Kapital eines festen Referenzbuchs (Short-Straddle ATM mit 30 Tagen Laufzeit, 1 Kontrakt je Bein, konstruiert an jedem Tag um 08:00 UTC aus dem Verfall, der 30 Tagen am nächsten liegt) je Tag unter SM, Legacy-PM und PM2, dazu dasselbe Buch mit den Parametern des Vortags (reiner Parametereffekt) nach `results/p2/reference_book.csv`.
- [ ] Implementieren.

**Orchestrator nach Stufe B:** Suite grün, Commit.

---

## Stufe C: Inferenz

### Task C1: H1 bis H4 und Sensitivitäten

**Files:** Create `derive_surface/inference_p2.py`, `tests/test_p2_inference.py`, `scripts/p2_zahlenblatt.py`, `results/p2/h1_cells.csv`, `h1.json`, `h2.json`, `h3.json`, `h4.json`, `h4_placebo.csv`, `sensitivity.json`, `summary.json`, `docs/paper2/ZAHLENBLATT.md`.

**Interfaces:** Consumes `capital.parquet`, `marginal.parquet`, `maker_days.parquet`, `h4_panel.parquet`, `inference_p1.analysis_frame` und die Bootstrap-Helfer aus `inference_p1` (`cluster_mean_ci`, `wild_cluster_mean_p`). Produces die genannten Dateien; jedes Urteil als `{"stat": .., "lo": .., "hi": .., "rejected": bool, "rule": ".."}`.

- [ ] Failing tests: Zell-Verhältnis der Summen; ρ-Bootstrap auf synthetischen Daten mit bekanntem ρ; Median-Bootstrap; DiD-Schätzer gegen Brute-Force-OLS mit Fixeffekten auf Mini-Panel; Wild-Bootstrap-p für bekanntes Signal < 0,05 und für Nullsignal gleichverteilt (grober Test).
- [ ] Implementieren und laufen lassen (B = 9 999, Seed 20260924). Exploratives getrennt in `sensitivity.json`: Karten unter SM und Legacy-PM, MM, API-Semantik (2 %, nur heute), Zeitnormierungen, Werte je Basiswert.
- [ ] `scripts/p2_zahlenblatt.py` schreibt `docs/paper2/ZAHLENBLATT.md` aus `results/p2` (Stichtag aus den Daten, nicht fest eingetragen).

---

## Stufe D: Abbildungen

### Task D1: Entwürfe, Jury, Bau

**Files:** Create `derive_surface/figdata_p2.py`, `derive_surface/figures_p2.py`, `tests/test_p2_figures.py`, `scripts/p2_figure_check.py`, `paper2/figures/*.pdf|png`, `docs/paper2/ABBILDUNGEN.md`, `docs/paper2/ABBILDUNGSWAHL.md`, `docs/media/p2_*.gif`.

- [ ] Drei unabhängige Entwurfssätze (Mechanismus, Empirie, Praktiker) für die Slots der Spec §6, Jury aus Referee (Nachrechnung) und Gestaltung (8 pt, Graustufen), Lückencheck; Wahl in `ABBILDUNGSWAHL.md`.
- [ ] Registry `FIGURES` wie `figures_p1.py`; jede Zahl einer Abbildung als Tabelle unter `results/p2/fig_*.csv`; keine Schrift unter 7 pt (Test prüft `fontsize` aller Textobjekte ≥ 7); Graustufen-Test (Luminanz-Abstand der Kategorien).
- [ ] `p2_figure_check.py` vergleicht Abbildungszahlen gegen `results/p2` (nicht gegen sich selbst).
- [ ] Oberfläche T1 und Animation über `p2surface`; Social-Karten 1600×900.

---

## Stufe E: Manuskript

### Task E1: Text, Literatur, Bau

**Files:** Create `paper2/main.tex`, `paper2/refs.bib`, `scripts/p2_build.py`, `scripts/p2_wordcount.py`, `scripts/p2_number_check.py`, `docs/paper2/MANUSKRIPT.md`.

- [ ] Gliederung und Wortbudget aus Spec §7; `p2_wordcount.py` mit Budget je Abschnitt (±10 %).
- [ ] Literatur: nur Quellen mit geprüfter DOI oder Verlagsseite (ein Web-Agent), Liste mit Prüfvermerk in `MANUSKRIPT.md`.
- [ ] `p2_number_check.py`: jede Zahl im Text muss in `results/p2` vorkommen (Rundung erlaubt, Liste der Ausnahmen explizit).
- [ ] Bau mit tectonic, Prüfung Log, Overfull-Boxen, Budget. Präregistrierungs-Commit `1d13227` im Text nennen.

---

## Stufe F: Audit

### Task F1: Audit über das gesamte Paper

- [ ] Parallel: Zahlen (Text ↔ results ↔ Rohdaten), Code-Review (Korrektheit der Nachbauten und der Inferenz), Präregistrierungstreue (jede Abweichung als Nachtrag?), Abbildungen (Regeln, Lesbarkeit), Literatur (DOIs), Sprache (keine Gedankenstriche, Budget). Befunde nach Schwere in `docs/paper2/AUDIT.md`, Korrekturen einarbeiten, erneut prüfen.
