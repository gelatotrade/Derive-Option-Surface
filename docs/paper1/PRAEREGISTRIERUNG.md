# Präregistrierung Paper 1: Adverse Selection auf Derive

Festgelegt am 17.09.2026, bevor eine Markout-Zahl berechnet wurde. Der Git-Commit dieser Datei ist der Zeitstempel. Änderungen danach nur als datierter Nachtrag am Ende, nie durch Überschreiben.

## Stichprobe
- Fills (Paar aus Maker- und Taker-Zeile derselben `trade_id`) auf BTC-, ETH- und HYPE-Optionen mit Taker-Zeitstempel in [2024-01-11 00:00, 2026-09-30 08:00] UTC.
- Ausschlüsse: `tx_status` ≠ `settled`; Paare mit abweichendem Preis, abweichender Menge oder gleicher Richtung; Fills in den letzten 30 Minuten vor Verfall; Fills ohne Mark-Pfad (b) zum Fill-Zeitpunkt.
- Die neun übrigen Underlyings nur deskriptiv im Anhang.

## Markout
- Maker-Richtung s = +1, wenn der Maker kauft, sonst −1. MO_τ = s · (M(t+τ) − P) in USDC je Kontrakt; negativ = Verlust des Makers.
- Primärer Mark-Pfad (b): Black-76-Preis aus der zuletzt vor t+τ onchain gepushten SVI-Kurve des Verfalls (Formel wie `SVI.sol`, vol = √(w/SVI_refTau)), Forward aus der gleichen Kurve (`SVI_fwd`), Diskontfaktor 1.
- Robustheit: (a) `mark_price` des nächsten Fills desselben Instruments nach t+τ; (c) Settlement-Auszahlung; (d) Deribit-Mark an Tardis-Monatsersten.
- Einheiten: USDC; delta-neutral MO^Δ_τ = MO_τ − s·Δ(t)·(S(t+τ) − S(t)) mit Δ aus Pfad (b) und S = `index_price` des Fills bzw. `SVI_fwd` zum Zeitpunkt t+τ; Vol-Punkte MO^σ_τ = s·(IV_(b)(t+τ) − IV_fill(t)).
- Horizonte: 1 min, 5 min, 30 min, 4 h, 24 h, Settlement. **Primärer Horizont 30 min.**
- VRP-Bereinigung des Settlement-Markouts: Abzug des mittleren Settlement-Markouts aller Fills derselben Zelle (Delta-Bucket × Tenor-Bucket × Underlying × Kalendermonat).

## Zellen und Klassen
- |Δ|-Buckets: [0,10), [10,25), [25,40), [40,60), [60,75), [75,90), [90,100]. Tenor: ≤2 d, (2,7], (7,30], (30,90], >90 d.
- Taker-Klasse mit Vorrang: Liquidation (tx_hash einer Liquidationsauktion) > Vault (Wallet in `docs/paper1/meta/vault_wallets.csv`) > RFQ (`rfq_id` gesetzt) > dominanter Maker (Wallet-Monat mit Maker-Anteil ≥ 80 % am eigenen Notional und ≥ 1 % am Maker-Notional des Monats) > MM-Programm (Wallet mit `total_score` > 0 in einer Options-Programm-Epoche, die den Fill enthält) > Grosswallet (Taker-Notional des Monats ≥ 99. Perzentil der Taker-Wallets des Monats) > Sonstige.
- Sweep: ≥ 5 Fills desselben Takers in ≤ 10 s über ≥ 3 Strikes.

