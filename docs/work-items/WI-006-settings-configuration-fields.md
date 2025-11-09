# WI-006: Add Missing Configuration Fields to Settings

**Status:** Not Started
**Priority:** Critical
**Complexity:** Low
**Component:** Configuration

## Description

The `Settings` class is missing several configuration fields that are referenced in `main.py`. These fields need to be added to the Settings model with proper types, validation, and documentation.

**File:** `src/kuru_copytr_bot/config/settings.py`

## Missing Fields Referenced in main.py

1. `wallet_private_key` (main.py:55) - currently named `private_key`
2. `max_position_size` (main.py:84, 89, 102)
3. `min_order_size` (main.py:85, 90)
4. `min_balance_threshold` (main.py:97, 101)
5. `max_total_exposure` (main.py:98, 103)
6. `poll_interval_seconds` (main.py:123, 140)

## Research Requirements

Before implementation, research and verify:

1. **Settings Model Structure:**
   - Review current Settings class implementation
   - Check if using Pydantic or dataclass
   - Understand validation mechanisms in place

2. **Configuration Best Practices:**
   - Review environment variable naming conventions
   - Check for configuration documentation needs
   - Understand default value requirements

3. **Field Types and Validation:**
   - Determine appropriate types for each field
   - Define reasonable default values
   - Set validation constraints (min/max, format)

## Requirements

### Functional Requirements

1. Add all missing fields to Settings class
2. Provide sensible default values
3. Add field validation where appropriate
4. Support environment variable loading
5. Add documentation for each field

### Non-Functional Requirements

1. Maintain backward compatibility if possible
2. Follow existing naming conventions
3. Use consistent type hints
4. Add helpful validation error messages

## Acceptance Criteria

### Research Phase
- [ ] Current Settings implementation reviewed
- [ ] Field types determined based on usage in main.py
- [ ] Default values researched (industry standards where applicable)
- [ ] Validation rules defined

### Implementation Phase

#### wallet_private_key
- [ ] Field added to Settings class
- [ ] Type: `str`
- [ ] Validation: 64 hex characters (or with 0x prefix = 66 chars)
- [ ] Environment variable: `WALLET_PRIVATE_KEY` or `PRIVATE_KEY`
- [ ] No default value (must be provided)
- [ ] Field marked as sensitive (not logged)
- [ ] Backward compatibility: Consider aliasing old `private_key` field

#### max_position_size
- [ ] Field added to Settings class
- [ ] Type: `Decimal` or `float`
- [ ] Validation: Greater than 0
- [ ] Environment variable: `MAX_POSITION_SIZE`
- [ ] Default value: Reasonable value (e.g., 1000.0 USDC)
- [ ] Description added explaining this is per-market limit

#### min_order_size
- [ ] Field added to Settings class
- [ ] Type: `Decimal` or `float`
- [ ] Validation: Greater than 0, less than max_position_size
- [ ] Environment variable: `MIN_ORDER_SIZE`
- [ ] Default value: Reasonable value (e.g., 10.0 USDC)
- [ ] Description added

#### min_balance_threshold
- [ ] Field added to Settings class
- [ ] Type: `Decimal` or `float`
- [ ] Validation: Greater than or equal to 0
- [ ] Environment variable: `MIN_BALANCE_THRESHOLD`
- [ ] Default value: Reasonable value (e.g., 100.0 USDC)
- [ ] Description added explaining bot stops if balance below this

#### max_total_exposure
- [ ] Field added to Settings class
- [ ] Type: `Decimal` or `float`
- [ ] Validation: Greater than 0
- [ ] Environment variable: `MAX_TOTAL_EXPOSURE`
- [ ] Default value: Reasonable value (e.g., 5000.0 USDC)
- [ ] Description added explaining this is total across all markets

#### poll_interval_seconds
- [ ] Field added to Settings class
- [ ] Type: `int` or `float`
- [ ] Validation: Greater than 0, reasonable maximum (e.g., < 3600)
- [ ] Environment variable: `POLL_INTERVAL_SECONDS`
- [ ] Default value: Reasonable value (e.g., 5 seconds)
- [ ] Description added

### Documentation
- [ ] Each field has docstring or comment explaining purpose
- [ ] Example `.env.example` file updated with new fields
- [ ] README updated if configuration documentation exists
- [ ] Type hints are correct and complete

### Testing
- [ ] Unit tests for Settings loading with all fields
- [ ] Tests for field validation (invalid values rejected)
- [ ] Tests for default values
- [ ] Tests for environment variable loading
- [ ] Tests verify private_key is not logged
- [ ] Tests verify field constraints (min_order_size < max_position_size, etc.)

### General
- [ ] All fields properly typed and validated
- [ ] No hardcoded values in application code after this change
- [ ] Backward compatibility maintained if possible
- [ ] Code committed to current branch with message: "feat: add missing configuration fields to Settings (WI-006)"

## Implementation Notes

1. If using Pydantic, use `Field()` for validation and descriptions
2. Consider using `SecretStr` type for `wallet_private_key`
3. Add validation to ensure logical constraints:
   - `min_order_size < max_position_size`
   - `min_balance_threshold > min_order_size`
4. Update `.env.example` with all new fields and descriptions
5. Consider adding configuration validation on startup

## Example Implementation

```python
from pydantic import Field, SecretStr, validator
from decimal import Decimal

class Settings(BaseSettings):
    # Wallet configuration
    wallet_private_key: SecretStr = Field(
        ...,
        description="Private key for the wallet (64 hex chars, with or without 0x prefix)",
        env="WALLET_PRIVATE_KEY"
    )

    # Risk management
    max_position_size: Decimal = Field(
        default=Decimal("1000.0"),
        gt=0,
        description="Maximum position size per market (in quote currency)"
    )

    min_order_size: Decimal = Field(
        default=Decimal("10.0"),
        gt=0,
        description="Minimum order size (in quote currency)"
    )

    # ... etc
```

## Dependencies

- None (should be implemented early as other components depend on it)

## Estimated Effort

2-3 hours (including tests and documentation)
