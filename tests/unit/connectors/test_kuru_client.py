"""Unit tests for Kuru Exchange client."""

import pytest
import requests
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient
from src.kuru_copytr_bot.core.enums import OrderSide, OrderType
from src.kuru_copytr_bot.core.exceptions import (
    InsufficientBalanceError,
    InvalidMarketError,
    OrderExecutionError,
    BlockchainConnectionError,
)


@pytest.fixture
def mock_blockchain():
    """Create a mock blockchain client."""
    blockchain = MagicMock()
    blockchain.wallet_address = "0x1234567890123456789012345678901234567890"
    blockchain.send_transaction.return_value = "0x" + "a" * 64  # 66 chars total
    blockchain.get_balance.return_value = Decimal("100.0")
    blockchain.get_token_balance.return_value = Decimal("10000.0")  # USDC balance
    blockchain.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 1000000,
        "transactionHash": "0x" + "b" * 64,  # 66 chars total
        "logs": [],
    }
    return blockchain


@pytest.fixture
def kuru_client(mock_blockchain):
    """Create KuruClient with mocked blockchain."""
    return KuruClient(
        blockchain=mock_blockchain,
        api_url="https://api.kuru.io",
        contract_address="0x4444444444444444444444444444444444444444",
    )


class TestKuruClientInitialization:
    """Test KuruClient initialization."""

    def test_kuru_client_initializes_successfully(self, mock_blockchain):
        """KuruClient should initialize with blockchain and API URL."""
        client = KuruClient(
            blockchain=mock_blockchain,
            api_url="https://api.kuru.io",
            contract_address="0x4444444444444444444444444444444444444444",
        )

        assert client is not None
        assert client.blockchain == mock_blockchain
        assert client.api_url == "https://api.kuru.io"
        assert client.contract_address == "0x4444444444444444444444444444444444444444"

    def test_kuru_client_validates_contract_address(self, mock_blockchain):
        """KuruClient should validate contract address format."""
        with pytest.raises(ValueError):
            KuruClient(
                blockchain=mock_blockchain,
                api_url="https://api.kuru.io",
                contract_address="invalid_address",
            )


class TestKuruClientMarginDeposit:
    """Test Kuru margin deposit functionality."""

    def test_kuru_client_deposits_margin(self, kuru_client, mock_blockchain):
        """Client should deposit margin to Kuru contract."""
        # Use valid USDC testnet address
        usdc_address = "0x9A29e9Bab1f0B599d1c6C39b60a79596b3875f56"
        tx_hash = kuru_client.deposit_margin(
            token=usdc_address,
            amount=Decimal("100.0"),
        )

        assert tx_hash.startswith("0x")
        assert len(tx_hash) == 66
        # ERC20 deposits require 2 transactions: approve + deposit
        assert mock_blockchain.send_transaction.call_count == 2

        # Verify approve transaction was sent to token contract
        first_call = mock_blockchain.send_transaction.call_args_list[0]
        assert first_call[1]["to"] == usdc_address
        assert first_call[1]["data"] != "0x"  # Should have encoded data

        # Verify deposit transaction was sent to margin account
        second_call = mock_blockchain.send_transaction.call_args_list[1]
        assert second_call[1]["to"] == kuru_client.margin_account_address
        assert second_call[1]["data"] != "0x"  # Should have encoded data

    def test_kuru_client_deposits_native_token(self, kuru_client, mock_blockchain):
        """Client should deposit native token (ETH/MON) to margin."""
        tx_hash = kuru_client.deposit_margin(
            token="0x0000000000000000000000000000000000000000",  # Native token
            amount=Decimal("1.0"),
        )

        assert tx_hash.startswith("0x")
        # Should send only one transaction (no approve needed for native)
        assert mock_blockchain.send_transaction.call_count == 1

        # Should send transaction with value
        call_args = mock_blockchain.send_transaction.call_args
        assert call_args[1]["value"] > 0
        assert call_args[1]["to"] == kuru_client.margin_account_address
        assert call_args[1]["data"] != "0x"  # Should have encoded deposit data

    def test_kuru_client_checks_balance_before_deposit(self, kuru_client, mock_blockchain):
        """Client should check balance before deposit."""
        mock_blockchain.get_token_balance.return_value = Decimal("50.0")

        usdc_address = "0x9A29e9Bab1f0B599d1c6C39b60a79596b3875f56"
        with pytest.raises(InsufficientBalanceError):
            kuru_client.deposit_margin(
                token=usdc_address,
                amount=Decimal("100.0"),
            )

    def test_kuru_client_approves_erc20_before_deposit(self, kuru_client, mock_blockchain):
        """Client should approve ERC20 tokens before deposit."""
        usdc_address = "0x9A29e9Bab1f0B599d1c6C39b60a79596b3875f56"
        kuru_client.deposit_margin(
            token=usdc_address,
            amount=Decimal("100.0"),
        )

        # Should call send_transaction twice (approve + deposit)
        assert mock_blockchain.send_transaction.call_count == 2

        # First call should be approve to token contract
        first_call = mock_blockchain.send_transaction.call_args_list[0]
        assert first_call[1]["to"] == usdc_address

        # Second call should be deposit to margin account
        second_call = mock_blockchain.send_transaction.call_args_list[1]
        assert second_call[1]["to"] == kuru_client.margin_account_address


