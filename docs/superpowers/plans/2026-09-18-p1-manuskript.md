# Paper 1, Plan 5: Manuskript

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein fertiges, kompaktes Manuskript im Elsevier-CAS-Satz, das die neun Abbildungen trägt und sonst so wenig Text wie möglich enthält. Zielgrösse 12 bis 13 Seiten, davon rund 5 Seiten Abbildungen, rund 3 800 Wörter Fliesstext.

**Architecture:** Der Text erklärt nichts, was eine Abbildung zeigt. Jeder Abschnitt hat ein hartes Wortbudget und eine Liste der Behauptungen, die er aufstellen muss. Zahlen stehen im Fliesstext nur, wenn sie das Argument tragen; alles andere steht in den Abbildungen. Jede Einschränkung wird genau einmal gemacht, in Abschnitt 7, ausser sie ändert die Lesart eines Ergebnisses.

**Tech Stack:** LaTeX, Elsevier CAS (`cas-dc`), tectonic; Literatur in `paper/refs.bib`.

**Sprache:** Das Manuskript ist englisch, wie Titel und Bildunterschriften. Die Projektdokumentation bleibt deutsch.

## Global Constraints

- Jede Zahl im Fliesstext muss in `results/p1` oder in einer Abbildung nachweisbar sein. Keine Zahl ohne Verweis auf die Abbildung, die sie zeigt.
- Kein Absatz wiederholt, was eine Bildunterschrift schon sagt.
- Drei der vier präregistrierten Hypothesen sind abgelehnt. Das wird im Abstract genannt, nicht versteckt, und der Beitrag wird darauf aufgebaut.
- Einschränkungen genau einmal, gesammelt in Abschnitt 7. Ausnahme: wo eine Einschränkung die Lesart eines Ergebnisses ändert, steht ein Halbsatz an der Stelle und der Verweis auf Abschnitt 7.
- Keine Literaturangabe ohne geprüfte Felder. Ungeprüfte Einträge tragen ein `note`-Feld und dürfen nicht zitiert werden.
- Der Pilot mit Stichtag 17.09.2026 trägt den Text. Vor der Abgabe ersetzt der Enddatenlauf mit Stichtag 30.09.2026 alle Zahlen; deshalb steht jede Zahl im Text auch in `docs/paper1/ZAHLENBLATT.md`.

## Wortbudget

| Abschnitt | Wörter | trägt welche Abbildung |
|---|---|---|
| Abstract | 150 | — |
| 1 Introduction | 550 | — |
| 2 The venue and the tape | 450 | — |
| 3 What a markout measures | 550 | T1, T2 |
| 4 Pre-registration and inference | 250 | — |
| 5 Results | 1 100 | F1 bis F6 |
| 6 What this means for a maker | 350 | F5 |
| 7 What this cannot show | 250 | A1 |
| 8 Conclusion | 180 | — |
| **Summe** | **3 830** | |

Abweichung nach oben höchstens zehn Prozent je Abschnitt. Ein Abschnitt, der sein Budget reisst, wird gekürzt, nicht das Budget erhöht.

## Dateien

| Datei | Verantwortung |
|---|---|
| `paper/main.tex` | Manuskript |
| `paper/refs.bib` | geprüfte Literatur |
| `scripts/p1_wordcount.py` | zählt je Abschnitt und meldet Budgetüberschreitungen |
| `docs/paper1/MANUSKRIPT.md` | Abnahmeprotokoll: Wortzahl je Abschnitt, Seitenzahl, offene Punkte |

---

### Task 1: Gerüst, Wortzähler und Abnahme

**Files:**
- Create: `scripts/p1_wordcount.py`, `tests/test_p1_wordcount.py`
- Modify: `paper/main.tex`

**Interfaces:**
- Produces: `sections(tex: str) -> dict[str, int]`, `check(tex_path, budget) -> list[dict]`, CLI `python3 scripts/p1_wordcount.py`
- Zählt Wörter je `\section`, ohne Abbildungsumgebungen, ohne Bildunterschriften, ohne Literatur.

- [x] **Step 1: Test schreiben** — ein `.tex`-Schnipsel mit zwei Abschnitten, einer Abbildung und einer Bildunterschrift; erwartet wird, dass die Abbildung und ihre Unterschrift nicht mitzählen und dass ein gerissenes Budget gemeldet wird.
- [x] **Step 2: Test laufen lassen** → FAIL
- [x] **Step 3: Implementieren**
- [x] **Step 4: Tests grün, Commit**

