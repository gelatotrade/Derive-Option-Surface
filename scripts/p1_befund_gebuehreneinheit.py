#!/usr/bin/env python3
"""Fee-unit finding for paper 1: what the headline numbers become when fee and rebate are taken per contract.

Paper 1 (``inference_p1.analysis_frame``) forms
    net_edge = mo_usd - fee_maker + rebate_maker - hedge,
where ``mo_usd`` and ``hedge`` are per contract but ``fee_maker`` and ``rebate_maker`` are the sums booked on
the maker row of the fill (P2 pre-registration, addendum 2).  This script copies that logic, reproduces the
paper 1 numbers exactly (``fee_unit="p1"``) and recomputes them with fee and rebate divided by the fill amount
(``fee_unit="per_contract"``).  Nothing in paper 1 is changed; the helpers that do not touch the fee
(``hedge_cost``, ``cluster_mean_ci``, ``cell_table``, ``figdata.cell_matrix``) are imported unchanged.
Finding and numbers: docs/paper1/BEFUND_2026-09-25_GEBUEHRENEINHEIT.md, results/p1_befund/.

    python3 scripts/p2_heavy.py --wait-max 500 -- python3 scripts/p1_befund_gebuehreneinheit.py

Inputs are the paper 1 files under data/p1 (markouts, funding) and results/p1.  The run is resumable: every
step writes a part file under ``--parts`` (default data/p1/befund_gebuehreneinheit, ignored by git) and is
skipped when that file exists; ``--max-seconds`` stops before starting a step once the budget is spent (exit
code 3 = call again).  The sections of results/p1_befund/gebuehreneinheit.csv up to ``f1_premium_share`` are
the numbers of the finding as committed on 25.09.2026; the sections after it answer the audit of Paper 2
(docs/paper2/AUDIT.md, A65 to A68) and are appended so that the earlier rows stay where they were.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from derive_surface import figdata  # noqa: E402
from derive_surface import inference_p1 as inf  # noqa: E402

SCRIPT = "scripts/p1_befund_gebuehreneinheit.py"
HORIZON = "30m"
P1_SEED = 20260917                  # paper 1 registered seed: needed to reproduce its intervals exactly
B_CELLS = 9_999                     # paper 1 registered H4 run, and the draws the paper 1 text states
B_FIGURE = 999                      # paper 1 figures (T2 error bars) and the class net-edge intervals here
HALF_SPREADS = (1.0, 0.0, 3.0)      # registered value first, then the paper 1 sensitivity
FEE_UNITS = ("p1", "per_contract")
PACKAGE_UNIT = "per_contract_package"   # sensitivity: an RFQ package's fee spread over its legs (audit A67)
CURRENCIES = ("BTC", "ETH", "HYPE")
ATM = {"currencies": ("BTC", "ETH"), "delta_bucket": "40-60", "tenor_bucket": "<=2d"}
H4_RULE = ("P1 H4: rejected if >= 50 % of occupied cells (>= 200 fills) have a positive 90 % cluster bootstrap "
           "interval of the mean net edge, or if cell BTC/ETH x [40,60) x <=2d has a positive interval")
COLUMNS = ["trade_id", "ts", "instrument_name", "currency", "price", "amount", "index_price", "notional",
           "maker_side", "mark_b_t", "mo_usd_30m", "mo_dn_30m", "mo_vol_30m", "delta_t", "fwd_t", "fee_maker",
           "rebate_maker", "taker_wallet", "taker_class", "delta_bucket", "tenor_bucket", "rfq_id", "maker_wallet"]
PACKAGE_KEY = ["rfq_id", "maker_wallet"]

MARKOUTS = REPO / "data" / "p1" / "derived" / "markouts.parquet"
FUNDING = REPO / "data" / "p1" / "ref" / "funding_history.parquet"
P1_RESULTS = REPO / "results" / "p1"
ABBILDUNGEN = REPO / "docs" / "paper1" / "ABBILDUNGEN.md"
PARTS = REPO / "data" / "p1" / "befund_gebuehreneinheit"
OUT_DIR = REPO / "results" / "p1_befund"


# ------------------------------------------------------------------------------------------ the net edge

def _is_rfq(frame: pd.DataFrame) -> np.ndarray:
    if "rfq_id" not in frame:
        return np.zeros(len(frame), dtype=bool)
    ids = frame["rfq_id"]
    return (ids.notna() & (ids.astype(str) != "")).to_numpy()


def package_per_contract(frame: pd.DataFrame) -> Dict[str, np.ndarray]:
    """Fee and rebate per contract with an RFQ package's booking spread over its legs.

    On a multi-leg RFQ the maker fee is almost always booked on one leg of the package (audit A67); dividing
    it by that leg's amount puts the whole package on one leg.  Here every leg of a package (same ``rfq_id``
    and maker wallet) carries sum(fee) / sum(amount).  Order book fills and one-leg packages are unchanged.
    """
    amount = frame["amount"].to_numpy(float)
    amount = np.where(amount > 0, amount, np.nan)
    fee = frame["fee_maker"].to_numpy(float) / amount
    rebate = frame["rebate_maker"].to_numpy(float) / amount
    rfq = _is_rfq(frame)
    if rfq.any():
        sub = frame.loc[rfq, PACKAGE_KEY].assign(
            amount=amount[rfq], fee=frame["fee_maker"].to_numpy(float)[rfq],
            rebate=frame["rebate_maker"].to_numpy(float)[rfq])
        g = sub.groupby(PACKAGE_KEY, sort=False, dropna=False)
        total = g["amount"].transform("sum").to_numpy(float)
        total = np.where(total > 0, total, np.nan)
        ok = np.isfinite(amount[rfq])
        fee[rfq] = np.where(ok, g["fee"].transform("sum").to_numpy(float) / total, np.nan)
        rebate[rfq] = np.where(ok, g["rebate"].transform("sum").to_numpy(float) / total, np.nan)
    return {"fee": fee, "rebate": rebate}


def net_edge_frame(markouts: pd.DataFrame, funding: pd.DataFrame, fee_unit: str = "p1",
                   half_spread_bp: float = 1.0, horizon: str = HORIZON) -> pd.DataFrame:
    """Copy of ``inference_p1.analysis_frame`` (same operations, same order) with a choice of fee unit.

    ``fee_unit="p1"`` subtracts the fee and rebate sums of the fill from the per-contract markout, exactly as
    paper 1 does; ``"per_contract"`` divides both by the fill amount first; ``"per_contract_package"`` also
    spreads the fee of a multi-leg RFQ package over its legs.  ``fill_edge`` = net_edge x amount is the edge
    of the whole fill in USDC.
    """
    if fee_unit not in FEE_UNITS + (PACKAGE_UNIT,):
        raise ValueError("fee_unit must be one of {}".format(FEE_UNITS + (PACKAGE_UNIT,)))
    tau = inf.HORIZON_SECONDS[horizon]
    f = markouts.copy()
    rates = (funding.assign(ccy=funding["instrument_name"].str.split("-").str[0])
                    .groupby("ccy")["funding_rate"].apply(lambda x: float(np.median(np.abs(x)))))
    f["funding_per_hour"] = f["currency"].map(rates).fillna(
        float(np.median(np.abs(funding["funding_rate"]))) if len(funding) else 0.0)
    side = f["maker_side"].to_numpy(float)
    f["hs"] = side * (f["mark_b_t"].to_numpy() - f["price"].to_numpy())
    f["y_usd"] = f["mo_usd_{}".format(horizon)].to_numpy()
    f["as_usd"] = f["y_usd"] - f["hs"]
    f["hedge"] = inf.hedge_cost(f["delta_t"].to_numpy(), f["fwd_t"].to_numpy(), tau, f["funding_per_hour"].to_numpy(),
                                half_spread_bp=half_spread_bp)
    if fee_unit == "p1":
        f["fee"] = f["fee_maker"].to_numpy()
        f["rebate"] = f["rebate_maker"].to_numpy()
    elif fee_unit == "per_contract":
        amount = f["amount"].to_numpy(float)
        amount = np.where(amount > 0, amount, np.nan)
        f["fee"] = f["fee_maker"].to_numpy(float) / amount
        f["rebate"] = f["rebate_maker"].to_numpy(float) / amount
    else:
        spread = package_per_contract(f)
        f["fee"], f["rebate"] = spread["fee"], spread["rebate"]
    f["net_edge"] = f["y_usd"] - f["fee"].to_numpy() + f["rebate"].to_numpy() - f["hedge"].to_numpy()
    f["fill_edge"] = f["net_edge"] * f["amount"].to_numpy(float)
    f["day"] = pd.to_datetime(f["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    f["cluster"] = f["taker_wallet"]
    f["fee_unit"] = fee_unit
    return f


def _ci(values, clusters, b: int, seed: int, level: float = 0.95) -> Dict[str, float]:
    """Same as ``figures_p1._ci``: finite values only, cluster pairs bootstrap over taker wallets."""
    values = np.asarray(values, dtype=float)
    ok = np.isfinite(values)
    if ok.sum() == 0:
        return {"mean": np.nan, "lo": np.nan, "hi": np.nan, "n": 0}
    return inf.cluster_mean_ci(values[ok], np.asarray(clusters)[ok], b=b, seed=seed, level=level)


def decomposition(frame: pd.DataFrame, b: int = B_FIGURE, seed: int = P1_SEED, level: float = 0.95) -> pd.DataFrame:
    """The T2 identity per contract, each component with its cluster bootstrap interval, plus fill-level totals."""
    rows = []
    for item, col, sign in (("half spread", "hs", 1.0), ("adverse selection", "as_usd", 1.0),
                            ("markout", "y_usd", 1.0), ("maker fee", "fee", -1.0), ("maker rebate", "rebate", 1.0),
                            ("hedge cost", "hedge", -1.0), ("net edge", "net_edge", 1.0)):
        ci = _ci(sign * frame[col].to_numpy(float), frame["cluster"].to_numpy(), b=b, seed=seed, level=level)
        rows.append({"item": item, "value": ci["mean"], "lo": ci["lo"], "hi": ci["hi"], "n": int(ci["n"]),
                     "b": b, "level": level})
    ne = frame["net_edge"].to_numpy(float)
    edge = frame["fill_edge"].to_numpy(float)
    amount = frame["amount"].to_numpy(float)
    ok = np.isfinite(edge)
    extra = [("net edge, median", float(np.nanmedian(ne))),
             ("net edge, contract weighted", float(edge[ok].sum() / amount[ok].sum())),
             ("net edge, sum over fills (USDC)", float(edge[ok].sum())),
             ("maker fee, sum over fills (USDC)", -float(np.nansum(frame["fee_maker"].to_numpy(float)))),
             ("maker rebate, sum over fills (USDC)", float(np.nansum(frame["rebate_maker"].to_numpy(float)))),
             ("net edge, share of fills negative", float(np.mean(ne[np.isfinite(ne)] < 0)))]
    for item, value in extra:
        rows.append({"item": item, "value": value, "lo": np.nan, "hi": np.nan, "n": int(ok.sum()), "b": 0,
                     "level": np.nan})
    return pd.DataFrame(rows)


def class_table(frame: pd.DataFrame, b: int = B_FIGURE, seed: int = P1_SEED, level: float = 0.95) -> pd.DataFrame:
    """Per counterparty class: the (unchanged) markout and the components that move with the fee unit."""
    out = []
    for name, g in frame.groupby("taker_class", sort=True):
        ci = _ci(g["net_edge"].to_numpy(float), g["cluster"].to_numpy(), b=b, seed=seed, level=level)
        out.append({"class": name, "fills": int(len(g)), "clusters": int(g["cluster"].nunique()),
                    "mean_markout": float(np.nanmean(g["y_usd"])), "mean_hs": float(np.nanmean(g["hs"])),
                    "mean_as": float(np.nanmean(g["as_usd"])), "mean_fee": float(np.nanmean(g["fee"])),
                    "mean_rebate": float(np.nanmean(g["rebate"])), "mean_hedge": float(np.nanmean(g["hedge"])),
                    "mean_ne": float(np.nanmean(g["net_edge"])), "ne_lo": ci["lo"], "ne_hi": ci["hi"],
                    "fill_edge_sum": float(np.nansum(g["fill_edge"])), "b": b, "level": level})
    return pd.DataFrame(out)


def class_concentration(frame: pd.DataFrame) -> pd.DataFrame:
    """Taker wallets (bootstrap clusters) behind each class and the share of its fills the largest carry.

    A percentile cluster bootstrap over G = 8 wallets, one of which carries a third of the fills, gives an
    interval that is too narrow (audit A66); the table makes G visible next to every class interval.
    """
    out = []
    for name, g in frame.groupby("taker_class", sort=True):
        shares = g["cluster"].value_counts(normalize=True).to_numpy(float)
        out.append({"class": name, "fills": int(len(g)), "clusters": int(len(shares)),
                    "top1_share": float(shares[:1].sum()), "top2_share": float(shares[:2].sum())})
    return pd.DataFrame(out)


def rfq_booking(frame: pd.DataFrame) -> dict:
    """How the maker fee of an RFQ package is booked across its legs (audit A67).

    A package is one ``rfq_id`` filled by one maker wallet.  Returns counts of packages by the number of legs
    that carry a fee and the mean fee per contract over the RFQ fills, leg by leg and spread over the package.
    """
    rfq = _is_rfq(frame)
    sub = frame.loc[rfq, PACKAGE_KEY + ["fee_maker", "rebate_maker", "amount"]]
    g = sub.groupby(PACKAGE_KEY, sort=False, dropna=False)
    legs = g.size()
    fee_legs = (sub["fee_maker"] > 0).groupby([sub[k] for k in PACKAGE_KEY], sort=False, dropna=False).sum()
    rebate_legs = (sub["rebate_maker"] > 0).groupby([sub[k] for k in PACKAGE_KEY], sort=False, dropna=False).sum()
    fee_legs, rebate_legs = fee_legs.reindex(legs.index), rebate_legs.reindex(legs.index)
    multi = legs > 1
    amount = sub["amount"].to_numpy(float)
    leg = sub["fee_maker"].to_numpy(float) / np.where(amount > 0, amount, np.nan)
    package = package_per_contract(frame)["fee"][rfq]
    return {"fills": int(len(frame)), "rfq_fills": int(rfq.sum()), "orderbook_fills": int((~rfq).sum()),
            "packages": int(len(legs)), "multi_leg_packages": int(multi.sum()),
            "multi_leg_with_fee": int((multi & (fee_legs > 0)).sum()),
            "multi_leg_fee_on_one_leg": int((multi & (fee_legs == 1)).sum()),
            "multi_leg_fee_on_every_leg": int((multi & (fee_legs == legs)).sum()),
            "multi_leg_with_rebate": int((multi & (rebate_legs > 0)).sum()),
            "rfq_fee_per_contract_leg": float(np.nanmean(leg)) if len(leg) else float("nan"),
            "rfq_fee_per_contract_package": float(np.nanmean(package)) if len(package) else float("nan"),
            "note": "package = rfq_id x maker wallet; fee per contract as the mean over RFQ fills"}


def h4_verdict(cells: pd.DataFrame) -> dict:
    """Paper 1 H4 verdict from a cell table (columns as ``inference_p1.cell_table``)."""
    share = float(cells["positive"].mean()) if len(cells) else float("nan")
    atm = cells[cells["currency"].isin(ATM["currencies"]) & (cells["delta_bucket"] == ATM["delta_bucket"])
                & (cells["tenor_bucket"] == ATM["tenor_bucket"])]
    majority = bool(share >= 0.5)
    atm_positive = bool(atm["positive"].astype(bool).any())
    return {"stat": share, "lo": None, "hi": None, "rejected": bool(majority or atm_positive), "rule": H4_RULE,
            "n": int(len(cells)), "positive_cells": int(cells["positive"].astype(bool).sum()),
            "negative_cells": int(cells["negative"].astype(bool).sum()) if "negative" in cells else None,
            "branch_majority": majority, "branch_atm": atm_positive,
            "atm": [{"currency": r["currency"], "stat": float(r["mean"]), "lo": float(r["lo"]), "hi": float(r["hi"]),
                     "positive": bool(r["positive"]), "n": int(r["fills"])} for _, r in atm.iterrows()],
            "note": "stat = share of occupied cells with a positive 90 % interval; lo/hi undefined for the share"}


def bp_map(frame: pd.DataFrame, denominator: str = "notional", min_fills: int = 200) -> pd.DataFrame:
    """Median net edge in bp per cell as in figure F5.

    ``denominator="notional"`` is paper 1 (per-contract net edge over the notional of the whole fill,
    amount x index); ``"index"`` is net edge x amount over amount x index, i.e. the edge of the fill in bp of
    its notional.
    """
    if denominator == "notional":
        denom = frame["notional"]
    elif denominator == "index":
        denom = frame["index_price"]
    else:
        raise ValueError("denominator must be 'notional' or 'index'")
    edge_bp = frame.assign(bp=1e4 * frame["net_edge"] / denom.replace(0, np.nan))
    rows = []
    for ccy in [c for c in CURRENCIES if (edge_bp["currency"] == c).any()]:
        values, counts = figdata.cell_matrix(edge_bp[edge_bp["currency"] == ccy], "bp", stat="median",
                                             min_fills=min_fills)
        for tenor in counts.index:
            for delta in counts.columns:
                rows.append({"currency": ccy, "tenor_bucket": tenor, "delta_bucket": delta,
                             "median_bp": float(values.loc[tenor, delta]), "fills": int(counts.loc[tenor, delta])})
    return pd.DataFrame(rows)


def bp_summary(maps: pd.DataFrame) -> pd.DataFrame:
    """Median over the occupied cells of each bp map, per variant (fee unit | denominator) and currency."""
    out = []
    maps = maps.assign(variant=maps["fee_unit"] + "|" + maps["denominator"])
    for (variant, ccy), g in maps.groupby(["variant", "currency"], sort=True):
        fin = g["median_bp"].dropna()
        out.append({"variant": variant, "currency": ccy, "median_over_cells": float(fin.median()) if len(fin)
                    else float("nan"), "cells": int(len(fin))})
    return pd.DataFrame(out)


def premium_share_quartiles(frame: pd.DataFrame, per: str = "fill", col: str = "y_usd") -> dict:
    """Quartiles of a per-contract quantity as a share of the premium (figure F1 panel c).

    ``per="fill"`` is paper 1 (premium = price x amount), ``"contract"`` divides by the price only.
    """
    premium = frame["price"] * (frame["amount"] if per == "fill" else 1.0)
    share = (100.0 * frame[col] / premium.replace(0, np.nan)).to_numpy(float)
    share = share[np.isfinite(share)]
    q = np.percentile(share, [25, 50, 75])
    return {"q25": float(q[0]), "q50": float(q[1]), "q75": float(q[2]), "n": int(len(share))}


def matches(value, reference, digits: Optional[int] = None, tol: float = 1e-6,
            abs_tol: Optional[float] = None) -> bool:
    """Equal to the paper 1 reference: within ``abs_tol`` (numbers written as words), rounded to ``digits``
    (printed numbers), else within a relative tolerance (numbers read from results files)."""
    try:
        a, r = float(value), float(reference)
    except (TypeError, ValueError):
        return False
    if not (np.isfinite(a) and np.isfinite(r)):
        return False
    if abs_tol is not None:
        return abs(a - r) <= abs_tol
    if digits is not None:
        return abs(round(a, digits) - round(r, digits)) < 0.5 * 10 ** (-digits - 3)
    return abs(a - r) <= tol * max(1.0, abs(r))


# ------------------------------------------------------------------------------------------------ runner

def load_inputs() -> Dict[str, pd.DataFrame]:
    markouts = pd.read_parquet(MARKOUTS, columns=COLUMNS)
    funding = pd.read_parquet(FUNDING)
    return {"markouts": markouts, "funding": funding}


def _write(path: Path, result) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    if isinstance(result, pd.DataFrame):
        result.to_csv(tmp, index=False)
    else:
        tmp.write_text(json.dumps(result, indent=1, default=str))
    tmp.replace(path)


def run_steps(max_seconds: float, b_cells: int, b_figure: int, parts: Path = None) -> bool:
    """Compute every missing part file; return True when all parts exist."""
    t0 = time.monotonic()
    parts = PARTS if parts is None else Path(parts)
    parts.mkdir(parents=True, exist_ok=True)
    cache: Dict[str, object] = {}
    frames: Dict[tuple, pd.DataFrame] = {}

    def inputs() -> Dict[str, pd.DataFrame]:
        if "inputs" not in cache:                     # loaded only when a step has to run
            cache["inputs"] = load_inputs()
        return cache["inputs"]

    def frame(unit: str, bp: float = 1.0) -> pd.DataFrame:
        key = (unit, bp)
        if key not in frames:
            frames[key] = net_edge_frame(inputs()["markouts"], inputs()["funding"], fee_unit=unit, half_spread_bp=bp)
        return frames[key]

    def cells(unit: str, bp: float, ccy: str) -> pd.DataFrame:
        f = frame(unit, bp)
        return inf.cell_table(f[f["currency"] == ccy], "net_edge", b=b_cells, seed=P1_SEED)

    steps: List[tuple] = []
    # the finding as committed on 25.09.2026
    steps.append(("reproduce_frame.json", lambda: _reproduce_frame(inputs(), frame("p1"))))
    for unit in FEE_UNITS:
        steps.append(("decomposition_{}.csv".format(unit), lambda u=unit: decomposition(frame(u), b=b_figure)))
        steps.append(("classes_{}.csv".format(unit), lambda u=unit: class_table(frame(u), b=b_figure)))
    for bp in HALF_SPREADS:
        for unit in FEE_UNITS:
            for ccy in CURRENCIES:
                steps.append(("cells_{}_{:.0f}bp_{}.csv".format(unit, bp, ccy),
                              lambda u=unit, h=bp, c=ccy: cells(u, h, c)))

    def bp_maps() -> pd.DataFrame:
        out = []
        for unit in FEE_UNITS:
            for denom in ("notional", "index"):
                out.append(bp_map(frame(unit), denominator=denom).assign(fee_unit=unit, denominator=denom))
        return pd.concat(out, ignore_index=True)
    steps.append(("bp_maps.csv", bp_maps))

    def premium() -> pd.DataFrame:
        rows = []
        for per in ("fill", "contract"):
            rows.append(dict(premium_share_quartiles(frame("p1"), per=per, col="y_usd"), quantity="markout", per=per))
            for unit in FEE_UNITS:
                rows.append(dict(premium_share_quartiles(frame(unit), per=per, col="net_edge"),
                                 quantity="net_edge_{}".format(unit), per=per))
        return pd.DataFrame(rows)
    steps.append(("premium_share.csv", premium))

    # audit of paper 2 (A66 to A68)
    steps.append(("class_clusters.csv", lambda: class_concentration(frame("p1"))))
    for unit in FEE_UNITS:
        steps.append(("decomposition_{}_b{}.csv".format(unit, b_cells),
                      lambda u=unit: decomposition(frame(u), b=b_cells)))
        steps.append(("classes_{}_b{}.csv".format(unit, b_cells), lambda u=unit: class_table(frame(u), b=b_cells)))
    steps.append(("rfq_booking.json", lambda: rfq_booking(inputs()["markouts"])))
    steps.append(("decomposition_{}.csv".format(PACKAGE_UNIT), lambda: decomposition(frame(PACKAGE_UNIT), b=b_figure)))
    steps.append(("classes_{}.csv".format(PACKAGE_UNIT), lambda: class_table(frame(PACKAGE_UNIT), b=b_figure)))
    for ccy in CURRENCIES:
        steps.append(("cells_{}_1bp_{}.csv".format(PACKAGE_UNIT, ccy), lambda c=ccy: cells(PACKAGE_UNIT, 1.0, c)))

    for name, fn in steps:
        path = parts / name
        if path.exists():
            continue
        if time.monotonic() - t0 > max_seconds:
            print("budget spent before {}; call again".format(name), flush=True)
            return False
        s0 = time.monotonic()
        _write(path, fn())
        print("{} in {:.1f} s".format(name, time.monotonic() - s0), flush=True)
    return True


def _reproduce_frame(inputs: Dict[str, pd.DataFrame], ours: pd.DataFrame) -> dict:
    """Paper 1's own ``analysis_frame`` on the same rows must give the same net edge, bit for bit."""
    theirs = inf.analysis_frame(inputs["markouts"], inputs["funding"], horizon=HORIZON, half_spread_bp=1.0)
    out = {"fills": int(len(theirs))}
    for col in ("hs", "y_usd", "as_usd", "hedge", "net_edge"):
        a, b = ours[col].to_numpy(float), theirs[col].to_numpy(float)
        same = (a == b) | (np.isnan(a) & np.isnan(b))
        out[col] = {"identical": bool(same.all()), "max_abs_diff": float(np.nanmax(np.abs(a - b)))}
    return out


