#!/bin/bash
set -e # コマンドが失敗したらすぐにスクリプトを終了する

# --- 設定 ---
# CI環境では環境変数が直接設定されるため、ローカル実行時のみ .env を読み込む
if [ -f .env ] && [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ] || [ -z "$AUDIO_UPLOAD_BUCKET" ]; then
  echo "エラー: 必須の環境変数が設定されていません。.env ファイルを確認してください。"
  exit 1
fi

# 共通の設定変数を読み込む
source "$(dirname "$0")/config.sh"

# デプロイ対象を第一引数から取得。指定がなければ 'all' をデフォルト値とする。
TARGET=${1:-all}

# --- デプロイ用関数 ---

deploy_rules() {
  echo "--- [1/5] Firestore & Storage ルールをデプロイ中 ---"
  firebase deploy --only firestore:rules
  firebase deploy --only storage
}

deploy_functions() {
  echo "--- [2/5] Cloud Functions をデプロイ中 ---"
  (cd functions && firebase deploy --only "functions:${FUNCTION_NAME}" \
    --set-env-vars="AUDIO_UPLOAD_BUCKET=${AUDIO_UPLOAD_BUCKET},FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION}")
}

deploy_backend() {
  echo "--- [3/5] バックエンドをCloud Runへデプロイ中 ---"
  (
    cd backend
    IMAGE_TAG="${REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${BACKEND_SERVICE_NAME}:$(date +%Y%m%d-%H%M%S)"
    echo "Building and pushing image: ${IMAGE_TAG}"
    gcloud builds submit --tag "${IMAGE_TAG}" --quiet
    echo "Deploying to Cloud Run..."
    gcloud run deploy ${BACKEND_SERVICE_NAME} \
      --image "${IMAGE_TAG}" \
      --platform managed \
      --region ${REGION} \
      --service-account ${SERVICE_ACCOUNT_EMAIL} \
      --no-allow-unauthenticated \
      --set-env-vars="^##^GOOGLE_CLOUD_PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID}##AUDIO_UPLOAD_BUCKET=${AUDIO_UPLOAD_BUCKET}##PROCESSED_AUDIO_BUCKET=${PROCESSED_AUDIO_BUCKET}##GENERATED_IMAGE_BUCKET=${GENERATED_IMAGE_BUCKET}##FIRESTORE_COLLECTION=${FIRESTORE_COLLECTION}##SESSION_SERVICE=vertex"
  )
}

deploy_trigger() {
  echo "--- [4/5] Eventarcトリガーを設定中 ---"
  # Eventarc用のサービスアカウントは setup_infra.sh で作成済みとします
  gcloud run services add-iam-policy-binding ${BACKEND_SERVICE_NAME} \
    --region=${REGION} \
    --member="serviceAccount:${TRIGGER_SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.invoker" > /dev/null 2>&1
  if gcloud eventarc triggers describe ${TRIGGER_NAME} --location=${REGION} >/dev/null 2>&1; then
    echo "Eventarcトリガー ${TRIGGER_NAME} は既に存在します。"
  else
    echo "Eventarcトリガーを作成中..."
    gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} --member="serviceAccount:service-$(gcloud projects describe ${GOOGLE_CLOUD_PROJECT_ID} --format='value(projectNumber)')@gcp-sa-pubsub.iam.gserviceaccount.com" --role='roles/pubsub.publisher' >/dev/null 2>&1 || true
    gcloud eventarc triggers create ${TRIGGER_NAME} \
      --location=${REGION} \
      --destination-run-service=${BACKEND_SERVICE_NAME} \
      --destination-run-region=${REGION} \
      --event-filters="type=google.cloud.storage.object.v1.finalized" \
      --event-filters="bucket=${AUDIO_UPLOAD_BUCKET}" \
      --service-account=${TRIGGER_SERVICE_ACCOUNT_EMAIL}
  fi
}

deploy_app() {
  echo "--- [5/5] フロントエンドをFirebase Hostingへデプロイ中 ---"
  # FlutterのビルドはCloud Buildの別ステップで実行されるため、ここではデプロイのみ行う
  firebase deploy --only hosting
}

# --- 実行 ---
case "$TARGET" in
  rules) deploy_rules ;;
  functions) deploy_functions ;;
  backend) deploy_backend; deploy_trigger ;; # バックエンドデプロイ後にトリガーも設定
  app) deploy_app ;;
  all)
    deploy_rules
    deploy_functions
    deploy_backend
    deploy_trigger
    deploy_app
    ;;
  *)
    echo "エラー: 不明なデプロイターゲット '$TARGET'"
    echo "利用可能なターゲット: rules, functions, backend, app, all"
    exit 1
    ;;
esac

echo "✅ デプロイが正常に完了しました！ (Target: $TARGET)"
