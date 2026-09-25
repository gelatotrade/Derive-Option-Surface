# Handover: status on 2026-09-24 and start of paper 2

This file is written for a new session that knows nothing about the work so far.
Read it first, then start.

## Where everything is

| | |
|---|---|
| Repo, working clone | `~/Documents/Papers/Finished Papers/Derive_Options/Derive-Option-Surface` |
| Branch | `paper1-adverse-selection`, 49 local commits, **nothing pushed** |
| Private notes outside the repo | `~/Documents/Papers/Finished Papers/Derive_Options/docs/` |
| Bot foundation | `~/Documents/Derive MarketMaker Bot/dq` |

Until 2026-09-23 the folder was under *Working Papers*; the user then moved it to *Finished Papers*.
Older notes still give the old path.

## Paper 1 is finished

“Who trades against the maker? Adverse selection with counterparty identity on an on-chain options order
book.” Nine pages in Elsevier CAS typesetting, 3,818 words, nine figures, 150 tests, built with
`python3 scripts/p1_build.py`.

Core findings, all from the pilot cut of 2026-09-17 with 603,940 fills:

- Decomposition per contract: half spread +15.70, adverse selection −2.65, fee −1.56, rebate +0.59,
  hedge −3.15, net edge +8.93. Median markout only 0.98.
- The counterparty decides: +24.73 against ordinary takers, −25.41 against the 17 dominant makers.
- Ten wallets carry 90.5 % of the maker loss, a single address 39.0 %.
- Size and sweeps explain nothing under instrument-by-day fixed effects: t = −0.74 and t = −0.10.
- Three of four pre-registered hypotheses are rejected, and that carries the structure of the paper.

### What is still open on paper 1

1. **Final data run** after 2026-10-01 with cut-off 2026-09-30, then check all numbers against the new numbers
   sheet. Check `pmset -g batt` beforehand and ask the user for the power adapter, otherwise the Mac goes to sleep.
2. **Push and pull request.** When merging, choose “Create a merge commit”, not “Squash”, otherwise
   the pre-registration commit `3fd9caa` disappears from the history, and exactly this hash is cited in the manuscript.
3. **Access:** the token in the keychain has no write permission, 403. An SSH key was generated on 2026-09-24
   and is at `~/.ssh/id_ed25519`, but its public part is **not** yet registered with GitHub.
   After that, switch the remote to SSH.
4. **Open user decision:** `results/p1/h1_lorenz.csv` contains 1,388 wallet addresses sorted by gain against
   makers. The manuscript names none. Clarify before the merge whether the column gets hashed.
5. Proofreading by a human; so far only the model has read the text.

## Paper 2: margin polytope and capital-adjusted edge

**The question.** Paper 1 says where on the surface a maker gets paid. It does not say how much of that one
can afford. The right target quantity for a bot is not the edge per contract but the edge per unit of
margin consumed. On centralised exchanges, portfolio margin is a black box. On Derive, the
risk engine is a deterministic, publicly callable function, so the admissible
position space can be sampled completely without tying up capital.

**What was checked on 2026-09-24.** `public/get_margin` responds without an account and without a key.
Required fields are `margin_type`, `simulated_positions`, `simulated_collaterals`; for `PM` and `PM2`,
`market` is added. Important: the API blocks requests without a User-Agent with HTTP 403; any value will do.
There are 814 active BTC options.

Measurement with 50 BTC options across five expiries, 200,000 USDC of collateral, requirement read as
capital minus `post_initial_margin`:

| Portfolio | Standard margin | Portfolio margin | Factor |
|---|---|---|---|
| 50 short, one-sided | 1,472,630 | 1,007,583 | 1.5 |
| 25 long / 25 short | 707,994 | 595,818 | 1.2 |

**Unresolved contradiction that paper 2 has to resolve.** The note of 2026-09-17 gives a netting factor of about
11 for a similar setup. The measurement of 2026-09-24 gives 1.2 to 1.5. Either
parameters have changed, or the earlier probe interpreted the fields differently. The oracle returns
margin **balances**, not requirements, and the conversion mixes position value and margin. Clarifying the semantics
cleanly is the first work step and already a contribution.

**Four parts of the paper.**

1. *Geometry.* The admissible region under PM2 arises from scenario shocks to spot, vol and skew and is
   not convex. Characterising it is the theory part.
2. *Map.* The same delta-by-tenor map as in paper 1, but in edge per margin instead of per contract.
3. *Breaking point.* Up to what size the marginal contract is almost free, and where the portfolio tips over.
4. *Time axis.* Parameter changes are on-chain events (`*ParamsUpdated`), and therefore reconstructible: when
   the engine became stricter, and what that did to book depth.

**Known constraints.** PM2 requires a `market` parameter, so there is no netting across
underlyings, and a bot needs its own subaccount per underlying. Sampling across many
dimensions costs a very large number of API calls, so it needs an experimental design rather than a grid. The
portfolios are hypothetical; the paper is about the space of possibilities and not about realised books,
and that belongs in the title.

## Working style the user expects

- **Superpowers workflow:** brainstorming, then writing-plans, then executing-plans. Plans under
  `docs/superpowers/plans/`, specifications under `docs/superpowers/specs/`.
- **Test-driven.** First the failing test, then the code. The suite must stay green.
- **Pre-registration** before every measurement, with dated addenda. Never change anything retroactively.
- **Paper in English, project documentation in German.** No em or en dashes in running text.
- **Little text, many figures.** Hard word budgets per section, monitored by
  `scripts/p1_wordcount.py`. A section that exceeds its budget gets cut.
- **Every number in the text must be traceable in `results/`.** Check scripts enforce this.
- **No invented references.** Check every source against the publisher, RePEc or DOI.
- For long runs, check `pmset -g batt` beforehand; on battery the Mac sleeps despite `caffeinate`.
- At most one web research agent at a time, otherwise the session limit is used up in about 25 minutes.

## First step in the new session

Clarify the semantics of `get_margin` before anything else happens. Specifically: what exactly is
`pre_initial_margin` as opposed to `post_initial_margin`, how does that relate to `simulated_collaterals`, and
how does one read from it a requirement that is comparable across portfolios. Only once this question
is answered is an experimental design for the sampling worthwhile.
