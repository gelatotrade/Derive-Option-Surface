# Semantik von `public/get_margin`

Stand 24.09.2026, 10:49 bis 12:21 UTC. Gilt für BTC auf dem produktiven v2-Host `api.lyra.finance`.
Grundlage sind fünf Untersuchungsagenten und sechs adversariale Prüfer mit zusammen rund 9 800
protokollierten Anfragen an API und Chain 957, dazu Vertragscode `derivexyz/v2-core` in Commit
`96796a6` und die Doku unter docs.derive.xyz. Rohdaten liegen unter `data/p2/semantik_20260924/`
(nicht im Git), kleine Tabellen unter `results/p2/semantik/`.

Alle Zahlen sind Erkundung, keine präregistrierte Messung. Für das Papier werden sie mit getestetem
Code unter einem Versuchsplan neu erhoben.

## 1. Kurzantwort

**Was liefert die Methode?** Für X ∈ {IM, MM} gibt sie Netto-Margin zurück:

    net_X(q; C) = C + V_eng(q) − R_X(q)

Dabei ist C der Collateralwert, V_eng der Marktwert der Positionen in der Bewertung des Managers und
R_X die Anforderung. Positiv heisst gedeckt. Die Doku nennt die Werte „net margin“ und erklärt sie als
„mark-to-market value minus the requirement“.

**pre gegen post.** `pre_*` ist `net` für `simulated_positions` und `simulated_collaterals`. `post_*`
ist derselbe Zustand, nachdem `simulated_position_changes` und `simulated_collateral_changes` addiert
wurden. Ohne changes sind beide gleich, bis auf 1 bis 2 ULP. Beide rechnen innerhalb einer Anfrage
zum selben Preisstand. Zwischen zwei Anfragen wandert `pre` dagegen je nach Buch um einige USD bis
über 1 000 USD: 23 USD bei einem Testbuch im Sekundenabstand, bis 1 903 USD in 0,6 s bei grossen
Perp-Büchern.

**Rolle von `simulated_collaterals`.** USDC geht additiv mit Steigung genau 1 ein, auch negativ.
C hat deshalb keinen Einfluss auf R, verschiebt `net` aber 1:1 und entscheidet damit über die
Zulässigkeit. Andere Collaterals gehen mit Haircut ein. Unter PM2 wirkt BTC neben Positionen
risikomindernd und nicht linear (mit Short-Call: erster BTC +72 315 USD, zweiter +60 133 USD), ohne
Positionen linear.

**Vergleichbare Grösse.** Die Anforderung ist nicht `C − net`, denn das ist R − V und mischt
Positionswert und Margin. Primär empfohlen ist das Kapitalmass

    K_p(q) = Σ_Optionen p_i·q_i − net_IM(q; C = 0)

Es gibt die Einlage an, die man braucht, um das Buch q zu Preisen p zu eröffnen und die IM zu
erfüllen. K_p braucht kein V, nur die Handelspreise p, und ist direkt aus einer Anfrage ablesbar.
Seine Grenzform für eine Order Δq erhält man in einer einzigen Anfrage: positions = q, changes = Δq,
collateral_changes USDC = −p·Δq. Dann gilt ΔK = −(post − pre).

## 2. Was sonst zur Rückgabe gehört

