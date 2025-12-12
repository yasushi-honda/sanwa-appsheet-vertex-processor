---
layout: default
title: CI/CD
---

# CI/CD パイプライン

## 概要

GitHub Actionsを使用した自動デプロイパイプラインを構築しています。

## パイプライン構成

<div class="mermaid">
flowchart LR
    subgraph GitHub["GitHub"]
        PUSH[Push to main]
        GA[GitHub Actions]
    end

    subgraph Auth["認証"]
        WIF[Workload Identity<br/>Federation]
        SA[Service Account]
    end

    subgraph GCP["Google Cloud"]
        AR[Artifact Registry]
        CR[Cloud Run]
    end

    PUSH --> GA
    GA -->|OIDC| WIF
    WIF -->|偽装| SA
    GA -->|Build & Push| AR
    GA -->|Deploy| CR
</div>

## ワークフロー

### Deploy to Cloud Run

**トリガー**: `main` ブランチへのプッシュ（docsとmdファイルを除く）

<div class="mermaid">
flowchart TB
    A[Checkout] --> B[Authenticate to GCP]
    B --> C[Setup Cloud SDK]
    C --> D[Configure Docker]
    D --> E[Build Image]
    E --> F[Push to Artifact Registry]
    F --> G[Deploy to Cloud Run]
    G --> H[Show URL]
</div>

#### ステップ詳細

| ステップ | 説明 |
|---|---|
| Checkout | リポジトリをチェックアウト |
| Authenticate | Workload Identity Federationで認証 |
| Setup Cloud SDK | gcloudをセットアップ |
| Configure Docker | Artifact Registry用にDocker認証 |
| Build Image | Dockerイメージをビルド（sha + latest） |
| Push | Artifact Registryにプッシュ |
| Deploy | Cloud Runにデプロイ |
| Show URL | デプロイ先URLを表示 |

### GitHub Pages

**トリガー**: `main` ブランチへのプッシュ（docsの変更時）

docs/配下のMarkdownをJekyllでビルドし、GitHub Pagesにデプロイします。

---

## 認証方式

### Workload Identity Federation

サービスアカウントキーを使用せず、OIDCトークンで認証します。

```yaml
- id: auth
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/330887614596/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider'
    service_account: 'github-actions-deployer@sanwa-appsheet-vertex.iam.gserviceaccount.com'
```

#### 必要なパーミッション

```yaml
permissions:
  contents: read
  id-token: write  # OIDC認証に必須
```

---

## 設定ファイル

### .github/workflows/deploy.yml

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
    paths-ignore:
      - 'docs/**'
      - '*.md'

env:
  PROJECT_ID: sanwa-appsheet-vertex
  REGION: asia-northeast1
  SERVICE_NAME: appsheet-ai-processor

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: '...'
          service_account: '...'

      - uses: google-github-actions/setup-gcloud@v2

      - run: gcloud auth configure-docker ...

      - run: docker build ...

      - run: docker push ...

      - run: gcloud run deploy ...
```

---

## デプロイ設定

### Cloud Run

| 項目 | 値 |
|---|---|
| サービス名 | appsheet-ai-processor |
| リージョン | asia-northeast1 |
| サービスアカウント | ai-processor@ |
| 認証 | 未認証の呼び出しを許可 |
| メモリ | 512Mi |
| タイムアウト | 300秒 |
| 最小インスタンス | 0 |
| 最大インスタンス | 10 |

### Artifact Registry

| 項目 | 値 |
|---|---|
| リポジトリ | appsheet-ai-processor |
| リージョン | asia-northeast1 |
| イメージ名 | processor |
| タグ | `{commit-sha}`, `latest` |
| クリーンアップ | 最新2バージョン保持 |

---

## 手動デプロイ

GitHub Actionsを使わず手動でデプロイする場合：

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

---

## トラブルシューティング

### 認証エラー

```
Error: Unable to retrieve access token
```

確認事項：
- `id-token: write` パーミッションが設定されているか
- Workload Identity Providerの設定が正しいか
- サービスアカウントにWorkload Identity Userロールが付与されているか

### デプロイエラー

```
Error: Permission denied
```

確認事項：
- `github-actions-deployer` に `roles/run.admin` が付与されているか
- `roles/iam.serviceAccountUser` で ai-processor を使用できるか

### イメージプッシュエラー

```
Error: denied: Permission denied
```

確認事項：
- `github-actions-deployer` に `roles/artifactregistry.writer` が付与されているか

<script>
  mermaid.initialize({ startOnLoad: true, theme: 'default' });
</script>
