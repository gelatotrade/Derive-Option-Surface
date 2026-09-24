# Literatur Paper 2: geprüfte Quellen

Stand: 24.09.2026. Datei zu `paper2/refs.bib` (20 Einträge). Geprüft wurden alle Einträge am 24.09.2026. Für jeden
Eintrag wurden Autoren, Jahr, Titel, Zeitschrift, Band, Heft, Seiten und DOI mit dem DOI-Datensatz unter
`https://api.crossref.org/works/<DOI>` abgeglichen. Dazu wurde geprüft, dass `https://doi.org/<DOI>` auf die
Verlagsseite weiterleitet (HTTP 302 an OUP, Elsevier, Wiley, Springer, Taylor & Francis, De Gruyter oder ACM). Bei
vier Einträgen kam RePEc (IDEAS) als zweite Quelle dazu. Die Datei wurde mit `cas-dc` und `cas-model2-names` per
tectonic gebaut, fehlerfrei. Alle 20 Einträge erscheinen korrekt, auch die SICI-DOI von `kupiec1996`.

Bei Zeitschriften mit Online-Vorabveröffentlichung gilt das Jahr des Hefts: `brunnermeier2009` (online 2008),
`gueant2013` (online 2012), `christoffersen2018` (online 2017), `alexander2020` (Reserve, online 2019).

Die Schlüssel `garleanu2009`, `muravyev2016` und `christoffersen2018` stammen aus Paper 1 (`paper/refs.bib`). Sie
sind dort und hier Zeichen für Zeichen gleich; per `diff` geprüft.

## Aufgenommene Quellen

