from beanie import Document


class PushModel(Document):
    telegram_id: str
    secret_id: str

    class Settings:
        name = "pushes"
