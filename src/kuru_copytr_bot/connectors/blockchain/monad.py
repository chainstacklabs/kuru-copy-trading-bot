"""Monad blockchain connector using Web3.py."""

import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from web3 import Web3
from web3.exceptions import Web3Exception
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.kuru_copytr_bot.core.interfaces import BlockchainConnector
from src.kuru_copytr_bot.core.exceptions import (
    BlockchainConnectionError,
    TransactionFailedError,
    InsufficientGasError,
)
from src.kuru_copytr_bot.config.constants import (
    DEFAULT_GAS_LIMIT,
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS,
)


class MonadClient(BlockchainConnector):
    """Monad blockchain connector implementing BlockchainConnector interface."""

    # Standard ERC20 ABI for balanceOf
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
    ]

    def __init__(self, rpc_url: str, private_key: str):
        """Initialize Monad client.

        Args:
            rpc_url: Monad RPC endpoint URL
            private_key: Private key for signing transactions

        Raises:
            BlockchainConnectionError: If connection fails
        """
        self.rpc_url = rpc_url
        self.private_key = private_key

        # Initialize Web3
        try:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        except Exception as e:
            raise BlockchainConnectionError(f"Failed to initialize Web3: {e}")

        # Verify connection
        if not self.w3.is_connected():
            raise BlockchainConnectionError(f"Failed to connect to {rpc_url}")

        # Set up account from private key
        try:
            self.account = self.w3.eth.account.from_key(private_key)
            self.wallet_address = self.account.address
        except Exception as e:
            raise ValueError(f"Invalid private key: {e}")

    def is_connected(self) -> bool:
        """Check if connected to blockchain.

        Returns:
            bool: True if connected, False otherwise
        """
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def get_balance(self, address: str) -> Decimal:
        """Get native token balance for an address.

        Args:
            address: Ethereum address

        Returns:
            Decimal: Balance in native tokens (MON)

        Raises:
            BlockchainConnectionError: If connection fails
            ValueError: If address is invalid
        """
        # Validate address
        if not self._is_valid_address(address):
            raise ValueError(f"Invalid Ethereum address: {address}")

        @retry(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=RETRY_BACKOFF_SECONDS, min=1, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        )
        def _get_balance_with_retry():
            return self.w3.eth.get_balance(address)

        try:
            balance_wei = _get_balance_with_retry()
            # Convert wei to ETH/MON (18 decimals)
            return Decimal(balance_wei) / Decimal(10**18)
        except (ConnectionError, TimeoutError) as e:
            raise BlockchainConnectionError(f"Failed to get balance after retries: {e}")
        except Exception as e:
            raise BlockchainConnectionError(f"Failed to get balance: {e}")

    def get_token_balance(self, address: str, token_address: str) -> Decimal:
        """Get ERC20 token balance for an address.

        Args:
            address: Ethereum address
            token_address: ERC20 token contract address

        Returns:
            Decimal: Token balance

        Raises:
            BlockchainConnectionError: If connection fails
            ValueError: If address is invalid
        """
        # Validate addresses
        if not self._is_valid_address(address):
            raise ValueError(f"Invalid Ethereum address: {address}")
        if not self._is_valid_address(token_address):
            raise ValueError(f"Invalid token address: {token_address}")

        @retry(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=RETRY_BACKOFF_SECONDS, min=1, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        )
        def _get_token_balance_with_retry():
            contract = self.w3.eth.contract(address=token_address, abi=self.ERC20_ABI)
            balance_raw = contract.functions.balanceOf(address).call()
            try:
                decimals = contract.functions.decimals().call()
            except Exception:
                decimals = 18
            return balance_raw, decimals

        try:
            balance_raw, decimals = _get_token_balance_with_retry()
            # Convert to decimal
            return Decimal(balance_raw) / Decimal(10**decimals)
        except (ConnectionError, TimeoutError) as e:
            raise BlockchainConnectionError(f"Failed to get token balance after retries: {e}")
        except Exception as e:
            raise BlockchainConnectionError(f"Failed to get token balance: {e}")

    def send_transaction(
        self,
        to: str,
        data: str = "0x",
        value: int = 0,
        gas: Optional[int] = None,
    ) -> str:
        """Build, sign, and send a transaction.

        Args:
            to: Recipient address
            data: Transaction data (hex string)
            value: Amount to send in wei
            gas: Gas limit (estimated if not provided)

        Returns:
            str: Transaction hash (hex string with 0x prefix)

        Raises:
            TransactionFailedError: If transaction fails
            InsufficientGasError: If gas estimation fails
            BlockchainConnectionError: If connection fails
            ValueError: If validation fails
        """
        # Validate address
        if not self._is_valid_address(to):
            raise ValueError(f"Invalid recipient address: {to}")

        @retry(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=RETRY_BACKOFF_SECONDS, min=1, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        )
        def _send_with_retry(tx):
            signed_tx = self.account.sign_transaction(tx)
            return self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        try:
            # Get nonce
            nonce = self.w3.eth.get_transaction_count(self.wallet_address, "pending")

            # Build transaction
            tx = {
                "from": self.wallet_address,
                "to": to,
                "value": value,
                "data": data,
                "nonce": nonce,
                "chainId": self.w3.eth.chain_id,
                "gasPrice": self.w3.eth.gas_price,
            }

            # Estimate gas if not provided
            if gas is None:
                try:
                    estimated_gas = self.w3.eth.estimate_gas(tx)
                    tx["gas"] = estimated_gas
                except Web3Exception as e:
                    if "out of gas" in str(e).lower():
                        raise InsufficientGasError(f"Gas estimation failed: {e}")
                    raise InsufficientGasError(f"Failed to estimate gas: {e}")
            else:
                tx["gas"] = gas

            # Send transaction with retry
            tx_hash = _send_with_retry(tx)

            # Return hex string
            if isinstance(tx_hash, bytes):
                # Convert bytes to hex string
                result = tx_hash.hex() if not tx_hash.startswith(b'0x') else tx_hash.decode('utf-8')
                return result if result.startswith('0x') else '0x' + result
            return tx_hash

        except (ConnectionError, TimeoutError) as e:
            raise BlockchainConnectionError(f"Failed to send transaction after retries: {e}")
        except InsufficientGasError:
            # Don't wrap gas errors
            raise
        except (ValueError, Web3Exception) as e:
            # Wrap transaction validation/execution errors
            raise TransactionFailedError(f"Transaction failed: {e}")
        except Exception as e:
            raise BlockchainConnectionError(f"Failed to send transaction: {e}")

    def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction receipt.

        Args:
            tx_hash: Transaction hash

        Returns:
            Dict[str, Any]: Transaction receipt

        Raises:
            BlockchainConnectionError: If connection fails
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if receipt is None:
                return None
            # Convert to dict if needed
            return dict(receipt) if not isinstance(receipt, dict) else receipt
        except Exception as e:
            raise BlockchainConnectionError(f"Failed to get transaction receipt: {e}")

    def wait_for_transaction_receipt(
        self,
        tx_hash: str,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """Wait for transaction to be confirmed.

        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds

        Returns:
            Dict[str, Any]: Transaction receipt

        Raises:
            TransactionFailedError: If transaction fails
            BlockchainConnectionError: If connection fails
            TimeoutError: If timeout is reached
        """
        start_time = time.time()
        poll_interval = 1  # seconds

        while time.time() - start_time < timeout:
            receipt = self.get_transaction_receipt(tx_hash)

            if receipt is not None:
                # Check if transaction succeeded
                if receipt.get("status") == 0:
                    raise TransactionFailedError(
                        f"Transaction {tx_hash} failed (status=0)"
                    )
                return receipt

            # Wait before polling again
            time.sleep(poll_interval)

        raise TimeoutError(f"Transaction {tx_hash} not confirmed within {timeout}s")

    def parse_event_logs(
        self,
        logs: List[Dict[str, Any]],
        event_abi: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Parse event logs from transaction receipt.

        Args:
            logs: Raw event logs from receipt
            event_abi: Event ABI specification

        Returns:
            List[Dict[str, Any]]: Parsed events

        Raises:
            ValueError: If log parsing fails
        """
        if not logs:
            return []

        try:
            # Create a contract interface for parsing
            # We need a minimal contract ABI with just the event
            contract_abi = [event_abi]
            # Use a dummy address since we're only parsing logs
            dummy_address = "0x" + "0" * 40
            contract = self.w3.eth.contract(address=dummy_address, abi=contract_abi)

            parsed_events = []
            for log in logs:
                try:
                    # Try to parse this log with the event ABI
                    event_name = event_abi.get("name", "Unknown")
                    # Get the event from contract
                    event = getattr(contract.events, event_name, None)
                    if event:
                        parsed = event.process_log(log)
                        parsed_events.append(dict(parsed))
                except Exception:
                    # Skip logs that don't match this event
                    continue

            return parsed_events

        except Exception as e:
            raise ValueError(f"Failed to parse event logs: {e}")

    def get_nonce(self, address: str) -> int:
        """Get current nonce for address.

        Args:
            address: Ethereum address

        Returns:
            int: Current nonce

        Raises:
            BlockchainConnectionError: If connection fails
            ValueError: If address is invalid
        """
        # Validate address
        if not self._is_valid_address(address):
            raise ValueError(f"Invalid Ethereum address: {address}")

        @retry(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=RETRY_BACKOFF_SECONDS, min=1, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        )
        def _get_nonce_with_retry():
            return self.w3.eth.get_transaction_count(address, "pending")

        try:
            return _get_nonce_with_retry()
        except (ConnectionError, TimeoutError) as e:
            raise BlockchainConnectionError(f"Failed to get nonce after retries: {e}")
        except Exception as e:
            raise BlockchainConnectionError(f"Failed to get nonce: {e}")

    def estimate_gas(
        self,
        to: str,
        data: str = "0x",
        value: int = 0,
    ) -> int:
        """Estimate gas for a transaction.

        Args:
            to: Recipient address
            data: Transaction data
            value: Amount to send in wei

        Returns:
            int: Estimated gas

        Raises:
            InsufficientGasError: If estimation fails
            BlockchainConnectionError: If connection fails
            ValueError: If validation fails
        """
        # Validate address
        if not self._is_valid_address(to):
            raise ValueError(f"Invalid recipient address: {to}")

        try:
            tx = {
                "from": self.wallet_address,
                "to": to,
                "value": value,
                "data": data,
            }
            return self.w3.eth.estimate_gas(tx)
        except Web3Exception as e:
            if "out of gas" in str(e).lower():
                raise InsufficientGasError(f"Gas estimation failed: {e}")
            raise InsufficientGasError(f"Failed to estimate gas: {e}")
        except Exception as e:
            raise BlockchainConnectionError(f"Failed to estimate gas: {e}")

    def get_latest_transactions(
        self,
        addresses: List[str],
        from_block: int,
    ) -> List[Dict[str, Any]]:
        """Get latest transactions for addresses.

        Args:
            addresses: List of Ethereum addresses
            from_block: Starting block number

        Returns:
            List[Dict[str, Any]]: List of transactions

        Raises:
            BlockchainConnectionError: If connection fails
        """
        # This is a placeholder for future implementation
        # Would require filtering through blocks or using event logs
        return []

    def _is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address format.

        Args:
            address: Address to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(address, str):
            return False
        if not address.startswith("0x"):
            return False
        if len(address) != 42:
            return False
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
