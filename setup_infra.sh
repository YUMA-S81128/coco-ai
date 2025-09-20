#!/bin/bash
set -e # コマンドが失敗したらすぐにスクリプトを終了する

# --- 設定 ---
# このスクリプトは、Cloud Shellなどの環境で実行されることを想定しています。
# 実行前に、以下の環境変数を設定してください。
#
# export GOOGLE_CLOUD_PROJECT
# export AUDIO_UPLOAD_BUCKET
# export PROCESSED_AUDIO_BUCKET
# export GENERATED_IMAGE_BUCKET

# 必須の環境変数が設定されているか確認
if [ -z "$GOOGLE_CLOUD_PROJECT" ] || [ -z "$AUDIO_UPLOAD_BUCKET" ] || [ -z "$PROCESSED_AUDIO_BUCKET" ] || [ -z "$GENERATED_IMAGE_BUCKET" ]; then
  echo "エラー: 必須の環境変数（GOOGLE_CLOUD_PROJECT, AUDIO_UPLOAD_BUCKET, PROCESSED_AUDIO_BUCKET, GENERATED_IMAGE_BUCKET）が設定されていません。"
  echo "スクリプトの冒頭のコメントを参考に、環境変数を設定してから再実行してください。"
  exit 1
fi

echo "--- プロジェクトを設定中 ---"
# 共通の設定変数を読み込む
source "$(dirname "$0")/config.sh"
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

echo "--- Cloud Storage バケットを作成中 ---"
# Firebaseコンソールでの管理やセキュリティルールを適用したい場合は、
# 作成後にFirebaseコンソールからこのバケットを手動でインポートしてください。
for BUCKET in ${AUDIO_UPLOAD_BUCKET} ${PROCESSED_AUDIO_BUCKET} ${GENERATED_IMAGE_BUCKET}; do
  if gcloud storage buckets describe gs://${BUCKET} >/dev/null 2>&1; then
    echo "Bucket gs://${BUCKET} は既に存在します。作成をスキップします。"
  else
    echo "Creating bucket: gs://${BUCKET}"
    gcloud storage buckets create gs://${BUCKET} \
      --project=${GOOGLE_CLOUD_PROJECT} \
      --location=${GOOGLE_CLOUD_LOCATION} \
      --uniform-bucket-level-access \
      --public-access-prevention
  fi
done

echo "--- アップロード用バケットにCORS設定を適用中 ---"
# フロントエンド（Firebase Hosting）からのアップロードを許可するためのCORS設定
CORS_CONFIG_FILE=$(mktemp)
cat > "${CORS_CONFIG_FILE}" <<EOF
[
  {
    "origin": [
      "https://${GOOGLE_CLOUD_PROJECT}.web.app"
    ],
    "method": ["PUT"],
    "responseHeader": [
      "Content-Type",
      "x-goog-meta-job_id",
      "x-goog-meta-user_id"
    ],
    "maxAgeSeconds": 3600
  }
]
EOF

gcloud storage buckets update "gs://${AUDIO_UPLOAD_BUCKET}" --cors-file="${CORS_CONFIG_FILE}"
rm "${CORS_CONFIG_FILE}" # 一時ファイルを削除

echo "--- 画像表示用バケットにCORS設定を適用中 ---"
# フロントエンド（Firebase Hosting）からの画像読み込みを許可するためのCORS設定
IMAGE_CORS_CONFIG_FILE=$(mktemp)
cat > "${IMAGE_CORS_CONFIG_FILE}" <<EOF
[
  {
    "origin": [
      "https://${GOOGLE_CLOUD_PROJECT}.web.app"
    ],
    "method": ["GET"],
    "maxAgeSeconds": 3600
  }
]
EOF

gcloud storage buckets update "gs://${GENERATED_IMAGE_BUCKET}" --cors-file="${IMAGE_CORS_CONFIG_FILE}"
rm "${IMAGE_CORS_CONFIG_FILE}" # 一時ファイルを削除

echo "--- Secret Managerのシークレットを確認・作成中 ---"
# Cloud Buildでフロントエンドのビルドに必要なFirebase設定キーのリスト
# これらのキーに対応するシークレットを作成します。
# 値は後で手動でコンソールから設定してください。
SECRET_KEYS=(
  "FIREBASE_API_KEY"
  "FIREBASE_APP_ID"
  "FIREBASE_MESSAGING_SENDER_ID"
  "FIREBASE_PROJECT_ID"
  "FIREBASE_STORAGE_BUCKET"
  "FIREBASE_AUTH_DOMAIN"
)

