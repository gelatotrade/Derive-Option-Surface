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

## Nachtrag 2 (25.09.2026, vor der ersten Inferenz)

1. **Einheit von Gebühr und Rabatt:** `trade_fee` und `expected_rebate` der Maker-Zeile sind Summen je Fill, nicht
   je Kontrakt (die Taker-Gebühr steigt mit der Menge: Median 0,89 USDC bei ≤ 0,2 Kontrakten, 18,5 bei 1, 49,1 bei
   5 Kontrakten; BTC-Stichprobe). Der Netto-Edge je Kontrakt ist deshalb
   NE_i = MO_30min,i − (fee_maker,i − rebate_maker,i) / a_i − Hedge_i, und NE_i·a_i ist der Edge des Fills in USDC.
   So ist die präregistrierte Definition („in USDC je Kontrakt“) gemeint. Der Code von Paper 1
   (`inference_p1.analysis_frame`) zieht die Summen ungeteilt vom Markout je Kontrakt ab; über alle 603 940 Fills
   ist die mittlere Gebühr dort 1,56 statt 1,09 USDC je Kontrakt und der mittlere Rabatt 0,59 statt 0,77. Paper 2
   verwendet die Form je Kontrakt; die Form aus Paper 1 wird als Sensitivität berichtet. Der Befund geht als
   Korrekturhinweis an Paper 1.

## Nachtrag 3 (25.09.2026, vor der ersten Inferenz): Präzisierungen ohne inhaltliche Änderung

1. **H1-Bootstrap:** Die Menge der Zellen ist die der Originalstichprobe (≥ 200 Fills im PM2-Fenster). In jeder
   Replikation werden die Tage mit Zurücklegen gezogen, beide Zellgrössen aus den gewichteten Tagessummen neu
   gerechnet und ρ über die Zellen mit mindestens einem Fill in der Replikation bestimmt. Intervall: 5. und
   95. Perzentil der 9 999 Replikationen.
2. **H2 und H3:** Intervall für den Median ebenso über gezogene UTC-Tage (alle Fills bzw. Maker-Tage eines
   gezogenen Tages gehen mit dessen Vielfachheit ein).
3. **H4-Placebo:** Eine Placebo-Replikation zieht für jedes behaltene echte Ereignis e einen Placebo-Termin aus den
   zulässigen Tagen seines Basiswerts (mindestens 28 Tage Abstand zu jedem Ereignis dieses Basiswerts) und gibt ihm
   den Dosisvektor eines zufällig gewählten behaltenen Ereignisses desselben Basiswerts; dann wird das Panel wie
   für die echten Ereignisse gebaut und β geschätzt. 100 Replikationen, Seed 20260924.
4. **H4-Fixeffekte:** α je (Zelle, Ereignis), γ je (UTC-Tag, Basiswert); Schätzung durch wechselseitiges
   Herausmitteln (within), Wild-Cluster-Bootstrap mit restringierten Residuen (β = 0), Rademacher-Gewichte je
   UTC-Tag, einseitiges p für β > 0.

## Nachtrag 4 (25.09.2026, nach der Validierung, vor der ersten Teststatistik)

Die Validierung gegen `eth_call` ist bestanden (`docs/paper2/VALIDIERUNG.md`: unter IM Median |rel| 8,7e−10,
p95 1,4e−8 bei Einzelkontrakten; Bücher mit 2 bis 245 Beinen Median 2,2e−9). Offene Lesarten werden hier festgelegt,
bevor eine Teststatistik berechnet wird:

1. **H2-Grösse:** ΔK umfasst den ganzen Fill (q = Maker-Seite × Menge); die Teststatistik ist
   ratio = (ΔK / Menge) / K_PM2,Einzel, also die Grenzkosten je Kontrakt dieses Fills. Die Variante „nächster
   einzelner Kontrakt“ (ratio_unit), die MM-Variante und das Tape-Buch sind Sensitivitäten. Die Stichprobe wurde vor
   dem Ausschluss K_Einzel ≤ 0 gezogen (1 Fill betroffen).
2. **H3:** K_SM und K_PM2 werden auf denselben Beinen gerechnet (Basiswerte mit offenem PM2-Fenster). An 1 431 von
   1 943 Maker-Tagen hält das Buch mehr als 63 Optionen, die ein SM-Konto auf v2 halten kann; K_SM ist dort
   kontrafaktisch. Das wird im Papier genannt, die Teststatistik bleibt unverändert. Legacy-PM nur als Sensitivität
   auf BTC- und ETH-Beinen.
