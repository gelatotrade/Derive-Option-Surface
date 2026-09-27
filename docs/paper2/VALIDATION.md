# Validation of the replica against the chain (task B1)

Status 25 September 2026, pilot cut 17 September 2026 12:00 UTC. Gate of the pre-registration, section "Validation
before measurement" (threshold: median of the absolute relative deviation of K below 0.1 % and 95th percentile below
1 %, per underlying and manager). Code `derive_surface/p2validate.py`, tests `tests/test_p2_validate.py` (21 tests,
offline; two of them read the private fixture `data/p2/fixtures_private/b1_chain_cases.json` with real maker books
and are skipped without it, audit A01).
Results `results/p2/validation.csv` (1,754 rows) and `results/p2/validation_summary.json`, raw data under
`data/p2/validation/`. No inference: only the measurement is checked here.

## Result

**The threshold is met in all cells, with a margin of at least five orders of magnitude.** Over all 799 valid single
contracts, the median of the absolute relative deviation of K under IM is 8.7·10⁻¹⁰, the 95th percentile 1.4·10⁻⁸
and the maximum 8.9·10⁻⁸. Over the 77 valid book rows under IM, the values are 2.2·10⁻⁹, 1.3·10⁻⁸ and 3.4·10⁻⁸.
The largest absolute deviation is 0.00033 USD for single contracts (median K 301 USD) and 0.050 USD for books (K up
to 19.5 million USD). Source: `results/p2/validation.csv`, `results/p2/validation_summary.json`. No addendum to the
pre-registration is needed.

IM (primary), |rel| = |K_replica − K_chain| / |K_chain|, percentile with linear interpolation:

| Type | Underlying | Manager | n | missing | Median \|rel\| | p95 \|rel\| | Max \|rel\| | Threshold |
|---|---|---|---:|---:|---:|---:|---:|---|
| Single contract | BTC | SM | 100 | 0 | 1.4·10⁻¹⁰ | 6.9·10⁻⁹ | 2.4·10⁻⁸ | met |
| Single contract | BTC | Legacy PM | 100 | 0 | 2.4·10⁻⁹ | 1.5·10⁻⁸ | 3.1·10⁻⁸ | met |
| Single contract | BTC | PM2 | 100 | 0 | 1.8·10⁻¹⁰ | 1.4·10⁻⁸ | 5.0·10⁻⁸ | met |
| Single contract | ETH | SM | 100 | 0 | 0 | 9.5·10⁻⁹ | 1.4·10⁻⁸ | met |
| Single contract | ETH | Legacy PM | 100 | 0 | 3.2·10⁻⁹ | 2.0·10⁻⁸ | 6.5·10⁻⁸ | met |
| Single contract | ETH | PM2 | 100 | 0 | 7.4·10⁻¹⁰ | 2.3·10⁻⁸ | 8.9·10⁻⁸ | met |
| Single contract | HYPE | SM | 100 | 0 | 9.2·10⁻¹² | 5.6·10⁻⁹ | 1.2·10⁻⁸ | met |
| Single contract | HYPE | PM2 | 99 | 1 | 1.7·10⁻⁹ | 1.5·10⁻⁸ | 3.5·10⁻⁸ | met |
| Book | BTC | SM | 7 | 0 | 7.1·10⁻¹⁰ | 9.3·10⁻⁹ | 1.2·10⁻⁸ | met |
| Book | BTC | Legacy PM | 7 | 0 | 1.3·10⁻⁹ | 8.0·10⁻⁹ | 8.1·10⁻⁹ | met |
| Book | BTC | PM2 | 7 | 0 | 2.2·10⁻¹⁰ | 9.1·10⁻⁹ | 1.1·10⁻⁸ | met |
| Book | ETH | SM | 18 | 0 | 7.5·10⁻¹⁰ | 4.0·10⁻⁹ | 6.8·10⁻⁹ | met |
| Book | ETH | Legacy PM | 18 | 0 | 3.9·10⁻⁹ | 2.4·10⁻⁸ | 3.4·10⁻⁸ | met |
| Book | ETH | PM2 | 18 | 0 | 3.8·10⁻⁹ | 1.3·10⁻⁸ | 2.1·10⁻⁸ | met |
| Book | HYPE | SM | 1 | 0 | 2.6·10⁻⁹ | 2.6·10⁻⁹ | 2.6·10⁻⁹ | met |
| Book | HYPE | PM2 | 1 | 0 | 4.3·10⁻⁹ | 4.3·10⁻⁹ | 4.3·10⁻⁹ | met |

