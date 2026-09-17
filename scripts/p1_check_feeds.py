"""Check the three core vol-feed addresses over time and against Derive's live mark IV.

1. Continuity: sample 200-block windows every 500 000 blocks, list every VolDataUpdated emitter and flag
   any unknown emitter whose forward lies within 20 % of a core feed's forward (a possible replacement feed).
2. Reproduction: decode the latest on-chain SVI of the three nearest expiries per core currency and compare
   svi_vol with the mark IV of every live option of that expiry.

Writes docs/paper1/feed_check.md.  Run from the repository root: python3 scripts/p1_check_feeds.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from derive_surface.api import DeriveClient, OptionName, expiry_date_str  # noqa: E402
from derive_surface.chainfeeds import VOL_DATA_UPDATED, VOL_FEEDS, ChainClient, decode_vol_log, scan_emitters, svi_vol  # noqa: E402

OUT = Path("docs/paper1/feed_check.md")


def main() -> None:
    chain = ChainClient()
    head = chain.block_number()
    blocks = list(range(2_500_000, head, 500_000))
    emitters = scan_emitters(chain, blocks, span=200)
    known = {spec["address"]: ccy for ccy, spec in VOL_FEEDS.items()}
    emitters["feed"] = emitters["address"].map(known).fillna("other")
    lines = ["# Vol-Feed-Prüfung", "",
             f"Lauf {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}, Kopf-Block {head}, "
             f"{len(blocks)} Stichproben zu je 200 Blöcken ab Block 2 500 000 im Abstand 500 000.", "",
             "## Kontinuität", "", "| Feed | Stichproben mit Events | erste | letzte | Forward erste → letzte |", "|---|---|---|---|---|"]
    for ccy in VOL_FEEDS:
        g = emitters[emitters["feed"] == ccy].sort_values("sample_block")
        if g.empty:
            lines.append(f"| {ccy} | 0 | – | – | – |")
            continue
        lines.append(f"| {ccy} | {len(g)} | {g.sample_block.iloc[0]} | {g.sample_block.iloc[-1]} | "
                     f"{g.fwd.iloc[0]:,.2f} → {g.fwd.iloc[-1]:,.2f} |")
    conflicts = []
    for block, g in emitters.groupby("sample_block"):
        for _, core in g[g["feed"] != "other"].iterrows():
            rivals = g[(g["feed"] == "other") & ((g["fwd"] / core["fwd"] - 1).abs() < 0.2)]
            for _, r in rivals.iterrows():
                conflicts.append(f"| {block} | {core['feed']} {core['fwd']:,.2f} | {r['address']} {r['fwd']:,.2f} |")
    lines += ["", "## Mögliche Ersatz-Feeds (unbekannte Adresse mit Forward ±20 % eines Kern-Feeds)", ""]
    lines += (["| Block | Kern-Feed | Kandidat |", "|---|---|---|"] + conflicts) if conflicts else ["Keine."]
    lines += ["", "## Gegenprobe SVI gegen Live-Mark-IV", "",
              "| Underlying | Verfall | Optionen | max. |Δ IV| | Median |Δ IV| | Alter der SVI (s) |", "|---|---|---|---|---|---|"]
    api = DeriveClient()
    for ccy, spec in VOL_FEEDS.items():
        latest = {}
        for entry in chain.get_logs(spec["address"], VOL_DATA_UPDATED, head - 900, head):
            d = decode_vol_log(entry)
            latest[d["expiry"]] = d
        now = time.time()
        for expiry in sorted(e for e in latest if e > now + 3600)[:3]:
            d = latest[expiry]
            tickers = api.tickers(ccy, expiry_date_str(expiry))
            strikes = np.array([OptionName.parse(n).strike for n in tickers])
            marks = np.array([float(t["option_pricing"]["i"]) for t in tickers.values()])
            model = svi_vol(strikes, d["svi_a"], d["svi_b"], d["svi_rho"], d["svi_m"], d["svi_sigma"], d["svi_fwd"], d["svi_ref_tau"])
            diff = np.abs(model - marks)
            lines.append(f"| {ccy} | {expiry_date_str(expiry)} | {len(marks)} | {np.nanmax(diff):.5f} | "
                         f"{np.nanmedian(diff):.5f} | {now - d['feed_ts']:.0f} |")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
