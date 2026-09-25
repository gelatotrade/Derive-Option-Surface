from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import classify as cl

JAN = 1_704_931_200_000  # 2024-01-11
FEB = 1_707_004_800_000  # 2024-02-04


def row(tid, role, ts, wallet, sub, direction, price=10.0, amount=1.0, rfq=None, tx="0x1", ccy="BTC", index=40_000.0):
    return {"trade_id": tid, "timestamp": ts, "instrument_name": f"{ccy}-20240126-45000-C", "direction": direction,
            "liquidity_role": role, "trade_price": price, "trade_amount": amount, "mark_price": 11.0, "index_price": index,
            "wallet": wallet, "subaccount_id": sub, "rfq_id": rfq, "quote_id": None, "trade_fee": 0.5 if role == "taker" else 0.0,
            "expected_rebate": 0.1 if role == "maker" else 0.0, "extra_fee": 0.0, "realized_pnl": 0.0,
            "realized_pnl_excl_fees": 0.0, "tx_hash": tx, "tx_status": "settled", "currency": ccy, "expiry": 1_706_256_000,
            "strike": 45_000.0, "option_type": "C"}


def fill(tid, ts, maker, taker, taker_dir="buy", **kw):
    maker_dir = "sell" if taker_dir == "buy" else "buy"
    return [row(tid, "maker", ts - 5, maker, 1, maker_dir, **kw), row(tid, "taker", ts, taker, 2, taker_dir, **kw)]


def test_pair_fills_pairs_and_flags_unpaired():
    rows = fill("a", JAN, "0xm", "0xt") + fill("b", JAN + 1, "0xm", "0xt", taker_dir="sell")
    rows += [row("c", "taker", JAN + 2, "0xt", 2, "buy")]
    rows[1]["rfq_id"] = None
    rows[0]["rfq_id"] = "r1"  # only the maker row carries the rfq id
    fills, unpaired = cl.pair_fills(pd.DataFrame(rows))
    assert list(fills["trade_id"]) == ["a", "b"]
    assert list(fills["taker_side"]) == [1, -1]
    assert fills["ts"].iloc[0] == JAN and fills["ts_maker"].iloc[0] == JAN - 5
    assert fills["rfq_id"].iloc[0] == "r1"
    assert fills["pair_ok"].all()
    assert fills["notional"].iloc[0] == pytest.approx(40_000.0)
    assert fills["rebate_maker"].iloc[0] == pytest.approx(0.1) and fills["fee_taker"].iloc[0] == pytest.approx(0.5)
    assert list(unpaired["trade_id"]) == ["c"]


def test_pair_ok_detects_price_mismatch():
    rows = fill("a", JAN, "0xm", "0xt")
    rows[0]["trade_price"] = 10.5
    fills, _ = cl.pair_fills(pd.DataFrame(rows))
    assert not fills["pair_ok"].iloc[0]


def base_fills():
    rows = []
    for i, taker in enumerate(["0xliq", "0xvault", "0xrfq", "0xdom", "0xmm", "0xbig", "0xnone"]):
        rows += fill(f"f{i}", JAN + 100 * i, "0xmaker", taker, tx=f"0x{i}", rfq="r" if taker in ("0xliq", "0xvault", "0xrfq") else None)
    fills, _ = cl.pair_fills(pd.DataFrame(rows))
    return fills


