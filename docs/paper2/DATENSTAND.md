# Datenstand Paper 2

## A3 Nachbau PM2 (`derive_surface/margin_pm2.py`)

Stand 24.09.2026. Offline-Nachbau von `PMRMLib_2` samt `PMRM_2._arrangePortfolio` (v2-core `96796a6`), Port des
vektorisierten Prototyps `data/p2/semantik_20260924/verify-konvex/pm2v.py`, Zeile für Zeile gegen `PMRMLib_2.sol`,
`PMRM_2.sol` und `code-pm2/pm2_replica.py` geprüft (Zeilenverweise im Code). `PMRM_2_1` ändert nur die Wahl der Lib
je Konto, nicht die Rechnung.

| Prüfung | Umfang | Ergebnis |
|---|---|---|
| v2-core-Referenzfälle `PMRM_2/portfolio_cases` | 139 von 139 (IM und MM), inklusive `test_67`, den der Solidity-Harness überspringt | max. relativer Fehler 9,2e-15 |
| Chain-Fälle (`tests/fixtures/p2/pm2_chain_cases.json`) | 25 Bücher an 4 Blöcken: BTC 27 013 992 (01.08.2025, Altregime), BTC 45 113 645 (24.09.2026, die 10 Bücher aus `rep_vs_chain.json`), ETH 36 777 192 (15.03.2026), HYPE 38 116 392 (15.04.2026); je IM und MM | max. absolute Abweichung von net 5,1e-11 USD, max. relative Abweichung von R 1,6e-13, schlechtestes Szenario 50 von 50 gleich |
| Gegenprobe gegen `pm2v.py` | 3 000 Zufallsbücher (1 bis 39 Beine, teils mit Perp) am Block 45 113 645 | max. relativer Unterschied 4,5e-13 |
| `single` gegen `net_margin` | 200 Zufallskontrakte (4 Parametersätze, Kanten bei 0 s, 30 min, 30 Tagen, Konfidenz unter Schwelle, negativer Zins, Peg) | gleich bis 1e-10 relativ |
| Laufzeit `single` | 600 000 Einzelkontrakte | rund 1 s (Grenze 120 s) |

Chain-Fälle: Feeds und Parameter per `eth_call` am Block, Portfolio wie `PMRM_2._arrangePortfolio` gebaut, Ergebnis
von `PMRMLib_2.addPrecomputes` und `getMarginAndMarkToMarket` am selben Block. Erzeugt mit
`data/p2/margin_pm2/build_chain_cases.py` (241 RPC-Anfragen, höchstens 2/s, Log `data/p2/logs/A3.jsonl`, Cache
`data/p2/margin_pm2/cache.json`). Multicall3 (`0xcA11bde05977b3631167028862bE2a173976CA11`) hat auf Chain 957 Code
(3 808 Bytes); für A3 nicht nötig und nicht genutzt. Die A2-Zeitlinien `results/p2/params/{BTC,ETH,HYPE}_pm2.json`
stimmen an allen vier Blöcken feldgleich mit den Gettern der Chain-Fälle überein, und `margin_pm2` nimmt sie
unverändert (Stand der A2-Dateien am 24.09.2026 abends).

Schnittstelle: `net_margin(book, state, params, is_initial=True, *, vols=None, collaterals=()) -> (net, mtm)`,
`requirement(...) -> float`, `margin_details(...) -> dict` (mit `worst`, `minSPAN`, Kontingenzen),
`single(arrays, params, is_initial=True) -> (net, mtm)`. Parameter im A2-Schema; `VolShockParameters.dteFloor` in
Sekunden (ein 1e18-skalierter Wert unter 1 löst `ValueError` aus); `volShock` als 0 bis 4 oder Name. Vol-Schocks und
Skew wirken auf die Vol am Strike, Diskont `exp(-max(r, 0) τ)` aus `ExpiryState.rate`, Perp-Wert `q (P − Einstand)`,
Perp-Szenario `q (Schock − 1) P`, Perp-Kontingenz `|q| S pct`, Orakel-Kontingenz über die kleinste Konfidenz je
gehaltenem Verfall (Spot, Perp falls gehalten, Forward, Zins, Vol).

Offene Punkte für die Folgetasks:
- `ExpiryState` kennt weder den festen Forward-Anteil im 30-min-Settlement-Fenster noch die Konfidenz des Zins-Feeds.
  Der Nachbau liest beide, falls vorhanden (`fwd_fixed`, Vorgabe 0; `rate_conf`, Vorgabe 1), und `single` nimmt sie
  als optionale Spalten. Ohne sie weicht der Nachbau nur in den letzten 30 min vor Verfall bzw. bei Zins-Konfidenz
  unter 0,55 ab.
- `maxExpiries` wird nicht erzwungen (die Chain würde bei mehr Verfällen revertieren).
- Die v2-core-Referenzfälle werden direkt aus `data/p2/v2-core` gelesen (BUSL-Lizenz, nicht ins Repo kopiert); fehlt
  das Verzeichnis, werden diese Tests übersprungen.

## A4 Nachbau SM und Legacy-PM (`derive_surface/margin_sm.py`, `derive_surface/margin_pm.py`)

Stand 24.09.2026 (Fix-Runde nach Review). Offline-Nachbau des `StandardManager` (mit
`SRMPortfolioViewer.arrangeSRMPortfolio`) und des Legacy-Managers `PMRM` mit `PMRMLib` (v2-core `96796a6`),
Zeilenverweise im Code. Beide Motoren saldieren zuerst die Beine je Instrument `(expiry, strike, is_call)` wie
`SubAccounts` (ein Saldo je subId, Nullsalden entfallen und zählen weder als Position noch als Verfall); ein an ein
Buch angehängter Fill ergibt damit den Saldo nach dem Trade. SM: isolierte Margin je Option (Long ohne Margin), je
Verfall `max(Σ isoliert, Max-Loss)` mit Max-Loss am Gitter {0} ∪ Strikes des Verfalls plus
`unpaired*Scale · F · netCalls` bei netto Short-Calls, Verfälle addiert, MtM Black-76 auf dem Forward mit D = 1, Perp
`−|q| · P · (im|mm)PerpReq` plus unrealisierter PnL, Basis-Collateral mit `marginFactor` (IM zusätzlich `IMScale`),
nur für IM Orakel-Kontingenzen (Perp, Verfall, Basis) und Depeg-Aufschlag auf `|Perp| + alle Shorts`. Legacy-PM:
MtM ohne Diskont und ohne Skew, Spot-Schock nur auf den variablen Forward-Anteil, Vol-Schock multiplikativ je
Verfall, positive Szenariowerte mal Static Discount `baseStaticDiscount · exp(−τ (max(r, 0) · rateMultScale +
rateAddScale))` mit dem Legacy-Zins r = 0 (siehe Befunde), `minSPAN` = Minimum aus Basis-Kontingenz und Szenarien
aus `params["scenarios"]`, minus statische Kontingenzen (Perp, Basis, Naked Shorts je Strike), für IM mal `imFactor`
(plus Peg-Aufschlag) minus Konfidenz-Kontingenz; MM mit Faktor 1.

| Prüfung | Umfang | Ergebnis |
|---|---|---|
| v2-core `StandardManager/test-cases.json` | 28 von 28, IM, MM und MtM (ETH und BTC, Perps mit Funding, Basis, Depeg, Konfidenzen) | max. relative Abweichung 2,4e-14 (Solidity-Test erlaubt 0,1 %) |
| v2-core `StandardManager/test-cases-portfolio.json` | 42 von 42, IM und MM in ganzen USD | alle exakt |
| Chain SM isoliert (`tests/fixtures/p2/sm_chain_cases.json`) | `getIsolatedMargin` an 12 Blöcken (BTC 5, ETH 4, HYPE 3; 15.02.2024 bis 10.09.2026), je 2 Verfälle × 5 Strikes × Call/Put × 3 Mengen × IM/MM = 1 440 Positionen | max. absolute Abweichung 5,8e-11 USD, relativ 8,0e-12 |
| Chain SM ganze Konten (`sm_chain_accounts.json`) | `getMarginAndMarkToMarket` für 12 echte SM-Konten an 6 Blöcken (20.03.2024 bis 20.08.2026), 14 bis 30 Optionen, bis 8 Märkte, 8 Konten mit Basis-Collateral, 5 mit Perps samt unrealisiertem PnL; IM und MM, net und MtM | max. absolute Abweichung 3,7e-9 USD |
| v2-core `PMRM/test-cases-portfolio-pm.json` | 44 von 44, IM und MM in ganzen USD | alle exakt |
| v2-core `PMRM/testAndVerifyScenarios.json` | 21 von 21, IM, MM und MtM | max. absolute Abweichung 5,1e-11 USD (Solidity-Test erlaubt 1e-10 USD) |
| Chain Legacy-PM Lib (`pm_chain_cases.json`) | deployte `PMRMLib` (`addPrecomputes`, `getMarginAndMarkToMarket`) an 8 Blöcken (BTC und ETH, 01.03.2024 bis 01.03.2026, alle drei Parameterstände), je 5 Bücher (3 mit einem Bein, 2 gemischt mit Perp bzw. Perp und Basis), IM und MM | max. absolute Abweichung 7,3e-11 USD, relativ 8,9e-14 |
| Chain Legacy-PM ganze Konten (`pm_chain_accounts.json`) | `PMRM.getMargin(acc, true/false)` und MtM aus `getMarginAndMarkToMarket(acc, true, 0)` für 5 Maker-Konten unter dem Legacy-PM (ETH 10.03.2024, BTC 15.09.2024, ETH 15.12.2024, BTC 16.06.2025, ETH 15.12.2025; alle drei Parameterstände), 26 bis 59 Optionen, 6 bis 9 Verfälle, je ein Perp mit offenem Cash, Cash bis 1,1 Mio. USD; Eingaben per Multicall am selben Block, Legacy-Zins nicht übergeben (Default 0), `strict_expiries=True` | max. absolute Abweichung 4,7e-10 USD, relativ 2,0e-15 |
| Parameter gegen A2-Zeitlinien | SM an 12 Blöcken, Legacy-PM an 13 Blöcken (beide Chain-Fixtures) gegen `p2params.Timeline(ccy, mgr).at(ts)`, einschliesslich `scenarios` und `maxExpiries` | alle feldgleich (jetzt als Test) |
| `single` gegen `net_margin` | je 200 Zufallskontrakte, IM und MM (Konfidenzen unter Schwelle, Depeg, 0 s Restlaufzeit, negativer Legacy-Zins über `rate_pm`) | gleich bis 1e-12 relativ |
| Saldierung je Instrument | Beine +1 und −2 gleich −1, +1 und −1 gleich leeres Buch, SM und Legacy-PM, IM und MM, Konfidenz unter Schwelle und Depeg | gleich bis 1e-12 relativ (vorher beim SM doppelte Margin, z. B. BTC 90 000 C: −22 984 statt −11 492 USD) |
| Laufzeit `single` | 600 000 Einzelkontrakte | SM 0,05 s, Legacy-PM 0,75 s (Grenze im Test 10 s) |

