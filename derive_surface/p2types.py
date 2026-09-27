"""Shared types for Paper 2 (capital-adjusted edge on Derive).

Every margin engine (``margin_sm``, ``margin_pm``, ``margin_pm2``) takes a :class:`Book` and a
:class:`MarketState` and returns the net margin ``net = cash + V - R`` in USD, exactly like
``public/get_margin`` and the v2-core managers (see ``docs/paper2/get_margin_semantics.md``).
The comparable capital of a book traded at prices ``p`` is ``K_p = sum(p q) - net(q; cash = 0)``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

YEAR = 365.0 * 86400.0


@dataclass(frozen=True)
class ExpiryState:
    """Feed state of one expiry: forward, SVI curve ``(a, b, rho, m, sigma, ref_tau)`` and rate."""

    expiry: int
    forward: float
    svi: Optional[Tuple[float, float, float, float, float, float]]
    rate: float = 0.0
    vol_conf: float = 1.0
    fwd_conf: float = 1.0
    svi_fwd: Optional[float] = None  # forward the SVI curve was fitted on; defaults to ``forward``

    def vol(self, strike: float) -> float:
        """Implied vol at ``strike`` as the Lyra vol feed returns it: sqrt(w(k) / ref_tau)."""
        if self.svi is None:
            raise ValueError(f"no SVI curve for expiry {self.expiry}")
        from .chainfeeds import svi_vol  # exact LyraVolFeed.getVol (moneyness clip, w cap)

        a, b, rho, m, sig, ref_tau = self.svi
        f = self.svi_fwd if self.svi_fwd is not None else self.forward
        return float(svi_vol(strike, a, b, rho, m, sig, f, ref_tau))


@dataclass(frozen=True)
class MarketState:
    currency: str
    ts: int
    spot: float
    expiries: Dict[int, ExpiryState]
    perp: Optional[float] = None
    stable: float = 1.0
    spot_conf: float = 1.0
    perp_conf: float = 1.0

    def tau(self, expiry: int) -> float:
        return max(expiry - self.ts, 0) / YEAR

    @property
    def perp_price(self) -> float:
        return self.perp if self.perp is not None else self.spot


@dataclass(frozen=True)
class OptionLeg:
    expiry: int
    strike: float
    is_call: bool
    amount: float  # contracts, positive = long

    @property
    def key(self) -> Tuple[int, float, bool]:
        return (self.expiry, self.strike, self.is_call)


@dataclass
class Book:
    options: List[OptionLeg] = field(default_factory=list)
    perp: float = 0.0
    perp_entry: Optional[float] = None  # None = entry at the engine's perp price (no unrealised PnL)
    cash: float = 0.0

    def expiries(self) -> List[int]:
        return sorted({leg.expiry for leg in self.options})

    def premium(self, prices: Dict[Tuple[int, float, bool], float]) -> float:
        """sum p q over the option legs (perps carry no premium)."""
        return sum(prices[leg.key] * leg.amount for leg in self.options)


def capital_from_net(premium: float, net_zero_cash: float) -> float:
    """K_p = sum p q - net(q; cash = 0): the deposit needed to open the book at prices p."""
    return premium - net_zero_cash
