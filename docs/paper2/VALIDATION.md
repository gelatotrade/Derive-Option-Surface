# Validierung des Nachbaus gegen die Chain (Task B1)

Stand 25.09.2026, Pilotschnitt 17.09.2026 12:00 UTC. Gate der Präregistrierung, Abschnitt „Validierung vor der
Messung“ (Schwelle: Median der absoluten relativen Abweichung von K unter 0,1 % und 95. Perzentil unter 1 %, je
Basiswert und Manager). Code `derive_surface/p2validate.py`, Tests `tests/test_p2_validate.py` (21 Tests, offline;
zwei davon lesen die private Fixture `data/p2/fixtures_private/b1_chain_cases.json` mit echten Maker-Büchern und
werden ohne sie übersprungen, Audit A01).
Ergebnisse `results/p2/validation.csv` (1 754 Zeilen) und `results/p2/validation_summary.json`, Rohdaten unter
`data/p2/validation/`. Keine Inferenz: Hier wird nur die Messung geprüft.

## Ergebnis

**Die Schwelle ist in allen Zellen erfüllt, mit mindestens fünf Grössenordnungen Abstand.** Über alle 799 gültigen
Einzelkontrakte liegt der Median der absoluten relativen Abweichung von K unter IM bei 8,7·10⁻¹⁰, das
95. Perzentil bei 1,4·10⁻⁸ und das Maximum bei 8,9·10⁻⁸. Über die 77 gültigen Buch-Zeilen unter IM sind es
2,2·10⁻⁹, 1,3·10⁻⁸ und 3,4·10⁻⁸. Die grösste absolute Abweichung beträgt bei Einzelkontrakten 0,00033 USD (K im
Median 301 USD), bei Büchern 0,050 USD (K bis 19,5 Mio. USD). Quelle: `results/p2/validation.csv`,
`results/p2/validation_summary.json`. Ein Nachtrag zur Präregistrierung ist nicht nötig.

IM (primär), |rel| = |K_Nachbau − K_Chain| / |K_Chain|, Perzentil mit linearer Interpolation:

| Art | Basiswert | Manager | n | fehlend | Median \|rel\| | p95 \|rel\| | Max \|rel\| | Schwelle |
|---|---|---|---:|---:|---:|---:|---:|---|
| Einzelkontrakt | BTC | SM | 100 | 0 | 1,4·10⁻¹⁰ | 6,9·10⁻⁹ | 2,4·10⁻⁸ | erfüllt |
| Einzelkontrakt | BTC | Legacy-PM | 100 | 0 | 2,4·10⁻⁹ | 1,5·10⁻⁸ | 3,1·10⁻⁸ | erfüllt |
| Einzelkontrakt | BTC | PM2 | 100 | 0 | 1,8·10⁻¹⁰ | 1,4·10⁻⁸ | 5,0·10⁻⁸ | erfüllt |
| Einzelkontrakt | ETH | SM | 100 | 0 | 0 | 9,5·10⁻⁹ | 1,4·10⁻⁸ | erfüllt |
| Einzelkontrakt | ETH | Legacy-PM | 100 | 0 | 3,2·10⁻⁹ | 2,0·10⁻⁸ | 6,5·10⁻⁸ | erfüllt |
| Einzelkontrakt | ETH | PM2 | 100 | 0 | 7,4·10⁻¹⁰ | 2,3·10⁻⁸ | 8,9·10⁻⁸ | erfüllt |
| Einzelkontrakt | HYPE | SM | 100 | 0 | 9,2·10⁻¹² | 5,6·10⁻⁹ | 1,2·10⁻⁸ | erfüllt |
| Einzelkontrakt | HYPE | PM2 | 99 | 1 | 1,7·10⁻⁹ | 1,5·10⁻⁸ | 3,5·10⁻⁸ | erfüllt |
| Buch | BTC | SM | 7 | 0 | 7,1·10⁻¹⁰ | 9,3·10⁻⁹ | 1,2·10⁻⁸ | erfüllt |
| Buch | BTC | Legacy-PM | 7 | 0 | 1,3·10⁻⁹ | 8,0·10⁻⁹ | 8,1·10⁻⁹ | erfüllt |
| Buch | BTC | PM2 | 7 | 0 | 2,2·10⁻¹⁰ | 9,1·10⁻⁹ | 1,1·10⁻⁸ | erfüllt |
| Buch | ETH | SM | 18 | 0 | 7,5·10⁻¹⁰ | 4,0·10⁻⁹ | 6,8·10⁻⁹ | erfüllt |
| Buch | ETH | Legacy-PM | 18 | 0 | 3,9·10⁻⁹ | 2,4·10⁻⁸ | 3,4·10⁻⁸ | erfüllt |
| Buch | ETH | PM2 | 18 | 0 | 3,8·10⁻⁹ | 1,3·10⁻⁸ | 2,1·10⁻⁸ | erfüllt |
| Buch | HYPE | SM | 1 | 0 | 2,6·10⁻⁹ | 2,6·10⁻⁹ | 2,6·10⁻⁹ | erfüllt |
| Buch | HYPE | PM2 | 1 | 0 | 4,3·10⁻⁹ | 4,3·10⁻⁹ | 4,3·10⁻⁹ | erfüllt |

