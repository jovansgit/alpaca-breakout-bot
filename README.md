# Alpaca Breakout Bot

An experimental 15-minute breakout trading bot using the Alpaca API, with 42 per-symbol strategy configurations.

**Paper trading is enabled by default.** This repository is a sanitized snapshot of the trading logic discussed for a July 2025 deployment, not independently verified performance or an assurance of safe live trading.

## Installation

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create your own **Alpaca paper** credentials and provide them as environment variables:

```bash
export ALPACA_API_KEY_PAPER='YOUR_OWN_PAPER_KEY'
export ALPACA_API_SECRET_PAPER='YOUR_OWN_PAPER_SECRET'
python breakout_bot_v1.py
```

The `.env.example` file shows variable names only; the script does not automatically load a `.env` file. Never commit credentials, real or paper.

## Strategy

The script checks 15-minute candles for price breakouts and elevated volume, using per-symbol breakout windows, volume multipliers, take-profit thresholds, and stop-loss thresholds. It submits whole-share market orders with bracket exits and keeps a local CSV activity log.

## Important limitations

- For **research/paper trading only** until execution and risk controls have been independently tested. Do not assume results from past short-window backtests predict future profit.
- A quote-based estimate determines order quantity and bracket levels. Actual fills can differ; the nominal $75–$500 allocation logic is **not** a hard dollar-loss risk cap.
- The volume average includes the signal candle; results may differ from other breakout implementations.
- The latest fetched bar may still be forming, causing unstable signals.
- The script checks positions, but not open pending orders, before buying; duplicate entry attempts may occur.
- Some bracket order parameters (including GTC and stop-limit behavior) may be rejected or fail to execute as expected. Stop-limit orders do not guarantee exits.
- CSV logging records the submitted buy at an indicative quote, not confirmed fills, and may log completed sell orders repeatedly.
- It does not impose a maximum concurrent position count or a daily loss limit.

## Secrets and repository history

**No real API keys are included.** Configure credentials locally via environment variables. The included `.gitignore` excludes common secret files, logs and private keys, but cannot protect secrets that are manually added to tracked files or committed later. Rotate any keys previously committed to another repository.

## License

No license granted at present. Public visibility does not automatically grant rights to reuse or redistribute.
