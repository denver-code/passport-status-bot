"""
Enhanced user models with proper validation, indexing, and type safety.
"""

from datetime import UTC, datetime

from beanie import Document
from pydantic import Field, field_validator
from pymongo import ASCENDING, IndexModel


class UserModel(Document):
    """User model with enhanced validation and indexing."""

    telegram_id: str = Field(
        ...,
        description="Telegram user ID",
        pattern=r"^\d+$",
        min_length=1,
        max_length=20,
    )

    session_id: str = Field(
        ..., description="MFA session ID", min_length=6, max_length=20
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(default=True, description="User account status")

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session ID format."""
        if not v.isdigit():
            raise ValueError("Session ID must contain only digits")
        return v

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id(cls, v: str) -> str:
        """Validate Telegram ID format."""
        if not v.isdigit():
            raise ValueError("Telegram ID must contain only digits")
        if int(v) <= 0:
            raise ValueError("Telegram ID must be positive")
        return v

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("telegram_id", ASCENDING)], unique=True),
            IndexModel([("session_id", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)]),
            IndexModel([("is_active", ASCENDING)]),
        ]


class SubscriptionModel(Document):
    """Subscription model with enhanced validation and constraints."""

    telegram_id: str = Field(
        ...,
        description="Telegram user ID",
        pattern=r"^\d+$",
        min_length=1,
        max_length=20,
    )

    session_id: str = Field(
        ..., description="MFA session ID to monitor", min_length=6, max_length=20
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(default=True, description="Subscription status")
    last_checked: datetime | None = Field(None, description="Last status check time")
    check_count: int = Field(default=0, ge=0, description="Number of status checks")

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session ID format."""
        if not v.isdigit():
            raise ValueError("Session ID must contain only digits")
        return v

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id(cls, v: str) -> str:
        """Validate Telegram ID format."""
        if not v.isdigit():
            raise ValueError("Telegram ID must contain only digits")
        if int(v) <= 0:
            raise ValueError("Telegram ID must be positive")
        return v

    def mark_checked(self) -> None:
        """Update check timestamp and increment counter."""
        self.last_checked = datetime.now(UTC)
        self.check_count += 1

    @classmethod
    async def get_user_subscriptions(
        cls, telegram_id: str, active_only: bool = True
    ) -> list["SubscriptionModel"]:
        """Get all subscriptions for a user."""
        query: dict[str, str | bool] = {"telegram_id": telegram_id}
        if active_only:
            query["is_active"] = True
        result: list[SubscriptionModel] = await cls.find(query).to_list()
        return result

    @classmethod
    async def count_user_subscriptions(cls, telegram_id: str) -> int:
        """Count active subscriptions for a user."""
        count = await cls.find({"telegram_id": telegram_id, "is_active": True}).count()
        return int(count)

    @classmethod
    async def subscription_exists(cls, telegram_id: str, session_id: str) -> bool:
        """Check if subscription already exists."""
        return (
            await cls.find_one(
                {
                    "telegram_id": telegram_id,
                    "session_id": session_id,
                    "is_active": True,
                }
            )
            is not None
        )

    class Settings:
        name = "subscriptions"
        indexes = [
            IndexModel(
                [("telegram_id", ASCENDING), ("session_id", ASCENDING)], unique=True
            ),
            IndexModel([("telegram_id", ASCENDING)]),
            IndexModel([("session_id", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)]),
            IndexModel([("is_active", ASCENDING)]),
            IndexModel([("last_checked", ASCENDING)]),
        ]
