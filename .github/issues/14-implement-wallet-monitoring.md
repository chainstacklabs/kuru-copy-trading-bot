# Implement Wallet Monitoring

**Labels:** `priority: high`, `type: implementation`, `mvp`, `tdd`, `monitoring`

## Description
Implement wallet monitoring and Kuru event detection to pass all tests from Issue #13.

## Tasks
- [ ] Implement `src/kuru_copytr_bot/monitoring/monitor.py`:
  - [ ] `WalletMonitor` class
  - [ ] `start()` - Begin monitoring
  - [ ] `stop()` - Stop monitoring
  - [ ] `get_new_transactions()` - Poll for new transactions
  - [ ] Filter by target wallets
  - [ ] Filter by Kuru contract address
  - [ ] Track processed transactions (no duplicates)
- [ ] Implement `src/kuru_copytr_bot/monitoring/detector.py`:
  - [ ] `KuruEventDetector` class
  - [ ] `parse_order_placed()` - Parse OrderPlaced event
  - [ ] `parse_trade_executed()` - Parse TradeExecuted event
  - [ ] `parse_order_cancelled()` - Parse OrderCancelled event
  - [ ] Convert event logs to Trade/Order models
  - [ ] Handle decoding errors gracefully
- [ ] Add Kuru event ABIs to constants

## Acceptance Criteria
- All tests from Issue #13 pass
- Unit tests pass with mocked blockchain
- Integration test detects real testnet transactions
- No duplicate event processing
- Proper error handling for malformed events
- No functionality beyond test requirements

## Dependencies
- Issue #8: Implement Monad Blockchain Connector
- Issue #4: Implement Core Data Models
- Issue #13: Write Tests for Wallet Monitoring
