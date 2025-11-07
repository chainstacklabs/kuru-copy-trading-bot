# Implement Logging System

**Labels:** `priority: medium`, `type: implementation`, `mvp`, `tdd`, `logging`

## Description
Implement structured logging to pass all tests from Issue #21.

## Tasks
- [ ] Implement `src/kuru_copytr_bot/utils/logger.py`:
  - [ ] Configure structlog
  - [ ] JSON output format
  - [ ] Timestamp processor
  - [ ] Context processors
  - [ ] Sensitive data filter (private keys, full addresses)
  - [ ] `get_logger()` factory function
- [ ] Add logging to all modules:
  - [ ] Startup/shutdown events
  - [ ] Trade detection
  - [ ] Trade copying
  - [ ] Order execution
  - [ ] Validation failures
  - [ ] Errors

## Acceptance Criteria
- All tests from Issue #21 pass
- All modules use structured logger
- Sensitive data never logged
- Logs are JSON formatted
- No functionality beyond test requirements

## Dependencies
- Issue #21: Write Tests for Logging System
