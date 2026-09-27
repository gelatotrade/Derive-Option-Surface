# Literatur Paper 2: geprüfte Quellen

Stand: 25.09.2026. Datei zu `paper2/refs.bib` (30 Einträge). Die ersten 20 Einträge wurden am 24.09.2026 geprüft,
die sieben nach dem Audit aufgenommenen Artikel (Abschnitt „Nachtrag Audit“ unten) am 25.09.2026. Für jeden
Eintrag wurden Autoren, Jahr, Titel, Zeitschrift, Band, Heft, Seiten und DOI mit dem DOI-Datensatz unter
`https://api.crossref.org/works/<DOI>` abgeglichen. Dazu wurde geprüft, dass `https://doi.org/<DOI>` auf die
Verlagsseite weiterleitet (HTTP 302 an OUP, Elsevier, Wiley, Springer, Taylor & Francis, De Gruyter oder ACM). Bei
vier Einträgen kam RePEc (IDEAS) als zweite Quelle dazu. Die Datei wurde mit `cas-dc` und `cas-model2-names` per
tectonic gebaut, fehlerfrei. Im Bau vom 24.09.2026 erschienen alle 20 damaligen Einträge korrekt, auch die SICI-DOI
von `kupiec1996`; für die später aufgenommenen gilt der Probe-Bau im „Nachtrag Audit“. Drei Einträge
ohne DOI (eigene Arbeit, Vertragscode, API-Doku) stehen unter „Primärquellen ohne DOI“. Die Tests in
`tests/test_p2_refs.py` sichern, dass jeder Eintrag hier als Zeile steht, dass die Zahl oben stimmt, dass die mit
Paper 1 geteilten Einträge zeichengleich sind und dass die geprüften DOIs unverändert bleiben.

Bei Zeitschriften mit Online-Vorabveröffentlichung gilt das Jahr des Hefts: `brunnermeier2009` (online 2008),
`gueant2013` (online 2012), `christoffersen2018` (online 2017), `chen2019` (online 2018), `fournier2020` (online 2019),
`ahn2025` (online 2024), `mackinnon2017` (online 2016), `alexander2020` (Reserve, online 2019).

Die Schlüssel `garleanu2009`, `muravyev2016`, `christoffersen2018`, `cameron2008`, `mackinnon2017`, `roodman2019` und
`burlig2018` stammen aus Paper 1 (`paper/refs.bib`). Sie sind dort und hier Zeichen für Zeichen gleich; geprüft per
`diff` und dauerhaft durch `tests/test_p2_refs.py`.

## Aufgenommene Quellen

