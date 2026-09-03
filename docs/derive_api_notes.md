# Derive Public API — was es wirklich gibt (empirisch geprüft am 2026-09-03)

Host: `https://api.lyra.finance` (JSON-RPC über HTTP-POST, `/public/<method>`),
WebSocket: `wss://api.lyra.finance/ws`. Alle Aufrufe ohne Wallet/Session-Key.
Die Doku unter `docs.derive.xyz/reference` ist eine readme.io-Seite; die
Parameter unten sind gegen den Live-Server verifiziert.

## Orderbuch

| Was | Endpoint | Befund |
|---|---|---|
| Top-of-Book aller Optionen eines Verfalls | `get_tickers` `{currency, instrument_type:"option", expiry_date:"YYYYMMDD"}` | ~30 KB, ~0,5 s. Slim-Ticker: `b/a` (Bid/Ask), `B/A` (Mengen), `M` Mark, `I` Index, `option_pricing.{i, bi, ai, d, g, v, t, r, f, df}` = Mark-IV, Bid-IV, Ask-IV, Delta, Gamma, Vega, Theta, Rho, Forward, Diskontfaktor |
| Ein Instrument, volle Felder | `get_ticker` `{instrument_name}` | inkl. `five_percent_bid_depth` / `five_percent_ask_depth` |
| Preis-Level (Tiefe) | WS-Kanal `orderbook.{instrument}.{group}.{depth}` (z. B. `orderbook.BTC-20260911-80000-C.1.10`) | Push alle ~100 ms bei Änderung, `bids`/`asks` als `[price, amount]`. **Es gibt keinen REST-Endpoint für Tiefe** (`get_order_book`, `get_orderbook` → 404) |
| Ticker-Stream | WS-Kanal `ticker_slim.{instrument}.{interval_ms}` | `ticker.*` ist deprecated |

**Historische Orderbuch-Snapshots gibt es öffentlich nicht.** Kein Endpoint
liefert vergangene Bid/Ask-Stände oder vergangene IVs. Was es stattdessen gibt:

## Historie

| Was | Endpoint | Tiefe |
|---|---|---|
| Alle Options-Trades (jeder Fill) | `get_trade_history` `{currency, instrument_type:"option", page, page_size≤1000, from_timestamp, to_timestamp}` | vollständig seit Start (BTC ab 2024-01-11): BTC 301 905, ETH 795 312, HYPE 83 530 Zeilen (Maker- und Taker-Zeile je Fill). Jeder Fill trägt `trade_price`, `mark_price`, `index_price`, `timestamp` |
| Spot/Index-Feed | `get_spot_feed_history` `{currency, start_timestamp, end_timestamp, period}` | max. 500 Punkte pro Aufruf; Retention **60 s: 24 h, 300 s: 7 Tage, 900 s: 30 Tage, 3600 s: 90 Tage** |
| Spot-Kerzen | `get_spot_feed_history_candles` | OHLC, gleiche Retention |
| Perp-Kerzen (Chart) | `get_tradingview_chart_data` `{instrument_name:"BTC-PERP", period:"<enum>", start_timestamp, end_timestamp}` | Enum ≠ Sekunden; nicht benötigt |
| Settlement-Preise | `get_option_settlement_history`, `get_option_settlement_prices` | Verfallspreise |

## Konventionen

* Optionen verfallen 08:00 UTC; `expiry` ist Unix-Sekunden, `timestamp` in Tickern/Trades Millisekunden.
* Preise in USDC je Kontrakt (1 Kontrakt = 1 Einheit Underlying). Delta ist w. r. t. **Forward**.
* Instrumentname: `BTC-20260904-110000-C`; Bruch-Strikes mit Unterstrich: `HYPE-20260904-77_5-C` (= 77,5; Vorsicht,
  `float("77_5")` liest in Python 775).
* WebSocket `orderbook.*`: die Verbindung wird serverseitig gelegentlich ohne Close-Frame beendet (nach ~90 min beobachtet);
  der Recorder verbindet neu und schreibt den Puffer in jedem Fall weg.
* `depth-snapshot` über alle 2 166 lebenden Optionen: nur 1 184 Bücher hatten ruhende Orders; die übrigen sind leer
  (die Market-Maker quotieren dort nur per RFQ oder gar nicht).
* Rate-Limits: mit 4–6 parallelen Requests keine 429 beobachtet; der Client wartet exponentiell bei 429/5xx.
