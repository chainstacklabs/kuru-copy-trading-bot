# WI-003: Implement Real Orderbook Price Fetching in estimate_cost()

**Status:** Not Started
**Priority:** High
**Complexity:** Medium
**Component:** KuruClient (Platform Connector)

## Description

The `estimate_cost()` method currently uses a hardcoded price (`Decimal("2000.0")`) instead of fetching the actual market price from the orderbook. This needs to be replaced with real price data.

**File:** `src/kuru_copytr_bot/connectors/platforms/kuru.py`
**Line:** 382

## Current Implementation

```python
# Get market price (simplified - would fetch from orderbook)
if price is None:
    price = Decimal("2000.0")  # Placeholder - would fetch from orderbook
```

## Research Requirements

Before implementation, research and verify:

1. **Kuru SDK Documentation:**
   - Review orderbook API endpoints
   - Check if SDK provides orderbook querying methods
   - Understand orderbook data structure
   - Verify rate limits for orderbook requests

2. **Kuru API:**
   - Check for REST API endpoints for orderbook data
   - Review WebSocket feeds if available
   - Understand best bid/ask retrieval
   - Check for market data APIs

3. **Price Calculation:**
   - Understand how to calculate effective price for market orders
   - Review slippage calculation methods
   - Consider order size impact on price

## Requirements

### Functional Requirements

1. Fetch current orderbook data for the specified market
2. Calculate effective price based on order side (buy/sell)
3. Consider order size when estimating price
4. Handle markets with insufficient liquidity
5. Return realistic cost estimate

### Non-Functional Requirements

1. Minimize API calls (cache orderbook if appropriate)
2. Handle API failures gracefully
3. Set reasonable timeout for orderbook requests
4. Log warnings for stale data

## Acceptance Criteria

### Research Phase
- [ ] Kuru SDK orderbook API reviewed
- [ ] Orderbook data structure documented
- [ ] Price calculation method determined
- [ ] Rate limits identified and documented

### Implementation Phase
- [ ] Hardcoded price removed
- [ ] Real orderbook data fetched from Kuru API/SDK
- [ ] Best bid price used for sell orders
- [ ] Best ask price used for buy orders
- [ ] Order size considered in price calculation
- [ ] Slippage impact calculated if size affects multiple levels
- [ ] Error handling for:
  - API connection failures
  - Empty orderbook
  - Invalid market symbol
  - Timeout errors
- [ ] Appropriate logging added
- [ ] Orderbook data caching implemented (with short TTL, e.g., 1-2 seconds)

### Testing
- [ ] Unit tests for price calculation logic
- [ ] Unit tests for error handling
- [ ] Tests for both buy and sell side estimates
- [ ] Tests for large orders affecting multiple price levels
- [ ] Integration test with real Kuru testnet (if available)
- [ ] Tests verify no hardcoded prices

### General
- [ ] No mockups or fallback hardcoded prices
- [ ] Real orderbook data used exclusively
- [ ] Code committed to current branch with message: "feat: implement real orderbook price fetching in estimate_cost (WI-003)"

## Implementation Notes

1. Consider adding orderbook caching to reduce API load
2. Implement exponential backoff for API retries
3. Add metrics/logging for price estimation accuracy
4. Consider creating a dedicated orderbook manager class
5. Handle edge cases (empty orderbook, insufficient liquidity)

## Dependencies

- None (can be implemented independently)

## Estimated Effort

4-6 hours (including research)
