# Abbildungen von Paper 1

Erzeugt von `scripts/p1_figure_check.py`. Die Spalte *geprueft* vergleicht, was die Abbildung
zeichnet, mit dem, was der Inferenzlauf in `results/p1` entschieden hat.

| Abbildung | Breite | Datei | Quelle |
|---|---|---|---|
| T1 | 21 kB | `paper/figures/t1.pdf` | one fill from markouts.parquet plus its neighbours |
| T2 | 21 kB | `paper/figures/t2.pdf` | markouts.parquet, cluster bootstrap per component |
| F1 | 23 kB | `paper/figures/f1.pdf` | markouts.parquet, four readings of the same column |
| F2 | 21 kB | `paper/figures/f2.pdf` | markouts.parquet, balanced subsample |
| F3 | 24 kB | `paper/figures/f3.pdf` | class_means.csv and the implied vols of markouts.parquet |
| F4 | 21 kB | `paper/figures/f4.pdf` | h1_lorenz.csv and summary.json |
| F5 | 41 kB | `paper/figures/f5.pdf` | h4_cells.csv, h4_sensitivity.csv and markouts.parquet |
| F6 | 25 kB | `paper/figures/f6.pdf` | markouts.parquet by month and summary.json |
| A1 | 22 kB | `paper/figures/a1.pdf` | markouts.parquet and path_agreement.csv |

## Geprueffte Zahlen

| Abbildung | Groesse | gezeichnet | registriert | stimmt |
|---|---|---|---|---|
| T2 | the five components add up to the net edge | 8.93245 | 8.93245 | ja |
| T2 | half spread plus adverse selection is the markout | 13.0506 | 13.0506 | ja |
| F1 | mean markout, 30 min | 13.0506 | 13.0506 | ja |
| F3 | class mean, dominant_maker | -25.4141 | -25.4141 | ja |
| F3 | wallets behind dominant_maker | 17 | 17 | ja |
| F3 | class mean, other | 24.7319 | 24.7319 | ja |
| F3 | wallets behind other | 10749 | 10749 | ja |
| F4 | top ten share against the Lorenz curve | 0.905372 | 0.905372 | ja |
| F5 | share of positive cells | 0.494845 | 0.494845 | ja |
| F5 | sensitivity at the registered half spread reproduces the headline | 0.494845 | 0.494845 | ja |
| F6 | placebo estimates available for the histogram | 100 | 100 | ja |

Bildunterschriften stehen in `derive_surface/figures_p1.py` unter `CAPTIONS` und gehen von
dort ins Manuskript.
