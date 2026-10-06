# Pre-registration Paper 2: Capital-adjusted edge on Derive (English translation)

> **Translation, not part of the registration.** This English text was made on 25 September 2026, after all
> registered results on the pilot cut had been computed and after the audit of the paper (`docs/paper2/AUDIT.md`, finding A64);
> Addendum 5 was translated on 27 September 2026, Addendum 6 on 30 September 2026 and Addendum 7 on 5 October
> 2026. It translates `docs/paper2/PRAEREGISTRIERUNG.md` as it stands with Addenda 1 to 7, git blob `f492585cf4a3308154ba764ef4616e09d3d68621`
> (`git hash-object docs/paper2/PRAEREGISTRIERUNG.md`). **The German original is binding**; where the two texts
> differ, the German text applies. The registration itself is commit `c9e9162`; the commits of Addenda 1 to 6 are
> named in the section "Data, code and pre-registration" of `paper2/main.tex`. These are the hashes after the
> second history rewrite of 5 October 2026 (Addendum 7): the registration was `1d13227` until 27 September 2026
> and `cc0a29f` until 5 October 2026. Addendum 5 maps old to new, and
> `docs/paper2/HISTORY_REWRITE.md` shows that `PRAEREGISTRIERUNG.md` is byte-identical in each pair of old and
> new commit. Until 27 September 2026 this translation was `docs/paper2/PREREGISTRATION_EN.md`.
>
> Conventions: "Nachtrag" is rendered as "Addendum", as in the paper. Numbers use a decimal point instead of the
> German decimal comma and dates are written out; code names, symbols and formulas are unchanged. File paths are
> those of the original, except that files renamed on 27 September 2026 appear under their new names
> (`get_margin_semantics.md`, `VALIDATION.md`); the German original keeps the old ones. Two symbols keep their
> German subscripts: `Einzel` (single contract) in K_PM2,Einzel and K_Einzel, and `nach` / `vor` (after / before
> the event) in K_nach and K_vor.

Fixed on 24 September 2026, before any capital figure of the paper was computed. The git commit of this file is
the timestamp. Later changes only as a dated addendum at the end, never by overwriting.

## Sample
- The fills of the Paper 1 sample (`docs/paper1/PRAEREGISTRIERUNG.md` with its addenda), i.e. BTC, ETH and HYPE
  options with a taker timestamp in [2024-01-11 00:00, 2026-09-30 08:00] UTC and the same exclusions.
- Pilot figures with cut-off 17 September 2026 12:00 UTC as in Paper 1; the final data run follows together with
  Paper 1.
- Manager windows: SM over the whole period (HYPE from 11 November 2025), legacy PM for BTC and ETH over the whole
  period, PM2 for BTC and ETH from 12 June 2025 23:00 UTC and for HYPE from 11 November 2025 00:00 UTC. The
  **PM2 window** of an underlying is its period from that time on.

## Semantics and capital
- Chain semantics: parameters and feeds at the time of the fill (block from the taker timestamp, 2 s per block from
  block 2 454 793 = 11 January 2024 00:00:01 UTC). For each feed, the value last pushed before that time applies
  (spot, forward per expiry, SVI per expiry, PM2 rate per expiry). No exclusion because of feed age; the age is
  carried along. Standard lib per manager; in the maker book, the lib of the account.
- Initial margin is primary, maintenance margin a sensitivity.
- Capital of a book q at prices p: **K_p(q) = Σ_options p_i·q_i − net_IM(q; cash = 0)**, with net_IM from the
  replica of the manager. Perps without premium, entry price equal to the perp price of the engine. Non-USDC
  collateral stays outside.
- **Capital per fill:** q = +1 for a maker buy and −1 for a maker sell, p = fill price, otherwise an empty book, per
  contract, under every manager available in the window (K_SM, K_PM, K_PM2).
- **Net edge:** NE after 30 min from Paper 1 (Addendum 2 there), in USDC per contract.
- **Cells:** underlying × maker side (buy, sell) × |Δ| bucket × tenor bucket from Paper 1; populated from 200 fills
  in the respective window.
- **Edge in bp of notional** of a cell: 10⁴·Σ NE_i·a_i / Σ Index_i·a_i. **Edge per capital** of a cell:
  10⁴·Σ NE_i·a_i / Σ K_i·a_i (a = amount).

## Maker books
- **Dominant maker subaccounts:** the ten subaccounts with the most maker fills in the Paper 1 sample (all
  underlyings together).
