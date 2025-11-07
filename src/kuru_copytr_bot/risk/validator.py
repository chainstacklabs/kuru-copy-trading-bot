"""Trade validation for risk management."""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from src.kuru_copytr_bot.models.trade import Trade
from src.kuru_copytr_bot.core.enums import OrderSide


@dataclass
class ValidationResult:
    """Result of trade validation."""

    is_valid: bool
    reason: Optional[str] = None


class TradeValidator:
    """Validate trades against risk management rules."""

    def __init__(
        self,
        min_balance: Optional[Decimal] = None,
        max_position_size: Optional[Decimal] = None,
        min_order_size: Optional[Decimal] = None,
        market_whitelist: Optional[List[str]] = None,
        market_blacklist: Optional[List[str]] = None,
        max_exposure_usd: Optional[Decimal] = None,
    ):
        """Initialize trade validator.

        Args:
            min_balance: Minimum balance required
            max_position_size: Maximum position size allowed
            min_order_size: Minimum order size allowed
            market_whitelist: List of allowed markets (if set, only these markets allowed)
            market_blacklist: List of disallowed markets
            max_exposure_usd: Maximum total exposure in USD
        """
        self.min_balance = min_balance
        self.max_position_size = max_position_size
        self.min_order_size = min_order_size
        self.market_whitelist = market_whitelist
        self.market_blacklist = market_blacklist
        self.max_exposure_usd = max_exposure_usd

    def validate(
        self,
        trade: Trade,
        current_balance: Decimal,
        current_position: Decimal,
    ) -> ValidationResult:
        """Validate a trade against all configured rules.

        Args:
            trade: Trade to validate
            current_balance: Current available balance
            current_position: Current position size (positive for long, negative for short)

        Returns:
            ValidationResult: Validation result with reason if invalid
        """
        # Check 1: Minimum balance
        if self.min_balance is not None:
            if current_balance < self.min_balance:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Insufficient balance: {current_balance} < minimum {self.min_balance}"
                )

        # Check 2: Balance covers trade cost
        trade_cost = trade.notional_value  # price * size
        if current_balance < trade_cost:
            return ValidationResult(
                is_valid=False,
                reason=f"Insufficient balance for trade: {current_balance} < {trade_cost}"
            )

        # Check 3: Minimum order size
        if self.min_order_size is not None:
            if trade.size < self.min_order_size:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Order size {trade.size} below minimum {self.min_order_size}"
                )

        # Check 4: Market whitelist (takes precedence over blacklist)
        if self.market_whitelist is not None:
            if trade.market not in self.market_whitelist:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Market {trade.market} not in whitelist"
                )

        # Check 5: Market blacklist (if no whitelist)
        elif self.market_blacklist is not None:
            if trade.market in self.market_blacklist:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Market {trade.market} is blacklisted"
                )

        # Check 6: Maximum position size
        if self.max_position_size is not None:
            # Calculate new position after trade
            if trade.side == OrderSide.BUY:
                new_position = current_position + trade.size
            else:  # SELL
                new_position = current_position - trade.size

            # Check if absolute position size exceeds limit
            if abs(new_position) > self.max_position_size:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Position size would exceed limit: {abs(new_position)} > {self.max_position_size}"
                )

        # Check 7: Maximum exposure
        if self.max_exposure_usd is not None:
            # Calculate current exposure
            current_exposure = abs(current_position * trade.price)

            # Calculate new exposure after trade
            if trade.side == OrderSide.BUY:
                new_position = current_position + trade.size
            else:
                new_position = current_position - trade.size

            new_exposure = abs(new_position * trade.price)

            if new_exposure > self.max_exposure_usd:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Exposure would exceed limit: {new_exposure} > {self.max_exposure_usd}"
                )

        # All checks passed
        return ValidationResult(is_valid=True, reason=None)
