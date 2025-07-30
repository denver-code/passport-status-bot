"""
Custom exception classes for better error handling and categorization.
"""

from typing import Any


class BotError(Exception):
    """Base exception for all bot-related errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(BotError):
    """Raised when configuration is invalid or missing."""

    pass


class DatabaseError(BotError):
    """Base exception for database-related errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class DocumentNotFoundError(DatabaseError):
    """Raised when a required document is not found in database."""

    pass


class UserError(BotError):
    """Base exception for user-related errors."""

    pass


class UserNotFoundError(UserError):
    """Raised when user is not found in database."""

    pass


class UserPermissionError(UserError):
    """Raised when user lacks required permissions."""

    pass


class SubscriptionError(BotError):
    """Base exception for subscription-related errors."""

    pass


class SubscriptionLimitError(SubscriptionError):
    """Raised when user has reached subscription limit."""

    pass


class SubscriptionNotFoundError(SubscriptionError):
    """Raised when subscription is not found."""

    pass


class ExternalServiceError(BotError):
    """Base exception for external service errors."""

    pass


class ScraperError(ExternalServiceError):
    """Raised when scraper fails to get data."""

    pass


class NotificationError(ExternalServiceError):
    """Raised when notification sending fails."""

    pass


class ValidationError(BotError):
    """Raised when data validation fails."""

    pass


class RateLimitError(BotError):
    """Raised when rate limit is exceeded."""

    pass


class TimeoutError(BotError):
    """Raised when operation times out."""

    pass


# Error code constants
class ErrorCodes:
    """Standard error codes for consistent error handling."""

    # Configuration errors
    INVALID_CONFIG = "CONFIG_001"
    MISSING_CONFIG = "CONFIG_002"

    # Database errors
    DB_CONNECTION_FAILED = "DB_001"
    DB_QUERY_FAILED = "DB_002"
    DB_DOCUMENT_NOT_FOUND = "DB_003"

    # User errors
    USER_NOT_FOUND = "USER_001"
    USER_PERMISSION_DENIED = "USER_002"
    USER_ALREADY_EXISTS = "USER_003"

    # Subscription errors
    SUBSCRIPTION_LIMIT_REACHED = "SUB_001"
    SUBSCRIPTION_NOT_FOUND = "SUB_002"
    SUBSCRIPTION_ALREADY_EXISTS = "SUB_003"

    # External service errors
    SCRAPER_FAILED = "EXT_001"
    NOTIFICATION_FAILED = "EXT_002"
    EXTERNAL_API_ERROR = "EXT_003"

    # Validation errors
    INVALID_SESSION_ID = "VAL_001"
    INVALID_USER_INPUT = "VAL_002"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_001"

    # Timeout errors
    OPERATION_TIMEOUT = "TIME_001"
