## C5b API-Momentaufnahme: `public/get_margin` gegen den Nachbau am aktuellen Block

Stand 25.09.2026. **Explorativ:** Die Präregistrierung führt „API-Semantik mit 2 %“ unter den explorativen Grössen. Die v2-API rechnet off-chain mit Ticker-Preisen und einem pauschalen PM2-Diskont von 2 % (`docs/paper2/get_margin_semantik.md`, Abschnitt 3); ihr Verlauf ist nicht rekonstruierbar, gemessen wird deshalb nur heute. Keine Konten: Alle Bücher sind simuliert (API: `simulated_positions`; Chain: zwei synthetische Konten per State-Override). Keine Inferenz, kein Eingang in H1 bis H4. Tests: `tests/test_p2_api.py` (offline, API und Chain als Attrappen, Nachbau auf `results/p2/params`).

### Lauf

- Zeit: 25.09.2026 00:44:17 bis 25.09.2026 00:47:51 UTC; Blöcke 45 137 723 bis 45 137 828.
- Anfragen: 263 an `https://api.lyra.finance` und 123 `eth_call` an `https://rpc.lyra.finance`, zusammen höchstens 2 je Sekunde (gemessen im Log: höchstens 2 Starts in einem Fenster von 1 s), User-Agent `derive-option-surface/p2-C5b (research, public endpoints only)`. Log mit allen Antworten, auch Instrumentlisten und Tickern: `data/p2/logs/C5b.jsonl`.
- Parameter (Standard-Lib, `results/p2/params`, gültiger Eintrag): BTC SM ab 2024-10-08 18:46:47, PM2 ab 2026-09-04 22:51:37; ETH SM ab 2024-10-08 18:46:47, PM2 ab 2026-09-04 22:51:37; HYPE SM ab 2026-08-20 22:09:25, PM2 ab 2026-09-04 22:51:37 UTC.
- Typwahl aus: `data/p1/derived/markouts.parquet` (Maker-Seite, |Δ|- und Laufzeit-Bucket, PM2-Fenster).
- Ergebnis: `results/p2/api_snapshot.csv` (210 Zeilen, eine je Zelle), Metadaten `data/p2/api_snapshot/meta.json`.

### Festlegungen

1. **Zellen:** Basiswert × Maker-Seite (Kauf, Verkauf) × 7 |Δ|-Buckets × 5 Laufzeit-Buckets der Paper-1-Karte, also 70 Zellen je Basiswert.
2. **Verfall:** unter den gelisteten, aktiven Verfällen mit mindestens 30 min Restlaufzeit der mit Restlaufzeit im Bucket, die der Bucket-Mitte am nächsten liegt (1; 4,5; 18,5; 60 Tage; für > 90 Tage die Mitte zwischen 90 Tagen und dem längsten gelisteten Verfall). Gleichstand: der frühere.
3. **Typ:** Call oder Put, je nachdem, welcher Typ unter den Paper-1-Fills derselben Zelle im PM2-Fenster häufiger ist (Gleichstand oder keine Fills: Call). Die Präregistrierung legt keinen Typ fest; so ist das Instrument für die Zelle der Karte repräsentativ.
4. **Strike:** das aktive Instrument dieses Typs und Verfalls mit Ticker, dessen |Δ| (Ticker-Delta, Forward-Delta wie in Paper 1) der Bucket-Mitte am nächsten liegt (5; 17,5; 32,5; 50; 67,5; 82,5; 95 %) und im Bucket liegt. Gleichstand: der kleinere Strike.
5. **Preis:** p = Ticker-Mark aus `get_tickers` des Verfalls, gelesen direkt vor den Messungen seiner Instrumente.
6. **K_api** = p·q − net_IM(q; C = 0) aus `get_margin` mit `market` = Basiswert unter SM und unter PM2, je Instrument und Manager eine Anfrage: `simulated_positions` q = +1, `simulated_position_changes` −2, kein Collateral. `pre` ist net(+1), `post` net(−1), beide zum selben Preisstand.
7. **K_chain** = p·q − net_IM(q; C = 0) aus dem Nachbau (`margin_sm`, `margin_pm2`, Weg von B2) mit den On-Chain-Feeds am aktuellen Block: ein `eth_call` über Multicall3 liefert Block, Blockzeit, `getSpot`, `getForwardPricePortions`, `getVol` am Strike, den PM2-Zins und den Stable-Feed. PM2 mit dem Zins-Feed, SM ohne Diskont. Derselbe Preis p wie bei K_api; Laufzeit ab der Blockzeit.
8. **Gegenprobe K_oracle:** Dieselbe Multicall ruft `getMargin(konto, true)` von StandardManager und PMRM_2 für zwei synthetische Konten mit +1 und −1 Kontrakt auf (State-Override von `SubAccounts` wie in B1).
9. **Nachbau in API-Semantik K_rep_api:** Nachbau mit Index als Spot, Ticker-Forward, Mark-IV, PM2-Zins 2 % und Konfidenzen 1, Laufzeit ab der Zeit der API-Anfrage.
10. **Abweichung:** rel = K_api / K_chain − 1 (Vorzeichen: positiv heisst, die API bindet mehr Kapital). Der Preis p kürzt sich in K_api − K_chain heraus; er wirkt nur über den Nenner.

