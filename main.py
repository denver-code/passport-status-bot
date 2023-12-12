from beanie import init_beanie
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
import asyncio
from aiogram.utils import executor
from datetime import datetime, timedelta

from requests import session
from core.api import Scraper
from core.config import settings
from core.database import db
from core.models.application import ApplicationModel, StatusModel
from core.models.user import SubscriptionModel, UserModel

bot = Bot(settings.TOKEN)
dp = Dispatcher(bot, loop=asyncio.get_event_loop())

scraper = Scraper()


async def notify_subscribers():
    pass


async def startup(dp: Dispatcher):
    # set bot commands
    commands = [
        types.BotCommand(command="/start", description="Почати роботу з ботом"),
        types.BotCommand(command="/help", description="Допомога"),
        types.BotCommand(
            command="/policy", description="Політика бота та конфіденційність"
        ),
        types.BotCommand(command="/cabinet", description="Персональний кабінет"),
        types.BotCommand(command="/link", description="Прив'язати ідентифікатор"),
        types.BotCommand(
            command="/unlink",
            description="Відв'язати ідентифікатор та видалити профіль",
        ),
        types.BotCommand(command="/subscribe", description="Підписатися на сповіщення"),
        types.BotCommand(
            command="/unsubscribe", description="Відписатися від сповіщень"
        ),
        types.BotCommand(command="/subscriptions", description="Список підписок"),
    ]

    await bot.set_my_commands(commands)
    await init_beanie(
        database=db,
        document_models=[
            UserModel,
            SubscriptionModel,
            ApplicationModel,
        ],
    )


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        """
             *Вітаю!*👋
             
Цей бот повідомляє про зміни статусу вашої заявки на _passport.mfa.gov.ua_, щоб почати користуватися ботом надішли свій ідентифікатор.
Для користування всіма функціями надішліть /cabinet або /help для детальнішої інформації.
        
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


@dp.message_handler(commands=["cabinet"])
async def cabinet(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває отримання даних...")
    await message.answer_chat_action("typing")

    _user = await UserModel.find_one({"telgram_id": str(message.from_user.id)})
    if not _user:
        await _message.edit_text(
            "Вашого ідентифікатора не знайдено, надішліть його, будь ласка використовуючи команду /link \nНаприклад /link 1006655"
        )
        return

    _init_message = f"""
  *Ваш кабінет:*
Telegram ID: `{message.from_user.id}`
Сесія: `{_user.session_id}`
"""

    await _message.edit_text(
        f"""
{_init_message}
Стауси заявки:
_Зачекайте, будь ласка, триває отримання даних..._
        """,
        parse_mode="Markdown",
    )

    application = await ApplicationModel.find_one(
        {
            "session_id": _user.session_id,
        }
    )

    if not application:
        await _message.edit_text(
            f"""
{_init_message}
Стауси заявки:
_Заявка не знайдена_
            """,
            parse_mode="Markdown",
        )
        return

    _msg_text = f"""
{_init_message}
*Статуси заявки:*
"""

    for i, s in enumerate(application.statuses):
        _date = datetime.fromtimestamp(int(s.date) / 1000).strftime("%Y-%m-%d %H:%M")
        _msg_text += f"{i+1}. *{s.status}* \n_{_date}_\n\n"

    _msg_text += f"""
Останнє оновлення: {application.last_update.strftime("%Y-%m-%d %H:%M")}
    """

    await _message.edit_text(_msg_text, parse_mode="Markdown")


@dp.message_handler(commands=["link"])
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
    status = scraper.check(session_id, retrive_all=True)
    print(f"{status=}")

    _user = await UserModel.find_one({"telgram_id": str(message.from_user.id)})

    if not status:
        await _message.edit_text(
            "Виникла помилка перевірки ідентифікатора, можливо дані некоректні чи ще не внесені в базу, спробуйте пізніше."
        )
        return

    _application = await ApplicationModel.find_one({"session_id": session_id})
    if not _application:
        _statuses = []
        for s in status:
            _statuses.append(
                StatusModel(
                    status=s.get("status"),
                    date=s.get("date"),
                )
            )
        _application = ApplicationModel(
            session_id=session_id,
            statuses=_statuses,
            last_update=datetime.now(),
        )
        await _application.insert()

    if _user:
        _user.session_id = session_id
        await _user.update()
    else:
        _user = UserModel(
            telgram_id=str(message.from_user.id),
            session_id=session_id,
        )
        await _user.insert()

    await _message.edit_text(
        f"""
