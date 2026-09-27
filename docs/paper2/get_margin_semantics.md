# Semantics of `public/get_margin`

Status 24 September 2026, 10:49 to 12:21 UTC. Applies to BTC on the production v2 host `api.lyra.finance`.
It rests on five investigating agents and six adversarial reviewers with about 9,800 logged requests to the API
and to chain 957 in total, plus the contract code `derivexyz/v2-core` at commit `96796a6` and the documentation at
docs.derive.xyz. Raw data are under `data/p2/semantik_20260924/` (not in git), small tables under
`results/p2/semantics/`.

All numbers are exploration, not a pre-registered measurement. For the paper they are collected again with tested
code under an experimental design.

## 1. Short answer

**What does the method return?** For X ∈ {IM, MM} it returns net margin:

    net_X(q; C) = C + V_eng(q) − R_X(q)

Here C is the collateral value, V_eng the market value of the positions as the manager values them, and R_X the
requirement. Positive means covered. The documentation calls the values "net margin" and explains them as
"mark-to-market value minus the requirement".

**pre versus post.** `pre_*` is `net` for `simulated_positions` and `simulated_collaterals`. `post_*` is the same
state after `simulated_position_changes` and `simulated_collateral_changes` have been added. Without changes the
two are equal up to 1 to 2 ULP. Within one request both use the same price state. Between two requests, by
contrast, `pre` drifts by a few USD to more than 1,000 USD depending on the book: 23 USD for a test book one
second apart, up to 1,903 USD in 0.6 s for large perp books.

**Role of `simulated_collaterals`.** USDC enters additively with a slope of exactly 1, also when negative. C
therefore has no effect on R, but it shifts `net` 1:1 and so decides admissibility. Other collaterals enter with a
haircut. Under PM2, BTC held next to positions reduces risk and enters nonlinearly (with a short call: first BTC
+72,315 USD, second +60,133 USD); without positions it enters linearly.

**Comparable quantity.** The requirement is not `C − net`, because that is R − V and mixes position value and
margin. The primary recommendation is the capital measure

    K_p(q) = Σ_options p_i·q_i − net_IM(q; C = 0)

It gives the deposit needed to open the book q at prices p and meet the IM. K_p needs no V, only the trade prices
p, and can be read directly from one request. Its marginal form for an order Δq comes from a single request:
positions = q, changes = Δq, collateral_changes USDC = −p·Δq. Then ΔK = −(post − pre).

## 2. What else belongs to the response

| Item | Finding |
|---|---|
| `entry_price` | acts only on perps and shifts `net` by −q·Δentry. For options it has no effect, not even at 0 or 10·mark |
| Perps in changes | are added together with their entry basis; the entry price is weighted by amount. On closing, the realised PnL stays in `post` |
| Perps in Σ p·q | do not belong there, because a perp has no premium. Otherwise an error of q·p arises |
| Errors | duplicate in one of the four lists: −32602, even with amount 0. Missing required field: −32602; an empty list `[]` is allowed. BTC below zero: 11020 |
| `market` | SM ignores it. PM2 requires it; a different currency gives 10015 |
| `margin_type` | `PM` is the legacy PMRM and not an alias. It requires 1.6 to 3.5 times as much as PM2 and accepts only USDC. Use only SM and PM2 for the paper |
| `is_valid_trade` | is not usable as an admissibility indicator. 27 of 82 constructed cases contradict the rule first derived; all 82 fit only a rule adjusted afterwards that depends on ΔR and pre_MM. Two SM requests with the same pattern (pre == post, IM < 0 < MM) give different verdicts. Admissible means `post_initial_margin ≥ 0` |
| Open-order margin | not included, according to the documentation |
| Size | R is exactly positively homogeneous of degree 1, from k = 1e−4 to 1e7 under SM, PM and PM2. The method does not check OI caps or order limits |
| Account limit | SM on v2: at most 63 options plus cash; 64 gives 10007. PM2 accepts at least 262 positions |
| Instrument list | `get_instruments` is not reproducible: 814 entries at 09:23 UTC, 820 at 11:20 UTC. It contains 126 inactive instruments. `get_margin` values such instruments anyway, shown for 10 of them (expiry 29 September). Archive lists and tickers for each measurement |

## 3. Why `C − net` is not enough, and what V is

From the response, `C − net = R − V`. For a short book of deep in-the-money options, the premium value |V| sits
inside it and masks the requirement. An example under PM2: for the short BTC-20261030-110000-P the on-chain oracle
gives `C − net` = 38,082 USD (API: 38,086 USD), of which 26,060 USD is position value and only 12,022 USD
requirement. When two managers are compared via `C − net`, a large |V| pushes the ratio towards 1.

