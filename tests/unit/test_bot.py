"""Tests for copy trading bot orchestrator (WebSocket-based)."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from src.kuru_copytr_bot.bot import CopyTradingBot
from src.kuru_copytr_bot.core.enums import OrderSide
from src.kuru_copytr_bot.models.order import OrderResponse
from src.kuru_copytr_bot.models.trade import Trade, TradeResponse


@pytest.fixture
def mock_ws_client():
    """Mock WebSocket client."""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.is_connected = True
    client.set_trade_callback = Mock()
    client.set_order_created_callback = Mock()
    client.set_orders_canceled_callback = Mock()
    return client


@pytest.fixture
def mock_copier():
    """Mock trade copier."""
    copier = Mock()
    copier.process_trade = Mock(return_value="order_123")
    copier.process_order = Mock(return_value="order_456")
    copier.cancel_orders = Mock(return_value=True)
    copier.get_statistics = Mock(
        return_value={
            "successful_trades": 0,
            "failed_trades": 0,
            "rejected_trades": 0,
            "successful_orders": 0,
            "failed_orders": 0,
            "rejected_orders": 0,
            "orders_canceled": 0,
        }
    )
    copier.reset_statistics = Mock()
    return copier


@pytest.fixture
def sample_trade_response():
    """Sample TradeResponse for testing."""
    return TradeResponse(
        orderid=12345,
        makeraddress="0x1111111111111111111111111111111111111111",
        takeraddress="0x2222222222222222222222222222222222222222",
        isbuy=True,
        price="2000.50",
        filledsize="1.5",
        transactionhash="0x" + "a" * 64,
        triggertime=int(datetime.now(UTC).timestamp()),
    )


@pytest.fixture
def sample_trade():
    """Sample Trade for testing."""
    return Trade(
        id="trade_123",
        trader_address="0x1111111111111111111111111111111111111111",
        market="0x4444444444444444444444444444444444444444",
        side=OrderSide.BUY,
        price=Decimal("2000.0"),
        size=Decimal("5.0"),
        timestamp=datetime.now(UTC),
        tx_hash="0x" + "a" * 64,
    )


@pytest.fixture
def sample_order_response():
    """Sample OrderResponse for testing."""
    return OrderResponse(
        order_id=12345,
        market_address="0x4444444444444444444444444444444444444444",
        owner="0x1111111111111111111111111111111111111111",
        price="2000.50",
        size="1.5",
        remaining_size="1.5",
        is_buy=True,
        is_canceled=False,
        transaction_hash="0x" + "b" * 64,
        trigger_time=int(datetime.now(UTC).timestamp()),
        cloid="test-cloid-123",
    )


class TestCopyTradingBotInitialization:
    """Test bot initialization."""

    def test_bot_initializes_with_required_components(self, mock_ws_client, mock_copier):
        """Bot should initialize with required components."""
        market_address = "0x4444444444444444444444444444444444444444"
        source_wallets = ["0x1111111111111111111111111111111111111111"]

        bot = CopyTradingBot(
            ws_clients=[(market_address, mock_ws_client)],
            source_wallets=source_wallets,
            copier=mock_copier,
        )

        assert len(bot.ws_clients) == 1
        assert bot.ws_clients[0][0] == market_address
        assert bot.source_wallets == [w.lower() for w in source_wallets]
        assert bot.copier == mock_copier

    def test_bot_initializes_with_multiple_markets(self, mock_copier):
        """Bot should initialize with multiple market WebSocket clients."""
        ws_client1 = AsyncMock()
        ws_client1.set_trade_callback = Mock()
        ws_client2 = AsyncMock()
        ws_client2.set_trade_callback = Mock()

        market1 = "0x4444444444444444444444444444444444444444"
        market2 = "0x5555555555555555555555555555555555555555"

        bot = CopyTradingBot(
            ws_clients=[(market1, ws_client1), (market2, ws_client2)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        assert len(bot.ws_clients) == 2
        assert bot.ws_clients[0][0] == market1
        assert bot.ws_clients[1][0] == market2

    def test_bot_registers_trade_callbacks(self, mock_ws_client, mock_copier):
        """Bot should register trade callbacks with WebSocket clients."""
        CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        # Should have called set_trade_callback
        mock_ws_client.set_trade_callback.assert_called_once()
        # Verify the callback is callable
        callback = mock_ws_client.set_trade_callback.call_args[0][0]
        assert callable(callback)


class TestCopyTradingBotLifecycle:
    """Test bot lifecycle management."""

    @pytest.mark.asyncio
    async def test_bot_starts_and_connects_websockets(self, mock_ws_client, mock_copier):
        """Bot should connect all WebSocket clients when started."""
        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        await bot.start()

        mock_ws_client.connect.assert_called_once()
        assert bot.is_running is True

    @pytest.mark.asyncio
    async def test_bot_stops_and_disconnects_websockets(self, mock_ws_client, mock_copier):
        """Bot should disconnect all WebSocket clients when stopped."""
        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        await bot.start()
        await bot.stop()

        mock_ws_client.disconnect.assert_called_once()
        assert bot.is_running is False

    @pytest.mark.asyncio
    async def test_bot_connects_multiple_websockets(self, mock_copier):
        """Bot should connect all WebSocket clients in parallel."""
        ws_client1 = AsyncMock()
        ws_client1.set_trade_callback = Mock()
        ws_client2 = AsyncMock()
        ws_client2.set_trade_callback = Mock()

        bot = CopyTradingBot(
            ws_clients=[
                ("0x4444444444444444444444444444444444444444", ws_client1),
                ("0x5555555555555555555555555555555555555555", ws_client2),
            ],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        await bot.start()

        ws_client1.connect.assert_called_once()
        ws_client2.connect.assert_called_once()


class TestCopyTradingBotTradeProcessing:
    """Test trade processing workflow."""

    @pytest.mark.asyncio
    async def test_bot_processes_trade_from_monitored_wallet(
        self, mock_ws_client, mock_copier, sample_trade_response
    ):
        """Bot should process trades from monitored source wallets."""
        market_address = "0x4444444444444444444444444444444444444444"
        source_wallet = "0x1111111111111111111111111111111111111111"

        CopyTradingBot(
            ws_clients=[(market_address, mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        # Get the registered callback
        callback = mock_ws_client.set_trade_callback.call_args[0][0]

        # Simulate Trade event from WebSocket
        await callback(sample_trade_response)

        # Should process the trade
        mock_copier.process_trade.assert_called_once()
        call_args = mock_copier.process_trade.call_args[0][0]
        assert isinstance(call_args, Trade)
        assert call_args.trader_address.lower() == source_wallet.lower()

    @pytest.mark.asyncio
    async def test_bot_ignores_trade_from_unmonitored_wallet(
        self, mock_ws_client, mock_copier, sample_trade_response
    ):
        """Bot should ignore trades from wallets not in source_wallets."""
        market_address = "0x4444444444444444444444444444444444444444"
        # Source wallet is different from trade maker
        source_wallet = "0x9999999999999999999999999999999999999999"

        CopyTradingBot(
            ws_clients=[(market_address, mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        # Get the registered callback
        callback = mock_ws_client.set_trade_callback.call_args[0][0]

        # Simulate Trade event from unmonitored wallet
        await callback(sample_trade_response)

        # Should NOT process the trade
        mock_copier.process_trade.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_tracks_trades_detected(
        self, mock_ws_client, mock_copier, sample_trade_response
    ):
        """Bot should track number of trades detected."""
        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_trade_callback.call_args[0][0]

        # Process multiple trades
        await callback(sample_trade_response)
        await callback(sample_trade_response)

        stats = bot.get_statistics()
        assert stats["trades_detected"] == 2

    @pytest.mark.asyncio
    async def test_bot_converts_trade_response_to_trade_model(
        self, mock_ws_client, mock_copier, sample_trade_response
    ):
        """Bot should convert TradeResponse to Trade model with market address."""
        market_address = "0x4444444444444444444444444444444444444444"

        CopyTradingBot(
            ws_clients=[(market_address, mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_trade_callback.call_args[0][0]
        await callback(sample_trade_response)

        # Verify Trade model passed to copier
        mock_copier.process_trade.assert_called_once()
        trade = mock_copier.process_trade.call_args[0][0]
        assert isinstance(trade, Trade)
        assert trade.market == market_address
        assert trade.price == Decimal(sample_trade_response.price)
        assert trade.size == Decimal(sample_trade_response.filledsize)


class TestCopyTradingBotErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_bot_handles_copier_errors_gracefully(
        self, mock_ws_client, mock_copier, sample_trade_response
    ):
        """Bot should handle copier errors without crashing."""
        mock_copier.process_trade.side_effect = Exception("Execution error")

        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_trade_callback.call_args[0][0]

        # Should not raise exception
        await callback(sample_trade_response)

        # Trade should still be counted
        stats = bot.get_statistics()
        assert stats["trades_detected"] == 1

    @pytest.mark.asyncio
    async def test_bot_handles_trade_conversion_errors(self, mock_ws_client, mock_copier):
        """Bot should handle errors in trade conversion gracefully."""
        CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_trade_callback.call_args[0][0]

        # Malformed trade response
        bad_trade_response = TradeResponse(
            orderid=12345,
            makeraddress="0x1111111111111111111111111111111111111111",
            takeraddress="0x2222222222222222222222222222222222222222",
            isbuy=True,
            price="invalid_price",  # This will cause conversion error
            filledsize="1.5",
            transactionhash="0x" + "a" * 64,
            triggertime=int(datetime.now(UTC).timestamp()),
        )

        # Should not raise exception
        await callback(bad_trade_response)

        # Trade should not be processed
        mock_copier.process_trade.assert_not_called()


class TestCopyTradingBotStatistics:
    """Test statistics tracking."""

    def test_bot_includes_copier_statistics(self, mock_ws_client, mock_copier):
        """Bot should include copier statistics in get_statistics()."""
        mock_copier.get_statistics.return_value = {
            "successful_trades": 5,
            "failed_trades": 2,
            "rejected_trades": 1,
        }

        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        stats = bot.get_statistics()
        assert stats["successful_trades"] == 5
        assert stats["failed_trades"] == 2
        assert stats["rejected_trades"] == 1
        assert stats["trades_detected"] == 0  # Bot's own stat

    @pytest.mark.asyncio
    async def test_bot_resets_statistics(self, mock_ws_client, mock_copier, sample_trade_response):
        """Bot should reset statistics including copier stats."""
        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_trade_callback.call_args[0][0]
        await callback(sample_trade_response)

        # Reset statistics
        bot.reset_statistics()

        stats = bot.get_statistics()
        assert stats["trades_detected"] == 0
        mock_copier.reset_statistics.assert_called_once()


class TestCopyTradingBotOrderCreatedProcessing:
    """Test OrderCreated event processing."""

    @pytest.mark.asyncio
    async def test_bot_processes_order_from_monitored_wallet(
        self, mock_ws_client, mock_copier, sample_order_response
    ):
        """Bot should process OrderCreated events from monitored source wallets."""
        market_address = "0x4444444444444444444444444444444444444444"
        source_wallet = "0x1111111111111111111111111111111111111111"

        CopyTradingBot(
            ws_clients=[(market_address, mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        # Get the registered callback
        callback = mock_ws_client.set_order_created_callback.call_args[0][0]

        # Simulate OrderCreated event from WebSocket
        await callback(sample_order_response)

        # Should process the order
        mock_copier.process_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_bot_ignores_order_from_unmonitored_wallet(
        self, mock_ws_client, mock_copier, sample_order_response
    ):
        """Bot should ignore OrderCreated events from wallets not in source_wallets."""
        market_address = "0x4444444444444444444444444444444444444444"
        # Source wallet is different from order owner
        source_wallet = "0x9999999999999999999999999999999999999999"

        CopyTradingBot(
            ws_clients=[(market_address, mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        # Get the registered callback
        callback = mock_ws_client.set_order_created_callback.call_args[0][0]

        # Simulate OrderCreated event from unmonitored wallet
        await callback(sample_order_response)

        # Should NOT process the order
        mock_copier.process_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_tracks_orders_detected(
        self, mock_ws_client, mock_copier, sample_order_response
    ):
        """Bot should track number of orders detected."""
        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_order_created_callback.call_args[0][0]

        # Process multiple orders
        await callback(sample_order_response)
        await callback(sample_order_response)

        stats = bot.get_statistics()
        assert stats["orders_detected"] == 2

    @pytest.mark.asyncio
    async def test_bot_tracks_order_mapping(
        self, mock_ws_client, mock_copier, sample_order_response
    ):
        """Bot should track mapping between source and mirrored orders."""
        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_order_created_callback.call_args[0][0]

        # Process order
        await callback(sample_order_response)

        # Should track the mapping
        stats = bot.get_statistics()
        assert stats["tracked_orders"] == 1
        assert sample_order_response.order_id in bot._order_mapping
        assert bot._order_mapping[sample_order_response.order_id] == "order_456"

    @pytest.mark.asyncio
    async def test_bot_handles_order_processing_errors(
        self, mock_ws_client, mock_copier, sample_order_response
    ):
        """Bot should handle order processing errors gracefully."""
        mock_copier.process_order.side_effect = Exception("Processing error")

        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_order_created_callback.call_args[0][0]

        # Should not raise exception
        await callback(sample_order_response)

        # Order should still be counted
        stats = bot.get_statistics()
        assert stats["orders_detected"] == 1

    @pytest.mark.asyncio
    async def test_bot_does_not_track_failed_orders(
        self, mock_ws_client, mock_copier, sample_order_response
    ):
        """Bot should not track orders that failed to mirror."""
        mock_copier.process_order.return_value = None  # Failed

        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        callback = mock_ws_client.set_order_created_callback.call_args[0][0]

        # Process order
        await callback(sample_order_response)

        # Should not track the mapping
        stats = bot.get_statistics()
        assert stats["tracked_orders"] == 0
        assert sample_order_response.order_id not in bot._order_mapping


class TestCopyTradingBotOrdersCanceledProcessing:
    """Test OrdersCanceled event processing."""

    @pytest.mark.asyncio
    async def test_bot_cancels_mirrored_orders(
        self, mock_ws_client, mock_copier, sample_order_response
    ):
        """Bot should cancel mirrored orders when source trader cancels."""
        source_wallet = "0x1111111111111111111111111111111111111111"

        CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        # First, create an order so we have something to cancel
        order_callback = mock_ws_client.set_order_created_callback.call_args[0][0]
        await order_callback(sample_order_response)

        # Now simulate OrdersCanceled event
        cancel_callback = mock_ws_client.set_orders_canceled_callback.call_args[0][0]
        await cancel_callback(
            [sample_order_response.order_id],
            ["test-cloid"],
            source_wallet,
            [{"order_id": sample_order_response.order_id, "reason": "user_cancelled"}],
        )

        # Should have called cancel_orders
        mock_copier.cancel_orders.assert_called_once_with(["order_456"])

    @pytest.mark.asyncio
    async def test_bot_ignores_cancellations_from_unmonitored_wallet(
        self, mock_ws_client, mock_copier
    ):
        """Bot should ignore OrdersCanceled events from wallets not in source_wallets."""
        CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=["0x1111111111111111111111111111111111111111"],
            copier=mock_copier,
        )

        # Simulate OrdersCanceled event from unmonitored wallet
        cancel_callback = mock_ws_client.set_orders_canceled_callback.call_args[0][0]
        await cancel_callback(
            [12345],
            ["cloid-123"],
            "0x9999999999999999999999999999999999999999",
            [{"order_id": 12345, "reason": "user_cancelled"}],
        )

        # Should NOT call cancel_orders
        mock_copier.cancel_orders.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_tracks_cancellations_detected(self, mock_ws_client, mock_copier):
        """Bot should track number of order cancellations detected."""
        source_wallet = "0x1111111111111111111111111111111111111111"

        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        cancel_callback = mock_ws_client.set_orders_canceled_callback.call_args[0][0]

        # Process multiple cancellations
        await cancel_callback(
            [12345, 67890],
            ["cloid-1", "cloid-2"],
            source_wallet,
            [
                {"order_id": 12345, "reason": "user_cancelled"},
                {"order_id": 67890, "reason": "user_cancelled"},
            ],
        )
        await cancel_callback(
            [11111], ["cloid-3"], source_wallet, [{"order_id": 11111, "reason": "user_cancelled"}]
        )

        stats = bot.get_statistics()
        assert stats["orders_canceled_detected"] == 2

    @pytest.mark.asyncio
    async def test_bot_removes_canceled_orders_from_tracking(
        self, mock_ws_client, mock_copier, sample_order_response
    ):
        """Bot should remove canceled orders from tracking map."""
        source_wallet = "0x1111111111111111111111111111111111111111"

        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        # First, create an order
        order_callback = mock_ws_client.set_order_created_callback.call_args[0][0]
        await order_callback(sample_order_response)

        assert bot.get_statistics()["tracked_orders"] == 1

        # Now cancel it
        cancel_callback = mock_ws_client.set_orders_canceled_callback.call_args[0][0]
        await cancel_callback(
            [sample_order_response.order_id],
            ["test-cloid"],
            source_wallet,
            [{"order_id": sample_order_response.order_id, "reason": "user_cancelled"}],
        )

        # Should be removed from tracking
        assert bot.get_statistics()["tracked_orders"] == 0
        assert sample_order_response.order_id not in bot._order_mapping

    @pytest.mark.asyncio
    async def test_bot_handles_cancellation_of_unmapped_orders(self, mock_ws_client, mock_copier):
        """Bot should handle cancellation of orders not in tracking map."""
        source_wallet = "0x1111111111111111111111111111111111111111"

        CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        # Cancel orders that were never mirrored
        cancel_callback = mock_ws_client.set_orders_canceled_callback.call_args[0][0]
        await cancel_callback(
            [99999, 88888],
            ["cloid-999", "cloid-888"],
            source_wallet,
            [
                {"order_id": 99999, "reason": "user_cancelled"},
                {"order_id": 88888, "reason": "user_cancelled"},
            ],
        )

        # Should not call cancel_orders (no orders to cancel)
        mock_copier.cancel_orders.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_handles_batch_cancellations(self, mock_ws_client, mock_copier):
        """Bot should handle cancellation of multiple orders at once."""
        source_wallet = "0x1111111111111111111111111111111111111111"

        bot = CopyTradingBot(
            ws_clients=[("0x4444444444444444444444444444444444444444", mock_ws_client)],
            source_wallets=[source_wallet],
            copier=mock_copier,
        )

        order_callback = mock_ws_client.set_order_created_callback.call_args[0][0]

        # Create multiple orders
        order1 = OrderResponse(
            order_id=100,
            market_address="0x4444444444444444444444444444444444444444",
            owner=source_wallet,
            price="2000.0",
            size="1.0",
            remaining_size="1.0",
            is_buy=True,
            is_canceled=False,
            transaction_hash="0x" + "c" * 64,
            trigger_time=int(datetime.now(UTC).timestamp()),
        )
        order2 = OrderResponse(
            order_id=200,
            market_address="0x4444444444444444444444444444444444444444",
            owner=source_wallet,
            price="2001.0",
            size="2.0",
            remaining_size="2.0",
            is_buy=True,
            is_canceled=False,
            transaction_hash="0x" + "d" * 64,
            trigger_time=int(datetime.now(UTC).timestamp()),
        )

        await order_callback(order1)
        await order_callback(order2)

        assert bot.get_statistics()["tracked_orders"] == 2

        # Cancel both at once
        cancel_callback = mock_ws_client.set_orders_canceled_callback.call_args[0][0]
        await cancel_callback(
            [100, 200],
            ["cloid-100", "cloid-200"],
            source_wallet,
            [
                {"order_id": 100, "reason": "user_cancelled"},
                {"order_id": 200, "reason": "user_cancelled"},
            ],
        )

        # Should have called cancel_orders with both mirrored order IDs
        mock_copier.cancel_orders.assert_called_once()
        call_args = mock_copier.cancel_orders.call_args[0][0]
        assert len(call_args) == 2
        assert "order_456" in call_args

        # Should be removed from tracking
        assert bot.get_statistics()["tracked_orders"] == 0
