# Daten

Alle Dateien sind parquet (zstd). Zeitstempel: `timestamp`, `ts`, `cycle_ts`, `book_ts`, `flush_ts` in **Millisekunden** UTC,
`expiry` in **Sekunden** UTC (Verfall 08:00 UTC).

| Datei | Inhalt | Spalten |
|---|---|---|
| `trades/<CCY>_option_trades.parquet` | jeder Fill seit Handelsstart, dedupliziert auf die Taker-Zeile | `trade_id, timestamp, instrument_name, expiry, strike, option_type, direction (Aggressor), trade_price, trade_amount, mark_price, index_price, liquidity_role, tx_status` |
| `spot/<CCY>_{1m,5m,15m,1h}.parquet` | Derive-Spot-/Index-Feed | `timestamp (s), price` |
| `live/<CCY>_tickers.parquet` | Top-of-Book jeder lebenden Option, ein Zyklus alle 20 s | `cycle_ts, currency, ts, instrument_name, expiry, strike, option_type, bid, ask, bid_amount, ask_amount, mark, index, forward, iv, bid_iv, ask_iv, delta, gamma, vega, theta, rho, discount_factor, open_interest` |
| `live/depth.parquet` | Preis-Level (bis 10 je Seite) der Optionen nahe am Geld, alle 10 s | `flush_ts, book_ts, instrument_name, side, level, price, amount` |
| `live/depth_snapshot.parquet` | Preis-Level (bis 20 je Seite) **aller** lebenden Optionen, ein Zeitpunkt | `instrument_name, book_ts, side, level, price, amount` |

`raw/` (git-ignored) enthält die Rohseiten der Trade-Historie und die Recorder-Teilstücke; `python -m derive_surface download`
und `merge` bauen daraus die obigen Dateien neu.