Under SM, long options receive no isolated credit; a pure long book gives exactly `net = C`. They act only through
the max-loss branch within the same expiry, for example in spreads. Under PM2, by contrast, their value counts. In
K_p the long premium under SM therefore mostly appears in full as tied-up capital. That is economically correct, but
the paper should say so explicitly.

**The engine requirement R_eng = C + V_eng − net** needs V exactly as the manager computes it. That is not the
ticker `mark_price`:

| Engine | Discount D in V = D·B76(F, K, σ, τ) |
|---|---|
| SM on v2 | D = 1, so V = M·F/S |
| PM2 on v2 (`api.lyra.finance`) | D = e^(−0.02·τ), a flat rate of 2 % that is documented nowhere |
| PM2 on-chain and PM2/SM on v3 | D = e^(−r_feed·τ), with r_feed 3.64 to 3.82 % from `LyraRateFeed` |
| Ticker | D = S/F from the basis. `mark_price` is rounded to 1 USD; exactly, M = −rho/τ |

Two reviewers measured the 2 % rate independently with box spreads: one over all 14 expiries with
|r − 0.02| ≤ 3e−7 (`results/p2/semantics/box_discount.json`, repeated at 11:44 UTC), the other over 9 expiries with
|r − 0.02| < 1e−8 (`data/p2/semantik_20260924/verify-mtm/box_api.json`). The error made by taking ticker marks
instead of V_eng grows roughly with (b − r_Engine)·τ·V:

| Tenor | 8 d | 36 d | 92 d | 183 d | 274 d | 1 y |
|---|---|---|---|---|---|---|
| SM v2 | +0.16 % | +0.48 % | +1.22 % | +2.60 % | +3.96 % | +5.33 % |
| PM2 v2 | +0.12 % | +0.28 % | +0.71 % | +1.58 % | +2.39 % | +3.25 % |

Median per tenor. Source: `results/p2/semantics/v_convention.json`, 24 options at 11:22 UTC.

K_p − R_eng = Σ p·q − V_eng. The difference between the two is therefore a valuation convention, not capital. This
makes K_p the better denominator for "edge per margin", while R_eng is the better quantity for the geometry of the
engine itself.

**Live probe of K_p** (12:21 UTC, `results/p2/semantics/capital_measure_check.jsonl`): a book with four legs is opened
with deposit K and premium flow at the mark. This gives `net_IM` = −0.88 USD (SM, K = 48,963 USD) and −6.73 USD
(PM2, K = 15,215 USD). The marginal form via pre/post matches K(q+Δ) − K(q) to within 0.88 and 9.17 USD
respectively. The remainder is price drift between separate requests.

## 4. The contradiction 11 versus 1.2 is resolved

Both original scripts were found in old session logs. The two measurements used **different books** and both read
the requirement as `C − net`. Both books were rebuilt and recomputed at the historical block.

| | 17 September, 10:45 UTC | 24 September, 09:25 UTC |
|---|---|---|
| Expiries | 25 September, 30 October, 27 November, 25 December 2026, 26 March 2027 (8 d to 6 m) | the first five by date, 25 to 29 September (at most 5 d) |
| Strikes | per expiry the 10 closest to the index, OTM side | every (n/10)-th instrument per expiry. On 25 September from 20,000 to 420,000 with deep ITM wings, on 26 to 29 September from 70,000 to 95,000 |
| Case B | strictly alternating by strike | random signs, `random.seed(7)` |
| Manager | PM2 and SM | PM2 and SM (not legacy PM) |
| Factor SM/PM2 on `C − net`, A / B | 2.33 / 11.86 | 1.46 / 1.19 |
| Factor SM/PM2 on R_eng, A / B | 3.19 / 10.76 | 3.61 / 2.14 |

IM, in chain semantics at the respective block (PM2 via eth_call with the feed rate, SM via the offline engine with
D = 1). The difference from the API semantics is small for these books. The rebuild matches the original numbers to
within 374 USD. Source: `results/p2/semantics/factors.csv`.

The gap in case B (11.86 versus 1.19) has two causes:

1. **The book.** On R_eng, 10.76 versus 2.14 remain. In the live crossover experiment (11.69 versus 2.12), the
   choice of instruments explains about three quarters of the gap (log), the sign pattern about one quarter. With
   the signs of 24 September, the exact book of 17 September falls from 11.7 to 4.5.
2. **The mixing with V.** It roughly doubles the gap, from 5.0 on R_eng to 10.0 on `C − net`. The book of
   24 September had V ≈ −497,000 USD.

A parameter change is ruled out. All 33 parameter getters of SM, PM, PM2 and both libs return byte-identical values
at both blocks. In between there were only two `LibOverrideUpdated` events, each for a single account.

