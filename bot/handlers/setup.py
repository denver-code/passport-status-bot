from aiogram import Dispatcher

from bot.handlers import start, message, cabinet, subscriptions


def setup(dp: Dispatcher):
    start.setup(dp)
    message.setup(dp)
    cabinet.setup(dp)
    subscriptions.setup(dp)
