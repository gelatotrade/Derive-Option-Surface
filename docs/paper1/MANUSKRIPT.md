# Manuskript von Paper 1

Abnahmeprotokoll. Erstfassung am Ende von Plan 5 (19.09.2026), Revision am 25.09.2026 nach dem
Befund zur Gebuehreneinheit (`BEFUND_2026-09-25_GEBUEHRENEINHEIT.md`, Nachtrag 3 der Praeregistrierung,
Aenderungsliste in `REVISION_2026-09-25.md`). Der Wortzaehler ist `scripts/p1_wordcount.py`; das Budget gilt je
Abschnitt mit 10 % Toleranz.

| Abschnitt | Erstfassung | Revision | Budget | Stand |
|---|---|---|---|---|
| abstract | 156 | 156 | 150 | im Budget |
| Introduction | 571 | 571 | 550 | im Budget |
| The venue and the tape | 396 | 396 | 450 | im Budget |
| What a markout measures | 419 | 484 | 550 | im Budget |
| Pre-registration and inference | 239 | 270 | 250 | im Budget (Grenze 275) |
| Results | 1025 | 1198 | 1100 | im Budget (Grenze 1210) |
| What this means for a maker | 353 | 378 | 350 | im Budget (Grenze 385) |
| What this cannot show | 238 | 238 | 250 | im Budget |
| Conclusion | 177 | 181 | 180 | im Budget |
| **Summe** | **3574** | **3872** | **3 830** | |

Die Revisionsnotiz auf Seite 1 steht als Titelfussnote (`\tnotetext`) vor `\maketitle` und zaehlt nicht.

## Bau (Revision)

| Groesse | Wert |
|---|---|
| Seiten | 9 |
| Abbildungen | 9, davon 8 zweispaltig |
| Literatureintraege gesamt | 24 |
| davon zitiert | 22 |
| Ueberlaufende Zeilen | keine |
| Abbildungspruefung (`scripts/p1_figure_check.py`) | 29 Pruefungen, 0 abweichend |
| Upload-Datei | `paper/Derive Orderbook Adverse Selection.pdf` = Kopie von `paper/main.pdf` |

Bildunterschriften: `derive_surface/figures_p1.py`, `CAPTIONS`, wortgleich mit `paper/main.tex` (T2, F1, F2 und F5
in der Revision angepasst). Jeder Literatureintrag wurde gegen Verlagsseite, RePEc oder DOI geprueft.

## Offen

- SSRN: Revision hochladen, Abstract-Feld und Revisionsbeschreibung aus `REVISION_2026-09-25.md`.
- Enddatenlauf mit dem registrierten Stichtag 30.09.2026 08:00 UTC; danach alle Zahlen im Text gegen das neue
  Zahlenblatt pruefen und als weitere Revision hochladen.
- Push oder Pull Request fuer das oeffentliche Repo ist eine Nutzerentscheidung.
