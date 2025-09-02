import logging
import uuid
from datetime import timedelta

from firebase_admin import firestore, initialize_app
from firebase_functions import https_fn, options
from google.cloud import storage

from config import get_settings

settings = get_settings()


initialize_app()

# Set the default region to Japan (asia-northeast1) for all functions.
options.set_global_options(region=options.SupportedRegion.ASIA_NORTHEAST1)

# Get the Cloud Storage bucket name from environment variables.
# This is the bucket where the client will upload audio files.
AUDIO_UPLOAD_BUCKET_NAME = settings.audio_upload_bucket


@https_fn.on_call()
def generate_signed_url(req: https_fn.CallableRequest) -> https_fn.Response:
    """
    Generates a v4 signed URL for uploading an audio file to Cloud Storage.

    This is a Callable Function that must be invoked by an authenticated user
    from the client application. It performs several key tasks:
    1. Generates a unique job ID for the entire workflow.
    2. Creates a Firestore document to track the job's status.
    3. Generates a short-lived, secure URL that the client can use to directly
       upload the audio file to a specific path in Cloud Storage.
    4. Requires the client to include custom metadata (`job-id`, `user-id`)
       in the upload request, which is then attached to the Storage object.

    Args:
        req.data['contentType']: The content type of the file to be uploaded
                                 (e.g., 'audio/webm').

    Returns:
        A dictionary containing the `jobId` and the `signedUrl`.

    Raises:
        https_fn.HttpsError: If the user is not authenticated, or if required
                             parameters or server configurations are missing.
    """
    # 1. Authentication Check
    if req.auth is None:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="The function must be called while authenticated.",
        )
    user_id = req.auth.uid

    # 2. Server Configuration Check
    if AUDIO_UPLOAD_BUCKET_NAME is None:
        logging.error("Environment variable 'AUDIO_UPLOAD_BUCKET' is not set.")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message="The server is not configured correctly.",
        )

    # 3. Request Parameter Check
    content_type = req.data.get("contentType")
    if not content_type:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="The request must include a 'contentType' field.",
        )

    # 4. Generate Job ID and Define File Path
    job_id = str(uuid.uuid4())
    # Include user ID in the file path for better organization and security rules.
    file_name = f"uploads/{user_id}/{job_id}/audio.webm"

    storage_client = storage.Client()
    bucket = storage_client.bucket(AUDIO_UPLOAD_BUCKET_NAME)
    blob = bucket.blob(file_name)

    # 5. Generate a v4 signed URL for a PUT request (expires in 15 minutes).
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        content_type=content_type,
        # The client MUST include these headers in the PUT request.
        # These headers will be stored as custom metadata on the GCS object.
        headers={
            "x-goog-meta-job-id": job_id,
            "x-goog-meta-user-id": user_id,
        },
    )

    # 6. Create an initial job document in Firestore to track progress.
    db = firestore.client()
    db.collection("jobs").document(job_id).set(
        {
            "userId": user_id,
            "status": "initializing",
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
    )

    logging.info(f"Generated signed URL for user {user_id} and job {job_id}.")

    return {"jobId": job_id, "signedUrl": signed_url}
