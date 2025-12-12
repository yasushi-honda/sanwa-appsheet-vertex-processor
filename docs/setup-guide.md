---
layout: default
title: Setup Guide
---

# セットアップガイド

## 前提条件

- GCPプロジェクトが作成済みであること
- `gcloud` CLIがインストール・認証済みであること
- Dockerがインストール済みであること
- GitHub CLIがインストール済みであること

## クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor.git
cd sanwa-appsheet-vertex-processor
```

### 2. 環境変数の設定（direnv使用）

```bash
# direnvのインストール（未インストールの場合）
brew install direnv

# シェル設定に追加
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# 環境変数テンプレートをコピー
cp .envrc.example .envrc

# 値を設定
vim .envrc

# direnvを有効化
direnv allow
```

### 3. GCPリソースのセットアップ

```bash
# gcloud認証
gcloud auth login

# セットアップスクリプト実行
./deploy/setup.sh sanwa-appsheet-vertex
```

### 4. スプレッドシートの共有設定

対象スプレッドシートで以下のサービスアカウントを「編集者」として追加：

```
ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com
```

### 5. デプロイ

mainブランチにプッシュすると自動デプロイされます。

```bash
git add .
git commit -m "Deploy"
git push origin main
```

---

## 詳細セットアップ

### GCPリソース一覧

セットアップスクリプトで作成されるリソース：

| リソース | 名前 |
|---|---|
| サービスアカウント | ai-processor |
| サービスアカウント | github-actions-deployer |
| Artifact Registry | appsheet-ai-processor |
| Workload Identity Pool | github-actions-pool |
| Workload Identity Provider | github-actions-provider |

### 有効化されるAPI

- Cloud Run API
- Vertex AI API
- Google Sheets API
- Artifact Registry API
- IAM Credentials API

---

## ローカル開発

### 環境構築

```bash
# Python仮想環境
python -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# Application Default Credentials
gcloud auth application-default login
gcloud auth application-default set-quota-project sanwa-appsheet-vertex
```

### 環境変数設定

`.envrc` に以下を設定：

```bash
export PROJECT_ID="sanwa-appsheet-vertex"
export SPREADSHEET_ID="your-spreadsheet-id"
export SHEET_NAME="Sheet1"
export PK_COLUMN="RowID"
export TARGET_COLUMN="TargetText"
export RESULT_COLUMN="AIResult"
export WEBHOOK_SECRET="your-secret-32-chars-minimum"
```

### 実行

```bash
python src/main.py
```

### テストリクエスト

```bash
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -H "X-AppSheet-Secret: your-secret-32-chars-minimum" \
  -d '{"RowID": "test-1", "TargetText": "テストテキスト"}'
```

---

## AppSheet設定

### Webhook設定

1. AppSheetアプリの **Automation** を開く
2. 新しい **Bot** を作成
3. **Event** でトリガー条件を設定（例: ボタン押下時）
4. **Process** で **Call a webhook** を追加
5. 以下を設定：

| 項目 | 値 |
|---|---|
| URL | `https://appsheet-ai-processor-xxx.run.app/process` |
| HTTP Method | POST |
| HTTP Content-Type | application/json |
| Body | `<<_ROW_TO_JSON>>` |

6. **HTTP Headers** に追加：

```
X-AppSheet-Secret: your-webhook-secret
```

### ボタン設定

1. **UX** → **Views** でフォームビューを開く
2. **Actions** でAI処理ボタンを追加
3. ボタンのアクションでWebhookを呼び出す Bot をトリガー

---

## トラブルシューティング

### ローカルでの認証エラー

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project sanwa-appsheet-vertex
```

### Cloud Runデプロイエラー

GitHub Actionsのログを確認：

1. リポジトリの **Actions** タブを開く
2. 失敗したワークフローを選択
3. エラーログを確認

### Webhook認証エラー

`X-AppSheet-Secret` ヘッダーが正しく設定されているか確認。
WEBHOOK_SECRET環境変数と一致している必要があります。

### スプレッドシート書き込みエラー

サービスアカウントがスプレッドシートに「編集者」として共有されているか確認：

```
ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com
```

<script>
  mermaid.initialize({ startOnLoad: true, theme: 'default' });
</script>
