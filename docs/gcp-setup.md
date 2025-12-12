# GCPセットアップ手順書

## 概要

このドキュメントでは、AppSheet AI Processorを動作させるためのGCPリソースのセットアップ手順を記載します。

## プロジェクト情報

| 項目 | 値 |
|---|---|
| プロジェクトID | sanwa-appsheet-vertex |
| プロジェクト名 | Sanwa AppSheet Vertex |
| プロジェクト番号 | 330887614596 |
| リージョン | asia-northeast1 |
| 作成日 | 2025-12-12 |
| オーナーアカウント | sanwaminamihonda@gmail.com |

## セットアップ完了状況

| リソース | ステータス | 備考 |
|---|---|---|
| プロジェクト作成 | ✅ 完了 | 2025-12-12 |
| 課金アカウントリンク | ✅ 完了 | 011092-7C90AB-F84603 |
| Cloud Run API | ✅ 有効化済み | run.googleapis.com |
| Vertex AI API | ✅ 有効化済み | aiplatform.googleapis.com |
| Sheets API | ✅ 有効化済み | sheets.googleapis.com |
| Artifact Registry API | ✅ 有効化済み | artifactregistry.googleapis.com |
| IAM Credentials API | ✅ 有効化済み | iamcredentials.googleapis.com |
| サービスアカウント (AI) | ✅ 作成済み | ai-processor@ |
| サービスアカウント (CI/CD) | ✅ 作成済み | github-actions-deployer@ |
| IAMロール付与 | ✅ 完了 | 下記参照 |
| Artifact Registry | ✅ 作成済み | appsheet-ai-processor |
| クリーンアップポリシー | ✅ 設定済み | 最新2バージョン保持 |
| Workload Identity Pool | ✅ 作成済み | github-actions-pool |
| Workload Identity Provider | ✅ 作成済み | github-actions-provider |

## 1. 認証

### 1.1 gcloud認証

```bash
gcloud auth login --account=sanwaminamihonda@gmail.com
```

### 1.2 プロジェクトの設定

```bash
gcloud config set project sanwa-appsheet-vertex
```

### 1.3 Application Default Credentials（ローカル開発用）

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project sanwa-appsheet-vertex
```

## 2. 必要なAPIの有効化

以下のAPIを有効化する必要があります：

| API | 用途 | ステータス |
|---|---|---|
| Cloud Run API | アプリケーションのホスティング | ✅ 有効 |
| Vertex AI API | Geminiモデルの利用 | ✅ 有効 |
| Google Sheets API | スプレッドシートの読み書き | ✅ 有効 |
| Artifact Registry API | Dockerイメージの保存 | ✅ 有効 |
| IAM Credentials API | Workload Identity Federation | ✅ 有効 |

### 実行コマンド

```bash
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  sheets.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com
```

## 3. サービスアカウントの作成

### 3.1 AI Processor用サービスアカウント

Cloud Run上でアプリケーションが使用するサービスアカウント。

```bash
gcloud iam service-accounts create ai-processor \
  --display-name="AppSheet AI Processor Service Account" \
  --description="Cloud Run上のAppSheet AI Processorが使用するサービスアカウント"

gcloud projects add-iam-policy-binding sanwa-appsheet-vertex \
  --member="serviceAccount:ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

| 項目 | 値 |
|---|---|
| 名前 | ai-processor |
| 表示名 | AppSheet AI Processor Service Account |
| メールアドレス | ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com |
| 付与ロール | roles/aiplatform.user |
| ステータス | ✅ 有効 |

### 3.2 GitHub Actions用サービスアカウント

CI/CDパイプラインが使用するサービスアカウント。

