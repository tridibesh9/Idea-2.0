from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://complaintiq_user:wppt2j121gQNmKnbWR8GZVhEsrozBpbQ@dpg-d8a47iml51nc73ep5kkg-a.singapore-postgres.render.com/complaintiq"
    DATABASE_URL_SYNC: str = "postgresql://complaintiq_user:wppt2j121gQNmKnbWR8GZVhEsrozBpbQ@dpg-d8a47iml51nc73ep5kkg-a.singapore-postgres.render.com/complaintiq"
    GEMINI_API_KEY: str = ""
    JWT_SECRET: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # Email Configuration
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_EMAIL: str = "support@example.com"
    IMAP_PASSWORD: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_EMAIL: str = "support@example.com"
    SMTP_PASSWORD: str = ""

    SUPPORT_EMAIL: str = "support@example.com"
    SUPPORT_NAME: str = "ComplaintIQ Support"

    # Email listener enabled/disabled
    EMAIL_LISTENER_ENABLED: bool = False
    EMAIL_CHECK_INTERVAL: int = 60  # seconds

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

