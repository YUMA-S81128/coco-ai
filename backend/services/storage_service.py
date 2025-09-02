import asyncio

from google.cloud import storage

from services.logging_service import get_logger

storage_client = storage.Client()
logger = get_logger(__name__)


async def upload_blob_from_memory(
    bucket_name: str, destination_blob_name: str, data: bytes, content_type: str
) -> str:
    """
    メモリ上のデータをCloud Storageにアップロードし、GCS URIを返す。
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        await asyncio.to_thread(
            blob.upload_from_string, data, content_type=content_type
        )

        gcs_path = f"gs://{bucket_name}/{destination_blob_name}"
        logger.info(f"File uploaded to {gcs_path}")
        return gcs_path
    except Exception as e:
        logger.error(
            f"Failed to upload to GCS bucket '{bucket_name}': {e}", exc_info=True
        )
        raise
