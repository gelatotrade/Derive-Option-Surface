"""Write docs/paper1/ZAHLENBLATT.md from results/p1 (single source of numbers for the manuscript).

Run from the repository root after `p1 inference`:
    python3 scripts/p1_zahlenblatt.py
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

RESULTS = Path("results/p1")
OUT = Path("docs/paper1/ZAHLENBLATT.md")


def de(x, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "–"
    return f"{x:,.{digits}f}".replace(",", " ").replace(".", ",")


def di(x) -> str:
    """Integer with a thin space as thousands separator."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "–"
    return f"{int(x):,}".replace(",", " ")


def verdict(rejected: bool) -> str:
    return "**abgelehnt**" if rejected else "nicht abgelehnt"


def main() -> None:
    s = json.loads((RESULTS / "summary.json").read_text())
    cells = pd.read_csv(RESULTS / "h4_cells.csv")
    classes = pd.read_csv(RESULTS / "class_means.csv")
    horizons = pd.read_csv(RESULTS / "horizon_means.csv")
    sens = pd.read_csv(RESULTS / "h4_sensitivity.csv")
    h1, h2, h3, h4 = s["H1"], s["H2"], s["H3"], s["H4"]
    lines = [
        "# Zahlenblatt Paper 1", "",
        f"Erzeugt {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M UTC} aus `results/p1` mit `scripts/p1_zahlenblatt.py`. "
        f"Pilotdaten bis 17.09.2026 12:00 UTC. Primärer Horizont {s['horizon']}, Mark-Pfad (b) nach Push-Zeit, "
        f"Cluster Taker-Wallet, B = {s['b']}, Seed {s['seed']}, Perp-Halbspread {de(s['half_spread_bp'], 1)} bp. "
        f"{di(s['fills'])} Fills; ohne Fill-IV (nur Vol-Einheit betroffen): {di(s['missing_vol_unit'])}.", "",
        "## H1 Konzentration der Toxizität", "",
        f"- Top-10-Anteil am aggregierten Maker-Verlust: **{de(100 * h1['top10_share']['share'], 1)} %** "
        f"(90-%-Intervall {de(100 * h1['top10_share']['lo'], 1)} bis {de(100 * h1['top10_share']['hi'], 1)} %), "
        f"Verlustsumme {de(h1['top10_share']['loss_total'], 0)} USDC über {di(h1['top10_share']['wallets'])} Wallets.",
        f"- Grösse über dem 90. Perzentil: Koeffizient {de(h1['size_coefficient']['beta'], 3)} USDC "
        f"(t {de(h1['size_coefficient']['t'], 2)}, p {de(h1['size_coefficient']['p'], 4)}).",
        f"- Sweep: Koeffizient {de(h1['sweep_coefficient']['beta'], 3)} USDC "
        f"(t {de(h1['sweep_coefficient']['t'], 2)}, p {de(h1['sweep_coefficient']['p'], 4)}).",
        f"- Urteil: {verdict(h1['rejected'])}.", "",
        "## H2 Vault-Flow uninformiert", "",
        f"- 30-min-Markout der Vault-Fills: {de(h2['markout_30m']['mean'], 3)} USDC "
        f"(95-%-Intervall {de(h2['markout_30m']['lo'], 3)} bis {de(h2['markout_30m']['hi'], 3)}, p {de(h2['markout_30m']['p'], 4)}, "
        f"{di(h2['markout_30m']['n'])} Fills, {h2['markout_30m']['clusters']} Wallets).",
        f"- VRP-bereinigter Settlement-Markout: {de(h2['settlement_vrp']['mean'], 3)} USDC "
        f"(95-%-Intervall {de(h2['settlement_vrp']['lo'], 3)} bis {de(h2['settlement_vrp']['hi'], 3)}).",
        f"- Urteil: {verdict(h2['rejected'])}.", "",
        "## H3 HYPE vor und nach der Deribit-Listung", "",
        f"- Ereignis 23.06.2026 09:00 UTC, Fenster ±{h3['did']['window_days']} Tage, Zielgrösse Vol-Markout.",
        f"- DiD-Koeffizient {de(h3['did']['beta'], 3)} Vol-Punkte (t {de(h3['did']['t'], 2)}, p {de(h3['did']['p'], 4)}, "
        f"{di(h3['did']['n'])} Fills, {h3['did']['clusters']} Wallets).",
        f"- Placebo-Daten: {h3['did']['placebos']}, davon extremer {de(100 * (h3['did']['placebo_share_more_extreme'] or 0), 1)} %.",
        f"- Urteil: {verdict(h3['rejected'])}.", "",
        "## H4 Netto-Edge je Zelle", "",
        f"- Besetzte Zellen (≥ 200 Fills): {h4['cells']}; davon mit positivem 90-%-Intervall: "
        f"**{de(100 * h4['share_positive'], 1)} %**.",
    ]
    for row in h4["atm_short"]:
        lines.append(f"- ATM-Kurzläufer {row['currency']} 40–60 Δ, ≤ 2 d: {de(row['mean'], 3)} USDC "
                     f"(90-%-Intervall {de(row['lo'], 3)} bis {de(row['hi'], 3)}, {di(row['fills'])} Fills)")
    lines += [f"- Urteil: {verdict(h4['rejected'])}.", "",
              "### Sensitivität des Perp-Halbspreads", "",
              "| Halbspread (bp) | Zellen | Anteil positiv |", "|---|---|---|"]
    for r in sens.itertuples():
        lines.append(f"| {de(r.half_spread_bp, 1)} | {r.cells} | {de(100 * r.share_positive, 1)} % |")
    lines += ["", "## Gegenparteiklassen (30 min, Pfad b)", "",
              "| Klasse | Fills | Halbspread | Adverse Selection | Markout USDC | 95-%-Intervall | Gebühr | Rebate | Hedge | Netto-Edge | Anteil negativ |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in classes.sort_values("mean").iterrows():
        lines.append(f"| {r['class']} | {di(r['fills'])} | {de(r['mean_hs'])} | {de(r['mean_as'])} | {de(r['mean'])} | "
                     f"{de(r['lo'])} bis {de(r['hi'])} | {de(r['mean_fee'])} | {de(r['mean_rebate'])} | "
                     f"{de(r['mean_hedge'])} | {de(r['mean_ne'])} | {de(100 * r['share_negative'], 1)} % |")
    lines += ["", "## Horizonte (Pfad b, Mittelwerte)", "",
              "| Horizont | Fills | USDC | delta-neutral | Vol-Punkte | Pfad (a) USDC |", "|---|---|---|---|---|---|"]
    for r in horizons.itertuples():
        lines.append(f"| {r.horizon} | {di(r.n)} | {de(r.mean, 3)} | {de(r.mean_dn, 3)} | {de(r.mean_vol, 3)} | "
                     f"{de(r.mean_path_a, 3)} |")
    lines += ["", "## Zellen mit dem grössten und kleinsten Netto-Edge", "",
              "| Underlying | Delta | Tenor | Fills | Netto-Edge | 90-%-Intervall |", "|---|---|---|---|---|---|"]
    ranked = cells.sort_values("mean")
    for r in pd.concat([ranked.head(5), ranked.tail(5)]).itertuples():
        lines.append(f"| {r.currency} | {r.delta_bucket} | {r.tenor_bucket} | {di(r.fills)} | {de(r.mean, 3)} | "
                     f"{de(r.lo, 3)} bis {de(r.hi, 3)} |")
    lines += ["", "## Einschränkungen dieser Zahlen", "",
              f"- Pilotstand: Stichprobe bis 17.09.2026 12:00 UTC. Die Zahlen des Manuskripts entstehen erst mit dem "
              f"Stichtag 30.09.2026 08:00 UTC.",
              f"- H2 beruht auf {h2['markout_30m']['clusters']} Vault-Wallets; bei so wenigen Clustern ist der "
              f"Wild-Cluster-Bootstrap unzuverlässig, das Ergebnis ist ein Hinweis, kein Beweis.",
              f"- Pfad (b) ist ein um Minuten verzögerter Mark (onchain-Push je Verfall im Median alle 60 s, Forward der "
              f"Kurve statt Live-Forward). Die Horizonte 1 min und 5 min sind davon am stärksten betroffen; Pfad (a) steht "
              f"in der Horizont-Tabelle daneben.",
              f"- Die Vol-Einheit fehlt für {di(s['missing_vol_unit'])} Fills ohne Fill-IV (Preis ausserhalb der "
              f"Arbitragegrenzen).",
              "- Die Klasse „liquidation“ ist leer: Liquidationen laufen ausserhalb des Trade-Tapes."]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
