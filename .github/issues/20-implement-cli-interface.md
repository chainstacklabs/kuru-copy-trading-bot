# Implement CLI Interface

**Labels:** `priority: high`, `type: implementation`, `mvp`, `tdd`, `cli`

## Description
Implement terminal CLI interface to pass all tests from Issue #19.

## Tasks
- [ ] Implement `src/kuru_copytr_bot/main.py`:
  - [ ] Use Click for CLI framework
  - [ ] Arguments:
    - [ ] `--config PATH` - Path to .env file (default: .env)
    - [ ] `--dry-run` - Run without executing orders
    - [ ] `--log-level LEVEL` - Set log level (default: INFO)
  - [ ] `start()` command:
    - [ ] Load configuration
    - [ ] Initialize bot
    - [ ] Setup signal handlers (SIGINT, SIGTERM)
    - [ ] Start bot
    - [ ] Keep running until signal
  - [ ] Handle errors with user-friendly messages
  - [ ] Display startup info (wallet address, source wallets, etc.)

## CLI Usage
```bash
# Basic usage
uv run python -m kuru_copytr_bot.main --config .env

# Dry run mode
uv run python -m kuru_copytr_bot.main --config .env --dry-run

# Debug logging
uv run python -m kuru_copytr_bot.main --config .env --log-level DEBUG

# Stop with Ctrl+C (SIGINT)
```

## Acceptance Criteria
- All tests from Issue #19 pass
- CLI accepts all specified arguments
- Bot starts and runs from CLI
- Graceful shutdown on Ctrl+C
- Clear error messages on failure
- Displays useful startup information
- No functionality beyond test requirements

## Dependencies
- Issue #18: Implement Bot Orchestrator
- Issue #19: Write Tests for CLI Interface
