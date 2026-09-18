"""``python3 -m derive_surface p1 <command>``: data layer of paper 1 (adverse selection on Derive)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from pathlib import Path
from typing import List, Optional

ROOT = Path("data/p1")
VAULTS = Path("docs/paper1/meta/vault_wallets.csv")
TAPE_START = "2023-12-01T00:00:00"  # first option fill on the tape: 2023-12-06 03:13 UTC
CORE = ["BTC", "ETH", "HYPE"]


def to_ms(iso: str) -> int:
    text = iso.strip()
    if text[-1:] in ("Z", "z"):  # fromisoformat accepts "Z" only from Python 3.11 on
        text = text[:-1] + "+00:00"
    d = dt.datetime.fromisoformat(text)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp() * 1000)


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="derive_surface p1", description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("tape", help="full option tape (all underlyings, both rows per fill)")
    s.add_argument("--start", default=TAPE_START)
    s.add_argument("--end", required=True, help="inclusive end, ISO time (UTC if no offset)")
    s.add_argument("--workers", type=int, default=6)
    s = sub.add_parser("volfeed", help="VolDataUpdated history from Derive Chain")
    s.add_argument("currencies", nargs="*", default=CORE)
    s.add_argument("--end", required=True, help="last block at or before this ISO time")
    s.add_argument("--workers", type=int, default=4)
    s.add_argument("--window", type=int, default=5_000)
    s = sub.add_parser("compact", help="monthly SVI parquet files from the fetched chunks")
    s.add_argument("currencies", nargs="*", default=CORE)
    s = sub.add_parser("ref", help="settlements, liquidations, maker programmes, vaults, fees, funding")
    s.add_argument("--skip-liquidations", action="store_true", help="keep the liquidation files already on disk")
    s = sub.add_parser("fills", help="pair rows into fills and classify takers")
    s.add_argument("--vaults", type=Path, default=VAULTS)
    s = sub.add_parser("markouts", help="markouts of the pre-registered sample (paths a/b/c)")
    s.add_argument("--cutoff", default="2026-09-17T12:00:00Z", help="sample cut-off (taker time), ISO")
    s = sub.add_parser("figures", help="draw the manuscript figures")
    s.add_argument("--results", type=Path, default=Path("results/p1"))
    s.add_argument("--out", type=Path, default=Path("paper/figures"))
    s.add_argument("--only", default=None, help="comma separated keys, e.g. T1,F5")
    s = sub.add_parser("inference", help="pre-registered hypotheses, net edge, robustness")
    s.add_argument("--results", type=Path, default=Path("results/p1"))
    s.add_argument("--half-spread-bp", type=float, default=1.0)
    s.add_argument("--bootstrap", type=int, default=9999)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if a.cmd == "tape":
        from .api import DeriveClient
        from .fulltape import condense, download_tape, write_tape

        raw = a.root / "raw" / "tape" / "option"
        manifest = download_tape(DeriveClient(), raw, to_ms(a.start), to_ms(a.end), workers=a.workers)
        report = {k: v for k, v in manifest.items() if k != "leaves"}
        if manifest["day_mismatches"]:
            print(json.dumps(report, indent=1))
            raise SystemExit("tape not written: some days still differ from the API (see day_mismatches)")
        report["files"] = write_tape(condense(raw, manifest), a.root / "tape")
        print(json.dumps(report, indent=1))
    elif a.cmd == "volfeed":
        from .chainfeeds import ChainClient, block_at, sync_feed

        client = ChainClient()
        to_block = block_at(client, to_ms(a.end) // 1000)
        for ccy in a.currencies:
            print(json.dumps(sync_feed(client, ccy, a.root / "raw" / "volfeed", to_block, workers=a.workers, window=a.window)))
    elif a.cmd == "compact":
        from .chainfeeds import compact_feed

        for ccy in a.currencies:
            print(ccy, json.dumps(compact_feed(a.root / "raw" / "volfeed", ccy, a.root / "volfeed")))
    elif a.cmd == "ref":
        from .api import DeriveClient
        from .refdata import save_all

        # few retries: some liquidation windows fail deterministically and are handled by smaller pages instead
        print(json.dumps(save_all(DeriveClient(max_retries=3), a.root / "ref", skip_liquidations=a.skip_liquidations),
                         indent=1, default=str))
    elif a.cmd == "fills":
        from .classify import build_fills

        out = a.root / "derived" / "fills.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        summary = build_fills(a.root / "tape", a.root / "ref", a.vaults, out)
        (a.root / "derived" / "fills_summary.json").write_text(json.dumps(summary, indent=1, default=str))
        print(json.dumps({k: v for k, v in summary.items() if k != "classes"}, indent=1))
    elif a.cmd == "inference":
        from .inference_p1 import run_all

        summary = run_all(a.root, a.results, half_spread_bp=a.half_spread_bp, b=a.bootstrap)
        print(json.dumps(summary, indent=1, default=str))
    elif a.cmd == "figures":
        from .figures_p1 import build

        written = build(a.root, a.results, a.out, only=a.only.split(",") if a.only else None)
        print(json.dumps({k: [str(q) for q in v] for k, v in written.items()}, indent=1))
    elif a.cmd == "markouts":
        from .markouts import build_markouts

        out = a.root / "derived" / "markouts.parquet"
        summary = build_markouts(a.root, to_ms(a.cutoff), out)
        print(json.dumps(summary, indent=1))