Über die Basiswerte zusammengefasst (Bücher, IM): PM2 26 Bücher, Median 3,7·10⁻⁹, p95 1,1·10⁻⁸; SM 26 Bücher,
7,5·10⁻¹⁰ und 6,0·10⁻⁹; Legacy-PM 25 Bücher, 3,3·10⁻⁹ und 2,1·10⁻⁸.

MM (Sensitivität), gleiche Fälle:

| Art | Basiswert | Manager | n | Median \|rel\| | p95 \|rel\| | Max \|rel\| | Schwelle |
|---|---|---|---:|---:|---:|---:|---|
| Einzelkontrakt | BTC | SM | 100 | 2,1·10⁻¹⁰ | 1,0·10⁻⁸ | 3,5·10⁻⁸ | erfüllt |
| Einzelkontrakt | BTC | Legacy-PM | 100 | 2,7·10⁻¹⁰ | 1,2·10⁻⁸ | 2,7·10⁻⁸ | erfüllt |
| Einzelkontrakt | BTC | PM2 | 100 | 2,6·10⁻⁹ | 3,4·10⁻⁸ | 1,9·10⁻⁷ | erfüllt |
| Einzelkontrakt | ETH | SM | 100 | 0 | 1,4·10⁻⁸ | 2,9·10⁻⁸ | erfüllt |
| Einzelkontrakt | ETH | Legacy-PM | 100 | 2,1·10⁻⁹ | 1,8·10⁻⁸ | 6,6·10⁻⁸ | erfüllt |
| Einzelkontrakt | ETH | PM2 | 100 | 3,2·10⁻⁹ | 3,8·10⁻⁸ | 1,0·10⁻⁷ | erfüllt |
| Einzelkontrakt | HYPE | SM | 100 | 1,4·10⁻¹¹ | 7,9·10⁻⁹ | 1,7·10⁻⁸ | erfüllt |
| Einzelkontrakt | HYPE | PM2 | 99 | 1,8·10⁻⁹ | 2,3·10⁻⁸ | 7,5·10⁻⁸ | erfüllt |
| Buch | BTC | SM | 7 | 1,1·10⁻⁹ | 1,3·10⁻⁸ | 1,7·10⁻⁸ | erfüllt |
| Buch | BTC | Legacy-PM | 7 | 1,3·10⁻⁹ | 7,9·10⁻⁹ | 9,5·10⁻⁹ | erfüllt |
| Buch | BTC | PM2 | 7 | 2,4·10⁻¹⁰ | 1,3·10⁻⁸ | 1,4·10⁻⁸ | erfüllt |
| Buch | ETH | SM | 18 | 1,0·10⁻⁹ | 5,9·10⁻⁹ | 1,0·10⁻⁸ | erfüllt |
| Buch | ETH | Legacy-PM | 18 | 2,2·10⁻⁹ | 1,3·10⁻⁸ | 3,7·10⁻⁸ | erfüllt |
| Buch | ETH | PM2 | 18 | 9,0·10⁻⁹ | 3,1·10⁻⁸ | 4,2·10⁻⁸ | erfüllt |
| Buch | HYPE | SM | 1 | 3,1·10⁻⁹ | 3,1·10⁻⁹ | 3,1·10⁻⁹ | erfüllt |
| Buch | HYPE | PM2 | 1 | 6,1·10⁻⁹ | 6,1·10⁻⁹ | 6,1·10⁻⁹ | erfüllt |

