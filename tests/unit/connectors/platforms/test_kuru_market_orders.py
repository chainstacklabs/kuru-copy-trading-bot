"""Unit tests for KuruClient market order functionality."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient
from src.kuru_copytr_bot.core.enums import OrderSide
from src.kuru_copytr_bot.core.exceptions import InvalidMarketError, OrderExecutionError


@pytest.fixture
def mock_blockchain():
    """Create a mock blockchain connector."""
    blockchain = MagicMock()
    blockchain.is_connected.return_value = True
    blockchain.wallet_address = "0x1234567890123456789012345678901234567890"
    blockchain.send_transaction.return_value = "0xabcdef"
    blockchain.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 1000,
        "logs": [],
    }
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
            client = KuruClient(
                blockchain=mock_blockchain,
                api_url="https://testnet-api.kuru.io",
                contract_address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            )
            client._market_cache = {
                "MON-USDC": MagicMock(
                    price_precision=1000000,
                    size_precision=100000,
                    base_asset="0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                    base_asset_decimals=18,
                    quote_asset="0xcccccccccccccccccccccccccccccccccccccccc",
                    quote_asset_decimals=6,
                    tick_size=Decimal("0.01"),
                    min_size=Decimal("0.001"),
                    max_size=Decimal("1000"),
                )
            }
            mock_function = MagicMock()
            mock_function.build_transaction.return_value = {"data": "0xabcdef"}
            client.orderbook_contract.functions.placeAndExecuteMarketBuy = MagicMock(return_value=mock_function)
            client.orderbook_contract.functions.placeAndExecuteMarketSell = MagicMock(return_value=mock_function)
            return client


class TestMarketOrderNoBalanceCheck:
    """Test that market orders don't check balance (done in TradeCopier)."""

    def test_place_market_buy_no_balance_check(self, kuru_client, mock_blockchain):
        """Test market BUY order does not check balance."""
        kuru_client.place_market_order(market="MON-USDC", side=OrderSide.BUY, size=Decimal("1.0"))

        mock_blockchain.get_token_balance.assert_not_called()
        mock_blockchain.get_balance.assert_not_called()
        mock_blockchain.send_transaction.assert_called_once()

    def test_place_market_sell_no_balance_check(self, kuru_client, mock_blockchain):
        """Test market SELL order does not check balance."""
        kuru_client.place_market_order(market="MON-USDC", side=OrderSide.SELL, size=Decimal("1.0"))

        mock_blockchain.get_token_balance.assert_not_called()
        mock_blockchain.get_balance.assert_not_called()
        mock_blockchain.send_transaction.assert_called_once()

    def test_place_market_order_insufficient_balance(self, kuru_client, mock_blockchain):
        """Test market order does not raise InsufficientBalanceError."""
        kuru_client.place_market_order(market="MON-USDC", side=OrderSide.BUY, size=Decimal("1.0"))

        mock_blockchain.send_transaction.assert_called_once()

    def test_place_market_order_invalid_market(self, kuru_client, mock_blockchain):
        """Test handling of market without params."""
        with pytest.raises(InvalidMarketError):
            kuru_client.place_market_order(market="INVALID-MARKET", side=OrderSide.BUY, size=Decimal("1.0"))

    def test_place_market_order_validates_size(self, kuru_client):
        """Test market order validates size."""
        with pytest.raises(ValueError) as exc_info:
            kuru_client.place_market_order(market="MON-USDC", side=OrderSide.BUY, size=Decimal("0"))

        assert "Size must be positive" in str(exc_info.value)