---

### Task 2: Abschnitte 1 bis 4, der Rahmen

**Files:** `paper/main.tex`

**Was Abschnitt 1 behaupten muss (550 Wörter):**
- Auf einem Buch, dessen Gegenpartei on chain sichtbar ist, lässt sich zum ersten Mal messen, gegen wen ein Optionsmaker verliert, statt es aus Handelsgrösse und Aggressivität zu erraten.
- Der mittlere Markout des Makers ist positiv, aber das ist fast vollständig eine Aussage über die Gegenpartei, nicht über die Option.
- Drei Beiträge: die vollständige Zerlegung der Maker-Marge auf einem Tape mit identifizierter Gegenpartei; der Konzentrationsbefund und sein Scheitern an den üblichen Toxizitätsmassen; die Quotierlandkarte je Delta und Laufzeit.
- Vierter Beitrag, ausdrücklich: vier vor jeder Messung festgelegte Hypothesen, drei davon abgelehnt. Das Papier berichtet die Ablehnungen als Ergebnis.
- Erlaubte Zahlen: +15,70 Halbspread, −2,65 adverse Selektion, +8,93 Netto-Edge, Median 0,98, Top-10-Anteil 90,5 Prozent, dominante Maker −25,41 gegen sonstige Taker +24,73.

**Was Abschnitt 2 behaupten muss (450 Wörter):**
- Derive führt das Buch ausserhalb der Kette und siedelt auf einer eigenen OP-Stack-Kette ab; der Mark ist keine Meinung des Autors, sondern eine SVI-Kurve, die der Handelsplatz selbst je Verfall on chain schreibt.
- Das öffentliche Tape ist nicht anonym: Wallet, Subaccount, RFQ-Kennung, Gebühren, Rabatt und realisierter PnL stehen darin. Genau das macht die Frage messbar.
- Stichprobe, Basiswerte, Zeitraum, Fillzahl.
- Was nicht öffentlich ist: die Historie des Buchs, also alles, was quotiert und nie gehandelt wurde. Ein Satz, Verweis auf Abschnitt 7.

**Was Abschnitt 3 behaupten muss (550 Wörter), getragen von T1 und T2:**
- Definition des Markouts und der Vorzeichenkonvention, in zwei Sätzen, Rest zeigt T1.
- Die Identität Halbspread plus adverse Selektion gleich Markout, und Markout minus Gebühr plus Rabatt minus Hedge gleich Netto-Edge. Ein Satz dazu, dass der Halbspread im Markout enthalten ist und nicht doppelt gezählt wird.
- Drei Markenpfade, warum die On-Chain-Kurve der Hauptpfad ist. Ein Satz, Verweis auf A1.
- Die vier Einheiten und warum es vier braucht. Verweis auf F1.
- Die Zuteilungskaskade der Gegenparteiklassen in einem Satz, Rest zeigt F3.

**Was Abschnitt 4 behaupten muss (250 Wörter):**
- H1 bis H4 im Wortlaut, je ein Satz, mit der Ablehnungsregel.
- Inferenz: Cluster auf Taker-Wallet, Wild-Cluster-Bootstrap mit B gleich 9 999 und festem Startwert, Instrument-mal-Tag-Fixeffekte, Perzentilintervalle aus einem Paar-Bootstrap.
- Ein Satz zur Präregistrierung mit Datum und Commit, und dass zwei datierte Nachträge existieren.

- [x] **Step 1:** Abschnitte 1 bis 4 schreiben
- [x] **Step 2:** `python3 scripts/p1_wordcount.py` → jeder Abschnitt im Budget
- [x] **Step 3:** tectonic baut ohne Überlauf
- [x] **Step 4:** Commit

---

### Task 3: Abschnitt 5, die Ergebnisse

**Files:** `paper/main.tex`

**1 100 Wörter, sechs Unterabschnitte, je einer je Abbildung. Reihenfolge und Kernsatz:**

