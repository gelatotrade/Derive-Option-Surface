from __future__ import annotations

import calendar
import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from derive_surface import books, margin_sm, p2validate as pv
from derive_surface.p2chain import block_at_ts, ts_at_block
from derive_surface.p2feeds import FeedExpiryState, FeedHistory
from derive_surface.p2types import Book, MarketState, OptionLeg

# b1_chain_cases.json holds real maker books (M-labels and their positions on a day), so fixture and generator live
# in data/p2/fixtures_private (not tracked, Nachtrag 1.4, audit A01); without them these tests are skipped.
PRIVATE = Path(__file__).resolve().parents[1] / "data" / "p2" / "fixtures_private"


def _private(name: str) -> dict:
    path = PRIVATE / name
    if not path.exists():
        pytest.skip(f"private chain fixture missing (account-identifying, not in the repository): {path}")
    return json.loads(path.read_text())


def _ts(text: str) -> int:
    return calendar.timegm(dt.datetime.strptime(text, "%Y-%m-%d %H:%M").timetuple())


# ---------------------------------------------------------------- keccak and selectors

def test_keccak256_known_vectors():
    assert pv.keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    assert pv.keccak256(b"abc").hex() == "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45"
    # padding edge cases around the 136-byte rate and a multi-block input
    assert pv.keccak256(b"a" * 135).hex() == "34367dc248bbd832f4e3e69dfaac2f92638bd0bbd18f2912ba4ef454919cf446"
    assert pv.keccak256(b"a" * 136).hex() == "a6c4d403279fe3e0af03729caada8374b5ca54d8065329a3ebcaeb4b60aa386e"
    assert pv.keccak256(bytes(range(256)) * 2).hex() == \
        "f55ba327291604f0e5be6651752398b7be2331aad65f5763ce067df95cc13be1"


def test_keccak256_reproduces_event_topics_of_other_modules():
    sig = "BalanceAdjusted(uint256,address,bytes32,int256,int256,int256,uint256)"
    assert "0x" + pv.keccak256(sig.encode()).hex() == books.T_BALANCE_ADJUSTED


def test_selectors_are_keccak_of_signatures():
    for sig, sel in pv.SELECTOR_SIGNATURES.items():
        assert pv.selector(sig).hex() == sel, sig
    assert pv.SEL["getMargin"] == "623bb445"
    assert pv.SEL["getMarginAndMarkToMarket"] == "6691bc04"
    assert pv.SEL["getUnsettledAndUnrealizedCash"] == "7a4c2c3a"


# ---------------------------------------------------------------- SubAccounts storage layout

def test_storage_slots_match_chain_layout_of_subaccounts():
    # values read with eth_getStorageAt at block 44 800 000 for account 5 (not a maker account): heldAssets.length = 1
    # at the length slot, element 0 = the cash asset (subId 0), balanceAndOrder of that element =
    # 503836387299999999988 (order 0), as getAccountBalances(5) returns
    assert pv.held_assets_slot(5) == 0x6bda57492eba051cb4a12a1e19df47c9755d78165341d4009b1d09b3f3616204
    assert pv.held_assets_element_slot(5, 0) == 0x113b67e4b13ef21afafa7a5b3bf3fe5e00801d5b295d3ef940a049cb9aa539f5
    assert pv.held_assets_element_slot(5, 3) == 0x113b67e4b13ef21afafa7a5b3bf3fe5e00801d5b295d3ef940a049cb9aa539f5 + 3
    cash = "0x57b03e14d409adc7fab6cfc44b5886cad2d5f02b"
    assert pv.balance_slot(5, cash, 0) == 0x63055ccaf2754c65b49585c5dc41401050993885ccd72de4d2fe9f848a41dcf8
    assert pv.unpack_held(int("57b03e14d409adc7fab6cfc44b5886cad2d5f02b", 16)) == (cash, 0)
    assert pv.unpack_balance(0x1b50226ccf4ca1e7f4) == (503836387299999999988, 0)
    assert pv.unpack_balance(((1 << 240) - 7) | (3 << 240)) == (-7, 3)


