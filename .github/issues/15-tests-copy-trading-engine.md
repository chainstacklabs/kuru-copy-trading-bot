# Write Tests for Copy Trading Engine

**Labels:** `priority: critical`, `type: testing`, `mvp`, `tdd`, `trading`

## Description
Write tests for the core copy trading logic before implementation.

## Tasks
- [ ] Create `tests/unit/trading/test_copier.py`:
  - [ ] Test copying source trade with ratio
  - [ ] Test trade filtering (size, market)
  - [ ] Test validation before copying
  - [ ] Test handling validation failures
  - [ ] Test dry run mode (no execution)
  - [ ] Test order submission
- [ ] Create `tests/unit/trading/test_executor.py`:
  - [ ] Test order execution via Kuru client
  - [ ] Test confirmation polling
  - [ ] Test retry on failure
  - [ ] Test execution timeout
- [ ] Create `tests/integration/test_end_to_end.py`:
  - [ ] Test full copy flow on testnet
  - [ ] Detect source trade → validate → copy → execute

## Test Examples
```python
def test_copier_copies_trade_with_ratio(mock_validator, mock_calculator, mock_executor):
    """Copier should apply ratio and copy valid trades"""
    mock_validator.validate.return_value = ValidationResult(is_valid=True)
    mock_calculator.calculate.return_value = Decimal("5.0")

    copier = TradeCopier(
        validator=mock_validator,
        calculator=mock_calculator,
        executor=mock_executor
    )

    source_trade = Trade(size=Decimal("10"), price=Decimal("100"), ...)
    copier.copy_trade(source_trade)

    mock_calculator.calculate.assert_called_with(Decimal("10"), ...)
    mock_executor.execute_order.assert_called_once()

def test_copier_skips_invalid_trades(mock_validator, mock_executor):
    """Copier should not execute invalid trades"""
    mock_validator.validate.return_value = ValidationResult(
        is_valid=False,
        reason="Insufficient balance"
    )

    copier = TradeCopier(validator=mock_validator, executor=mock_executor)
    source_trade = Trade(size=Decimal("10"), ...)
    copier.copy_trade(source_trade)

    mock_executor.execute_order.assert_not_called()

def test_executor_retries_failed_orders(mock_kuru_client):
    """Executor should retry failed order submissions"""
    mock_kuru_client.place_limit_order.side_effect = [
        Exception("Network error"),
        "order_123"
    ]
    executor = OrderExecutor(kuru_client=mock_kuru_client, max_retries=3)
    order = Order(...)
    order_id = executor.execute_order(order)
    assert order_id == "order_123"
    assert mock_kuru_client.place_limit_order.call_count == 2
```

## Acceptance Criteria
- Unit tests with all dependencies mocked
- Integration test with real testnet
- Tests verify full copy flow
- Tests verify filtering and validation
- Tests verify error handling and retries
- All tests initially fail

## Dependencies
- Issue #10: Implement Python Kuru SDK Wrapper
- Issue #12: Implement Risk Management
