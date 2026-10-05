# Data status of Paper 2

## A3 Replica of PM2 (`derive_surface/margin_pm2.py`)

As of 2026-09-24. Offline replica of `PMRMLib_2` including `PMRM_2._arrangePortfolio` (v2-core `96796a6`), a port of
the vectorised prototype `data/p2/semantik_20260924/verify-konvex/pm2v.py`, checked line by line against `PMRMLib_2.sol`,
`PMRM_2.sol` and `code-pm2/pm2_replica.py` (line references in the code). `PMRM_2_1` only changes the choice of lib
per account, not the computation.

| Check | Scope | Result |
|---|---|---|
| v2-core reference cases `PMRM_2/portfolio_cases` | 139 of 139 (IM and MM), including `test_67`, which the Solidity harness skips | max. relative error 9.2e-15 |
| Chain cases (`tests/fixtures/p2/pm2_chain_cases.json`) | 25 books at 4 blocks: BTC 27 013 992 (2025-08-01, old regime), BTC 45 113 645 (2026-09-24, the 10 books from `rep_vs_chain.json`), ETH 36 777 192 (2026-03-15), HYPE 38 116 392 (2026-04-15); IM and MM each | max. absolute deviation of net 5.1e-11 USD, max. relative deviation of R 1.6e-13, worst scenario equal in 50 of 50 |
| Cross-check against `pm2v.py` | 3 000 random books (1 to 39 legs, some with a perp) at block 45 113 645 | max. relative difference 4.5e-13 |
| `single` against `net_margin` | 200 random contracts (4 parameter sets, edge cases at 0 s, 30 min, 30 days, confidence below threshold, negative rate, peg) | equal to 1e-10 relative |
| Runtime of `single` | 600 000 single contracts | about 1 s (limit 120 s) |

Chain cases: feeds and parameters by `eth_call` at the block, portfolio built as in `PMRM_2._arrangePortfolio`, result
of `PMRMLib_2.addPrecomputes` and `getMarginAndMarkToMarket` at the same block. Generated with
`data/p2/margin_pm2/build_chain_cases.py` (241 RPC requests, at most 2/s, log `data/p2/logs/A3.jsonl`, cache
`data/p2/margin_pm2/cache.json`). Multicall3 (`0xcA11bde05977b3631167028862bE2a173976CA11`) has code on chain 957
(3 808 bytes); not needed for A3 and not used. The A2 timelines `results/p2/params/{BTC,ETH,HYPE}_pm2.json`
agree field by field with the getters of the chain cases at all four blocks, and `margin_pm2` takes them
unchanged (state of the A2 files on the evening of 2026-09-24).

Interface: `net_margin(book, state, params, is_initial=True, *, vols=None, collaterals=()) -> (net, mtm)`,
`requirement(...) -> float`, `margin_details(...) -> dict` (with `worst`, `minSPAN`, contingencies),
`single(arrays, params, is_initial=True) -> (net, mtm)`. Parameters in the A2 schema; `VolShockParameters.dteFloor` in
seconds (a 1e18-scaled value below 1 raises `ValueError`); `volShock` as 0 to 4 or as a name. Vol shocks and
skew act on the vol at the strike, discount `exp(-max(r, 0) τ)` from `ExpiryState.rate`, perp value `q (P − entry)`,
perp scenario `q (shock − 1) P`, perp contingency `|q| S pct`, oracle contingency via the smallest confidence per
held expiry (spot, perp if held, forward, rate, vol).

Open points for the follow-up tasks:
- `ExpiryState` knows neither the fixed forward portion in the 30-min settlement window nor the confidence of the
  rate feed. The replica reads both if present (`fwd_fixed`, default 0; `rate_conf`, default 1), and `single` takes
  them as optional columns. Without them the replica deviates only in the last 30 min before expiry or at a rate
  confidence below 0.55.
- `maxExpiries` is not enforced (the chain would revert with more expiries).
- The v2-core reference cases are read directly from `data/p2/v2-core` (BUSL licence, not copied into the repo); if
  the directory is missing, these tests are skipped.

## A4 Replica of SM and legacy PM (`derive_surface/margin_sm.py`, `derive_surface/margin_pm.py`)

As of 2026-09-24 (fix round after review). Offline replica of the `StandardManager` (with
`SRMPortfolioViewer.arrangeSRMPortfolio`) and of the legacy manager `PMRM` with `PMRMLib` (v2-core `96796a6`),
line references in the code. Both engines first net the legs per instrument `(expiry, strike, is_call)` like
`SubAccounts` (one balance per subId; zero balances drop out and count neither as a position nor as an expiry); a
fill appended to a book thus yields the balance after the trade. SM: isolated margin per option (long without margin), per
expiry `max(Σ isolated, max loss)` with max loss on the grid {0} ∪ strikes of the expiry plus
`unpaired*Scale · F · netCalls` for net short calls, expiries summed, MtM Black-76 on the forward with D = 1, perp
`−|q| · P · (im|mm)PerpReq` plus unrealised PnL, base collateral with `marginFactor` (IM additionally `IMScale`),
oracle contingencies (perp, expiry, base) only for IM, and a depeg surcharge on `|perp| + all shorts`. Legacy PM:
MtM without discount and without skew, spot shock only on the variable forward portion, vol shock multiplicative per
expiry, positive scenario values times the static discount `baseStaticDiscount · exp(−τ (max(r, 0) · rateMultScale +
rateAddScale))` with the legacy rate r = 0 (see findings), `minSPAN` = minimum of basis contingency and scenarios
from `params["scenarios"]`, minus static contingencies (perp, base, naked shorts per strike), for IM times `imFactor`
(plus peg surcharge) minus confidence contingency; MM with factor 1.

| Check | Scope | Result |
|---|---|---|
| v2-core `StandardManager/test-cases.json` | 28 of 28, IM, MM and MtM (ETH and BTC, perps with funding, base, depeg, confidences) | max. relative deviation 2.4e-14 (the Solidity test allows 0.1 %) |
| v2-core `StandardManager/test-cases-portfolio.json` | 42 of 42, IM and MM in whole USD | all exact |
| Chain SM isolated (`tests/fixtures/p2/sm_chain_cases.json`) | `getIsolatedMargin` at 12 blocks (BTC 5, ETH 4, HYPE 3; 2024-02-15 to 2026-09-10), each 2 expiries × 5 strikes × call/put × 3 amounts × IM/MM = 1 440 positions | max. absolute deviation 5.8e-11 USD, relative 8.0e-12 |
| Chain SM whole accounts (`sm_chain_accounts.json`) | `getMarginAndMarkToMarket` for 12 real SM accounts at 6 blocks (2024-03-20 to 2026-08-20), 14 to 30 options, up to 8 markets, 8 accounts with base collateral, 5 with perps including unrealised PnL; IM and MM, net and MtM | max. absolute deviation 3.7e-9 USD |
| v2-core `PMRM/test-cases-portfolio-pm.json` | 44 of 44, IM and MM in whole USD | all exact |
| v2-core `PMRM/testAndVerifyScenarios.json` | 21 of 21, IM, MM and MtM | max. absolute deviation 5.1e-11 USD (the Solidity test allows 1e-10 USD) |
| Chain legacy PM lib (`pm_chain_cases.json`) | deployed `PMRMLib` (`addPrecomputes`, `getMarginAndMarkToMarket`) at 8 blocks (BTC and ETH, 2024-03-01 to 2026-03-01, all three parameter states), 5 books each (3 with one leg, 2 mixed with a perp or with a perp and base), IM and MM | max. absolute deviation 7.3e-11 USD, relative 8.9e-14 |
| Chain legacy PM whole accounts (`pm_chain_accounts.json`) | `PMRM.getMargin(acc, true/false)` and MtM from `getMarginAndMarkToMarket(acc, true, 0)` for 5 maker accounts under the legacy PM (ETH 2024-03-10, BTC 2024-09-15, ETH 2024-12-15, BTC 2025-06-16, ETH 2025-12-15; all three parameter states), 26 to 59 options, 6 to 9 expiries, each with one perp and open cash, cash up to 1.1 million USD; inputs via Multicall at the same block, legacy rate not passed (default 0), `strict_expiries=True` | max. absolute deviation 4.7e-10 USD, relative 2.0e-15 |
| Parameters against the A2 timelines | SM at 12 blocks, legacy PM at 13 blocks (both chain fixtures) against `p2params.Timeline(ccy, mgr).at(ts)`, including `scenarios` and `maxExpiries` | all equal field by field (now as a test) |
| `single` against `net_margin` | 200 random contracts each, IM and MM (confidences below threshold, depeg, 0 s remaining tenor, negative legacy rate via `rate_pm`) | equal to 1e-12 relative |
| Netting per instrument | legs +1 and −2 equal −1, +1 and −1 equal an empty book, SM and legacy PM, IM and MM, confidence below threshold and depeg | equal to 1e-12 relative (previously double margin for SM, e.g. BTC 90 000 C: −22 984 instead of −11 492 USD) |
| Runtime of `single` | 600 000 single contracts | SM 0.05 s, legacy PM 0.75 s (limit in the test 10 s) |

