# Implement Python Kuru SDK Wrapper

**Labels:** `priority: critical`, `type: implementation`, `mvp`, `tdd`, `kuru`

## Description
Implement Python wrapper for Kuru Exchange to pass all tests from Issue #9.

## Tasks
- [ ] Define `PlatformConnector` interface in `src/kuru_copytr_bot/core/interfaces.py`
- [ ] Implement `src/kuru_copytr_bot/connectors/platforms/kuru.py`:
  - [ ] `KuruClient` class implementing `PlatformConnector`
  - [ ] `deposit_margin()` - Deposit tokens to margin account
  - [ ] `place_limit_order()` - Place GTC limit order
  - [ ] `place_market_order()` - Place IOC market order
  - [ ] `cancel_order()` - Cancel order by ID
  - [ ] `get_market_params()` - Fetch market configuration
  - [ ] `estimate_cost()` - Estimate trade cost
  - [ ] Transaction building for each operation
  - [ ] Gas estimation
  - [ ] ERC20 approval handling
- [ ] Add Kuru contract ABIs to constants
- [ ] Define exceptions:
  - [ ] `InsufficientBalanceError`
  - [ ] `InvalidMarketError`
  - [ ] `OrderExecutionError`

## Technical Reference
- Port from TypeScript SDK: https://github.com/Kuru-Labs/kuru-sdk
- Use Web3.py for contract interaction
- Follow same transaction structure as TypeScript SDK

## Acceptance Criteria
- All tests from Issue #9 pass
- Unit tests pass with mocked blockchain
- Integration tests pass with real Kuru testnet
- Implements PlatformConnector interface
- Properly handles approvals and gas
- No functionality beyond test requirements

## Dependencies
- Issue #8: Implement Monad Blockchain Connector
- Issue #9: Write Tests for Kuru SDK Wrapper
