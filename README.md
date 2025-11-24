# Kuru Copy Trading Bot

> **⚠️ Work in Progress**: Educational project for Monad. Currently mirrors limit orders from specified Kuru markets only. After each signal, multiple RPC calls are made that could be optimized. Good base for enhancements.

Copy trading bot for Kuru Exchange on Monad blockchain. Monitors target wallets and mirrors their limit orders. Interacts directly with blockchain contracts.

## What Gets Copied

| Event | Action |
|-------|--------|
| **OrderCreated** | Copies limit orders from source wallets (this is the copy trigger) |
| **Trade** | Tracks fills on our orders for statistics; logs source activity (no copying) |
| **OrdersCanceled** | Cancels our mirrored orders when source cancels theirs |

> **Note**: Market orders are not copied.

## Features

- Monitors blockchain events via RPC WebSocket
- Position sizing with copy ratio
- Basic risk management (balance checks, position limits, market filters)

## Installation

```bash
git clone https://github.com/chainstacklabs/kuru-copy-trading-bot
cd kuru-copy-trading-bot
uv sync
```

## Configuration

Copy `.env.example` to `.env` and configure environment variables (RPC endpoint, source wallets, etc.).

## Usage

```bash
# Run bot
uv run python -m src.kuru_copytr_bot.main

# Custom config file
uv run python -m src.kuru_copytr_bot.main --env-file .env.prod

# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
uv run python -m src.kuru_copytr_bot.main --log-level DEBUG

# JSON logs (for log aggregation)
uv run python -m src.kuru_copytr_bot.main --json-logs
```

Press `Ctrl+C` to stop. Final statistics will be displayed.

## Architecture

```
┌────────────────────────┐
│ Blockchain Event       │  Subscribes to OrderBook contract events
│ Subscriber (RPC WSS)   │  via eth_subscribe on market address
└──────────┬─────────────┘
           │ (OrderCreated / Trade event)
           ▼
┌─────────────────┐
│  Event Filter   │  Filters trades from monitored source wallets
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PositionSizer   │  Calculates position size: copy_ratio × source_size
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TradeValidator  │  Validates against risk rules
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TradeCopier     │  Executes mirror trade via Kuru Exchange
└─────────────────┘
```

>  **FYI**: Kuru Exchange API has been reverse-engineered from the [Kuru SDK repository](https://github.com/Kuru-Labs/kuru-sdk). Full specification available in [docs/KURU_API_SPEC.md](docs/KURU_API_SPEC.md).

## Development

Install dev dependencies:
```bash
uv sync --extra dev
```

Lint and format:
```bash
uvx ruff check --fix .
uvx ruff format .
uvx mypy src/
```

Run tests:
```bash
uv run pytest
uv run pytest --cov
uv run pytest tests/unit/test_bot.py -v
```

Install pre-commit hooks:
```bash
uv run pre-commit install
```

## Requirements

- Python 3.10+
- uv package manager
- Monad testnet RPC access (WSS endpoint for event subscriptions)
- Private key with MON tokens for gas

## License

MIT

