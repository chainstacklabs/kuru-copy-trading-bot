# Kuru Copy Trading Bot

## Structure

```
src/kuru_copytr_bot/    # Core bot package
examples/               # Learning scripts
tests/                  # Test suite
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
