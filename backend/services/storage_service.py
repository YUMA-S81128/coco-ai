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


async def rename_blob(
    bucket_name: str, blob_name: str, new_name: str
) -> str:
    """
    同じバケット内でBlobの名前を変更（移動）する。

    Args:
        bucket_name: GCSバケットの名前。
        blob_name: 変更元のBlobの名前。
        new_name: 新しいBlobの名前。

    Returns:
        名前変更後のファイルのGCS URI。
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # GCSの操作は同期的I/Oのため、別スレッドで実行
        new_blob = await asyncio.to_thread(bucket.rename_blob, blob, new_name)

        new_gcs_path = f"gs://{bucket_name}/{new_blob.name}"
        logger.info(f"ファイルを {blob.name} から {new_blob.name} に移動しました。")
        return new_gcs_path
    except Exception as e:
        logger.error(
            f"GCSバケット '{bucket_name}' 内でのファイル移動に失敗しました: {e}", exc_info=True
        )
        raise