class TestKuruClientLimitOrders:
    """Test Kuru limit order placement."""

    def test_kuru_client_places_limit_order(self, kuru_client, mock_blockchain):
        """Client should place GTC limit order."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

            order_id = kuru_client.place_limit_order(
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("1.0"),
                post_only=True,
            )

            assert order_id is not None
            assert isinstance(order_id, str)
            mock_blockchain.send_transaction.assert_called_once()

    def test_kuru_client_places_sell_limit_order(self, kuru_client, mock_blockchain):
        """Client should place sell limit order."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

            order_id = kuru_client.place_limit_order(
                market="ETH-USDC",
                side=OrderSide.SELL,
                price=Decimal("2100.0"),
                size=Decimal("0.5"),
                post_only=False,
            )

            assert order_id is not None
            mock_blockchain.send_transaction.assert_called_once()

    def test_kuru_client_validates_limit_order_price(self, kuru_client, mock_blockchain):
        """Client should validate limit order price is positive."""
        with pytest.raises(ValueError):
            kuru_client.place_limit_order(
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("0"),
                size=Decimal("1.0"),
            )

    def test_kuru_client_validates_limit_order_size(self, kuru_client, mock_blockchain):
        """Client should validate limit order size is positive."""
        with pytest.raises(ValueError):
            kuru_client.place_limit_order(
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("0"),
            )

    def test_kuru_client_validates_market_exists(self, kuru_client, mock_blockchain):
        """Client should validate market exists."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.side_effect = InvalidMarketError("Market not found")

            with pytest.raises(InvalidMarketError):
                kuru_client.place_limit_order(
                    market="INVALID-MARKET",
                    side=OrderSide.BUY,
                    price=Decimal("2000.0"),
                    size=Decimal("1.0"),
                )

    def test_kuru_client_places_limit_order_async(self, kuru_client, mock_blockchain):
        """Client should place limit order asynchronously and return tx_hash."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

            tx_hash = kuru_client.place_limit_order(
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("1.0"),
                post_only=True,
                async_execution=True,
            )

            # Should return tx_hash
            assert tx_hash == mock_blockchain.send_transaction.return_value
            assert tx_hash.startswith("0x")
            assert len(tx_hash) == 66

            # Should not wait for receipt
            mock_blockchain.wait_for_transaction_receipt.assert_not_called()
            mock_blockchain.send_transaction.assert_called_once()

    def test_kuru_client_places_limit_order_sync(self, kuru_client, mock_blockchain):
        """Client should place limit order synchronously and return order_id."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

            order_id = kuru_client.place_limit_order(
                market="ETH-USDC",
                side=OrderSide.BUY,
                price=Decimal("2000.0"),
                size=Decimal("1.0"),
                post_only=True,
                async_execution=False,
            )

            # Should wait for receipt and return order_id
            assert order_id is not None
            mock_blockchain.send_transaction.assert_called_once()
            mock_blockchain.wait_for_transaction_receipt.assert_called_once()


class TestKuruClientMarketOrders:
    """Test Kuru market order placement."""

    def test_kuru_client_places_market_order(self, kuru_client, mock_blockchain):
        """Client should place IOC market order."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market, \
             patch.object(kuru_client, 'get_best_price') as mock_get_best_price:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }
            mock_get_best_price.return_value = Decimal("2000.0")

            order_id = kuru_client.place_market_order(
                market="ETH-USDC",
                side=OrderSide.BUY,
                size=Decimal("1.0"),
            )

            assert order_id is not None
            assert isinstance(order_id, str)
            mock_blockchain.send_transaction.assert_called_once()

    def test_kuru_client_places_market_sell_order(self, kuru_client, mock_blockchain):
        """Client should place market sell order."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market, \
             patch.object(kuru_client, 'get_best_price') as mock_get_best_price:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }
            mock_get_best_price.return_value = Decimal("2000.0")

            order_id = kuru_client.place_market_order(
                market="ETH-USDC",
                side=OrderSide.SELL,
                size=Decimal("0.5"),
                slippage=Decimal("0.01"),  # 1% slippage
            )

            assert order_id is not None
            mock_blockchain.send_transaction.assert_called_once()

    def test_kuru_client_validates_market_order_size(self, kuru_client, mock_blockchain):
        """Client should validate market order size is positive."""
        with pytest.raises(ValueError):
            kuru_client.place_market_order(
                market="ETH-USDC",
                side=OrderSide.BUY,
                size=Decimal("-1.0"),
            )

    def test_kuru_client_checks_balance_for_market_order(self, kuru_client, mock_blockchain):
        """Client should check sufficient balance for market order."""
        mock_blockchain.get_token_balance.return_value = Decimal("0")

        with patch.object(kuru_client, 'get_market_params') as mock_get_market, \
             patch.object(kuru_client, 'get_best_price') as mock_get_best_price:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }
            mock_get_best_price.return_value = Decimal("2000.0")

            with pytest.raises(InsufficientBalanceError):
                kuru_client.place_market_order(
                    market="ETH-USDC",
                    side=OrderSide.BUY,
                    size=Decimal("1000.0"),
                )

    def test_kuru_client_places_market_order_async(self, kuru_client, mock_blockchain):
        """Client should place market order asynchronously and return tx_hash."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market, \
             patch.object(kuru_client, 'get_best_price') as mock_get_best_price:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }
            mock_get_best_price.return_value = Decimal("2000.0")

            tx_hash = kuru_client.place_market_order(
                market="ETH-USDC",
                side=OrderSide.BUY,
                size=Decimal("1.0"),
                async_execution=True,
            )

            # Should return tx_hash
            assert tx_hash == mock_blockchain.send_transaction.return_value
            assert tx_hash.startswith("0x")
            assert len(tx_hash) == 66

            # Should not wait for receipt
            mock_blockchain.wait_for_transaction_receipt.assert_not_called()


