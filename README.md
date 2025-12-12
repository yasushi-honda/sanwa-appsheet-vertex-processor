# AppSheet AI Processor

AppSheetアプリケーションからユーザーが選択した行データに対して、GCP上のCloud Runサービス経由でVertex AI（Gemini）による処理を実行し、結果をGoogleスプレッドシートに書き戻すシステム。

## リンク

| リソース | URL |
|---|---|
| GitHub | https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor |
| ドキュメント | https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/ |

## CI/CD

[![Deploy to Cloud Run](https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor/actions/workflows/deploy.yml/badge.svg)](https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor/actions/workflows/deploy.yml)
[![Deploy GitHub Pages](https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor/actions/workflows/pages.yml/badge.svg)](https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor/actions/workflows/pages.yml)

| パイプライン | トリガー | 内容 |
|---|---|---|
| Deploy to Cloud Run | mainへのpush（docs以外） | Dockerビルド → Artifact Registry → Cloud Run |
| Deploy GitHub Pages | mainへのpush（docs変更時） | Jekyll ビルド → GitHub Pages |

## システム構成

```
[AppSheet]
    ↓ Webhook (POST JSON)
[Cloud Run Service]
    ├─→ [Vertex AI API] Gemini による処理
    └─→ [Google Sheets API] 結果書き戻し
    ↓
[Google スプレッドシート] (データソース)
```

詳細は[アーキテクチャドキュメント](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/architecture)を参照。

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| ランタイム | Python 3.11 |
| Webフレームワーク | Flask |
| コンテナ | Docker |
| AI/ML | Vertex AI (gemini-1.5-flash) |
| データストア | Google Sheets API v4 |
| インフラ | Google Cloud Run |
| CI/CD | GitHub Actions |
| ドキュメント | GitHub Pages (Jekyll) |
| リージョン | asia-northeast1 |

## 認証方式

**Workload Identity のみで完結する設計**

- サービスアカウントキーの発行: 禁止
- Secret Manager: 使用しない
- OAuth認証情報ファイル: 使用しない
- `google.auth.default()` による自動認証のみを使用

## クイックスタート

### リポジトリのクローン

```bash
git clone https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor.git
cd sanwa-appsheet-vertex-processor
```

### 環境変数の設定（direnv使用）

```bash
# direnvのインストール（未インストールの場合）
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# 環境変数テンプレートをコピー
cp .envrc.example .envrc
vim .envrc
direnv allow
```

### GCPリソースのセットアップ

```bash
./deploy/setup.sh sanwa-appsheet-vertex
```

### デプロイ

mainブランチにプッシュすると自動デプロイされます。

```bash
git add .
git commit -m "Deploy"
git push origin main
```

詳細は[セットアップガイド](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/setup-guide)を参照。

## ドキュメント

GitHub Pagesでドキュメントを公開しています。

- [ホーム](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/) - 概要
- [アーキテクチャ](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/architecture) - システム構成図
- [API仕様](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/api-spec) - エンドポイント仕様
- [セットアップガイド](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/setup-guide) - 環境構築手順
- [CI/CD](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/ci-cd) - 自動デプロイ
- [GCPセットアップ](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/gcp-setup) - GCPリソース設定

## 環境変数

### 必須

| 変数名 | 説明 |
|---|---|
| PROJECT_ID | GCPプロジェクトID |
| SPREADSHEET_ID | 対象スプレッドシートのID |
| SHEET_NAME | 対象シート名 |
| PK_COLUMN | 主キーカラム名 |
| TARGET_COLUMN | 処理対象データのカラム名 |
| RESULT_COLUMN | AI処理結果を書き込むカラム名 |
| WEBHOOK_SECRET | Webhook認証用シークレット（32文字以上推奨） |

### オプション

| 変数名 | デフォルト値 | 説明 |
|---|---|---|
| VERTEX_AI_LOCATION | asia-northeast1 | Vertex AIリージョン |
| VERTEX_AI_MODEL | gemini-1.5-flash | 使用するGeminiモデル |
| LOG_LEVEL | INFO | ログレベル |

## API仕様

詳細は[API仕様ドキュメント](https://yasushi-honda.github.io/sanwa-appsheet-vertex-processor/api-spec)を参照。

### POST /process

AppSheet Webhookからのリクエストを受け付け、AI処理を実行。

```bash
curl -X POST https://appsheet-ai-processor-xxx.run.app/process \
  -H "Content-Type: application/json" \
  -H "X-AppSheet-Secret: your-secret" \
  -d '{"RowID": "abc-123", "TargetText": "処理対象テキスト"}'
```

### GET /health

ヘルスチェック用エンドポイント。

```json
{"status": "healthy", "version": "1.0.0"}
```

## ファイル構成

```
sanwa-appsheet-vertex-processor/
├── .github/
│   └── workflows/
│       ├── deploy.yml        # Cloud Runデプロイ
│       └── pages.yml         # GitHub Pagesデプロイ
├── docs/                     # ドキュメント（GitHub Pages）
│   ├── _config.yml
│   ├── index.md
│   ├── architecture.md
│   ├── api-spec.md
│   ├── setup-guide.md
│   ├── ci-cd.md
│   └── gcp-setup.md
├── src/
│   ├── main.py               # Flaskエントリーポイント
│   ├── config.py             # 環境変数管理
│   ├── auth.py               # Webhook認証
│   ├── vertex_ai.py          # Vertex AI連携
│   └── sheets.py             # Sheets API連携
├── deploy/
│   └── setup.sh              # GCPセットアップスクリプト
├── Dockerfile
├── requirements.txt
├── .env.example
├── .envrc.example
└── .gitignore
```

## ライセンス

Private
