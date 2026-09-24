"""Pseudonymous account labels for Paper 2 (pre-registration, addendum 1, item 4).

Subaccounts appear in ``results/``, in ``docs/paper2/`` and in the paper only as labels:

* ``M1`` .. ``M10``: the ten dominant maker subaccounts, ranked by maker fills in the Paper 1 sample
  (``data/p1/derived/markouts.parquet``, ties by smaller id; same rule as ``books.top_maker_subaccounts``);
* ``X`` + the first 10 hex digits of ``HMAC-SHA256(salt, str(id))`` for every other account.

The salt is 32 random bytes, stored hex encoded in ``data/p2/secret_salt.txt`` (git-ignored). It is created once
(``create_salt`` or ``python3 -m derive_surface p2 ids salt``) and never overwritten. ``label`` never creates it, so a
missing salt is an error instead of silently producing different labels. An unsalted ``sha256(str(id))[:10]`` of a
small subaccount id is reversible by enumeration and is not used any more.

Raw ids stay under ``data/p2``; code that writes to ``results/`` or ``docs/`` labels at export with ``label`` or
``labels``.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import numbers
import os
import secrets
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SALT_PATH = REPO / "data" / "p2" / "secret_salt.txt"
MARKOUTS = REPO / "data" / "p1" / "derived" / "markouts.parquet"
TOP_MAKERS = REPO / "data" / "p2" / "books" / "top_makers.json"  # written by ``books top`` (A5)
N_TOP = 10
SALT_BYTES = 32


# ---------------------------------------------------------------- salt

def create_salt(path: Optional[Path] = None) -> bool:
    """Write a new random salt to ``path`` unless the file exists; returns whether it was created."""
    path = Path(path) if path is not None else SALT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w") as fh:
        fh.write(secrets.token_hex(SALT_BYTES) + "\n")
    return True


def load_salt(path: Optional[Path] = None) -> bytes:
    path = Path(path) if path is not None else SALT_PATH
    if not path.exists():
        raise FileNotFoundError(f"salt file {path} is missing; create it once with p2ids.create_salt() "
                                f"(python3 -m derive_surface p2 ids salt). A new salt changes every X label.")
    text = path.read_text().strip()
    try:
        salt = bytes.fromhex(text)
    except ValueError:
        raise ValueError(f"salt file {path} is not hex encoded") from None
    if len(salt) != SALT_BYTES:
        raise ValueError(f"salt file {path} holds {len(salt)} bytes, expected {SALT_BYTES}")
    return salt


# ---------------------------------------------------------------- ranking

def ranking_from_markouts(markouts: pd.DataFrame, n: int = N_TOP) -> List[int]:
    """Subaccounts with the most maker fills (ties by smaller id), as in ``books.top_maker_subaccounts``."""
    from .books import top_maker_subaccounts  # lazy: books imports the chain client

    return top_maker_subaccounts(n, markouts)


def _read_top_makers(path: Path) -> Optional[List[int]]:
    if not path.exists():
        return None
    return [int(x) for x in json.loads(path.read_text())["subaccounts"]]


# ---------------------------------------------------------------- labels

def _account_id(subaccount) -> int:
    if isinstance(subaccount, (bool,)) or subaccount is None:
        raise TypeError(f"not a subaccount id: {subaccount!r}")
    if isinstance(subaccount, str):
        if not subaccount.strip().isdigit():
            raise ValueError(f"not a subaccount id: {subaccount!r}")
        return int(subaccount)
    if not isinstance(subaccount, numbers.Integral):
        raise TypeError(f"not a subaccount id: {subaccount!r}")
    x = int(subaccount)
    if x < 0:
        raise ValueError(f"not a subaccount id: {subaccount!r}")
    return x


class Labeler:
    """``label(id)``: ``M<rank>`` for the first ``N_TOP`` entries of ``ranking``, else ``X`` + HMAC-SHA256[:10]."""

    def __init__(self, ranking: Sequence[int], salt: bytes):
        if len(salt) != SALT_BYTES:
            raise ValueError(f"salt must be {SALT_BYTES} bytes")
        ids = [_account_id(x) for x in ranking]
        if len(set(ids)) != len(ids):
            raise ValueError("ranking contains an account twice")
        self.ranking = ids[:N_TOP]
        self._rank = {x: i + 1 for i, x in enumerate(self.ranking)}
        self._salt = bytes(salt)

    def hmac_label(self, subaccount) -> str:
        x = _account_id(subaccount)
        return "X" + hmac.new(self._salt, str(x).encode(), hashlib.sha256).hexdigest()[:10]

    def label(self, subaccount) -> str:
        x = _account_id(subaccount)
        r = self._rank.get(x)
        return f"M{r}" if r is not None else self.hmac_label(x)

    def labels(self, subaccounts: Iterable) -> List[str]:
        cache = {}
        out = []
        for s in subaccounts:
            x = _account_id(s)
            if x not in cache:
                cache[x] = self.label(x)
            out.append(cache[x])
        return out


_TOP: Optional[List[int]] = None
_LABELER: Optional[Labeler] = None


def reset() -> None:
    """Forget the cached ranking and salt (after the files changed, and in tests)."""
    global _TOP, _LABELER
    _TOP = None
    _LABELER = None


def top_makers() -> List[int]:
    """Ranked top-10 maker subaccounts from ``MARKOUTS``; must agree with ``TOP_MAKERS`` when both exist.

    Without the markouts (e.g. on a machine with only ``data/p2``) the list of the books task is used.
    """
    global _TOP
    if _TOP is None:
        books = _read_top_makers(Path(TOP_MAKERS))
        if Path(MARKOUTS).exists():
            top = ranking_from_markouts(pd.read_parquet(MARKOUTS, columns=["maker_sub"]))
            if books is not None and books != top:
                raise RuntimeError(f"{TOP_MAKERS} ({books}) disagrees with the maker ranking of {MARKOUTS} ({top}); "
                                   "the books were loaded for other accounts: rerun `p2 books top` and the books "
                                   "pipeline, or restore the markouts of the sample")
        elif books is not None:
            top = books
        else:
            raise FileNotFoundError(f"neither {MARKOUTS} nor {TOP_MAKERS} exists: no maker ranking")
        _TOP = top
    return list(_TOP)


def labeler() -> Labeler:
    global _LABELER
    if _LABELER is None:
        _LABELER = Labeler(top_makers(), load_salt(SALT_PATH))
    return _LABELER


def label(subaccount) -> str:
    """Public label of a subaccount: ``M1`` .. ``M10`` or ``X`` + salted HMAC."""
    return labeler().label(subaccount)


def labels(subaccounts: Iterable) -> List[str]:
    return labeler().labels(subaccounts)


# ---------------------------------------------------------------- CLI

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface p2 ids", description="account labels (Paper 2)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("salt", help=f"create the secret salt once (never overwrites {SALT_PATH.name})")
    lb = sub.add_parser("label", help="print the label of each subaccount id (terminal only)")
    lb.add_argument("ids", nargs="+")
    a = ap.parse_args(argv)
    if a.cmd == "salt":
        created = create_salt(SALT_PATH)
        print(f"{SALT_PATH}: {'created' if created else 'exists, left unchanged'}")
        return 0
    for s in a.ids:
        print(s, label(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
