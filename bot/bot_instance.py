import asyncio
from aiogram import Bot

from bot.core.config import settings

loop = asyncio.get_event_loop()
bot = Bot(settings.TOKEN, loop=loop)

version = "0.1.2"
link = "https://github.com/denver-code/passport-status-bot/releases/tag/v0.1.2"
codename = "Silence"
