# Master Plan: Kuru API Spec Alignment

**Date**: 2025-11-10
**Reference**: `docs/KURU_API_SPEC.md` (source of truth)
**Tracking**: Progress tracked in this document

## Overview

This master plan outlines isolated work items to align the copy trading bot implementation with the official Kuru API specification. Each work item is independently testable and committable.

**Total Work Items**: 23
**Completed**: 19
**In Progress**: 0
**Pending**: 4
**Blocked**: 0

---

## Phase 1: Critical Fixes (7 work items)

### WI-001: Fix Event Topic Signatures [CRITICAL]

**Status**: ✅ Completed

**Problem**: Event detection uses placeholder topics that never match real events

**Files to Modify**:
- `src/kuru_copytr_bot/monitoring/detector.py`
- `tests/unit/monitoring/test_detector.py`

**Work Steps**:
1. Update test file first:
   - Add test for `calculate_event_topic()` helper function
   - Add test cases with known event signatures and expected topics
   - Test `OrderCreated(uint40,address,uint96,uint32,bool)` signature

2. Implement in `detector.py`:
   - Add helper function: `calculate_event_topic(signature: str) -> str`
   - Calculate Keccak256 hash using `Web3.keccak(text=signature).hex()`
   - Replace placeholder constants with calculated topics:
     - `OrderCreated` event
     - `Trade` event (need to find actual signature)
     - `OrdersCanceled` event (need to find actual signature)

3. Verify contract ABI:
   - Check `OrderBook.json` for actual event signatures
   - Update if event names/parameters differ

**Acceptance Criteria**:
- ✅ Test validates Keccak256 calculation matches Web3.py output
- ✅ All three event topics are properly calculated (not hardcoded)
- ✅ Topics match actual events in OrderBook contract
- ✅ Existing detector tests pass with new topics
- ✅ Manual verification: query testnet logs to confirm topic match

**Commit Message**: `fix: replace placeholder event topics with calculated Keccak256 hashes`

---

### WI-002: Add Client Order ID (CLOID) Support [CRITICAL]

**Status**: ✅ Completed

**Problem**: Cannot track mirrored orders; no way to map bot orders to source trader orders

**Files to Modify**:
- `src/kuru_copytr_bot/models/order.py`
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/models/test_order.py`
- `tests/unit/connectors/test_kuru_client.py`

**Work Steps**:
1. Update test file first (`test_order.py`):
   - Add test for Order with CLOID
   - Test CLOID auto-generation if None
   - Test CLOID validation (max length, format)

2. Update Order model:
   - Add field: `cloid: Optional[str] = None`
   - Add validator to generate UUID if None
   - Add validator for CLOID format (alphanumeric + dash/underscore, max 36 chars)

3. Update KuruClient methods (`test_kuru_client.py` then `kuru.py`):
   - Add `cloid` parameter to `place_limit_order()` signature
   - Add `cloid` parameter to `place_market_order()` signature
   - Store CLOID in order tracking (if needed for mapping)

4. Update event detector (`detector.py`):
   - Parse `cloid` field from `OrderCreated` events
   - Parse `cloid` field from `Trade` events

**Acceptance Criteria**:
- ✅ Order model includes optional `cloid` field
- ✅ CLOID auto-generated as UUID if not provided
- ✅ CLOID validated for format and length
- ✅ Order placement methods accept CLOID parameter
- ✅ Event parsing extracts CLOID from logs
- ✅ All existing tests pass
- ✅ New tests cover CLOID generation and validation

**Commit Message**: `feat: add client order ID (CLOID) support for order tracking`

---

### WI-003: Fix REST API - Get User Orders Endpoint [CRITICAL]

**Status**: ✅ Completed

**Problem**: Using wrong endpoint; fetching single order by ID instead of all user orders

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`
- `tests/integration/test_kuru_testnet.py` (if exists)

**Work Steps**:
1. Update test file first:
   - Rename test from `test_get_order_status()` to `test_get_user_orders()`
   - Mock response with `List[Order]` instead of single order
   - Test pagination parameters (limit, offset)
   - Test filtering by user address

2. Rename method in `kuru.py`:
   - Rename `get_order_status()` to `get_user_orders()` (lines 605-631)
   - Change signature: `get_user_orders(user_address: str, limit: int = 100, offset: int = 0)`
   - Update endpoint: `GET /orders/user/{user_address}?limit={limit}&offset={offset}`
   - Return `List[Dict[str, Any]]` instead of single dict

