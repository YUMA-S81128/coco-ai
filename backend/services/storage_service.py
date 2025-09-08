import asyncio

from google.cloud import storage
from services.logging_service import get_logger

storage_client = storage.Client()
logger = get_logger(__name__)


async def upload_blob_from_memory(
    bucket_name: str, destination_blob_name: str, data: bytes, content_type: str
) -> str:
    """
    メモリ上のバイトオブジェクトからCloud Storageバケットにデータをアップロードする。

    Args:
        bucket_name: GCSバケットの名前。
        destination_blob_name: バケット内のオブジェクトの希望の名前。
        data: アップロードするデータ（バイトオブジェクト）。
        content_type: データのコンテントタイプ（例: 'audio/mpeg'）。

    Returns:
        アップロードされたファイルのGCS URI（例: 'gs://bucket-name/file-name'）。
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # GCSへのアップロードは同期的I/Oのため、別スレッドで実行
        await asyncio.to_thread(
            blob.upload_from_string, data, content_type=content_type
        )

        gcs_path = f"gs://{bucket_name}/{destination_blob_name}"
        logger.info(f"ファイルを {gcs_path} にアップロードしました。")
        return gcs_path
    except Exception as e:
        logger.error(
            f"GCSバケット '{bucket_name}' へのアップロードに失敗しました: {e}", exc_info=True
        )
        raise