| Punkt | Befund |
|---|---|
| `entry_price` | wirkt nur bei Perps, verschiebt `net` um −q·Δentry. Bei Optionen hat er keine Wirkung, auch nicht mit 0 oder 10·mark |
| Perps in changes | werden samt Einstandsbasis addiert, der Einstand wird mengengewichtet. Beim Schliessen bleibt der realisierte PnL in `post` |
| Perps in Σ p·q | gehören nicht hinein, weil ein Perp keine Prämie hat. Sonst entsteht ein Fehler von q·p |
| Fehler | Duplikat in einer der vier Listen: −32602, auch bei Menge 0. Fehlendes Pflichtfeld: −32602, eine leere Liste `[]` ist erlaubt. BTC unter null: 11020 |
| `market` | SM ignoriert ihn. PM2 verlangt ihn, fremde Währung ergibt 10015 |
| `margin_type` | `PM` ist der Legacy-PMRM und kein Alias. Er verlangt 1,6 bis 3,5 mal so viel wie PM2 und nimmt nur USDC. Für das Papier nur SM und PM2 verwenden |
| `is_valid_trade` | taugt nicht als Zulässigkeitsindikator. 27 von 82 konstruierten Fällen widersprechen der zunächst abgeleiteten Regel, alle 82 passen nur zu einer nachträglich angepassten Regel, die von ΔR und pre_MM abhängt. Zwei SM-Anfragen mit demselben Muster (pre == post, IM < 0 < MM) liefern verschiedene Urteile. Zulässig ist `post_initial_margin ≥ 0` |
| Open-Order-Margin | nicht enthalten, laut Doku |
| Grösse | R ist exakt positiv homogen vom Grad 1, von k = 1e−4 bis 1e7 bei SM, PM und PM2. OI-Caps und Ordergrenzen prüft die Methode nicht |
| Kontogrenze | SM auf v2: höchstens 63 Optionen plus Cash, bei 64 kommt 10007. PM2 akzeptiert mindestens 262 Positionen |
| Instrumentliste | `get_instruments` ist nicht reproduzierbar: 814 Einträge um 09:23 UTC, 820 um 11:20 UTC. Sie enthält 126 inaktive Instrumente. `get_margin` bewertet solche Instrumente trotzdem, belegt für 10 davon (Verfall 29.09.). Listen und Ticker je Messung archivieren |

## 3. Warum `C − net` nicht genügt und was V ist

Aus der Rückgabe folgt `C − net = R − V`. Bei einem Short-Buch aus tief im Geld liegenden Optionen
steckt der Prämienwert |V| darin und überdeckt die Anforderung. Ein Beispiel unter PM2: für den Short
BTC-20261030-110000-P liefert das On-Chain-Orakel `C − net` = 38 082 USD (API: 38 086 USD), davon
26 060 USD Positionswert und nur 12 022 USD Anforderung. Werden zwei Manager über `C − net` verglichen, drückt ein grosses |V| den
Quotienten gegen 1.

Unter SM erhalten Long-Optionen keine isolierte Gutschrift; ein reines Long-Buch ergibt `net = C`
exakt. Sie wirken nur über den Max-Loss-Zweig im selben Verfall, etwa in Spreads. Unter PM2 zählt ihr
Wert dagegen. In K_p erscheint die Long-Prämie unter SM deshalb meist voll als gebundenes Kapital.
Das ist ökonomisch richtig, gehört aber im Papier ausdrücklich gesagt.

**Die Engine-Anforderung R_eng = C + V_eng − net** braucht das V genau so, wie der Manager es
rechnet. Das ist nicht der Ticker-`mark_price`:

| Engine | Diskont D in V = D·B76(F, K, σ, τ) |
|---|---|
| SM auf v2 | D = 1, also V = M·F/S |
| PM2 auf v2 (`api.lyra.finance`) | D = e^(−0,02·τ), ein pauschaler Satz von 2 %, der nirgends dokumentiert ist |
| PM2 on-chain und PM2/SM auf v3 | D = e^(−r_feed·τ), mit r_feed 3,64 bis 3,82 % aus `LyraRateFeed` |
| Ticker | D = S/F aus der Basis. `mark_price` ist auf 1 USD gerundet, exakt ist M = −rho/τ |

Den Satz von 2 % haben zwei Prüfer unabhängig per Box-Spread gemessen: einer über alle 14 Verfälle
mit |r − 0,02| ≤ 3e−7 (`results/p2/semantik/box_diskont.json`, Wiederholung um 11:44 UTC), der andere
über 9 Verfälle mit |r − 0,02| < 1e−8 (`data/p2/semantik_20260924/verify-mtm/box_api.json`). Der Fehler, den man
macht, wenn man Ticker-Marks statt V_eng nimmt, wächst etwa mit (b − r_Engine)·τ·V:

