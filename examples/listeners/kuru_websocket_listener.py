#!/usr/bin/env python3
"""
Standalone Kuru WebSocket Listener - No SDK Required

This script connects to the Kuru Exchange WebSocket and prints raw event messages
with basic parsing to understand the data structure.

Events monitored:
- OrderCreated: New limit orders placed
- Trade: Orders filled (partially or fully)
- OrdersCanceled: Orders cancelled

Usage:
    python examples/listeners/kuru_websocket_listener.py
"""

import asyncio
import json
import signal
from typing import Any

import socketio

# Configuration - Change these values as needed
DEFAULT_MARKET_ADDRESS = "0xd3af145f1aa1a471b5f0f62c52cf8fcdc9ab55d3"
DEFAULT_WS_URL = "wss://ws.staging.kuru.io"  # "wss://ws.testnet.kuru.io"


class KuruWebSocketListener:
    """Simple WebSocket listener for Kuru Exchange events."""

    def __init__(self, market_address: str, ws_url: str = "wss://ws.testnet.kuru.io"):
        """Initialize the WebSocket listener.

        Args:
            market_address: OrderBook contract address to monitor
            ws_url: WebSocket URL (default: Kuru testnet)
        """
        self.market_address = market_address.lower()
        self.ws_url = ws_url
        self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        self.shutdown_event = asyncio.Event()
        self.is_connected = False

        # Statistics
        self.stats = {
            "orders_created": 0,
            "trades": 0,
            "orders_canceled": 0,
            "total_messages": 0,
        }

        # Setup event handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup Socket.IO event handlers."""

        @self.sio.event
        async def connect():
            print(f"✓ Connected to {self.ws_url}")
            print(f"  Market: {self.market_address}")
            print("-" * 80)
            self.is_connected = True

        @self.sio.event
        async def disconnect():
            print("\n✗ Disconnected from WebSocket")
            self.is_connected = False

        @self.sio.event
        async def connect_error(data):
            print(f"✗ Connection error: {data}")

        # Order events
        @self.sio.on("OrderCreated")
        async def on_order_created(data):
            self.stats["orders_created"] += 1
            self.stats["total_messages"] += 1
            self._print_order_created(data)

        @self.sio.on("Trade")
        async def on_trade(data):
            self.stats["trades"] += 1
            self.stats["total_messages"] += 1
            self._print_trade(data)

        @self.sio.on("OrdersCanceled")
        async def on_orders_canceled(data):
            self.stats["orders_canceled"] += 1
            self.stats["total_messages"] += 1
            self._print_orders_canceled(data)

        # Generic event handler for debugging
        @self.sio.event
        async def message(data):
            print("\n📨 Generic message received:")
            print(json.dumps(data, indent=2))

    def _print_order_created(self, data: dict[str, Any]):
        """Print OrderCreated event with basic parsing."""
        print(f"\n🆕 OrderCreated Event #{self.stats['orders_created']}")
        print(f"   Raw: {json.dumps(data, indent=6)}")

        # Try to parse common fields
        try:
            order_id = data.get("orderid") or data.get("orderId")
            owner = data.get("owner")
            price = data.get("price")
            size = data.get("size")
            remaining = data.get("remainingsize") or data.get("remainingSize")
            is_buy = data.get("isbuy") or data.get("isBuy")
            is_canceled = data.get("iscanceled") or data.get("isCanceled")
            cloid = data.get("cloid")

            print("\n   Parsed:")
            print(f"      Order ID: {order_id}")
            print(f"      Owner: {owner}")
            print(f"      Side: {'BUY' if is_buy else 'SELL'}")
            print(f"      Price: {price}")
            print(f"      Size: {size}")
            print(f"      Remaining: {remaining}")
            print(f"      Canceled: {is_canceled}")
            if cloid:
                print(f"      Client Order ID: {cloid}")
        except Exception as e:
            print(f"   ⚠ Parsing error: {e}")

    def _print_trade(self, data: dict[str, Any]):
        """Print Trade event with basic parsing."""
        print(f"\n💰 Trade Event #{self.stats['trades']}")
        print(f"   Raw: {json.dumps(data, indent=6)}")

        # Try to parse common fields
        try:
            order_id = data.get("orderid") or data.get("orderId")
            maker = data.get("makeraddress") or data.get("makerAddress")
            taker = data.get("takeraddress") or data.get("takerAddress")
            is_buy = data.get("isbuy") or data.get("isBuy")
            price = data.get("price")
            filled_size = data.get("filledsize") or data.get("filledSize")
            updated_size = data.get("updatedsize") or data.get("updatedSize")
            tx_hash = data.get("transactionhash") or data.get("transactionHash")

            print("\n   Parsed:")
            print(f"      Order ID: {order_id}")
            print(f"      Maker: {maker}")
            print(f"      Taker: {taker}")
            print(f"      Side: {'BUY' if is_buy else 'SELL'}")
            print(f"      Price: {price}")
            print(f"      Filled Size: {filled_size}")
            print(f"      Updated Size: {updated_size}")
            print(f"      Tx Hash: {tx_hash}")
        except Exception as e:
            print(f"   ⚠ Parsing error: {e}")

    def _print_orders_canceled(self, data: dict[str, Any]):
        """Print OrdersCanceled event with basic parsing."""
        print(f"\n❌ OrdersCanceled Event #{self.stats['orders_canceled']}")
        print(f"   Raw: {json.dumps(data, indent=6)}")

        # Try to parse common fields
        try:
            order_ids = data.get("orderids") or data.get("orderIds") or []
            cloids = data.get("cloids") or []
            maker = data.get("makeraddress") or data.get("makerAddress")

            print("\n   Parsed:")
            print(f"      Maker: {maker}")
            print(f"      Order IDs: {order_ids}")
            if cloids:
                print(f"      Client Order IDs: {cloids}")
            print(f"      Count: {len(order_ids)}")
        except Exception as e:
            print(f"   ⚠ Parsing error: {e}")

    async def connect(self):
        """Connect to the WebSocket."""
        print(f"Connecting to {self.ws_url}...")
        print(f"Market address: {self.market_address}")

        try:
            # Connect with market address as query parameter
            url_with_params = f"{self.ws_url}?marketAddress={self.market_address}"
            await self.sio.connect(
                url_with_params,
                transports=["websocket"],
                wait_timeout=10,
            )
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the WebSocket."""
        if self.is_connected:
            print("\nDisconnecting...")
            await self.sio.disconnect()

    def _print_stats(self):
        """Print statistics summary."""
        print("\n" + "=" * 80)
        print("📊 Session Statistics:")
        print(f"   Total Messages: {self.stats['total_messages']}")
        print(f"   Orders Created: {self.stats['orders_created']}")
        print(f"   Trades: {self.stats['trades']}")
        print(f"   Orders Canceled: {self.stats['orders_canceled']}")
        print("=" * 80)

    async def run(self):
        """Run the listener indefinitely."""
        try:
            # Setup signal handlers for graceful shutdown
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._shutdown(s)))

            # Connect to WebSocket
            await self.connect()

            print("\n👂 Listening for events... Press Ctrl+C to exit\n")
            print("=" * 80)

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except asyncio.CancelledError:
            print("\n⚠ Task cancelled")
        finally:
            await self.disconnect()
            self._print_stats()

    async def _shutdown(self, sig):
        """Handle shutdown signal."""
        print(f"\n\n🛑 Received signal {sig.name}, shutting down...")
        self.shutdown_event.set()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Listen to Kuru Exchange WebSocket events (raw messages)"
    )
    parser.add_argument(
        "--market",
        default=DEFAULT_MARKET_ADDRESS,
        help=f"OrderBook contract address to monitor (default: {DEFAULT_MARKET_ADDRESS})",
    )
    parser.add_argument(
        "--ws-url",
        default=DEFAULT_WS_URL,
        help=f"WebSocket URL (default: {DEFAULT_WS_URL})",
    )

    args = parser.parse_args()

    # Create and run listener
    listener = KuruWebSocketListener(
        market_address=args.market,
        ws_url=args.ws_url,
    )

    try:
        await listener.run()
    except KeyboardInterrupt:
        print("\n\n⚠ KeyboardInterrupt - exiting...")
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
