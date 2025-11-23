# Kuru API Reference

> **Note**: This API documentation has been compiled from the [Kuru SDK Python](https://github.com/Kuru-Labs/kuru-sdk-py) and [Kuru SDK TypeScript](https://github.com/Kuru-Labs/kuru-sdk) repositories.

Technical API documentation for copy trading bot implementation (or whatever you want to build).

## 1. REST API - read operations

Base URL: `https://api.testnet.kuru.io` (see [API endpoints](#7-api-endpoints))

| Endpoint | Method | Parameters | Returns |
|----------|--------|------------|---------|
| `/orders/user/{user_address}` | GET | `user_address`, `limit`, `offset` | List[Order] |
| `/{user_address}/user/orders/active` | GET | `user_address`, `limit`, `offset` | List[Order] (active only) |
| `/{market_address}/trades/user/{user_address}` | GET | `market_address`, `user_address`, `start_timestamp`, `end_timestamp` | List[Trade] |
| `/orders/market/{market_address}` | GET | `market_address`, `order_ids` | List[Order] |
| `/orders/client` | POST | Body: `{clientOrderIds[], marketAddress, userAddress}` | List[Order] |

---

## 2. Smart contract - write operations

Contract: `Orderbook` at `market_address`

| Operation | Contract Function | Key Parameters | Returns |
|-----------|------------------|----------------|---------|
| Limit Buy | `addBuyOrder(price, size, post_only)` | `price: str`, `size: str`, `post_only: bool` | tx_hash |
| Limit Sell | `addSellOrder(price, size, post_only)` | `price: str`, `size: str`, `post_only: bool` | tx_hash |
| Market Buy | `placeAndExecuteMarketBuy(size, min_amount_out, is_margin, fill_or_kill)` | `size: str`, `min_amount_out: str`, `is_margin: bool` | tx_hash |
| Market Sell | `placeAndExecuteMarketSell(size, min_amount_out, is_margin, fill_or_kill)` | `size: str`, `min_amount_out: str`, `is_margin: bool` | tx_hash |
| Cancel Orders | `batchCancelOrders(order_ids)` | `order_ids: List[int]` | tx_hash |
| Batch Update | `batchUpdate(buy_prices, buy_sizes, sell_prices, sell_sizes, order_ids, post_only)` | Lists of prices/sizes, `order_ids_to_cancel` | tx_hash |

**Common Parameters**:
- `tick_normalization: str` - "round_up" or "round_down"
- `fill_or_kill: bool` - Revert if not filled
- `is_margin: bool` - Use margin account
- `async_execution: bool` - Non-blocking mode
- `tx_options: TxOptions` - Gas config

---

## 3. Smart contract - read operations

Contract: `Orderbook` at `market_address`

| Function | Contract Method | Returns |
|----------|----------------|---------|
| `fetch_orderbook()` | `getL2Book()` | L2Book (block_num, buy_orders, sell_orders, amm orders) |
| `get_l2_book()` | `getL2Book()` | `[[sells], [buys]]` as `[price, size]` pairs |
| `get_market_params()` | `getMarketParams()` | MarketParams (tick_size, min_size, max_size, fees, decimals) |
| `get_vault_params()` | `getVaultParams()` | VaultParams (AMM vault data) |
| `get_order_id_from_receipt(receipt)` | N/A | `order_id: int` or None |

---

## 4. WebSocket - real-time updates

URL: `{websocket_url}?marketAddress={market_address}` (Socket.IO)
Default: `wss://ws.testnet.kuru.io`

| Event | Trigger | Payload Fields |
|-------|---------|---------------|
| `OrderCreated` | New order placed | `order_id`, `owner`, `price`, `size`, `is_buy`, `block_number`, `transaction_hash`, `trigger_time`, `market_address` |
| `Trade` | Order matched/filled | `order_id`, `maker_address`, `taker_address`, `is_buy`, `price`, `filled_size`, `updated_size`, `block_number`, `transaction_hash`, `trigger_time` |
| `OrdersCanceled` | Orders canceled | `order_ids[]`, `maker_address`, `canceled_orders_data[]` (each with `orderid`, `owner`, `size`, `price`, `isbuy`, `remainingsize`, `iscanceled`, `blocknumber`, `transactionhash`, `triggertime`) |

---

## 5. Margin account

Contract: `MarginAccount` at `margin_account_address`

| Operation | Contract Function | Parameters | Returns |
|-----------|------------------|------------|---------|
| Deposit | `deposit(user, token, amount)` | `token: str`, `amount: int` (wei) | tx_hash |
| Withdraw | `withdraw(amount, token)` | `token: str`, `amount: int` (wei) | tx_hash |
| Get Balance | `getBalance(user_address, token)` | `user_address: str`, `token: str` | `int` (wei) |

**Note**: Native token address: `0x0000000000000000000000000000000000000000`

---

## 6. Data types

### OrderRequest
```python
market_address: str
order_type: str  # "limit", "market", "cancel"
side: str        # "buy", "sell"
price: str
size: str
post_only: bool = False
is_margin: bool = False
fill_or_kill: bool = False
min_amount_out: str = None
cloid: str = None  # Auto-generated if None
```

### Order (Response)
```python
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

### Trade (Response)
```python
order_id: int
maker_address: str
taker_address: str
is_buy: bool
price: str
filled_size: str
updated_size: str       # Remaining size after fill
block_number: str
transaction_hash: str
trigger_time: int
```

### MarketParams
```python
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

### VaultParams (AMM)
```python
kuru_amm_vault: str          # Vault contract address
vault_best_bid: int          # Current best bid price (wei)
bid_partially_filled_size: int
vault_best_ask: int          # Current best ask price (wei)
ask_partially_filled_size: int
vault_bid_order_size: int
vault_ask_order_size: int
spread: int                  # Spread constant
```

### TxOptions
```python
gas_limit: int = None
gas_price: int = None  # Used as maxFeePerGas
max_priority_fee_per_gas: int = None
nonce: int = None
```

---

## 7. API endpoints

### Testnet
- **REST API**: https://api.testnet.kuru.io
- **WebSocket**: wss://ws.testnet.kuru.io
- **Blockchain RPC**: Available at https://chainlist.org/chain/10143

### Testnet contract addresses

Reference: [Kuru Contracts Documentation](https://docs.kuru.io/developers/contracts)

**Core Kuru Contracts:**
```
Router:          0xc816865f172d640d93712C68a7E1F83F3fA63235
Margin Account:  0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef
Kuru Forwarder:  0x350678D87BAa7f513B262B7273ad8Ccec6FF0f78
Kuru Deployer:   0x67a4e43C7Ce69e24d495A39c43489BC7070f009B
Kuru Utils:      0x9E50D9202bEc0D046a75048Be8d51bBa93386Ade
```

**Official Tokens:**
```
USDC/kUSDC:      0xf817257fed379853cDe0fa4F97AB987181B1E5Ea
USDT:            0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D
DAK:             0x0F0BDEbF0F83cD1EE3974779Bcb7315f9808c714
CHOG:            0xE0590015A873bF326bd645c3E1266d4db41C4E6B
YAKI:            0xfe140e1dCe99Be9F4F15d657CD9b7BF622270C50
Native Token:    0x0000000000000000000000000000000000000000
```

**Official Markets:**
```
MON-USDC:        0xd3af145f1aa1a471b5f0f62c52cf8fcdc9ab55d3
DAK-MON:         0x94b72620e65577de5fb2b8a8b93328caf6ca161b
CHOG-MON:        0x277bf4a0aac16f19d7bf592feffc8d2d9a890508
YAKI-MON:        0xd5c1dc181c359f0199c83045a85cd2556b325de0
```

### Authentication
- **Transactions**: Signed with private key (EIP-1559 Type 2)
- **REST API**: No authentication required for reads
- **WebSocket**: Market address filter only

---

## 8. Error codes

### Common errors
| Code | Error |
|------|-------|
| `bb55fd27` | Insufficient Liquidity |
| `ff633a38` | Length Mismatch |
| `fd993161` | Insufficient Native Asset |
| `829f7240` | Order Already Filled Or Cancelled |
| `06e6da4d` | Post Only Error |
| `91f53656` | Price Error |
| `0a5c4f1f` | Size Error |
| `8199f5f3` | Slippage Exceeded |
| `272d3bf7` | Tick Size Error |
| `f4d678b8` | Insufficient Balance |

### Additional errors
| Code | Error |
|------|-------|
| `3cd146b1` | Invalid Spread |
| `a9269545` | Market Fee Error |
| `004b65ba` | Market State Error |
| `ead59376` | Native Asset Not Required |
| `70d7ec56` | Native Asset Transfer Failed |
| `a0cdd781` | Only Owner Allowed |
| `b1460438` | Only Vault Allowed |
| `0b252431` | Too Much Size Filled |
| `7939f424` | Transfer From Failed |
| `cd41a9e3` | Native Asset Mismatch |
| `e84c4d58` | Only Router Allowed |
| `e8430787` | Only Verified Markets Allowed |
| `8579befe` | Zero Address Not Allowed |
| `130e7978` | Base And Quote Asset Same |
| `9db8d5b1` | Invalid Market |
| `d09b273e` | No Markets Passed |
| `d226f9d4` | Insufficient Liquidity Minted |
| `b9873846` | Insufficient Quote Token |
| `40accb6f` | Deposit Uses Stale Quote |
| `05d13eef` | Vault Deposit Price Crosses OrderBook |
| `d8415400` | Vault Liquidity Insufficient |
| `98de0cd0` | Vault Deposit Uses Invalid Price |
| `bb2b4138` | Incorrect Order Type Passed |
| `6a2628d9` | New Size Exceeds Partially Filled Size |

See SDK `src/utils/errors.json` for complete list.

---

## Copy trading bot flow

### Monitor target trader
1. **WebSocket**: Subscribe to `OrderCreated`, `Trade`, `OrdersCanceled` events filtered by target trader address
2. **REST API**: Poll `/orders/user/{target_address}` for initial state
3. **REST API**: Fetch `/trades/user/{target_address}` for historical trades

### Mirror trades
1. Parse incoming `OrderCreated` event or REST order data
2. Calculate position size (apply copy ratio)
3. **Smart Contract**: Call `addBuyOrder()` or `addSellOrder()` with adjusted parameters
4. Store `cloid` for order tracking
5. **WebSocket**: Listen for own `Trade` events to confirm fill

### Cancel mirrored orders
1. **WebSocket**: Detect `OrdersCanceled` event for target trader
2. Map target `order_id` to own `order_id` via tracking database
3. **Smart Contract**: Call `batchCancelOrders([order_ids])`

### Query order status
1. **REST API**: GET `/orders/client` with `cloids[]` to fetch current order status
2. **Smart Contract**: Call `get_l2_book()` to check order book state
3. **WebSocket**: Monitor `Trade` events for fill updates

---

**Note**: Price/size values auto-normalized based on `MarketParams`. Use `async_execution=True` for non-blocking operations.