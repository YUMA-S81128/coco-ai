#!/bin/bash
#
# setup_infra.sh と deploy.sh で共有される設定を定義します。
# このスクリプトは、実行前に .env ファイルが読み込まれていることを前提とします。

# --- 基本設定 ---
export REGION="asia-northeast1"

# --- サービス名 ---
export BACKEND_SERVICE_NAME="coco-ai-backend"
export FUNCTION_NAME="generate_signed_url"

# --- サービスアカウント名 (メールアドレスの@より前の部分) ---
export BACKEND_SA_NAME="coco-ai-backend-sa"
export TRIGGER_SA_NAME="coco-ai-eventarc-invoker"
export CLOUDBUILD_SA_NAME="coco-ai-cloudbuild-sa"

# --- リソース名 ---
export TRIGGER_NAME="trigger-coco-ai-storage"
export FIRESTORE_COLLECTION="jobs"
export ARTIFACT_REGISTRY_REPO="coco-ai"

# --- 派生変数 (メールアドレスなど) ---
# GOOGLE_CLOUD_PROJECT_ID が設定されている場合のみ実行
if [ -n "$GOOGLE_CLOUD_PROJECT_ID" ]; then
    export SERVICE_ACCOUNT_EMAIL="${BACKEND_SA_NAME}@${GOOGLE_CLOUD_PROJECT_ID}.iam.gserviceaccount.com"
    export TRIGGER_SERVICE_ACCOUNT_EMAIL="${TRIGGER_SA_NAME}@${GOOGLE_CLOUD_PROJECT_ID}.iam.gserviceaccount.com"
    export CLOUDBUILD_SERVICE_ACCOUNT_EMAIL="${CLOUDBUILD_SA_NAME}@${GOOGLE_CLOUD_PROJECT_ID}.iam.gserviceaccount.com"
fi