## Was verglichen wird

- **Grösse:** K = Σ p·q − net(q; cash = 0) wie in der Präregistrierung. Beide Seiten nutzen dasselbe Buch und
  dieselben Preise p, also gilt |K_Nachbau − K_Chain| = |net_Nachbau − net_Chain|. Normiert wird mit |K_Chain|.
- **Nachbau:** `FeedHistory.state_at` aus `data/p2/feeds` und der SVI-Historie von Paper 1 (`data/p1/volfeed`),
  `Timeline.at` aus `results/p2/params` (Standard-Lib des Managers), dann `margin_sm.net_margin`,
  `margin_pm.net_margin` (statischer Zins 0, fester Forward-Anteil aus dem Feed-Zustand) bzw.
  `margin_pm2.net_margin`. Für die Einzelkontrakte zusätzlich der vektorisierte Weg von B2 (`FeedHistory.bulk` und
  `margin_*.single`): Er ergibt in allen 1 598 Zeilen exakt dieselbe Zahl wie `net_margin` (Differenz 0, Spalte
  `K_replica_single`).
- **Chain:** Ein synthetisches Konto (Nummer 2⁶⁴ + 20260924, weit über `lastAccountId`) erhält per `eth_call`
  State-Override von `SubAccounts` genau die Salden des Buchs (`heldAssets` Slot 15, `balanceAndOrder` Slot 14,
  Layout per `eth_getStorageAt` an zwei bestehenden Konten geprüft). Dann rechnet der Manager selbst:
  `StandardManager.getMargin`, `PMRM.getMargin` bzw. `PMRM_2.getMargin(konto, isInitial)` am selben Block. Das
  Portfolio baut die Chain aus ihren eigenen Feeds (Spot, Forward, Vol, Zins, Perp, Stable), aus unseren Daten geht
  nichts in den Aufruf ein.
- **Perps:** Beide Manager addieren `PerpAsset.getUnsettledAndUnrealizedCash(konto)` linear zu Margin und MtM. Dieser
  Wert wird mit demselben Override gelesen und abgezogen. Damit geht der Perp wie im Nachbau mit Einstand gleich
  Perp-Preis der Engine ein (18 der 26 Bücher halten einen Perp).
- **Grosse Bücher:** Ein `eth_call` darf höchstens 50 Mio. Gas verbrauchen. PM2 braucht für ein Buch mit rund 300
  Beinen etwa 110 Mio. Bei 13 der 51 Buch-Fälle unter Legacy-PM und PM2 (75 bis 245 Beine) scheiterte `getMargin`
  an dieser Grenze, im Bündel über Multicall3 oder direkt. Dort rechnet die Chain je Szenario:
  `getMarginAndMarkToMarket(konto, isInitial, j)` führt die Lib mit Szenario j allein aus. Weil die Anforderung
  monoton in minSPAN = min(Basis, PnL_j) ist, ist net das Minimum über j. An 6 Büchern mit 23 bis 84 Beinen, bei
  denen auch der direkte Aufruf durchläuft, stimmen beide Wege bitgleich überein
  (`results/p2/validation_summary.json`, Schlüssel `per_scenario_check`).

## Stichprobe

- **Einzelkontrakte:** je Basiswert und Manager 100 Zufallsblöcke (präregistriert: mindestens 48) im Fenster der
  Präregistrierung bis zum Pilotschnitt, Seed 20260924, je Zelle ein eigener Zweig
  `SeedSequence(20260924, spawn_key=(k,))`, damit BTC und ETH nicht dieselben Blöcke ziehen. Je Block ein Fill
  desselben UTC-Tags aus dem Tape von Paper 1 (Strike, Typ, Preis p), dessen Verfall aktiv ist (Forward-Push höchstens
  1 h alt, `FeedHistory.live_expiries`) und einen frischen Vol-Push hat (signiert höchstens 20 min vor dem Block);
  Seite zufällig. Ohne passenden Fill wird der Block neu gezogen: 7 Mal über alle 8 Zellen. Die Blöcke reichen vom
  14.01.2024 bis 17.09.2026, die Restlaufzeit liegt je Zelle im Median bei 5,5 bis 11,0 Tagen, 410 von 799
  Kontrakten sind Short.