Pooled over the underlyings (books, IM): PM2 26 books, median 3.7·10⁻⁹, p95 1.1·10⁻⁸; SM 26 books, 7.5·10⁻¹⁰ and
6.0·10⁻⁹; legacy PM 25 books, 3.3·10⁻⁹ and 2.1·10⁻⁸.

MM (sensitivity), same cases:

| Type | Underlying | Manager | n | Median \|rel\| | p95 \|rel\| | Max \|rel\| | Threshold |
|---|---|---|---:|---:|---:|---:|---|
| Single contract | BTC | SM | 100 | 2.1·10⁻¹⁰ | 1.0·10⁻⁸ | 3.5·10⁻⁸ | met |
| Single contract | BTC | Legacy PM | 100 | 2.7·10⁻¹⁰ | 1.2·10⁻⁸ | 2.7·10⁻⁸ | met |
| Single contract | BTC | PM2 | 100 | 2.6·10⁻⁹ | 3.4·10⁻⁸ | 1.9·10⁻⁷ | met |
| Single contract | ETH | SM | 100 | 0 | 1.4·10⁻⁸ | 2.9·10⁻⁸ | met |
| Single contract | ETH | Legacy PM | 100 | 2.1·10⁻⁹ | 1.8·10⁻⁸ | 6.6·10⁻⁸ | met |
| Single contract | ETH | PM2 | 100 | 3.2·10⁻⁹ | 3.8·10⁻⁸ | 1.0·10⁻⁷ | met |
| Single contract | HYPE | SM | 100 | 1.4·10⁻¹¹ | 7.9·10⁻⁹ | 1.7·10⁻⁸ | met |
| Single contract | HYPE | PM2 | 99 | 1.8·10⁻⁹ | 2.3·10⁻⁸ | 7.5·10⁻⁸ | met |
| Book | BTC | SM | 7 | 1.1·10⁻⁹ | 1.3·10⁻⁸ | 1.7·10⁻⁸ | met |
| Book | BTC | Legacy PM | 7 | 1.3·10⁻⁹ | 7.9·10⁻⁹ | 9.5·10⁻⁹ | met |
| Book | BTC | PM2 | 7 | 2.4·10⁻¹⁰ | 1.3·10⁻⁸ | 1.4·10⁻⁸ | met |
| Book | ETH | SM | 18 | 1.0·10⁻⁹ | 5.9·10⁻⁹ | 1.0·10⁻⁸ | met |
| Book | ETH | Legacy PM | 18 | 2.2·10⁻⁹ | 1.3·10⁻⁸ | 3.7·10⁻⁸ | met |
| Book | ETH | PM2 | 18 | 9.0·10⁻⁹ | 3.1·10⁻⁸ | 4.2·10⁻⁸ | met |
| Book | HYPE | SM | 1 | 3.1·10⁻⁹ | 3.1·10⁻⁹ | 3.1·10⁻⁹ | met |
| Book | HYPE | PM2 | 1 | 6.1·10⁻⁹ | 6.1·10⁻⁹ | 6.1·10⁻⁹ | met |

## What is compared

- **Quantity:** K = Σ p·q − net(q; cash = 0) as in the pre-registration. Both sides use the same book and the same
  prices p, so |K_replica − K_chain| = |net_replica − net_chain|. The deviation is normalised by |K_chain|.
- **Replica:** `FeedHistory.state_at` from `data/p2/feeds` and the SVI history of Paper 1 (`data/p1/volfeed`),
  `Timeline.at` from `results/p2/params` (standard lib of the manager), then `margin_sm.net_margin`,
  `margin_pm.net_margin` (static rate 0, fixed forward share from the feed state) or `margin_pm2.net_margin`. For
  the single contracts, also the vectorised path of B2 (`FeedHistory.bulk` and `margin_*.single`): in all 1,598
  rows it gives exactly the same number as `net_margin` (difference 0, column `K_replica_single`).
