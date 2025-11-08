"""Unit tests for wallet monitor."""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone

from src.kuru_copytr_bot.monitoring.monitor import WalletMonitor


@pytest.fixture
def mock_blockchain():
    """Create a mock blockchain client."""
    blockchain = MagicMock()
    blockchain.get_latest_transactions.return_value = []
    return blockchain


@pytest.fixture
def kuru_contract_address():
    """Kuru contract address."""
    return "0x4444444444444444444444444444444444444444"


class TestWalletMonitorInitialization:
    """Test WalletMonitor initialization."""

    def test_monitor_initializes_with_target_wallets(self, mock_blockchain, kuru_contract_address):
        """Monitor should initialize with target wallet list."""
        target_wallets = [
            "0x1111111111111111111111111111111111111111",
            "0x2222222222222222222222222222222222222222",
        ]
        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=target_wallets,
            kuru_contract_address=kuru_contract_address,
        )

        assert monitor.target_wallets == target_wallets
        assert monitor.kuru_contract_address == kuru_contract_address

    def test_monitor_initializes_with_empty_processed_set(self, mock_blockchain, kuru_contract_address):
        """Monitor should start with empty processed transactions set."""
        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=["0x1111111111111111111111111111111111111111"],
            kuru_contract_address=kuru_contract_address,
        )

        assert len(monitor._processed_transactions) == 0


class TestWalletMonitorTransactionDetection:
    """Test transaction detection functionality."""

    def test_monitor_detects_wallet_transaction(self, mock_blockchain, kuru_contract_address):
        """Monitor should detect transactions from target wallets."""
        target_wallet = "0x1111111111111111111111111111111111111111"

        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xabc123",
                "from": target_wallet,
                "to": kuru_contract_address,
                "blockNumber": 1000,
            }
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[target_wallet],
            kuru_contract_address=kuru_contract_address,
        )

        transactions = monitor.get_new_transactions()
        assert len(transactions) == 1
        assert transactions[0]["hash"] == "0xabc123"

    def test_monitor_filters_by_target_wallets(self, mock_blockchain, kuru_contract_address):
        """Monitor should only return transactions from target wallets."""
        target_wallet = "0x1111111111111111111111111111111111111111"
        other_wallet = "0x9999999999999999999999999999999999999999"

        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xabc123",
                "from": target_wallet,
                "to": kuru_contract_address,
                "blockNumber": 1000,
            },
            {
                "hash": "0xdef456",
                "from": other_wallet,  # Not in target list
                "to": kuru_contract_address,
                "blockNumber": 1001,
            },
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[target_wallet],
            kuru_contract_address=kuru_contract_address,
        )

        transactions = monitor.get_new_transactions()
        assert len(transactions) == 1
        assert transactions[0]["from"] == target_wallet

    def test_monitor_filters_by_kuru_contract(self, mock_blockchain, kuru_contract_address):
        """Monitor should only return transactions to Kuru contract."""
        target_wallet = "0x1111111111111111111111111111111111111111"
        other_contract = "0x8888888888888888888888888888888888888888"

        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xabc123",
                "from": target_wallet,
                "to": kuru_contract_address,  # To Kuru
                "blockNumber": 1000,
            },
            {
                "hash": "0xdef456",
                "from": target_wallet,
                "to": other_contract,  # To different contract
                "blockNumber": 1001,
            },
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[target_wallet],
            kuru_contract_address=kuru_contract_address,
        )

        transactions = monitor.get_new_transactions()
        assert len(transactions) == 1
        assert transactions[0]["to"] == kuru_contract_address

    def test_monitor_handles_no_transactions(self, mock_blockchain, kuru_contract_address):
        """Monitor should handle case with no new transactions."""
        mock_blockchain.get_latest_transactions.return_value = []

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=["0x1111111111111111111111111111111111111111"],
            kuru_contract_address=kuru_contract_address,
        )

        transactions = monitor.get_new_transactions()
        assert len(transactions) == 0


class TestWalletMonitorDuplicatePrevention:
    """Test duplicate transaction prevention."""

    def test_monitor_tracks_processed_transactions(self, mock_blockchain, kuru_contract_address):
        """Monitor should track processed transaction hashes."""
        target_wallet = "0x1111111111111111111111111111111111111111"

        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xabc123",
                "from": target_wallet,
                "to": kuru_contract_address,
                "blockNumber": 1000,
            }
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[target_wallet],
            kuru_contract_address=kuru_contract_address,
        )

        # First call should return transaction
        transactions = monitor.get_new_transactions()
        assert len(transactions) == 1

        # Second call with same transaction should return empty
        transactions = monitor.get_new_transactions()
        assert len(transactions) == 0

    def test_monitor_prevents_duplicate_processing(self, mock_blockchain, kuru_contract_address):
        """Monitor should not return already processed transactions."""
        target_wallet = "0x1111111111111111111111111111111111111111"

        transaction = {
            "hash": "0xabc123",
            "from": target_wallet,
            "to": kuru_contract_address,
            "blockNumber": 1000,
        }

        mock_blockchain.get_latest_transactions.return_value = [transaction]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[target_wallet],
            kuru_contract_address=kuru_contract_address,
        )

        # Process transaction first time
        monitor.get_new_transactions()

        # Try to process same transaction again
        mock_blockchain.get_latest_transactions.return_value = [transaction]
        transactions = monitor.get_new_transactions()

        assert len(transactions) == 0

    def test_monitor_processes_new_transactions_after_duplicates(self, mock_blockchain, kuru_contract_address):
        """Monitor should process new transactions even after seeing duplicates."""
        target_wallet = "0x1111111111111111111111111111111111111111"

        # First transaction
        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xabc123",
                "from": target_wallet,
                "to": kuru_contract_address,
                "blockNumber": 1000,
            }
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[target_wallet],
            kuru_contract_address=kuru_contract_address,
        )

        transactions = monitor.get_new_transactions()
        assert len(transactions) == 1

        # Second, different transaction
        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xdef456",  # New hash
                "from": target_wallet,
                "to": kuru_contract_address,
                "blockNumber": 1001,
            }
        ]

        transactions = monitor.get_new_transactions()
        assert len(transactions) == 1
        assert transactions[0]["hash"] == "0xdef456"


