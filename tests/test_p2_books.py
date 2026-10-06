from __future__ import annotations

import calendar
import datetime as dt
import json
from pathlib import Path

import pandas as pd
import pytest

from derive_surface import books
from derive_surface.p2chain import Rpc, ts_at_block

FIX = Path(__file__).parent / "fixtures" / "p2"
# Real chain data of top-maker accounts (a whole multicall answer, a day of BalanceAdjusted logs with tx hashes)
# identifies the account, so these fixtures live in data/p2/fixtures_private (not tracked, Addendum 1.4, audit A01);
# without them the tests that need them are skipped. books_registry.json holds the non-identifying part.
PRIVATE = Path(__file__).resolve().parents[1] / "data" / "p2" / "fixtures_private"


def _private(name: str) -> dict:
    path = PRIVATE / name
    if not path.exists():
        pytest.skip(f"private chain fixture missing (account-identifying, not in the repository): {path}")
    return json.loads(path.read_text())


def _snap_fixture() -> dict:
    return _private("books_chain_snapshot.json")


def _reg_fixture() -> dict:
    """Asset registry (protocol addresses, managers, cash asset, a day-start block) without account data."""
    return json.loads((FIX / "books_registry.json").read_text())


def _registry(fx: dict) -> "books.AssetRegistry":
    return books.AssetRegistry.from_dicts(fx["addresses_head_cur"], fx["all_currencies_result"], fx["managers"])


def _day_ts(day: str) -> int:
    return calendar.timegm(dt.date.fromisoformat(day).timetuple())


# ---------------------------------------------------------------- sub id decoding (OptionEncoding.sol)

def test_decode_option_subid_matches_api_instruments():
    cases = json.loads((FIX / "books_subid_api.json").read_text())["cases"]
    assert len(cases) >= 3
    for c in cases:
        od = c["option_details"]
        expiry, strike, is_call = books.decode_option_subid(int(c["base_asset_sub_id"]))
        assert expiry == od["expiry"]
        assert strike == float(od["strike"])
        assert is_call is (od["option_type"] == "C")
        ccy, e2, k2, c2 = books.parse_instrument_name(c["instrument_name"])
        assert (e2, k2, c2) == (expiry, strike, is_call)
        assert books.instrument_name(ccy, expiry, strike, is_call) == c["instrument_name"]
        assert books.encode_option_subid(expiry, strike, is_call) == int(c["base_asset_sub_id"])


def test_decode_option_subid_bit_layout():
    # [1 bit isCall][63 bits strike / 1e10 (8 decimals)][32 bits expiry]
    sub = (1 << 95) | (8_543_210_000 << 32) | 1_790_323_200
    assert books.decode_option_subid(sub) == (1_790_323_200, 85.4321, True)
    assert books.decode_option_subid(7) == (7, 0.0, False)
    with pytest.raises(ValueError):
        books.decode_option_subid(1 << 96)  # SafeCast.toUint96 reverts


# ---------------------------------------------------------------- ABI

def test_encode_aggregate3_matches_reference_calldata():
    fx = _reg_fixture()
    calls = []
    for acc in fx["encoder_reference"]["accounts"]:
        calls += books.account_calls(acc)
    assert books.encode_aggregate3(calls) == fx["encoder_reference"]["calldata"]


def test_decode_aggregate3_and_balances_from_real_response():
    fx = _snap_fixture()
    res = books.decode_aggregate3(bytes.fromhex(fx["response_hex"][2:]))
    assert len(res) == 2 and all(ok for ok, _ in res)
    bals = books.decode_balances(res[0][1])
    assert len(bals) == 38
    assert books.decode_address(res[1][1]) == fx["manager"]
    cash = [b for b in bals if b[0] == fx["cash_asset"]]
    assert len(cash) == 1 and cash[0][1] == 0 and cash[0][2] < 0  # negative int256 balance decoded


# ---------------------------------------------------------------- snapshot with a fake RPC

class _FakeChain:
    """Answers Multicall3.aggregate3 with a recorded response and manager.cashAsset() with the fixture address."""

    def __init__(self, fx: dict, response_hex: str = None):
        self.fx = fx
        self.response_hex = response_hex or fx["response_hex"]
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        tx, _blk = params
        if tx["to"].lower() == books.MULTICALL3.lower():
            return self.response_hex
        if tx["data"] == "0x" + books.SEL_CASH_ASSET:
            return "0x" + "00" * 12 + self.fx["cash_asset"][2:]
        raise AssertionError(f"unexpected call {tx}")


def test_snapshot_decodes_real_balances():
    fx = _snap_fixture()
    chain = _FakeChain(fx)
    rpc = Rpc(client=chain, rate=1000.0)
    rows = books.snapshot(rpc, 12345, fx["block"], registry=_registry(fx))
    exp = fx["expected"]  # account-specific values stay in the private fixture
    kinds = pd.Series([r["kind"] for r in rows]).value_counts().to_dict()
    assert kinds == exp["kinds"] and sum(kinds.values()) == 38
    assert {r["manager"] for r in rows} == {fx["manager"]}
    opts = [r for r in rows if r["kind"] == "option"]
    assert {r["ccy"] for r in opts} == set(exp["option_ccys"])
    open_names = set(fx["open_tape_instruments"])
    # every on-chain option leg decodes to an instrument this account traded before the block, except one leg
    # that reached the account without a tape fill
    missing = {books.instrument_name(r["ccy"], r["expiry"], r["strike"], r["is_call"]) for r in opts} - open_names
    assert missing == set(exp["missing_from_tape"]) and len(missing) == 1
    for r in opts:
        assert r["amount"] == r["balance"] / 1e18
    base = {r["ccy"] for r in rows if r["kind"] == "base"}
    assert base == set(exp["base_ccys"])
    cash = [r for r in rows if r["kind"] == "cash"][0]
    assert cash["ccy"] == "USDC" and cash["amount"] == pytest.approx(exp["cash_usdc"]) and cash["amount"] < 0
    # one aggregate3 call and one cashAsset() call for the (new) manager
    assert [c[0] for c in chain.calls] == ["eth_call", "eth_call"]


def _aggregate3_response(entries) -> str:
    """ABI-encode (bool,bytes)[] for tests."""
    return "0x" + books._encode_bool_bytes_array(entries).hex()


def test_snapshot_empty_and_missing_account():
    fx = _reg_fixture()
    empty_bal = books._encode_balances([])
    mgr_word = bytes(12) + bytes.fromhex(fx["manager"][2:])
    resp = _aggregate3_response([(True, empty_bal), (True, mgr_word)])
    rpc = Rpc(client=_FakeChain(fx, resp), rate=1000.0)
    rows = books.snapshot(rpc, 1, fx["block"], registry=_registry(fx))
    assert len(rows) == 1 and rows[0]["kind"] == "none" and rows[0]["manager"] == fx["manager"]
    resp0 = _aggregate3_response([(True, empty_bal), (True, bytes(32))])
    rpc0 = Rpc(client=_FakeChain(fx, resp0), rate=1000.0)
    assert books.snapshot(rpc0, 1, fx["block"], registry=_registry(fx)) == []  # not yet created


def test_balances_roundtrip_negative():
    rows = [("0x" + "11" * 20, 5, -3 * 10 ** 18), ("0x" + "22" * 20, (1 << 95) | 9, 10 ** 17)]
    assert books.decode_balances(books._encode_balances(rows)) == rows


# ---------------------------------------------------------------- top makers

def test_top_maker_subaccounts_orders_by_fill_count_then_id():
    m = pd.DataFrame({"maker_sub": [5, 5, 5, 9, 9, 9, 2, 2, 7]})
    assert books.top_maker_subaccounts(n=3, markouts=m) == [5, 9, 2]
    assert books.top_maker_subaccounts(n=10, markouts=m) == [5, 9, 2, 7]


def test_first_block_of_day():
    assert books.first_block_of_day(_day_ts("2024-01-11")) == 2_454_793
    b = books.first_block_of_day(_day_ts("2025-12-01"))
    assert ts_at_block(b) == _day_ts("2025-12-01") + 1 and ts_at_block(b - 1) < _day_ts("2025-12-01")


# ---------------------------------------------------------------- book before a fill

def _snap_rows(day: str, sub: int = 42) -> pd.DataFrame:
    base = dict(subaccount=sub, day=pd.Timestamp(day), block=1, manager="0xm", asset="0xa", sub_id="0")
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600      # alive
    e0 = _day_ts(day) + 8 * 3600                  # expires at 08:00 of the same day
    rows = [
        dict(base, kind="option", ccy="BTC", expiry=e1, strike=100000.0, is_call=True, amount=-2.0),
        dict(base, kind="option", ccy="BTC", expiry=e1, strike=90000.0, is_call=False, amount=1.5),
        dict(base, kind="option", ccy="ETH", expiry=e0, strike=3000.0, is_call=True, amount=4.0),
        dict(base, kind="perp", ccy="BTC", expiry=None, strike=None, is_call=None, amount=-0.3),
        dict(base, kind="cash", ccy="USDC", expiry=None, strike=None, is_call=None, amount=1e6),
        dict(base, kind="base", ccy="ETH", expiry=None, strike=None, is_call=None, amount=3.0),
    ]
    return pd.DataFrame(rows)


