"""Main entry point for Kuru Copy Trading Bot."""

import signal
import sys
import time
from decimal import Decimal
from typing import Optional

import click
from dotenv import load_dotenv

from src.kuru_copytr_bot.config.settings import Settings
from src.kuru_copytr_bot.config.constants import (
    KURU_CONTRACT_ADDRESS_TESTNET,
)
from src.kuru_copytr_bot.connectors.blockchain.monad import MonadClient
from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient
from src.kuru_copytr_bot.monitoring.monitor import WalletMonitor
from src.kuru_copytr_bot.monitoring.detector import KuruEventDetector
from src.kuru_copytr_bot.risk.calculator import PositionSizeCalculator
from src.kuru_copytr_bot.risk.validator import TradeValidator
from src.kuru_copytr_bot.trading.copier import TradeCopier
from src.kuru_copytr_bot.bot import CopyTradingBot
from src.kuru_copytr_bot.core.enums import OrderType
from src.kuru_copytr_bot.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


class BotRunner:
    """Manages bot lifecycle and component initialization."""

    def __init__(self, settings: Settings):
        """Initialize bot runner.

        Args:
            settings: Bot configuration settings
        """
        self.settings = settings
        self.bot: Optional[CopyTradingBot] = None
        self.running = False

    def initialize_components(self) -> CopyTradingBot:
        """Initialize all bot components.

        Returns:
            Configured CopyTradingBot instance
        """
        logger.info("Initializing bot components")

        # Initialize blockchain connector
        logger.debug("Creating Monad blockchain client", rpc_url=self.settings.monad_rpc_url)
        monad_client = MonadClient(
            rpc_url=self.settings.monad_rpc_url,
            private_key=self.settings.wallet_private_key,
        )

        # Initialize Kuru Exchange client
        logger.debug("Creating Kuru Exchange client")
        kuru_client = KuruClient(
            blockchain=monad_client,
            contract_address=KURU_CONTRACT_ADDRESS_TESTNET,
        )

        # Initialize wallet monitor
        logger.debug(
            "Creating wallet monitor",
            wallet_count=len(self.settings.source_wallets),
        )
        monitor = WalletMonitor(
            blockchain=monad_client,
            target_wallets=self.settings.source_wallets,
            kuru_contract_address=KURU_CONTRACT_ADDRESS_TESTNET,
        )

        # Initialize event detector
        logger.debug("Creating event detector")
        detector = KuruEventDetector()

        # Initialize position size calculator
        logger.debug(
            "Creating position size calculator",
            copy_ratio=float(self.settings.copy_ratio),
            max_position_size=float(self.settings.max_position_size),
            min_order_size=float(self.settings.min_order_size),
        )
        calculator = PositionSizeCalculator(
            copy_ratio=self.settings.copy_ratio,
            max_position_size=self.settings.max_position_size,
            min_order_size=self.settings.min_order_size,
            respect_balance=True,
        )

        # Initialize trade validator
        logger.debug(
            "Creating trade validator",
            min_balance=float(self.settings.min_balance_threshold),
            max_total_exposure=float(self.settings.max_total_exposure),
        )
        validator = TradeValidator(
            min_balance=self.settings.min_balance_threshold,
            max_position_size=self.settings.max_position_size,
            max_total_exposure=self.settings.max_total_exposure,
            market_whitelist=self.settings.market_whitelist,
            market_blacklist=self.settings.market_blacklist,
        )

        # Initialize trade copier
        logger.debug("Creating trade copier")
        copier = TradeCopier(
            kuru_client=kuru_client,
            calculator=calculator,
            validator=validator,
            default_order_type=OrderType.LIMIT,
        )

        # Initialize bot orchestrator
        logger.debug("Creating bot orchestrator")
        bot = CopyTradingBot(
            monitor=monitor,
            detector=detector,
            copier=copier,
            poll_interval=self.settings.poll_interval_seconds,
        )

        logger.info("All bot components initialized successfully")
        return bot

    def run(self) -> None:
        """Run the copy trading bot."""
        # Initialize components
        click.echo("Initializing Kuru Copy Trading Bot...")
        self.bot = self.initialize_components()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Start the bot
        click.echo(f"Starting bot (polling every {self.settings.poll_interval_seconds}s)...")
        click.echo(f"Monitoring wallets: {', '.join(self.settings.source_wallets)}")
        click.echo("Press Ctrl+C to stop\n")

        self.bot.start()
        self.running = True

        # Main loop
        while self.running:
            try:
                # Process one cycle
                self.bot.process_once()

                # Display statistics periodically
                stats = self.bot.get_statistics()
                click.echo(
                    f"Stats: {stats['transactions_processed']} txs | "
                    f"{stats['trades_detected']} trades | "
                    f"{stats['successful_trades']} successful | "
                    f"{stats['failed_trades']} failed | "
                    f"{stats['rejected_trades']} rejected"
                )

                # Sleep until next poll
                time.sleep(self.bot.poll_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                click.echo(f"Error in main loop: {e}", err=True)
                time.sleep(self.bot.poll_interval)

        # Graceful shutdown
        self.stop()

    def stop(self) -> None:
        """Stop the bot gracefully."""
        if self.bot and self.running:
            click.echo("\nStopping bot...")
            self.bot.stop()
            self.running = False

            # Display final statistics
            stats = self.bot.get_statistics()
            click.echo("\n=== Final Statistics ===")
            click.echo(f"Transactions processed: {stats['transactions_processed']}")
            click.echo(f"Trades detected: {stats['trades_detected']}")
            click.echo(f"Successful trades: {stats['successful_trades']}")
            click.echo(f"Failed trades: {stats['failed_trades']}")
            click.echo(f"Rejected trades: {stats['rejected_trades']}")
            click.echo("\nBot stopped.")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.running = False


@click.command()
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    default=".env",
    help="Path to .env file (default: .env)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default="INFO",
    help="Logging level (default: INFO)",
)
@click.option(
    "--json-logs",
    is_flag=True,
    help="Output logs in JSON format instead of human-readable format",
)
def main(env_file: str, log_level: str, json_logs: bool) -> None:
    """Kuru Copy Trading Bot - Mirror trades from expert wallets on Monad testnet.

    This bot monitors specified source wallets and automatically mirrors their
    trades on Kuru Exchange with configurable position sizing and risk management.

    Configuration is loaded from environment variables or a .env file.
    """
    # Load environment variables
    load_dotenv(env_file)

    # Configure logging first
    configure_logging(log_level=log_level, json_logs=json_logs)

    logger.info(
        "Starting Kuru Copy Trading Bot",
        log_level=log_level,
        json_logs=json_logs,
        env_file=env_file,
    )

    try:
        # Load settings
        settings = Settings()

        # Create and run bot
        runner = BotRunner(settings)
        runner.run()

    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
        click.echo(f"Fatal error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
