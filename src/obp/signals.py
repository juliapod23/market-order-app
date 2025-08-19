from __future__ import annotations
from typing import Optional, Deque
from collections import deque
from .schemas import FeatureVector, Signal

class ThresholdSignalEngine:
    def __init__(self, imbalance_threshold: float = 0.12, min_update_rate: float = 2.0, confirm_n: int = 2):
        self.imb_th = imbalance_threshold
        self.min_rate = min_update_rate
        self.confirm_n = confirm_n
        self.buf: Deque[str] = deque(maxlen=confirm_n)

    def evaluate(self, fv: FeatureVector) -> Optional[Signal]:
        if fv.update_rate < self.min_rate:
            self.buf.clear()
            return None
        kind = None
        if fv.imbalance > self.imb_th and fv.bid_slope > fv.ask_slope:
            kind = "BUY_PRESSURE"
        elif fv.imbalance < -self.imb_th and fv.ask_slope > fv.bid_slope:
            kind = "SELL_PRESSURE"
        if kind:
            self.buf.append(kind)
            if len(self.buf) == self.buf.maxlen and all(k == kind for k in self.buf):
                self.buf.clear()
                strength = abs(fv.imbalance)
                return Signal(ts=fv.ts, kind=kind, strength=float(strength))
        else:
            self.buf.clear()
        return None
