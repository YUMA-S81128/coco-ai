from google.cloud import firestore
from services.logging_service import get_logger

from config import get_settings

logger = get_logger(__name__)


async def update_job_status(
    db: firestore.AsyncClient, job_id: str, status: str, data: dict | None = None
):
    """
    Firestoreのジョブステータスと追加情報を更新する。

    Args:
        db: Firestoreクライアントのインスタンス。
        job_id: 更新対象のジョブID。
        status: 新しいステータス文字列。
        data: 保存する追加情報の辞書（任意）。
    """
    settings = get_settings()
    logger.info(f"[{job_id}] ステータスを '{status}' に更新中... データ: {data}")
    job_ref = db.collection(settings.firestore_collection).document(job_id)
    update_data = {
        "status": status,
        "updatedAt": firestore.SERVER_TIMESTAMP,  # サーバー側のタイムスタンプを使用
    }
    if data:
        update_data.update(data)

    try:
        await job_ref.set(update_data, merge=True)
        logger.info(f"[{job_id}] ステータスを '{status}' に更新しました。")
    except Exception as e:
        logger.error(
            f"[{job_id}] ステータス更新中にエラーが発生しました: {e}", exc_info=True
        )
        raise
