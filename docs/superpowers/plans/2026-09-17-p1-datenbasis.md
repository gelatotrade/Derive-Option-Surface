# Paper 1, Plan 1: Datenbasis und Gegenparteiklassen

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Den vollständigen Options-Tape (alle 20 Felder, beide Zeilen je Fill), die onchain SVI-Historie von BTC/ETH/HYPE und alle Referenzdaten sichern, Maker- und Taker-Zeilen zu Fills paaren und jedem Fill eine Gegenparteiklasse geben, nachdem die Hypothesen präregistriert sind.

**Architecture:** Vier fokussierte Module im bestehenden Paket `derive_surface` (fulltape, chainfeeds, refdata, classify), ein CLI-Einstieg `python3 -m derive_surface p1 …`, ein Prüfskript für die Vol-Feeds. Alle Downloads sind wiederaufnehmbar und schreiben Stück für Stück auf Platte; alle Tests laufen offline gegen Fake-Clients.

**Tech Stack:** Python 3.9.6 (System), numpy 2.0, pandas 2.3, pyarrow 21, requests; pytest. Keine neuen Abhängigkeiten.

**Spec:** `docs/superpowers/specs/2026-09-17-adverse-selection-design.md` (insbesondere §2a mit den Befunden der Datenprobe).

## Global Constraints

- Python 3.9.6: jede neue Datei beginnt mit `from __future__ import annotations`; kein `match`, kein `zip(strict=…)`, keine `X | Y`-Typen ausserhalb von Annotationen.
- Keine neuen Abhängigkeiten über `requirements.txt` hinaus.
- Tests offline, kein Netzwerk; `python3 -m pytest -q` muss vor jedem Commit grün sein (bisher 28 Tests).
- Aufrufe aus dem Repo-Wurzelverzeichnis `~/Documents/Papers/Working Papers/Derive_Options/Derive-Option-Surface`; kein `pip install -e` (pyproject verlangt ≥ 3.10).
- Daten nur unter `data/p1/` (git-ignoriert). Nichts löschen, was nicht in dieser Sitzung erzeugt wurde.
- Pilot-Stichtag `2026-09-17T12:00:00+00:00`; finaler Stichtag `2026-09-30T08:00:00+00:00` (eigener Lauf später). Vor dem Commit der Präregistrierung wird **keine** Markout-Zahl gerechnet.
- Code, Kommentare, Commit-Nachrichten englisch; Dokumente unter `docs/paper1/` deutsch mit Umlauten.
- Commits nur lokal auf Branch `paper1-adverse-selection`; kein Push ohne Freigabe des Autors. Commit-Trailer: `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- Vol-Feed-Adressen (kleingeschrieben): BTC `0x388341d9e5a7d7d5accd738b2a31b0622e0c1b87`, ETH `0xb27cb6b08e6c298c8634d73d5f6649665e90d160`, HYPE `0x481916590863053ea2d8f21b64ee9429820512d1`; Topic `VolDataUpdated` = `0x0b6ec9c174360425894fd5ff56d14f3450d70f2c9cde3a25983d652a72b84606`.
- Plattenplatz: 15 GB frei. Kein Rohformat der Chain-Logs speichern, nur dekodierte Parquet-Stücke.

## Dateien

| Datei | Verantwortung |
|---|---|
| `derive_surface/fulltape.py` | Options-Tape in Einzelseiten-Fenstern laden, Manifest, zu Parquet verdichten |
| `derive_surface/chainfeeds.py` | RPC-Client, adaptive `eth_getLogs`, Dekodierung `VolDataUpdated`, Stück-Sync, Verdichtung, SVI-Vol |
| `derive_surface/refdata.py` | Settlement-Preise, Liquidationen, Maker-Programme/Scores, Vaults, Instrument-Gebühren, Funding |
| `derive_surface/classify.py` | Fills paaren, Wallet-Monats-Kennzahlen, Klassen-Mengen, Klassifikation, Orchestrierung |
| `derive_surface/p1cli.py` | Unterbefehle `tape`, `volfeed`, `compact`, `ref`, `fills` |
| `derive_surface/__main__.py` | Weiterleitung von `p1` an `p1cli` |
| `scripts/p1_check_feeds.py` | Feed-Kontinuität (Stichproben) und Gegenprobe SVI gegen Live-Mark |
| `tests/test_p1_fulltape.py`, `tests/test_p1_chainfeeds.py`, `tests/test_p1_refdata.py`, `tests/test_p1_classify.py`, `tests/test_p1_cli.py` | Offline-Tests |
| `tests/fixtures/vol_log_btc_44814062.json` | echter Log vom 17.09.2026 (liegt bereits vor) |
| `docs/paper1/PRAEREGISTRIERUNG.md` | Hypothesen, Tests, Ausschlüsse, festgelegt vor jeder Markout-Zahl |
| `docs/paper1/meta/vault_wallets.csv` | kuratierte Vault-Wallets mit Quelle |
| `docs/paper1/DATENSTAND.md` | Zählungen und Prüfungen nach den Läufen |
| `docs/paper1/feed_check.md` | Ausgabe von `scripts/p1_check_feeds.py` |

---

### Task 0: Branch, Präregistrierung, Ignore-Regel

**Files:**
- Create: `docs/paper1/PRAEREGISTRIERUNG.md`
- Modify: `.gitignore` (Zeile `data/p1/` ist bereits angehängt)
- Add: `docs/superpowers/specs/2026-09-17-adverse-selection-design.md`, dieser Plan, `tests/fixtures/vol_log_btc_44814062.json`

**Interfaces:** keine Code-Schnittstellen. Legt die Definitionen fest, die Plan 2 exakt umsetzen muss.

- [ ] **Step 1: Präregistrierung schreiben**

Datei `docs/paper1/PRAEREGISTRIERUNG.md` mit folgendem Inhalt:

```markdown
# Präregistrierung Paper 1: Adverse Selection auf Derive

Festgelegt am 17.09.2026, bevor eine Markout-Zahl berechnet wurde. Der Git-Commit dieser Datei ist der Zeitstempel. Änderungen danach nur als datierter Nachtrag am Ende, nie durch Überschreiben.

## Stichprobe
- Fills (Paar aus Maker- und Taker-Zeile derselben `trade_id`) auf BTC-, ETH- und HYPE-Optionen mit Taker-Zeitstempel in [2024-01-11 00:00, 2026-09-30 08:00] UTC.
- Ausschlüsse: `tx_status` ≠ `settled`; Paare mit abweichendem Preis, abweichender Menge oder gleicher Richtung; Fills in den letzten 30 Minuten vor Verfall; Fills ohne Mark-Pfad (b) zum Fill-Zeitpunkt.
- Die neun übrigen Underlyings nur deskriptiv im Anhang.

## Markout
- Maker-Richtung s = +1, wenn der Maker kauft, sonst −1. MO_τ = s · (M(t+τ) − P) in USDC je Kontrakt; negativ = Verlust des Makers.
- Primärer Mark-Pfad (b): Black-76-Preis aus der zuletzt vor t+τ onchain gepushten SVI-Kurve des Verfalls (Formel wie `SVI.sol`, vol = √(w/SVI_refTau)), Forward aus der gleichen Kurve (`SVI_fwd`), Diskontfaktor 1.
- Robustheit: (a) `mark_price` des nächsten Fills desselben Instruments nach t+τ; (c) Settlement-Auszahlung; (d) Deribit-Mark an Tardis-Monatsersten.
- Einheiten: USDC; delta-neutral MO^Δ_τ = MO_τ − s·Δ(t)·(S(t+τ) − S(t)) mit Δ aus Pfad (b) und S = `index_price` des Fills bzw. `SVI_fwd` zum Zeitpunkt t+τ; Vol-Punkte MO^σ_τ = s·(IV_(b)(t+τ) − IV_fill(t)).
- Horizonte: 1 min, 5 min, 30 min, 4 h, 24 h, Settlement. **Primärer Horizont 30 min.**
- VRP-Bereinigung des Settlement-Markouts: Abzug des mittleren Settlement-Markouts aller Fills derselben Zelle (Delta-Bucket × Tenor-Bucket × Underlying × Kalendermonat).

## Zellen und Klassen
- |Δ|-Buckets: [0,10), [10,25), [25,40), [40,60), [60,75), [75,90), [90,100]. Tenor: ≤2 d, (2,7], (7,30], (30,90], >90 d.
- Taker-Klasse mit Vorrang: Liquidation (tx_hash einer Liquidationsauktion) > Vault (Wallet in `docs/paper1/meta/vault_wallets.csv`) > RFQ (`rfq_id` gesetzt) > dominanter Maker (Wallet-Monat mit Maker-Anteil ≥ 80 % am eigenen Notional und ≥ 1 % am Maker-Notional des Monats) > MM-Programm (Wallet mit `total_score` > 0 in einer Options-Programm-Epoche, die den Fill enthält) > Grosswallet (Taker-Notional des Monats ≥ 99. Perzentil der Taker-Wallets des Monats) > Sonstige.
- Sweep: ≥ 5 Fills desselben Takers in ≤ 10 s über ≥ 3 Strikes.

## Hypothesen und Ablehnungsregeln
- **H1 Konzentration:** Die 10 Taker-Wallets mit dem grössten aggregierten negativen 30-min-Markout (USDC) tragen mehr als 50 % davon; Fills über dem 90. Perzentil der Grösse und Sweep-Fills haben einen negativeren Markout als die übrigen. Abgelehnt, wenn die obere Grenze des 90-%-Bootstrap-Intervalls (Resampling über Taker-Wallets, B = 9 999) des Top-10-Anteils unter 50 % liegt, oder wenn der Grössen- bzw. Sweep-Koeffizient in der Panel-Regression (FE Instrument × Tag, Cluster Taker-Wallet) nicht negativ mit |t| ≥ 1,96 ist.
- **H2 Vault-Flow uninformiert:** Mittlerer 30-min-Markout (b) der Vault-Taker-Fills ≥ 0 für den Maker. Abgelehnt, wenn das 95-%-Wild-Cluster-Bootstrap-Intervall vollständig unter 0 liegt. Sekundär derselbe Test für den VRP-bereinigten Settlement-Markout.
- **H3 HYPE vor Referenzmarkt:** Der 30-min-Vol-Markout von HYPE war vor der Deribit-Listung der HYPE_USDC-Optionen negativer als danach, relativ zu BTC/ETH (Differenz-in-Differenzen, Cluster Taker-Wallet). Ereignisdatum: erster Handelstag der HYPE_USDC-Optionen auf Deribit laut offizieller Ankündigung; ist sie nicht auffindbar, der erste Tag mit HYPE_USDC-Optionsdaten bei Tardis. Abgelehnt, wenn der DiD-Koeffizient nicht mit |t| ≥ 1,96 das erwartete Vorzeichen hat oder wenn er unter 100 zufälligen Placebo-Daten (gleiche Fensterlänge, vor der Listung) nicht im äussersten 5-%-Bereich liegt.
- **H4 Zellenabhängiger Netto-Edge:** Netto-Edge NE_30min = Halbspread + MO_30min − Maker-Gebühr + Maker-Rebate − Hedge-Kosten ist in weniger als der Hälfte der besetzten Zellen (≥ 200 Fills) positiv, und in der Zelle BTC/ETH × [40,60) × ≤2 d negativ. Abgelehnt, wenn ≥ 50 % der besetzten Zellen ein positives 90-%-Bootstrap-Intervall haben oder die genannte Zelle ein positives Intervall hat.

