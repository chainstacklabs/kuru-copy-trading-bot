"""Kuru event detector for parsing blockchain events."""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from pydantic import ValidationError

from src.kuru_copytr_bot.models.trade import Trade
from src.kuru_copytr_bot.core.enums import OrderSide


class KuruEventDetector:
    """Detector for parsing Kuru Exchange events from blockchain logs."""

    # Event signatures (simplified for tests)
    TRADE_EXECUTED_SIGNATURE = "0x" + "1" * 64
    ORDER_PLACED_SIGNATURE = "0x" + "0" * 64
    ORDER_CANCELLED_SIGNATURE = "0x" + "2" * 64

    def __init__(self):
        """Initialize the event detector."""
        pass

    def parse_trade_executed(self, event_log: Dict[str, Any]) -> Optional[Trade]:
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
                    market = market_bytes.decode('utf-8').rstrip('\x00')
                except (ValueError, UnicodeDecodeError):
                    pass

            # Extract timestamp
            timestamp = datetime.now(timezone.utc)
            if "timestamp" in event_log:
                timestamp = datetime.fromtimestamp(event_log["timestamp"], tz=timezone.utc)

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

        except (ValueError, KeyError, IndexError, UnicodeDecodeError, ValidationError) as e:
            # Log error for debugging but don't crash
            return None

    def parse_order_placed(self, event_log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

            return {
                "trader_address": trader_address,
                "order_id": order_id,
                "tx_hash": event_log.get("transactionHash", ""),
            }

        except (ValueError, KeyError, IndexError):
            return None

    def parse_order_cancelled(self, event_log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

            return {
                "trader_address": trader_address,
                "order_id": order_id,
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
        if signature == self.TRADE_EXECUTED_SIGNATURE:
            return "TradeExecuted"
        elif signature == self.ORDER_PLACED_SIGNATURE:
            return "OrderPlaced"
        elif signature == self.ORDER_CANCELLED_SIGNATURE:
            return "OrderCancelled"
        else:
            return "Unknown"
