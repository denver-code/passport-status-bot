from datetime import datetime

from beanie import Document


class RequestLog(Document):
    telegram_id: str
    timestamp: datetime

    class Settings:
        name = "request_logs"