Chain-Fälle: alle Eingaben (Feeds des jeweiligen Managers, Parameter-Getter, Szenarien, Kontosalden) per `eth_call`
am selben Block, gebündelt über Multicall3 (`0xcA11bde05977b3631167028862bE2a173976CA11`, Code seit spätestens Block
2 454 793, bei Block 843 000 noch nicht); `PMRM.getMargin` direkt. Erzeugt mit
`tests/fixtures/p2/gen_a4_chain_fixtures.py {sm,pm,accounts,pm_accounts}` (wird von pytest nicht gesammelt, braucht
`eth_abi`/`eth_hash` vom System, keine Paketabhängigkeit): insgesamt 265 RPC-Anfragen, höchstens 2/s, Log
`data/p2/logs/A4.jsonl`. SM-Konten sind aktive Taker- und Maker-Subaccounts aus Paper 1; die Legacy-PM-Konten wählt
der Generator nach festen Kriterien aus `data/p2/books/snapshots.parquet` (A5): Optionen und Perp unter dem
Legacy-PM, 3 bis 11 Verfälle, 10 bis 60 Optionen, nächster Tag zum Zieldatum. Konto-IDs in beiden Fixtures nur als
`sha256(str(id))[:10]`. Die v2-core-Referenzfälle werden wie in A3 direkt aus `data/p2/v2-core` gelesen (BUSL,
nicht ins Repo kopiert) und ohne das Verzeichnis übersprungen; die Chain-Fixtures laufen immer.

Parameter im A2-Schema (Solidity-Struktur- und Feldnamen, 1e18 zurückgerechnet, `dteFloor` in Sekunden,
`volShock` 0 None, 1 Up, 2 Down); `results/p2/params/*_sm.json` und `*_pm.json` gehen unverändert hinein.
`tests/fixtures/p2/a4_params_today.json` enthält die heutigen Werte (SM BTC aus `srm_params_live.json`, Legacy-PM
BTC aus `params_live.json`, `lib1.*`).

Befunde:
- Legacy-Zins konstant 0: Die `interestRateFeed` beider Legacy-Manager sind `LyraRateFeedStatic`
  (BTC `0x6fef1bb8…004f`, ETH `0x30a6e6a3…9feb`). Per `eth_getLogs` von Block 800 000 bis 45 131 522 gibt es je genau
  ein `RateUpdated`, beim Deploy (BTC Block 843 076, ETH 843 060), mit rate 0 und confidence 1e18, und auf beiden
  PMRM kein `InterestRateFeedUpdated`. Der Static Discount hängt damit nur an `rateAddScale` 0,12. `margin_pm` rechnet
  deshalb standardmässig mit Zins 0 und Konfidenz 1 und liest `ExpiryState.rate` (den PM2-Zins aus A1) nicht mehr;
  `single` ignoriert die Spalte `rate` und liest nur eine optionale Spalte `rate_pm` (Default 0). `rates=` und
  `rate_confs=` bleiben als Overrides für Referenzfälle. Ohne diese Korrektur wäre K_pm einer Long-Option im
  PM2-Fenster (PM2-Zins rund 4,2 %) zu hoch gewesen: ATM-Long-Call BTC (σ 0,5, heutige Parameter) +0,02 % bei
  30 Tagen, +0,27 % bei 90 Tagen, +0,92 % bei 180 Tagen.
- Legacy-PM-Parameter, drei Stände (je Basiswert gleich, laut A2 und an allen 13 Blöcken bestätigt): Basis-Kontingenz
  `basisContAddFactor`/`basisContMultFactor` 1,0/1,2 bis 12.06.2024 00:01 UTC, danach 0,5/2,0; `maxExpiries` 11 bis
  25.09.2024 04:47 UTC, danach 18; am 22.02.2025 19:52 UTC `volRangeUp` 0,6 → 0,5, `optionPercent` 0,02 → 0,015 und
  Szenarien ±20 % → ±18 %.
- SM: BTC und ETH Optionsparameter über den ganzen Zeitraum gleich (`maxSpotReq` 0,15, `minSpotReq` 0,13, MM 0,09);
  HYPE deutlich strenger (0,30, 0,25, MM 0,18, `unpairedIMScale` 1,3), Perp- und Basisparameter ändern sich.
- An allen Chain-Blöcken lagen die Konfidenzen über den Schwellen (Vol 0,95, Spot und Perp 1,0), die
  Orakel-Kontingenzen sind dort ruhend; geprüft sind sie über die v2-core-Referenzfälle und die Saldierungstests.

Schnittstellen:
- `margin_sm.net_margin(book, state, params, is_initial=True, *, vols=None, base=0.0) -> (net, mtm)` je Markt,
  `margin_sm.net_margin_multi(books, states, params_by_ccy, is_initial=True, *, cash=0.0, vols=None, bases=None)`
  für Konten über mehrere Märkte (Cash einmal), `margin_sm.single(arrays, params, is_initial=True) -> (net, mtm)`,
  `margin_sm.isolated_margin(...)`, `margin_sm.requirement(...)`, `margin_sm.b76_prices(F, K, σ, sec, D=1)`,
  `margin_sm.merged_options(book) -> list[OptionLeg]` (Saldierung je Instrument),
  `margin_sm.MARKET_ID = {"ETH": 1, "BTC": 2, "HYPE": 48}`.
- `margin_pm.net_margin(book, state, params, is_initial=True, *, vols=None, base=0.0, rates=None, rate_confs=None,
  fwd_fixed=None, strict_expiries=False) -> (net, mtm)`, `margin_pm.single(arrays, params, is_initial=True) ->
  (net, mtm)` (optionale Spalten `stable`, `rate_pm`, `rate_conf`, `fwd_fixed`; `rate` wird ignoriert),
  `margin_pm.requirement(...)`, `margin_pm.TooManyExpiries` (Unterklasse von `ValueError`).
- `vols` bildet `(expiry, strike)` auf den Vol-Feed-Wert ab; ohne Eintrag gilt die SVI-Kurve von `ExpiryState`.
  Kapital je Fill: `K = p · q − net` mit cash 0 (`p2types.capital_from_net`).
- B2 kann die `bulk_state`-Spalten aus A1 unverändert an beide `single` geben; der PM2-Zins in `rate` wirkt dort
  nicht.
- B3: Mit `strict_expiries=True` löst `margin_pm.net_margin` `TooManyExpiries` aus, wenn das saldierte Buch mehr
  Verfälle hält als `params["maxExpiries"]` (11 bis 25.09.2024, danach 18). PMRM revertiert dann
  (`PMRM_TooManyExpiries`, gezählt werden alle gehaltenen Verfälle, auch verfallene, noch nicht abgerechnete). B3
  muss solche Bücher unter dem Legacy-PM als NaN führen, statt ein Kapital auszuweisen.

Offene Punkte:
- `Book` hat kein Feld für Basis-Collateral; es geht über `base=` ein. `ExpiryState` kennt weder den festen
  Forward-Anteil der letzten 30 min noch die Zins-Konfidenz (Legacy-PM: `fwd_fixed`, `rate_confs`).
- Nicht erzwungen: `maxAccountSize` beider Manager, OI-Caps; `maxExpiries` nur mit `strict_expiries=True`.

## A2 Parameter-Zeitlinien (`derive_surface/p2params.py`)

Stand 24.09.2026, Chain 957 bis Block 45 130 786 (24.09.2026 20:53:07 UTC). Zeitlinien je Basiswert und Manager unter
`results/p2/params/{CCY}_{sm,pm,pm2}.json`, dazu die Override-Libs `{CCY}_pm2_lib_<addr8>.json` und die Zuweisungen
`{CCY}_pm2_overrides.json`. Schema wie im Plan: Liste aufsteigend nach Block, je Eintrag `from_block`, `from_ts`,
`from_utc`, `source`, `changed` (geänderte Strukturen gegenüber dem Vorgänger), `params` und bei PM und PM2 `lib`.
Schlüssel in `params` sind die Struktur- und Feldnamen aus v2-core `96796a6`; 1e18-Werte als float (`int / 10**18`,
korrekt gerundet), `dteFloor` in Sekunden, `maxExpiries` und `volShock` als int (PM2: 0 None, 1 Up, 2 Down, 3 Linear,
4 Abs; Legacy-PM: 0 bis 2), `CollateralParameters` als `{asset: {...}}` nur mit gesetzten Assets. Aufeinanderfolgende
gleiche Stände sind zusammengefasst, jeder Eintrag ist also eine echte Änderung. `HYPE_pm.json` ist eine leere Liste
(kein Legacy-PM für HYPE), `Timeline("HYPE", "pm").at(ts)` löst deshalb wie vor jedem ersten Eintrag `KeyError` aus.

Vorgehen:
- Ereignisse per `eth_getLogs` (Adress- und Topic-Filter, Bereich bei Fehlern halbiert): SRM `OptionMarginParamsSet`,
  `PerpMarginRequirementsSet`, `BaseMarginParamsSet`, `OracleContingencySet`, `DepegParametersSet` (248);
  Legacy-PMRM `ScenariosUpdated`, `MaxExpiriesUpdated` (6); PM2-Manager und Standard-Libs alle `*ParamsUpdated`,
  `CollateralParametersUpdated`, `ScenariosUpdated`, `MaxExpiriesUpdated`, `LibOverrideUpdated`, `Upgraded`,
  `Initialized` (198); die drei Override-Libs ihre `*ParamsUpdated` und `CollateralParametersUpdated` (113). Zusammen
  565 Ereignisse. Alle 449 passenden Ereignisse aus `data/p2/kontext/margin-historie/events.json` sind enthalten, neu
  sind die 3 `Initialized` und die 113 Ereignisse der Override-Libs.
