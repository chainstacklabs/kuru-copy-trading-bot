# Write Tests for Kuru SDK Wrapper

**Labels:** `priority: critical`, `type: testing`, `mvp`, `tdd`, `kuru`

## Description
Write tests for Python Kuru SDK wrapper before implementation.

## Tasks
- [ ] Create `tests/unit/connectors/test_kuru_client.py`:
  - [ ] Test margin deposit
  - [ ] Test limit order placement (GTC)
  - [ ] Test market order placement (IOC)
  - [ ] Test order cancellation
  - [ ] Test market parameter fetching
  - [ ] Test cost estimation
  - [ ] Test error handling (insufficient balance, invalid market)
- [ ] Create `tests/integration/test_kuru_testnet.py`:
  - [ ] Test real margin deposit on testnet
  - [ ] Test real limit order on testnet
  - [ ] Test real order cancellation
  - [ ] Test cleanup after tests

## Test Examples
```python
def test_kuru_client_deposits_margin(mock_blockchain):
    """Client should deposit margin to Kuru"""
    client = KuruClient(blockchain=mock_blockchain, api_url="http://test")
    tx_hash = client.deposit_margin(token="USDC", amount=Decimal("100"))
    assert tx_hash.startswith("0x")
    mock_blockchain.send_transaction.assert_called_once()

def test_kuru_client_places_limit_order(mock_blockchain):
    """Client should place GTC limit order"""
    client = KuruClient(blockchain=mock_blockchain, api_url="http://test")
    order_id = client.place_limit_order(
        market="ETH-USDC",
        side=OrderSide.BUY,
        price=Decimal("2000"),
        size=Decimal("1.0"),
        post_only=True
    )
    assert order_id is not None

def test_kuru_client_rejects_insufficient_balance(mock_blockchain):
    """Client should reject orders with insufficient balance"""
    mock_blockchain.get_balance.return_value = Decimal("0")
    client = KuruClient(blockchain=mock_blockchain, api_url="http://test")
    with pytest.raises(InsufficientBalanceError):
        client.place_market_order(market="ETH-USDC", side=OrderSide.BUY, size=Decimal("1000"))

# Integration test
@pytest.mark.integration
def test_place_and_cancel_real_order_on_testnet():
    """Should place and cancel order on real Kuru testnet"""
    settings = Settings()
    blockchain = MonadClient(settings.monad_rpc_url, settings.private_key)
    kuru = KuruClient(blockchain=blockchain, api_url=settings.kuru_api_url)

    # Place order
    order_id = kuru.place_limit_order(
        market="ETH-USDC",
        side=OrderSide.BUY,
        price=Decimal("1000"),  # Far from market to avoid fill
        size=Decimal("0.01"),
        post_only=True
    )
    assert order_id is not None

    # Cancel order
    tx_hash = kuru.cancel_order(order_id)
    assert tx_hash.startswith("0x")
```

## Acceptance Criteria
- Unit tests with mocked blockchain
- Integration tests with real Kuru testnet
- Tests cover all essential SDK methods
- Tests verify error handling
- Integration tests clean up after themselves
- All tests initially fail

## Dependencies
- Issue #4: Implement Core Data Models
- Issue #8: Implement Monad Blockchain Connector

## Technical Reference
- TypeScript SDK: https://github.com/Kuru-Labs/kuru-sdk
