from beanie import Document, Indexed
from pydantic import BaseModel
from datetime import date, datetime


class StatusModel(BaseModel):
    status: str
    date: int


class ApplicationModel(Document):
    session_id: str
    statuses: list[StatusModel]
    last_update: datetime

    class Settings:
        name = "applications"
