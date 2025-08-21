from __future__ import annotations
import argparse
from pathlib import Path
from collections import deque
import pandas as pd
import altair as alt
import sys
from pathlib import Path

# --- bootstrap so Streamlit can import from src/ ---
SRC_DIR = Path(__file__).resolve().parents[1]  # .../repo/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from moa.config import load_config
from moa.ingest import ReplayIngestor, BinanceIngestor
from moa.features import FeatureEngine
from moa.signals import ThresholdSignalEngine
from moa.backtest import RollingBacktester

# --- header with left-aligned logo the size of the font ---
import base64
import streamlit as st

def header_with_logo(title: str, logo_path: str, size_rem: float = 1.6, gap_px: int = 10):
    """
    Renders a header with a logo to the left of the title text.
    size_rem ~1.4–1.8 looks close to Streamlit's default title height.
    """
    logo_bytes = Path(logo_path).read_bytes()
    b64 = base64.b64encode(logo_bytes).decode("utf-8")

    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:{gap_px}px;">
            <img src="data:image/png;base64,{b64}" style="height:{size_rem}rem; width:auto; border-radius:6px;"/>
            <span style="font-size:{size_rem}rem; font-weight:700; line-height:1;">
                {title}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Ensure the project "src" is on sys.path
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=str, default="configs/default.yaml")
    return p.parse_known_args()[0]

def main(cfg_path: str):
    cfg = load_config(cfg_path)

    st.set_page_config(page_title="Market Order App", layout="wide")
    
    header_with_logo(
    title="Market Order — Real-Time Microstructure Signals",
    logo_path="assets/logo.PNG", 
    size_rem=5
    )

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
                df_mid["time"] = pd.to_datetime(df_mid["ts"], unit="s")
                mid_chart = (
                    alt.Chart(df_mid)
                    .mark_line()
                    .encode(
                        x=alt.X("time:T", title="Time"),
                        y=alt.Y("mid:Q", title="Mid Price"),
                        tooltip=[alt.Tooltip("time:T", title="Time"), alt.Tooltip("mid:Q", title="Mid")]
                    )
                    .properties(title="Mid Price Over Time", width="container", height=400)
                )
                placeholder_chart.altair_chart(mid_chart, use_container_width=True)

            # seed cum_pnl so the chart has an initial point if desired
            if not cum_pnl:
                cum_pnl.append({"ts": snap.ts, "cum_pnl_ticks": cum})

            df_pnl = pd.DataFrame(cum_pnl)
            if not df_pnl.empty and "ts" in df_pnl.columns:
                df_pnl["time"] = pd.to_datetime(df_pnl["ts"], unit="s")
                pnl_chart = (
                    alt.Chart(df_pnl)
                    .mark_line()
                    .encode(
                        x=alt.X("time:T", title="Time"),
                        y=alt.Y("cum_pnl_ticks:Q", title="Cumulative P&L (ticks)"),
                        tooltip=[alt.Tooltip("time:T", title="Time"), alt.Tooltip("cum_pnl_ticks:Q", title="PnL (ticks)")]
                    )
                    .properties(title="Cumulative P&L", width="container", height=400)
                )
                placeholder_pnl.altair_chart(pnl_chart, use_container_width=True)

            # keep the signal tape as-is
            df_tape = pd.DataFrame(tape).tail(15)
            placeholder_table.dataframe(df_tape)


            df_tape = pd.DataFrame(tape).tail(15)
            placeholder_table.dataframe(df_tape)


    st.success("Replay complete.")
    st.json(bt.summary())

if __name__ == "__main__":
    args = parse_args()
    main(args.config)
