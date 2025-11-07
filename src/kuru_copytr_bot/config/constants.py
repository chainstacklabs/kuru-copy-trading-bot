"""Constants for the Kuru copy trading bot."""

# Monad Blockchain Chain IDs
MONAD_CHAIN_ID = 41454  # Mainnet (placeholder - to be confirmed)
MONAD_TESTNET_CHAIN_ID = 41454  # Testnet

# Kuru Contract Addresses
KURU_CONTRACT_ADDRESS_TESTNET = "0xKuruTestnetAddress0000000000000000000000"  # Placeholder
KURU_CONTRACT_ADDRESS_MAINNET = None  # To be determined when mainnet launches

# Kuru Event Signatures (Keccak256 hashes of event signatures)
# These are placeholders - actual values should be obtained from Kuru contracts
ORDER_PLACED_EVENT_SIGNATURE = "0x" + "0" * 64  # OrderPlaced(address,string,uint256,uint256,uint256,uint8)
TRADE_EXECUTED_EVENT_SIGNATURE = "0x" + "1" * 64  # TradeExecuted(address,string,uint256,uint256,uint256,uint8)
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
