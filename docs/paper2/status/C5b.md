## C5b API snapshot: `public/get_margin` against the replica at the current block

Status as of 25 September 2026. **Exploratory:** the pre-registration lists "API semantics with 2 %" among the exploratory quantities. The v2 API computes off-chain with ticker prices and a flat PM2 discount of 2 % (`docs/paper2/get_margin_semantics.md`, section 3); its history cannot be reconstructed, so only today is measured. No accounts: all books are simulated (API: `simulated_positions`; chain: two synthetic accounts via state override). No inference, no input to H1 to H4. Tests: `tests/test_p2_api.py` (offline, API and chain as mocks, replica on `results/p2/params`).

### Run

- Time: 25 September 2026 00:44:17 to 25 September 2026 00:47:51 UTC; blocks 45,137,723 to 45,137,828.
- Requests: 263 to `https://api.lyra.finance` and 123 `eth_call` to `https://rpc.lyra.finance`, together at most 2 per second (measured in the log: at most 2 starts in a window of 1 s), user agent `derive-option-surface/p2-C5b (research, public endpoints only)`. Log with all responses, instrument lists and tickers included: `data/p2/logs/C5b.jsonl`.
- Parameters (standard lib, `results/p2/params`, valid entry): BTC SM from 2024-10-08 18:46:47, PM2 from 2026-09-04 22:51:37; ETH SM from 2024-10-08 18:46:47, PM2 from 2026-09-04 22:51:37; HYPE SM from 2026-08-20 22:09:25, PM2 from 2026-09-04 22:51:37 UTC.
- Type choice from: `data/p1/derived/markouts.parquet` (maker side, |Δ| and tenor bucket, PM2 window).
- Result: `results/p2/api_snapshot.csv` (210 rows, one per cell), metadata `data/p2/api_snapshot/meta.json`.

### Decisions

1. **Cells:** underlying × maker side (buy, sell) × 7 |Δ| buckets × 5 tenor buckets of the Paper 1 map, that is 70 cells per underlying.
2. **Expiry:** among the listed, active expiries with at least 30 min to expiry, the one whose time to expiry lies in the bucket and is closest to the bucket midpoint (1, 4.5, 18.5, 60 days; for > 90 days the midpoint between 90 days and the longest listed expiry). Tie: the earlier one.
3. **Type:** call or put, whichever type is more frequent among the Paper 1 fills of the same cell in the PM2 window (tie or no fills: call). The pre-registration fixes no type; this way the instrument is representative of the cell of the map.
4. **Strike:** the active instrument of this type and expiry with a ticker whose |Δ| (ticker delta, forward delta as in Paper 1) is closest to the bucket midpoint (5, 17.5, 32.5, 50, 67.5, 82.5, 95 %) and lies in the bucket. Tie: the smaller strike.
5. **Price:** p = ticker mark from `get_tickers` of the expiry, read directly before the measurements of its instruments.
6. **K_api** = p·q − net_IM(q; C = 0) from `get_margin` with `market` = underlying under SM and under PM2, one request per instrument and manager: `simulated_positions` q = +1, `simulated_position_changes` −2, no collateral. `pre` is net(+1), `post` net(−1), both at the same prices.
7. **K_chain** = p·q − net_IM(q; C = 0) from the replica (`margin_sm`, `margin_pm2`, path of B2) with the on-chain feeds at the current block: one `eth_call` via Multicall3 returns block, block time, `getSpot`, `getForwardPricePortions`, `getVol` at the strike, the PM2 rate and the stable feed. PM2 with the rate feed, SM without discounting. The same price p as for K_api; time to expiry from the block time.
8. **Cross-check K_oracle:** the same multicall calls `getMargin(account, true)` of StandardManager and PMRM_2 for two synthetic accounts with +1 and −1 contract (state override of `SubAccounts` as in B1).
9. **Replica in API semantics K_rep_api:** replica with the index as spot, ticker forward, mark IV, PM2 rate 2 % and confidences 1, time to expiry from the time of the API request.
10. **Deviation:** rel = K_api / K_chain − 1 (sign: positive means the API binds more capital). The price p cancels out of K_api − K_chain; it acts only through the denominator.

### Coverage

- 195 of 210 cells measured, 123 distinct instruments.
- no listed expiry in the tenor bucket: 14 cells.
- no strike of the type in the |Δ| bucket: 1 cell.
- HYPE without an expiry in: 2-7d.

### K_api against K_chain

| Underlying | Side | Manager | Cells | Median rel | Minimum | Maximum | Median \|rel\| |
|---|---|---|---:|---:|---:|---:|---:|
| BTC | buy | SM | 35 | 0.000 % | 0.000 % | 0.000 % | 0.000 % |
| BTC | buy | PM2 | 35 | 0.000 % | −2.103 % | +0.133 % | 0.004 % |
| BTC | sell | SM | 34 | +0.015 % | −0.301 % | +0.197 % | 0.055 % |
| BTC | sell | PM2 | 34 | +0.030 % | −0.284 % | +0.487 % | 0.121 % |
| ETH | buy | SM | 35 | 0.000 % | 0.000 % | 0.000 % | 0.000 % |
| ETH | buy | PM2 | 35 | 0.000 % | −2.413 % | +0.081 % | 0.004 % |
| ETH | sell | SM | 35 | −0.050 % | −0.294 % | +0.288 % | 0.115 % |
| ETH | sell | PM2 | 35 | −0.089 % | −0.584 % | +0.311 % | 0.172 % |
| HYPE | buy | SM | 28 | 0.000 % | 0.000 % | 0.000 % | 0.000 % |
| HYPE | buy | PM2 | 28 | 0.000 % | −0.342 % | +0.058 % | 0.008 % |
| HYPE | sell | SM | 28 | −0.045 % | −0.158 % | +0.125 % | 0.061 % |
| HYPE | sell | PM2 | 28 | −0.014 % | −0.216 % | +0.143 % | 0.082 % |

