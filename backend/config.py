from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SessionService(str, Enum):
    inmemory = "inmemory"
    vertex = "vertex"


class Settings(BaseSettings):
    """
    Configuration class to manage environment variables for the application.

    It uses pydantic-settings to load configuration from a .env file and/or
    environment variables. If required variables are not set, Pydantic will
    raise a validation error on startup.
    """

    # Pydantic V2 style for model configuration.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        alias_generator=(lambda x: x.upper()),
        extra="ignore",
    )

    # Google Cloud Settings
    google_cloud_project_id: str = Field(...)
    region: str = Field(default="asia-northeast1")

    # Cloud Storage Buckets
    audio_upload_bucket: str = Field(...)
    processed_audio_bucket: str = Field(...)
    generated_image_bucket: str = Field(...)

    # Gemini API Settings
    google_genai_use_vertexai: bool = True

    # Firestore Collection
    firestore_collection: str = "jobs"

    # timeout
    agent_timeout: int = 300

    # ADK Session Service configuration
    session_service: SessionService = Field(default=SessionService.inmemory)


@lru_cache
def get_settings() -> Settings:
    """
    Singleton function to get and cache the application settings.

    Using @lru_cache ensures that the Settings object is created only once,
    improving performance by avoiding repeated file I/O and validation.
    """
    return Settings()  # type: ignore