3. Add new method for single order:
   - Add `get_order(order_id: str) -> Dict[str, Any]`
   - Use endpoint: `GET /orders/{order_id}` (keep existing endpoint for this)

4. Update callers:
   - Find usages of old `get_order_status()` method
   - Update to use `get_user_orders()` or `get_order()` as appropriate

**Acceptance Criteria**:
- ✅ `get_user_orders()` fetches all orders for a user address
- ✅ Pagination parameters work correctly
- ✅ Returns list of orders, not single order
- ✅ New `get_order()` method for single order lookup
- ✅ Tests cover pagination edge cases (empty results, offset beyond total)
- ✅ Integration test validates endpoint response format

**Commit Message**: `fix: correct REST API endpoint for fetching user orders`

---

### WI-004: Add REST API - Get Active User Orders [HIGH]

**Status**: ✅ Completed

**Problem**: No way to fetch only active orders; must fetch all and filter client-side

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`

**Work Steps**:
1. Update test file first:
   - Add `test_get_active_orders()`
   - Mock response with list of OPEN and PARTIALLY_FILLED orders only
   - Test pagination parameters

2. Add method to `kuru.py`:
   - Method: `get_active_orders(user_address: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]`
   - Endpoint: `GET /{user_address}/user/orders/active?limit={limit}&offset={offset}`
   - Parse response and return list of orders

3. Add convenience method:
   - Method: `get_my_active_orders(market: Optional[str] = None) -> List[Dict[str, Any]]`
   - Uses `self.wallet_address` from config
   - Optionally filters by market client-side

**Acceptance Criteria**:
- ✅ Method fetches only active orders (OPEN, PARTIALLY_FILLED)
- ✅ Pagination works correctly
- ✅ Returns empty list if no active orders
- ✅ Tests validate response format
- ✅ Convenience method uses wallet address from settings

**Commit Message**: `feat: add REST API endpoint for fetching active user orders`

---

### WI-005: Add REST API - Get User Trades [HIGH]

**Status**: ✅ Completed

**Problem**: Cannot fetch historical trades for analysis or verification

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`

**Work Steps**:
1. Update test file first:
   - Add `test_get_user_trades()`
   - Mock response with list of trades
   - Test timestamp filtering (start_timestamp, end_timestamp)
   - Test market_address and user_address parameters

2. Add method to `kuru.py`:
   - Method: `get_user_trades(market_address: str, user_address: str, start_timestamp: Optional[int] = None, end_timestamp: Optional[int] = None) -> List[Dict[str, Any]]`
   - Endpoint: `GET /{market_address}/trades/user/{user_address}`
   - Add query params for timestamps if provided
   - Parse response and return list of trades

3. Add convenience method:
   - Method: `get_my_trades(market: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]`
   - Convert datetime to Unix timestamp
   - Uses `self.wallet_address`

**Acceptance Criteria**:
- ✅ Method fetches trades for specific user and market
- ✅ Timestamp filtering works correctly
- ✅ Returns empty list if no trades
- ✅ Tests validate response parsing
- ✅ Convenience method handles datetime conversion

**Commit Message**: `feat: add REST API endpoint for fetching user trades with time filtering`

---

### WI-006: Align Order Model with API Response Format [HIGH]

**Status**: ✅ Completed

**Problem**: Order model fields don't match API spec; cannot deserialize responses

