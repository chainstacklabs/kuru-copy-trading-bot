"""Constants for the Kuru copy trading bot."""

from web3 import Web3

# Monad Blockchain Chain IDs
# Source: https://docs.monad.xyz/developer-essentials/network-information
MONAD_CHAIN_ID = 41454  # Mainnet (not launched yet)
MONAD_TESTNET_CHAIN_ID = 10143  # Testnet - Active

# Kuru Contract Addresses
# Main Kuru Protocol Contracts (Testnet)
KURU_ROUTER_ADDRESS_TESTNET = "0xc816865f172d640d93712C68a7E1F83F3fA63235"
KURU_MARGIN_ACCOUNT_ADDRESS_TESTNET = "0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef"
KURU_FORWARDER_ADDRESS_TESTNET = "0x350678D87BAa7f513B262B7273ad8Ccec6FF0f78"
KURU_DEPLOYER_ADDRESS_TESTNET = "0x67a4e43C7Ce69e24d495A39c43489BC7070f009B"
KURU_UTILS_ADDRESS_TESTNET = "0x9E50D9202bEc0D046a75048Be8d51bBa93386Ade"

# Official Token Addresses (Testnet)
USDC_ADDRESS_TESTNET = "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea"
KUSDC_ADDRESS_TESTNET = "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea"  # Kuru USDC
USDT_ADDRESS_TESTNET = "0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D"
DAK_ADDRESS_TESTNET = "0x0F0BDEbF0F83cD1EE3974779Bcb7315f9808c714"
CHOG_ADDRESS_TESTNET = "0xE0590015A873bF326bd645c3E1266d4db41C4E6B"
YAKI_ADDRESS_TESTNET = "0xfe140e1dCe99Be9F4F15d657CD9b7BF622270C50"

# Official Market Addresses (Testnet)
MON_USDC_MARKET_ADDRESS = "0xD3AF145f1Aa1A471b5f0F62c52Cf8fcdc9AB55D3"
DAK_MON_MARKET_ADDRESS = "0x94B72620e65577De5FB2b8a8B93328CAf6Ca161b"
CHOG_MON_MARKET_ADDRESS = "0x277bF4a0AAc16f19d7bf592FeFFc8D2d9a890508"
YAKI_MON_MARKET_ADDRESS = "0xD5C1Dc181c359f0199c83045A85Cd2556B325De0"

# Legacy constant for backward compatibility (points to Router)
KURU_CONTRACT_ADDRESS_TESTNET = KURU_ROUTER_ADDRESS_TESTNET

# Mainnet Addresses (not launched yet)
KURU_CONTRACT_ADDRESS_MAINNET = None  # TBD - Mainnet not launched yet

# Gas Configuration
DEFAULT_GAS_LIMIT = 300_000  # Default gas limit for transactions
DEFAULT_GAS_PRICE_GWEI = 20  # Default gas price in Gwei (20 Gwei)

# Retry Configuration
MAX_RETRIES = 3  # Maximum number of retry attempts for failed operations
RETRY_BACKOFF_SECONDS = 2  # Initial backoff time in seconds (exponential backoff)

# Transaction Confirmation
CONFIRMATION_BLOCKS = 1  # Number of blocks to wait for confirmation
TRANSACTION_TIMEOUT_SECONDS = 120  # Timeout for transaction confirmation

# Order Configuration
MIN_ORDER_SIZE_USD = 1.0  # Minimum order size in USD
MAX_SLIPPAGE_PERCENT = 5.0  # Maximum allowed slippage percentage

# ============================================================
# Address Validation (Runtime checks at module import)
# ============================================================
# Validate that all contract addresses are properly checksummed
# This ensures we catch any address errors at import time rather than runtime

_ADDRESSES_TO_VALIDATE = {
    "KURU_ROUTER_ADDRESS_TESTNET": KURU_ROUTER_ADDRESS_TESTNET,
    "KURU_MARGIN_ACCOUNT_ADDRESS_TESTNET": KURU_MARGIN_ACCOUNT_ADDRESS_TESTNET,
    "KURU_FORWARDER_ADDRESS_TESTNET": KURU_FORWARDER_ADDRESS_TESTNET,
    "KURU_DEPLOYER_ADDRESS_TESTNET": KURU_DEPLOYER_ADDRESS_TESTNET,
    "KURU_UTILS_ADDRESS_TESTNET": KURU_UTILS_ADDRESS_TESTNET,
    "USDC_ADDRESS_TESTNET": USDC_ADDRESS_TESTNET,
    "KUSDC_ADDRESS_TESTNET": KUSDC_ADDRESS_TESTNET,
    "USDT_ADDRESS_TESTNET": USDT_ADDRESS_TESTNET,
    "DAK_ADDRESS_TESTNET": DAK_ADDRESS_TESTNET,
    "CHOG_ADDRESS_TESTNET": CHOG_ADDRESS_TESTNET,
    "YAKI_ADDRESS_TESTNET": YAKI_ADDRESS_TESTNET,
    "MON_USDC_MARKET_ADDRESS": MON_USDC_MARKET_ADDRESS,
    "DAK_MON_MARKET_ADDRESS": DAK_MON_MARKET_ADDRESS,
    "CHOG_MON_MARKET_ADDRESS": CHOG_MON_MARKET_ADDRESS,
    "YAKI_MON_MARKET_ADDRESS": YAKI_MON_MARKET_ADDRESS,
}

for _name, _address in _ADDRESSES_TO_VALIDATE.items():
    try:
        if not Web3.is_checksum_address(_address):
            raise ValueError(
                f"{_name} address '{_address}' is not properly checksummed. "
                f"Expected: {Web3.to_checksum_address(_address)}"
            )
    except Exception as e:
        raise ValueError(f"Invalid address for {_name}: {_address}") from e

# Clean up namespace
del _name, _address, _ADDRESSES_TO_VALIDATE