- **Book at the start of the day:** on-chain holdings (`SubAccounts.getAccountBalances`) at the first block of the
  UTC day, with options and perps; manager of the account (`SubAccounts.manager`) at the same block.
- **Book before a fill:** book at the start of the day plus all fills of the subaccount (maker and taker rows) of
  that day with an earlier timestamp; expired options (expiry ≤ time) are removed.
- **Marginal cost:** ΔK = K(book after the fill) − K(book before the fill), the new contract at the fill price.
- **Netting value of a maker day:** K of the book at the start of the day under SM and under PM2, existing positions
  at the mark M_b of Paper 1 (Black-76 on the last pushed SVI curve, forward `SVI_fwd`, D = 1). Under PM2 and the
  legacy PM, each underlying is computed separately and the results are summed. Only legs of underlyings whose PM2
  window is open on that day.

## Hypotheses and rejection rules
- **H1 ranking:** Across all populated cells in the PM2 window, the Spearman rank correlation ρ between edge in bp of
  notional and edge per PM2 capital is smaller than 0.5. **Rejected** if the upper bound of the 90 % interval is
  ≥ 0.5.
- **H2 marginal cost:** For the fills of the dominant maker subaccounts in the PM2 window whose account is margined
  under PM2 at the start of the day, the median of ΔK / K_PM2,Einzel is smaller than 0.5. Fills with
  K_PM2,Einzel ≤ 0 are excluded and counted. With more than 20 000 fills, a simple random sample of 20 000 applies
  (seed 20260924). **Rejected** if the upper bound of the 90 % interval is ≥ 0.5.
- **H3 netting value:** Across the maker days of the dominant subaccounts in the PM2 window with at least one option
  position, the median of K_SM / K_PM2 is greater than 2. Maker days with K_PM2 ≤ 0 are excluded and counted.
  **Rejected** if the lower bound of the 90 % interval is ≤ 2.
- **H4 price of capital:** If a parameter change makes capital cheaper, the half spread falls.
  - *Events:* all on-chain parameter changes of PM2 per underlying in the PM2 window and the two parameter changes of
    the legacy PM (12 June 2024, 22 February 2025) for BTC and ETH. Changes of the same underlying on the same UTC
    day are combined. Events whose largest absolute dose across all cells is below 1 % are dropped.
  - *Dose:* d_{c,e} is the mean over the fills of cell c in [e − 14 days, e) of log(K_nach / K_vor). K_nach and
    K_vor compute the same fill with the same market state, once with the parameters after and once with the
    parameters before the event, under the changed manager.
  - *Outcome:* half spread per fill in bp of the index, y_i = 10⁴·HS_i / Index_i, HS from Paper 1.
  - *Regression:* window [e − 14 days, e + 14 days] without the event day; y_i = α_{c,e} + γ_{day,underlying}
    + β·post_i·d_{c,e} + ε_i. Cells need at least 20 fills before and 20 after the event.
  - *Rejection:* **rejected** if β is not positive with a one-sided wild cluster bootstrap p ≤ 0.05, or if β does not
    lie above the 95th percentile among 100 placebo dates. Placebo dates are drawn uniformly from the days of the
    window that are at least 28 days away from every event of the same underlying. Each placebo date receives the
    dose vector of a randomly chosen real event of the same underlying.

## Inference
- Intervals: percentile interval of a cluster bootstrap over UTC days, B = 9 999, seed 20260924. H1 draws days and
  recomputes both cell quantities and ρ in every replication; cells without a fill in a replication drop out
  there.
- H4: wild cluster bootstrap (Rademacher, restricted residuals), cluster UTC day, B = 9 999, seed 20260924.
- Everything else is exploratory and is labelled as such: maps under SM and the legacy PM, MM instead of IM, API
  semantics with 2 %, time normalisations (to expiry, empirical holding time), values per underlying, surfaces and
  animations.

## Validation before measurement
- Before capital figures enter a test, the replica is checked against `eth_call` per underlying and available
  manager at no fewer than 48 random blocks (single contracts), and the maker books on no fewer than 20 maker days.
- Threshold: median of the absolute relative deviation of K below 0.1 % and 95th percentile below 1 %. If it is
  missed, the cause is recorded as a dated addendum before the inference.

## State of the data before this commit
- Computed so far, exploratively: the semantics probes (`docs/paper2/get_margin_semantics.md`, netting factors of
  synthetic books from 2× to 11×, which entered the threshold of H3) and a feasibility probe under SM for BTC
  (`data/p2/kontext/oberflaeche/proto_fill_capital.py`: pooled edge per SM capital 41 bp for maker sells, 74 bp for
  maker buys).
