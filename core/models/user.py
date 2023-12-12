from beanie import Document, Indexed


class UserModel(Document):
    telgram_id: str
    session_id: str

    class Settings:
        name = "users"


class SubscriptionModel(Document):
    telgram_id: str
    session_id: str

    class Settings:
        name = "subscriptions"