## Inferenz
- Wild-Cluster-Bootstrap (Rademacher) mit Cluster Taker-Wallet, B = 9 999, Seed 20260917, Kleinstichprobenkorrektur G/(G−1), p = (1 + #)/(B + 1).
- Alles andere (Tageszeit, VPIN, Inventar-konditionierter Markout, Fill-Finalität) ist explorativ und wird so gekennzeichnet.

## Datenstand vor diesem Commit
- Pilotdaten bis 17.09.2026 12:00 UTC dürfen zum Bau der Pipeline geladen, gepaart und klassifiziert werden. Markouts werden erst nach diesem Commit berechnet.
```

- [ ] **Step 2: Tests laufen lassen (Ausgangslage)**

Run: `python3 -m pytest -q`
Expected: `28 passed`

- [ ] **Step 3: Commit**

```bash
git add .gitignore docs/superpowers/specs/2026-09-17-adverse-selection-design.md docs/superpowers/plans/2026-09-17-p1-datenbasis.md docs/paper1/PRAEREGISTRIERUNG.md tests/fixtures/vol_log_btc_44814062.json
git commit -m "paper1: spec, plan, pre-registration (before any markout is computed)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 1: `fulltape.py` — Options-Tape in Einzelseiten-Fenstern

**Files:**
- Create: `derive_surface/fulltape.py`
- Test: `tests/test_p1_fulltape.py`

**Interfaces:**
- Consumes: `derive_surface.api.OptionName.parse(name) -> OptionName` (Felder `currency`, `expiry_ts`, `strike`, `option_type`); ein Client mit `call(method: str, **params) -> dict` (wie `DeriveClient`).
- Produces:
  - `PAGE_SIZE: int = 1000`, `DAY_MS: int`, `FIELDS: list[str]`, `NUMERIC: list[str]`, `ROW_KEY = ["trade_id", "liquidity_role", "subaccount_id"]`
  - `window_path(out_dir: Path, lo_ms: int, hi_ms: int) -> Path`
  - `fetch_range(client, lo_ms: int, hi_ms: int, out_dir: Path, instrument_type: str = "option") -> list[tuple[int, int, int]]`
  - `download_tape(client, out_dir: Path, start_ms: int, end_ms: int, *, instrument_type: str = "option", workers: int = 6) -> dict` mit Schlüsseln `instrument_type, from_ms, to_ms, rows_in_windows, api_count, windows, leaves, finished_ms`
  - `condense(out_dir: Path, manifest: dict) -> pd.DataFrame` mit Spalten `FIELDS + ["currency", "expiry", "strike", "option_type"]`
  - `write_tape(df: pd.DataFrame, tape_dir: Path) -> dict` schreibt `<CCY>_options_full.parquet` und `MANIFEST.json`

- [ ] **Step 1: Failing tests schreiben**

`tests/test_p1_fulltape.py`:

```python
from __future__ import annotations

import gzip
import json
import random

import pandas as pd
import pytest

from derive_surface import fulltape


class FakeTape:
    """In-memory get_trade_history: inclusive bounds, pages in a window-specific shuffled order."""

    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def call(self, method, **p):
        assert method == "get_trade_history"
        self.calls += 1
        lo, hi = p["from_timestamp"], p["to_timestamp"]
        sel = sorted((r for r in self.rows if lo <= r["timestamp"] <= hi), key=lambda r: (r["trade_id"], r["liquidity_role"]))
        random.Random(lo * 7 + hi).shuffle(sel)
        ps, page = p["page_size"], p["page"]
        return {"trades": sel[(page - 1) * ps: page * ps], "pagination": {"count": len(sel), "num_pages": max(1, -(-len(sel) // ps))}}


def make_rows(n_fills, t0=1_704_931_200_000, spread_ms=10_000, seed=0, same_ts=False, instrument="BTC-20240126-45000-C"):
    rng = random.Random(seed)
    rows = []
    for i in range(n_fills):
        ts = t0 if same_ts else t0 + rng.randrange(spread_ms)
        base = dict(trade_id=f"t{seed}-{i:05d}", timestamp=ts, instrument_name=instrument, trade_price="100", trade_amount="0.5",
                    mark_price="101", index_price="44000", rfq_id=None, quote_id=None, trade_fee="0.1", expected_rebate="0",
                    extra_fee="0", realized_pnl="0", realized_pnl_excl_fees="0", tx_hash=f"0x{i:064x}", tx_status="settled")
        rows.append({**base, "direction": "buy", "liquidity_role": "maker", "wallet": "0xAAA", "subaccount_id": 1})
        rows.append({**base, "direction": "sell", "liquidity_role": "taker", "wallet": "0xBBB", "subaccount_id": 2})
    return rows


def read_all(out_dir):
    got = []
    for p in out_dir.glob("*.json.gz"):
        with gzip.open(p, "rt") as fh:
            got.extend(json.load(fh)["trades"])
    return got


def test_fetch_range_gets_every_row_once_and_splits(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    rows = make_rows(40)
    leaves = fulltape.fetch_range(FakeTape(rows), 1_704_931_200_000, 1_704_931_200_000 + 10_000, tmp_path)
    assert sum(n for _, _, n in leaves) == 80
    assert all(n <= 5 for _, _, n in leaves)
    got = read_all(tmp_path)
    keys = {(r["trade_id"], r["liquidity_role"], r["subaccount_id"]) for r in got}
    assert len(got) == 80 and len(keys) == 80


def test_single_millisecond_window_is_paged(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    rows = make_rows(8, same_ts=True)
    t = rows[0]["timestamp"]
    leaves = fulltape.fetch_range(FakeTape(rows), t - 1000, t + 1000, tmp_path)
    assert (t, t, 16) in leaves
    doc = json.load(gzip.open(fulltape.window_path(tmp_path, t, t), "rt"))
    assert len(doc["trades"]) == 16


def test_resume_only_recounts_split_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    rows = make_rows(40)
    first = FakeTape(rows)
    leaves = fulltape.fetch_range(first, 1_704_931_200_000, 1_704_931_210_000, tmp_path)
    second = FakeTape(rows)
    again = fulltape.fetch_range(second, 1_704_931_200_000, 1_704_931_210_000, tmp_path)
    assert sorted(again) == sorted(leaves)
    assert second.calls == first.calls - len(leaves)


def test_download_tape_manifest_and_condense(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    day = fulltape.DAY_MS
    t0 = 1_704_931_200_000
    rows = make_rows(20, t0=t0, spread_ms=2 * day, seed=1) + make_rows(3, t0=t0 + 5, seed=2, instrument="HYPE-20240126-77_5-P")
    man = fulltape.download_tape(FakeTape(rows), tmp_path, t0, t0 + 2 * day - 1, workers=2)
    assert man["rows_in_windows"] == man["api_count"] == 46
    assert len(man["leaves"]) == man["windows"]
    df = fulltape.condense(tmp_path, man)
    assert len(df) == 46
    assert list(df.columns) == fulltape.FIELDS + ["currency", "expiry", "strike", "option_type"]
    assert df["timestamp"].dtype == "int64" and df["trade_price"].dtype == "float64"
    assert (df["wallet"] == df["wallet"].str.lower()).all()
    hype = df[df["currency"] == "HYPE"].iloc[0]
    assert hype["strike"] == 77.5 and hype["option_type"] == "P"
    assert hype["expiry"] == 1706256000  # 2024-01-26 08:00 UTC
    files = fulltape.write_tape(df, tmp_path / "tape")
    assert files["BTC_options_full.parquet"]["rows"] == 40
    assert json.loads((tmp_path / "tape" / "MANIFEST.json").read_text())["HYPE_options_full.parquet"]["rows"] == 6
    assert len(pd.read_parquet(tmp_path / "tape" / "HYPE_options_full.parquet")) == 6


def test_condense_rejects_window_with_missing_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    t0 = 1_704_931_200_000
    man = fulltape.download_tape(FakeTape(make_rows(4, t0=t0)), tmp_path, t0, t0 + fulltape.DAY_MS - 1, workers=1)
    a, b, n = next(w for w in man["leaves"] if w[2] > 0)
    path = fulltape.window_path(tmp_path, a, b)
    doc = json.load(gzip.open(path, "rt"))
    doc["trades"] = doc["trades"][:-1]
    with gzip.open(path, "wt") as fh:
        json.dump(doc, fh)
    with pytest.raises(ValueError, match="row count"):
        fulltape.condense(tmp_path, man)
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag prüfen**

Run: `python3 -m pytest -q tests/test_p1_fulltape.py`
Expected: FAIL mit `ImportError: cannot import name 'fulltape'`

- [ ] **Step 3: Implementierung**

`derive_surface/fulltape.py`:

```python
"""Full-field option trade tape: both rows of every fill, fetched in single-page time windows.

Measured against api.lyra.finance on 2026-09-17:

* ``get_trade_history`` returns the rows of a page in no stable chronological order, so walking the
  pages of a large range can skip or repeat rows.  We split every day until each window fits into
  one page and fetch that window exactly once.
* ``from_timestamp`` and ``to_timestamp`` are both inclusive (count[a, m-1] + count[m, b] == count[a, b]).
* Every fill has a maker row and a taker row with the same ``trade_id``; each row carries wallet,
  subaccount_id, rfq_id, fees, rebate and realised PnL.

Window files ``<from>_<to>.json.gz`` are written atomically, so an interrupted download resumes where
it stopped.  The manifest lists the leaf windows of one run; ``condense`` reads exactly those, so
windows of an earlier run with a different end time can never be counted twice.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

import pandas as pd

from .api import OptionName

log = logging.getLogger(__name__)

PAGE_SIZE = 1000
DAY_MS = 86_400_000
FIELDS = [
    "trade_id", "timestamp", "instrument_name", "direction", "liquidity_role", "trade_price", "trade_amount",
    "mark_price", "index_price", "wallet", "subaccount_id", "rfq_id", "quote_id", "trade_fee", "expected_rebate",
    "extra_fee", "realized_pnl", "realized_pnl_excl_fees", "tx_hash", "tx_status",
]
NUMERIC = [
    "trade_price", "trade_amount", "mark_price", "index_price", "trade_fee", "expected_rebate", "extra_fee",
    "realized_pnl", "realized_pnl_excl_fees",
]
ROW_KEY = ["trade_id", "liquidity_role", "subaccount_id"]
Window = Tuple[int, int, int]  # (from_ms, to_ms, rows); both bounds inclusive


def _query(client, lo_ms: int, hi_ms: int, page: int, instrument_type: str) -> dict:
    return client.call(
        "get_trade_history", instrument_type=instrument_type, page=page, page_size=PAGE_SIZE,
        from_timestamp=lo_ms, to_timestamp=hi_ms,
    )


def window_path(out_dir: Path, lo_ms: int, hi_ms: int) -> Path:
    return out_dir / f"{lo_ms}_{hi_ms}.json.gz"


def _write_window(path: Path, lo_ms: int, hi_ms: int, count: int, trades: list) -> None:
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as fh:
        json.dump({"from_ms": lo_ms, "to_ms": hi_ms, "count": count, "fetched_ms": int(time.time() * 1000), "trades": trades}, fh)
    tmp.replace(path)


def _read_window(path: Path) -> dict:
    with gzip.open(path, "rt") as fh:
        return json.load(fh)


def fetch_range(client, lo_ms: int, hi_ms: int, out_dir: Path, instrument_type: str = "option") -> List[Window]:
    """Fetch every row in [lo_ms, hi_ms] into single-page window files and return the leaf windows."""
    leaves: List[Window] = []
    stack = [(lo_ms, hi_ms)]
    while stack:
        a, b = stack.pop()
        path = window_path(out_dir, a, b)
        if path.exists():
            leaves.append((a, b, int(_read_window(path)["count"])))
            continue
        res = _query(client, a, b, 1, instrument_type)
        n = int(res["pagination"]["count"])
        if n > PAGE_SIZE and a < b:
            m = (a + b) // 2
            stack.append((m + 1, b))
            stack.append((a, m))
            continue
        trades = list(res["trades"])
        if n > PAGE_SIZE:  # one millisecond holding more than a page: walk its pages and de-duplicate
            for page in range(2, int(res["pagination"]["num_pages"]) + 1):
                trades.extend(_query(client, a, b, page, instrument_type)["trades"])
            trades = list({(t["trade_id"], t["liquidity_role"], t["subaccount_id"]): t for t in trades}.values())
            if len(trades) != n:
                log.warning("window %d: %d unique rows after paging, API count %d", a, len(trades), n)
        _write_window(path, a, b, n, trades)
        leaves.append((a, b, n))
    return leaves


def download_tape(
    client, out_dir: Path, start_ms: int, end_ms: int, *, instrument_type: str = "option", workers: int = 6
) -> dict:
    """Fetch [start_ms, end_ms] day by day (parallel) and write a manifest listing the leaf windows."""
    out_dir.mkdir(parents=True, exist_ok=True)
    days = [(d, min(d + DAY_MS - 1, end_ms)) for d in range(start_ms, end_ms + 1, DAY_MS)]
    leaves: List[Window] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch_range, client, a, b, out_dir, instrument_type) for a, b in days]
        for i, fut in enumerate(as_completed(futures), 1):
            leaves.extend(fut.result())
            if i % 50 == 0 or i == len(futures):
                log.info("tape %s: %d/%d days, %d rows, %.0f s", instrument_type, i, len(futures),
                         sum(w[2] for w in leaves), time.time() - t0)
    leaves.sort()
    api_count = int(_query(client, start_ms, end_ms, 1, instrument_type)["pagination"]["count"])
    manifest = {
        "instrument_type": instrument_type, "from_ms": start_ms, "to_ms": end_ms,
        "rows_in_windows": sum(w[2] for w in leaves), "api_count": api_count, "windows": len(leaves),
        "leaves": [list(w) for w in leaves], "finished_ms": int(time.time() * 1000),
    }
    (out_dir / f"manifest_{start_ms}_{end_ms}.json").write_text(json.dumps(manifest))
    if manifest["rows_in_windows"] != api_count:
        log.warning("row count mismatch: windows %d vs API %d", manifest["rows_in_windows"], api_count)
    return manifest


def condense(out_dir: Path, manifest: dict) -> pd.DataFrame:
    """All rows of the manifest's windows as one typed frame (both rows of every fill)."""
    frames, bad = [], []
    for a, b, n in manifest["leaves"]:
        trades = _read_window(window_path(out_dir, a, b))["trades"]
        if len(trades) != n:
            bad.append((a, b, n, len(trades)))
        if trades:
            frames.append(pd.DataFrame(trades).reindex(columns=FIELDS))
    if bad:
        raise ValueError(f"{len(bad)} windows whose row count differs from the API count, e.g. {bad[:3]}")
    if not frames:
        return pd.DataFrame(columns=FIELDS + ["currency", "expiry", "strike", "option_type"])
    df = pd.concat(frames, ignore_index=True)
    before = len(df)
    df = df.drop_duplicates(ROW_KEY)
    if len(df) != before:
        log.warning("dropped %d duplicate rows", before - len(df))
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    df["timestamp"] = df["timestamp"].astype("int64")
    df["subaccount_id"] = pd.to_numeric(df["subaccount_id"]).astype("int64")
    df["wallet"] = df["wallet"].str.lower()
    parsed = {name: OptionName.parse(name) for name in df["instrument_name"].unique()}
    df["currency"] = df["instrument_name"].map(lambda n: parsed[n].currency)
    df["expiry"] = df["instrument_name"].map(lambda n: parsed[n].expiry_ts).astype("int64")
    df["strike"] = df["instrument_name"].map(lambda n: parsed[n].strike).astype("float64")
    df["option_type"] = df["instrument_name"].map(lambda n: parsed[n].option_type)
    return df.sort_values(["timestamp", "trade_id", "liquidity_role"]).reset_index(drop=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_tape(df: pd.DataFrame, tape_dir: Path) -> dict:
    """One parquet per underlying plus MANIFEST.json (rows, sha256)."""
    tape_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for ccy, g in df.groupby("currency"):
        path = tape_dir / f"{ccy}_options_full.parquet"
        g.reset_index(drop=True).to_parquet(path, index=False, compression="zstd")
        files[path.name] = {"rows": int(len(g)), "sha256": _sha256(path)}
    (tape_dir / "MANIFEST.json").write_text(json.dumps(files, indent=1, sort_keys=True))
    return files
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q tests/test_p1_fulltape.py`
Expected: `5 passed`

- [ ] **Step 5: Gesamtsuite und Commit**

Run: `python3 -m pytest -q` → Expected: `33 passed`

```bash
git add derive_surface/fulltape.py tests/test_p1_fulltape.py
git commit -m "paper1: full-field option tape in single-page windows

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `chainfeeds.py` — SVI-Historie von der Derive Chain

**Files:**
- Create: `derive_surface/chainfeeds.py`
- Test: `tests/test_p1_chainfeeds.py`
- Uses: `tests/fixtures/vol_log_btc_44814062.json`

**Interfaces:**
- Consumes: nichts aus früheren Tasks.
- Produces:
  - Konstanten `RPC_URL`, `VOL_DATA_UPDATED`, `VOL_FEEDS: dict[str, dict]` (Schlüssel `address`, `from_block`), `CHUNK_BLOCKS = 50_000`, `MAX_WINDOW = 50_000`, `LOG_LIMIT = 10_000`, `COLUMNS`
  - `class RpcError(RuntimeError)` mit Attribut `error: dict` und Property `too_many_logs: bool`
  - `class ChainClient` mit `call(method, params)`, `block_number() -> int`, `block_timestamp(n) -> int`, `get_logs(address: str | None, topic0, from_block, to_block) -> list[dict]`
  - `block_at(client, ts: int, lo: int = 1, hi: int | None = None) -> int`
  - `get_logs_adaptive(client, address, topic0, lo, hi, window=5000) -> tuple[list, int]`
  - `decode_vol_log(entry: dict) -> dict` (Schlüssel `block, log_index, expiry, feed_ts, svi_a, svi_b, svi_rho, svi_m, svi_sigma, svi_fwd, svi_ref_tau, confidence`)
  - `logs_to_frame(entries: list) -> pd.DataFrame`
  - `chunk_path(out_dir, start, end) -> Path`, `feed_chunks(from_block, to_block) -> list[tuple[int, int]]`
  - `sync_feed(client, currency, out_root: Path, to_block: int, *, workers=4, window=5000) -> dict`
  - `load_feed(out_root: Path, currency: str) -> pd.DataFrame`, `compact_feed(out_root, currency, dest_dir) -> dict`
  - `svi_vol(strike, svi_a, svi_b, svi_rho, svi_m, svi_sigma, svi_fwd, svi_ref_tau) -> np.ndarray`
  - `scan_emitters(client, blocks: list[int], span: int = 300) -> pd.DataFrame` (Spalten `sample_block, address, n, fwd, ts`)

- [ ] **Step 1: Failing tests schreiben**

`tests/test_p1_chainfeeds.py`:

```python
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from derive_surface import chainfeeds as cf

FIXTURE = Path(__file__).parent / "fixtures" / "vol_log_btc_44814062.json"


def word(x: int) -> str:
    return (x % (1 << 256)).to_bytes(32, "big").hex()


def make_log(block, idx, expiry, fwd=50_000.0, ts=1_700_000_000, a=0.0001, b=0.01, rho=-0.2, m=-0.005, sig=0.01, tau=0.002):
    vals = [a, b, rho, m, sig, fwd, tau, 0.95]
    data = "0x" + "".join(word(int(round(v * 1e18))) for v in vals) + word(ts)
    return {"address": "0xfeed", "topics": [cf.VOL_DATA_UPDATED, "0x" + word(expiry)], "data": data,
            "blockNumber": hex(block), "logIndex": hex(idx)}


class FakeChain:
    """One log every 10 blocks; refuses ranges longer than max_span blocks with the real -32005 error."""

    def __init__(self, max_span=1000, head=100_000):
        self.max_span, self.head, self.calls = max_span, head, 0

    def get_logs(self, address, topic0, from_block, to_block):
        self.calls += 1
        if to_block - from_block + 1 > self.max_span:
            raise cf.RpcError({"code": -32005, "message": "logs count limit exceeded (10000)"})
        return [make_log(b, 0, 1_800_000_000) for b in range(from_block, to_block + 1) if b % 10 == 0]

    def block_number(self):
        return self.head

    def block_timestamp(self, n):
        return 1_000 + 2 * n


def test_decode_real_log():
    d = cf.decode_vol_log(json.loads(FIXTURE.read_text()))
    assert d["block"] == 44_814_062 and d["expiry"] == 1_789_718_400 and d["feed_ts"] == 1_789_649_694
    assert d["svi_fwd"] == pytest.approx(76735.40114792966, rel=1e-12)
    assert d["svi_rho"] == pytest.approx(-0.21917865955083932, rel=1e-9)
    assert d["svi_a"] == pytest.approx(9.7272545053122e-05, rel=1e-9)
    assert d["svi_ref_tau"] == pytest.approx(0.0021803652968, rel=1e-9)
    assert d["confidence"] == pytest.approx(0.95)


def test_decode_rejects_wrong_payload():
    bad = make_log(1, 0, 1)
    bad["data"] = bad["data"][:-64]
    with pytest.raises(ValueError):
        cf.decode_vol_log(bad)


def test_svi_vol_real_params_atm_is_plausible():
    d = cf.decode_vol_log(json.loads(FIXTURE.read_text()))
    vol = cf.svi_vol(d["svi_fwd"], d["svi_a"], d["svi_b"], d["svi_rho"], d["svi_m"], d["svi_sigma"], d["svi_fwd"], d["svi_ref_tau"])
    assert 0.28 < float(vol) < 0.30


def test_svi_vol_formula_bound_and_cap():
    a, b, rho, m, sig, fwd, tau = 0.01, 0.1, -0.3, 0.02, 0.1, 100.0, 0.5
    K = 110.0
    k = math.log(K / fwd)
    w = a + b * (rho * (k - m) + math.sqrt((k - m) ** 2 + sig ** 2))
    assert float(cf.svi_vol(K, a, b, rho, m, sig, fwd, tau)) == pytest.approx(math.sqrt(w / tau), rel=1e-12)
    bound = 4 * math.sqrt(a + b * sig)
    far = float(cf.svi_vol(fwd * math.exp(10), a, b, rho, m, sig, fwd, tau))
    at_bound = float(cf.svi_vol(fwd * math.exp(bound), a, b, rho, m, sig, fwd, tau))
    assert far == pytest.approx(at_bound, rel=1e-12)
    assert float(cf.svi_vol(fwd, 500.0, 0.0, 0.0, 0.0, 0.1, fwd, 1.0)) == pytest.approx(12.0)  # w capped at 144
    assert np.isnan(cf.svi_vol(fwd, -1.0, 0.0, 0.0, 0.0, 0.1, fwd, 1.0))


def test_adaptive_window_halves_and_returns_each_log_once():
    chain = FakeChain(max_span=1000)
    logs, window = cf.get_logs_adaptive(chain, "0xfeed", cf.VOL_DATA_UPDATED, 0, 9_999, window=5_000)
    blocks = [int(x["blockNumber"], 16) for x in logs]
    assert blocks == list(range(0, 10_000, 10))
    assert window <= 1000


def test_adaptive_window_reraises_other_errors():
    class Broken(FakeChain):
        def get_logs(self, *a):
            raise cf.RpcError({"code": -32000, "message": "header not found"})

    with pytest.raises(cf.RpcError):
        cf.get_logs_adaptive(Broken(), "0xfeed", cf.VOL_DATA_UPDATED, 0, 100)


def test_block_at_binary_search():
    chain = FakeChain(head=50_000)
    assert cf.block_at(chain, 1_000 + 2 * 12_345) == 12_345
    assert cf.block_at(chain, 1_000 + 2 * 12_345 + 1) == 12_345
    assert cf.block_at(chain, 10 ** 12) == 50_000


def test_sync_feed_writes_chunks_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "CHUNK_BLOCKS", 2_000)
    monkeypatch.setitem(cf.VOL_FEEDS, "TST", {"address": "0xfeed", "from_block": 1_000})
    chain = FakeChain(max_span=1000)
    res = cf.sync_feed(chain, "TST", tmp_path, 6_499, workers=2, window=4_000)
    assert res["chunks"] == 4 and res["fetched"] == 4 and res["events_fetched"] == 650  # chunk 0 starts at block 0
    files = sorted(p.name for p in (tmp_path / "TST").glob("*.parquet"))
    assert files[0] == "000000000_000001999.parquet" and files[-1] == "000006000_000006499.parquet"
    again = cf.sync_feed(chain, "TST", tmp_path, 6_499, workers=2)
    assert again["fetched"] == 0
    df = cf.load_feed(tmp_path, "TST")
    assert len(df) == 650 and df["svi_a"].dtype == "float32" and df["svi_fwd"].dtype == "float64"


def test_load_feed_prefers_longest_chunk(tmp_path):
    d = tmp_path / "TST"
    d.mkdir()
    short = cf.logs_to_frame([make_log(10, 0, 1)])
    long = cf.logs_to_frame([make_log(10, 0, 1), make_log(20, 0, 1)])
    short.to_parquet(cf.chunk_path(d, 0, 15))
    long.to_parquet(cf.chunk_path(d, 0, 49_999))
    assert len(cf.load_feed(tmp_path, "TST")) == 2


def test_compact_feed_by_month(tmp_path):
    d = tmp_path / "TST"
    d.mkdir()
    frame = cf.logs_to_frame([make_log(10, 0, 1, ts=1_704_067_200), make_log(20, 0, 1, ts=1_706_745_600)])
    frame.to_parquet(cf.chunk_path(d, 0, 49_999))
    counts = cf.compact_feed(tmp_path, "TST", tmp_path / "out")
    assert counts == {"2024-01": 1, "2024-02": 1}
    assert (tmp_path / "out" / "TST_svi_2024-02.parquet").exists()


def test_scan_emitters_groups_by_address():
    class Multi(FakeChain):
        def get_logs(self, address, topic0, a, b):
            assert address is None
            x = make_log(a, 0, 1, fwd=100.0)
            y = make_log(a, 1, 1, fwd=50_000.0)
            y["address"] = "0xABC"
            return [x, y, y]

    out = cf.scan_emitters(Multi(), [100, 200], span=10)
    assert set(out["address"]) == {"0xfeed", "0xabc"}
    row = out[(out.sample_block == 100) & (out.address == "0xabc")].iloc[0]
    assert row.n == 2 and row.fwd == pytest.approx(50_000.0)
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag prüfen**

Run: `python3 -m pytest -q tests/test_p1_chainfeeds.py`
Expected: FAIL mit `ImportError: cannot import name 'chainfeeds'`

- [ ] **Step 3: Implementierung**

`derive_surface/chainfeeds.py`:

```python
"""Vol-feed history from Derive Chain (id 957): every ``VolDataUpdated`` push since launch.

The mark IV of every Derive option is an SVI curve per expiry that Derive signs off-chain and pushes to
``LyraVolFeed``.  Each push emits ``VolDataUpdated(uint64 indexed expiry, VolDetails)`` with nine words:
SVI_a, SVI_b, SVI_rho, SVI_m, SVI_sigma, SVI_fwd (all 1e18), SVI_refTau (1e18 years), confidence (1e18),
timestamp (s).  The feed addresses below were identified on 2026-09-17 by matching SVI_fwd against the
live forward of each currency; BTC and ETH never changed address since January 2024.

``svi_vol`` reproduces ``lyra-utils/src/math/SVI.sol``: k = ln(K / SVI_fwd) clipped to
±4·sqrt(a + b·sigma); w = a + b·(rho·(k − m) + sqrt((k − m)² + sigma²)) capped at 144;
vol = sqrt(w / SVI_refTau).  The reference tau of the fit is used, not the live time to expiry.
"""
from __future__ import annotations

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

log = logging.getLogger(__name__)

RPC_URL = "https://rpc.derive.xyz"
VOL_DATA_UPDATED = "0x0b6ec9c174360425894fd5ff56d14f3450d70f2c9cde3a25983d652a72b84606"
VOL_FEEDS: Dict[str, dict] = {
    "BTC": {"address": "0x388341d9e5a7d7d5accd738b2a31b0622e0c1b87", "from_block": 2_400_000},
    "ETH": {"address": "0xb27cb6b08e6c298c8634d73d5f6649665e90d160", "from_block": 2_400_000},
    "HYPE": {"address": "0x481916590863053ea2d8f21b64ee9429820512d1", "from_block": 30_000_000},
}
CHUNK_BLOCKS = 50_000
MAX_WINDOW = 50_000
LOG_LIMIT = 10_000
COLUMNS = ["block", "log_index", "expiry", "feed_ts", "svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma",
           "svi_fwd", "svi_ref_tau", "confidence"]
FLOAT32 = ["svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_ref_tau", "confidence"]
E18 = 1e18


class RpcError(RuntimeError):
    """A JSON-RPC error returned by the chain node."""

    def __init__(self, error: dict):
        self.error = error
        super().__init__(str(error))

    @property
    def too_many_logs(self) -> bool:
        return self.error.get("code") == -32005 or "limit exceeded" in str(self.error.get("message", "")).lower()


class ChainClient:
    """Minimal JSON-RPC client with retry/backoff for rpc.derive.xyz."""

    def __init__(self, url: str = RPC_URL, timeout: float = 120.0, max_retries: int = 8, session=None):
        self.url, self.timeout, self.max_retries = url, timeout, max_retries
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "derive-option-surface/p1")

    def call(self, method: str, params: list):
        delay = 1.0
        for attempt in range(self.max_retries):
            try:
                resp = self.session.post(self.url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                                         timeout=self.timeout)
            except requests.RequestException as exc:
                log.warning("%s: network error %s (attempt %d)", method, exc, attempt + 1)
            else:
                if resp.status_code == 429 or resp.status_code >= 500:
                    log.warning("%s: HTTP %s (attempt %d)", method, resp.status_code, attempt + 1)
                else:
                    payload = resp.json()
                    if "error" not in payload:
                        return payload["result"]
                    if "rate" not in str(payload["error"].get("message", "")).lower():
                        raise RpcError(payload["error"])
                    log.warning("%s: rate limited (attempt %d)", method, attempt + 1)
            if attempt < self.max_retries - 1:
                time.sleep(delay + random.uniform(0, 0.5))
                delay = min(delay * 2, 30)
        raise RuntimeError(f"{method}: giving up after {self.max_retries} attempts")

    def block_number(self) -> int:
        return int(self.call("eth_blockNumber", []), 16)

    def block_timestamp(self, number: int) -> int:
        return int(self.call("eth_getBlockByNumber", [hex(number), False])["timestamp"], 16)

    def get_logs(self, address: Optional[str], topic0: str, from_block: int, to_block: int) -> list:
        flt = {"topics": [topic0], "fromBlock": hex(from_block), "toBlock": hex(to_block)}
        if address:
            flt["address"] = address
        return self.call("eth_getLogs", [flt])


def block_at(client, ts: int, lo: int = 1, hi: Optional[int] = None) -> int:
    """Last block whose timestamp is <= ts (binary search)."""
    hi = client.block_number() if hi is None else hi
    if client.block_timestamp(hi) <= ts:
        return hi
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if client.block_timestamp(mid) <= ts:
            lo = mid
        else:
            hi = mid - 1
    return lo


def get_logs_adaptive(client, address: Optional[str], topic0: str, lo: int, hi: int, window: int = 5_000) -> Tuple[list, int]:
    """All logs in [lo, hi]; halves the block window on 'too many logs' (and stops growing for this range),
    doubles it while results stay sparse."""
    logs: list = []
    a = lo
    can_grow = True
    while a <= hi:
        b = min(a + window - 1, hi)
        try:
            part = client.get_logs(address, topic0, a, b)
        except RpcError as err:
            if not err.too_many_logs or window == 1:
                raise
            window = max(1, window // 2)
            can_grow = False
            continue
        logs.extend(part)
        a = b + 1
        if can_grow and len(part) < LOG_LIMIT // 4:
            window = min(window * 2, MAX_WINDOW)
    return logs, window


def _word(data: bytes, i: int, signed: bool = False) -> int:
    return int.from_bytes(data[32 * i: 32 * (i + 1)], "big", signed=signed)


def decode_vol_log(entry: dict) -> dict:
    data = bytes.fromhex(entry["data"][2:])
    if len(data) != 9 * 32:
        raise ValueError(f"unexpected VolDataUpdated payload of {len(data)} bytes")
    return {
        "block": int(entry["blockNumber"], 16),
        "log_index": int(entry["logIndex"], 16),
        "expiry": int(entry["topics"][1], 16),
        "feed_ts": _word(data, 8),
        "svi_a": _word(data, 0, True) / E18,
        "svi_b": _word(data, 1) / E18,
        "svi_rho": _word(data, 2, True) / E18,
        "svi_m": _word(data, 3, True) / E18,
        "svi_sigma": _word(data, 4) / E18,
        "svi_fwd": _word(data, 5) / E18,
        "svi_ref_tau": _word(data, 6) / E18,
        "confidence": _word(data, 7) / E18,
    }


def logs_to_frame(entries: list) -> pd.DataFrame:
    df = pd.DataFrame([decode_vol_log(e) for e in entries], columns=COLUMNS)
    dtypes = {"block": "int64", "log_index": "int32", "expiry": "int64", "feed_ts": "int64", "svi_fwd": "float64"}
    dtypes.update({c: "float32" for c in FLOAT32})
    return df.astype(dtypes)


def chunk_path(out_dir: Path, start: int, end: int) -> Path:
    return out_dir / f"{start:09d}_{end:09d}.parquet"


def feed_chunks(from_block: int, to_block: int) -> List[Tuple[int, int]]:
    first = from_block - from_block % CHUNK_BLOCKS
    return [(s, min(s + CHUNK_BLOCKS - 1, to_block)) for s in range(first, to_block + 1, CHUNK_BLOCKS)]


def sync_feed(client, currency: str, out_root: Path, to_block: int, *, workers: int = 4, window: int = 5_000) -> dict:
    """Fetch every missing chunk of one feed up to ``to_block``; each chunk is written atomically."""
    spec = VOL_FEEDS[currency]
    out_dir = out_root / currency
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks = feed_chunks(spec["from_block"], to_block)
    todo = [c for c in chunks if not chunk_path(out_dir, *c).exists()]
    log.info("%s: %d chunks, %d to fetch", currency, len(chunks), len(todo))
    t0 = time.time()
    events = 0

    def run(chunk: Tuple[int, int]) -> int:
        logs, _ = get_logs_adaptive(client, spec["address"], VOL_DATA_UPDATED, chunk[0], chunk[1], window)
        frame = logs_to_frame(logs)
        path = chunk_path(out_dir, *chunk)
        tmp = path.with_suffix(".tmp")
        frame.to_parquet(tmp, index=False, compression="zstd")
        tmp.replace(path)
        return len(frame)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run, c) for c in todo]
        for i, fut in enumerate(as_completed(futures), 1):
            events += fut.result()
            if i % 20 == 0 or i == len(futures):
                elapsed = max(time.time() - t0, 1e-9)
                log.info("%s: %d/%d chunks, %d events, %.0f events/s", currency, i, len(futures), events, events / elapsed)
    return {"currency": currency, "to_block": to_block, "chunks": len(chunks), "fetched": len(todo), "events_fetched": events}