| Laufzeit | 8 T | 36 T | 92 T | 183 T | 274 T | 1 J |
|---|---|---|---|---|---|---|
| SM v2 | +0,16 % | +0,48 % | +1,22 % | +2,60 % | +3,96 % | +5,33 % |
| PM2 v2 | +0,12 % | +0,28 % | +0,71 % | +1,58 % | +2,39 % | +3,25 % |

Median je Laufzeit. Quelle: `results/p2/semantik/v_konvention.json`, 24 Optionen um 11:22 UTC.

Es gilt K_p − R_eng = Σ p·q − V_eng. Der Unterschied zwischen beiden ist also eine
Bewertungskonvention und kein Kapital. Deshalb ist K_p der bessere Nenner für „Edge je Margin“,
R_eng dagegen die bessere Grösse für die Geometrie der Engine selbst.

**Live-Probe von K_p** (12:21 UTC, `results/p2/semantik/kapitalmass_check.jsonl`): Ein Buch mit vier
Beinen wird mit Einlage K und Prämienfluss zum Mark eröffnet. Das ergibt `net_IM` = −0,88 USD (SM,
K = 48 963 USD) bzw. −6,73 USD (PM2, K = 15 215 USD). Die Grenzform über pre/post trifft
K(q+Δ) − K(q) auf 0,88 bzw. 9,17 USD. Der Rest ist Preisdrift zwischen getrennten Anfragen.

## 4. Der Widerspruch 11 gegen 1,2 ist aufgelöst

Beide Originalskripte wurden in alten Sitzungsprotokollen gefunden. Die beiden Messungen hatten
**verschiedene Bücher** und lasen beide die Anforderung als `C − net`. Beide Bücher wurden nachgebaut und
am historischen Block nachgerechnet.

| | 17.09., 10:45 UTC | 24.09., 09:25 UTC |
|---|---|---|
| Verfälle | 25.09., 30.10., 27.11., 25.12.2026, 26.03.2027 (8 T bis 6 M) | die fünf ersten nach Datum, 25. bis 29.09. (höchstens 5 T) |
| Strikes | je Verfall die 10 dem Index nächsten, OTM-Seite | jedes (n/10)-te Instrument je Verfall. Am 25.09. von 20 000 bis 420 000 mit tief ITM Flügeln, am 26. bis 29.09. von 70 000 bis 95 000 |
| Fall B | streng abwechselnd nach Strike | zufällige Vorzeichen, `random.seed(7)` |
| Manager | PM2 und SM | PM2 und SM (nicht Legacy-PM) |
| Faktor SM/PM2 auf `C − net`, A / B | 2,33 / 11,86 | 1,46 / 1,19 |
| Faktor SM/PM2 auf R_eng, A / B | 3,19 / 10,76 | 3,61 / 2,14 |

IM, in Chain-Semantik am jeweiligen Block (PM2 per eth_call mit Feed-Zins, SM per Offline-Engine
mit D = 1). Der Unterschied zur API-Semantik ist bei diesen Büchern klein. Der Nachbau trifft die Originalzahlen auf
höchstens 374 USD. Quelle: `results/p2/semantik/faktoren.csv`.

Die Lücke im Fall B (11,86 gegen 1,19) hat zwei Ursachen:

1. **Das Buch.** Auf R_eng bleiben 10,76 gegen 2,14. Im Live-Kreuzversuch (11,69 gegen 2,12)
   erklärt die Instrumentauswahl etwa drei Viertel der Lücke (log), das Vorzeichenmuster etwa ein
   Viertel. Das exakte Buch vom 17.09. fällt mit den Vorzeichen vom 24.09. von 11,7 auf 4,5.
2. **Die Vermischung mit V.** Sie verdoppelt die Lücke ungefähr, von 5,0 auf R_eng zu 10,0 auf
   `C − net`. Das Buch vom 24.09. hatte V ≈ −497 000 USD.

Eine Parameteränderung ist ausgeschlossen. Alle 33 Parameter-Getter von SM, PM, PM2 und beiden Libs
liefern an beiden Blöcken bytegleiche Werte. Dazwischen gab es nur zweimal `LibOverrideUpdated` für
einzelne Konten.

