from google.adk.sessions import InMemorySessionService, VertexAiSessionService

from config import get_settings
from services.logging_service import get_logger

settings = get_settings()
logger = get_logger(__name__)


# ---------------------------
# セッションサービスのファクトリ
# ---------------------------
def create_session_service():
    """
    設定に基づいて適切なセッションサービス（インメモリまたはVertex AI）を作成する。

    Returns:
        セッションサービスのインスタンス。
    """
    session_type_setting = settings.session_service

    if session_type_setting == "inmemory":
        logger.info("ADKセッションにInMemorySessionServiceを使用します（開発用）。")
        return InMemorySessionService()

    logger.info("ADKセッションにVertexAiSessionServiceを使用します（本番用）。")
    return VertexAiSessionService(
        project=settings.google_cloud_project_id, location=settings.region
    )
