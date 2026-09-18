# Befunde, die beim Bau der Abbildungen entstanden sind

Stand: 18.09.2026, Pilotstichprobe mit Stichtag 17.09.2026 12:00 UTC, 603 940 Fills.
Nichts hiervon aendert die Praeregistrierung; es sind beschreibende Zusatzgroessen fuer die Abbildungen.

## 1. Der registrierte Netto-Edge in USDC ist keine Landkarte, sondern ein Preisniveau

Die registrierte H4-Groesse ist der Netto-Edge in USDC je Kontrakt. Ueber die Zellen gerechnet steigt sie
fast monoton mit der Laufzeit, fuer BTC von rund 10 USDC bei <= 2 Tagen auf 200 bis 300 USDC jenseits von
90 Tagen. Das misst vor allem, dass lange Optionen teuer sind. Fuer die Frage, wo ein Market Maker quotieren
soll, ist der Edge je eingegangenem Risiko die richtige Groesse.

## 2. Je Nominal geordnet, ist die Landkarte monoton und zwischen den Basiswerten vergleichbar

Median-Netto-Edge in Basispunkten des Nominals (Nominal = Menge x Indexpreis), Zellen ab 200 Fills:

| Basiswert | ATM, <= 2 d | ATM, 30 bis 90 d | tief im Geld, <= 2 d |
|---|---|---|---|
| BTC | 9,0 | 28,5 | 73,8 |
| ETH | 0,9 | 3,3 | 4,8 |
| HYPE | 0,3 | 0,5 | 0,1 |

Die Ordnung ist in allen drei Basiswerten dieselbe: der Edge waechst mit dem Betrag des Delta und mit der
Laufzeit. Zwischen den Basiswerten liegt jeweils rund eine Groessenordnung. HYPE traegt im Median
zwischen 0,0 und 0,6 Basispunkten, also praktisch nichts.

Die Abbildung zur Praktiker-Landkarte zeigt deshalb beide Einheiten: USDC je Kontrakt als registrierte
Groesse und Basispunkte des Nominals als die Groesse, nach der ein Bot entscheidet.

## 3. Der Beispiel-Fill fuer die Mechanismus-Abbildung ist echt

BTC-20260807-64000-C, 01.08.2026. Der Maker verkauft zu 496,68 gegen eine Kurve, die 473,98 sagt, verdient
also 22,70 USDC Halbspread. Dreissig Minuten spaeter steht die Kurve bei 669,46, der Markout betraegt
-172,78 USDC. Die Kurve zum Fill war 25 Sekunden alt. Beide Kurven lassen sich aus dem On-Chain-Feed
rekonstruieren, der Fill gehoert zu einer zweibeinigen RFQ.

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