**Files to Modify**:
- `src/kuru_copytr_bot/models/order.py`
- `tests/unit/models/test_order.py`
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`

**Work Steps**:
1. Update test file first:
   - Add tests for `OrderResponse` model (API format)
   - Add tests for mapping `OrderResponse` -> `Order`
   - Test field aliases (market_address vs market)

2. Create API response model in `order.py`:
   ```python
   class OrderResponse(BaseModel):
       """Raw order data from Kuru API"""
       order_id: int
       market_address: str
       owner: str
       price: str
       size: str
       remaining_size: str
       is_buy: bool
       is_canceled: bool
       transaction_hash: str
       trigger_time: int
       cloid: Optional[str] = None
   ```

3. Add conversion method:
   - Method: `OrderResponse.to_order() -> Order`
   - Map fields: `market_address` -> `market`
   - Derive `side`: `OrderSide.BUY if is_buy else OrderSide.SELL`
   - Derive `status`: based on `is_canceled` and `remaining_size`
   - Convert `trigger_time` to `datetime`
   - Parse string decimals to `Decimal`

4. Update KuruClient:
   - Parse API responses into `OrderResponse` first
   - Convert to internal `Order` model
   - Return `Order` objects from API methods

**Acceptance Criteria**:
- ✅ `OrderResponse` model matches API spec exactly
- ✅ Conversion to `Order` model works correctly
- ✅ Field mapping preserves all data
- ✅ Tests validate conversion edge cases (canceled, partially filled)
- ✅ All API methods return properly typed Order objects

**Commit Message**: `refactor: align Order model with Kuru API response format`

---

### WI-007: Align Trade Model with API Response Format [HIGH]

**Status**: ✅ Completed

**Problem**: Trade field names use camelCase in API but snake_case in model

**Files to Modify**:
- `src/kuru_copytr_bot/models/trade.py`
- `tests/unit/models/test_trade.py`
- `src/kuru_copytr_bot/monitoring/detector.py`

**Work Steps**:
1. Update test file first:
   - Add tests for `TradeResponse` model (API format)
   - Add tests for field aliases (orderid vs order_id)
   - Test mapping to internal `Trade` model

2. Create API response model in `trade.py`:
   ```python
   class TradeResponse(BaseModel):
       """Raw trade data from Kuru API"""
       orderid: int
       makeraddress: str
       takeraddress: str
       isbuy: bool
       price: str
       filledsize: str
       transactionhash: str
       triggertime: int
       cloid: Optional[str] = None

       class Config:
           # Allow field access by both names
           populate_by_name = True
   ```

3. Add conversion method:
   - Method: `TradeResponse.to_trade(market: str) -> Trade`
   - Map fields to internal model
   - Convert triggertime to datetime
   - Parse string decimals to Decimal
   - Derive side from isbuy

4. Update event detector:
   - Use `TradeResponse` for parsing WebSocket events
   - Convert to internal `Trade` model

**Acceptance Criteria**:
- ✅ `TradeResponse` model matches API spec camelCase format
- ✅ Conversion to `Trade` model works correctly
- ✅ Tests validate field mapping
- ✅ Event detector uses new model
- ✅ All existing trade tests pass

**Commit Message**: `refactor: align Trade model with Kuru API response format`

---

## Phase 2: Performance Improvements (2 work items)

### WI-008: Implement WebSocket Client for Real-Time Updates [CRITICAL]

**Status**: ✅ Completed

**Problem**: Block polling is inefficient and has high latency (5+ seconds)

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/websocket/` (new package)
- `src/kuru_copytr_bot/connectors/websocket/kuru_ws_client.py` (new file)
- `tests/unit/connectors/test_kuru_ws_client.py` (new file)
- `src/kuru_copytr_bot/monitoring/monitor.py`
- `requirements.txt`

**Work Steps**:
1. Add dependencies:
   - Add `python-socketio[client]>=5.10.0` to requirements.txt
   - Add `aiohttp>=3.9.0` for async HTTP

2. Create test file first:
   - Add `test_kuru_ws_client.py`
   - Mock Socket.IO connection
   - Test event callbacks (OrderCreated, Trade, OrdersCanceled)
   - Test reconnection logic
   - Test market address filtering

3. Implement WebSocket client:
   ```python
   class KuruWebSocketClient:
       def __init__(self, ws_url: str, market_address: str):
           self.ws_url = ws_url
           self.market_address = market_address
           self.sio = socketio.AsyncClient()

       async def connect(self):
           """Connect to WebSocket with market filter"""

       async def on_order_created(self, data: Dict):
           """Handle OrderCreated event"""

       async def on_trade(self, data: Dict):
           """Handle Trade event"""

       async def on_orders_canceled(self, data: Dict):
           """Handle OrdersCanceled event"""
   ```

4. Integrate with monitor:
   - Add WebSocket mode to `WalletMonitor`
   - Use WebSocket for real-time, fallback to polling
   - Add config option: `use_websocket: bool = True`

**Acceptance Criteria**:
- ✅ WebSocket client connects to `wss://ws.testnet.kuru.io`
- ✅ Market address filter applied in connection params
- ✅ All three event types handled correctly
- ✅ Auto-reconnection on disconnect
- ✅ Events parsed into `OrderResponse`/`TradeResponse` models
- ✅ Integration with existing monitor without breaking polling mode
- ✅ Tests mock Socket.IO and validate event handling
- ✅ Manual test confirms real-time updates (< 1 second latency)

**Commit Message**: `feat: implement WebSocket client for real-time order updates`

---

### WI-009: Add Async Execution Mode for Transactions [HIGH]

**Status**: ✅ Completed

