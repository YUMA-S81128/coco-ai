from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SessionService(str, Enum):
    inmemory = "inmemory"
    vertex = "vertex"


class Settings(BaseSettings):
    """
    環境変数を管理する設定クラス。
    .envファイルや環境変数から値を読み込む。
    Pydanticの機能により、必須の環境変数が設定されていない場合は起動時にエラーとなります。
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
    設定オブジェクトをキャッシュして返すシングルトン関数
    ValidationErrorはそのまま起動失敗とする
    """
    return Settings()  # type: ignore
