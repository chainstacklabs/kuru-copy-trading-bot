# Implement Core Data Models

**Labels:** `priority: critical`, `type: implementation`, `mvp`, `tdd`, `models`

## Description
Implement Pydantic data models to pass all tests from Issue #3.

## Tasks
- [ ] Define enums in `src/kuru_copytr_bot/core/enums.py`:
  - [ ] `OrderSide` (BUY, SELL)
  - [ ] `OrderType` (LIMIT, MARKET, GTC, IOC)
  - [ ] `OrderStatus` (PENDING, OPEN, FILLED, PARTIALLY_FILLED, CANCELLED, FAILED)
- [ ] Implement `src/kuru_copytr_bot/models/trade.py`:
  - [ ] All fields with proper types (Decimal for prices/sizes)
  - [ ] Pydantic validators for price/size > 0
  - [ ] Timestamp handling
- [ ] Implement `src/kuru_copytr_bot/models/order.py`:
  - [ ] All fields with proper types
  - [ ] Status transition logic
  - [ ] Partial fill tracking
- [ ] Implement `src/kuru_copytr_bot/models/position.py`:
  - [ ] Position tracking fields
  - [ ] PnL calculation methods
  - [ ] Average entry price calculation
  - [ ] Position update methods
- [ ] Implement `src/kuru_copytr_bot/models/wallet.py`:
  - [ ] Balance tracking
  - [ ] Allowance tracking
  - [ ] Margin calculations

## Acceptance Criteria
- All tests from Issue #3 pass
- Models use Pydantic BaseModel
- Decimal used for all financial values
- Type hints complete and pass mypy strict checks
- No additional functionality beyond test requirements

## Dependencies
- Issue #1: Add Project Dependencies
- Issue #3: Write Tests for Core Data Models
