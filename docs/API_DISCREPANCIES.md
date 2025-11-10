# API Spec vs Implementation Discrepancies

**Date**: 2025-11-10
**Reference**: `docs/KURU_API_SPEC.md` (source of truth)
**Current Implementation**: `src/kuru_copytr_bot/`

## Executive Summary

This document identifies discrepancies between the Kuru API specification (reverse-engineered from the official Kuru SDK) and the current bot implementation. The API spec is considered the source of truth for all refactoring work.

**Status**: 23 discrepancies identified across 6 categories

---

## 1. REST API Endpoints (9 discrepancies)

### 1.1 Get User Orders Endpoint - INCORRECT

**API Spec**: `GET /orders/user/{user_address}?limit={limit}&offset={offset}`

**Current Implementation**: `GET /orders/{order_id}` (line: `kuru.py:605-631`)

**Impact**: Cannot fetch all orders for a user; only single order lookup

**Expected Behavior**:
- Endpoint should accept user address, not order ID
- Should support pagination with limit/offset
- Should return `List[Order]` not single order

---

### 1.2 Get Active User Orders - MISSING

**API Spec**: `GET /{user_address}/user/orders/active?limit={limit}&offset={offset}`

**Current Implementation**: None

**Impact**: No way to get only active orders; must fetch all and filter client-side

**Expected Behavior**:
- Fetch only OPEN and PARTIALLY_FILLED orders
- Support pagination
- Return `List[Order]`

---

### 1.3 Get User Trades - MISSING

**API Spec**: `GET /{market_address}/trades/user/{user_address}?start_timestamp={start}&end_timestamp={end}`

**Current Implementation**: None

**Impact**: Cannot fetch historical trades for monitoring or analysis

**Expected Behavior**:
- Filter trades by market and user
- Support time range filtering
- Return `List[Trade]`

---

### 1.4 Get Market Orders - MISSING

**API Spec**: `GET /orders/market/{market_address}?order_ids={ids}`

**Current Implementation**: None

**Impact**: Cannot bulk fetch specific orders from a market

**Expected Behavior**:
- Fetch multiple orders by ID from specific market
- Support comma-separated order_ids parameter
- Return `List[Order]`

---

### 1.5 Get Orders by Client Order IDs - MISSING

**API Spec**: `POST /orders/client` with body `{clientOrderIds[], marketAddress, userAddress}`

**Current Implementation**: None

**Impact**: Cannot track orders by CLOID; harder to match mirrored orders

**Expected Behavior**:
- Lookup orders by custom client-assigned IDs
- Support batch lookup
- Return `List[Order]`

---

### 1.6 Get Market Parameters - WRONG SOURCE

**API Spec**: Contract call to `getMarketParams()` on Orderbook contract

**Current Implementation**: REST API call to `GET /markets/{market}` (line: `kuru.py:487-532`)

**Impact**: Data may be stale or inconsistent; extra network latency

**Expected Behavior**:
- Call Orderbook contract `getMarketParams()` directly
- Return: `MarketParams` with tick_size, min/max_size, decimals, fees
- No REST API dependency for this data

---

### 1.7 Get Orderbook - WRONG SOURCE

**API Spec**: Contract call to `getL2Book()` on Orderbook contract

**Current Implementation**: REST API call to `GET /orderbook?market={market}` (line: `kuru.py:677-725`)

**Impact**: Orderbook data may be delayed; cannot get block number for consistency

**Expected Behavior**:
- Call Orderbook contract `getL2Book()` directly
- Return: `L2Book` with block_num, buy_orders, sell_orders, AMM orders
- Format: `[[sells], [buys]]` as `[price, size]` pairs

---

### 1.8 Get Positions Endpoint - NOT IN SPEC

**Current Implementation**: `GET /positions?market={market}` (line: `kuru.py:649-676`)

**API Spec**: No mention of positions endpoint

**Impact**: May break if unofficial endpoint removed

**Expected Behavior**: Unknown; not documented in spec

**Action**: Verify this endpoint exists or remove if deprecated

---

### 1.9 Get Open Orders - WRONG ENDPOINT

**Current Implementation**: `GET /orders?market={market}` (line: `kuru.py:632-648`)

**API Spec**: Should use `GET /{user_address}/user/orders/active`

**Impact**: May be fetching wrong data or using deprecated endpoint

---

## 2. WebSocket Real-Time Updates (1 critical missing feature)

### 2.1 WebSocket Client - NOT IMPLEMENTED

**API Spec**:
- URL: `wss://ws.testnet.kuru.io?marketAddress={market_address}`
- Protocol: Socket.IO
- Events: `OrderCreated`, `Trade`, `OrdersCanceled`

**Current Implementation**: Block polling via `MonadClient.get_latest_transactions()` (line: `monad.py:433-548`)

**Impact**:
- High latency (5 second polling interval)
- Inefficient blockchain scanning (1000 blocks max per scan)
- Missed events if blocks exceed scan limit
- High RPC costs

