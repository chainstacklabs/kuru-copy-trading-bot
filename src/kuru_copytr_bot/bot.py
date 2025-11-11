"""Copy trading bot orchestrator using WebSocket."""

import asyncio
from typing import Any

from src.kuru_copytr_bot.connectors.websocket.kuru_ws_client import KuruWebSocketClient
from src.kuru_copytr_bot.models.order import OrderResponse
from src.kuru_copytr_bot.models.trade import TradeResponse
from src.kuru_copytr_bot.trading.copier import TradeCopier
from src.kuru_copytr_bot.utils.logger import get_logger

logger = get_logger(__name__)


class CopyTradingBot:
    """Orchestrates copy trading workflow using WebSocket for real-time events."""

    def __init__(
        self,
        ws_clients: list[tuple[str, KuruWebSocketClient]],
        source_wallets: list[str],
        copier: TradeCopier,
    ):
        """Initialize copy trading bot.

        Args:
            ws_clients: List of (market_address, WebSocketClient) tuples
            source_wallets: List of source wallet addresses to monitor
            copier: Trade copier for executing mirror trades
        """
        self.ws_clients = ws_clients
        self.source_wallets = [addr.lower() for addr in source_wallets]
        self.copier = copier

        # Running state
        self.is_running = False

        # Statistics
        self._trades_detected = 0
        self._orders_detected = 0
        self._orders_canceled_detected = 0

        # Order tracking: maps source_order_id -> our_order_id
        # This allows us to cancel our orders when source trader cancels theirs
        self._order_mapping: dict[int, str] = {}

        # Set up WebSocket callbacks
        for market_address, ws_client in self.ws_clients:
            # Create closures to capture market_address
            ws_client.set_order_created_callback(
                self._create_order_created_callback(market_address)
            )
            ws_client.set_trade_callback(self._create_trade_callback(market_address))
            ws_client.set_orders_canceled_callback(
                self._create_orders_canceled_callback(market_address)
            )

    def _create_trade_callback(self, market_address: str):
        """Create a trade callback that captures the market address.

        Args:
            market_address: Market contract address

        Returns:
            Async callback function for trade events
        """

        async def on_trade(trade_response: TradeResponse):
            """Handle Trade event from WebSocket.

            Args:
                trade_response: Trade data from WebSocket
            """
            try:
                # Filter for our source wallets (check maker address)
                if trade_response.makeraddress.lower() not in self.source_wallets:
                    logger.debug(
                        "Trade from non-monitored wallet, skipping",
                        maker=trade_response.makeraddress,
                        order_id=trade_response.orderid,
                    )
                    return

                # Convert TradeResponse to Trade model
                trade = trade_response.to_trade(market=market_address)

                self._trades_detected += 1
                logger.info(
                    "Trade detected",
                    trade_id=trade.id,
                    market=trade.market,
                    side=trade.side.value,
                    size=str(trade.size),
                    price=str(trade.price),
                    tx_hash=trade.tx_hash,
                )

                # Execute mirror trade
                try:
                    self.copier.process_trade(trade)
                except Exception as e:
                    # Copier handles its own errors internally
                    logger.debug("Copier raised exception (expected)", error=str(e))

            except Exception as e:
                # Failed to process trade
                logger.error(
                    "Failed to process trade event",
                    error=str(e),
                    order_id=trade_response.orderid,
                    exc_info=True,
                )

        return on_trade

    def _create_order_created_callback(self, market_address: str):
        """Create an order created callback that captures the market address.

        Args:
            market_address: Market contract address

        Returns:
            Async callback function for OrderCreated events
        """

        async def on_order_created(order_response: OrderResponse):
            """Handle OrderCreated event from WebSocket.

            Args:
                order_response: Order data from WebSocket
            """
            try:
                # Filter for our source wallets (check owner address)
                if order_response.owner.lower() not in self.source_wallets:
                    logger.debug(
                        "Order from non-monitored wallet, skipping",
                        owner=order_response.owner,
                        order_id=order_response.order_id,
                    )
                    return

                # Convert OrderResponse to Order model
                order = order_response.to_order()

                self._orders_detected += 1
                logger.info(
                    "Order created detected",
                    order_id=order.order_id,
                    market=order.market,
                    side=order.side.value,
                    size=str(order.size),
                    price=str(order.price),
                )

                # Mirror the limit order
                try:
                    # Use copier to mirror the order (it will handle validation and sizing)
                    mirrored_order_id = self.copier.process_order(order)

                    if mirrored_order_id:
                        # Track the mapping for future cancellations
                        self._order_mapping[order_response.order_id] = mirrored_order_id
                        logger.info(
                            "Order mirrored successfully",
                            source_order_id=order_response.order_id,
                            mirrored_order_id=mirrored_order_id,
                        )
                except Exception as e:
                    # Copier handles its own errors internally
                    logger.debug("Copier raised exception (expected)", error=str(e))

            except Exception as e:
                # Failed to process order event
                logger.error(
                    "Failed to process OrderCreated event",
                    error=str(e),
                    order_id=order_response.order_id,
                    exc_info=True,
                )

        return on_order_created

    def _create_orders_canceled_callback(self, market_address: str):
        """Create an orders canceled callback that captures the market address.

        Args:
            market_address: Market contract address

        Returns:
            Async callback function for OrdersCanceled events
        """

        async def on_orders_canceled(
            order_ids: list[int],
            cloids: list[str],
            maker_address: str,
            canceled_orders_data: list[dict],
        ):
            """Handle OrdersCanceled event from WebSocket.

            Args:
                order_ids: List of canceled order IDs
                cloids: List of client order IDs
                maker_address: Maker wallet address
                canceled_orders_data: Additional cancellation data
            """
            try:
                # Filter for our source wallets
                if maker_address.lower() not in self.source_wallets:
                    logger.debug(
                        "Orders canceled by non-monitored wallet, skipping",
                        maker_address=maker_address,
                        order_count=len(order_ids),
                    )
                    return

                self._orders_canceled_detected += 1
                logger.info(
                    "Orders canceled detected",
                    order_count=len(order_ids),
                    order_ids=order_ids,
                    cloids=cloids,
                    maker_address=maker_address,
                )

                # Find our mirrored orders
                our_order_ids = []
                for source_order_id in order_ids:
                    if source_order_id in self._order_mapping:
                        our_order_id = self._order_mapping[source_order_id]
                        our_order_ids.append(our_order_id)
                        logger.debug(
                            "Mapped source order to our order",
                            source_order_id=source_order_id,
                            our_order_id=our_order_id,
                        )

                # Cancel our mirrored orders
                if our_order_ids:
                    try:
                        self.copier.cancel_orders(our_order_ids, market_address)
                        logger.info(
                            "Mirrored orders canceled successfully",
                            canceled_count=len(our_order_ids),
                            order_ids=our_order_ids,
                            market=market_address,
                        )

                        # Remove from tracking
                        for source_order_id in order_ids:
                            self._order_mapping.pop(source_order_id, None)
                    except Exception as e:
                        logger.error(
                            "Failed to cancel mirrored orders",
                            error=str(e),
                            order_ids=our_order_ids,
                            exc_info=True,
                        )
                else:
                    logger.debug(
                        "No mirrored orders found for canceled source orders",
                        source_order_ids=order_ids,
                    )

            except Exception as e:
                # Failed to process cancellation event
                logger.error(
                    "Failed to process OrdersCanceled event",
                    error=str(e),
                    order_ids=order_ids,
                    exc_info=True,
                )

        return on_orders_canceled

    async def start(self) -> None:
        """Start the copy trading bot and connect all WebSockets."""
        logger.info(
            "Starting copy trading bot",
            markets=len(self.ws_clients),
            source_wallets=len(self.source_wallets),
        )

        # Connect all WebSocket clients
        connect_tasks = []
        for market_address, ws_client in self.ws_clients:
            logger.debug("Connecting to WebSocket", market=market_address)
            connect_tasks.append(ws_client.connect())

        # Connect all in parallel
        await asyncio.gather(*connect_tasks)

        self.is_running = True
        logger.info("Copy trading bot started successfully")

    async def stop(self) -> None:
        """Stop the copy trading bot and disconnect all WebSockets."""
        logger.info("Stopping copy trading bot")

        # Disconnect all WebSocket clients
        disconnect_tasks = []
        for market_address, ws_client in self.ws_clients:
            logger.debug("Disconnecting from WebSocket", market=market_address)
            disconnect_tasks.append(ws_client.disconnect())

        # Disconnect all in parallel
        await asyncio.gather(*disconnect_tasks)

        self.is_running = False
        logger.info("Copy trading bot stopped")

    async def run(self) -> None:
        """Run the bot indefinitely until stopped.

        This method starts the bot and keeps it running.
        Call stop() to gracefully shutdown.
        """
        await self.start()

        try:
            # Keep running until stop() is called
            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Bot cancelled, shutting down")
        finally:
            await self.stop()

    def get_statistics(self) -> dict[str, Any]:
        """Get bot statistics.

        Returns:
            Dictionary with bot and copier statistics
        """
        stats = {
            "trades_detected": self._trades_detected,
            "orders_detected": self._orders_detected,
            "orders_canceled_detected": self._orders_canceled_detected,
            "tracked_orders": len(self._order_mapping),
        }

        # Include copier statistics
        copier_stats = self.copier.get_statistics()
        stats.update(copier_stats)

        return stats

    def reset_statistics(self) -> None:
        """Reset bot statistics."""
        self._trades_detected = 0
        self._orders_detected = 0
        self._orders_canceled_detected = 0
        self._order_mapping.clear()
        self.copier.reset_statistics()