def _tape(day: str, sub: int = 42) -> pd.DataFrame:
    d0 = _day_ts(day) * 1000
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600
    exp_name = dt.datetime.utcfromtimestamp(e1).strftime("%Y%m%d")
    rows = [
        # maker row: sells 0.5 more of the existing short call -> -2.5
        dict(timestamp=d0 + 3_600_000, instrument_name=f"BTC-{exp_name}-100000-C", direction="sell",
             liquidity_role="maker", trade_amount=0.5, subaccount_id=sub, currency="BTC", expiry=e1,
             strike=100000.0, option_type="C"),
        # taker row: buys a new ETH put
        dict(timestamp=d0 + 7_200_000, instrument_name=f"ETH-{exp_name}-2500-P", direction="buy",
             liquidity_role="taker", trade_amount=10.0, subaccount_id=sub, currency="ETH", expiry=e1,
             strike=2500.0, option_type="P"),
        # sells the whole long put leg -> leg vanishes (1.5 - 1.5 = 0)
        dict(timestamp=d0 + 7_300_000, instrument_name=f"BTC-{exp_name}-90000-P", direction="sell",
             liquidity_role="maker", trade_amount=1.5, subaccount_id=sub, currency="BTC", expiry=e1,
             strike=90000.0, option_type="P"),
        # after ts: ignored
        dict(timestamp=d0 + 40_000_000, instrument_name=f"BTC-{exp_name}-100000-C", direction="buy",
             liquidity_role="maker", trade_amount=9.0, subaccount_id=sub, currency="BTC", expiry=e1,
             strike=100000.0, option_type="C"),
        # other subaccount: ignored
        dict(timestamp=d0 + 3_600_000, instrument_name=f"BTC-{exp_name}-100000-C", direction="buy",
             liquidity_role="taker", trade_amount=0.5, subaccount_id=sub + 1, currency="BTC", expiry=e1,
             strike=100000.0, option_type="C"),
        # previous day: already in the day-start snapshot, ignored
        dict(timestamp=d0 - 1_000, instrument_name=f"BTC-{exp_name}-100000-C", direction="sell",
             liquidity_role="maker", trade_amount=7.0, subaccount_id=sub, currency="BTC", expiry=e1,
             strike=100000.0, option_type="C"),
    ]
    return pd.DataFrame(rows)


def test_book_at_adds_fills_before_ts_and_drops_expired():
    day = "2025-07-01"
    ts = _day_ts(day) * 1000 + 9 * 3_600_000  # 09:00 UTC, after the ETH expiry at 08:00
    out = books.book_at(_snap_rows(day), _tape(day), ts)
    assert set(out) == {"BTC", "ETH"}
    btc = {leg.key: leg.amount for leg in out["BTC"].options}
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600
    assert btc == {(e1, 100000.0, True): -2.5}
    assert out["BTC"].perp == -0.3 and out["BTC"].perp_entry is None and out["BTC"].cash == 0.0
    eth = {leg.key: leg.amount for leg in out["ETH"].options}
    assert eth == {(e1, 2500.0, False): 10.0}  # expired ETH call removed, taker fill added
    assert out["ETH"].perp == 0.0


def test_book_at_before_expiry_keeps_leg_and_excludes_fill_at_ts():
    day = "2025-07-01"
    ts = _day_ts(day) * 1000 + 3_600_000  # exactly the first fill's timestamp: strictly earlier fills only
    out = books.book_at(_snap_rows(day), _tape(day), ts)
    e0 = _day_ts(day) + 8 * 3600
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600
    assert {leg.key: leg.amount for leg in out["BTC"].options} == {(e1, 100000.0, True): -2.0, (e1, 90000.0, False): 1.5}
    assert {leg.key: leg.amount for leg in out["ETH"].options} == {(e0, 3000.0, True): 4.0}


def test_book_at_rejects_mixed_snapshots():
    rows = pd.concat([_snap_rows("2025-07-01"), _snap_rows("2025-07-02")])
    with pytest.raises(ValueError):
        books.book_at(rows, _tape("2025-07-01"), _day_ts("2025-07-01") * 1000)


# ---------------------------------------------------------------- resumable loader and compaction

class _DayChain:
    """Multicall answers for two accounts: account 1 always exists, account 2 only from the second day on."""

    def __init__(self, fx: dict, second_day_block: int):
        self.fx, self.second_day_block, self.calls = fx, second_day_block, []

    def call(self, method, params):
        self.calls.append((method, params))
        tx, blk = params
        blk = int(blk, 16)
        if tx["to"].lower() == books.MULTICALL3.lower():
            real = books.decode_aggregate3(bytes.fromhex(self.fx["response_hex"][2:]))
            mgr = bytes(12) + bytes.fromhex(self.fx["manager"][2:])
            acc2 = [(True, books._encode_balances([])), (True, mgr if blk >= self.second_day_block else bytes(32))]
            return _aggregate3_response(list(real) + acc2)
        if tx["data"] == "0x" + books.SEL_CASH_ASSET:
            return "0x" + "00" * 12 + self.fx["cash_asset"][2:]
        raise AssertionError(tx)


def test_load_is_resumable_and_compacts(tmp_path):
    fx = _snap_fixture()
    days = ["2025-12-01", "2025-12-02", "2025-12-03"]
    second = books.first_block_of_day(_day_ts("2025-12-02"))
    chain = _DayChain(fx, second)
    rpc = Rpc(client=chain, rate=1000.0)
    reg = _registry(fx)
    st = books.load_snapshots(rpc, [1, 2], days[0], days[-1], out_dir=tmp_path, registry=reg, max_days=2)
    assert st["done"] == 2 and st["remaining"] == 1
    st = books.load_snapshots(rpc, [1, 2], days[0], days[-1], out_dir=tmp_path, registry=reg)
    assert st["done"] == 1 and st["remaining"] == 0
    n_mc = sum(1 for _, p in chain.calls if p[0]["to"].lower() == books.MULTICALL3.lower())
    assert n_mc == 3  # one aggregate3 per day, none repeated
    df = books.compact(tmp_path, registry=reg)
    assert list(df.columns[:12]) == ["subaccount", "day", "block", "manager", "asset", "sub_id", "kind", "ccy",
                                      "expiry", "strike", "is_call", "amount"]
    assert (tmp_path / "snapshots.parquet").exists()
    per = df.groupby(["subaccount", "day"]).size()
    assert per.loc[(1, pd.Timestamp("2025-12-01"))] == 38
    assert (2, pd.Timestamp("2025-12-01")) not in per.index  # account 2 not yet created
    two = df[(df.subaccount == 2)]
    assert list(two.kind) == ["none", "none"] and set(two.manager) == {fx["manager"]}
    assert df.block.min() == books.first_block_of_day(_day_ts("2025-12-01"))
    assert set(df.manager_label) == {reg.manager_label(fx["manager"])} and "unknown" not in set(df.manager_label)


# ---------------------------------------------------------------- reconciliation day -> next day

def test_reconcile_day_counts_matches_and_breaks():
    day, nxt = "2025-07-01", "2025-07-02"
    snap = _snap_rows(day)
    tape = _tape(day)
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600
    base = dict(subaccount=42, day=pd.Timestamp(nxt), block=2, manager="0xm", asset="0xa", sub_id="0")
    # expected next day: BTC call -2.0-0.5+9.0 = 6.5, BTC put 0, ETH put 10 (ETH call expired)
    nxt_rows = pd.DataFrame([
        dict(base, kind="option", ccy="BTC", expiry=e1, strike=100000.0, is_call=True, amount=6.5),
        dict(base, kind="option", ccy="ETH", expiry=e1, strike=2500.0, is_call=False, amount=9.0),  # transfer: off by 1
    ])
    r = books.reconcile_day(snap, nxt_rows, tape)
    assert r["n_legs"] == 2 and r["n_match"] == 1 and r["day_match"] is False
    assert r["max_abs_diff"] == pytest.approx(1.0)


class _GasCapChain:
    """Rejects Multicall batches with more than one account (as an RPC gas-cap error would)."""

    def __init__(self, fx: dict):
        self.fx, self.batches = fx, []

    def call(self, method, params):
        tx, _ = params
        if tx["to"].lower() == books.MULTICALL3.lower():
            body = tx["data"][2 + 8:]  # strip 0x and selector: [offset][n calls][...]
            n_accounts = int(body[64:128], 16) // 2
            self.batches.append(n_accounts)
            if n_accounts > 1:
                from derive_surface.chainfeeds import RpcError
                raise RpcError({"code": -32000, "message": "gas required exceeds allowance"})
            return self.fx["response_hex"]
        if tx["data"] == "0x" + books.SEL_CASH_ASSET:
            return "0x" + "00" * 12 + self.fx["cash_asset"][2:]
        raise AssertionError(tx)


def test_fetch_raw_splits_batch_on_rpc_error():
    fx = _snap_fixture()
    chain = _GasCapChain(fx)
    rpc = Rpc(client=chain, rate=1000.0)
    out = books.snapshot_many(rpc, [1, 2, 3], fx["block"], registry=_registry(fx))
    assert sorted(out) == [1, 2, 3] and all(len(v) == 38 for v in out.values())
    assert chain.batches == [3, 1, 2, 1, 1]  # halves until every batch fits


