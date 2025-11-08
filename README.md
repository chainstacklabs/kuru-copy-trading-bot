# Kuru Copy Trading Bot

A production-ready copy trading bot for Kuru Exchange on Monad testnet. Automatically mirrors trades from expert wallets with configurable position sizing and comprehensive risk management.

## Features

✅ **Real-time Monitoring** - Watches target wallets for Kuru Exchange transactions
✅ **Event Detection** - Parses TradeExecuted, OrderPlaced, and OrderCancelled events
✅ **Position Sizing** - Configurable copy ratio with min/max limits
✅ **Risk Management** - Balance validation, position limits, market filters
✅ **Graceful Error Handling** - Never crashes, continues on errors
✅ **Statistics Tracking** - Comprehensive metrics for monitoring performance
✅ **Test Coverage** - 286+ tests passing, 87% code coverage

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/kuru-copy-trading-bot.git
cd kuru-copy-trading-bot

# Install dependencies
uv sync
```

### 2. Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Blockchain
MONAD_RPC_URL=https://testnet-rpc.monad.xyz
WALLET_PRIVATE_KEY=your_private_key_here

# Source Wallets (comma-separated)
SOURCE_WALLETS=0x1111...,0x2222...

# Position Sizing
COPY_RATIO=0.1                    # Copy 10% of source position size
MAX_POSITION_SIZE=100.0           # Maximum position size
MIN_ORDER_SIZE=0.01               # Minimum order size

# Risk Management
MIN_BALANCE_THRESHOLD=10.0        # Minimum balance to maintain
MAX_TOTAL_EXPOSURE=1000.0         # Maximum total exposure

# Market Filters (optional)
MARKET_WHITELIST=ETH-USDC,BTC-USDC
# MARKET_BLACKLIST=DOGE-USDC

# Bot Settings
POLL_INTERVAL_SECONDS=5           # How often to check for new trades
```

### 3. Run the Bot

```bash
uv run python -m src.kuru_copytr_bot.main
```

Or with a custom .env file:

```bash
uv run python -m src.kuru_copytr_bot.main --env-file .env.production
```

### 4. Configure Logging

Control logging output with command-line options:

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
uv run python -m src.kuru_copytr_bot.main --log-level DEBUG

# Output logs in JSON format (for log aggregation systems)
uv run python -m src.kuru_copytr_bot.main --json-logs

# Combine options
uv run python -m src.kuru_copytr_bot.main --log-level INFO --json-logs
```

Default log output is human-readable with structured fields:

```
2025-11-08T10:30:45.123456Z [info     ] Starting copy trading bot   poll_interval=5
2025-11-08T10:30:46.789012Z [info     ] Trade detected              market=ETH-USDC side=buy size=5.0 price=2000.0
2025-11-08T10:30:47.345678Z [info     ] Successfully executed mirror trade order_id=0x1234...
```

### 5. Monitor Performance

The bot displays real-time statistics:

```
Stats: 42 txs | 15 trades | 12 successful | 2 failed | 1 rejected
```

Press `Ctrl+C` to stop gracefully and see final statistics.

## Architecture

## Structure

```
src/kuru_copytr_bot/
├── main.py              # Entry point
├── bot.py               # Main orchestrator
├── models/              # Data structures (Trade, Order, Position, Wallet)
├── core/                # Interfaces and exceptions
├── monitoring/          # Watch source trader activity
├── trading/             # Copy and execute trades
├── risk/                # Validate trades and calculate position sizes
├── connectors/          # Platform and blockchain integrations
│   ├── blockchain/      # Blockchain clients (Ethereum, etc.)
│   └── platforms/       # Trading platforms (Uniswap, etc.)
├── utils/               # Logging, decorators, helpers
└── config/              # Settings and constants

examples/                # Learning scripts
tests/                   # Test suite (unit, integration, fixtures)
```

## Setup

Install dependencies for testing:

```bash
uv sync --extra dev
```

## Development

**Linting and formatting**:

```bash
uvx ruff check --fix .
uvx ruff format .
uvx mypy src/
```

**Git hooks** (requires `uv sync --extra dev`):

```bash
uv run pre-commit install
```

**Testing** (requires `uv sync --extra dev`):

```bash
uv run pytest
uv run pytest --cov
```

## How It Works

```
┌─────────────────┐
│ WalletMonitor   │  Watches target wallets for Kuru transactions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ EventDetector   │  Parses TradeExecuted events from transactions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PositionSizer   │  Calculates position size (copy_ratio × source_size)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TradeValidator  │  Validates against risk rules
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TradeCopier     │  Executes mirror trade on Kuru Exchange
└─────────────────┘
```

## Components

- **MonadClient** - Web3.py-based blockchain connector with retry logic
- **KuruClient** - Python wrapper for Kuru Exchange API
- **WalletMonitor** - Detects transactions from target wallets with structured logging
- **KuruEventDetector** - Parses blockchain events (TradeExecuted, OrderPlaced, etc.)
- **PositionSizeCalculator** - Calculates position sizes with copy ratio and limits
- **TradeValidator** - Validates trades against risk management rules
- **TradeCopier** - Executes mirror trades with comprehensive error logging
- **CopyTradingBot** - Orchestrates the entire workflow with structured logging

## Logging

The bot uses **structlog** for structured logging with the following features:

- **Structured Fields** - All log entries include contextual data (trade IDs, markets, sizes, etc.)
- **Multiple Log Levels** - DEBUG, INFO, WARNING, ERROR, CRITICAL
- **JSON Output** - Optional JSON format for log aggregation systems (Elasticsearch, Datadog, etc.)
- **Human-Readable** - Default colored console output for development
- **Error Tracking** - Full exception traces with `exc_info=True` for debugging

### Log Examples

**Human-Readable Format** (default):
```
2025-11-08T10:30:45.123Z [info     ] Starting wallet monitor  target_wallets=['0x1234...']
2025-11-08T10:30:46.789Z [info     ] Trade detected           trade_id=abc123 market=ETH-USDC side=buy
2025-11-08T10:30:47.345Z [warning  ] Trade validation failed  reason="Insufficient balance"
```

**JSON Format** (`--json-logs`):
```json
{"event": "Trade detected", "timestamp": "2025-11-08T10:30:46.789Z", "level": "info", "trade_id": "abc123", "market": "ETH-USDC", "side": "buy", "app": "kuru-copy-trading-bot"}
```

## Testing

Run the test suite:

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/unit/test_bot.py -v

# Integration tests only
uv run pytest -m integration
```

Current test coverage: **87%** (286/294 tests passing)

## Requirements

- Python >=3.13
- uv package manager
- Monad testnet RPC access
- Private key with MON tokens for gas
