# Design: What does the edge cost? Capital-adjusted edge of an options maker under a public risk engine (Derive 2024 to 2026)

As of: 2026-09-24 · Author: Gregor Albiez (FHNW) · Target: SSRN working paper in the format of Paper 1 (Elsevier CAS
two-column, about 3 800 words, nine figures, little text) · Branch `paper2-capital`.

**Author's decisions (2026-09-24):**
- the whole period of Paper 1 with three managers;
- edge per capital per fill as the main quantity, time normalisation only as a sensitivity;
- capital both for the single contract and in the real maker book;
- historical capital via an offline replica with sample validation against `eth_call`;
- hypotheses H1 to H4 as in section 4 with the thresholds given there;
- then continue autonomously, write the paper and audit it at the end.

Basis: `docs/paper2/get_margin_semantics.md` (semantics of the engine), `docs/paper2/HANDOVER.md`, the data of
Paper 1 (`data/p1/`) and the context probes under `data/p2/kontext/`.

---

## 1 · Question and contribution

**Question.** How much capital does the edge of an options maker on Derive tie up, and does the picture from Paper 1
change when edge is measured per capital instead of per contract?

**Contribution.**
1. **Capital map.** Edge per capital across the delta-by-tenor map of Paper 1, computed with the real,
   public risk engine and not with a model assumption.
2. **Marginal cost.** The capital that a fill additionally ties up in the actual book of a dominant maker, under
   that maker's actual manager.
3. **Netting value.** Capital of the same real books under standard margin, legacy portfolio margin and PM2.
4. **Price of capital.** Parameter changes of the engine as a natural experiment: the counterfactual
   change in capital per cell can be computed exactly and serves as the dose for the half spread.

The title states that capital is measured through hypothetical portfolios of the engine (space of possibilities),
not through observed account balances.

**Not part of the paper:** margin for open orders, book depth, a bot algorithm, the API semantics (flat
2 %) in the history, liquidations.

---

## 2 · Data

| Component | Source | Status |
|---|---|---|
| Fills with net edge | `data/p1/derived/markouts.parquet` and `inference_p1.analysis_frame` (Paper 1) | 603 940 fills, 2024-01-11 to 2026-09-17 12:00 UTC (pilot cut) |
| SVI curves per expiry | `data/p1/volfeed/{CCY}_svi_YYYY-MM.parquet` (on-chain `VolDataUpdated`) | available |
| Spot, forward, rate | on-chain feed events (`SpotPriceUpdated`, `ForwardDataUpdated`, `RateUpdated`) per underlying, to be loaded anew into `data/p2/feeds/` | period as in Paper 1 |
| Parameters per manager | on-chain getters at the event blocks, legacy PM by bisection (no events) | `results/p2/params/` |
| Maker books | `SubAccounts.getAccountBalances` and `manager()` by historical `eth_call` at the start of the day for the ten largest maker subaccounts, plus the fills of the day from the tape | `data/p2/books/` |
| Manager shares of OI | `OptionAsset.totalPosition` per manager, monthly | `data/p2/kontext/margin-historie/oi_legacy.json` |

Availability (from `data/p2/kontext/margin-historie`):

| | SM | Legacy PM | PM2 |
|---|---|---|---|
| BTC | whole period | whole period (used until 02/2026) | from 2025-06-12 23:00 UTC |
| ETH | whole period | whole period (used until 03/2026) | from 2025-06-12 23:00 UTC |
| HYPE | from 2025-11-11 | does not exist | from 2025-11-11 |

Block time on chain 957: exactly 2 s since genesis, block 2 454 793 = 2024-01-11 00:00:01 UTC. Time and block
convert into each other without any queries.

---

## 3 · Measures

**Semantics.** Historically only in chain semantics: parameters and feeds at the respective block, rate from the PM2
rate feed, standard lib (no account overrides except in the maker book, where the lib of the account applies). The
API semantics with a flat 2 % serves only as a present-day sensitivity. IM is primary, MM a sensitivity.

**Capital of a book q at prices p** (from the semantics note):

    K_p(q) = Σ_options p_i·q_i − net_IM(q; cash = 0)

Perps carry no premium and enter with an entry price equal to the perp price. Non-USDC collateral stays outside
K (a limitation, stated in the paper).

**Per fill (single contract).** q = +1 for a maker buy, −1 for a maker sell, p = fill price, book otherwise empty,
under every available manager: K_SM, K_PM, K_PM2 per contract.

**Edge.** Net edge NE after 30 min from Paper 1 (USDC per contract; half spread + adverse selection − fee + rebate
− hedge).

**Edge per capital of a cell** = Σ NE_i·a_i / Σ K_i·a_i (ratio of sums, a = amount), in bp of capital.
Cells: underlying × maker side (buy, sell) × |Δ| bucket × tenor bucket from Paper 1, populated from 200 fills.
Comparison quantity: edge in bp of notional = Σ NE_i·a_i / Σ Index_i·a_i.

**Marginal cost per fill (maker book).** Book before the fill = on-chain holdings at the start of the day plus the
fills of the subaccount since the start of the day from the tape. ΔK = K(after) − K(before), existing positions at
the mark M_b (Paper 1), the new contract at the fill price. Ratio ΔK / K_Einzel (single contract) under the manager of the account.

**Netting value per maker day.** K of the on-chain book at the start of the day under SM, legacy PM and PM2,
positions at the mark M_b. Under PM2 and legacy PM each underlying separately, then summed (no netting across underlyings).

**Time normalisation (sensitivity).** (i) to expiry: NE / (K·remaining tenor), annualised; (ii) empirical
holding time: median of the time until the position is closed out in the maker books, per cell.

---

