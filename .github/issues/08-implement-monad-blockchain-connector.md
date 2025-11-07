# Implement Monad Blockchain Connector

**Labels:** `priority: critical`, `type: implementation`, `mvp`, `tdd`, `blockchain`

## Description
Implement Monad/EVM blockchain connector to pass all tests from Issue #7.

## Tasks
- [ ] Define `BlockchainConnector` interface in `src/kuru_copytr_bot/core/interfaces.py`
- [ ] Implement `src/kuru_copytr_bot/connectors/blockchain/monad.py`:
  - [ ] `MonadClient` class implementing `BlockchainConnector`
  - [ ] Initialize Web3 provider
  - [ ] Wallet/signer setup
  - [ ] `send_transaction()` - Build, sign, submit
  - [ ] `get_transaction_receipt()` - Poll for confirmation
  - [ ] `parse_event_logs()` - Decode event logs
  - [ ] `get_balance()` - Query native token balance
  - [ ] `get_token_balance()` - Query ERC20 balance
  - [ ] `get_nonce()` - Get current nonce
  - [ ] Error handling with custom exceptions
  - [ ] Retry logic with exponential backoff
- [ ] Define exceptions in `src/kuru_copytr_bot/core/exceptions.py`:
  - [ ] `BlockchainConnectionError`
  - [ ] `TransactionFailedError`
  - [ ] `InsufficientGasError`

## Acceptance Criteria
- All tests from Issue #7 pass
- Unit tests pass with mocked Web3
- Integration tests pass with real Monad testnet
- Implements BlockchainConnector interface
- Proper error handling and retries
- No functionality beyond test requirements

## Dependencies
- Issue #1: Add Project Dependencies
- Issue #2: Define Test Fixtures and Mocks
- Issue #6: Implement Configuration Management
- Issue #7: Write Tests for Monad Blockchain Connector
