# Design: Who trades against the maker? Adverse selection on an onchain options CLOB (Derive 2024-2026)

As of: 2026-09-17 · Author: Gregor Albiez (FHNW) · Target: SSRN working paper, 15 to 18 pages, Elsevier CAS two-column, little text, many explanatory figures · Role: scientific groundwork for the market-maker bot (supplies the adverse selection model for the quoting rule).

**Author's decisions (2026-09-17):** core BTC/ETH/HYPE, alts as an appendix · cutoff 2026-09-30 08:00 UTC · pre-registration before the first markout number · inform the Derive team in advance · code, spec, plan and manuscript in the existing repo `gelatotrade/Derive-Option-Surface` (branch `paper1-adverse-selection`), raw data under `data/p1/` (not versioned). The repo is public: internal notes on the data request stay outside it (`Derive_Options/docs/`).

Order as for HIP-4: **pipeline and numbers sheet first, then writing.** Hypotheses H1 to H4 are fixed before the first analysis (`docs/paper1/PREREGISTRATION.md`), extensions afterwards are kept clearly separate.

---

## 1 · Question and contribution

**Question.** How large is a passive maker's loss after an option fill on Derive (markout from 1 min to settlement), which counterparty classes does it come from, and in which cells of the surface (delta × tenor × underlying) does a positive net edge remain after markout, fee, rebate and hedging costs?

**Contribution.**
1. First adverse selection study with **account identity per option fill**: the public Derive tape carries wallet, subaccount_id, rfq_id, fee, rebate and realised P&L. Cartea et al. (toxic flow), Barzykin et al. (adverse selection and price reading) and Albers et al. (fill vs post-fill) are theory or perp experiments without options; Alexander et al. (Deribit) measure buying pressure without identity; the Hyperliquid identity papers concern perps.
2. **Model-free settlement markout** as a control against the circularity of the exchange mark (the mark is a backend SVI that can follow the fills).
3. **Onchain reconstruction of the mark history** from `VolDataUpdated` events (SVI parameters per expiry since 01/2024) as a data contribution in its own right.
4. **Net edge waterfall** per class and cell: half spread − markout − fee + rebate − hedging costs, with the 12.5% fee cap and the maker tiers.

Not part of this paper (later papers): margin polytope, vault roll event study, maker inventory paths, HYPE listing experiment as the main result. HYPE before/after the Deribit listing appears here only as a split in H3.

---

## 2 · Data

| Dataset | Source | Fields | Scope / status |
|---|---|---|---|
| **Option tape** | `public/get_trade_history {instrument_type: option, page_size 1000}` without currency (mixed, paginated), additionally per currency as a cross-check | trade_id, instrument_name, timestamp (ms), trade_price, trade_amount, mark_price, index_price, direction, liquidity_role, wallet, subaccount_id, rfq_id, quote_id, trade_fee, expected_rebate, realized_pnl, realized_pnl_excl_fees, tx_hash, tx_status, extra_fee | since 2024-01-11; BTC 309,273, ETH ~800 k, HYPE ~85 k rows (maker and taker row per fill); **keep both rows**, pairing via tx_hash + instrument + timestamp + amount + price; cutoff **2026-09-30 08:00 UTC** |
| Perp tape (hedging costs, maker detection) | same with `instrument_type: perp` | as above | since launch |
| **Mark path (a)** | mark_price of later fills of the same instrument | | in the tape |
| **Mark path (b)** | Chain: `VolDataUpdated` per currency vol feed (SVI_a, b, ρ, m, σ, fwd, refTau, confidence, timestamp), `ForwardDataUpdated`, `SpotPriceUpdated`; feed addresses from `v2-core/deployments/957/<CCY>.json` and its Git history | | `eth_getLogs` on rpc.derive.xyz, windows ≤ 2,000 blocks (limit 10,000 logs), topic0 filter; cross-check against `get_latest_signed_feeds` |
| **Settlement** | `get_option_settlement_prices {currency}`; `get_option_settlement_history` (P&L per subaccount) | expiry, price; subaccount_id, amount, settlement_pnl | 944 BTC expiries; 254,986 BTC rows |
| External reference | Tardis Deribit `options_chain` on the 1st of each month 2024-2026 (free); DVOL history | mark_iv, bid_iv, ask_iv per series | 33 snapshot dates; check HYPE_USDC |
| Book mids (pilot) | live recording 2026-09-03 (1.9 h, all options every 20 s) and recorder weeks from deployment onwards | bid, ask, bid_iv, ask_iv | pilot; recorder as an extension |
| **Classification** | vault contracts (help.derive.xyz "Vault Smart Contracts", `get_vault_statistics`) → vault subaccounts via `AccountCreated`; `get_liquidation_history` (83 auctions, tx_hash, bids); `get_maker_program_scores` per epoch (wallets in the MM programme); rfq_id in the tape | | table wallet/subaccount → class |
| Fees, rebates | trade_fee, expected_rebate per fill; `get_instrument` (maker_fee_rate, taker_fee_rate, base_fee, mark_price_fee_rate_cap); institutional tiers (help.derive) | | |
| Hedging costs | `get_funding_rate_history` (30 d rolling, collect from now on), perp tape, recorder perp book | | |

