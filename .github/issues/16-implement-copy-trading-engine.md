# Implement Copy Trading Engine

**Labels:** `priority: critical`, `type: implementation`, `mvp`, `tdd`, `trading`

## Description
Implement the core copy trading engine to pass all tests from Issue #15.

## Tasks
- [ ] Implement `src/kuru_copytr_bot/trading/copier.py`:
  - [ ] `TradeCopier` class
  - [ ] `copy_trade()` - Main copy logic
  - [ ] `should_copy()` - Apply filters
  - [ ] Apply copy ratio via calculator
  - [ ] Validate via validator
  - [ ] Create target order
  - [ ] Submit to executor
  - [ ] Handle dry run mode
  - [ ] Log all actions
- [ ] Implement `src/kuru_copytr_bot/trading/executor.py`:
  - [ ] `OrderExecutor` class
  - [ ] `execute_order()` - Execute via Kuru client
  - [ ] Route to correct order type (limit/market)
  - [ ] Poll for confirmation
  - [ ] Retry on failure with backoff
  - [ ] Handle execution errors
  - [ ] Return order ID or raise exception

## Acceptance Criteria
- All tests from Issue #15 pass
- Unit tests pass with mocked dependencies
- Integration test copies real trade on testnet
- Proper filtering and validation
- Retry logic works correctly
- No functionality beyond test requirements

## Dependencies
- Issue #10: Implement Python Kuru SDK Wrapper
- Issue #12: Implement Risk Management
- Issue #15: Write Tests for Copy Trading Engine
