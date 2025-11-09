"""Constants for the Kuru copy trading bot."""

# Monad Blockchain Chain IDs
# Source: https://docs.monad.xyz/developer-essentials/network-information
# Verified: 2025-01-09
MONAD_CHAIN_ID = 41454  # Mainnet (not launched yet)
MONAD_TESTNET_CHAIN_ID = 10143  # Testnet - Active

# Kuru Contract Addresses
# Source: https://docs.kuru.io/ - Official Kuru documentation
# Verified: 2025-01-09
# Network: Monad Testnet (Chain ID: 10143)

# Main Kuru Protocol Contracts
KURU_ROUTER_ADDRESS_TESTNET = "0xc816865f172d640d93712C68a7E1F83F3fA63235"
# Explorer: https://testnet.monadscan.com/address/0xc816865f172d640d93712C68a7E1F83F3fA63235

KURU_MARGIN_ACCOUNT_ADDRESS_TESTNET = "0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef"
# Explorer: https://testnet.monadscan.com/address/0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef

KURU_FORWARDER_ADDRESS_TESTNET = "0x350678D87BAa7f513B262B7273ad8Ccec6FF0f78"
# Explorer: https://testnet.monadscan.com/address/0x350678D87BAa7f513B262B7273ad8Ccec6FF0f78

KURU_DEPLOYER_ADDRESS_TESTNET = "0x67a4e43C7Ce69e24d495A39c43489BC7070f009B"
# Explorer: https://testnet.monadscan.com/address/0x67a4e43C7Ce69e24d495A39c43489BC7070f009B

KURU_UTILS_ADDRESS_TESTNET = "0x9E50D9202bEc0D046a75048Be8d51bBa93386Ade"
# Explorer: https://testnet.monadscan.com/address/0x9E50D9202bEc0D046a75048Be8d51bBa93386Ade

# Official Token Addresses (Testnet)
USDC_ADDRESS_TESTNET = "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea"
KUSDC_ADDRESS_TESTNET = "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea"  # Kuru USDC
USDT_ADDRESS_TESTNET = "0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D"
DAK_ADDRESS_TESTNET = "0x0F0BDEbF0F83cD1EE3974779Bcb7315f9808c714"
CHOG_ADDRESS_TESTNET = "0xE0590015A873bF326bd645c3E1266d4db41C4E6B"
YAKI_ADDRESS_TESTNET = "0xfe140e1dCe99Be9F4F15d657CD9b7BF622270C50"

# Official Market Addresses (Testnet)
MON_USDC_MARKET_ADDRESS = "0xD3AF145f1Aa1A471b5f0F62c52Cf8fcdc9AB55D3"
DAK_MON_MARKET_ADDRESS = "0x94B72620e65577De5FB2B8A8b93328cAF6CA161b"
CHOG_MON_MARKET_ADDRESS = "0x277BF4A0aAc16f19D7Bf592FefFc8D2D9a890508"
YAKI_MON_MARKET_ADDRESS = "0xD5c1DC181C359f0199C83045a85CD2556B325dE0"

# Legacy constant for backward compatibility (points to Router)
KURU_CONTRACT_ADDRESS_TESTNET = KURU_ROUTER_ADDRESS_TESTNET

# Mainnet Addresses (not launched yet)
KURU_CONTRACT_ADDRESS_MAINNET = None  # TBD - Mainnet not launched yet

# Kuru Event Signatures (Keccak256 hashes of event signatures)
# These are placeholders - actual values should be obtained from Kuru contracts
ORDER_PLACED_EVENT_SIGNATURE = (
    "0x" + "0" * 64
)  # OrderPlaced(address,string,uint256,uint256,uint256,uint8)
TRADE_EXECUTED_EVENT_SIGNATURE = (
    "0x" + "1" * 64
)  # TradeExecuted(address,string,uint256,uint256,uint256,uint8)
ORDER_CANCELLED_EVENT_SIGNATURE = "0x" + "2" * 64  # OrderCancelled(address,uint256)
MARGIN_DEPOSIT_EVENT_SIGNATURE = "0x" + "3" * 64  # MarginDeposit(address,address,uint256)

# Gas Configuration
DEFAULT_GAS_LIMIT = 300_000  # Default gas limit for transactions
DEFAULT_GAS_PRICE_GWEI = 20  # Default gas price in Gwei (20 Gwei)

# Retry Configuration
MAX_RETRIES = 3  # Maximum number of retry attempts for failed operations
RETRY_BACKOFF_SECONDS = 2  # Initial backoff time in seconds (exponential backoff)

# Transaction Confirmation
CONFIRMATION_BLOCKS = 1  # Number of blocks to wait for confirmation
TRANSACTION_TIMEOUT_SECONDS = 120  # Timeout for transaction confirmation

# Polling Intervals
BLOCK_POLLING_INTERVAL_SECONDS = 1  # How often to poll for new blocks
WALLET_MONITORING_INTERVAL_SECONDS = 2  # How often to check wallet transactions

# Order Configuration
MIN_ORDER_SIZE_USD = 1.0  # Minimum order size in USD
MAX_SLIPPAGE_PERCENT = 5.0  # Maximum allowed slippage percentage
