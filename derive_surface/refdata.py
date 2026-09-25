"""Reference data for paper 1: settlement prices, liquidations, maker programmes, vaults, fees, funding.

``get_liquidation_history`` covers only the last seven days unless a time window is given, so the full
history is walked in daily windows with small pages (see ``liquidations``).
"""
from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from .api import DeriveError

log = logging.getLogger(__name__)

OPTION_CURRENCIES = ["BTC", "ETH", "HYPE", "SOL", "XRP", "ZEC", "ADA", "XAUT", "CC", "VVV", "LIT", "PUMP"]
PERPS = ("BTC-PERP", "ETH-PERP", "HYPE-PERP")
DAY_MS = 86_400_000
HISTORY_START_MS = 1_704_067_200_000  # 2024-01-01 00:00 UTC
SCORE_FIELDS = ["total_score", "coverage_score", "quality_score", "volume_multiplier", "holder_boost", "volume"]


def settlement_prices(client, currencies: Iterable[str]) -> pd.DataFrame:
    rows = []
    for ccy in currencies:
        for e in client.call("get_option_settlement_prices", currency=ccy)["expiries"]:
            rows.append({"currency": ccy, "expiry": int(e["utc_expiry_sec"]), "expiry_date": e["expiry_date"],
                         "settlement_price": float(e["price"])})
    df = pd.DataFrame(rows, columns=["currency", "expiry", "expiry_date", "settlement_price"])
    return df.sort_values(["currency", "expiry"]).reset_index(drop=True)


def _liquidation_pages(client, lo: int, hi: int, page_size: int, found: dict) -> None:
    page, pages = 1, 1
    while page <= pages:
        res = client.call("get_liquidation_history", page=page, page_size=page_size, start_timestamp=lo, end_timestamp=hi)
        pages = int(res["pagination"]["num_pages"])  # the endpoint reports page+1 while more rows follow
        for a in res["auctions"]:
            cur = found.setdefault(a["auction_id"], {**a, "bids": []})
            seen = {(b.get("tx_hash"), b.get("timestamp")) for b in cur["bids"]}
            cur["bids"].extend(b for b in a.get("bids") or [] if (b.get("tx_hash"), b.get("timestamp")) not in seen)
        page += 1


def _liquidation_window(client, lo: int, hi: int, page_sizes: Sequence[int], min_window_ms: int, found: dict, gaps: list) -> None:
    for size in page_sizes:  # first page size that works; all sizes return the same auctions
        try:
            _liquidation_pages(client, lo, hi, size, found)
            return
        except RuntimeError as err:
            log.warning("liquidations [%d, %d] page_size %d failed: %s", lo, hi, size, err)
    if hi - lo + 1 > min_window_ms:
        mid = (lo + hi) // 2
        _liquidation_window(client, lo, mid, page_sizes, min_window_ms, found, gaps)
        _liquidation_window(client, mid + 1, hi, page_sizes, min_window_ms, found, gaps)
    else:
        gaps.append([lo, hi])


def _merge_auctions(into: dict, other: dict) -> None:
    for aid, a in other.items():
        cur = into.setdefault(aid, {**a, "bids": []})
        seen = {(b.get("tx_hash"), b.get("timestamp")) for b in cur["bids"]}
        cur["bids"].extend(b for b in a["bids"] if (b.get("tx_hash"), b.get("timestamp")) not in seen)