class TestKuruClientOrderCancellation:
    """Test Kuru order cancellation."""

    def test_kuru_client_cancels_order(self, kuru_client, mock_blockchain):
        """Client should cancel order by ID."""
        tx_hash = kuru_client.cancel_order(order_id="order_123456")

        assert tx_hash.startswith("0x")
        assert len(tx_hash) == 66
        mock_blockchain.send_transaction.assert_called_once()

    def test_kuru_client_cancels_multiple_orders(self, kuru_client, mock_blockchain):
        """Client should cancel multiple orders in batch."""
        order_ids = ["order_001", "order_002", "order_003"]
        tx_hash = kuru_client.cancel_orders(order_ids)

        assert tx_hash.startswith("0x")
        mock_blockchain.send_transaction.assert_called_once()

    def test_kuru_client_validates_order_id_format(self, kuru_client, mock_blockchain):
        """Client should validate order ID format."""
        with pytest.raises(ValueError):
            kuru_client.cancel_order(order_id="")


class TestKuruClientMarketParams:
    """Test Kuru market parameter fetching."""

    @patch('requests.get')
    def test_kuru_client_fetches_market_params(self, mock_get, kuru_client):
        """Client should fetch market parameters from API."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "market_id": "ETH-USDC",
            "base_token": "ETH",
            "quote_token": "USDC",
            "min_order_size": "0.001",
            "max_order_size": "1000.0",
            "tick_size": "0.01",
            "step_size": "0.001",
            "maker_fee": "0.0002",
            "taker_fee": "0.0005",
            "is_active": True,
        }

        params = kuru_client.get_market_params("ETH-USDC")

        assert params["market_id"] == "ETH-USDC"
        assert params["base_token"] == "ETH"
        assert params["quote_token"] == "USDC"
        assert isinstance(params["min_order_size"], Decimal)
        assert isinstance(params["tick_size"], Decimal)
        assert params["is_active"] is True

    @patch('requests.get')
    def test_kuru_client_handles_invalid_market(self, mock_get, kuru_client):
        """Client should raise error for invalid market."""
        mock_get.return_value.status_code = 404

        with pytest.raises(InvalidMarketError):
            kuru_client.get_market_params("INVALID-MARKET")

    @patch('requests.get')
    def test_kuru_client_caches_market_params(self, mock_get, kuru_client):
        """Client should cache market parameters."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "market_id": "ETH-USDC",
            "base_token": "ETH",
            "quote_token": "USDC",
            "min_order_size": "0.001",
            "is_active": True,
        }

        # Fetch twice
        kuru_client.get_market_params("ETH-USDC")
        kuru_client.get_market_params("ETH-USDC")

        # Should only call API once (cached)
        assert mock_get.call_count == 1


