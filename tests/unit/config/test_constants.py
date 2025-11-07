"""Tests for Constants configuration."""

import pytest

# These imports will fail initially - that's expected for TDD
from src.kuru_copytr_bot.config.constants import (
    MONAD_CHAIN_ID,
    MONAD_TESTNET_CHAIN_ID,
    KURU_CONTRACT_ADDRESS_TESTNET,
    KURU_CONTRACT_ADDRESS_MAINNET,
    ORDER_PLACED_EVENT_SIGNATURE,
    TRADE_EXECUTED_EVENT_SIGNATURE,
    ORDER_CANCELLED_EVENT_SIGNATURE,
    MARGIN_DEPOSIT_EVENT_SIGNATURE,
    DEFAULT_GAS_LIMIT,
    DEFAULT_GAS_PRICE_GWEI,
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS,
)


class TestConstants:
    """Test that constants are properly defined."""

    def test_monad_chain_id_is_defined(self):
        """MONAD_CHAIN_ID should be defined."""
        assert MONAD_CHAIN_ID is not None
        assert isinstance(MONAD_CHAIN_ID, int)

    def test_monad_testnet_chain_id_is_defined(self):
        """MONAD_TESTNET_CHAIN_ID should be defined."""
        assert MONAD_TESTNET_CHAIN_ID is not None
        assert isinstance(MONAD_TESTNET_CHAIN_ID, int)

    def test_kuru_contract_addresses_are_valid_ethereum_addresses(self):
        """Kuru contract addresses should be valid Ethereum addresses."""
        assert KURU_CONTRACT_ADDRESS_TESTNET.startswith("0x")
        assert len(KURU_CONTRACT_ADDRESS_TESTNET) == 42

        if KURU_CONTRACT_ADDRESS_MAINNET:
            assert KURU_CONTRACT_ADDRESS_MAINNET.startswith("0x")
            assert len(KURU_CONTRACT_ADDRESS_MAINNET) == 42

    def test_event_signatures_are_valid_hex_strings(self):
        """Event signatures should be valid 66-char hex strings."""
        assert ORDER_PLACED_EVENT_SIGNATURE.startswith("0x")
        assert len(ORDER_PLACED_EVENT_SIGNATURE) == 66

        assert TRADE_EXECUTED_EVENT_SIGNATURE.startswith("0x")
        assert len(TRADE_EXECUTED_EVENT_SIGNATURE) == 66

        assert ORDER_CANCELLED_EVENT_SIGNATURE.startswith("0x")
        assert len(ORDER_CANCELLED_EVENT_SIGNATURE) == 66

        assert MARGIN_DEPOSIT_EVENT_SIGNATURE.startswith("0x")
        assert len(MARGIN_DEPOSIT_EVENT_SIGNATURE) == 66

    def test_default_gas_limit_is_reasonable(self):
        """Default gas limit should be reasonable (100k-10M)."""
        assert DEFAULT_GAS_LIMIT > 100_000
        assert DEFAULT_GAS_LIMIT < 10_000_000

    def test_default_gas_price_is_positive(self):
        """Default gas price should be positive."""
        assert DEFAULT_GAS_PRICE_GWEI > 0

    def test_max_retries_is_positive(self):
        """Max retries should be positive."""
        assert MAX_RETRIES > 0
        assert MAX_RETRIES <= 10  # Reasonable upper bound

    def test_retry_backoff_is_positive(self):
        """Retry backoff should be positive."""
        assert RETRY_BACKOFF_SECONDS > 0
        assert RETRY_BACKOFF_SECONDS <= 60  # Reasonable upper bound
