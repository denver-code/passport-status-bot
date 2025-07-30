from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.core.logger import log_error, log_function, log_info


def get_safe_user_id(event: TelegramObject) -> int | None:
    """Safely extract user ID from event."""
    if hasattr(event, "from_user") and event.from_user:
        return int(event.from_user.id)  # Explicitly cast to int
    return None


class LoggerMiddleware(BaseMiddleware):
    @log_function("setup_logger_middleware")
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        This handler is called when dispatcher receives a message
        """
        try:
            if hasattr(event, "from_user") and event.from_user:
                user_id = event.from_user.id
                username = event.from_user.username or "No username"
                message_text = (
                    getattr(event, "text", None)
                    or getattr(event, "caption", None)
                    or "[Media/File]"
                )

                # Log the message
                log_info(f"Message from @{username}: {message_text}", user_id)

                # Also keep the old file logging for backward compatibility
                with open("out.txt", "a", encoding="utf-8") as f:
                    print(
                        f"\nПрийшло повідомлення від {user_id} (@{username}) з текстом: {message_text}",
                        file=f,
                    )
        except Exception as e:
            log_error("Error in LoggerMiddleware", get_safe_user_id(event), e)

        return await handler(event, data)