## Hypothesen und Ablehnungsregeln
- **H1 Konzentration:** Die 10 Taker-Wallets mit dem grössten aggregierten negativen 30-min-Markout (USDC) tragen mehr als 50 % davon; Fills über dem 90. Perzentil der Grösse und Sweep-Fills haben einen negativeren Markout als die übrigen. Abgelehnt, wenn die obere Grenze des 90-%-Bootstrap-Intervalls (Resampling über Taker-Wallets, B = 9 999) des Top-10-Anteils unter 50 % liegt, oder wenn der Grössen- bzw. Sweep-Koeffizient in der Panel-Regression (FE Instrument × Tag, Cluster Taker-Wallet) nicht negativ mit |t| ≥ 1,96 ist.
- **H2 Vault-Flow uninformiert:** Mittlerer 30-min-Markout (b) der Vault-Taker-Fills ≥ 0 für den Maker. Abgelehnt, wenn das 95-%-Wild-Cluster-Bootstrap-Intervall vollständig unter 0 liegt. Sekundär derselbe Test für den VRP-bereinigten Settlement-Markout.
- **H3 HYPE vor Referenzmarkt:** Der 30-min-Vol-Markout von HYPE war vor der Deribit-Listung der HYPE_USDC-Optionen negativer als danach, relativ zu BTC/ETH (Differenz-in-Differenzen, Cluster Taker-Wallet). Ereignisdatum: erster Handelstag der HYPE_USDC-Optionen auf Deribit laut offizieller Ankündigung; ist sie nicht auffindbar, der erste Tag mit HYPE_USDC-Optionsdaten bei Tardis. Abgelehnt, wenn der DiD-Koeffizient nicht mit |t| ≥ 1,96 das erwartete Vorzeichen hat oder wenn er unter 100 zufälligen Placebo-Daten (gleiche Fensterlänge, vor der Listung) nicht im äussersten 5-%-Bereich liegt.
- **H4 Zellenabhängiger Netto-Edge:** Netto-Edge NE_30min = Halbspread + MO_30min − Maker-Gebühr + Maker-Rebate − Hedge-Kosten ist in weniger als der Hälfte der besetzten Zellen (≥ 200 Fills) positiv, und in der Zelle BTC/ETH × [40,60) × ≤2 d negativ. Abgelehnt, wenn ≥ 50 % der besetzten Zellen ein positives 90-%-Bootstrap-Intervall haben oder die genannte Zelle ein positives Intervall hat.

