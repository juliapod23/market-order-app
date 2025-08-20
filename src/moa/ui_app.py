from __future__ import annotations
import argparse
from pathlib import Path
from collections import deque

import sys
from pathlib import Path

# Ensure the project "src" is on sys.path
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import pandas as pd

from moa.config import load_config
from moa.ingest import ReplayIngestor, BinanceIngestor
from moa.features import FeatureEngine
from moa.signals import ThresholdSignalEngine
from moa.backtest import RollingBacktester

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=str, default="configs/default.yaml")
    return p.parse_known_args()[0]

def main(cfg_path: str):
    cfg = load_config(cfg_path)

    st.set_page_config(page_title="Market Order App", layout="wide")
    st.title("Market Order App — Real-time Microstructure Signals")

    left, right = st.columns([1, 2])

    with left:
        st.subheader("Configuration")
        st.write(f"**Mode:** {cfg.mode}")
        st.write(f"**Symbol:** {cfg.symbol}")
        st.write(f"**Levels:** {cfg.levels}")
        imb_th = st.slider("Imbalance threshold", 0.0, 0.5, float(cfg.signals['imbalance_threshold']), 0.01)
        min_rate = st.slider("Min update rate (events/s)", 0.0, 10.0, float(cfg.signals['min_update_rate']), 0.1)
        confirm_n = st.slider("Consecutive confirmations", 1, 5, int(cfg.signals['confirm_n']), 1)
        horizon = st.slider("Backtest horizon (s)", 1, 30, int(cfg.backtest['horizon_seconds']), 1)

    # engines
    fe = FeatureEngine(window_size=cfg.features["window_size"],
                       update_rate_window=cfg.features["update_rate_window"],
                       depth_levels=cfg.levels)
    se = ThresholdSignalEngine(imbalance_threshold=imb_th, min_update_rate=min_rate, confirm_n=confirm_n)
    bt = RollingBacktester(tick_size=cfg.tick_size, horizon_seconds=horizon)

    # state
    tape = []
    history_mid = []
    cum_pnl = []
    cum = 0.0

    # Ingestor selection
    if cfg.mode == "replay":
        ing = ReplayIngestor(cfg.replay["file"], speedup=cfg.replay.get("speedup", 0.0))
        iterator = ing.iter()
    else:
        ing = BinanceIngestor(cfg.ws_url, levels=cfg.levels)
        iterator = ing.stream()  # note: this is async; Streamlit won't run it here

        st.warning("Live mode is defined, but the Streamlit loop uses synchronous replay. Use scripts/capture_ws.py or integrate asyncio in a custom runner.")
        return

    # Main sync loop for replay
    placeholder_chart = right.empty()
    placeholder_pnl = right.empty()
    placeholder_table = right.empty()

    for i, snap in enumerate(iterator):
        history_mid.append({"ts": snap.ts, "mid": snap.mid})
        fv = fe.push(snap)
        sig = se.evaluate(fv)
        if sig:
            tape.append({"ts": sig.ts, "signal": sig.kind, "strength": sig.strength})
            bt.on_signal(snap, sig)
        ev = bt.on_snapshot(snap)
        if ev:
            cum += ev.pnl_ticks
            cum_pnl.append({"ts": ev.ts, "cum_pnl_ticks": cum})

        if i % 5 == 0:
            # update charts every 5 ticks
            df_mid = pd.DataFrame(history_mid)
            if not df_mid.empty and "ts" in df_mid.columns:
                placeholder_chart.line_chart(df_mid.set_index("ts"))

            # Seed cum_pnl so it always has a ts for the chart (optional but nice)
            if not cum_pnl:
                cum_pnl.append({"ts": snap.ts, "cum_pnl_ticks": cum})

            df_pnl = pd.DataFrame(cum_pnl)
            if not df_pnl.empty and "ts" in df_pnl.columns:
                placeholder_pnl.line_chart(df_pnl.set_index("ts"))

            df_tape = pd.DataFrame(tape).tail(15)
            placeholder_table.dataframe(df_tape)


    st.success("Replay complete.")
    st.json(bt.summary())

if __name__ == "__main__":
    args = parse_args()
    main(args.config)
