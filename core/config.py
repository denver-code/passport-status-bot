from typing import List, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TOKEN: str = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    ADMIN_ID: str = "123456789"
    DATABASE_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "apexlikeproject"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
