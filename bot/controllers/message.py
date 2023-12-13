from datetime import datetime
from aiogram import types

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
