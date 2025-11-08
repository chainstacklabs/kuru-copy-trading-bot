"""Unit tests for Kuru event detector."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from src.kuru_copytr_bot.monitoring.detector import KuruEventDetector
from src.kuru_copytr_bot.models.trade import Trade
from src.kuru_copytr_bot.core.enums import OrderSide


class TestKuruEventDetectorInitialization:
    """Test KuruEventDetector initialization."""

    def test_detector_initializes_successfully(self):
        """Detector should initialize without errors."""
        detector = KuruEventDetector()
        assert detector is not None


class TestKuruEventDetectorTradeExecuted:
    """Test parsing TradeExecuted events."""

    def test_detector_parses_trade_executed_event(self):
        """Detector should parse TradeExecuted event to Trade model."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "1" * 64,  # TradeExecuted event signature
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",  # trader
            ],
            "data": "0x" +
                    "00000000000000000000000000000000000000000000006c6b935b8bbd400000" +  # price=2000 * 10^18
                    "0000000000000000000000000000000000000000000000000de0b6b3a7640000" +  # size=1.0 * 10^18
                    "0000000000000000000000000000000000000000000000000000000000000000",  # side=0 (BUY)
            "blockNumber": 1000,
            "transactionHash": "0xabc123def4567890123456789012345678901234567890123456789012345678",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert isinstance(trade, Trade)
        assert trade.trader_address == "0x1111111111111111111111111111111111111111"
        assert trade.tx_hash == "0xabc123def4567890123456789012345678901234567890123456789012345678"

    def test_detector_parses_buy_trade(self):
        """Detector should correctly identify buy trades."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "1" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" +
                    "00000000000000000000000000000000000000000000000000000000000007d0" +  # price=2000
                    "0000000000000000000000000000000000000000000000000de0b6b3a7640000" +  # size=1.0
                    "0000000000000000000000000000000000000000000000000000000000000000",  # side=0 (BUY)
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade.side == OrderSide.BUY

    def test_detector_parses_sell_trade(self):
        """Detector should correctly identify sell trades."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "1" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" +
                    "00000000000000000000000000000000000000000000000000000000000007d0" +  # price
                    "0000000000000000000000000000000000000000000000000de0b6b3a7640000" +  # size
                    "0000000000000000000000000000000000000000000000000000000000000001",  # side=1 (SELL)
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade.side == OrderSide.SELL

    def test_detector_converts_price_from_wei(self):
        """Detector should convert price from wei to decimal."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "1" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" +
                    "00000000000000000000000000000000000000000000006c6b935b8bbd400000" +  # 2000 * 10^18
                    "0000000000000000000000000000000000000000000000000de0b6b3a7640000" +
                    "0000000000000000000000000000000000000000000000000000000000000000",
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert isinstance(trade.price, Decimal)
        assert trade.price == Decimal("2000.0")

    def test_detector_converts_size_from_wei(self):
        """Detector should convert size from wei to decimal."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "1" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" +
                    "00000000000000000000000000000000000000000000000000000000000007d0" +
                    "0000000000000000000000000000000000000000000000000de0b6b3a7640000" +  # 1.0 * 10^18
                    "0000000000000000000000000000000000000000000000000000000000000000",
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert isinstance(trade.size, Decimal)
        assert trade.size == Decimal("1.0")


class TestKuruEventDetectorOrderPlaced:
    """Test parsing OrderPlaced events."""

    def test_detector_parses_order_placed_event(self):
        """Detector should parse OrderPlaced event."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "0" * 64,  # OrderPlaced event signature
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",  # trader
            ],
            "data": "0x" + "a" * 128,  # order data
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        order_data = detector.parse_order_placed(event_log)

        assert order_data is not None
        assert "trader_address" in order_data

    def test_detector_extracts_order_id_from_event(self):
        """Detector should extract order ID from OrderPlaced event."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "0" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" +
                    "0000000000000000000000000000000000000000000000000000000000000001" +  # order_id=1
                    "00000000000000000000000000000000000000000000000000000000000007d0" +  # price
                    "0000000000000000000000000000000000000000000000000de0b6b3a7640000",  # size
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        order_data = detector.parse_order_placed(event_log)

        assert order_data["order_id"] == "1"


