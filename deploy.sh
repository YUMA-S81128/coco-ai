#!/bin/bash
set -e # コマンドが失敗したらすぐにスクリプトを終了する

# --- 設定 ---
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ] || [ -z "$AUDIO_UPLOAD_BUCKET" ]; then
  echo "エラー: 必須の環境変数が設定されていません。.env ファイルを確認してください。"
  exit 1
fi

# 共通の設定変数を読み込む
source "$(dirname "$0")/config.sh"

# --- 1. FirestoreルールとFirebase Hostingのデプロイ ---
echo "--- Firestoreルールをデプロイ中 ---"
firebase deploy --only firestore:rules

echo "--- Cloud Storageルールをデプロイ中 ---"
firebase deploy --only storage

# --- 2. Cloud Functionsのデプロイ ---
echo "--- Cloud Functionsをデプロイ中 ---"
cd functions
firebase deploy --only "functions:${FUNCTION_NAME}" \
  --set-env-vars="AUDIO_UPLOAD_BUCKET=${AUDIO_UPLOAD_BUCKET},FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION}"
cd ..

# --- 3. バックエンドをCloud Runへデプロイ ---
echo "--- バックエンドをビルドしてCloud Runへデプロイ中 ---"
cd backend

# Artifact Registry用のイメージタグを生成 (例: asia-northeast1-docker.pkg.dev/your-proj/coco-ai/coco-ai-backend:20231027-153000)
IMAGE_TAG="${REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${BACKEND_SERVICE_NAME}:$(date +%Y%m%d-%H%M%S)"

# Cloud Buildでコンテナイメージをビルド
gcloud builds submit --tag "${IMAGE_TAG}"

# Cloud Runへデプロイ
gcloud run deploy ${BACKEND_SERVICE_NAME} \
  --image "${IMAGE_TAG}" \
  --platform managed \
  --region ${REGION} \
  --service-account ${SERVICE_ACCOUNT_EMAIL} \
  --no-allow-unauthenticated \
  --set-env-vars="^##^GOOGLE_CLOUD_PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID}##AUDIO_UPLOAD_BUCKET=${AUDIO_UPLOAD_BUCKET}##PROCESSED_AUDIO_BUCKET=${PROCESSED_AUDIO_BUCKET}##GENERATED_IMAGE_BUCKET=${GENERATED_IMAGE_BUCKET}##FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION}##SESSION_SERVICE=vertex"

cd ..

# --- 4. Eventarcトリガーの作成 ---
echo "--- Eventarcトリガー用のサービスアカウントと権限を設定中 ---"
# EventarcがCloud Runを呼び出すための、最小権限の原則に従った専用サービスアカウントを作成します。
if ! gcloud iam service-accounts describe ${TRIGGER_SERVICE_ACCOUNT_EMAIL} >/dev/null 2>&1; then
  gcloud iam service-accounts create ${TRIGGER_SA_NAME} --display-name="Coco-Ai Eventarc Invoker"
fi

# トリガーがCloud Runサービスを呼び出すアイデンティティとしてこのサービスアカウントを使用するため、
# トリガー作成の前に、対象サービスに対する呼び出し元(run.invoker)ロールを付与しておく必要があります。
gcloud run services add-iam-policy-binding ${BACKEND_SERVICE_NAME} \
  --region=${REGION} \
  --member="serviceAccount:${TRIGGER_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/run.invoker" > /dev/null 2>&1

echo "--- Eventarcトリガーを確認・作成中: ${TRIGGER_NAME} ---"
if gcloud eventarc triggers describe ${TRIGGER_NAME} --location=${REGION} >/dev/null 2>&1; then
  echo "Eventarcトリガー ${TRIGGER_NAME} は既に存在します。"
else
  echo "Eventarcトリガーを作成中..."
  # EventarcがGCSイベントをリッスンするための権限をPub/Subサービスアカウントに付与
  # これは初回のみ必要な設定
  gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} --member="serviceAccount:service-$(gcloud projects describe ${GOOGLE_CLOUD_PROJECT_ID} --format='value(projectNumber)')@gcp-sa-pubsub.iam.gserviceaccount.com" --role='roles/pubsub.publisher' >/dev/null 2>&1 || true
  gcloud eventarc triggers create ${TRIGGER_NAME} \
    --location=${REGION} \
    --destination-run-service=${BACKEND_SERVICE_NAME} \
    --destination-run-region=${REGION} \
    --event-filters="type=google.cloud.storage.object.v1.finalized" \
    --event-filters="bucket=${AUDIO_UPLOAD_BUCKET}" \
    --service-account=${TRIGGER_SERVICE_ACCOUNT_EMAIL} # ここで指定したSAが呼び出しのアイデンティティになる
fi

# --- 5. フロントエンドをFirebase Hostingへデプロイ ---
echo "--- フロントエンドをビルドしてFirebase Hostingへデプロイ中 ---"
cd app
flutter build web --release
cd ..
firebase deploy --only hosting

echo "--- 全てのデプロイが正常に完了しました！ ---"
