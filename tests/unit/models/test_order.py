"""Tests for Order model."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

# These imports will fail initially - that's expected for TDD
from src.kuru_copytr_bot.models.order import Order
from src.kuru_copytr_bot.core.enums import OrderSide, OrderType, OrderStatus
from src.kuru_copytr_bot.core.exceptions import InvalidStateTransition
from pydantic import ValidationError


class TestOrderModel:
    """Test Order model creation and validation."""

    def test_order_creation_with_valid_data(self):
        """Order model should accept valid data."""
        order = Order(
            order_id="order_001",
            order_type=OrderType.LIMIT,
            status=OrderStatus.PENDING,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.5"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert order.order_id == "order_001"
        assert order.order_type == OrderType.LIMIT
        assert order.status == OrderStatus.PENDING
        assert order.side == OrderSide.BUY
        assert order.price == Decimal("2000.00")
        assert order.size == Decimal("1.5")
        assert order.filled_size == Decimal("0")

    def test_order_creation_market_order(self):
        """Order model should handle market orders (no price)."""
        order = Order(
            order_id="order_002",
            order_type=OrderType.MARKET,
            status=OrderStatus.PENDING,
            side=OrderSide.SELL,
            price=None,  # Market orders have no price
            size=Decimal("1.0"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert order.order_type == OrderType.MARKET
        assert order.price is None

    def test_order_requires_price_for_limit_orders(self):
        """Limit orders must have a price."""
        with pytest.raises(ValidationError):
            Order(
                order_id="order_003",
                order_type=OrderType.LIMIT,
                status=OrderStatus.PENDING,
                side=OrderSide.BUY,
                price=None,  # Invalid for limit orders
                size=Decimal("1.0"),
                filled_size=Decimal("0"),
                market="ETH-USDC",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    def test_order_status_transition_pending_to_open(self):
        """Order should transition from PENDING to OPEN."""
        order = Order(
            order_id="order_004",
            order_type=OrderType.LIMIT,
            status=OrderStatus.PENDING,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        order.transition_to(OrderStatus.OPEN)
        assert order.status == OrderStatus.OPEN

    def test_order_status_transition_open_to_filled(self):
        """Order should transition from OPEN to FILLED."""
        order = Order(
            order_id="order_005",
            order_type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("1.0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        order.transition_to(OrderStatus.FILLED)
        assert order.status == OrderStatus.FILLED

    def test_order_cannot_transition_from_filled_to_cancelled(self):
        """Filled orders cannot be cancelled."""
        order = Order(
            order_id="order_006",
            order_type=OrderType.LIMIT,
            status=OrderStatus.FILLED,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("1.0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(InvalidStateTransition):
            order.transition_to(OrderStatus.CANCELLED)

    def test_order_cannot_transition_from_cancelled_to_open(self):
        """Cancelled orders cannot be reopened."""
        order = Order(
            order_id="order_007",
            order_type=OrderType.LIMIT,
            status=OrderStatus.CANCELLED,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(InvalidStateTransition):
            order.transition_to(OrderStatus.OPEN)

    def test_order_partial_fill_updates_filled_size(self):
        """Order should track partial fills."""
        order = Order(
            order_id="order_008",
            order_type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("2.0"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        order.add_fill(Decimal("0.5"))
        assert order.filled_size == Decimal("0.5")
        assert order.status == OrderStatus.PARTIALLY_FILLED

        order.add_fill(Decimal("0.3"))
        assert order.filled_size == Decimal("0.8")
        assert order.status == OrderStatus.PARTIALLY_FILLED

    def test_order_fully_filled_updates_status(self):
        """Order should update status to FILLED when fully filled."""
        order = Order(
            order_id="order_009",
            order_type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        order.add_fill(Decimal("1.0"))
        assert order.filled_size == Decimal("1.0")
        assert order.status == OrderStatus.FILLED
        assert order.is_fully_filled

    def test_order_cannot_overfill(self):
        """Order should reject fills that exceed size."""
        order = Order(
            order_id="order_010",
            order_type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(ValidationError):
            order.add_fill(Decimal("1.5"))

    def test_order_remaining_size_calculation(self):
        """Order should calculate remaining size correctly."""
        order = Order(
            order_id="order_011",
            order_type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("2.0"),
            filled_size=Decimal("0.7"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert order.remaining_size == Decimal("1.3")

    def test_order_fill_percentage_calculation(self):
        """Order should calculate fill percentage."""
        order = Order(
            order_id="order_012",
            order_type=OrderType.LIMIT,
            status=OrderStatus.PARTIALLY_FILLED,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("2.0"),
            filled_size=Decimal("1.0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert order.fill_percentage == Decimal("50.0")

    def test_order_is_active_property(self):
        """Order should report if it's active."""
        order_open = Order(
            order_id="order_013",
            order_type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        order_filled = Order(
            order_id="order_014",
            order_type=OrderType.LIMIT,
            status=OrderStatus.FILLED,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("1.0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert order_open.is_active is True
        assert order_filled.is_active is False

    def test_order_uses_decimal_for_amounts(self):
        """Order should use Decimal for all amounts."""
        order = Order(
            order_id="order_015",
            order_type=OrderType.LIMIT,
            status=OrderStatus.OPEN,
            side=OrderSide.BUY,
            price=Decimal("2000.00"),
            size=Decimal("1.0"),
            filled_size=Decimal("0"),
            market="ETH-USDC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert isinstance(order.price, Decimal)
        assert isinstance(order.size, Decimal)
        assert isinstance(order.filled_size, Decimal)
