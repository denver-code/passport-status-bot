from aiogram import Dispatcher
from bot.controllers.start import start, policy, help


def setup(dp: Dispatcher):
    dp.register_message_handler(start, commands=["start"], state="*")
    dp.register_message_handler(policy, commands=["policy"], state="*")
    dp.register_message_handler(help, commands=["help"], state="*")
