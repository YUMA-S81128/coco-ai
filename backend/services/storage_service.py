import asyncio
import random

from google.cloud import storage
from services.logging_service import get_logger
from urllib3.exceptions import SSLError

storage_client = storage.Client()
logger = get_logger(__name__)


async def upload_blob_from_memory(
    bucket_name: str,
    destination_blob_name: str,
    data: bytes,
    content_type: str,
    max_retries: int = 5,
) -> str:
    """
    メモリ上のバイトオブジェクトからCloud Storageバケットにデータをアップロードする。
    一時的なエラー（特にSSLError）に対応するため、リトライ処理を実装。

    Args:
        bucket_name: GCSバケットの名前。
        destination_blob_name: バケット内のオブジェクトの希望の名前。
        data: アップロードするデータ（バイトオブジェクト）。
        content_type: データのコンテントタイプ（例: 'audio/mpeg'）。
        max_retries: 最大リトライ回数。

    Returns:
        アップロードされたファイルのGCS URI（例: 'gs://bucket-name/file-name'）。
    """
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    for attempt in range(max_retries):
        try:
            # GCSへのアップロードは同期的I/Oのため、別スレッドで実行
            await asyncio.to_thread(
                blob.upload_from_string, data, content_type=content_type
            )

            gcs_path = f"gs://{bucket_name}/{destination_blob_name}"
            logger.info(f"ファイルを {gcs_path} にアップロードしました。")
            return gcs_path
        except SSLError as e:
            if attempt < max_retries - 1:
                wait_time = (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    f"GCSへのアップロード中にSSLErrorが発生しました。リトライします... (試行 {attempt + 1}/{max_retries}) "
                    f"{wait_time:.2f}秒待機します。"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"GCSバケット '{bucket_name}' へのアップロードに失敗しました（リトライ上限到達）: {e}",
                    exc_info=True,
                )
                raise
        except Exception as e:
            logger.error(
                f"GCSバケット '{bucket_name}' へのアップロード中に予期せぬエラーが発生しました: {e}",
                exc_info=True,
            )
            raise
    # This should be unreachable if max_retries > 0, but as a fallback.
    raise Exception(f"Failed to upload to GCS after {max_retries} retries.")


async def rename_blob(
    bucket_name: str, blob_name: str, new_name: str, max_retries: int = 5
) -> str:
    """
    同じバケット内でBlobの名前を変更（移動）する。
    一時的なエラー（特にSSLError）に対応するため、リトライ処理を実装。

    Args:
        bucket_name: GCSバケットの名前。
        blob_name: 変更元のBlobの名前。
        new_name: 新しいBlobの名前。
        max_retries: 最大リトライ回数。

    Returns:
        名前変更後のファイルのGCS URI。
    """
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    for attempt in range(max_retries):
        try:
            # GCSの操作は同期的I/Oのため、別スレッドで実行
            new_blob = await asyncio.to_thread(bucket.rename_blob, blob, new_name)

            new_gcs_path = f"gs://{bucket_name}/{new_blob.name}"
            logger.info(f"ファイルを {blob.name} から {new_blob.name} に移動しました。")
            return new_gcs_path
        except SSLError as e:
            if attempt < max_retries - 1:
                wait_time = (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    f"GCSでのファイル移動中にSSLErrorが発生しました。リトライします... (試行 {attempt + 1}/{max_retries}) "
                    f"{wait_time:.2f}秒待機します。"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"GCSバケット '{bucket_name}' 内でのファイル移動に失敗しました（リトライ上限到達）: {e}",
                    exc_info=True,
                )
                raise
        except Exception as e:
            logger.error(
                f"GCSバケット '{bucket_name}' 内でのファイル移動中に予期せぬエラーが発生しました: {e}",
                exc_info=True,
            )
            raise
    # This should be unreachable if max_retries > 0, but as a fallback.
    raise Exception(f"Failed to move file in GCS after {max_retries} retries.")