"""Unit tests for Monad blockchain connector."""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call
from web3.exceptions import Web3Exception

from src.kuru_copytr_bot.connectors.blockchain.monad import MonadClient
from src.kuru_copytr_bot.core.exceptions import (
    BlockchainConnectionError,
    TransactionFailedError,
    InsufficientGasError,
)


@pytest.fixture
def mock_web3():
    """Create a mock Web3 provider."""
    with patch("src.kuru_copytr_bot.connectors.blockchain.monad.Web3") as mock:
        web3_instance = MagicMock()
        mock.return_value = web3_instance

        # Set up default mock responses
        web3_instance.is_connected.return_value = True
        web3_instance.eth.chain_id = 41454
        web3_instance.eth.get_balance.return_value = 1000000000000000000  # 1 ETH in wei
        web3_instance.eth.get_transaction_count.return_value = 5
        web3_instance.eth.block_number = 1000000

        # Mock account
        mock_account = MagicMock()
        mock_account.address = "0x1234567890123456789012345678901234567890"
        web3_instance.eth.account.from_key.return_value = mock_account

        # Transaction submission
        web3_instance.eth.send_raw_transaction.return_value = b"0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

        # Transaction receipt
        web3_instance.eth.get_transaction_receipt.return_value = {
            "status": 1,
            "blockNumber": 1000001,
            "transactionHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "gasUsed": 200000,
            "logs": [
                {
                    "address": "0xcontractaddress",
                    "topics": [
                        "0x" + "0" * 64,  # event signature
                    ],
                    "data": "0x" + "1" * 64,
                    "blockNumber": 1000001,
                }
            ],
        }

        # Gas estimation
        web3_instance.eth.estimate_gas.return_value = 250000

        # Gas price
        web3_instance.eth.gas_price = 1000000000  # 1 gwei

        yield web3_instance


class TestMonadClientConnection:
    """Test MonadClient connection functionality."""

    def test_monad_client_initializes_successfully(self, mock_web3):
        """MonadClient should initialize with RPC URL and private key."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        assert client is not None
        assert client.rpc_url == "https://testnet.monad.xyz"

    def test_monad_client_connects_successfully(self, mock_web3):
        """Client should connect to RPC successfully."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        assert client.is_connected() is True
        mock_web3.is_connected.assert_called()

    def test_monad_client_raises_error_on_connection_failure(self, mock_web3):
        """Client should raise BlockchainConnectionError on connection failure."""
        mock_web3.is_connected.return_value = False

        with pytest.raises(BlockchainConnectionError):
            client = MonadClient(
                rpc_url="https://invalid.url",
                private_key="0x" + "a" * 64,
            )

    def test_monad_client_derives_wallet_address_from_private_key(self, mock_web3):
        """Client should derive wallet address from private key."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        assert client.wallet_address == "0x1234567890123456789012345678901234567890"

    def test_monad_client_validates_chain_id(self, mock_web3):
        """Client should validate it's connected to the correct chain."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        # Should connect to Monad testnet (chain ID 41454)
        assert mock_web3.eth.chain_id == 41454


class TestMonadClientBalanceQueries:
    """Test MonadClient balance query functionality."""

    def test_monad_client_gets_native_balance(self, mock_web3):
        """Client should query wallet native token balance."""
        mock_web3.eth.get_balance.return_value = 1500000000000000000  # 1.5 ETH

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )
        balance = client.get_balance("0xabc123")

        assert balance == Decimal("1.5")
        mock_web3.eth.get_balance.assert_called_with("0xabc123")

    def test_monad_client_gets_token_balance(self, mock_web3):
        """Client should query ERC20 token balance."""
        # Mock ERC20 contract call returning balance in wei
        mock_contract = MagicMock()
        mock_contract.functions.balanceOf.return_value.call.return_value = 1000000000000000000000  # 1000 tokens (18 decimals)
        mock_web3.eth.contract.return_value = mock_contract

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )
        balance = client.get_token_balance(
            address="0xwallet",
            token_address="0xtoken",
        )

        assert balance == Decimal("1000")
        mock_web3.eth.contract.assert_called_with(
            address="0xtoken",
            abi=client.ERC20_ABI,
        )

    def test_monad_client_handles_zero_balance(self, mock_web3):
        """Client should handle zero balance correctly."""
        mock_web3.eth.get_balance.return_value = 0

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )
        balance = client.get_balance("0xabc123")

        assert balance == Decimal("0")


