# Configuración de la aplicación utilizando Pydantic y Pydantic Settings

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "Turnix API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = Field(default_factory=list)

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "turnix"

    SECRET_KEY: str = "insecure-development-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DEFAULT_TIMEZONE: str = "America/Bogota"
    DEFAULT_CURRENCY: str = "COP"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    EMAILS_FROM: str = "Turnix <no-reply@turnix.app>"

    FREEMIUM_MAX_EMPLOYEES: int = 2
    FREEMIUM_MAX_SERVICES: int = 5
    FREEMIUM_MAX_BOOKINGS_PER_MONTH: int = 100
    FREEMIUM_MAX_WAITLIST_ENABLED: bool = False
    PRO_MAX_EMPLOYEES: int = 50
    PRO_MAX_SERVICES: int = 100
    PRO_MAX_BOOKINGS_PER_MONTH: int = 10_000
    PRO_MAX_WAITLIST_ENABLED: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip().startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
