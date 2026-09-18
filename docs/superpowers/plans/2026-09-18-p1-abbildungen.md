# Paper 1, Plan 4: Abbildungen

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sieben Abbildungen plus eine Anhangsabbildung, die die Theorie und die Befunde des Papers tragen, sodass die Prosa auf das gekürzt werden kann, was die Abbildungen nicht zeigen. Jede Abbildung entsteht aus getesteten Aggregationen, baut im CAS-Layout und stimmt mit dem Zahlenblatt überein.

**Architecture:** `derive_surface/figures_p1.py` hält eine Registry `FIGURES` mit einer Funktion je Abbildung; jede Funktion bekommt den Analyse-Rahmen, die Ergebnisdateien und ein Ausgabeverzeichnis und gibt die geschriebenen Pfade zurück. Gezeichnet wird mit `figstyle` (CAS-Breiten, feste Klassenfarben), gerechnet mit `figdata` (Median-Cluster-Bootstrap, Delta-Tenor-Matrix, Wochenreihe, Wasserfall). CLI `p1 figures`. Ein Prüfskript vergleicht die Zahlen in den Abbildungen gegen `results/p1`.

**Tech Stack:** Python 3.9.6, matplotlib 3.9 (Agg), numpy, pandas; pytest; tectonic für den Einbau ins Manuskript.

**Grundlage:** Entwurfs-Workflow vom 18.09.2026 (drei Blickwinkel: Mechanismus, Empirie, Praktiker; zwei Juroren: Referee, Gestaltung). Die Auswahl je Slot steht in Task 2.

## Global Constraints

- Constraints aus Plan 1 bis 3 gelten weiter (Python 3.9, keine neuen Abhängigkeiten, Tests offline, lokale Commits mit Trailer).
- Breiten: einspaltig 3,4 Zoll, zweispaltig 7,0 Zoll; Schrift 8 pt; Ausgabe PDF (Manuskript) und PNG (Kontrolle) nach `paper/figures/`.
- Farben nur aus `figstyle.PALETTE`; Klassen immer in `figstyle.CLASS_COLORS`; jede Abbildung muss in Graustufen lesbar bleiben (Form, Strichart oder Schraffur zusätzlich zur Farbe).
- Jede Abbildung ist ohne Bildunterschrift verständlich: Achsen mit Einheit, Vorzeichenkonvention genannt, Stichprobengrösse sichtbar.
- Keine Zahl in einer Abbildung, die nicht aus `data/p1/derived/markouts.parquet` oder `results/p1/` stammt; Prüfskript vergleicht Kernzahlen gegen `results/p1/summary.json`.
- Ehrlichkeit: Mittelwerte nie ohne Median oder Verteilung; Zellen unter 200 Fills werden nicht eingefärbt; Klassen mit wenigen Wallets zeigen ihre Wallet-Zahl (dominante Maker 17, MM-Programm 33, Vaults 8, gross 104, RFQ 4 512, sonstige 10 749).
- Vol-Punkte nur für |Δ| ≤ 90 zeigen: bei tief im Geld liegenden Optionen geht die Vega gegen null und die Vol-Einheit explodiert (Pilot: 21 Vol-Punkte im Bucket 90–100 bei ≤ 2 d).
- Pilotdaten. Die Abbildungen des Manuskripts entstehen mit dem Stichtag 30.09.2026; der Code bleibt gleich.

## Dateien

| Datei | Verantwortung |
|---|---|
| `derive_surface/figures_p1.py` | Registry und je eine Funktion pro Abbildung |
| `derive_surface/p1cli.py` | Unterbefehl `figures` |
| `scripts/p1_figure_check.py` | vergleicht Abbildungszahlen mit `results/p1`, schreibt `docs/paper1/ABBILDUNGEN.md` |
| `tests/test_p1_figures.py` | Offline-Tests je Abbildung (Rauchtest plus geprüfte Eigenschaften) |
| `paper/figures/*.pdf`, `*.png` | Ausgabe |

---

### Task 1: Registry, CLI und Rauchtests

**Files:**
- Create: `derive_surface/figures_p1.py` (Registry und Gerüst), `tests/test_p1_figures.py`
- Modify: `derive_surface/p1cli.py`

**Interfaces:**
- Consumes: `figstyle.figure/save/CLASS_COLORS/CLASS_LABELS/CLASS_ORDER/robust_limits`, `figdata.horizon_curve/cell_matrix/weekly_series/waterfall_components/example_fill`, `inference_p1.analysis_frame`, `markouts.HORIZONS_S`.
- Produces:
  - `FIGURES: dict[str, callable]` mit den Schlüsseln `T1, T2, F1, F2, F3, F4, F5, A1`
  - jede Funktion `fig_x(frame: pd.DataFrame, results: dict, out_dir: Path) -> list[Path]`
  - `load_inputs(root: Path, results_dir: Path) -> (frame, results)`
  - `build(root: Path, results_dir: Path, out_dir: Path, only: Sequence[str] = None) -> dict[str, list[Path]]`
  - CLI `python3 -m derive_surface p1 figures [--only T1,F1] [--out paper/figures]`

