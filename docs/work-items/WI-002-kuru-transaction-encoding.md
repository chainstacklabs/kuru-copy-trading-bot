# WI-002: Implement Kuru Transaction Data Encoding

**Status:** Not Started
**Priority:** Critical
**Complexity:** High
**Component:** KuruClient (Platform Connector)

## Description

Multiple methods in `KuruClient` have stub transaction data encoding (using `"0x"` placeholder). These methods need proper contract function encoding to interact with the Kuru smart contracts.

**File:** `src/kuru_copytr_bot/connectors/platforms/kuru.py`

## Affected Methods

1. **`deposit_margin()`** - Lines 90, 116
2. **`place_limit_order()`** - Line 175
3. **`place_market_order()`** - Line 237
4. **`cancel_order()`** - Line 262
5. **`cancel_orders()`** - Line 283
6. **`_approve_token()`** - Line 517

## Research Requirements

Before implementation, research and verify:

1. **Kuru SDK Documentation:**
   - Review official Kuru SDK documentation
   - Check if SDK provides contract ABIs
   - Look for example transaction encodings
   - Verify contract addresses for testnet/mainnet

2. **Kuru Smart Contracts:**
   - Obtain official Kuru contract ABIs
   - Review contract function signatures
   - Understand function parameters and types
   - Check for any special encoding requirements

3. **Web3.py Contract Encoding:**
   - Review web3.py contract interaction methods
   - Understand `contract.encodeABI()` usage
   - Check for batch transaction encoding support

4. **Order ID Extraction:**
   - Research how to parse order IDs from transaction receipts
   - Check if Kuru emits events with order IDs
   - Understand event log structure

## Requirements

### Functional Requirements

1. Encode deposit margin transactions (native and ERC20)
2. Encode limit order placement with all parameters
3. Encode market order placement with slippage handling
4. Encode single order cancellation
5. Encode batch order cancellation
6. Encode ERC20 token approval
7. Extract order IDs from transaction receipts

### Non-Functional Requirements

1. Use official Kuru contract ABIs (not hardcoded)
2. Validate all parameters before encoding
3. Handle encoding errors gracefully
4. Log transaction data for debugging

## Acceptance Criteria

### Research Phase
- [ ] Kuru SDK documentation reviewed
- [ ] Kuru contract ABIs obtained (official source)
- [ ] Contract function signatures documented
- [ ] Event schemas documented (for order ID extraction)
- [ ] Example transactions analyzed (if available on explorer)

### Implementation Phase

#### deposit_margin()
- [ ] Native token deposit encoding implemented
- [ ] ERC20 token deposit encoding implemented
- [ ] Contract ABI loaded correctly
- [ ] Parameters validated before encoding
- [ ] Transaction data is valid hex string (not "0x")

#### place_limit_order()
- [ ] Order parameters encoded correctly (market, side, price, size, post_only)
- [ ] Order ID extraction from receipt implemented
- [ ] Event logs parsed to get order ID
- [ ] No hardcoded tx_hash as order_id

#### place_market_order()
- [ ] Market order parameters encoded correctly
- [ ] Slippage parameter included in encoding
- [ ] Quote token address resolved (not hardcoded placeholder)
- [ ] Order ID extraction from receipt implemented

#### cancel_order()
- [ ] Single order cancellation encoded correctly
- [ ] Order ID parameter validated

#### cancel_orders()
- [ ] Batch cancellation encoded correctly
- [ ] Multiple order IDs handled properly

#### _approve_token()
- [ ] ERC20 approve function encoded correctly
- [ ] Spender address (Kuru contract) used
- [ ] Amount parameter encoded properly

### Testing
- [ ] Unit tests for each encoding method
- [ ] Tests verify encoded data structure
- [ ] Tests verify parameter handling
- [ ] Integration tests with testnet (if available)
- [ ] Tests verify order ID extraction from receipts

### General
- [ ] No mockups, stubs, or fallbacks
- [ ] Real contract interactions only
- [ ] Error handling for encoding failures
- [ ] Logging added for transaction data
- [ ] Code committed to current branch with message: "feat: implement Kuru transaction encoding for all methods (WI-002)"

## Implementation Notes

1. Store contract ABIs in `src/kuru_copytr_bot/config/abis/` directory
2. Create helper methods for common encoding patterns
3. Use web3.py's `contract.encodeABI()` for type safety
4. Consider creating a separate module for contract interactions
5. Document the contract interface in code comments

## Dependencies

- WI-004 (Kuru contract address constant must be updated first)

## Estimated Effort

12-16 hours (including research and testing)
