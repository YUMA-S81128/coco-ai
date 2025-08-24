import os
import uuid
from datetime import timedelta

from firebase_admin import initialize_app, firestore
from firebase_functions import https_fn, options
from google.cloud import storage

initialize_app()

# 日本リージョン (asia-northeast1) をデフォルトに設定
options.set_global_options(region=options.SupportedRegion.ASIA_NORTHEAST1)

# 環境変数からCloud Storageのバケット名を取得
# このバケットは音声ファイルをアップロードする場所です
BUCKET_NAME = os.environ.get("AUDIO_UPLOAD_BUCKET")


@https_fn.on_call()
def generate_signed_url(req: https_fn.CallableRequest) -> https_fn.Response:
    """
    Cloud Storageへの音声ファイルアップロード用署名付きURLとジョブIDを生成する。

    Args:
        req.data['contentType']: アップロードするファイルのContent-Type (例: 'audio/wav')

    Returns:
        A dict containing the `jobId` and `signedUrl`.
    """
    if BUCKET_NAME is None:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="環境変数 'AUDIO_UPLOAD_BUCKET' が設定されていません。",
        )

    content_type = req.data.get("contentType")
    if not content_type:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="リクエストに 'contentType' が含まれていません。",
        )

    job_id = str(uuid.uuid4())
    file_name = f"uploads/{job_id}.wav"  # ファイル名をジョブIDと紐付ける

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)

    # 署名付きURLを生成（有効期限: 15分）
    # カスタムメタデータにジョブIDを含める
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        content_type=content_type,
        headers={"x-goog-meta-job-id": job_id},
    )

    # Firestoreにジョブドキュメントを初期状態で作成
    db = firestore.client()
    db.collection("jobs").document(job_id).set({
        "status": "initializing",
        "createdAt": firestore.SERVER_TIMESTAMP,
    })

    return {"jobId": job_id, "signedUrl": signed_url}