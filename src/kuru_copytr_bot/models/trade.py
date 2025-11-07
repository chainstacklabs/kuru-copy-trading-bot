"""Trade model."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from ..core.enums import OrderSide


class Trade(BaseModel):
    """Represents a trade execution."""

    id: str = Field(..., description="Unique trade identifier")
    trader_address: str = Field(..., description="Source trader wallet address")
    market: str = Field(..., description="Trading pair/market (e.g., ETH-USDC)")
    side: OrderSide = Field(..., description="Trade side (BUY or SELL)")
    price: Decimal = Field(..., description="Execution price", gt=0)
    size: Decimal = Field(..., description="Trade size", gt=0)
    timestamp: datetime = Field(..., description="Trade execution time")
    tx_hash: str = Field(..., description="Transaction hash")

    @field_validator("trader_address")
    @classmethod
    def validate_trader_address(cls, v: str) -> str:
        """Validate Ethereum address format."""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format")
        return v

    @field_validator("tx_hash")
    @classmethod
    def validate_tx_hash(cls, v: str) -> str:
        """Validate transaction hash format."""
        if not v.startswith("0x") or len(v) != 66:
            raise ValueError("Invalid transaction hash format")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        if v.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")
        return v

    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value (price * size)."""
        return self.price * self.size

    def __str__(self) -> str:
        """String representation of trade."""
        return f"Trade({self.id}, {self.market}, {self.side.value}, {self.size}@{self.price})"