def test_class_priority():
    fills = base_fills()
    months = "2024-01"
    everyone = {"0xliq", "0xvault", "0xrfq", "0xdom", "0xmm", "0xbig"}
    lookup = (np.array([JAN - 1]), np.array([JAN + 10_000]), [{"0xmm", "0xdom", "0xliq", "0xvault", "0xrfq"}])
    out = cl.classify_fills(
        fills,
        liquidation_tx={"0x0"},
        vault_wallets={"0xvault", "0xliq"},
        dominant={(w, months) for w in ("0xdom", "0xliq", "0xvault", "0xrfq")},
        large={(w, months) for w in everyone},
        mm_lookup=lookup,
    )
    assert list(out["taker_class"]) == ["liquidation", "vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]
    assert out["is_rfq"].sum() == 3 and out["month"].iloc[0] == months


def test_wallet_month_stats_dominant_and_large():
    rows = []
    for i in range(10):
        rows += fill(f"a{i}", JAN + i, "0xmm", f"0xt{i}", amount=1.0)
    rows += fill("b0", JAN + 50, "0xsmall", "0xmm", amount=0.5)
    rows += fill("c0", JAN + 60, "0xmm", "0xwhale", amount=100.0)
    rows += fill("d0", FEB, "0xt1", "0xmm", amount=1.0)
    fills, _ = cl.pair_fills(pd.DataFrame(rows))
    stats = cl.wallet_month_stats(fills)
    mm_jan = stats[(stats.wallet == "0xmm") & (stats.month == "2024-01")].iloc[0]
    assert mm_jan.maker_share == pytest.approx(110 / 110.5)
    assert mm_jan.maker_volume_share == pytest.approx(110 / 110.5)
    dom = cl.dominant_makers(stats)
    assert ("0xmm", "2024-01") in dom and ("0xmm", "2024-02") not in dom and ("0xsmall", "2024-01") not in dom
    assert ("0xwhale", "2024-01") in cl.large_takers(stats)
    assert ("0xt3", "2024-01") not in cl.large_takers(stats)


def test_mm_programme_lookup_and_membership():
    scores = pd.DataFrame([
        {"program": "OPTIONS-MAJ", "start_ms": 100, "end_ms": 200, "wallet": "0xa", "total_score": 1.0},
        {"program": "OPTIONS-MID", "start_ms": 100, "end_ms": 200, "wallet": "0xc", "total_score": 2.0},
        {"program": "OPTIONS-MAJ", "start_ms": 100, "end_ms": 200, "wallet": "0xb", "total_score": 0.0},
        {"program": "OPTIONS-MAJ", "start_ms": 300, "end_ms": 400, "wallet": "0xb", "total_score": 5.0},
    ])
    lookup = cl.mm_programme_lookup(scores)
    got = cl.in_mm_programme(np.array([150, 150, 150, 250, 350, 50]), np.array(["0xa", "0xb", "0xc", "0xa", "0xb", "0xa"]), lookup)
    assert list(got) == [True, False, True, False, True, False]
    empty = cl.mm_programme_lookup(scores.iloc[0:0])
    assert not cl.in_mm_programme(np.array([150]), np.array(["0xa"]), empty).any()


def test_mm_programme_overlapping_epochs():
    nested = pd.DataFrame([
        {"program": "A", "start_ms": 100, "end_ms": 400, "wallet": "0xa", "total_score": 1.0},
        {"program": "B", "start_ms": 200, "end_ms": 300, "wallet": "0xb", "total_score": 1.0},
    ])
    got = cl.in_mm_programme(np.array([250, 250, 350]), np.array(["0xa", "0xb", "0xb"]), cl.mm_programme_lookup(nested))
    assert list(got) == [True, True, False]
    same_start = pd.DataFrame([
        {"program": "A", "start_ms": 100, "end_ms": 400, "wallet": "0xa", "total_score": 1.0},
        {"program": "B", "start_ms": 100, "end_ms": 300, "wallet": "0xb", "total_score": 1.0},
    ])
    got = cl.in_mm_programme(np.array([150, 350]), np.array(["0xb", "0xb"]), cl.mm_programme_lookup(same_start))
    assert list(got) == [True, False]


def test_load_vault_wallets_validates(tmp_path):
    good = tmp_path / "v.csv"
    good.write_text("# comment\nwallet,vault_name,source\n0xAbCdEf0123456789abcdef0123456789ABCDEF01,Test,https://x\n")
    assert cl.load_vault_wallets(good) == {"0xabcdef0123456789abcdef0123456789abcdef01"}
    bad = tmp_path / "b.csv"
    bad.write_text("wallet,vault_name,source\n0x123,Test,https://x\n")
    with pytest.raises(ValueError, match="invalid"):
        cl.load_vault_wallets(bad)
    missing = tmp_path / "m.csv"
    missing.write_text("wallet,name\n0xAbCdEf0123456789abcdef0123456789ABCDEF01,x\n")
    with pytest.raises(ValueError, match="columns"):
        cl.load_vault_wallets(missing)


def test_build_fills_end_to_end(tmp_path):
    tape_dir, ref_dir = tmp_path / "tape", tmp_path / "ref"
    tape_dir.mkdir()
    ref_dir.mkdir()
    rows = fill("a", JAN, "0xm", "0xt", tx="0xLIQ") + fill("b", JAN + 1, "0xm", "0xu", amount=0.1)
    pd.DataFrame(rows).to_parquet(tape_dir / "BTC_options_full.parquet")
    pd.DataFrame({"auction_id": ["x"], "tx_hash": ["0xnope"]}).to_parquet(ref_dir / "liquidation_auctions.parquet")
    pd.DataFrame({"auction_id": ["x"], "tx_hash": ["0xliq"]}).to_parquet(ref_dir / "liquidation_bids.parquet")
    pd.DataFrame(columns=["program", "start_ms", "end_ms", "wallet", "total_score"]).to_parquet(ref_dir / "maker_scores.parquet")
    vaults = tmp_path / "v.csv"
    vaults.write_text("wallet,vault_name,source\n")
    out = tmp_path / "derived" / "fills.parquet"
    out.parent.mkdir()
    summary = cl.build_fills(tape_dir, ref_dir, vaults, out)
    assert summary["fills"] == 2 and summary["unpaired_rows"] == 0 and summary["pair_mismatch"] == 0
    got = pd.read_parquet(out)
    assert list(got["taker_class"]) == ["liquidation", "other"]
    assert (tmp_path / "derived" / "wallet_month_stats.parquet").exists()