Der Fall A zeigt dagegen keinen Widerspruch (3,19 gegen 3,61). Die Aussage „Netting etwa 11×“ gilt
auf R für ein gemischtes Buch nahe am Geld über mehrere Laufzeiten, heute 11,7× auf das exakte Buch
vom 17.09. Sie ist aber keine Konstante, sondern hängt stark vom Buch ab.

## 5. Zwei Engines und ein Schattenhost

| | Off-chain v2 (`api.lyra.finance`) | On-chain (Chain 957) | v3 (`api.derive.xyz/v3`) |
|---|---|---|---|
| Status | produktiv: UI und Trades laufen hierüber | Abwicklung, Liquidation und Auktionen | Schattenbetrieb: stündlicher Schnappschuss von v2, keine Trades |
| PM2-Diskont | pauschal 2 % | Rate-Feed 3,64 bis 3,82 % | Rate-Feed |
| Preise | frisch (Ticker) | Feeds hinken nach, Spot bis etwa 42 USD, Forward bis etwa 74 USD | frisch |
| Wofür | IM und Kontosicht (`margin_watch` stimmt mit `get_margin` bis auf Zinsen und uPnL überein, an 2 Konten geprüft) | MM für die Liquidation (DutchAuction.sol:163 bis 166), mit Kontenlib | nichts Produktives |

Drei Besonderheiten sind für das Papier wichtig:

1. **Override-Libs.** Seit dem 17.02.2026 haben nach und nach 15 Konten per `LibOverrideUpdated`
   eine eigene Lib mit mmFactor 0,35 statt 0,8 erhalten, die letzten zwei am 21.09.2026. Das gilt
   on-chain. `margin_watch` zeigte für das geprüfte Konto Xcaa362b31b die Standard-MM.
2. **Schwache On-Chain-Prüfung.** Ein vertrauenswürdiger Risk-Assessor prüft on-chain nur 3
   Spot-Szenarien plus Basis und Kontingenzen. Das sind 5 bis 34 % der vollen R_IM. Dass die Börse
   die volle IM off-chain durchsetzt, ist plausibel, aber nicht belegt.
3. **Abweichende Doku.** Die Doku beschreibt v3 (Put-Anforderung am Strike, vier Skew-Rails,
   einen Vol-Floor, der laut Tabelle nur für Up und laut Rechenbeispiel auch für Down gilt,
   `STATIC_RATE 0,05`). Für v2 ist sie nicht zitierfähig, für v2 gelten
   der Code und die On-Chain-Parameter.

API und On-Chain-Orakel stimmen deshalb nicht allgemein überein. Über 30 Zufallsbücher lag
|API − Orakel| bei IM im Median bei rund 265 USD (0,15 % von R_IM), im p90 je nach Quantilmethode
bei 10 800 bis 15 600 USD und im Maximum bei 207 000 USD (5,3 %). Die Differenz ist klein, solange Laufzeiten kurz sind oder ein
reguläres Szenario ein short-lastiges Buch bindet. Dann kürzt sich D heraus, weil δ⁻ = 1/D.

## 6. Eigenschaften für die Geometrie

- **Kegel.** R ist positiv homogen vom Grad 1. Die zulässige Menge {q : K_p(q) ≤ E} skaliert
  linear mit der Einlage E. Eine absolute „Bruchstelle“ in der Grösse gibt es in `get_margin` nicht.
  Sie kann nur relativ als Knick entlang eines Strahls q + tΔ entstehen oder von aussen kommen:
  Kapital, OI-Caps, Kontogrenzen, Open-Order-Margin, Liquidität.
- **SM ist nicht konvex.** Je Verfall gilt R_e = min(R_isoliert, R_MaxLoss), im Vertrag als max der
  negativen Margins geschrieben. Über Verfälle wird addiert. Das
  ergibt eine Vereinigung von bis zu 2^E Polyedern. Live bestätigt ist zum Beispiel eine
  Subadditivitätslücke von +9 959 USD IM bei Dezember-Puts. Eine Menge mit Einlage 24 916 USDC ist
  an beiden Enden zulässig und in der Mitte nicht.
