import asyncio
import logging
import ssl

import requests
from google.cloud import storage
from services.logging_service import get_logger
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)
from urllib3.exceptions import SSLError as UrllibSSLError

storage_client = storage.Client()
logger = get_logger(__name__)


def is_ssl_error(exc: BaseException) -> bool:
    """
    tenacity の predicate 用。例外自身または __cause__/__context__ に
    SSL 関連の例外が含まれているかを判定する（requests, urllib3, stdlib ssl）。
    """
    ssl_types = (requests.exceptions.SSLError, UrllibSSLError, ssl.SSLError)

    if isinstance(exc, ssl_types):
        return True

    # 例外チェーンにネストされているケースをカバー
    cause = getattr(exc, "__cause__", None)
    if isinstance(cause, ssl_types):
        return True

    context = getattr(exc, "__context__", None)
    if isinstance(context, ssl_types):
        return True

    return False


# tenacity の helper を使って RetryBase を作る
gcs_retry_decorator = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=10, max=60),
    retry=retry_if_exception(is_ssl_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


@gcs_retry_decorator
async def upload_blob_from_memory(
    bucket_name: str,
    destination_blob_name: str,
    data: bytes,
    content_type: str,
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
    logger.info(
        f"ファイルを {destination_blob_name} としてGCSバケット {bucket_name} にアップロードしています..."
    )
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # GCS クライアントは同期 API のため別スレッドで実行
    await asyncio.to_thread(blob.upload_from_string, data, content_type=content_type)

    gcs_path = f"gs://{bucket_name}/{destination_blob_name}"
    logger.info(f"ファイルを {gcs_path} にアップロードしました。")
    return gcs_path


@gcs_retry_decorator
async def rename_blob(bucket_name: str, blob_name: str, new_name: str) -> str:
    """
    同じバケット内でBlobの名前を変更（ファイル移動）する。

    Args:
        bucket_name: GCSバケットの名前。
        blob_name: 変更元のBlobの名前。
        new_name: 新しいBlobの名前。

    Returns:
        名前変更後のファイルのGCS URI。
    """
    logger.info(
        f"GCSバケット {bucket_name} 内で {blob_name} を {new_name} に移動しています..."
    )
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # 同様に別スレッドで実行
    new_blob = await asyncio.to_thread(bucket.rename_blob, blob, new_name)

    new_gcs_path = f"gs://{bucket_name}/{new_blob.name}"
    logger.info(f"ファイルを {blob.name} から {new_blob.name} に移動しました。")
    return new_gcs_path
