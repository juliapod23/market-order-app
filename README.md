# Order Book Pulse

A 100% open-source toolkit that ingests live or replayed order-book data, computes microstructure features (e.g., liquidity imbalance, book slope, update rate), emits **buy/sell pressure** alerts, and evaluates a rolling edge with a micro back-tester.


## Quickstart (Replay Mode)

```bash
git clone <your-fork-url>
cd market-order-app
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run a quick replay with the bundled sample file
python scripts/run_replay.py --config configs/default.yaml
```

## Streamlit Dashboard

```bash
streamlit run src/obp/ui_app.py -- --config configs/default.yaml
```

## Live Mode (Crypto, Free)

By default, `configs/default.yaml` points to Binance Futures depth20@100ms for `btcusdt` (no API key needed).

> **Note**: Real-time redistribution policies vary by venue. This repo uses public, no-cost endpoints for demo purposes only.

## Why it’s useful

- Visual, quantitative signal on short-horizon **order flow pressure**.
- Built-in **rolling evaluation**: forward returns and simple P/L.
- Clean, pluggable architecture so researchers can drop in new features or signals.

## License

MIT — permissive for internal forks and experiments.

