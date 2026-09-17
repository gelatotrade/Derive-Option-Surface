from __future__ import annotations

import gzip
import json
import random

import pandas as pd
import pytest

from derive_surface import fulltape


class FakeTape:
    """In-memory get_trade_history: inclusive bounds, pages in a window-specific shuffled order."""

    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def call(self, method, **p):
        assert method == "get_trade_history"
        self.calls += 1
        lo, hi = p["from_timestamp"], p["to_timestamp"]
        sel = sorted((r for r in self.rows if lo <= r["timestamp"] <= hi), key=lambda r: (r["trade_id"], r["liquidity_role"]))
        random.Random(lo * 7 + hi).shuffle(sel)
        ps, page = p["page_size"], p["page"]
        return {"trades": sel[(page - 1) * ps: page * ps], "pagination": {"count": len(sel), "num_pages": max(1, -(-len(sel) // ps))}}


def make_rows(n_fills, t0=1_704_931_200_000, spread_ms=10_000, seed=0, same_ts=False, instrument="BTC-20240126-45000-C"):
    rng = random.Random(seed)
    rows = []
    for i in range(n_fills):
        ts = t0 if same_ts else t0 + rng.randrange(spread_ms)
        base = dict(trade_id=f"t{seed}-{i:05d}", timestamp=ts, instrument_name=instrument, trade_price="100", trade_amount="0.5",
                    mark_price="101", index_price="44000", rfq_id=None, quote_id=None, trade_fee="0.1", expected_rebate="0",
                    extra_fee="0", realized_pnl="0", realized_pnl_excl_fees="0", tx_hash=f"0x{i:064x}", tx_status="settled")
        rows.append({**base, "direction": "buy", "liquidity_role": "maker", "wallet": "0xAAA", "subaccount_id": 1})
        rows.append({**base, "direction": "sell", "liquidity_role": "taker", "wallet": "0xBBB", "subaccount_id": 2})
    return rows


def read_all(out_dir):
    got = []
    for p in out_dir.glob("*.json.gz"):
        with gzip.open(p, "rt") as fh:
            got.extend(json.load(fh)["trades"])
    return got


def test_fetch_range_gets_every_row_once_and_splits(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    rows = make_rows(40)
    leaves = fulltape.fetch_range(FakeTape(rows), 1_704_931_200_000, 1_704_931_200_000 + 10_000, tmp_path)
    assert sum(n for _, _, n in leaves) == 80
    assert all(n <= 5 for _, _, n in leaves)
    got = read_all(tmp_path)
    keys = {(r["trade_id"], r["liquidity_role"], r["subaccount_id"]) for r in got}
    assert len(got) == 80 and len(keys) == 80


def test_single_millisecond_window_is_paged(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    rows = make_rows(8, same_ts=True)
    t = rows[0]["timestamp"]
    leaves = fulltape.fetch_range(FakeTape(rows), t - 1000, t + 1000, tmp_path)
    assert (t, t, 16) in leaves
    doc = json.load(gzip.open(fulltape.window_path(tmp_path, t, t), "rt"))
    assert len(doc["trades"]) == 16


def test_resume_only_recounts_split_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    rows = make_rows(40)
    first = FakeTape(rows)
    leaves = fulltape.fetch_range(first, 1_704_931_200_000, 1_704_931_210_000, tmp_path)
    second = FakeTape(rows)
    again = fulltape.fetch_range(second, 1_704_931_200_000, 1_704_931_210_000, tmp_path)
    assert sorted(again) == sorted(leaves)
    assert second.calls == first.calls - len(leaves)


def test_download_tape_manifest_and_condense(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    day = fulltape.DAY_MS
    t0 = 1_704_931_200_000
    rows = make_rows(20, t0=t0, spread_ms=2 * day, seed=1) + make_rows(3, t0=t0 + 5, seed=2, instrument="HYPE-20240126-77_5-P")
    man = fulltape.download_tape(FakeTape(rows), tmp_path, t0, t0 + 2 * day - 1, workers=2)
    assert man["rows_in_windows"] == man["api_count"] == 46
    assert len(man["leaves"]) == man["windows"]
    df = fulltape.condense(tmp_path, man)
    assert len(df) == 46
    assert list(df.columns) == fulltape.FIELDS + ["currency", "expiry", "strike", "option_type"]
    assert df["timestamp"].dtype == "int64" and df["trade_price"].dtype == "float64"
    assert (df["wallet"] == df["wallet"].str.lower()).all()
    hype = df[df["currency"] == "HYPE"].iloc[0]
    assert hype["strike"] == 77.5 and hype["option_type"] == "P"
    assert hype["expiry"] == 1706256000  # 2024-01-26 08:00 UTC
    files = fulltape.write_tape(df, tmp_path / "tape")
    assert files["BTC_options_full.parquet"]["rows"] == 40
    assert json.loads((tmp_path / "tape" / "MANIFEST.json").read_text())["HYPE_options_full.parquet"]["rows"] == 6
    assert len(pd.read_parquet(tmp_path / "tape" / "HYPE_options_full.parquet")) == 6


def test_condense_rejects_window_with_missing_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(fulltape, "PAGE_SIZE", 5)
    t0 = 1_704_931_200_000
    man = fulltape.download_tape(FakeTape(make_rows(4, t0=t0)), tmp_path, t0, t0 + fulltape.DAY_MS - 1, workers=1)
    a, b, n = next(w for w in man["leaves"] if w[2] > 0)
    path = fulltape.window_path(tmp_path, a, b)
    doc = json.load(gzip.open(path, "rt"))
    doc["trades"] = doc["trades"][:-1]
    with gzip.open(path, "wt") as fh:
        json.dump(doc, fh)
    with pytest.raises(ValueError, match="row count"):
        fulltape.condense(tmp_path, man)
