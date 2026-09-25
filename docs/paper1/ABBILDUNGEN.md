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
| F5 | 39 kB | `paper/figures/f5.pdf` | h4_cells.csv, h4_sensitivity.csv and markouts.parquet |
| F6 | 25 kB | `paper/figures/f6.pdf` | markouts.parquet by month and summary.json |
| A1 | 22 kB | `paper/figures/a1.pdf` | markouts.parquet and path_agreement.csv |

## Geprueffte Zahlen

| Abbildung | Groesse | gezeichnet | registriert | stimmt |
|---|---|---|---|---|
| T2 | the five components add up to the net edge | 9.57949 | 9.57949 | ja |
| T2 | half spread plus adverse selection is the markout | 13.0506 | 13.0506 | ja |
| T2 | maker fee step is the fee of the fill over its amount | -1.09111 | -1.09111 | ja |
| T2 | maker rebate step is the rebate of the fill over its amount | 0.769454 | 0.769454 | ja |
| F1 | mean markout, 30 min | 13.0506 | 13.0506 | ja |
| F1 | median markout share of the premium, per contract and per fill agree | 3.4292 | 3.4292 | ja |
| F3 | class mean, dominant_maker | -25.4141 | -25.4141 | ja |
| F3 | wallets behind dominant_maker | 17 | 17 | ja |
| F3 | class mean, other | 24.7319 | 24.7319 | ja |
| F3 | wallets behind other | 10749 | 10749 | ja |
| Klassen | maker fee per contract, dominant_maker | 2.75189 | 2.75189 | ja |
| Klassen | net edge per contract, dominant_maker | -31.9846 | -31.9846 | ja |
| Klassen | maker fee per contract, large | 1.35385 | 1.35385 | ja |
| Klassen | net edge per contract, large | 0.794406 | 0.794406 | ja |
| Klassen | maker fee per contract, mm_programme | 1.82023 | 1.82023 | ja |
| Klassen | net edge per contract, mm_programme | -26.7605 | -26.7605 | ja |
| Klassen | maker fee per contract, other | 0.961932 | 0.961932 | ja |
| Klassen | net edge per contract, other | 22.0418 | 22.0418 | ja |
| Klassen | maker fee per contract, rfq | 0.29791 | 0.29791 | ja |
| Klassen | net edge per contract, rfq | 11.7994 | 11.7994 | ja |
| Klassen | maker fee per contract, vault | 1.1297 | 1.1297 | ja |
| Klassen | net edge per contract, vault | 2.08756 | 2.08756 | ja |
| F4 | top ten share against the Lorenz curve | 0.905372 | 0.905372 | ja |
| F5 | share of positive cells | 0.762887 | 0.762887 | ja |
| F5 | median bp of notional, BTC [40,60) <=2d | 2.80783 | 2.80783 | ja |
| F5 | median bp of notional, ETH [40,60) <=2d | 3.78446 | 3.78446 | ja |
| F5 | median bp of notional, HYPE [40,60) <=2d | 4.96248 | 4.96248 | ja |
| F5 | sensitivity at the registered half spread reproduces the headline | 0.762887 | 0.762887 | ja |
| F6 | placebo estimates available for the histogram | 100 | 100 | ja |

Bildunterschriften stehen in `derive_surface/figures_p1.py` unter `CAPTIONS` und gehen von
dort ins Manuskript.