def load_feed(out_root: Path, currency: str) -> pd.DataFrame:
    """All chunks of one feed; for chunks with the same start the one reaching furthest wins."""
    best: Dict[int, Tuple[int, Path]] = {}
    for path in (out_root / currency).glob("*.parquet"):
        start, end = (int(x) for x in path.stem.split("_"))
        if start not in best or end > best[start][0]:
            best[start] = (end, path)
    frames = [pd.read_parquet(best[s][1]) for s in sorted(best)]
    if not frames:
        return logs_to_frame([])
    df = pd.concat(frames, ignore_index=True).drop_duplicates(["block", "log_index"])
    return df.sort_values(["expiry", "feed_ts", "block", "log_index"]).reset_index(drop=True)


def compact_feed(out_root: Path, currency: str, dest_dir: Path) -> dict:
    """Monthly files ``<CCY>_svi_<YYYY-MM>.parquet`` (month of the feed timestamp)."""
    df = load_feed(out_root, currency)
    dest_dir.mkdir(parents=True, exist_ok=True)
    month = pd.to_datetime(df["feed_ts"], unit="s", utc=True).dt.strftime("%Y-%m")
    counts = {}
    for m, g in df.groupby(month):
        g.reset_index(drop=True).to_parquet(dest_dir / f"{currency}_svi_{m}.parquet", index=False, compression="zstd")
        counts[m] = int(len(g))
    return counts


