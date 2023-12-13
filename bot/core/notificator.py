from datetime import datetime
import requests
from bot.core.models.application import ApplicationModel, StatusModel
from bot.core.models.push import PushModel
from bot.core.models.user import SubscriptionModel
from bot.bot_instance import bot


def send_push(user, title, message):
    requests.post(
        f"https://ntfy.sh/{user}",
        data=message.encode(encoding="utf-8"),
        headers={
            "Title": title.encode(encoding="utf-8"),
            "Priority": "urgent",
        },
    )


async def notify_subscribers(
    target_application: ApplicationModel = None, new_statuses: list[StatusModel] = None
):
    if target_application:
        _subscriptions = await SubscriptionModel.find(
            {"session_id": target_application.session_id}
        ).to_list()
    else:
        _subscriptions = await SubscriptionModel.find({}).to_list()

    if not _subscriptions:
        return

    _msg_text = f"""
    Ми помітили зміну статусу заявки *#{target_application.session_id}:*
    """

    for i, s in enumerate(new_statuses):
        _date = datetime.fromtimestamp(int(s.date) / 1000).strftime("%Y-%m-%d %H:%M")
        _msg_text += f"{i+1}. *{s.status}* \n_{_date}_\n\n"

    for _subscription in _subscriptions:
        _push_subscription = await PushModel.find_one(
            {"telgram_id": _subscription.telgram_id}
        )
        if _push_subscription:
            _message = f""
            for status in new_statuses:
                _message += f"{status.status}\n"
            send_push(
                f"MFA_{_subscription.telgram_id}_{_push_subscription.secret_id}",
                f"Оновлення заявки #{target_application.session_id}",
                _message,
            )

        try:
            await bot.send_message(
                _subscription.telgram_id,
                _msg_text,
                parse_mode="Markdown",
            )
        except:
            pass
