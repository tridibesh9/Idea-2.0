from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://complaintiq_user:wppt2j121gQNmKnbWR8GZVhEsrozBpbQ@dpg-d8a47iml51nc73ep5kkg-a.singapore-postgres.render.com/complaintiq"
    DATABASE_URL_SYNC: str = "postgresql://complaintiq_user:wppt2j121gQNmKnbWR8GZVhEsrozBpbQ@dpg-d8a47iml51nc73ep5kkg-a.singapore-postgres.render.com/complaintiq"
    GEMINI_API_KEY: str = "AIzaSyCuSw3RFQuKtuQkgUsYSIWu8kh3M3gLnzw"
    JWT_SECRET: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
