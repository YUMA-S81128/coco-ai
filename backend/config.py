from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SessionService(str, Enum):
    """セッションサービスの種別を定義するEnum"""

    inmemory = "inmemory"
    vertex = "vertex"


class Settings(BaseSettings):
    """
    アプリケーション（Cloud Run）の環境変数を管理するための設定クラス。

    pydantic-settingsを利用して設定を読み込む。
    読み込みの優先順位は、環境変数 > .envファイル。
    Cloud Build環境では環境変数を読み込み、ローカル開発では.envファイルを利用する。
    """

    # Pydantic V2 スタイルのモデル設定
    model_config = SettingsConfigDict(
        env_file="../.env",  # プロジェクトルートにある.envファイルを参照
        env_file_encoding="utf-8",
        case_sensitive=False,
        alias_generator=(lambda x: x.upper()),  # 環境変数を大文字に変換
        extra="ignore",  # 未定義のフィールドは無視
    )

    # Google Cloud 設定
    google_cloud_project: str = Field(..., description="Google CloudプロジェクトID")
    google_cloud_location: str = Field(
        default="asia-northeast1", description="デフォルトのリージョン/ロケーション"
    )

    # Cloud Storage バケット設定
    audio_upload_bucket: str = Field(..., description="音声アップロード用のバケット名")
    processed_audio_bucket: str = Field(
        ..., description="処理済み音声保存用のバケット名"
    )
    generated_image_bucket: str = Field(..., description="生成画像保存用のバケット名")

    # Gemini API 設定
    google_genai_use_vertexai: bool = Field(
        default=True, description="Vertex AI経由でGemini APIを使用するかどうか"
    )

    # Firestore コレクション設定
    firestore_collection: str = Field(..., description="Firestoreのコレクション名")

    # タイムアウト設定
    agent_timeout: int = Field(default=300, description="エージェントのタイムアウト秒")

    # ADK セッションサービス設定
    session_service: SessionService = Field(
        default=SessionService.inmemory, description="使用するセッションサービスの種類"
    )


@lru_cache
def get_settings() -> Settings:
    """
    アプリケーション設定をシングルトンとして取得し、キャッシュする関数。
    """
    return Settings()  # type: ignore
