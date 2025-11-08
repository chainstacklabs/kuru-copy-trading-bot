"""Wallet monitor for tracking target wallet transactions."""

from typing import List, Dict, Any, Set, Optional

from src.kuru_copytr_bot.core.interfaces import BlockchainConnector
from src.kuru_copytr_bot.core.exceptions import BlockchainConnectionError


class WalletMonitor:
    """Monitor target wallets for transactions to Kuru Exchange."""

    def __init__(
        self,
        blockchain: BlockchainConnector,
        target_wallets: List[str],
        kuru_contract_address: str,
        from_block: Optional[int] = None,
    ):
        """Initialize wallet monitor.

        Args:
            blockchain: Blockchain connector instance
            target_wallets: List of wallet addresses to monitor
            kuru_contract_address: Kuru Exchange contract address
            from_block: Starting block number (optional)
        """
        self.blockchain = blockchain
        self.target_wallets = [addr.lower() for addr in target_wallets]
        self.kuru_contract_address = kuru_contract_address.lower()

        # Track seen transactions to prevent duplicates
        self._processed_transactions: Set[str] = set()

        # Track last processed block
        self._last_block: Optional[int] = from_block

        # Running state
        self.is_running = False

    def get_new_transactions(self) -> List[Dict[str, Any]]:
        """Get new transactions from target wallets to Kuru contract.

        Returns:
            List of transaction dictionaries

        Raises:
            BlockchainConnectionError: If blockchain connection fails
        """
        try:
            # Get latest transactions from blockchain
            all_transactions = self.blockchain.get_latest_transactions()

            # Filter for target wallets and Kuru contract
            new_transactions = []

            for tx in all_transactions:
                # Validate transaction structure
                if not self._is_valid_transaction(tx):
                    continue

                tx_hash = tx["hash"]
                from_addr = tx.get("from", "").lower()
                to_addr = tx.get("to", "").lower()

                # Skip if already seen
                if tx_hash in self._processed_transactions:
                    continue

                # Check if from target wallet and to Kuru contract
                if from_addr in self.target_wallets and to_addr == self.kuru_contract_address:
                    new_transactions.append(tx)
                    self._processed_transactions.add(tx_hash)

                    # Update last processed block
                    if "blockNumber" in tx:
                        block_num = tx["blockNumber"]
                        if self._last_block is None or block_num > self._last_block:
                            self._last_block = block_num

            return new_transactions

        except BlockchainConnectionError:
            # Handle blockchain connection errors gracefully
            return []
        except Exception as e:
            # Wrap other errors
            raise BlockchainConnectionError(f"Failed to get transactions: {e}")

    def _is_valid_transaction(self, tx: Dict[str, Any]) -> bool:
        """Check if transaction has required fields.

        Args:
            tx: Transaction dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["hash", "from", "to"]
        return all(field in tx for field in required_fields)

    def get_last_processed_block(self) -> Optional[int]:
        """Get the last processed block number.

        Returns:
            Block number or None if no blocks processed yet
        """
        return self._last_block

    @property
    def last_processed_block(self) -> Optional[int]:
        """Get the last processed block number as a property.

        Returns:
            Block number or None if no blocks processed yet
        """
        return self._last_block

    def start(self):
        """Start monitoring wallets."""
        self.is_running = True

    def stop(self):
        """Stop monitoring wallets."""
        self.is_running = False

    def reset(self):
        """Reset the monitor state (clear seen transactions and block tracking)."""
        self._processed_transactions.clear()
        self._last_block = None
