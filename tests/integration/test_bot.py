"""Integration tests for end-to-end copy trading bot workflow.

These tests verify the complete workflow from transaction detection
through trade execution, using mocked blockchain and API responses.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, call

from src.kuru_copytr_bot.bot import CopyTradingBot
from src.kuru_copytr_bot.monitoring.monitor import WalletMonitor
from src.kuru_copytr_bot.monitoring.detector import KuruEventDetector
from src.kuru_copytr_bot.trading.copier import TradeCopier
from src.kuru_copytr_bot.risk.calculator import PositionSizeCalculator
from src.kuru_copytr_bot.risk.validator import TradeValidator
from src.kuru_copytr_bot.connectors.blockchain.monad import MonadClient
from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient
from src.kuru_copytr_bot.models.trade import Trade
from src.kuru_copytr_bot.core.enums import OrderSide, OrderType
from src.kuru_copytr_bot.core.exceptions import BlockchainConnectionError


@pytest.fixture
def mock_blockchain():
    """Mock blockchain connector."""
    blockchain = MagicMock()
    blockchain.get_latest_transactions.return_value = []
    blockchain.get_balance.return_value = Decimal("10000.0")
    blockchain.send_transaction.return_value = "0x" + "a" * 64
    blockchain.is_connected.return_value = True
    blockchain.wallet_address = "0x5555555555555555555555555555555555555555"
    return blockchain


@pytest.fixture
def mock_kuru_api():
    """Mock Kuru API responses."""
    with patch('src.kuru_copytr_bot.connectors.platforms.kuru.requests.get') as mock_get, \
         patch('src.kuru_copytr_bot.connectors.platforms.kuru.requests.post') as mock_post:

        # Mock market parameters
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "min_order_size": "0.001",
            "max_order_size": "1000",
            "tick_size": "0.01",
            "is_active": True,
        }

        yield mock_get, mock_post


@pytest.fixture
def integrated_bot(mock_blockchain, mock_kuru_api):
    """Create a fully integrated bot with mocked external dependencies."""
    # Create Kuru client
    kuru_client = KuruClient(
        blockchain=mock_blockchain,
        api_url="https://api.kuru.exchange",
        contract_address="0x4444444444444444444444444444444444444444",
    )

    # Create wallet monitor
    monitor = WalletMonitor(
        blockchain=mock_blockchain,
        target_wallets=["0x1111111111111111111111111111111111111111"],
        kuru_contract_address="0x4444444444444444444444444444444444444444",
    )

    # Create event detector
    detector = KuruEventDetector()

    # Create position size calculator
    calculator = PositionSizeCalculator(
        copy_ratio=Decimal("0.1"),
        max_position_size=Decimal("100.0"),
        min_order_size=Decimal("0.01"),
        respect_balance=True,
    )

    # Create trade validator
    validator = TradeValidator(
        min_balance=Decimal("10.0"),
        max_position_size=Decimal("100.0"),
        max_exposure_usd=Decimal("100000.0"),  # High limit for integration tests
        market_whitelist=None,
        market_blacklist=None,
    )

    # Create trade copier
    copier = TradeCopier(
        kuru_client=kuru_client,
        calculator=calculator,
        validator=validator,
        default_order_type=OrderType.LIMIT,
    )

    # Create bot
    bot = CopyTradingBot(
        monitor=monitor,
        detector=detector,
        copier=copier,
        poll_interval=5,
    )

    return bot, mock_blockchain


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_successful_trade_detection_and_execution(self, integrated_bot, mock_kuru_api):
        """Should detect trade and execute mirror trade successfully."""
        bot, mock_blockchain = integrated_bot
        mock_get, mock_post = mock_kuru_api

        # Setup: Create a transaction with TradeExecuted event
        tx_hash = "0x" + "a" * 64
        transaction = {
            "hash": tx_hash,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1000,
            "logs": [{
                "topics": [
                    # TradeExecuted event signature
                    "0x" + "b" * 64,
                ],
                "data": "0x" + "0" * 512,
            }],
        }

        # Mock blockchain to return the transaction
        mock_blockchain.get_latest_transactions.return_value = [transaction]

        # Mock detector to parse a valid trade
        with patch.object(bot.detector, 'parse_trade_executed') as mock_parse:
            trade = Trade(
                id="trade_123",
                trader_address="0x1111111111111111111111111111111111111111",
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("5.0"),
                timestamp=datetime.now(timezone.utc),
                tx_hash=tx_hash,
            )
            mock_parse.return_value = trade

            # Start bot
            bot.start()

            # Process one cycle
            bot.process_once()

            # Verify workflow
            assert bot.is_running is True
            mock_blockchain.get_latest_transactions.assert_called_once()
            mock_parse.assert_called_once_with(transaction)

            # Verify statistics
            stats = bot.get_statistics()
            assert stats["transactions_processed"] == 1
            assert stats["trades_detected"] == 1
            assert stats["successful_trades"] == 1
            assert stats["failed_trades"] == 0
            assert stats["rejected_trades"] == 0

            # Stop bot
            bot.stop()
            assert bot.is_running is False

    def test_trade_rejected_due_to_validation(self, integrated_bot, mock_kuru_api):
        """Should reject trade that fails validation."""
        bot, mock_blockchain = integrated_bot

        # Create transaction
        tx_hash = "0x" + "b" * 64
        transaction = {
            "hash": tx_hash,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1001,
            "logs": [{"topics": ["0x" + "c" * 64], "data": "0x" + "0" * 512}],
        }

        mock_blockchain.get_latest_transactions.return_value = [transaction]

        # Mock a trade that will fail validation (insufficient balance)
        with patch.object(bot.detector, 'parse_trade_executed') as mock_parse:
            trade = Trade(
                id="trade_456",
                trader_address="0x1111111111111111111111111111111111111111",
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("5000.0"),  # Very large size will fail validation
                timestamp=datetime.now(timezone.utc),
                tx_hash=tx_hash,
            )
            mock_parse.return_value = trade

            # Mock get_balance to return low balance
            mock_blockchain.get_balance.return_value = Decimal("5.0")

            bot.start()
            bot.process_once()

            # Verify trade was rejected
            stats = bot.get_statistics()
            assert stats["transactions_processed"] == 1
            assert stats["trades_detected"] == 1
            assert stats["successful_trades"] == 0
            assert stats["rejected_trades"] == 1

    def test_multiple_trades_in_sequence(self, integrated_bot, mock_kuru_api):
        """Should process multiple trades in sequence."""
        bot, mock_blockchain = integrated_bot
        mock_get, mock_post = mock_kuru_api

        # Create two transactions
        tx1 = {
            "hash": "0x" + "a" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1000,
            "logs": [{"topics": ["0x" + "b" * 64], "data": "0x" + "0" * 512}],
        }

        tx2 = {
            "hash": "0x" + "c" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1001,
            "logs": [{"topics": ["0x" + "d" * 64], "data": "0x" + "0" * 512}],
        }

        with patch.object(bot.detector, 'parse_trade_executed') as mock_parse, \
             patch.object(bot.copier.kuru_client, 'get_market_params') as mock_market_params:

            # Mock market params for both markets
            mock_market_params.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

            trade1 = Trade(
                id="trade_1",
                trader_address="0x1111111111111111111111111111111111111111",
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("1.0"),
                timestamp=datetime.now(timezone.utc),
                tx_hash=tx1["hash"],
            )

            trade2 = Trade(
                id="trade_2",
                trader_address="0x1111111111111111111111111111111111111111",
                market="BTC-USDC",
                side=OrderSide.SELL,
                price=Decimal("50000.0"),
                size=Decimal("0.5"),
                timestamp=datetime.now(timezone.utc),
                tx_hash=tx2["hash"],
            )

            mock_parse.side_effect = [trade1, trade2]

            # Process first cycle with first transaction
            mock_blockchain.get_latest_transactions.return_value = [tx1]
            bot.start()
            bot.process_once()

            # Process second cycle with second transaction
            mock_blockchain.get_latest_transactions.return_value = [tx2]
            bot.process_once()

            # Verify both trades processed
            stats = bot.get_statistics()
            assert stats["transactions_processed"] == 2
            assert stats["trades_detected"] == 2
            assert stats["successful_trades"] == 2

    def test_handles_non_trade_transactions(self, integrated_bot):
        """Should skip transactions that are not trades."""
        bot, mock_blockchain = integrated_bot

        # Create transaction without trade event
        tx = {
            "hash": "0x" + "e" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1002,
            "logs": [],
        }

        mock_blockchain.get_latest_transactions.return_value = [tx]

        with patch.object(bot.detector, 'parse_trade_executed') as mock_parse:
            mock_parse.return_value = None  # No trade detected

            bot.start()
            bot.process_once()

            # Verify transaction processed but no trade detected
            stats = bot.get_statistics()
            assert stats["transactions_processed"] == 1
            assert stats["trades_detected"] == 0
            assert stats["successful_trades"] == 0

    def test_handles_blockchain_connection_errors(self, integrated_bot):
        """Should handle blockchain connection errors gracefully."""
        bot, mock_blockchain = integrated_bot

        # Mock blockchain to raise connection error
        mock_blockchain.get_latest_transactions.side_effect = BlockchainConnectionError(
            "Connection failed"
        )

        bot.start()

        # Should not raise exception
        bot.process_once()

        # Verify stats unchanged
        stats = bot.get_statistics()
        assert stats["transactions_processed"] == 0
        assert stats["trades_detected"] == 0

    def test_statistics_reset(self, integrated_bot, mock_kuru_api):
        """Should reset statistics correctly."""
        bot, mock_blockchain = integrated_bot

        # Process a trade
        tx = {
            "hash": "0x" + "f" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1003,
            "logs": [{"topics": ["0x" + "g" * 64], "data": "0x" + "0" * 512}],
        }

        mock_blockchain.get_latest_transactions.return_value = [tx]

        with patch.object(bot.detector, 'parse_trade_executed') as mock_parse:
            trade = Trade(
                id="trade_reset",
                trader_address="0x1111111111111111111111111111111111111111",
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("1.0"),
                timestamp=datetime.now(timezone.utc),
                tx_hash=tx["hash"],
            )
            mock_parse.return_value = trade

            bot.start()
            bot.process_once()

            # Verify stats before reset
            stats_before = bot.get_statistics()
            assert stats_before["transactions_processed"] > 0

            # Reset
            bot.reset_statistics()

            # Verify stats after reset
            stats_after = bot.get_statistics()
            assert stats_after["transactions_processed"] == 0
            assert stats_after["trades_detected"] == 0
            assert stats_after["successful_trades"] == 0

    def test_continuous_monitoring_cycle(self, integrated_bot, mock_kuru_api):
        """Should handle continuous monitoring cycles."""
        bot, mock_blockchain = integrated_bot

        # First cycle: no transactions
        mock_blockchain.get_latest_transactions.return_value = []

        bot.start()
        bot.process_once()

        stats1 = bot.get_statistics()
        assert stats1["transactions_processed"] == 0

        # Second cycle: one transaction with trade
        tx = {
            "hash": "0x" + "h" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1004,
            "logs": [{"topics": ["0x" + "i" * 64], "data": "0x" + "0" * 512}],
        }

        mock_blockchain.get_latest_transactions.return_value = [tx]

        with patch.object(bot.detector, 'parse_trade_executed') as mock_parse:
            trade = Trade(
                id="trade_continuous",
                trader_address="0x1111111111111111111111111111111111111111",
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("1.0"),
                timestamp=datetime.now(timezone.utc),
                tx_hash=tx["hash"],
            )
            mock_parse.return_value = trade

            bot.process_once()

            stats2 = bot.get_statistics()
            assert stats2["transactions_processed"] == 1
            assert stats2["trades_detected"] == 1

        # Third cycle: no new transactions
        mock_blockchain.get_latest_transactions.return_value = []
        bot.process_once()

        stats3 = bot.get_statistics()
        assert stats3["transactions_processed"] == 1  # Still 1
        assert stats3["trades_detected"] == 1  # Still 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_handles_detector_parse_errors(self, integrated_bot):
        """Should handle detector parse errors gracefully."""
        bot, mock_blockchain = integrated_bot

        tx = {
            "hash": "0x" + "j" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1005,
            "logs": [{"topics": ["0x" + "k" * 64], "data": "0x" + "0" * 512}],
        }

        mock_blockchain.get_latest_transactions.return_value = [tx]

        # Mock detector to raise exception
        with patch.object(bot.detector, 'parse_trade_executed') as mock_parse:
            mock_parse.side_effect = Exception("Parse error")

            bot.start()
            bot.process_once()

            # Should handle error gracefully
            stats = bot.get_statistics()
            assert stats["transactions_processed"] == 1
            assert stats["trades_detected"] == 0

    def test_handles_copier_execution_errors(self, integrated_bot):
        """Should handle copier execution errors gracefully."""
        bot, mock_blockchain = integrated_bot

        tx = {
            "hash": "0x" + "l" * 64,
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x4444444444444444444444444444444444444444",
            "blockNumber": 1006,
            "logs": [{"topics": ["0x" + "m" * 64], "data": "0x" + "0" * 512}],
        }

        mock_blockchain.get_latest_transactions.return_value = [tx]

        with patch.object(bot.detector, 'parse_trade_executed') as mock_parse, \
             patch.object(bot.copier, 'process_trade') as mock_copier:

            trade = Trade(
                id="trade_error",
                trader_address="0x1111111111111111111111111111111111111111",
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("1.0"),
                timestamp=datetime.now(timezone.utc),
                tx_hash=tx["hash"],
            )
            mock_parse.return_value = trade
            mock_copier.side_effect = Exception("Execution error")

            bot.start()
            bot.process_once()

            # Should handle error gracefully
            stats = bot.get_statistics()
            assert stats["transactions_processed"] == 1
            assert stats["trades_detected"] == 1

    def test_empty_transaction_batch(self, integrated_bot):
        """Should handle empty transaction batches."""
        bot, mock_blockchain = integrated_bot

        mock_blockchain.get_latest_transactions.return_value = []

        bot.start()
        bot.process_once()

        # Should complete without errors
        stats = bot.get_statistics()
        assert stats["transactions_processed"] == 0
        assert stats["trades_detected"] == 0