def test_book_at_creation_day_without_snapshot_needs_subaccount():
    day = "2025-07-01"
    ts = _day_ts(day) * 1000 + 9 * 3_600_000
    empty = pd.DataFrame(columns=["subaccount", "day", "kind", "ccy", "expiry", "strike", "is_call", "amount"])
    with pytest.raises(ValueError):
        books.book_at(empty, _tape(day), ts)  # tape holds two subaccounts: ambiguous
    out = books.book_at(empty, _tape(day), ts, subaccount=42)
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600
    assert {leg.key: leg.amount for leg in out["BTC"].options} == {(e1, 100000.0, True): -0.5, (e1, 90000.0, False): -1.5}
    assert {leg.key: leg.amount for leg in out["ETH"].options} == {(e1, 2500.0, False): 10.0}


# ---------------------------------------------------------------- fix round: which timestamp cuts the book

def _rfq_tape(day: str, sub: int = 42) -> pd.DataFrame:
    """RFQ fill X: the maker row (this account) is 4 s older than the taker row (other account) that markouts.ts
    carries; fill Y of the same account lies between the two; Z shares X's millisecond (second RFQ leg)."""
    d0 = _day_ts(day) * 1000
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600
    t_m = d0 + 5 * 3_600_000
    common = dict(currency="BTC", expiry=e1, option_type="C")
    rows = [
        dict(trade_id="X", timestamp=t_m, direction="sell", liquidity_role="maker", trade_amount=0.01,
             subaccount_id=sub, strike=145000.0, **common),
        dict(trade_id="X", timestamp=t_m + 4_000, direction="buy", liquidity_role="taker", trade_amount=0.01,
             subaccount_id=sub + 1, strike=145000.0, **common),
        dict(trade_id="Y", timestamp=t_m + 2_000, direction="sell", liquidity_role="maker", trade_amount=3.0,
             subaccount_id=sub, strike=100000.0, **common),
        dict(trade_id="Z", timestamp=t_m, direction="buy", liquidity_role="maker", trade_amount=1.0,
             subaccount_id=sub, strike=150000.0, **common),
    ]
    return pd.DataFrame(rows)


def test_book_before_fill_excludes_own_rfq_fill_and_later_fills():
    day = "2025-10-30"
    snap, tape = _snap_rows(day), _rfq_tape(day)
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600
    t_m = int(tape.loc[(tape.trade_id == "X") & (tape.subaccount_id == 42), "timestamp"].iloc[0])
    t_taker = t_m + 4_000  # markouts.ts of this fill
    start = {(e1, 100000.0, True): -2.0, (e1, 90000.0, False): 1.5}
    by_trade = books.book_before_fill(snap, tape, "X")
    assert {leg.key: leg.amount for leg in by_trade["BTC"].options} == start  # neither X, Y nor Z (same ms)
    by_maker_ts = books.book_at(snap, tape, t_m)
    assert {leg.key: leg.amount for leg in by_maker_ts["BTC"].options} == start
    # the pitfall: markouts.ts (taker row) puts X itself and Y into the book "before" the fill
    wrong = {leg.key: leg.amount for leg in books.book_at(snap, tape, t_taker)["BTC"].options}
    assert wrong[(e1, 145000.0, True)] == -0.01 and wrong[(e1, 100000.0, True)] == -5.0
    # explicit exclusion of the fill's trade id keeps Y (a genuinely earlier fill in that window) but never X
    excl = {leg.key: leg.amount for leg in books.book_at(snap, tape, t_taker, exclude_trade_ids=["X"])["BTC"].options}
    assert (e1, 145000.0, True) not in excl and excl[(e1, 100000.0, True)] == -5.0
    with pytest.raises(KeyError):
        books.book_before_fill(snap, tape, "unknown-trade")


def test_book_at_rejects_ts_outside_the_snapshot_day_and_seconds():
    day = "2025-07-01"
    snap = _snap_rows(day)
    with pytest.raises(ValueError):
        books.book_at(snap, _tape(day), _day_ts(day) * 1000 - 1)  # before the snapshot day: book from the future
    with pytest.raises(ValueError):
        books.book_at(snap, _tape(day), (_day_ts(day) + 86400) * 1000)  # next day needs the next snapshot
    with pytest.raises(ValueError):
        books.book_at(snap, _tape(day), _day_ts(day) + 3600)  # seconds instead of milliseconds
    books.book_at(snap, _tape(day), (_day_ts(day) + 86400) * 1000 - 1)  # last millisecond of the day is fine


def test_fill_day_is_the_utc_day_of_the_given_row():
    ts_maker = _day_ts("2025-10-30") * 1000 + 86_400_000 - 100  # 23:59:59.900
    assert books.fill_day(ts_maker) == pd.Timestamp("2025-10-30")
    assert books.fill_day(ts_maker + 4_000) == pd.Timestamp("2025-10-31")


def test_book_at_perp_only_account():
    day = "2025-07-01"
    snap = _snap_rows(day)
    snap = snap[snap.kind.isin(["perp", "cash"])]
    out = books.book_at(snap, None, _day_ts(day) * 1000 + 1)
    assert list(out) == ["BTC"]
    assert out["BTC"].options == [] and out["BTC"].perp == -0.3 and out["BTC"].perp_entry is None


def test_registry_labels_and_unknown_assets():
    fx = _reg_fixture()
    reg = _registry(fx)
    assert reg.classify("0x" + "ab" * 20) == ("other", None)
    assert reg.manager_label(books.ZERO_ADDRESS) == "none" and reg.manager_label(None) == "none"
    assert reg.manager_label("0x" + "cd" * 20) == "unknown"
    assert reg.manager_label("0xC755DAe3fd295A687adf3e192387163f813F0598") == "PM2:ETH"
    btc = fx["addresses_head_cur"]["BTC"]
    assert reg.classify(btc["option"]) == ("option", "BTC") and reg.classify(btc["perp"]) == ("perp", "BTC")


class _NetDownChain:
    def __init__(self):
        self.n = 0

    def call(self, method, params):
        self.n += 1
        raise RuntimeError("eth_call: giving up after 8 attempts")


def test_fetch_raw_does_not_split_on_network_errors():
    fx = _reg_fixture()
    chain = _NetDownChain()
    with pytest.raises(RuntimeError):
        books.snapshot_many(Rpc(client=chain, rate=1000.0), [1, 2, 3, 4], fx["block"], registry=_registry(fx))
    assert chain.n == 1


# ---------------------------------------------------------------- fix round: exact on-chain book (BalanceAdjusted)

def _ev_fixture() -> dict:
    return _private("books_events_day.json")


def _ev_registry() -> "books.AssetRegistry":
    fx, ev = _reg_fixture(), _ev_fixture()
    reg = _registry(fx)
    reg.cash_by_manager[ev["day_start"]["manager"].lower()] = fx["cash_asset"].lower()
    return reg


