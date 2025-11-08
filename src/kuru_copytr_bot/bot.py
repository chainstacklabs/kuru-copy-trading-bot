"""Copy trading bot orchestrator."""

from typing import Dict, Any

from src.kuru_copytr_bot.monitoring.monitor import WalletMonitor
from src.kuru_copytr_bot.monitoring.detector import KuruEventDetector
from src.kuru_copytr_bot.trading.copier import TradeCopier
from src.kuru_copytr_bot.core.exceptions import BlockchainConnectionError


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
        self.monitor.start()
        self.is_running = True

    def stop(self) -> None:
        """Stop the copy trading bot."""
        self.monitor.stop()
        self.is_running = False

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

            # Step 2: Process each transaction
            for tx in transactions:
                self._transactions_processed += 1

                try:
                    # Step 3: Parse trade events from transaction
                    # Try to parse as TradeExecuted event
                    trade = self.detector.parse_trade_executed(tx)

                    if trade is None:
                        # Not a trade event, skip
                        continue

                    self._trades_detected += 1

                    # Step 4: Execute mirror trade
                    try:
                        self.copier.process_trade(trade)
                    except Exception:
                        # Copier handles its own errors internally
                        # Just continue to next trade
                        pass

                except Exception:
                    # Failed to parse event, skip this transaction
                    continue

        except BlockchainConnectionError:
            # Monitor connection error, skip this iteration
            pass
        except Exception:
            # Unexpected error, skip this iteration
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