def svi_vol(strike, svi_a, svi_b, svi_rho, svi_m, svi_sigma, svi_fwd, svi_ref_tau) -> np.ndarray:
    """Mark vol exactly as ``LyraVolFeed.getVol`` computes it (vectorised); nan where the contract reverts."""
    a, b, rho, m, sig, fwd, tau, K = (np.asarray(x, dtype=float) for x in
                                      (svi_a, svi_b, svi_rho, svi_m, svi_sigma, svi_fwd, svi_ref_tau, strike))
    base = a + b * sig
    bound = 4.0 * np.sqrt(np.maximum(base, 0.0))
    with np.errstate(divide="ignore"):
        k = np.clip(np.log(K / fwd), -bound, bound)
    km = k - m
    w = np.minimum(a + b * (np.sqrt(km * km + sig * sig) + rho * km), 144.0)
    ok = (base >= 0) & (w >= 0) & (tau > 0)
    return np.where(ok, np.sqrt(np.where(ok, w, 0.0) / np.where(tau > 0, tau, 1.0)), np.nan)


def scan_emitters(client, blocks: List[int], span: int = 300) -> pd.DataFrame:
    """Every address that emitted VolDataUpdated in [b, b + span] for each sample block b."""
    rows = []
    for b in blocks:
        for entry in client.get_logs(None, VOL_DATA_UPDATED, b, b + span):
            d = decode_vol_log(entry)
            rows.append({"sample_block": b, "address": entry["address"].lower(), "svi_fwd": d["svi_fwd"], "feed_ts": d["feed_ts"]})
    df = pd.DataFrame(rows, columns=["sample_block", "address", "svi_fwd", "feed_ts"])
    return (df.groupby(["sample_block", "address"])
              .agg(n=("svi_fwd", "size"), fwd=("svi_fwd", "median"), ts=("feed_ts", "max"))
              .reset_index())
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q tests/test_p1_chainfeeds.py`
Expected: `11 passed`

- [ ] **Step 5: Gesamtsuite und Commit**

Run: `python3 -m pytest -q` → Expected: `44 passed`

```bash
git add derive_surface/chainfeeds.py tests/test_p1_chainfeeds.py
git commit -m "paper1: vol-feed (SVI) history from Derive Chain

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: `refdata.py` — Referenzdaten

**Files:**
- Create: `derive_surface/refdata.py`
- Test: `tests/test_p1_refdata.py`

**Interfaces:**
- Consumes: Client mit `call(method, **params)`; `derive_surface.api.DeriveError` (für übersprungene Score-Epochen).
- Produces:
  - `OPTION_CURRENCIES: list[str]` (12 Underlyings)
  - `settlement_prices(client, currencies) -> DataFrame[currency, expiry, expiry_date, settlement_price]`
  - `liquidations(client, page_sizes=(5, 20, 50, 100)) -> (auctions: DataFrame, bids: DataFrame, info: dict)`; `auctions` Spalten `auction_id, subaccount_id, start_timestamp, end_timestamp, auction_type, fee, tx_hash`; `bids` Spalten `auction_id, subaccount_id, timestamp, tx_hash, percent_liquidated, cash_received, discount_pnl, instruments`
  - `maker_programs(client) -> DataFrame[name, asset_types, currencies, min_notional, start_ms, end_ms, rewards]`
  - `maker_scores(client, programs, asset_type="option") -> DataFrame[program, start_ms, end_ms, wallet, total_score, coverage_score, quality_score, volume_multiplier, holder_boost, volume]`
  - `vault_statistics(client) -> DataFrame`, `instrument_fees(client, currencies) -> DataFrame`, `funding_history(client, instruments) -> DataFrame[instrument_name, timestamp, funding_rate]`
  - `merge_append(path, new, key) -> DataFrame`
  - `save_all(client, ref_dir: Path, currencies=OPTION_CURRENCIES) -> dict`; Dateien `settlement_prices.parquet`, `liquidation_auctions.parquet`, `liquidation_bids.parquet`, `maker_programs.parquet`, `maker_scores.parquet`, `vault_statistics_<YYYYMMDD>.parquet`, `instrument_fees_<YYYYMMDD>.parquet`, `funding_history.parquet`, `REFDATA.json`

- [ ] **Step 1: Failing tests schreiben**

`tests/test_p1_refdata.py`:

