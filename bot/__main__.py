import datetime

from beanie import init_beanie

from aiogram import types
from aiogram.dispatcher import Dispatcher

from aiogram.contrib.fsm_storage.memory import MemoryStorage

import asyncio
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.bot_instance import bot, loop, version as bot_version, link, codename

from bot.core.database import db

from bot.core.models.application import ApplicationModel
from bot.core.models.push import PushModel
from bot.core.models.user import SubscriptionModel, UserModel
from bot.core.scheduler import scheduler_job

from bot.handlers import setup as handlers_setup
from bot.middlewares.antiflood import ThrottlingMiddleware, rate_limit
from bot.middlewares.debug import LoggerMiddleware


scheduler = AsyncIOScheduler()

dp = Dispatcher(
    bot,
    loop=loop,
    storage=MemoryStorage(),
)


async def startup(dp: Dispatcher):
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
        types.BotCommand(command="/update", description="Оновити статус заявки вручну"),
        types.BotCommand(
            command="/push", description="Підписатися на сповіщення через NTFY.sh"
        ),
        types.BotCommand(
            command="/dump",
            description="Отримати весь дамп доступних даних на ваші підписки",
        ),
        types.BotCommand(command="/ping", description="Перевірити чи працює бот"),
        types.BotCommand(command="/time", description="Поточний час сервера"),
        types.BotCommand(command="/version", description="Версія бота"),
    ]

    await bot.set_my_commands(commands)
    await init_beanie(
        database=db,
        document_models=[
            UserModel,
            SubscriptionModel,
            ApplicationModel,
            PushModel,
        ],
    )


@dp.message_handler(commands=["ping"])
@rate_limit(5, "ping")
async def ping(message: types.Message):
    await message.answer("Pong!")


@dp.message_handler(commands=["time"])
async def time(message: types.Message):
    await message.answer(f"Server time is: {str(datetime.datetime.now())}")


@dp.message_handler(commands=["version"])
async def version(message: types.Message):
    await message.answer(
        f"Bot version:\n*v{bot_version}*\n\nSource Code:\n[denver-code/passport-status-bot/{link.split('/')[-1]}]({link})\n\nCodename:\n*{codename}*",
        parse_mode="Markdown",
    )


def main():
    dp.middleware.setup(LoggerMiddleware())
    dp.middleware.setup(ThrottlingMiddleware())
    scheduler.add_job(
        scheduler_job,
        "interval",
        hours=1,
    )
    scheduler.start()
    handlers_setup.setup(dp)
    executor.start_polling(dp, loop=loop, skip_updates=True, on_startup=startup)


if __name__ == "__main__":
    main()
