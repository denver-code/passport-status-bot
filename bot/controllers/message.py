from datetime import datetime
from email.mime import image
from aiogram import types
from PIL import Image
import numpy as np
from qreader import QReader
import cv2
from bot.core.api import Scraper


async def custom_check(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває перевірка...")
    await message.answer_chat_action("typing")

    scraper = Scraper()

    status = scraper.check(message.text, retrive_all=True)
    if not status:
        await _message.edit_text("Виникла помилка, спробуйте пізніше.")
        return

    _msg_text = f"Статуси заявки *#{message.text}:*\n\n"

    for i, s in enumerate(status):
        _date = datetime.fromtimestamp(int(s.get("date")) / 1000).strftime(
            "%Y-%m-%d %H:%M"
        )
        _msg_text += f"{i+1}. *{s.get('status')}* \n_{_date}_\n\n"

    await _message.edit_text(_msg_text, parse_mode="Markdown")


# image qr recognition
async def image_qr_recognition(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває аналіз фото...")
    await message.answer_chat_action("typing")

    file = await message.bot.get_file(message.photo[-1].file_id)
    download_file = await message.bot.download_file(file.file_path)

    photo: Image = Image.open(download_file)
    image = cv2.cvtColor(np.array(photo), cv2.COLOR_RGB2BGR)

    qr = QReader()

    decoded = qr.detect_and_decode(image=image)

    if not decoded:
        await _message.edit_text(
            "Жодного QR-коду не знайдено, спробуйте ще раз з іншим фото."
        )
        return

    decoded_code = decoded[0]

    if len(decoded_code) != 7:
        await _message.edit_text("Схоже на те, що це некоректний QR-код.")
        return

    _message = await _message.edit_text(
        "Зачекайте, будь ласка, триває перевірка коду..."
    )
    await message.answer_chat_action("typing")

    scraper = Scraper()

    status = scraper.check(decoded_code, retrive_all=True)
    if not status:
        await _message.edit_text("Виникла помилка, спробуйте пізніше.")
        return

    _msg_text = f"Статуси заявки *#{decoded_code}:*\n\n"

    for i, s in enumerate(status):
        _date = datetime.fromtimestamp(int(s.get("date")) / 1000).strftime(
            "%Y-%m-%d %H:%M"
        )
        _msg_text += f"{i+1}. *{s.get('status')}* \n_{_date}_\n\n"

    await _message.edit_text(_msg_text, parse_mode="Markdown")
