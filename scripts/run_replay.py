from __future__ import annotations
import argparse
from pathlib import Path
import csv

from moa.config import load_config
from moa.ingest import ReplayIngestor
from moa.features import FeatureEngine
from moa.signals import ThresholdSignalEngine
from moa.backtest import RollingBacktester

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=str, default="configs/default.yaml")
    p.add_argument("--out", type=str, default="data/tmp/replay_results.csv")
    return p.parse_args()

def main():
    args = parse_args()
    cfg = load_config(args.config)

    ing = ReplayIngestor(cfg.replay["file"], speedup=cfg.replay.get("speedup", 0.0))
    fe = FeatureEngine(window_size=cfg.features["window_size"],
                       update_rate_window=cfg.features["update_rate_window"],
                       depth_levels=cfg.levels)
    se = ThresholdSignalEngine(imbalance_threshold=cfg.signals["imbalance_threshold"],
                               min_update_rate=cfg.signals["min_update_rate"],
                               confirm_n=cfg.signals["confirm_n"])
    bt = RollingBacktester(tick_size=cfg.tick_size, horizon_seconds=cfg.backtest["horizon_seconds"],
                           exit_on_opposite_signal=cfg.backtest.get("exit_on_opposite_signal", False),
                           slippage_ticks=cfg.backtest.get("slippage_ticks", 0.0))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts", "mid", "imbalance", "bid_slope", "ask_slope", "update_rate", "signal", "strength", "cum_pnl_ticks"])
        cum = 0.0
        for snap in ing.iter():
            fv = fe.push(snap)
            sig = se.evaluate(fv)
            if sig:
                bt.on_signal(snap, sig)
            ev = bt.on_snapshot(snap)
            if ev:
                cum += ev.pnl_ticks
            w.writerow([snap.ts, snap.mid, fv.imbalance, fv.bid_slope, fv.ask_slope, fv.update_rate, getattr(sig, "kind", ""), getattr(sig, "strength", ""), cum])

    print("Summary:", bt.summary())
    print(f"Wrote results to {out_path}")

if __name__ == "__main__":
    main()
