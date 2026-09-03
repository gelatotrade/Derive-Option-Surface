# Derive Option Surface

Implied-Volatility-Surfaces für **BTC, ETH und HYPE** aus dem Options-Orderbuch von [Derive](https://derive.xyz),
als 3D-Koordinatensystem *(Delta, Laufzeit, IV)*, das sich bewegt, wenn sich das Underlying bewegt, plus die
Frage dahinter: **welche Greeks beschreiben diese Bewegung wirklich?**

Drei Blickwinkel, jeweils als GIF (MP4 daneben in `docs/media/`):

| | Was die Animation zeigt | Datenquelle |
|---|---|---|
| **Live** | Orderbuch-Mids und Surface in Echtzeit, aufgezeichnet über 1,9 h (07:33–09:30 UTC) | Top-of-Book **jeder** lebenden Option alle 20 s (`get_tickers`) |
| **Tape** | Wie die Surface über die letzten 60 Tage gewandert ist (BTC +23 %, ETH +37 % im August) | Jeder Fill des Trade-Tapes (= gekreuzte Quote) + Spot-Feed |
| **Schock** | Mechanik isoliert: Forward ±6 %, Smile-Form eingefroren, Ladder mit Black-76 neu bepreist | Letzter Live-Snapshot |

---

## 1 · Live: Orderbuch-Mid → Surface

Links oben der Derive-Index, links unten das Options-Orderbuch des Front-Weeklys (Mid je Strike, Band = Bid/Ask),
rechts die Surface aus **allen** Optionen des Zeitpunkts. In diesen zwei Stunden bewegte sich der Spot nur um
0,6 % (BTC 77 570–78 045, ETH 2 395–2 412, HYPE 81,8–82,4), entsprechend fein ist die Bewegung; die großen Sprünge
zeigt Abschnitt 2. Die grauen Punkte auf der Surface sind die
Fixed-Strike-Mids, aus denen sie gefittet wurde: auf einer Delta-Achse **gleiten sie**, wenn der Spot läuft, während die
Fläche selbst nur das zeigt, was sich *relativ zum Spot* ändert. Genau diese Trennung ist die Regime-Information (Abschnitt 6).

![BTC live](docs/media/BTC_live.gif)

![ETH live](docs/media/ETH_live.gif)

![HYPE live](docs/media/HYPE_live.gif)

## 2 · Tape: 60 Tage Surface-Historie aus dem Trade-Tape

Derive hält **keine** historischen Orderbuch-Snapshots vor (Abschnitt 4). Aber jeder Fill ist ein Punkt, an dem das
Orderbuch nachweislich *war*. Aus dem kompletten Trade-Tape (590 378 Fills seit Januar 2024) wird alle 12 h die
Surface rekonstruiert: Black-76-Inversion jedes Fills, zeit- und größengewichteter SVI-Fit über ein 24-h-Fenster.
Links unten die Fills hinter dem Front-Smile.

![BTC tape](docs/media/BTC_tape.gif)

![ETH tape](docs/media/ETH_tape.gif)

![HYPE tape](docs/media/HYPE_tape.gif)

## 3 · Schock: was mit Ladder und Surface passiert, wenn *nur* der Spot sich bewegt

Der Forward läuft ±6 % durch, die Smile-Form in Moneyness bleibt (Regime *sticky-delta*), jede zweiseitig quotierte
Option der Ladder wird mit Black-76 neu bepreist. Die Surface ist hier in **Strike-Koordinaten** gezeichnet, damit man
sie *gleiten* sieht (in Delta-Koordinaten wäre sie unter sticky-delta per Konstruktion unbewegt); außerhalb der
quotierten Strikes wird nichts gezeichnet. Die Farbe ist **Δ_MV − Δ_BS = Vega · ∂σ/∂S**, der Betrag, um den der
Black-Scholes-Delta-Hedge wegen des Skews falsch ist (Abschnitt 6): blau, wo der Skew das Delta senkt, rot, wo er es hebt.

![BTC shock](docs/media/BTC_shock_sticky_delta.gif)

![ETH shock](docs/media/ETH_shock_sticky_delta.gif)

![HYPE shock](docs/media/HYPE_shock_sticky_delta.gif)

`--regime sticky_strike` rendert das Gegenstück (Vol je Strike eingefroren, Smile rutscht in Moneyness).

---

## 4 · Datenlage bei Derive

Alles über die öffentliche JSON-RPC/WebSocket-API (`api.lyra.finance`, ohne Wallet). Endpunkte, Parameter und
Retention sind in [`docs/derive_api_notes.md`](docs/derive_api_notes.md) live verifiziert, das Datenschema in
[`data/README.md`](data/README.md).

| Datensatz | Umfang | Datei |
|---|---|---|
| **Trade-Tape** BTC-Optionen | 150 957 Fills, 2024-01-11 → 2026-09-03 | `data/trades/BTC_option_trades.parquet` |
| **Trade-Tape** ETH-Optionen | 397 656 Fills, 2024-01-11 → 2026-09-03 | `data/trades/ETH_option_trades.parquet` |
| **Trade-Tape** HYPE-Optionen | 41 765 Fills, 2025-11-10 → 2026-09-03 | `data/trades/HYPE_option_trades.parquet` |
| **Spot-Feed** je Währung | 1 min (24 h), 5 min (7 d), 15 min (30 d), 1 h (90 d): länger hält Derive nicht vor | `data/spot/*.parquet` |
| **Live-Orderbuch, Top-of-Book** | alle lebenden Optionen (2 008 Instrumente), 348 Zyklen à 20 s: Bid/Ask/Mengen/Mark/IV/Greeks/Index/Forward | `data/live/<CCY>_tickers.parquet` |
| **Live-Orderbuch, Tiefe** | Preis-Level (bis 10 je Seite) von 95 Optionen nahe am Geld, alle 10 s, 553 Zeitscheiben | `data/live/depth.parquet` |
| **Aktuelle Orders, komplett** | alle Preis-Level (bis 20 je Seite) **jeder** lebenden Option: 6 093 ruhende Level in 1 184 Büchern, 2026-09-03 11:53 UTC | `data/live/depth_snapshot.parquet` |

Jeder Fill trägt `trade_price`, `mark_price` und `index_price` zum Zeitpunkt des Fills; Maker- und Taker-Zeile sind auf
die Taker-Zeile dedupliziert (`direction` = Aggressor-Seite; `liquidity_role` zeigt die wenigen Fills ohne Taker-Zeile).

## 5 · Das Surface: warum (Delta, Laufzeit, IV)

Die drei Koordinaten sind die zwei, die eine Option identifizieren, und die eine Zahl, mit der das ganze Orderbuch
sie bepreist:

* **x · Forward-Delta** eines Calls (0,05 … 0,95; Put-Delta = Δ − 1; nicht prämienadjustiert, weil Derive in USDC
  settelt). Delta statt Strike, weil nur so 1-Tages- und 6-Monats-Optionen auf derselben Achse vergleichbar sind, und
  weil der Markt Vol so quotiert (ATM, 25Δ-Risk-Reversal, 25Δ-Butterfly). Das Delta wird aus der **gefitteten** IV
  berechnet, nicht aus dem Mid, sonst rauscht die Achse mit dem Spread. `--axis std` zeigt alternativ die
  standardisierte Moneyness k/(σ√T), `--axis logm` und `--axis strike` die rohen Koordinaten.
* **y · Laufzeit** in Tagen, logarithmisch.
* **z · Implied Volatility** aus dem **Orderbuch-Mid**, nicht aus der Mark der Börse. Mid ist der Preis, auf den sich
  Bid und Ask gerade einigen; die Mark ist ein Modell der Börse.

Pipeline je Zeitstempel (`derive_surface/surface.py`):

1. Top-of-Book aller Optionen → Mid; nur zweiseitige Bücher, relative Spanne ≤ 80 %, |ln(K/F)| ≤ 1,2.
2. Nur die **OTM-Seite** jedes Strikes (Calls über, Puts unter dem Forward): dort liegt die Liquidität, und
   Put-Call-Parität macht die ITM-Seite redundant.
3. **Black-76 auf dem Forward**, den Derive je Verfall liefert (Basis heute: BTC +4 bp bei 8 d, +139 bp bei 113 d, +386 bp bei 295 d; ETH +4 / +94 / +317 bp; HYPE +5 / +130 / +243 bp), mit Diskontfaktor;
   Bisektion für IV von Mid, Bid und Ask. Unsere Bid-/Ask-IVs treffen Derives eigene `bid_iv`/`ask_iv` auf < 1 · 10⁻⁴.
4. Gewicht je Quote = 1 / (Ask-IV − Bid-IV)²: enge Bücher zählen, weite Bücher stören nicht.
5. Je Verfall ein Fit von **raw-SVI** in Total-Variance w(k) = a + b·(ρ(k−m) + √((k−m)² + σ²)) (robuste Least-Squares
   mit spreadrelativer Knickstelle, Positivitäts-, Steigungs- und Degenerations-Check, Fallback quadratisch/flach bei
   dünnen Büchern wie bei HYPE). Jenseits der letzten Quote wird der Smile **flach gehalten**, und zwar ab höchstens einer
   halben ATM-Standardabweichung: wir erfinden keine Flügel.
6. Zwischen den Verfällen linear in Total-Variance, mit **Kalender-Constraint** (Total-Variance darf in T nicht fallen;
   der Anteil angehobener Knoten wird protokolliert). Auf der Delta-Achse per Fixpunkt Strike ↔ Delta.

## 6 · Welche Greeks? Erste, zweite oder dritte Ordnung?

**Kurzantwort:** Keine Ordnung von Black-Scholes-Greeks beschreibt, wie sich die Surface mit dem Underlying bewegt.
Delta gehört auf die **Achse**, nicht auf die Fläche. Auf einer Delta-Laufzeit-Fläche sind Gamma, Vanna, Volga (und
erst recht Speed, Zomma, Color, Ultima) fast deterministische Funktionen der Koordinaten (d₁, σ, T): sie als Farbe
aufzutragen färbt die Black-Scholes-Formel ein, nicht den Markt. Die Marktinformation steckt in den **Ableitungen der
Fläche selbst** (Skew ∂σ/∂k, Krümmung) und im **Regime**, also darin, ob die Fläche bei Spot-Bewegung am Strike oder am
Delta klebt.

Deshalb kennt die Färbung neben allen Greeks zwei Flächen-Größen (`--color-by skew|mvdelta`):

| Größe | Bedeutung | Ordnung |
|---|---|---|
| **skew** = ∂σ/∂k | Steigung des gefitteten Smiles: das, was der Markt tatsächlich über die Richtung sagt | Eigenschaft der Fläche |
| **mvdelta** = Δ_MV − Δ_BS = Vega · ∂σ/∂S | Minimum-Variance-Delta (Hull/White) minus Black-Scholes-Delta: um so viele Delta-Punkte ist der BS-Hedge falsch, mit ∂σ/∂S = (SSR − 1) · ∂σ/∂k / F | zweite Ordnung, aber aus der Fläche, nicht aus der Formel |

**Erste Ordnung (Delta, Vega, Theta, Rho)** beschreibt, wie sich der *Preis einer Option* ändert. Delta ist die
Koordinate; Vega ist der Hebel, mit dem jede IV-Änderung durchschlägt, sagt aber nicht, woher sie kommt.

**Zweite Ordnung (Gamma, Vanna, Volga, Charm)** ist die richtige *Ordnung* für die Frage, aber nur, wenn man
Vanna als Vega × Skew der Fläche liest und nicht als Formel. Genau das ist `mvdelta`. Gamma zeigt die Konvexität der
Ladder um den Forward (der „Knick" der Mid-Kurven), Volga die Konvexität in Vol (die Flügel heben sich bei Vol-Schüben
stärker als das Zentrum, sichtbar im August-Sprung des Tape-GIFs).

**Dritte Ordnung (Speed, Zomma, Color, Ultima)** ist implementiert (`pricing.greeks`, `Surface.greeks_grid`), aber
nicht darstellungswürdig: aus einem DEX-Orderbuch nicht messbar, aus der SVI-Fläche nur eine Funktion von fünf
Parametern je Verfall. Gemessen an den letzten Live-Snapshots, Greeks einmal aus der Bid-IV- und einmal aus der
Ask-IV-Fläche (liquider Bereich 10Δ–90Δ, vorzeichenwechselnde Greeks auf ihr Maximum je Laufzeit normiert):

| Ordnung | Greek | BTC (Spread 1,35 vp) | ETH (1,53 vp) | HYPE (7,6 vp) |
|---|---|---|---|---|
| | | Median (75. Perzentil) der relativen Abweichung Bid- vs. Ask-Fläche | | |
| 1 | Delta | 1,7 % (3,4 %) | 1,7 % (3,0 %) | 6,6 % (13,1 %) |
| 1 | Vega | 0,9 % (2,2 %) | 0,9 % (2,0 %) | 3,0 % (7,8 %) |
| 1 | Theta | 2,4 % (3,4 %) | 2,5 % (3,4 %) | 11,4 % (14,2 %) |
| 2 | Gamma | 1,3 % (1,7 %) | 1,5 % (2,0 %) | 6,7 % (8,6 %) |
| 2 | Vanna | 1,6 % (2,5 %) | 1,9 % (2,5 %) | 8,9 % (11,7 %) |
| 2 | Volga | 2,2 % (3,4 %) | 2,4 % (3,6 %) | 12,5 % (17,4 %) |
| 2 | Charm | 0,6 % (1,1 %) | 0,7 % (1,1 %) | 2,9 % (5,1 %) |
| 3 | Speed | 3,0 % (4,5 %) | 3,3 % (4,6 %) | 14,8 % (19,4 %) |
| 3 | Zomma | 2,2 % (3,2 %) | 2,4 % (3,6 %) | 10,3 % (13,7 %) |
| 3 | Color | 1,6 % (2,4 %) | 1,7 % (2,5 %) | 7,0 % (10,4 %) |
| 3 | Ultima | 2,8 % (4,2 %) | 3,2 % (4,7 %) | 15,6 % (23,3 %) |

Bei BTC und ETH ist bis zur zweiten Ordnung alles Signal, die dritte liegt beim Doppelten. Bei HYPE mit 8 Vol-Punkten
Spread sind schon Gamma und Vanna nur aus der geglätteten Fläche lesbar, Volga und alles darüber nicht mehr.

**Regime: messen, nicht annehmen.** Bergomis Skew-Stickiness-Ratio SSR = (dσ_ATM/d ln F) / (∂σ/∂k): 0 = sticky-delta
(der Smile reitet mit dem Forward), 1 = sticky-strike (Vol je Strike eingefroren), ≈ 2 = Stochastic-Vol-Dynamik am
kurzen Ende (Aktienindizes: 1,5–2). Aus unseren Daten, per Regression von ATM-Vol-Änderungen auf Log-Forward-Änderungen:

| Quelle | Laufzeit | BTC SSR (R²) | ETH SSR (R²) | HYPE SSR (R²) |
|---|---|---|---|---|
| Tape, 60 Tage, 12-h-Schritte | 7 d | −1,1 (0,05) | −3,3 (0,15) | +0,7 (0,02) |
| | 30 d | −0,6 (0,01) | −1,2 (0,03) | +1,4 (0,00) |
| | 90 d | n. b. (Skew ≈ 0) | −0,4 (0,00) | n. b. (Skew ≈ 0) |
| Live, 2 h, 100-s-Schritte | 3 d | −1,0 (0,00) | −7,4 (0,29) | −5,5 (0,05) |
| | 8 d | n. b. (Skew ≈ 0) | +0,4 (0,00) | n. b. (Skew ≈ 0) |
| | 30 d | −6,3 (0,07) | −2,4 (0,04) | −2,0 (0,01) |

n. b. = nicht bestimmbar, weil der ATM-Skew dieser Laufzeit nahe null liegt und der Quotient explodiert.

Lesart: Die Bestimmtheitsmaße sind klein, das Vorzeichen wechselt zwischen Laufzeiten und Fenstern. In diesen 60 Tagen
(und in den zwei Live-Stunden) erklärt die Spot-Bewegung nur einen kleinen Teil der ATM-Vol-Änderungen, und bei
positiven Werten mit negativem Skew, wie ETH kurz, steigt die Vol *mit* dem Spot („vol up on up", die Krypto-Signatur
in Rallies), was keines der Lehrbuch-Regime abbildet. Deshalb zeigt das Schock-GIF beide Extreme als Mechanik, und die
Live-Animation führt die Fixed-Strike-Mids als Tracer mit: ihre Bewegung *relativ zur Fläche* ist das Regime.

## 7 · Reproduzieren

```bash
pip install -r requirements.txt
python -m pytest -q                                   # Put-Call-Parität, IV-Roundtrip, alle Greeks vs. finite Differenzen, SVI-Recovery, Kalender-Check

python -m derive_surface download BTC ETH HYPE        # komplettes Trade-Tape + Spot-Historie  (~10 min)
python -m derive_surface record tickers --duration 7200 &   # Top-of-Book alle 20 s
python -m derive_surface record depth   --duration 7200 &   # Preis-Level nahe am Geld
python -m derive_surface depth-snapshot               # alle Orders aller Optionen, jetzt
python -m derive_surface merge

python -m derive_surface animate live  BTC                       # docs/media/BTC_live.gif + .mp4
python -m derive_surface animate live  BTC --color-by skew --suffix _skew
python -m derive_surface animate tape  ETH --days 60 --step-hours 12
python -m derive_surface animate shock HYPE --regime sticky_strike --color-by gamma
python scripts/readme_numbers.py                      # Kennzahlen dieses READMEs aus den Daten
```

Alle Aufrufe brauchen nur die öffentliche API, kein Wallet, kein Key.

## 8 · Repository

```
derive_surface/
  api.py        JSON-RPC/WebSocket-Client (Retry, Slim-Ticker-Parser, Instrumentnamen inkl. Bruch-Strikes wie 77_5)
  history.py    Trade-Tape (paginiert, atomar, resumable) + Spot-Feed → parquet
  recorder.py   Live-Recorder: Top-of-Book je Verfall, WebSocket-Tiefe mit Reconnect, kompletter Depth-Snapshot
  pricing.py    Black-76, IV-Inversion (Bisektion), Greeks 1.–3. Ordnung, Forward-Delta
  surface.py    Quotes → SVI-Smiles → Gitter (Delta / std / log-Moneyness / Strike), Skew, Kalender-Constraint, Greeks je Knoten
  tape.py       Surfaces aus dem Trade-Tape (zeit-/größengewichtet)
  analysis.py   Greek-Rauschmaß (Bid- vs. Ask-Fläche), Skew-Stickiness-Ratio
  animate.py    Frames (Index · Ladder/Smile · 3D-Surface mit Quote-Tracern) → GIF/MP4
  shock.py      Spot-Schock-Szenario (sticky-delta / sticky-strike)
tests/          28 Tests
data/           Trade-Tape, Spot, Live-Aufzeichnung, Depth-Snapshot (parquet, Schema in data/README.md)
docs/           API-Befunde, Medien
scripts/        render_media.sh, readme_numbers.py
```

## 9 · Grenzen

* Historische Orderbuch-Zustände existieren bei Derive nicht; das Tape ist die dichteste öffentliche Spur. Bei HYPE ist es
  an ruhigen Tagen dünn: dann fällt der Fit auf quadratisch/flach zurück oder der Verfall entfällt.
* Im Tape ist der Forward ≈ Index (Derive liefert keinen historischen Forward). Die heutige Basis liegt bei 4–5 bp für eine Woche, 94–139 bp für vier Monate, bis 386 bp für zehn Monate;
  bei HYPE-Laufzeiten über einem Monat verschiebt das die Moneyness-Achse des Tape-Smiles um bis zu einige Prozent.
  Live wird der echte Forward je Verfall benutzt.
* Raw-SVI wird je Verfall unabhängig gefittet; der Kalender-Constraint greift erst auf dem Gitter. Eine gemeinsame
  SSVI-Parametrisierung und eine zeitliche Glättung der Parameter würden Frame-zu-Frame-Zittern weiter senken.
* Der Mid ist bei 8 Vol-Punkten Spread (HYPE) eine Konvention, keine Messung; die Bid/Ask-Fläche (`analysis.surface_from_side`)
  gibt die Bandbreite an.