class TestKuruEventDetectorOrderCancelled:
    """Test parsing OrderCancelled events."""

    def test_detector_parses_order_cancelled_event(self):
        """Detector should parse OrderCancelled event."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "2" * 64,  # OrderCancelled event signature
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",  # trader
            ],
            "data": "0x" + "0" * 63 + "1",  # order_id=1
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        cancel_data = detector.parse_order_cancelled(event_log)

        assert cancel_data is not None
        assert "order_id" in cancel_data

    def test_detector_extracts_cancelled_order_id(self):
        """Detector should extract order ID from cancelled event."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "2" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" + "0" * 63 + "5",  # order_id=5
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        cancel_data = detector.parse_order_cancelled(event_log)

        assert cancel_data["order_id"] == "5"


class TestKuruEventDetectorErrorHandling:
    """Test error handling for malformed events."""

    def test_detector_handles_malformed_event(self):
        """Detector should handle malformed events gracefully."""
        event_log = {
            "topics": [],
            "data": "0xinvalid",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade is None

    def test_detector_handles_missing_topics(self):
        """Detector should handle events with missing topics."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            # Missing topics field
            "data": "0x" + "a" * 128,
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade is None

    def test_detector_handles_missing_data(self):
        """Detector should handle events with missing data."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": ["0x" + "1" * 64],
            # Missing data field
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade is None

    def test_detector_handles_invalid_data_length(self):
        """Detector should handle events with invalid data length."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": ["0x" + "1" * 64],
            "data": "0xaa",  # Too short
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade is None

    def test_detector_handles_decoding_errors(self):
        """Detector should handle decoding errors gracefully."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": ["0x" + "1" * 64],
            "data": "0xZZZZZZZZ",  # Invalid hex
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade is None


class TestKuruEventDetectorMarketParsing:
    """Test market identifier parsing."""

    def test_detector_extracts_market_from_event(self):
        """Detector should extract market identifier from event."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "1" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" +
                    "00000000000000000000000000000000000000000000000000000000000007d0" +
                    "0000000000000000000000000000000000000000000000000de0b6b3a7640000" +
                    "0000000000000000000000000000000000000000000000000000000000000000" +
                    # Market string: "ETH-USDC" encoded
                    "4554482d55534443" + "0" * 48,  # "ETH-USDC" in hex
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade.market == "ETH-USDC"


class TestKuruEventDetectorTimestamp:
    """Test timestamp handling."""

    def test_detector_sets_timestamp_from_block(self):
        """Detector should set timestamp based on block time."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "1" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" +
                    "00000000000000000000000000000000000000000000000000000000000007d0" +
                    "0000000000000000000000000000000000000000000000000de0b6b3a7640000" +
                    "0000000000000000000000000000000000000000000000000000000000000000",
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
            "timestamp": 1234567890,
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert isinstance(trade.timestamp, datetime)
        assert trade.timestamp.tzinfo == timezone.utc


class TestKuruEventDetectorEventTypeDetection:
    """Test event type detection."""

    def test_detector_identifies_event_type(self):
        """Detector should identify event type from signature."""
        detector = KuruEventDetector()

        # TradeExecuted
        assert detector.get_event_type("0x" + "1" * 64) == "TradeExecuted"

        # OrderPlaced
        assert detector.get_event_type("0x" + "0" * 64) == "OrderPlaced"

        # OrderCancelled
        assert detector.get_event_type("0x" + "2" * 64) == "OrderCancelled"

    def test_detector_handles_unknown_event_type(self):
        """Detector should handle unknown event types."""
        detector = KuruEventDetector()

        event_type = detector.get_event_type("0x" + "9" * 64)
        assert event_type == "Unknown"


class TestKuruEventDetectorDecimalPrecision:
    """Test decimal precision in parsing."""

    def test_detector_maintains_decimal_precision(self):
        """Detector should maintain decimal precision for prices and sizes."""
        event_log = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                "0x" + "1" * 64,
                "0x000000000000000000000000" + "1111111111111111111111111111111111111111",
            ],
            "data": "0x" +
                    "00000000000000000000000000000000000000000000006c6b935b8bbd400000" +  # 2000 * 10^18
                    "00000000000000000000000000000000000000000000000006f05b59d3b20000" +  # 0.5 * 10^18
                    "0000000000000000000000000000000000000000000000000000000000000000",
            "blockNumber": 1000,
            "transactionHash": "0xabc1234567890123456789012345678901234567890123456789012345678901",
        }

        detector = KuruEventDetector()
        trade = detector.parse_trade_executed(event_log)

        assert trade.price == Decimal("2000.0")
        assert trade.size == Decimal("0.5")
        # Check precision is maintained
        assert isinstance(trade.price, Decimal)
        assert isinstance(trade.size, Decimal)