- Not computed: PM2 and legacy PM capital per fill, cell values for H1, marginal costs, netting values of real maker
  books, and doses.

## Addendum 1 (25 September 2026, after building the data base, before the first capital figure)

1. **Book before a fill (H2):** Instead of "book at the start of the day plus the day's fills from the tape", the
   exact on-chain holding applies: snapshot at the first block of the UTC day plus all `BalanceAdjusted` events of
   the account up to just before the transaction of the fill (options and perps). Reason: the options tape contains
   neither perp fills nor transfers. On 5 000 fills of the H2 population the tape book matched the on-chain holding
   in only 62.2 % of cases (options 88.4 %, perps 70.2 %; `data/p2/books/compare_books.json`), whereas snapshot plus
   events reproduces the next day exactly on 1 165 of 1 165 account days. The tape book is reported as a
   sensitivity. The fill is located through the timestamp of the account's own row and its transaction (for RFQ the
   maker row precedes the taker row).
2. **Rate per manager:** PM2 computes with the PM2 rate feed, the legacy PM with its own rate feed (constant 0 since
   deployment, checked with `eth_getLogs`), SM without discounting.
3. **Feed age:** measured as the time minus the signature time of the feed value (`feed_ts`), the clock of the
   contracts.
4. **Pseudonyms:** accounts appear in `results/` and in the paper as rank labels (M1 to M10 by maker fills) or as an
   HMAC with a secret salt. An unsalted SHA-256 of small account numbers can be reversed by enumeration.
5. **Observation without change:** of the ten dominant maker subaccounts, four are margined under PM2; the H2
   population consists of their fills in the PM2 window.

## Addendum 2 (25 September 2026, before the first inference)

1. **Unit of fee and rebate:** `trade_fee` and `expected_rebate` of the maker row are totals per fill, not per
   contract (the taker fee rises with the amount: median 0.89 USDC for ≤ 0.2 contracts, 18.5 for 1, 49.1 for 5
   contracts; BTC sample). The net edge per contract is therefore
   NE_i = MO_30min,i − (fee_maker,i − rebate_maker,i) / a_i − Hedge_i, and NE_i·a_i is the edge of the fill in USDC.
   This is how the pre-registered definition ("in USDC per contract") is meant. The code of Paper 1
   (`inference_p1.analysis_frame`) subtracts the totals undivided from the markout per contract; over all 603 940
   fills the mean fee there is 1.56 instead of 1.09 USDC per contract and the mean rebate 0.59 instead of 0.77.
   Paper 2 uses the per-contract form; the form from Paper 1 is reported as a sensitivity. The finding goes to
   Paper 1 as a correction note.

## Addendum 3 (25 September 2026, before the first inference): clarifications without change of substance

1. **H1 bootstrap:** The set of cells is that of the original sample (≥ 200 fills in the PM2 window). In each
   replication the days are drawn with replacement, both cell quantities are recomputed from the weighted daily
   sums, and ρ is determined over the cells with at least one fill in the replication. Interval: 5th and 95th
   percentile of the 9 999 replications.
2. **H2 and H3:** interval for the median likewise over drawn UTC days (all fills or maker days of a drawn day enter
   with its multiplicity).
3. **H4 placebo:** A placebo replication draws, for each retained real event e, a placebo date from the admissible
   days of its underlying (at least 28 days away from every event of that underlying) and gives it the dose vector
   of a randomly chosen retained event of the same underlying; the panel is then built as for the real events and
   β is estimated. 100 replications, seed 20260924.
4. **H4 fixed effects:** α per (cell, event), γ per (UTC day, underlying); estimation by alternating demeaning
   (within), wild cluster bootstrap with restricted residuals (β = 0), Rademacher weights per UTC day, one-sided p
   for β > 0.

## Addendum 4 (25 September 2026, after the validation, before the first test statistic)

The validation against `eth_call` is passed (`docs/paper2/VALIDATION.md`: under IM median |rel| 8.7e−10, p95
1.4e−8 for single contracts; books with 2 to 245 legs median 2.2e−9). Open readings are fixed here before any test
statistic is computed:

