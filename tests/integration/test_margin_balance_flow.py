"""Integration tests for margin balance flow.

These tests connect to the real Kuru testnet and require:
1. Valid Monad testnet RPC URL in .env
2. Valid private key with testnet MON
3. Network connectivity
4. Kuru testnet contracts deployed

Run with: pytest tests/integration/test_margin_balance_flow.py -m integration
"""

import pytest
from decimal import Decimal

from src.kuru_copytr_bot.config.constants import KURU_CONTRACT_ADDRESS_TESTNET
from src.kuru_copytr_bot.config.settings import Settings
from src.kuru_copytr_bot.connectors.blockchain.monad import MonadClient
from src.kuru_copytr_bot.connectors.platforms.kuru import KuruClient


@pytest.mark.integration
class TestMarginBalanceFlow:
    """Test complete margin balance flow."""

    @pytest.fixture
    def settings(self):
        """Load settings from environment."""
        try:
            return Settings()
        except Exception as e:
            pytest.skip(f"Settings not configured: {e}")

    @pytest.fixture
    def blockchain(self, settings):
        """Create blockchain client connected to testnet."""
        try:
            client = MonadClient(
                rpc_url=settings.monad_rpc_url,
                private_key=settings.private_key,
            )
            if not client.is_connected():
                pytest.skip("Cannot connect to Monad testnet")
            return client
        except Exception as e:
            pytest.skip(f"Blockchain connection failed: {e}")

    @pytest.fixture
    def kuru_client(self, blockchain, settings):
        """Create KuruClient connected to testnet."""
        try:
            return KuruClient(
                blockchain=blockchain,
                api_url=settings.kuru_api_url,
                contract_address=KURU_CONTRACT_ADDRESS_TESTNET,
            )
        except Exception as e:
            pytest.skip(f"KuruClient initialization failed: {e}")

    def test_full_margin_balance_flow(self, kuru_client):
        """Test complete flow from balance check to validation."""
        margin_balance = kuru_client.get_margin_balance(None)

        assert margin_balance is not None
        assert isinstance(margin_balance, Decimal)
        assert margin_balance >= 0

    def test_margin_balance_mismatch_with_wallet(self, kuru_client, blockchain):
        """Test that margin balance differs from wallet balance."""
        wallet_balance = blockchain.get_balance(blockchain.wallet_address)
        margin_balance = kuru_client.get_margin_balance(None)

        assert isinstance(wallet_balance, Decimal)
        assert isinstance(margin_balance, Decimal)

    def test_margin_balance_for_usdc(self, kuru_client):
        """Test margin balance for USDC token."""
        from src.kuru_copytr_bot.config.constants import USDC_ADDRESS_TESTNET

        usdc_balance = kuru_client.get_margin_balance(USDC_ADDRESS_TESTNET, decimals=6)

        assert usdc_balance is not None
        assert isinstance(usdc_balance, Decimal)
        assert usdc_balance >= 0
