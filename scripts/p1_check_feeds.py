"""Check the three core vol-feed addresses over time and against Derive's live mark IV.

1. Continuity: sample a 200-block window every 250 000 blocks from block 800 000 on and list every
   VolDataUpdated emitter.  For each core feed report the samples in which it emitted and every gap after
   its first appearance.  An emitter that is neither a core feed nor one of the known other feeds and whose
   forward lies within 15 % of the core feed's last known forward is listed as a possible replacement,
   also in samples where the core feed itself is silent.
2. Reproduction: decode the latest on-chain SVI of the three nearest expiries per core currency and
   compare svi_vol with the mark IV of every live option of that expiry.

Writes docs/paper1/feed_check.md.  Run from the repository root: python3 scripts/p1_check_feeds.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from derive_surface.api import DeriveClient, OptionName, expiry_date_str  # noqa: E402
from derive_surface.chainfeeds import (  # noqa: E402
    OTHER_FEEDS, VOL_DATA_UPDATED, VOL_FEEDS, ChainClient, decode_vol_log, scan_emitters, svi_vol,
)

OUT = Path("docs/paper1/feed_check.md")
FIRST_SAMPLE, STEP, SPAN, BAND = 800_000, 250_000, 200, 0.15


def continuity(chain: ChainClient, head: int) -> list:
    blocks = list(range(FIRST_SAMPLE, head, STEP))
    em = scan_emitters(chain, blocks, span=SPAN)
    core = {spec["address"]: ccy for ccy, spec in VOL_FEEDS.items()}
    em["feed"] = em["address"].map(lambda a: core.get(a) or OTHER_FEEDS.get(a) or "unknown")
    lines = [f"{len(blocks)} Stichproben zu je {SPAN} Blöcken ab Block {FIRST_SAMPLE:,} im Abstand {STEP:,}; "
             f"{em['address'].nunique()} verschiedene Emitter.", "",
             "| Feed | Stichproben mit Events | erste | letzte | Lücken nach dem Start | Forward erste → letzte |",
             "|---|---|---|---|---|---|"]
    rivals = []
    for ccy in VOL_FEEDS:
        mine = em[em["feed"] == ccy].sort_values("sample_block")
        if mine.empty:
            lines.append(f"| {ccy} | 0 | – | – | – | – |")
            continue
        present = set(mine["sample_block"])
        gaps = [b for b in blocks if b >= mine["sample_block"].iloc[0] and b not in present]
        gap_text = "keine" if not gaps else f"{len(gaps)}: " + ", ".join(f"{b:,}" for b in gaps[:8]) + (" …" if len(gaps) > 8 else "")
        lines.append(f"| {ccy} | {len(mine)} | {mine['sample_block'].iloc[0]:,} | {mine['sample_block'].iloc[-1]:,} | "
                     f"{gap_text} | {mine['fwd'].iloc[0]:,.2f} → {mine['fwd'].iloc[-1]:,.2f} |")
        last_fwd = None
        for b in blocks:
            g = em[em["sample_block"] == b]
            own = g[g["feed"] == ccy]
            if not own.empty:
                last_fwd = float(own["fwd"].iloc[0])
            if last_fwd is None:
                continue
            near = g[(g["feed"] == "unknown") & ((g["fwd"] / last_fwd - 1).abs() < BAND)]
            for _, r in near.iterrows():
                rivals.append(f"| {b:,} | {ccy} (zuletzt {last_fwd:,.2f}{'' if not own.empty else ', selbst stumm'}) | "
                              f"{r['address']} | {r['fwd']:,.2f} | {int(r['n'])} |")
    unknown = em[em["feed"] == "unknown"].groupby("address").agg(samples=("sample_block", "size"),
                                                                  first=("sample_block", "min"), last=("sample_block", "max"),
                                                                  fwd=("fwd", "median"))
    lines += ["", f"### Mögliche Ersatz-Feeds (unbekannte Adresse, Forward innerhalb ±{BAND:.0%} des letzten Kern-Forwards)", ""]
    lines += (["| Block | Kern-Feed | Kandidat | Forward | Events |", "|---|---|---|---|---|"] + rivals) if rivals else ["Keine."]
    lines += ["", "### Unbekannte Emitter (weder Kern- noch bekannte Neben-Feeds)", ""]
    if unknown.empty:
        lines.append("Keine.")
    else:
        lines += ["| Adresse | Stichproben | erste | letzte | Forward (Median) |", "|---|---|---|---|---|"]
        for addr, r in unknown.sort_values("first").iterrows():
            lines.append(f"| {addr} | {int(r['samples'])} | {int(r['first']):,} | {int(r['last']):,} | {r['fwd']:,.4g} |")
    return lines


def reproduction(chain: ChainClient, head: int) -> list:
    lines = ["| Underlying | Verfall | Optionen | max. abs. Δ IV | Median abs. Δ IV | Alter der SVI (s) |", "|---|---|---|---|---|---|"]
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
            if not tickers:
                lines.append(f"| {ccy} | {expiry_date_str(expiry)} | 0 | – | – | {now - d['feed_ts']:.0f} |")
                continue
            strikes = np.array([OptionName.parse(n).strike for n in tickers])
            marks = np.array([float(t["option_pricing"]["i"]) for t in tickers.values()])
            model = svi_vol(strikes, d["svi_a"], d["svi_b"], d["svi_rho"], d["svi_m"], d["svi_sigma"], d["svi_fwd"], d["svi_ref_tau"])
            diff = np.abs(model - marks)
            lines.append(f"| {ccy} | {expiry_date_str(expiry)} | {len(marks)} | {np.nanmax(diff):.5f} | "
                         f"{np.nanmedian(diff):.5f} | {now - d['feed_ts']:.0f} |")
    return lines


def formula_check() -> list:
    """svi_vol on the freshest signed curve (public/get_latest_signed_feeds) against the ticker mark IV."""
    lines = ["| Underlying | Verfall | Optionen | Alter der signierten Kurve (s) | max. abs. Δ IV | Median abs. Δ IV |", "|---|---|---|---|---|---|"]
    api = DeriveClient()
    for ccy in VOL_FEEDS:
        signed = api.call("get_latest_signed_feeds", currency=ccy)["vol_data"].get(ccy, {})
        now = time.time()
        for expiry in sorted(int(e) for e in signed if int(e) > now + 3600)[:3]:
            entry = signed[str(expiry)]
            d = entry["vol_data"]
            tickers = api.tickers(ccy, expiry_date_str(expiry))
            if not tickers:
                continue
            strikes = np.array([OptionName.parse(n).strike for n in tickers])
            marks = np.array([float(t["option_pricing"]["i"]) for t in tickers.values()])
            model = svi_vol(strikes, *(float(d[k]) for k in ["SVI_a", "SVI_b", "SVI_rho", "SVI_m", "SVI_sigma", "SVI_fwd", "SVI_refTau"]))
            diff = np.abs(model - marks)
            lines.append(f"| {ccy} | {expiry_date_str(expiry)} | {len(marks)} | {now - entry['timestamp']:.0f} | "
                         f"{np.nanmax(diff):.5f} | {np.nanmedian(diff):.5f} |")
    return lines


def main() -> None:
    chain = ChainClient()
    head = chain.block_number()
    lines = ["# Vol-Feed-Prüfung", "", f"Lauf {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}, Kopf-Block {head:,}.", "",
             "## Kontinuität", ""]
    lines += continuity(chain, head)
    lines += ["", "## Formel: neueste signierte Kurve gegen Live-Mark-IV", "",
              "Prüft `svi_vol` (Referenz-Tau, SVI-Forward) ohne Zeitverzug. Δ IV in Vol-Einheiten (0,01 = 1 Vol-Punkt).", ""]
    lines += formula_check()
    lines += ["", "## Gegenprobe: letzte onchain gepushte Kurve gegen Live-Mark-IV", "",
              "Die onchain Kurve läuft dem Backend-Mark um die angegebene Zeit hinterher; die Abweichung misst diesen Verzug, "
              "nicht die Formel.", ""]
    lines += reproduction(chain, head)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
