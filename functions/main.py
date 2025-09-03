from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Any

from firebase_admin import initialize_app
from firebase_functions import https_fn, options
from google.api_core.exceptions import GoogleAPIError
from google.cloud import firestore, storage

from config import get_settings

settings = get_settings()


# Initialize firebase admin app once (safe to call multiple times in some
# runtimes; guard in case it's already initialized).
try:
    initialize_app()
except Exception:
    # If it's already initialized, continue. Logging at debug level to avoid
    # noise in production logs.
    logging.debug("Firebase app already initialized or initialization skipped.")

options.set_global_options(region=options.SupportedRegion.ASIA_NORTHEAST1)

AUDIO_UPLOAD_BUCKET_NAME: str | None = settings.audio_upload_bucket
JOBS_COLLECTION_NAME: str = settings.firestore_collection

_storage_client = storage.Client()
_db = firestore.Client()


@https_fn.on_call()
def generate_signed_url(
    req: https_fn.CallableRequest[dict[str, Any]],
) -> dict[str, Any]:
    """Generates a short-lived v4 signed URL for client-side uploads.

    The client must call this Callable function while authenticated (Firebase
    Authentication). The returned signed URL requires the client to include
    specific headers (Content-Type and x-goog-meta-*) when performing the
    PUT upload.

    Request payload (req.data):
      {
        "contentType": "audio/webm"
      }

    Response:
      {
        "jobId": "job-xxxxxxxx-xxxx-...",
        "signedUrl": "https://storage.googleapis.com/...",
        "expiresIn": 900  # seconds
      }
    """
    # ---------------------- Authentication check -------------------------
    if req.auth is None or getattr(req.auth, "uid", None) is None:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="The function must be called while authenticated.",
        )

    user_id = req.auth.uid

    # ---------------------- Server configuration -------------------------
    if not AUDIO_UPLOAD_BUCKET_NAME:
        logging.error("Environment variable 'AUDIO_UPLOAD_BUCKET' is not set.")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="Server is not configured correctly.",
        )

    # ---------------------- Request validation ---------------------------
    content_type = None
    if isinstance(req.data, dict):
        content_type = req.data.get("contentType")

    if not content_type or not isinstance(content_type, str):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="The request must include a 'contentType' field.",
        )

    if not content_type.startswith("audio/"):
        logging.warning("contentType does not look like audio/*: %s", content_type)

    # ---------------------- Job & path generation ------------------------
    # Use a readable job-<uuid> id for traceability.
    job_uuid = str(uuid.uuid4())
    job_id = f"job-{job_uuid}"

    # Build object path. We use a simple map to ensure consistent file
    # extensions, as mimetypes.guess_extension can be unreliable for
    # some types like 'audio/webm'.
    ext_map = {
        "audio/webm": ".webm",
        "audio/mpeg": ".mp3",
    }
    ext = ext_map.get(content_type, "")

    # Use a more descriptive name to distinguish from generated audio.
    object_name = f"uploads/{user_id}/{job_id}/source_audio{ext}"

    bucket = _storage_client.bucket(AUDIO_UPLOAD_BUCKET_NAME)
    blob = bucket.blob(object_name)

    # Require the client to include custom metadata on upload.
    # These headers, prefixed with 'x-goog-meta-', are stored as object
    # metadata. Cloud Storage automatically makes them available in
    # CloudEvents (e.g., 'x-goog-meta-job_id' becomes 'job_id' in the
    # event payload's metadata field).
    required_metadata_headers = {
        "x-goog-meta-job_id": job_id,
        "x-goog-meta-user_id": user_id,
    }

    expiration_delta = timedelta(minutes=15)

    # ---------------------- Signed URL generation ------------------------
    try:
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_delta,
            method="PUT",
            content_type=content_type,
            headers=required_metadata_headers,
        )
    except GoogleAPIError as e:
        logging.exception("Failed to generate signed URL: %s", e)
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="Failed to generate signed URL.",
        ) from e

    # ---------------------- Firestore job registration -------------------
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
        logging.exception("Failed to create job document: %s", e)

        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="Failed to create job record.",
        ) from e

    logging.info(
        "Generated signed URL for user=%s job=%s object=%s",
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
