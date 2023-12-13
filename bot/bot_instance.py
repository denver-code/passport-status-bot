import asyncio
from aiogram import Bot

from bot.core.config import settings

loop = asyncio.get_event_loop()
bot = Bot(settings.TOKEN, loop=loop)
