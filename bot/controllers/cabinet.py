from aiogram import types
from datetime import datetime
from textwrap import dedent
from bot.core.api import Scraper
from bot.core.models.application import ApplicationModel, StatusModel
from bot.core.models.user import UserModel


async def cabinet(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває отримання даних...")
    await message.answer_chat_action("typing")

    user = await UserModel.find_one({"telgram_id": str(message.from_user.id)})
    if not user:
        await _message.edit_text(
            "Вашого ідентифікатора не знайдено, надішліть його, будь ласка використовуючи команду /link \nНаприклад /link 1006655"
        )
        return

    initial_message = dedent(
        f"""
            *Ваш кабінет:*
            Telegram ID: `{message.from_user.id}`
            Сесія: `{user.session_id}`
        """
    )

    await _message.edit_text(initial_message, parse_mode="Markdown")

    application = await ApplicationModel.find_one({"session_id": user.session_id})
    if not application:
        return

    msg_text = initial_message + "\n*Статуси заявки:*\n"
    for i, s in enumerate(application.statuses, start=1):
        date = datetime.fromtimestamp(int(s.date) / 1000).strftime("%Y-%m-%d %H:%M")
        msg_text += f"{i}. *{s.status}* \n_{date}_\n\n"

    msg_text += dedent(
        f"""
            Останнє оновлення: {application.last_update.strftime("%Y-%m-%d %H:%M")}
        """
    )

    await _message.edit_text(msg_text, parse_mode="Markdown")


async def link(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває перевірка...")
    await message.answer_chat_action("typing")

    parts = message.text.split(" ")
    if len(parts) != 2:
        await _message.edit_text(
            "Надішліть ваш ідентифікатор, будь ласка використовуючи команду /link \nНаприклад /link 1006655"
        )
        return

    session_id = parts[1]
    if not session_id.isdigit() or len(session_id) != 7:
        await _message.edit_text(
            "Ідентифікатор повинен містити лише цифри, спробуйте ще раз."
        )
        return

    scraper = Scraper()
    status = scraper.check(session_id, retrive_all=True)

    _user = await UserModel.find_one({"telgram_id": str(message.from_user.id)})
    if _user and _user.session_id:
        await _message.edit_text(
            f"""
            Ваш Telegram ID вже прив'язаний до ідентифікатора {_user.session_id}
            """
        )
        return

    if not status:
        await _message.edit_text(
            "Виникла помилка перевірки ідентифікатора, можливо дані некоректні чи ще не внесені в базу, спробуйте пізніше."
        )
        return

    _application = await ApplicationModel.find_one({"session_id": session_id})
    if not _application:
        _application = ApplicationModel(
            session_id=session_id,
            statuses=[
                StatusModel(status=s.get("status"), date=s.get("date")) for s in status
            ],
            last_update=datetime.now(),
        )
        await _application.insert()

    _user = UserModel(telgram_id=str(message.from_user.id), session_id=session_id)
    await _user.insert()

    await _message.edit_text(
        f"""
        Ваш Telegram ID успішно прив'язаний до ідентифікатора {_user.session_id}
        """
    )


async def unlink(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває перевірка...")
    await message.answer_chat_action("typing")

    _user = await UserModel.find_one({"telgram_id": str(message.from_user.id)})
    if not _user:
        await _message.edit_text(
            "Вашого ідентифікатора не знайдено, надішліть його, будь ласка використовуючи команду /link \nНаприклад /link 1006655"
        )
        return

    await _user.delete()
    await _message.edit_text(
        f"""
        Ваш Telegram ID успішно відв'язаний від ідентифікатора {_user.session_id}
        """
    )
