from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Any

from firebase_admin import initialize_app
from firebase_functions import https_fn, options
from google.auth import default as default_credentials
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from google.cloud import firestore, storage

from .config import settings

# Firebase Admin Appを一度だけ初期化
try:
    initialize_app()
except Exception:
    # すでに初期化済みの場合は続行
    # デバッグレベルでロギング
    logging.debug("Firebaseアプリはすでに初期化済みか、初期化がスキップされました。")

options.set_global_options(region=options.SupportedRegion.ASIA_NORTHEAST1)

AUDIO_UPLOAD_BUCKET_NAME: str | None = settings.audio_upload_bucket
JOBS_COLLECTION_NAME: str = settings.firestore_collection
FUNCTION_SA_EMAIL: str = settings.function_sa_email

_db = firestore.Client()


@https_fn.on_call()
def generate_signed_url(
    req: https_fn.CallableRequest[dict[str, Any]],
) -> dict[str, Any]:
    """クライアントサイドのアップロード用に、v4署名付きURLを生成。

    クライアントは認証済み（Firebase Authentication）の状態でこのCallable関数を呼び出す必要がある。
    返された署名付きURLでは、クライアントがPUTアップロードを実行する際にContent-Typeおよびx-goog-meta-*を含める必要がある。

    リクエストペイロード (req.data):
      {
        "contentType": "audio/webm"
      }

    レスポンス:
      {
        "jobId": "job-xxxxxxxx-xxxx-...",
        "signedUrl": "https://storage.googleapis.com/...",
        "expiresIn": 900,  # 秒
        "requiredHeaders": { ... }
      }
    """
    # ---------------------- 認証チェック -------------------------
    if req.auth is None or getattr(req.auth, "uid", None) is None:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="この関数は認証された状態で呼び出す必要があります。",
        )

    user_id = req.auth.uid

    # ---------------------- サーバー設定チェック -------------------------
    if not AUDIO_UPLOAD_BUCKET_NAME:
        logging.error("環境変数 'AUDIO_UPLOAD_BUCKET' が設定されていません。")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="サーバーが正しく設定されていません。",
        )

    # ---------------------- リクエスト検証 ---------------------------
    content_type = None
    if isinstance(req.data, dict):
        content_type = req.data.get("contentType")

    if not content_type or not isinstance(content_type, str):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="リクエストには'contentType'フィールドを含める必要があります。",
        )

    if not content_type.startswith("audio/"):
        logging.warning("contentTypeがaudio/*形式ではないようです: %s", content_type)

    # ---------------------- ジョブIDとパスの生成 ------------------------
    job_uuid = str(uuid.uuid4())
    job_id = f"job-{job_uuid}"

    # オブジェクトパスを構築する
    ext_map = {
        "audio/webm": ".webm",
        "audio/mpeg": ".mp3",
    }
    ext = ext_map.get(content_type)

    if not ext:
        logging.error("未対応のcontentTypeです: %s", content_type)
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"未対応のcontentTypeです: {content_type}。対応しているタイプ: {list(ext_map.keys())}",
        )

    object_name = f"{user_id}/{job_id}/source_audio{ext}"

    # クライアントにアップロード時にカスタムメタデータを含めるよう要求する。
    # Cloud StorageはこれらをCloudEventsで自動的に利用可能にする。
    # （例：'x-goog-meta-job_id'はイベントペイロードのmetadataフィールドで'job_id'になる）
    required_metadata_headers = {
        "x-goog-meta-job_id": job_id,
        "x-goog-meta-user_id": user_id,
    }

    expiration_delta = timedelta(minutes=15)

    # ---------------------- 署名付きURLの生成 ------------------------
    try:
        # ImpersonatedCredentials を使用して署名
        # Cloud Functionsの実行IDが、指定されたサービスアカウント(FUNCTION_SA_EMAIL)に
        # なりすまして署名を行う。

        # 1. Cloud Functionsの実行環境の認証情報（ソース）を取得
        source_credentials, project_id = default_credentials(
            scopes=["https://www.googleapis.com/auth/iam"]
        )

        # 2. なりすまし先のサービスアカウント（ターゲット）を指定して、署名可能な認証情報を作成
        lifetime_seconds = int(expiration_delta.total_seconds())
        if lifetime_seconds <= 0:
            lifetime_seconds = 3600
        if lifetime_seconds > 3600:
            lifetime_seconds = 3600

        impersonated_creds = ImpersonatedCredentials(
            source_credentials=source_credentials,
            target_principal=FUNCTION_SA_EMAIL,
            target_scopes=["https://www.googleapis.com/auth/devstorage.read_write"],
            lifetime=lifetime_seconds,
        )

        # 3. 作成した認証情報を使って署名付きURLを生成
        #    blobオブジェクトは、この署名可能な認証情報を使って署名処理を行います。
        #    Requester Pays のバケットの場合は user_project を指定する必要があるため、
        #    impersonated client を作成して bucket を取得する。
        client_for_signing = storage.Client(
            credentials=impersonated_creds, project=project_id
        )

        if project_id:
            bucket_for_signing = client_for_signing.bucket(
                AUDIO_UPLOAD_BUCKET_NAME, user_project=project_id
            )
        else:
            bucket_for_signing = client_for_signing.bucket(AUDIO_UPLOAD_BUCKET_NAME)

        blob_for_signing = bucket_for_signing.blob(object_name)

        signed_url = blob_for_signing.generate_signed_url(
            version="v4",
            expiration=expiration_delta,
            method="PUT",
            content_type=content_type,
            headers=required_metadata_headers,
            credentials=impersonated_creds,
        )
    except Exception as e:
        logging.exception("署名付きURLの生成に失敗しました。")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="署名付きURLの生成に失敗しました。",
        ) from e

    # ---------------------- Firestoreジョブの登録 -------------------
    try:
        _db.collection(JOBS_COLLECTION_NAME).document(job_id).set(
            {
                "userId": user_id,
                "status": "initializing",
                "createdAt": firestore.SERVER_TIMESTAMP,
                "objectName": object_name,
            }
        )
    except Exception as e:
        logging.exception("ジョブドキュメントの作成に失敗しました。")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="ジョブレコードの作成に失敗しました。",
        ) from e

    logging.info(
        "ユーザー=%s、ジョブ=%s、オブジェクト=%s の署名付きURLを生成しました",
        user_id,
        job_id,
        object_name,
    )

    return {
        "jobId": job_id,
        "signedUrl": signed_url,
        "expiresIn": int(expiration_delta.total_seconds()),
        "requiredHeaders": {
            "Content-Type": content_type,
            **required_metadata_headers,
        },
    }
