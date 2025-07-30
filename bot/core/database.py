import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from bot.core.config import settings

client: AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(
    settings.DATABASE_URL, uuidRepresentation="standard"
)
db: AsyncIOMotorDatabase = client[settings.DATABASE_NAME]
