# Write Tests for Logging System

**Labels:** `priority: medium`, `type: testing`, `mvp`, `tdd`, `logging`

## Description
Write tests for structured logging before implementation.

## Tasks
- [ ] Create `tests/unit/utils/test_logger.py`:
  - [ ] Test logger configuration
  - [ ] Test JSON output format
  - [ ] Test log levels
  - [ ] Test context addition (wallet, trade_id, etc.)
  - [ ] Test sensitive data filtering

## Test Examples
```python
def test_logger_outputs_json(capsys):
    """Logger should output JSON formatted logs"""
    logger = get_logger()
    logger.info("test message", key="value")

    captured = capsys.readouterr()
    log_data = json.loads(captured.out)
    assert log_data["message"] == "test message"
    assert log_data["key"] == "value"

def test_logger_includes_timestamp():
    """Logger should include timestamp"""
    logger = get_logger()
    logger.info("test")

    # Verify timestamp in output

def test_logger_filters_private_keys():
    """Logger should not log private keys"""
    logger = get_logger()
    logger.info("transaction", private_key="0x123secret")

    # Verify private key is redacted
    # captured output should contain [REDACTED] not actual key
```

## Acceptance Criteria
- Tests verify JSON output
- Tests verify sensitive data filtering
- Tests verify context processors
- All tests initially fail

## Dependencies
- Issue #1: Add Project Dependencies
