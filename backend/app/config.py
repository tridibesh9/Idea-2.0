import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


def find_env_file() -> str:
    # Resolve the root .env first (parents[2] from app/config.py is root)
    root_dir = Path(__file__).resolve().parents[2]
    root_env = root_dir / ".env"
    if root_env.exists():
        return str(root_env)
    
    # Fallback to backend/.env
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    if backend_env.exists():
        return str(backend_env)
        
    return ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://complaintiq:complaintiq@localhost:5432/complaintiq"
    DATABASE_URL_SYNC: str = "postgresql://complaintiq:complaintiq@localhost:5432/complaintiq"
    GEMINI_API_KEY: str = ""
    JWT_SECRET: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "models/gemini-embedding-2"
    
    # Security
    ENCRYPTION_KEY: str = "qMbafBAz52YvqrQxt3IxeyyADa6GG5Z77jauHSU7GjI="
    BLIND_INDEX_SALT: str = "super-secret-salt-for-blind-index"

    # Email Configuration
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_EMAIL: str = ""
    IMAP_PASSWORD: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_EMAIL: str = ""
    SMTP_PASSWORD: str = ""
    RESEND_API_KEY: str = ""

    SUPPORT_EMAIL: str = ""
    SUPPORT_NAME: str = ""

    # Email listener enabled/disabled
    EMAIL_LISTENER_ENABLED: bool = True
    EMAIL_CHECK_INTERVAL: int = 100  # seconds

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_LISTENER_ENABLED: bool = True
    TELEGRAM_CHECK_INTERVAL: int = 3  # seconds

    model_config = SettingsConfigDict(env_file=find_env_file(), env_file_encoding="utf-8", extra="ignore")

#hi
@lru_cache()
def get_settings() -> Settings:
    return Settings()