**Problem**: All transactions block until confirmed; cannot submit multiple orders in parallel

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/blockchain/monad.py`
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_monad_client.py`
- `tests/unit/connectors/test_kuru_client.py`

**Work Steps**:
1. Update test files first:
   - Add tests for async mode in `test_monad_client.py`
   - Test `send_transaction(async_execution=True)` returns tx_hash immediately
   - Test `send_transaction(async_execution=False)` waits for receipt
   - Add tests in `test_kuru_client.py` for async order placement

2. Update `MonadClient.send_transaction()`:
   - Add parameter: `async_execution: bool = False`
   - If True: return tx_hash after sending, don't wait
   - If False: wait for receipt as current behavior (lines 172-256)

3. Update all KuruClient transaction methods:
   - Add `async_execution: bool = False` parameter to:
     - `place_limit_order()`
     - `place_market_order()`
     - `cancel_orders()`
     - `deposit_margin()`
   - Pass parameter to `send_transaction()`
   - Document: async mode returns tx_hash, sync mode returns order_id/receipt

4. Add helper method:
   - Method: `wait_for_transaction(tx_hash: str, timeout: int = 120) -> Dict`
   - Allow manual waiting if needed after async submission

**Acceptance Criteria**:
- ✅ Async mode returns immediately after transaction sent
- ✅ Sync mode waits for receipt (current behavior preserved)
- ✅ All order placement methods support async parameter
- ✅ Tests validate both modes
- ✅ Documentation explains when to use each mode
- ✅ Helper method allows waiting for async transactions

**Commit Message**: `feat: add async execution mode for non-blocking transactions`

---

## Phase 3: Feature Completeness (8 work items)

### WI-010: Add REST API - Get Market Orders Endpoint [MEDIUM]

**Status**: ✅ Completed

**Problem**: Cannot bulk fetch specific orders from a market

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`

**Work Steps**:
1. Update test file first:
   - Add `test_get_market_orders()`
   - Mock response with list of orders
   - Test multiple order IDs in query

2. Add method to `kuru.py`:
   - Method: `get_market_orders(market_address: str, order_ids: List[int]) -> List[Dict[str, Any]]`
   - Endpoint: `GET /orders/market/{market_address}?order_ids={comma_separated_ids}`
   - Parse response and return list

**Acceptance Criteria**:
- ✅ Method fetches multiple orders by ID from specific market
- ✅ Handles empty order_ids list
- ✅ Tests validate response parsing

**Commit Message**: `feat: add REST API endpoint for bulk fetching market orders`

---

### WI-011: Add REST API - Get Orders by Client Order IDs [MEDIUM]

**Status**: ✅ Completed

**Problem**: Cannot lookup orders by CLOID; harder to track mirrored orders

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`

**Work Steps**:
1. Update test file first:
   - Add `test_get_orders_by_cloid()`
   - Mock POST request and response
   - Test multiple CLOIDs

2. Add method to `kuru.py`:
   - Method: `get_orders_by_cloid(market_address: str, user_address: str, client_order_ids: List[str]) -> List[Dict[str, Any]]`
   - Endpoint: `POST /orders/client`
   - Body: `{"clientOrderIds": client_order_ids, "marketAddress": market_address, "userAddress": user_address}`
   - Parse response and return list

3. Add convenience method:
   - Method: `get_my_orders_by_cloid(market: str, cloids: List[str]) -> List[Dict[str, Any]]`
   - Uses `self.wallet_address`

**Acceptance Criteria**:
- ✅ Method makes POST request with correct body format
- ✅ Returns matching orders
- ✅ Handles empty results
- ✅ Tests validate request and response

**Commit Message**: `feat: add REST API endpoint for looking up orders by CLOID`

---

### WI-012: Replace REST API with Contract Calls - Get Market Params [HIGH]

**Status**: ✅ Completed

**Problem**: Using REST API for market params; should call contract directly per spec

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`
- `src/kuru_copytr_bot/config/abis/OrderBook.json`

**Work Steps**:
1. Update OrderBook ABI:
   - Add `getMarketParams()` function ABI if missing
   - Verify return type matches spec

2. Update test file first:
   - Update `test_get_market_params()` to mock contract call instead of REST
   - Test return value parsing

3. Update `get_market_params()` method (lines 487-532):
   - Remove REST API call
   - Add contract call to `orderbook.functions.getMarketParams().call()`
   - Parse return value into `MarketParams` dict
   - Keep caching logic

4. Create `MarketParams` model:
   - Add typed model matching API spec (see WI-004 in Phase 4)
   - Use in return type

**Acceptance Criteria**:
- ✅ Method calls Orderbook contract, not REST API
- ✅ Return value matches API spec format
- ✅ Caching still works
- ✅ Tests validate contract call
- ✅ Performance comparable or better than REST

**Commit Message**: `refactor: replace REST API with contract call for market parameters`

---

### WI-013: Replace REST API with Contract Calls - Get Orderbook [HIGH]

**Status**: ✅ Completed

**Problem**: Using REST API for orderbook; should call contract directly per spec

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`
- `src/kuru_copytr_bot/config/abis/OrderBook.json`