- **Chain:** A synthetic account (number 2⁶⁴ + 20260924, far above `lastAccountId`) receives exactly the balances
  of the book through an `eth_call` state override of `SubAccounts` (`heldAssets` slot 15, `balanceAndOrder`
  slot 14, layout checked with `eth_getStorageAt` on two existing accounts). Then the manager computes itself:
  `StandardManager.getMargin`, `PMRM.getMargin` or `PMRM_2.getMargin(account, isInitial)` at the same block. The
  chain builds the portfolio from its own feeds (spot, forward, vol, rate, perp, stable); nothing from our data
  enters the call.
- **Perps:** Both managers add `PerpAsset.getUnsettledAndUnrealizedCash(account)` linearly to margin and MtM. This
  value is read with the same override and subtracted. The perp thus enters as in the replica, with entry price
  equal to the perp price of the engine (18 of the 26 books hold a perp).
- **Large books:** An `eth_call` may use at most 50 million gas. PM2 needs about 110 million for a book with about
  300 legs. In 13 of the 51 book cases under legacy PM and PM2 (75 to 245 legs), `getMargin` failed at this limit,
  whether bundled through Multicall3 or called directly. There the chain computes per scenario:
  `getMarginAndMarkToMarket(account, isInitial, j)` runs the lib with scenario j alone. Because the requirement is
  monotone in minSPAN = min(basis, PnL_j), net is the minimum over j. On 6 books with 23 to 84 legs, where the
  direct call also goes through, both paths agree bit for bit (`results/p2/validation_summary.json`, key
  `per_scenario_check`).

## Sample

- **Single contracts:** per underlying and manager 100 random blocks (pre-registered: at least 48) in the window of
  the pre-registration up to the pilot cut, seed 20260924, with a separate branch per cell,
  `SeedSequence(20260924, spawn_key=(k,))`, so that BTC and ETH do not draw the same blocks. Per block one fill of
  the same UTC day from the Paper 1 tape (strike, type, price p) whose expiry is active (forward push at most 1 h
  old, `FeedHistory.live_expiries`) and has a fresh vol push (signed at most 20 min before the block); side at
  random. Without a matching fill the block is drawn again: 7 times across all 8 cells. The blocks run from
  14 January 2024 to 17 September 2026, the median remaining tenor per cell is 5.5 to 11.0 days, and 410 of 799
  contracts are short.
- **Maker books:** 20 maker days, drawn at random (own branch of the seed) from the H3 population: the start-of-day
  book of a dominant subaccount with at least one live option of an underlying whose PM2 window is open
  (2,134 maker days). One book per day and underlying (options and perp from `data/p2/books/snapshots.parquet`,
  expired options removed, cash and collateral outside K), 26 books in total with 2 to 245 legs and 1 to 11
  expiries, each under PM2, SM and (BTC, ETH) legacy PM. Prices p = mark M_b (Black-76 on the SVI curve, forward
  `svi_fwd`, D = 1). Drawn were M1 (5 August 2025), M2 (3 July, 4 September, 13 September 2025, 27 February,
  14 March, 17 March, 30 March 2026), M3 (30 May 2026), M4 (13 July, 2 August, 21 September 2025), M5 (6 November
  2025, 6 February, 26 May 2026), M6 (5 October 2025) and M8 (1 July, 25 July, 6 September, 14 September 2026).

## Findings

1. **Spot and forward bit-identical.** In all 1,598 single-contract rows, `getSpot` and `getForwardPrice` of the
   chain agree exactly with `state_at` (columns `spot_rel_dev`, `fwd_rel_dev` equal to 0).
2. **The remainder comes from the vol.** `getVol` at the strike deviates by a median of 1.2·10⁻⁸ relative, at most
   by 2.3·10⁻⁷ (`vol_rel_dev`). Cause: the SVI parameters come from Paper 1 and are stored as float32 (known from
   A1). This explains the remaining deviations of K of the order of 10⁻⁸.
3. **SM long exact.** A long option has no margin under SM: net = 0 on both sides and K = premium. In all 294 rows
   with an SM long, the deviation is exactly 0 (hence the median of 0 for ETH SM).