class TestKuruClientOrderbook:
    """Test Kuru orderbook functionality."""

    @patch('requests.get')
    def test_kuru_client_fetches_orderbook(self, mock_get, kuru_client):
        """Client should fetch orderbook data."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "bids": [
                {"price": "2000.0", "size": "1.5"},
                {"price": "1999.0", "size": "2.0"},
            ],
            "asks": [
                {"price": "2001.0", "size": "1.0"},
                {"price": "2002.0", "size": "0.5"},
            ],
        }

        orderbook = kuru_client.get_orderbook("ETH-USDC")

        assert "bids" in orderbook
        assert "asks" in orderbook
        assert len(orderbook["bids"]) == 2
        assert len(orderbook["asks"]) == 2
        # Verify prices are converted to Decimal
        assert isinstance(orderbook["bids"][0]["price"], Decimal)
        assert isinstance(orderbook["asks"][0]["size"], Decimal)

    @patch('requests.get')
    def test_kuru_client_returns_empty_orderbook_on_error(self, mock_get, kuru_client):
        """Client should return empty orderbook on request failure."""
        mock_get.side_effect = requests.exceptions.RequestException("API error")

        orderbook = kuru_client.get_orderbook("ETH-USDC")

        assert orderbook == {"bids": [], "asks": []}

    @patch('requests.get')
    def test_kuru_client_handles_orderbook_timeout(self, mock_get, kuru_client):
        """Client should handle orderbook request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        orderbook = kuru_client.get_orderbook("ETH-USDC")

        assert orderbook == {"bids": [], "asks": []}

    @patch('requests.get')
    def test_kuru_client_tries_alternative_orderbook_endpoint(self, mock_get, kuru_client):
        """Client should try alternative endpoint if primary fails."""
        # First call returns 404, second succeeds
        mock_get.side_effect = [
            Mock(status_code=404),
            Mock(
                status_code=200,
                json=lambda: {"bids": [{"price": "2000.0", "size": "1.0"}], "asks": []},
            ),
        ]

        orderbook = kuru_client.get_orderbook("ETH-USDC")

        # Should have tried both endpoints
        assert mock_get.call_count == 2
        assert len(orderbook["bids"]) == 1

    @patch.object(KuruClient, 'get_orderbook')
    def test_kuru_client_gets_best_bid_price(self, mock_orderbook, kuru_client):
        """Client should get best bid price for sell orders."""
        mock_orderbook.return_value = {
            "bids": [
                {"price": Decimal("2000.0"), "size": Decimal("1.5")},
                {"price": Decimal("1999.0"), "size": Decimal("2.0")},
            ],
            "asks": [
                {"price": Decimal("2001.0"), "size": Decimal("1.0")},
            ],
        }

        best_price = kuru_client.get_best_price("ETH-USDC", OrderSide.SELL)

        assert best_price == Decimal("2000.0")

    @patch.object(KuruClient, 'get_orderbook')
    def test_kuru_client_gets_best_ask_price(self, mock_orderbook, kuru_client):
        """Client should get best ask price for buy orders."""
        mock_orderbook.return_value = {
            "bids": [
                {"price": Decimal("2000.0"), "size": Decimal("1.5")},
            ],
            "asks": [
                {"price": Decimal("2001.0"), "size": Decimal("1.0")},
                {"price": Decimal("2002.0"), "size": Decimal("0.5")},
            ],
        }

        best_price = kuru_client.get_best_price("ETH-USDC", OrderSide.BUY)

        assert best_price == Decimal("2001.0")

    @patch.object(KuruClient, 'get_orderbook')
    def test_kuru_client_returns_none_for_empty_orderbook(self, mock_orderbook, kuru_client):
        """Client should return None when orderbook is empty."""
        mock_orderbook.return_value = {"bids": [], "asks": []}

        best_price_buy = kuru_client.get_best_price("ETH-USDC", OrderSide.BUY)
        best_price_sell = kuru_client.get_best_price("ETH-USDC", OrderSide.SELL)

        assert best_price_buy is None
        assert best_price_sell is None

    @patch.object(KuruClient, 'get_orderbook')
    def test_kuru_client_handles_best_price_error(self, mock_orderbook, kuru_client):
        """Client should return None on error fetching best price."""
        mock_orderbook.side_effect = Exception("API error")

        best_price = kuru_client.get_best_price("ETH-USDC", OrderSide.BUY)

        assert best_price is None


