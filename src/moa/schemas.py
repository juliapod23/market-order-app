from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np

@dataclass
class BookSnapshot:
    ts: float  # unix timestamp seconds
    bids: np.ndarray  # shape (L, 2): [price, size]
    asks: np.ndarray  # shape (L, 2): [price, size]

    @property
    def best_bid(self) -> float:
        return float(self.bids[0,0]) if self.bids.size else np.nan

    @property
    def best_ask(self) -> float:
        return float(self.asks[0,0]) if self.asks.size else np.nan

    @property
    def mid(self) -> float:
        bb, ba = self.best_bid, self.best_ask
        if np.isfinite(bb) and np.isfinite(ba):
            return (bb + ba) / 2.0
        return np.nan

@dataclass
class FeatureVector:
    ts: float
    imbalance: float
    bid_slope: float
    ask_slope: float
    update_rate: float  # events per second

@dataclass
class Signal:
    ts: float
    kind: str   # "BUY_PRESSURE", "SELL_PRESSURE"
    strength: float

@dataclass
class Evaluation:
    ts: float
    signal_kind: str
    entry_mid: float
    exit_mid: float
    pnl_ticks: float

