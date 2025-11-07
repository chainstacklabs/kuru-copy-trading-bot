"""Tests for Settings configuration."""

import pytest
from decimal import Decimal
from unittest.mock import patch
from pydantic import ValidationError

# These imports will fail initially - that's expected for TDD
from src.kuru_copytr_bot.config.settings import Settings


class TestSettingsConfiguration:
    """Test Settings configuration loading and validation."""

    def test_settings_loads_from_environment_variables(self, monkeypatch):
        """Settings should load from environment variables."""
        monkeypatch.setenv("PRIVATE_KEY", "0x" + "a" * 64)
        monkeypatch.setenv("MONAD_RPC_URL", "https://testnet.monad.xyz")
        monkeypatch.setenv("KURU_API_URL", "https://api.kuru.io")
        monkeypatch.setenv("SOURCE_WALLETS", "0x1234567890123456789012345678901234567890")
        monkeypatch.setenv("MAX_POSITION_SIZE_USD", "10000.0")

        settings = Settings()

        assert settings.private_key == "0x" + "a" * 64
        assert settings.monad_rpc_url == "https://testnet.monad.xyz"
        assert settings.kuru_api_url == "https://api.kuru.io"
        assert "0x1234567890123456789012345678901234567890" in settings.source_wallets

    def test_settings_requires_private_key(self):
        """Settings should require private key."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                private_key=None,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets=["0x1234567890123456789012345678901234567890"],
                max_position_size_usd=Decimal("10000"),
            )

        assert "private_key" in str(exc_info.value).lower()

    def test_settings_validates_private_key_format(self):
        """Settings should validate private key is 66 characters hex string."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="invalid_key",
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets=["0x1234567890123456789012345678901234567890"],
                max_position_size_usd=Decimal("10000"),
            )

    def test_settings_derives_wallet_address_from_private_key(self):
        """Settings should derive wallet address from private key."""
        settings = Settings(
            private_key="0x" + "a" * 64,
            monad_rpc_url="https://testnet.monad.xyz",
            kuru_api_url="https://api.kuru.io",
            source_wallets=["0x1234567890123456789012345678901234567890"],
            max_position_size_usd=Decimal("10000"),
        )

        assert settings.wallet_address is not None
        assert settings.wallet_address.startswith("0x")
        assert len(settings.wallet_address) == 42

    def test_settings_validates_wallet_address_format(self):
        """Settings should validate Ethereum address format for source wallets."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets=["invalid_address"],
                max_position_size_usd=Decimal("10000"),
            )

    def test_settings_validates_source_wallets_is_list(self):
        """Settings should validate source_wallets is a list."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets="not_a_list",
                max_position_size_usd=Decimal("10000"),
            )

    def test_settings_requires_at_least_one_source_wallet(self):
        """Settings should require at least one source wallet."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets=[],
                max_position_size_usd=Decimal("10000"),
            )

    def test_settings_copy_ratio_must_be_positive(self):
        """Copy ratio must be > 0."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets=["0x1234567890123456789012345678901234567890"],
                copy_ratio=Decimal("-0.5"),
                max_position_size_usd=Decimal("10000"),
            )

    def test_settings_copy_ratio_cannot_be_zero(self):
        """Copy ratio cannot be zero."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets=["0x1234567890123456789012345678901234567890"],
                copy_ratio=Decimal("0"),
                max_position_size_usd=Decimal("10000"),
            )

    def test_settings_max_position_size_must_be_positive(self):
        """Max position size must be > 0."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets=["0x1234567890123456789012345678901234567890"],
                max_position_size_usd=Decimal("-1000"),
            )

    def test_settings_has_default_copy_ratio(self):
        """Settings should have default copy ratio of 1.0."""
        settings = Settings(
            private_key="0x" + "a" * 64,
            monad_rpc_url="https://testnet.monad.xyz",
            kuru_api_url="https://api.kuru.io",
            source_wallets=["0x1234567890123456789012345678901234567890"],
            max_position_size_usd=Decimal("10000"),
        )

        assert settings.copy_ratio == Decimal("1.0")

    def test_settings_has_default_dry_run_false(self):
        """Settings should have default dry_run = False."""
        settings = Settings(
            private_key="0x" + "a" * 64,
            monad_rpc_url="https://testnet.monad.xyz",
            kuru_api_url="https://api.kuru.io",
            source_wallets=["0x1234567890123456789012345678901234567890"],
            max_position_size_usd=Decimal("10000"),
        )

        assert settings.dry_run is False

    def test_settings_has_default_log_level_info(self):
        """Settings should have default log_level = INFO."""
        settings = Settings(
            private_key="0x" + "a" * 64,
            monad_rpc_url="https://testnet.monad.xyz",
            kuru_api_url="https://api.kuru.io",
            source_wallets=["0x1234567890123456789012345678901234567890"],
            max_position_size_usd=Decimal("10000"),
        )

        assert settings.log_level == "INFO"

    def test_settings_accepts_valid_log_levels(self):
        """Settings should accept valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="https://api.kuru.io",
                source_wallets=["0x1234567890123456789012345678901234567890"],
                max_position_size_usd=Decimal("10000"),
                log_level=level,
            )
            assert settings.log_level == level

    def test_settings_validates_rpc_url_format(self):
        """Settings should validate RPC URL format."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="not_a_url",
                kuru_api_url="https://api.kuru.io",
                source_wallets=["0x1234567890123456789012345678901234567890"],
                max_position_size_usd=Decimal("10000"),
            )

    def test_settings_validates_api_url_format(self):
        """Settings should validate API URL format."""
        with pytest.raises(ValidationError):
            Settings(
                private_key="0x" + "a" * 64,
                monad_rpc_url="https://testnet.monad.xyz",
                kuru_api_url="not_a_url",
                source_wallets=["0x1234567890123456789012345678901234567890"],
                max_position_size_usd=Decimal("10000"),
            )

    def test_settings_parses_source_wallets_from_comma_separated_string(self, monkeypatch):
        """Settings should parse comma-separated source wallets from env."""
        monkeypatch.setenv("PRIVATE_KEY", "0x" + "a" * 64)
        monkeypatch.setenv("MONAD_RPC_URL", "https://testnet.monad.xyz")
        monkeypatch.setenv("KURU_API_URL", "https://api.kuru.io")
        monkeypatch.setenv(
            "SOURCE_WALLETS",
            "0x1234567890123456789012345678901234567890,0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        )
        monkeypatch.setenv("MAX_POSITION_SIZE_USD", "10000.0")

        settings = Settings()

        assert len(settings.source_wallets) == 2
        assert "0x1234567890123456789012345678901234567890" in settings.source_wallets
        assert "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd" in settings.source_wallets

    def test_settings_uses_decimal_for_financial_values(self):
        """Settings should use Decimal for copy_ratio and max_position_size."""
        settings = Settings(
            private_key="0x" + "a" * 64,
            monad_rpc_url="https://testnet.monad.xyz",
            kuru_api_url="https://api.kuru.io",
            source_wallets=["0x1234567890123456789012345678901234567890"],
            max_position_size_usd=Decimal("10000"),
            copy_ratio=Decimal("0.5"),
        )

        assert isinstance(settings.copy_ratio, Decimal)
        assert isinstance(settings.max_position_size_usd, Decimal)

    def test_settings_supports_optional_market_whitelist(self):
        """Settings should support optional market whitelist."""
        settings = Settings(
            private_key="0x" + "a" * 64,
            monad_rpc_url="https://testnet.monad.xyz",
            kuru_api_url="https://api.kuru.io",
            source_wallets=["0x1234567890123456789012345678901234567890"],
            max_position_size_usd=Decimal("10000"),
            market_whitelist=["ETH-USDC", "BTC-USDC"],
        )

        assert settings.market_whitelist == ["ETH-USDC", "BTC-USDC"]

    def test_settings_supports_optional_market_blacklist(self):
        """Settings should support optional market blacklist."""
        settings = Settings(
            private_key="0x" + "a" * 64,
            monad_rpc_url="https://testnet.monad.xyz",
            kuru_api_url="https://api.kuru.io",
            source_wallets=["0x1234567890123456789012345678901234567890"],
            max_position_size_usd=Decimal("10000"),
            market_blacklist=["SCAM-USDC"],
        )

        assert settings.market_blacklist == ["SCAM-USDC"]

    def test_settings_loads_from_dotenv_file(self, tmp_path, monkeypatch):
        """Settings should load from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            f"""
PRIVATE_KEY=0x{"a" * 64}
MONAD_RPC_URL=https://testnet.monad.xyz
KURU_API_URL=https://api.kuru.io
SOURCE_WALLETS=0x1234567890123456789012345678901234567890
MAX_POSITION_SIZE_USD=10000.0
COPY_RATIO=0.75
DRY_RUN=true
LOG_LEVEL=DEBUG
"""
        )

        monkeypatch.chdir(tmp_path)
        settings = Settings()

        assert settings.copy_ratio == Decimal("0.75")
        assert settings.dry_run is True
        assert settings.log_level == "DEBUG"
