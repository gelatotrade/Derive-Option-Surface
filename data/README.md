# Data

All files are parquet (zstd). Timestamps: `timestamp`, `ts`, `cycle_ts`, `book_ts`, `flush_ts` in **milliseconds** UTC,
`expiry` in **seconds** UTC (expiry at 08:00 UTC).

| File | Content | Columns |
|---|---|---|
| `trades/<CCY>_option_trades.parquet` | every fill since the start of trading, deduplicated to the taker row | `trade_id, timestamp, instrument_name, expiry, strike, option_type, direction (Aggressor), trade_price, trade_amount, mark_price, index_price, liquidity_role, tx_status` |
| `spot/<CCY>_{1m,5m,15m,1h}.parquet` | Derive spot/index feed | `timestamp (s), price` |
| `live/<CCY>_tickers.parquet` | top of book of every live option, one cycle every 20 s | `cycle_ts, currency, ts, instrument_name, expiry, strike, option_type, bid, ask, bid_amount, ask_amount, mark, index, forward, iv, bid_iv, ask_iv, delta, gamma, vega, theta, rho, discount_factor, open_interest` |
| `live/depth.parquet` | price levels (up to 10 per side) of the options near the money, every 10 s | `flush_ts, book_ts, instrument_name, side, level, price, amount` |
| `live/depth_snapshot.parquet` | price levels (up to 20 per side) of **all** live options, one point in time | `instrument_name, book_ts, side, level, price, amount` |

`raw/` (git-ignored) holds the raw pages of the trade history and the recorder chunks; `python -m derive_surface download`
and `merge` rebuild the files above from them.
