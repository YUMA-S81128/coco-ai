import asyncio

from google.cloud import storage
from services.logging_service import get_logger

storage_client = storage.Client()
logger = get_logger(__name__)


async def upload_blob_from_memory(
    bucket_name: str, destination_blob_name: str, data: bytes, content_type: str
) -> str:
    """
    Uploads data from a bytes object in memory to a Cloud Storage bucket.

    Args:
        bucket_name: The name of the GCS bucket.
        destination_blob_name: The desired name for the object in the bucket.
        data: The data to upload as a bytes object.
        content_type: The content type of the data (e.g., 'audio/mpeg').

    Returns:
        The GCS URI of the uploaded file (e.g., 'gs://bucket-name/file-name').
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