Underlyings: **BTC, ETH, HYPE as the core** (full surface pipeline available); the nine others (SOL, XRP, ZEC, ADA, XAUT, CC, VVV, LIT, PUMP) only as a descriptive appendix table (fills, RFQ share, mean markout), without a surface.

Preservation: pull the tape and the chain logs completely **right away** and store them as Parquet with a manifest (SHA-256, row count, retrieval time) before v3 changes fields.

---

### 2a · Findings from the data probe of 2026-09-17 (these take precedence over anything earlier)

| Finding | Consequence |
|---|---|
| `get_trade_history` returns the rows of a page **not in chronological order** (a page of 1,000 is unsorted); paging across large ranges can skip or duplicate rows | download in time windows that fit on **one** page (recursive halving per day); one call per window |
| `from_timestamp` and `to_timestamp` are **both inclusive** (count[a,m−1] + count[m,b] = count[a,b], verified) | window [a, b], the next one from b+1 |
| Total number of option rows across all underlyings about 1.23 million (retrievable without the `currency` parameter); **first fill 2023-12-06 03:13 UTC** (1,402 rows before 2024-01-01) | one pass for all underlyings from 2023-12-01; sample per the pre-registration unchanged from 2024-01-11 |
| The API's `count` value is **not additive** over long ranges (61 days: 16 rows fewer than the sum of the halves); daily counts match the delivered rows exactly | integrity check by recounting every day; days that deviate are reloaded; the CLI writes nothing as long as any day deviates |
| Rows can appear long after their timestamp: for RFQ fills the maker row lies a median of 3 s, at the 99th percentile 75 s and at most 1,689 s (28 min) before the taker row; for book fills both are the same | the cutoff must be ≥ 60 min in the past; cached windows are reused only if they were loaded ≥ 60 min after the window end; final run no earlier than 2026-09-30 09:00 UTC |
| Maker and taker rows carry the same `trade_id`; for RFQ fills the maker timestamp lies a few seconds **before** the taker timestamp (quote vs execution) | fill time = taker timestamp; maker time as a separate column |
| Perp tape: BTC 2.04 million, ETH 3.56 million, HYPE 1.47 million rows | **not** loaded for Paper 1 (hedging costs from the fee formula, recorder spread, funding); belongs to Paper 3 |
| Vol feed addresses per underlying identified via `SVI_fwd` against the live forward: BTC `0x3883…1b87`, ETH `0xb27c…d160` (both **unchanged since 01/2024**; the address change suspected in R4 was a mix-up of the BTC and ETH feeds), HYPE `0x4819…12d1` (active between block 30.0 million and 31.38 million, i.e. around the HYPE launch on 2025-11-10); in addition SOL `0x7423`, ZEC `0x52aa`, XAUT `0x665b`, XRP `0xbf2e`, VVV `0x8df0`, ADA `0xe7b5`, CC `0x6a0d`, LIT `0xc9b3`, PUMP `0x0105`, inactive `0xd38b` (presumably AAVE) | feed table in the code; continuity checked by sampling |
| Every `VolDataUpdated` log carries `blockTimestamp`; in the example the curve lands onchain 45 s after its signature (`feed_ts`) | both times are stored (`feed_ts`, `block_ts`); the pre-registration speaks of the curve "pushed onchain" → `block_ts` |
| Formula check 2026-09-17: `svi_vol` on the latest signed curve (`get_latest_signed_feeds`, 12 s old) matches the ticker mark IV to 0.00001 at the median (BTC shortest expiry 0.00125); the curve last pushed **onchain** was 3 to 4 min old and deviated by 0.004 to 0.023 at the median | path (b) is a mark delayed by minutes, above all for the 1 and 5 min horizons; carry the curve age per horizon, path (a) as the counterpart; mention in the limitations |
| In parallel with the BTC core feed, a second address (`0x533a…de1e`) emitted curves with a BTC-like forward (about 1% lower) in 03-06/2024 | check the mark cross-check at fill time for these months (DATA_STATUS) |
| Event density ~0.5 `VolDataUpdated` per block for BTC and ETH (less at the start of 2024), ~0.35 for HYPE → roughly **38 million events** for the three core underlyings; RPC limit of 10,000 logs per `eth_getLogs` (error −32005) | adaptive block windows, 50,000-block chunks, resumable, background run; full resolution, stored compactly (parameters float32, forward float64); **only 15 GB free** |
| `SVI.sol` (lyra-utils): k = ln(K/SVI_fwd), bounded to ±4·√(a + b·σ); w = a + b·(ρ(k−m) + √((k−m)² + σ²)), capped at 144; **vol = √(w / SVI_refTau)** with the reference tau of the fit, not the running time to expiry | mark IV reconstruction exactly by this formula; cross-check against the live ticker |
| `get_liquidation_history` without a time filter covers only the **last 7 days**; `count`/`num_pages` only say whether another page follows; some windows fail reproducibly with HTTP 500 at page size 100 but work with small pages; very long windows return fewer auctions than the sum of short ones | daily windows, page size 100 with fallback to 20 and 5, halving down to 1 h on total failure, remaining gaps are reported. All page sizes return the same auctions, but the bids incompletely (2025-10-10: 242 auctions, 34 bids at size 100, 4 at size 5); complete bids only from the chain events (`DutchAuction`). The earlier statement "83 or 76 liquidations since launch" came from the 7-day default window; in fact there are thousands |
| Vault wallets: the help centre page "Vault Smart Contracts" lists 202 addresses (bridges, connectors, TSA tokens on several chains); 15 mainnet tokens on Derive Chain, 10 of them trading vaults, matching one to one the 10 vaults from `get_vault_statistics`; combined TVL only about 1.6 million USD (2026-09-17) | curated list `docs/paper1/meta/vault_wallets.csv` with the source per address, cross-check against the wallets in the tape; the low power of H2 is reported in DATA_STATUS |
| Maker programmes (DRV scores) exist only from 2024-11-20 | the class "MM programme" cannot be assigned before this date; report in DATA_STATUS |
| `get_settlement_history` per subaccount (BTC 254,986 rows) | not needed for Paper 1 (the settlement markout needs only the price per expiry) |
| System Python 3.9.6; the repo requires ≥ 3.10 in `pyproject.toml`, but all 28 tests run under 3.9 | no installation, invocation via `python3 -m derive_surface` from the repo; new code 3.9-compatible (`from __future__ import annotations`, no `match`) |