for SECRET_NAME in "${SECRET_KEYS[@]}"; do
  if gcloud secrets describe ${SECRET_NAME} >/dev/null 2>&1; then
    echo "Secret [${SECRET_NAME}] は既に存在します。作成をスキップします。"
  else
    echo "Secret [${SECRET_NAME}] を作成中..."
    gcloud secrets create ${SECRET_NAME} --replication-policy="automatic" >/dev/null
  fi
done

# --- Artifact Registryリポジトリを作成 ---
echo "--- Artifact Registryリポジトリを確認・作成中: ${ARTIFACT_REGISTRY_REPO} ---"
if gcloud artifacts repositories describe ${ARTIFACT_REGISTRY_REPO} --location=${GOOGLE_CLOUD_LOCATION} >/dev/null 2>&1; then
  echo "Artifact Registryリポジトリ ${ARTIFACT_REGISTRY_REPO} は既に存在します。"
else
  echo "Artifact Registryリポジトリ ${ARTIFACT_REGISTRY_REPO} を作成中..."
  gcloud artifacts repositories create ${ARTIFACT_REGISTRY_REPO} \
    --repository-format=docker --location=${GOOGLE_CLOUD_LOCATION}
fi

echo "--- Firestore データベースを確認・作成中 ---"
# Firestoreデータベースが存在しない場合のみ作成します。
if ! gcloud firestore databases describe --project=${GOOGLE_CLOUD_PROJECT} >/dev/null 2>&1; then
  echo "Firestore データベースを Native モードで作成中 (location: ${GOOGLE_CLOUD_LOCATION})..."
  gcloud firestore databases create --location=${GOOGLE_CLOUD_LOCATION} --project=${GOOGLE_CLOUD_PROJECT}
else
  echo "Firestore データベースは既に存在します。"
fi

# --- サービスアカウントの作成 ---
echo "--- サービスアカウントを確認・作成中 ---"

SERVICE_ACCOUNTS=(
  "${BACKEND_SA_NAME}|Coco-Ai Backend Service Account|${SERVICE_ACCOUNT_EMAIL}"
  "${TRIGGER_SA_NAME}|Coco-Ai Eventarc Invoker|${TRIGGER_SERVICE_ACCOUNT_EMAIL}"
  "${FUNCTION_SA_NAME}|Coco-Ai Function Service Account|${FUNCTION_SERVICE_ACCOUNT_EMAIL}"
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
  "roles/logging.logWriter"          # ログ書き込み
  "roles/aiplatform.user"            # Vertex AI (Gemini)
  "roles/speech.client"              # Speech-to-Text API
  "roles/datastore.user"             # Firestoreへの書き込み
)

echo "プロジェクトレベルのロールを付与中..."
for ROLE in "${PROJECT_LEVEL_ROLES[@]}"; do
  # 標準出力を/dev/nullにリダイレクトして成功時の長いポリシー出力を抑制し、エラー出力は表示されるようにします
  gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="${ROLE}" >/dev/null
done

# バケットごとに、より細かい権限を付与
# アップロードされた質問音声用バケットへの読み取り権限
gcloud storage buckets add-iam-policy-binding gs://${AUDIO_UPLOAD_BUCKET} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectViewer" >/dev/null

# 解説音声用バケットへの書き込み権限
gcloud storage buckets add-iam-policy-binding gs://${PROCESSED_AUDIO_BUCKET} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectCreator" >/dev/null

# 説明画像用バケットへのオブジェクトユーザー権限（オブジェクトの移動・削除を含む）
gcloud storage buckets add-iam-policy-binding gs://${GENERATED_IMAGE_BUCKET} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectUser" >/dev/null



