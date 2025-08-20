from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
import yaml
from pathlib import Path

@dataclass
class Config:
    mode: str
    symbol: str
    venue: str
    tick_size: float
    price_decimals: int
    levels: int
    ws_url: str
    replay: Dict[str, Any]
    features: Dict[str, Any]
    signals: Dict[str, Any]
    backtest: Dict[str, Any]

def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return Config(**d)