**Work Steps**:
1. Update OrderBook ABI:
   - Add `getL2Book()` function ABI if missing
   - Verify return type: `(uint256 blockNum, Order[] buyOrders, Order[] sellOrders, ...)`

2. Update test file first:
   - Update `test_get_orderbook()` to mock contract call
   - Test parsing buy/sell orders

3. Update `get_orderbook()` method (lines 677-725):
   - Remove REST API calls
   - Add contract call to `orderbook.functions.getL2Book().call()`
   - Parse return value: extract block_num, buy_orders, sell_orders
   - Format as `{bids: [...], asks: [...]}`

4. Add new method:
   - Method: `fetch_orderbook(market: str) -> Dict[str, Any]`
   - Returns full L2Book with block_num and AMM orders
   - Keep `get_orderbook()` for backward compatibility (returns only bids/asks)

**Acceptance Criteria**:
- ✅ Method calls Orderbook contract, not REST API
- ✅ Returns bids and asks in correct format
- ✅ New method returns full L2Book with block number
- ✅ Tests validate contract call and parsing
- ✅ Backward compatibility maintained

**Commit Message**: `refactor: replace REST API with contract call for orderbook data`

---

### WI-014: Add Contract Read - Get Vault Parameters [MEDIUM]

**Status**: ✅ Completed

**Problem**: Cannot access AMM vault configuration

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`
- `src/kuru_copytr_bot/config/abis/OrderBook.json`

**Work Steps**:
1. Update OrderBook ABI:
   - Add `getVaultParams()` function ABI

2. Update test file first:
   - Add `test_get_vault_params()`
   - Mock contract call and return value

3. Add method to `kuru.py`:
   - Method: `get_vault_params(market: str) -> Dict[str, Any]`
   - Call `orderbook.functions.getVaultParams().call()`
   - Parse return value into dict

**Acceptance Criteria**:
- ✅ Method calls Orderbook contract successfully
- ✅ Returns vault parameters
- ✅ Tests validate contract call

**Commit Message**: `feat: add contract read for AMM vault parameters`

---

### WI-015: Implement Batch Update Orders [HIGH]

**Status**: ✅ Completed

**Problem**: Cannot atomically update orders; must cancel and place separately

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`
- `src/kuru_copytr_bot/config/abis/OrderBook.json`

**Work Steps**:
1. Update OrderBook ABI:
   - Add `batchUpdate()` function if missing:
     ```json
     {
       "name": "batchUpdate",
       "inputs": [
         {"name": "buy_prices", "type": "uint32[]"},
         {"name": "buy_sizes", "type": "uint96[]"},
         {"name": "sell_prices", "type": "uint32[]"},
         {"name": "sell_sizes", "type": "uint96[]"},
         {"name": "order_ids", "type": "uint40[]"},
         {"name": "post_only", "type": "bool"}
       ]
     }
     ```

2. Update test file first:
   - Add `test_batch_update_orders()`
   - Mock contract call with buy/sell orders and cancellations
   - Test validation (array length checks)

3. Add method to `kuru.py`:
   ```python
   def batch_update_orders(
       self,
       market: str,
       buy_orders: List[Tuple[Decimal, Decimal]],  # [(price, size), ...]
       sell_orders: List[Tuple[Decimal, Decimal]],
       cancel_order_ids: List[str],
       post_only: bool = False,
       async_execution: bool = False
   ) -> str:
       """Atomically cancel and replace orders"""
   ```
   - Encode buy/sell prices and sizes
   - Parse cancel order IDs to uint40
   - Call `batchUpdate()` function
   - Return tx_hash or wait for receipt

**Acceptance Criteria**:
- ✅ Method calls batchUpdate contract function
- ✅ Encodes prices/sizes correctly
- ✅ Cancels specified orders and places new ones atomically
- ✅ Validates array lengths match
- ✅ Tests cover success and validation errors
- ✅ Documentation explains use case (order replacement strategies)