Chain cases: all inputs (feeds of the respective manager, parameter getters, scenarios, account balances) by `eth_call`
at the same block, bundled via Multicall3 (`0xcA11bde05977b3631167028862bE2a173976CA11`, code since block
2 454 793 at the latest, not yet at block 843 000); `PMRM.getMargin` directly. Generated with
`tests/fixtures/p2/gen_a4_chain_fixtures.py {sm,pm,accounts,pm_accounts}` (not collected by pytest, needs
`eth_abi`/`eth_hash` from the system, no package dependency): 265 RPC requests in total, at most 2/s, log
`data/p2/logs/A4.jsonl`. The SM accounts are active taker and maker subaccounts from Paper 1; the generator picks the
legacy PM accounts by fixed criteria from `data/p2/books/snapshots.parquet` (A5): options and a perp under the
legacy PM, 3 to 11 expiries, 10 to 60 options, the day nearest to the target date. Account IDs in both fixtures only as
`sha256(str(id))[:10]`. The v2-core reference cases are read directly from `data/p2/v2-core` as in A3 (BUSL,
not copied into the repo) and skipped without the directory; the chain fixtures always run.

Parameters in the A2 schema (Solidity struct and field names, 1e18 scaling reversed, `dteFloor` in seconds,
`volShock` 0 None, 1 Up, 2 Down); `results/p2/params/*_sm.json` and `*_pm.json` go in unchanged.
`tests/fixtures/p2/a4_params_today.json` contains today's values (SM BTC from `srm_params_live.json`, legacy PM
BTC from `params_live.json`, `lib1.*`).