- An jedem Ereignisblock liest ein historischer `eth_call` alle Getter (Stand nach dem Block): PM2
  `getScenarios`, `maxExpiries`, `lib` (geprüft gleich der Standard-Lib), `getMarginParams`, `getVolShockParams`,
  `getBasisContingencyParams`, `getOtherContingencyParams`, `getSkewShockParams`, `getCollateralParameters` je Asset
  (alle 25 bzw. 24 bzw. 8 Assets aus den Collateral-Ereignissen); Legacy-PM `getScenarios`, `maxExpiries`,
  `getStaticDiscountParams`, `getVolShockParams`, `getBasisContingencyParams`, `getOtherContingencyParams`; SM
  `optionMarginParams`, `perpMarginRequirements`, `baseMarginParams`, `oracleContingencyParams` je Markt (BTC 2, ETH 1,
  HYPE 48) und `depegParams`. Nie das Event: bei `OptionMarginParamsSet` stehen unpairedMM und unpairedIM vertauscht.
- Multicall3 (`0xcA11bde05977b3631167028862bE2a173976CA11`) hat Code ab Block 1 935 198 (29.12.2023 23:20:11 UTC,
  per Bisektion über `eth_getCode`); ab dort sind alle Getter eines Blocks in einem `aggregate3` gebündelt (höchstens
  250 Aufrufe je Anfrage, 189 je Tagesprobe, weit unter dem Gas-Cap), davor Einzelaufrufe.
- Legacy-PM (keine Events der Lib): Proben am Deploy-Block, am ersten Block jedes Monats und am Endblock (35 Proben),
  Bisektion jeder Änderung auf den Block, dann Tagesproben ±14 Tage um jede gefundene Änderung (137 Proben), bis keine
  neue Änderung mehr auftaucht. Ergebnis BTC und ETH gleich: Monatsproben mit Bisektion, Tagesproben um die Änderungen
  und die volle Tagesreihe liefern dieselben Blöcke. Um jede Änderung stimmen alle Tagesproben mit der Zeitlinie
  überein (BTC 14 bis 28, ETH 21 bis 28 Tage je Änderung). Die Vorarbeit (`oi_legacy.py`: 12.06.2024 und 22.02.2025)
  ist bestätigt, auf den Block genau (9 064 436 und 20 116 171).
- Tagesreihe für alle elf Zeitlinien: erster Block jedes UTC-Tags vom 30.12.2023 bis 24.09.2026 (1 000 Tage), alle
  Getter per Multicall3, verglichen mit `Timeline.at(ts)`. Ergebnis 11 000 von 11 000 Tagesproben gleich, davon aktiv
  (Manager bzw. Lib existiert): SM BTC und ETH je 1 000, SM HYPE 335, Legacy-PM BTC und ETH je 1 000, PM2 BTC und ETH
  je 472, PM2 HYPE 343, Override-Libs je 233. Kein Parameterstand ändert sich also ohne Ereignis, bis auf die Lib des
  Legacy-PM (dort über die Bisektion erfasst).
- Wiederaufnehmbar: jeder Stand je (Block, Zeitlinie) liegt in `data/p2/params/snapshots.jsonl` (7 021 Zeilen) mit
  165 verschiedenen Ständen in `states.jsonl`; Ereignisse in `logs_*.json` und `events_decoded.json`, Endblock in
  `meta.json`, Prüfergebnis in `summary.json`. Aufruf `python3 -m derive_surface.p2params load --max-seconds 520`
  bis `DONE`, Tabelle mit `python3 -m derive_surface.p2params report`. RPC insgesamt 3 391 Anfragen (3 348
  `eth_call`, 13 `eth_getLogs`, 28 `eth_getCode`, 2 `eth_blockNumber`), höchstens 2/s, Log `data/p2/logs/A2.jsonl`.

Kapitalrelevante Änderungen (ohne `CollateralParameters` und `maxExpiries`), abgefragt mit
`Timeline.changes(keys=[...])`:
- Legacy-PM BTC und ETH im Zeitraum von Paper 1: 12.06.2024 00:01:27 UTC (Basis-Kontingenz 1,0/1,2 → 0,5/2,0) und
  22.02.2025 19:52:37 UTC (Szenarien ±20 % → ±18 %, `volRangeUp` 0,6 → 0,5, `volRangeDown` 0,3 → 0,275, Basis-Schock
  0,95/1,05 → 0,955/1,045, `optionPercent` 0,02 → 0,015). Dazu `maxExpiries` 11 → 18 am 25.09.2024 04:47:15 UTC
  (Manager-Event, für Einzelkontrakte ohne Wirkung) und die Einrichtung im Dezember 2023 (vor dem Fenster).
- PM2 im PM2-Fenster (BTC und ETH ab 12.06.2025 23:00 UTC, HYPE ab 11.11.2025): BTC 10.10.2025, 08.01.2026,
  23.01.2026, 24.05.2026 (zwei Blöcke, 04:05 und 05:21 UTC), 20.08.2026; ETH 10.10.2025, 08.01.2026, 23.01.2026,
  24.05.2026, 20.08.2026; HYPE 08.01.2026, 08.05.2026, 24.05.2026, 20.08.2026. Die Änderung vom 12.06.2025 22:20 UTC
  (Static Discount Add 0,16 → 0,1, Mult 0,1 → 0) liegt 40 Minuten vor dem Fensterbeginn.
- SM: bei BTC und ETH keine Änderung der Optionsparameter seit dem Deploy (nur Perp 12.06.2024 und `IMScale` des
  Basis-Collaterals am 08.10.2024 für 57 Minuten auf 0); bei HYPE nur Perp- und Basisparameter.
- Die Standard-Libs ändern daneben oft `CollateralParameters` (Haircuts für Nicht-USDC-Collateral, ausserhalb von K):
  BTC 12, ETH 12, HYPE 8 Einträge nur dafür.

Override-Libs (`PMRM_2_1` seit 03.02.2026, `LibOverrideUpdated`): je Basiswert genau eine Lib, eingerichtet am
03.02.2026 zwischen 21:19 und 22:01 UTC. Ab dann gleichen sie an jedem Änderungszeitpunkt der Standard-Lib Feld für
Feld bis auf `mmFactor`: BTC `0x4e8ea8af…46c8` und ETH `0x902e3867…45f9` 0,35 statt 0,8; HYPE `0xf4caea4e…aa17`
0,45 statt 0,95, ab 24.05.2026 0,40 statt 0,9 und ab 20.08.2026 0,40 statt 0,8. Zugewiesen: BTC 15, ETH 16, HYPE 10 Konten, erste Zuweisung 10.02.2026 (ETH) bzw. 17.02.2026, letzte
21.09.2026, keine Aufhebung. In `results/` stehen die Konten nur als `sha256(str(id))[:10]`; die Rohzuordnung liegt in
`data/p2/params/{CCY}_pm2_overrides_raw.json`. Die Zeitlinie einer Override-Lib enthält Szenarien und `maxExpiries`
des Managers, ist also direkt als Parametersatz verwendbar.

Manager-Anteile am Options-OI: `results/p2/manager_oi_share.csv` (Spalten `month, ccy, sm, pm, pm2`, 75 Zeilen: BTC
2024-01 bis 2026-09, ETH 2024-02 bis 2026-09, HYPE 2025-12 bis 2026-09) aus
`data/p2/kontext/margin-historie/oi_legacy.json`, Anteil von `OptionAsset.totalPosition(manager)` (Summe der
Beträge aller Salden) an der Summe über die Manager, Stichtag jeweils der Monatserste 00:00:01 UTC. Monate ohne OI
und die Kopfzeile `head` fallen weg; HYPE hat keinen Legacy-PM (`pm` leer).

Schnittstellen:
- `p2params.Timeline(ccy, mgr, lib=None, root=None, entries=None)` mit `.at(ts) -> dict`, `.entry_at(ts) -> dict`,
  `.changes(keys=None) -> list[int]` (`from_ts` jeder Änderung nach dem ersten Eintrag, optional nur für bestimmte
  Strukturen), `.save(root=None)`, `Timeline.path(ccy, mgr, lib=None, root=None)`.
- `p2params.load_overrides(ccy)`, `p2params.account_lib(overrides, account_id, ts) -> str | None` (nimmt die rohe
  Konto-ID, hasht intern), `p2params.pm2_params_for_account(ccy, account_id, ts) -> dict` (Override-Lib falls
  gesetzt, sonst Standard-Lib).
- `p2params.manager_oi_share(oi_json) -> DataFrame`, `p2params.report_markdown()`.

Offene Punkte:
- Endblock ist der Kopf beim ersten Lauf (24.09.2026 20:53 UTC). Für den Enddatenlauf nach dem 01.10.2026
  `data/p2/params/meta.json` löschen oder `--to-block` setzen; die Collateral-Assets hängen am Endblock, der Cache
  unterscheidet deshalb Assetlisten.
- Eine Änderung der Legacy-Lib, die innerhalb eines Tages wieder zurückgenommen wurde, bliebe unsichtbar
  (Tagesraster); für die übrigen Manager schliesst die lückenlose Ereignisliste das aus.

Tabellen der Änderungen (Stand nach dem jeweiligen Block; Einträge, die nur `CollateralParameters` ändern, sind
gezählt, nicht einzeln aufgeführt; Dezimalkomma):