Case A, by contrast, shows no contradiction (3.19 versus 3.61). The statement "netting about 11×" holds on R for a
mixed book near the money across several tenors, today 11.7× on the exact book of 17 September. It is not a
constant, however; it depends strongly on the book.

## 5. Two engines and a shadow host

| | Off-chain v2 (`api.lyra.finance`) | On-chain (chain 957) | v3 (`api.derive.xyz/v3`) |
|---|---|---|---|
| Status | production: UI and trades run through it | settlement, liquidation and auctions | shadow operation: hourly snapshot of v2, no trades |
| PM2 discount | flat 2 % | rate feed 3.64 to 3.82 % | rate feed |
| Prices | fresh (ticker) | feeds lag behind, spot by up to about 42 USD, forward by up to about 74 USD | fresh |
| Used for | IM and account view (`margin_watch` agrees with `get_margin` except for interest and uPnL, checked on 2 accounts) | MM for liquidation (DutchAuction.sol:163 to 166), with the account lib | nothing productive |

Three particulars matter for the paper:

1. **Override libs.** Since 17 February 2026, 15 accounts have one by one received their own lib via
   `LibOverrideUpdated`, with mmFactor 0.35 instead of 0.8, the last two on 21 September 2026. This applies
   on-chain. For the checked account Xcaa362b31b, `margin_watch` showed the standard MM.
2. **Weak on-chain check.** A trusted risk assessor checks only 3 spot scenarios plus basis and contingencies
   on-chain. That is 5 to 34 % of the full R_IM. That the exchange enforces the full IM off-chain is plausible, but
   not shown.
3. **Divergent documentation.** The documentation describes v3 (put requirement at the strike, four skew rails, a
   vol floor that according to the table applies only to up and according to the worked example also to down,
   `STATIC_RATE 0.05`). It cannot be cited for v2; for v2 the code and the on-chain parameters apply.

API and on-chain oracle therefore do not agree in general. Over 30 random books, |API − oracle| for IM had a median
of about 265 USD (0.15 % of R_IM), a p90 of 10,800 to 15,600 USD depending on the quantile method, and a maximum of
207,000 USD (5.3 %). The difference is small as long as tenors are short or a regular scenario binds a short-heavy
book. Then D cancels out, because δ⁻ = 1/D.

## 6. Properties for the geometry

- **Cone.** R is positively homogeneous of degree 1. The admissible set {q : K_p(q) ≤ E} scales linearly with the
  deposit E. There is no absolute "breaking point" in size in `get_margin`. One can only arise in relative terms,
  as a kink along a ray q + tΔ, or come from outside: capital, OI caps, account limits, open-order margin,
  liquidity.
- **SM is not convex.** Per expiry, R_e = min(R_isolated, R_MaxLoss), written in the contract as the max of the
  negative margins. Across expiries the terms are added. This gives a union of up to 2^E polyhedra. Confirmed live,
  for example, is a subadditivity gap of +9,959 USD IM for December puts. With a deposit of 24,916 USDC, both ends
  of the tested segment are admissible and its middle is not.
- **PM2 is convex in practice, strictly speaking not.** R_PM2 is convex as long as no skew scenario binds in which
  the expiry sum M_e changes sign. The cause is the term |f(M_skew) − M| with a kink in the static discount. In
  14,500 midpoint tests on natural random books no violation occurred. In constructed books dominated by box
  spreads, violations reached up to 1,284 USD live (13 to 18 % of R at the midpoint). The bound is
  ½·Σ_e Δ_e·min|M_skew,e| with Δ_e = δ⁻ − δ⁺. Today Δ_e lies between 2.0 % (1 day) and 15.2 % (1 year) in chain
  semantics, and at about 13.3 % at 1 year on the v2 API with r = 2 %.
- **Old regime.** From 9 June 2025 to 8 January 2026, δ⁺ > δ⁻ held for short tenors: from 12 June 2025 for tenors
  below 73 days, before that below about 114 and 45 days respectively. At that time R_PM2 was not convex even in
  regular scenarios (69 of 3,000 tests, up to 478 USD).
- **Dormant breaking points.** The oracle contingency is a step in the feed confidence and is currently dormant
  (all ≥ 0.95, threshold 0.55). There is also maxExpiries 16.

## 7. Tools for the experimental design

