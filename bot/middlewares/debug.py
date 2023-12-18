import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled


class LoggerMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        """
        This handler is called when dispatcher receives a message

        :param message:

        """
        with open("out.txt", "w") as f:
            print(
                f"Прийшло повідомлення від {message.from_user.id} з текстом: {message}",
                file=f,
            )