**BTC SM** (4 Einträge, `results/p2/params/BTC_sm.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2023-12-04 16:36 | 843078 | start+event:OptionMarginParamsSet+OracleContingencySet+Pe… | Start |
| 2024-06-12 00:03 | 9064496 | event:PerpMarginRequirementsSet | imPerpReq 0,1→0,066; mmPerpReq 0,065→0,05 |
| 2024-10-08 17:49 | 14194091 | event:BaseMarginParamsSet | IMScale 0,93→0 |
| 2024-10-08 18:46 | 14195796 | event:BaseMarginParamsSet | IMScale 0→0,93 |

**BTC PM** (7 Einträge, `results/p2/params/BTC_pm.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2023-12-04 16:36 | 843077 | start | Start |
| 2023-12-04 16:36 | 843078 | bisection+event:ScenariosUpdatedLegacy | basisContAddFactor 0→0,4; basisContMultFactor 0→1,2; scenarioSpotDown 0→0,95; scenarioSpotUp 0→1,05; baseStaticDiscount 0→0,95; imFactor 0→1,25; rateAddScale 0→0,12; rateMultScale 0→1; basePercent 0→0,03; confMargin 0→1; confThreshold 0→0,55; optionPercent 0→0,01; pegLossFactor 0→4; pegLossThreshold 0→0,99; … (+7) |
| 2023-12-11 07:27 | 1129020 | bisection | basisContAddFactor 0,4→1 |
| 2023-12-11 07:27 | 1129024 | bisection | optionPercent 0,01→0,02 |
| 2024-06-12 00:01 | 9064436 | bisection | basisContAddFactor 1→0,5; basisContMultFactor 1,2→2 |
| 2024-09-25 04:47 | 13609010 | bisection+event:MaxExpiriesUpdated | maxExpiries 11→18 |
| 2025-02-22 19:52 | 20116171 | bisection+event:ScenariosUpdatedLegacy | scenarioSpotDown 0,95→0,955; scenarioSpotUp 1,05→1,045; optionPercent 0,02→0,015; volRangeDown 0,3→0,275; volRangeUp 0,6→0,5; scenarios: Gitter ±20 %→±18 % |

**BTC PM2** (23 Einträge, `results/p2/params/BTC_pm2.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2025-06-09 05:18 | 24712334 | start+event:Upgraded+MaxExpiriesUpdated+Initialized+Basis… | Start |
| 2025-06-09 08:21 | 24717845 | event:MarginParamsUpdated | longBaseStaticDiscount 1,05→1,02; longRateMultScale 0→0,1; shortBaseStaticDiscount 0,95→0,98; shortRateMultScale 0→0,1 |
| 2025-06-12 22:20 | 24872593 | event:MarginParamsUpdated | longRateAddScale 0,16→0,1; longRateMultScale 0,1→0; shortRateAddScale 0,16→0,1; shortRateMultScale 0,1→0 |
| 2025-09-17 21:41 | 29061847 | event:MaxExpiriesUpdated | maxExpiries 10→14 |
| 2025-10-10 22:55 | 30057658 | event:OtherContingencyParamsUpdated | confMargin 1→0,4 |
| 2026-01-08 22:50 | 33945517 | event:MarginParamsUpdated | longBaseStaticDiscount 1,02→0,98; shortBaseStaticDiscount 0,98→1,02 |
| 2026-01-23 04:24 | 34560315 | event:ScenariosUpdated | scenarios: Tail-Dämpfung geändert |
| 2026-05-24 04:05 | 39786946 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated… | IMPerpPercent 0,01→0,015; MMPerpPercent 0,03→0,015; volRangeUp 0,5→0,45; scenarios: Gitter ±18 %→±17 %, Tail-Dämpfung geändert |
| 2026-05-24 05:21 | 39789246 | event:BasisContingencyParamsUpdated | scenarioSpotDown 0,955→0,9575; scenarioSpotUp 1,045→1,0425 |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 14→16; Collateral (4 Werte) |
| 2026-08-20 22:09 | 43621075 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0,9575→0,965; scenarioSpotUp 1,0425→1,035; IMOptionPercent 0,002→0,001; IMPerpPercent 0,015→0,0075; MMOptionPercent 0,003→0,0015; MMPerpPercent 0,015→0,0075; minVolUpShock 0,4→0,5; volRangeDown 0,3→0,25; volRangeUp 0,45→0,4; scenarios: Gitter ±17 %→±14 %, Tail-Dämpfung geändert; Collateral (4 Werte) |

Dazu 12 Einträge, die nur `CollateralParameters` ändern (nicht USDC, ausserhalb von K).

**BTC PM2 Override-Lib 0x4e8ea8afeb1f7583c3d1e27176d864fa652546c8** (36 Einträge, `results/p2/params/BTC_pm2_lib_4e8ea8af.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2026-02-03 21:20 | 35065996 | start+event:BasisContingencyParamsUpdated | Start |
| 2026-02-03 21:20 | 35065998 | event:VolShockParamsUpdated | dteFloor 0→86400; longTermPower 0→0,13; minVolUpShock 0→0,4; shortTermPower 0→0,3; volRangeDown 0→0,3; volRangeUp 0→0,5 |
| 2026-02-03 21:20 | 35066000 | event:OtherContingencyParamsUpdated | IMOptionPercent 0→0,002; IMPerpPercent 0→0,01; MMOptionPercent 0→0,003; MMPerpPercent 0→0,03; confMargin 0→0,4; confThreshold 0→0,55; pegLossFactor 0→4; pegLossThreshold 0→0,99 |
| 2026-02-03 21:20 | 35066002 | event:MarginParamsUpdated | imFactor 0→1; longBaseStaticDiscount 0→0,98; longRateAddScale 0→0,1; mmFactor 0→0,35; shortBaseStaticDiscount 0→1,02; shortRateAddScale 0→0,1 |
| 2026-02-03 21:20 | 35066004 | event:SkewShockParamsUpdated | absBaseCap 0→0,25; absCBase 0→-0,1; linearBaseCap 0→0,25; linearCBase 0→-0,1; minKStar 0→0,01; volParamStatic 0→0,6; widthScale 0→4 |
| 2026-05-24 04:05 | 39786946 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated… | IMPerpPercent 0,01→0,015; MMPerpPercent 0,03→0,015; volRangeUp 0,5→0,45; scenarios: Gitter ±18 %→±17 %, Tail-Dämpfung geändert |
| 2026-05-24 05:21 | 39789246 | event:BasisContingencyParamsUpdated | scenarioSpotDown 0,955→0,9575; scenarioSpotUp 1,045→1,0425 |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 14→16; Collateral (4 Werte) |
| 2026-08-20 22:09 | 43621075 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0,9575→0,965; scenarioSpotUp 1,0425→1,035; IMOptionPercent 0,002→0,001; IMPerpPercent 0,015→0,0075; MMOptionPercent 0,003→0,0015; MMPerpPercent 0,015→0,0075; minVolUpShock 0,4→0,5; volRangeDown 0,3→0,25; volRangeUp 0,45→0,4; scenarios: Gitter ±17 %→±14 %, Tail-Dämpfung geändert; Collateral (4 Werte) |

Dazu 27 Einträge, die nur `CollateralParameters` ändern (nicht USDC, ausserhalb von K).

Zuweisungen: 15 Ereignisse für 15 Konten an 9 Tagen (2026-02-17 bis 2026-09-21); Aufhebungen: 0.

**ETH SM** (4 Einträge, `results/p2/params/ETH_sm.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2023-12-04 16:35 | 843061 | start+event:OptionMarginParamsSet+OracleContingencySet+Pe… | Start |
| 2024-06-12 00:03 | 9064496 | event:PerpMarginRequirementsSet | imPerpReq 0,1→0,066; mmPerpReq 0,065→0,05 |
| 2024-10-08 17:49 | 14194091 | event:BaseMarginParamsSet | IMScale 0,9375→0 |
| 2024-10-08 18:46 | 14195796 | event:BaseMarginParamsSet | IMScale 0→0,9375 |

**ETH PM** (6 Einträge, `results/p2/params/ETH_pm.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2023-12-04 16:35 | 843061 | start+event:ScenariosUpdatedLegacy | Start |
| 2023-12-11 07:27 | 1129013 | bisection | basisContAddFactor 0,4→1 |
| 2023-12-11 07:27 | 1129017 | bisection | optionPercent 0,01→0,02 |
| 2024-06-12 00:01 | 9064436 | bisection | basisContAddFactor 1→0,5; basisContMultFactor 1,2→2 |
| 2024-09-25 04:47 | 13609010 | bisection+event:MaxExpiriesUpdated | maxExpiries 11→18 |
| 2025-02-22 19:52 | 20116171 | bisection+event:ScenariosUpdatedLegacy | scenarioSpotDown 0,95→0,955; scenarioSpotUp 1,05→1,045; optionPercent 0,02→0,015; volRangeDown 0,3→0,275; volRangeUp 0,6→0,5; scenarios: Gitter ±20 %→±18 % |

**ETH PM2** (22 Einträge, `results/p2/params/ETH_pm2.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2025-06-09 05:16 | 24712302 | start+event:Upgraded+MaxExpiriesUpdated+Initialized+Basis… | Start |
| 2025-06-09 08:22 | 24717867 | event:MarginParamsUpdated | longBaseStaticDiscount 1,05→1,02; longRateMultScale 0→0,1; shortBaseStaticDiscount 0,95→0,98; shortRateMultScale 0→0,1 |
| 2025-06-12 22:20 | 24872593 | event:MarginParamsUpdated | longRateAddScale 0,16→0,1; longRateMultScale 0,1→0; shortRateAddScale 0,16→0,1; shortRateMultScale 0,1→0 |
| 2025-09-17 21:41 | 29061847 | event:MaxExpiriesUpdated | maxExpiries 10→14 |
| 2025-10-10 22:55 | 30057658 | event:OtherContingencyParamsUpdated | confMargin 1→0,4 |
| 2026-01-08 22:50 | 33945517 | event:MarginParamsUpdated | longBaseStaticDiscount 1,02→0,98; shortBaseStaticDiscount 0,98→1,02 |
| 2026-01-23 04:24 | 34560315 | event:ScenariosUpdated | scenarios: Tail-Dämpfung geändert |
| 2026-05-24 04:05 | 39786946 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated | IMPerpPercent 0,01→0,015; MMPerpPercent 0,03→0,015; volRangeUp 0,5→0,45 |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 14→16; Collateral (4 Werte) |
| 2026-08-20 22:09 | 43621075 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0,955→0,96; scenarioSpotUp 1,045→1,04; IMOptionPercent 0,002→0,001; IMPerpPercent 0,015→0,0075; MMOptionPercent 0,003→0,0015; MMPerpPercent 0,015→0,0075; minVolUpShock 0,4→0,5; volRangeDown 0,3→0,25; volRangeUp 0,45→0,4; scenarios: Gitter ±18 %→±16 %, Tail-Dämpfung geändert; Collateral (3 Werte) |

Dazu 12 Einträge, die nur `CollateralParameters` ändern (nicht USDC, ausserhalb von K).

**ETH PM2 Override-Lib 0x902e386778456398888a8872e51f73f23f8845f9** (35 Einträge, `results/p2/params/ETH_pm2_lib_902e3867.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2026-02-03 21:19 | 35065988 | start+event:BasisContingencyParamsUpdated | Start |
| 2026-02-03 21:19 | 35065989 | event:VolShockParamsUpdated | dteFloor 0→86400; longTermPower 0→0,13; minVolUpShock 0→0,4; shortTermPower 0→0,3; volRangeDown 0→0,3; volRangeUp 0→0,5 |
| 2026-02-03 21:19 | 35065990 | event:OtherContingencyParamsUpdated | IMOptionPercent 0→0,002; IMPerpPercent 0→0,01; MMOptionPercent 0→0,003; MMPerpPercent 0→0,03; confMargin 0→0,4; confThreshold 0→0,55; pegLossFactor 0→4; pegLossThreshold 0→0,99 |
| 2026-02-03 21:19 | 35065992 | event:MarginParamsUpdated | imFactor 0→1; longBaseStaticDiscount 0→0,98; longRateAddScale 0→0,1; mmFactor 0→0,35; shortBaseStaticDiscount 0→1,02; shortRateAddScale 0→0,1 |
| 2026-02-03 21:20 | 35065994 | event:SkewShockParamsUpdated | absBaseCap 0→0,25; absCBase 0→-0,1; linearBaseCap 0→0,25; linearCBase 0→-0,1; minKStar 0→0,01; volParamStatic 0→0,6; widthScale 0→4 |
| 2026-05-24 04:05 | 39786946 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated | IMPerpPercent 0,01→0,015; MMPerpPercent 0,03→0,015; volRangeUp 0,5→0,45 |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 14→16; Collateral (4 Werte) |
| 2026-08-20 22:09 | 43621075 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0,955→0,96; scenarioSpotUp 1,045→1,04; IMOptionPercent 0,002→0,001; IMPerpPercent 0,015→0,0075; MMOptionPercent 0,003→0,0015; MMPerpPercent 0,015→0,0075; minVolUpShock 0,4→0,5; volRangeDown 0,3→0,25; volRangeUp 0,45→0,4; scenarios: Gitter ±18 %→±16 %, Tail-Dämpfung geändert; Collateral (3 Werte) |

Dazu 27 Einträge, die nur `CollateralParameters` ändern (nicht USDC, ausserhalb von K).

Zuweisungen: 16 Ereignisse für 16 Konten an 9 Tagen (2026-02-10 bis 2026-09-21); Aufhebungen: 0.

**HYPE SM** (6 Einträge, `results/p2/params/HYPE_sm.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2025-10-24 03:12 | 30626980 | start+event:OracleContingencySet+PerpMarginRequirementsSe… | Start |
| 2025-10-29 21:59 | 30876782 | event:BaseMarginParamsSet | IMScale 0→0,834; marginFactor 0→0,6 |
| 2026-04-07 01:40 | 37752209 | event:PerpMarginRequirementsSet | imPerpReq 0,15→0,2 |
| 2026-04-14 21:06 | 38089586 | event:BaseMarginParamsSet | IMScale 0,834→0,75 |
| 2026-05-21 21:38 | 39688948 | event:PerpMarginRequirementsSet | imPerpReq 0,2→0,1; mmPerpReq 0,1→0,08 |
| 2026-08-20 22:09 | 43621075 | event:BaseMarginParamsSet | IMScale 0,75→0,9167 |

**HYPE PM2** (21 Einträge, `results/p2/params/HYPE_pm2.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2025-10-16 10:29 | 30294479 | start+event:Upgraded+MaxExpiriesUpdated+Initialized | Start |
| 2025-10-16 10:47 | 30295019 | event:ScenariosUpdated | scenarios: Gitter ±33 %, Tails 0→8, 0→33 Szenarien |
| 2025-10-16 10:47 | 30295021 | event:BasisContingencyParamsUpdated | basisContAddFactor 0→0,5; basisContMultFactor 0→2; scenarioSpotDown 0→0,9175; scenarioSpotUp 0→1,0825 |
| 2025-10-16 10:47 | 30295023 | event:VolShockParamsUpdated | dteFloor 0→86400; longTermPower 0→0,13; minVolUpShock 0→0,6; shortTermPower 0→0,3; volRangeDown 0→0,3; volRangeUp 0→0,65 |
| 2025-10-16 10:47 | 30295025 | event:OtherContingencyParamsUpdated | IMOptionPercent 0→0,0075; IMPerpPercent 0→0,025; MMOptionPercent 0→0,0175; MMPerpPercent 0→0,075; confMargin 0→0,4; confThreshold 0→0,55; pegLossFactor 0→4; pegLossThreshold 0→0,99 |
| 2025-10-16 10:47 | 30295027 | event:MarginParamsUpdated | imFactor 0→1,15; longBaseStaticDiscount 0→1,02; longRateAddScale 0→0,1; mmFactor 0→0,95; shortBaseStaticDiscount 0→0,98; shortRateAddScale 0→0,1 |
| 2025-10-16 10:47 | 30295028 | event:SkewShockParamsUpdated | absBaseCap 0→0,25; absCBase 0→-0,1; linearBaseCap 0→0,25; linearCBase 0→-0,1; minKStar 0→0,01; volParamStatic 0→0,6; widthScale 0→4 |
| 2025-10-17 04:27 | 30326813 | event:ScenariosUpdated | scenarios: Tails 8→7, 33→32 Szenarien |
| 2026-01-08 22:50 | 33945517 | event:MarginParamsUpdated | longBaseStaticDiscount 1,02→0,98; shortBaseStaticDiscount 0,98→1,02 |
| 2026-05-08 12:24 | 39110724 | event:BasisContingencyParamsUpdated+OtherContingencyParam… | basisContAddFactor 0,5→0,25; IMOptionPercent 0,0075→0,004; IMPerpPercent 0,025→0,01; MMOptionPercent 0,0175→0,006; MMPerpPercent 0,075→0,05 |
| 2026-05-24 04:05 | 39786946 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0,9175→0,9325; scenarioSpotUp 1,0825→1,0675; imFactor 1,15→1,1; mmFactor 0,95→0,9; IMPerpPercent 0,01→0,015; MMPerpPercent 0,05→0,02; volRangeUp 0,65→0,6; scenarios: Gitter ±33 %→±27 %, Tails 7→8, 32→33 Szenarien |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 10→16; Collateral (4 Werte) |
| 2026-08-20 22:09 | 43621075 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated… | imFactor 1,1→1; mmFactor 0,9→0,8; IMOptionPercent 0,004→0,002; IMPerpPercent 0,015→0,0075; MMOptionPercent 0,006→0,003; MMPerpPercent 0,02→0,01; volRangeUp 0,6→0,5; scenarios: Tail-Dämpfung geändert; Collateral (4 Werte) |

Dazu 8 Einträge, die nur `CollateralParameters` ändern (nicht USDC, ausserhalb von K).

**HYPE PM2 Override-Lib 0xf4caea4e521642d9dd2a4751140cc73d78adaa17** (16 Einträge, `results/p2/params/HYPE_pm2_lib_f4caea4e.json`)

| ab (UTC) | Block | Quelle | Änderung |
|---|---|---|---|
| 2026-02-03 21:20 | 35066014 | start+event:BasisContingencyParamsUpdated | Start |
| 2026-02-03 21:20 | 35066016 | event:VolShockParamsUpdated | dteFloor 0→86400; longTermPower 0→0,13; minVolUpShock 0→0,6; shortTermPower 0→0,3; volRangeDown 0→0,3; volRangeUp 0→0,65 |
| 2026-02-03 21:20 | 35066018 | event:OtherContingencyParamsUpdated | IMOptionPercent 0→0,0075; IMPerpPercent 0→0,025; MMOptionPercent 0→0,0175; MMPerpPercent 0→0,075; confMargin 0→0,4; confThreshold 0→0,55; pegLossFactor 0→4; pegLossThreshold 0→0,99 |
| 2026-02-03 21:20 | 35066020 | event:MarginParamsUpdated | imFactor 0→1,15; longBaseStaticDiscount 0→0,98; longRateAddScale 0→0,1; mmFactor 0→0,45; shortBaseStaticDiscount 0→1,02; shortRateAddScale 0→0,1 |
| 2026-02-03 21:20 | 35066022 | event:SkewShockParamsUpdated | absBaseCap 0→0,25; absCBase 0→-0,1; linearBaseCap 0→0,25; linearCBase 0→-0,1; minKStar 0→0,01; volParamStatic 0→0,6; widthScale 0→4 |
| 2026-05-08 12:24 | 39110724 | event:BasisContingencyParamsUpdated+OtherContingencyParam… | basisContAddFactor 0,5→0,25; IMOptionPercent 0,0075→0,004; IMPerpPercent 0,025→0,01; MMOptionPercent 0,0175→0,006; MMPerpPercent 0,075→0,05 |
| 2026-05-24 04:05 | 39786946 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0,9175→0,9325; scenarioSpotUp 1,0825→1,0675; imFactor 1,15→1,1; mmFactor 0,45→0,4; IMPerpPercent 0,01→0,015; MMPerpPercent 0,05→0,02; volRangeUp 0,65→0,6; scenarios: Gitter ±33 %→±27 %, Tails 7→8, 32→33 Szenarien |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 10→16; Collateral (4 Werte) |
| 2026-08-20 22:09 | 43621075 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated… | imFactor 1,1→1; IMOptionPercent 0,004→0,002; IMPerpPercent 0,015→0,0075; MMOptionPercent 0,006→0,003; MMPerpPercent 0,02→0,01; volRangeUp 0,6→0,5; scenarios: Tail-Dämpfung geändert; Collateral (4 Werte) |

Dazu 7 Einträge, die nur `CollateralParameters` ändern (nicht USDC, ausserhalb von K).

Zuweisungen: 10 Ereignisse für 10 Konten an 8 Tagen (2026-02-17 bis 2026-09-21); Aufhebungen: 0.

## A5 Maker-Bestände (`derive_surface/books.py`)

Stand 24.09.2026. Tests `tests/test_p2_books.py` (16, offline; Fixtures `tests/fixtures/p2/books_chain_snapshot.json`
mit einer echten Multicall-Antwort und `books_subid_api.json` mit vier Antworten von `public/get_instrument`).
RPC-Log `data/p2/logs/A5.jsonl`. Subaccounts hier nur als `sha256(str(id))[:10]`, rohe IDs in
`data/p2/books/top_makers.json`.

**Dominante Maker-Subaccounts** (meiste Maker-Fills in `data/p1/derived/markouts.parquet`, 603 940 Fills). Kein Konto
hat im Zeitraum den Manager gewechselt.

| Rang | Konto | Maker-Fills | Manager | erster Snapshot | Tage | Median Optionsbeine je Tag |
|---|---|---|---|---|---|---|
| 1 | M1 | 101 791 | PM:ETH | 11.01.2024 | 981 | 71 |
| 2 | M2 | 39 910 | SM | 11.01.2024 | 981 | 20 |
| 3 | M3 | 32 567 | PM2:HYPE | 11.11.2025 | 311 | 182 |
| 4 | M4 | 31 795 | PM:ETH | 14.12.2024 | 643 | 97 |
| 5 | M5 | 30 109 | PM2:ETH | 30.08.2025 | 384 | 187 |
| 6 | M6 | 27 227 | PM:BTC | 11.01.2024 | 981 | 44 |
| 7 | M7 | 22 173 | PM:ETH | 16.04.2024 | 885 | 102 |
| 8 | M8 | 21 707 | PM2:ETH | 24.09.2025 | 359 | 139,5 |
| 9 | M9 | 19 133 | PM:ETH | 11.01.2024 | 981 | 34 |
| 10 | M10 | 16 618 | PM2:ETH | 26.09.2025 | 357 | 197 |

Median der Optionsbeine über Tage mit mindestens einer Option.

**Snapshots.** `data/p2/books/snapshots.parquet`: 403 801 Zeilen, 6 863 Konto-Tage (4 488 mit Optionen), jeder
UTC-Tag vom 11.01.2024 bis 17.09.2026 am ersten Block des Tages (00:00:01 UTC, Blöcke 2 454 793 bis 44 790 793).
Ein Konto erscheint ab dem ersten Tagesbeginn, an dem `SubAccounts.manager(id)` nicht null ist (Erstellung).
Geladen mit einem `eth_call` je Tag: Multicall3 (`aggregate3`, Code auf Chain 957 schon vor Block 2 454 793) bündelt
`getAccountBalances` und `manager` aller zehn Konten; 981 Aufrufe plus 5 `cashAsset()`-Aufrufe, zwei Läufe von
zusammen 12 min, wiederaufnehmbar über eine JSON-Datei je Tag unter `data/p2/books/raw/`. Alle fünf beteiligten
Manager liefern dasselbe Cash-Asset `0x57b03e14…` (USDC).

| kind | Zeilen | Inhalt |
|---|---|---|
| option | 388 734 | ETH 303 916, HYPE 50 764, BTC 34 054 |
| cash | 6 614 | USDC |
| perp | 4 959 | 21 Basiswerte, am häufigsten ETH 2 135, HYPE 528, BTC 446 |
| base | 3 247 | ETH, WEETH, FXUSDC, USDT, WSTETH, BTC, SUSDE, DRV |
| none | 247 | Konto existiert, aber ohne Bestand (Manager gespeichert) |

Kein Asset blieb unklassifiziert. Spalten wie im Plan, dazu `balance_raw` (exakter 1e18-Wert als Text) und
`manager_label` (`SM`, `PM:BTC`, `PM2:ETH` usw.); `sub_id` als Dezimaltext, weil uint96 nicht in int64 passt.
SubId-Dekodierung nach `OptionEncoding.fromSubId`, geprüft an vier Instrumenten gegen `base_asset_sub_id` der API
(BTC, ETH, HYPE mit Strike 38,75): exakt.

**Abgleich Tagesbeginn plus Fills gegen Folgetag.** Bestand zu Tagesbeginn plus alle Tape-Fills des Kontos am Tag
(Maker- und Taker-Zeilen, Optionen auf BTC, ETH, HYPE) gegen den Bestand am nächsten Tagesbeginn; Beine mit Verfall
bis zum nächsten Tagesbeginn fallen auf beiden Seiten weg; Treffer bei einer Abweichung von höchstens 1e−9 Kontrakten.
Maker-Tag: Konto-Tag mit mindestens einem Maker-Fill und Snapshot am Folgetag (4 300).

| | Maker-Tage | vollständig gleich | Beine | Beine gleich |
|---|---|---|---|---|
| 20 Zufalls-Maker-Tage (Seed 20260924) | 20 | 6 (30 %) | 1 362 | 908 (66,7 %) |
| alle Maker-Tage | 4 300 | 1 713 (39,8 %) | 443 893 | 360 818 (81,3 %) |

Ein um 10, 60 oder 300 s verschobenes Fill-Fenster ändert nichts zum Besseren (1 703, 1 642, 1 439 gleiche Tage);
Verzug zwischen Match und Settlement ist nicht die Ursache. Je Konto (Anteil vollständig gleicher Maker-Tage):
die PM2-Konten M5 99,7 %, M3 98,7 %, M10 96,8 %, aber M8 25,4 %; die PM- und
SM-Konten M7 68,8 %, M6 24,5 %, M1 17,4 %, M4 16,3 %, M2 15,0 %,
M9 8,2 %.

**Ursache (on-chain an denselben 20 Tagen).** `BalanceAdjusted`-Events der SubAccounts je Konto zwischen den beiden
Snapshot-Blöcken, Transaktionen ausserhalb des Tapes über ihr Receipt zugeordnet (1 632 Receipts; Skript
`data/p2/books/diag_onchain.py`, Ergebnis `data/p2/books/diag_onchain.json`):
- Snapshot plus on-chain Optionsbuchungen ergibt den Snapshot des Folgetags für 1 002 von 1 002 Beinen. Die
  Snapshots sind in sich exakt.
- Vom bewegten Optionsvolumen (Summe der Beträge) stehen 57,8 % in Transaktionen, die das Tape des Kontos enthält;
  24,6 % sind Settlement verfallener Optionen (Transaktion nur mit Manager-Events); 16,4 % sind Trades über das
  Trade-Modul mit Subaccounts derselben Wallet; 1,2 % sind Trades über das Trade-Modul mit Gegenkonten, die im Tape
  gar nicht vorkommen.
- Die Abweichungen sind also Umbuchungen zwischen Subaccounts desselben Betreibers, abgewickelt als Trades über das
  Trade-Modul (zum Beispiel M2 mit M8, beide unter den zehn). Die öffentliche Trade-Historie, aus der
  das Tape von Paper 1 stammt, enthält sie nicht. Liquidationen kamen an diesen Tagen nicht vor.

**Folge für B3.** Das präregistrierte Buch vor dem Fill (Tagesbeginn plus Tape-Fills des Tages) trifft das
tatsächliche Buch der PM2-Konten M5, M3 und M10 fast immer, das der übrigen Konten an vielen
Tagen nicht. Exakt wäre das on-chain Buch am Block des Fills aus Tagesbeginn plus `BalanceAdjusted`. Über einen
datierten Nachtrag entscheidet der Orchestrator. Am Erstellungstag eines Kontos gibt es keinen Snapshot, weil das
Konto um 00:00 UTC noch nicht existierte; das Buch zu Tagesbeginn ist dann leer.

### A5 Fix-Runde (25.09.2026)

Nach dem Review geändert: `derive_surface/books.py` und `tests/test_p2_books.py` (jetzt 36 Tests, 20 davon neu,
offline). Neue Fixture `tests/fixtures/p2/books_events_day.json` mit echten Chain-Daten eines PM2-Kontos am
13.02.2026: Snapshots zu Tagesbeginn und am Folgetag, 109 `BalanceAdjusted`-Logs des Tages, `getAccountBalances` am
Block vor und am Block des Fills. Nur `topics[1]` ist durch den Platzhalter 4242 ersetzt.

**Zeitstempel des Buchs vor dem Fill (behoben).** Der Bericht zu A5 nannte für `book_at` den Zeitstempel "wie
`markouts.ts`". Das war falsch: `markouts.ts` ist die Taker-Zeile, und bei RFQ-Fills ist die Maker-Zeile älter.
Betroffen sind 62 929 von 343 030 Fills der zehn Konten und 41 294 von 101 001 Fills (40,9 %) der vier PM2-Konten;
Abstand bei PM2 im Median 4,0 s, 90 % unter 11,2 s, höchstens 10,5 min (über alle Fills höchstens 28 min). Mit
`markouts.ts` wäre der Fill selbst im Buch vor dem Fill gelandet. Jetzt gilt:
- `book_at(snapshot_rows, tape_rows, ts, subaccount=None, exclude_trade_ids=None)`: `ts` ist der Zeitstempel der
  eigenen Tape-Zeile des Kontos, für Maker-Fills also `markouts.ts_maker`. `ts` ausserhalb des Tags der
  Snapshot-Zeilen oder in Sekunden ergibt `ValueError`.
- `book_before_fill(snapshot_rows, tape_rows, trade_id, subaccount=None)` schneidet an der eigenen Zeile und lässt die
  `trade_id` des Fills immer weg. Für B3 ist das der vorgesehene Aufruf.
- `fill_day(ts_maker)` liefert den Snapshot-Tag. Bei 3 Fills der zehn Konten liegt der Maker-Tag vor dem Taker-Tag.
- Fills derselben Millisekunde bleiben draussen, wie präregistriert ("früherer Zeitstempel"). Das betrifft
  weitere Beine einer RFQ-Mehrbeinorder und gebündelte Matches: 69 291 von 395 232 Tape-Zeilen der zehn Konten
  (PM2: 27 303 von 110 617) teilen sich Konto und Millisekunde mit einem anderen Fill.

**Perps im präregistrierten Buch.** Das Tape von Paper 1 enthält nur Optionen. Im Buch aus Tagesbeginn plus Tape
stehen Perps deshalb auf dem Stand zu Tagesbeginn. Das steht jetzt auch im Docstring. Wie oft sich die Perp-Position
(BTC, ETH, HYPE) von einem Tagesbeginn zum nächsten ändert, zeigt `python3 -m derive_surface.books perp-drift` →
`data/p2/books/perp_drift.json`. Gezählt werden Paare aufeinanderfolgender Tage mit zwei Snapshots; die Änderung ist
die Summe von |Δ Perp| über die Basiswerte, in Kontrakten.

| Konto | Manager | Tagespaare | Paare mit Änderung | Median Änderung |
|---|---|---|---|---|
| M1 | PM:ETH | 980 | 108 (11,0 %) | 14,1 |
| M2 | SM | 980 | 45 (4,6 %) | 0,39 |
| M3 | PM2:HYPE | 310 | 209 (67,4 %) | 10 456 |
| M4 | PM:ETH | 642 | 8 (1,2 %) | 100 |
| M5 | PM2:ETH | 383 | 60 (15,7 %) | 160 |
| M6 | PM:BTC | 980 | 89 (9,1 %) | 0,40 |
| M7 | PM:ETH | 884 | 298 (33,7 %) | 47,5 |
| M8 | PM2:ETH | 358 | 30 (8,4 %) | 2,9 |
| M9 | PM:ETH | 980 | 0 | 0 |
| M10 | PM2:ETH | 356 | 3 (0,8 %) | 78,7 |

Das erfasst keine Perps, die im Lauf eines Tages geöffnet und wieder geschlossen werden. Für die PM2-Konten misst
das der Vergleich am Fill (unten).

**Exaktes on-chain Buch (neu, `books.py` Teil 2 vorgezogen).** Der Decoder aus `data/p2/books/diag_onchain.py` liegt
jetzt im Paket, mit Tests auf echten Logs:
- `decode_balance_adjusted(log)`, `fetch_balance_events(rpc, subaccount, lo, hi)`: `BalanceAdjusted`-Events der
  SubAccounts, gefiltert auf `accountId`. Das Fenster wird nur halbiert, wenn der Knoten zu viele Ergebnisse meldet;
  nach dünnen Fenstern wächst es wieder. Netzfehler werden nicht aufgeteilt.
- `load_events(...)` / `compact_events(...)`: je (Konto, UTC-Tag) die Blöcke (erster Block des Tages, erster Block des
  Folgetags], also genau die Änderungen zwischen zwei Snapshots. Wiederaufnehmbar, eine Datei je Konto-Tag unter
  `data/p2/books/events/`, zusammengefasst in `data/p2/books/events.parquet` (Spalten `subaccount, day, block,
  tx_index, log_index, tx_hash, manager, asset, sub_id, amount_raw, pre_raw, post_raw, trade_id, amount, kind, ccy`).
- `replay_balances(snapshot_rows, events, tx_hash=None, include_tx=False)` und `replay_balances_many`: Snapshot plus
  Events in Chain-Reihenfolge bis vor (bzw. durch) die Transaktion. Der `preBalance` jedes Events muss dem laufenden
  Stand gleichen, sonst `ValueError`. So fallen fehlende Events oder ein falscher Snapshot sofort auf.
- `onchain_book_before(snapshot_rows, events, tx_hash, registry=None, ts=None, include_tx=False)` und
  `OnchainBooks(snapshots, events).before(subaccount, tx_hash)` bzw. `.before_many(subaccount, tx_hashes)` liefern
  `dict[ccy, Book]` mit Optionen und Perps (Verfall-Schnitt an der Blockzeit, `perp_entry = None`, `cash = 0`). Der Tag
  ist der Tag der Event-Datei, die die Transaktion enthält, also der UTC-Tag des Blocks.

Prüfungen an echten Daten (Fixture): Snapshot plus alle 109 Events des Tages ergeben den Snapshot des Folgetags für
alle Assets auf das Wei genau, auch Cash und das Settlement um 08:00. Snapshot plus Events bis vor die
Fill-Transaktion ergeben exakt `getAccountBalances` am Block davor, bis durch die Transaktion exakt den Stand am
Fill-Block. Das präregistrierte Buch desselben Fills weicht ab, weil 24 Trades über das Trade-Modul fehlen.

**Event-Daten der PM2-Konten.** `python3 -m derive_surface.books events --accounts pm2` (wiederaufnehmbar, vier
Läufe von je etwa 9 min, RPC-Log `data/p2/logs/A5.jsonl`) lädt alle 1 168 Konto-Tage mit Maker-Fills der vier
PM2-Konten: 1 994 826 Events (Cash 1 380 421, Perp 483 567, Option 130 629, Collateral 209), 136 MB. Alle 101 169
Maker-Zeilen dieser Konten im Tape finden ihre Transaktion in den Events des Tages ihrer Maker-Zeile. Kein Fill wurde
erst nach Mitternacht abgewickelt (`data/p2/books/events_coverage.json`). Mit `verify-events` ergibt an allen 1 165
Konto-Tagen mit Snapshot am Folgetag der Snapshot plus die Events exakt den Folgetag, für alle Assets und bei jedem
passenden `preBalance` (`data/p2/books/events_verify.json`). Für die übrigen sechs Konten sind keine Events geladen;
`--accounts all` holt sie nach (3 175 weitere Konto-Tage).

**Tape-Buch gegen Chain-Buch am Fill (H2-Population).** `python3 -m derive_surface.books compare --n 5000` →
`data/p2/books/compare_books.json`: 5 000 zufällige Maker-Fills (Seed 20260924) aus den 101 001 Fills der vier
PM2-Konten in `markouts`. Verglichen wird im Basiswert des Fills `book_before_fill` mit `OnchainBooks.before`, beide
mit Verfall-Schnitt an `ts_maker`; gleich heisst Abweichung je Bein höchstens 1e−9 Kontrakte.

| Konto | Fills | Optionen gleich | Perp gleich | beides gleich |
|---|---|---|---|---|
| alle vier | 5 000 | 88,4 % | 70,2 % | 62,2 % |
| M5 (PM2:ETH) | 1 529 | 98,2 % | 83,2 % | 82,2 % |
| M8 (PM2:ETH) | 1 034 | 52,9 % | 85,9 % | 52,0 % |
| M10 (PM2:ETH) | 817 | 97,7 % | 99,0 % | 96,7 % |
| M3 (PM2:HYPE) | 1 620 | 97,0 % | 33,5 % | 32,6 % |

Bei M8 weicht die Optionsmenge am 90. Perzentil um 11,3 % ab (Summe |Δ| über die Beine relativ zur
Bruttomenge des Chain-Buchs). Bei M3 liegt die Perp-Position des Tape-Buchs im Median 3 321 HYPE-Kontrakte
(8,1 % der Position) neben der Chain. Unter PM2 verrechnet die Perp-Position das Options-Delta. Das präregistrierte
Buch verzerrt ΔK also vor allem bei diesen beiden Konten; wie stark, zeigt erst B3 mit beiden Büchern.

**Kleinere Punkte.** `fetch_raw` halbiert Multicall-Bündel nur noch bei Fehlern des Knotens (`RpcError`) und reicht
Netzfehler durch. `diag_onchain.py` nutzt den Paket-Decoder und teilt ebenfalls nur bei `RpcError`. Die Fixture
`books_chain_snapshot.json` nennt jetzt die Herkunft von `encoder_reference`: Es ist eine Regressionsreferenz, das
ABI-Layout wurde im Review mit `eth_abi` geprüft. Neue Tests decken `manager_label`, `classify` → `other`, `ts` in
Sekunden, ein Konto nur mit Perp und die Spalte `manager_label` in `compact` ab. Ein falscher Testkommentar ist
korrigiert.

**Offen für den Orchestrator.** (1) Ein datierter Nachtrag in `PRAEREGISTRIERUNG.md`: Buch vor dem Fill = Snapshot zu
Tagesbeginn plus `BalanceAdjusted`-Events des Kontos bis vor die Transaktion des Fills (`onchain_book_before`), mit
Optionen und Perps. Die Alternative ist, das präregistrierte Tape-Buch beizubehalten und die Perps ausdrücklich auf
dem Stand zu Tagesbeginn einzufrieren. (2) Die Pseudonymisierung `sha256(str(id))[:10]` lässt sich bei kleinen IDs
durch Durchprobieren sofort zurückrechnen, auch bei Konten unter den zehn. Für `results/` und das Paper braucht es
einen geheimen Salt oder Rang-Labels (M1 bis M10).

## A1 Feed-Historie (`derive_surface/p2feeds.py`)

Stand 24.09.2026. Alle Spot-, Forward-, PM2-Zins- und Perp-Pushes von BTC, ETH und HYPE auf Chain 957 vom Deploy des
jeweiligen Feeds bis Block 44 815 000 (17.09.2026 13:26:55 UTC), dazu der statische Zins-Feed des Legacy-PM,
vollständig geladen und je Feed zu einer Datei verdichtet. Die SVI-Kurven kommen unverändert aus `data/p1/volfeed/`.

**Quellen.** Adressen aus `deploy.json`, `addresses_head.json` und `eth_call` am 24.09.2026, im Code als `FEEDS`
(mit Deploy-Block je Feed):

| | Spot | Forward | Zins PM2 | Zins Legacy-PM | Perp-Preis (`PerpAsset.perpFeed()`) |
|---|---|---|---|---|---|
| BTC | `0x5eb5…fdb0` ab 843 075 | `0x958c…6279` ab 843 075 | `0x37d2…5461` ab 24 712 333 | `0x6fef…004f` | `0x34bc…4475` ab 843 076 |
| ETH | `0x727a…d6d5` ab 843 059 | `0x791a…f948` ab 843 059 | `0x1406…77e3` ab 24 712 300 | `0x30a6…9feb` | `0x33e1…d7c6` ab 843 059 |
| HYPE | `0x4fde…b143` ab 30 293 595 | `0x0f79…b695` ab 30 294 426 | `0x1852…0f17` ab 30 294 452 | keiner | `0x947e…503b` ab 30 294 378 |

Die Adressen haben nie gewechselt: `OraclesSet` des SRM nur beim Anlegen der Märkte, `PerpFeedUpdated` und
`SpotFeedUpdated` an Perp-Asset und Perp-Feed nur beim Deploy, der Perp-Feed hängt am selben Spot-Feed wie die
Optionen. `spotDiffCap` ist auf allen drei Perp-Feeds seit dem Deploy 0,06 (einziges `SpotDiffCapUpdated`). Der
Legacy-Zins-Feed ist ein `LyraRateFeedStatic` mit einem einzigen `RateUpdated(int64,uint64)` beim Deploy (Zins 0,
Konfidenz 1); `getInterestRate` liefert an den Blöcken 3 000 000, 20 000 000 und 44 812 000 jeweils 0. Heartbeats am
Block 44 812 000: Spot 180 s, Forward 3 600 s, Vol 1 200 s, Zins PM2 43 200 s, Perp 1 200 s. Multicall3 hat Code
ab etwa Block 1 935 198 (A2) und wird für die Gegenprobe genutzt.

**Ereignisse** (v2-core `src/interfaces`, Topics als keccak der Signatur im Code, an echten Logs geprüft):
`SpotPriceUpdated(uint96,uint96,uint64)`, `ForwardDataUpdated(uint64 indexed,(int96,uint64,uint64),(uint256,uint256))`,
`RateUpdated(uint64 indexed,int96,uint96,uint64)`, `SpotDiffUpdated(int96,uint96,uint64)` und für den Legacy-Feed
`RateUpdated(int64,uint64)`. Jeder Feed ignoriert Updates mit älterer oder gleicher Signaturzeit ohne Event, der
Speicher nach Block B ist also durch das letzte Event bis B vollständig bestimmt.

**Download.** `python3 -m derive_surface.p2feeds sync` in Stücken zu 250 000 Blöcken, jedes Stück atomar nach
`data/p2/feeds/raw/{CCY}/{kind}/`, wiederaufnehmbar; das Blockfenster je `eth_getLogs` folgt der beobachteten
Dichte (Ziel 8 000 Logs, Knotenlimit 10 000). Mit `--part k/n` teilen sich mehrere Prozesse einen Feed. Geladen am
24.09.2026 zwischen 20:40 und 21:45 UTC in sieben Runden zu je höchstens 7 min mit 4 bis 14 Prozessen, jeder
höchstens 2 Anfragen/s (gemessen zusammen etwa 4/s); 10 633 `eth_getLogs`, 6 Antworten HTTP 429 und ein
abgebrochener Transfer, alle per Backoff wiederholt. Log `data/p2/logs/A1.jsonl` (10 740 Anfragen inklusive Proben, Fixtures und Gegenprobe). Rohdaten 652 MB.

**Ergebnis.** `python3 -m derive_surface.p2feeds compact` schreibt `data/p2/feeds/{CCY}_{kind}.parquet`, sortiert
nach (expiry, block, log_index), Spalten `block, block_ts, log_index, expiry, value, confidence, feed_ts`, beim
Forward zusätzlich `fixed`. Alle Dateien decken den Bereich vom Deploy bis 44 815 000 lückenlos ab; `block_ts`
stimmt in allen 73 065 073 Zeilen mit der Blockformel überein, `feed_ts ≤ block_ts` überall.

| Feed | BTC | ETH | HYPE | erster Push (BTC / ETH / HYPE, UTC) |
|---|---|---|---|---|
| spot | 2 178 655 | 2 188 491 | 1 060 313 | 06.12.2023 05:03 / 06.12.2023 03:13 / 24.10.2025 09:56 |
| forward | 17 240 756 (968 Verfälle) | 17 253 562 (967) | 5 278 676 (325) | 08.12.2023 23:49 / 06.12.2023 03:13 / 24.10.2025 09:57 |
| rate_pm2 | 9 732 031 (477 Verfälle) | 9 741 690 (477) | 5 277 930 (325) | 12.06.2025 18:56 / 12.06.2025 18:57 / 24.10.2025 09:57 |
| perp | 1 319 631 | 1 322 389 | 470 947 | 06.12.2023 05:23 / 06.12.2023 03:13 / 24.10.2025 09:57 |
| rate_pm | 1 | 1 | – | Deploy |
| Grösse | 314 MB | 314 MB | 114 MB | |

Der erste PM2-Zins-Push am 12.06.2025 gegen 19 Uhr bestätigt, dass der Rate-Feed bis dahin veraltet war; das
PM2-Fenster der Präregistrierung (ab 12.06.2025 23:00 UTC) liegt ganz danach.

**Semantik von `FeedHistory`.** Je Feed gilt der letzte Push mit `block_ts ≤ ts` (bei Fills `ts = ts_ms // 1000`,
das wählt genau die Pushes mit `block_ts · 1000 ≤ ts_ms`). Forward exakt wie `LyraForwardFeed.getForwardPricePortions`:
variabel = aktueller Spot + `fwdSpotDifference`; wurde der Forward-Push weniger als 30 min vor Verfall signiert,
kommt der feste Anteil (currentSpotAggregate − settlementStartAggregate) / 1800 dazu und der variable Anteil wird mit
(Verfall − Signaturzeit) / 1800 skaliert. Forward-Konfidenz = min(Forward, Spot). Perp = Spot + spotDiff, begrenzt auf
±0,06 · Spot, Konfidenz min(Perp, Spot). Zins aus dem PM2-Feed je Verfall, 0 (Konfidenz 1) ohne Wert; `rate_pm` ist
der statische Legacy-Zins (0). SVI aus `volfeed`, Vol exakt wie `LyraVolFeed.getVol`. Das Alter je Feed ist
`ts − feed_ts` (Signaturzeit, die Uhr der Staleness-Prüfungen der Verträge); Paper 1 misst `svi_age_s_t` dagegen ab
dem Push. `state_at` liefert `FeedExpiryState` (Unterklasse von `ExpiryState`) mit den Feldern `fwd_fixed` und
`rate_conf`, die `margin_pm2` und `margin_pm` lesen; `bulk` liefert dieselben Werte als Spalten (dazu `perp`,
`spot_conf`, `perp_conf`, `rate_pm`). Kein Wert wird wegen seines Alters verworfen.

**Gegenprobe** (`python3 -m derive_surface.p2feeds crosscheck`, Ergebnis `data/p2/feeds/crosscheck_{CCY}.json`):
an 10 Zufallsblöcken je Basiswert (Seed 20260924; BTC und ETH ab Block 2 454 793, HYPE ab Forward-Deploy plus ein Tag)
`getSpot`, `getForwardPrice` für jeden Verfall mit Forward-Push der letzten Stunde, `getInterestRate` des PM2-Feeds
und `getPerpPrice` per `eth_call` über Multicall3 gegen `state_at`.

| | Aufrufe | Spot | Forward | Zins PM2 | Perp | Konfidenzen gleich |
|---|---|---|---|---|---|---|
| BTC | 190 | 10 von 10 exakt | 114 von 114 exakt | 56 von 56 exakt | 9 von 10 exakt, Rest 1,4e-16 relativ | 190 von 190 |
| ETH | 190 | 10 von 10 exakt | 114 von 114 exakt | 56 von 56 exakt | 9 von 10 exakt, Rest 1,3e-16 relativ | 190 von 190 |
| HYPE | 190 | 10 von 10 exakt | 85 von 85 exakt | 85 von 85 exakt | 9 von 10 exakt, Rest 1,2e-16 relativ | 190 von 190 |

Kein Aufruf revertierte. Zusätzlich im Settlement-Fenster (je Basiswert 5 zufällige Verfälle, Block 10 min vor
Verfall, `data/p2/feeds/crosscheck_settlement.json`): alle 15 Forwards im Fenster haben einen festen Anteil > 0 und
treffen die Chain bis auf höchstens 1 ulp (max. relativ 2,2e-16), über alle 189 Forwards dieser Blöcke ebenso.
Die verbleibenden Reste sind Rundung der Gleitkomma-Addition Spot + Differenz; in Ganzzahlarithmetik
(`forward_portions_int`) stimmt der Forward im Fixture-Fall bitgenau mit `getForwardPricePortions` überein.

**Leistung und Abgleich mit Paper 1.** `FeedHistory(ccy)` mit SVI lädt BTC in 8 s, ETH in 8 s, HYPE in 2 s (Spitze
des Prozesses rund 4 GB mit allen Fills im Speicher); `bulk` über alle 603 940 Fills braucht zusammen 1,0 s
(Grenze 60 s). Kein Fill ohne Spot, Forward oder Vol. Die Vol am Strike stimmt bei 603 938 Fills exakt mit
`iv_mark_t` von Paper 1 überein, `svi_fwd` ebenso mit `fwd_t`. Die zwei Abweichungen (ETH, 21.07.2024 und
29.07.2024) liegen an zwei SVI-Pushes desselben Verfalls im selben Block: Paper 1 (`markpath.attach_svi`,
`merge_asof` ohne Ordnung nach `log_index`) nimmt dort den früheren Push, `FeedHistory` den späteren, der nach dem
Block tatsächlich im Speicher steht. Median Spot-Alter bei Fills 26 bis 30 s, Forward 46 bis 54 s, Vol 57 bis 62 s,
Zins 53 bis 60 s. Ohne PM2-Zins (Fills vor dem 12.06.2025) sind 56 164 BTC- und 211 533 ETH-Fills; dort gilt Zins 0.

**Abweichungen vom Plan.**
- Geladen bis Block 44 815 000 statt 44 812 000: Block 44 812 000 ist 17.09.2026 11:46:55 UTC und liegt vor dem
  Schnitt 12:00 UTC (Block 44 812 392); der letzte Fill von Paper 1 (11:51:53 UTC) läge sonst ausserhalb.
- Perp: `value` ist `spotDiff` aus dem Event, nicht der Preis; der Preis entsteht wie im Vertrag erst mit dem Spot
  zum Abfragezeitpunkt. Forward-Dateien haben die zusätzliche Spalte `fixed`.
- `p2chain.Rpc` heisst `.eth_call` statt `.call` (lag so vor); `p2feeds` nutzt `.raw`.
- Zusätzlich zum Plan: `FeedExpiryState` mit `fwd_fixed`, `rate_conf`; Spalten `rate_pm`, `perp`, `perp_conf`;
  `FeedHistory(start_ts=, end_ts=, with_svi=)` lädt exakt nur ein Zeitfenster (plus letzten Wert davor je Verfall).
- Fixtures unter `tests/fixtures/p2/feeds_*.json`, erzeugt mit `tests/fixtures/p2/gen_a1_feed_fixtures.py`.
