from __future__ import annotations
from pathlib import Path
from obp.ingest import ReplayIngestor

def test_replay_iter(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    p.write_text('{"ts":0.0,"bids":[[100,1]],"asks":[[101,1]]}\n{"ts":0.1,"bids":[[100,2]],"asks":[[101,1]]}\n')
    ing = ReplayIngestor(p, speedup=0.0)
    snaps = list(ing.iter())
    assert len(snaps) == 2
    assert snaps[0].best_bid == 100
