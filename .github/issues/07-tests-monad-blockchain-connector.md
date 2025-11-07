# Write Tests for Monad Blockchain Connector

**Labels:** `priority: critical`, `type: testing`, `mvp`, `tdd`, `blockchain`

## Description
Write tests for blockchain interaction before implementation.

## Tasks
- [ ] Create `tests/unit/connectors/test_monad_client.py`:
  - [ ] Test connection initialization
  - [ ] Test transaction building
  - [ ] Test transaction signing
  - [ ] Test transaction submission
  - [ ] Test receipt polling
  - [ ] Test event log parsing
  - [ ] Test balance queries
  - [ ] Test nonce management
  - [ ] Test error handling (network errors, reverts)
  - [ ] Test retry logic
- [ ] Create `tests/integration/test_monad_testnet.py`:
  - [ ] Test actual connection to Monad testnet
  - [ ] Test submitting real transaction
  - [ ] Test querying real balance
  - [ ] Test parsing real event logs

## Test Examples
```python
def test_monad_client_connects_successfully(mock_web3):
    """Client should connect to RPC successfully"""
    client = MonadClient(rpc_url="http://test", private_key="0x...")
    assert client.is_connected()

def test_monad_client_gets_balance(mock_web3):
    """Client should query wallet balance"""
    mock_web3.eth.get_balance.return_value = 1000000000000000000
    client = MonadClient(rpc_url="http://test", private_key="0x...")
    balance = client.get_balance("0xabc...")
    assert balance == Decimal("1.0")

def test_monad_client_submits_transaction(mock_web3):
    """Client should build, sign, and submit transactions"""
    client = MonadClient(rpc_url="http://test", private_key="0x...")
    tx_hash = client.send_transaction(to="0x...", data="0x...")
    assert tx_hash.startswith("0x")
    mock_web3.eth.send_raw_transaction.assert_called_once()

def test_monad_client_retries_on_network_error(mock_web3):
    """Client should retry on network failures"""
    mock_web3.eth.send_raw_transaction.side_effect = [
        ConnectionError(),
        "0xtxhash"
    ]
    client = MonadClient(rpc_url="http://test", private_key="0x...")
    tx_hash = client.send_transaction(to="0x...", data="0x...")
    assert tx_hash == "0xtxhash"
    assert mock_web3.eth.send_raw_transaction.call_count == 2

# Integration test (runs against real testnet)
@pytest.mark.integration
def test_connect_to_real_monad_testnet():
    """Should connect to real Monad testnet"""
    settings = Settings()  # Loads from .env
    client = MonadClient(
        rpc_url=settings.monad_rpc_url,
        private_key=settings.private_key
    )
    assert client.is_connected()
    balance = client.get_balance(settings.wallet_address)
    assert balance >= 0
```

## Acceptance Criteria
- Unit tests with mocked Web3 provider
- Integration tests with real testnet
- Tests cover all core blockchain operations
- Tests verify retry logic
- Tests verify error handling
- All tests initially fail

## Dependencies
- Issue #1: Add Project Dependencies
- Issue #2: Define Test Fixtures and Mocks
- Issue #6: Implement Configuration Management
