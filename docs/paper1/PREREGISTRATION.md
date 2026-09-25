# Pre-registration, Paper 1: Adverse Selection on Derive

> English translation of docs/paper1/PRAEREGISTRIERUNG.md, made on 25 September 2026. The German original is binding; its history, including commit 3fd9caa, is the record. Files renamed on 25 September 2026 appear here under their new names; the German original keeps the old ones.

Fixed on 17 September 2026, before any markout number was computed. The Git commit of this file is the timestamp. Changes after that only as a dated addendum at the end, never by overwriting.

## Sample
- Fills (pair of maker and taker row of the same `trade_id`) on BTC, ETH and HYPE options with a taker timestamp in [2024-01-11 00:00, 2026-09-30 08:00] UTC.
- Exclusions: `tx_status` ≠ `settled`; pairs with a differing price, a differing amount or the same direction; fills in the last 30 minutes before expiry; fills without mark path (b) at the time of the fill.
- The nine remaining underlyings only descriptively in the appendix.

## Markout
- Maker direction s = +1 if the maker buys, otherwise −1. MO_τ = s · (M(t+τ) − P) in USDC per contract; negative = loss for the maker.
- Primary mark path (b): Black-76 price from the SVI curve of the expiry last pushed on chain before t+τ (formula as in `SVI.sol`, vol = √(w/SVI_refTau)), forward from the same curve (`SVI_fwd`), discount factor 1.
- Robustness: (a) `mark_price` of the next fill of the same instrument after t+τ; (c) settlement payout; (d) Deribit mark on the first days of the month available from Tardis.
- Units: USDC; delta-neutral MO^Δ_τ = MO_τ − s·Δ(t)·(S(t+τ) − S(t)) with Δ from path (b) and S = `index_price` of the fill or `SVI_fwd` at time t+τ, respectively; vol points MO^σ_τ = s·(IV_(b)(t+τ) − IV_fill(t)).
- Horizons: 1 min, 5 min, 30 min, 4 h, 24 h, settlement. **Primary horizon 30 min.**
- VRP adjustment of the settlement markout: subtraction of the mean settlement markout of all fills in the same cell (delta bucket × tenor bucket × underlying × calendar month).

## Cells and classes
- |Δ| buckets: [0,10), [10,25), [25,40), [40,60), [60,75), [75,90), [90,100]. Tenor: ≤2 d, (2,7], (7,30], (30,90], >90 d.
- Taker class, in order of precedence: liquidation (tx_hash of a liquidation auction) > vault (wallet in `docs/paper1/meta/vault_wallets.csv`) > RFQ (`rfq_id` set) > dominant maker (wallet-month with a maker share ≥ 80 % of its own notional and ≥ 1 % of the month's maker notional) > MM programme (wallet with `total_score` > 0 in an options programme epoch that contains the fill) > large wallet (taker notional of the month ≥ 99th percentile of the month's taker wallets) > other.
- Sweep: ≥ 5 fills by the same taker in ≤ 10 s across ≥ 3 strikes.

## Hypotheses and rejection rules
- **H1 Concentration:** The 10 taker wallets with the largest aggregate negative 30-min markout (USDC) carry more than 50 % of it; fills above the 90th percentile of size and sweep fills have a more negative markout than the rest. Rejected if the upper bound of the 90 % bootstrap interval (resampling over taker wallets, B = 9,999) of the top-10 share lies below 50 %, or if the size or sweep coefficient in the panel regression (FE instrument × day, clustered by taker wallet) is not negative with |t| ≥ 1.96.
- **H2 Vault flow uninformed:** Mean 30-min markout (b) of the vault taker fills ≥ 0 for the maker. Rejected if the 95 % wild cluster bootstrap interval lies entirely below 0. Secondary: the same test for the VRP-adjusted settlement markout.
- **H3 HYPE before the reference market:** The 30-min vol markout of HYPE was more negative before the Deribit listing of the HYPE_USDC options than after it, relative to BTC/ETH (difference-in-differences, clustered by taker wallet). Event date: first trading day of the HYPE_USDC options on Deribit according to the official announcement; if it cannot be found, the first day with HYPE_USDC options data at Tardis. Rejected if the DiD coefficient does not have the expected sign with |t| ≥ 1.96, or if it does not lie in the outermost 5 % among 100 random placebo dates (same window length, before the listing).
- **H4 Cell-dependent net edge:** The net edge NE_30min = half spread + MO_30min − maker fee + maker rebate − hedging costs is positive in fewer than half of the occupied cells (≥ 200 fills), and negative in the cell BTC/ETH × [40,60) × ≤2 d. Rejected if ≥ 50 % of the occupied cells have a positive 90 % bootstrap interval or the named cell has a positive interval.

