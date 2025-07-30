"""
Enhanced error handling middleware with proper exception categorization and user feedback.
"""

import asyncio
from collections.abc import Callable
from typing import Any

from aiogram import BaseMiddleware, types

from bot.core.constants import (
    ADMIN_PERMISSION_DENIED,
    ANTISPAM_BANNED_MESSAGE,
    ERROR_GENERIC,
    ERROR_GENERIC_DETAILED,
    ERROR_IDENTIFIER_VALIDATION,
)
from bot.core.exceptions import (
    BotError,
    DatabaseError,
    ErrorCodes,
    ExternalServiceError,
    RateLimitError,
    UserError,
    ValidationError,
)
from bot.core.logger import log_error


class ErrorHandlerMiddleware(BaseMiddleware):
    """Enhanced error handling middleware with user-friendly messages."""

    async def __call__(
        self,
        handler: Callable,
        event: types.TelegramObject,  # Changed from types.Update to match supertype
        data: dict[str, Any],
    ) -> Any:
        """Handle errors with proper categorization and user feedback."""
        try:
            return await handler(event, data)
        except Exception as error:
            await self._handle_error(error, event, data)
            return None

    async def _handle_error(
        self,
        error: Exception,
        event: types.TelegramObject,  # Changed from types.Update
        data: dict[str, Any],
    ) -> None:
        """Process and handle different types of errors."""
        user_id = None
        message_obj = None

        # Extract user info from event - handle TelegramObject
        if isinstance(event, types.Update):
            if hasattr(event, "message") and event.message:
                message_obj = event.message
                user_id = message_obj.from_user.id if message_obj.from_user else None
            elif hasattr(event, "callback_query") and event.callback_query:
                # event.callback_query.message can be Message | InaccessibleMessage | None
                message_obj = (
                    event.callback_query.message
                    if hasattr(event.callback_query, "message")
                    and event.callback_query.message is not None
                    and not isinstance(
                        event.callback_query.message, types.InaccessibleMessage
                    )
                    else None
                )
                user_id = (
                    event.callback_query.from_user.id
                    if event.callback_query.from_user
                    else None
                )
        elif isinstance(event, types.Message):
            message_obj = event
            user_id = message_obj.from_user.id if message_obj.from_user else None

        # Log the error with context
        log_error(
            f"Error handling update: {type(error).__name__}",
            user_id=user_id,
            exception=error,
            event_type=type(event).__name__,
        )

        # Send appropriate user message
        user_message = self._get_user_message(error)
        if message_obj and user_message:
            try:
                await message_obj.answer(user_message)
            except Exception as send_error:
                log_error(
                    "Failed to send error message to user",
                    user_id=user_id,
                    exception=send_error,
                )

    def _get_user_message(self, error: Exception) -> str:
        """Get user-friendly error message based on exception type."""
        if isinstance(error, RateLimitError):
            return ANTISPAM_BANNED_MESSAGE.format(minutes=5)

        elif isinstance(error, ValidationError):
            if (
                hasattr(error, "error_code")
                and error.error_code == ErrorCodes.INVALID_SESSION_ID
            ):
                return ERROR_IDENTIFIER_VALIDATION
            return ERROR_GENERIC_DETAILED.format(operation="валідації даних")

        elif isinstance(error, UserError):
            if "permission" in str(error).lower():
                return ADMIN_PERMISSION_DENIED
            return str(error) if len(str(error)) < 200 else ERROR_GENERIC

        elif isinstance(error, DatabaseError):
            log_error("Database error occurred", exception=error)
            return ERROR_GENERIC_DETAILED.format(operation="роботі з базою даних")

        elif isinstance(error, ExternalServiceError):
            return ERROR_GENERIC_DETAILED.format(operation="отриманні даних")

        elif isinstance(error, BotError):
            # Custom bot errors with user-friendly messages
            return str(error) if len(str(error)) < 200 else ERROR_GENERIC

        else:
            # Unexpected errors
            return ERROR_GENERIC


class GlobalErrorHandler:
    """Global error handler for uncaught exceptions."""

    @staticmethod
    async def handle_startup_error(error: Exception) -> None:
        """Handle errors during bot startup."""
        log_error("Bot startup failed", exception=error)
        print(f"❌ Failed to start bot: {error}")
        raise SystemExit(1)

    @staticmethod
    async def handle_shutdown_error(error: Exception) -> None:
        """Handle errors during bot shutdown."""
        log_error("Bot shutdown error", exception=error)
        print(f"⚠️ Error during shutdown: {error}")

    @staticmethod
    def setup_exception_handlers() -> None:
        """Setup global exception handlers."""
        import sys
        from types import TracebackType

        def handle_exception(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_traceback: TracebackType | None,
        ) -> None:
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            log_error(
                "Uncaught exception",
                exception=exc_value if isinstance(exc_value, Exception) else None,
                exc_type=exc_type.__name__,
            )

        sys.excepthook = handle_exception

        # Handle asyncio exceptions
        def handle_asyncio_exception(loop: Any, context: dict[str, Any]) -> None:
            exception = context.get("exception")
            if exception:
                log_error(
                    "Asyncio exception", exception=exception, context=str(context)
                )

        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(handle_asyncio_exception)
        except RuntimeError:
            # No event loop running
            pass
