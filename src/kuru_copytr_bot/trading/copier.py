"""Trade copier for executing mirror trades."""

from decimal import Decimal
from typing import List, Optional, Dict, Any

from src.kuru_copytr_bot.models.trade import Trade
from src.kuru_copytr_bot.core.enums import OrderType
from src.kuru_copytr_bot.core.exceptions import (
    InsufficientBalanceError,
    InvalidOrderError,
    OrderPlacementError,
)
from src.kuru_copytr_bot.risk.calculator import PositionSizeCalculator
from src.kuru_copytr_bot.risk.validator import TradeValidator
from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient


class TradeCopier:
    """Copies trades from source wallets with risk management."""

    def __init__(
        self,
        kuru_client: KuruClient,
        calculator: PositionSizeCalculator,
        validator: TradeValidator,
        default_order_type: OrderType = OrderType.LIMIT,
    ):
        """Initialize trade copier.

        Args:
            kuru_client: Kuru Exchange client for order execution
            calculator: Position size calculator
            validator: Trade validator
            default_order_type: Default order type (LIMIT or MARKET)
        """
        self.kuru_client = kuru_client
        self.calculator = calculator
        self.validator = validator
        self.default_order_type = default_order_type

        # Statistics tracking
        self._successful_trades = 0
        self._failed_trades = 0
        self._rejected_trades = 0

    def process_trade(self, trade: Trade) -> Optional[str]:
        """Process a single trade from source wallet.

        Args:
            trade: Trade detected from source wallet

        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Step 1: Get current balance
            balance = self.kuru_client.get_balance()

            # Step 2: Calculate position size
            calculated_size = self.calculator.calculate(
                source_size=trade.size,
                available_balance=balance,
                price=trade.price,
            )

            # Skip if calculated size is zero
            if calculated_size == 0:
                return None

            # Step 3: Create mirror trade with calculated size
            mirror_trade = Trade(
                id=f"mirror_{trade.id}",
                trader_address=trade.trader_address,
                market=trade.market,
                side=trade.side,
                price=trade.price,
                size=calculated_size,
                timestamp=trade.timestamp,
                tx_hash=trade.tx_hash,
            )

            # Step 4: Validate trade
            validation_result = self.validator.validate(
                trade=mirror_trade,
                current_balance=balance,
                current_position=Decimal("0"),  # TODO: Get actual position
            )

            if not validation_result.is_valid:
                self._rejected_trades += 1
                return None

            # Step 5: Execute order
            if self.default_order_type == OrderType.LIMIT:
                order_id = self.kuru_client.place_limit_order(
                    market=trade.market,
                    side=trade.side,
                    size=calculated_size,
                    price=trade.price,
                )
            else:  # MARKET
                order_id = self.kuru_client.place_market_order(
                    market=trade.market,
                    side=trade.side,
                    size=calculated_size,
                )

            self._successful_trades += 1
            return order_id

        except (InsufficientBalanceError, InvalidOrderError, OrderPlacementError):
            # Known trading errors
            self._failed_trades += 1
            return None
        except Exception:
            # Unexpected errors (e.g., balance check failure)
            self._failed_trades += 1
            return None

    def process_trades(self, trades: List[Trade]) -> List[str]:
        """Process multiple trades in batch.

        Args:
            trades: List of trades to process

        Returns:
            List of order IDs for successful trades
        """
        order_ids = []

        for trade in trades:
            order_id = self.process_trade(trade)
            if order_id is not None:
                order_ids.append(order_id)

        return order_ids

    def get_statistics(self) -> Dict[str, int]:
        """Get trade statistics.

        Returns:
            Dictionary with successful, failed, and rejected trade counts
        """
        return {
            "successful_trades": self._successful_trades,
            "failed_trades": self._failed_trades,
            "rejected_trades": self._rejected_trades,
        }

    def reset_statistics(self) -> None:
        """Reset trade statistics."""
        self._successful_trades = 0
        self._failed_trades = 0
        self._rejected_trades = 0
