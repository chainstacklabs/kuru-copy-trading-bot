"""Position model."""

from decimal import Decimal

from pydantic import BaseModel, Field
from pydantic_core import InitErrorDetails
from pydantic_core import ValidationError as CoreValidationError


class Position(BaseModel):
    """Represents a trading position."""

    market: str = Field(..., description="Trading pair/market")
    size: Decimal = Field(..., description="Position size (positive=long, negative=short)")
    entry_price: Decimal = Field(..., description="Average entry price", gt=0)
    current_price: Decimal = Field(..., description="Current market price", gt=0)
    margin_used: Decimal = Field(..., description="Margin allocated to position", ge=0)

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.size > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.size < 0

    @property
    def is_closed(self) -> bool:
        """Check if position is closed."""
        return self.size == 0

    @property
    def unrealized_pnl(self) -> Decimal:
        """Calculate unrealized PnL."""
        return self.size * (self.current_price - self.entry_price)

    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value of position."""
        return abs(self.size) * self.current_price

    @property
    def pnl_percentage(self) -> Decimal:
        """Calculate PnL as percentage of entry."""
        if self.entry_price == 0:
            return Decimal("0")
        return ((self.current_price - self.entry_price) / self.entry_price) * Decimal("100")

    @property
    def leverage(self) -> Decimal:
        """Calculate leverage (notional / margin)."""
        if self.margin_used == 0:
            return Decimal("0")
        return self.notional_value / self.margin_used

    def update_price(self, new_price: Decimal) -> None:
        """Update current price."""
        self.current_price = new_price

    def add(self, size: Decimal, price: Decimal) -> None:
        """Add to position (increases position size and updates average entry)."""
        # Calculate new average entry price
        if self.size == 0:
            # Starting fresh position
            self.size = size
            self.entry_price = price
        else:
            # Adding to existing position
            # New average = (old_size * old_price + new_size * new_price) / (old_size + new_size)
            total_cost = (self.size * self.entry_price) + (size * price)
            new_size = self.size + size
            if new_size != 0:
                self.entry_price = total_cost / new_size
            self.size = new_size

    def reduce(self, size: Decimal, price: Decimal) -> Decimal:
        """Reduce position size and return realized PnL."""
        if abs(size) > abs(self.size):
            raise CoreValidationError.from_exception_data(
                "Position",
                [
                    InitErrorDetails(
                        type="value_error",
                        loc=("size",),
                        input=size,
                        ctx={
                            "error": f"Cannot reduce by {size}, position size is only {self.size}"
                        },
                    )
                ],
            )

        # Calculate realized PnL on the reduced portion
        realized_pnl = size * (price - self.entry_price)

        # Reduce position size (entry price stays same)
        self.size -= size

        return realized_pnl

    def close(self, price: Decimal) -> Decimal:
        """Close entire position and return realized PnL."""
        realized_pnl = self.size * (price - self.entry_price)
        self.size = Decimal("0")
        self.margin_used = Decimal("0")
        return realized_pnl