## Inference
- Wild cluster bootstrap (Rademacher), clustered by taker wallet, B = 9,999, seed 20260917, small-sample correction G/(G−1), p = (1 + #)/(B + 1).
- Everything else (time of day, VPIN, inventory-conditioned markout, fill finality) is exploratory and is labelled as such.

## Data status before this commit
- Pilot data up to 17 September 2026 12:00 UTC may be loaded, paired and classified in order to build the pipeline. Markouts are computed only after this commit.

## Addendum 1 (17 September 2026, before the first markout computation)

1. **Delta-neutral markout:** S(t) and S(t+τ) are both the forward (`SVI_fwd`) of the SVI curve valid at the respective time. The original wording ("`index_price` of the fill or `SVI_fwd` at time t+τ, respectively") would have carried the basis between index and forward, up to several 100 bp at long maturities, into the markout.
2. **Data beyond the cutoff date:** Tape and SVI history are loaded up to 1 October 2026 09:00 UTC (cutoff + 25 h), so that fills in the last 24 h before the cutoff receive all horizons. The sample remains limited to taker timestamps ≤ 30 September 2026 08:00 UTC. Settlement markouts exist only for expiries up to the end of the loaded data; a horizon that reaches or passes the expiry is not defined for path (b).
3. **Start of the tape:** The tape begins on 6 December 2023; the sample begins, unchanged, on 11 January 2024.
4. **Path (a):** Mark of the first fill of the same instrument with a timestamp ≥ t+τ; the distance to the target time is stored as well, so that analyses can be restricted to nearby fills (e.g. ≤ 10 % of τ or ≤ 5 min).
5. **Sweeps** are determined per (taker wallet, underlying): a fill belongs to a sweep if a 10-s window starting at a fill of the same taker contains at least 5 fills across at least 3 strikes and the fill lies within it.
6. **Size feature:** "above the 90th percentile of size" refers to the notional (amount × index) within the underlying across the whole sample.

## Addendum 2 (18 September 2026, before the first inference)

1. **Event date H3:** HYPE_USDC **options** launched on Deribit on **23 June 2026 09:00 UTC** (official announcement "HYPE Derivatives Launching On Deribit", published 16 June 2026: perp 16 June 09:00 UTC, options and dated futures 23 June 09:00 UTC). The date noted earlier, 16 June 2026, was the launch of the perp. Deribit's delivery price history covers only 100 days and is not suitable for dating.
2. **Net edge, decomposition without double counting:** The half spread is part of the markout. HS = s·(M(t) − P) (markout at horizon 0), adverse selection AS_τ = s·(M(t+τ) − M(t)) and MO_τ = HS + AS_τ. The net edge is therefore NE_τ = MO_τ − maker fee + maker rebate − hedging costs, with the **observed** fees and rebates of the maker row from the tape. Hedging costs = |Δ(t)|·F(t)·(perp taker fee 0.03 % + assumed perp half spread) + |Δ(t)|·F(t)·funding rate per hour·(τ/3600 s); the perp half spread is set at 1 bp and reported with 0 bp and 3 bp as a sensitivity, and the funding rate is the median of the absolute hourly value over the last 30 days per underlying.
3. **H1 metric:** For each taker wallet w, S_w = Σ MO_30min (USDC, path b). L = Σ_{w: S_w < 0} S_w is the aggregate loss of the maker. The top-10 share is the sum of the ten smallest (most negative) S_w divided by L. The 90 % interval comes from a cluster bootstrap over wallets (B = 9,999, seed 20260917).
4. **Intervals for means:** For means (H2, cells in H4) the reported interval is the percentile interval of a cluster bootstrap over taker wallets; in addition, the p-value of the wild cluster bootstrap against zero is reported. For regression coefficients (H1, H3) the wild cluster bootstrap applies (restricted residuals, Rademacher).
5. **Exclusion without a fill IV:** Fills whose price lies outside the Black-76 arbitrage bounds and for which therefore no fill IV exists (pilot: 10,745 of 603,940) do not enter the tests in vol points; in USDC and delta-neutral they remain included. The number is reported for each test.
6. **The class "liquidation" is empty:** Liquidations are settled outside the trade tape (27,694 auctions, no match on an options fill). The class analysis runs over the six remaining classes.

## Addendum 3 (25 September 2026, after the first version of 19 September 2026)

1. **Unit of fee and rebate in the net edge:** In the tape, `trade_fee` and `expected_rebate` of the maker row are sums over the whole fill (in the order book the maker fee is mostly amount · min(rate · index, 12.5 % · mark), in RFQ it is not; in both cases it grows with the amount), whereas markout and hedging costs are per contract. The definition from addendum 2, item 2, is therefore implemented with fee and rebate per contract: NE_τ = MO_τ − (maker fee − maker rebate) / amount − hedging costs, in USDC per contract; the edge of the whole fill is NE_τ · amount. A fill without a positive amount has no net edge (none in the pilot). The first version subtracted the sums of the fill from the markout per contract; that is the same only for one contract.
2. **Net edge in bp of notional (exploratory, figure F5 and card S5):** 10⁴ · NE_τ / index, equal to the edge of the fill divided by its notional (amount · index). The first version divided the value per contract by the notional of the whole fill. Likewise, the markout as a share of the premium (figures F1c and F2c) is formed per contract: markout per contract / price.
3. **RFQ packages:** In multi-leg RFQs, Derive almost always books the maker fee of the package on exactly one leg (pilot: of 4,996 packages with more than one leg and a maker fee, 4,511 on exactly one leg; there are no rebates in RFQ). Fee / amount places it on the leg on which it is booked. The distribution across the package (Σ fee / Σ amount per `rfq_id` and maker wallet) is reported as a sensitivity: `results/p1_finding/fee_units.csv`, section `rfq_package`, and a sentence in section 3 of the manuscript.
4. **Discovery and cause:** The unit issue came to light on 25 September 2026 while Paper 2 was being built, that is, after the first version and with knowledge of its pilot results. The test of the first version checked the net edge only with fills of amount 1. Finding, recomputation and the numbers of both forms: `docs/paper1/FINDING_2026-09-25_FEE_UNITS.md`, `scripts/p1_fee_units_finding.py`, `results/p1_finding/` (the old form as variant `p1`, where it remains traceable as a comparison).
5. **Unchanged:** hypotheses H1 to H4, rejection rules and thresholds, sample and pilot cut (17 September 2026 12:00 UTC), horizon, hedging assumptions, bootstrap (B = 9,999, seed 20260917). Only the unit in which the registered definition is implemented has changed. The reference of the pre-registration remains commit `3fd9caa`.
