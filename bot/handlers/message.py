from aiogram import Dispatcher

from bot.controllers.message import custom_check, image_qr_recognition


def setup(dp: Dispatcher):
    dp.register_message_handler(custom_check, regexp=r"^\d{7}$", state="*")
    dp.register_message_handler(
        image_qr_recognition, content_types=["photo"], state="*"
    )
