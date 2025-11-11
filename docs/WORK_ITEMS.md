# Work Items - Production Readiness

**Status:** In Progress
**Last Updated:** 2025-01-11
**Test-Driven Approach:** All items require tests BEFORE implementation

---

## 📚 Important Reference

**For ALL work items:** When you have questions about:
- Kuru Exchange API endpoints and data structures
- Smart contract functions and parameters
- WebSocket event formats
- Margin account operations
- Error codes and their meanings

**ALWAYS examine:** [docs/KURU_API_SPEC.md](KURU_API_SPEC.md)

This is the authoritative reference for all Kuru Exchange integrations in this bot.

---

## Work Item Index

### Phase 1: Critical Blockers (P0)
- [WI-001](#wi-001-implement-blockchain-contract-read-functionality) - Implement blockchain contract read functionality
- [WI-002](#wi-002-integrate-margin-account-balance-system) - Integrate margin account balance system
- [WI-003](#wi-003-fix-market-order-token-address-resolution) - Fix market order token address resolution

### Phase 2: Core Reliability (P1)
- [WI-004](#wi-004-implement-order-fill-tracking-system) - Implement order fill tracking system
- [WI-005](#wi-005-build-failed-order-retry-mechanism) - Build failed order retry mechanism
- [WI-006](#wi-006-implement-position-tracking-and-reconciliation) - Implement position tracking and reconciliation

### Phase 3: Production Hardening (P2)
- [WI-007](#wi-007-add-transaction-simulation-and-validation) - Add transaction simulation and validation
- [WI-008](#wi-008-implement-aggregate-risk-management) - Implement aggregate risk management
- [WI-009](#wi-009-build-comprehensive-error-recovery) - Build comprehensive error recovery
- [WI-010](#wi-010-add-gas-price-monitoring-and-limits) - Add gas price monitoring and limits

### Phase 4: Operational Excellence (P3)
- [WI-011](#wi-011-implement-position-synchronization-checker) - Implement position synchronization checker
- [WI-012](#wi-012-add-rate-limiting-and-throttling) - Add rate limiting and throttling
- [WI-013](#wi-013-build-health-check-and-monitoring-api) - Build health check and monitoring API

---

## Phase 1: Critical Blockers (P0)

### WI-001: Implement Blockchain Contract Read Functionality

**Priority:** P0 - BLOCKING
**Status:** 🔴 Not Started
**Depends On:** None
**Blocks:** All contract read operations, market parameter fetching, orderbook queries

#### Problem Statement
The `MonadClient` is missing the `call_contract_function()` method that is called 4 times in `KuruClient`. This causes the bot to crash on startup when attempting to fetch market parameters, orderbook data, or vault parameters.

**API Reference:** See [KURU_API_SPEC.md Section 3](KURU_API_SPEC.md#3-smart-contract---read-operations) for contract read operations: `getMarketParams()`, `getL2Book()`, `getVaultParams()`.

#### Acceptance Criteria
1. ✅ `BlockchainConnector` interface defines `call_contract_function()` method
2. ✅ `MonadClient` implements `call_contract_function()` with proper Web3.py contract calls
3. ✅ Method supports both view and pure function calls
4. ✅ Retry logic implemented with tenacity (same as other methods)
5. ✅ Returns decoded values matching ABI specification
6. ✅ Raises `BlockchainConnectionError` on connection failures
7. ✅ **NO placeholder values allowed**
8. ✅ **NO hardcoded contract addresses**
9. ✅ **NO mock/stub implementations**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/connectors/blockchain/test_monad_contract_calls.py

def test_call_contract_function_view_function_success():
    """Test successful view function call returns decoded data"""
    # Given: Connected MonadClient with mock web3
    # When: call_contract_function() with valid view function
    # Then: Returns decoded result from contract

def test_call_contract_function_with_arguments():
    """Test contract function call with arguments"""
    # Given: Function requiring arguments (e.g., balanceOf(address))
    # When: call_contract_function() with args list
    # Then: Calls contract with correct encoded arguments

def test_call_contract_function_connection_failure():
    """Test connection error handling"""
    # Given: Disconnected blockchain
    # When: call_contract_function() called
    # Then: Raises BlockchainConnectionError after retries

def test_call_contract_function_invalid_abi():
    """Test invalid ABI handling"""
    # Given: Invalid ABI specification
    # When: call_contract_function() called
    # Then: Raises ValueError with clear message

def test_call_contract_function_retries_on_timeout():
    """Test retry logic on network timeout"""
    # Given: Network experiencing timeouts
    # When: call_contract_function() called
    # Then: Retries 3 times before failing
```

**Integration Tests:**
```python
# tests/integration/test_kuru_contract_reads.py

def test_get_market_params_returns_valid_data():
    """Test fetching real market params from testnet"""
    # Given: KuruClient connected to testnet
    # When: get_market_params(market_address) called
    # Then: Returns MarketParams with valid tick_size, min_size, etc.

def test_fetch_orderbook_returns_bids_and_asks():
    """Test fetching orderbook from contract"""
    # Given: Market with active orders
    # When: fetch_orderbook() called
    # Then: Returns L2Book with bid and ask levels

def test_get_vault_params_returns_amm_data():
    """Test fetching AMM vault parameters"""
    # Given: Market with AMM vault
    # When: get_vault_params() called
    # Then: Returns vault balance and price data
```

#### Implementation Files
- `src/kuru_copytr_bot/core/interfaces.py` - Add method to interface
- `src/kuru_copytr_bot/connectors/blockchain/monad.py` - Implement method
- `tests/unit/connectors/blockchain/test_monad_contract_calls.py` - Unit tests
- `tests/integration/test_kuru_contract_reads.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass (100% coverage for new method)
- [ ] All integration tests pass on testnet
- [ ] `KuruClient.get_market_params()` successfully fetches data
- [ ] `KuruClient.fetch_orderbook()` successfully fetches data
- [ ] `KuruClient.get_vault_params()` successfully fetches data
- [ ] No exceptions during bot startup
- [ ] Code review approved
- [ ] Documentation updated

#### Notes
- Use Web3.py's `contract.functions.function_name(*args).call()` pattern
- Ensure proper type conversion (int, bytes, address)
- Handle both single return values and tuples
- Must work with existing ABI loading in `KuruClient._load_abis()`

---

### WI-002: Integrate Margin Account Balance System

**Priority:** P0 - CRITICAL
**Status:** 🔴 Not Started
**Depends On:** WI-001 (requires `call_contract_function`)
**Blocks:** Correct balance validation, trade execution

#### Problem Statement
The bot currently checks wallet balance instead of margin account balance. Kuru Exchange executes trades against margin account, not wallet. This causes:
1. Incorrect balance validation (checks wrong source)
2. Orders fail with "Insufficient Balance" from contract
3. Balance checks pass but order execution fails

**API Reference:** See [KURU_API_SPEC.md Section 5](KURU_API_SPEC.md#5-margin-account) for margin account operations: `deposit()`, `withdraw()`, `getBalance()`. Contract address: `0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef`.

#### Acceptance Criteria
1. ✅ `KuruClient` has `get_margin_balance(token)` method
2. ✅ Method calls `MarginAccount.getBalance(user, token)` contract function
3. ✅ `TradeCopier.process_trade()` uses margin balance for validation
4. ✅ `TradeCopier.process_order()` uses margin balance for validation
5. ✅ Supports both native token (0x0...0) and ERC20 tokens
6. ✅ Returns balance as Decimal with correct decimal places
7. ✅ **NO hardcoded token addresses**
8. ✅ **NO placeholder balance values**
9. ✅ **NO mock balance responses**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/connectors/platforms/test_kuru_margin_balance.py

def test_get_margin_balance_native_token():
    """Test fetching native token margin balance"""
    # Given: User with margin balance in native token
    # When: get_margin_balance(None) or get_margin_balance("0x0...0")
    # Then: Returns Decimal balance with 18 decimals

def test_get_margin_balance_erc20_token():
    """Test fetching ERC20 token margin balance"""
    # Given: User with USDC margin balance
    # When: get_margin_balance(usdc_address)
    # Then: Returns Decimal balance with token decimals

def test_get_margin_balance_zero_balance():
    """Test handling zero balance"""
    # Given: User with no margin balance
    # When: get_margin_balance() called
    # Then: Returns Decimal("0")

def test_get_margin_balance_invalid_token():
    """Test invalid token address handling"""
    # Given: Invalid token address
    # When: get_margin_balance("invalid")
    # Then: Raises ValueError

# tests/unit/trading/test_copier_margin_integration.py

def test_process_trade_uses_margin_balance():
    """Test trade processing checks margin balance"""
    # Given: Trade and copier with margin balance
    # When: process_trade() called
    # Then: Calls get_margin_balance(), not get_balance()

def test_process_trade_insufficient_margin_balance():
    """Test trade rejected with insufficient margin"""
    # Given: Trade requiring more margin than available
    # When: process_trade() called
    # Then: Returns None, increments _rejected_trades

def test_process_order_uses_margin_balance():
    """Test order processing checks margin balance"""
    # Given: Order and copier with margin balance
    # When: process_order() called
    # Then: Calls get_margin_balance(), not get_balance()
```

**Integration Tests:**
```python
# tests/integration/test_margin_balance_flow.py

def test_full_margin_balance_flow():
    """Test complete flow from balance check to order placement"""
    # Given: Bot with margin balance
    # When: Trade event received
    # Then: Checks margin balance, validates, places order successfully

def test_margin_balance_mismatch_with_wallet():
    """Test that margin balance differs from wallet balance"""
    # Given: User with different wallet and margin balances
    # When: Both balances checked
    # Then: Returns different values, uses margin for validation
```

#### Implementation Files
- `src/kuru_copytr_bot/connectors/platforms/kuru.py` - Add `get_margin_balance()` method
- `src/kuru_copytr_bot/trading/copier.py` - Update balance checks
- `tests/unit/connectors/platforms/test_kuru_margin_balance.py` - Unit tests
- `tests/unit/trading/test_copier_margin_integration.py` - Unit tests
- `tests/integration/test_margin_balance_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass on testnet
- [ ] `get_margin_balance()` successfully reads from contract
- [ ] `process_trade()` uses margin balance exclusively
- [ ] `process_order()` uses margin balance exclusively
- [ ] Orders execute successfully with correct balance validation
- [ ] Balance validation logs show margin balance values
- [ ] Code review approved
- [ ] Documentation updated with margin account flow

#### Notes
- MarginAccount contract address: `0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef` (from constants)
- Native token address: `0x0000000000000000000000000000000000000000`
- Must handle both 18-decimal (native) and 6-decimal (USDC) tokens
- Update logging to show margin balance vs wallet balance
- Consider caching margin balance for short duration (5-10 seconds)

---

### WI-003: Fix Market Order Token Address Resolution

**Priority:** P0 - BLOCKING
**Status:** 🔴 Not Started
**Depends On:** WI-001, WI-002
**Blocks:** Market order execution

#### Problem Statement
Line 362 in `kuru.py` contains hardcoded placeholder: `"0xUSDCAddress00000000000000000000000000000"`. This causes market orders to crash when checking balance. The token address should be dynamically resolved from market parameters.

**API Reference:** See [KURU_API_SPEC.md Section 2](KURU_API_SPEC.md#2-smart-contract---write-operations) for market order functions: `placeAndExecuteMarketBuy()`, `placeAndExecuteMarketSell()`. Token addresses in [Section 7](KURU_API_SPEC.md#7-api-endpoints).

#### Acceptance Criteria
1. ✅ `place_market_order()` resolves token address from `MarketParams`
2. ✅ Uses `quote_asset` for BUY orders (spending quote to buy base)
3. ✅ Uses `base_asset` for SELL orders (selling base for quote)
4. ✅ Balance check uses correct token address
5. ✅ Balance check uses margin balance (not wallet)
6. ✅ Works for all supported markets (MON-USDC, DAK-MON, etc.)
7. ✅ **NO hardcoded token addresses**
8. ✅ **NO placeholder values**
9. ✅ **NO skipped validation**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/connectors/platforms/test_kuru_market_orders.py

def test_place_market_buy_resolves_quote_token():
    """Test market BUY order uses quote token for balance"""
    # Given: BUY market order and market params with USDC quote
    # When: place_market_order(side=BUY) called
    # Then: Checks balance of quote_asset (USDC)

def test_place_market_sell_resolves_base_token():
    """Test market SELL order uses base token for balance"""
    # Given: SELL market order and market params with MON base
    # When: place_market_order(side=SELL) called
    # Then: Checks balance of base_asset (MON)

def test_place_market_order_insufficient_balance():
    """Test market order rejected with insufficient balance"""
    # Given: Market order exceeding balance
    # When: place_market_order() called
    # Then: Raises InsufficientBalanceError

def test_place_market_order_uses_margin_balance():
    """Test market order checks margin balance"""
    # Given: Market order and margin balance
    # When: place_market_order() called
    # Then: Calls get_margin_balance(correct_token)

def test_place_market_order_multiple_markets():
    """Test market orders work for different market pairs"""
    # Given: Multiple markets (MON-USDC, DAK-MON, CHOG-MON)
    # When: place_market_order() called for each
    # Then: Each resolves correct token address

def test_place_market_order_invalid_market():
    """Test handling of market without params"""
    # Given: Market with missing parameters
    # When: place_market_order() called
    # Then: Raises InvalidMarketError
```

**Integration Tests:**
```python
# tests/integration/test_market_order_execution.py

def test_market_buy_order_execution():
    """Test full market BUY order execution on testnet"""
    # Given: Account with USDC margin balance
    # When: place_market_order(side=BUY) executed
    # Then: Order succeeds, balance decreases

def test_market_sell_order_execution():
    """Test full market SELL order execution on testnet"""
    # Given: Account with base token balance
    # When: place_market_order(side=SELL) executed
    # Then: Order succeeds, receives quote tokens
```

#### Implementation Files
- `src/kuru_copytr_bot/connectors/platforms/kuru.py` - Fix lines 356-367
- `tests/unit/connectors/platforms/test_kuru_market_orders.py` - Unit tests
- `tests/integration/test_market_order_execution.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass on testnet
- [ ] Market BUY orders execute successfully
- [ ] Market SELL orders execute successfully
- [ ] Correct token address resolved for all markets
- [ ] Balance checks use margin balance with correct token
- [ ] No crashes or placeholder errors
- [ ] Code review approved
- [ ] Documentation updated

#### Notes
- Remove lines 356-367 entirely (the balance check section)
- Balance validation should happen in `TradeCopier` using margin balance
- `KuruClient` should focus on order execution, not validation
- Consider removing balance check from `place_market_order()` entirely

#### Implementation Guidance
```python
# BEFORE (line 356-367):
balance = self.blockchain.get_token_balance(
    self.blockchain.wallet_address,
    "0xUSDCAddress00000000000000000000000000000",  # ❌ PLACEHOLDER
)
if balance < estimated_cost:
    raise InsufficientBalanceError(...)

# AFTER:
# Remove this entire section - balance validation happens in TradeCopier
# using margin balance before calling place_market_order()
```

---

## Phase 2: Core Reliability (P1)

### WI-004: Implement Order Fill Tracking System

**Priority:** P1 - HIGH
**Status:** 🔴 Not Started
**Depends On:** WI-001, WI-002, WI-003
**Blocks:** WI-006 (position tracking)

#### Problem Statement
The bot places orders but has no mechanism to track if they fill. It listens for source wallet trades but not its own fill events. This means:
1. Bot doesn't know if mirrored orders executed
2. Cannot detect partial fills
3. Cannot calculate actual position vs intended position
4. No way to reconcile divergence from source

**API Reference:** See [KURU_API_SPEC.md Section 4](KURU_API_SPEC.md#4-websocket---real-time-updates) for WebSocket Trade events. Also [Copy trading bot flow](KURU_API_SPEC.md#copy-trading-bot-flow) for recommended implementation.

#### Acceptance Criteria
1. ✅ Bot listens to its own Trade events (not just source wallet)
2. ✅ Maintains order state: PENDING → OPEN → PARTIALLY_FILLED → FILLED
3. ✅ Tracks filled size vs total size for each order
4. ✅ Updates order mapping with fill status
5. ✅ Emits metrics for fill rate and latency
6. ✅ Handles out-of-order event delivery
7. ✅ **NO assumptions about immediate fills**
8. ✅ **NO mock fill confirmations**
9. ✅ **NO placeholder order IDs**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/test_order_tracking.py

def test_order_tracker_registers_new_order():
    """Test registering new order for tracking"""
    # Given: OrderTracker instance
    # When: register_order(order_id, size) called
    # Then: Order tracked with OPEN status

def test_order_tracker_updates_on_fill():
    """Test updating order on fill event"""
    # Given: Tracked order
    # When: on_fill(order_id, filled_size) called
    # Then: Order status updated, filled_size incremented

def test_order_tracker_marks_fully_filled():
    """Test marking order as FILLED when complete"""
    # Given: Order with size=10, filled=8
    # When: on_fill(order_id, filled_size=2) called
    # Then: Order status becomes FILLED

def test_order_tracker_handles_partial_fill():
    """Test partial fill tracking"""
    # Given: Order with size=10, filled=0
    # When: on_fill(order_id, filled_size=3) called
    # Then: Order status PARTIALLY_FILLED, filled=3

def test_order_tracker_handles_overfill():
    """Test handling fill exceeding order size"""
    # Given: Order with size=10, filled=9
    # When: on_fill(order_id, filled_size=5) called
    # Then: Logs warning, caps filled at size

def test_order_tracker_ignores_unknown_orders():
    """Test handling fill for untracked order"""
    # Given: Empty tracker
    # When: on_fill(unknown_order_id, filled_size=1)
    # Then: Logs warning, no error

# tests/unit/test_bot_fill_tracking.py

def test_bot_registers_own_orders_for_tracking():
    """Test bot registers orders after placement"""
    # Given: CopyTradingBot with order tracker
    # When: process_order() places order
    # Then: Order registered in tracker

def test_bot_listens_to_own_trade_events():
    """Test bot processes own fill events"""
    # Given: Bot with placed orders
    # When: Trade event received for bot's wallet
    # Then: Order tracker updated with fill

def test_bot_distinguishes_own_vs_source_trades():
    """Test bot separates own fills from source trades"""
    # Given: Trade event
    # When: maker_address checked
    # Then: Routes to tracker if own, copier if source
```

**Integration Tests:**
```python
# tests/integration/test_order_fill_flow.py

def test_full_order_fill_lifecycle():
    """Test order from placement through fill tracking"""
    # Given: Bot places limit order
    # When: Order fills on exchange
    # Then: Bot receives Trade event, updates tracker, marks FILLED

def test_partial_fill_tracking():
    """Test tracking order that fills in multiple chunks"""
    # Given: Large order placed
    # When: Multiple smaller fills occur
    # Then: Each fill tracked, order eventually FILLED

def test_concurrent_order_tracking():
    """Test tracking multiple orders simultaneously"""
    # Given: Bot with 5 open orders
    # When: Various fill events arrive
    # Then: All orders tracked correctly
```

#### Implementation Files
- `src/kuru_copytr_bot/trading/order_tracker.py` - New file for OrderTracker class
- `src/kuru_copytr_bot/bot.py` - Add fill event handling
- `src/kuru_copytr_bot/trading/copier.py` - Register orders after placement
- `tests/unit/test_order_tracking.py` - Unit tests
- `tests/unit/test_bot_fill_tracking.py` - Unit tests
- `tests/integration/test_order_fill_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass on testnet
- [ ] OrderTracker class implemented
- [ ] Bot listens to Trade events for own wallet
- [ ] Fill status visible in statistics
- [ ] Logging shows fill rate and latency
- [ ] Out-of-order events handled gracefully
- [ ] Code review approved
- [ ] Documentation includes fill tracking architecture

#### Notes
- Create new `OrderTracker` class to manage state
- Store mapping: `order_id -> OrderFillState`
- `OrderFillState` = {order_id, size, filled_size, status, timestamps}
- Bot needs to filter Trade events by maker_address (own vs source)
- Consider TTL for filled orders (clean up after 1 hour)
- Emit metrics: fill_rate, avg_fill_latency, partial_fill_count

---

### WI-005: Build Failed Order Retry Mechanism

**Priority:** P1 - HIGH
**Status:** 🔴 Not Started
**Depends On:** WI-001, WI-002, WI-003
**Blocks:** None

#### Problem Statement
When order placement fails (network error, gas spike, nonce conflict, contract revert), the order is lost. The bot logs the error but never retries. In production with network instability, this causes:
1. Missed trading opportunities
2. Position divergence from source
3. No recovery without manual intervention

**API Reference:** See [KURU_API_SPEC.md Section 8](KURU_API_SPEC.md#8-error-codes) for contract error codes to distinguish retriable vs permanent failures.

#### Acceptance Criteria
1. ✅ Failed orders queued for retry with exponential backoff
2. ✅ Distinguishes retriable errors from permanent failures
3. ✅ Maximum retry attempts configurable (default: 3)
4. ✅ Retry delay: 1s, 2s, 4s (exponential)
5. ✅ Permanent failures logged and reported
6. ✅ Retry queue persisted across restarts (optional)
7. ✅ Circuit breaker: stops retrying if many failures
8. ✅ **NO infinite retry loops**
9. ✅ **NO retry on user-caused errors (insufficient balance)**
10. ✅ **NO hardcoded retry delays**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/trading/test_retry_queue.py

def test_retry_queue_enqueues_failed_order():
    """Test adding failed order to retry queue"""
    # Given: RetryQueue instance
    # When: enqueue(failed_order, error) called
    # Then: Order in queue with retry_count=0

def test_retry_queue_exponential_backoff():
    """Test retry delays increase exponentially"""
    # Given: Order in queue with retry_count=2
    # When: get_next_retry_time() called
    # Then: Returns 4 seconds from now

def test_retry_queue_max_retries_exceeded():
    """Test order marked dead after max retries"""
    # Given: Order with retry_count=3, max_retries=3
    # When: should_retry() called
    # Then: Returns False, moves to dead letter queue

def test_retry_queue_distinguishes_error_types():
    """Test separating retriable from permanent errors"""
    # Given: Various exception types
    # When: is_retriable(error) called
    # Then: True for network/gas, False for validation

def test_retry_queue_circuit_breaker():
    """Test circuit breaker stops retries after many failures"""
    # Given: 10 consecutive failures in 1 minute
    # When: should_retry() called
    # Then: Returns False, circuit open

def test_retry_queue_processes_due_items():
    """Test retrieving orders ready for retry"""
    # Given: Queue with orders at different retry times
    # When: get_due_retries() called
    # Then: Returns only orders past retry time

# tests/unit/trading/test_copier_retry_integration.py

def test_copier_enqueues_failed_order():
    """Test copier adds failed orders to retry queue"""
    # Given: Copier with retry queue
    # When: process_trade() fails with network error
    # Then: Order enqueued for retry

def test_copier_retries_queued_order():
    """Test copier processes retry queue"""
    # Given: Order in retry queue, retry time passed
    # When: process_retry_queue() called
    # Then: Attempts order placement again

def test_copier_skips_permanent_failures():
    """Test copier doesn't retry validation errors"""
    # Given: Order failed with InsufficientBalanceError
    # When: Error handled
    # Then: NOT enqueued for retry
```

**Integration Tests:**
```python
# tests/integration/test_retry_flow.py

def test_retry_after_network_failure():
    """Test full retry flow after network error"""
    # Given: Order fails due to RPC timeout
    # When: Retry queue processes order after delay
    # Then: Order placed successfully on retry

def test_multiple_retry_attempts():
    """Test order retried multiple times"""
    # Given: Order fails 2 times
    # When: Retried with backoff
    # Then: Eventually succeeds on 3rd attempt
```

#### Implementation Files
- `src/kuru_copytr_bot/trading/retry_queue.py` - New file for RetryQueue class
- `src/kuru_copytr_bot/trading/copier.py` - Integrate retry queue
- `src/kuru_copytr_bot/config/settings.py` - Add retry configuration
- `tests/unit/trading/test_retry_queue.py` - Unit tests
- `tests/unit/trading/test_copier_retry_integration.py` - Unit tests
- `tests/integration/test_retry_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] RetryQueue class implemented
- [ ] Failed orders automatically retried
- [ ] Circuit breaker prevents infinite loops
- [ ] Retry statistics visible in metrics
- [ ] Dead letter queue for permanent failures
- [ ] Code review approved
- [ ] Documentation includes retry architecture

#### Notes
- **Retriable errors:** `BlockchainConnectionError`, `TransactionFailedError` (gas), `TimeoutError`
- **Permanent errors:** `InsufficientBalanceError`, `InvalidOrderError`, `TradeValidationError`
- Use `asyncio.sleep()` for retry delays
- Store retry queue in memory (optional: persist to SQLite)
- Circuit breaker: Open after 10 failures in 60 seconds, close after 5 minutes
- Configuration:
  ```python
  RETRY_MAX_ATTEMPTS = 3
  RETRY_BASE_DELAY = 1.0  # seconds
  RETRY_BACKOFF_MULTIPLIER = 2.0
  RETRY_CIRCUIT_BREAKER_THRESHOLD = 10
  RETRY_CIRCUIT_BREAKER_WINDOW = 60  # seconds
  ```

---

### WI-006: Implement Position Tracking and Reconciliation

**Priority:** P1 - HIGH
**Status:** 🔴 Not Started
**Depends On:** WI-004 (order fill tracking)
**Blocks:** WI-008 (aggregate risk), WI-011 (position sync)

#### Problem Statement
The `Position` model exists but is completely unused. The bot has no concept of current positions, PnL, or exposure. This means:
1. Cannot validate total exposure across markets
2. Cannot calculate unrealized PnL
3. Cannot detect position divergence from source
4. Cannot implement proper risk management

#### Acceptance Criteria
1. ✅ `PositionTracker` class maintains current positions per market
2. ✅ Updates positions on order fills (from WI-004)
3. ✅ Calculates unrealized PnL using current market prices
4. ✅ Tracks total notional exposure across all markets
5. ✅ Provides position summary in statistics
6. ✅ Handles both LONG and SHORT positions
7. ✅ Updates average entry price on partial fills
8. ✅ **NO assumed positions without fill confirmation**
9. ✅ **NO hardcoded position sizes**
10. ✅ **NO mock PnL calculations**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/trading/test_position_tracker.py

def test_position_tracker_opens_position_on_buy():
    """Test opening LONG position on buy fill"""
    # Given: PositionTracker with no positions
    # When: on_fill(market, side=BUY, size=10, price=100)
    # Then: Creates LONG position, size=10, entry=100

def test_position_tracker_opens_position_on_sell():
    """Test opening SHORT position on sell fill"""
    # Given: PositionTracker with no positions
    # When: on_fill(market, side=SELL, size=5, price=200)
    # Then: Creates SHORT position, size=-5, entry=200

def test_position_tracker_adds_to_long_position():
    """Test increasing LONG position"""
    # Given: Existing LONG position size=10, entry=100
    # When: on_fill(market, side=BUY, size=5, price=110)
    # Then: Position size=15, entry=103.33 (average)

def test_position_tracker_closes_position():
    """Test closing position completely"""
    # Given: LONG position size=10, entry=100
    # When: on_fill(market, side=SELL, size=10, price=110)
    # Then: Position size=0, realized_pnl=100

def test_position_tracker_reduces_position():
    """Test partially closing position"""
    # Given: LONG position size=10, entry=100
    # When: on_fill(market, side=SELL, size=3, price=110)
    # Then: Position size=7, realized_pnl=30

def test_position_tracker_calculates_unrealized_pnl():
    """Test unrealized PnL calculation"""
    # Given: LONG position size=10, entry=100
    # When: update_price(market, current_price=110)
    # Then: unrealized_pnl=100 (10 * (110-100))

def test_position_tracker_calculates_total_exposure():
    """Test total notional exposure across markets"""
    # Given: Positions in 3 markets
    # When: get_total_exposure() called
    # Then: Returns sum of abs(size * current_price)

def test_position_tracker_handles_flipped_position():
    """Test position flipping from LONG to SHORT"""
    # Given: LONG position size=10, entry=100
    # When: on_fill(market, side=SELL, size=15, price=110)
    # Then: Position size=-5, entry=110, realized_pnl for closed portion

# tests/unit/trading/test_copier_position_integration.py

def test_copier_updates_positions_on_fill():
    """Test copier updates position tracker on fill"""
    # Given: Copier with position tracker
    # When: Order fills (from fill tracking)
    # Then: Position tracker updated with fill data

def test_copier_validates_against_total_exposure():
    """Test new orders validated against total exposure"""
    # Given: Positions with total exposure = 4500 USD
    # When: New order would exceed 5000 USD limit
    # Then: Order rejected, _rejected_trades incremented
```

**Integration Tests:**
```python
# tests/integration/test_position_tracking_flow.py

def test_full_position_lifecycle():
    """Test position from open through close"""
    # Given: Bot places and fills BUY order
    # When: Later fills SELL order
    # Then: Position tracked through lifecycle, PnL calculated

def test_position_tracking_across_multiple_markets():
    """Test tracking positions in multiple markets simultaneously"""
    # Given: Bot trading in MON-USDC and DAK-MON
    # When: Orders fill in both markets
    # Then: Each position tracked separately, total exposure calculated
```

#### Implementation Files
- `src/kuru_copytr_bot/trading/position_tracker.py` - New file for PositionTracker class
- `src/kuru_copytr_bot/trading/copier.py` - Integrate position tracker
- `src/kuru_copytr_bot/bot.py` - Add position tracking hooks
- `tests/unit/trading/test_position_tracker.py` - Unit tests
- `tests/unit/trading/test_copier_position_integration.py` - Unit tests
- `tests/integration/test_position_tracking_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] PositionTracker class implemented
- [ ] Positions updated on order fills
- [ ] Unrealized PnL calculated correctly
- [ ] Total exposure tracked across markets
- [ ] Position summary in bot statistics
- [ ] Risk validation uses total exposure
- [ ] Code review approved
- [ ] Documentation includes position tracking architecture

#### Notes
- Reuse existing `Position` model from `models/position.py`
- PositionTracker maintains `dict[str, Position]` (market -> position)
- Integrate with OrderTracker (WI-004) to receive fill notifications
- Update position on each fill, not just complete fills
- Fetch current prices from orderbook for unrealized PnL
- Consider price update interval (every 10 seconds?)
- Emit metrics: total_exposure_usd, unrealized_pnl, position_count

---

## Phase 3: Production Hardening (P2)

### WI-007: Add Transaction Simulation and Validation

**Priority:** P2 - MEDIUM
**Status:** 🔴 Not Started
**Depends On:** WI-001, WI-002, WI-003
**Blocks:** None

#### Problem Statement
The bot sends transactions without simulating them first. This wastes gas on transactions that will revert. Common revert reasons:
1. Insufficient margin balance (contract-side check)
2. Invalid price (not aligned to tick size)
3. Order size below minimum
4. Slippage exceeded on market orders

#### Acceptance Criteria
1. ✅ All transactions simulated with `eth_call` before sending
2. ✅ Simulation detects common revert reasons
3. ✅ Failed simulations logged with revert reason
4. ✅ Gas estimation updated based on simulation
5. ✅ Simulation timeout: 2 seconds
6. ✅ Optional: skip simulation flag for high-speed trading
7. ✅ **NO simulations skipped by default**
8. ✅ **NO ignored simulation failures**
9. ✅ **NO mock simulation results**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/connectors/blockchain/test_transaction_simulation.py

def test_simulate_transaction_success():
    """Test successful transaction simulation"""
    # Given: Valid transaction data
    # When: simulate_transaction() called
    # Then: Returns success=True, estimated_gas

def test_simulate_transaction_revert():
    """Test transaction simulation detects revert"""
    # Given: Transaction that will revert
    # When: simulate_transaction() called
    # Then: Returns success=False, revert_reason

def test_simulate_transaction_timeout():
    """Test simulation timeout handling"""
    # Given: Slow RPC endpoint
    # When: simulate_transaction() called with timeout
    # Then: Raises TimeoutError after 2 seconds

def test_simulate_transaction_parses_revert_reason():
    """Test extracting revert reason from error"""
    # Given: Transaction reverted with custom error
    # When: simulate_transaction() called
    # Then: Returns human-readable revert reason

# tests/unit/connectors/platforms/test_kuru_simulation.py

def test_place_limit_order_simulates_first():
    """Test limit order simulated before sending"""
    # Given: Order data
    # When: place_limit_order() called
    # Then: Calls simulate_transaction(), then send_transaction()

def test_place_limit_order_simulation_failure():
    """Test order rejected on simulation failure"""
    # Given: Order that will revert
    # When: place_limit_order() called
    # Then: Raises OrderExecutionError, no transaction sent
```

**Integration Tests:**
```python
# tests/integration/test_simulation_flow.py

def test_simulation_prevents_invalid_order():
    """Test simulation catches invalid order before sending"""
    # Given: Order with price not aligned to tick size
    # When: place_limit_order() called
    # Then: Simulation fails, no gas wasted
```

#### Implementation Files
- `src/kuru_copytr_bot/connectors/blockchain/monad.py` - Add `simulate_transaction()`
- `src/kuru_copytr_bot/connectors/platforms/kuru.py` - Call simulation before sending
- `tests/unit/connectors/blockchain/test_transaction_simulation.py` - Unit tests
- `tests/unit/connectors/platforms/test_kuru_simulation.py` - Unit tests
- `tests/integration/test_simulation_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] `simulate_transaction()` implemented
- [ ] All order placement methods simulate first
- [ ] Revert reasons parsed and logged
- [ ] Gas estimation based on simulation
- [ ] Simulation metrics tracked (success rate)
- [ ] Code review approved
- [ ] Documentation updated

#### Notes
- Use `web3.eth.call()` for simulation
- Common revert reasons to decode:
  - `InsufficientBalance` (0xf4d678b8)
  - `TickSizeError` (0x272d3bf7)
  - `SizeError` (0x0a5c4f1f)
  - `PriceError` (0x91f53656)
- Consider caching simulation results for identical transactions
- Skip simulation flag: `ENABLE_TRANSACTION_SIMULATION=true` (default)

---

### WI-008: Implement Aggregate Risk Management

**Priority:** P2 - MEDIUM
**Status:** 🔴 Not Started
**Depends On:** WI-006 (position tracking)
**Blocks:** None

#### Problem Statement
The `TradeValidator` checks per-order limits but not aggregate portfolio limits. The `max_exposure_usd` parameter is interpreted as per-order, not total portfolio. This means the bot could:
1. Exceed total exposure by placing multiple small orders
2. Over-concentrate in a single market
3. Build correlated positions across markets

#### Acceptance Criteria
1. ✅ Validator checks total portfolio exposure (not just per-order)
2. ✅ Validates against `max_total_exposure` across all positions
3. ✅ Enforces market concentration limits (e.g., max 30% per market)
4. ✅ Considers existing positions when validating new orders
5. ✅ Rejects orders that would exceed portfolio limits
6. ✅ Configuration for concentration limits
7. ✅ **NO per-order interpretation of exposure limits**
8. ✅ **NO validation bypass for existing positions**
9. ✅ **NO hardcoded concentration percentages**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/risk/test_aggregate_validator.py

def test_validator_checks_total_exposure():
    """Test validation against total portfolio exposure"""
    # Given: Positions with total exposure = 4500 USD
    # When: Validate order adding 1000 USD, limit = 5000 USD
    # Then: Rejects order (would exceed limit)

def test_validator_allows_within_exposure_limit():
    """Test order allowed within exposure limit"""
    # Given: Positions with total exposure = 3000 USD
    # When: Validate order adding 500 USD, limit = 5000 USD
    # Then: Accepts order

def test_validator_checks_market_concentration():
    """Test validation against market concentration limit"""
    # Given: Position in MON-USDC = 40% of portfolio
    # When: Validate order adding to MON-USDC, limit = 30%
    # Then: Rejects order (exceeds concentration)

def test_validator_concentration_allows_reducing_position():
    """Test reducing over-concentrated position allowed"""
    # Given: Position in MON-USDC = 40% of portfolio
    # When: Validate SELL order reducing position
    # Then: Accepts order (reduces concentration)

def test_validator_considers_existing_positions():
    """Test new order validation includes existing positions"""
    # Given: Existing positions
    # When: validate() called with new order
    # Then: Calculates impact on total exposure and concentration
```

**Integration Tests:**
```python
# tests/integration/test_aggregate_risk_flow.py

def test_multiple_orders_respect_total_exposure():
    """Test multiple orders cannot exceed total exposure"""
    # Given: Bot with exposure limit 5000 USD
    # When: Multiple orders placed totaling 6000 USD
    # Then: Later orders rejected when limit approached
```

#### Implementation Files
- `src/kuru_copytr_bot/risk/validator.py` - Update validation logic
- `src/kuru_copytr_bot/config/settings.py` - Add concentration limits
- `tests/unit/risk/test_aggregate_validator.py` - Unit tests
- `tests/integration/test_aggregate_risk_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Total exposure validation implemented
- [ ] Market concentration validation implemented
- [ ] Validation considers existing positions
- [ ] Configuration options added
- [ ] Rejection reasons logged clearly
- [ ] Code review approved
- [ ] Documentation updated

#### Notes
- Require `PositionTracker` instance in `TradeValidator.__init__()`
- Calculate total exposure: `sum(abs(position.notional_value) for all positions)`
- Calculate concentration: `position.notional_value / total_exposure`
- Configuration:
  ```python
  MAX_TOTAL_EXPOSURE = 10000.0  # USD
  MAX_MARKET_CONCENTRATION = 0.30  # 30%
  MAX_POSITION_SIZE = 2000.0  # Per order (existing)
  ```
- Rename existing `max_exposure_usd` → `max_total_exposure` for clarity

---

### WI-009: Build Comprehensive Error Recovery

**Priority:** P2 - MEDIUM
**Status:** 🔴 Not Started
**Depends On:** WI-005 (retry mechanism), WI-006 (position tracking)
**Blocks:** None

#### Problem Statement
The bot has basic error handling but no comprehensive recovery strategy. When errors occur:
1. Some errors swallowed silently (line 100-103 in bot.py)
2. No context preserved for debugging
3. No alerting on critical errors
4. No graceful degradation

**API Reference:** See [KURU_API_SPEC.md Section 8](KURU_API_SPEC.md#8-error-codes) for complete list of contract error codes and their meanings for proper error classification.

#### Acceptance Criteria
1. ✅ All exceptions categorized: CRITICAL, HIGH, MEDIUM, LOW
2. ✅ CRITICAL errors trigger immediate alerting
3. ✅ Error context captured (market, order ID, state)
4. ✅ Recovery actions defined per error type
5. ✅ Circuit breaker halts bot on repeated critical errors
6. ✅ Graceful degradation: disable failing markets, continue others
7. ✅ Error metrics tracked and exposed
8. ✅ **NO silent error swallowing**
9. ✅ **NO generic catch-all handlers without logging**
10. ✅ **NO continued operation after critical errors**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/core/test_error_recovery.py

def test_error_handler_categorizes_errors():
    """Test error severity categorization"""
    # Given: Various exception types
    # When: categorize_error(exception) called
    # Then: Returns correct severity (CRITICAL, HIGH, MEDIUM, LOW)

def test_error_handler_captures_context():
    """Test error context capture"""
    # Given: Exception with context (market, order_id)
    # When: handle_error(exception, context) called
    # Then: Context preserved in error record

def test_error_handler_triggers_alert():
    """Test alerting on critical errors"""
    # Given: CRITICAL error
    # When: handle_error(exception) called
    # Then: Alert sent (log, webhook, etc.)

def test_circuit_breaker_opens_on_repeated_errors():
    """Test circuit breaker halts on error threshold"""
    # Given: 5 CRITICAL errors in 60 seconds
    # When: 6th error occurs
    # Then: Circuit breaker opens, bot halts

def test_graceful_degradation_disables_market():
    """Test disabling failing market"""
    # Given: Market with repeated errors
    # When: Error threshold exceeded
    # Then: Market disabled, other markets continue

# tests/unit/test_bot_error_handling.py

def test_bot_preserves_error_context():
    """Test bot includes context in error handling"""
    # Given: Trade processing fails
    # When: Error handled
    # Then: Context includes trade_id, market, source_wallet

def test_bot_doesnt_swallow_critical_errors():
    """Test critical errors not swallowed"""
    # Given: Critical error during trade processing
    # When: Error occurs
    # Then: Error propagated, logged, alerted
```

**Integration Tests:**
```python
# tests/integration/test_error_recovery_flow.py

def test_bot_recovers_from_network_error():
    """Test bot continues after transient network error"""
    # Given: Bot experiencing network error
    # When: Network recovers
    # Then: Bot resumes normal operation

def test_bot_halts_on_repeated_critical_errors():
    """Test bot stops on persistent critical errors"""
    # Given: Bot encountering repeated blockchain errors
    # When: Error threshold exceeded
    # Then: Bot halts gracefully with alert
```

#### Implementation Files
- `src/kuru_copytr_bot/core/error_handler.py` - New file for ErrorHandler class
- `src/kuru_copytr_bot/core/circuit_breaker.py` - New file for CircuitBreaker
- `src/kuru_copytr_bot/bot.py` - Integrate error handling
- `src/kuru_copytr_bot/trading/copier.py` - Integrate error handling
- `tests/unit/core/test_error_recovery.py` - Unit tests
- `tests/unit/test_bot_error_handling.py` - Unit tests
- `tests/integration/test_error_recovery_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] ErrorHandler class implemented
- [ ] All exceptions categorized by severity
- [ ] Critical errors trigger alerts
- [ ] Circuit breaker implemented
- [ ] Graceful degradation for failing markets
- [ ] Error metrics tracked
- [ ] Code review approved
- [ ] Documentation includes error handling guide

#### Notes
- **Error Severity:**
  - CRITICAL: Blockchain connection lost, contract error, wallet compromised
  - HIGH: Order execution failed, margin insufficient, market unavailable
  - MEDIUM: Validation failed, retry exhausted, WebSocket disconnected
  - LOW: Parsing error, non-critical timeout
- **Recovery Actions:**
  - CRITICAL: Alert, halt bot, require manual intervention
  - HIGH: Retry with backoff, alert if persistent
  - MEDIUM: Retry, log warning
  - LOW: Log info, continue
- Circuit breaker: 5 CRITICAL errors in 60 seconds → OPEN
- Alert mechanisms: Structured logs, optional webhook/email
- Remove lines 100-103 in bot.py (silent exception swallowing)

---

### WI-010: Add Gas Price Monitoring and Limits

**Priority:** P2 - MEDIUM
**Status:** 🔴 Not Started
**Depends On:** WI-001
**Blocks:** None

#### Problem Statement
The bot sends transactions at current gas price without checking if it's acceptable. During network congestion:
1. Could pay excessive gas (eating profits)
2. No option to wait for lower gas prices
3. No cost-benefit analysis (gas cost vs trade profit)

#### Acceptance Criteria
1. ✅ Gas price fetched before each transaction
2. ✅ Configurable max gas price limit
3. ✅ Transactions queued if gas too high (optional)
4. ✅ Cost-benefit check: skip if gas > expected profit
5. ✅ Gas price metrics tracked and logged
6. ✅ EIP-1559 support (base fee + priority fee)
7. ✅ **NO unlimited gas spending**
8. ✅ **NO ignored gas price spikes**
9. ✅ **NO hardcoded gas price limits**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/connectors/blockchain/test_gas_monitoring.py

def test_get_current_gas_price():
    """Test fetching current gas price"""
    # Given: Connected blockchain
    # When: get_current_gas_price() called
    # Then: Returns current base_fee and priority_fee

def test_gas_price_validator_accepts_low_gas():
    """Test transaction allowed with acceptable gas"""
    # Given: Current gas = 20 gwei, limit = 50 gwei
    # When: validate_gas_price() called
    # Then: Returns True

def test_gas_price_validator_rejects_high_gas():
    """Test transaction rejected with excessive gas"""
    # Given: Current gas = 100 gwei, limit = 50 gwei
    # When: validate_gas_price() called
    # Then: Returns False

def test_gas_cost_benefit_analysis():
    """Test gas cost vs trade profit analysis"""
    # Given: Trade profit = $5, gas cost = $10
    # When: should_execute_trade() called
    # Then: Returns False (unprofitable)

# tests/unit/connectors/platforms/test_kuru_gas_limits.py

def test_place_limit_order_checks_gas_price():
    """Test order placement validates gas price"""
    # Given: High gas price
    # When: place_limit_order() called
    # Then: Raises InsufficientGasError if above limit
```

**Integration Tests:**
```python
# tests/integration/test_gas_price_flow.py

def test_order_queued_during_high_gas():
    """Test order queued when gas too high"""
    # Given: Gas price above limit
    # When: Trade event received
    # Then: Order queued, executed when gas drops
```

#### Implementation Files
- `src/kuru_copytr_bot/connectors/blockchain/monad.py` - Add gas monitoring
- `src/kuru_copytr_bot/trading/copier.py` - Integrate gas validation
- `src/kuru_copytr_bot/config/settings.py` - Add gas configuration
- `tests/unit/connectors/blockchain/test_gas_monitoring.py` - Unit tests
- `tests/unit/connectors/platforms/test_kuru_gas_limits.py` - Unit tests
- `tests/integration/test_gas_price_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Gas price monitoring implemented
- [ ] Max gas price validation added
- [ ] Cost-benefit analysis implemented (optional)
- [ ] Gas metrics tracked (avg, max, rejected count)
- [ ] Configuration options added
- [ ] Code review approved
- [ ] Documentation updated

#### Notes
- Use `web3.eth.gas_price` for legacy, `web3.eth.fee_history()` for EIP-1559
- Configuration:
  ```python
  MAX_GAS_PRICE_GWEI = 50.0  # Maximum acceptable gas price
  MAX_PRIORITY_FEE_GWEI = 2.0  # Maximum priority fee
  ENABLE_GAS_QUEUE = False  # Queue orders when gas high
  MIN_PROFIT_TO_GAS_RATIO = 2.0  # Trade profit must be 2x gas cost
  ```
- Gas cost calculation: `gas_limit * (base_fee + priority_fee) * MON_price_usd`
- Trade profit estimation: `size * abs(source_price - current_price) * token_price_usd`
- Optional: Queue orders when gas high, execute when gas drops

---

## Phase 4: Operational Excellence (P3)

### WI-011: Implement Position Synchronization Checker

**Priority:** P3 - LOW
**Status:** 🔴 Not Started
**Depends On:** WI-006 (position tracking)
**Blocks:** None

#### Problem Statement
The bot mirrors orders but doesn't verify that its actual position matches the source trader's position. Over time, positions can diverge due to:
1. Missed events (WebSocket disconnect)
2. Failed orders
3. Partial fills
4. Manual intervention

**API Reference:** See [KURU_API_SPEC.md Section 1](KURU_API_SPEC.md#1-rest-api---read-operations) for endpoints to fetch source trader positions: `/trades/user/{user_address}` and `/orders/user/{user_address}`.

#### Acceptance Criteria
1. ✅ Periodic check (every 60 seconds) compares positions
2. ✅ Fetches source trader's position via API
3. ✅ Compares with bot's tracked position
4. ✅ Logs divergence if difference > threshold (e.g., 5%)
5. ✅ Optional: Auto-reconcile by placing adjustment order
6. ✅ Metrics for position drift over time
7. ✅ **NO assumed synchronization**
8. ✅ **NO ignored divergence**
9. ✅ **NO automatic reconciliation without validation**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/trading/test_position_sync.py

def test_position_sync_checker_detects_divergence():
    """Test detecting position mismatch"""
    # Given: Source position = 100, bot position = 95
    # When: check_sync() called
    # Then: Returns divergence = 5%

def test_position_sync_checker_within_threshold():
    """Test no alert when within threshold"""
    # Given: Source position = 100, bot position = 98, threshold = 5%
    # When: check_sync() called
    # Then: Returns OK, no alert

def test_position_sync_checker_calculates_adjustment():
    """Test calculating adjustment order size"""
    # Given: Source position = 100, bot position = 90
    # When: calculate_adjustment() called
    # Then: Returns BUY order, size = 10

def test_position_sync_fetches_source_position():
    """Test fetching source trader position"""
    # Given: Source wallet address
    # When: fetch_source_position(wallet, market) called
    # Then: Returns current position size from API
```

**Integration Tests:**
```python
# tests/integration/test_position_sync_flow.py

def test_periodic_position_sync_check():
    """Test position sync runs periodically"""
    # Given: Bot running with source trader
    # When: 60 seconds elapsed
    # Then: Position sync check executes

def test_position_sync_reconciliation():
    """Test reconciling diverged position"""
    # Given: Bot position diverged from source
    # When: Reconciliation triggered
    # Then: Adjustment order placed, positions aligned
```

#### Implementation Files
- `src/kuru_copytr_bot/trading/position_sync.py` - New file for PositionSyncChecker
- `src/kuru_copytr_bot/bot.py` - Add periodic sync checks
- `src/kuru_copytr_bot/connectors/platforms/kuru.py` - Add source position fetching
- `tests/unit/trading/test_position_sync.py` - Unit tests
- `tests/integration/test_position_sync_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] PositionSyncChecker implemented
- [ ] Periodic checks running
- [ ] Divergence logged and alerted
- [ ] Optional reconciliation working
- [ ] Metrics tracked (drift_percentage, sync_frequency)
- [ ] Code review approved
- [ ] Documentation updated

#### Notes
- Fetch source position: Sum open orders + filled trades from API
- Compare: `abs(bot_position - source_position) / source_position`
- Threshold: 5% divergence triggers alert
- Reconciliation: Place adjustment order if divergence > 10%
- Configuration:
  ```python
  POSITION_SYNC_INTERVAL = 60  # seconds
  POSITION_SYNC_DIVERGENCE_THRESHOLD = 0.05  # 5%
  POSITION_SYNC_AUTO_RECONCILE = False
  POSITION_SYNC_RECONCILE_THRESHOLD = 0.10  # 10%
  ```
- Use REST API: `GET /trades/user/{source_address}` to calculate position

---

### WI-012: Add Rate Limiting and Throttling

**Priority:** P3 - LOW
**Status:** 🔴 Not Started
**Depends On:** None
**Blocks:** None

#### Problem Statement
The bot has no rate limiting. If source trader places many orders rapidly:
1. Bot floods exchange with orders
2. Could hit API/contract rate limits
3. Excessive gas spending
4. No cooldown between failed attempts

#### Acceptance Criteria
1. ✅ Maximum orders per minute configurable
2. ✅ Cooldown period after order placement
3. ✅ Separate limits for different order types
4. ✅ Queue orders when limit reached
5. ✅ Metrics for rate limit hits
6. ✅ Graceful handling of external rate limits (429 errors)
7. ✅ **NO unlimited order submission**
8. ✅ **NO ignored rate limit errors**
9. ✅ **NO hardcoded rate limits**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/trading/test_rate_limiter.py

def test_rate_limiter_allows_within_limit():
    """Test request allowed within rate limit"""
    # Given: RateLimiter with 10 requests/minute
    # When: 5 requests made
    # Then: All allowed

def test_rate_limiter_blocks_over_limit():
    """Test request blocked when limit exceeded"""
    # Given: RateLimiter with 10 requests/minute
    # When: 11th request attempted
    # Then: Blocked, returns False

def test_rate_limiter_resets_after_window():
    """Test rate limit resets after time window"""
    # Given: RateLimiter at limit
    # When: 60 seconds elapsed
    # Then: Limit reset, requests allowed

def test_rate_limiter_different_limits_per_type():
    """Test different limits for limit vs market orders"""
    # Given: Limit orders = 20/min, Market orders = 10/min
    # When: Requests for both types
    # Then: Each tracked separately

def test_rate_limiter_cooldown_enforced():
    """Test cooldown between orders"""
    # Given: Cooldown = 1 second
    # When: Two orders 0.5 seconds apart
    # Then: Second order blocked
```

**Integration Tests:**
```python
# tests/integration/test_rate_limit_flow.py

def test_rate_limit_queues_orders():
    """Test orders queued when rate limited"""
    # Given: Burst of 20 orders, limit = 10/minute
    # When: Orders processed
    # Then: First 10 executed, rest queued for next window
```

#### Implementation Files
- `src/kuru_copytr_bot/trading/rate_limiter.py` - New file for RateLimiter class
- `src/kuru_copytr_bot/trading/copier.py` - Integrate rate limiting
- `src/kuru_copytr_bot/config/settings.py` - Add rate limit configuration
- `tests/unit/trading/test_rate_limiter.py` - Unit tests
- `tests/integration/test_rate_limit_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] RateLimiter class implemented
- [ ] Rate limits enforced on order placement
- [ ] Orders queued when limit reached
- [ ] Cooldown enforced between orders
- [ ] Rate limit metrics tracked
- [ ] Code review approved
- [ ] Documentation updated

#### Notes
- Use token bucket or sliding window algorithm
- Configuration:
  ```python
  MAX_ORDERS_PER_MINUTE = 20
  MAX_LIMIT_ORDERS_PER_MINUTE = 20
  MAX_MARKET_ORDERS_PER_MINUTE = 10
  ORDER_COOLDOWN_SECONDS = 0.5
  ENABLE_RATE_LIMITING = True
  ```
- Handle external rate limits (HTTP 429) with exponential backoff
- Metrics: rate_limit_hits, queued_orders, cooldown_violations

---

### WI-013: Build Health Check and Monitoring API

**Priority:** P3 - LOW
**Status:** 🔴 Not Started
**Depends On:** WI-006 (position tracking), WI-004 (order tracking)
**Blocks:** None

#### Problem Statement
The bot has no external monitoring interface. Cannot check:
1. Is bot running?
2. Are WebSockets connected?
3. Current positions and exposure
4. Recent errors
5. Performance metrics

#### Acceptance Criteria
1. ✅ HTTP health check endpoint (GET /health)
2. ✅ Returns status: HEALTHY, DEGRADED, UNHEALTHY
3. ✅ Includes key metrics: positions, exposure, fill rate, error rate
4. ✅ WebSocket connection status
5. ✅ Recent errors (last 10)
6. ✅ Uptime and statistics
7. ✅ Optional: Prometheus metrics endpoint
8. ✅ **NO sensitive data exposed (private keys, balances)**
9. ✅ **NO unauthenticated admin operations**
10. ✅ **NO hardcoded status responses**

#### Test Requirements (TDD - Write First)

**Unit Tests:**
```python
# tests/unit/test_health_api.py

def test_health_endpoint_returns_healthy():
    """Test health check returns HEALTHY when all OK"""
    # Given: Bot running normally
    # When: GET /health
    # Then: Returns 200, status=HEALTHY

def test_health_endpoint_returns_degraded():
    """Test health check returns DEGRADED on non-critical issues"""
    # Given: One WebSocket disconnected
    # When: GET /health
    # Then: Returns 200, status=DEGRADED

def test_health_endpoint_returns_unhealthy():
    """Test health check returns UNHEALTHY on critical issues"""
    # Given: Blockchain connection lost
    # When: GET /health
    # Then: Returns 503, status=UNHEALTHY

def test_health_endpoint_includes_positions():
    """Test health response includes position summary"""
    # Given: Bot with open positions
    # When: GET /health
    # Then: Response includes position count, exposure

def test_health_endpoint_includes_recent_errors():
    """Test health response includes recent errors"""
    # Given: Recent errors occurred
    # When: GET /health
    # Then: Response includes last 10 errors (sanitized)

def test_metrics_endpoint_prometheus_format():
    """Test metrics endpoint returns Prometheus format"""
    # Given: Bot with metrics
    # When: GET /metrics
    # Then: Returns Prometheus text format
```

**Integration Tests:**
```python
# tests/integration/test_health_api_flow.py

def test_health_api_reflects_bot_state():
    """Test health API reflects actual bot state"""
    # Given: Running bot
    # When: Health endpoint polled
    # Then: Returns accurate status and metrics
```

#### Implementation Files
- `src/kuru_copytr_bot/api/health.py` - New file for health API
- `src/kuru_copytr_bot/api/server.py` - New file for HTTP server
- `src/kuru_copytr_bot/main.py` - Start API server alongside bot
- `tests/unit/test_health_api.py` - Unit tests
- `tests/integration/test_health_api_flow.py` - Integration tests

#### Definition of Done
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Health check API implemented
- [ ] Health status accurately reflects bot state
- [ ] Metrics endpoint working (optional)
- [ ] No sensitive data exposed
- [ ] API documentation written
- [ ] Code review approved
- [ ] Deployment guide updated

#### Notes
- Use FastAPI or aiohttp for HTTP server
- Health check criteria:
  - HEALTHY: All WebSockets connected, no recent critical errors
  - DEGRADED: Some WebSockets down OR recent high errors
  - UNHEALTHY: Blockchain disconnected OR circuit breaker open
- Health response format:
  ```json
  {
    "status": "HEALTHY",
    "timestamp": "2025-01-11T10:00:00Z",
    "uptime_seconds": 3600,
    "websockets": {
      "connected": 3,
      "total": 3
    },
    "positions": {
      "count": 2,
      "total_exposure_usd": 4500.0
    },
    "orders": {
      "open": 5,
      "filled_24h": 42
    },
    "errors": {
      "critical_1h": 0,
      "high_1h": 2
    }
  }
  ```
- Bind to localhost only by default (security)
- Configuration:
  ```python
  ENABLE_HEALTH_API = True
  HEALTH_API_HOST = "127.0.0.1"
  HEALTH_API_PORT = 8080
  ```

---

## Master Tracking Plan

### Progress Tracker

| Phase | Work Item | Status | Tests Written | Tests Passing | Review | Merged |
|-------|-----------|--------|---------------|---------------|--------|--------|
| **P0** | WI-001 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P0** | WI-002 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P0** | WI-003 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P1** | WI-004 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P1** | WI-005 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P1** | WI-006 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P2** | WI-007 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P2** | WI-008 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P2** | WI-009 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P2** | WI-010 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P3** | WI-011 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P3** | WI-012 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |
| **P3** | WI-013 | 🔴 Not Started | ⬜ | ⬜ | ⬜ | ⬜ |

### Dependency Graph

```
WI-001 (Contract reads) ─┬─→ WI-002 (Margin balance) ──→ WI-003 (Market orders)
                         │
                         ├─→ WI-004 (Fill tracking) ──→ WI-006 (Position tracking)
                         │
                         └─→ WI-007 (Simulation)

WI-005 (Retry) ──┬─→ WI-009 (Error recovery)
                 │
WI-006 ──────────┴─→ WI-008 (Aggregate risk)
                 └─→ WI-011 (Position sync)
                 └─→ WI-013 (Health API)

WI-010 (Gas limits) [Independent]
WI-012 (Rate limiting) [Independent]
```

### Quality Gates

Each work item must pass ALL gates before merging:

1. ✅ **Tests Written First** (TDD)
2. ✅ **All Unit Tests Pass** (100% coverage for new code)
3. ✅ **All Integration Tests Pass** (testnet)
4. ✅ **No Placeholders** (verified in code review)
5. ✅ **No Hardcoded Values** (verified in code review)
6. ✅ **No Mock/Stub Production Code** (verified in code review)
7. ✅ **Documentation Updated**
8. ✅ **Code Review Approved** (1+ reviewer)
9. ✅ **CI Pipeline Green**

### Deployment Strategy

**Phase 1 (P0):** BLOCKING - Must complete before ANY deployment
- WI-001, WI-002, WI-003
- Estimated: Critical path to testnet

**Phase 2 (P1):** Required for reliable operation
- WI-004, WI-005, WI-006
- Deploy to testnet, monitor for 1 week

**Phase 3 (P2):** Production hardening
- WI-007, WI-008, WI-009, WI-010
- Deploy to testnet, monitor for 2 weeks
- Gradual rollout with increasing limits

**Phase 4 (P3):** Operational excellence
- WI-011, WI-012, WI-013
- Can deploy independently as completed

### Success Metrics

**Phase 1 Complete:**
- Bot starts without crashes
- Market params load successfully
- Orders execute with correct balance validation
- No placeholder errors

**Phase 2 Complete:**
- 95%+ order fill rate
- Failed orders retry successfully
- Position tracking accurate
- Can run for 24+ hours without intervention

**Phase 3 Complete:**
- 99%+ transaction success rate (after simulation)
- Total exposure limits enforced
- Errors handled gracefully, bot recovers
- Gas costs under control

**Phase 4 Complete:**
- Position drift < 5%
- No rate limit violations
- Health API operational
- Full monitoring and alerting

---

## Notes

### Test-Driven Development (TDD) Mandate

**ALL work items MUST follow TDD:**

1. **Write tests FIRST** (before any implementation)
2. **Tests must FAIL initially** (red phase)
3. **Implement minimum code to pass** (green phase)
4. **Refactor while keeping tests green** (refactor phase)

**No exceptions.** Work items without tests-first approach will be rejected in code review.

### Code Quality Standards

**Explicitly FORBIDDEN:**
- ❌ Hardcoded addresses, values, or IDs
- ❌ Placeholder strings ("TODO", "FIXME", "0x000...")
- ❌ Mock/stub implementations in production code
- ❌ Disabled tests or skipped validations
- ❌ Magic numbers without constants
- ❌ Silent error swallowing (except where explicitly designed)
- ❌ Assumed state without verification
- ❌ Copy-paste code (DRY principle)

**Required for ALL code:**
- ✅ Type hints on all functions
- ✅ Docstrings (Google style)
- ✅ Error handling with specific exceptions
- ✅ Logging at appropriate levels
- ✅ Input validation
- ✅ Unit tests (100% coverage for new code)
- ✅ Integration tests (happy path + edge cases)

### Work Item Lifecycle

1. **Not Started** 🔴 - Default state
2. **Tests Written** 🟡 - Tests written and failing
3. **In Progress** 🟡 - Implementation underway
4. **Tests Passing** 🟢 - All tests green
5. **In Review** 🔵 - Code review in progress
6. **Merged** ✅ - Merged to main branch

### Review Checklist

For each work item, reviewer must verify:

- [ ] Tests written before implementation
- [ ] All acceptance criteria met
- [ ] No placeholders or hardcoded values
- [ ] No mock implementations in production
- [ ] Error handling comprehensive
- [ ] Logging appropriate
- [ ] Documentation updated
- [ ] Dependencies correct
- [ ] Definition of Done complete

---

**Document Version:** 1.0
**Last Updated:** 2025-01-11
**Status:** Ready for implementation