**Expected Behavior**:
- Connect to WebSocket with Socket.IO client
- Subscribe to events filtered by market address
- Parse event payloads: `{order_id, cloid, owner, price, size, is_buy, ...}`
- Real-time order updates (< 1 second latency)

---

## 3. Smart Contract Write Operations (4 discrepancies)

### 3.1 Batch Update Orders - MISSING

**API Spec**: `batchUpdate(buy_prices, buy_sizes, sell_prices, sell_sizes, order_ids, post_only)`

**Current Implementation**: None

**Impact**: Cannot atomically update multiple orders; must cancel + place new

**Expected Behavior**:
- Single transaction to cancel old orders and place new ones
- Reduces gas costs for order replacement strategies
- Accepts lists of prices/sizes and order IDs to cancel

---

### 3.2 Fill-or-Kill Parameter - NOT EXPOSED

**API Spec**: `fill_or_kill: bool` parameter for market orders

**Current Implementation**: Hardcoded to `False` (line: `kuru.py:367, 383`)

**Impact**: Cannot use FOK orders; partial fills always accepted

**Expected Behavior**:
- Add `fill_or_kill` parameter to `place_market_order()` method
- Pass to contract as `_isFillOrKill` parameter
- Document behavior: reverts if not fully filled

---

### 3.3 Tick Normalization - MISSING

**API Spec**: `tick_normalization: str` - "round_up" or "round_down"

**Current Implementation**: None

**Impact**: Prices may be rejected if not aligned to tick size

**Expected Behavior**:
- Add `tick_normalization` parameter to order placement methods
- Round price to nearest tick before encoding
- Prevent "Tick Size Error" (code: `272d3bf7`)

---

### 3.4 Async Execution Mode - MISSING

**API Spec**: `async_execution: bool` - non-blocking transaction mode

**Current Implementation**: All transactions block until receipt (line: `monad.py:252-254`)

**Impact**: Cannot submit multiple orders in parallel; sequential bottleneck

**Expected Behavior**:
- Add `async_execution` parameter to all transaction methods
- If True: return tx_hash immediately without waiting for receipt
- If False: wait for receipt as current behavior

---

## 4. Smart Contract Read Operations (3 missing functions)

### 4.1 Fetch Orderbook - MISSING

**API Spec**: `fetch_orderbook()` calls `getL2Book()` and returns full `L2Book` object

**Current Implementation**: Uses REST API (see 1.7)

**Impact**: See 1.7

**Expected Behavior**:
- Call `getL2Book()` on Orderbook contract
- Return: `{block_num, buy_orders, sell_orders, amm_orders}`
- Use for order book state synchronization

---

### 4.2 Get Vault Parameters - MISSING

**API Spec**: `get_vault_params()` calls `getVaultParams()` on Orderbook contract

**Current Implementation**: None

**Impact**: Cannot access AMM vault data; may need for liquidity analysis

**Expected Behavior**:
- Call `getVaultParams()` on Orderbook contract
- Return: `VaultParams` with AMM vault configuration

---

### 4.3 Get Order ID from Receipt - INCOMPLETE

**API Spec**: `get_order_id_from_receipt(receipt)` extracts order ID from tx receipt

**Current Implementation**: `_extract_order_id_from_receipt()` (line: `kuru.py:461-485`)

**Impact**: Parsing works but is fragile (manual byte manipulation)

**Expected Behavior**:
- Use Web3.py contract event parsing with ABI
- Parse `OrderCreated` event from logs
- Extract `orderId` field (uint40)
- Return `int` or `None` if not found

---

## 5. Data Types and Models (4 discrepancies)

### 5.1 Client Order ID (CLOID) - MISSING

**API Spec**:
```python
OrderRequest.cloid: str = None  # Auto-generated if None
```
Events include `cloid` field for tracking

**Current Implementation**: No CLOID support in `Order` model or API calls

**Impact**: Cannot map mirrored orders to source orders; harder tracking

**Expected Behavior**:
- Add `cloid: Optional[str]` to Order model
- Generate UUID if not provided
- Store in database for order tracking
- Use CLOID in event parsing

---

### 5.2 Order Response Fields - MISMATCH

**API Spec**:
```python
Order:
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
```

**Current Implementation** (`models/order.py`):
```python
Order:
    order_id: str           # Should be int
    market: str             # Should be market_address
    # Missing: owner, is_buy, is_canceled, trigger_time
    order_type: OrderType   # Not in spec
    status: OrderStatus     # Not in spec
```

**Impact**: Cannot parse API responses correctly; field mismatches

**Expected Behavior**: Align Order model with API spec response format

---

### 5.3 Trade Response Fields - CAMELCASE MISMATCH

