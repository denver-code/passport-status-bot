from time import sleep
import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from datetime import datetime
from core.api import Scraper
from core.config import settings

bot = Bot(settings.TOKEN)
dp = Dispatcher(bot, loop=asyncio.get_event_loop())

scraper = Scraper()


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        """
             *Вітаю!*👋
             
Цей бот повідомляє про зміни статусу вашої заявки на _passport.mfa.gov.ua_, щоб почати користуватися ботом надішли свій ідентифікатор.
Для користування всіма функціями надішліть /cabinet
        
Важливо зазначити, що цей бот *НЕ ПОВ'ЯЗАНИЙ* з МЗС України, і не несе відповідальності за вірогідність чи своєчасність інформації, для детального пояснення надішліть /policy
        """,
        parse_mode="Markdown",
    )


@dp.message_handler(commands=["policy"])
async def policy(message: types.Message):
    await message.answer(
        """
        *Загальна інформація*
Бот розроблений для спрощення процесу відстеження статусу заявки на оформлення паспорту на сайті _passport.mfa.gov.ua_ незалежним розробником, і не пов'язаним з МЗС України.
Використання функцій бота не зобов'язує вас ні до чого, і не несе відповідальності за вірогідність чи своєчасність інформації, використання відбувається на ваш страх та ризик.

*Користування*
Функція відотворення статусу заявки доступна лише після надіслання боту вашого ідентифікатора, який ви отримали при реєстрації заявки на сайті _passport.mfa.gov.ua_ ніяким чином не зберігається, і використовується лише для надіслання цьго ідентифікатору на офіційний вебсайт.
Всі решта функцій доступні (кабінет, сповіщення про зміни статусу) - використовують базу даних та зберігають ваш Telegram ID, Ідентифікатор Сесії _passport.mfa.gov.ua_, та всі статуси заявки.
Використання цих функцій підтверджує вашу згоду на зберігання цих даних.

*Як використовується зібрана інформація*
Ваш Telegram ID використовується для ідентифікації вас в системі, і для надсилання вам сповіщень про зміну статусу заявки, а також привʼязки сесії.
Ваш ідентифікатор сесії використовується для отримання статусу заявки шляхом запиту на офіційний вебсайт _passport.mfa.gov.ua_.
Всі статуси заявки зберігаються для відтворення історії змін статусу заявки, та звірення нових статусів з попередніми для виявлення змін.

*Видалення даних*
Ви можете видалити всі дані, пов'язані з вашим Telegram ID, надіславши /delete, або зв'язавшись з розробником  @operatorSilence. 

*Source Code*
Бот поширюється з відкритим вихідним кодом, ви можете переглянути його за посиланням:
https://github.com/denver-code/passport-status-bot
та перевірити все вищезазначене, або ж підняти свій власний бот з власним функціоналом.
        """,
        parse_mode="Markdown",
    )


@dp.message_handler(regexp=r"^\d{7}$")
async def custom_check(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває перевірка...")
    await message.answer_chat_action("typing")

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


# @dp.message_handler(commands=["cabinet"])
# async def cabinet(message: types.Message):
#     await message.answer(
#         """
#         *Ваш кабінет:*
#         """
#     )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
