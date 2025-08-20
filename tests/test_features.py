from __future__ import annotations
import numpy as np
from moa.schemas import BookSnapshot
from moa.features import compute_imbalance, FeatureEngine

def test_imbalance_balanced():
    bids = np.array([[100, 5],[99,5]])
    asks = np.array([[101, 5],[102,5]])
    snap = BookSnapshot(ts=0.0, bids=bids, asks=asks)
    assert abs(compute_imbalance(snap, 2)) < 1e-9

def test_feature_engine_basic():
    bids = np.array([[100, 6],[99,4]])
    asks = np.array([[101, 5],[102,5]])
    fe = FeatureEngine(window_size=5, update_rate_window=5, depth_levels=2)
    for i in range(5):
        snap = BookSnapshot(ts=float(i), bids=bids, asks=asks)
        fv = fe.push(snap)
    assert fv.imbalance > 0.0
    assert fv.update_rate > 0.0