```bash
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer" \
  --description="Service account for GitHub Actions CI/CD"

# Artifact Registry書き込み権限
gcloud projects add-iam-policy-binding sanwa-appsheet-vertex \
  --member="serviceAccount:github-actions-deployer@sanwa-appsheet-vertex.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Cloud Run管理権限
gcloud projects add-iam-policy-binding sanwa-appsheet-vertex \
  --member="serviceAccount:github-actions-deployer@sanwa-appsheet-vertex.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# ai-processorサービスアカウントの使用権限
gcloud iam service-accounts add-iam-policy-binding \
  ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com \
  --member="serviceAccount:github-actions-deployer@sanwa-appsheet-vertex.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

| 項目 | 値 |
|---|---|
| 名前 | github-actions-deployer |
| 表示名 | GitHub Actions Deployer |
| メールアドレス | github-actions-deployer@sanwa-appsheet-vertex.iam.gserviceaccount.com |
| 付与ロール | roles/artifactregistry.writer, roles/run.admin, roles/iam.serviceAccountUser |
| ステータス | ✅ 有効 |

## 4. Artifact Registryリポジトリの作成

```bash
gcloud artifacts repositories create appsheet-ai-processor \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="AppSheet AI Processor Docker images"
```

### リポジトリ情報

| 項目 | 値 |
|---|---|
| リポジトリ名 | appsheet-ai-processor |
| 形式 | Docker |
| リージョン | asia-northeast1 |
| フルパス | asia-northeast1-docker.pkg.dev/sanwa-appsheet-vertex/appsheet-ai-processor |
| 作成日時 | 2025-12-12T17:44:33 |
| ステータス | ✅ 作成済み |

### 4.1 クリーンアップポリシー

古いDockerイメージを自動削除し、ストレージコストを抑制。

```bash
# ポリシーファイル作成
cat << 'EOF' > cleanup-policy.json
[
  {
    "name": "keep-minimum-versions",
    "action": {"type": "Keep"},
    "mostRecentVersions": {
      "keepCount": 2
    }
  }
]
EOF

# ポリシー適用
gcloud artifacts repositories set-cleanup-policies appsheet-ai-processor \
  --project=sanwa-appsheet-vertex \
  --location=asia-northeast1 \
  --policy=cleanup-policy.json
```

| 項目 | 値 |
|---|---|
| ポリシー名 | keep-minimum-versions |
| 保持バージョン数 | 2 |
| ステータス | ✅ 設定済み |

## 5. Workload Identity Federation（GitHub Actions用）

サービスアカウントキーを使用せず、GitHub ActionsからGCPリソースにアクセスするための設定。

### 5.1 Workload Identity Poolの作成

```bash
gcloud iam workload-identity-pools create github-actions-pool \
  --project=sanwa-appsheet-vertex \
  --location=global \
  --display-name="GitHub Actions Pool" \
  --description="Workload Identity Pool for GitHub Actions"
```

### 5.2 Workload Identity Providerの作成

```bash
gcloud iam workload-identity-pools providers create-oidc github-actions-provider \
  --project=sanwa-appsheet-vertex \
  --location=global \
  --workload-identity-pool=github-actions-pool \
  --display-name="GitHub Actions Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == 'yasushi-honda'"
```

### 5.3 サービスアカウントへの偽装許可

```bash
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-deployer@sanwa-appsheet-vertex.iam.gserviceaccount.com \
  --project=sanwa-appsheet-vertex \
  --member="principalSet://iam.googleapis.com/projects/330887614596/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/yasushi-honda/sanwa-appsheet-vertex-processor" \
  --role="roles/iam.workloadIdentityUser"
```

### 5.4 Workload Identity Federation情報

| 項目 | 値 |
|---|---|
| Pool名 | github-actions-pool |
| Provider名 | github-actions-provider |
| Provider フルネーム | projects/330887614596/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider |
| 許可リポジトリ | yasushi-honda/sanwa-appsheet-vertex-processor |
| ステータス | ✅ 設定済み |

### 5.5 GitHub Actionsでの使用方法

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # 必須：OIDC認証に必要

    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/330887614596/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider'
          service_account: 'github-actions-deployer@sanwa-appsheet-vertex.iam.gserviceaccount.com'

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker
        run: gcloud auth configure-docker asia-northeast1-docker.pkg.dev

      - name: Build and Push
        run: |
          docker build -t asia-northeast1-docker.pkg.dev/sanwa-appsheet-vertex/appsheet-ai-processor/processor:${{ github.sha }} .
          docker push asia-northeast1-docker.pkg.dev/sanwa-appsheet-vertex/appsheet-ai-processor/processor:${{ github.sha }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy appsheet-ai-processor \
            --image=asia-northeast1-docker.pkg.dev/sanwa-appsheet-vertex/appsheet-ai-processor/processor:${{ github.sha }} \
            --region=asia-northeast1 \
            --service-account=ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com
```

## 6. 課金の設定

### 課金アカウント情報

| 項目 | 値 |
|---|---|
| アカウントID | 011092-7C90AB-F84603 |
| アカウント名 | 請求先アカウント |
| リンク状況 | ✅ リンク済み |

### CLIコマンド

