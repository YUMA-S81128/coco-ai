from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Cloud Functionsの環境変数を管理するための設定クラス。

    pydantic-settingsを利用して設定を読み込む。
    読み込みの優先順位は、環境変数 > .envファイル。
    Cloud Build環境では環境変数を読み込み、ローカル開発では.envファイルを利用する。
    """

    model_config = SettingsConfigDict(
        env_file="../.env",  # プロジェクトルートにある.envファイルを参照
        env_file_encoding="utf-8",
        case_sensitive=False,
        alias_generator=(lambda x: x.upper()),  # 環境変数を大文字に変換
        extra="ignore",  # 未定義のフィールドは無視
    )

    # クライアントからの音声アップロード用Cloud Storageバケット
    audio_upload_bucket: str = Field(..., description="音声アップロード用のバケット名")

    # Firestoreコレクション
    firestore_collection: str = Field(..., description="Firestoreのコレクション名")

    # 署名付きURL生成に使用するサービスアカウントのメールアドレス
    function_sa_email: str = Field(
        ..., description="Cloud Functionのサービスアカウントメール"
    )


settings = Settings()  # type: ignore
