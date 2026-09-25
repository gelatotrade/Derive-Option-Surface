"""Offline tests for scripts/p1_befund_gebuehreneinheit.py (synthetic data, known answers).

The script recomputes the paper 1 numbers with the maker fee and rebate taken per contract; see
docs/paper1/BEFUND_2026-09-25_GEBUEHRENEINHEIT.md.  Nothing here reads data/p1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p1_befund_gebuehreneinheit as ge  # noqa: E402
from derive_surface import inference_p1 as inf  # noqa: E402


def fills(n=4, amount=(1.0, 4.0, 0.5, 2.0), fee=(0.4, 8.0, 1.0, 0.0), rebate=(0.1, 2.0, 0.0, 1.0),
          delta=(0.0, 0.0, 0.5, 0.0), currency="BTC", rfq_id=None, maker=None):
    rows = []
    for i in range(n):
        rows.append({
            "trade_id": "t{}".format(i), "ts": 1_700_000_000_000 + i * 1000, "currency": currency,
            "instrument_name": "{}-1-2-C".format(currency), "taker_wallet": "0xt{}".format(i % 2),
            "taker_class": "other" if i % 2 else "rfq", "delta_bucket": "40-60", "tenor_bucket": "<=2d",
            "price": 100.0, "mark_b_t": 105.0, "maker_side": 1, "mo_usd_30m": 10.0, "mo_dn_30m": 9.0,
            "mo_vol_30m": 5.0, "delta_t": delta[i], "fwd_t": 50_000.0, "amount": amount[i],
            "index_price": 50_000.0, "fee_maker": fee[i], "rebate_maker": rebate[i],
            "rfq_id": None if rfq_id is None else rfq_id[i],
            "maker_wallet": "0xm" if maker is None else maker[i],
        })
    f = pd.DataFrame(rows)
    f["notional"] = f["amount"] * f["index_price"]
    return f


FUNDING = pd.DataFrame({"instrument_name": ["BTC-PERP", "ETH-PERP"], "timestamp": [1, 1],
                        "funding_rate": [1e-5, 2e-5]})


# ------------------------------------------------------------------------ ported from data/p2/p1befund

def test_p1_mode_reproduces_paper1_analysis_frame_exactly():
    f = fills()
    ours = ge.net_edge_frame(f, FUNDING, fee_unit="p1")
    theirs = inf.analysis_frame(f, FUNDING, horizon="30m", half_spread_bp=1.0)
    for col in ("hs", "y_usd", "as_usd", "hedge", "net_edge"):
        assert np.array_equal(ours[col].to_numpy(), theirs[col].to_numpy()), col


def test_per_contract_mode_divides_fee_and_rebate_by_amount():
    f = fills()
    old = ge.net_edge_frame(f, FUNDING, fee_unit="p1")
    new = ge.net_edge_frame(f, FUNDING, fee_unit="per_contract")
    # fill 1: markout 10, amount 4, fee 8, rebate 2, no delta -> no hedge
    assert old.loc[1, "hedge"] == 0.0
    assert old.loc[1, "net_edge"] == pytest.approx(10.0 - 8.0 + 2.0)
    assert new.loc[1, "net_edge"] == pytest.approx(10.0 - (8.0 - 2.0) / 4.0)
    assert new.loc[1, "fill_edge"] == pytest.approx(4.0 * 8.5)          # edge of the fill in USDC
    assert new.loc[1, "fee"] == pytest.approx(2.0) and new.loc[1, "rebate"] == pytest.approx(0.5)
    # fill 0 has one contract: both readings agree
    assert old.loc[0, "net_edge"] == pytest.approx(new.loc[0, "net_edge"])
    # fill 2: half a contract doubles the per-contract fee, the hedge is per contract in both readings
    assert new.loc[2, "hedge"] == pytest.approx(old.loc[2, "hedge"]) and new.loc[2, "hedge"] > 0
    assert new.loc[2, "net_edge"] == pytest.approx(10.0 - 2.0 - new.loc[2, "hedge"])


def test_unknown_fee_unit_is_refused():
    with pytest.raises(ValueError):
        ge.net_edge_frame(fills(), FUNDING, fee_unit="per_lot")


def test_decomposition_adds_up_and_reports_fill_level_totals():
    f = ge.net_edge_frame(fills(), FUNDING, fee_unit="per_contract")
    d = ge.decomposition(f, b=99, seed=1).set_index("item")
    parts = ["half spread", "adverse selection", "maker fee", "maker rebate", "hedge cost"]
    assert d.loc[parts, "value"].sum() == pytest.approx(d.loc["net edge", "value"])
    assert d.loc["half spread", "value"] + d.loc["adverse selection", "value"] == pytest.approx(
        d.loc["markout", "value"])
    assert d.loc["maker fee", "value"] == pytest.approx(-np.mean([0.4, 2.0, 2.0, 0.0]))
    edge = f["net_edge"] * f["amount"]
    assert d.loc["net edge, sum over fills (USDC)", "value"] == pytest.approx(edge.sum())
    assert d.loc["net edge, contract weighted", "value"] == pytest.approx(edge.sum() / f["amount"].sum())


def test_class_table_leaves_the_markout_alone_and_moves_the_net_edge():
    old = ge.class_table(ge.net_edge_frame(fills(), FUNDING, fee_unit="p1"), b=99, seed=1).set_index("class")
    new = ge.class_table(ge.net_edge_frame(fills(), FUNDING, fee_unit="per_contract"), b=99, seed=1).set_index("class")
    assert np.allclose(old["mean_markout"], new["mean_markout"])
    # class "other" = fills 1 and 3 (amount 4 and 2): fee 8 -> 2, rebate 2 -> 0.5 and 1 -> 0.5
    assert new.loc["other", "mean_fee"] == pytest.approx((2.0 + 0.0) / 2)
    assert new.loc["other", "mean_rebate"] == pytest.approx((0.5 + 0.5) / 2)
    assert old.loc["other", "mean_ne"] == pytest.approx(10.0 - (8.0 + 0.0) / 2 + (2.0 + 1.0) / 2)


def test_h4_verdict_follows_the_registered_rule():
    base = {"fills": 300, "lo": 0.0, "hi": 1.0, "negative": False}
    cells = pd.DataFrame([
        dict(base, currency="BTC", delta_bucket="40-60", tenor_bucket="<=2d", mean=1.0, positive=False),
        dict(base, currency="ETH", delta_bucket="40-60", tenor_bucket="<=2d", mean=1.0, positive=False),
        dict(base, currency="BTC", delta_bucket="00-10", tenor_bucket="<=2d", mean=1.0, positive=True),
        dict(base, currency="HYPE", delta_bucket="40-60", tenor_bucket="<=2d", mean=1.0, positive=True),
    ])
    v = ge.h4_verdict(cells)
    assert v["stat"] == pytest.approx(0.5) and v["n"] == 4
    assert v["branch_majority"] and not v["branch_atm"] and v["rejected"]
    cells.loc[2, "positive"] = False                                  # 1 of 4, ATM not positive: stands
    v = ge.h4_verdict(cells)
    assert not v["rejected"] and v["stat"] == pytest.approx(0.25)
    cells.loc[0, "positive"] = True                                   # only BTC ATM positive: rejected
    cells.loc[3, "positive"] = False
    v = ge.h4_verdict(cells)
    assert v["rejected"] and v["branch_atm"] and not v["branch_majority"]
    assert set(v) >= {"stat", "lo", "hi", "rejected", "rule", "n"}


def test_bp_map_in_both_denominators_and_thin_cells_dropped():
    rows = []
    for i in range(250):
        rows.append({"currency": "BTC", "delta_bucket": "40-60", "tenor_bucket": "<=2d", "net_edge": 1.0,
                     "amount": 2.0, "index_price": 100.0, "notional": 200.0})
    for i in range(150):                                                   # under 200 fills
        rows.append({"currency": "BTC", "delta_bucket": "00-10", "tenor_bucket": "<=2d", "net_edge": 1.0,
                     "amount": 1.0, "index_price": 100.0, "notional": 100.0})
    f = pd.DataFrame(rows)
    per_fill = ge.bp_map(f, denominator="notional").set_index(["currency", "tenor_bucket", "delta_bucket"])
    per_index = ge.bp_map(f, denominator="index").set_index(["currency", "tenor_bucket", "delta_bucket"])
    assert per_fill.loc[("BTC", "<=2d", "40-60"), "median_bp"] == pytest.approx(50.0)     # Paper 1: NE / (a * index)
    assert per_index.loc[("BTC", "<=2d", "40-60"), "median_bp"] == pytest.approx(100.0)   # NE * a / (a * index)
    assert np.isnan(per_fill.loc[("BTC", "<=2d", "00-10"), "median_bp"])
    assert per_fill.loc[("BTC", "<=2d", "00-10"), "fills"] == 150


def test_premium_share_quartiles_per_fill_and_per_contract():
    f = pd.DataFrame({"y_usd": [1.0, 2.0, 3.0, 4.0], "price": [10.0] * 4, "amount": [0.5, 1.0, 2.0, 4.0]})
    fill = ge.premium_share_quartiles(f, per="fill")
    contract = ge.premium_share_quartiles(f, per="contract")
    assert contract["q50"] == pytest.approx(np.percentile([10.0, 20.0, 30.0, 40.0], 50))
    assert fill["q50"] == pytest.approx(np.percentile([20.0, 20.0, 15.0, 10.0], 50))


def test_compare_flags_mismatch_beyond_tolerance():
    assert ge.matches(8.93245, 8.93245) and ge.matches(15.70, 15.7043, digits=2)
    assert not ge.matches(15.70, 15.72, digits=2)
    assert not ge.matches(np.nan, 1.0)
    # words in the text ("about twenty-nine") are checked with an absolute tolerance
    assert ge.matches(28.46, 29.0, abs_tol=1.0) and not ge.matches(27.5, 29.0, abs_tol=1.0)


# ------------------------------------------------------------------------------ audit additions (A65-A68)

def rfq_fills():
    """q1: two legs, fee booked on one; q2: two legs, fee on both; q3: one leg; o: order book fill."""
    return fills(n=6, amount=(2.0, 1.0, 1.0, 3.0, 4.0, 2.0), fee=(6.0, 0.0, 1.0, 2.0, 4.0, 2.0),
                 rebate=(0.0, 0.0, 0.0, 0.0, 0.0, 1.0), delta=(0.0,) * 6,
                 rfq_id=("q1", "q1", "q2", "q2", "q3", None))


def test_package_mode_spreads_the_rfq_fee_over_the_legs_of_the_package():
    f = rfq_fills()
    leg = ge.net_edge_frame(f, FUNDING, fee_unit="per_contract")
    pkg = ge.net_edge_frame(f, FUNDING, fee_unit="per_contract_package")
    # q1: 6 USDC on the first leg of 2 + 1 contracts -> 2 per contract on both legs instead of 3 and 0
    assert leg.loc[0, "fee"] == pytest.approx(3.0) and leg.loc[1, "fee"] == pytest.approx(0.0)
    assert pkg.loc[0, "fee"] == pytest.approx(2.0) and pkg.loc[1, "fee"] == pytest.approx(2.0)
    # the fee of the package is kept, only its split over the legs moves
    for frame in (leg, pkg):
        assert (frame["fee"] * frame["amount"]).iloc[:2].sum() == pytest.approx(6.0)
    # q2: (1 + 2) / (1 + 3); single-leg package q3 and the order book fill are unchanged
    assert pkg.loc[2, "fee"] == pytest.approx(0.75) and pkg.loc[3, "fee"] == pytest.approx(0.75)
    assert pkg.loc[4, "fee"] == pytest.approx(leg.loc[4, "fee"])
    assert pkg.loc[5, "fee"] == pytest.approx(leg.loc[5, "fee"])
    assert pkg.loc[5, "rebate"] == pytest.approx(0.5)
    assert pkg.loc[0, "net_edge"] == pytest.approx(10.0 - 2.0)


def test_package_mode_keeps_packages_of_different_makers_apart():
    f = rfq_fills()
    f.loc[1, "maker_wallet"] = "0xother"                 # q1 filled by two makers: two packages of one leg
    pkg = ge.net_edge_frame(f, FUNDING, fee_unit="per_contract_package")
    assert pkg.loc[0, "fee"] == pytest.approx(3.0) and pkg.loc[1, "fee"] == pytest.approx(0.0)


def test_rfq_booking_counts_packages_by_the_legs_that_carry_the_fee():
    f = pd.concat([rfq_fills(), fills(n=3, amount=(1.0, 1.0, 1.0), fee=(0.0, 0.0, 0.0), rebate=(0.0,) * 3,
                                      delta=(0.0,) * 3, rfq_id=("q4", "q4", "q4"))], ignore_index=True)
    s = ge.rfq_booking(f)
    assert s["rfq_fills"] == 8 and s["orderbook_fills"] == 1
    assert s["packages"] == 4 and s["multi_leg_packages"] == 3
    assert s["multi_leg_with_fee"] == 2
    assert s["multi_leg_fee_on_one_leg"] == 1 and s["multi_leg_fee_on_every_leg"] == 1
    assert s["multi_leg_with_rebate"] == 0
    # mean fee per contract over the RFQ fills, leg by leg and spread over the package
    assert s["rfq_fee_per_contract_leg"] == pytest.approx(np.mean([3.0, 0.0, 1.0, 2.0 / 3.0, 1.0, 0, 0, 0]))
    assert s["rfq_fee_per_contract_package"] == pytest.approx(np.mean([2.0, 2.0, 0.75, 0.75, 1.0, 0, 0, 0]))


def test_class_concentration_counts_wallets_and_the_share_of_the_largest():
    f = pd.DataFrame({"taker_class": ["vault"] * 10 + ["other"] * 2,
                      "cluster": ["w1"] * 6 + ["w2"] * 3 + ["w3"] + ["a", "b"]})
    c = ge.class_concentration(f).set_index("class")
    assert c.loc["vault", "clusters"] == 3 and c.loc["vault", "fills"] == 10
    assert c.loc["vault", "top1_share"] == pytest.approx(0.6)
    assert c.loc["vault", "top2_share"] == pytest.approx(0.9)
    assert c.loc["other", "top2_share"] == pytest.approx(1.0)


def test_bp_summary_takes_the_median_over_the_occupied_cells():
    maps = pd.DataFrame({"fee_unit": ["p1"] * 4 + ["per_contract"] * 2,
                         "denominator": ["index"] * 4 + ["index"] * 2,
                         "currency": ["BTC", "BTC", "BTC", "HYPE", "BTC", "BTC"],
                         "delta_bucket": ["00-10", "10-25", "25-40", "00-10", "00-10", "10-25"],
                         "tenor_bucket": ["<=2d"] * 6,
                         "median_bp": [1.0, 3.0, np.nan, 5.0, 2.0, 4.0], "fills": [300, 300, 10, 300, 300, 300]})
    s = ge.bp_summary(maps).set_index(["variant", "currency"])
    assert s.loc[("p1|index", "BTC"), "median_over_cells"] == pytest.approx(2.0)
    assert s.loc[("p1|index", "BTC"), "cells"] == 2
    assert s.loc[("p1|index", "HYPE"), "median_over_cells"] == pytest.approx(5.0)
    assert s.loc[("per_contract|index", "BTC"), "median_over_cells"] == pytest.approx(3.0)


# ------------------------------------------------------------------- end to end on a synthetic sample

def synthetic_markouts(seed=7) -> pd.DataFrame:
    """250 fills per currency in the short-dated ATM cell, amounts far from one, some RFQ packages."""
    rng = np.random.default_rng(seed)
    parts = []
    for k, (ccy, index) in enumerate((("BTC", 60_000.0), ("ETH", 3_000.0), ("HYPE", 40.0))):
        n = 250
        amount = rng.choice([0.1, 0.5, 2.0, 25.0], n)
        f = pd.DataFrame({
            "trade_id": ["{}{}".format(ccy, i) for i in range(n)],
            "ts": 1_750_000_000_000 + np.arange(n) * 60_000,
            "instrument_name": "{}-20250701-{}-C".format(ccy, int(index)), "currency": ccy,
            "price": index * 0.02, "amount": amount, "index_price": index, "maker_side": rng.choice([-1, 1], n),
            "mo_dn_30m": rng.normal(0, 1, n), "mo_vol_30m": rng.normal(0, 1, n),
            "delta_t": rng.uniform(0.4, 0.6, n), "fwd_t": index,
            "fee_maker": amount * index * 1e-4 * (rng.random(n) > 0.3),
            "rebate_maker": amount * index * 2e-5 * (rng.random(n) > 0.7),
            "taker_wallet": rng.choice(["0x{}{}".format(k, w) for w in range(30)], n),
            "taker_class": rng.choice(["other", "rfq", "vault"], n),
            "delta_bucket": "40-60", "tenor_bucket": "<=2d",
            "rfq_id": [("{}p{}".format(ccy, i // 2) if i < 40 else None) for i in range(n)],
            "maker_wallet": "0xmaker",
        })
        f["mark_b_t"] = f["price"] + f["maker_side"] * rng.normal(index * 1e-4, index * 1e-4, n)
        f["mo_usd_30m"] = rng.normal(index * 1e-4, index * 5e-4, n)
        f["notional"] = f["amount"] * f["index_price"]
        parts.append(f)
    return pd.concat(parts, ignore_index=True)


def write_p1_results(markouts: pd.DataFrame, funding: pd.DataFrame, out: Path, b: int) -> None:
    """The four paper 1 result files the script compares against, made by paper 1's own functions."""
    out.mkdir(parents=True)
    frame = inf.analysis_frame(markouts, funding)
    inf.cell_table(frame, "net_edge", b=b, seed=ge.P1_SEED).to_csv(out / "h4_cells.csv", index=False)
    sens = [{"half_spread_bp": bp, "share_positive": float(inf.cell_table(
        inf.analysis_frame(markouts, funding, half_spread_bp=bp), "net_edge", b=b, seed=ge.P1_SEED)["positive"].mean())}
        for bp in (0.0, 1.0, 3.0)]
    pd.DataFrame(sens).to_csv(out / "h4_sensitivity.csv", index=False)
    pd.DataFrame([{"horizon": "30m", "mean": float(np.nanmean(frame["y_usd"]))}]).to_csv(
        out / "horizon_means.csv", index=False)
    classes = [{"class": name, "mean": float(np.nanmean(g["y_usd"])), "mean_hs": float(np.nanmean(g["hs"])),
                "mean_as": float(np.nanmean(g["as_usd"])), "mean_fee": float(np.nanmean(g["fee_maker"])),
                "mean_rebate": float(np.nanmean(g["rebate_maker"])), "mean_hedge": float(np.nanmean(g["hedge"])),
                "mean_ne": float(np.nanmean(g["net_edge"]))} for name, g in frame.groupby("taker_class")]
    pd.DataFrame(classes).to_csv(out / "class_means.csv", index=False)