| Schlüssel | Vollständige Angabe | DOI | Prüfquelle | Prüfdatum | Wozu wir sie zitieren |
|---|---|---|---|---|---|
| brunnermeier2009 | Brunnermeier, M. K., Pedersen, L. H. (2009). Market Liquidity and Funding Liquidity. *Review of Financial Studies* 22(6), 2201–2238. | 10.1093/rfs/hhn098 | https://api.crossref.org/works/10.1093/rfs/hhn098 | 24.09.2026 | Margin als Finanzierungsbeschränkung des Liquiditätsgebers: Das Kapital, das ein Fill bindet, begrenzt die Liquidität, die der Maker stellen kann. |
| garleanu2011 | Gârleanu, N., Pedersen, L. H. (2011). Margin-Based Asset Pricing and Deviations from the Law of One Price. *Review of Financial Studies* 24(6), 1980–2022. | 10.1093/rfs/hhr027 | https://api.crossref.org/works/10.1093/rfs/hhr027 | 24.09.2026 | Die geforderte Rendite hängt von der Margin ab, die ein Wertpapier bindet. Das begründet, Edge je Kapital statt je Kontrakt zu messen. |
| ho1981 | Ho, T., Stoll, H. R. (1981). Optimal Dealer Pricing under Transactions and Return Uncertainty. *Journal of Financial Economics* 9(1), 47–73. | 10.1016/0304-405X(81)90020-9 | https://api.crossref.org/works/10.1016/0304-405X(81)90020-9 | 24.09.2026 | Klassisches Inventarmodell: Der Spread entgilt das Inventarrisiko des Dealers. |
| avellaneda2008 | Avellaneda, M., Stoikov, S. (2008). High-Frequency Trading in a Limit Order Book. *Quantitative Finance* 8(3), 217–224. | 10.1080/14697680701381228 | https://api.crossref.org/works/10.1080/14697680701381228 | 24.09.2026 | Das Standardmodell für Quotes mit Inventarrisiko, von dem ein kapitalbewusster Maker ausgeht. |
| gueant2013 | Guéant, O., Lehalle, C.-A., Fernandez-Tapia, J. (2013). Dealing with the Inventory Risk: A Solution to the Market Making Problem. *Mathematics and Financial Economics* 7(4), 477–507. | 10.1007/s11579-012-0087-0 | https://api.crossref.org/works/10.1007/s11579-012-0087-0 | 24.09.2026 | Geschlossene Lösung mit Inventargrenzen in Stück; wir fragen, ob die Grenze bei Derive besser in Kapital zu messen ist (H2). |
| comertonforde2010 | Comerton-Forde, C., Hendershott, T., Jones, C. M., Moulton, P. C., Seasholes, M. S. (2010). Time Variation in Liquidity: The Role of Market-Maker Inventories and Revenues. *Journal of Finance* 65(1), 295–331. | 10.1111/j.1540-6261.2009.01530.x | https://api.crossref.org/works/10.1111/j.1540-6261.2009.01530.x | 24.09.2026 | Empirischer Beleg, dass Inventar und Erträge der Market Maker die Liquidität bestimmen; Vorbild für den Test von Bilanzbeschränkungen (H4). |
| stoikov2009 | Stoikov, S., Sağlam, M. (2009). Option Market Making under Inventory Risk. *Review of Derivatives Research* 12(1), 55–79. | 10.1007/s11147-009-9036-3 | https://api.crossref.org/works/10.1007/s11147-009-9036-3 | 24.09.2026 | Inventarmodell speziell für Optionen: Das Risiko des Buchs, nicht der einzelne Kontrakt, bestimmt die Quotes. Das ist die Logik der Grenzkosten (H2). |
| figlewski1984 | Figlewski, S. (1984). Margins and Market Integrity: Margin Setting for Stock Index Futures and Options. *Journal of Futures Markets* 4(3), 385–416. | 10.1002/fut.3990040307 | https://api.crossref.org/works/10.1002/fut.3990040307 ; https://ideas.repec.org/a/wly/jfutmk/v4y1984i3p385-416.html | 24.09.2026 | Frühe Arbeit zur Margin-Setzung für Index-Futures und -Optionen: Die Margin soll Preisänderungen mit vorgegebener Wahrscheinlichkeit abdecken. Das ist der Vorläufer der Szenario-Engines. |
| kupiec1994 | Kupiec, P. H. (1994). The Performance of S&P 500 Futures Product Margins under the SPAN Margining System. *Journal of Futures Markets* 14(7), 789–811. | 10.1002/fut.3990140704 | https://api.crossref.org/works/10.1002/fut.3990140704 ; https://ideas.repec.org/a/wly/jfutmk/v14y1994i7p789-811.html | 24.09.2026 | Empirische Prüfung von SPAN, der szenariobasierten Portfolio-Margin, deren On-Chain-Gegenstück PM2 ist. |
| kupiec1996 | Kupiec, P. H., White, A. P. (1996). Regulatory Competition and the Efficiency of Alternative Derivative Product Margining Systems. *Journal of Futures Markets* 16(8), 943–968. | 10.1002/(SICI)1096-9934(199612)16:8<943::AID-FUT6>3.0.CO;2-M | https://api.crossref.org/works/10.1002/(sici)1096-9934(199612)16:8%3C943::aid-fut6%3E3.0.co;2-m ; https://ideas.repec.org/a/wly/jfutmk/v16y1996i8p943-968.html | 24.09.2026 | Vergleich von strategiebasierter und portfoliobasierter Margin für dieselben Positionen. Das ist die direkte Vorlage für den Netting-Wert SM gegen PM2 (H3). |
| artzner1999 | Artzner, P., Delbaen, F., Eber, J.-M., Heath, D. (1999). Coherent Measures of Risk. *Mathematical Finance* 9(3), 203–228. | 10.1111/1467-9965.00068 | https://api.crossref.org/works/10.1111/1467-9965.00068 | 24.09.2026 | Szenariobasierte Margin (dort am Beispiel SPAN) als kohärentes Risikomaß; formale Grundlage für die Subadditivität, die Netting im Buch billiger macht. |
| duffie2011 | Duffie, D., Zhu, H. (2011). Does a Central Clearing Counterparty Reduce Counterparty Risk? *Review of Asset Pricing Studies* 1(1), 74–95. | 10.1093/rapstu/rar001 | https://api.crossref.org/works/10.1093/rapstu/rar001 | 24.09.2026 | Der Nutzen von Netting hängt davon ab, worüber verrechnet wird; Derive verrechnet nur innerhalb eines Basiswerts. |
| cont2014 | Cont, R., Kokholm, T. (2014). Central Clearing of OTC Derivatives: Bilateral vs Multilateral Netting. *Statistics & Risk Modeling* 31(1), 3–22. | 10.1515/strm-2013-1161 | https://api.crossref.org/works/10.1515/strm-2013-1161 | 24.09.2026 | Quantifiziert den Kapitaleffekt von Netting über Anlageklassen gegen Netting über Gegenparteien. Das ist die Parallele zu Netting je Basiswert unter PM2. |
| jameson1992 | Jameson, M., Wilhelm, W. (1992). Market Making in the Options Markets and the Costs of Discrete Hedge Rebalancing. *Journal of Finance* 47(2), 765–779. | 10.1111/j.1540-6261.1992.tb04409.x | https://api.crossref.org/works/10.1111/j.1540-6261.1992.tb04409.x | 24.09.2026 | Der Spread von Optionen entgilt nicht absicherbare Risiken des Makers; Kostenkomponente neben dem Kapital. |
| santaclara2009 | Santa-Clara, P., Saretto, A. (2009). Option Strategies: Good Deals and Margin Calls. *Journal of Financial Markets* 12(3), 391–417. | 10.1016/j.finmar.2009.01.002 | https://api.crossref.org/works/10.1016/j.finmar.2009.01.002 ; https://ideas.repec.org/a/eee/finmar/v12y2009i3p391-417.html | 24.09.2026 | Scheinbare Überrenditen von Optionsstrategien schrumpfen stark, sobald Margin-Anforderungen gelten. Das ist die Idee hinter H1, dort aus Sicht der Investoren. |
| garleanu2009 | Gârleanu, N., Pedersen, L. H., Poteshman, A. M. (2009). Demand-Based Option Pricing. *Review of Financial Studies* 22(10), 4259–4299. | 10.1093/rfs/hhp005 | https://api.crossref.org/works/10.1093/rfs/hhp005 (Übernahme aus Paper 1, erneut geprüft) | 24.09.2026 | Risikoaverse Maker, die nicht perfekt absichern können, verlangen eine Prämie; Kapital ist der Kanal dieser Prämie. |
| muravyev2016 | Muravyev, D. (2016). Order Flow and Expected Option Returns. *Journal of Finance* 71(2), 673–708. | 10.1111/jofi.12380 | https://api.crossref.org/works/10.1111/jofi.12380 (Übernahme aus Paper 1, erneut geprüft) | 24.09.2026 | Inventarrisiko der Options-Maker bewegt Preise; Bezug zu den Grenzkosten im Buch. |
| christoffersen2018 | Christoffersen, P., Goyenko, R., Jacobs, K., Karoui, M. (2018). Illiquidity Premia in the Equity Options Market. *Review of Financial Studies* 31(3), 811–851. | 10.1093/rfs/hhx113 | https://api.crossref.org/works/10.1093/rfs/hhx113 (Übernahme aus Paper 1, erneut geprüft) | 24.09.2026 | Optionsspreads als Entgelt für Maker-Risiko und Kapitalbindung, gemessen je Kontrakt. Unser Nenner ist stattdessen das Kapital. |
| soska2021 | Soska, K., Dong, J.-D., Khodaverdian, A., Zetlin-Jones, A., Routledge, B., Christin, N. (2021). Towards Understanding Cryptocurrency Derivatives: A Case Study of BitMEX. In *Proceedings of the Web Conference 2021 (WWW '21)*, ACM, 45–57. | 10.1145/3442381.3450059 | https://api.crossref.org/works/10.1145/3442381.3450059 | 24.09.2026 | Hebel, Margin und Liquidationen an einer zentralen Krypto-Derivatebörse als Vergleich zur öffentlichen On-Chain-Engine. |
| qin2021 | Qin, K., Zhou, L., Gamito, P., Jovanovic, P., Gervais, A. (2021). An Empirical Study of DeFi Liquidations: Incentives, Risks, and Instabilities. In *Proceedings of the 21st ACM Internet Measurement Conference (IMC '21)*, ACM, 336–350. | 10.1145/3487552.3487811 | https://api.crossref.org/works/10.1145/3487552.3487811 | 24.09.2026 | Margin- und Liquidationsregeln als öffentlicher Smart-Contract-Code in DeFi: Vorbild dafür, Regeln direkt aus der Chain zu messen. |

Hinweis zu (e): `soska2021` und `qin2021` sind begutachtete ACM-Konferenzbeiträge, keine Zeitschriftenartikel.
Den Untertitel von `qin2021` führt Crossref als eigenes Feld (`subtitle`), der Haupttitel lautet dort „An empirical
study of DeFi liquidations“. Einen begutachteten Zeitschriftenartikel zu Portfolio-Margin für On-Chain-Optionen hat
diese Recherche nicht gefunden. Es gibt nur arXiv-Preprints (z. B. arXiv:2512.19113, arXiv:2605.19146); sie wurden
weder geprüft noch aufgenommen.

## Geprüft, aber nicht aufgenommen (Reserve)

Die Metadaten stimmen mit Crossref überein und die DOI löst auf (24.09.2026). Die Einträge fehlen in `refs.bib`, damit
die Liste bei 20 bleibt. Bei Bedarf gegen einen schwächeren Eintrag tauschen.

| Vorschlag Schlüssel | Angabe | DOI | Grund für Reserve |
|---|---|---|---|
| hardouvelis2002 | Hardouvelis, G. A., Theodossiou, P. (2002). The Asymmetric Relation Between Initial Margin Requirements and Stock Market Volatility Across Bull and Bear Markets. *Review of Financial Studies* 15(5), 1525–1559. | 10.1093/rfs/15.5.1525 | Margin für Aktienkäufe (Reg T), nicht für Derivate; nur für H4 als Beleg nutzbar, dass Margin-Änderungen Preise bewegen. |
| fenn1993 | Fenn, G. W., Kupiec, P. (1993). Prudential Margin Policy in a Futures-Style Settlement System. *Journal of Futures Markets* 13(4), 389–408. | 10.1002/fut.3990130406 | Überschneidet sich mit `figlewski1984` und `kupiec1994`. |
| hendershott2014 | Hendershott, T., Menkveld, A. J. (2014). Price Pressures. *Journal of Financial Economics* 114(3), 405–423. | 10.1016/j.jfineco.2014.08.001 | Inventar-Preisdruck bei Aktien; überschneidet sich mit `comertonforde2010`. |
| alexander2020 | Alexander, C., Choi, J., Park, H., Sohn, S. (2020). BitMEX Bitcoin Derivatives: Price Discovery, Informational Efficiency, and Hedging Effectiveness. *Journal of Futures Markets* 40(1), 23–43. | 10.1002/fut.22050 | Preisfindung, nicht Margin; `soska2021` passt besser. |

Aus Paper 1 stehen zusätzlich geprüft und mit denselben Schlüsseln bereit: `cameron2008`, `mackinnon2017` und
`roodman2019` für die Cluster- und Wild-Cluster-Bootstrap-Inferenz (H1 bis H4) sowie `lehar2025`, `makarov2020` und
`aramonte2021` für den Krypto- und DeFi-Kontext. Werden sie im Manuskript zitiert, sind sie aus `paper/refs.bib`
unverändert zu übernehmen. Die Liste wächst dann über 20.

## Weggelassen, weil nicht belastbar

- He, S., Manela, A., Ross, O., von Wachter, V., „Fundamentals of Perpetual Futures“: Crossref kennt nur die
  SSRN-Fassung (10.2139/ssrn.4301150, 2022). Eine Zeitschriftenfassung mit Band und Seiten hat diese Recherche nicht
  gefunden.
- Didisheim, A., „Option Market Making with Inventory Risk: The Effect on Information Diffusion“: nur SSRN
  (10.2139/ssrn.3626992, 2020), keine begutachtete Fassung gefunden.
- dblp und die ACM-Verlagsseiten liessen sich nicht automatisch abrufen (Bot-Schutz, HTTP 403). Die beiden
  ACM-Einträge stützen sich deshalb auf den Crossref-Datensatz, die Weiterleitung von doi.org auf dl.acm.org und
  übereinstimmende Angaben in der Websuche (arXiv 2106.06389, UCL Discovery 10150722). Seiten 336–350 bzw. 45–57
  stimmen überall überein.

Nachtrag 25.09.2026: `albiez2026` (Paper 1, Working paper, FHNW) steht als `@unpublished` in `paper2/refs.bib`; ohne DOI und daher ausserhalb der Crossref-Prüfung.