echo "--- Functions用サービスアカウントに必要なIAMロールを付与中 ---"
# FunctionsがFirestoreにジョブを登録するための権限
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${FUNCTION_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/datastore.user" >/dev/null

# Functionsが自分自身の権限を借用して署名付きURLを生成するための権限
# (Service Account Token Creatorロールを自分自身に付与)
gcloud iam service-accounts add-iam-policy-binding ${FUNCTION_SERVICE_ACCOUNT_EMAIL} \
  --member="serviceAccount:${FUNCTION_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/iam.serviceAccountTokenCreator" >/dev/null

# FunctionsがCloud Storageバケットのオブジェクト情報を読み取るための権限
gcloud storage buckets add-iam-policy-binding gs://${AUDIO_UPLOAD_BUCKET} \
  --member="serviceAccount:${FUNCTION_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectAdmin" >/dev/null

echo "--- Eventarcトリガー用サービスアカウントに必要なIAMロールを付与中 ---"
# Eventarcがこのサービスアカウントとしてイベントを中継するために必要
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${TRIGGER_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/eventarc.eventReceiver" >/dev/null

# EventarcトリガーがCloud Runサービスを呼び出すために必要
echo "Eventarcトリガー用サービスアカウントにCloud Run起動者のロールを付与中..."
gcloud run services add-iam-policy-binding ${BACKEND_SERVICE_NAME} \
  --region=${GOOGLE_CLOUD_LOCATION} \
  --member="serviceAccount:${TRIGGER_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/run.invoker" \
  --platform=managed >/dev/null

echo "--- Google管理のサービスエージェントに必要な権限を付与中 ---"
# プロジェクト番号を一度だけ取得して、後続の処理で再利用する
PROJECT_NUMBER=$(gcloud projects describe ${GOOGLE_CLOUD_PROJECT} --format="value(projectNumber)")

# 1. Eventarc Service Agent
EVENTARC_SA="service-${PROJECT_NUMBER}@gcp-sa-eventarc.iam.gserviceaccount.com"
echo "Eventarc Service Agent (${EVENTARC_SA}) にロールを付与..."
# EventarcがPub/Subトピックにイベントを公開するため (pubsub.publisher)
# Cloud Storageバケットの通知設定を管理するため (storage.admin)
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${EVENTARC_SA}" \
    --role="roles/pubsub.publisher" >/dev/null
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${EVENTARC_SA}" \
    --role="roles/storage.admin" >/dev/null

# 2. Cloud Storage Service Agent
GCS_SA="service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"
echo "Cloud Storage Service Agent (${GCS_SA}) にロールを付与..."
# Cloud StorageがPub/Subに通知を発行するため (pubsub.publisher)
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${GCS_SA}" \
    --role="roles/pubsub.publisher" >/dev/null

echo "--- Cloud Build サービスアカウントに必要なIAMロールを付与中 ---"
CLOUDBUILD_ROLES=(
  "roles/logging.logWriter"           # ログ書き込み
  "roles/cloudbuild.builds.editor"    # Cloud Build を使用してビルドを実行
  "roles/run.admin"                   # Cloud Run サービスのデプロイとIAMポリシーの更新
  "roles/eventarc.admin"              # Eventarc トリガーの作成と管理
  "roles/iam.serviceAccountUser"      # Cloud Run/Functions にサービスアカウントを関連付ける
  "roles/datastore.indexAdmin"        # Firestore のインデックスをデプロイするために必要
  "roles/firebaserules.admin"         # Firestore/Storage ルールのデプロイ
  "roles/cloudfunctions.developer"    # Cloud Functions のデプロイ
  "roles/firebasehosting.admin"       # Firebase Hosting のデプロイ
  "roles/artifactregistry.writer"     # Artifact Registryへのイメージ書き込み
  "roles/firebase.viewer"             # Firebaseプロジェクト情報へのアクセス(Hostingデプロイ時に必要)
  "roles/firebasestorage.admin"       # Firebase Storage の管理
  "roles/storage.admin"               # Cloud Storage の管理
  "roles/secretmanager.secretAccessor" # Secret Managerから設定を読み込む
)

echo "Cloud Build サービスアカウント (${CLOUDBUILD_SA_NAME}) にロールを付与中..."
for ROLE in "${CLOUDBUILD_ROLES[@]}"; do
  # 標準出力を/dev/nullにリダイレクトして成功時の長いポリシー出力を抑制し、エラー出力は表示されるようにします
  gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${CLOUDBUILD_SERVICE_ACCOUNT_EMAIL}" \
    --role="${ROLE}" >/dev/null
done

echo "✅ Infrastructure setup complete."