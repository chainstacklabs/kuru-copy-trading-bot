# Write Tests for CLI Interface

**Labels:** `priority: high`, `type: testing`, `mvp`, `tdd`, `cli`

## Description
Write tests for terminal/CLI interface before implementation.

## Tasks
- [ ] Create `tests/unit/test_cli.py`:
  - [ ] Test CLI argument parsing
  - [ ] Test config file loading
  - [ ] Test dry-run flag
  - [ ] Test log level flag
  - [ ] Test start command
  - [ ] Test stop signal handling

## Test Examples
```python
def test_cli_parses_config_argument():
    """CLI should accept --config argument"""
    args = parse_args(["--config", ".env.test"])
    assert args.config == ".env.test"

def test_cli_parses_dry_run_flag():
    """CLI should accept --dry-run flag"""
    args = parse_args(["--dry-run"])
    assert args.dry_run is True

def test_cli_starts_bot(mock_bot):
    """CLI start command should initialize and start bot"""
    cli = CLI(args={"config": ".env"})
    cli.start()

    mock_bot.start.assert_called_once()

def test_cli_handles_sigint(mock_bot):
    """CLI should handle SIGINT and stop bot gracefully"""
    cli = CLI(args={"config": ".env"})
    cli.start()

    # Simulate SIGINT
    cli._handle_signal(signal.SIGINT, None)

    mock_bot.stop.assert_called_once()
```

## Acceptance Criteria
- Tests verify all CLI arguments
- Tests verify signal handling
- Tests verify bot lifecycle via CLI
- All tests initially fail

## Dependencies
- Issue #18: Implement Bot Orchestrator
