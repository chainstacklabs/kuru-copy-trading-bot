# Kuru Copy Trading Bot

> **⚠️ Work in Progress**: This is an educational project for Monad testnet. Not production-ready. Use at your own risk.

Copy trading bot for Kuru Exchange on Monad blockchain. Monitors target wallets and mirrors their trades with configurable position sizing and risk management.

## What Gets Copied

| Event | Action |
|-------|--------|
| **OrderCreated** | Copies limit orders from source wallets (this is the copy trigger) |
| **Trade** | Tracks fills on our orders for statistics; logs source activity (no copying) |
| **OrdersCanceled** | Cancels our mirrored orders when source cancels theirs |

> **Note**: Market orders are not copied. By the time we see the Trade event, the opportunity is gone and we can't match the execution price.

## Features

- Real-time blockchain event monitoring via RPC WebSocket
- Configurable position sizing with copy ratio
- Risk management (balance checks, position limits, market filters)

## Installation

```bash
git clone https://github.com/chainstacklabs/kuru-copy-trading-bot
cd kuru-copy-trading-bot
uv sync
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Blockchain
MONAD_RPC_URL=https://testnet.monad.xyz
WALLET_PRIVATE_KEY=0x...

# Kuru Exchange
KURU_API_URL=https://api.testnet.kuru.io

# Source wallets to copy (comma-separated)
SOURCE_WALLETS=0x1111...,0x2222...

# Markets to monitor (comma-separated contract addresses)
MARKET_ADDRESSES=0xd3af145f1aa1a471b5f0f62c52cf8fcdc9ab55d3

# Position sizing
COPY_RATIO=0.1                    # Copy 10% of source position size
MAX_POSITION_SIZE=1000.0          # Max position size in USD
MIN_ORDER_SIZE=10.0               # Min order size in USD

# Risk management
MIN_BALANCE_THRESHOLD=100.0       # Stop if balance falls below
MAX_TOTAL_EXPOSURE=5000.0         # Max total exposure in USD

# Optional: Market filters
MARKET_WHITELIST=                 # Only these markets (empty = all)
MARKET_BLACKLIST=                 # Never these markets
```

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

## Project Structure

```
src/kuru_copytr_bot/
├── main.py              # Entry point (async)
├── bot.py               # Main orchestrator (event handling)
├── models/              # Data models (Trade, Order, Market, etc.)
├── core/                # Interfaces and exceptions
├── trading/             # Trade copying and execution
├── risk/                # Position sizing and validation
├── connectors/
│   ├── blockchain/      # Monad blockchain client + event subscriber
│   └── platforms/       # Kuru Exchange REST API client
├── utils/               # Logging and helpers
└── config/              # Settings and constants

tests/                   # Unit tests
docs/                    # API documentation
```

## Kuru API Documentation

The Kuru Exchange API has been reverse-engineered from the [Kuru SDK Python repository](https://github.com/Kuru-Labs/kuru-sdk-py). Full specification available in [docs/KURU_API_SPEC.md](docs/KURU_API_SPEC.md).

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

