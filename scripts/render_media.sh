#!/usr/bin/env bash
# Re-render every animation in docs/media from the data in data/ (sequentially: matplotlib is CPU-bound).
set -euo pipefail
cd "$(dirname "$0")/.."
python -m derive_surface merge
for c in BTC ETH HYPE; do
  python -m derive_surface animate live  "$c" --suffix _en
  python -m derive_surface animate tape  "$c" --days 60 --step-hours 12 --suffix _en
  python -m derive_surface animate shock "$c" --regime sticky_delta --color-by mvdelta --suffix _en
done