4. **One chain revert.** At block 36,366,166 (5 March 2026 23:39 UTC, HYPE, PM2), `getMargin` reverts because
   `getSpot` reverts: the last spot value was signed 489 s before the block. The replica keeps computing with this
   value. The case is not comparable and counts as missing (n = 99). For B2 this means that at such times the chain
   would not have allowed a margin check. The pre-registration excludes nothing because of feed age; the age is
   carried along (`spot_age`).
5. **Dormant branches.** The stable price lay between 0.99938 and 1.00144 at all blocks, above the depeg (SM) and
   peg-loss (PM2) thresholds of 0.99; `stable` = 1 in the replica changes nothing. The lowest confidence was 0.95
   (thresholds 0.55): the oracle contingencies were never active and are not checked against the chain here, only
   against the v2-core reference cases from A3 and A4. No book exceeded `maxExpiries`.

## Limits

- The synthetic account has no override lib, so what is checked is the standard lib. The override libs differ only
  in mmFactor (A2); IM is not affected by this, MM in the maker book is (B3, sensitivity).
- What is checked is the book at the start of the day, not the book before a fill. The positions of the latter come
  from the snapshot plus `BalanceAdjusted` (Addendum 1); the valuation is the same.
- For HYPE only one maker day is in the draw (M3, 235 legs). The book cells per underlying are small; the
  pre-registered minimum of 20 maker days applies to all underlyings together.

## Order of validation and measurement (added on 25 September 2026, audit A63)

The specification committed together with the pre-registration
(`docs/superpowers/specs/2026-09-24-p2-capital-design.md`, section 8, step 3) says "Validation against `eth_call`;
only then capital per fill, maker books, doses", and the section of the pre-registration is headed "Validation
before measurement". That is not how it went. Creation times of the files on 25 September 2026 (file system, local
time UTC+2) and commit times:

| Step | File or commit | Time |
|---|---|---|
| Capital per fill | `data/p2/derived/capital.parquet` | 00:40:00 |
| H4 panel with doses | `data/p2/derived/h4_panel.parquet` | 00:40:43 |
| Validation plan (BTC) | `data/p2/validation/plan_BTC.json` | 00:49:37 |
| Maker days (H3) | `data/p2/derived/maker_days.parquet` | 00:53:09 |
| Chain responses | `data/p2/validation/chain.jsonl` | 00:53:40 to 01:08:47 |
| Validation result | `results/p2/validation_summary.json` | 01:16:57 |
| Addendum 4 ("The validation against `eth_call` is passed") | commit `c4fcb59` | 01:29:58 |
| First test statistic | `results/p2/h1.json` | 01:42:53 |

Capital per fill, doses and maker days were therefore created before or alongside the validation. What was kept is
the operative rule in the text of the pre-registration, "Before capital figures enter a test, the replica is
checked …": the validation had passed and was recorded in Addendum 4 before the first test statistic was created.
The manuscript likewise claims only this order ("Before any capital entered a test"). Not kept are step 3 of the
specification and the wording of the heading. The validation draws its own samples and compares replica and chain
directly; it uses none of the capital figures computed earlier. Whether the replica was still changed between 00:40
and commit `591d2d5` (01:30:22) the history does not show, because Stage B is a single commit; the audit recomputed
samples of the capital figures independently (32 fills, 5 maker days, 7 H2 fills, 16 dose fills;
`docs/paper2/AUDIT.md`, perspective engine). File and git times are set locally and prove nothing to third parties
(audit A02).

## Reproduction

```
python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface.p2validate plan --ccy BTC   # likewise ETH, HYPE
python3 -m derive_surface.p2validate chain --max-seconds 480    # repeat until "done": true
python3 -m derive_surface.p2validate chain --retry-failed       # failed cases again, e.g. after the gas limit
python3 -m derive_surface.p2validate check-scenarios            # scenario path against the direct call
python3 -m derive_surface.p2validate report
```

RPC: 1,997 requests (1,974 `eth_call`, most of them with a state override, plus 17 `eth_getStorageAt` and 6
`eth_estimateGas` for the pre-check), at most 2 per second, log `data/p2/logs/B1.jsonl`. The plans
(`data/p2/validation/plan_{BTC,ETH,HYPE}.json`) hold the feed state, book and replica values of each case; the chain
responses are in `data/p2/validation/chain.jsonl`. Raw account numbers appear only there; in `results/` and here,
accounts appear as labels from `derive_surface.p2ids`.