### Abdeckung

- 195 von 210 Zellen gemessen, 123 verschiedene Instrumente.
- kein gelisteter Verfall im Laufzeit-Bucket: 14 Zellen.
- kein Strike des Typs im |Δ|-Bucket: 1 Zelle.
- HYPE ohne Verfall in: 2-7d.

### K_api gegen K_chain

| Basiswert | Seite | Manager | Zellen | Median rel | Minimum | Maximum | Median \|rel\| |
|---|---|---|---:|---:|---:|---:|---:|
| BTC | Kauf | SM | 35 | 0,000 % | 0,000 % | 0,000 % | 0,000 % |
| BTC | Kauf | PM2 | 35 | 0,000 % | −2,103 % | +0,133 % | 0,004 % |
| BTC | Verkauf | SM | 34 | +0,015 % | −0,301 % | +0,197 % | 0,055 % |
| BTC | Verkauf | PM2 | 34 | +0,030 % | −0,284 % | +0,487 % | 0,121 % |
| ETH | Kauf | SM | 35 | 0,000 % | 0,000 % | 0,000 % | 0,000 % |
| ETH | Kauf | PM2 | 35 | 0,000 % | −2,413 % | +0,081 % | 0,004 % |
| ETH | Verkauf | SM | 35 | −0,050 % | −0,294 % | +0,288 % | 0,115 % |
| ETH | Verkauf | PM2 | 35 | −0,089 % | −0,584 % | +0,311 % | 0,172 % |
| HYPE | Kauf | SM | 28 | 0,000 % | 0,000 % | 0,000 % | 0,000 % |
| HYPE | Kauf | PM2 | 28 | 0,000 % | −0,342 % | +0,058 % | 0,008 % |
| HYPE | Verkauf | SM | 28 | −0,045 % | −0,158 % | +0,125 % | 0,061 % |
| HYPE | Verkauf | PM2 | 28 | −0,014 % | −0,216 % | +0,143 % | 0,082 % |

SM, Kauf: In 98 von 98 Zellen ist K_api = K_chain = p exakt; SM gibt einer Long-Option keine Gutschrift, das Kapital ist die Prämie.

Median von rel je Laufzeit-Bucket über alle Basiswerte und |Δ|-Buckets:

| Laufzeit | Seite | Zellen | SM | PM2 |
|---|---|---:|---:|---:|
| <=2d | Kauf | 21 | 0,000 % | 0,000 % |
| <=2d | Verkauf | 20 | −0,068 % | −0,126 % |
| 2-7d | Kauf | 14 | 0,000 % | 0,000 % |
| 2-7d | Verkauf | 14 | −0,052 % | −0,106 % |
| 7-30d | Kauf | 21 | 0,000 % | +0,002 % |
| 7-30d | Verkauf | 21 | +0,017 % | +0,026 % |
| 30-90d | Kauf | 21 | 0,000 % | −0,023 % |
| 30-90d | Verkauf | 21 | −0,065 % | −0,083 % |
| >90d | Kauf | 21 | 0,000 % | −0,342 % |
| >90d | Verkauf | 21 | +0,034 % | +0,117 % |

Grösste Abweichungen (8 Zellen mit dem grössten |rel| über beide Manager):