**API Spec**:
```python
Trade:
    orderid: int           # Note: lowercase, no underscore
    makeraddress: str
    takeraddress: str
    isbuy: bool
    price: str
    filledsize: str
    transactionhash: str
    triggertime: int
```

**Current Implementation** (`models/trade.py`):
```python
Trade:
    id: str
    trader_address: str
    market: str
    side: OrderSide
    price: Decimal
    size: Decimal
    timestamp: datetime
    tx_hash: str
```

**Impact**: Field names don't match API responses; cannot deserialize directly

**Expected Behavior**:
- Add API response model: `TradeResponse` with camelCase fields
- Map to internal `Trade` model with snake_case
- Use Pydantic aliases for field mapping

---

### 5.4 MarketParams Fields - MISMATCH

**API Spec**:
```python
MarketParams:
    price_precision: int
    size_precision: int
    base_asset: str
    base_asset_decimals: int
    quote_asset: str
    quote_asset_decimals: int
    tick_size: str
    min_size: str
    max_size: str
    taker_fee_bps: int
    maker_fee_bps: int
```

**Current Implementation** (`kuru.py:487-532`): Returns generic dict from REST API

**Impact**: No validation; inconsistent field access

**Expected Behavior**:
- Create `MarketParams` Pydantic model matching spec
- Validate response data
- Cache typed objects, not dicts

---

## 6. Event Parsing (2 critical issues)

### 6.1 Event Signatures - PLACEHOLDER VALUES

**API Spec**: Use Keccak256 hash of event signature

**Current Implementation** (`detector.py:14-16`):
```python
TRADE_EXECUTED_EVENT_TOPIC = "0x0000000000000000000000000000000000000000000000000000000000000000"
ORDER_PLACED_EVENT_TOPIC = "0x1111111111111111111111111111111111111111111111111111111111111111"
ORDER_CANCELLED_EVENT_TOPIC = "0x2222222222222222222222222222222222222222222222222222222222222222"
```

**Impact**: Event detection will NEVER work; no logs will match

**Expected Behavior**:
- Calculate Keccak256 hash of event signatures:
  - `OrderCreated(uint40,address,uint96,uint32,bool)`
  - `Trade(...)` - need actual signature from contract
  - `OrdersCanceled(...)` - need actual signature
- Store correct topic hashes

---

### 6.2 Event Field Names - MISMATCH

**API Spec** (WebSocket event payloads):
```python
OrderCreated: {order_id, cloid, owner, price, size, is_buy, remaining_size, is_canceled}
Trade: {order_id, cloid, maker_address, taker_address, is_buy, price, filled_size}
OrdersCanceled: {order_ids[], cloids[], maker_address, canceled_orders_data[]}
```

**Current Implementation**: Manual byte parsing, not using event ABI

**Impact**: Field extraction is fragile and error-prone

**Expected Behavior**:
- Use Web3.py contract event decoding with ABI
- Map event fields to internal models
- Handle indexed vs non-indexed parameters correctly

---

## 7. Contract Addresses and Configuration (1 verification needed)

### 7.1 Market Addresses - VERIFY CURRENT

**Current Constants** (`config/constants.py`):
```python
MON_USDC_MARKET_ADDRESS = "0xD3AF145f1Aa1A471b5f0F62c52Cf8fcdc9AB55D3"
DAK_MON_MARKET_ADDRESS = "0x94B72620e65577De5FB2B8A8b93328cAF6CA161b"
CHOG_MON_MARKET_ADDRESS = "0x277BF4A0aAc16f19D7Bf592FefFc8D2D9a890508"
YAKI_MON_MARKET_ADDRESS = "0xD5c1DC181C359f0199C83045a85CD2556B325dE0"
```

**API Spec**: Matches (lowercase in spec, uppercase in code)

**Action**: Verify addresses are current; checksummed format is correct

---

## Summary Statistics

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| REST API Endpoints | 3 | 4 | 2 | 0 |
| WebSocket | 1 | 0 | 0 | 0 |
| Smart Contract Writes | 1 | 2 | 1 | 0 |
| Smart Contract Reads | 0 | 2 | 1 | 0 |
| Data Types | 0 | 2 | 2 | 0 |
| Event Parsing | 2 | 0 | 0 | 0 |
| Configuration | 0 | 0 | 1 | 0 |
| **Total** | **7** | **10** | **7** | **0** |

**Critical**: Breaks core functionality
**High**: Impacts performance or reliability
**Medium**: Limits features or causes inefficiency
**Low**: Minor inconsistency or cosmetic issue

---

## Recommended Prioritization

1. **Phase 1 - Critical Fixes**: Event signatures, CLOID support, REST endpoint corrections
2. **Phase 2 - Performance**: WebSocket implementation, async execution
3. **Phase 3 - Feature Complete**: Batch updates, missing contract reads
4. **Phase 4 - Polish**: Data model alignment, tick normalization

---

**Next Steps**: See `docs/MASTER-PLAN.md` for detailed work items and acceptance criteria.
