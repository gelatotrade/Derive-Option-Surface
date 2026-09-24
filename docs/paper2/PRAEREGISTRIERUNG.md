# Präregistrierung Paper 2: Kapitalbereinigter Edge auf Derive

Festgelegt am 24.09.2026, bevor eine Kapitalzahl des Papiers berechnet wurde. Der Git-Commit dieser Datei ist der
Zeitstempel. Änderungen danach nur als datierter Nachtrag am Ende, nie durch Überschreiben.

## Stichprobe
- Die Fills der Stichprobe von Paper 1 (`docs/paper1/PRAEREGISTRIERUNG.md` mit Nachträgen), also BTC-, ETH- und
  HYPE-Optionen mit Taker-Zeitstempel in [2024-01-11 00:00, 2026-09-30 08:00] UTC und denselben Ausschlüssen.
- Pilotzahlen mit Schnitt 17.09.2026 12:00 UTC wie in Paper 1; der Enddatenlauf folgt gemeinsam mit Paper 1.
- Manager-Fenster: SM über den ganzen Zeitraum (HYPE ab 11.11.2025), Legacy-PM für BTC und ETH über den ganzen
  Zeitraum, PM2 für BTC und ETH ab 12.06.2025 23:00 UTC und für HYPE ab 11.11.2025 00:00 UTC. Das **PM2-Fenster**
  eines Basiswerts ist sein Zeitraum ab diesem Zeitpunkt.

## Semantik und Kapital
- Chain-Semantik: Parameter und Feeds zum Zeitpunkt des Fills (Block aus Taker-Zeitstempel, 2 s je Block ab
  Block 2 454 793 = 11.01.2024 00:00:01 UTC). Je Feed gilt der zuletzt vor diesem Zeitpunkt gepushte Wert (Spot,
  Forward je Verfall, SVI je Verfall, PM2-Zins je Verfall). Kein Ausschluss wegen Feed-Alter; das Alter wird
  mitgeführt. Standard-Lib je Manager; im Maker-Buch die Lib des Kontos.
- Initial Margin ist primär, Maintenance Margin eine Sensitivität.
- Kapital eines Buchs q zu Preisen p: **K_p(q) = Σ_Optionen p_i·q_i − net_IM(q; cash = 0)**, mit net_IM aus dem
  Nachbau des Managers. Perps ohne Prämie, Einstand gleich Perp-Preis der Engine. Nicht-USDC-Collateral bleibt
  ausserhalb.
- **Kapital je Fill:** q = +1 bei Maker-Kauf und −1 bei Maker-Verkauf, p = Fill-Preis, sonst leeres Buch, je
  Kontrakt, unter jedem im Fenster verfügbaren Manager (K_SM, K_PM, K_PM2).
- **Netto-Edge:** NE nach 30 min aus Paper 1 (Nachtrag 2 dort), in USDC je Kontrakt.
- **Zellen:** Basiswert × Maker-Seite (Kauf, Verkauf) × |Δ|-Bucket × Laufzeit-Bucket aus Paper 1; besetzt ab 200
  Fills im jeweiligen Fenster.
- **Edge in bp des Nominals** einer Zelle: 10⁴·Σ NE_i·a_i / Σ Index_i·a_i. **Edge je Kapital** einer Zelle:
  10⁴·Σ NE_i·a_i / Σ K_i·a_i (a = Menge).

## Maker-Bücher
- **Dominante Maker-Subaccounts:** die zehn Subaccounts mit den meisten Maker-Fills in der Stichprobe von Paper 1
  (alle Basiswerte zusammen).
- **Buch zu Tagesbeginn:** on-chain Bestände (`SubAccounts.getAccountBalances`) am ersten Block des UTC-Tags, mit
  Optionen und Perps; Manager des Kontos (`SubAccounts.manager`) am selben Block.
- **Buch vor einem Fill:** Buch zu Tagesbeginn plus alle Fills des Subaccounts (Maker- und Taker-Zeilen) des Tages
  mit früherem Zeitstempel; verfallene Optionen (Verfall ≤ Zeitpunkt) werden entfernt.
