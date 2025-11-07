# Kuru Copy Trading Bot

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

## Requirements

- Python >=3.13
- uv
