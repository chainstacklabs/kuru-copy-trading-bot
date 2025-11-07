# Write Tests for Core Data Models

**Labels:** `priority: critical`, `type: testing`, `mvp`, `tdd`, `models`

## Description
Write comprehensive tests for Trade, Order, Position, and Wallet models before implementation.

## Tasks
- [ ] Create `tests/unit/models/test_trade.py`:
  - [ ] Test Trade model creation with valid data
  - [ ] Test Trade validation (invalid prices, sizes)
  - [ ] Test Trade serialization/deserialization
  - [ ] Test decimal precision handling
- [ ] Create `tests/unit/models/test_order.py`:
  - [ ] Test Order model creation
  - [ ] Test Order status transitions
  - [ ] Test Order validation (invalid states)
  - [ ] Test partial fill calculations
- [ ] Create `tests/unit/models/test_position.py`:
  - [ ] Test Position creation and updates
  - [ ] Test PnL calculations (realized/unrealized)
  - [ ] Test position size updates on fills
  - [ ] Test average entry price calculations
- [ ] Create `tests/unit/models/test_wallet.py`:
  - [ ] Test Wallet balance updates
  - [ ] Test allowance tracking
  - [ ] Test margin balance calculations

## Test Examples
```python
def test_trade_rejects_negative_price():
    """Trade model should reject negative prices"""
    with pytest.raises(ValidationError):
        Trade(price=Decimal("-10.0"), ...)

def test_trade_rejects_negative_size():
    """Trade model should reject negative sizes"""
    with pytest.raises(ValidationError):
        Trade(size=Decimal("-5.0"), ...)

def test_order_cannot_transition_from_filled_to_cancelled():
    """Filled orders cannot be cancelled"""
    order = Order(status=OrderStatus.FILLED, ...)
    with pytest.raises(InvalidStateTransition):
        order.cancel()

def test_position_calculates_pnl_correctly():
    """Position PnL calculation should be accurate"""
    position = Position(size=Decimal("10"), entry_price=Decimal("100"))
    assert position.calculate_pnl(Decimal("110")) == Decimal("100")

def test_position_updates_average_entry_on_add():
    """Adding to position should update average entry price"""
    position = Position(size=Decimal("10"), entry_price=Decimal("100"))
    position.add(size=Decimal("10"), price=Decimal("110"))
    assert position.average_entry_price == Decimal("105")
```

## Acceptance Criteria
- All model tests written before implementation
- Tests cover happy paths and error cases
- Tests verify Pydantic validation
- Tests verify business logic (PnL, averages, etc.)
- Tests use Decimal for financial calculations
- All tests initially fail (no implementation yet)

## Dependencies
- Issue #1: Add Project Dependencies