**Commit Message**: `feat: implement batch update orders for atomic order replacement`

---

### WI-016: Expose Fill-or-Kill Parameter for Market Orders [MEDIUM]

**Status**: ✅ Completed

**Problem**: FOK parameter hardcoded to False; cannot use fill-or-kill orders

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `tests/unit/connectors/test_kuru_client.py`

**Work Steps**:
1. Update test file first:
   - Add test for `place_market_order(fill_or_kill=True)`
   - Verify parameter passed to contract

2. Update `place_market_order()` method (lines 290-395):
   - Add parameter: `fill_or_kill: bool = False`
   - Pass to contract calls instead of hardcoded False (lines 367, 383)
   - Update docstring to explain FOK behavior

**Acceptance Criteria**:
- ✅ Parameter exposed in method signature
- ✅ Default value is False (preserves current behavior)
- ✅ Correctly passed to contract
- ✅ Documentation explains: reverts if not fully filled
- ✅ Tests validate parameter usage

**Commit Message**: `feat: expose fill-or-kill parameter for market orders`

---

### WI-017: Add Tick Normalization for Price Validation [MEDIUM]

**Status**: ✅ Completed

**Problem**: Prices may be rejected if not aligned to tick size

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `src/kuru_copytr_bot/utils/price.py` (new file)
- `tests/unit/connectors/test_kuru_client.py`
- `tests/unit/utils/test_price.py` (new file)

**Work Steps**:
1. Create test file first (`test_price.py`):
   - Add tests for `normalize_to_tick(price, tick_size, mode)`
   - Test round_up mode
   - Test round_down mode
   - Test exact tick alignment (no rounding needed)

2. Create utility module (`price.py`):
   ```python
   def normalize_to_tick(
       price: Decimal,
       tick_size: Decimal,
       mode: Literal["round_up", "round_down"]
   ) -> Decimal:
       """Round price to nearest tick"""
   ```

3. Update `place_limit_order()` method:
   - Add parameter: `tick_normalization: Literal["round_up", "round_down"] = "round_down"`
   - Call `normalize_to_tick()` before encoding price
   - Update docstring

4. Update tests in `test_kuru_client.py`:
   - Test tick normalization in order placement
   - Verify prices aligned to tick size

**Acceptance Criteria**:
- ✅ Utility function rounds prices correctly
- ✅ Round up mode increases price to next tick
- ✅ Round down mode decreases price to previous tick
- ✅ Integrated into limit order placement
- ✅ Tests cover edge cases (exact ticks, very small ticks)
- ✅ Documentation explains tick size alignment

**Commit Message**: `feat: add tick normalization to prevent price rejection errors`

---

## Phase 4: Data Model Polish (3 work items)

### WI-018: Create Typed MarketParams Model [MEDIUM]

**Status**: ✅ Completed

**Problem**: Market params returned as untyped dict; no validation

**Files to Modify**:
- `src/kuru_copytr_bot/models/market.py` (new file)
- `tests/unit/models/test_market.py` (new file)
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`

**Work Steps**:
1. Create test file first:
   - Add `test_market.py`
   - Test `MarketParams` model validation
   - Test field types and constraints

2. Create model file:
   ```python
   class MarketParams(BaseModel):
       price_precision: int
       size_precision: int
       base_asset: str
       base_asset_decimals: int
       quote_asset: str
       quote_asset_decimals: int
       tick_size: Decimal
       min_size: Decimal
       max_size: Decimal
       taker_fee_bps: int
       maker_fee_bps: int

       @validator("*_fee_bps")
       def validate_fee_bps(cls, v):
           if v < 0 or v > 10000:
               raise ValueError("Fee must be between 0 and 10000 bps")
           return v
   ```

3. Update KuruClient:
   - Return `MarketParams` from `get_market_params()`
   - Update cache to store typed objects
   - Update callers to use typed model

**Acceptance Criteria**:
- ✅ MarketParams model matches API spec
- ✅ All fields validated
- ✅ Fee bps constrained to valid range
- ✅ Tests validate model constraints
- ✅ KuruClient returns typed objects

**Commit Message**: `refactor: create typed MarketParams model with validation`

---

### WI-019: Create Typed L2Book Model [MEDIUM]

**Status**: ✅ Completed

**Problem**: Orderbook data returned as untyped dict

**Files to Modify**:
- `src/kuru_copytr_bot/models/orderbook.py` (new file)
- `tests/unit/models/test_orderbook.py` (new file)
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`

