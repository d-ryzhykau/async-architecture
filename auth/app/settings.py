from pathlib import Path

from pydantic import PositiveInt, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROOT_DIR = Path(__file__).parent


class Settings(BaseSettings):
    database_url: PostgresDsn
    jwt_secret_key: SecretStr
    jwt_expire_seconds: PositiveInt

    model_config = SettingsConfigDict(env_file=APP_ROOT_DIR.parent / ".env")


# TODO: don't load settings on import time
settings = Settings()
