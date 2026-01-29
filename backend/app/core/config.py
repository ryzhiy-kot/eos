# PROJECT: MONAD
# AUTHOR: Kyrylo Yatsenko
# YEAR: 2026
# * COPYRIGHT NOTICE:
# © 2026 Kyrylo Yatsenko. All rights reserved.
#
# This work represents a proprietary methodology for Human-Machine Interaction (HMI).
# All source code, logic structures, and User Experience (UX) frameworks
# contained herein are the sole intellectual property of Kyrylo Yatsenko.
#
# ATTRIBUTION REQUIREMENT:
# Any use of this program, or any portion thereof (including code snippets and
# interaction patterns), may not be used, redistributed, or adapted
# without explicit, visible credit to Kyrylo Yatsenko as the original author.

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Monad API"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Database
    SQLALCHEMY_DATABASE_URL: str = "sqlite+aiosqlite:///./monad.db"
    SQLALCHEMY_ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
