from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://complaintiq_msvo_user:bSXUALiju1eUDOncZ1lmrZvLpzMHsZKz@dpg-d8c5tqcm0tmc73f2o29g-a.ohio-postgres.render.com/complaintiq_msvo"
    DATABASE_URL_SYNC: str = "postgresql://complaintiq_msvo_user:bSXUALiju1eUDOncZ1lmrZvLpzMHsZKz@dpg-d8c5tqcm0tmc73f2o29g-a.ohio-postgres.render.com/complaintiq_msvo"
    GEMINI_API_KEY: str = "AIzaSyCuSw3RFQuKtuQkgUsYSIWu8kh3M3gLnzw"
    JWT_SECRET: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # Email Configuration
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_EMAIL: str = "bytemysticop@gmail.com"
    IMAP_PASSWORD: str = "dfyzptbztxsimwxm"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_EMAIL: str = "bytemysticop@gmail.com"
    SMTP_PASSWORD: str = "dfyzptbztxsimwxm"

    SUPPORT_EMAIL: str = "support@example.com"
    SUPPORT_NAME: str = "ComplaintIQ Support"

    # Email listener enabled/disabled
    EMAIL_LISTENER_ENABLED: bool = True
    EMAIL_CHECK_INTERVAL: int = 5  # seconds

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_LISTENER_ENABLED: bool = True
    TELEGRAM_CHECK_INTERVAL: int = 3  # seconds

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

