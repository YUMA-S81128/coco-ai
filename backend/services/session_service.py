from functools import lru_cache

from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.cloud.firestore import AsyncClient
from services.logging_service import get_logger

from config import get_settings

from .firestore_session_service import FirestoreSessionService

settings = get_settings()
logger = get_logger(__name__)


@lru_cache
def get_db_client() -> AsyncClient:
    """Firestore AsyncClientのシングルトンインスタンスを生成・取得する。"""
    return AsyncClient()


# ---------------------------
# セッションサービスのファクトリ
# ---------------------------
def create_session_service(db_client: AsyncClient | None = None) -> BaseSessionService:
    """
    設定に基づいて適切なセッションサービス（インメモリまたはVertex AI）を作成する。

    Returns:
        セッションサービスのインスタンス。
    """
    session_type = settings.session_service

    if session_type == "inmemory":
        logger.info("ADKセッションにInMemorySessionServiceを使用します（開発用）。")
        return InMemorySessionService()

    if session_type == "firestore":
        logger.info("ADKセッションにFirestoreSessionServiceを使用します。")
        # Use a dedicated collection for ADK sessions to keep them separate.
        return FirestoreSessionService(
            db_client=db_client or get_db_client(), collection_name="adk_sessions"
        )

    raise ValueError(f"Unsupported session service type: {session_type}")
