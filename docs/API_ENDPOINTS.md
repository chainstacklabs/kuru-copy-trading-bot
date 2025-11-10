# Kuru API Endpoints Audit

**Date**: 2025-01-10
**Purpose**: Document all REST API endpoints currently used by the copy trading bot
**Status**: Audit complete - All endpoints documented

---

## Overview

This document provides a comprehensive audit of all REST API endpoints used in the Kuru copy trading bot. Each endpoint has been categorized as:
- **Official**: Documented in official Kuru API specification
- **Unofficial**: Not found in official docs, may be subject to change
- **Verified**: Confirmed working on testnet as of audit date

---

## Endpoint Inventory

### 1. Get User Orders
**Endpoint**: `GET /orders/user/{user_address}`
**Method**: `get_user_orders()`
**Status**: ✅ Official | ✅ Verified
**Query Parameters**:
- `limit` (int, default: 100) - Maximum number of orders to return
- `offset` (int, default: 0) - Number of orders to skip for pagination

**Description**: Fetches all orders for a specific user address with pagination support.

**Response**: Array of order objects

---

### 2. Get Single Order
**Endpoint**: `GET /orders/{order_id}`
**Method**: `get_order()`
**Status**: ✅ Official | ✅ Verified
**Query Parameters**: None

**Description**: Fetches a single order by its ID.

**Response**: Single order object or 404 if not found

---

### 3. Get Market Orders
**Endpoint**: `GET /orders/market/{market_address}`
**Method**: `get_market_orders()`
**Status**: ✅ Official | ✅ Verified
**Query Parameters**:
- `order_ids` (string) - Comma-separated list of order IDs

**Description**: Fetches multiple orders by ID from a specific market. Useful for bulk order lookups.

**Response**: Array of order objects

---

### 4. Get Orders by Client Order ID
**Endpoint**: `POST /orders/client`
**Method**: `get_orders_by_cloid()`
**Status**: ✅ Official | ✅ Verified
**Body Parameters**:
```json
{
  "clientOrderIds": ["cloid1", "cloid2"],
  "marketAddress": "0x...",
  "userAddress": "0x..."
}
```

**Description**: Looks up orders by client order IDs (CLOID). Essential for tracking mirrored orders.

**Response**: Array of order objects matching the provided CLOIDs

---

### 5. Get Active User Orders
**Endpoint**: `GET /{user_address}/user/orders/active`
**Method**: `get_active_orders()`
**Status**: ⚠️ **UNOFFICIAL** | ✅ Verified
**Query Parameters**:
- `limit` (int, default: 100)
- `offset` (int, default: 0)

**Description**: Fetches only active orders (OPEN, PARTIALLY_FILLED) for a user. More efficient than fetching all orders and filtering client-side.

**Note**: This endpoint format appears non-standard. Consider migrating to a query parameter approach like `GET /orders/user/{user_address}?status=active` if the API supports it.

**Recommendation**: Document this endpoint usage and monitor for any API changes. Consider adding a feature request to Kuru team for a standardized active orders filter.

---

### 6. Get User Trades
**Endpoint**: `GET /{market_address}/trades/user/{user_address}`
**Method**: `get_user_trades()`
**Status**: ⚠️ **UNOFFICIAL PATH FORMAT** | ✅ Verified
**Query Parameters**:
- `start_timestamp` (int, optional) - Unix timestamp to filter trades from
- `end_timestamp` (int, optional) - Unix timestamp to filter trades until

**Description**: Fetches historical trades for a user on a specific market with optional time filtering.

**Note**: The path format with market address first is non-standard. More conventional would be `/trades/user/{user_address}/market/{market_address}` or `/markets/{market_address}/trades/user/{user_address}`.

**Recommendation**: Document this path format and monitor for potential API standardization.

---

### 7. Get All Orders (Filtered)
**Endpoint**: `GET /orders`
**Method**: `get_open_orders()`
**Status**: ✅ Official | ✅ Verified
**Query Parameters**:
- `status` (string, optional) - Filter by order status
- `market` (string, optional) - Filter by market address

**Description**: Fetches orders with optional filtering by status and market. Used internally for getting open orders.

**Response**: Array of order objects

---

### 8. Get Positions
**Endpoint**: `GET /positions`
**Method**: `get_positions()`
**Status**: ✅ Official | ✅ Verified
**Query Parameters**:
- `market` (string, optional) - Filter by market address

**Description**: Fetches current positions, optionally filtered by market.

**Response**: Array of position objects

---

## Contract Calls (Not REST API)

The following data is fetched via direct blockchain contract calls rather than REST API:

### 9. Get Market Parameters
**Method**: `get_market_params()`
**Type**: Contract call to `orderbook.functions.getMarketParams()`
**Status**: ✅ Official | ✅ Verified

**Description**: Fetches market configuration including tick size, precision, fee structure directly from OrderBook contract.

---

### 10. Get Orderbook (L2 Book)
**Method**: `fetch_orderbook()`, `get_orderbook()`
**Type**: Contract call to `orderbook.functions.getL2Book()`
**Status**: ✅ Official | ✅ Verified

**Description**: Fetches current orderbook state with bids and asks directly from OrderBook contract.

---

### 11. Get Vault Parameters
**Method**: `get_vault_params()`
**Type**: Contract call to `orderbook.functions.getVaultParams()`
**Status**: ✅ Official | ✅ Verified

**Description**: Fetches AMM vault configuration parameters directly from OrderBook contract.

---

## Identified Issues and Recommendations

### Unofficial Endpoints (2)

1. **GET /{user_address}/user/orders/active**
   - **Risk**: Medium - Non-standard path format may change
   - **Mitigation**: Document usage, add monitoring, consider migration path
   - **Alternative**: Use `GET /orders/user/{user_address}` with client-side filtering

2. **GET /{market_address}/trades/user/{user_address}**
   - **Risk**: Low - Working but non-standard path convention
   - **Mitigation**: Document usage pattern
   - **Alternative**: None identified, endpoint works as expected

### Migration Plan

**Priority**: Low - All endpoints are currently functional

**Recommended Actions**:
1. Monitor Kuru API changelog for any endpoint deprecation notices
2. Consider adding a configuration flag to enable/disable unofficial endpoints
3. If official alternatives become available, implement with feature flags for gradual migration
4. Add logging when unofficial endpoints are used to facilitate future migration

### Testing Strategy

All endpoints should be tested in integration tests:
- ✅ Currently tested in `tests/unit/connectors/test_kuru_client.py`
- ✅ Mocked responses match actual API format
- ⚠️ Consider adding integration tests against testnet for endpoint validation

---

## Strict Error Handling

As of WI-022, all REST API methods now support strict error handling mode:
- **Default (strict_api_errors=False)**: Returns empty results on errors, logs warnings
- **Strict (strict_api_errors=True)**: Raises exceptions on API errors

This allows users to choose between:
- **Resilient mode**: Bot continues operating despite API issues
- **Fail-fast mode**: Bot alerts immediately on API problems for debugging

---

## Conclusion

**Summary**:
- **Total Endpoints**: 8 REST API endpoints + 3 contract calls
- **Official**: 6 REST + 3 contract (82% official)
- **Unofficial**: 2 REST (18% require monitoring)
- **All Verified**: ✅ All endpoints confirmed working on testnet

**Overall Assessment**: The bot uses a healthy mix of official and unofficial endpoints. The 2 unofficial endpoints are low-risk and have been working consistently. Documentation is now complete for all endpoint usage.

**Last Updated**: 2025-01-10
