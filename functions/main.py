import logging
import os
import uuid
from datetime import timedelta

from firebase_admin import firestore, initialize_app
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
    この関数はクライアントアプリから呼び出し可能で、ユーザー認証が必須です。

    Args:
        req.data['contentType']: アップロードファイルのContent-Type (例: 'audio/webm')

    Returns:
        jobIdとsignedUrlを含む辞書。

    Raises:
        https_fn.HttpsError: ユーザーが認証されていない場合、または
                             必須パラメータが不足しているか設定が不適切な場合。
    """
    # 1. 認証チェック
    if req.auth is None:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="The function must be called while authenticated.",
        )
    user_id = req.auth.uid

    # 2. 環境変数チェック
    if BUCKET_NAME is None:
        logging.error("Environment variable 'AUDIO_UPLOAD_BUCKET' is not set.")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="The server is not configured correctly.",
        )

    # 3. リクエストパラメータチェック
    content_type = req.data.get("contentType")
    if not content_type:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="The request must include a 'contentType' field.",
        )

    # 4. ジョブIDの生成とファイルパスの定義
    job_id = str(uuid.uuid4())
    # ファイルパスにユーザーIDを含め、セキュリティルールと整合させる
    file_name = f"uploads/{user_id}/{job_id}/audio.webm"

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)

    # 5. PUTリクエスト用のv4署名付きURLを生成（有効期限: 15分）
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        content_type=content_type,
        headers={"x-goog-meta-job-id": job_id},
    )

    # 6. Firestoreに初期状態のジョブドキュメントを作成
    db = firestore.client()
    db.collection("jobs").document(job_id).set(
        {
            "userId": user_id,  # 所有者のユーザーIDを保存
            "status": "initializing",
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
    )

    logging.info(f"Generated signed URL for user {user_id} and job {job_id}.")

    return {"jobId": job_id, "signedUrl": signed_url}