1. **H2 quantity:** ΔK covers the whole fill (q = maker side × amount); the test statistic is
   ratio = (ΔK / amount) / K_PM2,Einzel, i.e. the marginal cost per contract of this fill. The variant "next single
   contract" (ratio_unit), the MM variant and the tape book are sensitivities. The sample was drawn before the
   exclusion K_Einzel ≤ 0 (1 fill affected).
2. **H3:** K_SM and K_PM2 are computed on the same legs (underlyings with an open PM2 window). On 1 431 of 1 943
   maker days the book holds more than the 63 options that an SM account on v2 can hold; K_SM is counterfactual
   there. This is stated in the paper; the test statistic stays unchanged. Legacy PM only as a sensitivity on BTC
   and ETH legs.
3. **H4 events:** Changes only to `CollateralParameters` or `maxExpiries` do not enter the event list; they do not
   change the capital of a single contract and would have been dropped under the 1 % rule anyway. For the minimum
   distance of the placebo dates, by contrast, all parameter changes of the underlying count (every row of the
   timeline), including dropped ones. Fills with K ≤ 0 before or after the event (10 of 57 151) do not enter the
   mean dose. For combined changes on one day, e is the time of the first change, and K_nach applies with the state
   after the last.
4. **H1:** No exclusions; the 20 fills with K_PM2 ≤ 0 (RFQ legs priced far from the mark) stay in the sums.

## Addendum 5 (27 September 2026): rewriting the local history before publication

This addendum is written after all registered results. It changes no rule of the pre-registration or of Addenda 1
to 4, no test statistic and no result. It records why the commits of the pre-registration and of Addenda 1 to 4
carry new hashes:

| Version | Old commit | New commit | Author and committer time |
|---|---|---|---|
| Pre-registration | `1d13227b6f0698f29fcd95d18c5828ae6a0bbc5e` | `cc0a29f655b50c7415e01583b25952e9831bbecd` | 24 September 2026 22:33:50 +0200 |
| Addendum 1 | `eb534fe80dea66e651589e1ea01dfdeec6040c47` | `85bb0b7e17a3d32731a83de40ab88b8e012f3983` | 25 September 2026 00:26:54 +0200 |
| Addendum 2 | `94652106387bc1f6006e0dbe02ac0a7edb13ea67` | `6005d7c53ccf51d3df7d038025f546eb5d07a6ef` | 25 September 2026 00:29:29 +0200 |
| Addendum 3 | `bfc34c81c507c51a38e83878422b89d072f9ed18` | `8778432b49f01532809517d592acda4727d7aaa8` | 25 September 2026 00:29:56 +0200 |
| Addendum 4 | `c4fcb59d61b73549aa90cacbd3b997816f36d823` | `e492ba123c4c81ddc478c0c6ef2246867deeeaae` | 25 September 2026 01:29:58 +0200 |

1. **Reason:** Before the first publication, the local history of Paper 2, which had never been pushed, was
   rewritten (audit A01, `docs/paper2/AUDIT.md`). First, account identifiers were removed, mainly from test fixtures
   and tests: raw account numbers of dominant maker subaccounts and of PM2 override accounts, and unsalted hashes
   that can be reversed by enumeration (Addendum 1, point 4). Second, the Paper 2 commits now build on the corrected
   and cleaned history of Paper 1 (branch `main`), in which later Paper 1 commits carry new hashes as well. As a
   result, every Paper 2 commit has a new hash, the five commits of the table included.
2. **Byte-identical texts:** In each of the five new commits this file is byte-identical to the version in the old
   commit (same git blob, same SHA-256), and the diff of each of these commits against its parent is the same as in
   the original. The blob hashes and SHA-256 values of the five versions are in `docs/paper2/HISTORY_REWRITE.md`.
3. **Times:** Author and committer are kept with name, e-mail, date, time of day and time zone; in each of the five
   commits the author time equals the committer time (table). They remain local times of the author's machine.
   Because they are kept, the rewritten commits are dated before the commit `d2a2b43` on `main` (25 September 2026,
   12:37 +0200) on which they now build. The times state when the texts were first committed.
4. **Publication:** The old commits were never pushed and will not be published, because they contain the removed
   identifiers; the mapping from old to new can therefore be checked only in the author's local repository. The
   pre-registration becomes public only with the push of the rewritten history, that is, after the results. There is
   no public timestamp before the results.

## Addendum 6 (30 September 2026, after the results on the pilot cut, before the final data run): fee of multi-leg RFQ packages

This addendum is written after all results on the pilot cut of 17 September 2026 and before the data run up to the
registered cut-off (30 September 2026 08:00 UTC). It changes no test statistic, no rejection rule and no result; it
makes Addendum 2, point 1, precise and adds a sensitivity.

