"""
Comprehensive test utilities and fixtures for the bot application.
"""

import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

# Set up test environment variables before importing settings
os.environ.setdefault("TOKEN", "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890TEST")
os.environ.setdefault("ADMIN_ID", "123456789")
os.environ.setdefault("DATABASE_URL", "mongodb://localhost:27017")
os.environ.setdefault("DATABASE_NAME", "test_mfa_passport_bot")

from bot.core.config import settings
from bot.core.models.user import SubscriptionModel, UserModel


class MockTelegramUser:
    """Mock Telegram user for testing."""

    def __init__(self, user_id: int = 12345, username: str = "testuser"):
        self.id = user_id
        self.username = username
        self.first_name = "Test"
        self.last_name = "User"
        self.is_bot = False


class MockTelegramMessage:
    """Mock Telegram message for testing."""

    def __init__(self, text: str = "/test", user_id: int = 12345, chat_id: int = 12345):
        self.text = text
        self.from_user = MockTelegramUser(user_id)
        self.chat = MagicMock()
        self.chat.id = chat_id
        self.message_id = 1
        self.date = datetime.now(UTC)

        # Mock async methods
        self.answer = AsyncMock()
        self.edit_text = AsyncMock()
        self.delete = AsyncMock()

        # Mock bot reference
        self.bot = MagicMock()
        self.bot.get_file = AsyncMock()
        self.bot.download_file = AsyncMock()


class MockCallback:
    """Mock callback query for testing."""

    def __init__(self, data: str = "test_callback", user_id: int = 12345):
        self.data = data
        self.from_user = MockTelegramUser(user_id)
        self.message = MockTelegramMessage(user_id=user_id)
        self.answer = AsyncMock()


@pytest.fixture
def mock_message() -> MockTelegramMessage:
    """Create mock Telegram message."""
    return MockTelegramMessage()


@pytest.fixture
def mock_admin_message() -> MockTelegramMessage:
    """Create mock admin message."""
    admin_id = int(settings.ADMIN_ID)
    return MockTelegramMessage(user_id=admin_id)


@pytest.fixture
def mock_callback() -> MockCallback:
    """Create mock callback query."""
    return MockCallback()


@pytest.fixture
async def test_user(db_client: Any) -> AsyncGenerator[UserModel, None]:
    """Create test user in database."""
    user = UserModel(telegram_id="12345", session_id="1234567")
    await user.insert()
    yield user
    await user.delete()


@pytest.fixture
async def test_subscription(db_client: Any) -> AsyncGenerator[SubscriptionModel, None]:
    """Create test subscription in database."""
    subscription = SubscriptionModel(telegram_id="12345", session_id="1234567")
    await subscription.insert()
    yield subscription
    await subscription.delete()


# Test database fixture
@pytest.fixture
async def db_client() -> AsyncGenerator[Any, None]:
    """Create test database client."""
    client: AsyncIOMotorClient = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_mfa_bot

    # Initialize test collections
    await db.users.delete_many({})
    await db.subscriptions.delete_many({})
    await db.applications.delete_many({})

    yield db

    # Cleanup after tests
    await db.users.delete_many({})
    await db.subscriptions.delete_many({})
    await db.applications.delete_many({})
    client.close()


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_user_data(
        telegram_id: str = "12345", session_id: str = "1234567"
    ) -> dict[str, Any]:
        """Create user test data."""
        return {
            "telegram_id": telegram_id,
            "session_id": session_id,
            "created_at": datetime.now(UTC),
            "is_active": True,
        }

    @staticmethod
    def create_subscription_data(
        telegram_id: str = "12345", session_id: str = "1234567"
    ) -> dict[str, Any]:
        """Create subscription test data."""
        return {
            "telegram_id": telegram_id,
            "session_id": session_id,
            "created_at": datetime.now(UTC),
            "is_active": True,
        }

    @staticmethod
    def create_status_data() -> list[dict[str, Any]]:
        """Create status test data."""
        return [
            {"status": "Заявка подана", "date": "1640995200000"},
            {"status": "Заявка в обробці", "date": "1641081600000"},
        ]


# Async test utilities
class AsyncTestCase:
    """Base class for async test cases."""

    @staticmethod
    async def assert_message_sent(
        mock_message: MockTelegramMessage, expected_text: str
    ) -> None:
        """Assert that a message was sent with expected text."""
        mock_message.answer.assert_called()
        call_args = mock_message.answer.call_args[0]
        assert expected_text in call_args[0]

    @staticmethod
    async def assert_message_edited(
        mock_message: MockTelegramMessage, expected_text: str
    ) -> None:
        """Assert that a message was edited with expected text."""
        mock_message.edit_text.assert_called()
        call_args = mock_message.edit_text.call_args[0]
        assert expected_text in call_args[0]
