# Paper 2: Master Plan (Capital-Adjusted Edge) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** From the fills of Paper 1 and an offline replica of the three Derive margin managers, compute the capital per fill, the marginal cost in real maker books, the netting value and the dose of parameter changes, test H1 to H4, build nine figures and write the manuscript.

**Architecture:** New focused modules in the package `derive_surface` (prefix `p2`/`margin_`) that talk to each other through the types from `derive_surface/p2types.py` (exists). Data under `data/p2/` (git-ignored), results under `results/p2/`, manuscript under `paper2/`. Execution runs in stages A to G; within a stage, agents work in parallel on disjoint files, and the orchestrator commits after each stage.

**Tech Stack:** Python 3.9.6 (system), numpy, pandas, pyarrow, requests, scipy, matplotlib; pytest; tectonic for LaTeX. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-24-p2-capital-design.md` · **Pre-registration:** `docs/paper2/PRAEREGISTRIERUNG.md` (commit `1d13227`) · **Semantics:** `docs/paper2/get_margin_semantics.md`.

## Global Constraints

- Python 3.9.6: every new file starts with `from __future__ import annotations`; no `match`, no `X | Y` types outside annotations.
- No new dependencies. Tests offline, no network; `python3 -m pytest -q` must be green after every stage (currently: 154 tests).
- Calls from the repo root directory `~/Documents/Papers/Finished Papers/Derive_Options/Derive-Option-Surface`.
- Data only under `data/p2/` (git-ignored). Results (small) under `results/p2/`. Delete nothing that was not created in this session.
- RPC `https://rpc.lyra.finance` (chain 957) at most 2 requests/s per process; API `https://api.lyra.finance` at most 2 requests/s, set a User-Agent. Every request with a timestamp into a JSONL log under `data/p2/logs/`.
- Block time: `block = 2_454_793 + (ts − 1_704_931_201) // 2` (exactly 2 s per block; block 2 454 793 = 2024-01-11 00:00:01 UTC). Cross-check against `volfeed` (`block`, `block_ts`).
- Code, comments and commit messages in English; documents under `docs/paper2/` in German with umlauts, no em or en dashes in running text.
- Agents do not commit; the orchestrator commits after each stage.
- Maker subaccounts and wallets in `results/` only as `sha256(str(id))[:10]`.
- Reference sources: v2-core under `data/p2/v2-core/` (commit `96796a6`), prototypes under `data/p2/semantik_20260924/` and `data/p2/kontext/`, addresses in `data/p2/kontext/margin-historie/deploy.json` and `addresses_head.json`.
- No value from the pre-registration is changed. Deviations only as a dated addendum in `docs/paper2/PRAEREGISTRIERUNG.md`.

## Files

| File | Responsibility | Stage |
|---|---|---|
| `derive_surface/p2types.py` | types (exists) | n/a |
| `derive_surface/p2chain.py` | RPC client (eth_call, adaptive getLogs, log), block time | A1 |
| `derive_surface/p2feeds.py` | load and compact feed events; `FeedHistory` with `state_at` and `bulk_state` | A1 |
| `derive_surface/p2params.py` | parameter timelines per underlying and manager | A2 |
| `derive_surface/margin_pm2.py` | replica of `PMRMLib_2` | A3 |
| `derive_surface/margin_sm.py`, `derive_surface/margin_pm.py` | replica of `StandardManager` and the legacy `PMRMLib` | A4 |
| `derive_surface/books.py` | holdings of the maker subaccounts, decoding, book before the fill | A5, B3 |
| `derive_surface/p2validate.py` | replica against `eth_call` | B1 |
| `derive_surface/capital.py` | capital per fill | B2 |
| `derive_surface/p2events.py` | events, doses, H4 panel | B4 |
| `derive_surface/p2surface.py` | SVI → Surface, capital surface, animation | B5 |
| `derive_surface/inference_p2.py` | H1 to H4, sensitivities | C |
| `derive_surface/figdata_p2.py`, `derive_surface/figures_p2.py` | figures | D |
| `derive_surface/p2cli.py`, `derive_surface/__main__.py` | CLI `python3 -m derive_surface p2 …` | orchestrator after A |
| `scripts/p2_build.py`, `scripts/p2_wordcount.py`, `scripts/p2_numbers.py`, `scripts/p2_figure_check.py`, `scripts/p2_number_check.py` | check chain | C, D, E |
| `paper2/main.tex`, `paper2/refs.bib`, `paper2/figures/` | manuscript | E |
| `docs/paper2/NUMBERS.md`, `FIGURE_CHECKS.md`, `VALIDATION.md`, `DATA_STATUS.md`, `AUDIT.md` | documentation | B to F |

