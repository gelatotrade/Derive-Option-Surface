"""Derive Option Surface — orderbook-derived implied-volatility surfaces for Derive (derive.xyz).

The package is organised as a pipeline:

    api        -> thin JSON-RPC / WebSocket client for the public Derive API
    history    -> full historical download (option trades, spot feed) into parquet
    recorder   -> live orderbook recorder (slim tickers per expiry + WebSocket depth)
    pricing    -> Black-76 pricing, implied-vol inversion, first/second/third-order greeks
    surface    -> snapshot -> gridded (moneyness, tenor, iv) surface
    animate    -> underlying chart + option mids + 3D surface -> GIF / MP4
"""

__all__ = ["api", "history", "recorder", "pricing", "surface", "animate"]
__version__ = "0.1.0"
