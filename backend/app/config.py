from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # App
    APP_NAME: str = "FinAgent Platform"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finagent:finagent@localhost:5432/finagent"
    DATABASE_URL_SYNC: str = "postgresql://finagent:finagent@localhost:5432/finagent"

    # Session Database (SQLite for local dev, can use any SQLAlchemy-supported DB)
    SESSION_DB_URL: str = "sqlite+aiosqlite:///./data/sessions.db"

    # Auth - JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Auth - LDAP
    LDAP_SERVER: str = "ldap://localhost:389"
    LDAP_BIND_DN: str = ""
    LDAP_BIND_PASSWORD: str = ""
    LDAP_USER_SEARCH_BASE: str = "ou=users,dc=company,dc=com"
    LDAP_USER_SEARCH_FILTER: str = "(uid={username})"
    LDAP_GROUP_SEARCH_BASE: str = "ou=groups,dc=company,dc=com"

    # LLM Settings
    LLM_PROVIDER: str = "groq"  # "gemini" or "groq"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.1-8b-instant"

    # Demo Mode (mock LLM responses when no API key available)
    DEMO_MODE: bool = True

    # Financial API (mock mode)

    FINANCIAL_API_BASE_URL: str = "https://api.financial-data.internal"
    FINANCIAL_WS_URL: str = "wss://ws.financial-data.internal"

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
