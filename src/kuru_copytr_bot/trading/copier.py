"""Trade copier for executing mirror trades."""

from decimal import Decimal

from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient
from src.kuru_copytr_bot.core.enums import OrderType
from src.kuru_copytr_bot.core.exceptions import (
    InsufficientBalanceError,
    InvalidOrderError,
    OrderPlacementError,
)
from src.kuru_copytr_bot.models.order import Order
from src.kuru_copytr_bot.models.trade import Trade
from src.kuru_copytr_bot.risk.calculator import PositionSizeCalculator
from src.kuru_copytr_bot.risk.validator import TradeValidator
from src.kuru_copytr_bot.trading.order_tracker import OrderTracker
from src.kuru_copytr_bot.utils.logger import get_logger

logger = get_logger(__name__)


class TradeCopier:
    """Copies trades from source wallets with risk management."""

    def __init__(
        self,
        kuru_client: KuruClient,
        calculator: PositionSizeCalculator,
        validator: TradeValidator,
        order_tracker: OrderTracker | None = None,
        default_order_type: OrderType = OrderType.LIMIT,
    ):
        """Initialize trade copier.

        Args:
            kuru_client: Kuru Exchange client for order execution
            calculator: Position size calculator
            validator: Trade validator
            order_tracker: Optional order tracker for fill tracking
            default_order_type: Default order type (LIMIT or MARKET)
        """
        self.kuru_client = kuru_client
        self.calculator = calculator
        self.validator = validator
        self.order_tracker = order_tracker or OrderTracker()
        self.default_order_type = default_order_type

        # Statistics tracking
        self._successful_trades = 0
        self._failed_trades = 0
        self._rejected_trades = 0
        self._successful_orders = 0
        self._failed_orders = 0
        self._rejected_orders = 0
        self._orders_canceled = 0

    def process_trade(self, trade: Trade) -> str | None:
        """Process a single trade from source wallet.

        Args:
            trade: Trade detected from source wallet

        Returns:
            Order ID if successful, None otherwise
        """
        logger.info(
            "Processing trade for copying",
            trade_id=trade.id,
            market=trade.market,
            side=trade.side.value,
            size=str(trade.size),
            price=str(trade.price),
        )

        try:
            # Step 1: Get current margin balance
            balance = self.kuru_client.get_margin_balance(None)
            logger.debug("Retrieved margin balance", balance=str(balance))

            # Step 2: Calculate position size
            calculated_size = self.calculator.calculate(
                source_size=trade.size,
                available_balance=balance,
                price=trade.price,
            )

            logger.debug(
                "Calculated position size",
                source_size=str(trade.size),
                calculated_size=str(calculated_size),
            )

            # Skip if calculated size is zero
            if calculated_size == 0:
                logger.info("Calculated size is zero, skipping trade", trade_id=trade.id)
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
            )

            if not validation_result.is_valid:
                self._rejected_trades += 1
                logger.warning(
                    "Trade validation failed, rejecting",
                    trade_id=trade.id,
                    reason=validation_result.reason,
                )
                return None

            logger.info(
                "Executing mirror trade",
                market=mirror_trade.market,
                side=mirror_trade.side.value,
                size=str(mirror_trade.size),
                price=str(mirror_trade.price),
                order_type=self.default_order_type.value,
            )

            # Step 6: Execute order
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

            self.order_tracker.register_order(order_id=order_id, size=calculated_size)

            self._successful_trades += 1
            logger.info(
                "Successfully executed mirror trade",
                trade_id=trade.id,
                order_id=order_id,
            )
            return order_id

        except InsufficientBalanceError as e:
            self._failed_trades += 1
            logger.error(
                "Insufficient balance for trade",
                trade_id=trade.id,
                error=str(e),
            )
            return None
        except InvalidOrderError as e:
            self._failed_trades += 1
            logger.error(
                "Invalid order parameters",
                trade_id=trade.id,
                error=str(e),
            )
            return None
        except OrderPlacementError as e:
            self._failed_trades += 1
            logger.error(
                "Order placement failed",
                trade_id=trade.id,
                error=str(e),
            )
            return None
        except Exception as e:
            self._failed_trades += 1
            logger.error(
                "Unexpected error processing trade",
                trade_id=trade.id,
                error=str(e),
                exc_info=True,
            )
            return None

    def process_trades(self, trades: list[Trade]) -> list[str]:
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

    def process_order(self, order: Order) -> str | None:
        """Process a limit order from source wallet.

        Args:
            order: Order detected from source wallet

        Returns:
            Order ID if successful, None otherwise
        """
        logger.info(
            "Processing order for copying",
            order_id=order.order_id,
            market=order.market,
            side=order.side.value,
            size=str(order.size),
            price=str(order.price),
        )

        try:
            # Step 1: Get current margin balance
            balance = self.kuru_client.get_margin_balance(None)
            logger.debug("Retrieved margin balance", balance=str(balance))

            # Step 2: Calculate position size
            calculated_size = self.calculator.calculate(
                source_size=order.size,
                available_balance=balance,
                price=order.price,
            )

            logger.debug(
                "Calculated position size",
                source_size=str(order.size),
                calculated_size=str(calculated_size),
            )

            # Skip if calculated size is zero
            if calculated_size == 0:
                logger.info("Calculated size is zero, skipping order", order_id=order.order_id)
                return None

            # Step 3: Create mirror order for validation
            # Create a temporary Order object with calculated size
            from src.kuru_copytr_bot.core.enums import OrderStatus, OrderType

            mirror_order = Order(
                order_id=f"mirror_{order.order_id}",
                order_type=OrderType.LIMIT,
                status=OrderStatus.PENDING,
                side=order.side,
                price=order.price,
                size=calculated_size,
                filled_size=Decimal("0"),
                market=order.market,
                created_at=order.created_at,
                updated_at=order.created_at,
            )

            # Step 4: Validate order
            validation_result = self.validator.validate_order(
                order=mirror_order,
                current_balance=balance,
            )

            if not validation_result.is_valid:
                self._rejected_orders += 1
                logger.warning(
                    "Order validation failed, rejecting",
                    order_id=order.order_id,
                    reason=validation_result.reason,
                )
                return None

            logger.info(
                "Executing mirror order",
                market=order.market,
                side=order.side.value,
                size=str(calculated_size),
                price=str(order.price),
            )

            # Step 5: Place limit order
            order_id = self.kuru_client.place_limit_order(
                market=order.market,
                side=order.side,
                size=calculated_size,
                price=order.price,
                post_only=True,  # Mirror orders should be post-only to match source
            )

            self.order_tracker.register_order(order_id=order_id, size=calculated_size)

            self._successful_orders += 1
            logger.info(
                "Successfully executed mirror order",
                source_order_id=order.order_id,
                order_id=order_id,
            )
            return order_id

        except InsufficientBalanceError as e:
            self._failed_orders += 1
            logger.error(
                "Insufficient balance for order",
                order_id=order.order_id,
                error=str(e),
            )
            return None
        except InvalidOrderError as e:
            self._failed_orders += 1
            logger.error(
                "Invalid order parameters",
                order_id=order.order_id,
                error=str(e),
            )
            return None
        except OrderPlacementError as e:
            self._failed_orders += 1
            logger.error(
                "Order placement failed",
                order_id=order.order_id,
                error=str(e),
            )
            return None
        except Exception as e:
            self._failed_orders += 1
            logger.error(
                "Unexpected error processing order",
                order_id=order.order_id,
                error=str(e),
                exc_info=True,
            )
            return None

    def cancel_orders(self, order_ids: list[str], market_address: str) -> bool:
        """Cancel multiple orders.

        Args:
            order_ids: List of order IDs to cancel
            market_address: Market contract address where orders were placed

        Returns:
            True if successful, False otherwise
        """
        if not order_ids:
            logger.debug("No orders to cancel")
            return True

        logger.info(
            "Canceling orders",
            order_count=len(order_ids),
            order_ids=order_ids,
            market=market_address,
        )

        try:
            # Use batch cancel for efficiency
            tx_hash = self.kuru_client.cancel_orders(order_ids, market_address)

            self._orders_canceled += len(order_ids)
            logger.info(
                "Successfully canceled orders",
                order_count=len(order_ids),
                tx_hash=tx_hash,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to cancel orders",
                error=str(e),
                order_ids=order_ids,
                exc_info=True,
            )
            return False

    def get_statistics(self) -> dict[str, int]:
        """Get trade and order statistics.

        Returns:
            Dictionary with successful, failed, and rejected counts
        """
        return {
            "successful_trades": self._successful_trades,
            "failed_trades": self._failed_trades,
            "rejected_trades": self._rejected_trades,
            "successful_orders": self._successful_orders,
            "failed_orders": self._failed_orders,
            "rejected_orders": self._rejected_orders,
            "orders_canceled": self._orders_canceled,
        }

    def reset_statistics(self) -> None:
        """Reset trade and order statistics."""
        self._successful_trades = 0
        self._failed_trades = 0
        self._rejected_trades = 0
        self._successful_orders = 0
        self._failed_orders = 0
        self._rejected_orders = 0
        self._orders_canceled = 0
