"""Command line entry point: ``python -m derive_surface <command> ...``."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

CCYS = ["BTC", "ETH", "HYPE"]


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="derive_surface", description=__doc__)
    p.add_argument("--data", type=Path, default=Path("data"))
    p.add_argument("--media", type=Path, default=Path("docs/media"))
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("download", help="full trade tape + spot history")
    s.add_argument("currencies", nargs="*", default=CCYS)

    s = sub.add_parser("record", help="live top-of-book (tickers) or depth (WebSocket) recorder")
    s.add_argument("kind", choices=["tickers", "depth"])
    s.add_argument("--duration", type=float, default=3600)
    s.add_argument("--interval", type=float, default=20)
    s.add_argument("currencies", nargs="*", default=CCYS)

    s = sub.add_parser("merge", help="concatenate recorder parts into data/live/<CCY>_*.parquet")
    s.add_argument("currencies", nargs="*", default=CCYS)

    s = sub.add_parser("depth-snapshot", help="one complete depth-20 snapshot of every live option")
    s.add_argument("currencies", nargs="*", default=CCYS)

    s = sub.add_parser("animate", help="render GIF/MP4 (or a PNG still)")
    s.add_argument("kind", choices=["live", "tape", "shock", "still"])
    s.add_argument("currency")
    s.add_argument("--axis", default=None, help="delta | std | logm | strike")
    s.add_argument("--color-by", default=None, help="iv | skew | mvdelta | delta | gamma | vega | theta | vanna | volga | charm | speed | zomma | color | ultima")
    s.add_argument("--regime", default="sticky_delta", help="shock only: sticky_delta | sticky_strike")
    s.add_argument("--every", type=int, default=3, help="live only: use every n-th recorded cycle")
    s.add_argument("--days", type=int, default=60, help="tape only: trailing window in days")
    s.add_argument("--step-hours", type=int, default=12, help="tape only: hours between frames")
    s.add_argument("--suffix", default="")

    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if a.cmd == "download":
        from .history import download_all

        download_all(a.currencies, a.data)
    elif a.cmd == "record":
        from .recorder import record_depth, record_tickers

        out = a.data / "raw" / "live"
        if a.kind == "tickers":
            record_tickers(a.currencies, out, interval_s=a.interval, duration_s=a.duration)
        else:
            record_depth(a.currencies, out, duration_s=a.duration)
    elif a.cmd == "merge":
        from .recorder import merge_parts

        for c in a.currencies:
            merge_parts(a.data / "raw" / "live", f"tickers_{c}", a.data / "live" / f"{c}_tickers.parquet")
        if list((a.data / "raw" / "live").glob("depth_part*.parquet")):
            merge_parts(a.data / "raw" / "live", "depth", a.data / "live" / "depth.parquet")
    elif a.cmd == "depth-snapshot":
        from .recorder import depth_snapshot

        depth_snapshot(a.currencies, a.data / "live" / "depth_snapshot.parquet")
    elif a.cmd == "animate":
        color_by = a.color_by or ("mvdelta" if a.kind == "shock" else "iv")
        axis = a.axis or ("strike" if a.kind == "shock" else "delta")
        if a.kind == "still":
            from .animate import render_still

            render_still(a.data, a.currency, a.media / f"{a.currency}_still{a.suffix}.png", axis=axis, color_by=color_by)
        elif a.kind == "live":
            from .animate import animate_live

            animate_live(a.data, a.currency, a.media, every=a.every, axis=axis, color_by=color_by, suffix=a.suffix)
        elif a.kind == "tape":
            from .animate import animate_tape

            animate_tape(a.data, a.currency, a.media, days=a.days, step_h=a.step_hours, axis=axis, color_by=color_by, suffix=a.suffix)
        else:
            from .shock import animate_shock

            animate_shock(a.data, a.currency, a.media, regime=a.regime, axis=axis, color_by=color_by, suffix=a.suffix)


if __name__ == "__main__":
    main()
