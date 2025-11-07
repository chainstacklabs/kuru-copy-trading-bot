"""Order model."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from pydantic_core import ValidationError as CoreValidationError, InitErrorDetails

from ..core.enums import OrderSide, OrderType, OrderStatus
from ..core.exceptions import InvalidStateTransition


class Order(BaseModel):
    """Represents an order."""

    order_id: str = Field(..., description="Unique order identifier")
    order_type: OrderType = Field(..., description="Order type (LIMIT, MARKET, etc.)")
    status: OrderStatus = Field(..., description="Order status")
    side: OrderSide = Field(..., description="Order side (BUY or SELL)")
    price: Optional[Decimal] = Field(None, description="Order price (None for market orders)")
    size: Decimal = Field(..., description="Order size", gt=0)
    filled_size: Decimal = Field(..., description="Amount filled so far", ge=0)
    market: str = Field(..., description="Trading pair/market")
    created_at: datetime = Field(..., description="Order creation time")
    updated_at: datetime = Field(..., description="Last update time")

    @model_validator(mode="after")
    def validate_order(self) -> "Order":
        """Validate order constraints."""
        # Limit orders must have a price
        if self.order_type in (OrderType.LIMIT, OrderType.GTC) and self.price is None:
            raise ValueError("Limit orders must have a price")

        # Filled size cannot exceed total size
        if self.filled_size > self.size:
            raise ValueError("Filled size cannot exceed total size")

        return self

    @property
    def remaining_size(self) -> Decimal:
        """Calculate remaining unfilled size."""
        return self.size - self.filled_size

    @property
    def fill_percentage(self) -> Decimal:
        """Calculate fill percentage."""
        if self.size == 0:
            return Decimal("0")
        return (self.filled_size / self.size) * Decimal("100")

    @property
    def is_fully_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.filled_size >= self.size

    @property
    def is_active(self) -> bool:
        """Check if order is active (can still be filled or cancelled)."""
        return self.status in (OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED)

    def transition_to(self, new_status: OrderStatus) -> None:
        """Transition order to a new status."""
        # Define valid transitions
        valid_transitions = {
            OrderStatus.PENDING: {OrderStatus.OPEN, OrderStatus.FAILED, OrderStatus.CANCELLED},
            OrderStatus.OPEN: {OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED, OrderStatus.CANCELLED},
            OrderStatus.PARTIALLY_FILLED: {OrderStatus.FILLED, OrderStatus.CANCELLED},
            OrderStatus.FILLED: set(),  # Terminal state
            OrderStatus.CANCELLED: set(),  # Terminal state
            OrderStatus.FAILED: set(),  # Terminal state
        }

        if new_status not in valid_transitions.get(self.status, set()):
            raise InvalidStateTransition(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )

        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def add_fill(self, fill_size: Decimal) -> None:
        """Add a fill to the order."""
        new_filled_size = self.filled_size + fill_size

        if new_filled_size > self.size:
            # Raise pydantic ValidationError
            raise CoreValidationError.from_exception_data(
                "Order",
                [
                    InitErrorDetails(
                        type="value_error",
                        loc=("filled_size",),
                        input=new_filled_size,
                        ctx={"error": f"Fill would exceed order size: {new_filled_size} > {self.size}"},
                    )
                ],
            )

        self.filled_size = new_filled_size
        self.updated_at = datetime.now(timezone.utc)

        # Update status based on fill
        if self.is_fully_filled:
            self.status = OrderStatus.FILLED
        elif self.filled_size > 0 and self.status == OrderStatus.OPEN:
            self.status = OrderStatus.PARTIALLY_FILLED
