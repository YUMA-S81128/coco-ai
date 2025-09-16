from functools import lru_cache

from google.adk.sessions import BaseSessionService
from google.cloud import firestore
from services.session_service import create_session_service


@lru_cache
def get_session_service() -> BaseSessionService:
    """セッションサービスのシングルトンインスタンスを生成・取得する。"""
    return create_session_service()


@lru_cache
def get_firestore_client() -> firestore.Client:
    """Firestore Clientのシングルトンインスタンスを生成・取得する。"""
    return firestore.Client()
