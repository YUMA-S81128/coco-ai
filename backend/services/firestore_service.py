from google.cloud import firestore
from services.logging_service import get_logger

from config import get_settings

logger = get_logger(__name__)


async def _update_job(db: firestore.AsyncClient, job_id: str, payload: dict):
    """Firestoreのジョブドキュメントを更新する内部ヘルパー関数"""
    settings = get_settings()
    logger.info(f"[{job_id}] ジョブを更新中... ペイロード: {payload}")

    # タイムスタンプは共通ロジックとしてここで追加
    payload["updatedAt"] = firestore.SERVER_TIMESTAMP

    job_ref = db.collection(settings.firestore_collection).document(job_id)

    try:
        await job_ref.set(payload, merge=True)
        logger.info(f"[{job_id}] ジョブの更新が完了しました。")
    except Exception as e:
        logger.error(
            f"[{job_id}] ジョブ更新中にエラーが発生しました: {e}", exc_info=True
        )
        raise


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
    update_payload = {"status": status}
    if data:
        update_payload.update(data)
    await _update_job(db, job_id, update_payload)


async def update_job_data(db: firestore.AsyncClient, job_id: str, data: dict):
    """
    Firestoreのジョブドキュメントにデータのみをマージする。
    ステータスは変更しない。

    Args:
        db: Firestoreクライアントのインスタンス。
        job_id: 更新対象のジョブID。
        data: 保存する追加情報の辞書。
    """
    # ペイロードは渡されたデータ辞書そのもの
    await _update_job(db, job_id, data)