```bash
# 課金アカウント一覧
gcloud billing accounts list

# プロジェクトへのリンク（実行済み）
gcloud billing projects link sanwa-appsheet-vertex \
  --billing-account=011092-7C90AB-F84603
```

## 7. スプレッドシートの共有設定

対象のGoogleスプレッドシートで、以下のサービスアカウントを「編集者」として追加：

```
ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com
```

### 手順

1. 対象のスプレッドシートを開く
2. 右上の「共有」ボタンをクリック
3. 上記のメールアドレスを入力
4. 「編集者」権限を選択
5. 「送信」をクリック

**ステータス**: ⏳ 未実施（スプレッドシート作成後に実施）

## 8. 自動セットアップスクリプト

上記の手順を自動化するスクリプトが用意されています：

```bash
cd deploy
./setup.sh sanwa-appsheet-vertex
```

**実行結果**: ✅ 2025-12-12 完了

## 9. 確認コマンド

### プロジェクト情報

```bash
gcloud projects describe sanwa-appsheet-vertex
```

### 有効なAPI一覧

```bash
gcloud services list --enabled --project=sanwa-appsheet-vertex
```

### サービスアカウント一覧

```bash
gcloud iam service-accounts list --project=sanwa-appsheet-vertex
```

### IAMポリシー確認

```bash
gcloud projects get-iam-policy sanwa-appsheet-vertex \
  --flatten="bindings[].members" \
  --format="table(bindings.role,bindings.members)"
```

### Artifact Registryリポジトリ確認

```bash
gcloud artifacts repositories list --project=sanwa-appsheet-vertex --location=asia-northeast1
```

### クリーンアップポリシー確認

```bash
gcloud artifacts repositories describe appsheet-ai-processor \
  --project=sanwa-appsheet-vertex \
  --location=asia-northeast1
```

### Workload Identity Pool確認

```bash
gcloud iam workload-identity-pools describe github-actions-pool \
  --project=sanwa-appsheet-vertex \
  --location=global
```

### Workload Identity Provider確認

```bash
gcloud iam workload-identity-pools providers describe github-actions-provider \
  --project=sanwa-appsheet-vertex \
  --location=global \
  --workload-identity-pool=github-actions-pool
```

## 10. 次のステップ

1. **スプレッドシートの準備**
   - 対象スプレッドシートを作成または選定
   - サービスアカウントを編集者として追加

2. **環境変数の設定**
   - `.envrc` にSPREADSHEET_ID等を設定
   - WEBHOOK_SECRETを生成して設定

3. **GitHub Actions CI/CDの設定**
   - `.github/workflows/deploy.yml` を作成
   - 上記のWorkload Identity設定を使用

4. **Dockerイメージのビルド・デプロイ**
   ```bash
   # Artifact Registryへの認証
   gcloud auth configure-docker asia-northeast1-docker.pkg.dev

   # イメージのビルド
   docker build -t asia-northeast1-docker.pkg.dev/sanwa-appsheet-vertex/appsheet-ai-processor/processor:latest .

   # イメージのプッシュ
   docker push asia-northeast1-docker.pkg.dev/sanwa-appsheet-vertex/appsheet-ai-processor/processor:latest

   # Cloud Runへのデプロイ
   gcloud run deploy appsheet-ai-processor \
     --image=asia-northeast1-docker.pkg.dev/sanwa-appsheet-vertex/appsheet-ai-processor/processor:latest \
     --region=asia-northeast1 \
     --service-account=ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com \
     --allow-unauthenticated \
     --memory=512Mi \
     --timeout=300
   ```

## 11. トラブルシューティング

### API未有効化エラー

```
Error: API [xxx.googleapis.com] not enabled on project [sanwa-appsheet-vertex]
```

→ 該当APIを有効化：`gcloud services enable xxx.googleapis.com`

### 課金未設定エラー

```
Error: This project has no billing account
```

→ `gcloud billing projects link` コマンドで課金アカウントをリンク

### 権限不足エラー

```
Error: Permission denied
```

→ サービスアカウントのIAMロールを確認

### サービスアカウント作成直後のIAM付与エラー

```
ERROR: Service account xxx does not exist.
```

→ サービスアカウント作成後、数秒待ってから再実行

### GitHub ActionsでのWorkload Identity認証エラー

```
Error: Unable to retrieve access token
```

→ 以下を確認：
- `id-token: write` パーミッションが設定されているか
- Provider名とService Account名が正しいか
- リポジトリ名が attribute-condition に一致しているか