def test_end_to_end_writes_repo_paths_and_appends_the_audit_sections(tmp_path, monkeypatch):
    b = 19
    markouts = synthetic_markouts()
    funding = FUNDING.assign(instrument_name=["BTC-PERP", "HYPE-PERP"])
    markouts.to_parquet(tmp_path / "markouts.parquet")
    funding.to_parquet(tmp_path / "funding.parquet")
    write_p1_results(markouts, funding, tmp_path / "p1", b)
    monkeypatch.setattr(ge, "MARKOUTS", tmp_path / "markouts.parquet")
    monkeypatch.setattr(ge, "FUNDING", tmp_path / "funding.parquet")
    monkeypatch.setattr(ge, "P1_RESULTS", tmp_path / "p1")
    monkeypatch.setattr(ge, "ABBILDUNGEN", tmp_path / "missing.md")
    out, parts = tmp_path / "out", tmp_path / "parts"

    code = ge.main(["--parts", str(parts), "--out-dir", str(out), "--b-cells", str(b), "--b-figure", str(b)])
    assert code == 0
    report = json.loads((out / "gebuehreneinheit.json").read_text())
    table = pd.read_csv(out / "gebuehreneinheit.csv")
    assert (out / "h4_cells_per_contract.csv").exists()

    # A26: the result names the versioned script, not the ignored copy under data/p2
    assert report["meta"]["script"] == "scripts/p1_befund_gebuehreneinheit.py"
    # the checks against paper 1's own functions pass on the same rows
    checks = {(c["section"], c["item"]): c["matches"] for c in report["reproduction"]}
    assert all(checks[("analysis_frame", col)] for col in ("hs", "y_usd", "as_usd", "hedge", "net_edge"))
    assert checks[("h4_cells", "97 cells: mean, lo, hi, p, flags")]
    # the committed sections come first and in their order; the audit sections are appended after them
    order = list(dict.fromkeys(table["section"]))
    old = ["decomposition", "decomposition_check", "classes", "h4", "f5_bp_map", "f5_bp_check", "f5_bp_range",
           "f1_premium_share"]
    assert order[:len(old)] == old
    assert order[len(old):] == ["f5_bp_summary", "class_clusters", "decomposition_b9999", "classes_b9999",
                                "rfq_booking", "rfq_package"]
    # A68: intervals at the registered number of draws, A66: wallets behind each class, A67: package variant
    assert set(table.loc[table["section"] == "decomposition_b9999", "b"]) == {b}
    clusters = table[(table["section"] == "class_clusters") & (table["item"] == "vault clusters")]
    assert clusters["value"].iloc[0] == markouts.loc[markouts["taker_class"] == "vault", "taker_wallet"].nunique()
    assert set(table.loc[table["section"] == "rfq_package", "variant"]) == {"per_contract_package"}
    assert report["rfq_booking"]["multi_leg_packages"] == 60
    assert set(report["h4_rfq_package"]) == {"per_contract_package_1bp"}
    assert set(report["h4"]) == {"{}_{}bp".format(u, h) for u in ("p1", "per_contract") for h in (0, 1, 3)}

    # resumable: a second call finds every part and only assembles
    before = (out / "gebuehreneinheit.csv").read_bytes()
    assert ge.main(["--parts", str(parts), "--out-dir", str(out), "--b-cells", str(b), "--b-figure", str(b),
                    "--max-seconds", "0"]) == 0
    assert (out / "gebuehreneinheit.csv").read_bytes() == before