def test_account_state_diff_packs_assets_balances_and_order():
    acc = pv.SYNTHETIC_ACCOUNT
    opt = pv.OPTION_ASSET["BTC"]
    sid = books.encode_option_subid(1_790_000_000, 76_000.0, True)
    rows = [(opt, sid, -10 ** 18), (pv.PERP_ASSET["BTC"], 0, 3 * 10 ** 17)]
    diff = pv.account_state_diff(acc, rows)
    assert len(diff) == 1 + 2 * len(rows)
    word = lambda slot: int(diff["0x%064x" % slot], 16)  # noqa: E731
    assert word(pv.held_assets_slot(acc)) == 2
    for i, (asset, sub, bal) in enumerate(rows):
        assert pv.unpack_held(word(pv.held_assets_element_slot(acc, i))) == (asset.lower(), sub)
        assert pv.unpack_balance(word(pv.balance_slot(acc, asset, sub))) == (bal, i)
    for key, val in diff.items():
        assert key.startswith("0x") and len(key) == 66 and len(val) == 66


def test_account_state_diff_rejects_duplicates_and_out_of_range_balances():
    opt = pv.OPTION_ASSET["ETH"]
    with pytest.raises(ValueError):
        pv.account_state_diff(pv.SYNTHETIC_ACCOUNT, [(opt, 5, 1), (opt, 5, 2)])
    with pytest.raises(ValueError):
        pv.account_state_diff(pv.SYNTHETIC_ACCOUNT, [(opt, 5, 1 << 239)])
    with pytest.raises(ValueError):
        pv.account_state_diff(pv.SYNTHETIC_ACCOUNT, [(opt, 5, 0)])


def test_state_override_targets_subaccounts_and_merges_accounts():
    opt = pv.OPTION_ASSET["HYPE"]
    ov = pv.state_override({pv.SYNTHETIC_ACCOUNT: [(opt, 7, 10 ** 18)], pv.SYNTHETIC_ACCOUNT + 1: [(opt, 7, -10 ** 18)]})
    assert list(ov) == [pv.SUBACCOUNTS]
    assert len(ov[pv.SUBACCOUNTS]["stateDiff"]) == 6


def test_wei_is_exact_for_decimal_amounts():
    assert pv.wei(-1.0) == -10 ** 18
    assert pv.wei(0.3) == 3 * 10 ** 17
    assert pv.wei(12.5) == 125 * 10 ** 17
    assert pv.wei(1e-18) == 1


def test_book_balances_encode_options_and_perp():
    e = 1_790_000_000
    book = Book(options=[OptionLeg(e, 76_000.0, True, -1.0), OptionLeg(e, 70_000.0, False, 2.5)], perp=-0.3)
    rows = pv.book_balances("BTC", book)
    assert rows == [(pv.OPTION_ASSET["BTC"], books.encode_option_subid(e, 70_000.0, False), 25 * 10 ** 17),
                    (pv.OPTION_ASSET["BTC"], books.encode_option_subid(e, 76_000.0, True), -10 ** 18),
                    (pv.PERP_ASSET["BTC"], 0, -3 * 10 ** 17)]
    # legs of one instrument are netted, a zero leg is not held
    book = Book(options=[OptionLeg(e, 76_000.0, True, -1.0), OptionLeg(e, 76_000.0, True, 1.0)])
    assert pv.book_balances("BTC", book) == []


def test_raw_book_balances_keep_exact_snapshot_integers():
    e = 1_790_000_000
    snap = pd.DataFrame({"kind": ["option", "perp", "cash", "option"], "ccy": ["ETH", "ETH", "USDC", "ETH"],
                         "asset": [pv.OPTION_ASSET["ETH"].upper().replace("0X", "0x"), pv.PERP_ASSET["ETH"], "0xabc", pv.OPTION_ASSET["ETH"]],
                         "sub_id": [str(books.encode_option_subid(e, 3000.0, True)), "0", "0",
                                    str(books.encode_option_subid(e - 86_400, 3000.0, True))],
                         "expiry": [e, None, None, e - 86_400], "strike": [3000.0, None, None, 3000.0],
                         "is_call": [True, None, None, True], "amount": [-0.123456789012345678, 1.5, 100.0, 1.0],
                         "balance_raw": ["-123456789012345678", "1500000000000000000", "10", "1000000000000000000"]})
    rows, book = pv.snapshot_book(snap, "ETH", ts=e - 3600)
    assert rows == [(pv.OPTION_ASSET["ETH"], books.encode_option_subid(e, 3000.0, True), -123456789012345678),
                    (pv.PERP_ASSET["ETH"], 0, 1500000000000000000)]
    assert book.perp == 1.5 and book.perp_entry is None and book.cash == 0.0
    assert [(leg.expiry, leg.strike, leg.is_call) for leg in book.options] == [(e, 3000.0, True)]
    assert book.options[0].amount == pytest.approx(-0.123456789012345678)


