from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Elyon API"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Database
    SQLALCHEMY_DATABASE_URL: str = "sqlite+aiosqlite:///./elyon.db"
    SQLALCHEMY_ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
