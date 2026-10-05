# Literature, Paper 2: checked sources

Status: 25 September 2026. Record for `paper2/refs.bib` (30 entries). The first 20 entries were checked on
24 September 2026, the seven articles added after the audit (section "Audit addendum" below) on 25 September 2026.
For each entry, authors, year, title, journal, volume, issue, pages and DOI were compared with the DOI record at
`https://api.crossref.org/works/<DOI>`. It was also checked that `https://doi.org/<DOI>` redirects to the
publisher's page (HTTP 302 to OUP, Elsevier, Wiley, Springer, Taylor & Francis, De Gruyter or ACM). For four entries
RePEc (IDEAS) served as a second source. The file was built with `cas-dc` and `cas-model2-names` via tectonic,
without errors. In the build of 24 September 2026 all 20 entries of that time appeared correctly, including the
SICI DOI of `kupiec1996`; for the entries added later, the trial build in "Audit addendum" applies. Three entries
without a DOI (own work, contract code, API documentation) are listed under "Primary sources without DOI". The tests
in `tests/test_p2_refs.py` ensure that every entry is a row here, that the number above is right, that the entries
shared with Paper 1 are identical character for character, and that the checked DOIs stay unchanged.

For journals with advance online publication, the year of the issue applies: `brunnermeier2009` (online 2008),
`gueant2013` (online 2012), `christoffersen2018` (online 2017), `chen2019` (online 2018), `fournier2020` (online 2019),
`ahn2025` (online 2024), `mackinnon2017` (online 2016), `alexander2020` (reserve, online 2019).

The keys `garleanu2009`, `muravyev2016`, `christoffersen2018`, `cameron2008`, `mackinnon2017`, `roodman2019` and
`burlig2018` come from Paper 1 (`paper/refs.bib`). They are identical character for character there and here;
checked with `diff` and permanently by `tests/test_p2_refs.py`.

## Included sources

