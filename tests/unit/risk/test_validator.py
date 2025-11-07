"""Unit tests for trade validator."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from src.kuru_copytr_bot.risk.validator import TradeValidator, ValidationResult
from src.kuru_copytr_bot.models.trade import Trade
from src.kuru_copytr_bot.core.enums import OrderSide


@pytest.fixture
def sample_buy_trade():
    """Create a sample buy trade."""
    return Trade(
        id="trade_001",
        trader_address="0x1234567890123456789012345678901234567890",
        market="ETH-USDC",
        side=OrderSide.BUY,
        price=Decimal("2000.0"),
        size=Decimal("1.0"),
        timestamp=datetime.now(timezone.utc),
        tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    )


class TestValidationResult:
    """Test ValidationResult data class."""

    def test_validation_result_for_valid_trade(self):
        """ValidationResult should indicate valid trade."""
        result = ValidationResult(is_valid=True, reason=None)
        assert result.is_valid is True
        assert result.reason is None

    def test_validation_result_for_invalid_trade(self):
        """ValidationResult should indicate invalid trade with reason."""
        result = ValidationResult(
            is_valid=False,
            reason="Insufficient balance"
        )
        assert result.is_valid is False
        assert result.reason == "Insufficient balance"


class TestTradeValidatorInitialization:
    """Test TradeValidator initialization."""

    def test_validator_initializes_with_defaults(self):
        """Validator should initialize with default settings."""
        validator = TradeValidator()
        assert validator is not None

    def test_validator_initializes_with_min_balance(self):
        """Validator should initialize with minimum balance."""
        validator = TradeValidator(min_balance=Decimal("100.0"))
        assert validator.min_balance == Decimal("100.0")

    def test_validator_initializes_with_max_position_size(self):
        """Validator should initialize with max position size."""
        validator = TradeValidator(max_position_size=Decimal("10.0"))
        assert validator.max_position_size == Decimal("10.0")


class TestTradeValidatorBalanceValidation:
    """Test balance validation."""

    def test_validator_accepts_sufficient_balance(self, sample_buy_trade):
        """Validator should accept trade with sufficient balance."""
        validator = TradeValidator(min_balance=Decimal("100.0"))
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("5000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is True
        assert result.reason is None

    def test_validator_rejects_insufficient_balance(self, sample_buy_trade):
        """Validator should reject trade with insufficient balance."""
        validator = TradeValidator(min_balance=Decimal("100.0"))
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("50.0"),  # Below minimum
            current_position=Decimal("0"),
        )
        assert result.is_valid is False
        assert "balance" in result.reason.lower()

    def test_validator_checks_balance_for_trade_cost(self, sample_buy_trade):
        """Validator should check balance covers trade cost."""
        validator = TradeValidator()
        # Trade costs 2000 (1.0 @ 2000)
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("1500.0"),  # Insufficient for trade
            current_position=Decimal("0"),
        )
        assert result.is_valid is False
        assert "balance" in result.reason.lower()


class TestTradeValidatorPositionSizeLimits:
    """Test position size limit validation."""

    def test_validator_accepts_position_within_limit(self, sample_buy_trade):
        """Validator should accept position within size limit."""
        validator = TradeValidator(max_position_size=Decimal("10.0"))
        result = validator.validate(
            trade=sample_buy_trade,  # size=1.0
            current_balance=Decimal("10000.0"),
            current_position=Decimal("5.0"),
        )
        # New position would be 6.0, within limit
        assert result.is_valid is True

    def test_validator_rejects_position_exceeding_limit(self, sample_buy_trade):
        """Validator should reject position exceeding size limit."""
        validator = TradeValidator(max_position_size=Decimal("5.0"))
        result = validator.validate(
            trade=sample_buy_trade,  # size=1.0
            current_balance=Decimal("10000.0"),
            current_position=Decimal("5.0"),
        )
        # New position would be 6.0, exceeds limit of 5.0
        assert result.is_valid is False
        assert "position size" in result.reason.lower()

    def test_validator_handles_sell_reducing_position(self):
        """Validator should handle sells that reduce position."""
        sell_trade = Trade(
            id="trade_002",
            trader_address="0x1234567890123456789012345678901234567890",
            market="ETH-USDC",
            side=OrderSide.SELL,
            price=Decimal("2000.0"),
            size=Decimal("2.0"),
            timestamp=datetime.now(timezone.utc),
            tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )

        validator = TradeValidator(max_position_size=Decimal("10.0"))
        result = validator.validate(
            trade=sell_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("5.0"),
        )
        # Selling 2.0 from 5.0 position = 3.0, within limit
        assert result.is_valid is True


class TestTradeValidatorMinimumOrderSize:
    """Test minimum order size validation."""

    def test_validator_accepts_size_above_minimum(self, sample_buy_trade):
        """Validator should accept order size above minimum."""
        validator = TradeValidator(min_order_size=Decimal("0.1"))
        result = validator.validate(
            trade=sample_buy_trade,  # size=1.0
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is True

    def test_validator_rejects_size_below_minimum(self):
        """Validator should reject order size below minimum."""
        small_trade = Trade(
            id="trade_003",
            trader_address="0x1234567890123456789012345678901234567890",
            market="ETH-USDC",
            side=OrderSide.BUY,
            price=Decimal("2000.0"),
            size=Decimal("0.001"),  # Very small
            timestamp=datetime.now(timezone.utc),
            tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )

        validator = TradeValidator(min_order_size=Decimal("0.01"))
        result = validator.validate(
            trade=small_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is False
        assert "minimum" in result.reason.lower()


class TestTradeValidatorMarketWhitelist:
    """Test market whitelist validation."""

    def test_validator_accepts_whitelisted_market(self, sample_buy_trade):
        """Validator should accept trade in whitelisted market."""
        validator = TradeValidator(market_whitelist=["ETH-USDC", "BTC-USDC"])
        result = validator.validate(
            trade=sample_buy_trade,  # market="ETH-USDC"
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is True

    def test_validator_rejects_non_whitelisted_market(self, sample_buy_trade):
        """Validator should reject trade not in whitelist."""
        validator = TradeValidator(market_whitelist=["BTC-USDC", "SOL-USDC"])
        result = validator.validate(
            trade=sample_buy_trade,  # market="ETH-USDC"
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is False
        assert "whitelist" in result.reason.lower()

    def test_validator_accepts_all_markets_without_whitelist(self, sample_buy_trade):
        """Validator should accept any market without whitelist."""
        validator = TradeValidator()  # No whitelist
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is True


class TestTradeValidatorMarketBlacklist:
    """Test market blacklist validation."""

    def test_validator_rejects_blacklisted_market(self, sample_buy_trade):
        """Validator should reject trade in blacklisted market."""
        validator = TradeValidator(market_blacklist=["ETH-USDC"])
        result = validator.validate(
            trade=sample_buy_trade,  # market="ETH-USDC"
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is False
        assert "blacklist" in result.reason.lower()

    def test_validator_accepts_non_blacklisted_market(self, sample_buy_trade):
        """Validator should accept trade not in blacklist."""
        validator = TradeValidator(market_blacklist=["BTC-USDC", "SOL-USDC"])
        result = validator.validate(
            trade=sample_buy_trade,  # market="ETH-USDC"
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is True

    def test_validator_whitelist_overrides_blacklist(self, sample_buy_trade):
        """Validator should prioritize whitelist over blacklist."""
        validator = TradeValidator(
            market_whitelist=["ETH-USDC"],
            market_blacklist=["ETH-USDC"],
        )
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        # Whitelist should take precedence
        assert result.is_valid is True


class TestTradeValidatorMaxExposure:
    """Test maximum exposure validation."""

    def test_validator_accepts_exposure_within_limit(self, sample_buy_trade):
        """Validator should accept trade with exposure within limit."""
        validator = TradeValidator(max_exposure_usd=Decimal("10000.0"))
        result = validator.validate(
            trade=sample_buy_trade,  # notional=2000
            current_balance=Decimal("10000.0"),
            current_position=Decimal("2.0"),  # current exposure=4000
        )
        # Total exposure = 4000 + 2000 = 6000, within limit
        assert result.is_valid is True

    def test_validator_rejects_exposure_exceeding_limit(self, sample_buy_trade):
        """Validator should reject trade exceeding exposure limit."""
        validator = TradeValidator(max_exposure_usd=Decimal("5000.0"))
        result = validator.validate(
            trade=sample_buy_trade,  # notional=2000
            current_balance=Decimal("10000.0"),
            current_position=Decimal("4.0"),  # current exposure=8000
        )
        # Total exposure = 8000 + 2000 = 10000, exceeds limit of 5000
        assert result.is_valid is False
        assert "exposure" in result.reason.lower()


class TestTradeValidatorErrorMessages:
    """Test validation error message clarity."""

    def test_validator_provides_clear_balance_error(self, sample_buy_trade):
        """Validator should provide clear error for insufficient balance."""
        validator = TradeValidator(min_balance=Decimal("100.0"))
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("50.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is False
        assert "balance" in result.reason.lower()
        assert "50" in result.reason or "50.0" in result.reason  # Shows actual balance

    def test_validator_provides_clear_position_size_error(self, sample_buy_trade):
        """Validator should provide clear error for position size limit."""
        validator = TradeValidator(max_position_size=Decimal("5.0"))
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("5.0"),
        )
        assert result.is_valid is False
        assert "position size" in result.reason.lower()
        assert "5" in result.reason or "5.0" in result.reason  # Shows limit

    def test_validator_provides_clear_market_error(self, sample_buy_trade):
        """Validator should provide clear error for market restrictions."""
        validator = TradeValidator(market_whitelist=["BTC-USDC"])
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is False
        assert "ETH-USDC" in result.reason  # Shows the market


class TestTradeValidatorMultipleRules:
    """Test combinations of validation rules."""

    def test_validator_checks_all_rules(self, sample_buy_trade):
        """Validator should check all configured rules."""
        validator = TradeValidator(
            min_balance=Decimal("100.0"),
            max_position_size=Decimal("10.0"),
            min_order_size=Decimal("0.01"),
            market_whitelist=["ETH-USDC"],
            max_exposure_usd=Decimal("100000.0"),
        )
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("2.0"),
        )
        # Should pass all checks
        assert result.is_valid is True

    def test_validator_fails_on_first_violation(self, sample_buy_trade):
        """Validator should report first rule violation."""
        validator = TradeValidator(
            min_balance=Decimal("10000.0"),  # Will fail this
            max_position_size=Decimal("0.1"),  # Would also fail this
        )
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("100.0"),  # Below minimum
            current_position=Decimal("5.0"),
        )
        assert result.is_valid is False
        # Should report balance issue (checked first)
        assert result.reason is not None


class TestTradeValidatorEdgeCases:
    """Test edge cases and error handling."""

    def test_validator_handles_zero_position(self, sample_buy_trade):
        """Validator should handle zero current position."""
        validator = TradeValidator(max_position_size=Decimal("10.0"))
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is True

    def test_validator_handles_zero_balance(self, sample_buy_trade):
        """Validator should reject trade with zero balance."""
        validator = TradeValidator()
        result = validator.validate(
            trade=sample_buy_trade,
            current_balance=Decimal("0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is False

    def test_validator_handles_very_small_trade(self):
        """Validator should handle very small trade sizes."""
        tiny_trade = Trade(
            id="trade_004",
            trader_address="0x1234567890123456789012345678901234567890",
            market="ETH-USDC",
            side=OrderSide.BUY,
            price=Decimal("2000.0"),
            size=Decimal("0.0001"),
            timestamp=datetime.now(timezone.utc),
            tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )

        validator = TradeValidator(min_order_size=Decimal("0.00001"))
        result = validator.validate(
            trade=tiny_trade,
            current_balance=Decimal("1.0"),
            current_position=Decimal("0"),
        )
        assert result.is_valid is True

    def test_validator_validates_negative_position_for_short(self):
        """Validator should handle negative positions (shorts)."""
        sell_trade = Trade(
            id="trade_005",
            trader_address="0x1234567890123456789012345678901234567890",
            market="ETH-USDC",
            side=OrderSide.SELL,
            price=Decimal("2000.0"),
            size=Decimal("2.0"),
            timestamp=datetime.now(timezone.utc),
            tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )

        validator = TradeValidator(max_position_size=Decimal("10.0"))
        result = validator.validate(
            trade=sell_trade,
            current_balance=Decimal("10000.0"),
            current_position=Decimal("-5.0"),  # Short position
        )
        # Selling more from short: -5 - 2 = -7, within limit
        assert result.is_valid is True
