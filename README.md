# Market Order App

A 100% open-source toolkit that ingests live or replayed order-book data, computes microstructure features (e.g., liquidity imbalance, book slope, update rate), emits **buy/sell pressure** alerts, and evaluates a rolling edge with a micro back-tester.


## Quickstart (Replay Mode)

```bash
export PYTHONPATH=./src     # or: pip install -e .
streamlit run src/obp/ui_app.py -- --config configs/default.yaml
# Windows: .venv\Scripts\activate
$env:PYTHONPATH = ".\src"   # or: pip install -e .
streamlit run src\obp\ui_app.py -- --config configs\default.yaml

# Run a quick replay with the bundled sample file
python scripts/run_replay.py --config configs/default.yaml
```

## Streamlit Dashboard

```bash
streamlit run src/moa/ui_app.py -- --config configs/default.yaml
```

## Live Mode

By default, `configs/default.yaml` points to Binance Futures depth20@100ms for `btcusdt` (no API key needed).

```bash
#Record ~3 minutes of BTCUSDT depth to JSONL 

export PYTHONPATH=./src
python scripts/capture_ws.py --symbol btcusdt --minutes 3 --outfile data/samples/btcusdt.jsonl

# Point the config to your capture:
# configs/default.yaml -> replay.file: data/samples/btcusdt.jsonl

# Run Streamlit again
streamlit run src/obp/ui_app.py -- --config configs/default.yaml
```

> **Note**: Real-time redistribution policies vary by venue. This repo uses public, no-cost endpoints for demo purposes only.

## Why it’s useful

- Visual, quantitative signal on short-horizon **order flow pressure**.
- Built-in **rolling evaluation**: forward returns and simple P/L.
- Clean, pluggable architecture so researchers can drop in new features or signals.

## License

MIT — permissive for internal forks and experiments.

