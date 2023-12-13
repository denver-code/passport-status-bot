from aiogram import Dispatcher

from bot.controllers.message import custom_check


def setup(dp: Dispatcher):
    dp.register_message_handler(custom_check, regexp=r"^\d{7}$", state="*")
