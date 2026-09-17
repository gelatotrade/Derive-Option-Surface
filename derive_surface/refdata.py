"""Reference data for paper 1: settlement prices, liquidations, maker programmes, vaults, fees, funding.

``get_liquidation_history`` returned different subsets for different page sizes on 2026-09-17 (count 76,
page size 100 → 23 auctions), so auctions are collected as the union over several page sizes and the
reported count is kept next to the number actually found.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import pandas as pd

from .api import DeriveError

log = logging.getLogger(__name__)

OPTION_CURRENCIES = ["BTC", "ETH", "HYPE", "SOL", "XRP", "ZEC", "ADA", "XAUT", "CC", "VVV", "LIT", "PUMP"]
PERPS = ("BTC-PERP", "ETH-PERP", "HYPE-PERP")
SCORE_FIELDS = ["total_score", "coverage_score", "quality_score", "volume_multiplier", "holder_boost", "volume"]


def settlement_prices(client, currencies: Iterable[str]) -> pd.DataFrame:
    rows = []
    for ccy in currencies:
        for e in client.call("get_option_settlement_prices", currency=ccy)["expiries"]:
            rows.append({"currency": ccy, "expiry": int(e["utc_expiry_sec"]), "expiry_date": e["expiry_date"],
                         "settlement_price": float(e["price"])})
    df = pd.DataFrame(rows, columns=["currency", "expiry", "expiry_date", "settlement_price"])
    return df.sort_values(["currency", "expiry"]).reset_index(drop=True)


def liquidations(client, page_sizes: Sequence[int] = (5, 20, 50, 100)) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    found = {}
    reported = None
    for size in page_sizes:
        page, pages = 1, 1
        while page <= pages:
            res = client.call("get_liquidation_history", page=page, page_size=size)
            pages = int(res["pagination"]["num_pages"])
            reported = int(res["pagination"]["count"])
            for a in res["auctions"]:
                found[a["auction_id"]] = a
            page += 1
    auction_cols = ["auction_id", "subaccount_id", "start_timestamp", "end_timestamp", "auction_type", "fee", "tx_hash"]
    bid_cols = ["auction_id", "subaccount_id", "timestamp", "tx_hash", "percent_liquidated", "cash_received", "discount_pnl", "instruments"]
    arows, brows = [], []
    for a in found.values():
        arows.append({k: a.get(k) for k in auction_cols})
        for b in a.get("bids") or []:
            brows.append({"auction_id": a["auction_id"], "subaccount_id": a["subaccount_id"], "timestamp": b.get("timestamp"),
                          "tx_hash": b.get("tx_hash"), "percent_liquidated": b.get("percent_liquidated"),
                          "cash_received": b.get("cash_received"), "discount_pnl": b.get("discount_pnl"),
                          "instruments": json.dumps(b.get("amounts_liquidated") or {})})
    info = {"reported_count": reported, "unique_auctions": len(found)}
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
        except DeriveError as err:
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


def save_all(client, ref_dir: Path, currencies: Iterable[str] = OPTION_CURRENCIES) -> dict:
    ref_dir.mkdir(parents=True, exist_ok=True)
    currencies = list(currencies)
    stamp = time.strftime("%Y%m%d", time.gmtime())
    out: dict = {"fetched_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime())}
    sp = settlement_prices(client, currencies)
    sp.to_parquet(ref_dir / "settlement_prices.parquet", index=False)
    out["settlement_prices"] = sp.groupby("currency").size().to_dict()
    auctions, bids, info = liquidations(client)
    auctions.to_parquet(ref_dir / "liquidation_auctions.parquet", index=False)
    bids.to_parquet(ref_dir / "liquidation_bids.parquet", index=False)
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
