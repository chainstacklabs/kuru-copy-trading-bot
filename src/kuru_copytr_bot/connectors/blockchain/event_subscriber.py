"""Blockchain event subscriber using eth_subscribe for real-time contract events."""

import asyncio
import json
from collections.abc import Callable
from typing import Any

from web3 import Web3
from websockets import connect

from src.kuru_copytr_bot.models.order import OrderResponse
from src.kuru_copytr_bot.models.trade import TradeResponse
from src.kuru_copytr_bot.utils.logger import get_logger

logger = get_logger(__name__)


class BlockchainEventSubscriber:
    """Subscribes to blockchain contract events using eth_subscribe.

    Listens to OrderBook contract events directly from blockchain RPC:
    - OrderCreated
    - Trade
    - OrdersCanceled
    """

    def __init__(
        self,
        rpc_ws_url: str,
        market_address: str,
        orderbook_abi: list[dict[str, Any]],
    ):
        """Initialize event subscriber.

        Args:
            rpc_ws_url: WebSocket RPC URL (e.g., wss://monad-testnet.drpc.org)
            market_address: OrderBook contract address to monitor
            orderbook_abi: OrderBook contract ABI for event parsing
        """
        self.rpc_ws_url = rpc_ws_url
        self.market_address = market_address.lower()
        self.orderbook_abi = orderbook_abi

        # WebSocket connection
        self.ws = None
        self.subscription_id = None
        self.running = False

        # Web3 instance for event parsing (no provider needed)
        self.w3 = Web3()
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(market_address), abi=orderbook_abi
        )

        # Event signatures (keccak256 of event signature)
        # Compute event signature hashes from event ABIs
        self.event_signatures = {}
        for event_name in ["OrderCreated", "Trade", "OrdersCanceled"]:
            event = getattr(self.contract.events, event_name)
            event_abi = event._get_event_abi()
            # Build event signature string: EventName(type1,type2,...)
            input_types = ",".join([inp["type"] for inp in event_abi["inputs"]])
            event_signature = f"{event_abi['name']}({input_types})"
            # Compute keccak256 hash
            signature_hash = self.w3.keccak(text=event_signature).hex()
            self.event_signatures[event_name] = signature_hash

            logger.debug(
                "Computed event signature hash",
                event_name=event_name,
                signature=event_signature,
                hash=signature_hash,
            )

        # Callbacks
        self.on_order_created_callback: Callable[[OrderResponse], None] | None = None
        self.on_trade_callback: Callable[[TradeResponse], None] | None = None
        self.on_orders_canceled_callback: (
            Callable[[list[int], list[str], str, list[dict[str, Any]]], None] | None
        ) = None

    async def connect(self) -> None:
        """Connect to blockchain RPC and subscribe to logs."""
        try:
            logger.info("blockchain_event_subscriber_connecting", url=self.rpc_ws_url)

            # Connect to WebSocket RPC
            self.ws = await connect(self.rpc_ws_url)

            # Subscribe to logs from the OrderBook contract
            subscribe_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_subscribe",
                "params": [
                    "logs",
                    {
                        "address": self.market_address,
                        # No topics filter - get all events from this contract
                    },
                ],
            }

            await self.ws.send(json.dumps(subscribe_request))
            response = await self.ws.recv()
            response_data = json.loads(response)

            if "result" in response_data:
                self.subscription_id = response_data["result"]
                logger.info(
                    "blockchain_subscription_created",
                    subscription_id=self.subscription_id,
                    market=self.market_address,
                )
            else:
                error = response_data.get("error", "Unknown error")
                raise Exception(f"Failed to subscribe: {error}")

            # Start listening loop
            self.running = True
            self._listen_task = asyncio.create_task(self._listen_loop())

        except Exception as e:
            logger.error(
                "blockchain_subscription_failed",
                error=str(e),
                url=self.rpc_ws_url,
                exc_info=True,
            )
            raise

    async def disconnect(self) -> None:
        """Disconnect from blockchain RPC."""
        self.running = False

        if self.ws and self.subscription_id:
            try:
                # Unsubscribe
                unsubscribe_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "eth_unsubscribe",
                    "params": [self.subscription_id],
                }
                await self.ws.send(json.dumps(unsubscribe_request))
                await self.ws.close()
                logger.info("blockchain_subscription_closed")
            except Exception as e:
                logger.warning("blockchain_unsubscribe_error", error=str(e))

    async def _listen_loop(self) -> None:
        """Listen for incoming log events."""
        try:
            while self.running and self.ws:
                message = await self.ws.recv()
                await self._process_message(message)
        except Exception as e:
            if self.running:
                logger.error("blockchain_listen_error", error=str(e), exc_info=True)

    async def _process_message(self, message: str) -> None:
        """Process incoming log message.

        Args:
            message: JSON-RPC notification message
        """
        try:
            data = json.loads(message)

            # Check if this is a subscription notification
            if "params" not in data or "result" not in data["params"]:
                return

            log_entry = data["params"]["result"]

            # Parse the log entry
            await self._parse_log(log_entry)

        except Exception as e:
            logger.error("message_parse_error", error=str(e), message=message)

    async def _parse_log(self, log_entry: dict[str, Any]) -> None:
        """Parse log entry and call appropriate callback.

        Args:
            log_entry: Raw log entry from eth_subscribe
        """
        try:
            # Get the event signature (first topic)
            if not log_entry.get("topics") or len(log_entry["topics"]) == 0:
                return

            # Normalize event signature - remove 0x prefix if present for comparison
            event_signature = log_entry["topics"][0]
            if isinstance(event_signature, str) and event_signature.startswith("0x"):
                event_signature = event_signature[2:]

            # Identify which event this is
            if event_signature == self.event_signatures["OrderCreated"]:
                await self._handle_order_created(log_entry)
            elif event_signature == self.event_signatures["Trade"]:
                await self._handle_trade(log_entry)
            elif event_signature == self.event_signatures["OrdersCanceled"]:
                await self._handle_orders_canceled(log_entry)
            else:
                logger.debug("unknown_event_signature", signature=event_signature)

        except Exception as e:
            logger.error("log_parse_error", error=str(e), log=log_entry, exc_info=True)

    async def _handle_order_created(self, log_entry: dict[str, Any]) -> None:
        """Handle OrderCreated event.

        Args:
            log_entry: Raw log entry
        """
        try:
            # Decode the event using Web3
            event = self.contract.events.OrderCreated().process_log(log_entry)
            args = event["args"]

            # Create OrderResponse from event args
            order_response = OrderResponse(
                order_id=args["orderId"],
                market_address=self.market_address,
                owner=args["owner"],
                price=str(args["price"] / 1_000_000),  # Convert from price precision
                size=str(args["size"] / 10**18),  # Convert from wei
                remaining_size=str(args["remainingSize"] / 10**18),
                is_buy=args["isBuy"],
                is_canceled=args.get("isCanceled", False),
                cloid=args.get("cloid"),
            )

            logger.info(
                "order_created_event",
                order_id=order_response.order_id,
                owner=order_response.owner,
                side="BUY" if order_response.is_buy else "SELL",
                price=order_response.price,
                size=order_response.size,
            )

            # Call callback
            if self.on_order_created_callback:
                await self.on_order_created_callback(order_response)

        except Exception as e:
            logger.error("order_created_parse_error", error=str(e), log=log_entry)

    async def _handle_trade(self, log_entry: dict[str, Any]) -> None:
        """Handle Trade event.

        Args:
            log_entry: Raw log entry
        """
        try:
            # Decode the event using Web3
            event = self.contract.events.Trade().process_log(log_entry)
            args = event["args"]

            # Create TradeResponse from event args
            trade_response = TradeResponse(
                orderid=args["orderId"],
                makeraddress=args["makerAddress"],
                takeraddress=args.get("takerAddress", ""),
                isbuy=args["isBuy"],
                price=str(args["price"] / 1_000_000),  # Convert from price precision
                filledsize=str(args["filledSize"] / 10**18),  # Convert from wei
                transactionhash=log_entry["transactionHash"],
                triggertime=0,  # Not available in log
            )

            logger.info(
                "trade_event",
                order_id=trade_response.orderid,
                maker=trade_response.makeraddress,
                side="BUY" if trade_response.isbuy else "SELL",
                price=trade_response.price,
                filled_size=trade_response.filledsize,
            )

            # Call callback
            if self.on_trade_callback:
                await self.on_trade_callback(trade_response)

        except Exception as e:
            logger.error("trade_parse_error", error=str(e), log=log_entry)

    async def _handle_orders_canceled(self, log_entry: dict[str, Any]) -> None:
        """Handle OrdersCanceled event.

        Args:
            log_entry: Raw log entry
        """
        try:
            # Decode the event using Web3
            event = self.contract.events.OrdersCanceled().process_log(log_entry)
            args = event["args"]

            order_ids = args["orderIds"]
            maker_address = args["maker"]
            cloids = args.get("cloids", [])

            logger.info(
                "orders_canceled_event",
                order_count=len(order_ids),
                order_ids=order_ids,
                maker_address=maker_address,
            )

            # Call callback
            if self.on_orders_canceled_callback:
                await self.on_orders_canceled_callback(order_ids, cloids, maker_address, [])

        except Exception as e:
            logger.error("orders_canceled_parse_error", error=str(e), log=log_entry)

    def set_order_created_callback(self, callback: Callable[[OrderResponse], None]) -> None:
        """Set callback for OrderCreated events."""
        self.on_order_created_callback = callback

    def set_trade_callback(self, callback: Callable[[TradeResponse], None]) -> None:
        """Set callback for Trade events."""
        self.on_trade_callback = callback

    def set_orders_canceled_callback(
        self,
        callback: Callable[[list[int], list[str], str, list[dict[str, Any]]], None],
    ) -> None:
        """Set callback for OrdersCanceled events."""
        self.on_orders_canceled_callback = callback

    @property
    def is_connected(self) -> bool:
        """Check if connected to blockchain."""
        return self.ws is not None and not self.ws.closed
