from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://idea_hackathon_db_user:y1jDs8hGhSmgG8Ga5VnxeOSRj57k4JXu@dpg-d81i937aqgkc73b0jjgg-a.oregon-postgres.render.com/idea_hackathon_db"
    DATABASE_URL_SYNC: str = "postgresql://idea_hackathon_db_user:y1jDs8hGhSmgG8Ga5VnxeOSRj57k4JXu@dpg-d81i937aqgkc73b0jjgg-a.oregon-postgres.render.com/idea_hackathon_db"
    GEMINI_API_KEY: str = ""
    JWT_SECRET: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