| Key | Full reference | DOI | Checked against | Date checked | Why we cite it |
|---|---|---|---|---|---|
| brunnermeier2009 | Brunnermeier, M. K., Pedersen, L. H. (2009). Market Liquidity and Funding Liquidity. *Review of Financial Studies* 22(6), 2201–2238. | 10.1093/rfs/hhn098 | https://api.crossref.org/works/10.1093/rfs/hhn098 | 24 September 2026 | Margin as a funding constraint of the liquidity provider: the capital a fill ties up limits the liquidity the maker can provide. |
| garleanu2011 | Gârleanu, N., Pedersen, L. H. (2011). Margin-Based Asset Pricing and Deviations from the Law of One Price. *Review of Financial Studies* 24(6), 1980–2022. | 10.1093/rfs/hhr027 | https://api.crossref.org/works/10.1093/rfs/hhr027 | 24 September 2026 | The required return depends on the margin a security ties up. This justifies measuring edge per capital instead of per contract. |
| ho1981 | Ho, T., Stoll, H. R. (1981). Optimal Dealer Pricing under Transactions and Return Uncertainty. *Journal of Financial Economics* 9(1), 47–73. | 10.1016/0304-405X(81)90020-9 | https://api.crossref.org/works/10.1016/0304-405X(81)90020-9 | 24 September 2026 | Classic inventory model: the spread compensates the dealer's inventory risk. Inventory is a value account (dI = r_I I dt + p dq_b − p dq_a + I dZ_I), penalised through risk aversion, without a bound. Cited as a model that penalises the position rather than bounding it (audit A15). |
| avellaneda2008 | Avellaneda, M., Stoikov, S. (2008). High-Frequency Trading in a Limit Order Book. *Quantitative Finance* 8(3), 217–224. | 10.1080/14697680701381228 | https://api.crossref.org/works/10.1080/14697680701381228 | 24 September 2026 | The standard model for quotes with inventory risk, the starting point of a capital-aware maker. Inventory q in units, penalised through the exponential utility function (reservation price s − qγσ²(T − t)). The main model has no bound; only the stationary variant (sect. 2.3) interprets a parameter ω as an upper bound q_max. Cited as a model that penalises the position (audit A15). |
| gueant2013 | Guéant, O., Lehalle, C.-A., Fernandez-Tapia, J. (2013). Dealing with the Inventory Risk: A Solution to the Market Making Problem. *Mathematics and Financial Economics* 7(4), 477–507. | 10.1007/s11579-012-0087-0 | https://api.crossref.org/works/10.1007/s11579-012-0087-0 | 24 September 2026 | Closed-form solution with inventory limits in units: a hard bound q ∈ {−Q, …, Q} "depending in practice on risk limits" (arXiv:1105.3115, sect. 2), plus CARA utility. The only one of the three inventory references with a bound; we ask whether on Derive the limit is better measured in capital (H2). |
| comertonforde2010 | Comerton-Forde, C., Hendershott, T., Jones, C. M., Moulton, P. C., Seasholes, M. S. (2010). Time Variation in Liquidity: The Role of Market-Maker Inventories and Revenues. *Journal of Finance* 65(1), 295–331. | 10.1111/j.1540-6261.2009.01530.x | https://api.crossref.org/works/10.1111/j.1540-6261.2009.01530.x | 24 September 2026 | Empirical evidence that market makers' inventories and revenues drive liquidity; model for the test of balance-sheet constraints (H4). |
| stoikov2009 | Stoikov, S., Sağlam, M. (2009). Option Market Making under Inventory Risk. *Review of Derivatives Research* 12(1), 55–79. | 10.1007/s11147-009-9036-3 | https://api.crossref.org/works/10.1007/s11147-009-9036-3 | 24 September 2026 | Inventory model specifically for options: the risk of the book, not the single contract, determines the quotes. That is the logic of marginal cost (H2). |
| figlewski1984 | Figlewski, S. (1984). Margins and Market Integrity: Margin Setting for Stock Index Futures and Options. *Journal of Futures Markets* 4(3), 385–416. | 10.1002/fut.3990040307 | https://api.crossref.org/works/10.1002/fut.3990040307 ; https://ideas.repec.org/a/wly/jfutmk/v4y1984i3p385-416.html | 24 September 2026 | Early work on margin setting for index futures and options: the margin should cover price changes with a given probability. This is the forerunner of scenario engines. |
| kupiec1994 | Kupiec, P. H. (1994). The Performance of S&P 500 Futures Product Margins under the SPAN Margining System. *Journal of Futures Markets* 14(7), 789–811. | 10.1002/fut.3990140704 | https://api.crossref.org/works/10.1002/fut.3990140704 ; https://ideas.repec.org/a/wly/jfutmk/v14y1994i7p789-811.html | 24 September 2026 | Empirical test of SPAN, the scenario-based portfolio margin whose on-chain counterpart is PM2. |
| kupiec1996 | Kupiec, P. H., White, A. P. (1996). Regulatory Competition and the Efficiency of Alternative Derivative Product Margining Systems. *Journal of Futures Markets* 16(8), 943–968. | 10.1002/(SICI)1096-9934(199612)16:8<943::AID-FUT6>3.0.CO;2-M | https://api.crossref.org/works/10.1002/(sici)1096-9934(199612)16:8%3C943::aid-fut6%3E3.0.co;2-m ; https://ideas.repec.org/a/wly/jfutmk/v16y1996i8p943-968.html | 24 September 2026 | Comparison of strategy-based and portfolio-based margin for the same positions. This is the direct template for the netting value of SM versus PM2 (H3). |
| artzner1999 | Artzner, P., Delbaen, F., Eber, J.-M., Heath, D. (1999). Coherent Measures of Risk. *Mathematical Finance* 9(3), 203–228. | 10.1111/1467-9965.00068 | https://api.crossref.org/works/10.1111/1467-9965.00068 | 24 September 2026 | Scenario-based margin (there with SPAN as the example) as a coherent risk measure; formal basis for the subadditivity that makes netting in the book cheaper. |
| duffie2011 | Duffie, D., Zhu, H. (2011). Does a Central Clearing Counterparty Reduce Counterparty Risk? *Review of Asset Pricing Studies* 1(1), 74–95. | 10.1093/rapstu/rar001 | https://api.crossref.org/works/10.1093/rapstu/rar001 | 24 September 2026 | The benefit of netting depends on the set of positions it runs over; Derive nets only within one underlying. |
| cont2014 | Cont, R., Kokholm, T. (2014). Central Clearing of OTC Derivatives: Bilateral vs Multilateral Netting. *Statistics & Risk Modeling* 31(1), 3–22. | 10.1515/strm-2013-1161 | https://api.crossref.org/works/10.1515/strm-2013-1161 | 24 September 2026 | Measures how a central counterparty changes the expected exposures between dealers: multilateral netting across dealers versus bilateral netting across asset classes (Crossref abstract: "impact … on expected interdealer exposure"). It is about exposures, not capital. Parallel to netting per underlying under PM2: the scope of netting decides what it saves (audit A62). |
| jameson1992 | Jameson, M., Wilhelm, W. (1992). Market Making in the Options Markets and the Costs of Discrete Hedge Rebalancing. *Journal of Finance* 47(2), 765–779. | 10.1111/j.1540-6261.1992.tb04409.x | https://api.crossref.org/works/10.1111/j.1540-6261.1992.tb04409.x | 24 September 2026 | The option spread compensates the maker's unhedgeable risks; a cost component next to capital. |
| santaclara2009 | Santa-Clara, P., Saretto, A. (2009). Option Strategies: Good Deals and Margin Calls. *Journal of Financial Markets* 12(3), 391–417. | 10.1016/j.finmar.2009.01.002 | https://api.crossref.org/works/10.1016/j.finmar.2009.01.002 ; https://ideas.repec.org/a/eee/finmar/v12y2009i3p391-417.html | 24 September 2026 | Apparent excess returns of option strategies shrink sharply once margin requirements apply. This is the idea behind H1, there from the investors' point of view. |
| garleanu2009 | Gârleanu, N., Pedersen, L. H., Poteshman, A. M. (2009). Demand-Based Option Pricing. *Review of Financial Studies* 22(10), 4259–4299. | 10.1093/rfs/hhp005 | https://api.crossref.org/works/10.1093/rfs/hhp005 (taken over from Paper 1, checked again) | 24 September 2026 | Risk-averse makers who cannot hedge perfectly demand a premium; capital is the channel of this premium. |
| muravyev2016 | Muravyev, D. (2016). Order Flow and Expected Option Returns. *Journal of Finance* 71(2), 673–708. | 10.1111/jofi.12380 | https://api.crossref.org/works/10.1111/jofi.12380 (taken over from Paper 1, checked again) | 24 September 2026 | Inventory risk of option makers moves prices; link to marginal cost in the book. |
| christoffersen2018 | Christoffersen, P., Goyenko, R., Jacobs, K., Karoui, M. (2018). Illiquidity Premia in the Equity Options Market. *Review of Financial Studies* 31(3), 811–851. | 10.1093/rfs/hhx113 | https://api.crossref.org/works/10.1093/rfs/hhx113 (taken over from Paper 1, checked again) | 24 September 2026 | Option spreads as compensation for maker risk and tied-up capital, measured per contract. Our denominator is capital instead. |
| soska2021 | Soska, K., Dong, J.-D., Khodaverdian, A., Zetlin-Jones, A., Routledge, B., Christin, N. (2021). Towards Understanding Cryptocurrency Derivatives: A Case Study of BitMEX. In *Proceedings of the Web Conference 2021 (WWW '21)*, ACM, 45–57. | 10.1145/3442381.3450059 | https://api.crossref.org/works/10.1145/3442381.3450059 | 24 September 2026 | Leverage, margin and liquidations at a centralised crypto derivatives exchange, as a comparison with the on-chain engine. BitMEX sets margin as a percentage of notional per position (initial at least 1 %, maintenance θ = 0.0035 for XBTUSD, eqs. 1 to 5 on p. 3; margin requirements are in the public instrument specifications, p. 4); balances are kept in an internal database of the exchange (p. 3). Do not cite it as evidence for an engine that only the operator can compute: the source describes a simple rule that anyone can recompute (audit A14). |
| qin2021 | Qin, K., Zhou, L., Gamito, P., Jovanovic, P., Gervais, A. (2021). An Empirical Study of DeFi Liquidations: Incentives, Risks, and Instabilities. In *Proceedings of the 21st ACM Internet Measurement Conference (IMC '21)*, ACM, 336–350. | 10.1145/3487552.3487811 | https://api.crossref.org/works/10.1145/3487552.3487811 | 24 September 2026 | Margin and liquidation rules as public smart-contract code in DeFi: model for measuring rules directly from the chain. |
| fournier2020 | Fournier, M., Jacobs, K. (2020). A Tractable Framework for Option Pricing with Dynamic Market Maker Inventory and Wealth. *Journal of Financial and Quantitative Analysis* 55(4), 1117–1162. | 10.1017/S0022109019000462 | https://api.crossref.org/works/10.1017/S0022109019000462 (abstract in the Crossref record) | 25 September 2026 | Model of an index option market maker with limited capital: option prices and the variance premium depend on the maker's option holdings and wealth. The closest work on the question "the maker's capital and option prices"; distinguished from ours in the introduction (audit A16). |
| chen2019 | Chen, H., Joslin, S., Ni, S. X. (2019). Demand for Crash Insurance, Intermediary Constraints, and Risk Premia in Financial Markets. *Review of Financial Studies* 32(1), 228–265. | 10.1093/rfs/hhy004 | https://api.crossref.org/works/10.1093/rfs/hhy004 ; abstract from NBER WP 25573 | 25 September 2026 | Aggregate intermediary constraints, measured by the net trading of deep out-of-the-money SPX puts between public investors and intermediaries; tighter constraints go with more expensive options. Evidence that intermediary capital moves option prices, at the level of the sector (audit A16). |
| ahn2025 | Ahn, J. (2025). Margin Constraints and Asset Prices. *Review of Finance* 29(1), 141–168. | 10.1093/rof/rfae039 | https://api.crossref.org/works/10.1093/rof/rfae039 (abstract in the Crossref record) | 25 September 2026 | Regulatory changes of margin (clearing mandate 2010, uncleared margin rule 2016) as exogenous shocks in a quasi-experiment; swaption prices respond to them. Model for H4, where parameter changes are the shocks (audit A16). |
| cameron2008 | Cameron, A. C., Gelbach, J. B., Miller, D. L. (2008). Bootstrap-Based Improvements for Inference with Clustered Errors. *Review of Economics and Statistics* 90(3), 414–427. | 10.1162/rest.90.3.414 | https://api.crossref.org/works/10.1162/rest.90.3.414 (taken over from Paper 1, checked again) | 25 September 2026 | Cluster bootstrap over days and wild cluster bootstrap with restricted residuals (H1 to H4; audit A61). |
| mackinnon2017 | MacKinnon, J. G., Webb, M. D. (2017). Wild Bootstrap Inference for Wildly Different Cluster Sizes. *Journal of Applied Econometrics* 32(2), 233–254. | 10.1002/jae.2508 | https://api.crossref.org/works/10.1002/jae.2508 (taken over from Paper 1, checked again) | 25 September 2026 | Wild cluster bootstrap with very unequal cluster sizes; the 141 day clusters of H4 differ in size (audit A61). |
| roodman2019 | Roodman, D., Nielsen, M. Ø., MacKinnon, J. G., Webb, M. D. (2019). Fast and Wild: Bootstrap Inference in Stata Using boottest. *Stata Journal* 19(1), 4–60. | 10.1177/1536867X19830877 | https://api.crossref.org/works/10.1177/1536867X19830877 (taken over from Paper 1, checked again) | 25 September 2026 | Reference for the algorithm of the wild cluster bootstrap with Rademacher weights and restricted residuals, for the number of draws and for the fixed seed (audit A61). |
| burlig2018 | Burlig, F. (2018). Improving Transparency in Observational Social Science Research: A Pre-Analysis Plan Approach. *Economics Letters* 168, 56–60. | 10.1016/j.econlet.2018.03.036 | https://api.crossref.org/works/10.1016/j.econlet.2018.03.036 (taken over from Paper 1, checked again) | 25 September 2026 | Pre-registration as a procedure for observational data whose outcomes exist before the registration (audit A61). |

Note on (e): `soska2021` and `qin2021` are peer-reviewed ACM conference papers, not journal articles. Crossref lists
the subtitle of `qin2021` as a separate field (`subtitle`); the main title there reads "An empirical study of DeFi
liquidations". This search found no peer-reviewed journal article on portfolio margin for on-chain options. There
are only arXiv preprints (e.g. arXiv:2512.19113, arXiv:2605.19146); they were neither checked nor included.

## Checked but not included (reserve)

The metadata match Crossref and the DOI resolves (24 September 2026, `he2017` on 25 September 2026). The entries are
left out of `refs.bib` to keep the list short. Swap one in for a weaker entry if needed.

| Proposed key | Reference | DOI | Reason for the reserve |
|---|---|---|---|
| hardouvelis2002 | Hardouvelis, G. A., Theodossiou, P. (2002). The Asymmetric Relation Between Initial Margin Requirements and Stock Market Volatility Across Bull and Bear Markets. *Review of Financial Studies* 15(5), 1525–1559. | 10.1093/rfs/15.5.1525 | Margin for stock purchases (Reg T), not for derivatives; usable only for H4, as evidence that margin changes move prices. |
| fenn1993 | Fenn, G. W., Kupiec, P. (1993). Prudential Margin Policy in a Futures-Style Settlement System. *Journal of Futures Markets* 13(4), 389–408. | 10.1002/fut.3990130406 | Overlaps with `figlewski1984` and `kupiec1994`. |
| hendershott2014 | Hendershott, T., Menkveld, A. J. (2014). Price Pressures. *Journal of Financial Economics* 114(3), 405–423. | 10.1016/j.jfineco.2014.08.001 | Inventory price pressure in equities; overlaps with `comertonforde2010`. |
| alexander2020 | Alexander, C., Choi, J., Park, H., Sohn, S. (2020). BitMEX Bitcoin Derivatives: Price Discovery, Informational Efficiency, and Hedging Effectiveness. *Journal of Futures Markets* 40(1), 23–43. | 10.1002/fut.22050 | Price discovery, not margin; `soska2021` fits better. |
| he2017 | He, Z., Kelly, B., Manela, A. (2017). Intermediary Asset Pricing: New Evidence from Many Asset Classes. *Journal of Financial Economics* 126(1), 1–35. | 10.1016/j.jfineco.2017.08.002 | Capital ratio of primary dealers as a pricing factor across many asset classes, options included. More general than `chen2019`, which measures intermediary constraints directly in the options market; only if needed, for "intermediary capital" in general. |

Paper 1 also has, checked and under the same keys, `lehar2025`, `makarov2020` and `aramonte2021` for the crypto and
DeFi context. If the manuscript cites them, they are to be taken over unchanged from `paper/refs.bib`.
`cameron2008`, `mackinnon2017`, `roodman2019` and `burlig2018` have been included since 25 September 2026 (audit
A61).

## Left out as not reliable

- He, S., Manela, A., Ross, O., von Wachter, V., "Fundamentals of Perpetual Futures": Crossref knows only the SSRN
  version (10.2139/ssrn.4301150, 2022). This search found no journal version with volume and pages.
- Didisheim, A., "Option Market Making with Inventory Risk: The Effect on Information Diffusion": only SSRN
  (10.2139/ssrn.3626992, 2020), no peer-reviewed version found.
- Hitzemann, S., Hofmann, M., Uhrig-Homburg, M., Wagner, C., "Margin Requirements and Equity Option Returns"
  (SSRN 2789113): relevant (margin premium in the cross-section of option returns, explained by funding-constrained
  dealers), but still a working paper on 25 September 2026. The KIT publication list has it under "Working Papers",
  the CBS research portal as a conference paper (Paris December Finance Meeting 2016). Check again once published;
  next to `ahn2025` it would be the closest evidence on the margin premium in options.
- Cao, J., Jacobs, K., Ke, S., "Derivative Spreads: Evidence from SPX Options" (AFA 2024): working paper; measures
  spreads against volatility and order imbalance, not against capital.
- dblp and the ACM publisher pages could not be retrieved automatically (bot protection, HTTP 403). The two ACM
  entries therefore rest on the Crossref record, the redirect from doi.org to dl.acm.org and matching details found
  by web search (arXiv 2106.06389, UCL Discovery 10150722). Pages 336 to 350 and 45 to 57 agree everywhere.

## Primary sources without DOI

These three entries lie outside the Crossref check. What was checked is that the address resolves and that the
content matches what the entry stands for.

| Key | Reference | Check | Date checked | Why we cite it |
|---|---|---|---|---|
| albiez2026 | Albiez, G. (2026). Who trades against the maker? Adverse selection with counterparty identity on an on-chain options order book. SSRN working paper 7496818, FHNW (`@unpublished`, Paper 1 of this repository, `paper/main.tex`), doi 10.2139/ssrn.7496818 (resolves to https://www.ssrn.com/abstract=7496818, checked on 5 October 2026; the reader audit's B5 asked for a locator). | Own work. The cells of Paper 1 are underlying × delta bucket × tenor bucket without a maker side (`derive_surface/inference_p1.py`, `cell_table`); Paper 1 does not mention capital (`grep -ci capital paper/main.tex` gives 0). The version statement concerns audit A18. | 25 September 2026 | Fills, net edge and buckets. Only the delta and tenor buckets come from Paper 1; the split by maker side is new, and Paper 1 does not ask the capital question (audit A60). |
| derivev2core | Derive (2026). v2-core: Core smart contracts for the Lyra V2 Protocol. GitHub repository derivexyz/v2-core, https://github.com/derivexyz/v2-core/tree/96796a6, commit 96796a6 (96796a61dcb1dc852e25518b00cc1a79fb3caeeb) of 16 February 2026, accessed on 24 September 2026. Business Source License 1.1, licensor Lyra Foundation. | GitHub API: the commit exists (author and commit date 16 February 2026 23:22 UTC, "chore: docs"); repository description "Core smart contracts for the Lyra V2 Protocol"; local clone `data/p2/v2-core/COMMIT.txt` (cloned on 24 September 2026). Both URLs (short and full hash) return HTTP 200. | 25 September 2026 | Contract code of the three managers from which the replica is built (`docs/paper2/DATA_STATUS.md`); supports the description of the rules in section 2 and the phrase "public code" (audit A17). The commit appears only in the entry, not in the running text, because the number check resolves commit tokens against this repository. |
| derivegetmargin | Derive (2026). public/get_margin. Derive API reference, https://docs.derive.xyz/api-reference/subaccounts/publicget_margin, accessed on 24 September 2026. | Page saved on 24 September 2026 (`data/p2/semantik_20260924/docs/publicget_margin.md`) and retrieved live again on 25 September 2026: identical except for the page header. The page calls the values "net margin", explains them as "mark-to-market value minus the requirement" and says "Does not take open-order margin into account". It belongs to the documentation of the "Derive v3 API" (OpenAPI version 0.2.0); the probes ran through the v2 host `api.lyra.finance` with the same method name (`docs/paper2/get_margin_semantics.md`). The older address docs.derive.xyz/reference/post_public-get-margin returns 404. | 25 September 2026 | Endpoint whose response `net = C + V − R` is derived in section 2, and the limit "no open-order margin" (audit A17). |

The style `cas-model2-names` sets a note after the URL in lower case. In both `@misc` entries the first letter of the
note is therefore braced (`{A}ccessed`, `{C}ommit`); in the trial build they appear as "Accessed 24 September 2026."
and "Commit 96796a6 of 16 February 2026, …". Both entries carry the author `{Derive}`, so the text shows
"Derive (2026a)" (API documentation) and "Derive (2026b)" (code).

## Audit addendum (25 September 2026)

This covers findings A15, A16, A17, A60 and A61 from `docs/paper2/AUDIT.md` and the literature part of A14
(`soska2021`). The replacement sentences for `paper2/main.tex` are not here; they go to the revision of the
manuscript, and `main.tex` was not changed for this addendum. A trial build of a copy with all replacement sentences
and the new `refs.bib` ran with tectonic without errors, without overfull boxes and without unresolved citations
(11 instead of 10 pages).

- A15: The three inventory models were checked against the texts (Ho and Stoll via the presentation in
  arXiv:1512.08866, sect. 2.1; Avellaneda and Stoikov in the publisher's text, sect. 2.2 and 2.3; Guéant et al. in
  arXiv:1105.3115, sect. 2). The finding holds, with one qualification: in the stationary variant, Avellaneda and
  Stoikov interpret a parameter as an upper bound q_max. This does not matter for the introduction, where they
  penalise inventory.
- A16: `fournier2020`, `chen2019` and `ahn2025` included; `he2017` in the reserve; Hitzemann et al. and Cao et al.
  under "Left out".
- A17: `derivev2core` and `derivegetmargin` included as `@misc`.
- A60: Both attributions to `albiez2026` confirmed against the code and the text of Paper 1.
- A61: `cameron2008`, `mackinnon2017`, `roodman2019` and `burlig2018` taken over from `paper/refs.bib` character for
  character.

Open points for the author, both to be fixed in Paper 1 and then taken over character for character: `burlig2018`
has no `doi` field in `paper/refs.bib` (Crossref: 10.1016/j.econlet.2018.03.036), and the title of `roodman2019`
appears in the style as "… in stata using boottest", because `Stata` is not braced.

Status on 27 September 2026: the `roodman2019` point is settled. Since the Paper 1 revision, `paper/refs.bib` braces
`{Stata}`, and `paper2/refs.bib` took this over in commit `b637822`. `burlig2018` still has no `doi` field.

Status on 30 September 2026: the `burlig2018` point is settled. Both `paper/refs.bib` and `paper2/refs.bib` carry
`doi = {10.1016/j.econlet.2018.03.036}`, checked again against api.crossref.org on 30 September 2026 (title, journal,
volume 168, pages 56–60). The revised PDF of Paper 1 on SSRN (revision of 25 September 2026) still lists the entry without
the DOI; the next build of Paper 1 prints it.
