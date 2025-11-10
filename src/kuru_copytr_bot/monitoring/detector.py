"""Kuru event detector for parsing blockchain events."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import ValidationError
from web3 import Web3

from src.kuru_copytr_bot.core.enums import OrderSide
from src.kuru_copytr_bot.models.trade import Trade


def calculate_event_topic(signature: str) -> str:
    """Calculate Keccak256 hash of event signature.

    Args:
        signature: Event signature string (e.g., "OrderCreated(uint40,address,uint96,uint32,bool)")

    Returns:
        32-byte hex hash with 0x prefix
    """
    return "0x" + Web3.keccak(text=signature).hex()


class KuruEventDetector:
    """Detector for parsing Kuru Exchange events from blockchain logs."""

    # Event signatures - calculated from actual event definitions
    # Based on OrderBook contract events and Kuru API spec
    ORDER_CREATED_SIGNATURE = calculate_event_topic(
        "OrderCreated(uint40,address,uint96,uint32,bool)"
    )
    TRADE_SIGNATURE = calculate_event_topic("Trade(uint40,address,address,bool,uint256,uint256)")
    ORDERS_CANCELED_SIGNATURE = calculate_event_topic("OrdersCanceled(uint40[],address)")

    # Maintain old names for backward compatibility (map to new signatures)
    TRADE_EXECUTED_SIGNATURE = TRADE_SIGNATURE
    ORDER_PLACED_SIGNATURE = ORDER_CREATED_SIGNATURE
    ORDER_CANCELLED_SIGNATURE = ORDERS_CANCELED_SIGNATURE

    def __init__(self):
        """Initialize the event detector."""
        pass

    def parse_trade_executed(self, event_log: dict[str, Any]) -> Trade | None:
        """Parse TradeExecuted event to Trade model.

        Args:
            event_log: Raw event log from blockchain

        Returns:
            Trade object if parsing successful, None otherwise
        """
        try:
            # Validate required fields
            if "topics" not in event_log or "data" not in event_log:
                return None

            topics = event_log["topics"]
            data = event_log["data"]

            # Need at least 2 topics (signature + trader)
            if len(topics) < 2:
                return None

            # Extract trader address from topics[1]
            trader_topic = topics[1]
            if not isinstance(trader_topic, str) or not trader_topic.startswith("0x"):
                return None

            # Remove 0x and take last 40 characters (20 bytes = 40 hex chars)
            trader_address = "0x" + trader_topic[-40:]

            # Parse data field
            if not isinstance(data, str) or not data.startswith("0x"):
                return None

            # Remove 0x prefix
            hex_data = data[2:]

            # Each parameter is 32 bytes (64 hex chars)
            # Expected: price (64) + size (64) + side (64) + optional market
            if len(hex_data) < 192:  # Minimum 3 parameters
                return None

            # Extract price (first 64 chars)
            price_hex = hex_data[0:64]
            price_wei = int(price_hex, 16)
            price = Decimal(price_wei) / Decimal(10**18)

            # Extract size (next 64 chars)
            size_hex = hex_data[64:128]
            size_wei = int(size_hex, 16)
            size = Decimal(size_wei) / Decimal(10**18)

            # Extract side (next 64 chars)
            side_hex = hex_data[128:192]
            side_value = int(side_hex, 16)
            side = OrderSide.BUY if side_value == 0 else OrderSide.SELL

            # Extract market identifier if present
            market = "ETH-USDC"  # Default
            if len(hex_data) > 192:
                market_hex = hex_data[192:256]
                # Try to decode as UTF-8 string
                try:
                    market_bytes = bytes.fromhex(market_hex)
                    market = market_bytes.decode("utf-8").rstrip("\x00")
                except (ValueError, UnicodeDecodeError):
                    pass

            # Extract timestamp
            timestamp = datetime.now(UTC)
            if "timestamp" in event_log:
                timestamp = datetime.fromtimestamp(event_log["timestamp"], tz=UTC)

            # Create Trade object
            trade = Trade(
                id=event_log.get("transactionHash", ""),
                trader_address=trader_address,
                market=market,
                side=side,
                price=price if price > 0 else Decimal("0.000001"),  # Ensure price > 0
                size=size if size > 0 else Decimal("0.000001"),  # Ensure size > 0
                timestamp=timestamp,
                tx_hash=event_log.get("transactionHash", ""),
            )

            return trade

        except (ValueError, KeyError, IndexError, UnicodeDecodeError, ValidationError):
            # Log error for debugging but don't crash
            return None

    def parse_order_placed(self, event_log: dict[str, Any]) -> dict[str, Any] | None:
        """Parse OrderPlaced event.

        Args:
            event_log: Raw event log from blockchain

        Returns:
            Dict with order data if parsing successful, None otherwise
        """
        try:
            # Validate required fields
            if "topics" not in event_log or "data" not in event_log:
                return None

            topics = event_log["topics"]
            data = event_log["data"]

            # Need at least 2 topics (signature + trader)
            if len(topics) < 2:
                return None

            # Extract trader address from topics[1]
            trader_topic = topics[1]
            if not isinstance(trader_topic, str) or not trader_topic.startswith("0x"):
                return None

            trader_address = "0x" + trader_topic[-40:]

            # Parse data field
            if not isinstance(data, str) or not data.startswith("0x"):
                return None

            hex_data = data[2:]

            # Need at least order_id (64 chars)
            if len(hex_data) < 64:
                return None

            # Extract order_id (first 64 chars)
            order_id_hex = hex_data[0:64]
            order_id = str(int(order_id_hex, 16))

            # Extract CLOID if present (would be in subsequent data fields)
            # TODO: Determine exact field offset once full event structure is known
            cloid = None
            # If event includes CLOID field, it would be extracted here
            # For now, setting to None as current contract events don't include it

            return {
                "trader_address": trader_address,
                "order_id": order_id,
                "cloid": cloid,
                "tx_hash": event_log.get("transactionHash", ""),
            }

        except (ValueError, KeyError, IndexError):
            return None

    def parse_order_cancelled(self, event_log: dict[str, Any]) -> dict[str, Any] | None:
        """Parse OrderCancelled event.

        Args:
            event_log: Raw event log from blockchain

        Returns:
            Dict with cancel data if parsing successful, None otherwise
        """
        try:
            # Validate required fields
            if "topics" not in event_log or "data" not in event_log:
                return None

            topics = event_log["topics"]
            data = event_log["data"]

            # Need at least 2 topics (signature + trader)
            if len(topics) < 2:
                return None

            # Extract trader address from topics[1]
            trader_topic = topics[1]
            if not isinstance(trader_topic, str) or not trader_topic.startswith("0x"):
                return None

            trader_address = "0x" + trader_topic[-40:]

            # Parse data field
            if not isinstance(data, str) or not data.startswith("0x"):
                return None

            hex_data = data[2:]

            # Need at least order_id (64 chars)
            if len(hex_data) < 64:
                return None

            # Extract order_id (first 64 chars)
            order_id_hex = hex_data[0:64]
            order_id = str(int(order_id_hex, 16))

            # Extract CLOID if present
            # TODO: Determine exact field offset once full event structure is known
            cloid = None

            return {
                "trader_address": trader_address,
                "order_id": order_id,
                "cloid": cloid,
                "tx_hash": event_log.get("transactionHash", ""),
            }

        except (ValueError, KeyError, IndexError):
            return None

    def get_event_type(self, signature: str) -> str:
        """Identify event type from signature.

        Args:
            signature: Event signature hash

        Returns:
            Event type name or "Unknown"
        """
        if signature == self.ORDER_CREATED_SIGNATURE:
            return "OrderCreated"
        elif signature == self.TRADE_SIGNATURE:
            return "Trade"
        elif signature == self.ORDERS_CANCELED_SIGNATURE:
            return "OrdersCanceled"
        else:
            return "Unknown"
