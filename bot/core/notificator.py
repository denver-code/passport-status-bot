import requests

from bot.bot_instance import bot
from bot.core.constants import (
    PUSH_NOTIFICATION_ERROR,
    PUSH_NOTIFICATION_SEND_ERROR,
    PUSH_NOTIFICATION_TITLE,
)
from bot.core.logger import log_error, log_function
from bot.core.models.application import ApplicationModel, StatusModel
from bot.core.models.push import PushModel
from bot.core.models.user import SubscriptionModel
from bot.core.utils import format_new_status_message


@log_function("send_push")
def send_push(user: str, title: str, message: str) -> None:
    requests.post(
        f"https://ntfy.sh/{user}",
        data=message.encode(encoding="utf-8"),
        headers={
            "Title": title.encode(encoding="utf-8"),
            "Priority": "urgent",
        },
        timeout=10,
    )


@log_function("notify_subscribers")
async def notify_subscribers(
    target_application: ApplicationModel | None = None,
    new_statuses: list[StatusModel] | None = None,
) -> None:
    if not target_application or not new_statuses:
        return

    _subscriptions = await SubscriptionModel.find(
        {"session_id": target_application.session_id}
    ).to_list()

    if not _subscriptions:
        return

    # Use centralized status message formatting
    _msg_text = format_new_status_message(target_application.session_id, new_statuses)

    for _subscription in _subscriptions:
        _push_subscription = await PushModel.find_one(
            {"telegram_id": _subscription.telegram_id}
        )
        if _push_subscription:
            _message = ""
            for status in new_statuses:
                _message += f"{status.status}\n"
            try:
                send_push(
                    f"MFA_{_subscription.telegram_id}_{_push_subscription.secret_id}",
                    PUSH_NOTIFICATION_TITLE.format(
                        session_id=target_application.session_id
                    ),
                    _message,
                )
            except Exception as e:
                log_error(
                    PUSH_NOTIFICATION_ERROR.format(
                        telegram_id=_subscription.telegram_id, error=str(e)
                    ),
                    _subscription.telegram_id,
                    e,
                )

        try:
            await bot.send_message(
                _subscription.telegram_id,
                _msg_text,
                parse_mode="Markdown",
            )
        except Exception as e:
            log_error(
                PUSH_NOTIFICATION_SEND_ERROR.format(error=str(e)),
                _subscription.telegram_id,
                e,
            )