- **PM2 ist praktisch konvex, streng genommen nicht.** R_PM2 ist konvex, solange kein
  Skew-Szenario bindet, in dem die Verfallssumme M_e das Vorzeichen wechselt. Die Ursache ist der
  Term |f(M_skew) − M| mit Knick im Static Discount. In 14 500 Mittelpunkttests auf natürlichen
  Zufallsbüchern trat keine Verletzung auf. In konstruierten, von Box-Spreads dominierten Büchern
  waren es live bis 1 284 USD (13 bis 18 % von R am Mittelpunkt). Die Schranke ist
  ½·Σ_e Δ_e·min|M_skew,e| mit Δ_e = δ⁻ − δ⁺. Δ_e liegt heute in Chain-Semantik zwischen 2,0 %
  (1 Tag) und 15,2 % (1 Jahr), auf der v2-API mit r = 2 % bei 1 Jahr bei etwa 13,3 %.
- **Altregime.** Vom 09.06.2025 bis zum 08.01.2026 war δ⁺ > δ⁻ für kurze Laufzeiten, ab dem
  12.06.2025 für Laufzeiten unter 73 Tagen, davor unter etwa 114 bzw. 45 Tagen. R_PM2
  war damals auch in regulären Szenarien nicht konvex (69 von 3 000 Tests, bis 478 USD).
- **Ruhende Bruchstellen.** Die Oracle-Kontingenz ist eine Stufe in der Feed-Konfidenz und derzeit
  ruhend (alle ≥ 0,95, Schwelle 0,55). Hinzu kommt maxExpiries 16.

## 7. Werkzeuge für den Versuchsplan

| Werkzeug | Treue | Grenzen |
|---|---|---|
| API direkt, pre/post | die IM der Off-chain-Engine, gleich der Kontosicht `margin_watch`; zwei Bücher je Anfrage zum selben Preisstand (PM2 mit neuem Verfall in den changes: Rest bis 1,13 USD) | Zulassung damit nicht geprüft. Rate-Limit für v2 undokumentiert; in den Logs aller Agenten Spitze etwa 3,75 Anfragen/s über 60 s ohne Rate-Limit-Fehler |
| SM-Nachbau (`sm_model.py`, `engine.py`) | `sm_model.py` trifft die API auf ≤ 0,012 % an einem Buch mit 50 Optionen; `engine.py` trifft die Originalwerte auf ≤ 374 USD | braucht Ticker-Feeds |
| PM2-Nachbau (`pm2_replica.py`, `pm2v.py`) | trifft die deployte Lib auf 4e−15 relativ, 20 000 Bücher in Sekunden | Chain-Semantik: für die API r = 2 % und Ticker-Feeds einsetzen, noch nicht validiert. Nach Spot-Fit an die API bleibt beim MM ein Rest von median 3,3 USD, p90 81 USD, max. 1 137 USD; mit Ticker-Feeds ungeprüft |
| eth_call-Orakel | Chain-exakt, auch historisch ab 13.06.2025 | Gas-Cap von 50 M, also höchstens etwa 150 bis 200 Beine |
| Box-Spread | liefert den Engine-Diskont je Verfall in einer Anfrage | an jedem Messtag prüfen, weil der Satz von 2 % undokumentiert ist |

Die Skripte liegen unter `data/p2/semantik_20260924/` in den Unterordnern `code-pm2/`,
`verify-konvex/`, `verify-widerspruch/` und `code-sm/`. Für das Papier werden sie testgetrieben neu
geschrieben und nicht übernommen.

## 8. Parameterhistorie PM2 BTC

PM2 für BTC existiert seit dem 09.06.2025 um 05:18 UTC. Der Rate-Feed war bis zum 12.06.2025 veraltet,
rekonstruierbar ist ab dem 13.06.2025. Änderungen laut Events (`results/p2/semantik/pm2_parameter_btc.json`):

