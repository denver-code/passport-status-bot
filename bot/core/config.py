"""
Enhanced configuration management with proper validation and security.
"""

from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with enhanced validation and security."""

    # Bot Configuration
    TOKEN: SecretStr = Field(
        ...,
        description="Telegram Bot API token",
        min_length=45,  # Telegram tokens are typically 45+ characters
    )

    ADMIN_ID: str = Field(
        ...,
        description="Telegram Admin User ID",
        pattern=r"^\d+$",  # Only digits allowed
    )

    # Database Configuration
    DATABASE_URL: str = Field(
        default="mongodb://localhost:27003", description="MongoDB connection URL"
    )

    DATABASE_NAME: str = Field(
        default="mfa_passport_bot",
        description="Database name",
        min_length=1,
        max_length=64,
    )

    # Optional Configuration
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    MAX_SUBSCRIPTIONS_PER_USER: int = Field(default=5, ge=1, le=20)
    RATE_LIMIT_REQUESTS: int = Field(default=3, ge=1, le=100)
    RATE_LIMIT_WINDOW: int = Field(default=60, ge=1, le=3600)  # seconds

    # External Services
    NTFY_BASE_URL: str = Field(
        default="https://ntfy.sh", description="NTFY service URL"
    )

    # Security
    ALLOWED_UPDATES: list[str] = Field(
        default=["message", "callback_query"], description="Allowed update types"
    )

    # Performance
    MAX_CONCURRENT_REQUESTS: int = Field(default=100, ge=1, le=1000)
    REQUEST_TIMEOUT: int = Field(default=30, ge=5, le=300)  # seconds

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_assignment=True,
        extra="ignore",  # Ignore unknown environment variables
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate MongoDB connection URL format."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError(
                "DATABASE_URL must start with mongodb:// or mongodb+srv://"
            )

        try:
            parsed = urlparse(v)
            if not parsed.hostname:
                raise ValueError("DATABASE_URL must contain a valid hostname")
        except Exception as e:
            raise ValueError(f"Invalid DATABASE_URL format: {e}")

        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()

    @field_validator("NTFY_BASE_URL")
    @classmethod
    def validate_ntfy_url(cls, v: str) -> str:
        """Validate NTFY service URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("NTFY_BASE_URL must be a valid HTTP(S) URL")
        return v.rstrip("/")  # Remove trailing slash

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG

    @property
    def admin_id_int(self) -> int:
        """Get admin ID as integer."""
        return int(self.ADMIN_ID)

    @property
    def bot_token(self) -> str:
        """Get bot token as string."""
        return self.TOKEN.get_secret_value()

    def get_database_url(self, include_db_name: bool = True) -> str:
        """Get database URL with optional database name."""
        base_url = self.DATABASE_URL.rstrip("/")
        if include_db_name:
            return f"{base_url}/{self.DATABASE_NAME}"
        return base_url


# Global settings instance
try:
    settings = Settings()  # type: ignore[call-arg]
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    print("Please check your .env file and ensure all required variables are set.")
    raise SystemExit(1)


# Validation on startup
def validate_configuration() -> None:
    """Validate configuration on application startup."""
    errors = []

    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        errors.append(
            "❌ .env file not found. Please copy sample.env to .env and configure it."
        )

    # Validate critical settings
    try:
        if len(settings.bot_token) < 45:
            errors.append("❌ Invalid TOKEN: Telegram bot token is too short")
    except Exception:
        errors.append("❌ TOKEN is required and must be a valid Telegram bot token")

    try:
        admin_id = int(settings.ADMIN_ID)
        if admin_id <= 0:
            errors.append("❌ ADMIN_ID must be a positive integer")
    except ValueError:
        errors.append("❌ ADMIN_ID must be a valid integer")

    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(error)
        raise SystemExit(1)


# Export commonly used values
__all__ = ["settings", "validate_configuration"]
