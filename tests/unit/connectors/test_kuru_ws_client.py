"""Tests for Kuru WebSocket client."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.kuru_copytr_bot.connectors.websocket.kuru_ws_client import KuruWebSocketClient
from src.kuru_copytr_bot.models.order import OrderResponse
from src.kuru_copytr_bot.models.trade import TradeResponse


@contextmanager
def mock_socketio_client():
    """Context manager to properly mock Socket.IO AsyncClient."""
    with patch(
        "src.kuru_copytr_bot.connectors.websocket.kuru_ws_client.socketio.AsyncClient"
    ) as mock_socketio:
        mock_sio = AsyncMock()
        # Mock the decorators to return the original function
        mock_sio.event = Mock(return_value=lambda f: f)
        mock_sio.on = Mock(return_value=lambda f: f)
        mock_sio.connected = False
        mock_socketio.return_value = mock_sio
        yield mock_sio


@pytest.fixture
def ws_url():
    """WebSocket URL for testing."""
    return "wss://ws.testnet.kuru.io"


@pytest.fixture
def market_address():
    """Market address for testing."""
    return "0x1234567890123456789012345678901234567890"


@pytest.fixture
def sample_order_created_data():
    """Sample OrderCreated event data."""
    return {
        "order_id": 123456,
        "market_address": "0x1234567890123456789012345678901234567890",
        "owner": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "price": "2000.50",
        "size": "1.5",
        "remaining_size": "1.5",
        "is_buy": True,
        "is_canceled": False,
        "transaction_hash": "0xabc123def4567890123456789012345678901234567890123456789012345678",
        "trigger_time": 1234567890,
        "cloid": "test-cloid-123",
    }


@pytest.fixture
def sample_trade_data():
    """Sample Trade event data."""
    return {
        "orderid": 123456,
        "market_address": "0x1234567890123456789012345678901234567890",
        "makeraddress": "0x1234567890123456789012345678901234567890",
        "takeraddress": "0x0987654321098765432109876543210987654321",
        "isbuy": True,
        "price": "2000.50",
        "filledsize": "1.5",
        "transactionhash": "0xabc123def4567890123456789012345678901234567890123456789012345678",
        "triggertime": 1234567890,
        "cloid": "test-cloid-123",
    }


@pytest.fixture
def sample_orders_canceled_data():
    """Sample OrdersCanceled event data."""
    return {
        "order_ids": [123456, 789012],
        "cloids": ["cloid-123", "cloid-789"],
        "maker_address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "canceled_orders_data": [
            {"order_id": 123456, "reason": "user_cancelled"},
            {"order_id": 789012, "reason": "user_cancelled"},
        ],
    }


class TestKuruWebSocketClient:
    """Test Kuru WebSocket client."""

    @pytest.mark.asyncio
    async def test_websocket_client_initialization(self, ws_url, market_address):
        """WebSocket client should initialize with URL and market address."""
        client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)

        assert client.ws_url == ws_url
        assert client.market_address == market_address
        assert client.sio is not None

    @pytest.mark.asyncio
    async def test_websocket_client_connect(self, ws_url, market_address):
        """WebSocket client should connect with market filter."""
        with mock_socketio_client() as mock_sio:
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            await client.connect()

            # Should connect with market address in query params
            mock_sio.connect.assert_called_once()
            call_args = mock_sio.connect.call_args
            assert ws_url in str(call_args)

    @pytest.mark.asyncio
    async def test_websocket_client_disconnect(self, ws_url, market_address):
        """WebSocket client should disconnect properly."""
        with mock_socketio_client() as mock_sio:
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            await client.disconnect()

            mock_sio.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_handles_order_created_event(
        self, ws_url, market_address, sample_order_created_data
    ):
        """WebSocket client should handle OrderCreated events."""
        order_callback = Mock()

        with mock_socketio_client():
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_order_created_callback = order_callback

            # Simulate event
            await client.handle_order_created(sample_order_created_data)

            # Should call callback with OrderResponse
            order_callback.assert_called_once()
            order_response = order_callback.call_args[0][0]
            assert isinstance(order_response, OrderResponse)
            assert order_response.order_id == sample_order_created_data["order_id"]

    @pytest.mark.asyncio
    async def test_websocket_handles_trade_event(self, ws_url, market_address, sample_trade_data):
        """WebSocket client should handle Trade events."""
        trade_callback = Mock()

        with mock_socketio_client() as _:
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_trade_callback = trade_callback

            # Simulate event
            await client.handle_trade(sample_trade_data)

            # Should call callback with TradeResponse
            trade_callback.assert_called_once()
            trade_response = trade_callback.call_args[0][0]
            assert isinstance(trade_response, TradeResponse)
            assert trade_response.orderid == sample_trade_data["orderid"]

    @pytest.mark.asyncio
    async def test_websocket_handles_orders_canceled_event(
        self, ws_url, market_address, sample_orders_canceled_data
    ):
        """WebSocket client should handle OrdersCanceled events."""
        cancel_callback = Mock()

        with mock_socketio_client() as _:
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_orders_canceled_callback = cancel_callback

            # Simulate event
            await client.handle_orders_canceled(sample_orders_canceled_data)

            # Should call callback with order IDs, cloids, maker_address, and canceled_orders_data
            cancel_callback.assert_called_once()
            call_args = cancel_callback.call_args[0]
            assert call_args[0] == sample_orders_canceled_data["order_ids"]
            assert call_args[1] == sample_orders_canceled_data["cloids"]
            assert call_args[2] == sample_orders_canceled_data["maker_address"]
            assert call_args[3] == sample_orders_canceled_data["canceled_orders_data"]

    @pytest.mark.asyncio
    async def test_websocket_reconnection_on_disconnect(self, ws_url, market_address):
        """WebSocket client should handle reconnection on disconnect."""
        with mock_socketio_client() as _:
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)

            # Simulate disconnect event
            await client.handle_disconnect()

            # Should attempt reconnection
            assert client.should_reconnect is True

    @pytest.mark.asyncio
    async def test_websocket_filters_events_by_market(
        self, ws_url, market_address, sample_order_created_data
    ):
        """WebSocket client should filter events by market address."""
        order_callback = Mock()

        with mock_socketio_client() as _:
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_order_created_callback = order_callback

            # Event with matching market address
            await client.handle_order_created(sample_order_created_data)
            assert order_callback.call_count == 1

            # Event with different market address
            other_market_data = sample_order_created_data.copy()
            other_market_data["market_address"] = "0x9999999999999999999999999999999999999999"
            await client.handle_order_created(other_market_data)

            # Should not call callback again (filtered out)
            assert order_callback.call_count == 1

    @pytest.mark.asyncio
    async def test_websocket_handles_connection_error(self, ws_url, market_address):
        """WebSocket client should handle connection errors gracefully."""
        with mock_socketio_client() as mock_sio:
            mock_sio.connect.side_effect = Exception("Connection failed")

            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)

            # Should not raise exception
            try:
                await client.connect()
            except Exception:
                pytest.fail("WebSocket client should handle connection errors gracefully")

    @pytest.mark.asyncio
    async def test_websocket_registers_event_handlers(self, ws_url, market_address):
        """WebSocket client should register event handlers on connection."""
        with mock_socketio_client() as mock_sio:
            KuruWebSocketClient(ws_url=ws_url, market_address=market_address)

            # Should register handlers for all three event types
            assert mock_sio.on.call_count >= 3
            registered_events = [call[0][0] for call in mock_sio.on.call_args_list]
            assert "OrderCreated" in registered_events
            assert "Trade" in registered_events
            assert "OrdersCanceled" in registered_events

    @pytest.mark.asyncio
    async def test_websocket_sets_callbacks(self, ws_url, market_address):
        """WebSocket client should allow setting event callbacks."""
        order_callback = Mock()
        trade_callback = Mock()
        cancel_callback = Mock()

        client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)

        client.set_order_created_callback(order_callback)
        client.set_trade_callback(trade_callback)
        client.set_orders_canceled_callback(cancel_callback)

        assert client.on_order_created_callback == order_callback
        assert client.on_trade_callback == trade_callback
        assert client.on_orders_canceled_callback == cancel_callback

    @pytest.mark.asyncio
    async def test_websocket_connected_property(self, ws_url, market_address):
        """WebSocket client should track connection status."""
        with mock_socketio_client() as mock_sio:
            mock_sio.connected = True

            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)

            assert client.is_connected == mock_sio.connected

    @pytest.mark.asyncio
    async def test_websocket_filters_trade_events_by_market(
        self, ws_url, market_address, sample_trade_data
    ):
        """WebSocket client should filter Trade events by market address."""
        trade_callback = Mock()

        with mock_socketio_client() as _:
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_trade_callback = trade_callback

            # Event with matching market address
            await client.handle_trade(sample_trade_data)
            assert trade_callback.call_count == 1

            # Event with different market address
            other_market_data = sample_trade_data.copy()
            other_market_data["market_address"] = "0x9999999999999999999999999999999999999999"
            await client.handle_trade(other_market_data)

            # Should not call callback again (filtered out)
            assert trade_callback.call_count == 1


class TestKuruWebSocketClientMalformedData:
    """Test WebSocket client handling of malformed event data."""

    @pytest.mark.asyncio
    async def test_websocket_handles_missing_market_address_in_order_created(
        self, ws_url, market_address
    ):
        """WebSocket should log error when OrderCreated event missing market_address."""
        malformed_data = {
            "order_id": 123456,
            # "market_address" field is missing
            "owner": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "price": "2000.50",
            "size": "1.5",
            "remaining_size": "1.5",
            "is_buy": True,
            "is_canceled": False,
            "transaction_hash": "0xabc123def4567890123456789012345678901234567890123456789012345678",
            "trigger_time": 1234567890,
        }

        order_callback = Mock()

        with mock_socketio_client():
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_order_created_callback = order_callback

            # Should handle error gracefully and not call callback
            await client.handle_order_created(malformed_data)

            # Callback should not be called due to Pydantic validation error
            order_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_handles_missing_required_field_in_trade(self, ws_url, market_address):
        """WebSocket should log error when Trade event missing required fields."""
        malformed_data = {
            "orderid": 123456,
            "market_address": "0x1234567890123456789012345678901234567890",
            # "makeraddress" field is missing (required)
            "takeraddress": "0x0987654321098765432109876543210987654321",
            "isbuy": True,
            "price": "2000.50",
            "filledsize": "1.5",
            "transactionhash": "0xabc123def4567890123456789012345678901234567890123456789012345678",
            "triggertime": 1234567890,
        }

        trade_callback = Mock()

        with mock_socketio_client():
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_trade_callback = trade_callback

            # Should handle error gracefully and not call callback
            await client.handle_trade(malformed_data)

            # Callback should not be called due to Pydantic validation error
            trade_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_handles_missing_order_ids_in_orders_canceled(
        self, ws_url, market_address
    ):
        """WebSocket should reject OrdersCanceled event with missing order_ids."""
        malformed_data = {
            # "order_ids" field is missing (required)
            "cloids": ["cloid-123"],
            "maker_address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "canceled_orders_data": [{"order_id": 123456, "reason": "user_cancelled"}],
        }

        cancel_callback = Mock()

        with mock_socketio_client():
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_orders_canceled_callback = cancel_callback

            # Should handle error and not call callback (missing required field)
            await client.handle_orders_canceled(malformed_data)

            # Callback should not be called due to missing required field
            cancel_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_handles_empty_market_address_in_order_created(
        self, ws_url, market_address
    ):
        """WebSocket should filter out OrderCreated with empty market_address."""
        malformed_data = {
            "order_id": 123456,
            "market_address": "",  # Empty string
            "owner": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "price": "2000.50",
            "size": "1.5",
            "remaining_size": "1.5",
            "is_buy": True,
            "is_canceled": False,
            "transaction_hash": "0xabc123def4567890123456789012345678901234567890123456789012345678",
            "trigger_time": 1234567890,
        }

        order_callback = Mock()

        with mock_socketio_client():
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_order_created_callback = order_callback

            # Should filter out due to market mismatch (empty != market_address)
            await client.handle_order_created(malformed_data)

            # Callback should not be called due to market filtering
            order_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_handles_missing_maker_address_in_orders_canceled(
        self, ws_url, market_address
    ):
        """WebSocket should reject OrdersCanceled event with missing maker_address."""
        malformed_data = {
            "order_ids": [123456],
            "cloids": ["cloid-123"],
            # "maker_address" field is missing (required)
            "canceled_orders_data": [{"order_id": 123456, "reason": "user_cancelled"}],
        }

        cancel_callback = Mock()

        with mock_socketio_client():
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_orders_canceled_callback = cancel_callback

            # Should handle error and not call callback (missing required field)
            await client.handle_orders_canceled(malformed_data)

            # Callback should not be called due to missing required field
            cancel_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_allows_missing_optional_fields_in_orders_canceled(
        self, ws_url, market_address
    ):
        """WebSocket should allow OrdersCanceled with missing optional fields."""
        minimal_data = {
            "order_ids": [123456, 789012],
            "maker_address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            # cloids and canceled_orders_data are optional
        }

        cancel_callback = Mock()

        with mock_socketio_client():
            client = KuruWebSocketClient(ws_url=ws_url, market_address=market_address)
            client.on_orders_canceled_callback = cancel_callback

            # Should call callback with empty lists for optional fields
            await client.handle_orders_canceled(minimal_data)

            # Callback should be called successfully
            cancel_callback.assert_called_once()
            call_args = cancel_callback.call_args[0]
            assert call_args[0] == [123456, 789012]  # order_ids
            assert call_args[1] == []  # cloids (defaulted to empty list)
            assert call_args[2] == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"  # maker_address
            assert call_args[3] == []  # canceled_orders_data (defaulted to empty list)
