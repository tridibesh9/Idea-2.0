from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://complaintiq:complaintiq@localhost:5432/complaintiq"
    DATABASE_URL_SYNC: str = "postgresql://complaintiq:complaintiq@localhost:5432/complaintiq"
    OPENAI_API_KEY: str = ""
    JWT_SECRET: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"
    OPENAI_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