- **Maker-Bücher:** 20 Maker-Tage, zufällig gezogen (eigener Zweig des Seeds) aus der H3-Population: Tagesbeginn-Buch
  eines dominanten Subaccounts mit mindestens einer lebenden Option eines Basiswerts, dessen PM2-Fenster offen ist
  (2 134 Maker-Tage). Je Tag und Basiswert ein Buch (Optionen und Perp aus `data/p2/books/snapshots.parquet`,
  verfallene Optionen entfernt, Cash und Collateral ausserhalb von K), zusammen 26 Bücher mit 2 bis 245 Beinen und
  1 bis 11 Verfällen, je unter PM2, SM und (BTC, ETH) Legacy-PM. Preise p = Mark M_b (Black-76 auf der SVI-Kurve,
  Forward `svi_fwd`, D = 1). Gezogen wurden M1 (05.08.2025), M2 (03.07., 04.09., 13.09.2025, 27.02., 14.03., 17.03.,
  30.03.2026), M3 (30.05.2026), M4 (13.07., 02.08., 21.09.2025), M5 (06.11.2025, 06.02., 26.05.2026), M6
  (05.10.2025) und M8 (01.07., 25.07., 06.09., 14.09.2026).

## Befunde

1. **Spot und Forward bitgleich.** In allen 1 598 Einzelkontrakt-Zeilen stimmen `getSpot` und `getForwardPrice` der
   Chain exakt mit `state_at` überein (Spalten `spot_rel_dev`, `fwd_rel_dev` gleich 0).
2. **Der Rest kommt aus der Vol.** `getVol` am Strike weicht im Median um 1,2·10⁻⁸ relativ ab, höchstens um
   2,3·10⁻⁷ (`vol_rel_dev`). Ursache: Die SVI-Parameter stammen aus Paper 1 und liegen als float32 vor (bekannt aus
   A1). Das erklärt die Restabweichungen von K in der Grössenordnung 10⁻⁸.
3. **SM-Long exakt.** Eine Long-Option hat unter SM keine Margin, net = 0 auf beiden Seiten und K = Prämie. In allen
   294 Zeilen mit SM-Long ist die Abweichung exakt 0 (daher Median 0 bei ETH SM).
4. **Ein Chain-Revert.** Am Block 36 366 166 (05.03.2026 23:39 UTC, HYPE, PM2) revertiert `getMargin`, weil
   `getSpot` revertiert: Der letzte Spot-Wert war 489 s vor dem Block signiert. Der Nachbau rechnet mit diesem Wert
   weiter. Der Fall ist nicht vergleichbar und zählt als fehlend (n = 99). Für B2 heisst das: Zu solchen Zeitpunkten
   hätte die Chain keine Margin-Prüfung erlaubt. Die Präregistrierung schliesst wegen Feed-Alter nichts aus, das Alter
   wird mitgeführt (`spot_age`).
5. **Ruhende Zweige.** Der Stable-Kurs lag an allen Blöcken zwischen 0,99938 und 1,00144, also über den Schwellen
   von Depeg (SM) und Peg-Loss (PM2) bei 0,99; `stable` = 1 im Nachbau ändert nichts. Die kleinste Konfidenz war 0,95
   (Schwellen 0,55): Die Orakel-Kontingenzen waren nie aktiv und sind hier nicht gegen die Chain geprüft, nur gegen
   die v2-core-Referenzfälle aus A3 und A4. `maxExpiries` wurde von keinem Buch überschritten.

## Grenzen

- Das synthetische Konto hat keine Override-Lib, geprüft ist also die Standard-Lib. Die Override-Libs unterscheiden
  sich nur im mmFactor (A2); IM ist davon nicht berührt, MM im Maker-Buch schon (B3, Sensitivität).
- Geprüft ist das Buch zu Tagesbeginn, nicht das Buch vor einem Fill. Dessen Positionen stammen aus Snapshot plus
  `BalanceAdjusted` (Nachtrag 1), die Bewertung ist dieselbe.