```python
from __future__ import annotations

import pandas as pd

from derive_surface import refdata
from derive_surface.api import DeriveError


class Fake:
    def __init__(self, handlers):
        self.handlers = handlers

    def call(self, method, **p):
        return self.handlers[method](**p)


def auction(i, bids=1):
    return {"auction_id": f"a{i}", "subaccount_id": 100 + i, "start_timestamp": i, "end_timestamp": i + 1,
            "auction_type": "solvent", "fee": "1", "tx_hash": f"0xA{i}",
            "bids": [{"timestamp": i + 1, "tx_hash": f"0xB{i}{j}", "percent_liquidated": "0.1", "cash_received": "5",
                      "discount_pnl": "-1", "amounts_liquidated": {"ETH-PERP": "1"}} for j in range(bids)]}


def test_liquidations_union_across_page_sizes():
    subsets = {5: [0, 1, 2, 3, 4, 5, 6], 20: [5, 6, 7], 50: [], 100: [8]}

    def liq(page, page_size):
        ids = subsets[page_size]
        chunk = ids[(page - 1) * page_size: page * page_size]
        pages = max(1, -(-len(ids) // page_size))
        return {"auctions": [auction(i) for i in chunk], "pagination": {"num_pages": pages, "count": 12}}

    auctions, bids, info = refdata.liquidations(Fake({"get_liquidation_history": liq}))
    assert sorted(auctions["auction_id"]) == [f"a{i}" for i in range(9)]
    assert len(bids) == 9 and bids["instruments"].iloc[0] == '{"ETH-PERP": "1"}'
    assert info == {"reported_count": 12, "unique_auctions": 9}


def test_maker_scores_only_option_programmes_and_lowercase_wallets():
    programs = pd.DataFrame([
        {"name": "OPTIONS-MAJ", "asset_types": "option", "currencies": "BTC", "min_notional": 0.0, "start_ms": 1, "end_ms": 2, "rewards": "{}"},
        {"name": "PERPS-MAJ", "asset_types": "perp", "currencies": "BTC", "min_notional": 0.0, "start_ms": 1, "end_ms": 2, "rewards": "{}"},
        {"name": "OPTIONS-OLD", "asset_types": "option", "currencies": "ETH", "min_notional": 0.0, "start_ms": 0, "end_ms": 1, "rewards": "{}"},
    ])
    seen = []

    def scores(program_name, epoch_start_timestamp):
        seen.append(program_name)
        if program_name == "OPTIONS-OLD":
            raise DeriveError("get_maker_program_scores", {"code": 19000})
        return {"scores": [{"wallet": "0xAbC", "total_score": "3.5", "coverage_score": "1", "quality_score": "2",
                            "volume_multiplier": "1", "holder_boost": "1", "volume": "10"}]}

    out = refdata.maker_scores(Fake({"get_maker_program_scores": scores}), programs)
    assert seen == ["OPTIONS-MAJ", "OPTIONS-OLD"]
    assert out.to_dict("records") == [{"program": "OPTIONS-MAJ", "start_ms": 1, "end_ms": 2, "wallet": "0xabc", "total_score": 3.5,
                                       "coverage_score": 1.0, "quality_score": 2.0, "volume_multiplier": 1.0, "holder_boost": 1.0, "volume": 10.0}]


def test_settlement_prices_frame():
    def sp(currency):
        return {"expiries": [{"utc_expiry_sec": 20, "expiry_date": "20260102", "price": "2.5"},
                             {"utc_expiry_sec": 10, "expiry_date": "20260101", "price": "1.5"}]}

    df = refdata.settlement_prices(Fake({"get_option_settlement_prices": sp}), ["HYPE", "BTC"])
    assert list(df["currency"]) == ["BTC", "BTC", "HYPE", "HYPE"]
    assert list(df["expiry"][:2]) == [10, 20] and df["settlement_price"].dtype == "float64"


def test_merge_append_dedupes(tmp_path):
    path = tmp_path / "f.parquet"
    a = pd.DataFrame({"instrument_name": ["X", "X"], "timestamp": [1, 2], "funding_rate": [0.1, 0.2]})
    b = pd.DataFrame({"instrument_name": ["X", "X"], "timestamp": [2, 3], "funding_rate": [0.25, 0.3]})
    refdata.merge_append(path, a, ["instrument_name", "timestamp"])
    out = refdata.merge_append(path, b, ["instrument_name", "timestamp"])
    assert list(out["timestamp"]) == [1, 2, 3] and list(out["funding_rate"]) == [0.1, 0.25, 0.3]
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag prüfen**

Run: `python3 -m pytest -q tests/test_p1_refdata.py`
Expected: FAIL mit `ImportError: cannot import name 'refdata'`

- [ ] **Step 3: Implementierung**

`derive_surface/refdata.py`:

```python
"""Reference data for paper 1: settlement prices, liquidations, maker programmes, vaults, fees, funding.

``get_liquidation_history`` returned different subsets for different page sizes on 2026-09-17 (count 76,
page size 100 → 23 auctions), so auctions are collected as the union over several page sizes and the
reported count is kept next to the number actually found.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import pandas as pd

from .api import DeriveError

log = logging.getLogger(__name__)

OPTION_CURRENCIES = ["BTC", "ETH", "HYPE", "SOL", "XRP", "ZEC", "ADA", "XAUT", "CC", "VVV", "LIT", "PUMP"]
PERPS = ("BTC-PERP", "ETH-PERP", "HYPE-PERP")
SCORE_FIELDS = ["total_score", "coverage_score", "quality_score", "volume_multiplier", "holder_boost", "volume"]


def settlement_prices(client, currencies: Iterable[str]) -> pd.DataFrame:
    rows = []
    for ccy in currencies:
        for e in client.call("get_option_settlement_prices", currency=ccy)["expiries"]:
            rows.append({"currency": ccy, "expiry": int(e["utc_expiry_sec"]), "expiry_date": e["expiry_date"],
                         "settlement_price": float(e["price"])})
    df = pd.DataFrame(rows, columns=["currency", "expiry", "expiry_date", "settlement_price"])
    return df.sort_values(["currency", "expiry"]).reset_index(drop=True)


def liquidations(client, page_sizes: Sequence[int] = (5, 20, 50, 100)) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    found = {}
    reported = None
    for size in page_sizes:
        page, pages = 1, 1
        while page <= pages:
            res = client.call("get_liquidation_history", page=page, page_size=size)
            pages = int(res["pagination"]["num_pages"])
            reported = int(res["pagination"]["count"])
            for a in res["auctions"]:
                found[a["auction_id"]] = a
            page += 1
    auction_cols = ["auction_id", "subaccount_id", "start_timestamp", "end_timestamp", "auction_type", "fee", "tx_hash"]
    bid_cols = ["auction_id", "subaccount_id", "timestamp", "tx_hash", "percent_liquidated", "cash_received", "discount_pnl", "instruments"]
    arows, brows = [], []
    for a in found.values():
        arows.append({k: a.get(k) for k in auction_cols})
        for b in a.get("bids") or []:
            brows.append({"auction_id": a["auction_id"], "subaccount_id": a["subaccount_id"], "timestamp": b.get("timestamp"),
                          "tx_hash": b.get("tx_hash"), "percent_liquidated": b.get("percent_liquidated"),
                          "cash_received": b.get("cash_received"), "discount_pnl": b.get("discount_pnl"),
                          "instruments": json.dumps(b.get("amounts_liquidated") or {})})
    info = {"reported_count": reported, "unique_auctions": len(found)}
    return pd.DataFrame(arows, columns=auction_cols), pd.DataFrame(brows, columns=bid_cols), info


def maker_programs(client) -> pd.DataFrame:
    rows = []
    for p in client.call("get_maker_programs"):
        rows.append({"name": p["name"], "asset_types": ",".join(p.get("asset_types") or []),
                     "currencies": ",".join(p.get("currencies") or []), "min_notional": float(p.get("min_notional") or 0),
                     "start_ms": int(p["start_timestamp"]), "end_ms": int(p["end_timestamp"]),
                     "rewards": json.dumps(p.get("rewards") or {}, sort_keys=True)})
    cols = ["name", "asset_types", "currencies", "min_notional", "start_ms", "end_ms", "rewards"]
    return pd.DataFrame(rows, columns=cols).sort_values(["start_ms", "name"]).reset_index(drop=True)


def maker_scores(client, programs: pd.DataFrame, asset_type: str = "option") -> pd.DataFrame:
    rows = []
    selected = programs[programs["asset_types"].str.split(",").map(lambda xs: asset_type in xs)]
    for name, start_ms, end_ms in zip(selected["name"], selected["start_ms"], selected["end_ms"]):
        try:
            res = client.call("get_maker_program_scores", program_name=name, epoch_start_timestamp=int(start_ms))
        except DeriveError as err:
            log.warning("scores %s@%s unavailable: %s", name, start_ms, err)
            continue
        for s in res.get("scores") or []:
            row = {"program": name, "start_ms": int(start_ms), "end_ms": int(end_ms), "wallet": s["wallet"].lower()}
            row.update({k: float(s.get(k) or 0) for k in SCORE_FIELDS})
            rows.append(row)
    return pd.DataFrame(rows, columns=["program", "start_ms", "end_ms", "wallet"] + SCORE_FIELDS)


def vault_statistics(client) -> pd.DataFrame:
    return pd.DataFrame(client.call("get_vault_statistics")).astype(str)


def instrument_fees(client, currencies: Iterable[str]) -> pd.DataFrame:
    keep = ["instrument_name", "maker_fee_rate", "taker_fee_rate", "base_fee", "mark_price_fee_rate_cap",
            "pro_rata_fraction", "fifo_min_allocation", "pro_rata_amount_step", "tick_size", "minimum_amount", "amount_step"]
    rows = []
    for ccy in currencies:
        for inst in client.call("get_instruments", currency=ccy, instrument_type="option", expired=False):
            row = {"currency": ccy}
            row.update({k: None if inst.get(k) is None else str(inst.get(k)) for k in keep})
            rows.append(row)
    return pd.DataFrame(rows, columns=["currency"] + keep)


def funding_history(client, instruments: Iterable[str] = PERPS) -> pd.DataFrame:
    rows = []
    for name in instruments:
        for r in client.call("get_funding_rate_history", instrument_name=name)["funding_rate_history"]:
            rows.append({"instrument_name": name, "timestamp": int(r["timestamp"]), "funding_rate": float(r["funding_rate"])})
    return pd.DataFrame(rows, columns=["instrument_name", "timestamp", "funding_rate"])


def merge_append(path: Path, new: pd.DataFrame, key: List[str]) -> pd.DataFrame:
    """Union of an existing parquet and ``new``; on key collisions the new row wins."""
    if path.exists():
        new = pd.concat([pd.read_parquet(path), new], ignore_index=True).drop_duplicates(key, keep="last")
    new = new.sort_values(key).reset_index(drop=True)
    new.to_parquet(path, index=False)
    return new


def save_all(client, ref_dir: Path, currencies: Iterable[str] = OPTION_CURRENCIES) -> dict:
    ref_dir.mkdir(parents=True, exist_ok=True)
    currencies = list(currencies)
    stamp = time.strftime("%Y%m%d", time.gmtime())
    out: dict = {"fetched_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime())}
    sp = settlement_prices(client, currencies)
    sp.to_parquet(ref_dir / "settlement_prices.parquet", index=False)
    out["settlement_prices"] = sp.groupby("currency").size().to_dict()
    auctions, bids, info = liquidations(client)
    auctions.to_parquet(ref_dir / "liquidation_auctions.parquet", index=False)
    bids.to_parquet(ref_dir / "liquidation_bids.parquet", index=False)
    out["liquidations"] = {**info, "bids": len(bids)}
    programs = maker_programs(client)
    programs.to_parquet(ref_dir / "maker_programs.parquet", index=False)
    scores = maker_scores(client, programs)
    scores.to_parquet(ref_dir / "maker_scores.parquet", index=False)
    out["maker_programmes"] = {"programmes": len(programs), "option_score_rows": len(scores),
                               "active_wallets": int(scores.loc[scores["total_score"] > 0, "wallet"].nunique())}
    vaults = vault_statistics(client)
    vaults.to_parquet(ref_dir / f"vault_statistics_{stamp}.parquet", index=False)
    out["vaults"] = len(vaults)
    fees = instrument_fees(client, currencies)
    fees.to_parquet(ref_dir / f"instrument_fees_{stamp}.parquet", index=False)
    out["instruments"] = len(fees)
    funding = merge_append(ref_dir / "funding_history.parquet", funding_history(client), ["instrument_name", "timestamp"])
    out["funding_rows"] = len(funding)
    (ref_dir / "REFDATA.json").write_text(json.dumps(out, indent=1, default=str))
    return out
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q tests/test_p1_refdata.py`
Expected: `4 passed`

- [ ] **Step 5: Gesamtsuite und Commit**

Run: `python3 -m pytest -q` → Expected: `48 passed`

```bash
git add derive_surface/refdata.py tests/test_p1_refdata.py
git commit -m "paper1: reference data (settlements, liquidations, maker programmes, vaults, fees, funding)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: `classify.py` — Fills paaren und Taker klassifizieren

**Files:**
- Create: `derive_surface/classify.py`
- Test: `tests/test_p1_classify.py`

**Interfaces:**
- Consumes: Tape-Frame aus `fulltape.condense` (Spalten `FIELDS + currency, expiry, strike, option_type`); `refdata`-Dateien `liquidation_auctions.parquet`, `liquidation_bids.parquet`, `maker_scores.parquet`.
- Produces:
  - `CLASS_ORDER = ["liquidation", "vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]`, Schwellen `DOMINANT_MAKER_SHARE = 0.80`, `DOMINANT_MIN_VOLUME_SHARE = 0.01`, `LARGE_TAKER_QUANTILE = 0.99`
  - `month_of(ts_ms) -> pd.Series` (`"YYYY-MM"`)
  - `pair_fills(tape) -> (fills, unpaired_rows)`; `fills` Spalten: `trade_id, ts, ts_maker, instrument_name, currency, expiry, strike, option_type, price, amount, mark_price, index_price, mark_price_maker_row, taker_side, taker_wallet, taker_sub, maker_wallet, maker_sub, rfq_id, tx_hash, tx_status, fee_taker, fee_maker, rebate_maker, rebate_taker, pnl_taker, pnl_maker, notional, pair_ok`
  - `wallet_month_stats(fills) -> DataFrame[wallet, month, maker_notional, taker_notional, maker_share, maker_volume_share]`
  - `dominant_makers(stats, …) -> set[tuple[str, str]]`, `large_takers(stats, q) -> set[tuple[str, str]]`
  - `mm_programme_lookup(scores) -> (starts: ndarray, ends: ndarray, wallet_sets: list[set])`, `in_mm_programme(ts, wallets, lookup) -> ndarray[bool]`
  - `load_vault_wallets(path) -> set[str]` (CSV-Spalten `wallet, vault_name, source`)
  - `classify_fills(fills, *, liquidation_tx, vault_wallets, dominant, large, mm_lookup) -> DataFrame` (zusätzlich `is_liquidation, taker_is_vault, maker_is_vault, is_rfq, taker_is_dominant_maker, maker_is_dominant_maker, taker_in_mm_programme, taker_is_large, taker_class, month`)
  - `build_fills(tape_dir, ref_dir, vault_csv, out_path) -> dict` (schreibt `fills.parquet` und `wallet_month_stats.parquet`)

- [ ] **Step 1: Failing tests schreiben**

`tests/test_p1_classify.py`:

```python
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import classify as cl

JAN = 1_704_931_200_000  # 2024-01-11
FEB = 1_707_004_800_000  # 2024-02-04


def row(tid, role, ts, wallet, sub, direction, price=10.0, amount=1.0, rfq=None, tx="0x1", ccy="BTC", index=40_000.0):
    return {"trade_id": tid, "timestamp": ts, "instrument_name": f"{ccy}-20240126-45000-C", "direction": direction,
            "liquidity_role": role, "trade_price": price, "trade_amount": amount, "mark_price": 11.0, "index_price": index,
            "wallet": wallet, "subaccount_id": sub, "rfq_id": rfq, "quote_id": None, "trade_fee": 0.5 if role == "taker" else 0.0,
            "expected_rebate": 0.1 if role == "maker" else 0.0, "extra_fee": 0.0, "realized_pnl": 0.0,
            "realized_pnl_excl_fees": 0.0, "tx_hash": tx, "tx_status": "settled", "currency": ccy, "expiry": 1_706_256_000,
            "strike": 45_000.0, "option_type": "C"}


def fill(tid, ts, maker, taker, taker_dir="buy", **kw):
    maker_dir = "sell" if taker_dir == "buy" else "buy"
    return [row(tid, "maker", ts - 5, maker, 1, maker_dir, **kw), row(tid, "taker", ts, taker, 2, taker_dir, **kw)]


def test_pair_fills_pairs_and_flags_unpaired():
    rows = fill("a", JAN, "0xm", "0xt") + fill("b", JAN + 1, "0xm", "0xt", taker_dir="sell")
    rows += [row("c", "taker", JAN + 2, "0xt", 2, "buy")]
    rows[1]["rfq_id"] = None
    rows[0]["rfq_id"] = "r1"  # only the maker row carries the rfq id
    fills, unpaired = cl.pair_fills(pd.DataFrame(rows))
    assert list(fills["trade_id"]) == ["a", "b"]
    assert list(fills["taker_side"]) == [1, -1]
    assert fills["ts"].iloc[0] == JAN and fills["ts_maker"].iloc[0] == JAN - 5
    assert fills["rfq_id"].iloc[0] == "r1"
    assert fills["pair_ok"].all()
    assert fills["notional"].iloc[0] == pytest.approx(40_000.0)
    assert fills["rebate_maker"].iloc[0] == pytest.approx(0.1) and fills["fee_taker"].iloc[0] == pytest.approx(0.5)
    assert list(unpaired["trade_id"]) == ["c"]


def test_pair_ok_detects_price_mismatch():
    rows = fill("a", JAN, "0xm", "0xt")
    rows[0]["trade_price"] = 10.5
    fills, _ = cl.pair_fills(pd.DataFrame(rows))
    assert not fills["pair_ok"].iloc[0]


def base_fills():
    rows = []
    for i, taker in enumerate(["0xliq", "0xvault", "0xrfq", "0xdom", "0xmm", "0xbig", "0xnone"]):
        rows += fill(f"f{i}", JAN + 100 * i, "0xmaker", taker, tx=f"0x{i}", rfq="r" if taker in ("0xliq", "0xvault", "0xrfq") else None)
    fills, _ = cl.pair_fills(pd.DataFrame(rows))
    return fills


def test_class_priority():
    fills = base_fills()
    months = "2024-01"
    everyone = {"0xliq", "0xvault", "0xrfq", "0xdom", "0xmm", "0xbig"}
    lookup = (np.array([JAN - 1]), np.array([JAN + 10_000]), [{"0xmm", "0xdom", "0xliq", "0xvault", "0xrfq"}])
    out = cl.classify_fills(
        fills,
        liquidation_tx={"0x0"},
        vault_wallets={"0xvault", "0xliq"},
        dominant={(w, months) for w in ("0xdom", "0xliq", "0xvault", "0xrfq")},
        large={(w, months) for w in everyone},
        mm_lookup=lookup,
    )
    assert list(out["taker_class"]) == ["liquidation", "vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]
    assert out["is_rfq"].sum() == 3 and out["month"].iloc[0] == months


def test_wallet_month_stats_dominant_and_large():
    rows = []
    for i in range(10):
        rows += fill(f"a{i}", JAN + i, "0xmm", f"0xt{i}", amount=1.0)
    rows += fill("b0", JAN + 50, "0xsmall", "0xmm", amount=0.5)
    rows += fill("c0", JAN + 60, "0xmm", "0xwhale", amount=100.0)
    rows += fill("d0", FEB, "0xt1", "0xmm", amount=1.0)
    fills, _ = cl.pair_fills(pd.DataFrame(rows))
    stats = cl.wallet_month_stats(fills)
    mm_jan = stats[(stats.wallet == "0xmm") & (stats.month == "2024-01")].iloc[0]
    assert mm_jan.maker_share == pytest.approx(110 / 110.5)
    assert mm_jan.maker_volume_share == pytest.approx(110 / 110.5)
    dom = cl.dominant_makers(stats)
    assert ("0xmm", "2024-01") in dom and ("0xmm", "2024-02") not in dom and ("0xsmall", "2024-01") not in dom
    assert ("0xwhale", "2024-01") in cl.large_takers(stats)
    assert ("0xt3", "2024-01") not in cl.large_takers(stats)


def test_mm_programme_lookup_and_membership():
    scores = pd.DataFrame([
        {"program": "OPTIONS-MAJ", "start_ms": 100, "end_ms": 200, "wallet": "0xa", "total_score": 1.0},
        {"program": "OPTIONS-MID", "start_ms": 100, "end_ms": 200, "wallet": "0xc", "total_score": 2.0},
        {"program": "OPTIONS-MAJ", "start_ms": 100, "end_ms": 200, "wallet": "0xb", "total_score": 0.0},
        {"program": "OPTIONS-MAJ", "start_ms": 300, "end_ms": 400, "wallet": "0xb", "total_score": 5.0},
    ])
    lookup = cl.mm_programme_lookup(scores)
    got = cl.in_mm_programme(np.array([150, 150, 150, 250, 350, 50]), np.array(["0xa", "0xb", "0xc", "0xa", "0xb", "0xa"]), lookup)
    assert list(got) == [True, False, True, False, True, False]
    empty = cl.mm_programme_lookup(scores.iloc[0:0])
    assert not cl.in_mm_programme(np.array([150]), np.array(["0xa"]), empty).any()


def test_load_vault_wallets_validates(tmp_path):
    good = tmp_path / "v.csv"
    good.write_text("# comment\nwallet,vault_name,source\n0xAbCdEf0123456789abcdef0123456789ABCDEF01,Test,https://x\n")
    assert cl.load_vault_wallets(good) == {"0xabcdef0123456789abcdef0123456789abcdef01"}
    bad = tmp_path / "b.csv"
    bad.write_text("wallet,vault_name,source\n0x123,Test,https://x\n")
    with pytest.raises(ValueError, match="invalid"):
        cl.load_vault_wallets(bad)
    missing = tmp_path / "m.csv"
    missing.write_text("wallet,name\n0xAbCdEf0123456789abcdef0123456789ABCDEF01,x\n")
    with pytest.raises(ValueError, match="columns"):
        cl.load_vault_wallets(missing)


def test_build_fills_end_to_end(tmp_path):
    tape_dir, ref_dir = tmp_path / "tape", tmp_path / "ref"
    tape_dir.mkdir()
    ref_dir.mkdir()
    rows = fill("a", JAN, "0xm", "0xt", tx="0xLIQ") + fill("b", JAN + 1, "0xm", "0xu", amount=0.1)
    pd.DataFrame(rows).to_parquet(tape_dir / "BTC_options_full.parquet")
    pd.DataFrame({"auction_id": ["x"], "tx_hash": ["0xnope"]}).to_parquet(ref_dir / "liquidation_auctions.parquet")
    pd.DataFrame({"auction_id": ["x"], "tx_hash": ["0xliq"]}).to_parquet(ref_dir / "liquidation_bids.parquet")
    pd.DataFrame(columns=["program", "start_ms", "end_ms", "wallet", "total_score"]).to_parquet(ref_dir / "maker_scores.parquet")
    vaults = tmp_path / "v.csv"
    vaults.write_text("wallet,vault_name,source\n")
    out = tmp_path / "derived" / "fills.parquet"
    out.parent.mkdir()
    summary = cl.build_fills(tape_dir, ref_dir, vaults, out)
    assert summary["fills"] == 2 and summary["unpaired_rows"] == 0 and summary["pair_mismatch"] == 0
    got = pd.read_parquet(out)
    assert list(got["taker_class"]) == ["liquidation", "other"]
    assert (tmp_path / "derived" / "wallet_month_stats.parquet").exists()
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag prüfen**

Run: `python3 -m pytest -q tests/test_p1_classify.py`
Expected: FAIL mit `ImportError: cannot import name 'classify'`

- [ ] **Step 3: Implementierung**

`derive_surface/classify.py`:

```python
"""Pair maker and taker rows into fills and classify the taker of every fill (paper 1, spec §3).