1. **Finding (audit A67):** On multi-leg RFQs Derive books the maker fee of the package almost always on exactly one
   leg (pilot: of 4 996 packages with more than one leg and a maker fee, 4 511 on exactly one leg; RFQs carry no
   rebates). "Totals per fill" in Addendum 2, point 1, holds literally only for order book fills; on a multi-leg RFQ
   the booked fee is a total over the package.
2. **Main reading unchanged:** NE_i = MO_30min,i − (fee_maker,i − rebate_maker,i) / a_i − Hedge_i as in Addendum 2;
   the fee stays on the leg on which it is booked. This is the reading of Addendum 3, point 3, of the Paper 1
   pre-registration, so both papers use the same net edge.
3. **Sensitivity:** H1 is also reported with the fee spread over the package: every leg of a package (same `rfq_id`
   and maker wallet) carries its amount times (Σ fee − Σ rebate) / Σ amount of the package; order book fills are
   unchanged, and the sum of the edge over all fills stays the same (`inference_p2.package_fee_net`,
   `results/p2/sensitivity.json`, section `c2_rfq_package`).
4. **Size (pilot, from the finding on Paper 1):** The mean maker fee per contract over the RFQ fills is 0.3115 USDC
   leg by leg and 0.3177 USDC spread over the package (`results/p1_finding/fee_units.json`, `rfq_booking`); in
   Paper 1 the spreading changes no cell verdict.

## Addendum 7 (5 October 2026): second rewrite of the history before publication

This addendum is written after all results on the pilot cut and before the final data run. It changes no rule of the
pre-registration or of Addenda 1 to 6, no test statistic and no result. It records why the commits of the
pre-registration and of Addenda 1 to 6 carry new hashes once more:

| Version | Commit after Addenda 5 and 6 | New commit | Author and committer time |
|---|---|---|---|
| Pre-registration | `cc0a29f655b50c7415e01583b25952e9831bbecd` | `c9e9162dd368ffd86867b205dc795c9af119a387` | 24 September 2026 22:33:50 +0200 |
| Addendum 1 | `85bb0b7e17a3d32731a83de40ab88b8e012f3983` | `b5c905c33f918dfc069df1b06b2cb779d9cc9c31` | 25 September 2026 00:26:54 +0200 |
| Addendum 2 | `6005d7c53ccf51d3df7d038025f546eb5d07a6ef` | `60896fe9f8b3aaa2f4c05f3f6abc6b634f083ccb` | 25 September 2026 00:29:29 +0200 |
| Addendum 3 | `8778432b49f01532809517d592acda4727d7aaa8` | `2416902f883868adb5de6e13da40ebf48d62b57c` | 25 September 2026 00:29:56 +0200 |
| Addendum 4 | `e492ba123c4c81ddc478c0c6ef2246867deeeaae` | `a02058a4ce292cd07cfc580d962a04b636b197b1` | 25 September 2026 01:29:58 +0200 |
| Addendum 5 | `a3282d6474ebd4c0c5c81bb084ea3ce5e8f2afdd` | `8c066a767ded79e17290dfdb5ada577ebaac68f1` | 27 September 2026 14:23:27 +0200 |
| Addendum 6 | `1b46e80fa5297144e8b830b6b64d2737db7da0e5` | `6f2436e2b91cb1529afff70637352a7086f7aee0` | 30 September 2026 12:42:41 +0200 |

1. **Reason:** Before the first publication of Paper 2, the whole history of the repository was rewritten, including
   the history of Paper 1, which had been public since 25 September 2026. The authorship records were made uniform:
   some early commits named the AI coding tool that was used as their author, and most named it as co-author in a
   "Co-Authored-By" line; now every commit names the author. German commit messages were translated into English,
   and example lines of this kind in planning documents were removed. The paper discloses the use of generative
   tools in its section "Use of generative tools".
2. **Byte-identical texts:** In each new commit of the table this file is byte-identical to the version in the
   corresponding old commit (same git blob). The full mapping of all commits and the blob hashes are in
   `docs/paper2/HISTORY_REWRITE.md`.
3. **Times:** Author, committer, date, time of day and time zone of every commit are kept.
4. **Publication:** The commits of the left column were never pushed. The pre-registration of Paper 2 becomes public
   for the first time with the push of 5 October 2026, after the results on the pilot cut and before the final data
   run. There is still no public timestamp before the results.