def _ev_frames():
    ev, reg = _ev_fixture(), _ev_registry()
    acc = ev["placeholder_account"]
    nxt = (pd.Timestamp(ev["day"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    s0 = books.snapshot_frame(acc, ev["day"], ev["day_start"]["block"], ev["day_start"]["manager"],
                              ev["day_start"]["balances"], reg)
    s1 = books.snapshot_frame(acc, nxt, ev["next_day"]["block"], ev["next_day"]["manager"], ev["next_day"]["balances"], reg)
    events = books.events_frame([books.decode_balance_adjusted(lg) for lg in ev["logs"]], day=ev["day"])
    return ev, reg, s0, s1, events


def _nonzero(d: dict) -> dict:
    return {k: v for k, v in d.items() if v != 0}


def test_decode_balance_adjusted_real_logs():
    ev, reg = _ev_fixture(), _ev_registry()
    rows = [books.decode_balance_adjusted(lg) for lg in ev["logs"]]
    assert books.T_BALANCE_ADJUSTED == ev["logs"][0]["topics"][0]
    r, lg = rows[0], ev["logs"][0]
    key = int(lg["topics"][3], 16)
    assert r["subaccount"] == 4242 and r["manager"] == ev["day_start"]["manager"].lower()
    assert int(r["asset"], 16) == key >> 96 and r["sub_id"] == key & ((1 << 96) - 1)
    assert (r["block"], r["tx_index"], r["log_index"]) == tuple(int(lg[k], 16) for k in
                                                               ("blockNumber", "transactionIndex", "logIndex"))
    assert r["tx_hash"] == lg["transactionHash"].lower() and r["trade_id"] > 0
    assert all(x["pre"] + x["amount"] == x["post"] for x in rows)  # v2-core emits delta = post - pre
    kinds = pd.Series([reg.classify(x["asset"])[0] for x in rows]).value_counts().to_dict()
    assert kinds == {"option": 57, "cash": 52}
    assert len({x["tx_hash"] for x in rows}) == 27


def test_replay_day_start_plus_events_equals_next_day_start():
    ev, _, s0, _, events = _ev_frames()
    got = _nonzero(books.replay_balances(s0, events))
    exp = {(a.lower(), int(s)): int(b) for a, s, b in ev["next_day"]["balances"]}
    assert got == exp  # every asset incl. cash and the 08:00 settlement, to the wei


def test_replay_before_and_through_fill_tx_match_eth_call():
    ev, _, s0, _, events = _ev_frames()
    tx = ev["fill_tape_row"]["tx_hash"]
    before = {(a, s): b for a, s, b in books.decode_balances(bytes.fromhex(ev["balances_before_fill_hex"][2:]))}
    after = {(a, s): b for a, s, b in books.decode_balances(bytes.fromhex(ev["balances_after_fill_hex"][2:]))}
    assert _nonzero(books.replay_balances(s0, events, tx_hash=tx)) == before
    assert _nonzero(books.replay_balances(s0, events, tx_hash=tx, include_tx=True)) == after
    with pytest.raises(KeyError):
        books.replay_balances(s0, events, tx_hash="0x" + "00" * 32)


def test_replay_detects_missing_events_and_missing_snapshot():
    ev, reg, s0, _, events = _ev_frames()
    cash = _reg_fixture()["cash_asset"].lower()
    gap = events.drop(index=events.index[events.asset == cash][0])
    with pytest.raises(ValueError):
        books.replay_balances(s0, gap)
    with pytest.raises(ValueError):
        books.replay_balances(s0.iloc[0:0], events)  # the account held these legs at 00:00: pre balance != 0


def test_onchain_book_before_fill_vs_tape_book():
    ev, reg, s0, _, events = _ev_frames()
    row = ev["fill_tape_row"]
    tx = row["tx_hash"]
    on = books.onchain_book_before(s0, events, tx, registry=reg)
    blk = int(events.loc[events.tx_hash == tx, "block"].min())
    assert blk == ev["fill_block"]
    exp_legs, exp_perp = {}, 0.0
    for a, s, b in books.decode_balances(bytes.fromhex(ev["balances_before_fill_hex"][2:])):
        kind, ccy = reg.classify(a)
        if kind == "option" and ccy == "ETH":
            e, k, c = books.decode_option_subid(s)
            if e > ts_at_block(blk):
                exp_legs[(e, k, c)] = round(b / 1e18, 10)
        elif kind == "perp" and ccy == "ETH":
            exp_perp += b / 1e18
    assert set(on) == {"ETH"}
    assert {leg.key: leg.amount for leg in on["ETH"].options} == exp_legs
    assert on["ETH"].perp == exp_perp != 0.0 and on["ETH"].perp_entry is None and on["ETH"].cash == 0.0
    # the tape-based book (day start + tape fills) misses 24 trade-module transfers of the same operator
    tape = pd.DataFrame([dict(row, subaccount_id=4242)])
    tb = books.book_before_fill(s0, tape, row["trade_id"], subaccount=4242)
    cmp = books.compare_books(tb.get("ETH"), on.get("ETH"))
    assert cmp["options_equal"] is False and cmp["perp_equal"] is True and cmp["n_diff"] > 0
    tape_keys = {leg.key for leg in tb["ETH"].options}
    moved = set()
    for r in events[(events.tx_hash != tx) & (events.block < blk)].itertuples():
        if reg.classify(r.asset)[0] == "option":
            e, k, c = books.decode_option_subid(int(r.sub_id))
            if e > ts_at_block(blk):
                moved.add((e, k, c))
    diff_keys = {k for k in tape_keys | set(exp_legs)
                 if abs({leg.key: leg.amount for leg in tb["ETH"].options}.get(k, 0.0) - exp_legs.get(k, 0.0)) > 1e-9}
    assert diff_keys and diff_keys <= moved and cmp["n_diff"] == len(diff_keys)


def test_onchain_book_applies_perp_events_before_the_fill_tx():
    fx = _reg_fixture()
    reg = _registry(fx)
    btc = fx["addresses_head_cur"]["BTC"]
    perp, opt = btc["perp"].lower(), btc["option"].lower()
    day = "2025-12-01"
    b0 = books.first_block_of_day(_day_ts(day))
    e1 = _day_ts(day) + 86400 * 7 + 8 * 3600
    sid = books.encode_option_subid(e1, 90000.0, False)
    snap = books.snapshot_frame(7, day, b0, fx["manager"], [[perp, "0", str(-3 * 10 ** 17)], [opt, str(sid), str(2 * 10 ** 18)]], reg)

    def ev(block, tx, li, asset, sub, pre, amt):
        return dict(subaccount=7, manager=fx["manager"].lower(), block=block, tx_index=0, log_index=li, tx_hash=tx,
                    asset=asset, sub_id=sub, amount=amt, pre=pre, post=pre + amt, trade_id=block)

    events = books.events_frame([
        ev(b0 + 10, "0xa", 0, perp, 0, -3 * 10 ** 17, 10 ** 17),
        ev(b0 + 20, "0xb", 1, opt, sid, 2 * 10 ** 18, -10 ** 18),
        ev(b0 + 20, "0xb", 2, perp, 0, -2 * 10 ** 17, 5 * 10 ** 17),
    ], day=day)
    before = books.onchain_book_before(snap, events, "0xb", registry=reg)
    assert before["BTC"].perp == pytest.approx(-0.2) and [lg.amount for lg in before["BTC"].options] == [2.0]
    through = books.onchain_book_before(snap, events, "0xb", registry=reg, include_tx=True)
    assert through["BTC"].perp == pytest.approx(0.3) and [lg.amount for lg in through["BTC"].options] == [1.0]


class _LogChain:
    """eth_getLogs over the fixture logs; more than ``limit`` results raise the node's result-limit error."""

    def __init__(self, logs, limit=None):
        self.logs, self.limit, self.ranges = logs, limit, []

    def call(self, method, params):
        assert method == "eth_getLogs"
        flt = params[0]
        assert flt["address"] == books.SUBACCOUNTS and flt["topics"][0] == books.T_BALANCE_ADJUSTED
        acc = int(flt["topics"][1], 16)
        lo, hi = int(flt["fromBlock"], 16), int(flt["toBlock"], 16)
        self.ranges.append((lo, hi))
        sel = [lg for lg in self.logs if lo <= int(lg["blockNumber"], 16) <= hi and int(lg["topics"][1], 16) == acc]
        if self.limit is not None and len(sel) > self.limit:
            from derive_surface.chainfeeds import RpcError
            raise RpcError({"code": -32005, "message": "query returns more than 10000 results"})
        return sel


def test_fetch_balance_events_splits_on_result_limit():
    ev = _ev_fixture()
    b0, b1 = ev["day_start"]["block"], ev["next_day"]["block"]
    chain = _LogChain(ev["logs"], limit=40)
    rows = books.fetch_balance_events(Rpc(client=chain, rate=1000.0), 4242, b0 + 1, b1)
    assert len(rows) == 109 and len(chain.ranges) > 1
    assert [(r["block"], r["log_index"]) for r in rows] == sorted((r["block"], r["log_index"]) for r in rows)
    chain2 = _NetDownChain()
    with pytest.raises(RuntimeError):
        books.fetch_balance_events(Rpc(client=chain2, rate=1000.0), 4242, b0 + 1, b1)
    assert chain2.n == 1


def test_load_events_resumable_compact_and_index(tmp_path):
    ev, reg, s0, _, _ = _ev_frames()
    chain = _LogChain(ev["logs"])
    rpc = Rpc(client=chain, rate=1000.0)
    st = books.load_events(rpc, [(4242, ev["day"])], out_dir=tmp_path)
    assert st == {"done": 1, "remaining": 0, "total": 1}
    assert chain.ranges == [(ev["day_start"]["block"] + 1, ev["next_day"]["block"])]
    assert books.load_events(rpc, [(4242, ev["day"])], out_dir=tmp_path)["done"] == 0
    df = books.compact_events(tmp_path, path=tmp_path / "events.parquet", registry=reg)
    assert len(df) == 109 and set(df.day) == {pd.Timestamp(ev["day"])}
    assert df.kind.value_counts().to_dict() == {"option": 57, "cash": 52}
    assert (tmp_path / "events.parquet").exists()
    idx = books.OnchainBooks(s0, df, registry=reg)
    tx = ev["fill_tape_row"]["tx_hash"]
    assert idx.locate(4242, tx) == pd.Timestamp(ev["day"])
    got, ref = idx.before(4242, tx), books.onchain_book_before(s0, df, tx, registry=reg)
    assert {leg.key: leg.amount for leg in got["ETH"].options} == {leg.key: leg.amount for leg in ref["ETH"].options}
    with pytest.raises(KeyError):
        idx.before(4242, "0x" + "11" * 32)


def test_perp_drift_counts_day_to_day_changes():
    rows = []
    for day, amt in [("2025-07-01", -1.0), ("2025-07-02", -1.0), ("2025-07-03", -0.5), ("2025-07-05", -0.5),
                     ("2025-07-06", None)]:
        base = dict(subaccount=1, day=pd.Timestamp(day), block=1, manager="0xm", asset="0xp", sub_id="0",
                    expiry=None, strike=None, is_call=None)
        if amt is None:
            rows.append(dict(base, kind="none", ccy=None, amount=0.0))
        else:
            rows.append(dict(base, kind="perp", ccy="ETH", amount=amt))
    out = books.perp_drift(pd.DataFrame(rows))
    r = out.set_index("subaccount").loc[1]
    # pairs: 01->02 same, 02->03 changed, 03->05 not consecutive, 05->06 closed (-0.5 -> 0)
    assert r["day_pairs"] == 3 and r["days_changed"] == 2
    assert r["median_abs_change"] == pytest.approx(0.5)


def test_onchain_before_many_equals_single_replays():
    ev, reg, s0, _, events = _ev_frames()
    idx = books.OnchainBooks(s0, events, registry=reg)
    txs = list(dict.fromkeys(events.sort_values(["block", "log_index"]).tx_hash))
    pick = [txs[0], txs[7], txs[-1]]  # first trade, the 08:00 settlement, the fill
    many = idx.before_many(4242, pick)
    for tx in pick:
        one = books.onchain_book_before(s0, events, tx, registry=reg)
        assert set(many[tx]) == set(one)
        for c in one:
            assert many[tx][c].options == one[c].options and many[tx][c].perp == one[c].perp
    # before the 08:00 settlement the legs expiring at 08:00 are already cut (block time >= expiry)
    settle_blk = int(events.loc[events.tx_hash == txs[7], "block"].min())
    assert all(leg.expiry > ts_at_block(settle_blk) for leg in many[txs[7]]["ETH"].options)


def test_event_days_for_fills_and_gap_filling():
    d = _day_ts("2026-02-13") * 1000
    maker = pd.DataFrame({"subaccount_id": [5, 5, 6], "timestamp": [d + 1, d + 86_399_000, d + 5],
                          "tx_hash": ["0xA", "0xB", "0xC"], "liquidity_role": ["maker"] * 3})
    assert books.event_days_for_fills(maker) == {(5, "2026-02-13"), (6, "2026-02-13")}
    ev = pd.DataFrame({"subaccount": [5, 6], "tx_hash": ["0xa", "0xc"]})
    loaded = {(5, "2026-02-13"), (6, "2026-02-13")}
    # 0xB settled after midnight: look in the next day, then the day after; nothing more once both are loaded
    assert books.missing_fill_days(maker, ev, loaded) == {(5, "2026-02-14")}
    assert books.missing_fill_days(maker, ev, loaded | {(5, "2026-02-14")}) == {(5, "2026-02-15")}
    assert books.missing_fill_days(maker, ev, loaded | {(5, "2026-02-14"), (5, "2026-02-15")}) == set()


def test_compare_tape_vs_chain_on_real_day():
    ev, reg, s0, _, events = _ev_frames()
    row = ev["fill_tape_row"]
    tape = pd.DataFrame([dict(row, subaccount_id=4242)])
    fills = pd.DataFrame([{"maker_sub": 4242, "trade_id": row["trade_id"], "ts_maker": row["timestamp"],
                           "ts": row["timestamp"], "currency": "ETH", "tx_hash": row["tx_hash"]},
                          {"maker_sub": 4242, "trade_id": row["trade_id"], "ts_maker": row["timestamp"],
                           "ts": row["timestamp"] + 4000, "currency": "ETH", "tx_hash": "0x" + "ee" * 32}])
    df = books.compare_tape_vs_chain(s0, events, tape, fills, registry=reg)
    assert list(df.chain_found) == [True, False]
    r = df.iloc[0]
    assert r.options_equal == False and r.perp_equal == True and r.n_diff > 0  # noqa: E712
    assert r.chain_day_differs == False and df.rfq_lag_ms.tolist() == [0, 4000]  # noqa: E712


def test_fetch_balance_events_window_hint_avoids_repeated_failures():
    ev = _ev_fixture()
    b0, b1 = ev["day_start"]["block"], ev["next_day"]["block"]
    chain = _LogChain(ev["logs"], limit=40)
    rpc = Rpc(client=chain, rate=1000.0)
    rows, w = books.fetch_balance_events_windowed(rpc, 4242, b0 + 1, b1, grow_below=10)
    assert len(rows) == 109 and w <= b1 - b0
    n_first = len(chain.ranges)
    assert n_first < 40  # the window grows again after sparse stretches
    ok = [r for r in chain.ranges]
    chain.ranges.clear()
    small = books.fetch_balance_events_windowed(rpc, 4242, b0 + 1, b1, window=2_000, grow_below=10)[0]
    assert small == rows and len(chain.ranges) <= n_first  # a working start window saves refused requests
    assert min(r[0] for r in ok) == b0 + 1 and max(r[1] for r in ok) == b1


def test_verify_event_days_against_next_snapshot():
    ev, reg, s0, s1, events = _ev_frames()
    snaps = pd.concat([s0, s1], ignore_index=True)
    out = books.verify_event_days(snaps, events)
    assert len(out) == 1
    r = out.iloc[0]
    assert r.chain_ok == True and r.exact == True and r.n_events == 109 and r.n_diff == 0  # noqa: E712
    cash = _reg_fixture()["cash_asset"].lower()
    gap = events.drop(index=events.index[events.asset == cash][0])
    r2 = books.verify_event_days(snaps, gap).iloc[0]
    assert r2.chain_ok == False and r2.exact == False  # noqa: E712


# ================================================================ task B3: marginal capital, netting value, holding time

import math  # noqa: E402

import numpy as np  # noqa: E402

from derive_surface import margin_pm, margin_pm2, margin_sm  # noqa: E402
from derive_surface.markpath import mark_from_svi  # noqa: E402
from derive_surface.p2params import Timeline  # noqa: E402
from derive_surface.p2types import YEAR, Book, ExpiryState, MarketState, OptionLeg, capital_from_net  # noqa: E402

B3_TS = _day_ts("2026-01-15") + 1  # first block of a day inside every PM2 window


def _b3_state(ccy: str = "ETH", ts: int = B3_TS, spot: float = 3000.0, n_exp: int = 2, perp: float = None) -> MarketState:
    exps = {}
    for i in range(n_exp):
        e = ts - 1 + 86400 * (7 + 14 * i) + 8 * 3600
        tau = (e - ts) / YEAR
        fwd = spot * (1.0 + 0.001 * (i + 1))
        svi = (0.01 * tau / 0.05, 0.04 * math.sqrt(tau / 0.05) * 0.2, -0.25, 0.01, 0.12, tau)
        exps[e] = ExpiryState(expiry=e, forward=fwd, svi=svi, rate=0.03, svi_fwd=fwd * 0.9995)
    return MarketState(currency=ccy, ts=ts, spot=spot, expiries=exps, perp=perp if perp is not None else spot * 1.0002)


def _b3_params(ccy: str, mgr: str, ts: int = B3_TS) -> dict:
    return Timeline(ccy, mgr).at(ts)


def _b3_book(state: MarketState, perp: float = -1.5) -> Book:
    e1, e2 = sorted(state.expiries)
    s = state.spot
    return Book(options=[OptionLeg(e1, round(s * 1.1, -1), True, -3.0), OptionLeg(e1, round(s * 0.9, -1), False, 2.0),
                         OptionLeg(e2, round(s, -1), True, -1.0), OptionLeg(e2, round(s * 1.2, -1), True, 4.0)],
                perp=perp, perp_entry=None, cash=0.0)


def test_leg_vols_and_mark_b_match_svi_and_paper1_markpath():
    st = _b3_state()
    book = _b3_book(st)
    vols = books.leg_vols(st, book.options)
    for leg in book.options:
        assert vols[(leg.expiry, leg.strike)] == pytest.approx(st.expiries[leg.expiry].vol(leg.strike), rel=1e-14)
    marks = books.mark_b(st, book.options)
    rows = []
    for leg in book.options:
        a, b, rho, m, sig, ref = st.expiries[leg.expiry].svi
        rows.append(dict(expiry=leg.expiry, strike=leg.strike, option_type="C" if leg.is_call else "P", ts=st.ts * 1000,
                         svi_a=a, svi_b=b, svi_rho=rho, svi_m=m, svi_sigma=sig, svi_ref_tau=ref,
                         svi_fwd=st.expiries[leg.expiry].svi_fwd))
    exp = mark_from_svi(pd.DataFrame(rows)).to_numpy()
    assert np.allclose(marks, exp, rtol=1e-13, atol=0)  # Paper 1 mark: Black-76 on SVI_fwd, D = 1


def test_marginal_capital_equals_difference_of_book_capital():
    st = _b3_state()
    prm = _b3_params("ETH", "pm2")
    book = _b3_book(st)
    e1 = min(st.expiries)
    k_new, q_new, p = round(st.spot * 1.05, -1), -2.5, 41.7
    res = books.marginal_capital(book, st, prm, e1, k_new, True, q_new, p)
    net_b = margin_pm2.net_margin(book, st, prm)[0]
    after = Book(options=book.options + [OptionLeg(e1, k_new, True, q_new)], perp=book.perp)
    net_a = margin_pm2.net_margin(after, st, prm)[0]
    assert res["net_before"] == pytest.approx(net_b, rel=1e-12) and res["net_after"] == pytest.approx(net_a, rel=1e-12)
    assert res["dK"] == pytest.approx(p * q_new + net_b - net_a, rel=1e-12)
    # identical to K(after) - K(before) for any marks of the existing legs (they cancel)
    marks = {leg.key: 10.0 + 3.0 * i for i, leg in enumerate(book.options)}
    k_before = capital_from_net(book.premium(marks), net_b)
    k_after = capital_from_net(book.premium(marks) + p * q_new, net_a)
    assert res["dK"] == pytest.approx(k_after - k_before, rel=1e-12)
    # MM and the book's own perp enter; cash is always zero
    mm = books.marginal_capital(book, st, prm, e1, k_new, True, q_new, p, is_initial=False)
    assert mm["dK"] != res["dK"]
    rich = Book(options=book.options, perp=book.perp, cash=5e6)
    assert books.marginal_capital(rich, st, prm, e1, k_new, True, q_new, p)["dK"] == pytest.approx(res["dK"], rel=1e-12)
    # a precomputed net(before) is used as given
    assert books.marginal_capital(book, st, prm, e1, k_new, True, q_new, p, net_before=net_b)["dK"] == \
        pytest.approx(res["dK"], rel=1e-12)


def test_marginal_capital_on_empty_book_is_the_single_contract_capital():
    st = _b3_state()
    prm = _b3_params("ETH", "pm2")
    e = max(st.expiries)
    es = st.expiries[e]
    for k, call, q, p in [(3300.0, True, -1.0, 55.0), (2700.0, False, 1.0, 30.0), (3000.0, True, -4.0, 120.0)]:
        res = books.marginal_capital(None, st, prm, e, k, call, q, p)
        assert res["net_before"] == 0.0
        arrays = dict(spot=st.spot, forward=es.forward, sigma=es.vol(k), tau=(e - st.ts) / YEAR, rate=es.rate,
                      strike=k, is_call=call, amount=np.sign(q), vol_conf=1.0, fwd_conf=1.0, spot_conf=1.0)
        net1 = margin_pm2.single({kk: np.atleast_1d(v) for kk, v in arrays.items()}, prm)[0][0]
        k_single = p * np.sign(q) - net1  # per contract, as B2
        assert res["dK"] / abs(q) == pytest.approx(k_single, rel=1e-9)


def test_marginal_capital_nets_the_same_instrument():
    st = _b3_state()
    prm = _b3_params("ETH", "pm2")
    book = _b3_book(st, perp=0.0)
    leg = book.options[0]  # short 3 calls; buying 3 closes the leg
    res = books.marginal_capital(book, st, prm, leg.expiry, leg.strike, leg.is_call, 3.0, 20.0)
    rest = Book(options=book.options[1:])
    assert res["net_after"] == pytest.approx(margin_pm2.net_margin(rest, st, prm)[0], rel=1e-12)


def test_filter_pm2_window_keeps_only_open_windows():
    bk = Book(options=[OptionLeg(1_800_000_000, 1.0, True, 1.0)])
    books_in = {"BTC": bk, "ETH": bk, "HYPE": bk, "SOL": bk}
    assert books.PM2_WINDOW_START == {"BTC": 1_749_769_200, "ETH": 1_749_769_200, "HYPE": 1_762_819_200}
    assert set(books.filter_pm2_window(books_in, _day_ts("2025-06-12") + 1)) == set()
    assert set(books.filter_pm2_window(books_in, 1_749_769_200)) == {"BTC", "ETH"}
    assert set(books.filter_pm2_window(books_in, _day_ts("2025-11-10") + 1)) == {"BTC", "ETH"}
    assert set(books.filter_pm2_window(books_in, _day_ts("2025-11-11") + 1)) == {"BTC", "ETH", "HYPE"}
    assert books.pm2_window_open("HYPE", 1_762_819_200) and not books.pm2_window_open("HYPE", 1_762_819_199)
    assert not books.pm2_window_open("SOL", B3_TS)


def _b3_day_inputs():
    sb, se = _b3_state("BTC", spot=90000.0), _b3_state("ETH")
    books_in = {"BTC": _b3_book(sb, perp=0.2), "ETH": _b3_book(se)}
    states = {"BTC": sb, "ETH": se}
    params = {m: {c: _b3_params(c, m) for c in ("BTC", "ETH")} for m in ("sm", "pm", "pm2")}
    return books_in, states, params


def test_maker_day_capital_per_currency_and_summed():
    books_in, states, params = _b3_day_inputs()
    out = books.maker_day_capital(books_in, states, params)
    for ccy in ("BTC", "ETH"):
        bk, st = books_in[ccy], states[ccy]
        prem = float(np.dot(books.mark_b(st, bk.options), [leg.amount for leg in bk.options]))
        assert out[f"premium_{ccy}"] == pytest.approx(prem, rel=1e-12)
        exp = {"pm2": prem - margin_pm2.net_margin(bk, st, params["pm2"][ccy])[0],
               "pm": prem - margin_pm.net_margin(bk, st, params["pm"][ccy])[0],
               "sm": prem - margin_sm.net_margin(bk, st, params["sm"][ccy])[0]}
        for mgr, v in exp.items():
            assert out[f"K_{mgr}_{ccy}"] == pytest.approx(v, rel=1e-12)
        assert out[f"K_pm2_mm_{ccy}"] == pytest.approx(prem - margin_pm2.net_margin(bk, st, params["pm2"][ccy], False)[0],
                                                       rel=1e-12)
    for col in ("K_sm", "K_pm", "K_pm2", "K_sm_mm", "K_pm_mm", "K_pm2_mm"):
        assert out[col] == pytest.approx(out[col + "_BTC"] + out[col + "_ETH"], rel=1e-12)
    # PM2 does not net across currencies: the sum differs from one joint book is impossible to form, but each
    # currency is its own portfolio, so moving the ETH book does not change the BTC part
    only_btc = books.maker_day_capital({"BTC": books_in["BTC"]}, states, params)
    assert only_btc["K_pm2"] == pytest.approx(out["K_pm2_BTC"], rel=1e-12)
    assert out["n_legs"] == 8 and out["gross_contracts"] == pytest.approx(20.0)
    assert out["perp_gross"] == pytest.approx(1.7) and out["ccys"] == "BTC,ETH"
    assert out["K_pm2"] >= out["K_pm2_mm"]  # IM binds more capital than MM for this short book


def test_maker_day_capital_legacy_pm_nan_on_too_many_expiries_and_without_btc_eth():
    books_in, states, params = _b3_day_inputs()
    st = _b3_state("BTC", spot=90000.0, n_exp=int(params["pm"]["BTC"]["maxExpiries"]) + 1)
    legs = [OptionLeg(e, 90000.0, True, -1.0) for e in sorted(st.expiries)]
    out = books.maker_day_capital({"BTC": Book(options=legs), "ETH": books_in["ETH"]}, {"BTC": st, "ETH": states["ETH"]},
                                  params)
    assert math.isnan(out["K_pm_BTC"]) and math.isnan(out["K_pm"]) and math.isnan(out["K_pm_mm"])
    assert not math.isnan(out["K_pm_ETH"]) and out["pm_too_many_expiries"] is True
    assert math.isfinite(out["K_sm"]) and math.isfinite(out["K_pm2"])
    hs = _b3_state("HYPE", spot=40.0)
    hp = {"sm": {"HYPE": _b3_params("HYPE", "sm")}, "pm": {}, "pm2": {"HYPE": _b3_params("HYPE", "pm2")}}
    out_h = books.maker_day_capital({"HYPE": _b3_book(hs, perp=0.0)}, {"HYPE": hs}, hp)
    assert math.isnan(out_h["K_pm"]) and out_h["n_legs_pm"] == 0 and math.isfinite(out_h["K_pm2"])


def test_maker_day_capital_nan_when_a_leg_has_no_vol():
    books_in, states, params = _b3_day_inputs()
    st = states["ETH"]
    e1 = min(st.expiries)
    exps = dict(st.expiries)
    exps[e1] = ExpiryState(expiry=e1, forward=exps[e1].forward, svi=None)
    bad = MarketState(currency="ETH", ts=st.ts, spot=st.spot, expiries=exps, perp=st.perp)
    out = books.maker_day_capital({"ETH": books_in["ETH"]}, {"ETH": bad}, params)
    assert out["status"] == "no_state" and math.isnan(out["K_pm2"]) and math.isnan(out["K_sm"])


def _b3_markouts():
    d = _day_ts("2025-12-01") * 1000
    rows = []
    for i, (sub, ccy, t) in enumerate([(1, "ETH", d + 1000), (1, "ETH", d + 500), (2, "ETH", d + 2000),
                                       (3, "ETH", d + 3000), (1, "HYPE", d + 4000), (1, "ETH", d - 86_400_000 * 200),
                                       (1, "ETH", d + 86_400_000), (9, "ETH", d + 5000)]):
        rows.append(dict(trade_id=f"t{i}", ts=t + 10, ts_maker=t, currency=ccy, maker_sub=sub))
    return pd.DataFrame(rows)


def _b3_snaps():
    rows = []
    for sub, lab in [(1, "PM2:ETH"), (2, "SM"), (3, "PM:ETH"), (9, "PM2:ETH")]:
        for day in ("2025-05-15", "2025-12-01"):
            rows.append(dict(subaccount=sub, day=pd.Timestamp(day), manager_label=lab))
    return pd.DataFrame(rows)


def test_h2_population_filters_accounts_manager_and_window():
    pop = books.h2_population(_b3_markouts(), _b3_snaps(), top=[1, 2, 3])
    # t5: before the ETH PM2 window; t6: no day-start snapshot (not under PM2 at 00:00); t7: not a top account
    assert pop["trade_id"].tolist() == ["t1", "t0", "t4"]  # sorted by (ts, trade_id)
    assert (pop["day_manager"] == "PM2:ETH").all()


def test_h2_sample_is_a_seeded_simple_random_sample():
    pop = pd.DataFrame({"trade_id": [f"x{i:03d}" for i in range(50)], "ts": np.arange(50)})
    s = books.h2_sample(pop, n=7, seed=20260924)
    idx = np.sort(np.random.default_rng(20260924).choice(50, size=7, replace=False))
    assert s["trade_id"].tolist() == pop["trade_id"].iloc[idx].tolist()
    assert books.h2_sample(pop, n=7, seed=20260924)["trade_id"].tolist() == s["trade_id"].tolist()
    assert len(books.h2_sample(pop, n=80)) == 50
    assert books.H2_N == 20_000 and books.H2_SEED == 20260924


# ---------------------------------------------------------------- FIFO holding time

H = 3_600_000
INST = ("ETH", 1_800_000_000, 3000.0, True)


def _pieces(inv) -> list:
    return [(p[0], p[1], p[2], round(p[3], 9), p[4]) for p in inv.pieces]


def test_fifo_closes_oldest_lots_first_and_opens_the_remainder():
    inv = books.FifoInventory()
    assert inv.trade(INST, 0, 2.0, "A") == 2.0
    assert inv.trade(INST, 1 * H, 1.0, "B") == 1.0
    assert inv.trade(INST, 3 * H, -2.5, "C") == 0.0  # closes A fully and half of B
    assert _pieces(inv) == [("A", 0, 3 * H, 2.0, "fill"), ("B", H, 3 * H, 0.5, "fill")]
    assert inv.position(INST) == pytest.approx(0.5)
    assert inv.trade(INST, 4 * H, -1.5, "D") == pytest.approx(1.0)  # closes the rest of B, opens -1 for D
    assert _pieces(inv)[-1] == ("B", H, 4 * H, 0.5, "fill") and inv.position(INST) == pytest.approx(-1.0)


def test_fifo_expiry_transfer_and_censoring():
    inv = books.FifoInventory()
    other = ("ETH", 1_900_000_000, 3000.0, False)
    inv.trade(INST, 0, -2.0, "A")
    inv.trade(other, 0, 1.0, "B")
    inv.set_position(INST, 2 * H, -0.5)  # 1.5 moved away (transfer), closed FIFO
    inv.set_position(other, 2 * H, 3.0)  # 2 appeared: new lot of unknown origin
    assert _pieces(inv) == [("A", 0, 2 * H, 1.5, "transfer")]
    inv.expire(INST[1] * 1000 + 5)  # INST expired: closed at its expiry, other still open
    assert _pieces(inv)[-1] == ("A", 0, INST[1] * 1000, 0.5, "expiry")
    inv.close_all(1_850_000_000_000)
    assert ("B", 0, 1_850_000_000_000, 1.0, "censored") in _pieces(inv)
    assert all(p[0] is not None for p in inv.pieces)  # lots without a maker fill are not recorded
    assert inv.position(other) == 0.0


def test_fifo_account_reconciles_to_day_start_snapshots():
    day0, day1 = _day_ts("2025-07-01"), _day_ts("2025-07-02")
    e = _day_ts("2025-07-10") + 8 * 3600
    inst = ("ETH", e, 3000.0, True)
    snaps = pd.DataFrame([
        dict(subaccount=5, day=pd.Timestamp("2025-07-01"), kind="option", ccy="ETH", expiry=e, strike=3000.0,
             is_call=True, amount=1.0),
        dict(subaccount=5, day=pd.Timestamp("2025-07-02"), kind="option", ccy="ETH", expiry=e, strike=3000.0,
             is_call=True, amount=0.0 + 2.0),  # tape says 1 - 2 + 0 = -1 ... +3 transferred in
        dict(subaccount=5, day=pd.Timestamp("2025-07-02"), kind="option", ccy="SOL", expiry=e, strike=100.0,
             is_call=True, amount=5.0),
    ])
    tape = pd.DataFrame([
        dict(trade_id="m1", timestamp=day0 * 1000 + 2 * H, direction="sell", liquidity_role="maker", trade_amount=2.0,
             subaccount_id=5, currency="ETH", expiry=e, strike=3000.0, option_type="C"),
        dict(trade_id="t1", timestamp=day0 * 1000 + 5 * H, direction="buy", liquidity_role="taker", trade_amount=0.5,
             subaccount_id=5, currency="ETH", expiry=e, strike=3000.0, option_type="C"),
        dict(trade_id="m2", timestamp=day1 * 1000 + 3 * H, direction="sell", liquidity_role="maker", trade_amount=1.0,
             subaccount_id=5, currency="ETH", expiry=e, strike=3000.0, option_type="C"),
    ])
    pieces, opened = books.fifo_account(tape, snaps, end_ms=_day_ts("2025-07-05") * 1000)
    assert opened == {"m1": pytest.approx(1.0), "m2": pytest.approx(0.0)}
    got = sorted((r.key, r.open_ms, r.close_ms, round(r.qty, 9), r.how) for r in pieces.itertuples())
    s1 = (day1 + 1) * 1000
    # day 1: snapshot 1 (legacy lot); m1 sells 2: closes legacy 1, opens -1 (m1); t1 buys 0.5: closes 0.5 of m1;
    # day 2 snapshot +2 vs FIFO -0.5: +2.5 transfer closes m1's 0.5 and opens +2 unknown; m2 sells 1 against it
    assert got == [("m1", day0 * 1000 + 2 * H, day0 * 1000 + 5 * H, 0.5, "fill"),
                   ("m1", day0 * 1000 + 2 * H, s1, 0.5, "transfer")]
    ht = books.fill_holding_times(pieces, opened)
    r = ht.set_index("trade_id").loc["m1"]
    assert r.q_open == pytest.approx(1.0)
    assert r.ht_days == pytest.approx((0.5 * 3 * H + 0.5 * (s1 - day0 * 1000 - 2 * H)) / 1.0 / 86_400_000)
    assert r.ht_days_excl_transfer == pytest.approx(3 * H / 86_400_000)
    assert r.c_fill == pytest.approx(0.5) and r.c_transfer == pytest.approx(0.5) and r.c_censored == 0.0
    assert "m2" not in set(ht["trade_id"])  # m2 opened nothing


def test_weighted_median_and_holding_cells():
    assert books.weighted_median([1.0, 2.0, 10.0], [1.0, 1.0, 5.0]) == 10.0
    assert books.weighted_median([1.0, 2.0, 10.0], [3.0, 1.0, 1.0]) == 1.0
    assert math.isnan(books.weighted_median([], []))
    fills = pd.DataFrame(dict(trade_id=["a", "b", "c", "d"], currency="ETH", maker_side=[-1, -1, -1, 1],
                              delta_bucket="10-25", tenor_bucket="7-30d",
                              ts=[1_700_000_000_000, 1_760_000_000_000, 1_760_000_000_001, 1_760_000_000_002]))
    ht = pd.DataFrame(dict(trade_id=["a", "b", "d"], q_open=[1.0, 3.0, 2.0], ht_days=[1.0, 5.0, 2.0],
                           ht_days_excl_transfer=[1.0, np.nan, 2.0], c_fill=[1.0, 1.0, 0.0], c_expiry=[0.0, 0.0, 2.0],
                           c_transfer=[0.0, 2.0, 0.0], c_censored=[0.0, 0.0, 0.0]))
    pieces = pd.DataFrame(dict(key=["a", "b", "b", "d"], qty=[1.0, 1.0, 2.0, 2.0], days=[1.0, 2.0, 6.5, 2.0],
                               how=["fill", "fill", "transfer", "expiry"]))
    cells = books.holding_cells(fills, ht, pieces)
    row = cells[(cells.window == "all") & (cells.side == "sell")].iloc[0]
    assert row.n_fills == 3 and row.n_opening == 2 and row.median_days == pytest.approx(3.0)
    assert row.median_days_w == pytest.approx(2.0)  # 1 + 1 + 2 contracts: lower weighted median
    assert row.share_transfer == pytest.approx(2.0 / 4.0) and row.share_fill == pytest.approx(2.0 / 4.0)
    pm2 = cells[(cells.window == "pm2") & (cells.side == "sell")].iloc[0]
    assert pm2.n_fills == 2 and pm2.n_opening == 1  # fill a lies before the ETH PM2 window
    assert set(cells.columns) >= {"window", "ccy", "side", "delta_bucket", "tenor_bucket", "n_fills", "n_opening",
                                  "median_days", "median_days_w", "median_days_excl_transfer", "share_fill",
                                  "share_expiry", "share_transfer", "share_censored"}


def test_fill_marginal_combines_chain_tape_unit_mm_and_single():
    st = _b3_state()
    prm_acct = dict(_b3_params("ETH", "pm2"))
    prm_std = _b3_params("ETH", "pm2")
    chain = _b3_book(st)
    tape = Book(options=chain.options[:2], perp=-1.0)
    e = max(st.expiries)
    k, q, p = 3150.0, -2.0, 60.0
    r = books.fill_marginal(chain, tape, st, prm_acct, prm_std, e, k, True, q, p)
    assert r["status"] == "ok" and r["tape_ok"] is True
    assert r["dK"] == pytest.approx(books.marginal_capital(chain, st, prm_acct, e, k, True, q, p)["dK"], rel=1e-12)
    assert r["dK_mm"] == pytest.approx(
        books.marginal_capital(chain, st, prm_acct, e, k, True, q, p, is_initial=False)["dK"], rel=1e-12)
    assert r["dK_unit"] == pytest.approx(books.marginal_capital(chain, st, prm_acct, e, k, True, -1.0, p)["dK"], rel=1e-12)
    assert r["dK_tape"] == pytest.approx(books.marginal_capital(tape, st, prm_acct, e, k, True, q, p)["dK"], rel=1e-12)
    assert r["K_single_book"] == pytest.approx(books.marginal_capital(None, st, prm_std, e, k, True, -1.0, p)["dK"],
                                               rel=1e-12)
    assert r["n_legs_before"] == 4 and r["gross_before"] == pytest.approx(10.0) and r["perp_before"] == -1.5
    assert r["n_legs_tape"] == 2 and r["perp_tape"] == -1.0
    # no position in this currency before the fill: dK is the single-contract capital times |q|
    r0 = books.fill_marginal(None, None, st, prm_std, prm_std, e, k, True, q, p)
    assert r0["dK"] == pytest.approx(abs(q) * r0["K_single_book"], rel=1e-12)
    assert r0["tape_ok"] is False and math.isnan(r0["dK_tape"])
    exps = dict(st.expiries)
    exps[e] = ExpiryState(expiry=e, forward=exps[e].forward, svi=None)
    bad = MarketState(currency="ETH", ts=st.ts, spot=st.spot, expiries=exps, perp=st.perp)
    rb = books.fill_marginal(chain, tape, bad, prm_acct, prm_std, e, k, True, q, p)
    assert rb["status"] == "no_state" and math.isnan(rb["dK"])


def _b3_acct_params(mm_factor: float = 0.35) -> dict:
    """An override lib as on chain: the standard parameters with another mmFactor (C5a)."""
    import copy

    prm = copy.deepcopy(_b3_params("ETH", "pm2"))
    assert prm["MarginParameters"]["mmFactor"] != mm_factor
    prm["MarginParameters"]["mmFactor"] = mm_factor
    return prm


def test_fill_marginal_mm_libs_one_lib_per_ratio():
    """C5a: MM numerator and denominator come from the same lib, once the account's and once the standard lib."""
    st = _b3_state()
    prm_acct, prm_std = _b3_acct_params(), _b3_params("ETH", "pm2")
    chain = _b3_book(st)
    e = max(st.expiries)
    k, q, p = 3150.0, -2.0, 60.0
    leg = (e, k, True)
    r = books.fill_marginal(chain, None, st, prm_acct, prm_std, *leg, q, p)
    mc = books.marginal_capital
    assert r["dK_mm_std"] == pytest.approx(mc(chain, st, prm_std, *leg, q, p, is_initial=False)["dK"], rel=1e-12)
    assert r["dK_mm"] == pytest.approx(mc(chain, st, prm_acct, *leg, q, p, is_initial=False)["dK"], rel=1e-12)
    assert r["dK_mm"] != pytest.approx(r["dK_mm_std"], rel=1e-6)
    assert r["K_single_book_mm_acct"] == pytest.approx(mc(None, st, prm_acct, *leg, -1.0, p, is_initial=False)["dK"],
                                                       rel=1e-12)
    assert r["K_single_book_mm"] == pytest.approx(mc(None, st, prm_std, *leg, -1.0, p, is_initial=False)["dK"],
                                                  rel=1e-12)
    # IM does not use mmFactor: the account lib gives the standard single-contract IM capital bit for bit
    assert r["K_single_book_acct"] == r["K_single_book"]
    # empty book: each consistent MM ratio is exactly 1, the mixed one (account dK_mm / standard K_single_mm) is not
    r0 = books.fill_marginal(None, None, st, prm_acct, prm_std, *leg, q, p)
    assert r0["dK_mm"] / abs(q) / r0["K_single_book_mm_acct"] == pytest.approx(1.0, rel=1e-12)
    assert r0["dK_mm_std"] / abs(q) / r0["K_single_book_mm"] == pytest.approx(1.0, rel=1e-12)
    assert r0["dK_mm"] / abs(q) / r0["K_single_book_mm"] != pytest.approx(1.0, rel=1e-3)


def test_fill_marginal_standard_lib_account_copies_and_no_state_is_nan():
    st = _b3_state()
    prm_std = _b3_params("ETH", "pm2")
    chain = _b3_book(st)
    e = max(st.expiries)
    r = books.fill_marginal(chain, None, st, prm_std, prm_std, e, 3150.0, True, -2.0, 60.0)
    assert r["dK_mm_std"] == r["dK_mm"]
    assert r["K_single_book_mm_acct"] == r["K_single_book_mm"]
    assert r["K_single_book_acct"] == r["K_single_book"]
    exps = dict(st.expiries)
    exps[e] = ExpiryState(expiry=e, forward=exps[e].forward, svi=None)
    bad = MarketState(currency="ETH", ts=st.ts, spot=st.spot, expiries=exps, perp=st.perp)
    rb = books.fill_marginal(chain, None, bad, _b3_acct_params(), prm_std, e, 3150.0, True, -2.0, 60.0)
    for key in ("dK_mm_std", "K_single_book_mm_acct", "K_single_book_acct"):
        assert math.isnan(rb[key]), key


def test_combine_marginal_mm_ratios_use_one_lib(tmp_path, monkeypatch):
    """marginal.parquet: ratio_mm = account lib in both, ratio_mm_std = standard lib in both; IM columns untouched."""
    st = _b3_state()
    prm_acct, prm_std = _b3_acct_params(), _b3_params("ETH", "pm2")
    chain = _b3_book(st)
    e = max(st.expiries)
    rows = []
    for i, (book, prm, lib, q) in enumerate([(chain, prm_acct, "0xacc", -2.0), (None, prm_acct, "0xacc", 3.0),
                                             (chain, prm_std, "std", 1.5), (None, prm_std, "std", -1.0)]):
        r = books.fill_marginal(book, None, st, prm, prm_std, e, 3150.0, True, q, 60.0)
        t_ms = (st.ts + (3 - i)) * 1000         # reverse time order: combine_marginal re-sorts the rows
        rows.append({"fill_key": f"t{i}", "subaccount": 4242, "ts": t_ms, "ts_maker": t_ms,
                     "block_ts": st.ts, "ccy": "ETH", "manager": "pm2", "lib": lib, "amount": abs(q), "q": q, **r})
    parts = tmp_path / "parts"
    parts.mkdir()
    pd.DataFrame(rows).to_parquet(parts / "ETH_2026-01.parquet")
    one = {i: books.fill_marginal(None, None, st, prm_std, prm_std, e, 3150.0, True, -1.0 if r["q"] < 0 else 1.0,
                                  60.0) for i, r in enumerate(rows)}
    cap = pd.DataFrame({"trade_id": [r["fill_key"] for r in rows],
                        "K_pm2": [one[i]["K_single_book"] for i in range(len(rows))],
                        "K_pm2_mm": [one[i]["K_single_book_mm"] for i in range(len(rows))]})
    cap.to_parquet(tmp_path / "capital.parquet")
    monkeypatch.setattr(books, "_labels", lambda subs: {int(s): "M3" for s in subs})
    df, check = books.combine_marginal(parts, tmp_path / "marginal.parquet", tmp_path / "capital.parquet")
    df = df.set_index("fill_key")
    a = df["amount"]
    assert (df["dK_mm_std_per_contract"] == df["dK_mm_std"] / a).all()
    assert (df["K_single_pm2_mm_acct"] == df["K_single_book_mm_acct"]).all()
    assert np.allclose(df["ratio_mm"], df["dK_mm_per_contract"] / df["K_single_pm2_mm_acct"], rtol=0, atol=0)
    assert np.allclose(df["ratio_mm_std"], df["dK_mm_std_per_contract"] / df["K_single_pm2_mm"], rtol=0, atol=0)
    assert np.allclose(df["ratio"], df["dK_per_contract"] / df["K_single_pm2"], rtol=0, atol=0)
    # empty books: both consistent MM ratios are 1
    assert df.loc["t1", "ratio_mm"] == pytest.approx(1.0, rel=1e-12)
    assert df.loc["t1", "ratio_mm_std"] == pytest.approx(1.0, rel=1e-12)
    assert df.loc["t3", "ratio_mm"] == pytest.approx(1.0, rel=1e-12)
    # standard-lib fills: both variants coincide
    assert df.loc["t2", "ratio_mm"] == df.loc["t2", "ratio_mm_std"]
    assert df.loc["t0", "ratio_mm"] != pytest.approx(df.loc["t0", "ratio_mm_std"], rel=1e-6)
    assert check["fills_account_lib"] == 2
    assert check["single_im_acct_vs_std_max_abs"] == 0.0
    assert check["single_mm_acct_vs_b2_std_lib_max_abs"] == 0.0
    assert check["dK_mm_std_vs_dK_mm_std_lib_max_abs"] == 0.0
    assert check["empty_book_dK_mm_vs_single_mm_acct_max_abs"] == pytest.approx(0.0, abs=1e-9)


def test_maker_day_list_uses_maker_rows_of_top_accounts_in_the_pm2_window():
    d = _day_ts("2025-06-13") * 1000
    m = pd.DataFrame(dict(maker_sub=[1, 1, 1, 2, 9, 1],
                          ts_maker=[d + 5, d + 9, d - 3_600_000, d + 86_400_000 * 2, d + 5, _day_ts("2026-10-01") * 1000]))
    out = books.maker_day_list(m, top=[1, 2])
    assert list(zip(out["subaccount"], out["day"].dt.strftime("%Y-%m-%d"))) == [(1, "2025-06-13"), (2, "2025-06-15")]