- **Grenzkosten:** ΔK = K(Buch nach dem Fill) − K(Buch vor dem Fill), der neue Kontrakt zum Fill-Preis.
- **Netting-Wert eines Maker-Tags:** K des Buchs zu Tagesbeginn unter SM und unter PM2, bestehende Positionen zum
  Mark M_b von Paper 1 (Black-76 auf der zuletzt gepushten SVI-Kurve, Forward `SVI_fwd`, D = 1). Unter PM2 und
  Legacy-PM wird je Basiswert getrennt gerechnet und summiert. Nur Beine von Basiswerten, deren PM2-Fenster am Tag
  offen ist.

## Hypothesen und Ablehnungsregeln
- **H1 Rangfolge:** Über alle besetzten Zellen im PM2-Fenster ist die Spearman-Rangkorrelation ρ zwischen Edge in bp
  des Nominals und Edge je PM2-Kapital kleiner als 0,5. **Abgelehnt**, wenn die obere Grenze des 90-%-Intervalls
  ≥ 0,5 ist.
- **H2 Grenzkosten:** Für die Fills der dominanten Maker-Subaccounts im PM2-Fenster, deren Konto zu Tagesbeginn unter
  PM2 geführt wird, ist der Median von ΔK / K_PM2,Einzel kleiner als 0,5. Fills mit K_PM2,Einzel ≤ 0 werden
  ausgeschlossen und gezählt. Bei mehr als 20 000 Fills gilt eine einfache Zufallsstichprobe von 20 000 (Seed
  20260924). **Abgelehnt**, wenn die obere Grenze des 90-%-Intervalls ≥ 0,5 ist.
- **H3 Netting-Wert:** Über die Maker-Tage der dominanten Subaccounts im PM2-Fenster mit mindestens einer
  Optionsposition ist der Median von K_SM / K_PM2 grösser als 2. Maker-Tage mit K_PM2 ≤ 0 werden ausgeschlossen und
  gezählt. **Abgelehnt**, wenn die untere Grenze des 90-%-Intervalls ≤ 2 ist.
- **H4 Preis des Kapitals:** Wird Kapital durch eine Parameteränderung billiger, sinkt der Halbspread.
  - *Ereignisse:* alle on-chain Parameteränderungen von PM2 je Basiswert im PM2-Fenster und die beiden
    Parameteränderungen des Legacy-PM (12.06.2024, 22.02.2025) für BTC und ETH. Änderungen desselben Basiswerts am
    selben UTC-Tag werden zusammengefasst. Ereignisse, deren grösste absolute Dosis über alle Zellen unter 1 % liegt,
    fallen weg.
  - *Dosis:* d_{c,e} ist das Mittel über die Fills der Zelle c in [e − 14 Tage, e) von
    log(K_nach / K_vor). K_nach und K_vor rechnen denselben Fill mit demselben Marktzustand, einmal mit den Parametern
    nach und einmal vor dem Ereignis, unter dem geänderten Manager.
  - *Ergebnisgrösse:* Halbspread je Fill in bp des Index, y_i = 10⁴·HS_i / Index_i, HS aus Paper 1.
  - *Regression:* Fenster [e − 14 Tage, e + 14 Tage] ohne den Ereignistag; y_i = α_{c,e} + γ_{Tag,Basiswert}
    + β·post_i·d_{c,e} + ε_i. Zellen brauchen mindestens 20 Fills vor und 20 nach dem Ereignis.
  - *Ablehnung:* **abgelehnt**, wenn β nicht positiv ist mit einseitigem Wild-Cluster-Bootstrap-p ≤ 0,05, oder wenn
    β unter 100 Placebo-Terminen nicht über dem 95. Perzentil liegt. Placebo-Termine werden gleichverteilt aus den
    Tagen des Fensters gezogen, die mindestens 28 Tage von jedem Ereignis desselben Basiswerts entfernt sind. Jeder
    Placebo-Termin erhält den Dosisvektor eines zufällig gewählten echten Ereignisses desselben Basiswerts.