---

## Stage A: Foundations (parallel, disjoint files)

### Task A1: Chain client and feed history

**Files:** Create `derive_surface/p2chain.py`, `derive_surface/p2feeds.py`, `tests/test_p2_chain.py`, `tests/test_p2_feeds.py`, `tests/fixtures/p2/` (real logs as JSON).

**Interfaces:**
- Consumes: `derive_surface.p2types.MarketState`, `ExpiryState`; `derive_surface.chainfeeds.svi_vol`, the `load_feed` pattern; SVI history `data/p1/volfeed/{CCY}_svi_YYYY-MM.parquet` (columns `block, block_ts, log_index, expiry, feed_ts, svi_a, svi_b, svi_rho, svi_m, svi_sigma, svi_fwd, svi_ref_tau, confidence`).
- Produces:
  - `p2chain.block_at_ts(ts: int) -> int`, `p2chain.ts_at_block(block: int) -> int` (formula from Global Constraints).
  - `p2chain.Rpc(url=..., rate=2.0, log_path=...)` with `.call(to, data, block) -> bytes`, `.logs(address, topic0, lo, hi) -> list[dict]` (adaptive windows, limit 10 000 logs).
  - `p2feeds.FEEDS[ccy]` = dict with the addresses `spot`, `forward`, `vol`, `rate_pm2`, `rate_pm`, `perp` (from `deploy.json`/`addresses_head.json`; HYPE addresses from the chain).
  - `p2feeds.sync(ccy, kind, to_block)` loads `SpotPriceUpdated`, `ForwardDataUpdated`, `RateUpdated` (PM2 rate feed) and the perp price feed in chunks into `data/p2/feeds/raw/{ccy}/{kind}/`, `p2feeds.compact(ccy, kind)` writes `data/p2/feeds/{ccy}_{kind}.parquet` with columns `block, block_ts, log_index, expiry, value, confidence, feed_ts` (spot/perp: `expiry = 0`, `value` = price; forward: `value` = `fwdSpotDifference`; rate: `value` = rate as float).
  - `p2feeds.FeedHistory(ccy)` with `.state_at(ts: int, expiries: list[int]) -> MarketState` (for each feed the last value with `block_ts ≤ ts`; forward = spot + `fwdSpotDifference` exactly as in `LyraForwardFeed.getForwardPricePortions`; SVI from `volfeed`; rate from `rate_pm2`, 0 if there is no value) and `.bulk(ts: np.ndarray, expiry: np.ndarray, strike: np.ndarray) -> pd.DataFrame` with columns `spot, forward, sigma, rate, svi_fwd, vol_conf, fwd_conf, spot_age, fwd_age, vol_age, rate_age` (vectorised via `np.searchsorted` per expiry).

