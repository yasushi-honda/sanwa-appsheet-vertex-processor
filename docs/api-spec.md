---
layout: default
title: API Spec
---

# API仕様

## 概要

AppSheet AI Processorは2つのエンドポイントを提供します。

## 処理フロー

<div class="mermaid">
sequenceDiagram
    participant AS as AppSheet
    participant CR as Cloud Run
    participant VA as Vertex AI
    participant GS as Google Sheets

    AS->>CR: POST /process
    Note over CR: X-AppSheet-Secret検証

    alt 認証失敗
        CR-->>AS: 403 Forbidden
    end

    CR->>CR: JSONパース

    alt パースエラー
        CR-->>AS: 400 Bad Request
    end

    CR->>VA: Gemini処理リクエスト

    alt AI処理エラー
        CR-->>AS: 500 Internal Server Error
    end

    VA-->>CR: 処理結果

    CR->>GS: 結果書き込み

    alt 書き込みエラー
        CR-->>AS: 500 Internal Server Error
    end

    GS-->>CR: 完了

    CR-->>AS: 200 OK + 結果JSON
</div>

---

## POST /process

AppSheet Webhookからのリクエストを受け付け、AI処理を実行します。

### リクエスト

#### ヘッダー

| ヘッダー | 必須 | 説明 |
|---|---|---|
| Content-Type | はい | `application/json` |
| X-AppSheet-Secret | はい | Webhook認証用シークレット |

#### ボディ

AppSheetの `<<_ROW_TO_JSON>>` 形式のJSONデータ。

```json
{
  "RowID": "abc-123",
  "TargetText": "処理対象のテキストデータ",
  "Category": "カテゴリA",
  "Status": "未処理"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| {PK_COLUMN} | string | 主キー（環境変数で指定） |
| {TARGET_COLUMN} | string | AI処理対象テキスト（環境変数で指定） |
| その他 | any | AppSheetの行データ |

### レスポンス

#### 成功時 (200 OK)

```json
{
  "status": "success",
  "row_id": "abc-123",
  "ai_result": "AIによる処理結果テキスト...",
  "processed_at": "2025-12-12T10:00:05Z"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| status | string | `"success"` |
| row_id | string | 処理した行の主キー |
| ai_result | string | Geminiによる処理結果 |
| processed_at | string | 処理日時（ISO 8601形式） |

#### エラー時

| ステータス | 説明 | レスポンス例 |
|---|---|---|
| 400 Bad Request | リクエスト形式エラー | `{"error": "必須フィールドがありません: RowID"}` |
| 403 Forbidden | 認証エラー | `{"error": "認証に失敗しました"}` |
| 500 Internal Server Error | サーバーエラー | `{"error": "AI処理中にエラーが発生しました"}` |

### cURLサンプル

```bash
curl -X POST https://appsheet-ai-processor-xxx.run.app/process \
  -H "Content-Type: application/json" \
  -H "X-AppSheet-Secret: your-webhook-secret" \
  -d '{
    "RowID": "abc-123",
    "TargetText": "処理対象のテキスト"
  }'
```

---

## GET /health

ヘルスチェック用エンドポイント。Cloud Runのヘルスチェックやモニタリングに使用します。

### リクエスト

認証不要。

### レスポンス

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| status | string | `"healthy"` |
| version | string | アプリケーションバージョン |

### cURLサンプル

```bash
curl https://appsheet-ai-processor-xxx.run.app/health
```

---

## 環境変数

APIの動作に必要な環境変数です。

### 必須

| 変数名 | 説明 | 例 |
|---|---|---|
| PROJECT_ID | GCPプロジェクトID | `sanwa-appsheet-vertex` |
| SPREADSHEET_ID | スプレッドシートID | `1ABC...xyz` |
| SHEET_NAME | シート名 | `介護記録` |
| PK_COLUMN | 主キーカラム名 | `RowID` |
| TARGET_COLUMN | 処理対象カラム名 | `TargetText` |
| RESULT_COLUMN | 結果書き込みカラム名 | `AIResult` |
| WEBHOOK_SECRET | 認証シークレット | `32文字以上のランダム文字列` |

### オプション

| 変数名 | デフォルト | 説明 |
|---|---|---|
| VERTEX_AI_LOCATION | `asia-northeast1` | Vertex AIリージョン |
| VERTEX_AI_MODEL | `gemini-1.5-flash` | 使用モデル |
| LOG_LEVEL | `INFO` | ログレベル |

---

## エラーハンドリング

### 認証エラー (403)

X-AppSheet-Secretヘッダーが存在しない、または値が不正な場合。

```json
{
  "error": "認証ヘッダーがありません"
}
```

```json
{
  "error": "認証に失敗しました"
}
```

### リクエストエラー (400)

JSONフォーマットエラーまたは必須フィールドの欠落。

```json
{
  "error": "無効なJSONフォーマットです"
}
```

```json
{
  "error": "必須フィールドがありません: RowID, TargetText"
}
```

### サーバーエラー (500)

Vertex AIまたはSheets APIでのエラー。

```json
{
  "error": "AI処理中にエラーが発生しました"
}
```

```json
{
  "error": "スプレッドシートへの書き込み中にエラーが発生しました"
}
```

<script>
  mermaid.initialize({ startOnLoad: true, theme: 'default' });
</script>
