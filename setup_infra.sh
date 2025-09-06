#!/bin/bash
set -e # コマンドが失敗したらすぐにスクリプトを終了する

# --- 設定 ---
# プロジェクトルートの .env ファイルから環境変数を読み込む
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# 必須の環境変数が設定されているか確認
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ] || [ -z "$AUDIO_UPLOAD_BUCKET" ] || [ -z "$PROCESSED_AUDIO_BUCKET" ] || [ -z "$GENERATED_IMAGE_BUCKET" ]; then
  echo "エラー: 必須の環境変数が設定されていません。.env ファイルを確認してください。"
  exit 1
fi

echo "--- プロジェクトを設定中 ---"
# 共通の設定変数を読み込む
source "$(dirname "$0")/config.sh"
gcloud config set project ${GOOGLE_CLOUD_PROJECT_ID}

echo "--- Cloud Storage バケットを作成中 ---"
# Firebaseコンソールでの管理やセキュリティルールを適用したい場合は、
# 作成後にFirebaseコンソールからこのバケットを手動でインポートしてください。
for BUCKET in ${AUDIO_UPLOAD_BUCKET} ${PROCESSED_AUDIO_BUCKET} ${GENERATED_IMAGE_BUCKET}; do
  echo "Creating bucket: ${BUCKET}"
  gcloud storage buckets create gs://${BUCKET} \
    --project=${GOOGLE_CLOUD_PROJECT_ID} \
    --location=${REGION} \
    --uniform-bucket-level-access \
    --public-access-prevention
done

# --- Artifact Registryリポジトリを作成 ---
echo "--- Artifact Registryリポジトリを確認・作成中: ${ARTIFACT_REGISTRY_REPO} ---"
if gcloud artifacts repositories describe ${ARTIFACT_REGISTRY_REPO} --location=${REGION} >/dev/null 2>&1; then
  echo "Artifact Registryリポジトリ ${ARTIFACT_REGISTRY_REPO} は既に存在します。"
else
  echo "Artifact Registryリポジトリ ${ARTIFACT_REGISTRY_REPO} を作成中..."
  gcloud artifacts repositories create ${ARTIFACT_REGISTRY_REPO} \
    --repository-format=docker --location=${REGION}
fi

# --- サービスアカウント作成（Cloud Run実行用） ---
echo "--- Cloud Run用のサービスアカウントを確認・作成中: ${BACKEND_SA_NAME} ---"
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} >/dev/null 2>&1; then
  echo "サービスアカウント ${BACKEND_SA_NAME} は既に存在します。"
else
  echo "サービスアカウント ${BACKEND_SA_NAME} を作成中..."
  gcloud iam service-accounts create ${BACKEND_SA_NAME} \
    --display-name="Coco-Ai Backend Service Account"
fi

# --- サービスアカウントへの権限付与 ---
echo "--- サービスアカウントに必要なIAMロールを付与中 ---"

# プロジェクトレベルで付与するロールのリスト。可読性とメンテナンス性向上のためループ処理に集約。
PROJECT_LEVEL_ROLES=(
  "roles/logging.logWriter"      # ログ書き込み
  "roles/aiplatform.user"        # Vertex AI (Gemini)
  "roles/cloudtts.client"        # Text-to-Speech API
  "roles/cloudspeech.client"     # Speech-to-Text API
  "roles/datastore.user"         # Firestoreへの書き込み
)

echo "プロジェクトレベルのロールを付与中..."
for ROLE in "${PROJECT_LEVEL_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="${ROLE}" > /dev/null 2>&1
done

# バケットごとに、より細かい権限を付与
# アップロードされた質問音声用バケットへの読み取り権限
gcloud storage buckets add-iam-policy-binding gs://${AUDIO_UPLOAD_BUCKET} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectViewer" > /dev/null 2>&1

# 解説音声用バケットへの書き込み権限
gcloud storage buckets add-iam-policy-binding gs://${PROCESSED_AUDIO_BUCKET} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectCreator" > /dev/null 2>&1

# 説明画像用バケットへの書き込み権限
gcloud storage buckets add-iam-policy-binding gs://${GENERATED_IMAGE_BUCKET} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectCreator" > /dev/null 2>&1

echo "✅ Infrastructure setup complete."