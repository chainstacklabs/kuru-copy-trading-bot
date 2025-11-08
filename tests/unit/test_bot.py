"""Tests for copy trading bot orchestrator."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, call

from src.kuru_copytr_bot.bot import CopyTradingBot
from src.kuru_copytr_bot.models.trade import Trade
from src.kuru_copytr_bot.core.enums import OrderSide
from src.kuru_copytr_bot.core.exceptions import BlockchainConnectionError


@pytest.fixture
def mock_monitor():
    """Mock wallet monitor."""
    monitor = Mock()
    monitor.get_new_transactions.return_value = []
    monitor.is_running = False
    return monitor


@pytest.fixture
def mock_detector():
    """Mock event detector."""
    detector = Mock()
    return detector


@pytest.fixture
def mock_copier():
    """Mock trade copier."""
    copier = Mock()
    copier.process_trade.return_value = "order_123"
    copier.get_statistics.return_value = {
        "successful_trades": 0,
        "failed_trades": 0,
        "rejected_trades": 0,
    }
    return copier


@pytest.fixture
def sample_transaction():
    """Sample transaction for testing."""
    return {
        "hash": "0x" + "a" * 64,
        "from": "0x1111111111111111111111111111111111111111",
        "to": "0x4444444444444444444444444444444444444444",
        "blockNumber": 1000,
    }


@pytest.fixture
def sample_trade():
    """Sample trade for testing."""
    return Trade(
        id="trade_123",
        trader_address="0x1111111111111111111111111111111111111111",
        market="ETH-USDC",
        side=OrderSide.BUY,
        price=Decimal("2000.0"),
        size=Decimal("5.0"),
        timestamp=datetime.now(timezone.utc),
        tx_hash="0x" + "a" * 64,
    )


class TestCopyTradingBotInitialization:
    """Test bot initialization."""

    def test_bot_initializes_with_required_components(
        self, mock_monitor, mock_detector, mock_copier
    ):
        """Bot should initialize with required components."""
        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        assert bot.monitor == mock_monitor
        assert bot.detector == mock_detector
        assert bot.copier == mock_copier

    def test_bot_initializes_with_default_poll_interval(
        self, mock_monitor, mock_detector, mock_copier
    ):
        """Bot should have default poll interval."""
        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        assert bot.poll_interval == 5  # 5 seconds default

    def test_bot_initializes_with_custom_poll_interval(
        self, mock_monitor, mock_detector, mock_copier
    ):
        """Bot should accept custom poll interval."""
        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
            poll_interval=10,
        )

        assert bot.poll_interval == 10


class TestCopyTradingBotLifecycle:
    """Test bot lifecycle management."""

    def test_bot_starts_monitoring(self, mock_monitor, mock_detector, mock_copier):
        """Bot should start wallet monitor when started."""
        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.start()

        mock_monitor.start.assert_called_once()
        assert bot.is_running is True

    def test_bot_stops_monitoring(self, mock_monitor, mock_detector, mock_copier):
        """Bot should stop wallet monitor when stopped."""
        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.start()
        bot.stop()

        mock_monitor.stop.assert_called_once()
        assert bot.is_running is False


class TestCopyTradingBotProcessing:
    """Test trade processing workflow."""

    def test_bot_processes_transactions(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction
    ):
        """Bot should process new transactions."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()

        mock_monitor.get_new_transactions.assert_called_once()

    def test_bot_parses_events_from_transactions(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction, sample_trade
    ):
        """Bot should parse events from transaction receipts."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.return_value = sample_trade

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()

        # Should attempt to parse the transaction
        mock_detector.parse_trade_executed.assert_called()

    def test_bot_copies_detected_trades(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction, sample_trade
    ):
        """Bot should copy detected trades."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.return_value = sample_trade

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()

        mock_copier.process_trade.assert_called_once_with(sample_trade)

    def test_bot_handles_no_transactions(
        self, mock_monitor, mock_detector, mock_copier
    ):
        """Bot should handle no new transactions gracefully."""
        mock_monitor.get_new_transactions.return_value = []

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()

        mock_detector.parse_trade_executed.assert_not_called()
        mock_copier.process_trade.assert_not_called()

    def test_bot_skips_unparseable_events(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction
    ):
        """Bot should skip events that cannot be parsed."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.return_value = None

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()

        mock_copier.process_trade.assert_not_called()

    def test_bot_processes_multiple_transactions(
        self, mock_monitor, mock_detector, mock_copier, sample_trade
    ):
        """Bot should process multiple transactions in one cycle."""
        tx1 = {
            "hash": "0x" + "a" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1000,
        }
        tx2 = {
            "hash": "0x" + "b" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1001,
        }

        mock_monitor.get_new_transactions.return_value = [tx1, tx2]
        mock_detector.parse_trade_executed.return_value = sample_trade

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()

        assert mock_copier.process_trade.call_count == 2


class TestCopyTradingBotErrorHandling:
    """Test error handling."""

    def test_bot_handles_monitor_errors(
        self, mock_monitor, mock_detector, mock_copier
    ):
        """Bot should handle monitor errors gracefully."""
        mock_monitor.get_new_transactions.side_effect = BlockchainConnectionError(
            "Connection failed"
        )

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        # Should not raise exception
        bot.process_once()

        mock_detector.parse_trade_executed.assert_not_called()

    def test_bot_continues_on_detector_errors(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction
    ):
        """Bot should continue processing if detector fails."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.side_effect = Exception("Parse error")

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        # Should not raise exception
        bot.process_once()

    def test_bot_continues_on_copier_errors(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction, sample_trade
    ):
        """Bot should continue processing if copier fails."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.return_value = sample_trade
        mock_copier.process_trade.side_effect = Exception("Execution error")

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        # Should not raise exception
        bot.process_once()


class TestCopyTradingBotStatistics:
    """Test statistics tracking."""

    def test_bot_tracks_processed_transactions(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction, sample_trade
    ):
        """Bot should track number of processed transactions."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.return_value = sample_trade

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()
        bot.process_once()

        stats = bot.get_statistics()
        assert stats["transactions_processed"] == 2

    def test_bot_tracks_trades_detected(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction, sample_trade
    ):
        """Bot should track number of trades detected."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.return_value = sample_trade

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()

        stats = bot.get_statistics()
        assert stats["trades_detected"] == 1

    def test_bot_includes_copier_statistics(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction, sample_trade
    ):
        """Bot should include copier statistics."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.return_value = sample_trade
        mock_copier.get_statistics.return_value = {
            "successful_trades": 5,
            "failed_trades": 2,
            "rejected_trades": 1,
        }

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        stats = bot.get_statistics()
        assert stats["successful_trades"] == 5
        assert stats["failed_trades"] == 2
        assert stats["rejected_trades"] == 1

    def test_bot_resets_statistics(
        self, mock_monitor, mock_detector, mock_copier, sample_transaction, sample_trade
    ):
        """Bot should reset statistics."""
        mock_monitor.get_new_transactions.return_value = [sample_transaction]
        mock_detector.parse_trade_executed.return_value = sample_trade

        bot = CopyTradingBot(
            monitor=mock_monitor,
            detector=mock_detector,
            copier=mock_copier,
        )

        bot.process_once()
        bot.reset_statistics()

        stats = bot.get_statistics()
        assert stats["transactions_processed"] == 0
        assert stats["trades_detected"] == 0
        mock_copier.reset_statistics.assert_called_once()
