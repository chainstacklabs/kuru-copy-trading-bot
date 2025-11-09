# WI-005: Implement Real Position Tracking in TradeCopier

**Status:** Not Started
**Priority:** High
**Complexity:** Medium
**Component:** TradeCopier (Trading Engine)

## Description

The `process_trade()` method in `TradeCopier` currently uses a hardcoded position value (`Decimal("0")`) with a TODO comment. This needs to fetch the actual current position from the platform.

**File:** `src/kuru_copytr_bot/trading/copier.py`
**Line:** 106

## Current Implementation

```python
current_position=Decimal("0"),  # TODO: Get actual position
```

## Research Requirements

Before implementation, research and verify:

1. **KuruClient API:**
   - Review `get_positions()` method implementation
   - Understand position data structure
   - Check how to filter positions by market
   - Verify position side and size representation

2. **Position State Management:**
   - Determine if positions should be cached
   - Understand position update frequency requirements
   - Consider race conditions with concurrent orders

3. **Risk Management Integration:**
   - Review how RiskManager uses position data
   - Understand position calculation for multiple markets
   - Check total exposure calculations

## Requirements

### Functional Requirements

1. Fetch current position for the relevant market
2. Parse position data to extract size and side
3. Handle both long and short positions correctly
4. Return zero if no position exists
5. Aggregate position across multiple orders if needed

### Non-Functional Requirements

1. Minimize API calls (cache positions with short TTL)
2. Handle API failures gracefully
3. Log position data for debugging
4. Ensure thread-safety if applicable

## Acceptance Criteria

### Research Phase
- [ ] KuruClient.get_positions() method reviewed
- [ ] Position data structure documented
- [ ] Position calculation logic understood
- [ ] Caching strategy determined

### Implementation Phase
- [ ] Hardcoded `Decimal("0")` removed
- [ ] Real position fetched from KuruClient.get_positions()
- [ ] Market parameter used to filter positions
- [ ] Position size extracted correctly
- [ ] Position side (long/short) handled correctly:
  - Long positions: positive Decimal
  - Short positions: negative Decimal
  - No position: Decimal("0")
- [ ] Multiple positions in same market aggregated if applicable
- [ ] Error handling for:
  - API connection failures
  - Invalid market
  - Malformed position data
  - Timeout errors
- [ ] Position caching implemented (optional, with ~1-5 second TTL)
- [ ] Appropriate logging added

### Testing
- [ ] Unit tests for position extraction logic
- [ ] Tests for long positions
- [ ] Tests for short positions
- [ ] Tests for no position (returns zero)
- [ ] Tests for error handling
- [ ] Tests verify position aggregation if applicable
- [ ] Integration test with KuruClient mock
- [ ] Tests verify no hardcoded values

### General
- [ ] No hardcoded position values
- [ ] Real position data from platform only
- [ ] Proper error handling and logging
- [ ] Code committed to current branch with message: "feat: implement real position tracking in TradeCopier (WI-005)"

## Implementation Notes

1. Consider creating a dedicated method `_get_current_position(market: str) -> Decimal`
2. Position caching should be short-lived to ensure accuracy
3. Handle edge cases:
   - Multiple position entries for same market
   - Positions in closing state
   - Partially filled positions
4. Consider adding position change logging for audit trail
5. Ensure position sign convention is consistent with RiskManager

## Dependencies

- None (KuruClient.get_positions() already exists)

## Estimated Effort

3-4 hours (including testing)
