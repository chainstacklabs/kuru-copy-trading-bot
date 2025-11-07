"""Settings configuration for the Kuru copy trading bot."""

import os
from decimal import Decimal
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from eth_account import Account
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Wallet Configuration
    private_key: str = Field(..., description="Private key for signing transactions")
    wallet_address: Optional[str] = Field(None, description="Wallet address (derived from private key)")

    # Blockchain Configuration
    monad_rpc_url: str = Field(..., description="Monad blockchain RPC URL")
    kuru_api_url: str = Field(..., description="Kuru Exchange API URL")

    # Trading Configuration
    source_wallets: Union[str, List[str]] = Field(..., description="List of source trader wallet addresses to copy")
    copy_ratio: Decimal = Field(default=Decimal("1.0"), description="Copy ratio (1.0 = 100%)", gt=0)
    max_position_size_usd: Decimal = Field(..., description="Maximum position size in USD", gt=0)

    # Optional Market Filters
    market_whitelist: Optional[Union[str, List[str]]] = Field(None, description="Only copy trades in these markets")
    market_blacklist: Optional[Union[str, List[str]]] = Field(None, description="Never copy trades in these markets")

    # Operational Settings
    dry_run: bool = Field(default=False, description="Run in dry-run mode (no actual trades)")
    log_level: str = Field(default="INFO", description="Logging level")

    @field_validator("private_key")
    @classmethod
    def validate_private_key(cls, v: str) -> str:
        """Validate private key format."""
        if not v.startswith("0x") or len(v) != 66:
            raise ValueError("Private key must be a 66-character hex string starting with 0x")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Private key must be a valid hexadecimal string")
        return v

    @field_validator("source_wallets", mode="before")
    @classmethod
    def parse_source_wallets(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse source wallets from string or list."""
        if isinstance(v, str):
            # Split comma-separated string and strip whitespace
            return [addr.strip() for addr in v.split(",") if addr.strip()]
        return v

    @field_validator("source_wallets")
    @classmethod
    def validate_source_wallets(cls, v: List[str]) -> List[str]:
        """Validate source wallet addresses."""
        if not v:
            raise ValueError("At least one source wallet is required")

        for addr in v:
            if not addr.startswith("0x") or len(addr) != 42:
                raise ValueError(f"Invalid Ethereum address format: {addr}")

        return v

    @field_validator("monad_rpc_url", "kuru_api_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper

    @field_validator("copy_ratio", "max_position_size_usd", mode="before")
    @classmethod
    def parse_decimal(cls, v) -> Decimal:
        """Parse string or number to Decimal."""
        if isinstance(v, str):
            return Decimal(v)
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_validator("dry_run", mode="before")
    @classmethod
    def parse_bool(cls, v) -> bool:
        """Parse string to boolean."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "y")
        return bool(v)

    @field_validator("market_whitelist", "market_blacklist", mode="before")
    @classmethod
    def parse_market_list(cls, v: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
        """Parse market list from string or list."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return [market.strip() for market in v.split(",") if market.strip()]
        return v

    @model_validator(mode="after")
    def derive_wallet_address(self) -> "Settings":
        """Derive wallet address from private key."""
        if not self.wallet_address:
            try:
                account = Account.from_key(self.private_key)
                self.wallet_address = account.address
            except Exception as e:
                raise ValueError(f"Failed to derive wallet address from private key: {e}")
        return self
