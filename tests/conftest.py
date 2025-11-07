"""Pytest configuration and shared fixtures."""

import pytest
from decimal import Decimal
from typing import Any, Dict

from tests.mocks.blockchain import MockBlockchainClient, MockWeb3Provider
from tests.mocks.kuru import MockKuruClient
from tests.fixtures.trades import (
    SAMPLE_TRADE_BUY,
    SAMPLE_TRADE_SELL,
    ALL_VALID_TRADES,
    ALL_INVALID_TRADES,
)
from tests.fixtures.transactions import (
    SAMPLE_TRANSACTION_KURU,
    SAMPLE_TRANSACTION_RECEIPT,
    ALL_TRANSACTIONS,
    ALL_RECEIPTS,
)
from tests.fixtures.events import (
    SAMPLE_EVENT_ORDER_PLACED,
    SAMPLE_EVENT_TRADE_EXECUTED,
    ALL_VALID_EVENTS,
    ALL_MALFORMED_EVENTS,
)
from tests.fixtures.markets import (
    SAMPLE_MARKET_ETH_USDC,
    ALL_ACTIVE_MARKETS,
    MARKETS_BY_ID,
)


# ===== Pytest Markers =====

def pytest_configure(config: Any) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (may require testnet)")
    config.addinivalue_line("markers", "slow: Slow tests (may take several seconds)")


# ===== Mock Client Fixtures =====

@pytest.fixture
def mock_web3() -> MockWeb3Provider:
    """Create a mock Web3 provider."""
    return MockWeb3Provider()


@pytest.fixture
def mock_blockchain() -> MockBlockchainClient:
    """Create a mock blockchain client."""
    return MockBlockchainClient()


@pytest.fixture
def mock_kuru(mock_blockchain: MockBlockchainClient) -> MockKuruClient:
    """Create a mock Kuru client."""
    return MockKuruClient(blockchain=mock_blockchain)


# ===== Trade Fixtures =====

@pytest.fixture
def sample_trade_buy() -> Dict[str, Any]:
    """Sample BUY trade."""
    return SAMPLE_TRADE_BUY.copy()


@pytest.fixture
def sample_trade_sell() -> Dict[str, Any]:
    """Sample SELL trade."""
    return SAMPLE_TRADE_SELL.copy()


@pytest.fixture
def all_valid_trades() -> list:
    """List of all valid trades."""
    return [trade.copy() for trade in ALL_VALID_TRADES]


@pytest.fixture
def all_invalid_trades() -> list:
    """List of all invalid trades."""
    return [trade.copy() for trade in ALL_INVALID_TRADES]


# ===== Transaction Fixtures =====

@pytest.fixture
def sample_transaction_kuru() -> Dict[str, Any]:
    """Sample Kuru transaction."""
    return SAMPLE_TRANSACTION_KURU.copy()


@pytest.fixture
def sample_transaction_receipt() -> Dict[str, Any]:
    """Sample transaction receipt with logs."""
    return SAMPLE_TRANSACTION_RECEIPT.copy()


@pytest.fixture
def all_transactions() -> list:
    """List of all transactions."""
    return [tx.copy() for tx in ALL_TRANSACTIONS]


@pytest.fixture
def all_receipts() -> list:
    """List of all transaction receipts."""
    return [receipt.copy() for receipt in ALL_RECEIPTS]


# ===== Event Fixtures =====

@pytest.fixture
def sample_event_order_placed() -> Dict[str, Any]:
    """Sample OrderPlaced event."""
    return SAMPLE_EVENT_ORDER_PLACED.copy()


@pytest.fixture
def sample_event_trade_executed() -> Dict[str, Any]:
    """Sample TradeExecuted event."""
    return SAMPLE_EVENT_TRADE_EXECUTED.copy()


@pytest.fixture
def all_valid_events() -> list:
    """List of all valid events."""
    return [event.copy() for event in ALL_VALID_EVENTS]


@pytest.fixture
def all_malformed_events() -> list:
    """List of all malformed events."""
    return [event.copy() for event in ALL_MALFORMED_EVENTS]


# ===== Market Fixtures =====

@pytest.fixture
def sample_market() -> Dict[str, Any]:
    """Sample market parameters (ETH-USDC)."""
    return SAMPLE_MARKET_ETH_USDC.copy()


@pytest.fixture
def all_active_markets() -> list:
    """List of all active markets."""
    return [market.copy() for market in ALL_ACTIVE_MARKETS]


@pytest.fixture
def markets_by_id() -> Dict[str, Dict[str, Any]]:
    """Dictionary of markets by ID."""
    return {k: v.copy() for k, v in MARKETS_BY_ID.items()}


# ===== Test Settings Fixtures =====

@pytest.fixture
def test_settings() -> Dict[str, Any]:
    """Mock settings for testing."""
    return {
        "private_key": "0xtest_private_key_1234567890abcdef1234567890abcdef1234567890abcd",
        "wallet_address": "0x1234567890123456789012345678901234567890",
        "monad_rpc_url": "http://mock-monad-rpc",
        "kuru_api_url": "http://mock-kuru-api",
        "source_wallets": ["0x1234567890123456789012345678901234567890"],
        "copy_ratio": Decimal("1.0"),
        "max_position_size_usd": Decimal("10000.0"),
        "dry_run": False,
        "log_level": "INFO",
    }