- [ ] **Step 1:** Read the event ABIs from `data/p2/v2-core/src/interfaces/ILyraSpotFeed.sol:17`, `ILyraForwardFeed.sol:26`, `ILyraRateFeed.sol:17` and the perp feed; compute the topics as keccak of the signatures and store them in the code as constants with a comment. Fetch real example logs of each kind with a single `eth_getLogs` and save them as a fixture.
- [ ] **Step 2: Failing tests:** decoding of each fixture log into the expected fields; `block_at_ts(1_704_931_201) == 2_454_793`; `state_at` on a synthetic mini history (three spot values, two forward values, one SVI curve) returns the last value ≤ ts in each case and forward = spot + difference; `bulk` matches `state_at` row by row.
- [ ] **Step 3:** Implement, tests green.
- [ ] **Step 4: Load data** for BTC, ETH, HYPE from block 843 000 (BTC/ETH) or from the HYPE deploy up to block 44 812 000 (2026-09-17 12:00 UTC + buffer): spot, forward, rate_pm2 (from the PM2 deploy), perp. Resumable. Result and row counts in `docs/paper2/DATA_STATUS.md` (section Feeds).
- [ ] **Step 5: Cross-check:** at 10 random blocks per underlying, `getSpot`/`getForwardPrice`/`getInterestRate` by `eth_call` against `state_at` (deviation 0 expected); result in `DATA_STATUS.md`.

### Task A2: Parameter timelines

**Files:** Create `derive_surface/p2params.py`, `tests/test_p2_params.py`, `results/p2/params/{ccy}_{mgr}.json` (mgr ∈ `sm`, `pm`, `pm2`).

**Interfaces:**
- Consumes: `p2chain.Rpc` (task A1; until then a minimal client of its own is allowed, switch over afterwards), event lists `data/p2/kontext/margin-historie/events.json`, `data/p2/semantik_20260924/code-pm2/param_timeline_btc.json`, getter signatures from v2-core (`IPMRMLib_2`, `IPMRMLib`, `IStandardManager`, `PMRM_2`, `PMRM`).
- Produces: JSON list `[{"from_block": int, "from_ts": int, "source": str, "params": {...}}]` per (underlying, manager), ascending. **Keys = Solidity struct names and field names exactly as in v2-core**, values as float (1e18 scaling reversed), e.g. PM2: `{"VolShockParameters": {...}, "MarginParameters": {...}, "BasisContingencyParameters": {...}, "OtherContingencyParameters": {...}, "SkewShockParameters": {...}, "CollateralParameters": {...}, "scenarios": [{"spotShock": .., "volShock": 0|1|2, "dampeningFactor": ..}, ...], "maxExpiries": int}`; SM (market ID per underlying: BTC 2, ETH 1, HYPE 48): `{"OptionMarginParams": {...}, "PerpMarginRequirements": {...}, "BaseMarginParams": {...}, "OracleContingencyParams": {...}, "DepegParams": {...}}`; legacy PM like the `IPMRMLib` structs plus `scenarios`. `p2params.Timeline(ccy, mgr).at(ts) -> dict` and `.changes() -> list[int]`.

- [ ] **Step 1: Failing tests:** `Timeline.at` selects the last entry with `from_ts ≤ ts`; before the first entry `KeyError`; a JSON round trip keeps all keys.
- [ ] **Step 2:** Implement, tests green.
- [ ] **Step 3: Load:** at each event block (PM2: all `*ParamsUpdated`, `ScenariosUpdated`, `MaxExpiriesUpdated` of the standard lib and the manager; SM: `OptionMarginParamsSet` etc. per market; legacy PM: monthly samples of the getters plus bisection as in `data/p2/kontext/margin-historie/oi_legacy.py`), read all getters by historical `eth_call` at the event block. Caution: in the SM event `OptionMarginParamsSet`, unpairedIM/MM are swapped, so always read the getter, never the event.
- [ ] **Step 4:** Table of the changes per underlying and manager in `docs/paper2/DATA_STATUS.md` (section Parameters), plus the monthly manager shares of OI from `oi_legacy.json` into `results/p2/manager_oi_share.csv` (columns `month, ccy, sm, pm, pm2`).

### Task A3: Replica of PM2

**Files:** Create `derive_surface/margin_pm2.py`, `tests/test_p2_margin_pm2.py`, `tests/fixtures/p2/pm2_chain_cases.json`.

