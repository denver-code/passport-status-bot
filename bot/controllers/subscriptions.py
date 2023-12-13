from datetime import datetime, timedelta
import secrets
from textwrap import dedent
from aiogram import types
from bot.core.api import Scraper
from bot.core.models.application import ApplicationModel, StatusModel
from bot.core.models.push import PushModel

from bot.core.models.user import SubscriptionModel, UserModel
from bot.core.notificator import notify_subscribers


async def subscribe(message: types.Message):
    _message = await message.answer("Зачекайте, будь ласка, триває перевірка...")
    await message.answer_chat_action("typing")

    parts = message.text.split(" ")
    if len(parts) <= 1:
        await _message.edit_text(
            "Надішліть ваш ідентифікатор, будь ласка використовуючи команду /subscribe \nНаприклад /subscribe 1006655"
        )
        return

    session_ids = parts[1:]

    for session_id in session_ids:
        _message = await _message.edit_text(
            f"Зачекайте, будь ласка, триває оформлення підписки #{session_id}..."
        )
        _subscription = await SubscriptionModel.find_one(
            {"telgram_id": str(message.from_user.id), "session_id": session_id}
        )
        if _subscription:
            continue

        _count_subscriptions = await SubscriptionModel.find_all(
            {"telgram_id": str(message.from_user.id)}
        ).count()

        if _count_subscriptions > 5:
            await _message.edit_text(
                "Ви досягли максимальної кількості підписок на сповіщення про зміну статусу заявки"
            )
            return

        _application = await ApplicationModel.find_one({"session_id": session_id})
        if not _application:
            scraper = Scraper()
            # create application
            status = scraper.check(session_id, retrive_all=True)
            if not status:
                continue

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

        _subscription = SubscriptionModel(
            telgram_id=str(message.from_user.id),
            session_id=session_id,
        )
        await _subscription.insert()

    await _message.edit_text("Ви успішно підписані на сповіщення про зміну статусу")


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
        "Ви успішно відписані від сповіщень про зміну статусу заявки"
    )


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

    _msg_text = dedent(
        f"""
            *Ваші підписки:*
        """
    )

    for i, s in enumerate(_subscriptions):
        _msg_text += f"{i+1}. *{s.session_id}* \n"

    _msg_text += dedent(
        f"""
            Всього: {len(_subscriptions)}
        """
    )

    await _message.edit_text(_msg_text, parse_mode="Markdown")


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

    scraper = Scraper()
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


async def enable_push(message: types.Message):
    _push = await PushModel.find_one({"telgram_id": str(message.from_user.id)})
    if _push:
        await message.answer(
            f"Ви вже підписані на сповіщення про зміну статусу заявки.\nTopic: `MFA_{message.from_id}_{_push.secret_id}`",
            parse_mode="Markdown",
        )

        return

    # generate random secret id for push - lenght 32
    _secret_id = secrets.token_hex(16)

    _push = PushModel(
        telgram_id=str(message.from_user.id),
        secret_id=_secret_id,
    )
    await _push.insert()

    await message.answer(
        dedent(
            f"""
                Ви успішно підписані на сповіщення про зміну статусу заявки
                Ваш секретний ідентифікатор: {_secret_id}

                Щоб підписатиня на сповіщення, додайте наступний топік до NTFY.sh:
                `MFA_{message.from_id}_{_secret_id}`
            """,
        ),
        parse_mode="Markdown",
    )


async def dump_subscriptions(message: types.Message):
    _subscriptions = await SubscriptionModel.find(
        {"telgram_id": str(message.from_user.id)}
    ).to_list()

    if not _subscriptions:
        await message.answer("Ви не підписані на сповіщення про зміну статусу заявки")
        return

    _msg_text = dedent(
        f"""
            *Ваші підписки:*
        """
    )

    for i, s in enumerate(_subscriptions):
        _msg_text += f"{i+1}. *{s.session_id}* \n"

    _msg_text += dedent(
        f"""
            Всього: {len(_subscriptions)}
        """
    )

    _message = await message.answer(_msg_text, parse_mode="Markdown")

    applications = await ApplicationModel.find(
        {"session_id": {"$in": [s.session_id for s in _subscriptions]}}
    ).to_list()

    _msg_text = dedent(
        f"""
            *Заявки:*
        """
    )

    for i, s in enumerate(_subscriptions):
        _msg_text += f"\n📑*{s.session_id}* \n"
        # add statuses
        _application = next(
            filter(lambda a: a.session_id == s.session_id, applications), None
        )
        if not _application:
            continue
        for j, st in enumerate(_application.statuses):
            _date = datetime.fromtimestamp(int(st.date) / 1000).strftime(
                "%Y-%m-%d %H:%M"
            )
            _msg_text += f"     *{st.status}* \n          _{_date}_\n"

    _msg_text += dedent(f"\nВсього: {len(_subscriptions)}")

    await _message.edit_text(_msg_text, parse_mode="Markdown")