# ---------------------------------------------------------------- chain results

def test_decode_signed_words_and_scenario_minimum():
    assert pv.decode_int(((1 << 256) - 5).to_bytes(32, "big")) == -5
    assert pv.decode_int((7).to_bytes(32, "big") + bytes(32)) == 7
    # net over all scenarios = min over the single-scenario nets (R is monotone in minSPAN)
    assert pv.net_from_scenarios([-3 * 10 ** 18, -5 * 10 ** 18, -4 * 10 ** 18]) == -5.0
    with pytest.raises(ValueError):
        pv.net_from_scenarios([])


def test_capital_and_relative_error():
    assert pv.capital(120.0, -380.0) == 500.0
    assert pv.capital(-120.0, -500.0) == 380.0
    assert pv.rel_err(101.0, 100.0) == pytest.approx(0.01)
    assert pv.rel_err(-99.0, -100.0) == pytest.approx(0.01)
    assert math.isnan(pv.rel_err(float("nan"), 100.0))


# ---------------------------------------------------------------- windows and draws

def test_windows_follow_the_preregistration():
    start, end = _ts("2024-01-11 00:00"), _ts("2026-09-17 12:00")
    assert pv.WINDOWS[("BTC", "sm")] == (start, end)
    assert pv.WINDOWS[("ETH", "pm")] == (start, end)
    assert pv.WINDOWS[("BTC", "pm2")] == (_ts("2025-06-12 23:00"), end)
    assert pv.WINDOWS[("ETH", "pm2")] == (_ts("2025-06-12 23:00"), end)
    assert pv.WINDOWS[("HYPE", "pm2")] == (_ts("2025-11-11 00:00"), end)
    assert pv.WINDOWS[("HYPE", "sm")] == (_ts("2025-11-11 00:00"), end)
    assert ("HYPE", "pm") not in pv.WINDOWS
    assert pv.CELLS == [("BTC", "sm"), ("BTC", "pm"), ("BTC", "pm2"), ("ETH", "sm"), ("ETH", "pm"), ("ETH", "pm2"),
                        ("HYPE", "sm"), ("HYPE", "pm2")]
    assert pv.N_SINGLE >= 48 and pv.N_BOOK_DAYS == 20 and pv.SEED == 20260924


def test_draw_block_stays_in_window_and_is_reproducible():
    lo, hi = _ts("2025-06-12 23:00"), _ts("2025-06-13 00:00")
    a = [pv.draw_block(pv.cell_rng(2), lo, hi) for _ in range(3)]
    b = [pv.draw_block(pv.cell_rng(2), lo, hi) for _ in range(3)]
    assert a == b
    rng = pv.cell_rng(0)
    blocks = [pv.draw_block(rng, lo, hi) for _ in range(500)]
    assert min(blocks) >= block_at_ts(lo) and ts_at_block(min(blocks)) >= lo
    assert max(blocks) <= block_at_ts(hi)
    assert len(set(blocks)) > 400
    # different cells draw different blocks from the same window
    assert pv.draw_block(pv.cell_rng(0), lo, hi) != pv.draw_block(pv.cell_rng(3), lo, hi)


def _frame(rows, cols=("block", "log_index", "expiry", "value", "confidence", "feed_ts")):
    df = pd.DataFrame(rows, columns=list(cols))
    df.insert(1, "block_ts", [ts_at_block(b) for b in df["block"]])
    return df


def _svi(rows):
    """rows of (block, expiry, feed_ts)."""
    n = len(rows)
    return pd.DataFrame({"block": [r[0] for r in rows], "block_ts": [ts_at_block(r[0]) for r in rows],
                         "log_index": list(range(n)), "expiry": [r[1] for r in rows], "feed_ts": [r[2] for r in rows],
                         "svi_a": np.float32([0.01] * n), "svi_b": np.float32([0.05] * n),
                         "svi_rho": np.float32([-0.2] * n), "svi_m": np.float32([0.0] * n),
                         "svi_sigma": np.float32([0.1] * n), "svi_fwd": [100.0] * n,
                         "svi_ref_tau": np.float32([0.1] * n), "confidence": np.float32([1.0] * n)})


