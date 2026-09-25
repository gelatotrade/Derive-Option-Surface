"""Write docs/paper1/DATA_STATUS.md from the files under data/p1 (counts and checks only, no markouts).

Run from the repository root after `p1 tape`, `p1 ref`, `p1 volfeed`, `p1 fills`:
    python3 scripts/p1_data_status.py
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from derive_surface.chainfeeds import VOL_FEEDS, load_feed, svi_vol  # noqa: E402
from derive_surface.classify import load_vault_wallets  # noqa: E402

ROOT = Path("data/p1")
OUT = Path("docs/paper1/DATA_STATUS.md")
CORE = list(VOL_FEEDS)
MISSING = "n/a"


def utc(ms: float) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def num(x: float, digits: int = 0) -> str:
    """Decimal point and a thin space as thousands separator (as \\, in the manuscript)."""
    return f"{x:,.{digits}f}".replace(",", " ")


def tape_section() -> list:
    manifests = [json.loads(p.read_text()) for p in (ROOT / "raw/tape/option").glob("manifest_*.json")]
    man = max(manifests, key=lambda m: m.get("finished_ms", 0))
    files = json.loads((ROOT / "tape/MANIFEST.json").read_text())
    lines = ["## Options tape", "",
             f"Period {utc(man['from_ms'])} to {utc(man['to_ms'])} (both inclusive), finished {utc(man['finished_ms'])}. "
             f"{num(man['rows_in_windows'])} rows in {num(man['windows'])} single-page windows; "
             f"days with a differing recount: {len(man['day_mismatches'])}. "
             f"The API reports {num(man['api_count_full_range'])} rows for the whole period; this number is not additive "
             f"over long ranges and is for information only.", "",
             "| Underlying | Rows | SHA-256 (prefix) |", "|---|---|---|"]
    for name, info in sorted(files.items(), key=lambda kv: -kv[1]["rows"]):
        lines.append(f"| {name.split('_')[0]} | {num(info['rows'])} | `{info['sha256'][:16]}` |")
    return lines


def fills_section() -> list:
    s = json.loads((ROOT / "derived/fills_summary.json").read_text())
    f = pd.read_parquet(ROOT / "derived/fills.parquet",
                        columns=["trade_id", "ts", "ts_maker", "currency", "taker_class", "notional", "is_rfq", "taker_is_vault",
                                 "maker_is_vault", "is_liquidation", "taker_in_mm_programme"])
    lines = ["", "## Fills and counterparty classes (without markouts)", "",
             f"{num(s['rows'])} rows give {num(s['fills'])} fills. Rows without a partner: {s['unpaired_rows']} "
             f"({s['unpaired_trade_ids']} trade_ids); pairs with a differing price, a differing amount or the same direction: "
             f"{s['pair_mismatch']}; not settled: {s['not_settled']}. Liquidation transactions in the match: {s['liquidation_tx']}.", ""]
    tape = pd.concat([pd.read_parquet(p, columns=["trade_id", "timestamp", "instrument_name", "liquidity_role", "wallet"])
                      for p in (ROOT / "tape").glob("*_options_full.parquet")])
    roles = tape.groupby("trade_id")["liquidity_role"].agg(lambda x: ",".join(sorted(x)))
    odd = tape[tape["trade_id"].isin(roles[roles != "maker,taker"].index)]
    if len(odd):
        lines.append("Rows without a partner: " + "; ".join(
            f"{r.instrument_name} {r.liquidity_role} {utc(r.timestamp)}" for r in odd.sort_values("timestamp").itertuples()) + ".")
        lines.append("")
    core = f[f["currency"].isin(CORE)]
    fills = core.pivot_table(index="taker_class", columns="currency", values="trade_id", aggfunc="size", fill_value=0)
    notional = core.pivot_table(index="taker_class", columns="currency", values="notional", aggfunc="sum", fill_value=0) / 1e6
    lines += ["| Taker class | " + " | ".join(f"{c} fills | {c} notional (million USD)" for c in CORE) + " |",
              "|---|" + "---|---|" * len(CORE)]
    for cls in ["liquidation", "vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]:
        cells = []
        for c in CORE:
            n = int(fills.loc[cls, c]) if cls in fills.index and c in fills.columns else 0
            v = float(notional.loc[cls, c]) if cls in notional.index and c in notional.columns else 0.0
            cells.append(f"{num(n)} | {num(v)}")
        lines.append(f"| {cls} | " + " | ".join(cells) + " |")
    lines += ["", f"Flags (core): RFQ {num(core['is_rfq'].sum())}, vault as taker {num(core['taker_is_vault'].sum())}, "
                  f"vault as maker {num(core['maker_is_vault'].sum())}, liquidation {num(core['is_liquidation'].sum())}, "
                  f"taker in the MM programme {num(core['taker_in_mm_programme'].sum())}."]
    first_prog = pd.read_parquet(ROOT / "ref/maker_programs.parquet")["start_ms"].min()
    lines.append(f"The class MM programme can only be assigned from {utc(first_prog)} on; "
                 f"{num((core['ts'] < first_prog).sum())} core fills lie before that.")
    lag = (f["ts"] - f["ts_maker"]) / 1000
    for flag, name in [(True, "RFQ"), (False, "book")]:
        x = lag[f["is_rfq"] == flag]
        lines.append(f"Time gap taker minus maker row, {name}: median {num(x.median(), 1)} s, 99th percentile {num(x.quantile(.99), 1)} s, "
                     f"maximum {num(x.max(), 0)} s.")
    return lines


def vault_section() -> list:
    csv = pd.read_csv("docs/paper1/meta/vault_wallets.csv", comment="#")
    csv["wallet"] = csv["wallet"].str.lower()
    wallets = load_vault_wallets(Path("docs/paper1/meta/vault_wallets.csv"))
    tape = pd.concat([pd.read_parquet(p, columns=["wallet", "liquidity_role", "rfq_id", "trade_amount", "index_price"])
                      for p in (ROOT / "tape").glob("*_options_full.parquet")])
    hit = tape[tape["wallet"].isin(wallets)].assign(notional=lambda d: d["trade_amount"] * d["index_price"])
    lines = ["", "## Vaults", "", f"{len(wallets)} vault wallets listed, {hit['wallet'].nunique()} seen in the tape, "
             f"{num(len(hit))} rows ({num(100 * len(hit) / len(tape), 2)} % of all rows).", "",
             "| Token | Vault | Maker rows | Taker rows | RFQ share | Notional (million USD) |", "|---|---|---|---|---|---|"]
    for r in csv.itertuples():
        h = hit[hit["wallet"] == r.wallet]
        lines.append(f"| {r.token} | {r.vault_name} | {num((h.liquidity_role == 'maker').sum())} | {num((h.liquidity_role == 'taker').sum())} | "
                     f"{MISSING if h.empty else num(100 * h['rfq_id'].notna().mean()) + ' %'} | {num(h['notional'].sum() / 1e6, 1)} |")
    stats = sorted((ROOT / "ref").glob("vault_statistics_*.parquet"))
    if stats:
        v = pd.read_parquet(stats[-1])
        lines.append("")
        lines.append(f"TVL according to `get_vault_statistics` ({stats[-1].stem[-8:]}): "
                     f"{num(v['usd_tvl'].astype(float).sum() / 1e6, 2)} million USD in total.")
    return lines


def ref_section() -> list:
    r = json.loads((ROOT / "ref/REFDATA.json").read_text())
    liq = r["liquidations"]
    auctions = pd.read_parquet(ROOT / "ref/liquidation_auctions.parquet")
    lines = ["", "## Reference data", "", f"Fetched {r['fetched_utc']} UTC.", "",
             "- Settlement prices per underlying: " + ", ".join(f"{k} {v}" for k, v in sorted(r["settlement_prices"].items())) + ".",
             f"- Liquidations: {num(liq.get('unique_auctions', 0))} auctions, {num(liq.get('bids', 0))} bids"
             + (f" from {num(liq['windows'])} daily windows" if liq.get("windows") else " (taken over from the existing files)")
             + f"; remaining gaps: {len(liq.get('gaps') or [])}"
             + (" (" + ", ".join(f"{utc(a)} to {utc(b)}" for a, b in liq["gaps"][:10]) + ")" if liq.get("gaps") else "")
             + ". The bids are incomplete depending on the page size (2025-10-10: 242 auctions, 34 bids at page size 100, "
               "4 at size 5); complete bids only from the chain events."]
    if len(auctions):
        fills_liq = int(pd.read_parquet(ROOT / "derived/fills.parquet", columns=["is_liquidation"])["is_liquidation"].sum())
        lines.append(f"  Period of the auctions {utc(auctions['start_timestamp'].min())} to {utc(auctions['start_timestamp'].max())}. "
                     f"Of {num(len(auctions))} auctions, not a single option fill carries the transaction ({fills_liq} matches): "
                     "liquidations transfer positions outside the trade tape. The class \"liquidation\" therefore stays empty.")
    mp = r["maker_programmes"]
    lines += [f"- Maker programmes: {mp['programmes']} epoch programmes, {mp['option_score_rows']} score rows for option programmes, "
              f"{mp['active_wallets']} wallets with a score > 0.",
              f"- Instrument fees: {r['instruments']} live options; funding history {r['funding_rows']} hourly values "
              f"(rolling 30 days, extended as it goes)."]
    return lines


def volfeed_section() -> list:
    lines = ["", "## SVI history (vol feeds)", "",
             "| Underlying | Events | first block | last block | first curve | last curve | Expiries | Median push minus signature (s) | "
             "Gap between pushes per expiry, median / 90th percentile (s) |",
             "|---|---|---|---|---|---|---|---|---|"]
    monthly = {}
    for ccy in CORE:
        df = load_feed(ROOT / "raw/volfeed", ccy)
        if df.empty:
            lines.append(f"| {ccy} | 0 | {MISSING} | {MISSING} | {MISSING} | {MISSING} | {MISSING} | {MISSING} |")
            continue
        push = (df["block_ts"] - df["feed_ts"])[df["block_ts"] > 0]
        by_push = df[df["block_ts"] > 0].sort_values(["expiry", "block_ts"])
        gaps = by_push.groupby("expiry")["block_ts"].diff().dropna()
        lines.append(f"| {ccy} | {num(len(df))} | {num(df['block'].min())} | {num(df['block'].max())} | {utc(df['feed_ts'].min() * 1000)} | "
                     f"{utc(df['feed_ts'].max() * 1000)} | {df['expiry'].nunique()} | {num(push.median(), 0)} | "
                     f"{num(gaps.median(), 0)} / {num(gaps.quantile(0.9), 0)} |")
        monthly[ccy] = df.groupby(pd.to_datetime(df["feed_ts"], unit="s").dt.strftime("%Y-%m")).size()
    if monthly:
        tab = pd.DataFrame(monthly).fillna(0).astype(int)
        lines += ["", "Events per month:", "", "| Month | " + " | ".join(tab.columns) + " |", "|---|" + "---|" * len(tab.columns)]
        for m, row in tab.iterrows():
            lines.append(f"| {m} | " + " | ".join(num(v) for v in row) + " |")
    return lines


def mark_check_section() -> list:
    """Mark price at fill time rebuilt from the on-chain SVI vs the tape's mark_price (no future data: not a markout)."""
    from derive_surface import pricing
    from derive_surface.markpath import attach_svi

    f = pd.read_parquet(ROOT / "derived/fills.parquet",
                        columns=["trade_id", "ts", "currency", "expiry", "strike", "option_type", "mark_price", "index_price",
                                 "tx_status", "pair_ok"])
    f = f[(f["tx_status"] == "settled") & f["pair_ok"] & (f["expiry"] * 1000 - f["ts"] > 30 * 60_000) & (f["mark_price"] > 0)]
    lines = ["", "## Cross-check: mark at fill time from the on-chain SVI curve", "",
             "For every core fill (settled, more than 30 min before expiry) the last SVI curve of the same expiry is looked up, "
             "by push time (`block_ts`, pre-registered) and by signature time (`feed_ts`). Vol from the curve (exactly as `SVI.sol`), "
             "price with Black-76. The comparison is with the `mark_price` of the taker row: as a vol distance (both prices inverted "
             "over the same forward `SVI_fwd`) and as a relative price error, once with forward `SVI_fwd`, once with the index of the fill.", "",
             "| Underlying | Clock | Fills with curve | Median age (s) | Median abs. Δ IV (vp) | Share ≤ 0.5 vp | Share ≤ 2 vp |",
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
            lines.append(f"| {ccy} | {clock} | {num(len(m))} ({num(100 * len(m) / len(rows), 1)} %) | {num(m['svi_age_s'].median(), 0)} | "
                         f"{num(np.median(dv[ok]), 3)} | {num(100 * np.mean(dv[ok] <= 0.5), 1)} % | {num(100 * np.mean(dv[ok] <= 2), 1)} % |")
            if clock != "block_ts":
                continue
            with np.errstate(all="ignore"):
                rel_curve = np.abs(pricing.price(m["svi_fwd"].to_numpy(float), K, T, vol, kind, 1.0) / tape - 1)
                rel_index = np.abs(pricing.price(m["index_price"].to_numpy(float), K, T, vol, kind, 1.0) / tape - 1)
            for label, sel in [("≤ 3 d", T <= 3 / 365), ("3-30 d", (T > 3 / 365) & (T <= 30 / 365)), ("> 30 d", T > 30 / 365)]:
                a, b = rel_curve[sel & np.isfinite(rel_curve)], rel_index[sel & np.isfinite(rel_index)]
                if len(a):
                    fwd_rows.append(f"| {ccy} | {label} | {num(len(a))} | {num(100 * np.median(a), 2)} % | {num(100 * np.median(b), 2)} % |")
            quarter = pd.to_datetime(m["ts"], unit="ms").dt.to_period("Q").astype(str).to_numpy()
            quarter_rows[ccy] = pd.Series(rel_curve).groupby(quarter).median() * 100
    lines += ["", "Median relative price error by time to expiry (push time):", "",
              "| Underlying | Time to expiry | Fills | Forward = `SVI_fwd` | Forward = index of the fill |", "|---|---|---|---|---|"] + fwd_rows
    if quarter_rows:
        tab = pd.DataFrame(quarter_rows)
        lines += ["", "Median relative price error per quarter (forward = `SVI_fwd`, push time):", "",
                  "| Quarter | " + " | ".join(tab.columns) + " |", "|---|" + "---|" * len(tab.columns)]
        for q, row in tab.iterrows():
            lines.append(f"| {q} | " + " | ".join(MISSING if pd.isna(v) else num(v, 2) + " %" for v in row) + " |")
    lines += ["", "Reading: the tape mark uses a current forward (at short maturities the index is closer), the on-chain curve "
              "uses its own forward, which can be up to minutes old; on top of that comes the lag of the curve itself. Path (b) is "
              "therefore a delayed mark with a fixed forward. The delta-neutral unit and the vol unit are less affected by this "
              "than the USDC markout at short horizons."]
    return lines


def disk_section() -> list:
    out = subprocess.run(["du", "-sh"] + [str(p) for p in sorted(ROOT.iterdir()) if p.is_dir()], capture_output=True, text=True,
                         env=dict(os.environ, LC_ALL="C")).stdout      # decimal point in the sizes
    return ["", "## Disk usage", "", "```", out.strip(), "```"]


def main() -> None:
    lines = ["# Data status of paper 1 (pilot)", "",
             f"Generated {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} with `scripts/p1_data_status.py`. "
             "Contains only counts and checks, no markouts (pre-registration). Pilot cut-off 2026-09-17 12:00 UTC; "
             "the final cut-off is 2026-09-30 08:00 UTC.", ""]
    for section in (tape_section, fills_section, vault_section, ref_section, volfeed_section, mark_check_section, disk_section):
        lines += section()
    check = Path("docs/paper1/feed_check.md")
    lines += ["", "## Vol feed check", "", "See `docs/paper1/feed_check.md`." if check.exists() else "Not run yet."]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