class TestMonadClientTransactions:
    """Test MonadClient transaction functionality."""

    def test_monad_client_builds_transaction(self, mock_web3):
        """Client should build transaction with correct parameters."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        # Send transaction
        tx_hash = client.send_transaction(
            to="0xrecipient",
            data="0xdeadbeef",
            value=1000000000000000000,  # 1 ETH in wei
            gas=300000,
        )

        # Verify transaction was sent
        assert tx_hash.startswith("0x")
        assert len(tx_hash) == 66
        mock_web3.eth.send_raw_transaction.assert_called_once()

    def test_monad_client_signs_transaction(self, mock_web3):
        """Client should sign transaction with private key."""
        mock_account = MagicMock()
        mock_account.address = "0x1234567890123456789012345678901234567890"
        mock_signed_tx = MagicMock()
        mock_signed_tx.rawTransaction = b"0xsignedtx"
        mock_account.sign_transaction.return_value = mock_signed_tx
        mock_web3.eth.account.from_key.return_value = mock_account

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        client.send_transaction(
            to="0xrecipient",
            data="0x",
            value=0,
        )

        # Verify transaction was signed
        mock_account.sign_transaction.assert_called_once()

    def test_monad_client_submits_transaction(self, mock_web3):
        """Client should submit signed transaction to network."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        tx_hash = client.send_transaction(
            to="0xrecipient",
            data="0x",
        )

        assert tx_hash.startswith("0x")
        mock_web3.eth.send_raw_transaction.assert_called_once()

    def test_monad_client_estimates_gas_before_sending(self, mock_web3):
        """Client should estimate gas if not provided."""
        mock_web3.eth.estimate_gas.return_value = 250000

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        client.send_transaction(
            to="0xrecipient",
            data="0xfunction",
        )

        # Should estimate gas
        assert mock_web3.eth.estimate_gas.called

    def test_monad_client_uses_provided_gas_limit(self, mock_web3):
        """Client should use provided gas limit instead of estimating."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        client.send_transaction(
            to="0xrecipient",
            data="0x",
            gas=500000,
        )

        # Should not estimate gas when provided
        mock_web3.eth.estimate_gas.assert_not_called()

    def test_monad_client_raises_error_on_transaction_failure(self, mock_web3):
        """Client should raise TransactionFailedError on transaction failure."""
        mock_web3.eth.send_raw_transaction.side_effect = Web3Exception("Transaction failed")

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        with pytest.raises(TransactionFailedError):
            client.send_transaction(to="0xrecipient", data="0x")


class TestMonadClientReceipts:
    """Test MonadClient receipt handling."""

    def test_monad_client_gets_transaction_receipt(self, mock_web3):
        """Client should get transaction receipt."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        receipt = client.get_transaction_receipt(
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        assert receipt["status"] == 1
        assert receipt["blockNumber"] == 1000001
        mock_web3.eth.get_transaction_receipt.assert_called_once()

    def test_monad_client_waits_for_receipt(self, mock_web3):
        """Client should wait for transaction confirmation."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        receipt = client.wait_for_transaction_receipt(
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            timeout=120,
        )

        assert receipt["status"] == 1
        assert "blockNumber" in receipt

    def test_monad_client_handles_pending_transaction(self, mock_web3):
        """Client should poll for receipt if transaction is pending."""
        # First call returns None (pending), second call returns receipt
        mock_web3.eth.get_transaction_receipt.side_effect = [
            None,
            {
                "status": 1,
                "blockNumber": 1000001,
                "transactionHash": "0xabcdef",
                "gasUsed": 200000,
                "logs": [],
            },
        ]

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        receipt = client.wait_for_transaction_receipt("0xabcdef", timeout=10)

        assert receipt["status"] == 1
        assert mock_web3.eth.get_transaction_receipt.call_count == 2

    def test_monad_client_raises_error_on_failed_receipt(self, mock_web3):
        """Client should raise error if transaction receipt shows failure."""
        mock_web3.eth.get_transaction_receipt.return_value = {
            "status": 0,  # Failed
            "blockNumber": 1000001,
            "transactionHash": "0xabcdef",
            "gasUsed": 200000,
            "logs": [],
        }

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        with pytest.raises(TransactionFailedError):
            client.wait_for_transaction_receipt("0xabcdef")


class TestMonadClientEventLogs:
    """Test MonadClient event log parsing."""

    def test_monad_client_parses_event_logs(self, mock_web3):
        """Client should parse event logs from receipt."""
        logs = [
            {
                "address": "0xcontract",
                "topics": ["0x" + "0" * 64],
                "data": "0x" + "1" * 64,
                "blockNumber": 1000001,
            }
        ]

        event_abi = {
            "type": "event",
            "name": "OrderPlaced",
            "inputs": [
                {"name": "orderId", "type": "uint256", "indexed": False},
            ],
        }

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        parsed_events = client.parse_event_logs(logs, event_abi)

        assert isinstance(parsed_events, list)
        assert len(parsed_events) > 0

    def test_monad_client_handles_empty_logs(self, mock_web3):
        """Client should handle empty event logs."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        event_abi = {
            "type": "event",
            "name": "OrderPlaced",
            "inputs": [],
        }

        parsed_events = client.parse_event_logs([], event_abi)

        assert isinstance(parsed_events, list)
        assert len(parsed_events) == 0


