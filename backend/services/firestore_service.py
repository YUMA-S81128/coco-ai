import asyncio

from google.cloud import firestore
from services.logging_service import get_logger

from config import get_settings

settings = get_settings()
db = firestore.Client()
logger = get_logger(__name__)


async def update_job_status(job_id: str, status: str, data: dict | None = None):
    """
    Update the job status and additional information in Firestore.

    Args:
        job_id: The ID of the job to update.
        status: The new status string.
        data: Optional dictionary of additional data to store.
    """
    logger.info(f"[{job_id}] Updating status to '{status}' with data: {data}")
    job_ref = db.collection(settings.firestore_collection).document(job_id)
    update_data = {
        "status": status,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    if data:
        update_data.update(data)

    try:
        await asyncio.to_thread(lambda: job_ref.set(update_data, merge=True))
        logger.info(f"[{job_id}] Status updated to '{status}'")
    except Exception as e:
        logger.error(f"[{job_id}] Error updating status: {e}", exc_info=True)
        raise