## 3 · Definitions

For each fill at time t with price P, quantity q and maker direction s ∈ {+1 maker buys, −1 maker sells}:

- **Markout in USDC per contract:** MO_τ = s · (M(t+τ) − P), M = mark price at time t+τ from path (a) or (b). Horizons τ ∈ {1 min, 5 min, 30 min, 4 h, 24 h, settlement}. Negative = loss for the maker.
- **Delta-neutral markout:** MO^Δ_τ = MO_τ − s · Δ(t) · (S(t+τ) − S(t)), Δ from the mark IV at fill time (Black-76 on the forward), S = index. Removes the spot move; the remainder is vol and skew movement.
- **Markout in vol points:** MO^σ_τ = s · (IV_mark(t+τ) − IV_fill(t)), both via Black-76 inversion (existing pipeline from Derive-Option-Surface, bid/ask IV match < 1e-4 verified).
- **Settlement markout:** MO_set = s · (payoff at expiry − P), model-free. **VRP-adjusted:** MO_set minus the mean of MO_set over all fills in the same cell (delta bucket × tenor bucket × underlying × calendar month), so that the premium that every position in the cell carries drops out (robustness: DVOL-based expectation).
- **Effective half spread:** HS = s_taker · (P − M(t)) with s_taker = −s (positive when the taker trades worse than the mark), in USDC and vol points.
- **Maker's net edge:** NE_τ = HS + MO_τ − fee_maker + rebate_maker − hedge, hedge = perp half spread + taker fee + expected funding over τ, weighted by delta per fill.
- **Cells:** delta buckets |Δ| ∈ {0-10, 10-25, 25-40, 40-60 (ATM), 60-75, 75-90, 90-100}; tenor ∈ {≤ 2 d, 2-7 d, 7-30 d, 30-90 d, > 90 d}; underlying.
- **Exclusions:** fills in the last 30 min before expiry (settlement TWAP window, cockpit `FEED_TWAP_SEC`), `tx_status ≠ settled`, instruments without a forward.
- **Counterparty classes (taker side):** vault · RFQ · liquidation · dominant maker as taker (wallet with a maker share ≥ 80% and ≥ 1% of maker volume) · MM programme wallet · large wallet (≥ p99 of notional, otherwise unclassified) · retail/other. Assignment per wallet and month; the table is published (pseudonymised).
- **Sweep:** ≥ 5 fills by the same taker in ≤ 10 s across ≥ 3 strikes.