SM, buy: in 98 of 98 cells K_api = K_chain = p exactly; SM gives a long option no credit, and the capital is the premium.

Median of rel per tenor bucket over all underlyings and |Δ| buckets:

| Tenor | Side | Cells | SM | PM2 |
|---|---|---:|---:|---:|
| <=2d | buy | 21 | 0.000 % | 0.000 % |
| <=2d | sell | 20 | −0.068 % | −0.126 % |
| 2-7d | buy | 14 | 0.000 % | 0.000 % |
| 2-7d | sell | 14 | −0.052 % | −0.106 % |
| 7-30d | buy | 21 | 0.000 % | +0.002 % |
| 7-30d | sell | 21 | +0.017 % | +0.026 % |
| 30-90d | buy | 21 | 0.000 % | −0.023 % |
| 30-90d | sell | 21 | −0.065 % | −0.083 % |
| >90d | buy | 21 | 0.000 % | −0.342 % |
| >90d | sell | 21 | +0.034 % | +0.117 % |

Largest deviations (8 cells with the largest |rel| over both managers):

| Cell | Instrument | Manager | p | K_api | K_chain | rel | K_api/K_rep_api − 1 |
|---|---|---|---:|---:|---:|---:|---:|
| ETH, buy, 90-100, >90d | `ETH-20270326-1400-C` | PM2 | 1,352.00 | 389.30 | 398.93 | −2.413 % | −0.228 % |
| BTC, buy, 90-100, >90d | `BTC-20270326-50000-C` | PM2 | 36,421.00 | 10,819.21 | 11,051.65 | −2.103 % | −0.005 % |
| ETH, buy, 75-90, >90d | `ETH-20270326-2000-C` | PM2 | 844.30 | 345.24 | 350.40 | −1.473 % | −0.314 % |
| BTC, buy, 75-90, >90d | `BTC-20270326-70000-C` | PM2 | 19,142.00 | 8,800.42 | 8,896.01 | −1.074 % | −0.001 % |
| ETH, buy, 60-75, >90d | `ETH-20270326-2500-C` | PM2 | 517.80 | 280.01 | 282.62 | −0.923 % | −0.263 % |
| BTC, buy, 60-75, >90d | `BTC-20270326-80000-C` | PM2 | 12,351.00 | 7,149.07 | 7,201.81 | −0.732 % | −0.013 % |
| ETH, buy, 40-60, >90d | `ETH-20270326-3000-C` | PM2 | 309.40 | 204.08 | 205.31 | −0.598 % | −0.151 % |
| ETH, sell, 00-10, 2-7d | `ETH-20260928-2900-C` | PM2 | 2.90 | 248.72 | 250.18 | −0.584 % | −0.382 % |

### Cross-checks

| Manager | Cells | Median \|K_chain/K_oracle − 1\| | Max | Median K_api/K_rep_api − 1 | Median \|…\| | Max \|…\| |
|---|---:|---:|---:|---:|---:|---:|
| SM | 195 | 0 | 1.8·10⁻¹⁵ | 0.000 % | 0.000 % | 0.356 % |
| PM2 | 195 | 4.4·10⁻¹⁶ | 4.8·10⁻¹⁴ | 0.000 % | 0.036 % | 0.425 % |

Feeds per underlying (median over the measured instruments): ticker against chain at the same instrument.

| Underlying | Instruments | Index/spot − 1 (bp) | Forward ticker/chain − 1 (bp) | Mark IV − chain vol (vol points) | PM2 rate feed |
|---|---:|---:|---:|---:|---:|
| BTC | 50 | 0.0 | +1.1 | +0.01 | 3.64 % |
| ETH | 39 | −0.9 | −1.1 | 0.00 | 3.64 % |
| HYPE | 34 | −0.2 | −4.1 | 0.00 | 3.64 % |

### Limitations

- A snapshot of one point in time with one instrument per cell; no statement about the sample of Paper 2 and no inference.
- K_api − K_chain mixes three causes: the API's flat 2 % discount against the rate feed, ticker prices against the lagging on-chain feeds, and any differences of the off-chain engine. K_rep_api separates the first and second part from the third.
- API and chain are read per instrument in three requests shortly after one another (gap ≥ 0.5 s); price moves in between enter rel.
- The parameters come from `results/p2/params` (state of the last load run); K_oracle shows whether they still apply at the current block.

### Interfaces

- `derive_surface/p2api.py`: `run(ccys, ...)`, `snapshot_ccy`, `measure_instrument`, `chain_calls`, `decode_chain`, `replica_capital`, `replica_api_semantics`, `choose_expiry`, `choose_instrument`, `cell_types`, `render_doc`; `ApiClient` and `SharedRpc` share a `Throttle` (2 per second).
- CLI: `python3 -m derive_surface p2 api run [--ccy BTC ETH HYPE]` and `p2 api report` (document rebuilt from the CSV and the metadata). Not a heavy run (reads only 6 columns from `markouts.parquet`).
- New in `p2cli`: `p2 infer` (H1 to H3 as before), `p2 infer-h4` (`inference_p2_h4.main`), `p2 numbers` (`scripts/p2_numbers.py`, imported as a module), `p2 api` (`p2api.main`).
