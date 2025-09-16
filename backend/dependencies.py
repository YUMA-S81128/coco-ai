from functools import lru_cache

from google.adk.sessions import BaseSessionService
from google.cloud.firestore import AsyncClient
from services.session_service import create_session_service, get_db_client


@lru_cache
def get_session_service(db_client: AsyncClient | None = None) -> BaseSessionService:
    """
    セッションサービスのシングルトンインスタンスを生成・取得する。
    引数で渡された場合、そのクライアントを使用してサービスを初期化する。
    """
    # db_clientがNoneの場合、create_session_service内で新しいクライアントが生成される
    return create_session_service(db_client)


@lru_cache
def get_firestore_client() -> AsyncClient:
    """Firestore AsyncClientのシングルトンインスタンスを生成・取得する。"""
    return get_db_client()