1. *Reading the number* (F1, 180 Wörter). Der Mittelwert ist kein Handelsergebnis. Median 0,98 gegen Mittelwert 13,05, kontraktgewichtet 0,264. Die drei Basiswerte tragen fast dieselbe Dollarsumme bei Indexpreisen, die sich um den Faktor 1 599 unterscheiden. Daraus folgt die Leseregel für alles Weitere.
2. *How long adverse selection lasts* (F2, 180 Wörter). Auf der balancierten Teilmenge ist der Markout über fünf Horizonte flach. Adverse Selektion ist nicht das, was die Marge frisst. Professioneller Fluss liegt durchweg unter null, übriger Fluss darüber.
3. *Who the counterparty is* (F3, 200 Wörter). Die Klassenmittel, die Clusterzahlen, die beiden p-Werte über fünf Prozent. Der entscheidende Satz: die beiden Verlustklassen handeln bereits mit negativem Halbspread, sind also beim Einstieg auf der besseren Seite des Marks, bevor adverse Selektion überhaupt einsetzt. Das ist eine andere Aussage als informiert.
4. *Concentration, and why H1 fails* (F4, 200 Wörter). 90,5 Prozent bei zehn Wallets, ein einziges trägt 39 Prozent, aber Grösse und Sweep erklären unter Fixeffekten nichts. 98,8 und 92,4 Prozent verbinden den Konzentrations- mit dem Klassenbefund.
5. *Where the edge survives, and why H4 fails* (F5, 200 Wörter). 48 von 97 Zellen positiv, drei negativ, alle ETH. Der Befund kippt zwischen null und einem Basispunkt unterstellter Perp-Spanne. Je Nominal ist die Landkarte monoton in Delta und Laufzeit.
6. *The sample is not one market, and why H3 fails* (F6, 140 Wörter). Zusammensetzungswechsel über 33 Monate, HYPE tritt erst im November 2025 ein, MM-Programm erst ab November 2024. Der DiD-Schätzer liegt mitten in der Placebo-Verteilung.

**Regel:** Kein Unterabschnitt wiederholt eine Zahl, die schon in einem früheren steht.

- [x] **Step 1:** Abschnitt 5 schreiben
- [x] **Step 2:** Wortzähler und tectonic
- [x] **Step 3:** Commit

---

### Task 4: Abschnitte 6 bis 8, Literatur, Abstract

**Files:** `paper/main.tex`, `paper/refs.bib`

**Abschnitt 6 (350 Wörter):** Was ein Maker aus der Landkarte macht. Wo quotieren, wo nicht, und warum die Einheit Basispunkte des Nominals und nicht USDC je Kontrakt ist. HYPE trägt im Median 0,1 bis 0,6 Basispunkte und damit praktisch nichts. Ein Absatz dazu, dass die Konzentration ein Handelsargument ist: zehn Adressen zu erkennen ist billiger, als Grösse und Aggressivität zu modellieren, weil letztere nachweislich nichts erklären.

**Abschnitt 7 (250 Wörter), jede Einschränkung genau einmal:** der Mark ist der Mark des Handelsplatzes selbst, A1 zeigt, dass das die Zielgrösse nicht bewegt; Pfad (a) ist bei 30 Minuten keine Gegenprobe; Wallets können mehrere Adressen halten, die Konzentration ist eine Untergrenze; die Vault-Klasse hat acht Wallets, H2 ist ein Hinweis und kein Beweis; Liquidationen laufen ausserhalb des Trade-Tapes; die Vol-Einheit fehlt für 10 745 Fills; die Historie des Buchs fehlt, also alles, was quotiert und nie gehandelt wurde.

**Abschnitt 8 (180 Wörter):** Was bleibt, wenn drei Hypothesen fallen.

**Abstract (150 Wörter):** Gegenstand, Stichprobe, die Zerlegung mit drei Zahlen, der Konzentrationsbefund, die drei Ablehnungen, der Satz für den Praktiker.

**Literatur:** aus `paper/refs_verified.bib` übernehmen, nur geprüfte Einträge zitieren. Mindestens Mikrostrukturtheorie, Optionsmikrostruktur, DeFi-Marktstruktur, SVI und die Bootstrap-Methodik.

- [x] **Step 1:** Abschnitte 6 bis 8 und Abstract schreiben
- [x] **Step 2:** Literatur einbauen, jedes Zitat gegen `refs.bib` prüfen
- [x] **Step 3:** Wortzähler, tectonic, Seitenzahl prüfen
- [x] **Step 4:** `docs/paper1/MANUSKRIPT.md` schreiben
- [x] **Step 5:** Commit