| Schlüssel | Vollständige Angabe | DOI | Prüfquelle | Prüfdatum | Wozu wir sie zitieren |
|---|---|---|---|---|---|
| brunnermeier2009 | Brunnermeier, M. K., Pedersen, L. H. (2009). Market Liquidity and Funding Liquidity. *Review of Financial Studies* 22(6), 2201–2238. | 10.1093/rfs/hhn098 | https://api.crossref.org/works/10.1093/rfs/hhn098 | 24.09.2026 | Margin als Finanzierungsbeschränkung des Liquiditätsgebers: Das Kapital, das ein Fill bindet, begrenzt die Liquidität, die der Maker stellen kann. |
| garleanu2011 | Gârleanu, N., Pedersen, L. H. (2011). Margin-Based Asset Pricing and Deviations from the Law of One Price. *Review of Financial Studies* 24(6), 1980–2022. | 10.1093/rfs/hhr027 | https://api.crossref.org/works/10.1093/rfs/hhr027 | 24.09.2026 | Die geforderte Rendite hängt von der Margin ab, die ein Wertpapier bindet. Das begründet, Edge je Kapital statt je Kontrakt zu messen. |
| ho1981 | Ho, T., Stoll, H. R. (1981). Optimal Dealer Pricing under Transactions and Return Uncertainty. *Journal of Financial Economics* 9(1), 47–73. | 10.1016/0304-405X(81)90020-9 | https://api.crossref.org/works/10.1016/0304-405X(81)90020-9 | 24.09.2026 | Klassisches Inventarmodell: Der Spread entgilt das Inventarrisiko des Dealers. Das Inventar ist ein Wertkonto (dI = r_I I dt + p dq_b − p dq_a + I dZ_I), bestraft über die Risikoaversion, ohne Schranke. Zitiert als Modell, das die Position bestraft, nicht begrenzt (Audit A15). |
| avellaneda2008 | Avellaneda, M., Stoikov, S. (2008). High-Frequency Trading in a Limit Order Book. *Quantitative Finance* 8(3), 217–224. | 10.1080/14697680701381228 | https://api.crossref.org/works/10.1080/14697680701381228 | 24.09.2026 | Das Standardmodell für Quotes mit Inventarrisiko, von dem ein kapitalbewusster Maker ausgeht. Inventar q in Stück, bestraft über die exponentielle Nutzenfunktion (Reservationspreis s − qγσ²(T − t)). Das Hauptmodell hat keine Schranke; nur die stationäre Variante (Abschn. 2.3) deutet einen Parameter ω als Obergrenze q_max. Zitiert als Modell, das die Position bestraft (Audit A15). |
| gueant2013 | Guéant, O., Lehalle, C.-A., Fernandez-Tapia, J. (2013). Dealing with the Inventory Risk: A Solution to the Market Making Problem. *Mathematics and Financial Economics* 7(4), 477–507. | 10.1007/s11579-012-0087-0 | https://api.crossref.org/works/10.1007/s11579-012-0087-0 | 24.09.2026 | Geschlossene Lösung mit Inventargrenzen in Stück: harte Schranke q ∈ {−Q, …, Q} „depending in practice on risk limits“ (arXiv:1105.3115, Abschn. 2), zusätzlich CARA-Nutzen. Einziger der drei Inventar-Belege mit Schranke; wir fragen, ob die Grenze bei Derive besser in Kapital zu messen ist (H2). |
| comertonforde2010 | Comerton-Forde, C., Hendershott, T., Jones, C. M., Moulton, P. C., Seasholes, M. S. (2010). Time Variation in Liquidity: The Role of Market-Maker Inventories and Revenues. *Journal of Finance* 65(1), 295–331. | 10.1111/j.1540-6261.2009.01530.x | https://api.crossref.org/works/10.1111/j.1540-6261.2009.01530.x | 24.09.2026 | Empirischer Beleg, dass Inventar und Erträge der Market Maker die Liquidität bestimmen; Vorbild für den Test von Bilanzbeschränkungen (H4). |
| stoikov2009 | Stoikov, S., Sağlam, M. (2009). Option Market Making under Inventory Risk. *Review of Derivatives Research* 12(1), 55–79. | 10.1007/s11147-009-9036-3 | https://api.crossref.org/works/10.1007/s11147-009-9036-3 | 24.09.2026 | Inventarmodell speziell für Optionen: Das Risiko des Buchs, nicht der einzelne Kontrakt, bestimmt die Quotes. Das ist die Logik der Grenzkosten (H2). |
| figlewski1984 | Figlewski, S. (1984). Margins and Market Integrity: Margin Setting for Stock Index Futures and Options. *Journal of Futures Markets* 4(3), 385–416. | 10.1002/fut.3990040307 | https://api.crossref.org/works/10.1002/fut.3990040307 ; https://ideas.repec.org/a/wly/jfutmk/v4y1984i3p385-416.html | 24.09.2026 | Frühe Arbeit zur Margin-Setzung für Index-Futures und -Optionen: Die Margin soll Preisänderungen mit vorgegebener Wahrscheinlichkeit abdecken. Das ist der Vorläufer der Szenario-Engines. |
| kupiec1994 | Kupiec, P. H. (1994). The Performance of S&P 500 Futures Product Margins under the SPAN Margining System. *Journal of Futures Markets* 14(7), 789–811. | 10.1002/fut.3990140704 | https://api.crossref.org/works/10.1002/fut.3990140704 ; https://ideas.repec.org/a/wly/jfutmk/v14y1994i7p789-811.html | 24.09.2026 | Empirische Prüfung von SPAN, der szenariobasierten Portfolio-Margin, deren On-Chain-Gegenstück PM2 ist. |
| kupiec1996 | Kupiec, P. H., White, A. P. (1996). Regulatory Competition and the Efficiency of Alternative Derivative Product Margining Systems. *Journal of Futures Markets* 16(8), 943–968. | 10.1002/(SICI)1096-9934(199612)16:8<943::AID-FUT6>3.0.CO;2-M | https://api.crossref.org/works/10.1002/(sici)1096-9934(199612)16:8%3C943::aid-fut6%3E3.0.co;2-m ; https://ideas.repec.org/a/wly/jfutmk/v16y1996i8p943-968.html | 24.09.2026 | Vergleich von strategiebasierter und portfoliobasierter Margin für dieselben Positionen. Das ist die direkte Vorlage für den Netting-Wert SM gegen PM2 (H3). |
| artzner1999 | Artzner, P., Delbaen, F., Eber, J.-M., Heath, D. (1999). Coherent Measures of Risk. *Mathematical Finance* 9(3), 203–228. | 10.1111/1467-9965.00068 | https://api.crossref.org/works/10.1111/1467-9965.00068 | 24.09.2026 | Szenariobasierte Margin (dort am Beispiel SPAN) als kohärentes Risikomaß; formale Grundlage für die Subadditivität, die Netting im Buch billiger macht. |
| duffie2011 | Duffie, D., Zhu, H. (2011). Does a Central Clearing Counterparty Reduce Counterparty Risk? *Review of Asset Pricing Studies* 1(1), 74–95. | 10.1093/rapstu/rar001 | https://api.crossref.org/works/10.1093/rapstu/rar001 | 24.09.2026 | Der Nutzen von Netting hängt davon ab, worüber verrechnet wird; Derive verrechnet nur innerhalb eines Basiswerts. |
| cont2014 | Cont, R., Kokholm, T. (2014). Central Clearing of OTC Derivatives: Bilateral vs Multilateral Netting. *Statistics & Risk Modeling* 31(1), 3–22. | 10.1515/strm-2013-1161 | https://api.crossref.org/works/10.1515/strm-2013-1161 | 24.09.2026 | Misst, wie eine zentrale Gegenpartei die erwarteten Exposures zwischen Händlern verändert: multilaterales Netting über die Händler gegen bilaterales Netting über Anlageklassen (Crossref-Abstract: „impact … on expected interdealer exposure“). Es geht um Exposures, nicht um Kapital. Parallele zu Netting je Basiswert unter PM2: Der Umfang des Nettings entscheidet, was es einspart (Audit A62). |
| jameson1992 | Jameson, M., Wilhelm, W. (1992). Market Making in the Options Markets and the Costs of Discrete Hedge Rebalancing. *Journal of Finance* 47(2), 765–779. | 10.1111/j.1540-6261.1992.tb04409.x | https://api.crossref.org/works/10.1111/j.1540-6261.1992.tb04409.x | 24.09.2026 | Der Spread von Optionen entgilt nicht absicherbare Risiken des Makers; Kostenkomponente neben dem Kapital. |
| santaclara2009 | Santa-Clara, P., Saretto, A. (2009). Option Strategies: Good Deals and Margin Calls. *Journal of Financial Markets* 12(3), 391–417. | 10.1016/j.finmar.2009.01.002 | https://api.crossref.org/works/10.1016/j.finmar.2009.01.002 ; https://ideas.repec.org/a/eee/finmar/v12y2009i3p391-417.html | 24.09.2026 | Scheinbare Überrenditen von Optionsstrategien schrumpfen stark, sobald Margin-Anforderungen gelten. Das ist die Idee hinter H1, dort aus Sicht der Investoren. |
| garleanu2009 | Gârleanu, N., Pedersen, L. H., Poteshman, A. M. (2009). Demand-Based Option Pricing. *Review of Financial Studies* 22(10), 4259–4299. | 10.1093/rfs/hhp005 | https://api.crossref.org/works/10.1093/rfs/hhp005 (Übernahme aus Paper 1, erneut geprüft) | 24.09.2026 | Risikoaverse Maker, die nicht perfekt absichern können, verlangen eine Prämie; Kapital ist der Kanal dieser Prämie. |
| muravyev2016 | Muravyev, D. (2016). Order Flow and Expected Option Returns. *Journal of Finance* 71(2), 673–708. | 10.1111/jofi.12380 | https://api.crossref.org/works/10.1111/jofi.12380 (Übernahme aus Paper 1, erneut geprüft) | 24.09.2026 | Inventarrisiko der Options-Maker bewegt Preise; Bezug zu den Grenzkosten im Buch. |
| christoffersen2018 | Christoffersen, P., Goyenko, R., Jacobs, K., Karoui, M. (2018). Illiquidity Premia in the Equity Options Market. *Review of Financial Studies* 31(3), 811–851. | 10.1093/rfs/hhx113 | https://api.crossref.org/works/10.1093/rfs/hhx113 (Übernahme aus Paper 1, erneut geprüft) | 24.09.2026 | Optionsspreads als Entgelt für Maker-Risiko und Kapitalbindung, gemessen je Kontrakt. Unser Nenner ist stattdessen das Kapital. |
| soska2021 | Soska, K., Dong, J.-D., Khodaverdian, A., Zetlin-Jones, A., Routledge, B., Christin, N. (2021). Towards Understanding Cryptocurrency Derivatives: A Case Study of BitMEX. In *Proceedings of the Web Conference 2021 (WWW '21)*, ACM, 45–57. | 10.1145/3442381.3450059 | https://api.crossref.org/works/10.1145/3442381.3450059 | 24.09.2026 | Hebel, Margin und Liquidationen an einer zentralen Krypto-Derivatebörse als Vergleich zur On-Chain-Engine. BitMEX setzt Margin als Prozentsatz des Nominals je Position (Initial mindestens 1 %, Maintenance θ = 0,0035 für XBTUSD, Gl. 1 bis 5 auf S. 3; Margin-Anforderungen stehen in den öffentlichen Instrumentenspezifikationen, S. 4); Kontostände führt eine interne Datenbank der Börse (S. 3). Nicht als Beleg für eine Engine zitieren, die nur der Betreiber rechnen kann: Die Quelle beschreibt eine einfache, öffentlich nachrechenbare Regel (Audit A14). |
| qin2021 | Qin, K., Zhou, L., Gamito, P., Jovanovic, P., Gervais, A. (2021). An Empirical Study of DeFi Liquidations: Incentives, Risks, and Instabilities. In *Proceedings of the 21st ACM Internet Measurement Conference (IMC '21)*, ACM, 336–350. | 10.1145/3487552.3487811 | https://api.crossref.org/works/10.1145/3487552.3487811 | 24.09.2026 | Margin- und Liquidationsregeln als öffentlicher Smart-Contract-Code in DeFi: Vorbild dafür, Regeln direkt aus der Chain zu messen. |
| fournier2020 | Fournier, M., Jacobs, K. (2020). A Tractable Framework for Option Pricing with Dynamic Market Maker Inventory and Wealth. *Journal of Financial and Quantitative Analysis* 55(4), 1117–1162. | 10.1017/S0022109019000462 | https://api.crossref.org/works/10.1017/S0022109019000462 (Abstract im Crossref-Datensatz) | 25.09.2026 | Modell eines Index-Options-Market-Makers mit begrenztem Kapital: Optionspreise und Varianzprämie hängen von seinen Optionsbeständen und seinem Vermögen ab. Nächste Arbeit zur Frage „Kapital des Makers und Optionspreise“; Abgrenzung in der Einleitung (Audit A16). |
| chen2019 | Chen, H., Joslin, S., Ni, S. X. (2019). Demand for Crash Insurance, Intermediary Constraints, and Risk Premia in Financial Markets. *Review of Financial Studies* 32(1), 228–265. | 10.1093/rfs/hhy004 | https://api.crossref.org/works/10.1093/rfs/hhy004 ; Abstract aus NBER WP 25573 | 25.09.2026 | Aggregierte Beschränkungen der Intermediäre, gemessen am Nettohandel tief aus dem Geld liegender SPX-Puts zwischen Publikum und Intermediären; engere Beschränkungen gehen mit teureren Optionen einher. Beleg, dass Intermediärskapital Optionspreise bewegt, auf Ebene des Sektors (Audit A16). |
| ahn2025 | Ahn, J. (2025). Margin Constraints and Asset Prices. *Review of Finance* 29(1), 141–168. | 10.1093/rof/rfae039 | https://api.crossref.org/works/10.1093/rof/rfae039 (Abstract im Crossref-Datensatz) | 25.09.2026 | Regulatorische Änderungen der Margin (Clearingpflicht 2010, Uncleared-Margin-Regel 2016) als exogene Schocks in einem Quasi-Experiment; Swaption-Preise reagieren darauf. Vorbild für H4, wo Parameteränderungen die Schocks sind (Audit A16). |
| cameron2008 | Cameron, A. C., Gelbach, J. B., Miller, D. L. (2008). Bootstrap-Based Improvements for Inference with Clustered Errors. *Review of Economics and Statistics* 90(3), 414–427. | 10.1162/rest.90.3.414 | https://api.crossref.org/works/10.1162/rest.90.3.414 (Übernahme aus Paper 1, erneut geprüft) | 25.09.2026 | Cluster-Bootstrap über Tage und Wild-Cluster-Bootstrap mit restringierten Residuen (H1 bis H4; Audit A61). |
| mackinnon2017 | MacKinnon, J. G., Webb, M. D. (2017). Wild Bootstrap Inference for Wildly Different Cluster Sizes. *Journal of Applied Econometrics* 32(2), 233–254. | 10.1002/jae.2508 | https://api.crossref.org/works/10.1002/jae.2508 (Übernahme aus Paper 1, erneut geprüft) | 25.09.2026 | Wild-Cluster-Bootstrap bei sehr ungleichen Clustergrössen; die 141 Tagescluster von H4 sind ungleich gross (Audit A61). |
| roodman2019 | Roodman, D., Nielsen, M. Ø., MacKinnon, J. G., Webb, M. D. (2019). Fast and Wild: Bootstrap Inference in Stata Using boottest. *Stata Journal* 19(1), 4–60. | 10.1177/1536867X19830877 | https://api.crossref.org/works/10.1177/1536867X19830877 (Übernahme aus Paper 1, erneut geprüft) | 25.09.2026 | Referenz für den Algorithmus des Wild-Cluster-Bootstraps mit Rademacher-Gewichten und restringierten Residuen, für die Zahl der Ziehungen und den festen Seed (Audit A61). |
| burlig2018 | Burlig, F. (2018). Improving Transparency in Observational Social Science Research: A Pre-Analysis Plan Approach. *Economics Letters* 168, 56–60. | 10.1016/j.econlet.2018.03.036 (im Eintrag nicht gesetzt, siehe unten) | https://api.crossref.org/works/10.1016/j.econlet.2018.03.036 (Übernahme aus Paper 1, erneut geprüft) | 25.09.2026 | Präregistrierung als Verfahren für Beobachtungsdaten, deren Ergebnisse vor der Registrierung existieren (Audit A61). |

Hinweis zu (e): `soska2021` und `qin2021` sind begutachtete ACM-Konferenzbeiträge, keine Zeitschriftenartikel.
Den Untertitel von `qin2021` führt Crossref als eigenes Feld (`subtitle`), der Haupttitel lautet dort „An empirical
study of DeFi liquidations“. Einen begutachteten Zeitschriftenartikel zu Portfolio-Margin für On-Chain-Optionen hat
diese Recherche nicht gefunden. Es gibt nur arXiv-Preprints (z. B. arXiv:2512.19113, arXiv:2605.19146); sie wurden
weder geprüft noch aufgenommen.

## Geprüft, aber nicht aufgenommen (Reserve)

Die Metadaten stimmen mit Crossref überein und die DOI löst auf (24.09.2026, `he2017` am 25.09.2026). Die Einträge
fehlen in `refs.bib`, damit die Liste kurz bleibt. Bei Bedarf gegen einen schwächeren Eintrag tauschen.

| Vorschlag Schlüssel | Angabe | DOI | Grund für Reserve |
|---|---|---|---|
| hardouvelis2002 | Hardouvelis, G. A., Theodossiou, P. (2002). The Asymmetric Relation Between Initial Margin Requirements and Stock Market Volatility Across Bull and Bear Markets. *Review of Financial Studies* 15(5), 1525–1559. | 10.1093/rfs/15.5.1525 | Margin für Aktienkäufe (Reg T), nicht für Derivate; nur für H4 als Beleg nutzbar, dass Margin-Änderungen Preise bewegen. |
| fenn1993 | Fenn, G. W., Kupiec, P. (1993). Prudential Margin Policy in a Futures-Style Settlement System. *Journal of Futures Markets* 13(4), 389–408. | 10.1002/fut.3990130406 | Überschneidet sich mit `figlewski1984` und `kupiec1994`. |
| hendershott2014 | Hendershott, T., Menkveld, A. J. (2014). Price Pressures. *Journal of Financial Economics* 114(3), 405–423. | 10.1016/j.jfineco.2014.08.001 | Inventar-Preisdruck bei Aktien; überschneidet sich mit `comertonforde2010`. |
| alexander2020 | Alexander, C., Choi, J., Park, H., Sohn, S. (2020). BitMEX Bitcoin Derivatives: Price Discovery, Informational Efficiency, and Hedging Effectiveness. *Journal of Futures Markets* 40(1), 23–43. | 10.1002/fut.22050 | Preisfindung, nicht Margin; `soska2021` passt besser. |
| he2017 | He, Z., Kelly, B., Manela, A. (2017). Intermediary Asset Pricing: New Evidence from Many Asset Classes. *Journal of Financial Economics* 126(1), 1–35. | 10.1016/j.jfineco.2017.08.002 | Kapitalquote der Primary Dealer als Preisfaktor über viele Anlageklassen, Optionen eingeschlossen. Allgemeiner als `chen2019`, das Intermediärsbeschränkungen direkt am Optionsmarkt misst; nur bei Bedarf für „Intermediärskapital“ allgemein. |

Aus Paper 1 stehen zusätzlich geprüft und mit denselben Schlüsseln bereit: `lehar2025`, `makarov2020` und
`aramonte2021` für den Krypto- und DeFi-Kontext. Werden sie im Manuskript zitiert, sind sie aus `paper/refs.bib`
unverändert zu übernehmen. `cameron2008`, `mackinnon2017`, `roodman2019` und `burlig2018` sind seit dem 25.09.2026
aufgenommen (Audit A61).

## Weggelassen, weil nicht belastbar

- He, S., Manela, A., Ross, O., von Wachter, V., „Fundamentals of Perpetual Futures“: Crossref kennt nur die
  SSRN-Fassung (10.2139/ssrn.4301150, 2022). Eine Zeitschriftenfassung mit Band und Seiten hat diese Recherche nicht
  gefunden.
- Didisheim, A., „Option Market Making with Inventory Risk: The Effect on Information Diffusion“: nur SSRN
  (10.2139/ssrn.3626992, 2020), keine begutachtete Fassung gefunden.
- Hitzemann, S., Hofmann, M., Uhrig-Homburg, M., Wagner, C., „Margin Requirements and Equity Option Returns“
  (SSRN 2789113): einschlägig (Margin-Prämie im Querschnitt der Optionsrenditen, erklärt über
  finanzierungsbeschränkte Dealer), aber am 25.09.2026 weiter ein Working Paper. Die Publikationsliste des KIT
  führt es unter „Working Papers“, das CBS-Forschungsportal als Konferenzbeitrag (Paris December Finance Meeting
  2016). Bei Veröffentlichung neu prüfen; es wäre neben `ahn2025` der nächste Beleg zur Margin-Prämie bei Optionen.
- Cao, J., Jacobs, K., Ke, S., „Derivative Spreads: Evidence from SPX Options“ (AFA 2024): Working Paper; misst
  Spreads gegen Volatilität und Orderungleichgewicht, nicht gegen Kapital.
- dblp und die ACM-Verlagsseiten liessen sich nicht automatisch abrufen (Bot-Schutz, HTTP 403). Die beiden
  ACM-Einträge stützen sich deshalb auf den Crossref-Datensatz, die Weiterleitung von doi.org auf dl.acm.org und
  übereinstimmende Angaben in der Websuche (arXiv 2106.06389, UCL Discovery 10150722). Seiten 336–350 bzw. 45–57
  stimmen überall überein.

## Primärquellen ohne DOI

Diese drei Einträge liegen ausserhalb der Crossref-Prüfung. Geprüft wurde, dass die Adresse auflöst und der Inhalt
dem entspricht, wofür der Eintrag steht.

| Schlüssel | Angabe | Prüfung | Prüfdatum | Wozu wir sie zitieren |
|---|---|---|---|---|
| albiez2026 | Albiez, G. (2026). Who trades against the maker? Adverse selection with counterparty identity on an on-chain options order book. Working paper, FHNW (`@unpublished`, Paper 1 dieses Repos, `paper/main.tex`). | Eigene Arbeit. Zellen von Paper 1 sind Basiswert × Delta-Bucket × Tenor-Bucket ohne Maker-Seite (`derive_surface/inference_p1.py`, `cell_table`); Paper 1 erwähnt Kapital nicht (`grep -ci capital paper/main.tex` ergibt 0). Die Fassungsangabe betrifft Audit A18. | 25.09.2026 | Fills, Netto-Edge und Buckets. Nur die Delta- und Tenor-Buckets stammen aus Paper 1, die Teilung nach Maker-Seite ist neu; die Kapitalfrage stellt Paper 1 nicht (Audit A60). |
| derivev2core | Derive (2026). v2-core: Core smart contracts for the Lyra V2 Protocol. GitHub repository derivexyz/v2-core, https://github.com/derivexyz/v2-core/tree/96796a6, Commit 96796a6 (96796a61dcb1dc852e25518b00cc1a79fb3caeeb) vom 16.02.2026, abgerufen am 24.09.2026. Business Source License 1.1, Lizenzgeber Lyra Foundation. | GitHub-API: Commit existiert (Autor- und Commitdatum 16.02.2026 23:22 UTC, „chore: docs“); Repo-Beschreibung „Core smart contracts for the Lyra V2 Protocol“; lokaler Klon `data/p2/v2-core/COMMIT.txt` (geklont 24.09.2026). Beide URLs (Kurz- und Vollhash) liefern HTTP 200. | 25.09.2026 | Vertragscode der drei Manager, aus dem der Nachbau stammt (`docs/paper2/DATENSTAND.md`); belegt die Beschreibung der Regeln in Abschnitt 2 und den Satz „public code“ (Audit A17). Der Commit steht nur im Eintrag, nicht im Fliesstext, weil die Zahlenprüfung Commit-Token gegen dieses Repo auflöst. |
| derivegetmargin | Derive (2026). public/get_margin. Derive API reference, https://docs.derive.xyz/api-reference/subaccounts/publicget_margin, abgerufen am 24.09.2026. | Seite am 24.09.2026 gesichert (`data/p2/semantik_20260924/docs/publicget_margin.md`), am 25.09.2026 live erneut abgerufen: bis auf den Kopf der Seite identisch. Die Seite nennt die Werte „net margin“, erklärt sie als „mark-to-market value minus the requirement“ und sagt „Does not take open-order margin into account“. Sie gehört zur Doku der „Derive v3 API“ (OpenAPI-Version 0.2.0); die Proben liefen über den v2-Host `api.lyra.finance` mit demselben Methodennamen (`docs/paper2/get_margin_semantik.md`). Die ältere Adresse docs.derive.xyz/reference/post_public-get-margin liefert 404. | 25.09.2026 | Endpunkt, dessen Rückgabe `net = C + V − R` Abschnitt 2 herleitet, und Grenze „no open-order margin“ (Audit A17). |

Der Stil `cas-model2-names` setzt eine Notiz nach der URL klein. In beiden `@misc`-Einträgen ist der erste Buchstabe der
Notiz deshalb geklammert (`{A}ccessed`, `{C}ommit`); im Probe-Bau erscheinen sie als „Accessed 24 September 2026.“
und „Commit 96796a6 of 16 February 2026, …“. Beide Einträge tragen den Autor `{Derive}`, im Text also „Derive (2026a)“
(API-Doku) und „Derive (2026b)“ (Code).

## Nachtrag Audit (25.09.2026)

Behandelt sind die Befunde A15, A16, A17, A60 und A61 aus `docs/paper2/AUDIT.md` sowie der Literaturteil von A14
(`soska2021`). Die Ersatzsätze für `paper2/main.tex` stehen nicht hier, sondern gehen an die Überarbeitung des
Manuskripts; `main.tex` wurde für diesen Nachtrag nicht geändert. Ein Probe-Bau einer Kopie mit allen Ersatzsätzen und
der neuen `refs.bib` lief mit tectonic ohne Fehler, ohne Overfull-Box und ohne offene Zitate (11 statt 10 Seiten).

- A15: Die drei Inventarmodelle wurden an den Texten geprüft (Ho und Stoll über die Darstellung in arXiv:1512.08866,
  Abschn. 2.1; Avellaneda und Stoikov im Verlagstext, Abschn. 2.2 und 2.3; Guéant et al. in arXiv:1105.3115,
  Abschn. 2). Der Befund trifft zu; eine Einschränkung: Avellaneda und Stoikov deuten in der stationären Variante
  einen Parameter als Obergrenze q_max. Für die Einleitung trägt das nicht, dort bestrafen sie das Inventar.
- A16: `fournier2020`, `chen2019` und `ahn2025` aufgenommen; `he2017` in der Reserve; Hitzemann et al. und Cao et al.
  unter „Weggelassen“.
- A17: `derivev2core` und `derivegetmargin` als `@misc` aufgenommen.
- A60: Beide Zuschreibungen an `albiez2026` am Code und am Text von Paper 1 bestätigt.
- A61: `cameron2008`, `mackinnon2017`, `roodman2019` und `burlig2018` zeichengleich aus `paper/refs.bib` übernommen.

Offene Punkte für den Autor, beide in Paper 1 zu beheben und dann zeichengleich zu übernehmen: `burlig2018` hat in
`paper/refs.bib` kein Feld `doi` (Crossref: 10.1016/j.econlet.2018.03.036), und der Titel von `roodman2019` erscheint
im Stil als „… in stata using boottest“, weil `Stata` nicht geklammert ist.
