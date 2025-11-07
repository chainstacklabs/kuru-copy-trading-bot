# Implement Error Handling

**Labels:** `priority: medium`, `type: implementation`, `mvp`, `tdd`, `utils`

## Description
Implement custom exceptions and error handling utilities to pass all tests from Issue #23.

## Tasks
- [ ] Implement `src/kuru_copytr_bot/core/exceptions.py`:
  - [ ] `BlockchainConnectionError`
  - [ ] `TransactionFailedError`
  - [ ] `InsufficientBalanceError`
  - [ ] `OrderExecutionError`
  - [ ] `TradeValidationError`
  - [ ] `InvalidMarketError`
  - [ ] `ConfigurationError`
  - [ ] All with clear error messages
- [ ] Implement `src/kuru_copytr_bot/utils/decorators.py`:
  - [ ] `@retry` decorator
  - [ ] Exponential backoff
  - [ ] Max attempts
  - [ ] Configurable exceptions to retry
  - [ ] `@async_timeout` decorator

## Acceptance Criteria
- All tests from Issue #23 pass
- Exceptions have clear messages
- Retry decorator works with async functions
- Timeout decorator works correctly
- No functionality beyond test requirements

## Dependencies
- Issue #23: Write Tests for Error Handling