- [ ] **Step 1: Test schreiben** (`tests/test_p1_figures.py`)

```python
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from derive_surface import figures_p1  # noqa: E402

T0 = 1_735_689_600_000
WEEK = 7 * 86_400_000


def frame(n=600, seed=0):
    rng = np.random.default_rng(seed)
    classes = np.array(["other", "rfq", "dominant_maker", "mm_programme", "large", "vault"])
    f = pd.DataFrame({
        "trade_id": [f"t{i}" for i in range(n)],
        "ts": T0 + rng.integers(0, 8 * WEEK, n),
        "currency": rng.choice(["BTC", "ETH", "HYPE"], n),
        "instrument_name": ["BTC-20250131-100000-C"] * n,
        "taker_class": rng.choice(classes, n),
        "cluster": rng.choice([f"w{i}" for i in range(25)], n),
        "delta_bucket": rng.choice(["00-10", "25-40", "40-60", "90-100"], n),
        "tenor_bucket": rng.choice(["<=2d", "7-30d", ">90d"], n),
        "abs_delta_pct": rng.uniform(1, 99, n),
        "tenor_days": rng.uniform(0.5, 120, n),
        "notional": rng.lognormal(9, 1.2, n),
        "price": rng.lognormal(4, 1, n),
        "mark_b_t": rng.lognormal(4, 1, n),
        "maker_side": rng.choice([-1, 1], n),
        "hs": rng.normal(2.0, 3.0, n),
        "as_usd": rng.normal(-0.5, 2.0, n),
        "net_edge": rng.normal(1.0, 3.0, n),
        "fee_maker": np.abs(rng.normal(0.4, 0.1, n)),
        "rebate_maker": np.abs(rng.normal(0.1, 0.05, n)),
        "hedge": np.abs(rng.normal(0.5, 0.2, n)),
        "svi_age_s_t": np.abs(rng.normal(30, 20, n)),
        "is_sweep": rng.random(n) < 0.1,
        "size_above_p90": rng.random(n) < 0.1,
        "expiry": (T0 + 30 * 86_400_000) // 1000,
        "strike": 100_000.0,
        "option_type": rng.choice(["C", "P"], n),
    })
    for h in ("1m", "5m", "30m", "4h", "24h"):
        f[f"mo_usd_{h}"] = rng.normal(1.5, 6.0, n)
        f[f"mo_dn_{h}"] = f[f"mo_usd_{h}"] - rng.normal(0, 0.5, n)
        f[f"mo_vol_{h}"] = rng.normal(2.0, 4.0, n)
        f[f"mo_usd_a_{h}"] = f[f"mo_usd_{h}"] + rng.normal(0, 1.0, n)
        f[f"lag_a_{h}_s"] = np.abs(rng.normal(600, 400, n))
        f[f"iv_b_{h}"] = np.abs(rng.normal(0.6, 0.1, n))
        f[f"mark_b_{h}"] = f["mark_b_t"] + rng.normal(0, 1, n)
        f[f"fwd_b_{h}"] = 100_000 + rng.normal(0, 100, n)
    f["iv_fill"] = np.abs(rng.normal(0.6, 0.1, n))
    f["iv_mark_t"] = np.abs(rng.normal(0.6, 0.1, n))
    f["fwd_t"] = 100_000.0
    f["delta_t"] = rng.uniform(-1, 1, n)
    f["mo_set"] = rng.normal(1.0, 8.0, n)
    f["mo_set_vrp"] = rng.normal(0.0, 8.0, n)
    f["month"] = pd.to_datetime(f["ts"], unit="ms").dt.strftime("%Y-%m")
    return f


def results():
    return {
        "summary": {"fills": 600, "horizon": "30m", "half_spread_bp": 1.0, "missing_vol_unit": 12,
                    "H1": {"top10_share": {"share": 0.905, "lo": 0.698, "hi": 0.943, "loss_total": -3_240_781, "wallets": 25},
                           "size_coefficient": {"beta": -0.76, "t": -0.74, "p": 0.476},
                           "sweep_coefficient": {"beta": -0.36, "t": -0.10, "p": 0.944}, "rejected": True},
                    "H2": {"markout_30m": {"mean": 4.22, "lo": 1.64, "hi": 8.55, "p": 0.0075, "n": 1994, "clusters": 8},
                           "settlement_vrp": {"mean": -6.37, "lo": -17.79, "hi": 5.14}, "rejected": False},
                    "H3": {"did": {"beta": -1.05, "t": -1.23, "p": 0.24, "n": 147_240, "clusters": 3879,
                                   "placebos": 100, "placebo_share_more_extreme": 0.46, "window_days": 90,
                                   "event_ms": 1_782_205_200_000}, "rejected": True},
                    "H4": {"cells": 97, "share_positive": 0.495, "atm_short": [], "rejected": True}},
        "cells": pd.DataFrame({"currency": ["BTC", "ETH"], "delta_bucket": ["40-60", "25-40"],
                               "tenor_bucket": ["<=2d", "7-30d"], "fills": [8902, 23718],
                               "mean": [23.9, 0.4], "lo": [7.2, -0.4], "hi": [44.8, 1.3],
                               "positive": [True, False]}),
        "classes": pd.DataFrame({"class": ["other", "dominant_maker"], "fills": [329_432, 56_274],
                                 "mean_hs": [25.6, -16.6], "mean_as": [-0.87, -8.81], "mean": [24.73, -25.41],
                                 "lo": [21.9, -28.1], "hi": [28.1, -19.9], "mean_fee": [1.24, 1.23],
                                 "mean_rebate": [0.57, 0.08], "mean_hedge": [2.87, 3.93],
                                 "mean_ne": [21.19, -30.49], "share_negative": [0.27, 0.676],
                                 "mean_dn": [25.3, -16.0], "mean_vol": [3.6, -1.3]}),
        "lorenz": pd.DataFrame({"wallet_share": np.linspace(0.01, 1.0, 50), "loss_share": np.linspace(0.39, 1.0, 50)}),
        "horizons": pd.DataFrame({"horizon": ["1m", "5m", "30m", "4h", "24h"], "n": [600] * 5,
                                  "mean": [15.2, 13.3, 13.1, 13.1, 13.0], "mean_dn": [15.7, 15.6, 15.5, 15.4, 16.0],
                                  "mean_vol": [2.6, 2.6, 2.6, 2.5, 1.9], "mean_path_a": [13.0, 12.8, 12.5, 12.6, 13.2]}),
        "sensitivity": pd.DataFrame({"half_spread_bp": [0.0, 1.0, 3.0], "cells": [97, 97, 97],
                                     "share_positive": [0.557, 0.505, 0.381]}),
        "paths": pd.DataFrame({"group": ["all", "lag_a <= 300 s", "svi_age <= 60 s"], "fills": [540_531, 26_885, 501_384],
                               "correlation": [0.390, 0.896, 0.397], "sign_agreement": [0.691, 0.913, 0.688],
                               "median_gap": [0.022, -0.005, 0.023], "median_lag_a_s": [15_026, 118, 15_047]}),
    }


@pytest.mark.parametrize("name", sorted(figures_p1.FIGURES))
def test_every_figure_writes_pdf_and_png(tmp_path, name):
    paths = figures_p1.FIGURES[name](frame(), results(), tmp_path)
    assert [p.suffix for p in paths] == [".pdf", ".png"]
    assert all(p.exists() and p.stat().st_size > 1500 for p in paths)
    assert all(p.stem.startswith(name.lower()) for p in paths)


def test_registry_covers_the_planned_slots():
    assert sorted(figures_p1.FIGURES) == ["A1", "F1", "F2", "F3", "F4", "F5", "T1", "T2"]


def test_build_runs_a_subset(tmp_path, monkeypatch):
    monkeypatch.setattr(figures_p1, "load_inputs", lambda root, results_dir: (frame(), results()))
    out = figures_p1.build("data/p1", "results/p1", tmp_path, only=["T2", "F3"])
    assert sorted(out) == ["F3", "T2"] and all(len(v) == 2 for v in out.values())
```

