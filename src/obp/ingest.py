from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import AsyncIterator, Iterator, Optional
import numpy as np
from .schemas import BookSnapshot

class ReplayIngestor:
    """
    Reads JSONL snapshots produced by capture_ws.py or synthetic samples.
    Each line must be a JSON object: {"ts": float, "bids": [[p, q],...], "asks": [[p,q],...]}
    """
    def __init__(self, file_path: str | Path, speedup: float = 0.0):
        self.file_path = Path(file_path)
        self.speedup = speedup if speedup is not None else 0.0

    def iter(self) -> Iterator[BookSnapshot]:
        last_ts = None
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                ts = float(d["ts"])
                bids = np.array(d["bids"], dtype=float)
                asks = np.array(d["asks"], dtype=float)
                snap = BookSnapshot(ts=ts, bids=bids, asks=asks)
                if self.speedup > 0 and last_ts is not None:
                    dt = ts - last_ts
                    if dt > 0:
                        asyncio.run(asyncio.sleep(dt / self.speedup))
                last_ts = ts
                yield snap

    async def stream(self) -> AsyncIterator[BookSnapshot]:
        last_ts = None
        loop = asyncio.get_event_loop()
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                ts = float(d["ts"])
                bids = np.array(d["bids"], dtype=float)
                asks = np.array(d["asks"], dtype=float)
                snap = BookSnapshot(ts=ts, bids=bids, asks=asks)
                if self.speedup > 0 and last_ts is not None:
                    dt = ts - last_ts
                    if dt > 0:
                        await asyncio.sleep(dt / self.speedup)
                last_ts = ts
                yield snap

class BinanceIngestor:
    """
    Minimal WebSocket depth20@100ms ingestor for Binance Futures.
    Requires the `websockets` package. Not used during offline tests.
    """
    def __init__(self, ws_url: str, levels: int = 5):
        self.ws_url = ws_url
        self.levels = levels

    async def stream(self) -> AsyncIterator[BookSnapshot]:
        import websockets  # lazy import so unit tests don't need it
        async with websockets.connect(self.ws_url, max_size=2**22) as ws:
            async for msg in ws:
                d = json.loads(msg)
                payload = d.get("data", d)
                # Binance depth stream fields: 'b' bids [price, qty], 'a' asks
                bids = np.array([[float(p), float(q)] for p, q in payload.get("b", [])[:self.levels]], dtype=float)
                asks = np.array([[float(p), float(q)] for p, q in payload.get("a", [])[:self.levels]], dtype=float)
                ts = float(payload.get("E", payload.get("T", 0))) / 1000.0
                if bids.size == 0 or asks.size == 0:
                    continue
                # ensure best-first order
                bids = bids[np.argsort(-bids[:,0])]
                asks = asks[np.argsort(asks[:,0])]
                yield BookSnapshot(ts=ts, bids=bids, asks=asks)
