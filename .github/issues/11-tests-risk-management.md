# Write Tests for Risk Management

**Labels:** `priority: high`, `type: testing`, `mvp`, `tdd`, `risk`

## Description
Write tests for position size calculation and trade validation before implementation.

## Tasks
- [ ] Create `tests/unit/risk/test_calculator.py`:
  - [ ] Test fixed ratio copying (1.0x, 0.5x, 2.0x)
  - [ ] Test maximum position size enforcement
  - [ ] Test minimum order size enforcement
  - [ ] Test insufficient balance returns zero
  - [ ] Test margin calculation
  - [ ] Test rounding to tick size
- [ ] Create `tests/unit/risk/test_validator.py`:
  - [ ] Test balance validation
  - [ ] Test position size limits
  - [ ] Test market whitelist/blacklist
  - [ ] Test minimum order size
  - [ ] Test maximum exposure
  - [ ] Test validation error messages

## Test Examples
```python
def test_calculator_applies_copy_ratio():
    """Calculator should apply copy ratio to source size"""
    calc = PositionSizeCalculator(copy_ratio=Decimal("0.5"))
    source_size = Decimal("10.0")
    target_size = calc.calculate(source_size, available_balance=Decimal("1000"))
    assert target_size == Decimal("5.0")

def test_calculator_respects_max_position_size():
    """Calculator should not exceed max position size"""
    calc = PositionSizeCalculator(
        copy_ratio=Decimal("1.0"),
        max_position_size=Decimal("5.0")
    )
    source_size = Decimal("10.0")
    target_size = calc.calculate(source_size, available_balance=Decimal("1000"))
    assert target_size == Decimal("5.0")

def test_validator_accepts_valid_trade():
    """Validator should accept valid trades"""
    validator = TradeValidator(
        min_balance=Decimal("100"),
        max_position_size=Decimal("10")
    )
    trade = Trade(size=Decimal("5"), price=Decimal("100"), ...)
    result = validator.validate(
        trade,
        current_balance=Decimal("1000"),
        current_position=Decimal("0")
    )
    assert result.is_valid
    assert result.reason is None
```

## Acceptance Criteria
- All risk management logic tested
- Tests cover edge cases (zero balance, max limits)
- Tests verify error messages are clear
- Calculator tests verify decimal precision
- Validator tests verify all validation rules
- All tests initially fail

## Dependencies
- Issue #4: Implement Core Data Models
