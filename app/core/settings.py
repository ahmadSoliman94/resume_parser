from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    APP_NAME: str = "Resume Parser AI"
    USE_GPU: bool = True
    BATCH_SIZE: int = 3
    PARALLEL_BATCHES: int = 1
    ENABLE_ANNOTATION: bool = True
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "*"
    MAX_FILE_SIZE: int = 10_000_000  # 10 MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
