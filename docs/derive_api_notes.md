# Derive public API: what actually exists (empirically verified on 2026-09-03)

Host: `https://api.lyra.finance` (JSON-RPC over HTTP POST, `/public/<method>`),
WebSocket: `wss://api.lyra.finance/ws`. All calls work without a wallet or session key.
The documentation at `docs.derive.xyz/reference` is a readme.io site; the
parameters below have been verified against the live server.

## Orderbook

| What | Endpoint | Finding |
|---|---|---|
| Top of book of all options of one expiry | `get_tickers` `{currency, instrument_type:"option", expiry_date:"YYYYMMDD"}` | ~30 KB, ~0.5 s. Slim ticker: `b/a` (bid/ask), `B/A` (amounts), `M` mark, `I` index, `option_pricing.{i, bi, ai, d, g, v, t, r, f, df}` = mark IV, bid IV, ask IV, delta, gamma, vega, theta, rho, forward, discount factor |
| One instrument, all fields | `get_ticker` `{instrument_name}` | incl. `five_percent_bid_depth` / `five_percent_ask_depth` |
| Price levels (depth) | WS channel `orderbook.{instrument}.{group}.{depth}` (e.g. `orderbook.BTC-20260911-80000-C.1.10`) | Push every ~100 ms on change, `bids`/`asks` as `[price, amount]`. **There is no REST endpoint for depth** (`get_order_book`, `get_orderbook` → 404) |
| Ticker stream | WS channel `ticker_slim.{instrument}.{interval_ms}` | `ticker.*` is deprecated |

**Historical orderbook snapshots are not publicly available.** No endpoint
returns past bid/ask levels or past IVs. What exists instead:

## History

| What | Endpoint | Depth |
|---|---|---|
| All option trades (every fill) | `get_trade_history` `{currency, instrument_type:"option", page, page_size≤1000, from_timestamp, to_timestamp}` | complete since launch (BTC from 2024-01-11): BTC 301,905, ETH 795,312, HYPE 83,530 rows (one maker and one taker row per fill). Every fill carries `trade_price`, `mark_price`, `index_price`, `timestamp` |
| Spot/index feed | `get_spot_feed_history` `{currency, start_timestamp, end_timestamp, period}` | at most 500 points per call; retention **60 s: 24 h, 300 s: 7 days, 900 s: 30 days, 3600 s: 90 days** |
| Spot candles | `get_spot_feed_history_candles` | OHLC, same retention |
| Perp candles (chart) | `get_tradingview_chart_data` `{instrument_name:"BTC-PERP", period:"<enum>", start_timestamp, end_timestamp}` | enum ≠ seconds; not needed |
| Settlement prices | `get_option_settlement_history`, `get_option_settlement_prices` | expiry prices |

## Conventions

* Options expire at 08:00 UTC; `expiry` is in Unix seconds, `timestamp` in tickers/trades in milliseconds.
* Prices in USDC per contract (1 contract = 1 unit of the underlying). Delta is w.r.t. the **forward**.
* Instrument name: `BTC-20260904-110000-C`; fractional strikes use an underscore: `HYPE-20260904-77_5-C` (= 77.5; careful,
  in Python `float("77_5")` reads 775).
* WebSocket `orderbook.*`: the server occasionally drops the connection without a close frame (observed after ~90 min);
  the recorder reconnects and writes out the buffer in every case.
* `depth-snapshot` across all 2,166 live options: only 1,184 books had resting orders; the rest are empty
  (the market makers quote there only via RFQ or not at all).
* Rate limits: no 429 observed with 4 to 6 parallel requests; the client backs off exponentially on 429/5xx.
