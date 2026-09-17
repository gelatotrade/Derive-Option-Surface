"""Pair maker and taker rows into fills and classify the taker of every fill (paper 1, spec §3).

Class priority (first match wins): liquidation > vault > rfq > dominant maker > MM programme > large > other.
Every flag is also kept as its own column so that analyses can cross-tabulate.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set, Tuple

import numpy as np
import pandas as pd

CLASS_ORDER = ["liquidation", "vault", "rfq", "dominant_maker", "mm_programme", "large", "other"]
DOMINANT_MAKER_SHARE = 0.80
DOMINANT_MIN_VOLUME_SHARE = 0.01
LARGE_TAKER_QUANTILE = 0.99
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
WalletMonths = Set[Tuple[str, str]]
MMLookup = Tuple[np.ndarray, np.ndarray, List[Set[str]]]


def month_of(ts_ms) -> pd.Series:
    return pd.to_datetime(pd.Series(ts_ms), unit="ms", utc=True).dt.strftime("%Y-%m")


def pair_fills(tape: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """One row per fill from its maker and taker row; rows of trade_ids without exactly one of each are returned apart."""
    roles = tape.assign(_maker=tape["liquidity_role"].eq("maker"), _taker=tape["liquidity_role"].eq("taker"))
    counts = roles.groupby("trade_id")[["_maker", "_taker"]].sum()
    good = counts.index[(counts["_maker"] == 1) & (counts["_taker"] == 1)]
    is_good = tape["trade_id"].isin(good)
    unpaired = tape[~is_good].reset_index(drop=True)
    paired = tape[is_good]
    t = paired[paired["liquidity_role"] == "taker"].set_index("trade_id")
    m = paired[paired["liquidity_role"] == "maker"].set_index("trade_id").loc[t.index]
    fills = pd.DataFrame({
        "trade_id": t.index.to_numpy(),
        "ts": t["timestamp"].to_numpy(),
        "ts_maker": m["timestamp"].to_numpy(),
        "instrument_name": t["instrument_name"].to_numpy(),
        "currency": t["currency"].to_numpy(),
        "expiry": t["expiry"].to_numpy(),
        "strike": t["strike"].to_numpy(),
        "option_type": t["option_type"].to_numpy(),
        "price": t["trade_price"].to_numpy(),
        "amount": t["trade_amount"].to_numpy(),
        "mark_price": t["mark_price"].to_numpy(),
        "index_price": t["index_price"].to_numpy(),
        "mark_price_maker_row": m["mark_price"].to_numpy(),
        "taker_side": np.where(t["direction"].to_numpy() == "buy", 1, -1),
        "taker_wallet": t["wallet"].to_numpy(),
        "taker_sub": t["subaccount_id"].to_numpy(),
        "maker_wallet": m["wallet"].to_numpy(),
        "maker_sub": m["subaccount_id"].to_numpy(),
        "rfq_id": t["rfq_id"].where(t["rfq_id"].notna(), m["rfq_id"]).to_numpy(),
        "tx_hash": t["tx_hash"].to_numpy(),
        "tx_status": t["tx_status"].to_numpy(),
        "fee_taker": t["trade_fee"].to_numpy(),
        "fee_maker": m["trade_fee"].to_numpy(),
        "rebate_maker": m["expected_rebate"].to_numpy(),
        "rebate_taker": t["expected_rebate"].to_numpy(),
        "pnl_taker": t["realized_pnl"].to_numpy(),
        "pnl_maker": m["realized_pnl"].to_numpy(),
    })
    fills["notional"] = fills["amount"] * fills["index_price"]
    fills["pair_ok"] = (
        np.isclose(t["trade_price"].to_numpy(float), m["trade_price"].to_numpy(float), rtol=1e-9, atol=0.0)
        & np.isclose(t["trade_amount"].to_numpy(float), m["trade_amount"].to_numpy(float), rtol=1e-9, atol=0.0)
        & (t["direction"].to_numpy() != m["direction"].to_numpy())
    )
    return fills.sort_values(["ts", "trade_id"]).reset_index(drop=True), unpaired


def wallet_month_stats(fills: pd.DataFrame) -> pd.DataFrame:
    month = month_of(fills["ts"].to_numpy()).to_numpy()
    maker = fills.groupby([fills["maker_wallet"].to_numpy(), month])["notional"].sum().rename("maker_notional")
    taker = fills.groupby([fills["taker_wallet"].to_numpy(), month])["notional"].sum().rename("taker_notional")
    stats = pd.concat([maker, taker], axis=1).fillna(0.0)
    stats.index = stats.index.set_names(["wallet", "month"])
    stats = stats.reset_index()
    stats["maker_share"] = stats["maker_notional"] / (stats["maker_notional"] + stats["taker_notional"])
    stats["maker_volume_share"] = stats["maker_notional"] / stats.groupby("month")["maker_notional"].transform("sum")
    return stats


def dominant_makers(stats: pd.DataFrame, min_share: float = DOMINANT_MAKER_SHARE,
                    min_volume_share: float = DOMINANT_MIN_VOLUME_SHARE) -> WalletMonths:
    sel = stats[(stats["maker_share"] >= min_share) & (stats["maker_volume_share"] >= min_volume_share)]
    return set(zip(sel["wallet"], sel["month"]))


def large_takers(stats: pd.DataFrame, q: float = LARGE_TAKER_QUANTILE) -> WalletMonths:
    takers = stats[stats["taker_notional"] > 0]
    threshold = takers.groupby("month")["taker_notional"].transform(lambda s: s.quantile(q))
    sel = takers[takers["taker_notional"] >= threshold]
    return set(zip(sel["wallet"], sel["month"]))


def mm_programme_lookup(scores: pd.DataFrame) -> MMLookup:
    active = scores[scores["total_score"] > 0]
    if active.empty:
        return np.array([], dtype="int64"), np.array([], dtype="int64"), []
    epochs = active.groupby(["start_ms", "end_ms"])["wallet"].apply(set).reset_index().sort_values("start_ms")
    return epochs["start_ms"].to_numpy("int64"), epochs["end_ms"].to_numpy("int64"), list(epochs["wallet"])


def in_mm_programme(ts: np.ndarray, wallets: np.ndarray, lookup: MMLookup) -> np.ndarray:
    starts, ends, sets = lookup
    out = np.zeros(len(ts), dtype=bool)
    if len(starts) == 0:
        return out
    idx = np.searchsorted(starts, ts, side="right") - 1
    for i, (j, wallet) in enumerate(zip(idx, wallets)):
        if j >= 0 and ts[i] < ends[j] and wallet in sets[j]:
            out[i] = True
    return out


def load_vault_wallets(path: Path) -> Set[str]:
    df = pd.read_csv(path, comment="#", dtype=str)
    missing = {"wallet", "vault_name", "source"} - set(df.columns)
    if missing:
        raise ValueError(f"vault list lacks columns {sorted(missing)}")
    wallets = df["wallet"].str.strip().str.lower()
    bad = wallets[~wallets.str.match(ADDRESS)]
    if len(bad):
        raise ValueError(f"invalid wallet addresses: {list(bad)[:3]}")
    return set(wallets)


def classify_fills(fills: pd.DataFrame, *, liquidation_tx: Set[str], vault_wallets: Set[str], dominant: WalletMonths,
                   large: WalletMonths, mm_lookup: MMLookup) -> pd.DataFrame:
    f = fills.copy()
    month = month_of(f["ts"].to_numpy()).to_numpy()
    taker = f["taker_wallet"].to_numpy()
    maker = f["maker_wallet"].to_numpy()
    f["is_liquidation"] = f["tx_hash"].str.lower().isin(liquidation_tx).to_numpy()
    f["taker_is_vault"] = f["taker_wallet"].isin(vault_wallets)
    f["maker_is_vault"] = f["maker_wallet"].isin(vault_wallets)
    f["is_rfq"] = f["rfq_id"].notna()
    f["taker_is_dominant_maker"] = [(w, mo) in dominant for w, mo in zip(taker, month)]
    f["maker_is_dominant_maker"] = [(w, mo) in dominant for w, mo in zip(maker, month)]
    f["taker_in_mm_programme"] = in_mm_programme(f["ts"].to_numpy("int64"), taker, mm_lookup)
    f["taker_is_large"] = [(w, mo) in large for w, mo in zip(taker, month)]
    flags = [("liquidation", "is_liquidation"), ("vault", "taker_is_vault"), ("rfq", "is_rfq"),
             ("dominant_maker", "taker_is_dominant_maker"), ("mm_programme", "taker_in_mm_programme"), ("large", "taker_is_large")]
    cls = np.full(len(f), "other", dtype=object)
    for name, col in reversed(flags):
        cls = np.where(f[col].to_numpy(bool), name, cls)
    f["taker_class"] = cls
    f["month"] = month
    return f


def build_fills(tape_dir: Path, ref_dir: Path, vault_csv: Path, out_path: Path) -> dict:
    tape = pd.concat([pd.read_parquet(p) for p in sorted(tape_dir.glob("*_options_full.parquet"))], ignore_index=True)
    fills, unpaired = pair_fills(tape)
    stats = wallet_month_stats(fills)
    auctions = pd.read_parquet(ref_dir / "liquidation_auctions.parquet")
    bids = pd.read_parquet(ref_dir / "liquidation_bids.parquet")
    liq = set(auctions["tx_hash"].dropna().str.lower()) | set(bids["tx_hash"].dropna().str.lower())
    scores = pd.read_parquet(ref_dir / "maker_scores.parquet")
    out = classify_fills(fills, liquidation_tx=liq, vault_wallets=load_vault_wallets(vault_csv),
                         dominant=dominant_makers(stats), large=large_takers(stats), mm_lookup=mm_programme_lookup(scores))
    out.to_parquet(out_path, index=False, compression="zstd")
    stats.to_parquet(out_path.with_name("wallet_month_stats.parquet"), index=False)
    classes = (out.groupby(["currency", "taker_class"])
                  .agg(fills=("trade_id", "size"), notional=("notional", "sum"))
                  .reset_index())
    return {
        "rows": int(len(tape)), "fills": int(len(out)), "unpaired_rows": int(len(unpaired)),
        "unpaired_trade_ids": int(unpaired["trade_id"].nunique()) if len(unpaired) else 0,
        "pair_mismatch": int((~out["pair_ok"]).sum()), "not_settled": int((out["tx_status"] != "settled").sum()),
        "liquidation_tx": len(liq), "classes": classes.to_dict("records"),
    }