**Interfaces:**
- Consumes: `p2types.Book`, `MarketState`; parameter dict in the schema from task A2; reference implementations `data/p2/semantik_20260924/verify-konvex/pm2v.py` (vectorised, chain-exact) and `code-pm2/pm2_replica.py`; Solidity `data/p2/v2-core/src/risk-managers/PMRMLib_2.sol`, `PMRM_2.sol`.
- Produces:
  - `margin_pm2.net_margin(book, state, params, is_initial=True) -> tuple[float, float]` = (net, mtm), net = cash + V − R, mtm = cash + V.
  - `margin_pm2.single(arrays: dict, params, is_initial=True) -> tuple[np.ndarray, np.ndarray]` for many single-contract books; `arrays` has the keys `spot, forward, sigma, tau, rate, strike, is_call, amount, vol_conf, fwd_conf, spot_conf` (1-D arrays of equal length). Vol shocks act multiplicatively on `sigma` at the strike.
  - `margin_pm2.requirement(book, state, params, is_initial=True) -> float` = mtm − net.

- [ ] **Step 1: Failing tests:** all 139 reference cases `data/p2/v2-core/test/risk-managers/unit-tests/PMRM_2/portfolio_cases/*.json` (relative error ≤ 1e-9 against the IM/MM expected in the case; reading logic as in `pm2_replica.py`); at least 10 chain cases with real feeds, parameters and the `eth_call` result as a fixture (from `data/p2/semantik_20260924/verify-konvex/rep_vs_chain.json` or newly generated), tolerance 1e-6 USD; `single` equal to `net_margin` for 200 random contracts.
- [ ] **Step 2:** Port `pm2v.py` into the schema of the parameter dicts; tests green.

### Task A4: Replica of SM and legacy PM

**Files:** Create `derive_surface/margin_sm.py`, `derive_surface/margin_pm.py`, `tests/test_p2_margin_sm.py`, `tests/test_p2_margin_pm.py`, fixtures under `tests/fixtures/p2/`.

**Interfaces:**
- Consumes: as A3; references `data/p2/semantik_20260924/verify-widerspruch/engine.py`, `code-sm/sm_model.py`, Solidity `StandardManager.sol`, `PMRMLib.sol`, `PMRM.sol`; reference cases `data/p2/v2-core/test/risk-managers/unit-tests/StandardManager/test-cases.json`, `test-cases-portfolio.json`, `.../PMRM/test-cases-portfolio-pm.json`, `.../PMRM/utils/*.json`.
- Produces: `margin_sm.net_margin(book, state, params, is_initial=True)`, `margin_sm.single(arrays, params, is_initial=True)`, `margin_pm.net_margin(...)`, `margin_pm.single(...)` with the same signature as A3. SM computes the option MtM undiscounted (Black-76, D = 1); the legacy PM likewise without discount.

- [ ] **Step 1: Failing tests:** SM reference cases from v2-core (IM and MM), legacy PM reference cases, at least 10 chain cases each with `eth_call` (`SRM.getIsolatedMargin`, `getMarginAndMarkToMarket` of the legacy PM with the lib call as in `data/p2/semantik_20260924/code-pm2/oracle_legacy.py`), `single` equal to `net_margin`.
- [ ] **Step 2:** Implement, tests green. SM: isolated, max loss per expiry on the grid {0} ∪ strikes plus unpaired calls, `max(I_e, L_e)`, perp, base; legacy PM: scenarios ±spot × vol, contingencies, `imFactor` on minSPAN.

### Task A5: Maker holdings

**Files:** Create `derive_surface/books.py` (part 1), `tests/test_p2_books.py`, `data/p2/books/snapshots.parquet`.