3. **H4-Ereignisse:** Änderungen nur an `CollateralParameters` oder `maxExpiries` gehen nicht in die Ereignisliste
   ein; sie ändern das Kapital eines Einzelkontrakts nicht und fielen unter der 1-%-Regel ohnehin weg. Für den
   Mindestabstand der Placebo-Termine zählen dagegen alle Parameteränderungen des Basiswerts (jede Zeile der
   Zeitlinie), auch weggefallene. Fills mit K ≤ 0 vor oder nach dem Ereignis (10 von 57 151) gehen nicht in das
   Dosismittel ein. Bei zusammengefassten Änderungen eines Tages ist e der Zeitpunkt der ersten Änderung, K_nach
   gilt mit dem Stand nach der letzten.
4. **H1:** Keine Ausschlüsse; die 20 Fills mit K_PM2 ≤ 0 (weit vom Mark bepreiste RFQ-Beine) bleiben in den
   Summen.

## Nachtrag 5 (27.09.2026): Umschreiben der lokalen Historie vor der Veröffentlichung

Dieser Nachtrag entsteht nach allen registrierten Ergebnissen. Er ändert keine Regel der Präregistrierung oder der
Nachträge 1 bis 4, keine Teststatistik und kein Ergebnis. Er hält fest, warum die Commits der Präregistrierung und
der Nachträge 1 bis 4 neue Hashes tragen:

| Fassung | Alter Commit | Neuer Commit | Autor- und Committer-Zeit |
|---|---|---|---|
| Präregistrierung | `1d13227b6f0698f29fcd95d18c5828ae6a0bbc5e` | `cc0a29f655b50c7415e01583b25952e9831bbecd` | 24.09.2026 22:33:50 +0200 |
| Nachtrag 1 | `eb534fe80dea66e651589e1ea01dfdeec6040c47` | `85bb0b7e17a3d32731a83de40ab88b8e012f3983` | 25.09.2026 00:26:54 +0200 |
| Nachtrag 2 | `94652106387bc1f6006e0dbe02ac0a7edb13ea67` | `6005d7c53ccf51d3df7d038025f546eb5d07a6ef` | 25.09.2026 00:29:29 +0200 |
| Nachtrag 3 | `bfc34c81c507c51a38e83878422b89d072f9ed18` | `8778432b49f01532809517d592acda4727d7aaa8` | 25.09.2026 00:29:56 +0200 |
| Nachtrag 4 | `c4fcb59d61b73549aa90cacbd3b997816f36d823` | `e492ba123c4c81ddc478c0c6ef2246867deeeaae` | 25.09.2026 01:29:58 +0200 |

1. **Grund:** Vor der ersten Veröffentlichung wurde die lokale, nie gepushte Historie von Paper 2 umgeschrieben
   (Audit A01, `docs/paper2/AUDIT.md`). Zum einen wurden Kontokennungen entfernt, vor allem aus Test-Fixtures und
   Tests: rohe Kontonummern dominanter Maker-Subaccounts und von PM2-Override-Konten sowie unsalzte, durch
   Durchprobieren umkehrbare Hashes (Nachtrag 1, Punkt 4). Zum anderen setzen die Commits von Paper 2 jetzt auf die
   korrigierte und bereinigte Historie von Paper 1 auf (Zweig `main`), in der auch jüngere Commits von Paper 1 neue
   Hashes tragen. Dadurch hat jeder Commit von Paper 2 einen neuen Hash, auch die fünf Commits der Tabelle.
2. **Bytegleiche Texte:** In jedem der fünf neuen Commits ist diese Datei bytegleich mit der Fassung im alten Commit
   (derselbe Git-Blob, derselbe SHA-256), und der Diff jedes dieser Commits gegenüber seinem Eltern-Commit ist
   derselbe wie im Original. Blob-Hashes und SHA-256 der fünf Fassungen stehen in `docs/paper2/HISTORY_REWRITE.md`.
3. **Zeiten:** Autor und Committer sind mit Name, E-Mail, Datum, Uhrzeit und Zeitzone erhalten; in jedem der fünf
   Commits ist die Autor-Zeit gleich der Committer-Zeit (Tabelle). Es bleiben lokale Zeiten des Rechners des Autors.
   Weil sie erhalten sind, liegen die umgeschriebenen Commits zeitlich vor dem Commit `d2a2b43` auf `main`
   (25.09.2026, 12:37 +0200), auf dem sie jetzt aufsetzen. Die Zeiten geben an, wann die Texte zuerst committet
   wurden.
4. **Öffentlichkeit:** Die alten Commits wurden nie gepusht und werden nicht veröffentlicht, weil sie die entfernten
   Kennungen enthalten; die Zuordnung alt → neu lässt sich daher nur im lokalen Repository des Autors prüfen.
   Öffentlich wird die Präregistrierung erst mit dem Push der umgeschriebenen Historie, also nach den Ergebnissen.
   Einen öffentlichen Zeitstempel vor den Ergebnissen gibt es nicht.