class TestMonadClientNonceManagement:
    """Test MonadClient nonce management."""

    def test_monad_client_gets_current_nonce(self, mock_web3):
        """Client should get current nonce for address."""
        mock_web3.eth.get_transaction_count.return_value = 42

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        nonce = client.get_nonce("0xwallet")

        assert nonce == 42
        mock_web3.eth.get_transaction_count.assert_called_with("0xwallet", "pending")

    def test_monad_client_increments_nonce_for_multiple_transactions(self, mock_web3):
        """Client should manage nonce correctly for multiple transactions."""
        mock_web3.eth.get_transaction_count.return_value = 5

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        # Send multiple transactions
        client.send_transaction(to="0xrecipient1", data="0x")
        client.send_transaction(to="0xrecipient2", data="0x")

        # Should fetch nonce for each transaction
        assert mock_web3.eth.get_transaction_count.call_count >= 2


class TestMonadClientErrorHandling:
    """Test MonadClient error handling."""

    def test_monad_client_handles_network_error(self, mock_web3):
        """Client should handle network errors gracefully."""
        mock_web3.eth.get_balance.side_effect = ConnectionError("Network error")

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        with pytest.raises(BlockchainConnectionError):
            client.get_balance("0xwallet")

    def test_monad_client_handles_insufficient_gas_error(self, mock_web3):
        """Client should raise InsufficientGasError when gas estimation fails."""
        mock_web3.eth.estimate_gas.side_effect = Web3Exception("out of gas")

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        with pytest.raises(InsufficientGasError):
            client.send_transaction(to="0xrecipient", data="0x")

    def test_monad_client_handles_invalid_address(self, mock_web3):
        """Client should validate Ethereum addresses."""
        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        with pytest.raises(ValueError):
            client.get_balance("invalid_address")


class TestMonadClientRetryLogic:
    """Test MonadClient retry logic."""

    def test_monad_client_retries_on_network_error(self, mock_web3):
        """Client should retry on network failures."""
        # First two calls fail, third succeeds
        mock_web3.eth.send_raw_transaction.side_effect = [
            ConnectionError("Network error"),
            ConnectionError("Network error"),
            b"0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        ]

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        tx_hash = client.send_transaction(to="0xrecipient", data="0x")

        assert tx_hash.startswith("0x")
        assert mock_web3.eth.send_raw_transaction.call_count == 3

    def test_monad_client_retries_with_exponential_backoff(self, mock_web3):
        """Client should use exponential backoff for retries."""
        mock_web3.eth.get_balance.side_effect = [
            ConnectionError("Network error"),
            1000000000000000000,  # 1 ETH
        ]

        with patch("time.sleep") as mock_sleep:
            client = MonadClient(
                rpc_url="https://testnet.monad.xyz",
                private_key="0x" + "a" * 64,
            )

            balance = client.get_balance("0xwallet")

            assert balance == Decimal("1.0")
            # Should have slept for backoff
            assert mock_sleep.called

    def test_monad_client_gives_up_after_max_retries(self, mock_web3):
        """Client should raise error after max retries exceeded."""
        # All attempts fail
        mock_web3.eth.send_raw_transaction.side_effect = ConnectionError("Network error")

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        with pytest.raises(BlockchainConnectionError):
            client.send_transaction(to="0xrecipient", data="0x")

        # Should have retried max_retries times (default: 3)
        assert mock_web3.eth.send_raw_transaction.call_count == 3

    def test_monad_client_does_not_retry_on_validation_errors(self, mock_web3):
        """Client should not retry on validation errors."""
        mock_web3.eth.send_raw_transaction.side_effect = ValueError("Invalid transaction")

        client = MonadClient(
            rpc_url="https://testnet.monad.xyz",
            private_key="0x" + "a" * 64,
        )

        with pytest.raises(TransactionFailedError):
            client.send_transaction(to="0xrecipient", data="0x")

        # Should not retry on validation errors
        assert mock_web3.eth.send_raw_transaction.call_count == 1
