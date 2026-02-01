# PROJECT: EoS
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
from typing import List, Optional
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "EoS API"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Database
    SQLALCHEMY_DATABASE_URL: str = "sqlite+aiosqlite:///./eos.db"
    SQLALCHEMY_ECHO: bool = False

    # Authentication
    AUTH_PROVIDER: str = "local"
    AUTH_SERVICE_URL: str = "http://localhost:8001/auth/login"
    AUTH_API_KEY: Optional[str] = None
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"

    # Artifact Storage
    ARTIFACT_STORAGE_BACKEND: str = "db"  # db, file, gcs, http
    ARTIFACT_STORAGE_PATH: str = "./artifacts"
    ARTIFACT_GCS_BUCKET: Optional[str] = None
    ARTIFACT_HTTP_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
