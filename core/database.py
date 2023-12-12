import motor.motor_asyncio
from core.config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(
    settings.DATABASE_URL, uuidRepresentation="standard"
)
db = client[settings.DATABASE_NAME]