Class priority (first match wins): liquidation > vault > rfq > dominant maker > MM programme > large > other.
Every flag is also kept as its own column so that analyses can cross-tabulate.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set, Tuple

import numpy as np
import pandas as pd

CLASS_ORDER = ["liquidation", "vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]
DOMINANT_MAKER_SHARE = 0.80
DOMINANT_MIN_VOLUME_SHARE = 0.01
LARGE_TAKER_QUANTILE = 0.99
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
WalletMonths = Set[Tuple[str, str]]
MMLookup = Tuple[np.ndarray, np.ndarray, List[Set[str]]]


def month_of(ts_ms) -> pd.Series:
    return pd.to_datetime(pd.Series(ts_ms), unit="ms", utc=True).dt.strftime("%Y-%m")


def pair_fills(tape: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """One row per fill from its maker and taker row; rows of trade_ids without exactly one of each are returned apart."""
    roles = tape.assign(_maker=tape["liquidity_role"].eq("maker"), _taker=tape["liquidity_role"].eq("taker"))
    counts = roles.groupby("trade_id")[["_maker", "_taker"]].sum()
    good = counts.index[(counts["_maker"] == 1) & (counts["_taker"] == 1)]
    is_good = tape["trade_id"].isin(good)
    unpaired = tape[~is_good].reset_index(drop=True)
    paired = tape[is_good]
    t = paired[paired["liquidity_role"] == "taker"].set_index("trade_id")
    m = paired[paired["liquidity_role"] == "maker"].set_index("trade_id").loc[t.index]
    fills = pd.DataFrame({
        "trade_id": t.index.to_numpy(),
        "ts": t["timestamp"].to_numpy(),
        "ts_maker": m["timestamp"].to_numpy(),
        "instrument_name": t["instrument_name"].to_numpy(),
        "currency": t["currency"].to_numpy(),
        "expiry": t["expiry"].to_numpy(),
        "strike": t["strike"].to_numpy(),
        "option_type": t["option_type"].to_numpy(),
        "price": t["trade_price"].to_numpy(),
        "amount": t["trade_amount"].to_numpy(),
        "mark_price": t["mark_price"].to_numpy(),
        "index_price": t["index_price"].to_numpy(),
        "mark_price_maker_row": m["mark_price"].to_numpy(),
        "taker_side": np.where(t["direction"].to_numpy() == "buy", 1, -1),
        "taker_wallet": t["wallet"].to_numpy(),
        "taker_sub": t["subaccount_id"].to_numpy(),
        "maker_wallet": m["wallet"].to_numpy(),
        "maker_sub": m["subaccount_id"].to_numpy(),
        "rfq_id": t["rfq_id"].where(t["rfq_id"].notna(), m["rfq_id"]).to_numpy(),
        "tx_hash": t["tx_hash"].to_numpy(),
        "tx_status": t["tx_status"].to_numpy(),
        "fee_taker": t["trade_fee"].to_numpy(),
        "fee_maker": m["trade_fee"].to_numpy(),
        "rebate_maker": m["expected_rebate"].to_numpy(),
        "rebate_taker": t["expected_rebate"].to_numpy(),
        "pnl_taker": t["realized_pnl"].to_numpy(),
        "pnl_maker": m["realized_pnl"].to_numpy(),
    })
    fills["notional"] = fills["amount"] * fills["index_price"]
    fills["pair_ok"] = (
        np.isclose(t["trade_price"].to_numpy(float), m["trade_price"].to_numpy(float), rtol=1e-9, atol=0.0)
        & np.isclose(t["trade_amount"].to_numpy(float), m["trade_amount"].to_numpy(float), rtol=1e-9, atol=0.0)
        & (t["direction"].to_numpy() != m["direction"].to_numpy())
    )
    return fills.sort_values(["ts", "trade_id"]).reset_index(drop=True), unpaired


def wallet_month_stats(fills: pd.DataFrame) -> pd.DataFrame:
    month = month_of(fills["ts"].to_numpy()).to_numpy()
    maker = fills.groupby([fills["maker_wallet"].to_numpy(), month])["notional"].sum().rename("maker_notional")
    taker = fills.groupby([fills["taker_wallet"].to_numpy(), month])["notional"].sum().rename("taker_notional")
    stats = pd.concat([maker, taker], axis=1).fillna(0.0)
    stats.index = stats.index.set_names(["wallet", "month"])
    stats = stats.reset_index()
    stats["maker_share"] = stats["maker_notional"] / (stats["maker_notional"] + stats["taker_notional"])
    stats["maker_volume_share"] = stats["maker_notional"] / stats.groupby("month")["maker_notional"].transform("sum")
    return stats


def dominant_makers(stats: pd.DataFrame, min_share: float = DOMINANT_MAKER_SHARE,
                    min_volume_share: float = DOMINANT_MIN_VOLUME_SHARE) -> WalletMonths:
    sel = stats[(stats["maker_share"] >= min_share) & (stats["maker_volume_share"] >= min_volume_share)]
    return set(zip(sel["wallet"], sel["month"]))


def large_takers(stats: pd.DataFrame, q: float = LARGE_TAKER_QUANTILE) -> WalletMonths:
    takers = stats[stats["taker_notional"] > 0]
    threshold = takers.groupby("month")["taker_notional"].transform(lambda s: s.quantile(q))
    sel = takers[takers["taker_notional"] >= threshold]
    return set(zip(sel["wallet"], sel["month"]))


def mm_programme_lookup(scores: pd.DataFrame) -> MMLookup:
    active = scores[scores["total_score"] > 0]
    if active.empty:
        return np.array([], dtype="int64"), np.array([], dtype="int64"), []
    epochs = active.groupby(["start_ms", "end_ms"])["wallet"].apply(set).reset_index().sort_values("start_ms")
    return epochs["start_ms"].to_numpy("int64"), epochs["end_ms"].to_numpy("int64"), list(epochs["wallet"])


def in_mm_programme(ts: np.ndarray, wallets: np.ndarray, lookup: MMLookup) -> np.ndarray:
    starts, ends, sets = lookup
    out = np.zeros(len(ts), dtype=bool)
    if len(starts) == 0:
        return out
    idx = np.searchsorted(starts, ts, side="right") - 1
    for i, (j, wallet) in enumerate(zip(idx, wallets)):
        if j >= 0 and ts[i] < ends[j] and wallet in sets[j]:
            out[i] = True
    return out


def load_vault_wallets(path: Path) -> Set[str]:
    df = pd.read_csv(path, comment="#", dtype=str)
    missing = {"wallet", "vault_name", "source"} - set(df.columns)
    if missing:
        raise ValueError(f"vault list lacks columns {sorted(missing)}")
    wallets = df["wallet"].str.strip().str.lower()
    bad = wallets[~wallets.str.match(ADDRESS)]
    if len(bad):
        raise ValueError(f"invalid wallet addresses: {list(bad)[:3]}")
    return set(wallets)


def classify_fills(fills: pd.DataFrame, *, liquidation_tx: Set[str], vault_wallets: Set[str], dominant: WalletMonths,
                   large: WalletMonths, mm_lookup: MMLookup) -> pd.DataFrame:
    f = fills.copy()
    month = month_of(f["ts"].to_numpy()).to_numpy()
    taker = f["taker_wallet"].to_numpy()
    maker = f["maker_wallet"].to_numpy()
    f["is_liquidation"] = f["tx_hash"].str.lower().isin(liquidation_tx).to_numpy()
    f["taker_is_vault"] = f["taker_wallet"].isin(vault_wallets)
    f["maker_is_vault"] = f["maker_wallet"].isin(vault_wallets)
    f["is_rfq"] = f["rfq_id"].notna()
    f["taker_is_dominant_maker"] = [(w, mo) in dominant for w, mo in zip(taker, month)]
    f["maker_is_dominant_maker"] = [(w, mo) in dominant for w, mo in zip(maker, month)]
    f["taker_in_mm_programme"] = in_mm_programme(f["ts"].to_numpy("int64"), taker, mm_lookup)
    f["taker_is_large"] = [(w, mo) in large for w, mo in zip(taker, month)]
    flags = [("liquidation", "is_liquidation"), ("vault", "taker_is_vault"), ("rfq", "is_rfq"),
             ("dominant_maker", "taker_is_dominant_maker"), ("mm_programme", "taker_in_mm_programme"), ("large", "taker_is_large")]
    cls = np.full(len(f), "other", dtype=object)
    for name, col in reversed(flags):
        cls = np.where(f[col].to_numpy(bool), name, cls)
    f["taker_class"] = cls
    f["month"] = month
    return f


def build_fills(tape_dir: Path, ref_dir: Path, vault_csv: Path, out_path: Path) -> dict:
    tape = pd.concat([pd.read_parquet(p) for p in sorted(tape_dir.glob("*_options_full.parquet"))], ignore_index=True)
    fills, unpaired = pair_fills(tape)
    stats = wallet_month_stats(fills)
    auctions = pd.read_parquet(ref_dir / "liquidation_auctions.parquet")
    bids = pd.read_parquet(ref_dir / "liquidation_bids.parquet")
    liq = set(auctions["tx_hash"].dropna().str.lower()) | set(bids["tx_hash"].dropna().str.lower())
    scores = pd.read_parquet(ref_dir / "maker_scores.parquet")
    out = classify_fills(fills, liquidation_tx=liq, vault_wallets=load_vault_wallets(vault_csv),
                         dominant=dominant_makers(stats), large=large_takers(stats), mm_lookup=mm_programme_lookup(scores))
    out.to_parquet(out_path, index=False, compression="zstd")
    stats.to_parquet(out_path.with_name("wallet_month_stats.parquet"), index=False)
    classes = (out.groupby(["currency", "taker_class"])
                  .agg(fills=("trade_id", "size"), notional=("notional", "sum"))
                  .reset_index())
    return {
        "rows": int(len(tape)), "fills": int(len(out)), "unpaired_rows": int(len(unpaired)),
        "unpaired_trade_ids": int(unpaired["trade_id"].nunique()) if len(unpaired) else 0,
        "pair_mismatch": int((~out["pair_ok"]).sum()), "not_settled": int((out["tx_status"] != "settled").sum()),
        "liquidation_tx": len(liq), "classes": classes.to_dict("records"),
    }
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q tests/test_p1_classify.py`
Expected: `7 passed`

- [ ] **Step 5: Gesamtsuite und Commit**

Run: `python3 -m pytest -q` → Expected: `55 passed`

```bash
git add derive_surface/classify.py tests/test_p1_classify.py
git commit -m "paper1: pair maker/taker rows and classify takers

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: CLI `p1`, Feed-Prüfskript

**Files:**
- Create: `derive_surface/p1cli.py`, `scripts/p1_check_feeds.py`
- Modify: `derive_surface/__main__.py` (Anfang von `main`)
- Test: `tests/test_p1_cli.py`

**Interfaces:**
- Consumes: `fulltape.download_tape/condense/write_tape`, `chainfeeds.ChainClient/block_at/sync_feed/compact_feed/scan_emitters/decode_vol_log/svi_vol/VOL_FEEDS/VOL_DATA_UPDATED`, `refdata.save_all`, `classify.build_fills`, `api.DeriveClient/expiry_date_str`.
- Produces: `p1cli.to_ms(iso: str) -> int`, `p1cli.main(argv: list[str] | None) -> None`; Befehle `python3 -m derive_surface p1 tape --end ISO [--start ISO] [--workers N]`, `p1 volfeed [CCY…] --end ISO [--workers N] [--window N]`, `p1 compact [CCY…]`, `p1 ref`, `p1 fills [--vaults CSV]`; Skript schreibt `docs/paper1/feed_check.md`.

- [ ] **Step 1: Failing tests schreiben**

`tests/test_p1_cli.py`:

```python
from __future__ import annotations

import pytest

from derive_surface import p1cli
from derive_surface.__main__ import main


def test_to_ms_assumes_utc():
    assert p1cli.to_ms("2026-09-17T12:00:00") == 1_789_646_400_000
    assert p1cli.to_ms("2026-09-17T14:00:00+02:00") == 1_789_646_400_000


def test_p1_is_routed_and_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["p1", "--help"])
    assert exc.value.code == 0
    assert "volfeed" in capsys.readouterr().out


def test_existing_cli_still_parses():
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag prüfen**

Run: `python3 -m pytest -q tests/test_p1_cli.py`
Expected: FAIL mit `ImportError: cannot import name 'p1cli'`

- [ ] **Step 3: Implementierung**

`derive_surface/p1cli.py`:

```python
"""``python3 -m derive_surface p1 <command>``: data layer of paper 1 (adverse selection on Derive)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from pathlib import Path
from typing import List, Optional

ROOT = Path("data/p1")
VAULTS = Path("docs/paper1/meta/vault_wallets.csv")
TAPE_START = "2024-01-01T00:00:00"
CORE = ["BTC", "ETH", "HYPE"]


def to_ms(iso: str) -> int:
    d = dt.datetime.fromisoformat(iso)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp() * 1000)


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="derive_surface p1", description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("tape", help="full option tape (all underlyings, both rows per fill)")
    s.add_argument("--start", default=TAPE_START)
    s.add_argument("--end", required=True, help="inclusive end, ISO time (UTC if no offset)")
    s.add_argument("--workers", type=int, default=6)
    s = sub.add_parser("volfeed", help="VolDataUpdated history from Derive Chain")
    s.add_argument("currencies", nargs="*", default=CORE)
    s.add_argument("--end", required=True, help="last block at or before this ISO time")
    s.add_argument("--workers", type=int, default=4)
    s.add_argument("--window", type=int, default=5_000)
    s = sub.add_parser("compact", help="monthly SVI parquet files from the fetched chunks")
    s.add_argument("currencies", nargs="*", default=CORE)
    sub.add_parser("ref", help="settlements, liquidations, maker programmes, vaults, fees, funding")
    s = sub.add_parser("fills", help="pair rows into fills and classify takers")
    s.add_argument("--vaults", type=Path, default=VAULTS)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if a.cmd == "tape":
        from .api import DeriveClient
        from .fulltape import condense, download_tape, write_tape

        raw = a.root / "raw" / "tape" / "option"
        manifest = download_tape(DeriveClient(), raw, to_ms(a.start), to_ms(a.end), workers=a.workers)
        files = write_tape(condense(raw, manifest), a.root / "tape")
        report = {k: v for k, v in manifest.items() if k != "leaves"}
        report["files"] = files
        print(json.dumps(report, indent=1))
    elif a.cmd == "volfeed":
        from .chainfeeds import ChainClient, block_at, sync_feed

        client = ChainClient()
        to_block = block_at(client, to_ms(a.end) // 1000)
        for ccy in a.currencies:
            print(json.dumps(sync_feed(client, ccy, a.root / "raw" / "volfeed", to_block, workers=a.workers, window=a.window)))
    elif a.cmd == "compact":
        from .chainfeeds import compact_feed

        for ccy in a.currencies:
            print(ccy, json.dumps(compact_feed(a.root / "raw" / "volfeed", ccy, a.root / "volfeed")))
    elif a.cmd == "ref":
        from .api import DeriveClient
        from .refdata import save_all

        print(json.dumps(save_all(DeriveClient(), a.root / "ref"), indent=1, default=str))
    elif a.cmd == "fills":
        from .classify import build_fills

        out = a.root / "derived" / "fills.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        summary = build_fills(a.root / "tape", a.root / "ref", a.vaults, out)
        (a.root / "derived" / "fills_summary.json").write_text(json.dumps(summary, indent=1, default=str))
        print(json.dumps({k: v for k, v in summary.items() if k != "classes"}, indent=1))
```

`derive_surface/__main__.py` — in `main` vor `p = argparse.ArgumentParser(...)` einfügen:

```python
    import sys

    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "p1":
        from .p1cli import main as p1_main

        p1_main(argv[1:])
        return
```

`scripts/p1_check_feeds.py`:

```python
"""Check the three core vol-feed addresses over time and against Derive's live mark IV.

1. Continuity: sample 200-block windows every 500 000 blocks, list every VolDataUpdated emitter and flag
   any unknown emitter whose forward lies within 20 % of a core feed's forward (a possible replacement feed).
2. Reproduction: decode the latest on-chain SVI of the three nearest expiries per core currency and compare
   svi_vol with the mark IV of every live option of that expiry.

Writes docs/paper1/feed_check.md.  Run from the repository root: python3 scripts/p1_check_feeds.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from derive_surface.api import DeriveClient, OptionName, expiry_date_str  # noqa: E402
from derive_surface.chainfeeds import VOL_DATA_UPDATED, VOL_FEEDS, ChainClient, decode_vol_log, scan_emitters, svi_vol  # noqa: E402

OUT = Path("docs/paper1/feed_check.md")


def main() -> None:
    chain = ChainClient()
    head = chain.block_number()
    blocks = list(range(2_500_000, head, 500_000))
    emitters = scan_emitters(chain, blocks, span=200)
    known = {spec["address"]: ccy for ccy, spec in VOL_FEEDS.items()}
    emitters["feed"] = emitters["address"].map(known).fillna("other")
    lines = ["# Vol-Feed-Prüfung", "",
             f"Lauf {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}, Kopf-Block {head}, "
             f"{len(blocks)} Stichproben zu je 200 Blöcken ab Block 2 500 000 im Abstand 500 000.", "",
             "## Kontinuität", "", "| Feed | Stichproben mit Events | erste | letzte | Forward erste → letzte |", "|---|---|---|---|---|"]
    for ccy in VOL_FEEDS:
        g = emitters[emitters["feed"] == ccy].sort_values("sample_block")
        if g.empty:
            lines.append(f"| {ccy} | 0 | – | – | – |")
            continue
        lines.append(f"| {ccy} | {len(g)} | {g.sample_block.iloc[0]} | {g.sample_block.iloc[-1]} | "
                     f"{g.fwd.iloc[0]:,.2f} → {g.fwd.iloc[-1]:,.2f} |")
    conflicts = []
    for block, g in emitters.groupby("sample_block"):
        for _, core in g[g["feed"] != "other"].iterrows():
            rivals = g[(g["feed"] == "other") & ((g["fwd"] / core["fwd"] - 1).abs() < 0.2)]
            for _, r in rivals.iterrows():
                conflicts.append(f"| {block} | {core['feed']} {core['fwd']:,.2f} | {r['address']} {r['fwd']:,.2f} |")
    lines += ["", "## Mögliche Ersatz-Feeds (unbekannte Adresse mit Forward ±20 % eines Kern-Feeds)", ""]
    lines += (["| Block | Kern-Feed | Kandidat |", "|---|---|---|"] + conflicts) if conflicts else ["Keine."]
    lines += ["", "## Gegenprobe SVI gegen Live-Mark-IV", "",
              "| Underlying | Verfall | Optionen | max. |Δ IV| | Median |Δ IV| | Alter der SVI (s) |", "|---|---|---|---|---|---|"]
    api = DeriveClient()
    for ccy, spec in VOL_FEEDS.items():
        latest = {}
        for entry in chain.get_logs(spec["address"], VOL_DATA_UPDATED, head - 900, head):
            d = decode_vol_log(entry)
            latest[d["expiry"]] = d
        now = time.time()
        for expiry in sorted(e for e in latest if e > now + 3600)[:3]:
            d = latest[expiry]
            tickers = api.tickers(ccy, expiry_date_str(expiry))
            strikes = np.array([OptionName.parse(n).strike for n in tickers])
            marks = np.array([float(t["option_pricing"]["i"]) for t in tickers.values()])
            model = svi_vol(strikes, d["svi_a"], d["svi_b"], d["svi_rho"], d["svi_m"], d["svi_sigma"], d["svi_fwd"], d["svi_ref_tau"])
            diff = np.abs(model - marks)
            lines.append(f"| {ccy} | {expiry_date_str(expiry)} | {len(marks)} | {np.nanmax(diff):.5f} | "
                         f"{np.nanmedian(diff):.5f} | {now - d['feed_ts']:.0f} |")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q tests/test_p1_cli.py`
Expected: `3 passed`

- [ ] **Step 5: Gesamtsuite und Commit**

Run: `python3 -m pytest -q` → Expected: `58 passed`

```bash
git add derive_surface/p1cli.py derive_surface/__main__.py scripts/p1_check_feeds.py tests/test_p1_cli.py
git commit -m "paper1: p1 CLI and vol-feed check script

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Kuratierte Vault-Wallets

**Files:**
- Create: `docs/paper1/meta/vault_wallets.csv`

**Interfaces:**
- Produces: CSV mit Kopfzeile `wallet,vault_name,source` (optional weitere Spalten `chain_note,verified_on`), lesbar mit `classify.load_vault_wallets`.

- [ ] **Step 1: Quellen auswerten**

Aus https://help.derive.xyz/en/articles/9351681-vault-smart-contracts (und verlinkten Artikeln der Sammlungen „Vaults“ und „Safe Harvest Vaults“) alle Tabellenzeilen mit Chain „Derive“ extrahieren: das sind die TSA-Token-Verträge (Tokenized SubAccounts) auf Derive Chain, die als Wallet im Tape erscheinen. Bridges, Connectors und Adressen anderer Chains nicht aufnehmen. Zusätzlich die Vault-Namen aus `get_vault_statistics` (10 Vaults) zuordnen. Jede Adresse mit der URL, aus der sie stammt.

- [ ] **Step 2: Gegenprobe gegen den Tape**

Nach Task 7 Step 1 (Tape geladen):

```bash
python3 - <<'EOF'
import pandas as pd
from pathlib import Path
from derive_surface.classify import load_vault_wallets
tape = pd.concat([pd.read_parquet(p, columns=["wallet","liquidity_role","rfq_id","currency"]) for p in Path("data/p1/tape").glob("*_options_full.parquet")])
v = load_vault_wallets(Path("docs/paper1/meta/vault_wallets.csv"))
hit = tape[tape.wallet.isin(v)]
print(len(v), "vault wallets,", hit.wallet.nunique(), "seen on the tape")
print(hit.groupby(["wallet","liquidity_role"]).size().unstack(fill_value=0))
print("rfq share of vault rows:", hit.rfq_id.notna().mean())
EOF
```

Expected: mindestens ein Teil der Adressen erscheint als Taker mit hohem RFQ-Anteil (Vault-Rolls laufen per RFQ-Auktion). Adressen ohne einen einzigen Tape-Treffer bleiben in der Liste, werden aber im Datenstand ausgewiesen.

- [ ] **Step 3: Commit**

```bash
python3 -m pytest -q
git add docs/paper1/meta/vault_wallets.csv
git commit -m "paper1: curated vault wallet list with sources

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Pilotläufe und Datenstand

**Files:**
- Create: `docs/paper1/DATENSTAND.md`, `docs/paper1/feed_check.md` (vom Skript)
- Daten: `data/p1/…` (nicht versioniert)

**Interfaces:**
- Consumes: alle CLI-Befehle aus Task 5.
- Produces: `data/p1/tape/*_options_full.parquet`, `data/p1/ref/*`, `data/p1/raw/volfeed/<CCY>/*.parquet`, `data/p1/volfeed/<CCY>_svi_<YYYY-MM>.parquet`, `data/p1/derived/fills.parquet`, `fills_summary.json`, `wallet_month_stats.parquet`.

- [ ] **Step 1: Tape bis zum Pilot-Stichtag**

Run: `nohup caffeinate -dimsu python3 -m derive_surface p1 tape --end 2026-09-17T12:00:00 > data/p1/logs_tape.txt 2>&1 &` (vorher `mkdir -p data/p1`)
Expected (nach ca. 30–60 min): letzte Zeile des JSON mit `rows_in_windows` gleich `api_count` (≈ 1 229 000), `files` mit 12 Underlyings. Bei Abweichung: Lauf wiederholen (Fenster-Dateien bleiben), dann Differenz je Tag untersuchen.

- [ ] **Step 2: Referenzdaten**

Run: `python3 -m derive_surface p1 ref`
Expected: `settlement_prices` für 12 Underlyings, `liquidations` mit `reported_count` und `unique_auctions`, `maker_programmes.active_wallets` > 0, `funding_rows` ≈ 2 160.

- [ ] **Step 3: Vol-Feed kalibrieren**

Run: `python3 -m derive_surface p1 volfeed BTC --end 2024-01-20T00:00:00 --workers 4`
Expected: rund 13 Stücke ab Block 2 400 000, Log-Zeile mit `events/s`. Danach dieselbe Stichprobe für ein spätes Fenster: `python3 - <<'EOF'` mit `sync_feed` auf `to_block=44_000_000` für eine Test-Currency ist nicht nötig; stattdessen Durchsatz aus dem Log ablesen und die Gesamtdauer für ~38 Mio Events schätzen. Liegt sie über 12 h, `--workers 6` und `--window 10000` verwenden.

- [ ] **Step 4: Vol-Feed voll im Hintergrund**

Run: `nohup caffeinate -dimsu python3 -m derive_surface p1 volfeed BTC ETH HYPE --end 2026-09-17T12:00:00 --workers 4 > data/p1/logs_volfeed.txt 2>&1 &`
Expected: läuft Stunden; Fortschritt mit `tail -3 data/p1/logs_volfeed.txt`; bei Abbruch denselben Befehl erneut starten (fertige Stücke werden übersprungen). Vor dem Start `pmset -g batt` prüfen: Netzteil nötig.

- [ ] **Step 5: Feed-Prüfung**

Run: `python3 scripts/p1_check_feeds.py`
Expected: jeder Kern-Feed mit Events in allen Stichproben nach seinem Start (BTC/ETH ab 2 500 000, HYPE ab 31 000 000), keine Ersatz-Kandidaten; Gegenprobe median |Δ IV| < 0,001 bei SVI-Alter unter ~60 s (grössere Abweichungen nur, wenn der Ticker schon eine neuere Kurve nutzt; dann Lauf wiederholen).

- [ ] **Step 6: Fills und Klassen**

Voraussetzung: Task 6 abgeschlossen.
Run: `python3 -m derive_surface p1 fills`
Expected: `fills` ≈ Hälfte der Zeilen, `unpaired_rows` klein und erklärt, `pair_mismatch` = 0 oder erklärt, `not_settled` ausgewiesen.

- [ ] **Step 7: Nach Abschluss des Vol-Feed-Laufs verdichten**

Run: `python3 -m derive_surface p1 compact BTC ETH HYPE`
Expected: Monatsdateien 2024-01 … 2026-09 für BTC/ETH, 2025-10/11 … 2026-09 für HYPE.

- [ ] **Step 8: `docs/paper1/DATENSTAND.md` schreiben**

Inhalt: Stichtag und Abrufzeit je Datensatz; Zeilen je Underlying (aus `data/p1/tape/MANIFEST.json`) mit SHA-256; `rows_in_windows` vs `api_count`; Fills, ungepaarte Zeilen, Paar-Abweichungen, nicht-settled; Klassenverteilung je Underlying (Fills und Notional) aus `fills_summary.json`, aber **keine Markouts**; Liquidationen gemeldet vs gefunden; Maker-Programme und aktive Wallets; Vault-Wallets gelistet vs im Tape gesehen; Vol-Feed-Events je Currency und Monat, Plattenbedarf (`du -sh data/p1/*`); Ergebnis der Feed-Prüfung; offene Punkte.

- [ ] **Step 9: Commit**

```bash
python3 -m pytest -q
git add docs/paper1/DATENSTAND.md docs/paper1/feed_check.md
git commit -m "paper1: pilot data status (no markouts)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Abweichungen während der Ausführung (17.09.2026)

Der Code im Repo ist massgeblich; die Blöcke oben zeigen den Stand vor diesen Änderungen.

- `fulltape`: Zahltypen erzwungen float64 (Ganzzahl-Strings ergaben int64). Die Gesamtzahl der API ist nicht additiv; statt dessen `recount_days` mit Neuladen abweichender Tage (`download_tape(max_refetch=2)`), `day_mismatches` und `api_count_full_range` im Manifest. `SETTLE_MS = 60 min` (RFQ-Maker-Zeilen bis 28 min vor dem Fill gestempelt): Stichtag muss zurückliegen, Cache nur nach Ablauf gültig. CLI schreibt nichts bei abweichenden Tagen. Tape-Start 2023-12-01 (erster Fill 06.12.2023).
- `api.DeriveClient.call`: unlesbare Antworten (leerer Body bei HTTP 200) werden wiederholt statt abzustürzen.
- `refdata.liquidations`: Tagesfenster parallel (6 Worker), Seitengrösse 100 mit Rückfall 20/5 (erster Erfolg gilt; alle Grössen liefern dieselben Auktionen, Gebote unvollständig), Halbierung bis 1 h, Lücken im Ergebnis; CLI nutzt `max_retries=3`. Eine zwischenzeitliche Vereinigung über Seitengrössen war unnötig und sehr langsam.
- `classify.in_mm_programme`: prüft jede Epoche, die den Fill enthält (überlappende Programme).
- `chainfeeds`: Spalte `block_ts` (Push-Zeit), `OTHER_FEEDS`, Startblöcke BTC/ETH 800 000 und HYPE 29 000 000.
- `p1cli.to_ms`: akzeptiert `Z`.
- `scripts/p1_check_feeds.py`: Stichproben ab Block 800 000 alle 250 000; führt den letzten Kern-Forward mit, listet Lücken und unbekannte Emitter.
- Kalibrierung Vol-Feed: 5 800 Events/s mit 4 Workern, 43 Bytes je Event; zwei Prozesse parallel lösen anfangs HTTP 429 aus, danach stabil.
- Adversariale Prüfung (2 Prüfer, 11 Befunde, 6 bestätigt) vor den langen Läufen; alle 6 eingearbeitet, Regressionstests ergänzt (68 Tests).

## Folgepläne

- **Plan 2 (Markouts und Inferenz):** beim Laden der SVI-Historie nach `block <= to_block` des Stichtags filtern (die Stück-Dateien können über den Stichtag hinausreichen); `markouts.py` (Pfade a/b/c/d, drei Einheiten, Zellen, Ausschlüsse, Sweeps), `inference_p1.py` (Panel mit FE, Wild-Cluster-Bootstrap, Placebo, Lorenz, Netto-Edge), Tardis-Monatserste mit Grössenprobe, HYPE-Listungsdatum belegen. Voraussetzung: Präregistrierung committet, finaler Lauf zum Stichtag 30.09.2026 08:00 UTC (`p1 tape --end 2026-09-30T08:00:00`, `p1 volfeed … --end 2026-09-30T08:00:00`).
- **Plan 3:** Abbildungen T1, T2, 1–5, A.
- **Plan 4:** Manuskript (CAS), Zahlenblatt, zwei Prüfer, SSRN.