| Zelle | Instrument | Manager | p | K_api | K_chain | rel | K_api/K_rep_api − 1 |
|---|---|---|---:|---:|---:|---:|---:|
| ETH, Kauf, 90-100, >90d | `ETH-20270326-1400-C` | PM2 | 1 352,00 | 389,30 | 398,93 | −2,413 % | −0,228 % |
| BTC, Kauf, 90-100, >90d | `BTC-20270326-50000-C` | PM2 | 36 421,00 | 10 819,21 | 11 051,65 | −2,103 % | −0,005 % |
| ETH, Kauf, 75-90, >90d | `ETH-20270326-2000-C` | PM2 | 844,30 | 345,24 | 350,40 | −1,473 % | −0,314 % |
| BTC, Kauf, 75-90, >90d | `BTC-20270326-70000-C` | PM2 | 19 142,00 | 8 800,42 | 8 896,01 | −1,074 % | −0,001 % |
| ETH, Kauf, 60-75, >90d | `ETH-20270326-2500-C` | PM2 | 517,80 | 280,01 | 282,62 | −0,923 % | −0,263 % |
| BTC, Kauf, 60-75, >90d | `BTC-20270326-80000-C` | PM2 | 12 351,00 | 7 149,07 | 7 201,81 | −0,732 % | −0,013 % |
| ETH, Kauf, 40-60, >90d | `ETH-20270326-3000-C` | PM2 | 309,40 | 204,08 | 205,31 | −0,598 % | −0,151 % |
| ETH, Verkauf, 00-10, 2-7d | `ETH-20260928-2900-C` | PM2 | 2,90 | 248,72 | 250,18 | −0,584 % | −0,382 % |

### Gegenproben

| Manager | Zellen | Median \|K_chain/K_oracle − 1\| | Max | Median K_api/K_rep_api − 1 | Median \|…\| | Max \|…\| |
|---|---:|---:|---:|---:|---:|---:|
| SM | 195 | 0 | 1,8·10⁻¹⁵ | 0,000 % | 0,000 % | 0,356 % |
| PM2 | 195 | 4,4·10⁻¹⁶ | 4,8·10⁻¹⁴ | 0,000 % | 0,036 % | 0,425 % |

Feeds je Basiswert (Median über die gemessenen Instrumente): Ticker gegen Chain am selben Instrument.

| Basiswert | Instrumente | Index/Spot − 1 (bp) | Forward Ticker/Chain − 1 (bp) | Mark-IV − Chain-Vol (Vol-Punkte) | PM2-Zins-Feed |
|---|---:|---:|---:|---:|---:|
| BTC | 50 | 0,0 | +1,1 | +0,01 | 3,64 % |
| ETH | 39 | −0,9 | −1,1 | 0,00 | 3,64 % |
| HYPE | 34 | −0,2 | −4,1 | 0,00 | 3,64 % |

### Einschränkungen

- Eine Momentaufnahme eines Zeitpunkts mit einem Instrument je Zelle; keine Aussage über die Stichprobe von Paper 2 und keine Inferenz.
- K_api − K_chain mischt drei Ursachen: den pauschalen 2-%-Diskont der API gegen den Zins-Feed, Ticker-Preise gegen die nachlaufenden On-Chain-Feeds und etwaige Unterschiede der Off-chain-Engine. K_rep_api trennt den ersten und zweiten Teil vom dritten.
- API und Chain werden je Instrument in drei Anfragen kurz nacheinander gelesen (Abstand ≥ 0,5 s); Preisbewegungen dazwischen gehen in rel ein.
- Die Parameter stammen aus `results/p2/params` (Stand des letzten Ladelaufs); K_oracle zeigt, ob sie am aktuellen Block noch gelten.

### Schnittstellen

- `derive_surface/p2api.py`: `run(ccys, ...)`, `snapshot_ccy`, `measure_instrument`, `chain_calls`, `decode_chain`, `replica_capital`, `replica_api_semantics`, `choose_expiry`, `choose_instrument`, `cell_types`, `render_doc`; `ApiClient` und `SharedRpc` teilen sich einen `Throttle` (2 je Sekunde).
- CLI: `python3 -m derive_surface p2 api run [--ccy BTC ETH HYPE]` und `p2 api report` (Dokument neu aus CSV und Metadaten). Kein schwerer Lauf (liest nur 6 Spalten aus `markouts.parquet`).
- `p2cli` neu: `p2 infer` (H1 bis H3 wie bisher), `p2 infer-h4` (`inference_p2_h4.main`), `p2 zahlenblatt` (`scripts/p2_zahlenblatt.py`, als Modul importiert), `p2 api` (`p2api.main`).