## 4 · Hypotheses (pre-registered in `docs/paper2/PRAEREGISTRIERUNG.md`)

| | Statement | Test and rejection rule |
|---|---|---|
| H1 ranking | The capital denominator reorders the map. | Spearman ρ between edge in bp of notional and edge per PM2 capital across all populated cells in the PM2 window. Rejected if the upper bound of the 90 % cluster bootstrap interval (cluster UTC day) is ≥ 0.5. |
| H2 marginal cost | In the book of a dominant maker, the next contract is cheap. | Median of ΔK / K_Einzel under PM2 across the fills of the ten largest maker subaccounts in the PM2 window. Rejected if the upper bound of the interval is ≥ 0.5. |
| H3 netting value | PM2 saves more than half of the capital compared with SM. | Median of K_SM / K_PM2 across maker days in the PM2 window. Rejected if the lower bound of the interval is ≤ 2. |
| H4 price of capital | When capital becomes cheaper, the half spread falls. | Difference-in-differences around parameter changes with the counterfactual change in capital per cell as the dose. Rejected if the coefficient is not positive with a one-sided wild cluster bootstrap p ≤ 0.05, or if it does not lie in the top 5 % among 100 placebo dates. |

---

## 5 · Architecture

New modules in the package `derive_surface` with the prefix `p2` or `margin_`, tests offline under `tests/test_p2_*.py`.

| Module | Task |
|---|---|
| `p2types.py` | shared types `MarketState`, `ExpiryState`, `Book`, `OptionLeg`, `capital_from_net` (exists) |
| `p2feeds.py` | loading the feed events (spot, forward, rate, perp) per underlying; `state_at(ccy, ts, expiries)` builds a `MarketState` from feeds and SVI |
| `p2params.py` | parameters per underlying, manager and time from `results/p2/params/*.json`; loading by `eth_call` at event blocks |
| `margin_sm.py` | replica of `StandardManager` (isolated, max loss per expiry, perp, base), single and vectorised |
| `margin_pm.py` | replica of the legacy `PMRMLib` (without discount, without skew, own scenarios) |
| `margin_pm2.py` | replica of `PMRMLib_2` (port of `data/p2/semantik_20260924/verify-konvex/pm2v.py`), vectorised |
| `p2validate.py` | comparison of the replica against `eth_call` at random blocks per underlying and manager |
| `capital.py` | capital per fill (single contract) under all available managers → `data/p2/derived/capital.parquet` |
| `books.py` | on-chain holdings of the maker subaccounts at the start of the day, decoding of the option subIds, marginal cost per fill, netting value per maker day |
| `p2events.py` | event list, dose per cell and event, panel for H4 |
| `inference_p2.py` | tests H1 to H4, sensitivities, `results/p2/*.csv|json` |
| `p2surface.py` | adapter SVI curve → `Surface`, capital surface on the delta-by-tenor grid, animation |
| `figures_p2.py`, `figdata_p2.py` | figures through a registry as in Paper 1, style from `figstyle.py` |
| `p2cli.py` | subcommands `feeds`, `params`, `validate`, `capital`, `books`, `events`, `infer`, `figures`, `surface` |
| `scripts/p2_*.py` | build, word count, numbers sheet, figure check (pattern of Paper 1, without tautological comparisons) |
| `paper2/` | manuscript `main.tex`, `refs.bib`, `figures/` |

The RPC load stays at ≤ 2 requests/s per process. All downloads are resumable and write in chunks.
Maker subaccounts and wallets appear in result files only as a hash (SHA-256, first 10 characters).

---

## 6 · Figures (draft, final choice as in Paper 1 through drafts and a jury)

| Slot | Content |
|---|---|
| T1 | The engine's view of the surface: BTC vol surface in 3D (height IV), coloured with the PM2 capital per short contract, SM next to it. |
| T2 | What `get_margin` returns: net = C + V − R and the resolution of 11 versus 1.2 (bars C − net against R). |
| F1 | Capital per contract by manager across |Δ| × tenor, buy and sell. |
| F2 | The map: edge in bp of notional against edge per PM2 capital per underlying and side, with rank scatter (H1). |
| F3 | Marginal cost in the maker book: distribution of ΔK / K_Einzel, share ≤ 0 (H2). |
| F4 | Netting value: K_SM / K_PM2 across maker days, legacy PM alongside (H3). |
| F5 | Timeline: manager shares of OI, parameter events per underlying, capital of a fixed reference book. |
| F6 | Price of capital: dose response and placebo distribution (H4). |
| A1 | Validation of the replica against `eth_call`. |

In addition, for the README and X: a GIF of the capital surface over time with the parameter events, social cards 1600×900.

Rules from Paper 1: CAS widths 3.4 and 7.0 inches, no font below 7 pt, readable in greyscale, one number per
cell, cells below 200 fills as an empty cross, every number of a figure also as a table under `results/p2/`.

---

## 7 · Manuscript

English, no em or en dashes in running text, word budget per section (introduction 600, engine and semantics 600,
data and measurement 600, results 1 400, discussion 400, conclusion 200). Every number in the text must be traceable
in `results/p2/` (check script). Literature only with a verified DOI or publisher page, at most one web agent
at a time.

---

## 8 · Order

1. Commit the specification and the pre-registration (this step).
2. Feeds, parameters, three engines with tests; load the maker holdings.
3. Validation against `eth_call`; only then capital per fill, maker books, doses.
4. Inference H1 to H4, numbers sheet.
5. Figures with a jury, surface and animation.
6. Manuscript, literature check, build.
7. Audit of the entire paper.

Pilot figures with cut 2026-09-17 12:00 UTC; the final data run follows with Paper 1 after 2026-10-01.
