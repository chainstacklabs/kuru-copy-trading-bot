# Implement Risk Management

**Labels:** `priority: high`, `type: implementation`, `mvp`, `tdd`, `risk`

## Description
Implement position size calculator and trade validator to pass all tests from Issue #11.

## Tasks
- [ ] Implement `src/kuru_copytr_bot/risk/calculator.py`:
  - [ ] `PositionSizeCalculator` class
  - [ ] `calculate()` - Calculate target position size
  - [ ] Apply copy ratio
  - [ ] Enforce maximum position size
  - [ ] Enforce minimum order size
  - [ ] Check available balance
  - [ ] Round to tick size
- [ ] Implement `src/kuru_copytr_bot/risk/validator.py`:
  - [ ] `TradeValidator` class
  - [ ] `validate()` - Validate trade against all rules
  - [ ] `ValidationResult` data class (is_valid, reason)
  - [ ] Balance validation
  - [ ] Position size validation
  - [ ] Market whitelist/blacklist validation
  - [ ] Minimum size validation
  - [ ] Return clear error messages

## Acceptance Criteria
- All tests from Issue #11 pass
- Calculator uses Decimal for precision
- Validator returns detailed results
- Clear error messages for each validation failure
- No functionality beyond test requirements

## Dependencies
- Issue #4: Implement Core Data Models
- Issue #11: Write Tests for Risk Management
