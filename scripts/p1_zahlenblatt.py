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
BEFUND = Path("results/p1_befund/gebuehreneinheit.csv")      # scripts/p1_befund_gebuehreneinheit.py
BEFUND_CELLS = Path("data/p1/befund_gebuehreneinheit")       # its intermediate cell tables (not in git)


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


def befund_lines() -> list:
    """Numbers the manuscript quotes from the fee-unit recalculation rather than from results/p1, with their source."""
    if not BEFUND.exists():
        return []
    b = pd.read_csv(BEFUND)
    out = ["", "## Aus der Nachrechnung der Gebühreneinheit (Revision 25.09.2026)", "",
           f"Diese Zahlen stehen nicht in `results/p1`, sondern in `{BEFUND.as_posix()}` "
           "(`scripts/p1_befund_gebuehreneinheit.py`); Quelle je Zeile.", "",
           "Zerlegung je Kontrakt mit B = 9 999 (Abschnitt `decomposition_b9999`, Variante `per_contract`; "
           "Text Abschnitt 3):", "",
           "| Grösse | Mittel USDC | 95-%-Intervall |", "|---|---|---|"]
    dec = b[(b["section"] == "decomposition_b9999") & (b["variant"] == "per_contract")]
    for r in dec.itertuples():
        out.append(f"| {r.item} | {de(r.value, 3)} | {de(r.lo, 3)} bis {de(r.hi, 3)} |")
    pkg = b[(b["section"] == "rfq_package") & (b["variant"] == "per_contract_package")].set_index("item")
    if "decomposition net edge" in pkg.index:
        counts = pkg.loc["h4 cells positive / negative, 1 bp"] if "h4 cells positive / negative, 1 bp" in pkg.index else None
        out += ["", f"- RFQ-Paket (Abschnitt `rfq_package`, Nachtrag 3 Nr. 3): Gebühr über das Paket verteilt, "
                    f"Netto-Edge {de(pkg.loc['decomposition net edge', 'value'], 3)} USDC je Kontrakt"
                    + (f"; Zellen positiv / negativ bei 1 bp {int(counts['value'])} / {int(counts['hi'])}"
                       if counts is not None else "") + "."]
    rows = []
    for bp in (0, 1, 3):
        files = [BEFUND_CELLS / f"cells_per_contract_{bp}bp_{c}.csv" for c in ("BTC", "ETH", "HYPE")]
        if not all(f.exists() for f in files):
            continue
        cells = pd.concat([pd.read_csv(f) for f in files])
        cells = cells[cells["fills"] >= 200]
        strict = int(((cells["mean"] > 0) & (cells["p"] <= 0.10)).sum())
        rows.append(f"| {bp} | {len(cells)} | {int(cells['positive'].sum())} | {strict} "
                    f"({de(100 * strict / len(cells), 1)} %) |")
    if rows:
        out += ["", "Robustheit von H4 nach Wild-p (positives Mittel und p ≤ 0,10, nicht die Regel; aus den "
                    f"Zelltabellen unter `{BEFUND_CELLS.as_posix()}`, Text Abschnitt 5.5):", "",
                "| Halbspread (bp) | Zellen | positiv (Regel) | positiv nach Wild-p |", "|---|---|---|---|"] + rows
    return out


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
        f"{di(s['fills'])} Fills; ohne Fill-IV (nur Vol-Einheit betroffen): {di(s['missing_vol_unit'])}. "
        f"Gebühr und Rebate gehen je Kontrakt ein (Summe des Fills durch seine Menge, Nachtrag 3 vom 25.09.2026).", "",
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
        f"- Zellen positiv / negativ / offen: {int(cells['positive'].sum())} / {int(cells['negative'].sum())} / "
        f"{int((~cells['positive'].astype(bool) & ~cells['negative'].astype(bool)).sum())}; "
        f"mit positivem Mittel und Wild-p ≤ 0,10 (Robustheit, nicht die Regel): "
        f"{int(((cells['p'] <= 0.10) & (cells['mean'] > 0)).sum())} "
        f"({de(100 * ((cells['p'] <= 0.10) & (cells['mean'] > 0)).mean(), 1)} %).",
    ]
    for row in h4["atm_short"]:
        lines.append(f"- ATM-Kurzläufer {row['currency']} 40–60 Δ, ≤ 2 d: {de(row['mean'], 3)} USDC "
                     f"(90-%-Intervall {de(row['lo'], 3)} bis {de(row['hi'], 3)}, Wild-p {de(row['p'], 3)}, "
                     f"{di(row['fills'])} Fills)")
    lines += [f"- Urteil: {verdict(h4['rejected'])}.", "",
              "### Sensitivität des Perp-Halbspreads", "",
              "| Halbspread (bp) | Zellen | Anteil positiv |", "|---|---|---|"]
    for r in sens.itertuples():
        lines.append(f"| {de(r.half_spread_bp, 1)} | {r.cells} | {de(100 * r.share_positive, 1)} % |")
    lines += ["", "## Gegenparteiklassen (30 min, Pfad b)", "",
              "Alle Beträge in USDC je Kontrakt; Gebühr und Rebate je Kontrakt. Das Intervall gilt dem Markout. "
              "Der Netto-Edge der Klasse vault beruht auf 8 Taker-Wallets und wird ohne Intervall berichtet.", "",
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
    lines += befund_lines()
    lines += ["", "## Einschränkungen dieser Zahlen", "",
              f"- Pilotstand: Stichprobe bis 17.09.2026 12:00 UTC. Auf diesem Stand beruhen die Erstfassung des "
              f"Manuskripts (19.09.2026) und die Revision (25.09.2026); der Enddatenlauf mit dem registrierten "
              f"Stichtag 30.09.2026 08:00 UTC steht aus.",
              f"- Die Erstfassung zog Gebühr und Rebate als Summen des Fills vom Markout je Kontrakt ab (Nachtrag 3, "
              f"`docs/paper1/BEFUND_2026-09-25_GEBUEHRENEINHEIT.md`); alle Zahlen hier sind korrigiert.",
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