- Für HYPE liegt nur ein Maker-Tag in der Ziehung (M3, 235 Beine). Die Buch-Zellen je Basiswert sind klein; die
  präregistrierte Mindestzahl von 20 Maker-Tagen gilt für alle Basiswerte zusammen.

## Reihenfolge von Validierung und Messung (ergänzt am 25.09.2026, Audit A63)

Die mit der Präregistrierung committete Spezifikation (`docs/superpowers/specs/2026-09-24-p2-kapital-design.md`,
Abschnitt 8, Schritt 3) sagt „Validierung gegen `eth_call`; erst danach Kapital je Fill, Maker-Bücher, Dosen“, und
der Abschnitt der Präregistrierung heisst „Validierung vor der Messung“. So ist es nicht gelaufen. Entstehungszeiten
der Dateien am 25.09.2026 (Dateisystem, Ortszeit UTC+2) und Commit-Zeiten:

| Schritt | Datei oder Commit | Zeit |
|---|---|---|
| Kapital je Fill | `data/p2/derived/capital.parquet` | 00:40:00 |
| H4-Panel mit Dosen | `data/p2/derived/h4_panel.parquet` | 00:40:43 |
| Plan der Validierung (BTC) | `data/p2/validation/plan_BTC.json` | 00:49:37 |
| Maker-Tage (H3) | `data/p2/derived/maker_days.parquet` | 00:53:09 |
| Chain-Antworten | `data/p2/validation/chain.jsonl` | 00:53:40 bis 01:08:47 |
| Ergebnis der Validierung | `results/p2/validation_summary.json` | 01:16:57 |
| Nachtrag 4 („Die Validierung gegen `eth_call` ist bestanden“) | Commit `c4fcb59` | 01:29:58 |
| erste Teststatistik | `results/p2/h1.json` | 01:42:53 |

Kapital je Fill, Dosen und Maker-Tage entstanden also vor oder neben der Validierung. Eingehalten ist die operative
Regel im Text der Präregistrierung, „Bevor Kapitalzahlen in einen Test eingehen, wird der Nachbau … geprüft“: Die
Validierung war bestanden und in Nachtrag 4 festgehalten, bevor die erste Teststatistik entstand. Das Manuskript
behauptet ebenfalls nur diese Reihenfolge („Before any capital entered a test“). Nicht eingehalten sind Schritt 3
der Spezifikation und der Wortlaut der Überschrift. Die Validierung zieht eigene Stichproben und vergleicht Nachbau
und Chain direkt; sie verwendet keine der vorher gerechneten Kapitalzahlen. Ob der Nachbau zwischen 00:40 und dem
Commit `591d2d5` (01:30:22) noch geändert wurde, zeigt die Historie nicht, weil Stufe B ein einziger Commit ist; das
Audit hat Stichproben der Kapitalzahlen unabhängig nachgerechnet (32 Fills, 5 Maker-Tage, 7 H2-Fills, 16
Dosis-Fills; `docs/paper2/AUDIT.md`, Blickwinkel engine). Datei- und Git-Zeiten sind lokal gesetzt und kein Beleg
gegenüber Dritten (Audit A02).

## Reproduktion

```
python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface.p2validate plan --ccy BTC   # ebenso ETH, HYPE
python3 -m derive_surface.p2validate chain --max-seconds 480    # wiederholen bis "done": true
python3 -m derive_surface.p2validate chain --retry-failed       # Fehlfälle neu, z. B. nach Gas-Grenze
python3 -m derive_surface.p2validate check-scenarios            # Szenario-Weg gegen direkten Aufruf
python3 -m derive_surface.p2validate report
```

RPC: 1 997 Anfragen (1 974 `eth_call`, davon die meisten mit State-Override, dazu 17 `eth_getStorageAt` und 6
`eth_estimateGas` für die Vorprüfung), höchstens 2 je Sekunde, Log `data/p2/logs/B1.jsonl`. Die Pläne
(`data/p2/validation/plan_{BTC,ETH,HYPE}.json`) enthalten je Fall Feed-Zustand, Buch und Nachbau-Werte, die
Chain-Antworten liegen in `data/p2/validation/chain.jsonl`. Rohe Kontonummern stehen nur dort; in `results/` und
hier erscheinen Konten als Labels aus `derive_surface.p2ids`.