---

## 4 · Hypotheses (pre-registration before the first analysis)

| | Hypothesis | Rejected if |
|---|---|---|
| H1 | Toxicity is concentrated: the 10 taker wallets with the largest maker loss account for > 50% of the aggregate negative markout (30 min); fills > p90 in size and sweeps have a significantly more negative markout than small fills | the bootstrap 90% band of the top-10 share excludes 50% from below; or the size effect has cluster-robust (wallet) \|t\| < 1.96 |
| H2 | Vault rolls are uninformed flow: VRP-adjusted settlement markout and 30 min markout of vault fills ≥ 0 for the maker | the 95% interval of the vault markout lies entirely below 0 |
| H3 | HYPE was more toxic before the Deribit listing (2026-06-16, verify the date) than afterwards and than BTC/ETH (vol markout) | the before/after difference (DiD against BTC/ETH, placebo dates) is not significant or has the wrong sign |
| H4 | Net edge depends on the cell: at 30 min, NE is positive in fewer than half of the populated cells; short-dated ATM BTC/ETH negative, wings and long tenors positive | share of positive cells ≥ 50% or short-dated ATM positive (bootstrap per cell) |

Secondary findings without pre-registration (clearly marked as exploratory): markout by time of day, by book vs RFQ, VPIN as a comparison measure, inventory-conditioned markout of the dominant makers (placebo permutation), fill finality (share reverted, match→settlement time).

---

## 5 · Methodology

1. **Panel regression:** MO_τ (three units) on class × size class × delta bucket, fixed effects instrument × day, clusters on the taker wallet; wild cluster bootstrap as in HIP-4 (`inference.py` pattern, cluster correction G/(G−1)).
2. **Variance decomposition** within/between wallet; **Lorenz curve** of toxicity (cumulative share of taker wallets vs cumulative maker loss).
3. **Placebo:** classes randomly permuted (1,000 draws) → distribution of the class effect under the null.
4. **Robustness of the mark path:** (a) later fill marks, (b) onchain SVI, (c) settlement, (d) Deribit snapshot dates: results must agree in sign and order of magnitude; table in the appendix.
5. **Multiple wallets:** sensitivity when wallets with an identical time/instrument pattern are merged (report the concentration as a lower bound).
6. **Net edge:** per cell with a bootstrap band; fee from trade_fee (cap visible as a step), rebate from expected_rebate, tier scenarios (standard, tier 4, tier 1).

---

## 6 · Figures (theory first, then empirics)

| # | Figure | Shows |
|---|---|---|
| T1 | Mechanics of the markout: one fill, three mark paths (fill marks, onchain SVI, settlement), three units (USDC, delta-neutral, vol) | the definition without formulas |
| T2 | Net edge decomposition as a waterfall schematic with the 12.5% fee cap and tier rebates | why wings and ATM work out differently |
| 1 | Markout fan across the horizon (1 min … settlement), book vs RFQ, BTC/ETH/HYPE, three units stacked | main finding and vol vs spot decomposition |
| 2 | Heatmap delta × tenor of the mean 30 min markout in vol points, next to it in bp of notional | where the maker loses |
| 3 | Lorenz curve of toxicity, segments vault / RFQ / liquidation / large wallet / other coloured | H1, H2 |
| 4 | Net edge waterfall per class (half spread, markout, fee, rebate, hedge) | H4 |
| 5 | Daily toxicity 2024-2026 with events: FalconX 10/2025, HYPE listing 06/2026, record month 03/2026, vault roll days | H3, time structure |
| A | Appendix: robustness of the four mark paths; class table; alt underlyings | |