- [ ] **Step 2: Test laufen lassen** → FAIL (`cannot import name 'figures_p1'`)

- [ ] **Step 3: Gerüst implementieren** — `derive_surface/figures_p1.py` mit `load_inputs`, `build`, `FIGURES` und den acht Funktionen (Inhalt in Task 2); CLI-Unterbefehl:

```python
    s = sub.add_parser("figures", help="build the manuscript figures")
    s.add_argument("--results", type=Path, default=Path("results/p1"))
    s.add_argument("--out", type=Path, default=Path("paper/figures"))
    s.add_argument("--only", default=None, help="comma separated figure keys, e.g. T1,F2")
```

```python
    elif a.cmd == "figures":
        from .figures_p1 import build

        only = a.only.split(",") if a.only else None
        written = build(a.root, a.results, a.out, only=only)
        print(json.dumps({k: [str(p) for p in v] for k, v in written.items()}, indent=1))
```

- [ ] **Step 4: Tests grün, Commit**

---

### Task 2: Die acht Abbildungen

Wird nach der Jury-Auswahl ergänzt (Slots T1, T2, F1 bis F5, A1) — je Abbildung Datenquelle, Panels, Achsen, Annotationen, Fallgruben und der Prosa-Absatz, den sie ersetzt.

---

### Task 3: Prüfskript und Einbau ins Manuskript

- [ ] `scripts/p1_figure_check.py`: liest `results/p1/summary.json` und die Abbildungsdaten, vergleicht die Kernzahlen (Klassenmittelwerte, Top-10-Anteil, Zellenanteil, Horizontverlauf) und schreibt `docs/paper1/ABBILDUNGEN.md` mit einer Zeile je Abbildung: Kennung, Titel, Datenquelle, geprüfte Zahlen, Breite, Dateigrösse.
- [ ] `paper/main.tex`: die acht Abbildungen mit Bildunterschriften einbauen, Platzhalter entfernen, mit tectonic bauen und prüfen, dass keine Abbildung über den Satzspiegel läuft (keine Overfull-hbox-Warnung über 5 pt).
- [ ] Commit mit den erzeugten PDFs.
