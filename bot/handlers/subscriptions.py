from aiogram import Dispatcher

from bot.controllers.subscriptions import (
    subscribe,
    unsubscribe,
    subscriptions,
    manual_application_update,
    enable_push,
    dump_subscriptions,
)


def setup(dp: Dispatcher):
    dp.register_message_handler(subscribe, commands=["subscribe"], state="*")
    dp.register_message_handler(unsubscribe, commands=["unsubscribe"], state="*")
    dp.register_message_handler(subscriptions, commands=["subscriptions"], state="*")
    dp.register_message_handler(
        manual_application_update, commands=["update"], state="*"
    )
    dp.register_message_handler(enable_push, commands=["push"], state="*")
    dp.register_message_handler(dump_subscriptions, commands=["dump"], state="*")