def _history(ts):
    b = block_at_ts(ts)
    e1, e2, e3 = ts + 86_400, ts + 7 * 86_400, ts + 30 * 86_400
    spot = _frame([(b - 5, 0, 0, 100.0, 1.0, ts - 12)])
    fwd = _frame([(b - 50, 0, e1, 1.0, 1.0, ts - 100), (b - 3000, 0, e2, 1.0, 1.0, ts - 6000),
                  (b - 50, 1, e3, 2.0, 1.0, ts - 100)])
    fwd["fixed"] = 0.0
    svi = _svi([(b - 50, e1, ts - 100), (b - 50, e2, ts - 100), (b - 1100, e3, ts - 2200)])
    frames = {"spot": spot, "forward": fwd, "svi": svi}
    return FeedHistory("BTC", frames=frames), (e1, e2, e3)


def test_eligible_expiries_need_live_forward_and_fresh_vol_push():
    ts = _ts("2026-03-02 10:00")
    hist, (e1, e2, e3) = _history(ts)
    # e2: forward push 6000 s old (not live); e3: vol push signed 2200 s before ts (older than 20 min)
    assert pv.eligible_expiries(hist, ts) == [e1]
    assert pv.eligible_expiries(hist, ts, max_vol_age=3000) == [e1, e3]


def test_pick_contract_takes_a_fill_of_the_same_utc_day_with_an_eligible_expiry():
    ts = _ts("2026-03-02 10:00")
    day0 = _ts("2026-03-02 00:00") * 1000
    e1, e2 = ts + 86_400, ts + 7 * 86_400
    tape = pd.DataFrame({"trade_id": ["a", "a", "b", "c", "d"],
                         "timestamp": [day0 + 5, day0 + 5, day0 + 3_600_000, day0 - 10, day0 + 86_400_000],
                         "expiry": [e1, e1, e2, e1, e1], "strike": [100.0, 100.0, 110.0, 90.0, 95.0],
                         "option_type": ["C", "C", "P", "P", "C"], "trade_price": [5.0, 5.0, 7.0, 1.0, 2.0]})
    fills = pv.day_fills(tape, ts)
    assert sorted(fills["trade_id"]) == ["a", "b"]
    sides = set()
    for k in range(40):
        c = pv.pick_contract(pv.cell_rng(k), fills, [e1])
        assert c["trade_id"] == "a" and c["expiry"] == e1 and c["strike"] == 100.0 and c["is_call"] is True
        assert c["price"] == 5.0
        sides.add(c["amount"])
    assert sides == {-1.0, 1.0}
    assert pv.pick_contract(pv.cell_rng(0), fills, [ts + 99]) is None
    assert pv.pick_contract(pv.cell_rng(5), fills, [e1, e2]) == pv.pick_contract(pv.cell_rng(5), fills, [e1, e2])


# ---------------------------------------------------------------- maker days

def _snaps():
    rows = []
    e = _ts("2025-07-25 08:00")

    def add(sub, day, kind, ccy, expiry=None, amount=1.0):
        rows.append({"subaccount": sub, "day": pd.Timestamp(day), "block": block_at_ts(_ts(day + " 00:00")) + 1,
                     "manager": "0x0", "kind": kind, "ccy": ccy, "expiry": expiry, "amount": amount})

    add(7, "2025-06-10", "option", "BTC", e)        # before the PM2 window
    add(7, "2025-07-01", "option", "BTC", e)        # eligible
    add(7, "2025-07-02", "perp", "BTC")             # no option position
    add(8, "2025-07-01", "option", "HYPE", e)       # HYPE window opens on 11.11.2025
    add(8, "2025-11-12", "option", "HYPE", _ts("2025-11-28 08:00"))  # eligible
    add(12, "2025-07-26", "option", "ETH", e)       # option expired before the day
    add(12, "2025-07-03", "option", "ETH", e)       # eligible
    add(12, "2025-07-03", "option", "BTC", e)
    return pd.DataFrame(rows)


def test_maker_day_population_follows_h3_and_draw_is_reproducible():
    pop = pv.maker_day_population(_snaps())
    assert sorted((int(s), str(d.date())) for s, d in zip(pop["subaccount"], pop["day"])) == \
        [(7, "2025-07-01"), (8, "2025-11-12"), (12, "2025-07-03")]
    row = pop[pop["subaccount"] == 12].iloc[0]
    assert row["ccys"] == ["BTC", "ETH"]
    a = pv.select_maker_days(_snaps(), n=2)
    b = pv.select_maker_days(_snaps(), n=2)
    assert len(a) == 2 and a.equals(b)
    assert len(pv.select_maker_days(_snaps(), n=10)) == 3


# ---------------------------------------------------------------- replica side