**Work Steps**:
1. Create test file first:
   - Add `test_orderbook.py`
   - Test `L2Book` model
   - Test `PriceLevel` model

2. Create models:
   ```python
   class PriceLevel(BaseModel):
       price: Decimal
       size: Decimal

   class L2Book(BaseModel):
       block_num: int
       bids: List[PriceLevel]  # Sorted descending by price
       asks: List[PriceLevel]  # Sorted ascending by price
       timestamp: datetime = Field(default_factory=datetime.now)

       @property
       def best_bid(self) -> Optional[Decimal]:
           return self.bids[0].price if self.bids else None

       @property
       def best_ask(self) -> Optional[Decimal]:
           return self.asks[0].price if self.asks else None

       @property
       def spread(self) -> Optional[Decimal]:
           if self.best_bid and self.best_ask:
               return self.best_ask - self.best_bid
           return None
   ```

3. Update KuruClient:
   - Return `L2Book` from `fetch_orderbook()`
   - Update `get_orderbook()` to return dict for backward compatibility
   - Add `get_best_bid()` and `get_best_ask()` convenience methods

**Acceptance Criteria**:
- ✅ L2Book model includes block number and timestamp
- ✅ PriceLevel model validates price and size > 0
- ✅ Best bid/ask properties work correctly
- ✅ Spread calculation correct
- ✅ Tests validate model behavior

**Commit Message**: `refactor: create typed L2Book model for orderbook data`

---

### WI-020: Improve Event Log Parsing with Web3 Decoding [HIGH]

**Status**: ⬜ Pending

**Problem**: Manual byte manipulation for event parsing; fragile and error-prone

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `src/kuru_copytr_bot/monitoring/detector.py`
- `tests/unit/connectors/test_kuru_client.py`
- `tests/unit/monitoring/test_detector.py`

**Work Steps**:
1. Update test files first:
   - Add tests for Web3 event decoding in `test_kuru_client.py`
   - Update detector tests to use proper event logs

2. Update `_extract_order_id_from_receipt()` (lines 461-485):
   - Remove manual byte parsing
   - Use Web3 contract instance to decode events:
     ```python
     contract = self.blockchain.web3.eth.contract(
         address=market_address,
         abi=ORDERBOOK_ABI
     )
     for log in receipt["logs"]:
         try:
             event = contract.events.OrderCreated().process_log(log)
             return event["args"]["orderId"]
         except:
             continue
     ```

3. Update KuruEventDetector:
   - Add contract instance initialization
   - Replace manual parsing with Web3 decoding
   - Use contract.events.EventName().process_log()

**Acceptance Criteria**:
- ✅ Uses Web3.py contract event decoding
- ✅ No manual byte manipulation
- ✅ Handles multiple event types correctly
- ✅ Extracts all event fields accurately
- ✅ Tests validate event parsing with real log data
- ✅ Backward compatible with existing code

**Commit Message**: `refactor: replace manual event parsing with Web3.py decoding`

---

## Phase 5: Configuration and Validation (3 work items)

### WI-021: Verify and Document Contract Addresses [LOW]

**Status**: ⬜ Pending

**Problem**: Need to verify addresses are current and checksummed

**Files to Modify**:
- `src/kuru_copytr_bot/config/constants.py`
- `docs/KURU_API_SPEC.md`
- `tests/unit/config/test_constants.py`

**Work Steps**:
1. Update test file first:
   - Add test to validate address checksums
   - Test all addresses are valid Ethereum addresses

2. Verify addresses:
   - Compare with official Kuru documentation
   - Verify checksums with Web3.toChecksumAddress()
   - Update any incorrect addresses

3. Add validation:
   ```python
   from web3 import Web3

   # Validate at module import
   for name, address in [
       ("KURU_ROUTER", KURU_ROUTER_ADDRESS_TESTNET),
       ("MARGIN_ACCOUNT", KURU_MARGIN_ACCOUNT_ADDRESS_TESTNET),
       # ...
   ]:
       assert Web3.isChecksumAddress(address), f"{name} not checksummed"
   ```

**Acceptance Criteria**:
- ✅ All addresses verified against official docs
- ✅ All addresses properly checksummed
- ✅ Tests validate address format
- ✅ Documentation updated with source references

**Commit Message**: `chore: verify and validate contract address checksums`

---

### WI-022: Add REST API Error Handling Strict Mode [MEDIUM]

**Status**: ⬜ Pending

**Problem**: REST API errors silently return empty lists; hides issues

