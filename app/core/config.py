"""Configuration settings for the application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    COINMARKETCAP_KEY: str | None = None
    REDIS_URL: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
