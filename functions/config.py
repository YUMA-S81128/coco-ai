from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration class to manage environment variables for Cloud Functions.

    It uses pydantic-settings to load configuration from a .env file and/or
    environment variables.
    """

    model_config = SettingsConfigDict(
        env_file="../.env",  # Look for .env in the project root
        env_file_encoding="utf-8",
        case_sensitive=False,
        alias_generator=(lambda x: x.upper()),
        extra="ignore",
    )

    # Cloud Storage Bucket for audio uploads from the client.
    audio_upload_bucket: str = Field(...)


@lru_cache
def get_settings() -> Settings:
    """Singleton function to get and cache the application settings."""
    return Settings()  # type: ignore