def _state(ts, e, forward=100.0, rate=0.03):
    es = FeedExpiryState(expiry=e, forward=forward, svi=(0.01, 0.05, -0.2, 0.0, 0.1, 0.1), rate=rate, vol_conf=1.0,
                         fwd_conf=1.0, svi_fwd=forward, fwd_fixed=0.0, rate_conf=1.0)
    return MarketState(currency="BTC", ts=ts, spot=99.0, expiries={e: es}, perp=99.5)


def test_mark_premium_is_black76_on_the_svi_forward_without_discount():
    ts = _ts("2026-03-02 10:00")
    e = ts + 30 * 86_400
    st = _state(ts, e)
    book = Book(options=[OptionLeg(e, 110.0, True, -2.0), OptionLeg(e, 90.0, False, 1.0)], perp=3.0)
    call, _ = margin_sm.b76_prices(100.0, 110.0, st.expiries[e].vol(110.0), e - ts)
    _, put = margin_sm.b76_prices(100.0, 90.0, st.expiries[e].vol(90.0), e - ts)
    assert pv.mark_premium(book, st) == pytest.approx(-2.0 * float(call) + float(put), rel=1e-12)


def test_replica_net_returns_nan_when_the_chain_would_refuse_too_many_expiries():
    ts = _ts("2026-03-02 10:00")
    exps = [ts + (k + 1) * 86_400 for k in range(3)]
    states = {e: _state(ts, e).expiries[e] for e in exps}
    st = MarketState(currency="BTC", ts=ts, spot=99.0, expiries=states)
    book = Book(options=[OptionLeg(e, 100.0, True, -1.0) for e in exps])
    cases = _private("b1_chain_cases.json")["cases"]
    pm = next(c["params"] for c in cases if c["manager"] == "pm")
    pm2 = next(c["params"] for c in cases if c["manager"] == "pm2")
    assert math.isnan(pv.replica_net("pm", book, st, dict(pm, maxExpiries=2), True))
    assert math.isnan(pv.replica_net("pm2", book, st, dict(pm2, maxExpiries=2), True))
    assert math.isfinite(pv.replica_net("pm", book, st, dict(pm, maxExpiries=3), True))
    assert math.isfinite(pv.replica_net("pm2", book, st, dict(pm2, maxExpiries=3), False))


def test_replica_matches_state_override_chain_values_of_the_fixture():
    """Real eth_call results (StandardManager, PMRM, PMRM_2 getMargin of a synthetic account under state override)
    against the replica on the same feed state (from data/p2/feeds and the Paper 1 SVI history) and parameters."""
    fx = _private("b1_chain_cases.json")
    assert len(fx["cases"]) >= 8
    kinds = {(c["kind"], c["manager"]) for c in fx["cases"]}
    assert {("single", "sm"), ("single", "pm"), ("single", "pm2"), ("book", "pm2"), ("book", "sm")} <= kinds
    for c in fx["cases"]:
        st = pv.state_from_json(c["state"])
        book = pv.book_from_json(c["book"])
        for key, is_initial in (("IM", True), ("MM", False)):
            chain = c["chain"][key]
            rep = pv.replica_net(c["manager"], book, st, c["params"], is_initial)
            k_chain = pv.capital(c["premium"], chain)
            assert abs(rep - chain) <= 1e-6 * max(abs(k_chain), 1.0), (c["id"], key, rep, chain)


# ---------------------------------------------------------------- summary

def test_summarize_checks_the_preregistered_thresholds():
    rows = []
    for i in range(100):
        rows.append({"kind": "single", "ccy": "BTC", "manager": "sm", "is_initial": True, "rel_err": 1e-5 * i})
        rows.append({"kind": "single", "ccy": "ETH", "manager": "pm2", "is_initial": True,
                     "rel_err": 0.02 if i >= 90 else 1e-6})
    rows.append({"kind": "single", "ccy": "ETH", "manager": "pm2", "is_initial": True, "rel_err": float("nan")})
    s = pv.summarize(pd.DataFrame(rows)).set_index(["kind", "ccy", "manager", "is_initial"])
    btc = s.loc[("single", "BTC", "sm", True)]
    assert btc["n"] == 100 and btc["median_rel"] == pytest.approx(np.median(1e-5 * np.arange(100)))
    assert btc["p95_rel"] == pytest.approx(np.percentile(1e-5 * np.arange(100), 95))
    assert bool(btc["passes"]) is True
    eth = s.loc[("single", "ETH", "pm2", True)]
    assert eth["n"] == 100 and eth["n_missing"] == 1
    assert bool(eth["passes"]) is False and eth["p95_rel"] == pytest.approx(0.02)
