from __future__ import annotations

import pandas as pd

from derive_surface import refdata
from derive_surface.api import DeriveError


class Fake:
    def __init__(self, handlers):
        self.handlers = handlers

    def call(self, method, **p):
        return self.handlers[method](**p)


def auction(i, bids=1):
    return {"auction_id": f"a{i}", "subaccount_id": 100 + i, "start_timestamp": i, "end_timestamp": i + 1,
            "auction_type": "solvent", "fee": "1", "tx_hash": f"0xA{i}",
            "bids": [{"timestamp": i + 1, "tx_hash": f"0xB{i}{j}", "percent_liquidated": "0.1", "cash_received": "5",
                      "discount_pnl": "-1", "amounts_liquidated": {"ETH-PERP": "1"}} for j in range(bids)]}


def test_liquidations_walks_time_windows_and_merges_pages():
    day = 86_400_000
    # auction i starts on day i; the endpoint paginates rows (one row per bid), auctions are grouped per page
    book = {i: auction(i * day, bids=2 if i == 3 else 1) for i in range(10)}
    calls = []

    def liq(page, page_size, start_timestamp, end_timestamp):
        calls.append((start_timestamp, end_timestamp, page))
        rows = [(i, j) for i, a in sorted(book.items()) if start_timestamp <= a["start_timestamp"] <= end_timestamp for j in range(len(a["bids"]))]
        chunk = rows[(page - 1) * page_size: page * page_size]
        grouped = {}
        for i, j in chunk:
            a = grouped.setdefault(i, {**book[i], "bids": []})
            a["bids"].append(book[i]["bids"][j])
        pages = max(1, -(-len(rows) // page_size))
        return {"auctions": list(grouped.values()), "pagination": {"num_pages": pages, "count": len(rows)}}

    auctions, bids, info = refdata.liquidations(Fake({"get_liquidation_history": liq}), 0, 10 * day - 1, window_ms=4 * day, page_sizes=(1,))
    assert sorted(auctions["auction_id"]) == sorted(f"a{i * day}" for i in range(10))
    assert len(bids) == 11 and bids["instruments"].iloc[0] == '{"ETH-PERP": "1"}'
    assert info == {"windows": 3, "unique_auctions": 10, "gaps": []}
    assert {c[:2] for c in calls} == {(0, 4 * day - 1), (4 * day, 8 * day - 1), (8 * day, 10 * day - 1)}


def test_liquidations_fall_back_to_smaller_pages_then_split_then_record_gap():
    hour = 3_600_000
    book = {i: auction(i * hour) for i in range(4)}

    def liq(page, page_size, start_timestamp, end_timestamp):
        if page_size > 5 and start_timestamp <= 1 * hour <= end_timestamp:
            raise RuntimeError("get_liquidation_history: giving up after 2 attempts")  # server 500 for big pages
        if start_timestamp <= 3 * hour <= end_timestamp:
            raise RuntimeError("get_liquidation_history: giving up after 2 attempts")  # broken for every page size
        rows = [a for a in book.values() if start_timestamp <= a["start_timestamp"] <= end_timestamp]
        return {"auctions": rows[(page - 1) * page_size: page * page_size],
                "pagination": {"num_pages": max(1, -(-len(rows) // page_size)), "count": len(rows)}}

    auctions, _, info = refdata.liquidations(Fake({"get_liquidation_history": liq}), 0, 4 * hour - 1,
                                             window_ms=4 * hour, page_sizes=(20, 5), min_window_ms=hour)
    assert sorted(auctions["start_timestamp"]) == [0, hour, 2 * hour]
    assert info["gaps"] == [[3 * hour, 4 * hour - 1]]


def test_maker_scores_only_option_programmes_and_lowercase_wallets():
    programs = pd.DataFrame([
        {"name": "OPTIONS-MAJ", "asset_types": "option", "currencies": "BTC", "min_notional": 0.0, "start_ms": 1, "end_ms": 2, "rewards": "{}"},
        {"name": "PERPS-MAJ", "asset_types": "perp", "currencies": "BTC", "min_notional": 0.0, "start_ms": 1, "end_ms": 2, "rewards": "{}"},
        {"name": "OPTIONS-OLD", "asset_types": "option", "currencies": "ETH", "min_notional": 0.0, "start_ms": 0, "end_ms": 1, "rewards": "{}"},
    ])
    seen = []

    def scores(program_name, epoch_start_timestamp):
        seen.append(program_name)
        if program_name == "OPTIONS-OLD":
            raise DeriveError("get_maker_program_scores", {"code": 19000})
        return {"scores": [{"wallet": "0xAbC", "total_score": "3.5", "coverage_score": "1", "quality_score": "2",
                            "volume_multiplier": "1", "holder_boost": "1", "volume": "10"}]}

    out = refdata.maker_scores(Fake({"get_maker_program_scores": scores}), programs)
    assert seen == ["OPTIONS-MAJ", "OPTIONS-OLD"]
    assert out.to_dict("records") == [{"program": "OPTIONS-MAJ", "start_ms": 1, "end_ms": 2, "wallet": "0xabc", "total_score": 3.5,
                                       "coverage_score": 1.0, "quality_score": 2.0, "volume_multiplier": 1.0, "holder_boost": 1.0, "volume": 10.0}]


def test_settlement_prices_frame():
    def sp(currency):
        return {"expiries": [{"utc_expiry_sec": 20, "expiry_date": "20260102", "price": "2.5"},
                             {"utc_expiry_sec": 10, "expiry_date": "20260101", "price": "1.5"}]}

    df = refdata.settlement_prices(Fake({"get_option_settlement_prices": sp}), ["HYPE", "BTC"])
    assert list(df["currency"]) == ["BTC", "BTC", "HYPE", "HYPE"]
    assert list(df["expiry"][:2]) == [10, 20] and df["settlement_price"].dtype == "float64"


def test_merge_append_dedupes(tmp_path):
    path = tmp_path / "f.parquet"
    a = pd.DataFrame({"instrument_name": ["X", "X"], "timestamp": [1, 2], "funding_rate": [0.1, 0.2]})
    b = pd.DataFrame({"instrument_name": ["X", "X"], "timestamp": [2, 3], "funding_rate": [0.25, 0.3]})
    refdata.merge_append(path, a, ["instrument_name", "timestamp"])
    out = refdata.merge_append(path, b, ["instrument_name", "timestamp"])
    assert list(out["timestamp"]) == [1, 2, 3] and list(out["funding_rate"]) == [0.1, 0.25, 0.3]


def test_liquidations_use_the_first_working_page_size():
    book = [auction(i) for i in range(6)]
    sizes = []

    def liq(page, page_size, start_timestamp, end_timestamp):
        sizes.append(page_size)
        if page_size == 100:
            raise RuntimeError("get_liquidation_history: giving up after 3 attempts")
        return {"auctions": book[(page - 1) * page_size: page * page_size],
                "pagination": {"num_pages": max(1, -(-len(book) // page_size)), "count": len(book)}}

    auctions, _, info = refdata.liquidations(Fake({"get_liquidation_history": liq}), 0, 10, window_ms=100, workers=1)
    assert sorted(auctions["auction_id"]) == [f"a{i}" for i in range(6)] and info["gaps"] == []
    assert sizes == [100, 20]  # page size 5 is never needed
