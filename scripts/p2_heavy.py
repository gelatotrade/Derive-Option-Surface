#!/usr/bin/env python3
"""Run a memory-heavy Paper 2 job under a machine-wide lock (16 GB RAM: one heavy job at a time).

    python3 scripts/p2_heavy.py [--wait-max 500] -- python3 -m derive_surface.capital run ...

Exit code 75 means the lock was not free within --wait-max seconds; call again later.
"""
from __future__ import annotations

import argparse
import fcntl
import subprocess
import sys
import time
from pathlib import Path

LOCK = Path("data/p2/heavy.lock")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait-max", type=float, default=500.0)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        ap.error("no command")
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    fh = LOCK.open("a+")
    t0 = time.monotonic()
    while True:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() - t0 > args.wait_max:
                print("heavy lock busy; try again later", file=sys.stderr)
                return 75
            time.sleep(5)
    try:
        return subprocess.call(cmd)
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)


if __name__ == "__main__":
    raise SystemExit(main())
