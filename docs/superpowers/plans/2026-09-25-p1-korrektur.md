# Paper 1: Korrektur der Gebühreneinheit (Revision für SSRN) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Paper 1 so korrigieren, dass Gebühr, Rabatt und die Karte je Nominal die registrierte Einheit „USDC je Kontrakt“ tatsächlich einhalten, alle betroffenen Zahlen, Abbildungen und Textstellen nachziehen und eine revidierte PDF für SSRN bauen.

**Architecture:** Branch `paper1-korrektur` von `paper1-adverse-selection`. Kleinste Code-Korrektur an der Quelle (`inference_p1.analysis_frame` und die Stellen, die rohe Gebühren- oder Nominal-Spalten lesen), testgetrieben mit Fills der Menge ≠ 1. Danach Neulauf der Inferenz und Abbildungen auf den Pilotdaten (Schnitt 17.09.2026 12:00 UTC), unabhängige Nachrechnung gegen `scripts/p1_befund_gebuehreneinheit.py`, Textrevision mit Revisionsnotiz, Audit, Bau.

**Tech Stack:** Python 3.9.6, pandas, numpy, matplotlib, pytest, tectonic.

**Befund:** `docs/paper1/BEFUND_2026-09-25_GEBUEHRENEINHEIT.md` (Ursache, Zahlen alt und neu, betroffene Stellen, Code-Empfehlung).

## Global Constraints

- Nur Paper-1-Dateien ändern (`derive_surface/*p1*`, `figdata.py`, `figures_p1.py`, `figures_social.py`, `classify.py` nur falls nötig, `scripts/p1_*`, `tests/test_p1_*`, `results/p1/`, `docs/paper1/`, `paper/`). Nichts unter `data/p2/` oder `paper2/` anfassen.
- Die Präregistrierung wird nicht überschrieben: nur ein datierter Nachtrag 3 am Ende von `docs/paper1/PRAEREGISTRIERUNG.md`. Der Präregistrierungs-Commit `3fd9caa` bleibt die Referenz im Manuskript.
- Hypothesen, Schwellen und Stichprobe bleiben unverändert; geändert wird nur die Einheit, in der die registrierte Definition umgesetzt ist.
- Agenten committen nicht; der Orchestrator committet mit ausgewählten Pfaden (nie `git add -A`, weil `data/p2/` und `paper2/` hier nicht ignoriert sind).
- Papier englisch, Doku deutsch, keine Gedankenstriche im Fliesstext, Wortbudgets von Paper 1 einhalten.

## Tasks

### K1: Nachtrag 3 zur Präregistrierung
- [ ] Datierter Nachtrag: Gebühr und Rabatt sind im Tape Summen je Fill; NE je Kontrakt = MO − (fee − rebate)/Menge − Hedge; die Karte je Nominal teilt die Summe des Edge durch die Summe des Nominals (oder NE je Kontrakt durch Index je Kontrakt); Ursache, Entdeckung am 25.09.2026, keine Änderung an Hypothesen oder Schwellen.

### K2: Code-Korrektur (testgetrieben)
- [ ] Fehlschlagende Tests mit Fills der Menge 0,1 und 5: NE je Kontrakt, Wasserfall-Identität (HS + AS − Gebühr + Rabatt − Hedge = NE), Klassentabelle, bp-Karte je Nominal.
- [ ] `inference_p1.analysis_frame`: Spalten `fee_pc`, `rebate_pc` je Kontrakt; `net_edge` daraus.
- [ ] Wasserfall, T2-Fehlerbalken und Klassentabelle (`figdata.py`, `inference_p1.py`) lesen die Spalten je Kontrakt.
- [ ] F5 (`figures_p1.py`) und S5 (`figures_social.py`): bp je Nominal konsistent (NE je Kontrakt geteilt durch Index je Kontrakt).
- [ ] F1c/F2c: Prämienanteil und Markout-Einheiten je Kontrakt.
- [ ] Suite grün.

### K3: Neulauf auf den Pilotdaten
- [ ] Inferenz (`python3 -m derive_surface p1 …`), Abbildungen, Zahlenblatt, Abbildungsprüfung.

### K4: Unabhängige Nachrechnung
- [ ] Alle geänderten Kopfzahlen gegen `results/p1_befund/gebuehreneinheit.csv` (erzeugt mit `scripts/p1_befund_gebuehreneinheit.py`); Abweichungen klären.

### K5: Manuskript und Begleitmaterial
- [ ] Alle betroffenen Stellen laut Befund (Abstract, Zerlegung, Klassen inkl. Vorzeichenwechsel Vault, H4-Abschnitt, Karte je Nominal, Schluss), Revisionsnotiz auf Seite 1 (Datum der Erstfassung 19.09.2026, Revision 25.09.2026, was korrigiert wurde).
- [ ] `docs/paper1/ZAHLENBLATT.md`, `ABBILDUNGS_BEFUNDE.md`, `MANUSKRIPT.md`, `paper/social/x_article.md` und die Karten S1/S5; neuer Text für das SSRN-Abstract-Feld und eine kurze Korrekturnotiz für X in `docs/paper1/REVISION_2026-09-25.md`.
- [ ] Bau mit `python3 scripts/p1_build.py`, Wortbudget, Abbildungsprüfung; Upload-Datei `paper/Derive Orderbook Adverse Selection.pdf` ersetzen.

### K6: Audit der Revision
- [ ] Zahlen (Text gegen results), Inhalt (Referee: stimmt jede Aussage nach der Korrektur, fair formulierte Revisionsnotiz), Form (Layout, Abbildungen, Gedankenstriche); Befunde beheben; Schlussbau.
