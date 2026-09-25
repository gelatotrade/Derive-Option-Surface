# Übergabe: Stand am 24.09.2026 und Start von Paper 2

Diese Datei ist für eine neue Sitzung geschrieben, die nichts über die bisherige Arbeit weiss.
Zuerst lesen, dann anfangen.

## Wo alles liegt

| | |
|---|---|
| Repo, Arbeitsklon | `~/Documents/Papers/Finished Papers/Derive_Options/Derive-Option-Surface` |
| Branch | `paper1-adverse-selection`, 49 lokale Commits, **nichts gepusht** |
| Private Notizen ausserhalb des Repos | `~/Documents/Papers/Finished Papers/Derive_Options/docs/` |
| Bot-Grundbaustein | `~/Documents/Derive MarketMaker Bot/dq` |

Der Ordner lag bis zum 23.09.2026 unter *Working Papers* und wurde vom Nutzer nach *Finished Papers*
verschoben. Ältere Notizen nennen noch den alten Pfad.

## Paper 1 ist fertig

„Who trades against the maker? Adverse selection with counterparty identity on an on-chain options order
book.“ Neun Seiten im Elsevier-CAS-Satz, 3 818 Wörter, neun Abbildungen, 150 Tests, Bau über
`python3 scripts/p1_build.py`.

Kernbefunde, alle aus dem Pilotschnitt zum 17.09.2026 mit 603 940 Fills:

- Zerlegung je Kontrakt: Halbspread +15,70, adverse Selektion −2,65, Gebühr −1,56, Rabatt +0,59,
  Hedge −3,15, Netto-Edge +8,93. Median-Markout nur 0,98.
- Gegenpartei entscheidet: +24,73 gegen gewöhnliche Taker, −25,41 gegen die 17 dominanten Maker.
- Zehn Wallets tragen 90,5 % des Maker-Verlusts, eine einzige Adresse 39,0 %.
- Grösse und Sweeps erklären unter Instrument-mal-Tag-Fixeffekten nichts: t = −0,74 und t = −0,10.
- Drei von vier präregistrierten Hypothesen sind abgelehnt, und das trägt den Aufbau des Papiers.

### Was an Paper 1 noch offen ist

1. **Enddatenlauf** nach dem 01.10.2026 mit Stichtag 30.09., danach alle Zahlen gegen das neue Zahlenblatt
   prüfen. Vorher `pmset -g batt` prüfen und den Nutzer um das Netzteil bitten, der Mac schläft sonst.
2. **Push und Pull Request.** Beim Mergen „Create a merge commit“ wählen, nicht „Squash“, sonst verschwindet
   der Präregistrierungs-Commit `3fd9caa` aus der Historie, und genau dieser Hash steht im Manuskript.
3. **Zugang:** der Token im Schlüsselbund hat kein Schreibrecht, 403. Ein SSH-Schlüssel wurde am 24.09.
   erzeugt und liegt unter `~/.ssh/id_ed25519`, der öffentliche Teil ist aber noch **nicht** bei GitHub
   hinterlegt. Danach Remote auf SSH umstellen.
4. **Offene Nutzerentscheidung:** `results/p1/h1_lorenz.csv` enthält 1 388 Wallet-Adressen nach Gewinn gegen
   Maker sortiert. Das Manuskript nennt keine. Vor dem Merge klären, ob die Spalte gehasht wird.
5. Korrekturlesen durch einen Menschen, bisher hat nur das Modell den Text gelesen.

## Paper 2: Margin-Polytop und kapitalbereinigter Edge

**Die Frage.** Paper 1 sagt, wo auf der Oberfläche ein Maker bezahlt wird. Es sagt nicht, was davon man
sich leisten kann. Die richtige Zielgrösse für einen Bot ist nicht der Edge je Kontrakt, sondern der Edge je
verbrauchter Margin. Auf zentralen Börsen ist Portfolio-Margin eine Blackbox. Bei Derive ist die
Risiko-Engine eine deterministische, öffentlich aufrufbare Funktion, also lässt sich der zulässige
Positionsraum vollständig abtasten, ohne Kapital zu binden.

**Was am 24.09.2026 geprüft wurde.** `public/get_margin` antwortet ohne Konto und ohne Schlüssel.
Pflichtfelder sind `margin_type`, `simulated_positions`, `simulated_collaterals`; für `PM` und `PM2` kommt
`market` dazu. Wichtig: die API blockt Anfragen ohne User-Agent mit HTTP 403, ein beliebiger Wert genügt.
Es gibt 814 aktive BTC-Optionen.

