from datetime import datetime

from beanie import Document
from pydantic import BaseModel


class StatusModel(BaseModel):
    status: str
    date: int


class ApplicationModel(Document):
    session_id: str
    statuses: list[StatusModel]
    last_update: datetime

    class Settings:
        name = "applications"