**Interfaces:**
- Consumes: `p2chain.Rpc` (a minimal client of its own until A1 is finished), `data/p1/derived/markouts.parquet` (columns `maker_sub`, `ts`, …), `data/p1/tape/{CCY}_options_full.parquet`, v2-core `SubAccounts.sol` (`getAccountBalances`, `manager`), `OptionEncoding.sol` (subId decoding).
- Produces:
  - `books.top_maker_subaccounts(n=10) -> list[int]` (most maker fills in the Paper 1 sample).
  - `books.decode_option_subid(sub_id: int) -> tuple[int, float, bool]` (expiry, strike, is_call) exactly as `OptionEncoding`.
  - `books.snapshot(rpc, subaccount: int, block: int) -> list[dict]` with `asset, sub_id, balance, kind ∈ {option, perp, cash, base}, ccy, expiry, strike, is_call` and `manager`.
  - `data/p2/books/snapshots.parquet` with columns `subaccount, day, block, manager, asset, sub_id, kind, ccy, expiry, strike, is_call, amount` for the ten subaccounts, every UTC day from 2024-01-11 to 2026-09-17 (first block of the day).
  - `books.book_at(snapshot_rows, tape_rows, ts) -> dict[ccy, Book]` (start of the day plus the fills of the day before ts, expired options removed, perps with entry price = None).

- [ ] **Step 1: Failing tests:** subId decoding on three real instruments (from the tape: instrument name ↔ `sub_id` of the positions API or the chain); `book_at` on synthetic data (holdings at the start of the day + two fills, one of them a taker row, one expired leg).
- [ ] **Step 2:** Implement, tests green.
- [ ] **Step 3: Load** the snapshots (about 10 × 980 days = 9 800 calls plus `manager`), resumable; accounts without holdings on a day produce no rows, but the manager is stored anyway (`kind = "none"`).
- [ ] **Step 4:** Reconciliation on 20 random maker days: holdings at the start of the day + fills of the day = holdings of the next day (deviations = transfers, liquidations, settlement) as a rate in `DATA_STATUS.md`.

**Orchestrator after stage A:** wire up the CLI `p2` with its subcommands, suite green, commit.

---

## Stage B: Measurement (only after validation B1 has passed)

### Task B1: Validation against eth_call

**Files:** Create `derive_surface/p2validate.py`, `tests/test_p2_validate.py`, `results/p2/validation.csv`, `docs/paper2/VALIDATION.md`.

**Interfaces:** Consumes A1 to A5. Produces `validation.csv` with `ccy, manager, kind ∈ {single, book}, block, ts, K_replica, K_chain, abs_err, rel_err, is_initial`.

- [ ] For each underlying and available manager at least 48 random blocks in the respective window (seed 20260924), per block one random contract from the active expiries with a vol push in the last 20 min (strike from the tape of the day), random side; capital K by the replica (`FeedHistory.state_at` + parameters) against `eth_call` at the lib or at the manager with the same positions (chain oracle as in `data/p2/semantik_20260924/code-pm2/oracle.py`, SM via `getIsolatedMargin`, legacy PM as in `oracle_legacy.py`). In addition 20 maker days (books) under PM2.
- [ ] Check the threshold from the pre-registration (median |rel| < 0.1 %, p95 < 1 %). Result in `VALIDATION.md`. If it is missed, find and fix the cause; if it cannot be fixed, write a dated addendum in the pre-registration before B2 starts.

### Task B2: Capital per fill

**Files:** Create `derive_surface/capital.py`, `tests/test_p2_capital.py`, `data/p2/derived/capital.parquet`.

**Interfaces:** Consumes `markouts.parquet` (columns `trade_id` or fill key, `ts`, `currency`, `expiry`, `strike`, `option_type`, `price`, `amount`, `maker_side`, `index_price`, `delta_bucket`, `tenor_bucket`, `abs_delta_pct`), `FeedHistory.bulk`, `Timeline.at`, `margin_*.single`. Produces `capital.parquet` with the fill key and `K_sm, K_pm, K_pm2, K_sm_mm, K_pm_mm, K_pm2_mm` (NaN outside the manager window), `spot, forward, sigma, rate, vol_age, fwd_age`.

