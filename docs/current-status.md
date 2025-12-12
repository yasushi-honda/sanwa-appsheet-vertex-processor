---
layout: default
title: Current Status
---

# プロジェクト現在状況

最終更新: 2025-12-12

## 実装状況

| 機能 | 状態 | 備考 |
|---|---|---|
| プロジェクト構造 | ✅ 完了 | Dockerfile, requirements.txt |
| Flask エンドポイント | ✅ 完了 | /health, /process |
| 環境変数管理 (config.py) | ✅ 完了 | dataclass使用 |
| Webhook認証 (auth.py) | ✅ 完了 | X-AppSheet-Secret検証 |
| Vertex AI連携 (vertex_ai.py) | ✅ 完了 | gemini-1.5-flash |
| Sheets API連携 (sheets.py) | ✅ 完了 | バッチ更新対応 |
| GCPリソース作成 | ✅ 完了 | setup.sh実行済み |
| CI/CD (GitHub Actions) | ✅ 完了 | deploy.yml, pages.yml |
| GitHub Pages | ✅ 完了 | Jekyll + Mermaid |
| ローカル動作確認 | ⏳ 未確認 | ADC認証必要 |
| Cloud Run本番デプロイ | ⏳ 未実施 | 環境変数設定待ち |
| スプレッドシート連携テスト | ⏳ 未実施 | シート作成待ち |
| ユニットテスト | ❌ 未実装 | - |

## GCPリソース状況

| リソース | ステータス | 識別子 |
|---|---|---|
| プロジェクト | ✅ 作成済み | sanwa-appsheet-vertex |
| 課金アカウント | ✅ リンク済み | 011092-7C90AB-F84603 |
| Artifact Registry | ✅ 作成済み | appsheet-ai-processor |
| サービスアカウント (AI) | ✅ 作成済み | ai-processor@ |
| サービスアカウント (CI/CD) | ✅ 作成済み | github-actions-deployer@ |
| Workload Identity Pool | ✅ 作成済み | github-actions-pool |
| Workload Identity Provider | ✅ 作成済み | github-actions-provider |
| Cloud Run サービス | ⏳ 未デプロイ | appsheet-ai-processor |

## 環境変数設定状況

| 変数 | ローカル(.envrc) | Cloud Run | 備考 |
|---|---|---|---|
| GCP_PROJECT_ID | ✅ 設定済み | - | sanwa-appsheet-vertex |
| SPREADSHEET_ID | ❌ 未設定 | ❌ 未設定 | シート作成後に設定 |
| SHEET_NAME | ❌ 未設定 | ❌ 未設定 | シート作成後に設定 |
| PK_COLUMN | ❌ 未設定 | ❌ 未設定 | シート作成後に設定 |
| TARGET_COLUMN | ❌ 未設定 | ❌ 未設定 | シート作成後に設定 |
| RESULT_COLUMN | ❌ 未設定 | ❌ 未設定 | シート作成後に設定 |
| WEBHOOK_SECRET | ❌ 未設定 | ❌ 未設定 | 生成して設定 |

## 次にやるべきこと（優先度順）

### 1. スプレッドシートの準備（必須）

```bash
# 1. Googleスプレッドシートを作成
# 2. 以下のカラム構成を設定:
#    - RowID: 主キー（例: UUID）
#    - TargetText: AI処理対象テキスト
#    - AIResult: 処理結果（空欄で開始）
#    - ProcessedAt: 処理日時（空欄で開始）

# 3. サービスアカウントを編集者として共有
#    ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com
```

### 2. 環境変数の設定（必須）

```bash
# WEBHOOK_SECRET生成
openssl rand -base64 32

# .envrc に設定
export SPREADSHEET_ID="your-spreadsheet-id"
export SHEET_NAME="Sheet1"
export PK_COLUMN="RowID"
export TARGET_COLUMN="TargetText"
export RESULT_COLUMN="AIResult"
export WEBHOOK_SECRET="生成したシークレット"

direnv allow
```

### 3. ローカル動作確認

```bash
# GCP認証
gcloud auth application-default login
gcloud auth application-default set-quota-project sanwa-appsheet-vertex

# サーバー起動
python src/main.py

# 別ターミナルでテスト
curl http://localhost:8080/health

curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -H "X-AppSheet-Secret: your-webhook-secret" \
  -d '{"RowID": "test-1", "TargetText": "テストテキスト"}'
```

### 4. Cloud Runデプロイ

```bash
# 手動デプロイ（環境変数付き）
gcloud run deploy appsheet-ai-processor \
  --image=asia-northeast1-docker.pkg.dev/sanwa-appsheet-vertex/appsheet-ai-processor/processor:latest \
  --region=asia-northeast1 \
  --service-account=ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --memory=512Mi \
  --timeout=300 \
  --set-env-vars="PROJECT_ID=sanwa-appsheet-vertex,SPREADSHEET_ID=xxx,SHEET_NAME=xxx,PK_COLUMN=RowID,TARGET_COLUMN=TargetText,RESULT_COLUMN=AIResult,WEBHOOK_SECRET=xxx"
```

または、GitHub Actionsワークフローを修正して環境変数を追加。

### 5. AppSheet Webhook設定

Cloud Runデプロイ後、AppSheetアプリでWebhook設定を行う。

## 既知の問題

1. **Cloud Runデプロイが失敗** - 環境変数未設定のため（想定通り）
2. **テストコードなし** - ユニットテスト未実装

## ファイル構成（実装済み）

```
sanwa-appsheet-vertex-processor/
├── .github/workflows/
│   ├── deploy.yml        ✅ Cloud Run自動デプロイ
│   └── pages.yml         ✅ GitHub Pages自動デプロイ
├── docs/                  ✅ ドキュメント（GitHub Pages）
├── src/
│   ├── main.py           ✅ Flaskエンドポイント
│   ├── config.py         ✅ 環境変数管理
│   ├── auth.py           ✅ Webhook認証
│   ├── vertex_ai.py      ✅ Vertex AI連携
│   └── sheets.py         ✅ Sheets API連携
├── deploy/
│   └── setup.sh          ✅ GCPセットアップスクリプト
├── Dockerfile            ✅ コンテナ定義
├── requirements.txt      ✅ Python依存関係
├── .env.example          ✅ 環境変数テンプレート
├── .envrc.example        ✅ direnv用テンプレート
├── .envrc                ✅ ローカル環境変数（git除外）
└── .gitignore            ✅ Git除外設定
```

<script>
  mermaid.initialize({ startOnLoad: true, theme: 'default' });
</script>
