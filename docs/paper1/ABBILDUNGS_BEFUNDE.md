# Befunde, die beim Bau der Abbildungen entstanden sind

Stand: 18.09.2026, Abschnitt 2 revidiert am 25.09.2026. Pilotstichprobe mit Stichtag 17.09.2026 12:00 UTC,
603 940 Fills.
Nichts hiervon aendert die Praeregistrierung; es sind beschreibende Zusatzgroessen fuer die Abbildungen.

## 1. Der registrierte Netto-Edge in USDC ist keine Landkarte, sondern ein Preisniveau

Die registrierte H4-Groesse ist der Netto-Edge in USDC je Kontrakt. Ueber die Zellen gerechnet steigt sie
fast monoton mit der Laufzeit, fuer BTC von rund 10 USDC bei <= 2 Tagen auf 200 bis 300 USDC jenseits von
90 Tagen. Das misst vor allem, dass lange Optionen teuer sind. Fuer die Frage, wo ein Market Maker quotieren
soll, ist der Edge je eingegangenem Risiko die richtige Groesse.

## 2. Je Nominal ist die Marge dort am duennsten, wo der Flow liegt

Revidiert am 25.09.2026 (Nachtrag 3 der Praeregistrierung, Befund `BEFUND_2026-09-25_GEBUEHRENEINHEIT.md`). Die
erste Fassung dieses Abschnitts teilte den Netto-Edge je Kontrakt durch das Nominal des ganzen Fills und zog
Gebuehr und Rebate als Summen des Fills ab. Ihre Tabelle (BTC 9,0 / 28,5 / 73,8, ETH 0,9 / 3,3 / 4,8, HYPE
0,3 / 0,5 / 0,1) und die Aussagen dazu (gleiche Ordnung in allen Basiswerten, eine Groessenordnung zwischen den
Basiswerten, HYPE praktisch null) stammten aus diesem Einheitenfehler. Richtig ist der Edge des Fills durch
sein Nominal, also 10^4 x NE je Kontrakt / Index.

Median-Netto-Edge in Basispunkten des Nominals, Zellen ab 200 Fills:

| Basiswert | ATM, <= 2 d | ATM, 30 bis 90 d | tief im Geld, <= 2 d | Median ueber die Zellen | Spanne der Zellen |
|---|---|---|---|---|---|
| BTC | 2,8 | 5,8 | 15,5 | 3,3 | 0,9 bis 15,6 |
| ETH | 3,8 | 9,8 | 15,5 | 5,7 | -82,8 bis 28,8 |
| HYPE | 5,0 | 27,2 | 11,8 | 15,1 | -6,2 bis 68,8 |

- In jedem Basiswert und jeder Delta-Zeile unter 75 liegt der Edge bei ueber 90 Tagen beim 2,5- bis 10-Fachen
  des Werts bei <= 2 Tagen. Streng monoton ist die Karte nicht: ETH steigt bis 75 Delta auch mit dem Delta,
  BTC und HYPE streuen mehr. Die Zeilen tief im Geld mit wenigen Fills brechen das Muster (ETH 90-100 ueber
  90 Tage -82,8 bp bei 325 Fills, HYPE 75-90 <= 2 d -6,2 bp).
- Die Ordnung der Basiswerte kehrt sich gegenueber USDC je Kontrakt um: BTC zahlt je Kontrakt am meisten und je
  Nominal am wenigsten, HYPE je Nominal am meisten.
- Wo der Flow liegt, ist die Marge duenn: Optionen bis 7 Tage mit |Delta| unter 60 tragen rund 46 % der BTC-
  und der ETH-Fills und bringen 1,0 bis 2,8 bp (BTC) bzw. 1,6 bis 3,8 bp (ETH).

Die Abbildung zur Praktiker-Landkarte zeigt deshalb beide Einheiten: USDC je Kontrakt als registrierte
Groesse und Basispunkte des Nominals als die Groesse, nach der ein Bot entscheidet.

## 3. Der Beispiel-Fill fuer die Mechanismus-Abbildung ist echt

T1 zeigt ETH-20250110-3600-C, 04.01.2025 12:38 UTC, Taker der Klasse other, kein RFQ. Der Maker kauft
1,00 Kontrakt zu 125,00 gegen eine Kurve, die 125,41 sagt, verdient also 0,41 USDC Halbspread. Dreissig
Minuten spaeter steht die Kurve bei 121,69: adverse Selektion -3,72, Markout -3,31 USDC. Die Kurve zum Fill
war 23 Sekunden alt. Gewaehlt wird der Fill von `figdata.example_fill`: Klasse other, Halbspread positiv,
Markout unter minus Halbspread, Nominal am naechsten am Median.

Stand 25.09.2026: Eine fruehere Fassung dieses Abschnitts nannte BTC-20260807-64000-C (01.08.2026, Maker
verkauft zu 496,68 gegen 473,98, Markout -172,78 USDC, zweibeinige RFQ). Dieser Fill erscheint in keiner
Abbildung mehr.

## 4. Die beiden Markenpfade stimmen ueberein, sobald der Vergleich fair ist

| Gruppe | Fills | Korrelation | Vorzeichen gleich | Median-Abstand |
|---|---|---|---|---|
| alle | 540 531 | 0,390 | 69,1 % | 0,022 |
| naechster Fill <= 300 s spaeter | 26 885 | 0,896 | 91,3 % | -0,005 |
| naechster Fill <= 3 600 s spaeter | 135 971 | 0,939 | 83,5 % | 0,007 |
| Kurve <= 60 s alt | 501 384 | 0,397 | 68,8 % | 0,023 |

Die schwache Gesamtkorrelation kommt vom Median-Abstand des naechsten Fills von 15 026 Sekunden, nicht von
der Kurve: bei frischer Kurve aendert sich fast nichts, bei zeitnahem Vergleichsfill steigt die Korrelation
auf 0,94.
