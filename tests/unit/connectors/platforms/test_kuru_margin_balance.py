"""Unit tests for KuruClient margin balance functionality."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient
from src.kuru_copytr_bot.core.exceptions import BlockchainConnectionError


@pytest.fixture
def mock_blockchain():
    """Create a mock blockchain connector."""
    blockchain = MagicMock()
    blockchain.is_connected.return_value = True
    blockchain.wallet_address = "0x1234567890123456789012345678901234567890"
    return blockchain


@pytest.fixture
def kuru_client(mock_blockchain):
    """Create a KuruClient instance for testing."""
    with patch("src.kuru_copytr_bot.connectors.platforms.kuru.Path"):
        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value="[]")))
                )
            ),
        ):
            return KuruClient(
                blockchain=mock_blockchain,
                api_url="https://testnet-api.kuru.io",
                contract_address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            )


class TestGetMarginBalance:
    """Test get_margin_balance method."""

    def test_get_margin_balance_native_token(self, kuru_client, mock_blockchain):
        """Test fetching native token margin balance."""
        mock_blockchain.call_contract_function.return_value = 1000000000000000000

        balance = kuru_client.get_margin_balance(None)

        assert balance == Decimal("1.0")
        mock_blockchain.call_contract_function.assert_called_once()
        call_args = mock_blockchain.call_contract_function.call_args[1]
        assert call_args["function_name"] == "getBalance"
        assert call_args["args"][1] == "0x0000000000000000000000000000000000000000"

    def test_get_margin_balance_native_token_with_zero_address(self, kuru_client, mock_blockchain):
        """Test fetching native token margin balance with explicit zero address."""
        mock_blockchain.call_contract_function.return_value = 2500000000000000000

        balance = kuru_client.get_margin_balance("0x0000000000000000000000000000000000000000")

        assert balance == Decimal("2.5")
        mock_blockchain.call_contract_function.assert_called_once()

    def test_get_margin_balance_erc20_token(self, kuru_client, mock_blockchain):
        """Test fetching ERC20 token margin balance."""
        mock_blockchain.call_contract_function.return_value = 1000000000000000000

        balance = kuru_client.get_margin_balance("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

        assert balance == Decimal("1.0")
        mock_blockchain.call_contract_function.assert_called_once()
        call_args = mock_blockchain.call_contract_function.call_args[1]
        assert call_args["function_name"] == "getBalance"
        assert call_args["args"][1] == "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    def test_get_margin_balance_with_6_decimals(self, kuru_client, mock_blockchain):
        """Test fetching USDC-like token with 6 decimals."""
        mock_blockchain.call_contract_function.return_value = 1000000

        balance = kuru_client.get_margin_balance("0xcccccccccccccccccccccccccccccccccccccccc", decimals=6)

        assert balance == Decimal("1.0")
        mock_blockchain.call_contract_function.assert_called_once()

    def test_get_margin_balance_zero_balance(self, kuru_client, mock_blockchain):
        """Test handling zero balance."""
        mock_blockchain.call_contract_function.return_value = 0

        balance = kuru_client.get_margin_balance(None)

        assert balance == Decimal("0")
        mock_blockchain.call_contract_function.assert_called_once()

    def test_get_margin_balance_invalid_token(self, kuru_client):
        """Test invalid token address handling."""
        with pytest.raises(ValueError) as exc_info:
            kuru_client.get_margin_balance("invalid_address")

        assert "Invalid token address" in str(exc_info.value)

    def test_get_margin_balance_connection_error(self, kuru_client, mock_blockchain):
        """Test handling connection errors."""
        mock_blockchain.call_contract_function.side_effect = BlockchainConnectionError("Network error")

        with pytest.raises(BlockchainConnectionError):
            kuru_client.get_margin_balance(None)

    def test_get_margin_balance_large_balance(self, kuru_client, mock_blockchain):
        """Test handling large balance values."""
        mock_blockchain.call_contract_function.return_value = 1234567890123456789012345

        balance = kuru_client.get_margin_balance(None)

        assert balance == Decimal("1234567.890123456789012345")
        mock_blockchain.call_contract_function.assert_called_once()

    def test_get_margin_balance_uses_wallet_address(self, kuru_client, mock_blockchain):
        """Test that get_margin_balance uses the correct wallet address."""
        mock_blockchain.call_contract_function.return_value = 1000000000000000000

        kuru_client.get_margin_balance(None)

        call_args = mock_blockchain.call_contract_function.call_args[1]
        assert call_args["args"][0] == mock_blockchain.wallet_address
