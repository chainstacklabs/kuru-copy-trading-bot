"""Core exceptions for the Kuru copy trading bot."""


class KuruCopyTradingBotException(Exception):
    """Base exception for all bot errors."""

    pass


class InvalidStateTransition(KuruCopyTradingBotException):
    """Raised when an invalid state transition is attempted."""

    pass


class BlockchainConnectionError(KuruCopyTradingBotException):
    """Raised when blockchain connection fails."""

    pass


class TransactionFailedError(KuruCopyTradingBotException):
    """Raised when a transaction fails."""

    pass


class InsufficientGasError(KuruCopyTradingBotException):
    """Raised when there's insufficient gas for a transaction."""

    pass


class InsufficientBalanceError(KuruCopyTradingBotException):
    """Raised when there's insufficient balance for an operation."""

    pass


class OrderExecutionError(KuruCopyTradingBotException):
    """Raised when order execution fails."""

    pass


class TradeValidationError(KuruCopyTradingBotException):
    """Raised when trade validation fails."""

    pass


class InvalidMarketError(KuruCopyTradingBotException):
    """Raised when an invalid or unknown market is specified."""

    pass


class ConfigurationError(KuruCopyTradingBotException):
    """Raised when configuration is invalid."""

    pass


class InvalidOrderError(KuruCopyTradingBotException):
    """Raised when order parameters are invalid."""

    pass


class OrderPlacementError(KuruCopyTradingBotException):
    """Raised when order placement fails."""

    pass
