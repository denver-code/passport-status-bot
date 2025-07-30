"""
User management business logic.
Handles all user-related operations including subscriptions and profiles.
"""

from datetime import datetime

from aiogram import types

from bot.core.api import Scraper
from bot.core.constants import (
    HEADER_YOUR_SUBSCRIPTIONS,
    NOT_SUBSCRIBED,
    SUBSCRIPTION_COUNT_FORMAT,
    # Add this as placeholder
)
from bot.core.logger import log_error, log_info
from bot.core.models.application import ApplicationModel
from bot.core.models.user import SubscriptionModel, UserModel
from bot.core.utils import (
    create_status_models_from_api_response,
    get_application_by_session_id,
    get_user_by_message,
    get_user_id_str,
)


class UserManager:
    """Manages user profiles and linking operations."""

    @staticmethod
    async def link_user_to_session(message: types.Message, session_id: str) -> bool:
        """Link a user to a session ID after validation."""
        try:
            # Check if user is already linked
            user = await get_user_by_message(message)
            if user and user.session_id:
                return False  # Already linked

            # Validate session ID with scraper
            scraper = Scraper()
            status_data = scraper.check(session_id, retrive_all=True)
            if not status_data:
                return False  # Invalid session

            # Create or update application
            application = await get_application_by_session_id(session_id)
            if not application:
                application = ApplicationModel(
                    session_id=session_id,
                    statuses=create_status_models_from_api_response(status_data),
                    last_update=datetime.now(),
                )
                await application.insert()

            # Create user record
            new_user = UserModel(
                telegram_id=get_user_id_str(message), session_id=session_id
            )
            await new_user.insert()

            return True

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Failed to link user to session", user_id, e)
            return False

    @staticmethod
    async def unlink_user(message: types.Message) -> str | None:
        """Unlink user from their session."""
        try:
            user = await get_user_by_message(message)
            if not user:
                return "User not found in database"

            old_session_id = user.session_id
            user.session_id = None  # type: ignore[assignment]
            await user.save()
            user_id = message.from_user.id if message.from_user else None
            log_info(f"User {user_id} unlinked from session")
            return old_session_id or "User unlinked successfully"

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Failed to unlink user", user_id, e)
            return "Failed to unlink user"


class SubscriptionManager:
    """Manages user subscriptions to status updates."""

    MAX_SUBSCRIPTIONS = 7

    @staticmethod
    async def check_subscription_limit(user_id: int) -> bool:
        """Check if user has reached subscription limit."""
        try:
            count = await SubscriptionModel.find({"telegram_id": str(user_id)}).count()
            return int(count) >= SubscriptionManager.MAX_SUBSCRIPTIONS
        except Exception as e:
            log_error("Failed to check subscription limit", user_id, e)
            return True  # Assume limit reached on error

    @staticmethod
    async def create_subscription(user_id: int, session_id: str) -> bool:
        """Create a subscription for a specific session ID."""
        try:
            # Check if subscription already exists
            existing = await SubscriptionModel.find_one(
                {"telegram_id": str(user_id), "session_id": session_id}
            )
            if existing:
                return False

            # Ensure application exists
            application = await get_application_by_session_id(session_id)
            if not application:
                scraper = Scraper()
                status_data = scraper.check(session_id, retrive_all=True)
                if not status_data:
                    return False

                application = ApplicationModel(
                    session_id=session_id,
                    statuses=create_status_models_from_api_response(status_data),
                    last_update=datetime.now(),
                )
                await application.insert()

            # Create subscription
            subscription = SubscriptionModel(
                telegram_id=str(user_id),
                session_id=session_id,
            )
            await subscription.insert()
            return True

        except Exception as e:
            log_error("Failed to create subscription", user_id, e)
            return False

    @staticmethod
    async def remove_subscription(user_id: int, session_id: str) -> bool:
        """Remove a subscription for a specific session ID."""
        try:
            subscription = await SubscriptionModel.find_one(
                {"telegram_id": str(user_id), "session_id": session_id}
            )

            if not subscription:
                return False

            await subscription.delete()
            return True

        except Exception as e:
            log_error("Failed to remove subscription", user_id, e)
            return False

    @staticmethod
    async def get_user_subscriptions(user_id: int) -> list[SubscriptionModel]:
        """Get all subscriptions for a user."""
        try:
            subs = await SubscriptionModel.find({"telegram_id": str(user_id)}).to_list()
            return list(subs)
        except Exception as e:
            log_error("Failed to get user subscriptions", user_id, e)
            return []

    @staticmethod
    def format_subscription_list(subscriptions: list[SubscriptionModel]) -> str:
        """Format subscription list into readable text."""
        if not subscriptions:
            return NOT_SUBSCRIBED

        msg_text = HEADER_YOUR_SUBSCRIPTIONS
        for i, subscription in enumerate(subscriptions, start=1):
            msg_text += f"{i}. *{subscription.session_id}* \n"

        msg_text += f"\n{SUBSCRIPTION_COUNT_FORMAT.format(count=len(subscriptions))}"
        return msg_text


class ApplicationStatusManager:
    """Manages application status tracking and updates."""

    @staticmethod
    async def get_application_status(session_id: str) -> ApplicationModel | None:
        """Get application status by session ID."""
        try:
            return await get_application_by_session_id(session_id)
        except Exception as e:
            log_error("Failed to get application status", None, e)
            return None

    @staticmethod
    async def update_application_status(
        session_id: str,
    ) -> tuple[bool, ApplicationModel | None]:
        """Update application status from external source."""
        try:
            scraper = Scraper()
            status_data = scraper.check(session_id, retrive_all=True)

            if not status_data:
                return False, None

            application = await get_application_by_session_id(session_id)
            if not application:
                application = ApplicationModel(
                    session_id=session_id,
                    statuses=create_status_models_from_api_response(status_data),
                    last_update=datetime.now(),
                )
                await application.insert()
            else:
                application.statuses = create_status_models_from_api_response(
                    status_data
                )
                application.last_update = datetime.now()
                await application.save()

            return True, application

        except Exception as e:
            log_error("Failed to update application status", None, e)
            return False, None

    @staticmethod
    def check_for_status_changes(
        current_statuses: list, previous_statuses: list
    ) -> list:
        """Check if there are new statuses compared to previous ones."""
        if len(current_statuses) > len(previous_statuses):
            return current_statuses[len(previous_statuses) :]
        return []


class CabinetManager:
    """Manages user cabinet operations and display."""

    @staticmethod
    async def get_user_cabinet_info(message: types.Message) -> dict | None:
        """Get comprehensive user cabinet information."""
        try:
            user = await get_user_by_message(message)
            if not user:
                return None

            application = await get_application_by_session_id(user.session_id)
            if not application:
                return None

            user_id = message.from_user.id if message.from_user else None
            if not user_id:
                return None

            subscriptions = await SubscriptionManager.get_user_subscriptions(user_id)

            return {
                "user": user,
                "application": application,
                "subscriptions": subscriptions,
                "user_id": user_id,
            }

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Failed to get user cabinet info", user_id, e)
            return None