## Inferenz
- Wild-Cluster-Bootstrap (Rademacher) mit Cluster Taker-Wallet, B = 9 999, Seed 20260917, Kleinstichprobenkorrektur G/(G−1), p = (1 + #)/(B + 1).
- Alles andere (Tageszeit, VPIN, Inventar-konditionierter Markout, Fill-Finalität) ist explorativ und wird so gekennzeichnet.

## Datenstand vor diesem Commit
- Pilotdaten bis 17.09.2026 12:00 UTC dürfen zum Bau der Pipeline geladen, gepaart und klassifiziert werden. Markouts werden erst nach diesem Commit berechnet.

## Nachtrag 1 (17.09.2026, vor der ersten Markout-Berechnung)

1. **Delta-neutraler Markout:** S(t) und S(t+τ) sind beide der Forward (`SVI_fwd`) der jeweils gültigen SVI-Kurve. Die ursprüngliche Formulierung („`index_price` des Fills bzw. `SVI_fwd` zum Zeitpunkt t+τ“) hätte die Basis zwischen Index und Forward, bis mehrere 100 bp bei langen Laufzeiten, in den Markout getragen.
2. **Datenstand über den Stichtag hinaus:** Tape und SVI-Historie werden bis 01.10.2026 09:00 UTC geladen (Stichtag + 25 h), damit Fills der letzten 24 h vor dem Stichtag alle Horizonte erhalten. Die Stichprobe bleibt auf Taker-Zeitstempel ≤ 30.09.2026 08:00 UTC begrenzt. Settlement-Markouts existieren nur für Verfälle bis zum Datenstand; ein Horizont, der den Verfall erreicht oder überschreitet, ist für Pfad (b) nicht definiert.
3. **Tape-Beginn:** Der Tape beginnt am 06.12.2023; die Stichprobe beginnt unverändert am 11.01.2024.
4. **Pfad (a):** Mark der ersten Fill desselben Instruments mit Zeitstempel ≥ t+τ; der Abstand zum Zielzeitpunkt wird mitgespeichert, damit Auswertungen auf nahe Fills (z. B. ≤ 10 % von τ oder ≤ 5 min) beschränkt werden können.
5. **Sweeps** werden je (Taker-Wallet, Underlying) bestimmt: ein Fill gehört zu einem Sweep, wenn ein 10-s-Fenster ab einem Fill desselben Takers mindestens 5 Fills über mindestens 3 Strikes enthält und der Fill darin liegt.
6. **Grössenmerkmal:** „über dem 90. Perzentil der Grösse“ bezieht sich auf das Notional (Menge × Index) innerhalb des Underlyings über die ganze Stichprobe.

## Nachtrag 2 (18.09.2026, vor der ersten Inferenz)

1. **Ereignisdatum H3:** HYPE_USDC-**Optionen** starteten auf Deribit am **23.06.2026 09:00 UTC** (offizielle Ankündigung „HYPE Derivatives Launching On Deribit“, veröffentlicht 16.06.2026: Perp 16.06. 09:00 UTC, Optionen und datierte Futures 23.06. 09:00 UTC). Das früher notierte Datum 16.06.2026 war der Perp-Start. Die Delivery-Preis-Historie von Deribit umfasst nur 100 Tage und taugt nicht zur Datierung.
2. **Netto-Edge, Zerlegung ohne Doppelzählung:** Der Halbspread ist Teil des Markouts. Es gilt HS = s·(M(t) − P) (Markout zum Horizont 0), Adverse Selection AS_τ = s·(M(t+τ) − M(t)) und MO_τ = HS + AS_τ. Der Netto-Edge ist damit NE_τ = MO_τ − Maker-Gebühr + Maker-Rebate − Hedge-Kosten, mit den **beobachteten** Gebühren und Rebates der Maker-Zeile aus dem Tape. Hedge-Kosten = |Δ(t)|·F(t)·(Perp-Taker-Gebühr 0,03 % + angenommener Perp-Halbspread) + |Δ(t)|·F(t)·Funding-Rate je Stunde·(τ/3600 s); der Perp-Halbspread wird mit 1 bp angesetzt und mit 0 bp und 3 bp als Sensitivität ausgewiesen, die Funding-Rate ist der Median des absoluten Stundenwerts der letzten 30 Tage je Underlying.
3. **H1-Metrik:** Je Taker-Wallet w ist S_w = Σ MO_30min (USDC, Pfad b). L = Σ_{w: S_w < 0} S_w ist der aggregierte Verlust des Makers. Der Top-10-Anteil ist die Summe der zehn kleinsten (negativsten) S_w geteilt durch L. Das 90-%-Intervall entsteht aus einem Cluster-Bootstrap über Wallets (B = 9 999, Seed 20260917).
4. **Intervalle für Mittelwerte:** Für Mittelwerte (H2, Zellen in H4) ist das berichtete Intervall das Perzentil-Intervall eines Cluster-Bootstraps über Taker-Wallets; zusätzlich wird der p-Wert des Wild-Cluster-Bootstraps gegen Null berichtet. Für Regressionskoeffizienten (H1, H3) gilt der Wild-Cluster-Bootstrap (restringierte Residuen, Rademacher).
5. **Ausschluss ohne Fill-IV:** Fills, deren Preis ausserhalb der Arbitragegrenzen von Black-76 liegt und für die deshalb keine Fill-IV existiert (Pilot: 10 745 von 603 940), gehen nicht in die Tests in Vol-Punkten ein; in USDC und delta-neutral bleiben sie enthalten. Die Zahl wird je Test ausgewiesen.
6. **Klasse „liquidation“ ist leer:** Liquidationen werden ausserhalb des Trade-Tapes abgewickelt (27 694 Auktionen, kein Treffer auf einem Options-Fill). Die Klassenanalyse läuft über die sechs verbleibenden Klassen.
