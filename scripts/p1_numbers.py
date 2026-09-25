"""Write docs/paper1/NUMBERS.md from results/p1 (single source of numbers for the manuscript).

Run from the repository root after `p1 inference`:
    python3 scripts/p1_numbers.py
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

RESULTS = Path("results/p1")
OUT = Path("docs/paper1/NUMBERS.md")
FINDING = Path("results/p1_finding/fee_units.csv")        # scripts/p1_fee_units_finding.py
FINDING_CELLS = Path("data/p1/fee_units_finding")         # its intermediate cell tables (not in git)
THIN = " "                                           # thousands separator, as \, in the manuscript
MISSING = "n/a"


def num(x, digits: int = 2) -> str:
    """Decimal number with a decimal point and a thin space as thousands separator."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return MISSING
    return f"{x:,.{digits}f}".replace(",", THIN)


def di(x) -> str:
    """Integer with a thin space as thousands separator."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return MISSING
    return f"{int(x):,}".replace(",", THIN)


def verdict(rejected: bool) -> str:
    return "**rejected**" if rejected else "not rejected"


def finding_lines() -> list:
    """Numbers the manuscript quotes from the fee-unit recalculation rather than from results/p1, with their source."""
    if not FINDING.exists():
        return []
    b = pd.read_csv(FINDING)
    out = ["", "## From the recalculation of the fee unit (revision 2026-09-25)", "",
           f"These numbers are not in `results/p1` but in `{FINDING.as_posix()}` "
           "(`scripts/p1_fee_units_finding.py`); the source is given per line.", "",
           "Decomposition per contract with B = 9 999 (section `decomposition_b9999`, variant `per_contract`; "
           "text section 3):", "",
           "| Quantity | Mean USDC | 95 % interval |", "|---|---|---|"]
    dec = b[(b["section"] == "decomposition_b9999") & (b["variant"] == "per_contract")]
    for r in dec.itertuples():
        out.append(f"| {r.item} | {num(r.value, 3)} | {num(r.lo, 3)} to {num(r.hi, 3)} |")
    pkg = b[(b["section"] == "rfq_package") & (b["variant"] == "per_contract_package")].set_index("item")
    if "decomposition net edge" in pkg.index:
        counts = pkg.loc["h4 cells positive / negative, 1 bp"] if "h4 cells positive / negative, 1 bp" in pkg.index else None
        out += ["", f"- RFQ package (section `rfq_package`, addendum 3 no. 3): fee spread over the package, "
                    f"net edge {num(pkg.loc['decomposition net edge', 'value'], 3)} USDC per contract"
                    + (f"; cells positive / negative at 1 bp {int(counts['value'])} / {int(counts['hi'])}"
                       if counts is not None else "") + "."]
    rows = []
    for bp in (0, 1, 3):
        files = [FINDING_CELLS / f"cells_per_contract_{bp}bp_{c}.csv" for c in ("BTC", "ETH", "HYPE")]
        if not all(f.exists() for f in files):
            continue
        cells = pd.concat([pd.read_csv(f) for f in files])
        cells = cells[cells["fills"] >= 200]
        strict = int(((cells["mean"] > 0) & (cells["p"] <= 0.10)).sum())
        rows.append(f"| {bp} | {len(cells)} | {int(cells['positive'].sum())} | {strict} "
                    f"({num(100 * strict / len(cells), 1)} %) |")
    if rows:
        out += ["", "Robustness of H4 by wild p (positive mean and p ≤ 0.10, not the rule; from the cell tables "
                    f"under `{FINDING_CELLS.as_posix()}`, text section 5.5):", "",
                "| Half spread (bp) | Cells | positive (rule) | positive by wild p |", "|---|---|---|---|"] + rows
    return out


def main() -> None:
    s = json.loads((RESULTS / "summary.json").read_text())
    cells = pd.read_csv(RESULTS / "h4_cells.csv")
    classes = pd.read_csv(RESULTS / "class_means.csv")
    horizons = pd.read_csv(RESULTS / "horizon_means.csv")
    sens = pd.read_csv(RESULTS / "h4_sensitivity.csv")
    h1, h2, h3, h4 = s["H1"], s["H2"], s["H3"], s["H4"]
    lines = [
        "# Numbers for paper 1", "",
        f"Generated {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M UTC} from `results/p1` with `scripts/p1_numbers.py`. "
        f"Pilot data up to 2026-09-17 12:00 UTC. Primary horizon {s['horizon']}, mark path (b) by push time, "
        f"clusters by taker wallet, B = {s['b']}, seed {s['seed']}, perp half spread {num(s['half_spread_bp'], 1)} bp. "
        f"{di(s['fills'])} fills; without a fill IV (only the vol unit is affected): {di(s['missing_vol_unit'])}. "
        f"Fee and rebate enter per contract (the sum of the fill divided by its amount, addendum 3 of 2026-09-25).", "",
        "## H1 Concentration of toxicity", "",
        f"- Top-10 share of the aggregate maker loss: **{num(100 * h1['top10_share']['share'], 1)} %** "
        f"(90 % interval {num(100 * h1['top10_share']['lo'], 1)} to {num(100 * h1['top10_share']['hi'], 1)} %), "
        f"total loss {num(h1['top10_share']['loss_total'], 0)} USDC over {di(h1['top10_share']['wallets'])} wallets.",
        f"- Size above the 90th percentile: coefficient {num(h1['size_coefficient']['beta'], 3)} USDC "
        f"(t {num(h1['size_coefficient']['t'], 2)}, p {num(h1['size_coefficient']['p'], 4)}).",
        f"- Sweep: coefficient {num(h1['sweep_coefficient']['beta'], 3)} USDC "
        f"(t {num(h1['sweep_coefficient']['t'], 2)}, p {num(h1['sweep_coefficient']['p'], 4)}).",
        f"- Verdict: {verdict(h1['rejected'])}.", "",
        "## H2 Vault flow is uninformed", "",
        f"- 30 min markout of the vault fills: {num(h2['markout_30m']['mean'], 3)} USDC "
        f"(95 % interval {num(h2['markout_30m']['lo'], 3)} to {num(h2['markout_30m']['hi'], 3)}, p {num(h2['markout_30m']['p'], 4)}, "
        f"{di(h2['markout_30m']['n'])} fills, {h2['markout_30m']['clusters']} wallets).",
        f"- VRP-adjusted settlement markout: {num(h2['settlement_vrp']['mean'], 3)} USDC "
        f"(95 % interval {num(h2['settlement_vrp']['lo'], 3)} to {num(h2['settlement_vrp']['hi'], 3)}).",
        f"- Verdict: {verdict(h2['rejected'])}.", "",
        "## H3 HYPE before and after the Deribit listing", "",
        f"- Event 2026-06-23 09:00 UTC, window ±{h3['did']['window_days']} days, outcome vol markout.",
        f"- DiD coefficient {num(h3['did']['beta'], 3)} vol points (t {num(h3['did']['t'], 2)}, p {num(h3['did']['p'], 4)}, "
        f"{di(h3['did']['n'])} fills, {h3['did']['clusters']} wallets).",
        f"- Placebo dates: {h3['did']['placebos']}, of which more extreme: {num(100 * (h3['did']['placebo_share_more_extreme'] or 0), 1)} %.",
        f"- Verdict: {verdict(h3['rejected'])}.", "",
        "## H4 Net edge per cell", "",
        f"- Occupied cells (≥ 200 fills): {h4['cells']}; of these with a positive 90 % interval: "
        f"**{num(100 * h4['share_positive'], 1)} %**.",
        f"- Cells positive / negative / open: {int(cells['positive'].sum())} / {int(cells['negative'].sum())} / "
        f"{int((~cells['positive'].astype(bool) & ~cells['negative'].astype(bool)).sum())}; "
        f"with a positive mean and wild p ≤ 0.10 (robustness, not the rule): "
        f"{int(((cells['p'] <= 0.10) & (cells['mean'] > 0)).sum())} "
        f"({num(100 * ((cells['p'] <= 0.10) & (cells['mean'] > 0)).mean(), 1)} %).",
    ]
    for row in h4["atm_short"]:
        lines.append(f"- Short-dated ATM {row['currency']} 40-60 Δ, ≤ 2 d: {num(row['mean'], 3)} USDC "
                     f"(90 % interval {num(row['lo'], 3)} to {num(row['hi'], 3)}, wild p {num(row['p'], 3)}, "
                     f"{di(row['fills'])} fills)")
    lines += [f"- Verdict: {verdict(h4['rejected'])}.", "",
              "### Sensitivity to the perp half spread", "",
              "| Half spread (bp) | Cells | Share positive |", "|---|---|---|"]
    for r in sens.itertuples():
        lines.append(f"| {num(r.half_spread_bp, 1)} | {r.cells} | {num(100 * r.share_positive, 1)} % |")
    lines += ["", "## Counterparty classes (30 min, path b)", "",
              "All amounts in USDC per contract; fee and rebate per contract. The interval refers to the markout. "
              "The net edge of the class vault rests on 8 taker wallets and is reported without an interval.", "",
              "| Class | Fills | Half spread | Adverse selection | Markout USDC | 95 % interval | Fee | Rebate | Hedge | Net edge | Share negative |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in classes.sort_values("mean").iterrows():
        lines.append(f"| {r['class']} | {di(r['fills'])} | {num(r['mean_hs'])} | {num(r['mean_as'])} | {num(r['mean'])} | "
                     f"{num(r['lo'])} to {num(r['hi'])} | {num(r['mean_fee'])} | {num(r['mean_rebate'])} | "
                     f"{num(r['mean_hedge'])} | {num(r['mean_ne'])} | {num(100 * r['share_negative'], 1)} % |")
    lines += ["", "## Horizons (path b, means)", "",
              "| Horizon | Fills | USDC | delta-neutral | Vol points | Path (a) USDC |", "|---|---|---|---|---|---|"]
    for r in horizons.itertuples():
        lines.append(f"| {r.horizon} | {di(r.n)} | {num(r.mean, 3)} | {num(r.mean_dn, 3)} | {num(r.mean_vol, 3)} | "
                     f"{num(r.mean_path_a, 3)} |")
    lines += ["", "## Cells with the largest and smallest net edge", "",
              "| Underlying | Delta | Tenor | Fills | Net edge | 90 % interval |", "|---|---|---|---|---|---|"]
    ranked = cells.sort_values("mean")
    for r in pd.concat([ranked.head(5), ranked.tail(5)]).itertuples():
        lines.append(f"| {r.currency} | {r.delta_bucket} | {r.tenor_bucket} | {di(r.fills)} | {num(r.mean, 3)} | "
                     f"{num(r.lo, 3)} to {num(r.hi, 3)} |")
    lines += finding_lines()
    lines += ["", "## Limitations of these numbers", "",
              f"- Pilot state: sample up to 2026-09-17 12:00 UTC. The first version of the manuscript (2026-09-19) "
              f"and the revision (2026-09-25) rest on this state; the final data run with the registered cut-off "
              f"2026-09-30 08:00 UTC is still outstanding.",
              f"- The first version subtracted fee and rebate as sums over the fill from the per-contract markout "
              f"(addendum 3, `docs/paper1/FINDING_2026-09-25_FEE_UNITS.md`); all numbers here are corrected.",
              f"- H2 rests on {h2['markout_30m']['clusters']} vault wallets; with so few clusters the wild cluster "
              f"bootstrap is unreliable, so the result is an indication, not proof.",
              f"- Path (b) is a mark delayed by minutes (on-chain push per expiry every 60 s at the median, the forward "
              f"of the curve instead of the live forward). The 1 min and 5 min horizons are affected most; path (a) is "
              f"shown next to it in the horizon table.",
              f"- The vol unit is missing for {di(s['missing_vol_unit'])} fills without a fill IV (price outside the "
              f"arbitrage bounds).",
              "- The class \"liquidation\" is empty: liquidations happen outside the trade tape."]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
