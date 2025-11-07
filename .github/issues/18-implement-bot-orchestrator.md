# Implement Bot Orchestrator

**Labels:** `priority: critical`, `type: implementation`, `mvp`, `tdd`, `bot`

## Description
Implement main bot controller to pass all tests from Issue #17.

## Tasks
- [ ] Implement `src/kuru_copytr_bot/bot.py`:
  - [ ] `CopyTradingBot` class
  - [ ] `__init__()` - Initialize all components
  - [ ] `start()` - Start monitoring and processing
  - [ ] `stop()` - Graceful shutdown
  - [ ] `_handle_detected_trade()` - Process detected trades
  - [ ] Wire monitor → detector → copier flow
  - [ ] Handle component errors
  - [ ] Add health check method
- [ ] Implement monitoring loop:
  - [ ] Poll for new transactions
  - [ ] Parse events
  - [ ] Pass trades to copier
  - [ ] Handle exceptions without crashing

## Acceptance Criteria
- All tests from Issue #17 pass
- Unit tests pass with mocked components
- Integration test runs bot on testnet successfully
- Bot starts and stops cleanly
- Event flow works end-to-end
- No functionality beyond test requirements

## Dependencies
- All previous components
- Issue #17: Write Tests for Bot Orchestrator
