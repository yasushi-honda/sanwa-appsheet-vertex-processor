# AppSheet AI Processor

AppSheetアプリケーションからユーザーが選択した行データに対して、GCP上のCloud Runサービス経由でVertex AI（Gemini）による処理を実行し、結果をGoogleスプレッドシートに書き戻すシステム。

## リポジトリ

- GitHub: https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor

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

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| ランタイム | Python 3.11 |
| Webフレームワーク | Flask |
| コンテナ | Docker |
| AI/ML | Vertex AI (gemini-1.5-flash) |
| データストア | Google Sheets API v4 |
| インフラ | Google Cloud Run |
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

direnvを使用してプロジェクト単位で環境変数を管理します。

```bash
# direnvのインストール（未インストールの場合）
# macOS
brew install direnv

# bashの場合、~/.bashrc に追加
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc

# zshの場合、~/.zshrc に追加
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

# シェルを再起動または設定を再読み込み
source ~/.zshrc  # または source ~/.bashrc
```

```bash
# 環境変数テンプレートをコピー
cp .envrc.example .envrc

# .envrcを編集して値を設定
vim .envrc

# direnvを有効化
direnv allow
```

### ローカル開発環境のセットアップ

```bash
# Python仮想環境の作成
python -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# ローカルでのGCP認証（Application Default Credentials）
gcloud auth application-default login

# アプリケーション実行
python src/main.py
```

## セットアップ手順

### 1. 前提条件

- GCPプロジェクトが作成済みであること
- `gcloud` CLIがインストール・認証済みであること
- Dockerがインストール済みであること

### 2. GCPリソースのセットアップ

```bash
cd deploy
./setup.sh <YOUR_PROJECT_ID>
```

このスクリプトで以下が実行されます：
- 必要なAPIの有効化
- Artifact Registryリポジトリの作成
- サービスアカウントの作成
- IAMロールの付与

### 3. スプレッドシートの共有設定

対象のGoogleスプレッドシートで、以下のサービスアカウントを「編集者」として共有設定に追加してください：

```
ai-processor@<YOUR_PROJECT_ID>.iam.gserviceaccount.com
```

### 4. Dockerイメージのビルドとプッシュ

```bash
# Artifact Registryへの認証
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージのビルド
docker build -t asia-northeast1-docker.pkg.dev/<PROJECT_ID>/appsheet-ai-processor/processor:latest .

# イメージのプッシュ
docker push asia-northeast1-docker.pkg.dev/<PROJECT_ID>/appsheet-ai-processor/processor:latest
```

### 5. Cloud Runへのデプロイ

```bash
gcloud run deploy appsheet-ai-processor \
  --image=asia-northeast1-docker.pkg.dev/<PROJECT_ID>/appsheet-ai-processor/processor:latest \
  --region=asia-northeast1 \
  --service-account=ai-processor@<PROJECT_ID>.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --memory=512Mi \
  --timeout=300 \
  --set-env-vars="PROJECT_ID=<PROJECT_ID>,SPREADSHEET_ID=<SPREADSHEET_ID>,SHEET_NAME=<SHEET_NAME>,PK_COLUMN=<PK_COLUMN>,TARGET_COLUMN=<TARGET_COLUMN>,RESULT_COLUMN=<RESULT_COLUMN>,WEBHOOK_SECRET=<WEBHOOK_SECRET>"
```

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

### POST /process

AppSheet Webhookからのリクエストを受け付け、AI処理を実行する。

#### リクエストヘッダー

| ヘッダー | 必須 | 説明 |
|---|---|---|
| Content-Type | はい | application/json |
| X-AppSheet-Secret | はい | Webhook認証用シークレット |

#### リクエストボディ

AppSheetの `<<_ROW_TO_JSON>>` 形式のJSONデータ。

```json
{
  "RowID": "abc-123",
  "TargetText": "処理対象のテキストデータ",
  "Category": "カテゴリA",
  "Is_Processed": true
}
```

#### レスポンス

**成功時 (200 OK)**

```json
{
  "status": "success",
  "row_id": "abc-123",
  "ai_result": "AIによる処理結果テキスト",
  "processed_at": "2024-12-01T10:00:05Z"
}
```

**エラー時**

| ステータス | 説明 |
|---|---|
| 400 Bad Request | リクエスト形式エラー |
| 403 Forbidden | 認証エラー |
| 500 Internal Server Error | 処理エラー |

### GET /health

ヘルスチェック用エンドポイント。

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## AppSheet Webhook設定

1. AppSheetアプリのAutomationを開く
2. 新しいBotを作成
3. トリガー条件を設定（例: ボタン押下時）
4. アクションで「Call a webhook」を選択
5. 以下を設定：
   - URL: Cloud RunサービスのURL + `/process`
   - HTTP Method: POST
   - HTTP Content-Type: application/json
   - HTTP Headers: `X-AppSheet-Secret: <WEBHOOK_SECRET>`
   - Body: `<<_ROW_TO_JSON>>`

## ファイル構成

```
sanwa-appsheet-vertex-processor/
├── README.md
├── Dockerfile
├── requirements.txt
├── .env.example
├── .envrc.example
├── .gitignore
├── docs/                 # ドキュメント格納用
├── src/
│   ├── main.py           # Flaskエントリーポイント、エンドポイント定義
│   ├── config.py         # 環境変数の読み込みと設定管理
│   ├── auth.py           # X-AppSheet-Secretによるリクエスト検証
│   ├── vertex_ai.py      # Vertex AI (Gemini) 連携処理
│   └── sheets.py         # Google Sheets API 連携処理
└── deploy/
    └── setup.sh          # GCPリソースセットアップスクリプト
```

## ライセンス

Private
