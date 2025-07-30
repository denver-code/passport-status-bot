"""
Subscription management commands.
"""

import secrets

from aiogram import types

from bot.core.constants import (
    NOT_SUBSCRIBED,
    PUSH_SUCCESS_MESSAGE,
    STATUS_NOT_CHANGED,
    SUBSCRIPTION_CREATE_FAILED,
    SUBSCRIPTION_LIMIT_REACHED,
    SUCCESS_SUBSCRIPTION_CREATED,
    SUCCESS_UNSUBSCRIPTION,
    WAIT_CHECKING,
    WAIT_SUBSCRIPTION_PROCESSING,
)
from bot.core.logger import log_error, log_function
from bot.core.models.push import PushModel
from bot.core.utils import (
    get_user_by_message,
    handle_invalid_session_id,
    handle_user_not_found,
    safe_edit_message,
    show_typing_and_wait_message,
)
from bot.services.user_service import ApplicationStatusManager, SubscriptionManager


class SubscriptionCommands:
    """Commands for managing user subscriptions."""

    @staticmethod
    @log_function("subscribe")
    async def subscribe(message: types.Message) -> None:
        """Subscribe user to notifications for session IDs."""
        _message = await show_typing_and_wait_message(message, WAIT_CHECKING)
        if not _message:
            return

        try:
            parts = message.text.split() if message.text else []
            if len(parts) <= 1:
                await handle_invalid_session_id(_message, "/subscribe")
                return

            # Check subscription limit
            user_id = message.from_user.id if message.from_user else None
            if not user_id or await SubscriptionManager.check_subscription_limit(
                user_id
            ):
                await safe_edit_message(_message, SUBSCRIPTION_LIMIT_REACHED)
                return

            session_ids = parts[1:]
            successful_subscriptions = 0

            for session_id in session_ids:
                await safe_edit_message(
                    _message, WAIT_SUBSCRIPTION_PROCESSING.format(session_id=session_id)
                )

                if await SubscriptionManager.create_subscription(user_id, session_id):
                    successful_subscriptions += 1

            if successful_subscriptions > 0:
                await safe_edit_message(_message, SUCCESS_SUBSCRIPTION_CREATED)
            else:
                await safe_edit_message(_message, SUBSCRIPTION_CREATE_FAILED)

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Subscribe command failed", user_id, e)

    @staticmethod
    @log_function("unsubscribe")
    async def unsubscribe(message: types.Message) -> None:
        """Unsubscribe user from notifications."""
        _message = await show_typing_and_wait_message(message, WAIT_CHECKING)
        if not _message:
            return

        try:
            parts = message.text.split(" ") if message.text else []
            if len(parts) != 2:
                await handle_invalid_session_id(_message, "/unsubscribe")
                return

            session_id = parts[1]
            user_id = message.from_user.id if message.from_user else None
            if not user_id:
                return

            success = await SubscriptionManager.remove_subscription(user_id, session_id)

            if success:
                await safe_edit_message(_message, SUCCESS_UNSUBSCRIPTION)
            else:
                await safe_edit_message(_message, NOT_SUBSCRIBED)

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Unsubscribe command failed", user_id, e)

    @staticmethod
    @log_function("subscriptions_list")
    async def subscriptions_list(message: types.Message) -> None:
        """Show user's subscription list."""
        _message = await show_typing_and_wait_message(message, WAIT_CHECKING)
        if not _message:
            return

        try:
            user_id = message.from_user.id if message.from_user else None
            if not user_id:
                return

            subscriptions = await SubscriptionManager.get_user_subscriptions(user_id)
            formatted_text = SubscriptionManager.format_subscription_list(subscriptions)
            await safe_edit_message(_message, formatted_text, parse_mode="Markdown")

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Subscriptions list command failed", user_id, e)

    @staticmethod
    @log_function("update_status")
    async def update_status(message: types.Message) -> None:
        """Manually update application status."""
        _message = await show_typing_and_wait_message(message, WAIT_CHECKING)
        if not _message:
            return

        try:
            user = await get_user_by_message(message)
            if not user:
                await handle_user_not_found(_message)
                return

            (
                success,
                application,
            ) = await ApplicationStatusManager.update_application_status(
                user.session_id
            )

            if success and application:
                from bot.core.utils import format_application_statuses_section

                status_section = format_application_statuses_section(
                    application.statuses
                )
                await safe_edit_message(_message, status_section, parse_mode="Markdown")
            else:
                await safe_edit_message(_message, STATUS_NOT_CHANGED)

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Update status command failed", user_id, e)

    @staticmethod
    @log_function("push_notifications")
    async def push_notifications(message: types.Message) -> None:
        """Setup push notifications via NTFY.sh."""
        _message = await show_typing_and_wait_message(message, WAIT_CHECKING)
        if not _message:
            return

        try:
            user = await get_user_by_message(message)
            if not user:
                await handle_user_not_found(_message)
                return

            # Check if push already exists
            from bot.core.utils import get_user_id_str

            existing_push = await PushModel.find_one(
                {"telegram_id": get_user_id_str(message)}
            )
            if existing_push:
                await safe_edit_message(
                    _message,
                    f"Push notifications already configured: `{existing_push.secret_id}`",
                )
                return

            # Create new push configuration
            secret_id = secrets.token_hex(8)
            push_model = PushModel(
                telegram_id=get_user_id_str(message), secret_id=secret_id
            )
            await push_model.insert()

            if message.from_user:
                await safe_edit_message(
                    _message,
                    PUSH_SUCCESS_MESSAGE.format(
                        secret_id=secret_id, user_id=message.from_user.id
                    ),
                    parse_mode="Markdown",
                )

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Push notifications command failed", user_id, e)

    @staticmethod
    @log_function("dump_subscriptions")
    async def dump_subscriptions(message: types.Message) -> None:
        """Dump all subscription data for user."""
        _message = await show_typing_and_wait_message(message, WAIT_CHECKING)
        if not _message:
            return

        try:
            user_id = message.from_user.id if message.from_user else None
            if not user_id:
                return

            subscriptions = await SubscriptionManager.get_user_subscriptions(user_id)

            if not subscriptions:
                await safe_edit_message(_message, NOT_SUBSCRIBED)
                return

            # Create comprehensive dump
            dump_lines = ["*Dump ваших підписок:*\n"]

            for i, subscription in enumerate(subscriptions, 1):
                application = await ApplicationStatusManager.get_application_status(
                    subscription.session_id
                )

                dump_lines.append(f"*{i}. Заявка #{subscription.session_id}*")

                if application and application.statuses:
                    latest_status = (
                        application.statuses[-1] if application.statuses else None
                    )
                    if latest_status:
                        from bot.core.utils import _get_formatted_date

                        date = _get_formatted_date(latest_status)
                        dump_lines.append(f"   Статус: {latest_status.status}")
                        dump_lines.append(f"   Дата: {date}")

                    dump_lines.append(
                        f"   Останнє оновлення: {application.last_update.strftime('%Y-%m-%d %H:%M')}"
                    )
                else:
                    dump_lines.append("   Статус: Не знайдено")

                dump_lines.append("")

            dump_text = "\n".join(dump_lines)
            await safe_edit_message(_message, dump_text, parse_mode="Markdown")

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Dump subscriptions command failed", user_id, e)