Messung mit 50 BTC-Optionen über fünf Verfälle, 200 000 USDC Sicherheiten, Anforderung gelesen als
Kapital minus `post_initial_margin`:

| Portfolio | Standard-Margin | Portfolio-Margin | Faktor |
|---|---|---|---|
| 50 short, einseitig | 1 472 630 | 1 007 583 | 1,5 |
| 25 long / 25 short | 707 994 | 595 818 | 1,2 |

**Ungeklärter Widerspruch, den Paper 2 auflösen muss.** Die Notiz vom 17.09.2026 nennt für einen ähnlichen
Aufbau einen Netting-Faktor von rund 11. Die Messung vom 24.09. ergibt 1,2 bis 1,5. Entweder haben sich
Parameter geändert, oder die frühere Probe hat die Felder anders interpretiert. Das Orakel liefert
Margin-**Salden**, nicht Anforderungen, und die Umrechnung mischt Positionswert und Margin. Die Semantik
sauber zu klären ist der erste Arbeitsschritt und bereits ein Beitrag.

**Vier Teile des Papiers.**

1. *Geometrie.* Der zulässige Bereich unter PM2 entsteht aus Szenarioschocks auf Spot, Vol und Skew und ist
   nicht konvex. Ihn zu charakterisieren ist der Theorieteil.
2. *Karte.* Dieselbe Delta-mal-Laufzeit-Karte wie in Paper 1, aber in Edge je Margin statt je Kontrakt.
3. *Bruchstelle.* Bis zu welcher Grösse ist der Grenzkontrakt fast gratis, und wo kippt das Portfolio.
4. *Zeitachse.* Parameteränderungen sind On-Chain-Ereignisse (`*ParamsUpdated`), also rekonstruierbar: wann
   wurde die Engine strenger und was machte das mit der Buchtiefe.

**Bekannte Randbedingungen.** PM2 verlangt einen `market`-Parameter, es gibt also kein Netting über
Basiswerte hinweg, und ein Bot braucht je Basiswert ein eigenes Subkonto. Ein Abtasten über viele
Dimensionen kostet sehr viele API-Aufrufe, es braucht einen Versuchsplan statt eines Rasters. Die
Portfolios sind hypothetisch, das Papier handelt vom Möglichkeitsraum und nicht von realisierten Büchern,
und das gehört in den Titel.

## Arbeitsweise, die der Nutzer erwartet

- **Superpowers-Ablauf:** brainstorming, dann writing-plans, dann executing-plans. Pläne unter
  `docs/superpowers/plans/`, Spezifikationen unter `docs/superpowers/specs/`.
- **Testgetrieben.** Erst der fehlschlagende Test, dann der Code. Die Suite muss grün bleiben.
- **Präregistrierung** vor jeder Messung, mit datierten Nachträgen. Nichts rückwirkend ändern.
- **Papier auf Englisch, Projektdokumentation auf Deutsch.** Keine Gedankenstriche im Fliesstext.
- **Wenig Text, viele Abbildungen.** Harte Wortbudgets je Abschnitt, überwacht von
  `scripts/p1_wordcount.py`. Ein Abschnitt, der sein Budget reisst, wird gekürzt.
- **Jede Zahl im Text muss in `results/` nachweisbar sein.** Prüfskripte erzwingen das.
- **Keine erfundenen Literaturangaben.** Jede Quelle gegen Verlag, RePEc oder DOI prüfen.
- Bei langen Läufen vorher `pmset -g batt` prüfen, der Mac schläft auf Batterie trotz `caffeinate`.
- Höchstens ein Web-Recherche-Agent gleichzeitig, sonst ist das Sitzungslimit in rund 25 Minuten erschöpft.

## Erster Schritt in der neuen Sitzung

Die Semantik von `get_margin` klären, bevor irgendetwas anderes passiert. Konkret: was genau ist
`pre_initial_margin` gegenüber `post_initial_margin`, wie verhält sich das zu `simulated_collaterals`, und
wie liest man daraus eine Anforderung, die über Portfolios vergleichbar ist. Erst wenn diese Frage
beantwortet ist, lohnt sich ein Versuchsplan für das Abtasten.
