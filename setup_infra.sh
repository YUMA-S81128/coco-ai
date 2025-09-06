#!/bin/bash
set -e # コマンドが失敗したらすぐにスクリプトを終了する

# --- 設定 ---
# このスクリプトは、Cloud Shellなどの環境で実行されることを想定しています。
# 実行前に、以下の環境変数を設定してください。
#
# export GOOGLE_CLOUD_PROJECT_ID="your-gcp-project-id"
# export AUDIO_UPLOAD_BUCKET="${GOOGLE_CLOUD_PROJECT_ID}-coco-ai-input-audio"
# export PROCESSED_AUDIO_BUCKET="${GOOGLE_CLOUD_PROJECT_ID}-coco-ai-output-narrations"
# export GENERATED_IMAGE_BUCKET="${GOOGLE_CLOUD_PROJECT_ID}-coco-ai-output-images"

# 必須の環境変数が設定されているか確認
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ] || [ -z "$AUDIO_UPLOAD_BUCKET" ] || [ -z "$PROCESSED_AUDIO_BUCKET" ] || [ -z "$GENERATED_IMAGE_BUCKET" ]; then
  echo "エラー: 必須の環境変数（GOOGLE_CLOUD_PROJECT_ID, AUDIO_UPLOAD_BUCKET, PROCESSED_AUDIO_BUCKET, GENERATED_IMAGE_BUCKET）が設定されていません。"
  echo "スクリプトの冒頭のコメントを参考に、環境変数を設定してから再実行してください。"
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
 
# --- サービスアカウントの作成 ---
echo "--- サービスアカウントを確認・作成中 ---"

SERVICE_ACCOUNTS=(
  "${BACKEND_SA_NAME}|Coco-Ai Backend Service Account|${SERVICE_ACCOUNT_EMAIL}"
  "${TRIGGER_SA_NAME}|Coco-Ai Eventarc Invoker|${TRIGGER_SERVICE_ACCOUNT_EMAIL}"
  "${CLOUDBUILD_SA_NAME}|Coco-Ai Cloud Build Service Account|${CLOUDBUILD_SERVICE_ACCOUNT_EMAIL}"
)

for sa_info in "${SERVICE_ACCOUNTS[@]}"; do
  IFS='|' read -r sa_name sa_display_name sa_email <<< "$sa_info"
  if ! gcloud iam service-accounts describe ${sa_email} >/dev/null 2>&1; then
    echo "サービスアカウント ${sa_name} を作成中..."
    gcloud iam service-accounts create ${sa_name} --display-name="${sa_display_name}"
  else
    echo "サービスアカウント ${sa_name} は既に存在します。"
  fi
done

# --- サービスアカウントへの権限付与 ---
echo "--- バックエンド用サービスアカウントに必要なIAMロールを付与中 ---"

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
  gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} >/dev/null 2>&1 \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="${ROLE}"
done

# バケットごとに、より細かい権限を付与
# アップロードされた質問音声用バケットへの読み取り権限
gcloud storage buckets add-iam-policy-binding gs://${AUDIO_UPLOAD_BUCKET} >/dev/null 2>&1 \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectViewer"

# 解説音声用バケットへの書き込み権限
gcloud storage buckets add-iam-policy-binding gs://${PROCESSED_AUDIO_BUCKET} >/dev/null 2>&1 \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectCreator"

# 説明画像用バケットへの書き込み権限
gcloud storage buckets add-iam-policy-binding gs://${GENERATED_IMAGE_BUCKET} >/dev/null 2>&1 \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectCreator"

echo "--- Cloud Build サービスアカウントに必要なIAMロールを付与中 ---"
CLOUDBUILD_ROLES=(
  "roles/cloudbuild.builds.editor"    # Cloud Build を使用してビルドを実行
  "roles/run.developer"               # Cloud Run サービスのデプロイと更新
  "roles/eventarc.admin"              # Eventarc トリガーの作成と管理
  "roles/iam.serviceAccountUser"      # Cloud Run/Functions にサービスアカウントを関連付ける
  "roles/firebaserules.admin"         # Firestore/Storage ルールのデプロイ
  "roles/cloudfunctions.developer"    # Cloud Functions のデプロイ
  "roles/firebasehosting.admin"       # Firebase Hosting のデプロイ
)

echo "Cloud Build サービスアカウント (${CLOUDBUILD_SA_NAME}) にロールを付与中..."
for ROLE in "${CLOUDBUILD_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} >/dev/null 2>&1 \
    --member="serviceAccount:${CLOUDBUILD_SERVICE_ACCOUNT_EMAIL}" \
    --role="${ROLE}"
done

echo "✅ Infrastructure setup complete."