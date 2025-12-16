# How to Build a Kuru Copy Trading Bot

Copy trading drives a significant share of trading volume on decentralized exchanges. On Kuru DEX, built on Monad's high-throughput blockchain, bots can automatically mirror successful traders' orders in real-time through transparent on-chain order books.

This guide shows you how to build a copy trading bot that monitors source wallets and replicates their limit orders on Kuru DEX using Chainstack infrastructure.

## Why Build a Kuru Copy Trading Bot?

Kuru operates as a decentralized token exchange on Monad, combining speed with full on-chain transparency. Copy trading bots on Kuru benefit from:

- **On-chain order books**: Every order is visible and verifiable on the blockchain
- **Event-driven architecture**: WebSocket subscriptions detect orders as they're placed
- **Limit order precision**: Mirror sophisticated strategies with exact price and size control

Automated copy trading eliminates manual intervention while giving you full control over position sizing and risk parameters.

## What You Need for a Kuru Copy Trading Bot

Before you start, gather these essentials:

- **RPC Endpoints**: HTTPS and WSS URLs to monitor events and submit orders to the Monad blockchain
- **Monad Wallet**: A funded wallet with testnet MON tokens for gas fees ([Monad faucet](https://faucet.monad.xyz/))
- **Python Environment**: Python 3.10+ and the `uv` package manager
- **Kuru Account**: Funded Kuru trading account for executing orders
- **Source Wallets**: Addresses of traders you want to copy

The most critical component is your RPC node connection. Public Monad endpoints work for initial testing, but copy trading demands consistent WebSocket stability and low-latency order submission.

## Choosing the Right Monad RPC Node

Chainstack offers two deployment models for Monad nodes:

### Global Elastic Nodes

Shared infrastructure suits teams starting out or running lighter workloads. Global nodes provide:
- Usage-based pricing with no upfront costs
- WebSocket support for event subscriptions
- Access controls like API key authentication
- Suitable for development and testing

Global nodes share resources across users, which can introduce variable latency during network congestion.

### Dedicated Nodes

Single-tenant infrastructure delivers predictable performance for continuous trading operations. Dedicated nodes offer:
- No rate limits on requests or WebSocket subscriptions
- Consistent low latency even during market volatility
- Higher request ceilings for burst activity
- Fixed monthly pricing for cost predictability

Dedicated infrastructure provides consistent performance without the resource contention of shared endpoints.

[Deploy a Monad node on Chainstack](https://console.chainstack.com/user/account/create) in minutes and retrieve your HTTPS and WSS endpoints from the access credentials panel.

## Set Up Your Environment

Clone the open-source Kuru copy trading bot repository:

```bash
git clone https://github.com/chainstacklabs/kuru-copy-trading-bot.git
cd kuru-copy-trading-bot
```

Install dependencies with `uv`:

```bash
pip install uv
uv sync
```

Configure your `.env` file with Chainstack endpoints and trading parameters:

```bash
MONAD_RPC_URL=https://your-chainstack-node.com
MONAD_WS_URL=wss://your-chainstack-node.com
BOT_PRIVATE_KEY=0xYourPrivateKeyHere
SOURCE_WALLETS=0xTraderAddress1,0xTraderAddress2
MARKETS=0xMarketContract1,0xMarketContract2
COPY_RATIO=1.0
MIN_ORDER_SIZE_USD=10
MAX_POSITION_SIZE_USD=1000
DRY_RUN=false
```

Fund your Kuru trading account:

```bash
uv run python scripts/deposit_margin.py --amount 1000
```

Launch the bot:

```bash
uv run python main.py
```

The bot connects to your Chainstack node's WebSocket endpoint and begins monitoring configured markets for source wallet activity.

## How a Kuru Copy Trading Bot Works

The bot monitors blockchain events through your Chainstack node's WebSocket connection and replicates orders from configured source wallets.

**Event Monitoring**

The bot subscribes to Kuru market contract events including order creation, trade execution, and order cancellations. When a monitored wallet places an order, the bot detects it through the WebSocket stream.

**Risk Management**

Built-in validation checks each detected order against configurable parameters like minimum balance thresholds, order size limits, and total exposure caps. Orders that fail validation are rejected and logged.

**Position Sizing**

The copy ratio setting controls order size relative to the source trader. You can copy at 50%, 100%, 200%, or any percentage of their order size. The bot enforces minimum and maximum size constraints and adjusts for available account balance.

**Order Execution**

Validated orders are submitted to Kuru DEX as limit orders matching the source trader's price and direction. The bot maintains internal tracking to map source orders to your mirrored orders.

**Cancellation Synchronization**

When source wallets cancel orders, the bot automatically cancels the corresponding mirrored orders to keep your positions aligned.

## Wrapping Up

This open-source bot demonstrates copy trading implementation on Kuru DEX using Monad blockchain infrastructure. The repository includes event monitoring, risk validation, and order execution capabilities.

Reliable RPC infrastructure is essential for WebSocket stability and transaction submission. [Chainstack provides Monad nodes](https://console.chainstack.com/user/account/create) with both shared and dedicated deployment options.

## Resources

- [Kuru Copy Trading Bot Repository](https://github.com/chainstacklabs/kuru-copy-trading-bot)
- [Chainstack Documentation](https://docs.chainstack.com/)
- [Deploy a Monad Node](https://console.chainstack.com/user/account/create)
- [Monad Documentation](https://docs.monad.xyz/)
- [Monad Testnet Faucet](https://faucet.monad.xyz/)

## FAQ

**What does a Monad RPC node provide for copy trading?**

Your Chainstack Monad node exposes JSON-RPC methods for blockchain interaction and WebSocket endpoints for real-time event subscriptions. The bot uses WebSockets to monitor Kuru market events and HTTPS for submitting order transactions.

**How do I get testnet funds for testing?**

Get testnet MON from the [Monad faucet](https://faucet.monad.xyz/) for gas fees. For Kuru trading account deposits, you'll need testnet tokens compatible with Kuru markets.

**What's the difference between Global and Dedicated nodes for this bot?**

Global nodes share resources across users, which can introduce latency spikes during high network activity. Dedicated nodes provide consistent performance with no rate limits on WebSocket subscriptions or RPC requests.

**Can I copy multiple traders simultaneously?**

Yes. Add multiple addresses to `SOURCE_WALLETS` separated by commas. The bot monitors all configured wallets and applies your risk limits to aggregate exposure across all copied trades.

**How do I avoid copying bad trades?**

Use the risk management parameters: set `MIN_ORDER_SIZE_USD` to filter noise, cap `MAX_POSITION_SIZE_USD` to limit downside, and configure `MAX_TOTAL_EXPOSURE_USD` for portfolio-level risk control. Market whitelisting lets you restrict trading to tokens you understand.

---

Explore the [open-source repository](https://github.com/chainstacklabs/kuru-copy-trading-bot) to see the implementation. [Chainstack Monad nodes](https://console.chainstack.com/user/account/create) provide the RPC infrastructure for blockchain connectivity.