# ---------------------------------------------------------------------------------------------- assembly

def _p1_manuscript_references() -> Dict[str, float]:
    """Headline decomposition as printed in paper/main.tex and docs/paper2/UEBERGABE.md (two decimals)."""
    return {"half spread": 15.70, "adverse selection": -2.65, "maker fee": -1.56, "maker rebate": 0.59,
            "hedge cost": -3.15, "net edge": 8.93, "markout": 13.05}


def _p1_figure_net_edge() -> float:
    if not Path(ABBILDUNGEN).exists():
        return float("nan")
    text = Path(ABBILDUNGEN).read_text()
    m = re.search(r"\| T2 \| the five components add up to the net edge \| ([0-9.\-]+) \|", text)
    return float(m.group(1)) if m else float("nan")


def _cells(parts: Path, unit: str, bp: float) -> pd.DataFrame:
    return pd.concat([pd.read_csv(parts / "cells_{}_{:.0f}bp_{}.csv".format(unit, bp, c)) for c in CURRENCIES],
                     ignore_index=True)


def assemble(parts: Path = None, out_dir: Path = None, b_cells: int = B_CELLS) -> dict:
    """Combine the parts into results/p1_befund/gebuehreneinheit.{csv,json} and check paper 1 is reproduced."""
    parts = PARTS if parts is None else Path(parts)
    out_dir = OUT_DIR if out_dir is None else Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: List[dict] = []
    checks: List[dict] = []

    def add(section, item, variant, value, lo=np.nan, hi=np.nan, level=np.nan, n=np.nan, b=0, seed=P1_SEED,
            ref=np.nan, source="", digits=None, abs_tol=None):
        ok = matches(value, ref, digits=digits, abs_tol=abs_tol) if source else None
        rows.append({"section": section, "item": item, "variant": variant, "value": value, "lo": lo, "hi": hi,
                     "level": level, "n": n, "b": b, "seed": seed if b else np.nan, "p1_reference": ref,
                     "p1_source": source, "matches_p1": ok})
        if source:
            checks.append({"section": section, "item": item, "value": value, "reference": ref, "source": source,
                           "matches": bool(ok)})

    repro = json.loads((parts / "reproduce_frame.json").read_text())
    for col in ("hs", "y_usd", "as_usd", "hedge", "net_edge"):
        checks.append({"section": "analysis_frame", "item": col, "value": repro[col]["max_abs_diff"], "reference": 0.0,
                       "source": "inference_p1.analysis_frame on the same rows", "matches": repro[col]["identical"]})

    # 1. decomposition per contract (T2, abstract)
    manuscript = _p1_manuscript_references()
    figure_ne = _p1_figure_net_edge()
    horizon = pd.read_csv(P1_RESULTS / "horizon_means.csv").set_index("horizon")
    for unit in FEE_UNITS:
        d = pd.read_csv(parts / "decomposition_{}.csv".format(unit))
        for _, r in d.iterrows():
            ref, src, digits = np.nan, "", None
            if unit == "p1" and r["item"] in manuscript:
                ref, src, digits = manuscript[r["item"]], "paper/main.tex, UEBERGABE.md (2 decimals)", 2
            add("decomposition", r["item"], unit, r["value"], r["lo"], r["hi"], r["level"], r["n"], int(r["b"]),
                ref=ref, source=src, digits=digits)
        if unit == "p1":
            d = d.set_index("item")
            add("decomposition_check", "net edge (exact)", unit, d.loc["net edge", "value"], ref=figure_ne,
                source="docs/paper1/ABBILDUNGEN.md, T2 check")
            add("decomposition_check", "markout (exact)", unit, d.loc["markout", "value"],
                ref=float(horizon.loc[HORIZON, "mean"]), source="results/p1/horizon_means.csv")

    # 2. counterparty classes
    p1_classes = pd.read_csv(P1_RESULTS / "class_means.csv").set_index("class")
    ref_cols = {"mean_markout": "mean", "mean_hs": "mean_hs", "mean_as": "mean_as", "mean_fee": "mean_fee",
                "mean_rebate": "mean_rebate", "mean_hedge": "mean_hedge", "mean_ne": "mean_ne"}
    for unit in FEE_UNITS:
        c = pd.read_csv(parts / "classes_{}.csv".format(unit))
        for _, r in c.iterrows():
            for col, p1col in ref_cols.items():
                ref, src = np.nan, ""
                if unit == "p1" and r["class"] in p1_classes.index:
                    ref, src = float(p1_classes.loc[r["class"], p1col]), "results/p1/class_means.csv"
                lo = r["ne_lo"] if col == "mean_ne" else np.nan
                hi = r["ne_hi"] if col == "mean_ne" else np.nan
                add("classes", "{} {}".format(r["class"], col), unit, r[col], lo, hi,
                    r["level"] if col == "mean_ne" else np.nan, r["fills"], int(r["b"]) if col == "mean_ne" else 0,
                    ref=ref, source=src)
            add("classes", "{} fill_edge_sum".format(r["class"]), unit, r["fill_edge_sum"], n=r["fills"])

    # 3. H4 cells and verdicts
    p1_cells = pd.read_csv(P1_RESULTS / "h4_cells.csv")
    p1_sens = pd.read_csv(P1_RESULTS / "h4_sensitivity.csv").set_index("half_spread_bp")
    verdicts = {}
    key = ["currency", "delta_bucket", "tenor_bucket"]
    for bp in HALF_SPREADS:
        for unit in FEE_UNITS:
            cells = _cells(parts, unit, bp)
            v = h4_verdict(cells)
            verdicts["{}_{:.0f}bp".format(unit, bp)] = v
            ref = float(p1_sens.loc[bp, "share_positive"]) if unit == "p1" and bp in p1_sens.index else np.nan
            add("h4", "share of cells positive, perp half spread {:.0f} bp".format(bp), unit, v["stat"], n=v["n"],
                b=B_CELLS, level=0.90, ref=ref, source="results/p1/h4_sensitivity.csv" if unit == "p1" else "")
            add("h4", "cells positive / negative, {:.0f} bp".format(bp), unit, v["positive_cells"],
                n=v["n"], hi=v["negative_cells"])
            add("h4", "rejected, {:.0f} bp".format(bp), unit, float(v["rejected"]), n=v["n"])
            if bp == 1.0:
                for a in v["atm"]:
                    ref, src = np.nan, ""
                    if unit == "p1":
                        m = p1_cells[(p1_cells["currency"] == a["currency"]) & (p1_cells["delta_bucket"] == "40-60")
                                     & (p1_cells["tenor_bucket"] == "<=2d")]
                        ref, src = float(m["mean"].iloc[0]), "results/p1/h4_cells.csv"
                    add("h4", "{} 40-60 <=2d mean net edge".format(a["currency"]), unit, a["stat"], a["lo"], a["hi"],
                        0.90, a["n"], B_CELLS, ref=ref, source=src)
                if unit == "p1":                                  # every cell, every interval, every flag
                    merged = cells.merge(p1_cells, on=key, suffixes=("", "_p1"), how="outer", indicator=True)
                    same_set = bool((merged["_merge"] == "both").all())
                    both = merged[merged["_merge"] == "both"]
                    diffs = {c: float(np.nanmax(np.abs(both[c] - both[c + "_p1"]))) for c in ("mean", "lo", "hi", "p")}
                    flags = bool((both["positive"].astype(bool) == both["positive_p1"].astype(bool)).all()
                                 and (both["negative"].astype(bool) == both["negative_p1"].astype(bool)).all())
                    checks.append({"section": "h4_cells", "item": "97 cells: mean, lo, hi, p, flags",
                                   "value": diffs, "reference": 0.0, "source": "results/p1/h4_cells.csv",
                                   "matches": bool(same_set and flags and max(diffs.values()) < 1e-9)})
                if unit == "per_contract":                        # the corrected cell table (p1 = results/p1)
                    cells.assign(fee_unit=unit).to_csv(out_dir / "h4_cells_per_contract.csv", index=False)

    # 4. F5 bp map
    maps = pd.read_csv(parts / "bp_maps.csv")
    for _, r in maps.iterrows():
        variant = "{}|{}".format(r["fee_unit"], r["denominator"])
        add("f5_bp_map", "{} {} {}".format(r["currency"], r["delta_bucket"], r["tenor_bucket"]), variant,
            r["median_bp"], n=r["fills"])
    text_refs = [("BTC", "40-60", "<=2d", 9.0), ("BTC", "40-60", "30-90d", 29.0)]
    for ccy, delta, tenor, ref in text_refs:
        m = maps[(maps["fee_unit"] == "p1") & (maps["denominator"] == "notional") & (maps["currency"] == ccy)
                 & (maps["delta_bucket"] == delta) & (maps["tenor_bucket"] == tenor)]
        add("f5_bp_check", "{} {} {} (text: about {:.0f} bp)".format(ccy, delta, tenor, ref), "p1|notional",
            float(m["median_bp"].iloc[0]) if len(m) else np.nan, ref=ref, source="paper/main.tex sec. maker",
            abs_tol=1.0)
    for (unit, denom), g in maps.groupby(["fee_unit", "denominator"]):
        variant = "{}|{}".format(unit, denom)
        for ccy, h in g.groupby("currency"):
            fin = h["median_bp"].dropna()
            add("f5_bp_range", "{} min".format(ccy), variant, float(fin.min()), n=int(len(fin)))
            add("f5_bp_range", "{} max".format(ccy), variant, float(fin.max()), n=int(len(fin)))

    # 5. F1 panel c (related unit mix, not the fee)
    prem = pd.read_csv(parts / "premium_share.csv")
    for _, r in prem.iterrows():
        for q in ("q25", "q50", "q75"):
            ref, src = np.nan, ""
            if r["quantity"] == "markout" and r["per"] == "fill":
                ref = {"q25": -1.6, "q50": 1.1, "q75": 21.1}[q]
                src = "paper/main.tex sec. results (1 decimal)"
            add("f1_premium_share", "{} {}".format(r["quantity"], q), "premium_per_{}".format(r["per"]), r[q], n=r["n"],
                ref=ref, source=src, digits=1 if src else None)

    # ---- audit of paper 2 (docs/paper2/AUDIT.md), appended after the committed sections
    # 6. A65: median over the cells of each F5 variant, the numbers the finding quotes per underlying
    for _, r in bp_summary(maps).iterrows():
        add("f5_bp_summary", "{} median over cells".format(r["currency"]), r["variant"], r["median_over_cells"],
            n=r["cells"])

    # 7. A66: taker wallets behind each class interval
    for _, r in pd.read_csv(parts / "class_clusters.csv").iterrows():
        add("class_clusters", "{} clusters".format(r["class"]), "all", float(r["clusters"]), n=r["fills"])
        add("class_clusters", "{} top1 share of fills".format(r["class"]), "all", r["top1_share"], n=r["fills"])
        add("class_clusters", "{} top2 share of fills".format(r["class"]), "all", r["top2_share"], n=r["fills"])

    # 8. A68: decomposition and class intervals with the draws paper 1 states for its intervals
    for unit in FEE_UNITS:
        d = pd.read_csv(parts / "decomposition_{}_b{}.csv".format(unit, b_cells))
        for _, r in d[d["b"] > 0].iterrows():
            add("decomposition_b9999", r["item"], unit, r["value"], r["lo"], r["hi"], r["level"], r["n"], int(r["b"]))
    for unit in FEE_UNITS:
        c = pd.read_csv(parts / "classes_{}_b{}.csv".format(unit, b_cells))
        for _, r in c.iterrows():
            add("classes_b9999", "{} mean_ne".format(r["class"]), unit, r["mean_ne"], r["ne_lo"], r["ne_hi"],
                r["level"], r["fills"], int(r["b"]))

    # 9. A67: how RFQ packages book the maker fee, and the net edge with the fee spread over the package
    booking = json.loads((parts / "rfq_booking.json").read_text())
    for k, v in booking.items():
        if k != "note":
            add("rfq_booking", k, "all", float(v))
    d = pd.read_csv(parts / "decomposition_{}.csv".format(PACKAGE_UNIT))
    for _, r in d.iterrows():
        add("rfq_package", "decomposition {}".format(r["item"]), PACKAGE_UNIT, r["value"], r["lo"], r["hi"],
            r["level"], r["n"], int(r["b"]))
    c = pd.read_csv(parts / "classes_{}.csv".format(PACKAGE_UNIT))
    for _, r in c.iterrows():
        for col in ("mean_fee", "mean_rebate", "mean_ne"):
            ne = col == "mean_ne"
            add("rfq_package", "class {} {}".format(r["class"], col), PACKAGE_UNIT, r[col],
                r["ne_lo"] if ne else np.nan, r["ne_hi"] if ne else np.nan, r["level"] if ne else np.nan,
                r["fills"], int(r["b"]) if ne else 0)
    package_cells = _cells(parts, PACKAGE_UNIT, 1.0)
    v_package = h4_verdict(package_cells)
    add("rfq_package", "h4 share of cells positive, perp half spread 1 bp", PACKAGE_UNIT, v_package["stat"],
        n=v_package["n"], b=B_CELLS, level=0.90)
    add("rfq_package", "h4 cells positive / negative, 1 bp", PACKAGE_UNIT, v_package["positive_cells"],
        n=v_package["n"], hi=v_package["negative_cells"])
    add("rfq_package", "h4 rejected, 1 bp", PACKAGE_UNIT, float(v_package["rejected"]), n=v_package["n"])
    for a in v_package["atm"]:
        add("rfq_package", "h4 {} 40-60 <=2d mean net edge".format(a["currency"]), PACKAGE_UNIT, a["stat"], a["lo"],
            a["hi"], 0.90, a["n"], B_CELLS)

    table = pd.DataFrame(rows)
    table.to_csv(out_dir / "gebuehreneinheit.csv", index=False)
    report = {"meta": {"horizon": HORIZON, "seed": P1_SEED, "b_cells": B_CELLS, "b_other": B_FIGURE,
                       "fills": int(repro["fills"]), "script": SCRIPT,
                       "note": "seed and B of paper 1 so that its numbers are reproduced exactly; "
                               "decomposition and class intervals at B = 999 (as the paper 1 figures), "
                               "exploratory; sections decomposition_b9999 and classes_b9999 repeat them at "
                               "B = 9 999 for quotation in the text (audit A68)"},
              "h4": verdicts, "reproduction": checks,
              "reproduced": bool(all(c["matches"] for c in checks)),
              "rfq_booking": booking,
              "h4_rfq_package": {"{}_1bp".format(PACKAGE_UNIT): v_package}}
    (out_dir / "gebuehreneinheit.json").write_text(json.dumps(report, indent=1, default=str))
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--max-seconds", type=float, default=480.0)
    ap.add_argument("--b-cells", type=int, default=B_CELLS)
    ap.add_argument("--b-figure", type=int, default=B_FIGURE)
    ap.add_argument("--parts", type=Path, default=None, help="cache of the steps (default {})".format(
        PARTS.relative_to(REPO)))
    ap.add_argument("--out-dir", type=Path, default=None, help="default {}".format(OUT_DIR.relative_to(REPO)))
    ap.add_argument("--assemble-only", action="store_true")
    a = ap.parse_args(argv)
    if not a.assemble_only and not run_steps(a.max_seconds, a.b_cells, a.b_figure, parts=a.parts):
        return 3
    report = assemble(parts=a.parts, out_dir=a.out_dir, b_cells=a.b_cells)
    bad = [c for c in report["reproduction"] if not c["matches"]]
    print(json.dumps({"reproduced": report["reproduced"], "mismatches": bad,
                      "h4": {k: {kk: v[kk] for kk in ("stat", "rejected", "branch_majority", "branch_atm")}
                             for k, v in report["h4"].items()}}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
