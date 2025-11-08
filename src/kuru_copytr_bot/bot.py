"""Copy trading bot orchestrator."""

from typing import Dict, Any

from src.kuru_copytr_bot.monitoring.monitor import WalletMonitor
from src.kuru_copytr_bot.monitoring.detector import KuruEventDetector
from src.kuru_copytr_bot.trading.copier import TradeCopier
from src.kuru_copytr_bot.core.exceptions import BlockchainConnectionError
from src.kuru_copytr_bot.utils.logger import get_logger

logger = get_logger(__name__)


class CopyTradingBot:
    """Orchestrates copy trading workflow by coordinating all components."""

    def __init__(
        self,
        monitor: WalletMonitor,
        detector: KuruEventDetector,
        copier: TradeCopier,
        poll_interval: int = 5,
    ):
        """Initialize copy trading bot.

        Args:
            monitor: Wallet monitor for detecting transactions
            detector: Event detector for parsing blockchain events
            copier: Trade copier for executing mirror trades
            poll_interval: Polling interval in seconds (default: 5)
        """
        self.monitor = monitor
        self.detector = detector
        self.copier = copier
        self.poll_interval = poll_interval

        # Running state
        self.is_running = False

        # Statistics
        self._transactions_processed = 0
        self._trades_detected = 0

    def start(self) -> None:
        """Start the copy trading bot."""
        logger.info("Starting copy trading bot", poll_interval=self.poll_interval)
        self.monitor.start()
        self.is_running = True
        logger.info("Copy trading bot started successfully")

    def stop(self) -> None:
        """Stop the copy trading bot."""
        logger.info("Stopping copy trading bot")
        self.monitor.stop()
        self.is_running = False
        logger.info("Copy trading bot stopped")

    def process_once(self) -> None:
        """Process one iteration of monitoring and copying.

        This method:
        1. Gets new transactions from wallet monitor
        2. Parses events from transactions
        3. Executes mirror trades for detected trades
        """
        try:
            # Step 1: Get new transactions from target wallets
            transactions = self.monitor.get_new_transactions()

            if transactions:
                logger.debug(
                    "Retrieved new transactions",
                    transaction_count=len(transactions),
                )

            # Step 2: Process each transaction
            for tx in transactions:
                self._transactions_processed += 1

                try:
                    # Step 3: Parse trade events from transaction
                    # Try to parse as TradeExecuted event
                    trade = self.detector.parse_trade_executed(tx)

                    if trade is None:
                        # Not a trade event, skip
                        logger.debug(
                            "Transaction is not a trade event, skipping",
                            tx_hash=tx.get("hash"),
                        )
                        continue

                    self._trades_detected += 1
                    logger.info(
                        "Trade detected",
                        trade_id=trade.id,
                        market=trade.market,
                        side=trade.side.value,
                        size=str(trade.size),
                        price=str(trade.price),
                        tx_hash=trade.tx_hash,
                    )

                    # Step 4: Execute mirror trade
                    try:
                        self.copier.process_trade(trade)
                    except Exception as e:
                        # Copier handles its own errors internally
                        # Just continue to next trade
                        logger.debug("Copier raised exception (expected)", error=str(e))
                        pass

                except Exception as e:
                    # Failed to parse event, skip this transaction
                    logger.warning(
                        "Failed to parse transaction event",
                        tx_hash=tx.get("hash"),
                        error=str(e),
                    )
                    continue

        except BlockchainConnectionError as e:
            # Monitor connection error, skip this iteration
            logger.warning("Blockchain connection error, skipping iteration", error=str(e))
            pass
        except Exception as e:
            # Unexpected error, skip this iteration
            logger.error("Unexpected error in process_once", error=str(e), exc_info=True)
            pass

    def get_statistics(self) -> Dict[str, Any]:
        """Get bot statistics.

        Returns:
            Dictionary with bot and copier statistics
        """
        stats = {
            "transactions_processed": self._transactions_processed,
            "trades_detected": self._trades_detected,
        }

        # Include copier statistics
        copier_stats = self.copier.get_statistics()
        stats.update(copier_stats)

        return stats

    def reset_statistics(self) -> None:
        """Reset bot statistics."""
        self._transactions_processed = 0
        self._trades_detected = 0
        self.copier.reset_statistics()
