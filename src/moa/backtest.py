from __future__ import annotations
from collections import deque
from typing import Deque, Optional, Tuple
import numpy as np
from .schemas import BookSnapshot, Signal, Evaluation

class RollingBacktester:
    def __init__(self, tick_size: float = 0.1, horizon_seconds: float = 5.0, exit_on_opposite_signal: bool = False, slippage_ticks: float = 0.0):
        self.tick_size = tick_size
        self.horizon = horizon_seconds
        self.exit_on_opposite = exit_on_opposite_signal
        self.slippage = slippage_ticks
        self.pending: Deque[Tuple[Signal, float]] = deque()  # (signal, entry_mid)

        # Metrics
        self.pnl_ticks_list = []
        self.count_buy = 0
        self.count_sell = 0

    def on_signal(self, snap: BookSnapshot, sig: Signal) -> None:
        entry = snap.mid
        if not np.isfinite(entry):
            return
        # apply slippage at entry
        if sig.kind == "BUY_PRESSURE":
            entry += self.slippage * self.tick_size
            self.count_buy += 1
        else:
            entry -= self.slippage * self.tick_size
            self.count_sell += 1
        self.pending.append((sig, entry))

    def on_snapshot(self, snap: BookSnapshot) -> Optional[Evaluation]:
        # Mature any positions beyond horizon
        if not self.pending:
            return None
        sig, entry = self.pending[0]
        if (snap.ts - sig.ts) >= self.horizon:
            exit_mid = snap.mid
            if not np.isfinite(exit_mid):
                return None
            direction = 1.0 if sig.kind == "BUY_PRESSURE" else -1.0
            pnl_ticks = (exit_mid - entry) * direction / self.tick_size
            self.pnl_ticks_list.append(pnl_ticks)
            self.pending.popleft()
            return Evaluation(ts=snap.ts, signal_kind=sig.kind, entry_mid=float(entry), exit_mid=float(exit_mid), pnl_ticks=float(pnl_ticks))
        return None

    def summary(self) -> dict:
        arr = np.array(self.pnl_ticks_list, dtype=float) if self.pnl_ticks_list else np.array([], dtype=float)
        return {
            "trades": int(arr.size),
            "avg_pnl_ticks": float(arr.mean()) if arr.size else 0.0,
            "win_rate": float((arr > 0).mean()) if arr.size else 0.0,
            "buy_signals": self.count_buy,
            "sell_signals": self.count_sell,
        }
