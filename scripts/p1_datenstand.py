"""Write docs/paper1/DATENSTAND.md from the files under data/p1 (counts and checks only, no markouts).

Run from the repository root after `p1 tape`, `p1 ref`, `p1 volfeed`, `p1 fills`:
    python3 scripts/p1_datenstand.py
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from derive_surface.chainfeeds import VOL_FEEDS, load_feed, svi_vol  # noqa: E402
from derive_surface.classify import load_vault_wallets  # noqa: E402

ROOT = Path("data/p1")
OUT = Path("docs/paper1/DATENSTAND.md")
CORE = list(VOL_FEEDS)


def utc(ms: float) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def de(x: float, digits: int = 0) -> str:
    s = f"{x:,.{digits}f}"
    return s.replace(",", " ").replace(".", ",")


def tape_section() -> list:
    manifests = [json.loads(p.read_text()) for p in (ROOT / "raw/tape/option").glob("manifest_*.json")]
    man = max(manifests, key=lambda m: m.get("finished_ms", 0))
    files = json.loads((ROOT / "tape/MANIFEST.json").read_text())
    lines = ["## Options-Tape", "",
             f"Zeitraum {utc(man['from_ms'])} bis {utc(man['to_ms'])} (beide inklusiv), fertig {utc(man['finished_ms'])}. "
             f"{de(man['rows_in_windows'])} Zeilen in {de(man['windows'])} Einzelseiten-Fenstern; "
             f"Tage mit abweichender Nachzählung: {len(man['day_mismatches'])}. "
             f"Die API meldet für den Gesamtzeitraum {de(man['api_count_full_range'])} Zeilen; diese Zahl ist über lange "
             f"Bereiche nicht additiv und dient nur zur Information.", "",
             "| Underlying | Zeilen | SHA-256 (Anfang) |", "|---|---|---|"]
    for name, info in sorted(files.items(), key=lambda kv: -kv[1]["rows"]):
        lines.append(f"| {name.split('_')[0]} | {de(info['rows'])} | `{info['sha256'][:16]}` |")
    return lines


def fills_section() -> list:
    s = json.loads((ROOT / "derived/fills_summary.json").read_text())
    f = pd.read_parquet(ROOT / "derived/fills.parquet",
                        columns=["trade_id", "ts", "ts_maker", "currency", "taker_class", "notional", "is_rfq", "taker_is_vault",
                                 "maker_is_vault", "is_liquidation", "taker_in_mm_programme"])
    lines = ["", "## Fills und Gegenparteiklassen (ohne Markouts)", "",
             f"{de(s['rows'])} Zeilen ergeben {de(s['fills'])} Fills. Zeilen ohne Partner: {s['unpaired_rows']} "
             f"({s['unpaired_trade_ids']} trade_ids); Paare mit abweichendem Preis, abweichender Menge oder gleicher Richtung: "
             f"{s['pair_mismatch']}; nicht settled: {s['not_settled']}. Liquidations-Transaktionen im Abgleich: {s['liquidation_tx']}.", ""]
    tape = pd.concat([pd.read_parquet(p, columns=["trade_id", "timestamp", "instrument_name", "liquidity_role", "wallet"])
                      for p in (ROOT / "tape").glob("*_options_full.parquet")])
    roles = tape.groupby("trade_id")["liquidity_role"].agg(lambda x: ",".join(sorted(x)))
    odd = tape[tape["trade_id"].isin(roles[roles != "maker,taker"].index)]
    if len(odd):
        lines.append("Zeilen ohne Partner: " + "; ".join(
            f"{r.instrument_name} {r.liquidity_role} {utc(r.timestamp)}" for r in odd.sort_values("timestamp").itertuples()) + ".")
        lines.append("")
    core = f[f["currency"].isin(CORE)]
    fills = core.pivot_table(index="taker_class", columns="currency", values="trade_id", aggfunc="size", fill_value=0)
    notional = core.pivot_table(index="taker_class", columns="currency", values="notional", aggfunc="sum", fill_value=0) / 1e6
    lines += ["| Taker-Klasse | " + " | ".join(f"{c} Fills | {c} Notional (Mio USD)" for c in CORE) + " |",
              "|---|" + "---|---|" * len(CORE)]
    for cls in ["liquidation", "vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]:
        cells = []
        for c in CORE:
            n = int(fills.loc[cls, c]) if cls in fills.index and c in fills.columns else 0
            v = float(notional.loc[cls, c]) if cls in notional.index and c in notional.columns else 0.0
            cells.append(f"{de(n)} | {de(v)}")
        lines.append(f"| {cls} | " + " | ".join(cells) + " |")
    lines += ["", f"Flags (Kern): RFQ {de(core['is_rfq'].sum())}, Vault als Taker {de(core['taker_is_vault'].sum())}, "
                  f"Vault als Maker {de(core['maker_is_vault'].sum())}, Liquidation {de(core['is_liquidation'].sum())}, "
                  f"Taker im MM-Programm {de(core['taker_in_mm_programme'].sum())}."]
    first_prog = pd.read_parquet(ROOT / "ref/maker_programs.parquet")["start_ms"].min()
    lines.append(f"Die Klasse MM-Programm ist erst ab {utc(first_prog)} vergebbar; davor liegen "
                 f"{de((core['ts'] < first_prog).sum())} Kern-Fills.")
    lag = (f["ts"] - f["ts_maker"]) / 1000
    for flag, name in [(True, "RFQ"), (False, "Buch")]:
        x = lag[f["is_rfq"] == flag]
        lines.append(f"Zeitabstand Taker- minus Maker-Zeile, {name}: Median {de(x.median(), 1)} s, 99. Perzentil {de(x.quantile(.99), 1)} s, "
                     f"Maximum {de(x.max(), 0)} s.")
    return lines


def vault_section() -> list:
    csv = pd.read_csv("docs/paper1/meta/vault_wallets.csv", comment="#")
    csv["wallet"] = csv["wallet"].str.lower()
    wallets = load_vault_wallets(Path("docs/paper1/meta/vault_wallets.csv"))
    tape = pd.concat([pd.read_parquet(p, columns=["wallet", "liquidity_role", "rfq_id", "trade_amount", "index_price"])
                      for p in (ROOT / "tape").glob("*_options_full.parquet")])
    hit = tape[tape["wallet"].isin(wallets)].assign(notional=lambda d: d["trade_amount"] * d["index_price"])
    lines = ["", "## Vaults", "", f"{len(wallets)} Vault-Wallets gelistet, {hit['wallet'].nunique()} im Tape gesehen, "
             f"{de(len(hit))} Zeilen ({de(100 * len(hit) / len(tape), 2)} % aller Zeilen).", "",
             "| Token | Vault | Maker-Zeilen | Taker-Zeilen | RFQ-Anteil | Notional (Mio USD) |", "|---|---|---|---|---|---|"]
    for r in csv.itertuples():
        h = hit[hit["wallet"] == r.wallet]
        lines.append(f"| {r.token} | {r.vault_name} | {de((h.liquidity_role == 'maker').sum())} | {de((h.liquidity_role == 'taker').sum())} | "
                     f"{'–' if h.empty else de(100 * h['rfq_id'].notna().mean()) + ' %'} | {de(h['notional'].sum() / 1e6, 1)} |")
    stats = sorted((ROOT / "ref").glob("vault_statistics_*.parquet"))
    if stats:
        v = pd.read_parquet(stats[-1])
        lines.append("")
        lines.append(f"TVL laut `get_vault_statistics` ({stats[-1].stem[-8:]}): zusammen {de(v['usd_tvl'].astype(float).sum() / 1e6, 2)} Mio USD.")
    return lines


def ref_section() -> list:
    r = json.loads((ROOT / "ref/REFDATA.json").read_text())
    liq = r["liquidations"]
    auctions = pd.read_parquet(ROOT / "ref/liquidation_auctions.parquet")
    lines = ["", "## Referenzdaten", "", f"Abruf {r['fetched_utc']} UTC.", "",
             "- Settlement-Preise je Underlying: " + ", ".join(f"{k} {v}" for k, v in sorted(r["settlement_prices"].items())) + ".",
             f"- Liquidationen: {liq.get('unique_auctions')} Auktionen aus {liq.get('windows')} Tagesfenstern, {liq.get('bids')} Gebote; "
             f"verbleibende Lücken: {len(liq.get('gaps', []))}"
             + (" (" + ", ".join(f"{utc(a)} bis {utc(b)}" for a, b in liq["gaps"][:10]) + ")" if liq.get("gaps") else "") + "."]
    if len(auctions):
        lines.append(f"  Zeitraum der Auktionen {utc(auctions['start_timestamp'].min())} bis {utc(auctions['start_timestamp'].max())}; "
                     "Liquidationen übertragen Positionen ausserhalb des Trade-Tapes, deshalb trägt kaum ein Options-Fill eine Liquidations-Transaktion.")
    mp = r["maker_programmes"]
    lines += [f"- Maker-Programme: {mp['programmes']} Epochen-Programme, {mp['option_score_rows']} Score-Zeilen für Options-Programme, "
              f"{mp['active_wallets']} Wallets mit Score > 0.",
              f"- Instrument-Gebühren: {r['instruments']} lebende Optionen; Funding-Historie {r['funding_rows']} Stundenwerte (rollierend 30 Tage, wird fortgeschrieben)."]
    return lines


def volfeed_section() -> list:
    lines = ["", "## SVI-Historie (Vol-Feeds)", "",
             "| Underlying | Events | erster Block | letzter Block | erste Kurve | letzte Kurve | Verfälle | Median Push minus Signatur (s) | "
             "Abstand zwischen Pushes je Verfall, Median / 90. Perzentil (s) |",
             "|---|---|---|---|---|---|---|---|---|"]
    monthly = {}
    for ccy in CORE:
        df = load_feed(ROOT / "raw/volfeed", ccy)
        if df.empty:
            lines.append(f"| {ccy} | 0 | – | – | – | – | – | – |")
            continue
        push = (df["block_ts"] - df["feed_ts"])[df["block_ts"] > 0]
        by_push = df[df["block_ts"] > 0].sort_values(["expiry", "block_ts"])
        gaps = by_push.groupby("expiry")["block_ts"].diff().dropna()
        lines.append(f"| {ccy} | {de(len(df))} | {de(df['block'].min())} | {de(df['block'].max())} | {utc(df['feed_ts'].min() * 1000)} | "
                     f"{utc(df['feed_ts'].max() * 1000)} | {df['expiry'].nunique()} | {de(push.median(), 0)} | "
                     f"{de(gaps.median(), 0)} / {de(gaps.quantile(0.9), 0)} |")
        monthly[ccy] = df.groupby(pd.to_datetime(df["feed_ts"], unit="s").dt.strftime("%Y-%m")).size()
    if monthly:
        tab = pd.DataFrame(monthly).fillna(0).astype(int)
        lines += ["", "Events je Monat:", "", "| Monat | " + " | ".join(tab.columns) + " |", "|---|" + "---|" * len(tab.columns)]
        for m, row in tab.iterrows():
            lines.append(f"| {m} | " + " | ".join(de(v) for v in row) + " |")
    return lines


def mark_check_section() -> list:
    """Mark price at fill time rebuilt from the on-chain SVI vs the tape's mark_price (no future data: not a markout)."""
    from derive_surface import pricing
    from derive_surface.markpath import attach_svi

    f = pd.read_parquet(ROOT / "derived/fills.parquet",
                        columns=["trade_id", "ts", "currency", "expiry", "strike", "option_type", "mark_price", "index_price",
                                 "tx_status", "pair_ok"])
    f = f[(f["tx_status"] == "settled") & f["pair_ok"] & (f["expiry"] * 1000 - f["ts"] > 30 * 60_000) & (f["mark_price"] > 0)]
    lines = ["", "## Gegenprobe: Mark zum Fill-Zeitpunkt aus der onchain SVI-Kurve", "",
             "Für jeden Kern-Fill (settled, mehr als 30 min vor Verfall) wird die letzte SVI-Kurve desselben Verfalls gesucht, "
             "nach Push-Zeit (`block_ts`, präregistriert) und nach Signaturzeit (`feed_ts`). Vol aus der Kurve (exakt wie `SVI.sol`), "
             "Preis mit Black-76. Verglichen wird mit dem `mark_price` der Taker-Zeile: als Vol-Abstand (beide Preise über denselben "
             "Forward `SVI_fwd` invertiert) und als relativer Preisfehler, einmal mit Forward `SVI_fwd`, einmal mit dem Index des Fills.", "",
             "| Underlying | Uhr | Fills mit Kurve | Median Alter (s) | Median abs. Δ IV (vp) | Anteil ≤ 0,5 vp | Anteil ≤ 2 vp |",
             "|---|---|---|---|---|---|---|"]
    fwd_rows = []
    quarter_rows = {}
    for ccy in CORE:
        svi = load_feed(ROOT / "raw/volfeed", ccy)
        rows = f[f["currency"] == ccy]
        if svi.empty or rows.empty:
            continue
        for clock in ("block_ts", "feed_ts"):
            m = attach_svi(rows, svi, at_ms="ts", clock=clock)
            m = m[m["svi_fwd"].notna()]
            T = ((m["expiry"] - m["ts"] / 1000) / pricing.YEAR).to_numpy(float)
            kind = np.where(m["option_type"] == "C", 1, -1)
            K = m["strike"].to_numpy(float)
            vol = svi_vol(K, *(m[c].to_numpy(float) for c in ["svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_fwd", "svi_ref_tau"]))
            tape = m["mark_price"].to_numpy(float)
            with np.errstate(all="ignore"):
                iv_tape = pricing.implied_vol(tape, m["svi_fwd"].to_numpy(float), K, T, kind)
                dv = np.abs(iv_tape - vol) * 100
            ok = np.isfinite(dv)
            lines.append(f"| {ccy} | {clock} | {de(len(m))} ({de(100 * len(m) / len(rows), 1)} %) | {de(m['svi_age_s'].median(), 0)} | "
                         f"{de(np.median(dv[ok]), 3)} | {de(100 * np.mean(dv[ok] <= 0.5), 1)} % | {de(100 * np.mean(dv[ok] <= 2), 1)} % |")
            if clock != "block_ts":
                continue
            with np.errstate(all="ignore"):
                rel_curve = np.abs(pricing.price(m["svi_fwd"].to_numpy(float), K, T, vol, kind, 1.0) / tape - 1)
                rel_index = np.abs(pricing.price(m["index_price"].to_numpy(float), K, T, vol, kind, 1.0) / tape - 1)
            for label, sel in [("≤ 3 d", T <= 3 / 365), ("3–30 d", (T > 3 / 365) & (T <= 30 / 365)), ("> 30 d", T > 30 / 365)]:
                a, b = rel_curve[sel & np.isfinite(rel_curve)], rel_index[sel & np.isfinite(rel_index)]
                if len(a):
                    fwd_rows.append(f"| {ccy} | {label} | {de(len(a))} | {de(100 * np.median(a), 2)} % | {de(100 * np.median(b), 2)} % |")
            quarter = pd.to_datetime(m["ts"], unit="ms").dt.to_period("Q").astype(str).to_numpy()
            quarter_rows[ccy] = pd.Series(rel_curve).groupby(quarter).median() * 100
    lines += ["", "Median relativer Preisfehler nach Restlaufzeit (Push-Zeit):", "",
              "| Underlying | Restlaufzeit | Fills | Forward = `SVI_fwd` | Forward = Index des Fills |", "|---|---|---|---|---|"] + fwd_rows
    if quarter_rows:
        tab = pd.DataFrame(quarter_rows)
        lines += ["", "Median relativer Preisfehler je Quartal (Forward = `SVI_fwd`, Push-Zeit):", "",
                  "| Quartal | " + " | ".join(tab.columns) + " |", "|---|" + "---|" * len(tab.columns)]
        for q, row in tab.iterrows():
            lines.append(f"| {q} | " + " | ".join("–" if pd.isna(v) else de(v, 2) + " %" for v in row) + " |")
    lines += ["", "Lesart: Der Tape-Mark rechnet mit einem aktuellen Forward (bei kurzen Laufzeiten liegt der Index näher), die "
              "onchain Kurve mit ihrem eigenen, bis zu Minuten alten Forward; dazu kommt der Verzug der Kurve selbst. Pfad (b) ist "
              "deshalb ein verzögerter, forward-fixierter Mark. Die delta-neutrale und die Vol-Einheit sind davon weniger betroffen "
              "als der USDC-Markout auf kurzen Horizonten."]
    return lines


def disk_section() -> list:
    out = subprocess.run(["du", "-sh"] + [str(p) for p in sorted(ROOT.iterdir()) if p.is_dir()], capture_output=True, text=True).stdout
    return ["", "## Plattenbedarf", "", "```", out.strip(), "```"]


def main() -> None:
    lines = ["# Datenstand Paper 1 (Pilot)", "",
             f"Erzeugt {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} mit `scripts/p1_datenstand.py`. "
             "Enthält nur Zählungen und Prüfungen, keine Markouts (Präregistrierung). Pilot-Stichtag 2026-09-17 12:00 UTC; "
             "der finale Stichtag ist 2026-09-30 08:00 UTC.", ""]
    for section in (tape_section, fills_section, vault_section, ref_section, volfeed_section, mark_check_section, disk_section):
        lines += section()
    check = Path("docs/paper1/feed_check.md")
    lines += ["", "## Vol-Feed-Prüfung", "", "Siehe `docs/paper1/feed_check.md`." if check.exists() else "Noch nicht gelaufen."]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