def liquidations(client, start_ms: int, end_ms: int, *, window_ms: int = DAY_MS, page_sizes: Sequence[int] = (100, 20, 5),
                 min_window_ms: int = 3_600_000, workers: int = 6) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Liquidation auctions in [start_ms, end_ms], walked in short windows (in parallel).

    Measured 2026-09-17: without time filters the endpoint returns only the last seven days; ``count`` and
    ``num_pages`` only say whether another page follows; some windows fail with HTTP 500 for page size 100 but
    work with small pages.  All page sizes return the same auctions, but the ``bids`` are incomplete and the
    more so the smaller the page (2025-10-10: 242 auctions, 34 bids at size 100, 4 at size 5), so the largest
    working size is used; a window that fails for all sizes is halved down to ``min_window_ms`` and otherwise
    returned as a gap.  Auctions split across pages or windows are merged.  Complete bid data would have to
    come from the on-chain DutchAuction events.
    """
    windows = [(lo, min(lo + window_ms - 1, end_ms)) for lo in range(start_ms, end_ms + 1, window_ms)]

    def run(window: Tuple[int, int]) -> Tuple[dict, list]:
        part: dict = {}
        part_gaps: list = []
        _liquidation_window(client, window[0], window[1], page_sizes, min_window_ms, part, part_gaps)
        return part, part_gaps

    found: dict = {}
    gaps: list = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, (part, part_gaps) in enumerate(pool.map(run, windows), 1):
            _merge_auctions(found, part)
            gaps.extend(part_gaps)
            if i % 50 == 0 or i == len(windows):
                log.info("liquidations: %d/%d windows, %d auctions, %d gaps", i, len(windows), len(found), len(gaps))
    auction_cols = ["auction_id", "subaccount_id", "start_timestamp", "end_timestamp", "auction_type", "fee", "tx_hash"]
    bid_cols = ["auction_id", "subaccount_id", "timestamp", "tx_hash", "percent_liquidated", "cash_received", "discount_pnl", "instruments"]
    arows, brows = [], []
    for a in found.values():
        arows.append({k: a.get(k) for k in auction_cols})
        for b in a["bids"]:
            brows.append({"auction_id": a["auction_id"], "subaccount_id": a["subaccount_id"], "timestamp": b.get("timestamp"),
                          "tx_hash": b.get("tx_hash"), "percent_liquidated": b.get("percent_liquidated"),
                          "cash_received": b.get("cash_received"), "discount_pnl": b.get("discount_pnl"),
                          "instruments": json.dumps(b.get("amounts_liquidated") or {})})
    info = {"windows": len(windows), "unique_auctions": len(found), "gaps": gaps}
    return pd.DataFrame(arows, columns=auction_cols), pd.DataFrame(brows, columns=bid_cols), info


def maker_programs(client) -> pd.DataFrame:
    rows = []
    for p in client.call("get_maker_programs"):
        rows.append({"name": p["name"], "asset_types": ",".join(p.get("asset_types") or []),
                     "currencies": ",".join(p.get("currencies") or []), "min_notional": float(p.get("min_notional") or 0),
                     "start_ms": int(p["start_timestamp"]), "end_ms": int(p["end_timestamp"]),
                     "rewards": json.dumps(p.get("rewards") or {}, sort_keys=True)})
    cols = ["name", "asset_types", "currencies", "min_notional", "start_ms", "end_ms", "rewards"]
    return pd.DataFrame(rows, columns=cols).sort_values(["start_ms", "name"]).reset_index(drop=True)


def maker_scores(client, programs: pd.DataFrame, asset_type: str = "option") -> pd.DataFrame:
    rows = []
    selected = programs[programs["asset_types"].str.split(",").map(lambda xs: asset_type in xs)]
    for name, start_ms, end_ms in zip(selected["name"], selected["start_ms"], selected["end_ms"]):
        try:
            res = client.call("get_maker_program_scores", program_name=name, epoch_start_timestamp=int(start_ms))
        except (DeriveError, RuntimeError) as err:  # RuntimeError: the client gave up (network)
            log.warning("scores %s@%s unavailable: %s", name, start_ms, err)
            continue
        for s in res.get("scores") or []:
            row = {"program": name, "start_ms": int(start_ms), "end_ms": int(end_ms), "wallet": s["wallet"].lower()}
            row.update({k: float(s.get(k) or 0) for k in SCORE_FIELDS})
            rows.append(row)
    return pd.DataFrame(rows, columns=["program", "start_ms", "end_ms", "wallet"] + SCORE_FIELDS)


def vault_statistics(client) -> pd.DataFrame:
    return pd.DataFrame(client.call("get_vault_statistics")).astype(str)


def instrument_fees(client, currencies: Iterable[str]) -> pd.DataFrame:
    keep = ["instrument_name", "maker_fee_rate", "taker_fee_rate", "base_fee", "mark_price_fee_rate_cap",
            "pro_rata_fraction", "fifo_min_allocation", "pro_rata_amount_step", "tick_size", "minimum_amount", "amount_step"]
    rows = []
    for ccy in currencies:
        for inst in client.call("get_instruments", currency=ccy, instrument_type="option", expired=False):
            row = {"currency": ccy}
            row.update({k: None if inst.get(k) is None else str(inst.get(k)) for k in keep})
            rows.append(row)
    return pd.DataFrame(rows, columns=["currency"] + keep)


def funding_history(client, instruments: Iterable[str] = PERPS) -> pd.DataFrame:
    rows = []
    for name in instruments:
        for r in client.call("get_funding_rate_history", instrument_name=name)["funding_rate_history"]:
            rows.append({"instrument_name": name, "timestamp": int(r["timestamp"]), "funding_rate": float(r["funding_rate"])})
    return pd.DataFrame(rows, columns=["instrument_name", "timestamp", "funding_rate"])


def merge_append(path: Path, new: pd.DataFrame, key: List[str]) -> pd.DataFrame:
    """Union of an existing parquet and ``new``; on key collisions the new row wins."""
    if path.exists():
        new = pd.concat([pd.read_parquet(path), new], ignore_index=True).drop_duplicates(key, keep="last")
    new = new.sort_values(key).reset_index(drop=True)
    new.to_parquet(path, index=False)
    return new


def save_all(client, ref_dir: Path, currencies: Iterable[str] = OPTION_CURRENCIES, end_ms: Optional[int] = None,
             skip_liquidations: bool = False) -> dict:
    ref_dir.mkdir(parents=True, exist_ok=True)
    end_ms = int(time.time() * 1000) if end_ms is None else end_ms
    currencies = list(currencies)
    stamp = time.strftime("%Y%m%d", time.gmtime())
    out: dict = {"fetched_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime())}
    sp = settlement_prices(client, currencies)
    sp.to_parquet(ref_dir / "settlement_prices.parquet", index=False)
    out["settlement_prices"] = sp.groupby("currency").size().to_dict()
    auction_path, bid_path = ref_dir / "liquidation_auctions.parquet", ref_dir / "liquidation_bids.parquet"
    if skip_liquidations and auction_path.exists() and bid_path.exists():
        out["liquidations"] = {"source": "existing files", "unique_auctions": len(pd.read_parquet(auction_path)),
                               "bids": len(pd.read_parquet(bid_path))}
    else:
        auctions, bids, info = liquidations(client, HISTORY_START_MS, end_ms)
        auctions.to_parquet(auction_path, index=False)
        bids.to_parquet(bid_path, index=False)
        out["liquidations"] = {**info, "bids": len(bids)}
    programs = maker_programs(client)
    programs.to_parquet(ref_dir / "maker_programs.parquet", index=False)
    scores = maker_scores(client, programs)
    scores.to_parquet(ref_dir / "maker_scores.parquet", index=False)
    out["maker_programmes"] = {"programmes": len(programs), "option_score_rows": len(scores),
                               "active_wallets": int(scores.loc[scores["total_score"] > 0, "wallet"].nunique())}
    vaults = vault_statistics(client)
    vaults.to_parquet(ref_dir / f"vault_statistics_{stamp}.parquet", index=False)
    out["vaults"] = len(vaults)
    fees = instrument_fees(client, currencies)
    fees.to_parquet(ref_dir / f"instrument_fees_{stamp}.parquet", index=False)
    out["instruments"] = len(fees)
    funding = merge_append(ref_dir / "funding_history.parquet", funding_history(client), ["instrument_name", "timestamp"])
    out["funding_rows"] = len(funding)
    (ref_dir / "REFDATA.json").write_text(json.dumps(out, indent=1, default=str))
    return out