class TestKuruClientCostEstimation:
    """Test Kuru cost estimation."""

    @patch('requests.get')
    def test_kuru_client_estimates_trade_cost(self, mock_get, kuru_client):
        """Client should estimate trade cost including fees."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "market_id": "ETH-USDC",
            "taker_fee": "0.0005",
            "maker_fee": "0.0002",
        }

        cost = kuru_client.estimate_cost(
            market="ETH-USDC",
            side=OrderSide.BUY,
            size=Decimal("1.0"),
            price=Decimal("2000.0"),
        )

        assert isinstance(cost, Decimal)
        assert cost > Decimal("2000.0")  # Should include fees

    @patch.object(KuruClient, 'get_best_price')
    @patch.object(KuruClient, 'get_market_params')
    def test_kuru_client_estimates_cost_from_orderbook(
        self, mock_get_market, mock_get_best_price, kuru_client
    ):
        """Client should fetch price from orderbook when not provided."""
        mock_get_market.return_value = {"taker_fee": Decimal("0.0005")}
        mock_get_best_price.return_value = Decimal("2001.0")

        cost = kuru_client.estimate_cost(
            market="ETH-USDC",
            side=OrderSide.BUY,
            size=Decimal("1.0"),
            price=None,  # Should fetch from orderbook
        )

        # Verify get_best_price was called
        mock_get_best_price.assert_called_once_with("ETH-USDC", OrderSide.BUY)

        # Cost should be based on orderbook price
        assert isinstance(cost, Decimal)
        expected = Decimal("2001.0") * Decimal("1.0") * (Decimal("1") + Decimal("0.0005"))
        assert cost == expected

    @patch.object(KuruClient, 'get_market_params')
    @patch.object(KuruClient, 'get_best_price')
    def test_kuru_client_raises_error_for_empty_orderbook(
        self, mock_get_best_price, mock_get_market, kuru_client
    ):
        """Client should raise error when orderbook is empty."""
        mock_get_market.return_value = {"taker_fee": Decimal("0.0005")}
        mock_get_best_price.return_value = None

        with pytest.raises(OrderExecutionError, match="orderbook empty"):
            kuru_client.estimate_cost(
                market="ETH-USDC",
                side=OrderSide.BUY,
                size=Decimal("1.0"),
                price=None,
            )

    def test_kuru_client_estimates_market_order_cost(self, kuru_client):
        """Client should estimate market order cost with slippage."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "taker_fee": Decimal("0.0005"),
            }

            cost = kuru_client.estimate_market_order_cost(
                market="ETH-USDC",
                side=OrderSide.BUY,
                size=Decimal("1.0"),
                expected_price=Decimal("2000.0"),
                slippage=Decimal("0.01"),  # 1%
            )

            assert isinstance(cost, Decimal)
            # Should include slippage and fees
            assert cost > Decimal("2000.0")


