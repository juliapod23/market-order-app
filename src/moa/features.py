from __future__ import annotations
import numpy as np
from collections import deque
from typing import Deque, List
try:
    from numba import njit
except Exception:  # pragma: no cover
    def njit(*args, **kwargs):
        def wrap(f): return f
        return wrap

from .schemas import BookSnapshot, FeatureVector

@njit(cache=True)
def _sum_depth_side(levels: np.ndarray, upto: int) -> float:
    s = 0.0
    n = min(upto, levels.shape[0])
    for i in range(n):
        s += levels[i,1]
    return s

def compute_imbalance(snapshot: BookSnapshot, depth_levels: int = 5) -> float:
    bid_vol = _sum_depth_side(snapshot.bids, depth_levels)
    ask_vol = _sum_depth_side(snapshot.asks, depth_levels)
    denom = bid_vol + ask_vol
    if denom <= 1e-12:
        return 0.0
    return (bid_vol - ask_vol) / denom

def _slope(levels: np.ndarray) -> float:
    """
    Very simple slope: volume at L1 relative to average of top-L volumes.
    Values >1 mean front-loaded; <1 means back-loaded.
    """
    if levels.shape[0] == 0:
        return 0.0
    v1 = levels[0,1]
    avg = levels[:,1].mean()
    if avg <= 1e-12:
        return 0.0
    return float(v1 / avg)

def compute_update_rate(ts_window: Deque[float]) -> float:
    if len(ts_window) < 2:
        return 0.0
    dts = np.diff(np.array(ts_window, dtype=float))
    mean_dt = float(np.mean(dts)) if dts.size else 0.0
    if mean_dt <= 1e-9:
        return 0.0
    return 1.0 / mean_dt

class FeatureEngine:
    def __init__(self, window_size: int = 20, update_rate_window: int = 30, depth_levels: int = 5):
        self.depth_levels = depth_levels
        self.snaps: Deque[BookSnapshot] = deque(maxlen=window_size)
        self.ts_window: Deque[float] = deque(maxlen=update_rate_window)

    def push(self, snap: BookSnapshot) -> FeatureVector:
        self.snaps.append(snap)
        self.ts_window.append(snap.ts)
        imb = compute_imbalance(snap, self.depth_levels)
        bid_s = _slope(snap.bids[:self.depth_levels])
        ask_s = _slope(snap.asks[:self.depth_levels])
        rate = compute_update_rate(self.ts_window)
        return FeatureVector(ts=snap.ts, imbalance=float(imb), bid_slope=float(bid_s), ask_slope=float(ask_s), update_rate=float(rate))