Ваш Telegram ID успішно прив'язаний до ідентифікатора {_user.session_id}
        """
    )


@dp.message_handler(commands=["unlink", "delete"])
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


@dp.message_handler(commands=["subscribe"])
async def subscribe(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває перевірка...")
    await message.answer_chat_action("typing")

    # max of 5 subscriptions
    # get session if from message.text

    parts = message.text.split(" ")
    if len(parts) != 2:
        await _message.edit_text(
            "Надішліть ваш ідентифікатор, будь ласка використовуючи команду /subscribe \nНаприклад /subscribe 1006655"
        )
        return

    session_id = parts[1]

    _subscription = await SubscriptionModel.find_one(
        {"telgram_id": str(message.from_user.id), "session_id": session_id}
    )
    if _subscription:
        await _message.edit_text(
            "Ви вже підписані на сповіщення про зміну статусу заявки"
        )
        return

    _count_subscriptions = await SubscriptionModel.find_all(
        {"telgram_id": str(message.from_user.id)}
    ).count()
    if _count_subscriptions >= 5:
        await _message.edit_text(
            "Ви досягли максимальної кількості підписок на сповіщення про зміну статусу заявки"
        )
        return

    _subscription = SubscriptionModel(
        telgram_id=str(message.from_user.id),
        session_id=session_id,
    )
    await _subscription.insert()

    await _message.edit_text(
        f"""
Ви успішно підписані на сповіщення про зміну статусу заявки
        """
    )


@dp.message_handler(commands=["unsubscribe"])
async def unsubscribe(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває перевірка...")
    await message.answer_chat_action("typing")
    parts = message.text.split(" ")
    if len(parts) != 2:
        await _message.edit_text(
            "Надішліть ваш ідентифікатор, будь ласка використовуючи команду /unsubscribe \nНаприклад /unsubscribe 1006655"
        )
        return

    session_id = parts[1]

    _subscription = await SubscriptionModel.find_one(
        {"telgram_id": str(message.from_user.id), "session_id": session_id}
    )
    if not _subscription:
        await _message.edit_text(
            "Ви не підписані на сповіщення про зміну статусу заявки"
        )
        return

    await _subscription.delete()

    await _message.edit_text(
        f"""
Ви успішно відписані від сповіщень про зміну статусу заявки
        """
    )


@dp.message_handler(commands=["subscriptions"])
async def subscriptions(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває отримання даних...")
    await message.answer_chat_action("typing")

    _subscriptions = await SubscriptionModel.find(
        {"telgram_id": str(message.from_user.id)}
    ).to_list()

    if not _subscriptions:
        await _message.edit_text(
            "Ви не підписані на сповіщення про зміну статусу заявки"
        )
        return

    _msg_text = f"""
*Ваші підписки:*
"""

    for i, s in enumerate(_subscriptions):
        _msg_text += f"{i+1}. *{s.session_id}* \n"

    _msg_text += f"""
Всього: {len(_subscriptions)}"""

    await _message.edit_text(_msg_text, parse_mode="Markdown")


@dp.message_handler(commands=["help"])
async def help(message: types.Message):
    await message.answer(
        """
*Основні:*
/start - почати роботу з ботом
/help - допомога
/policy - політика бота та конфіденційність

*Персональні Функції:*
/cabinet - персональний кабінет
/link <session ID> - прив'язати ідентифікатор
/unlink або /delete - відв'язати ідентифікатор та видалити профіль

*Сповіщення:*
_Keep in mind: ви можеше мати лише 5 активних підписок_
/subscribe <session ID> - підписатися на сповіщення
/unsubscribe <session ID> - відписатися від сповіщень
/subscriptions - список підписок
        """,
        parse_mode="Markdown",
    )


@dp.message_handler(commands=["update"])
async def manual_application_update(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває отримання даних...")
    await message.answer_chat_action("typing")

    _user = await UserModel.find_one({"telgram_id": str(message.from_user.id)})

    _application = await ApplicationModel.find_one(
        {
            "session_id": _user.session_id,
        }
    )
    if not _user or not _application:
        await _message.edit_text(
            "Вашого ідентифікатора не знайдено, надішліть його, будь ласка використовуючи команду /link \nНаприклад /link 1006655"
        )
        return

    if _application.last_update > datetime.now() - timedelta(minutes=20):
        await _message.edit_text(
            "Останнє оновлення було менше 20хв тому, спробуйте пізніше."
        )
        return

    status = scraper.check(_application.session_id, retrive_all=True)

    if not status:
        await _message.edit_text(
            "Виникла помилка перевірки ідентифікатора, можливо дані некоректні чи ще не внесені в базу, спробуйте пізніше."
        )
        return

    _statuses = []
    for s in status:
        _statuses.append(
            StatusModel(
                status=s.get("status"),
                date=s.get("date"),
            )
        )
    if len(_statuses) > len(_application.statuses):
        # find new statuses
        new_statuses = _statuses[len(_application.statuses) :]
        # notify subscribers
        await notify_subscribers()

        _msg_text = f"""
        Ми помітили зміну статусу заявки *#{_user.session_id}:*
        """

        for i, s in enumerate(new_statuses):
            _date = datetime.fromtimestamp(int(s.date) / 1000).strftime(
                "%Y-%m-%d %H:%M"
            )
            _msg_text += f"{i+1}. *{s.status}* \n_{_date}_\n\n"

        await _message.edit_text(_msg_text, parse_mode="Markdown")
    else:
        await _message.edit_text("Статуси не змінилися.")

    _application.statuses = _statuses
    _application.last_update = datetime.now()

    await _application.save()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=startup)