class TestKuruClientErrorHandling:
    """Test Kuru client error handling."""

    def test_kuru_client_handles_transaction_failure(self, kuru_client, mock_blockchain):
        """Client should handle transaction failures."""
        from src.kuru_copytr_bot.core.exceptions import TransactionFailedError
        mock_blockchain.send_transaction.side_effect = TransactionFailedError("Transaction failed")

        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

            with pytest.raises(OrderExecutionError):
                kuru_client.place_limit_order(
                    market="ETH-USDC",
                    side=OrderSide.BUY,
                    price=Decimal("2000.0"),
                    size=Decimal("1.0"),
                )

    def test_kuru_client_handles_network_error(self, kuru_client):
        """Client should handle network errors gracefully."""
        from src.kuru_copytr_bot.core.exceptions import BlockchainConnectionError

        with patch('requests.get') as mock_get:
            mock_get.side_effect = BlockchainConnectionError("Network error")

            with pytest.raises(BlockchainConnectionError):
                kuru_client.get_market_params("ETH-USDC")

    def test_kuru_client_validates_minimum_order_size(self, kuru_client):
        """Client should enforce minimum order size."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.01"),
                "is_active": True,
            }

            with pytest.raises(ValueError):
                kuru_client.place_limit_order(
                    market="ETH-USDC",
                    side=OrderSide.BUY,
                    price=Decimal("2000.0"),
                    size=Decimal("0.001"),  # Below minimum
                )

    def test_kuru_client_validates_maximum_order_size(self, kuru_client):
        """Client should enforce maximum order size."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.01"),
                "max_order_size": Decimal("1000.0"),
                "is_active": True,
            }

            with pytest.raises(ValueError):
                kuru_client.place_limit_order(
                    market="ETH-USDC",
                    side=OrderSide.BUY,
                    price=Decimal("2000.0"),
                    size=Decimal("10000.0"),  # Above maximum
                )

    def test_kuru_client_rejects_inactive_market(self, kuru_client):
        """Client should reject orders on inactive markets."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "is_active": False,
            }

            with pytest.raises(InvalidMarketError):
                kuru_client.place_limit_order(
                    market="INACTIVE-MARKET",
                    side=OrderSide.BUY,
                    price=Decimal("2000.0"),
                    size=Decimal("1.0"),
                )


class TestKuruClientOrderStatus:
    """Test Kuru order status queries."""

    @patch('requests.get')
    def test_kuru_client_gets_user_orders(self, mock_get, kuru_client):
        """Client should get all orders for a user."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"order_id": "order_001", "status": "OPEN", "filled_size": "0.5", "remaining_size": "0.5"},
            {"order_id": "order_002", "status": "FILLED", "filled_size": "1.0", "remaining_size": "0"},
        ]

        user_address = "0x1234567890123456789012345678901234567890"
        orders = kuru_client.get_user_orders(user_address)

        assert len(orders) == 2
        assert orders[0]["order_id"] == "order_001"
        assert orders[1]["order_id"] == "order_002"
        # Verify endpoint was called correctly
        mock_get.assert_called_once_with(
            f"{kuru_client.api_url}/orders/user/{user_address}",
            params={"limit": 100, "offset": 0}
        )

    @patch('requests.get')
    def test_kuru_client_gets_user_orders_with_pagination(self, mock_get, kuru_client):
        """Client should support pagination for user orders."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"order_id": "order_101", "status": "OPEN"},
        ]

        user_address = "0x1234567890123456789012345678901234567890"
        orders = kuru_client.get_user_orders(user_address, limit=50, offset=100)

        assert len(orders) == 1
        mock_get.assert_called_once_with(
            f"{kuru_client.api_url}/orders/user/{user_address}",
            params={"limit": 50, "offset": 100}
        )

    @patch('requests.get')
    def test_kuru_client_gets_user_orders_returns_empty_on_404(self, mock_get, kuru_client):
        """Client should return empty list when user has no orders."""
        mock_get.return_value.status_code = 404

        user_address = "0x1234567890123456789012345678901234567890"
        orders = kuru_client.get_user_orders(user_address)

        assert orders == []

    @patch('requests.get')
    def test_kuru_client_gets_single_order(self, mock_get, kuru_client):
        """Client should get a single order by ID."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "order_id": "order_123456",
            "status": "OPEN",
            "filled_size": "0.5",
            "remaining_size": "0.5",
        }

        order = kuru_client.get_order("order_123456")

        assert order["order_id"] == "order_123456"
        assert order["status"] == "OPEN"
        assert isinstance(order["filled_size"], Decimal)
        # Verify endpoint was called correctly
        mock_get.assert_called_once_with(f"{kuru_client.api_url}/orders/order_123456")

    @patch('requests.get')
    def test_kuru_client_gets_single_order_returns_none_on_404(self, mock_get, kuru_client):
        """Client should return None when order not found."""
        mock_get.return_value.status_code = 404

        order = kuru_client.get_order("order_999999")

        assert order is None

    @patch('requests.get')
    def test_kuru_client_gets_active_orders(self, mock_get, kuru_client):
        """Client should get only active orders for a user."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"order_id": "order_001", "status": "OPEN"},
            {"order_id": "order_002", "status": "PARTIALLY_FILLED"},
        ]

        user_address = "0x1234567890123456789012345678901234567890"
        orders = kuru_client.get_active_orders(user_address)

        assert len(orders) == 2
        assert orders[0]["status"] in ["OPEN", "PARTIALLY_FILLED"]
        # Verify endpoint was called correctly
        mock_get.assert_called_once_with(
            f"{kuru_client.api_url}/{user_address}/user/orders/active",
            params={"limit": 100, "offset": 0}
        )

    @patch('requests.get')
    def test_kuru_client_gets_active_orders_with_pagination(self, mock_get, kuru_client):
        """Client should support pagination for active orders."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"order_id": "order_050", "status": "OPEN"},
        ]

        user_address = "0x1234567890123456789012345678901234567890"
        orders = kuru_client.get_active_orders(user_address, limit=20, offset=40)

        assert len(orders) == 1
        mock_get.assert_called_once_with(
            f"{kuru_client.api_url}/{user_address}/user/orders/active",
            params={"limit": 20, "offset": 40}
        )

    @patch('requests.get')
    def test_kuru_client_gets_active_orders_returns_empty_on_404(self, mock_get, kuru_client):
        """Client should return empty list when no active orders."""
        mock_get.return_value.status_code = 404

        user_address = "0x1234567890123456789012345678901234567890"
        orders = kuru_client.get_active_orders(user_address)

        assert orders == []

    @patch('requests.get')
    def test_kuru_client_gets_open_orders(self, mock_get, kuru_client):
        """Client should get all open orders."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"order_id": "order_001", "status": "OPEN"},
            {"order_id": "order_002", "status": "OPEN"},
        ]

        orders = kuru_client.get_open_orders(market="ETH-USDC")

        assert len(orders) == 2
        assert orders[0]["order_id"] == "order_001"

    @patch('requests.get')
    def test_kuru_client_gets_market_orders(self, mock_get, kuru_client):
        """Client should get multiple orders by ID from a market."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"order_id": 12345, "status": "OPEN", "price": "2000.0"},
            {"order_id": 12346, "status": "PARTIALLY_FILLED", "price": "2001.0"},
            {"order_id": 12347, "status": "FILLED", "price": "2002.0"},
        ]

        market_address = "0x1234567890123456789012345678901234567890"
        order_ids = [12345, 12346, 12347]
        orders = kuru_client.get_market_orders(market_address, order_ids)

        assert len(orders) == 3
        assert orders[0]["order_id"] == 12345
        assert orders[1]["order_id"] == 12346
        assert orders[2]["order_id"] == 12347

        # Verify endpoint was called correctly
        mock_get.assert_called_once_with(
            f"{kuru_client.api_url}/orders/market/{market_address}",
            params={"order_ids": "12345,12346,12347"}
        )

    @patch('requests.get')
    def test_kuru_client_gets_market_orders_with_empty_list(self, mock_get, kuru_client):
        """Client should handle empty order_ids list."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []

        market_address = "0x1234567890123456789012345678901234567890"
        orders = kuru_client.get_market_orders(market_address, [])

        assert orders == []
        # Should still call API but with empty order_ids
        mock_get.assert_called_once_with(
            f"{kuru_client.api_url}/orders/market/{market_address}",
            params={"order_ids": ""}
        )

    @patch('requests.get')
    def test_kuru_client_gets_market_orders_returns_empty_on_404(self, mock_get, kuru_client):
        """Client should return empty list when orders not found."""
        mock_get.return_value.status_code = 404

        market_address = "0x1234567890123456789012345678901234567890"
        orders = kuru_client.get_market_orders(market_address, [12345])

        assert orders == []


class TestKuruClientTrades:
    """Test Kuru trade queries."""

    @patch('requests.get')
    def test_kuru_client_gets_user_trades(self, mock_get, kuru_client):
        """Client should get trades for a user on a specific market."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                "order_id": "123",
                "market": "ETH-USDC",
                "side": "BUY",
                "price": "2000.0",
                "size": "1.0",
                "timestamp": 1234567890
            },
            {
                "order_id": "124",
                "market": "ETH-USDC",
                "side": "SELL",
                "price": "2010.0",
                "size": "0.5",
                "timestamp": 1234567900
            },
        ]

        market_address = "0xMARKET00000000000000000000000000000000000"
        user_address = "0x1234567890123456789012345678901234567890"
        trades = kuru_client.get_user_trades(market_address, user_address)

        assert len(trades) == 2
        assert trades[0]["market"] == "ETH-USDC"
        # Verify endpoint was called correctly
        mock_get.assert_called_once_with(
            f"{kuru_client.api_url}/{market_address}/trades/user/{user_address}",
            params={}
        )

    @patch('requests.get')
    def test_kuru_client_gets_user_trades_with_time_filter(self, mock_get, kuru_client):
        """Client should filter trades by timestamp."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"order_id": "123", "market": "ETH-USDC", "timestamp": 1234567890},
        ]

        market_address = "0xMARKET00000000000000000000000000000000000"
        user_address = "0x1234567890123456789012345678901234567890"
        trades = kuru_client.get_user_trades(
            market_address,
            user_address,
            start_timestamp=1234567000,
            end_timestamp=1234568000
        )

        assert len(trades) == 1
        mock_get.assert_called_once_with(
            f"{kuru_client.api_url}/{market_address}/trades/user/{user_address}",
            params={"start_timestamp": 1234567000, "end_timestamp": 1234568000}
        )

    @patch('requests.get')
    def test_kuru_client_gets_user_trades_returns_empty_on_404(self, mock_get, kuru_client):
        """Client should return empty list when no trades found."""
        mock_get.return_value.status_code = 404

        market_address = "0xMARKET00000000000000000000000000000000000"
        user_address = "0x1234567890123456789012345678901234567890"
        trades = kuru_client.get_user_trades(market_address, user_address)

        assert trades == []


class TestKuruClientPositions:
    """Test Kuru position queries."""

    @patch('requests.get')
    def test_kuru_client_gets_positions(self, mock_get, kuru_client):
        """Client should get current positions."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                "market": "ETH-USDC",
                "size": "1.5",
                "entry_price": "2000.0",
                "unrealized_pnl": "50.0",
            }
        ]

        positions = kuru_client.get_positions()

        assert len(positions) == 1
        assert positions[0]["market"] == "ETH-USDC"
        assert isinstance(positions[0]["size"], Decimal)

    @patch('requests.get')
    def test_kuru_client_filters_positions_by_market(self, mock_get, kuru_client):
        """Client should filter positions by market."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {"market": "ETH-USDC", "size": "1.0"},
        ]

        positions = kuru_client.get_positions(market="ETH-USDC")

        assert len(positions) == 1
        mock_get.assert_called_with(
            f"{kuru_client.api_url}/positions",
            params={"market": "ETH-USDC"}
        )


class TestKuruClientBalance:
    """Tests for balance queries."""

    def test_kuru_client_gets_native_balance(self, kuru_client, mock_blockchain):
        """Client should get native token balance."""
        mock_blockchain.get_balance.return_value = Decimal("100.5")
        mock_blockchain.wallet_address = "0x1234567890123456789012345678901234567890"

        balance = kuru_client.get_balance()

        assert balance == Decimal("100.5")
        mock_blockchain.get_balance.assert_called_once_with(
            "0x1234567890123456789012345678901234567890"
        )

    def test_kuru_client_gets_token_balance(self, kuru_client, mock_blockchain):
        """Client should get ERC20 token balance."""
        token_address = "0xUSDC000000000000000000000000000000000000"
        mock_blockchain.get_token_balance.return_value = Decimal("500.25")
        mock_blockchain.wallet_address = "0x1234567890123456789012345678901234567890"

        balance = kuru_client.get_balance(token=token_address)

        assert balance == Decimal("500.25")
        mock_blockchain.get_token_balance.assert_called_once_with(
            token_address=token_address,
            wallet_address="0x1234567890123456789012345678901234567890"
        )

    def test_kuru_client_handles_balance_check_failure(self, kuru_client, mock_blockchain):
        """Client should handle balance check failures."""
        mock_blockchain.get_balance.side_effect = Exception("Connection error")

        with pytest.raises(BlockchainConnectionError, match="Failed to get balance"):
            kuru_client.get_balance()