| Tool | Fidelity | Limits |
|---|---|---|
| API directly, pre/post | the IM of the off-chain engine, equal to the account view `margin_watch`; two books per request at the same price state (PM2 with a new expiry in the changes: remainder up to 1.13 USD) | admission is not checked this way. Rate limit for v2 undocumented; in the logs of all agents a peak of about 3.75 requests/s over 60 s without rate-limit errors |
| SM replica (`sm_model.py`, `engine.py`) | `sm_model.py` matches the API to ≤ 0.012 % on a book with 50 options; `engine.py` matches the original values to ≤ 374 USD | needs ticker feeds |
| PM2 replica (`pm2_replica.py`, `pm2v.py`) | matches the deployed lib to 4e−15 relative, 20,000 books in seconds | chain semantics: for the API, plug in r = 2 % and ticker feeds, not yet validated. After a spot fit to the API, the MM keeps a remainder of median 3.3 USD, p90 81 USD, max. 1,137 USD; untested with ticker feeds |
| eth_call oracle | exact to the chain, also historically from 13 June 2025 | gas cap of 50 M, so at most about 150 to 200 legs |
| Box spread | gives the engine discount per expiry in one request | check on every measurement day, because the 2 % rate is undocumented |

The scripts are under `data/p2/semantik_20260924/` in the subfolders `code-pm2/`, `verify-konvex/`,
`verify-widerspruch/` and `code-sm/`. For the paper they are rewritten test-first and not reused.

## 8. Parameter history of PM2 BTC

PM2 for BTC has existed since 9 June 2025, 05:18 UTC. The rate feed was stale until 12 June 2025; reconstruction is
possible from 13 June 2025. Changes according to the events (`results/p2/semantics/pm2_parameters_btc.json`):

| Date (UTC) | Change |
|---|---|
| 9 June 2025 | Start. Grid ±18 %, vol +0.5/−0.3, static discount sBase/lBase 0.95/1.05. The same day 0.98/1.02 and rate mult 0.1 |
| 12 June 2025 | Static discount: add 0.16 → 0.1, mult 0.1 → 0 |
| 17 September 2025 | maxExpiries 10 → 14 |
| 10 October 2025 | confMargin 1.0 → 0.4 |
| 8 January 2026 | Static discount flipped to sBase/lBase 1.02/0.98; since then R is convex in the regular scenarios |
| 23 January 2026 | Tail weights lowered |
| 3 February 2026 | Upgrade to PMRM_2_1, allows libs per account |
| from 17 February 2026 | Account overrides for 15 accounts (mmFactor 0.35) |
| 24 May 2026 | Grid ±17 %, vol up 0.45, perp contingency 0.015 |
| 13 August 2026 | maxExpiries 16 |
| 20 August 2026 | Grid ±14 %, vol +0.40/−0.25, contingencies halved. Mostly a loosening; only minVolUp rises from 0.4 to 0.5 |

The SM option parameters for BTC have been unchanged since 4 December 2023. The legacy PMRMLib emits no events. The
2 % rate of the v2 API is off-chain, so the history of the API cannot be reconstructed, only that of the chain
semantics.

## 9. Corrections to the handover

- "Requirement read as capital minus `post_initial_margin`" is R − V and not a requirement.
- "Portfolio margin" on 24 September was PM2. The factor of 1.2 to 1.5 given there follows from the book and the
  reading. On R_eng it is 3.61 and 2.14.
- "The oracle returns margin balances" means, more precisely, `net = C + V − R`.
- "Deterministic, publicly callable function" holds only for the position IM of the off-chain engine. It uses an
  undocumented discount of 2 % instead of the on-chain parameters alone. Not covered are open-order margin, OI caps
  and liquidation, which runs on-chain with the feed rate and the account libs.
- "Not convex" for PM2: strictly correct, but for a different reason (section 6). The clearly non-convex one is SM.
- "Breaking point": there is no absolute size effect (section 6).
- "814 active BTC options": 814 was the number of listed instruments at 09:23 UTC. At 11:20 UTC there were 820, of
  which 694 were active.
- Time axis: after the start on 9 June 2025 there were 8 dates with parameter changes, plus the upgrade on
  3 February 2026 and account overrides from 17 February 2026. The most recent change was mostly a loosening.

## 10. Decisions before the experimental design

1. **Engine.** Recommended: v2 `api.lyra.finance` as the reference, with the chain semantics as a second engine for
   MM, liquidation and history. v3 only as a sensitivity.
2. **Denominator.** Recommended: K_p, with p equal to the mark or to the fill price from Paper 1. R_eng serves as
   the engine quantity.
3. **IM or MM.** The IM probably governs admission (not shown), the on-chain MM governs liquidation.
4. **Map.** A single contract per cell, or marginal cost in a reference inventory. Candidate inventories are
   synthetic books, real maker accounts via `margin_watch`, or books reconstructed from Paper 1 fills.
5. **Holding time.** Edge is a flow, capital a stock. Without a holding time, "edge per margin" is not defined.
6. **Scope.** Only BTC or also ETH and HYPE; only the PM2 era from 13 June 2025 or the whole period of Paper 1.
7. **Structure.** Part 1 as "convex in practice, not strictly, SM clearly not". Part 3 as a relative kink plus
   external limits.
