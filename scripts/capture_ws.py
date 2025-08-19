"""
Capture a Binance Futures depth20@100ms stream to JSONL for replay.
Usage:
    python scripts/capture_ws.py --symbol btcusdt --minutes 5 --outfile data/raw/btcusdt_depth.jsonl
"""
from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path

import websockets

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", type=str, default="btcusdt")
    p.add_argument("--minutes", type=int, default=5)
    p.add_argument("--outfile", type=str, default="data/raw/capture.jsonl")
    return p.parse_args()

async def run(symbol: str, minutes: int, outfile: str):
    url = f"wss://fstream.binance.com/stream?streams={symbol}@depth20@100ms"
    out_path = Path(outfile)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cutoff = minutes * 60
    first_ts = None
    async with websockets.connect(url, max_size=2**22) as ws, open(outfile, "w", encoding="utf-8") as f:
        async for msg in ws:
            d = json.loads(msg)
            data = d.get("data", d)
            ts = data.get("E", data.get("T", 0)) / 1000.0
            if first_ts is None:
                first_ts = ts
            elapsed = ts - first_ts
            bids = [[float(p), float(q)] for p,q in data.get("b", [])]
            asks = [[float(p), float(q)] for p,q in data.get("a", [])]
            if not bids or not asks:
                continue
            out = {"ts": ts, "bids": bids, "asks": asks}
            f.write(json.dumps(out) + "\n")
            if elapsed >= cutoff:
                break
    print(f"Wrote: {outfile}")

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(args.symbol, args.minutes, args.outfile))
