"""Kuru WebSocket client for real-time event updates."""

from collections.abc import Callable
from typing import Any, cast

import socketio  # type: ignore[import-untyped]
import structlog

from ...models.order import OrderResponse
from ...models.trade import TradeResponse

logger = structlog.get_logger(__name__)


class KuruWebSocketClient:
    """WebSocket client for Kuru DEX real-time updates.

    Connects to Kuru WebSocket server and receives real-time events:
    - OrderCreated: New order placed
    - Trade: Trade execution
    - OrdersCanceled: Orders canceled

    Example:
        ```python
        client = KuruWebSocketClient(
            ws_url="wss://ws.testnet.kuru.io",
            market_address="0x1234..."
        )

        client.set_order_created_callback(on_order_created)
        client.set_trade_callback(on_trade)

        await client.connect()
        ```
    """

    def __init__(self, ws_url: str, market_address: str):
        """Initialize WebSocket client.

        Args:
            ws_url: WebSocket server URL (e.g., wss://ws.testnet.kuru.io)
            market_address: Market contract address to filter events
        """
        self.ws_url = ws_url
        self.market_address = market_address.lower()  # Normalize to lowercase
        self.should_reconnect = True

        # Create Socket.IO async client
        self.sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=0,  # Infinite retries
            reconnection_delay=1,
            reconnection_delay_max=5,
            logger=False,  # Disable Socket.IO logger (use structlog)
            engineio_logger=False,
        )

        # Event callbacks
        self.on_order_created_callback: Callable[[OrderResponse], None] | None = None
        self.on_trade_callback: Callable[[TradeResponse], None] | None = None
        self.on_orders_canceled_callback: (
            Callable[[list[int], list[str], str, list[dict[str, Any]]], None] | None
        ) = None

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register Socket.IO event handlers."""

        @self.sio.event  # type: ignore[misc]
        async def connect() -> None:
            """Handle connection event."""
            logger.info("websocket_connected", url=self.ws_url, market=self.market_address)

        @self.sio.event  # type: ignore[misc]
        async def disconnect() -> None:
            """Handle disconnection event."""
            logger.warning("websocket_disconnected")
            await self.handle_disconnect()

        @self.sio.event  # type: ignore[misc]
        async def connect_error(data: Any) -> None:
            """Handle connection error."""
            logger.error("websocket_connection_error", error=data)

        @self.sio.on("OrderCreated")  # type: ignore[misc]
        async def on_order_created(data: Any) -> None:
            """Handle OrderCreated event."""
            await self.handle_order_created(data)

        @self.sio.on("Trade")  # type: ignore[misc]
        async def on_trade(data: Any) -> None:
            """Handle Trade event."""
            await self.handle_trade(data)

        @self.sio.on("OrdersCanceled")  # type: ignore[misc]
        async def on_orders_canceled(data: Any) -> None:
            """Handle OrdersCanceled event."""
            await self.handle_orders_canceled(data)

    async def connect(self) -> None:
        """Connect to WebSocket server with market filter."""
        try:
            # Connect with market address as query parameter
            await self.sio.connect(
                self.ws_url,
                transports=["websocket"],
                wait_timeout=10,
                namespaces=["/"],
            )

            # Send market subscription after connection
            await self.sio.emit("subscribe", {"market": self.market_address})

            logger.info("websocket_subscribed", market=self.market_address)

        except Exception as e:
            logger.error(
                "websocket_connect_failed",
                error=str(e),
                url=self.ws_url,
                market=self.market_address,
            )

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        self.should_reconnect = False
        await self.sio.disconnect()
        logger.info("websocket_disconnected_by_user")

    async def handle_disconnect(self) -> None:
        """Handle disconnection and prepare for reconnection."""
        if self.should_reconnect:
            logger.info("websocket_will_reconnect")

    async def handle_order_created(self, data: dict[str, Any]) -> None:
        """Handle OrderCreated event.

        Args:
            data: Raw event data from WebSocket
        """
        try:
            # Filter by market address (use .get() for filtering, validation happens in Pydantic)
            market = data.get("market_address", "").lower()
            if market != self.market_address:
                logger.debug(
                    "order_created_filtered",
                    event_market=market,
                    subscribed_market=self.market_address,
                )
                return

            # Parse into OrderResponse model (will raise ValidationError if required fields missing)
            order_response = OrderResponse(**data)

            logger.info(
                "order_created_event",
                order_id=order_response.order_id,
                market=order_response.market_address,
                owner=order_response.owner,
                side="BUY" if order_response.is_buy else "SELL",
                price=order_response.price,
                size=order_response.size,
            )

            # Call callback if set
            if self.on_order_created_callback:
                self.on_order_created_callback(order_response)

        except Exception as e:
            logger.error("order_created_parse_error", error=str(e), data=data)

    async def handle_trade(self, data: dict[str, Any]) -> None:
        """Handle Trade event.

        Args:
            data: Raw event data from WebSocket
        """
        try:
            # Filter by market address (use .get() for filtering, validation happens in Pydantic)
            market = data.get("market_address", "").lower()
            if market and market != self.market_address:
                logger.debug(
                    "trade_filtered",
                    event_market=market,
                    subscribed_market=self.market_address,
                )
                return

            # Parse into TradeResponse model (will raise ValidationError if required fields missing)
            trade_response = TradeResponse(**data)

            logger.info(
                "trade_event",
                order_id=trade_response.orderid,
                maker=trade_response.makeraddress,
                side="BUY" if trade_response.isbuy else "SELL",
                price=trade_response.price,
                size=trade_response.filledsize,
            )

            # Call callback if set
            if self.on_trade_callback:
                self.on_trade_callback(trade_response)

        except Exception as e:
            logger.error("trade_parse_error", error=str(e), data=data)

    async def handle_orders_canceled(self, data: dict[str, Any]) -> None:
        """Handle OrdersCanceled event.

        Args:
            data: Raw event data from WebSocket
        """
        try:
            # Validate required fields are present
            if "order_ids" not in data:
                logger.error(
                    "orders_canceled_missing_required_field",
                    field="order_ids",
                    data=data,
                )
                return

            if "maker_address" not in data:
                logger.error(
                    "orders_canceled_missing_required_field",
                    field="maker_address",
                    data=data,
                )
                return

            # Extract required fields
            order_ids = data["order_ids"]
            maker_address = data["maker_address"]

            # Extract optional fields
            cloids = data.get("cloids", [])
            canceled_orders_data = data.get("canceled_orders_data", [])

            logger.info(
                "orders_canceled_event",
                order_count=len(order_ids),
                order_ids=order_ids,
                cloids=cloids,
                maker_address=maker_address,
            )

            # Call callback if set
            if self.on_orders_canceled_callback:
                self.on_orders_canceled_callback(
                    order_ids, cloids, maker_address, canceled_orders_data
                )

        except Exception as e:
            logger.error("orders_canceled_parse_error", error=str(e), data=data)

    def set_order_created_callback(self, callback: Callable[[OrderResponse], None]) -> None:
        """Set callback for OrderCreated events.

        Args:
            callback: Function to call when OrderCreated event received
        """
        self.on_order_created_callback = callback

    def set_trade_callback(self, callback: Callable[[TradeResponse], None]) -> None:
        """Set callback for Trade events.

        Args:
            callback: Function to call when Trade event received
        """
        self.on_trade_callback = callback

    def set_orders_canceled_callback(
        self, callback: Callable[[list[int], list[str], str, list[dict[str, Any]]], None]
    ) -> None:
        """Set callback for OrdersCanceled events.

        Args:
            callback: Function to call when OrdersCanceled event received.
                     Signature: (order_ids, cloids, maker_address, canceled_orders_data) -> None
        """
        self.on_orders_canceled_callback = callback

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected.

        Returns:
            True if connected, False otherwise
        """
        return cast(bool, self.sio.connected)