- [ ] Failing tests: K = p·q − net for three hand-computed cases per manager (SM short call, SM long = premium, PM2 against `net_margin`); window boundaries (PM2 NaN before 2025-06-12 23:00 UTC, HYPE SM NaN before 2025-11-11, HYPE PM always NaN).
- [ ] Implement (grouped by underlying and parameter regime, vectorised), run over all 603 940 fills, row count and NaN shares in `DATA_STATUS.md`.

### Task B3: Marginal cost and netting value

**Files:** Modify `derive_surface/books.py` (part 2), `tests/test_p2_books.py`; Create `data/p2/derived/marginal.parquet`, `data/p2/derived/maker_days.parquet`.

**Interfaces:** Consumes A1 to A5 and B2. Produces `marginal.parquet` (`fill_key, subaccount_hash, ts, ccy, manager, dK, K_single_pm2, ratio`) for the pre-registered sample (account under PM2 at the start of the day, PM2 window, random selection of 20 000, seed 20260924) and `maker_days.parquet` (`subaccount_hash, day, K_sm, K_pm, K_pm2, K_*_mm, n_legs, gross_contracts, manager`).

- [ ] Failing tests: ΔK = p·q_new + net(before) − net(after) on a synthetic book; a maker day with two underlyings computes PM2 separately per underlying; legs without an open PM2 window drop out.
- [ ] In addition (sensitivity for the time normalisation): empirical holding time per cell from the daily holdings (FIFO close-out of the maker fills of the ten subaccounts, median per cell) into `results/p2/holding_time.csv`.
- [ ] Implement and run.

### Task B4: Events and doses (H4)

**Files:** Create `derive_surface/p2events.py`, `tests/test_p2_events.py`, `results/p2/events.csv`, `data/p2/derived/h4_panel.parquet`.

**Interfaces:** Consumes `Timeline.changes`, `capital.parquet`, `markouts.parquet` (half spread `hs`, or from `inference_p1.analysis_frame`), `FeedHistory`, `margin_*.single`. Produces `events.csv` (`ccy, manager, event_ts, kinds, max_abs_dose, kept`) and the panel (`fill_key, ccy, cell, event_id, post, dose, y_hs_bp, day`).

- [ ] Failing tests: merging of events on the same day; dose log(K_nach/K_vor) (after/before the event) on a synthetic example; window logic without the event day; exclusion if max |dose| < 1 %.
- [ ] Implement and run.

### Task B5: Surface and capital surface

**Files:** Create `derive_surface/p2surface.py`, `tests/test_p2_surface.py`.

**Interfaces:** Consumes `surface.py` (`Surface`, `greeks_grid`), `animate.py` (`Renderer`), `FeedHistory.state_at`, `margin_*.single`, prototype `data/p2/kontext/oberflaeche/proto_chain_surface.py`. Produces `p2surface.chain_surface(ccy, ts) -> Surface` (SVI curves of one point in time, adapter like `ChainSmile`), `p2surface.capital_grid(ccy, ts, manager, side) -> pd.DataFrame` (call Δ × tenor grid with `iv, strike, K_per_forward_bp`), `p2surface.render_frame(...)` and `p2surface.animate(ccy, days, out)` (GIF/MP4 as in `docs/media`, palette from `figstyle`).

- [ ] Failing tests: `chain_surface` returns the `svi_vol` values at the nodes; `capital_grid` capital of an SM short = a·S by the formula; delta self-consistency.
- [ ] `p2surface.reference_book_series(ccy) -> pd.DataFrame`: capital of a fixed reference book (ATM short straddle with 30 days to expiry, 1 contract per leg, constructed every day at 08:00 UTC from the expiry closest to 30 days) per day under SM, legacy PM and PM2, plus the same book with the parameters of the previous day (pure parameter effect) into `results/p2/reference_book.csv`.
- [ ] Implement.