## Inferenz
- Intervalle: Perzentil-Intervall eines Cluster-Bootstraps über UTC-Tage, B = 9 999, Seed 20260924. H1 zieht Tage,
  rechnet beide Zellgrössen und ρ in jeder Replikation neu; Zellen ohne Fill in einer Replikation fallen dort weg.
- H4: Wild-Cluster-Bootstrap (Rademacher, restringierte Residuen), Cluster UTC-Tag, B = 9 999, Seed 20260924.
- Alles andere ist explorativ und wird so gekennzeichnet: Karten unter SM und Legacy-PM, MM statt IM, API-Semantik
  mit 2 %, Zeitnormierungen (bis Verfall, empirische Haltedauer), Werte je Basiswert, Oberflächen und Animationen.

## Validierung vor der Messung
- Bevor Kapitalzahlen in einen Test eingehen, wird der Nachbau je Basiswert und verfügbarem Manager an mindestens 48
  Zufallsblöcken gegen `eth_call` geprüft (Einzelkontrakte), die Maker-Bücher an mindestens 20 Maker-Tagen.
- Schwelle: Median der absoluten relativen Abweichung von K unter 0,1 % und 95. Perzentil unter 1 %. Wird sie
  verfehlt, wird die Ursache vor der Inferenz als datierter Nachtrag festgehalten.

## Datenstand vor diesem Commit
- Explorativ berechnet wurden bisher: die Semantik-Proben (`docs/paper2/get_margin_semantik.md`, Netting-Faktoren
  synthetischer Bücher von 2× bis 11×, die in die Schwelle von H3 eingingen) und eine Machbarkeitsprobe unter SM für
  BTC (`data/p2/kontext/oberflaeche/proto_fill_capital.py`: gepoolter Edge je SM-Kapital 41 bp bei Maker-Verkauf,
  74 bp bei Maker-Kauf).
- Nicht berechnet wurden: PM2- und Legacy-PM-Kapital je Fill, Zellwerte für H1, Grenzkosten, Netting-Werte echter
  Maker-Bücher und Dosen.

## Nachtrag 1 (25.09.2026, nach dem Bau der Datenbasis, vor der ersten Kapitalzahl)

1. **Buch vor einem Fill (H2):** Statt „Buch zu Tagesbeginn plus Fills des Tages aus dem Tape“ gilt der exakte
   on-chain Bestand: Snapshot am ersten Block des UTC-Tags plus alle `BalanceAdjusted`-Ereignisse des Kontos bis vor
   die Transaktion des Fills (Optionen und Perps). Grund: Das Options-Tape enthält weder Perp-Fills noch Transfers.
   An 5 000 Fills der H2-Population traf das Tape-Buch den on-chain Bestand nur zu 62,2 % (Optionen 88,4 %, Perps
   70,2 %; `data/p2/books/compare_books.json`), während Snapshot plus Ereignisse an 1 165 von 1 165 Konto-Tagen den
   Folgetag exakt ergibt. Das Tape-Buch wird als Sensitivität berichtet. Der Fill wird über den Zeitstempel der
   eigenen Zeile des Kontos und seine Transaktion gefunden (bei RFQ liegt die Maker-Zeile vor der Taker-Zeile).
2. **Zins je Manager:** PM2 rechnet mit dem PM2-Zins-Feed, der Legacy-PM mit seinem eigenen Zins-Feed (seit dem
   Deploy konstant 0, geprüft per `eth_getLogs`), SM ohne Diskont.
3. **Feed-Alter:** gemessen als Zeitpunkt minus Signaturzeit des Feed-Werts (`feed_ts`), der Uhr der Verträge.
4. **Pseudonyme:** Konten erscheinen in `results/` und im Papier als Rang-Labels (M1 bis M10 nach Maker-Fills)
   bzw. als HMAC mit geheimem Salt. Ein unsalzter SHA-256 kleiner Kontonummern ist durch Durchprobieren umkehrbar.
5. **Feststellung ohne Änderung:** Von den zehn dominanten Maker-Subaccounts werden vier unter PM2 geführt; die
   H2-Population besteht aus deren Fills im PM2-Fenster.
