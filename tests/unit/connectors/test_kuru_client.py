"""Unit tests for Kuru Exchange client."""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient
from src.kuru_copytr_bot.core.enums import OrderSide, OrderType
from src.kuru_copytr_bot.core.exceptions import (
    InsufficientBalanceError,
    InvalidMarketError,
    OrderExecutionError,
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
        tx_hash = kuru_client.deposit_margin(
            token="0xUSDCAddress00000000000000000000000000000",
            amount=Decimal("100.0"),
        )

        assert tx_hash.startswith("0x")
        assert len(tx_hash) == 66
        # ERC20 deposits require 2 transactions: approve + deposit
        assert mock_blockchain.send_transaction.call_count == 2

    def test_kuru_client_deposits_native_token(self, kuru_client, mock_blockchain):
        """Client should deposit native token (ETH/MON) to margin."""
        tx_hash = kuru_client.deposit_margin(
            token="0x0000000000000000000000000000000000000000",  # Native token
            amount=Decimal("1.0"),
        )

        assert tx_hash.startswith("0x")
        # Should send transaction with value
        call_args = mock_blockchain.send_transaction.call_args
        assert call_args[1]["value"] > 0

    def test_kuru_client_checks_balance_before_deposit(self, kuru_client, mock_blockchain):
        """Client should check balance before deposit."""
        mock_blockchain.get_token_balance.return_value = Decimal("50.0")

        with pytest.raises(InsufficientBalanceError):
            kuru_client.deposit_margin(
                token="0xUSDCAddress00000000000000000000000000000",
                amount=Decimal("100.0"),
            )

    def test_kuru_client_approves_erc20_before_deposit(self, kuru_client, mock_blockchain):
        """Client should approve ERC20 tokens before deposit."""
        kuru_client.deposit_margin(
            token="0xUSDCAddress00000000000000000000000000000",
            amount=Decimal("100.0"),
        )

        # Should call send_transaction at least twice (approve + deposit)
        assert mock_blockchain.send_transaction.call_count >= 2


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


class TestKuruClientMarketOrders:
    """Test Kuru market order placement."""

    def test_kuru_client_places_market_order(self, kuru_client, mock_blockchain):
        """Client should place IOC market order."""
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

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
        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

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

        with patch.object(kuru_client, 'get_market_params') as mock_get_market:
            mock_get_market.return_value = {
                "min_order_size": Decimal("0.001"),
                "max_order_size": Decimal("1000"),
                "tick_size": Decimal("0.01"),
                "is_active": True,
            }

            with pytest.raises(InsufficientBalanceError):
                kuru_client.place_market_order(
                    market="ETH-USDC",
                    side=OrderSide.BUY,
                    size=Decimal("1000.0"),
                )


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
    def test_kuru_client_gets_order_status(self, mock_get, kuru_client):
        """Client should get order status from API."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "order_id": "order_123456",
            "status": "OPEN",
            "filled_size": "0.5",
            "remaining_size": "0.5",
        }

        status = kuru_client.get_order_status("order_123456")

        assert status["order_id"] == "order_123456"
        assert status["status"] == "OPEN"
        assert isinstance(status["filled_size"], Decimal)

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
