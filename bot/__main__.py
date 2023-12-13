import datetime

from beanie import init_beanie

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher

from aiogram.contrib.fsm_storage.memory import MemoryStorage

import asyncio
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.bot_instance import bot, loop

from bot.core.database import db

from bot.core.models.application import ApplicationModel
from bot.core.models.push import PushModel
from bot.core.models.user import SubscriptionModel, UserModel
from bot.core.scheduler import scheduler_job

from bot.handlers import setup as handlers_setup
from bot.middlewares.antiflood import ThrottlingMiddleware, rate_limit


scheduler = AsyncIOScheduler()

# storage = RedisStorage2(db=2)

# storage = RedisStorage2(
#     host="redis:/localhost",
#     port=6379,
#     db=7,
# )

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


def main():
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