**Files to Modify**:
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`
- `src/kuru_copytr_bot/config/settings.py`
- `tests/unit/connectors/test_kuru_client.py`

**Work Steps**:
1. Add config setting:
   - Add to `Settings`: `strict_api_errors: bool = False`
   - Document behavior in docstring

2. Update test file first:
   - Add tests for strict mode behavior
   - Test exception raised on API error
   - Test graceful fallback in non-strict mode

3. Update REST API methods:
   - Check response status code
   - If error and strict mode: raise exception
   - If error and non-strict: return empty result + log warning
   - Add to methods: `get_orderbook()`, `get_market_params()`, etc.

**Acceptance Criteria**:
- ✅ Strict mode raises exceptions on API errors
- ✅ Non-strict mode returns empty results (current behavior)
- ✅ All errors logged regardless of mode
- ✅ Tests cover both modes
- ✅ Documentation explains when to use strict mode

**Commit Message**: `feat: add strict mode for REST API error handling`

---

### WI-023: Document API Endpoints and Migrate from Unofficial Endpoints [LOW]

**Status**: ⬜ Pending

**Problem**: Some endpoints not in spec; may break if removed

**Files to Modify**:
- `docs/KURU_API_SPEC.md`
- `src/kuru_copytr_bot/connectors/platforms/kuru.py`

**Work Steps**:
1. Audit current endpoints:
   - List all REST endpoints used in `kuru.py`
   - Cross-reference with API spec
   - Identify unofficial endpoints

2. Test endpoint availability:
   - Manually test each endpoint against testnet
   - Document which are confirmed working
   - Note any deprecated endpoints

3. Update code:
   - Replace unofficial endpoints with spec-compliant alternatives
   - Add fallback logic if needed
   - Update error messages

4. Update documentation:
   - Add notes about endpoint verification
   - Document any workarounds needed
   - List confirmed working endpoints

**Acceptance Criteria**:
- ✅ All endpoints documented
- ✅ Unofficial endpoints identified
- ✅ Migration plan for deprecated endpoints
- ✅ Tests validate endpoint availability
- ✅ Documentation complete

**Commit Message**: `docs: audit and migrate from unofficial API endpoints`

---

## Work Item Status Tracking

### Phase 1: Critical Fixes (7 items)
- ✅ WI-001: Fix Event Topic Signatures
- ✅ WI-002: Add CLOID Support
- ✅ WI-003: Fix Get User Orders Endpoint
- ✅ WI-004: Add Get Active Orders Endpoint
- ✅ WI-005: Add Get User Trades Endpoint
- ✅ WI-006: Align Order Model
- ⬜ WI-007: Align Trade Model

### Phase 2: Performance (2 items)
- ⬜ WI-008: Implement WebSocket Client
- ⬜ WI-009: Add Async Execution Mode

### Phase 3: Feature Completeness (8 items)
- ✅ WI-010: Add Get Market Orders Endpoint
- ✅ WI-011: Add Get Orders by CLOID Endpoint
- ✅ WI-012: Contract Call for Market Params
- ✅ WI-013: Contract Call for Orderbook
- ✅ WI-014: Add Get Vault Params
- ✅ WI-015: Implement Batch Update Orders
- ✅ WI-016: Expose Fill-or-Kill Parameter
- ✅ WI-017: Add Tick Normalization

### Phase 4: Data Model Polish (3 items)
- ✅ WI-018: Create MarketParams Model
- ✅ WI-019: Create L2Book Model
- ⬜ WI-020: Improve Event Log Parsing

### Phase 5: Configuration (3 items)
- ⬜ WI-021: Verify Contract Addresses
- ⬜ WI-022: Add Strict Error Handling Mode
- ⬜ WI-023: Document and Migrate Endpoints

---

## Commit Strategy

Each work item should result in a single commit with the specified message. Follow this workflow:

1. Start work item: Update status to "In Progress" in this document
2. Create/update tests first (TDD approach)
3. Implement changes
4. Run all tests to ensure no regressions
5. Commit with specified message
6. Update work item status to "Completed" in this document
7. Push to current branch

---

## Notes

- All work items are designed to be independently testable
- Tests must be written/updated BEFORE implementation
- Each commit should be atomic and focused on one work item
- Follow TDD: Red (test fails) -> Green (test passes) -> Refactor
- No deadlines or time estimates specified per user request
- Work items can be completed in any order within a phase
- Some work items have dependencies (noted in descriptions)

---

**Last Updated**: 2025-11-10
**Document Version**: 1.0
