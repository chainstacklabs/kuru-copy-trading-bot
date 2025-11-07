# Write Tests for Wallet Monitoring

**Labels:** `priority: high`, `type: testing`, `mvp`, `tdd`, `monitoring`

## Description
Write tests for wallet monitoring and trade detection before implementation.

## Tasks
- [ ] Create `tests/unit/monitoring/test_monitor.py`:
  - [ ] Test monitoring multiple wallets
  - [ ] Test filtering Kuru transactions
  - [ ] Test transaction detection
  - [ ] Test event emission
- [ ] Create `tests/unit/monitoring/test_detector.py`:
  - [ ] Test parsing OrderPlaced events
  - [ ] Test parsing TradeExecuted events
  - [ ] Test parsing OrderCancelled events
  - [ ] Test handling malformed events
  - [ ] Test converting events to Trade models
- [ ] Create `tests/integration/test_monitoring.py`:
  - [ ] Test monitoring real wallet on testnet
  - [ ] Test detecting real Kuru transaction

## Test Examples
```python
def test_monitor_detects_wallet_transaction(mock_blockchain):
    """Monitor should detect transactions from target wallets"""
    mock_blockchain.get_latest_transactions.return_value = [
        {"from": "0xabc", "to": "0xkuru", "hash": "0x123"}
    ]
    monitor = WalletMonitor(
        blockchain=mock_blockchain,
        target_wallets=["0xabc"]
    )
    transactions = monitor.get_new_transactions()
    assert len(transactions) == 1

def test_detector_parses_trade_executed_event():
    """Detector should parse TradeExecuted event to Trade model"""
    event_log = {
        "topics": [...],
        "data": "0x...",
    }
    detector = KuruEventDetector()
    trade = detector.parse_trade_executed(event_log)
    assert isinstance(trade, Trade)
    assert trade.size == Decimal("1.0")

def test_detector_handles_malformed_event():
    """Detector should handle malformed events gracefully"""
    event_log = {"topics": [], "data": "0xinvalid"}
    detector = KuruEventDetector()
    result = detector.parse_trade_executed(event_log)
    assert result is None
```

## Acceptance Criteria
- Unit tests with mocked blockchain
- Integration test with real testnet
- Tests verify event parsing accuracy
- Tests verify filtering logic
- Tests verify error handling
- All tests initially fail

## Dependencies
- Issue #8: Implement Monad Blockchain Connector
- Issue #4: Implement Core Data Models