---

## 7 · Pipeline and storage

Everything in the repo `Derive-Option-Surface` (locally under `~/Documents/Papers/Working Papers/Derive_Options/Derive-Option-Surface`), branch `paper1-adverse-selection`:

```
derive_surface/
  fulltape.py      option tape with all 20 fields, both rows per fill, single-page windows, manifest         (Plan 1)
  chainfeeds.py    VolDataUpdated per feed, adaptive block windows, decoding, SVI vol per SVI.sol            (Plan 1)
  refdata.py       settlement prices, liquidations, maker programmes and scores, vaults, fees, funding       (Plan 1)
  classify.py      maker/taker pairing, wallet-month metrics, counterparty classes                           (Plan 1)
  p1cli.py         python3 -m derive_surface p1 tape|volfeed|compact|ref|fills                               (Plan 1)
  markouts.py      mark paths a/b/c/d, three units, cells, exclusions                                        (Plan 2)
  inference_p1.py  regressions, wild cluster bootstrap, placebo, Lorenz, net edge                            (Plan 2)
  figures_p1.py    T1, T2, 1-5, A                                                                            (Plan 3)
scripts/p1_check_feeds.py   feed continuity and cross-check of SVI vs live mark                              (Plan 1)
docs/paper1/     PREREGISTRATION.md, DATA_STATUS.md, NUMBERS.md, meta/vault_wallets.csv
paper/           CAS manuscript (Plan 4)
data/p1/         raw/, tape/, volfeed/, ref/, derived/  (git-ignored)
tests/           offline; test_p1_*.py
```

- Use pricing (Black-76, IV inversion, forward delta) directly from `derive_surface.pricing`.
- Every analysis as a script, every number in the numbers sheet with script and date (lesson from HIP-4: the dominance code was lost three times).
- Long runs (chain logs, tape) resumable, with `caffeinate` on mains power or on the VPS.

---

## 8 · Schedule (5 to 6 weeks)

| Week | Step | Result |
|---|---|---|
| 1 | Secure option tape + chain feeds + reference data; class table; pre-registration H1 to H4 (perps dropped, see §2a) | manifest, class statistics, `PREREGISTRATION.md` |
| 2 | Markouts in three units, four mark paths; descriptive statistics; theory figures T1/T2 | numbers sheet v1, Figs. T1, T2, 1, 2 |
| 3 | Inference (regressions, bootstrap, placebo), net edge, robustness, alt appendix | numbers sheet v2, Figs. 3-5, A |
| 4 | Writing (CAS, hard size targets per section, ≤ 18 pages), refs.bib with verified sources only | manuscript v1 |
| 5 | Two independent reviewers (numbers, text), revisions, inform the team, SSRN sheet | upload version |

---

## 9 · Risks and limits

- **Mark circularity:** the backend SVI can follow its own fills → settlement markout and Deribit snapshot dates as independent paths; report results only where the paths agree.
- **Multiple wallets:** concentration is a lower bound; sensitivity with merging.
- **Heuristic classes:** vault and RFQ hard (contracts, rfq_id), institution/retail soft; a class table from the team would replace this but is not required.
- **Rebate tier per wallet unknown:** expected_rebate per fill is observed; tier scenarios for the net edge.
- **v3 migration:** fields and events may change → secure the data now, cutoff 2026-09-30.
- **Ethics:** wallets are public, the paper shows only pseudonymous clusters ("Taker-A"); inform the Derive team before publication; Deribit snapshot dates only in aggregate (ToS "personal use").
- **Statistical power:** BTC/ETH ample (> 1 million rows); HYPE thin, H3 only with placebo dates and DiD.

---

## 10 · Decisions (confirmed by the author on 2026-09-17)

1. Core BTC/ETH/HYPE, the rest as an appendix.
2. Cutoff 2026-09-30 08:00 UTC; until then pilot data up to 2026-09-17 12:00 UTC only for building the pipeline, **no markouts**.
3. The pre-registration of H1 to H4 (`docs/paper1/PREREGISTRATION.md`) is committed before any markout number exists.
4. The Derive team is informed in advance (form).
5. The existing repo `gelatotrade/Derive-Option-Surface`, as far as possible.

Implementation in plans: Plan 1 data basis and classes (`docs/superpowers/plans/2026-09-17-p1-data.md`), Plan 2 markouts and inference, Plan 3 figures, Plan 4 manuscript.