**Orchestrator after stage B:** suite green, commit.

---

## Stage C: Inference

### Task C1: H1 to H4 and sensitivities

**Files:** Create `derive_surface/inference_p2.py`, `tests/test_p2_inference.py`, `scripts/p2_numbers.py`, `results/p2/h1_cells.csv`, `h1.json`, `h2.json`, `h3.json`, `h4.json`, `h4_placebo.csv`, `sensitivity.json`, `summary.json`, `docs/paper2/NUMBERS.md`.

**Interfaces:** Consumes `capital.parquet`, `marginal.parquet`, `maker_days.parquet`, `h4_panel.parquet`, `inference_p1.analysis_frame` and the bootstrap helpers from `inference_p1` (`cluster_mean_ci`, `wild_cluster_mean_p`). Produces the files listed; every verdict as `{"stat": .., "lo": .., "hi": .., "rejected": bool, "rule": ".."}`.

- [ ] Failing tests: cell ratio of sums; ρ bootstrap on synthetic data with known ρ; median bootstrap; DiD estimator against brute-force OLS with fixed effects on a mini panel; wild bootstrap p for a known signal < 0.05 and uniformly distributed for a null signal (rough test).
- [ ] Implement and run (B = 9 999, seed 20260924). Exploratory results separately in `sensitivity.json`: maps under SM and legacy PM, MM, API semantics (2 %, today only), time normalisations, values per underlying.
- [ ] `scripts/p2_numbers.py` writes `docs/paper2/NUMBERS.md` from `results/p2` (cut-off date taken from the data, not hard-coded).

---

## Stage D: Figures

### Task D1: Drafts, jury, build

**Files:** Create `derive_surface/figdata_p2.py`, `derive_surface/figures_p2.py`, `tests/test_p2_figures.py`, `scripts/p2_figure_check.py`, `paper2/figures/*.pdf|png`, `docs/paper2/FIGURE_CHECKS.md`, `docs/paper2/FIGURE_SELECTION.md`, `docs/media/p2_*.gif`.

- [ ] Three independent draft sets (mechanism, empirics, practitioner) for the slots of spec §6, a jury of referee (recalculation) and design (8 pt, greyscale), gap check; choice in `FIGURE_SELECTION.md`.
- [ ] Registry `FIGURES` as in `figures_p1.py`; every number of a figure as a table under `results/p2/fig_*.csv`; no font below 7 pt (a test checks `fontsize` of all text objects ≥ 7); greyscale test (luminance distance between the categories).
- [ ] `p2_figure_check.py` compares figure numbers against `results/p2` (not against themselves).
- [ ] Surface T1 and animation via `p2surface`; social cards 1600×900.

---

## Stage E: Manuscript

### Task E1: Text, literature, build

**Files:** Create `paper2/main.tex`, `paper2/refs.bib`, `scripts/p2_build.py`, `scripts/p2_wordcount.py`, `scripts/p2_number_check.py`, `docs/paper2/MANUSCRIPT.md`.

- [ ] Outline and word budget from spec §7; `p2_wordcount.py` with a budget per section (±10 %).
- [ ] Literature: only sources with a verified DOI or publisher page (one web agent), list with verification notes in `MANUSCRIPT.md`.
- [ ] `p2_number_check.py`: every number in the text must occur in `results/p2` (rounding allowed, explicit list of exceptions).
- [ ] Build with tectonic, check the log, overfull boxes, budget. Name the pre-registration commit `1d13227` in the text.

---

## Stage F: Audit

### Task F1: Audit of the entire paper

- [ ] In parallel: numbers (text ↔ results ↔ raw data), code review (correctness of the replicas and of the inference), fidelity to the pre-registration (every deviation as an addendum?), figures (rules, readability), literature (DOIs), language (no em or en dashes, budget). Findings by severity in `docs/paper2/AUDIT.md`, work the corrections in, check again.