Findings:
- Legacy rate constantly 0: the `interestRateFeed` of both legacy managers are `LyraRateFeedStatic`
  (BTC `0x6fef1bb8…004f`, ETH `0x30a6e6a3…9feb`). By `eth_getLogs` from block 800 000 to 45 131 522 there is exactly
  one `RateUpdated` each, at the deploy (BTC block 843 076, ETH 843 060), with rate 0 and confidence 1e18, and on both
  PMRM no `InterestRateFeedUpdated`. The static discount thus depends only on `rateAddScale` 0.12. `margin_pm` therefore
  computes with rate 0 and confidence 1 by default and no longer reads `ExpiryState.rate` (the PM2 rate from A1);
  `single` ignores the column `rate` and reads only an optional column `rate_pm` (default 0). `rates=` and
  `rate_confs=` remain as overrides for reference cases. Without this correction, K_pm of a long option in the
  PM2 window (PM2 rate about 4.2 %) would have been too high: ATM long call BTC (σ 0.5, today's parameters) +0.02 % at
  30 days, +0.27 % at 90 days, +0.92 % at 180 days.
- Legacy PM parameters, three states (the same for each underlying, according to A2 and confirmed at all 13 blocks):
  basis contingency `basisContAddFactor`/`basisContMultFactor` 1.0/1.2 until 2024-06-12 00:01 UTC, then 0.5/2.0; `maxExpiries` 11 until
  2024-09-25 04:47 UTC, then 18; on 2025-02-22 19:52 UTC `volRangeUp` 0.6 → 0.5, `optionPercent` 0.02 → 0.015 and
  scenarios ±20 % → ±18 %.
- SM: BTC and ETH option parameters the same over the whole period (`maxSpotReq` 0.15, `minSpotReq` 0.13, MM 0.09);
  HYPE considerably stricter (0.30, 0.25, MM 0.18, `unpairedIMScale` 1.3); perp and base parameters change.
- At all chain blocks the confidences were above the thresholds (vol 0.95, spot and perp 1.0), so the
  oracle contingencies are dormant there; they are checked through the v2-core reference cases and the netting tests.

Interfaces:
- `margin_sm.net_margin(book, state, params, is_initial=True, *, vols=None, base=0.0) -> (net, mtm)` per market,
  `margin_sm.net_margin_multi(books, states, params_by_ccy, is_initial=True, *, cash=0.0, vols=None, bases=None)`
  for accounts across several markets (cash once), `margin_sm.single(arrays, params, is_initial=True) -> (net, mtm)`,
  `margin_sm.isolated_margin(...)`, `margin_sm.requirement(...)`, `margin_sm.b76_prices(F, K, σ, sec, D=1)`,
  `margin_sm.merged_options(book) -> list[OptionLeg]` (netting per instrument),
  `margin_sm.MARKET_ID = {"ETH": 1, "BTC": 2, "HYPE": 48}`.
- `margin_pm.net_margin(book, state, params, is_initial=True, *, vols=None, base=0.0, rates=None, rate_confs=None,
  fwd_fixed=None, strict_expiries=False) -> (net, mtm)`, `margin_pm.single(arrays, params, is_initial=True) ->
  (net, mtm)` (optional columns `stable`, `rate_pm`, `rate_conf`, `fwd_fixed`; `rate` is ignored),
  `margin_pm.requirement(...)`, `margin_pm.TooManyExpiries` (subclass of `ValueError`).
- `vols` maps `(expiry, strike)` to the vol feed value; without an entry the SVI curve of `ExpiryState` applies.
  Capital per fill: `K = p · q − net` with cash 0 (`p2types.capital_from_net`).
- B2 can pass the `bulk_state` columns from A1 unchanged to both `single` functions; the PM2 rate in `rate` has no
  effect there.
- B3: with `strict_expiries=True`, `margin_pm.net_margin` raises `TooManyExpiries` if the netted book holds more
  expiries than `params["maxExpiries"]` (11 until 2024-09-25, then 18). PMRM then reverts
  (`PMRM_TooManyExpiries`; all held expiries count, including expired ones not yet settled). B3
  must carry such books under the legacy PM as NaN instead of reporting a capital.

Open points:
- `Book` has no field for base collateral; it enters through `base=`. `ExpiryState` knows neither the fixed
  forward portion of the last 30 min nor the rate confidence (legacy PM: `fwd_fixed`, `rate_confs`).
- Not enforced: `maxAccountSize` of both managers, OI caps; `maxExpiries` only with `strict_expiries=True`.

## A2 Parameter timelines (`derive_surface/p2params.py`)

As of 2026-09-24, chain 957 up to block 45 130 786 (2026-09-24 20:53:07 UTC). Timelines per underlying and manager
under `results/p2/params/{CCY}_{sm,pm,pm2}.json`, plus the override libs `{CCY}_pm2_lib_<addr8>.json` and the assignments
`{CCY}_pm2_overrides.json`. Schema as in the plan: list in ascending block order, each entry with `from_block`, `from_ts`,
`from_utc`, `source`, `changed` (structs changed relative to the predecessor), `params` and, for PM and PM2, `lib`.
Keys in `params` are the struct and field names from v2-core `96796a6`; 1e18 values as float (`int / 10**18`,
correctly rounded), `dteFloor` in seconds, `maxExpiries` and `volShock` as int (PM2: 0 None, 1 Up, 2 Down, 3 Linear,
4 Abs; legacy PM: 0 to 2), `CollateralParameters` as `{asset: {...}}` only with the assets that are set. Consecutive
identical states are merged, so every entry is a real change. `HYPE_pm.json` is an empty list
(no legacy PM for HYPE), so `Timeline("HYPE", "pm").at(ts)` raises `KeyError`, as it does before any first entry.

Procedure:
- Events by `eth_getLogs` (address and topic filter, range halved on errors): SRM `OptionMarginParamsSet`,
  `PerpMarginRequirementsSet`, `BaseMarginParamsSet`, `OracleContingencySet`, `DepegParametersSet` (248);
  legacy PMRM `ScenariosUpdated`, `MaxExpiriesUpdated` (6); PM2 managers and standard libs all `*ParamsUpdated`,
  `CollateralParametersUpdated`, `ScenariosUpdated`, `MaxExpiriesUpdated`, `LibOverrideUpdated`, `Upgraded`,
  `Initialized` (198); the three override libs their `*ParamsUpdated` and `CollateralParametersUpdated` (113). In total
  565 events. All 449 matching events from `data/p2/kontext/margin-historie/events.json` are included; new
  are the 3 `Initialized` and the 113 events of the override libs.
- At every event block a historical `eth_call` reads all getters (state after the block): PM2
  `getScenarios`, `maxExpiries`, `lib` (checked to equal the standard lib), `getMarginParams`, `getVolShockParams`,
  `getBasisContingencyParams`, `getOtherContingencyParams`, `getSkewShockParams`, `getCollateralParameters` per asset
  (all 25, 24 and 8 assets from the collateral events); legacy PM `getScenarios`, `maxExpiries`,
  `getStaticDiscountParams`, `getVolShockParams`, `getBasisContingencyParams`, `getOtherContingencyParams`; SM
  `optionMarginParams`, `perpMarginRequirements`, `baseMarginParams`, `oracleContingencyParams` per market (BTC 2, ETH 1,
  HYPE 48) and `depegParams`. Never the event: in `OptionMarginParamsSet`, unpairedMM and unpairedIM are swapped.
- Multicall3 (`0xcA11bde05977b3631167028862bE2a173976CA11`) has code from block 1 935 198 (2023-12-29 23:20:11 UTC,
  found by bisection over `eth_getCode`); from there on, all getters of a block are bundled in one `aggregate3` (at most
  250 calls per request, 189 per daily sample, far below the gas cap), before that as single calls.
- Legacy PM (no events from the lib): samples at the deploy block, at the first block of every month and at the end
  block (35 samples), bisection of every change down to the block, then daily samples ±14 days around every change found (137 samples), until no
  new change appears. The result is the same for BTC and ETH: monthly samples with bisection, daily samples around the changes
  and the full daily series give the same blocks. Around every change, all daily samples agree with the timeline
  (BTC 14 to 28, ETH 21 to 28 days per change). The preliminary work (`oi_legacy.py`: 2024-06-12 and 2025-02-22)
  is confirmed, exact to the block (9 064 436 and 20 116 171).
- Daily series for all eleven timelines: first block of every UTC day from 2023-12-30 to 2026-09-24 (1 000 days), all
  getters via Multicall3, compared with `Timeline.at(ts)`. Result: 11 000 of 11 000 daily samples equal, of which active
  (manager or lib exists): SM BTC and ETH 1 000 each, SM HYPE 335, legacy PM BTC and ETH 1 000 each, PM2 BTC and ETH
  472 each, PM2 HYPE 343, override libs 233 each. So no parameter state changes without an event, except the lib of
  the legacy PM (captured there through the bisection).
- Resumable: every state per (block, timeline) is stored in `data/p2/params/snapshots.jsonl` (7 021 lines) with
  165 distinct states in `states.jsonl`; events in `logs_*.json` and `events_decoded.json`, end block in
  `meta.json`, check result in `summary.json`. Run `python3 -m derive_surface.p2params load --max-seconds 520`
  until `DONE`, table with `python3 -m derive_surface.p2params report`. RPC in total 3 391 requests (3 348
  `eth_call`, 13 `eth_getLogs`, 28 `eth_getCode`, 2 `eth_blockNumber`), at most 2/s, log `data/p2/logs/A2.jsonl`.

Capital-relevant changes (without `CollateralParameters` and `maxExpiries`), queried with
`Timeline.changes(keys=[...])`:
- Legacy PM BTC and ETH in the period of Paper 1: 2024-06-12 00:01:27 UTC (basis contingency 1.0/1.2 → 0.5/2.0) and
  2025-02-22 19:52:37 UTC (scenarios ±20 % → ±18 %, `volRangeUp` 0.6 → 0.5, `volRangeDown` 0.3 → 0.275, basis shock
  0.95/1.05 → 0.955/1.045, `optionPercent` 0.02 → 0.015). In addition `maxExpiries` 11 → 18 on 2024-09-25 04:47:15 UTC
  (manager event, without effect for single contracts) and the setup in December 2023 (before the window).
- PM2 in the PM2 window (BTC and ETH from 2025-06-12 23:00 UTC, HYPE from 2025-11-11): BTC 2025-10-10, 2026-01-08,
  2026-01-23, 2026-05-24 (two blocks, 04:05 and 05:21 UTC), 2026-08-20; ETH 2025-10-10, 2026-01-08, 2026-01-23,
  2026-05-24, 2026-08-20; HYPE 2026-01-08, 2026-05-08, 2026-05-24, 2026-08-20. The change of 2025-06-12 22:20 UTC
  (static discount add 0.16 → 0.1, mult 0.1 → 0) lies 40 minutes before the start of the window.
- SM: for BTC and ETH no change of the option parameters since the deploy (only perp on 2024-06-12, and `IMScale` of the
  base collateral set to 0 for 57 minutes on 2024-10-08); for HYPE only perp and base parameters.
- Besides this, the standard libs often change `CollateralParameters` (haircuts for non-USDC collateral, outside K):
  BTC 12, ETH 12, HYPE 8 entries only for that.

Override libs (`PMRM_2_1` since 2026-02-03, `LibOverrideUpdated`): exactly one lib per underlying, set up on
2026-02-03 between 21:19 and 22:01 UTC. From then on they match the standard lib at every change point field by
field except for `mmFactor`: BTC `0x4e8ea8af…46c8` and ETH `0x902e3867…45f9` 0.35 instead of 0.8; HYPE `0xf4caea4e…aa17`
0.45 instead of 0.95, from 2026-05-24 0.40 instead of 0.9 and from 2026-08-20 0.40 instead of 0.8. Assigned: BTC 15, ETH 16, HYPE 10 accounts, first assignment 2026-02-10 (ETH) or 2026-02-17, last
2026-09-21, no revocation. In `results/` the accounts appear only as a label from `derive_surface.p2ids` (M1 to M10,
otherwise an HMAC with a secret salt); the raw assignment is in
`data/p2/params/{CCY}_pm2_overrides_raw.json`. The timeline of an override lib contains the scenarios and `maxExpiries`
of the manager, so it can be used directly as a parameter set.

Manager shares of options OI: `results/p2/manager_oi_share.csv` (columns `month, ccy, sm, pm, pm2`, 75 rows: BTC
2024-01 to 2026-09, ETH 2024-02 to 2026-09, HYPE 2025-12 to 2026-09) from
`data/p2/kontext/margin-historie/oi_legacy.json`, share of `OptionAsset.totalPosition(manager)` (sum of the
amounts of all balances) in the sum over the managers, reference date always the first of the month at 00:00:01 UTC. Months without OI
and the header row `head` are dropped; HYPE has no legacy PM (`pm` empty).

Interfaces:
- `p2params.Timeline(ccy, mgr, lib=None, root=None, entries=None)` with `.at(ts) -> dict`, `.entry_at(ts) -> dict`,
  `.changes(keys=None) -> list[int]` (`from_ts` of every change after the first entry, optionally only for certain
  structs), `.save(root=None)`, `Timeline.path(ccy, mgr, lib=None, root=None)`.
- `p2params.load_overrides(ccy)`, `p2params.account_lib(overrides, account_id, ts) -> str | None` (takes the raw
  account ID and forms the label internally), `p2params.pm2_params_for_account(ccy, account_id, ts) -> dict` (override lib if
  set, otherwise the standard lib).
- `p2params.manager_oi_share(oi_json) -> DataFrame`, `p2params.report_markdown()`.

Open points:
- The end block is the chain head at the first run (2026-09-24 20:53 UTC). For the final data run after 2026-10-01,
  delete `data/p2/params/meta.json` or set `--to-block`; the collateral assets depend on the end block, so the cache
  distinguishes asset lists.
- A change of the legacy lib that was reverted within the same day would stay invisible
  (daily grid); for the other managers the complete event list rules this out.

Tables of the changes (state after the respective block; entries that only change `CollateralParameters` are
counted, not listed individually; decimal point):

**BTC SM** (4 entries, `results/p2/params/BTC_sm.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2023-12-04 16:36 | 843078 | start+event:OptionMarginParamsSet+OracleContingencySet+Pe… | Start |
| 2024-06-12 00:03 | 9064496 | event:PerpMarginRequirementsSet | imPerpReq 0.1→0.066; mmPerpReq 0.065→0.05 |
| 2024-10-08 17:49 | 14194091 | event:BaseMarginParamsSet | IMScale 0.93→0 |
| 2024-10-08 18:46 | 14195796 | event:BaseMarginParamsSet | IMScale 0→0.93 |

**BTC PM** (7 entries, `results/p2/params/BTC_pm.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2023-12-04 16:36 | 843077 | start | Start |
| 2023-12-04 16:36 | 843078 | bisection+event:ScenariosUpdatedLegacy | basisContAddFactor 0→0.4; basisContMultFactor 0→1.2; scenarioSpotDown 0→0.95; scenarioSpotUp 0→1.05; baseStaticDiscount 0→0.95; imFactor 0→1.25; rateAddScale 0→0.12; rateMultScale 0→1; basePercent 0→0.03; confMargin 0→1; confThreshold 0→0.55; optionPercent 0→0.01; pegLossFactor 0→4; pegLossThreshold 0→0.99; … (+7) |
| 2023-12-11 07:27 | 1129020 | bisection | basisContAddFactor 0.4→1 |
| 2023-12-11 07:27 | 1129024 | bisection | optionPercent 0.01→0.02 |
| 2024-06-12 00:01 | 9064436 | bisection | basisContAddFactor 1→0.5; basisContMultFactor 1.2→2 |
| 2024-09-25 04:47 | 13609010 | bisection+event:MaxExpiriesUpdated | maxExpiries 11→18 |
| 2025-02-22 19:52 | 20116171 | bisection+event:ScenariosUpdatedLegacy | scenarioSpotDown 0.95→0.955; scenarioSpotUp 1.05→1.045; optionPercent 0.02→0.015; volRangeDown 0.3→0.275; volRangeUp 0.6→0.5; scenarios: grid ±20 %→±18 % |

**BTC PM2** (23 entries, `results/p2/params/BTC_pm2.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2025-06-09 05:18 | 24712334 | start+event:Upgraded+MaxExpiriesUpdated+Initialized+Basis… | Start |
| 2025-06-09 08:21 | 24717845 | event:MarginParamsUpdated | longBaseStaticDiscount 1.05→1.02; longRateMultScale 0→0.1; shortBaseStaticDiscount 0.95→0.98; shortRateMultScale 0→0.1 |
| 2025-06-12 22:20 | 24872593 | event:MarginParamsUpdated | longRateAddScale 0.16→0.1; longRateMultScale 0.1→0; shortRateAddScale 0.16→0.1; shortRateMultScale 0.1→0 |
| 2025-09-17 21:41 | 29061847 | event:MaxExpiriesUpdated | maxExpiries 10→14 |
| 2025-10-10 22:55 | 30057658 | event:OtherContingencyParamsUpdated | confMargin 1→0.4 |
| 2026-01-08 22:50 | 33945517 | event:MarginParamsUpdated | longBaseStaticDiscount 1.02→0.98; shortBaseStaticDiscount 0.98→1.02 |
| 2026-01-23 04:24 | 34560315 | event:ScenariosUpdated | scenarios: tail dampening changed |
| 2026-05-24 04:05 | 39786946 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated… | IMPerpPercent 0.01→0.015; MMPerpPercent 0.03→0.015; volRangeUp 0.5→0.45; scenarios: grid ±18 %→±17 %, tail dampening changed |
| 2026-05-24 05:21 | 39789246 | event:BasisContingencyParamsUpdated | scenarioSpotDown 0.955→0.9575; scenarioSpotUp 1.045→1.0425 |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 14→16; Collateral (4 values) |
| 2026-08-20 22:09 | 43621075 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0.9575→0.965; scenarioSpotUp 1.0425→1.035; IMOptionPercent 0.002→0.001; IMPerpPercent 0.015→0.0075; MMOptionPercent 0.003→0.0015; MMPerpPercent 0.015→0.0075; minVolUpShock 0.4→0.5; volRangeDown 0.3→0.25; volRangeUp 0.45→0.4; scenarios: grid ±17 %→±14 %, tail dampening changed; Collateral (4 values) |

Plus 12 entries that only change `CollateralParameters` (not USDC, outside K).

**BTC PM2 override lib 0x4e8ea8afeb1f7583c3d1e27176d864fa652546c8** (36 entries, `results/p2/params/BTC_pm2_lib_4e8ea8af.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2026-02-03 21:20 | 35065996 | start+event:BasisContingencyParamsUpdated | Start |
| 2026-02-03 21:20 | 35065998 | event:VolShockParamsUpdated | dteFloor 0→86400; longTermPower 0→0.13; minVolUpShock 0→0.4; shortTermPower 0→0.3; volRangeDown 0→0.3; volRangeUp 0→0.5 |
| 2026-02-03 21:20 | 35066000 | event:OtherContingencyParamsUpdated | IMOptionPercent 0→0.002; IMPerpPercent 0→0.01; MMOptionPercent 0→0.003; MMPerpPercent 0→0.03; confMargin 0→0.4; confThreshold 0→0.55; pegLossFactor 0→4; pegLossThreshold 0→0.99 |
| 2026-02-03 21:20 | 35066002 | event:MarginParamsUpdated | imFactor 0→1; longBaseStaticDiscount 0→0.98; longRateAddScale 0→0.1; mmFactor 0→0.35; shortBaseStaticDiscount 0→1.02; shortRateAddScale 0→0.1 |
| 2026-02-03 21:20 | 35066004 | event:SkewShockParamsUpdated | absBaseCap 0→0.25; absCBase 0→-0.1; linearBaseCap 0→0.25; linearCBase 0→-0.1; minKStar 0→0.01; volParamStatic 0→0.6; widthScale 0→4 |
| 2026-05-24 04:05 | 39786946 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated… | IMPerpPercent 0.01→0.015; MMPerpPercent 0.03→0.015; volRangeUp 0.5→0.45; scenarios: grid ±18 %→±17 %, tail dampening changed |
| 2026-05-24 05:21 | 39789246 | event:BasisContingencyParamsUpdated | scenarioSpotDown 0.955→0.9575; scenarioSpotUp 1.045→1.0425 |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 14→16; Collateral (4 values) |
| 2026-08-20 22:09 | 43621075 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0.9575→0.965; scenarioSpotUp 1.0425→1.035; IMOptionPercent 0.002→0.001; IMPerpPercent 0.015→0.0075; MMOptionPercent 0.003→0.0015; MMPerpPercent 0.015→0.0075; minVolUpShock 0.4→0.5; volRangeDown 0.3→0.25; volRangeUp 0.45→0.4; scenarios: grid ±17 %→±14 %, tail dampening changed; Collateral (4 values) |

Plus 27 entries that only change `CollateralParameters` (not USDC, outside K).

Assignments: 15 events for 15 accounts on 9 days (2026-02-17 to 2026-09-21); revocations: 0.

**ETH SM** (4 entries, `results/p2/params/ETH_sm.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2023-12-04 16:35 | 843061 | start+event:OptionMarginParamsSet+OracleContingencySet+Pe… | Start |
| 2024-06-12 00:03 | 9064496 | event:PerpMarginRequirementsSet | imPerpReq 0.1→0.066; mmPerpReq 0.065→0.05 |
| 2024-10-08 17:49 | 14194091 | event:BaseMarginParamsSet | IMScale 0.9375→0 |
| 2024-10-08 18:46 | 14195796 | event:BaseMarginParamsSet | IMScale 0→0.9375 |

**ETH PM** (6 entries, `results/p2/params/ETH_pm.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2023-12-04 16:35 | 843061 | start+event:ScenariosUpdatedLegacy | Start |
| 2023-12-11 07:27 | 1129013 | bisection | basisContAddFactor 0.4→1 |
| 2023-12-11 07:27 | 1129017 | bisection | optionPercent 0.01→0.02 |
| 2024-06-12 00:01 | 9064436 | bisection | basisContAddFactor 1→0.5; basisContMultFactor 1.2→2 |
| 2024-09-25 04:47 | 13609010 | bisection+event:MaxExpiriesUpdated | maxExpiries 11→18 |
| 2025-02-22 19:52 | 20116171 | bisection+event:ScenariosUpdatedLegacy | scenarioSpotDown 0.95→0.955; scenarioSpotUp 1.05→1.045; optionPercent 0.02→0.015; volRangeDown 0.3→0.275; volRangeUp 0.6→0.5; scenarios: grid ±20 %→±18 % |

**ETH PM2** (22 entries, `results/p2/params/ETH_pm2.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2025-06-09 05:16 | 24712302 | start+event:Upgraded+MaxExpiriesUpdated+Initialized+Basis… | Start |
| 2025-06-09 08:22 | 24717867 | event:MarginParamsUpdated | longBaseStaticDiscount 1.05→1.02; longRateMultScale 0→0.1; shortBaseStaticDiscount 0.95→0.98; shortRateMultScale 0→0.1 |
| 2025-06-12 22:20 | 24872593 | event:MarginParamsUpdated | longRateAddScale 0.16→0.1; longRateMultScale 0.1→0; shortRateAddScale 0.16→0.1; shortRateMultScale 0.1→0 |
| 2025-09-17 21:41 | 29061847 | event:MaxExpiriesUpdated | maxExpiries 10→14 |
| 2025-10-10 22:55 | 30057658 | event:OtherContingencyParamsUpdated | confMargin 1→0.4 |
| 2026-01-08 22:50 | 33945517 | event:MarginParamsUpdated | longBaseStaticDiscount 1.02→0.98; shortBaseStaticDiscount 0.98→1.02 |
| 2026-01-23 04:24 | 34560315 | event:ScenariosUpdated | scenarios: tail dampening changed |
| 2026-05-24 04:05 | 39786946 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated | IMPerpPercent 0.01→0.015; MMPerpPercent 0.03→0.015; volRangeUp 0.5→0.45 |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 14→16; Collateral (4 values) |
| 2026-08-20 22:09 | 43621075 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0.955→0.96; scenarioSpotUp 1.045→1.04; IMOptionPercent 0.002→0.001; IMPerpPercent 0.015→0.0075; MMOptionPercent 0.003→0.0015; MMPerpPercent 0.015→0.0075; minVolUpShock 0.4→0.5; volRangeDown 0.3→0.25; volRangeUp 0.45→0.4; scenarios: grid ±18 %→±16 %, tail dampening changed; Collateral (3 values) |

Plus 12 entries that only change `CollateralParameters` (not USDC, outside K).

**ETH PM2 override lib 0x902e386778456398888a8872e51f73f23f8845f9** (35 entries, `results/p2/params/ETH_pm2_lib_902e3867.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2026-02-03 21:19 | 35065988 | start+event:BasisContingencyParamsUpdated | Start |
| 2026-02-03 21:19 | 35065989 | event:VolShockParamsUpdated | dteFloor 0→86400; longTermPower 0→0.13; minVolUpShock 0→0.4; shortTermPower 0→0.3; volRangeDown 0→0.3; volRangeUp 0→0.5 |
| 2026-02-03 21:19 | 35065990 | event:OtherContingencyParamsUpdated | IMOptionPercent 0→0.002; IMPerpPercent 0→0.01; MMOptionPercent 0→0.003; MMPerpPercent 0→0.03; confMargin 0→0.4; confThreshold 0→0.55; pegLossFactor 0→4; pegLossThreshold 0→0.99 |
| 2026-02-03 21:19 | 35065992 | event:MarginParamsUpdated | imFactor 0→1; longBaseStaticDiscount 0→0.98; longRateAddScale 0→0.1; mmFactor 0→0.35; shortBaseStaticDiscount 0→1.02; shortRateAddScale 0→0.1 |
| 2026-02-03 21:20 | 35065994 | event:SkewShockParamsUpdated | absBaseCap 0→0.25; absCBase 0→-0.1; linearBaseCap 0→0.25; linearCBase 0→-0.1; minKStar 0→0.01; volParamStatic 0→0.6; widthScale 0→4 |
| 2026-05-24 04:05 | 39786946 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated | IMPerpPercent 0.01→0.015; MMPerpPercent 0.03→0.015; volRangeUp 0.5→0.45 |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 14→16; Collateral (4 values) |
| 2026-08-20 22:09 | 43621075 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0.955→0.96; scenarioSpotUp 1.045→1.04; IMOptionPercent 0.002→0.001; IMPerpPercent 0.015→0.0075; MMOptionPercent 0.003→0.0015; MMPerpPercent 0.015→0.0075; minVolUpShock 0.4→0.5; volRangeDown 0.3→0.25; volRangeUp 0.45→0.4; scenarios: grid ±18 %→±16 %, tail dampening changed; Collateral (3 values) |

Plus 27 entries that only change `CollateralParameters` (not USDC, outside K).

Assignments: 16 events for 16 accounts on 9 days (2026-02-10 to 2026-09-21); revocations: 0.

**HYPE SM** (6 entries, `results/p2/params/HYPE_sm.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2025-10-24 03:12 | 30626980 | start+event:OracleContingencySet+PerpMarginRequirementsSe… | Start |
| 2025-10-29 21:59 | 30876782 | event:BaseMarginParamsSet | IMScale 0→0.834; marginFactor 0→0.6 |
| 2026-04-07 01:40 | 37752209 | event:PerpMarginRequirementsSet | imPerpReq 0.15→0.2 |
| 2026-04-14 21:06 | 38089586 | event:BaseMarginParamsSet | IMScale 0.834→0.75 |
| 2026-05-21 21:38 | 39688948 | event:PerpMarginRequirementsSet | imPerpReq 0.2→0.1; mmPerpReq 0.1→0.08 |
| 2026-08-20 22:09 | 43621075 | event:BaseMarginParamsSet | IMScale 0.75→0.9167 |

**HYPE PM2** (21 entries, `results/p2/params/HYPE_pm2.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2025-10-16 10:29 | 30294479 | start+event:Upgraded+MaxExpiriesUpdated+Initialized | Start |
| 2025-10-16 10:47 | 30295019 | event:ScenariosUpdated | scenarios: grid ±33 %, tails 0→8, 0→33 scenarios |
| 2025-10-16 10:47 | 30295021 | event:BasisContingencyParamsUpdated | basisContAddFactor 0→0.5; basisContMultFactor 0→2; scenarioSpotDown 0→0.9175; scenarioSpotUp 0→1.0825 |
| 2025-10-16 10:47 | 30295023 | event:VolShockParamsUpdated | dteFloor 0→86400; longTermPower 0→0.13; minVolUpShock 0→0.6; shortTermPower 0→0.3; volRangeDown 0→0.3; volRangeUp 0→0.65 |
| 2025-10-16 10:47 | 30295025 | event:OtherContingencyParamsUpdated | IMOptionPercent 0→0.0075; IMPerpPercent 0→0.025; MMOptionPercent 0→0.0175; MMPerpPercent 0→0.075; confMargin 0→0.4; confThreshold 0→0.55; pegLossFactor 0→4; pegLossThreshold 0→0.99 |
| 2025-10-16 10:47 | 30295027 | event:MarginParamsUpdated | imFactor 0→1.15; longBaseStaticDiscount 0→1.02; longRateAddScale 0→0.1; mmFactor 0→0.95; shortBaseStaticDiscount 0→0.98; shortRateAddScale 0→0.1 |
| 2025-10-16 10:47 | 30295028 | event:SkewShockParamsUpdated | absBaseCap 0→0.25; absCBase 0→-0.1; linearBaseCap 0→0.25; linearCBase 0→-0.1; minKStar 0→0.01; volParamStatic 0→0.6; widthScale 0→4 |
| 2025-10-17 04:27 | 30326813 | event:ScenariosUpdated | scenarios: tails 8→7, 33→32 scenarios |
| 2026-01-08 22:50 | 33945517 | event:MarginParamsUpdated | longBaseStaticDiscount 1.02→0.98; shortBaseStaticDiscount 0.98→1.02 |
| 2026-05-08 12:24 | 39110724 | event:BasisContingencyParamsUpdated+OtherContingencyParam… | basisContAddFactor 0.5→0.25; IMOptionPercent 0.0075→0.004; IMPerpPercent 0.025→0.01; MMOptionPercent 0.0175→0.006; MMPerpPercent 0.075→0.05 |
| 2026-05-24 04:05 | 39786946 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0.9175→0.9325; scenarioSpotUp 1.0825→1.0675; imFactor 1.15→1.1; mmFactor 0.95→0.9; IMPerpPercent 0.01→0.015; MMPerpPercent 0.05→0.02; volRangeUp 0.65→0.6; scenarios: grid ±33 %→±27 %, tails 7→8, 32→33 scenarios |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 10→16; Collateral (4 values) |
| 2026-08-20 22:09 | 43621075 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated… | imFactor 1.1→1; mmFactor 0.9→0.8; IMOptionPercent 0.004→0.002; IMPerpPercent 0.015→0.0075; MMOptionPercent 0.006→0.003; MMPerpPercent 0.02→0.01; volRangeUp 0.6→0.5; scenarios: tail dampening changed; Collateral (4 values) |

Plus 8 entries that only change `CollateralParameters` (not USDC, outside K).

**HYPE PM2 override lib 0xf4caea4e521642d9dd2a4751140cc73d78adaa17** (16 entries, `results/p2/params/HYPE_pm2_lib_f4caea4e.json`)

| from (UTC) | Block | Source | Change |
|---|---|---|---|
| 2026-02-03 21:20 | 35066014 | start+event:BasisContingencyParamsUpdated | Start |
| 2026-02-03 21:20 | 35066016 | event:VolShockParamsUpdated | dteFloor 0→86400; longTermPower 0→0.13; minVolUpShock 0→0.6; shortTermPower 0→0.3; volRangeDown 0→0.3; volRangeUp 0→0.65 |
| 2026-02-03 21:20 | 35066018 | event:OtherContingencyParamsUpdated | IMOptionPercent 0→0.0075; IMPerpPercent 0→0.025; MMOptionPercent 0→0.0175; MMPerpPercent 0→0.075; confMargin 0→0.4; confThreshold 0→0.55; pegLossFactor 0→4; pegLossThreshold 0→0.99 |
| 2026-02-03 21:20 | 35066020 | event:MarginParamsUpdated | imFactor 0→1.15; longBaseStaticDiscount 0→0.98; longRateAddScale 0→0.1; mmFactor 0→0.45; shortBaseStaticDiscount 0→1.02; shortRateAddScale 0→0.1 |
| 2026-02-03 21:20 | 35066022 | event:SkewShockParamsUpdated | absBaseCap 0→0.25; absCBase 0→-0.1; linearBaseCap 0→0.25; linearCBase 0→-0.1; minKStar 0→0.01; volParamStatic 0→0.6; widthScale 0→4 |
| 2026-05-08 12:24 | 39110724 | event:BasisContingencyParamsUpdated+OtherContingencyParam… | basisContAddFactor 0.5→0.25; IMOptionPercent 0.0075→0.004; IMPerpPercent 0.025→0.01; MMOptionPercent 0.0175→0.006; MMPerpPercent 0.075→0.05 |
| 2026-05-24 04:05 | 39786946 | event:BasisContingencyParamsUpdated+VolShockParamsUpdated… | scenarioSpotDown 0.9175→0.9325; scenarioSpotUp 1.0825→1.0675; imFactor 1.15→1.1; mmFactor 0.45→0.4; IMPerpPercent 0.01→0.015; MMPerpPercent 0.05→0.02; volRangeUp 0.65→0.6; scenarios: grid ±33 %→±27 %, tails 7→8, 32→33 scenarios |
| 2026-08-13 02:50 | 43283912 | event:MaxExpiriesUpdated | maxExpiries 10→16; Collateral (4 values) |
| 2026-08-20 22:09 | 43621075 | event:VolShockParamsUpdated+OtherContingencyParamsUpdated… | imFactor 1.1→1; IMOptionPercent 0.004→0.002; IMPerpPercent 0.015→0.0075; MMOptionPercent 0.006→0.003; MMPerpPercent 0.02→0.01; volRangeUp 0.6→0.5; scenarios: tail dampening changed; Collateral (4 values) |

Plus 7 entries that only change `CollateralParameters` (not USDC, outside K).

Assignments: 10 events for 10 accounts on 8 days (2026-02-17 to 2026-09-21); revocations: 0.

## A5 Maker holdings (`derive_surface/books.py`)

As of 2026-09-24. Tests `tests/test_p2_books.py` (16, offline; fixtures `tests/fixtures/p2/books_chain_snapshot.json`
with a real Multicall response and `books_subid_api.json` with four responses from `public/get_instrument`).
RPC log `data/p2/logs/A5.jsonl`. Subaccounts appear here only as rank labels M1 to M10 (`derive_surface.p2ids`), raw IDs in
`data/p2/books/top_makers.json`.

**Dominant maker subaccounts** (most maker fills in `data/p1/derived/markouts.parquet`, 603 940 fills). No account
changed its manager during the period.

| Rank | Account | Maker fills | Manager | First snapshot | Days | Median option legs per day |
|---|---|---|---|---|---|---|
| 1 | M1 | 101 791 | PM:ETH | 2024-01-11 | 981 | 71 |
| 2 | M2 | 39 910 | SM | 2024-01-11 | 981 | 20 |
| 3 | M3 | 32 567 | PM2:HYPE | 2025-11-11 | 311 | 182 |
| 4 | M4 | 31 795 | PM:ETH | 2024-12-14 | 643 | 97 |
| 5 | M5 | 30 109 | PM2:ETH | 2025-08-30 | 384 | 187 |
| 6 | M6 | 27 227 | PM:BTC | 2024-01-11 | 981 | 44 |
| 7 | M7 | 22 173 | PM:ETH | 2024-04-16 | 885 | 102 |
| 8 | M8 | 21 707 | PM2:ETH | 2025-09-24 | 359 | 139.5 |
| 9 | M9 | 19 133 | PM:ETH | 2024-01-11 | 981 | 34 |
| 10 | M10 | 16 618 | PM2:ETH | 2025-09-26 | 357 | 197 |

Median of the option legs over days with at least one option.

**Snapshots.** `data/p2/books/snapshots.parquet`: 403 801 rows, 6 863 account days (4 488 with options), every
UTC day from 2024-01-11 to 2026-09-17 at the first block of the day (00:00:01 UTC, blocks 2 454 793 to 44 790 793).
An account appears from the first start of day at which `SubAccounts.manager(id)` is not zero (creation).
Loaded with one `eth_call` per day: Multicall3 (`aggregate3`, code on chain 957 already before block 2 454 793) bundles
`getAccountBalances` and `manager` of all ten accounts; 981 calls plus 5 `cashAsset()` calls, two runs taking
12 min together, resumable through one JSON file per day under `data/p2/books/raw/`. All five managers involved
return the same cash asset `0x57b03e14…` (USDC).

| kind | Rows | Content |
|---|---|---|
| option | 388 734 | ETH 303 916, HYPE 50 764, BTC 34 054 |
| cash | 6 614 | USDC |
| perp | 4 959 | 21 underlyings, most frequent ETH 2 135, HYPE 528, BTC 446 |
| base | 3 247 | ETH, WEETH, FXUSDC, USDT, WSTETH, BTC, SUSDE, DRV |
| none | 247 | account exists, but without holdings (manager stored) |

No asset remained unclassified. Columns as in the plan, plus `balance_raw` (exact 1e18 value as text) and
`manager_label` (`SM`, `PM:BTC`, `PM2:ETH` etc.); `sub_id` as decimal text, because uint96 does not fit into int64.
SubId decoding follows `OptionEncoding.fromSubId`, checked on four instruments against `base_asset_sub_id` of the API
(BTC, ETH, HYPE with strike 38.75): exact.

**Reconciliation of start of day plus fills against the next day.** Holdings at the start of the day plus all tape
fills of the account on that day (maker and taker rows, options on BTC, ETH, HYPE) against the holdings at the next start of day; legs expiring
before the next start of day drop out on both sides; a match means a deviation of at most 1e−9 contracts.
Maker day: an account day with at least one maker fill and a snapshot on the next day (4 300).

| | Maker days | Fully equal | Legs | Legs equal |
|---|---|---|---|---|
| 20 random maker days (seed 20260924) | 20 | 6 (30 %) | 1 362 | 908 (66.7 %) |
| all maker days | 4 300 | 1 713 (39.8 %) | 443 893 | 360 818 (81.3 %) |

Shifting the fill window by 10, 60 or 300 s does not improve anything (1 703, 1 642, 1 439 equal days); a
delay between match and settlement is not the cause. Per account (share of fully equal maker days):
the PM2 accounts M5 99.7 %, M3 98.7 %, M10 96.8 %, but M8 25.4 %; the PM and
SM accounts M7 68.8 %, M6 24.5 %, M1 17.4 %, M4 16.3 %, M2 15.0 %,
M9 8.2 %.

**Cause (on-chain on the same 20 days).** `BalanceAdjusted` events of the SubAccounts per account between the two
snapshot blocks, with transactions outside the tape assigned through their receipt (1 632 receipts; script
`data/p2/books/diag_onchain.py`, result `data/p2/books/diag_onchain.json`):
- Snapshot plus on-chain option postings gives the snapshot of the next day for 1 002 of 1 002 legs. The
  snapshots are exact in themselves.
- Of the option volume moved (sum of the amounts), 57.8 % is in transactions that the tape of the account contains;
  24.6 % is settlement of expired options (transaction with manager events only); 16.4 % are trades through the
  trade module with subaccounts of the same wallet; 1.2 % are trades through the trade module with counterparty accounts that
  do not appear in the tape at all.
- The deviations are therefore transfers between subaccounts of the same operator, executed as trades through the
  trade module (for example M2 with M8, both among the ten). The public trade history, from which
  the tape of Paper 1 comes, does not contain them. There were no liquidations on these days.

**Consequence for B3.** The pre-registered book before the fill (start of day plus tape fills of the day) almost always
matches the actual book of the PM2 accounts M5, M3 and M10, but misses that of the other accounts on many
days. The exact book would be the on-chain book at the block of the fill, from start of day plus `BalanceAdjusted`. The
orchestrator decides on a dated addendum. On the creation day of an account there is no snapshot, because the
account did not yet exist at 00:00 UTC; the book at the start of the day is then empty.

### A5 fix round (2026-09-25)

Changed after the review: `derive_surface/books.py` and `tests/test_p2_books.py` (now 36 tests, 20 of them new,
offline). New fixture `tests/fixtures/p2/books_events_day.json` with real chain data of a PM2 account on
2026-02-13: snapshots at the start of the day and on the next day, 109 `BalanceAdjusted` logs of the day, `getAccountBalances` at the
block before the fill and at the block of the fill. Only `topics[1]` is replaced by the placeholder 4242.

**Timestamp of the book before the fill (fixed).** The report on A5 gave the timestamp for `book_at` as "like
`markouts.ts`". That was wrong: `markouts.ts` is the taker row, and for RFQ fills the maker row is older.
Affected are 62 929 of 343 030 fills of the ten accounts and 41 294 of 101 001 fills (40.9 %) of the four PM2 accounts;
the gap for PM2 is 4.0 s in the median, 90 % below 11.2 s, at most 10.5 min (over all fills at most 28 min). With
`markouts.ts` the fill itself would have landed in the book before the fill. Now:
- `book_at(snapshot_rows, tape_rows, ts, subaccount=None, exclude_trade_ids=None)`: `ts` is the timestamp of the
  account's own tape row, for maker fills therefore `markouts.ts_maker`. A `ts` outside the day of the
  snapshot rows or in seconds raises `ValueError`.
- `book_before_fill(snapshot_rows, tape_rows, trade_id, subaccount=None)` cuts at the account's own row and always leaves out the
  `trade_id` of the fill. For B3 this is the intended call.
- `fill_day(ts_maker)` returns the snapshot day. For 3 fills of the ten accounts the maker day lies before the taker day.
- Fills in the same millisecond stay out, as pre-registered ("earlier timestamp"). This concerns
  further legs of an RFQ multi-leg order and bundled matches: 69 291 of 395 232 tape rows of the ten accounts
  (PM2: 27 303 of 110 617) share account and millisecond with another fill.

**Perps in the pre-registered book.** The tape of Paper 1 contains only options. In the book from start of day plus
tape, perps therefore stay at their start-of-day level. The docstring now says so as well. How often the perp position
(BTC, ETH, HYPE) changes from one start of day to the next is shown by `python3 -m derive_surface.books perp-drift` →
`data/p2/books/perp_drift.json`. Pairs of consecutive days with two snapshots are counted; the change is
the sum of |Δ perp| over the underlyings, in contracts.

| Account | Manager | Day pairs | Pairs with a change | Median change |
|---|---|---|---|---|
| M1 | PM:ETH | 980 | 108 (11.0 %) | 14.1 |
| M2 | SM | 980 | 45 (4.6 %) | 0.39 |
| M3 | PM2:HYPE | 310 | 209 (67.4 %) | 10 456 |
| M4 | PM:ETH | 642 | 8 (1.2 %) | 100 |
| M5 | PM2:ETH | 383 | 60 (15.7 %) | 160 |
| M6 | PM:BTC | 980 | 89 (9.1 %) | 0.40 |
| M7 | PM:ETH | 884 | 298 (33.7 %) | 47.5 |
| M8 | PM2:ETH | 358 | 30 (8.4 %) | 2.9 |
| M9 | PM:ETH | 980 | 0 | 0 |
| M10 | PM2:ETH | 356 | 3 (0.8 %) | 78.7 |

This does not capture perps that are opened and closed again within a day. For the PM2 accounts,
the comparison at the fill (below) measures this.

**Exact on-chain book (new, `books.py` part 2 brought forward).** The decoder from `data/p2/books/diag_onchain.py` is
now in the package, with tests on real logs:
- `decode_balance_adjusted(log)`, `fetch_balance_events(rpc, subaccount, lo, hi)`: `BalanceAdjusted` events of the
  SubAccounts, filtered on `accountId`. The window is halved only when the node reports too many results;
  after sparse windows it grows again. Network errors are not split.
- `load_events(...)` / `compact_events(...)`: per (account, UTC day) the blocks (first block of the day, first block of
  the next day], i.e. exactly the changes between two snapshots. Resumable, one file per account day under
  `data/p2/books/events/`, combined in `data/p2/books/events.parquet` (columns `subaccount, day, block,
  tx_index, log_index, tx_hash, manager, asset, sub_id, amount_raw, pre_raw, post_raw, trade_id, amount, kind, ccy`).
- `replay_balances(snapshot_rows, events, tx_hash=None, include_tx=False)` and `replay_balances_many`: snapshot plus
  events in chain order up to just before (or through) the transaction. The `preBalance` of each event must equal the
  running balance, otherwise `ValueError`. Missing events or a wrong snapshot thus show up immediately.
- `onchain_book_before(snapshot_rows, events, tx_hash, registry=None, ts=None, include_tx=False)` and
  `OnchainBooks(snapshots, events).before(subaccount, tx_hash)` or `.before_many(subaccount, tx_hashes)` return
  `dict[ccy, Book]` with options and perps (expiry cut at the block time, `perp_entry = None`, `cash = 0`). The day
  is the day of the event file that contains the transaction, i.e. the UTC day of the block.

Checks on real data (fixture): snapshot plus all 109 events of the day gives the snapshot of the next day for
all assets exactly to the wei, including cash and the settlement at 08:00. Snapshot plus events up to just before the
fill transaction gives exactly `getAccountBalances` at the block before; through the transaction, exactly the state at the
fill block. The pre-registered book of the same fill deviates, because 24 trades through the trade module are missing.

**Event data of the PM2 accounts.** `python3 -m derive_surface.books events --accounts pm2` (resumable, four
runs of about 9 min each, RPC log `data/p2/logs/A5.jsonl`) loads all 1 168 account days with maker fills of the four
PM2 accounts: 1 994 826 events (cash 1 380 421, perp 483 567, option 130 629, collateral 209), 136 MB. All 101 169
maker rows of these accounts in the tape find their transaction in the events of the day of their maker row. No fill was
settled only after midnight (`data/p2/books/events_coverage.json`). With `verify-events`, on all 1 165
account days with a snapshot on the next day, the snapshot plus the events gives exactly the next day, for all assets and with every
`preBalance` matching (`data/p2/books/events_verify.json`). For the other six accounts no events are loaded;
`--accounts all` fetches them (3 175 further account days).

**Tape book against chain book at the fill (H2 population).** `python3 -m derive_surface.books compare --n 5000` →
`data/p2/books/compare_books.json`: 5 000 random maker fills (seed 20260924) from the 101 001 fills of the four
PM2 accounts in `markouts`. In the underlying of the fill, `book_before_fill` is compared with `OnchainBooks.before`, both
with the expiry cut at `ts_maker`; equal means a deviation of at most 1e−9 contracts per leg.

| Account | Fills | Options equal | Perp equal | Both equal |
|---|---|---|---|---|
| all four | 5 000 | 88.4 % | 70.2 % | 62.2 % |
| M5 (PM2:ETH) | 1 529 | 98.2 % | 83.2 % | 82.2 % |
| M8 (PM2:ETH) | 1 034 | 52.9 % | 85.9 % | 52.0 % |
| M10 (PM2:ETH) | 817 | 97.7 % | 99.0 % | 96.7 % |
| M3 (PM2:HYPE) | 1 620 | 97.0 % | 33.5 % | 32.6 % |

For M8 the option amount at the 90th percentile deviates by 11.3 % (sum of |Δ| over the legs relative to the
gross amount of the chain book). For M3 the perp position of the tape book is off the chain by a median of 3 321 HYPE
contracts (8.1 % of the position). Under PM2 the perp position offsets the option delta. The pre-registered
book therefore biases ΔK mainly for these two accounts; how much, only B3 will show with both books.

**Smaller points.** `fetch_raw` now halves Multicall bundles only on errors of the node (`RpcError`) and passes
network errors through. `diag_onchain.py` uses the package decoder and likewise splits only on `RpcError`. The fixture
`books_chain_snapshot.json` now states the origin of `encoder_reference`: it is a regression reference; the
ABI layout was checked with `eth_abi` in the review. New tests cover `manager_label`, `classify` → `other`, `ts` in
seconds, an account with only a perp and the column `manager_label` in `compact`. A wrong test comment is
corrected.

**Open for the orchestrator.** (1) A dated addendum in `PRAEREGISTRIERUNG.md`: book before the fill = snapshot at the
start of the day plus the `BalanceAdjusted` events of the account up to just before the transaction of the fill (`onchain_book_before`), with
options and perps. The alternative is to keep the pre-registered tape book and to freeze the perps explicitly at
their start-of-day level. (2) The pseudonymisation `sha256(str(id))[:10]` can be reversed at once for small IDs
by enumeration, including for accounts among the ten. For `results/` and the paper a secret salt or rank labels
(M1 to M10) are needed.

## A1 Feed history (`derive_surface/p2feeds.py`)

As of 2026-09-24. All spot, forward, PM2 rate and perp pushes of BTC, ETH and HYPE on chain 957 from the deploy of
the respective feed up to block 44 815 000 (2026-09-17 13:26:55 UTC), plus the static rate feed of the legacy PM,
loaded completely and compacted into one file per feed. The SVI curves come unchanged from `data/p1/volfeed/`.

**Sources.** Addresses from `deploy.json`, `addresses_head.json` and `eth_call` on 2026-09-24, in the code as `FEEDS`
(with the deploy block per feed):

| | Spot | Forward | Rate PM2 | Rate legacy PM | Perp price (`PerpAsset.perpFeed()`) |
|---|---|---|---|---|---|
| BTC | `0x5eb5…fdb0` from 843 075 | `0x958c…6279` from 843 075 | `0x37d2…5461` from 24 712 333 | `0x6fef…004f` | `0x34bc…4475` from 843 076 |
| ETH | `0x727a…d6d5` from 843 059 | `0x791a…f948` from 843 059 | `0x1406…77e3` from 24 712 300 | `0x30a6…9feb` | `0x33e1…d7c6` from 843 059 |
| HYPE | `0x4fde…b143` from 30 293 595 | `0x0f79…b695` from 30 294 426 | `0x1852…0f17` from 30 294 452 | none | `0x947e…503b` from 30 294 378 |

The addresses never changed: `OraclesSet` of the SRM only when the markets were created, `PerpFeedUpdated` and
`SpotFeedUpdated` on the perp asset and the perp feed only at the deploy; the perp feed uses the same spot feed as the
options. `spotDiffCap` has been 0.06 on all three perp feeds since the deploy (the only `SpotDiffCapUpdated`). The
legacy rate feed is a `LyraRateFeedStatic` with a single `RateUpdated(int64,uint64)` at the deploy (rate 0,
confidence 1); `getInterestRate` returns 0 at blocks 3 000 000, 20 000 000 and 44 812 000. Heartbeats at
block 44 812 000: spot 180 s, forward 3 600 s, vol 1 200 s, rate PM2 43 200 s, perp 1 200 s. Multicall3 has code
from about block 1 935 198 (A2) and is used for the cross-check.

**Events** (v2-core `src/interfaces`, topics as keccak of the signature in the code, checked on real logs):
`SpotPriceUpdated(uint96,uint96,uint64)`, `ForwardDataUpdated(uint64 indexed,(int96,uint64,uint64),(uint256,uint256))`,
`RateUpdated(uint64 indexed,int96,uint96,uint64)`, `SpotDiffUpdated(int96,uint96,uint64)` and for the legacy feed
`RateUpdated(int64,uint64)`. Every feed ignores updates with an older or equal signature time without emitting an event, so
the storage after block B is fully determined by the last event up to B.

**Download.** `python3 -m derive_surface.p2feeds sync` in chunks of 250 000 blocks, each chunk written atomically to
`data/p2/feeds/raw/{CCY}/{kind}/`, resumable; the block window per `eth_getLogs` follows the observed
density (target 8 000 logs, node limit 10 000). With `--part k/n` several processes share one feed. Loaded on
2026-09-24 between 20:40 and 21:45 UTC in seven rounds of at most 7 min each with 4 to 14 processes, each at
most 2 requests/s (measured together about 4/s); 10 633 `eth_getLogs`, 6 HTTP 429 responses and one
aborted transfer, all retried with backoff. Log `data/p2/logs/A1.jsonl` (10 740 requests including probes, fixtures and cross-check). Raw data 652 MB.

**Result.** `python3 -m derive_surface.p2feeds compact` writes `data/p2/feeds/{CCY}_{kind}.parquet`, sorted
by (expiry, block, log_index), columns `block, block_ts, log_index, expiry, value, confidence, feed_ts`, for the
forward additionally `fixed`. All files cover the range from the deploy to 44 815 000 without gaps; `block_ts`
agrees with the block formula in all 73 065 073 rows, and `feed_ts ≤ block_ts` holds everywhere.

| Feed | BTC | ETH | HYPE | First push (BTC / ETH / HYPE, UTC) |
|---|---|---|---|---|
| spot | 2 178 655 | 2 188 491 | 1 060 313 | 2023-12-06 05:03 / 2023-12-06 03:13 / 2025-10-24 09:56 |
| forward | 17 240 756 (968 expiries) | 17 253 562 (967) | 5 278 676 (325) | 2023-12-08 23:49 / 2023-12-06 03:13 / 2025-10-24 09:57 |
| rate_pm2 | 9 732 031 (477 expiries) | 9 741 690 (477) | 5 277 930 (325) | 2025-06-12 18:56 / 2025-06-12 18:57 / 2025-10-24 09:57 |
| perp | 1 319 631 | 1 322 389 | 470 947 | 2023-12-06 05:23 / 2023-12-06 03:13 / 2025-10-24 09:57 |
| rate_pm | 1 | 1 | n/a | deploy |
| Size | 314 MB | 314 MB | 114 MB | |

The first PM2 rate push on 2025-06-12 at about 19:00 confirms that the rate feed had been stale until then; the
PM2 window of the pre-registration (from 2025-06-12 23:00 UTC) lies entirely after it.

**Semantics of `FeedHistory`.** For each feed the last push with `block_ts ≤ ts` applies (for fills `ts = ts_ms // 1000`,
which selects exactly the pushes with `block_ts · 1000 ≤ ts_ms`). Forward exactly as in `LyraForwardFeed.getForwardPricePortions`:
variable = current spot + `fwdSpotDifference`; if the forward push was signed less than 30 min before expiry,
the fixed portion (currentSpotAggregate − settlementStartAggregate) / 1800 is added and the variable portion is scaled by
(expiry − signature time) / 1800. Forward confidence = min(forward, spot). Perp = spot + spotDiff, capped at
±0.06 · spot, confidence min(perp, spot). Rate from the PM2 feed per expiry, 0 (confidence 1) without a value; `rate_pm` is
the static legacy rate (0). SVI from `volfeed`, vol exactly as in `LyraVolFeed.getVol`. The age per feed is
`ts − feed_ts` (signature time, the clock of the staleness checks in the contracts); Paper 1 instead measures `svi_age_s_t` from
the push. `state_at` returns `FeedExpiryState` (a subclass of `ExpiryState`) with the fields `fwd_fixed` and
`rate_conf`, which `margin_pm2` and `margin_pm` read; `bulk` returns the same values as columns (plus `perp`,
`spot_conf`, `perp_conf`, `rate_pm`). No value is discarded because of its age.

**Cross-check** (`python3 -m derive_surface.p2feeds crosscheck`, result `data/p2/feeds/crosscheck_{CCY}.json`):
at 10 random blocks per underlying (seed 20260924; BTC and ETH from block 2 454 793, HYPE from the forward deploy plus one day)
`getSpot`, `getForwardPrice` for every expiry with a forward push in the last hour, `getInterestRate` of the PM2 feed
and `getPerpPrice` by `eth_call` via Multicall3 against `state_at`.

| | Calls | Spot | Forward | Rate PM2 | Perp | Confidences equal |
|---|---|---|---|---|---|---|
| BTC | 190 | 10 of 10 exact | 114 of 114 exact | 56 of 56 exact | 9 of 10 exact, rest 1.4e-16 relative | 190 of 190 |
| ETH | 190 | 10 of 10 exact | 114 of 114 exact | 56 of 56 exact | 9 of 10 exact, rest 1.3e-16 relative | 190 of 190 |
| HYPE | 190 | 10 of 10 exact | 85 of 85 exact | 85 of 85 exact | 9 of 10 exact, rest 1.2e-16 relative | 190 of 190 |

No call reverted. In addition, in the settlement window (5 random expiries per underlying, block 10 min before
expiry, `data/p2/feeds/crosscheck_settlement.json`): all 15 forwards in the window have a fixed portion > 0 and
match the chain to within at most 1 ulp (max. relative 2.2e-16), and so do all 189 forwards of these blocks.
The remaining residuals are rounding in the floating-point addition spot + difference; in integer arithmetic
(`forward_portions_int`) the forward in the fixture case agrees bit for bit with `getForwardPricePortions`.

**Performance and comparison with Paper 1.** `FeedHistory(ccy)` with SVI loads BTC in 8 s, ETH in 8 s, HYPE in 2 s (peak
memory of the process about 4 GB with all fills in memory); `bulk` over all 603 940 fills takes 1.0 s in total
(limit 60 s). No fill lacks spot, forward or vol. The vol at the strike agrees exactly with
`iv_mark_t` of Paper 1 for 603 938 fills, and `svi_fwd` likewise with `fwd_t`. The two deviations (ETH, 2024-07-21 and
2024-07-29) come from two SVI pushes for the same expiry in the same block: Paper 1 (`markpath.attach_svi`,
`merge_asof` without ordering by `log_index`) takes the earlier push there, `FeedHistory` the later one, which is what
actually sits in storage after the block. Median spot age at fills 26 to 30 s, forward 46 to 54 s, vol 57 to 62 s,
rate 53 to 60 s. Without a PM2 rate (fills before 2025-06-12) there are 56 164 BTC and 211 533 ETH fills; rate 0 applies there.

**Deviations from the plan.**
- Loaded up to block 44 815 000 instead of 44 812 000: block 44 812 000 is 2026-09-17 11:46:55 UTC and lies before the
  cut at 12:00 UTC (block 44 812 392); the last fill of Paper 1 (11:51:53 UTC) would otherwise lie outside.
- Perp: `value` is `spotDiff` from the event, not the price; as in the contract, the price only arises together with
  the spot at query time. Forward files have the additional column `fixed`.
- `p2chain.Rpc` has `.eth_call` instead of `.call` (it already existed that way); `p2feeds` uses `.raw`.
- In addition to the plan: `FeedExpiryState` with `fwd_fixed`, `rate_conf`; columns `rate_pm`, `perp`, `perp_conf`;
  `FeedHistory(start_ts=, end_ts=, with_svi=)` loads exactly one time window (plus the last value before it per expiry).
- Fixtures under `tests/fixtures/p2/feeds_*.json`, generated with `tests/fixtures/p2/gen_a1_feed_fixtures.py`.
