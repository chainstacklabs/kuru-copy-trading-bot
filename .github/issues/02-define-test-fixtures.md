# Define Test Fixtures and Mocks

**Labels:** `priority: critical`, `type: testing`, `mvp`, `tdd-setup`

## Description
Create reusable test fixtures and mock objects for TDD across all components.

## Tasks
- [ ] Create `tests/fixtures/trades.py`:
  - [ ] Sample trade data (various sizes, sides, markets)
  - [ ] Edge cases (zero size, extreme prices)
- [ ] Create `tests/fixtures/transactions.py`:
  - [ ] Sample blockchain transaction data
  - [ ] Sample transaction receipts
- [ ] Create `tests/fixtures/events.py`:
  - [ ] Sample Kuru event logs (OrderPlaced, TradeExecuted, OrderCancelled)
  - [ ] Malformed event data for error handling tests
- [ ] Create `tests/fixtures/markets.py`:
  - [ ] Sample market parameters
  - [ ] Market configuration data
- [ ] Create `tests/mocks/blockchain.py`:
  - [ ] `MockWeb3Provider` - Mock Web3 responses
  - [ ] `MockBlockchainClient` - Mock blockchain interactions
- [ ] Create `tests/mocks/kuru.py`:
  - [ ] `MockKuruClient` - Mock Kuru API responses
- [ ] Create `tests/conftest.py`:
  - [ ] Pytest configuration
  - [ ] Shared fixtures
  - [ ] Test settings/configuration

## Tests Required
```python
# tests/fixtures/test_fixtures.py
def test_trade_fixtures_are_valid():
    """Verify all trade fixtures are valid Trade model instances"""

def test_transaction_fixtures_have_required_fields():
    """Verify transaction fixtures have all required blockchain fields"""

def test_event_fixtures_are_decodable():
    """Verify event fixtures can be decoded by Web3"""

def test_mock_blockchain_client_implements_interface():
    """Verify mock implements BlockchainConnector interface"""
```

## Acceptance Criteria
- All fixture data is realistic and valid
- Mocks implement the same interfaces as real objects
- Fixtures cover normal cases and edge cases
- Tests for fixtures themselves pass
- Fixtures are easily reusable across test files
