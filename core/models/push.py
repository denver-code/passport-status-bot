from beanie import Document, Indexed


class PushModel(Document):
    telgram_id: str
    secret_id: str

    class Settings:
        name = "pushes"