| Datum (UTC) | Änderung |
|---|---|
| 09.06.2025 | Start. Gitter ±18 %, Vol +0,5/−0,3, Static Discount sBase/lBase 0,95/1,05. Am selben Tag 0,98/1,02 und Zins-Mult 0,1 |
| 12.06.2025 | Static Discount: Add 0,16 → 0,1, Mult 0,1 → 0 |
| 17.09.2025 | maxExpiries 10 → 14 |
| 10.10.2025 | confMargin 1,0 → 0,4 |
| 08.01.2026 | Static Discount gedreht auf sBase/lBase 1,02/0,98, seither ist R regulär konvex |
| 23.01.2026 | Tail-Gewichte gesenkt |
| 03.02.2026 | Upgrade auf PMRM_2_1, erlaubt Libs je Konto |
| ab 17.02.2026 | Kontenoverrides für 15 Konten (mmFactor 0,35) |
| 24.05.2026 | Gitter ±17 %, Vol up 0,45, Perp-Kontingenz 0,015 |
| 13.08.2026 | maxExpiries 16 |
| 20.08.2026 | Gitter ±14 %, Vol +0,40/−0,25, Kontingenzen halbiert. Überwiegend eine Lockerung, nur minVolUp steigt von 0,4 auf 0,5 |

Die SM-Optionsparameter für BTC sind seit dem 04.12.2023 unverändert. Die Legacy-PMRMLib emittiert
keine Events. Der Satz von 2 % der v2-API ist off-chain, deshalb ist die Historie der API nicht
rekonstruierbar, nur die der Chain-Semantik.

## 9. Korrekturen an der Übergabe

- „Anforderung = Kapital minus post_initial_margin“ ist R − V und keine Anforderung.
- „Portfolio-Margin“ war am 24.09. PM2. Der dortige Faktor 1,2 bis 1,5 folgt aus Buch und Lesart.
  Auf R_eng sind es 3,61 und 2,14.
- „Das Orakel liefert Margin-Salden“ heisst genauer: `net = C + V − R`.
- „Deterministische, öffentlich aufrufbare Funktion“ gilt nur für die Positions-IM der Off-chain-Engine.
  Sie nutzt einen undokumentierten Diskont von 2 % statt allein der On-Chain-Parameter. Nicht erfasst
  sind Open-Order-Margin, OI-Caps und die Liquidation, die on-chain mit Feed-Zins und Kontenlibs läuft.
- „PM2 nicht konvex“: streng richtig, aber anders begründet (Abschnitt 6). Deutlich nicht konvex ist SM.
- „Bruchstelle“: Einen absoluten Grösseneffekt gibt es nicht (Abschnitt 6).
- „814 aktive BTC-Optionen“: 814 war die Zahl der gelisteten Instrumente um 09:23 UTC. Um 11:20 UTC
  waren es 820, davon 694 aktiv.
- Zeitachse: Nach dem Start am 09.06.2025 gab es 8 Daten mit Parameteränderungen, dazu das Upgrade am
  03.02.2026 und Kontenoverrides ab 17.02.2026. Die jüngste Änderung war überwiegend eine Lockerung.

## 10. Entscheidungen vor dem Versuchsplan

1. **Engine.** Empfohlen ist v2 `api.lyra.finance` als Referenz, mit der Chain-Semantik als zweiter
   Engine für MM, Liquidation und Historie. v3 nur als Sensitivität.
2. **Nenner.** Empfohlen ist K_p, mit p gleich Mark oder gleich Fill-Preis aus Paper 1. R_eng
   dient als Engine-Grösse.
3. **IM oder MM.** Die IM steuert vermutlich die Zulassung (nicht belegt), die On-Chain-MM die
   Liquidation.
4. **Karte.** Einzelkontrakt je Zelle oder Grenzkosten in einem Referenzinventar. Als Inventar kommen
   synthetische Bücher, echte Maker-Konten per `margin_watch` oder aus Paper-1-Fills rekonstruierte
   Bücher in Frage.
5. **Haltedauer.** Edge ist ein Fluss, Kapital ein Bestand. Ohne Haltedauer ist „Edge je Margin“
   nicht definiert.
6. **Umfang.** Nur BTC oder auch ETH und HYPE, nur die PM2-Ära ab 13.06.2025 oder der ganze Zeitraum
   von Paper 1.
7. **Gliederung.** Teil 1 als „praktisch konvex, streng nicht, SM klar nicht“. Teil 3 als relativer
   Knick plus externe Grenzen.
