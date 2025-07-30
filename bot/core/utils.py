"""
Core utility functions - streamlined to avoid redundancy with services.
Now focuses only on low-level helper functions.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any, cast

from aiogram import types

from bot.core.constants import (
    ADMIN_PERMISSION_DENIED,
    ERROR_GENERIC_DETAILED,
    ERROR_IDENTIFIER_VALIDATION,
    HEADER_APPLICATION_STATUSES,
    INSTRUCTION_INVALID_SESSION_ID,
    NOT_FOUND_IDENTIFIER,
    STATUS_APPLICATION_HEADER,
    STATUS_GENERAL_HEADER,
    WAIT_CHECKING,
)
from bot.core.logger import log_error
from bot.core.models.application import ApplicationModel, StatusModel
from bot.core.models.user import UserModel

# === BASIC UTILITY FUNCTIONS ===


def get_user_id_str(message: types.Message) -> str:
    """Convert message user ID to string."""
    if message.from_user is None:
        raise ValueError("Message has no from_user")
    return str(message.from_user.id)


def get_safe_user_id(message: types.Message) -> int | None:
    """Safely extract user ID from message."""
    if message.from_user:
        return int(message.from_user.id)
    return None


async def get_user_by_telegram_id(telegram_id: int) -> UserModel | None:
    """Get a user by Telegram ID as string."""
    result = await UserModel.find_one({"telegram_id": str(telegram_id)})
    return cast(UserModel | None, result)


async def get_user_by_message(message: types.Message) -> UserModel | None:
    """Get user by message."""
    result = await UserModel.find_one({"telegram_id": get_user_id_str(message)})
    return cast(UserModel | None, result)


async def get_application_by_session_id(session_id: str) -> ApplicationModel | None:
    """Get application by session ID."""
    result = await ApplicationModel.find_one({"session_id": session_id})
    return cast(ApplicationModel | None, result)


async def process_status_update(
    application: ApplicationModel, scraper: Any, notify_subscribers_func: Callable
) -> None:
    """Process status updates for an application and notify subscribers if there are new statuses."""
    try:
        # Fetch current statuses from the API using the correct method name
        current_statuses_data = scraper.check(application.session_id, retrive_all=True)

        if not current_statuses_data:
            return

        # Convert API response to StatusModel objects
        current_statuses = create_status_models_from_api_response(current_statuses_data)

        # Get existing statuses from the application
        existing_statuses = application.statuses or []

        # Find new statuses by comparing with existing ones
        new_statuses = []
        existing_status_texts = {status.status for status in existing_statuses}

        for status in current_statuses:
            if status.status not in existing_status_texts:
                new_statuses.append(status)

        # If there are new statuses, update the application and notify subscribers
        if new_statuses:
            # Update the application with all current statuses
            application.statuses = current_statuses
            await application.save()

            # Notify subscribers about new statuses
            await notify_subscribers_func(
                target_application=application, new_statuses=new_statuses
            )

    except Exception as e:
        from bot.core.logger import log_error

        log_error(
            f"Error processing status update for session {application.session_id}",
            exception=e,
        )
        raise


# === PERMISSION CHECKING ===


async def admin_permission_check(obj: types.Message | types.CallbackQuery) -> bool:
    """Check admin permission and send error message if not admin."""
    from bot.services import BotService

    if isinstance(obj, types.CallbackQuery):
        user_id = obj.from_user.id if obj.from_user else None
        message = obj.message
    else:
        user_id = obj.from_user.id if obj.from_user else None
        message = obj

    if not user_id or not BotService.is_admin(user_id):
        try:
            if message:
                await message.answer(ADMIN_PERMISSION_DENIED)
        except Exception as e:
            log_error("Failed to send admin permission error", user_id, e)
        return False
    return True


# === MESSAGE HANDLING UTILITIES ===


async def safe_edit_message(
    message: types.Message, text: str, parse_mode: str | None = None
) -> None:
    """Safely edit a message with error handling."""
    try:
        await message.edit_text(text, parse_mode=parse_mode)
    except Exception as e:
        log_error("Failed to edit message", get_safe_user_id(message), e)
        try:
            await message.answer(text, parse_mode=parse_mode)
        except Exception as fallback_error:
            log_error(
                "Failed to send fallback message",
                get_safe_user_id(message),
                fallback_error,
            )


async def safe_answer_message(
    message: types.Message, text: str, parse_mode: str | None = None
) -> types.Message | None:
    """Safely answer a message with error handling."""
    try:
        return await message.answer(text, parse_mode=parse_mode)
    except Exception as e:
        log_error("Failed to answer message", get_safe_user_id(message), e)
        return None


async def safe_edit_message_markdown(message: types.Message, text: str) -> None:
    """Safely edit message with markdown."""
    await safe_edit_message(message, text, parse_mode="Markdown")


async def safe_answer_message_markdown(
    message: types.Message, text: str
) -> types.Message | None:
    """Safely answer message with markdown."""
    try:
        return await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        log_error(
            "Failed to answer message with markdown", get_safe_user_id(message), e
        )
        return None


async def show_typing_action(message: types.Message) -> None:
    """Show typing action."""
    from bot.bot_instance import bot

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")


async def show_typing_and_wait_message(
    message: types.Message, wait_text: str | None = None
) -> types.Message | None:
    """Show typing indicator and send a wait message."""
    if wait_text is None:
        wait_text = WAIT_CHECKING
    await show_typing_action(message)
    return await safe_answer_message(message, wait_text)


# === STATUS FORMATTING UTILITIES ===


def _get_formatted_date(status: StatusModel) -> str:
    """Extract formatted date from status."""
    return datetime.fromtimestamp(int(status.date) / 1000).strftime("%Y-%m-%d %H:%M")


def _format_single_status(status: StatusModel, index: int) -> str:
    """Format a single status entry."""
    date = _get_formatted_date(status)
    return f"{index}. *{status.status}* _{date}_\n\n"


def format_new_status_message(session_id: str, new_statuses: list[StatusModel]) -> str:
    """Format new status updates for notifications."""
    if not new_statuses:
        return "Немає нових статусів."

    header = f"🔔 *Нові статуси для заявки {session_id}*\n\n"
    msg_text = header

    for status in new_statuses:
        date = _get_formatted_date(status)
        msg_text += f"📋 *{status.status}*\n⏰ _{date}_\n\n"

    return msg_text


def format_status_list(
    statuses: list[StatusModel], session_id: str | None = None
) -> str:
    """Format a list of statuses into readable text."""
    if not statuses:
        return "Немає статусів для відображення."

    header = (
        STATUS_APPLICATION_HEADER.format(session_id=session_id)
        if session_id
        else STATUS_GENERAL_HEADER
    )
    msg_text = header

    for i, status in enumerate(statuses, start=1):
        msg_text += _format_single_status(status, i)

    return msg_text


def format_application_statuses_section(statuses: list[StatusModel]) -> str:
    """Format application statuses section for cabinet display."""
    if not statuses:
        return ""

    msg_text = HEADER_APPLICATION_STATUSES
    for i, status in enumerate(statuses, start=1):
        msg_text += _format_single_status(status, i)

    return msg_text


def create_status_models_from_api_response(
    status_data: list[dict],
) -> list[StatusModel]:
    """Convert API response status data to StatusModel objects."""
    return [
        StatusModel(status=str(s.get("status")), date=int(s.get("date", 0)))
        for s in status_data
        if s.get("status") is not None and s.get("date") is not None
    ]


# === ERROR HANDLING UTILITIES ===


async def handle_user_not_found(message: types.Message) -> None:
    """Handle case when user is not found in database."""
    await safe_edit_message(message, NOT_FOUND_IDENTIFIER)


async def handle_invalid_session_id(message: types.Message, command: str) -> None:
    """Handle case when session ID format is invalid."""
    await safe_edit_message(
        message, INSTRUCTION_INVALID_SESSION_ID.format(command=command)
    )


async def handle_scraper_error(message: types.Message) -> None:
    """Handle case when scraper fails to get data."""
    await safe_edit_message(message, ERROR_IDENTIFIER_VALIDATION)


async def handle_generic_error(message: types.Message, operation: str) -> None:
    """Handle generic errors with consistent messaging."""
    await safe_edit_message(message, ERROR_GENERIC_DETAILED.format(operation=operation))


def log_handler_error(
    handler_name: str, message: types.Message, exception: Exception
) -> None:
    """Log handler error with consistent pattern."""
    log_error(f"{handler_name} failed", get_safe_user_id(message), exception)
