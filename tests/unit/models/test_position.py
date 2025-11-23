"""Tests for Position model."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

# These imports will fail initially - that's expected for TDD
from src.kuru_copytr_bot.models.position import Position


class TestPositionModel:
    """Test Position model creation and calculations."""

    def test_position_creation_long(self):
        """Position should be created for long position."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),  # Positive = long
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2000.00"),
            margin_used=Decimal("5000.00"),
        )

        assert position.market == "ETH-USDC"
        assert position.size == Decimal("10.0")
        assert position.entry_price == Decimal("2000.00")
        assert position.is_long is True
        assert position.is_short is False

    def test_position_creation_short(self):
        """Position should be created for short position."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("-10.0"),  # Negative = short
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2000.00"),
            margin_used=Decimal("5000.00"),
        )

        assert position.size == Decimal("-10.0")
        assert position.is_long is False
        assert position.is_short is True

    def test_position_pnl_calculation_long_profit(self):
        """Position should calculate PnL correctly for long profit."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2100.00"),
            margin_used=Decimal("5000.00"),
        )

        # PnL = size * (current_price - entry_price)
        # PnL = 10 * (2100 - 2000) = 1000
        expected_pnl = Decimal("1000.00")
        assert position.unrealized_pnl == expected_pnl

    def test_position_pnl_calculation_long_loss(self):
        """Position should calculate PnL correctly for long loss."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("1900.00"),
            margin_used=Decimal("5000.00"),
        )

        # PnL = 10 * (1900 - 2000) = -1000
        expected_pnl = Decimal("-1000.00")
        assert position.unrealized_pnl == expected_pnl

    def test_position_pnl_calculation_short_profit(self):
        """Position should calculate PnL correctly for short profit."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("-10.0"),  # Short position
            entry_price=Decimal("2000.00"),
            current_price=Decimal("1900.00"),  # Price went down = profit
            margin_used=Decimal("5000.00"),
        )

        # PnL = -10 * (1900 - 2000) = 1000
        expected_pnl = Decimal("1000.00")
        assert position.unrealized_pnl == expected_pnl

    def test_position_pnl_calculation_short_loss(self):
        """Position should calculate PnL correctly for short loss."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("-10.0"),  # Short position
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2100.00"),  # Price went up = loss
            margin_used=Decimal("5000.00"),
        )

        # PnL = -10 * (2100 - 2000) = -1000
        expected_pnl = Decimal("-1000.00")
        assert position.unrealized_pnl == expected_pnl

    def test_position_update_current_price(self):
        """Position should update current price and recalculate PnL."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2000.00"),
            margin_used=Decimal("5000.00"),
        )

        position.update_price(Decimal("2200.00"))
        assert position.current_price == Decimal("2200.00")
        assert position.unrealized_pnl == Decimal("2000.00")

    def test_position_add_to_long_position(self):
        """Position should correctly add to existing long position."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2000.00"),
            margin_used=Decimal("5000.00"),
        )

        # Add 5 more at 2100
        position.add(size=Decimal("5.0"), price=Decimal("2100.00"))

        # New average entry: (10*2000 + 5*2100) / 15 = 30500 / 15 = 2033.33...
        assert position.size == Decimal("15.0")
        expected_avg = (
            Decimal("10.0") * Decimal("2000.00") + Decimal("5.0") * Decimal("2100.00")
        ) / Decimal("15.0")
        assert position.entry_price == expected_avg

    def test_position_add_to_short_position(self):
        """Position should correctly add to existing short position."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("-10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2000.00"),
            margin_used=Decimal("5000.00"),
        )

        # Add 5 more shorts at 1900
        position.add(size=Decimal("-5.0"), price=Decimal("1900.00"))

        assert position.size == Decimal("-15.0")
        # Average: (-10*2000 + -5*1900) / -15 = -29500 / -15 = 1966.67
        expected_avg = (
            Decimal("-10.0") * Decimal("2000.00") + Decimal("-5.0") * Decimal("1900.00")
        ) / Decimal("-15.0")
        assert position.entry_price == expected_avg

    def test_position_reduce_long_position(self):
        """Position should correctly reduce long position."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2100.00"),
            margin_used=Decimal("5000.00"),
        )

        # Close 4 units at 2100
        realized_pnl = position.reduce(size=Decimal("4.0"), price=Decimal("2100.00"))

        assert position.size == Decimal("6.0")
        assert position.entry_price == Decimal("2000.00")  # Entry price doesn't change
        # Realized PnL = 4 * (2100 - 2000) = 400
        assert realized_pnl == Decimal("400.00")

    def test_position_close_completely(self):
        """Position should handle complete closure."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2050.00"),
            margin_used=Decimal("5000.00"),
        )

        realized_pnl = position.close(price=Decimal("2050.00"))

        assert position.size == Decimal("0")
        assert position.is_closed is True
        # Realized PnL = 10 * (2050 - 2000) = 500
        assert realized_pnl == Decimal("500.00")

    def test_position_cannot_reduce_more_than_size(self):
        """Position should reject reduction larger than position size."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2000.00"),
            margin_used=Decimal("5000.00"),
        )

        with pytest.raises(ValidationError):
            position.reduce(size=Decimal("15.0"), price=Decimal("2100.00"))

    def test_position_notional_value(self):
        """Position should calculate notional value."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2100.00"),
            margin_used=Decimal("5000.00"),
        )

        # Notional = abs(size) * current_price = 10 * 2100 = 21000
        assert position.notional_value == Decimal("21000.00")

    def test_position_pnl_percentage(self):
        """Position should calculate PnL percentage."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2200.00"),
            margin_used=Decimal("5000.00"),
        )

        # PnL% = ((current - entry) / entry) * 100 = ((2200 - 2000) / 2000) * 100 = 10%
        assert position.pnl_percentage == Decimal("10.0")

    def test_position_leverage_calculation(self):
        """Position should calculate leverage."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2000.00"),
            margin_used=Decimal("5000.00"),
        )

        # Leverage = notional / margin = (10 * 2000) / 5000 = 4x
        assert position.leverage == Decimal("4.0")

    def test_position_uses_decimal_for_all_amounts(self):
        """Position should use Decimal for all amounts."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("10.0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2100.00"),
            margin_used=Decimal("5000.00"),
        )

        assert isinstance(position.size, Decimal)
        assert isinstance(position.entry_price, Decimal)
        assert isinstance(position.current_price, Decimal)
        assert isinstance(position.margin_used, Decimal)
        assert isinstance(position.unrealized_pnl, Decimal)

    def test_position_zero_size_is_closed(self):
        """Position with zero size should be considered closed."""
        position = Position(
            market="ETH-USDC",
            size=Decimal("0"),
            entry_price=Decimal("2000.00"),
            current_price=Decimal("2000.00"),
            margin_used=Decimal("0"),
        )

        assert position.is_closed is True
        assert position.is_long is False
        assert position.is_short is False
