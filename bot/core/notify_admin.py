from aiogram import Bot

from bot.core.config import settings
from bot.core.logger import log_function


@log_function("notify_admin")
async def notify_admin(text: str) -> None:
    admin_id = getattr(settings, "ADMIN_ID", None)
    token = getattr(settings, "TOKEN", None)
    if not admin_id or not token:
        return
    try:
        # Unwrap SecretStr to plain string if necessary
        token_str = (
            token.get_secret_value()
            if hasattr(token, "get_secret_value")
            else str(token)
        )
        bot = Bot(token=token_str)
        await bot.send_message(chat_id=admin_id, text=text)
        await bot.session.close()
    except Exception as e:
        from bot.core.logger import log_error

        log_error("Failed to notify admin", admin_id, e)
