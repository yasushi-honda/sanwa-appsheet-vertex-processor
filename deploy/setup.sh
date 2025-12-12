#!/bin/bash
#
# GCPリソースセットアップスクリプト
# AppSheet AI Processor用のGCPリソースを作成します
#
# 使用方法:
#   ./setup.sh <PROJECT_ID>
#
# 例:
#   ./setup.sh my-gcp-project
#

set -e

# 引数チェック
if [ -z "$1" ]; then
    echo "エラー: PROJECT_IDを指定してください"
    echo "使用方法: ./setup.sh <PROJECT_ID>"
    exit 1
fi

PROJECT_ID="$1"
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="ai-processor"
REPOSITORY_NAME="appsheet-ai-processor"

echo "========================================"
echo "AppSheet AI Processor GCPセットアップ"
echo "========================================"
echo "PROJECT_ID: ${PROJECT_ID}"
echo "REGION: ${REGION}"
echo ""

# プロジェクトの設定
echo "[1/5] プロジェクトを設定中..."
gcloud config set project "${PROJECT_ID}"

# APIの有効化
echo "[2/5] 必要なAPIを有効化中..."
gcloud services enable \
    run.googleapis.com \
    aiplatform.googleapis.com \
    sheets.googleapis.com \
    artifactregistry.googleapis.com

echo "  - Cloud Run API: 有効"
echo "  - Vertex AI API: 有効"
echo "  - Google Sheets API: 有効"
echo "  - Artifact Registry API: 有効"

# Artifact Registryリポジトリの作成
echo "[3/5] Artifact Registryリポジトリを作成中..."
if gcloud artifacts repositories describe "${REPOSITORY_NAME}" \
    --location="${REGION}" &>/dev/null; then
    echo "  リポジトリ '${REPOSITORY_NAME}' は既に存在します"
else
    gcloud artifacts repositories create "${REPOSITORY_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="AppSheet AI Processor Docker images"
    echo "  リポジトリ '${REPOSITORY_NAME}' を作成しました"
fi

# サービスアカウントの作成
echo "[4/5] サービスアカウントを作成中..."
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "${SERVICE_ACCOUNT_EMAIL}" &>/dev/null; then
    echo "  サービスアカウント '${SERVICE_ACCOUNT_NAME}' は既に存在します"
else
    gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
        --display-name="AppSheet AI Processor Service Account" \
        --description="Cloud Run上のAppSheet AI Processorが使用するサービスアカウント"
    echo "  サービスアカウント '${SERVICE_ACCOUNT_NAME}' を作成しました"
fi

# IAMロールの付与
echo "[5/5] IAMロールを付与中..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/aiplatform.user" \
    --condition=None \
    --quiet

echo "  - roles/aiplatform.user を付与しました"

echo ""
echo "========================================"
echo "セットアップ完了"
echo "========================================"
echo ""
echo "次のステップ:"
echo ""
echo "1. Googleスプレッドシートの共有設定で、以下のサービスアカウントを"
echo "   「編集者」として追加してください:"
echo "   ${SERVICE_ACCOUNT_EMAIL}"
echo ""
echo "2. Dockerイメージをビルドしてプッシュしてください:"
echo "   docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/processor:latest ."
echo "   docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/processor:latest"
echo ""
echo "3. Cloud Runにデプロイしてください:"
echo "   gcloud run deploy appsheet-ai-processor \\"
echo "     --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/processor:latest \\"
echo "     --region=${REGION} \\"
echo "     --service-account=${SERVICE_ACCOUNT_EMAIL} \\"
echo "     --allow-unauthenticated \\"
echo "     --memory=512Mi \\"
echo "     --timeout=300 \\"
echo "     --set-env-vars=\"PROJECT_ID=${PROJECT_ID},SPREADSHEET_ID=<YOUR_SPREADSHEET_ID>,SHEET_NAME=<YOUR_SHEET_NAME>,PK_COLUMN=<YOUR_PK_COLUMN>,TARGET_COLUMN=<YOUR_TARGET_COLUMN>,RESULT_COLUMN=<YOUR_RESULT_COLUMN>,WEBHOOK_SECRET=<YOUR_WEBHOOK_SECRET>\""
echo ""