class TestWalletMonitorMultipleWallets:
    """Test monitoring multiple wallets simultaneously."""

    def test_monitor_handles_multiple_target_wallets(self, mock_blockchain, kuru_contract_address):
        """Monitor should detect transactions from all target wallets."""
        wallet1 = "0x1111111111111111111111111111111111111111"
        wallet2 = "0x2222222222222222222222222222222222222222"

        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xabc123",
                "from": wallet1,
                "to": kuru_contract_address,
                "blockNumber": 1000,
            },
            {
                "hash": "0xdef456",
                "from": wallet2,
                "to": kuru_contract_address,
                "blockNumber": 1001,
            },
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[wallet1, wallet2],
            kuru_contract_address=kuru_contract_address,
        )

        transactions = monitor.get_new_transactions()
        assert len(transactions) == 2

    def test_monitor_distinguishes_between_wallets(self, mock_blockchain, kuru_contract_address):
        """Monitor should correctly identify which wallet sent transaction."""
        wallet1 = "0x1111111111111111111111111111111111111111"
        wallet2 = "0x2222222222222222222222222222222222222222"

        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xabc123",
                "from": wallet1,
                "to": kuru_contract_address,
                "blockNumber": 1000,
            },
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[wallet1, wallet2],
            kuru_contract_address=kuru_contract_address,
        )

        transactions = monitor.get_new_transactions()
        assert len(transactions) == 1
        assert transactions[0]["from"] == wallet1


class TestWalletMonitorBlockTracking:
    """Test block number tracking."""

    def test_monitor_tracks_last_processed_block(self, mock_blockchain, kuru_contract_address):
        """Monitor should track the last processed block number."""
        target_wallet = "0x1111111111111111111111111111111111111111"

        mock_blockchain.get_latest_transactions.return_value = [
            {
                "hash": "0xabc123",
                "from": target_wallet,
                "to": kuru_contract_address,
                "blockNumber": 1000,
            }
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[target_wallet],
            kuru_contract_address=kuru_contract_address,
            from_block=900,
        )

        monitor.get_new_transactions()
        assert monitor.last_processed_block == 1000

    def test_monitor_starts_from_specified_block(self, mock_blockchain, kuru_contract_address):
        """Monitor should initialize with specified starting block."""
        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=["0x1111111111111111111111111111111111111111"],
            kuru_contract_address=kuru_contract_address,
            from_block=5000,
        )

        # Verify from_block is stored as last_processed_block
        assert monitor.last_processed_block == 5000


class TestWalletMonitorErrorHandling:
    """Test error handling in monitor."""

    def test_monitor_handles_blockchain_connection_error(self, mock_blockchain, kuru_contract_address):
        """Monitor should handle blockchain connection errors gracefully."""
        from src.kuru_copytr_bot.core.exceptions import BlockchainConnectionError

        mock_blockchain.get_latest_transactions.side_effect = BlockchainConnectionError("Network error")

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=["0x1111111111111111111111111111111111111111"],
            kuru_contract_address=kuru_contract_address,
        )

        # Should handle error and return empty list
        transactions = monitor.get_new_transactions()
        assert len(transactions) == 0

    def test_monitor_handles_malformed_transaction(self, mock_blockchain, kuru_contract_address):
        """Monitor should handle malformed transaction data."""
        target_wallet = "0x1111111111111111111111111111111111111111"

        mock_blockchain.get_latest_transactions.return_value = [
            {
                # Missing required fields
                "hash": "0xabc123",
            },
            {
                "hash": "0xdef456",
                "from": target_wallet,
                "to": kuru_contract_address,
                "blockNumber": 1000,
            },
        ]

        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=[target_wallet],
            kuru_contract_address=kuru_contract_address,
        )

        # Should skip malformed transaction and return valid one
        transactions = monitor.get_new_transactions()
        assert len(transactions) == 1
        assert transactions[0]["hash"] == "0xdef456"


class TestWalletMonitorStartStop:
    """Test start and stop functionality."""

    def test_monitor_start_sets_running_flag(self, mock_blockchain, kuru_contract_address):
        """Monitor start should set running flag."""
        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=["0x1111111111111111111111111111111111111111"],
            kuru_contract_address=kuru_contract_address,
        )

        monitor.start()
        assert monitor.is_running is True

    def test_monitor_stop_clears_running_flag(self, mock_blockchain, kuru_contract_address):
        """Monitor stop should clear running flag."""
        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=["0x1111111111111111111111111111111111111111"],
            kuru_contract_address=kuru_contract_address,
        )

        monitor.start()
        monitor.stop()
        assert monitor.is_running is False

    def test_monitor_can_restart_after_stop(self, mock_blockchain, kuru_contract_address):
        """Monitor should be able to restart after stopping."""
        monitor = WalletMonitor(
            blockchain=mock_blockchain,
            target_wallets=["0x1111111111111111111111111111111111111111"],
            kuru_contract_address=kuru_contract_address,
        )

        monitor.start()
        monitor.stop()
        monitor.start()

        assert monitor.is_running is True
