---
layout: default
title: Architecture
---

# システム構成

## 全体アーキテクチャ

<div class="mermaid">
flowchart TB
    subgraph User["ユーザー"]
        U[介護スタッフ]
    end

    subgraph AppSheet["AppSheet アプリ"]
        AS[介護記録アプリ]
        BTN[AI処理ボタン]
    end

    subgraph GitHub["GitHub"]
        REPO[リポジトリ]
        GA[GitHub Actions]
    end

    subgraph GCP["Google Cloud Platform"]
        subgraph CloudRun["Cloud Run"]
            CR[appsheet-ai-processor<br/>Flask App]
        end

        subgraph AR["Artifact Registry"]
            IMG[Docker Image]
        end

        subgraph AI["Vertex AI"]
            GEMINI[Gemini 1.5 Flash]
        end

        subgraph APIs["Google APIs"]
            SHEETS[Sheets API]
        end

        SA_AI[ai-processor<br/>Service Account]
        SA_CD[github-actions-deployer<br/>Service Account]
        WIF[Workload Identity<br/>Federation]
    end

    subgraph Data["データストア"]
        SS[Google スプレッドシート<br/>介護記録データ]
    end

    U --> AS
    AS --> BTN
    BTN -->|Webhook POST| CR
    CR -->|AI処理| GEMINI
    CR -->|結果書き込み| SHEETS
    SHEETS --> SS
    SS --> AS

    REPO -->|push| GA
    GA -->|認証| WIF
    WIF -->|偽装| SA_CD
    GA -->|push| IMG
    GA -->|deploy| CR

    CR -->|使用| SA_AI
    SA_AI -->|認可| GEMINI
    SA_AI -->|認可| SHEETS
</div>

## コンポーネント詳細

### Cloud Run サービス

| 項目 | 値 |
|---|---|
| サービス名 | appsheet-ai-processor |
| リージョン | asia-northeast1 |
| メモリ | 512Mi |
| タイムアウト | 300秒 |
| 最小インスタンス | 0 |
| 最大インスタンス | 10 |
| 認証 | 未認証の呼び出しを許可 |

### 認証フロー

<div class="mermaid">
sequenceDiagram
    participant AS as AppSheet
    participant CR as Cloud Run
    participant SA as Service Account
    participant VA as Vertex AI
    participant GS as Sheets API

    AS->>CR: POST /process<br/>X-AppSheet-Secret: xxx
    CR->>CR: Secret検証
    CR->>SA: google.auth.default()
    SA-->>CR: 認証情報
    CR->>VA: AI処理リクエスト
    VA-->>CR: 処理結果
    CR->>GS: 結果書き込み
    GS-->>CR: 完了
    CR-->>AS: 200 OK
</div>

## サービスアカウント

### ai-processor

Cloud Run上のアプリケーションが使用するサービスアカウント。

```
ai-processor@sanwa-appsheet-vertex.iam.gserviceaccount.com
```

| ロール | 用途 |
|---|---|
| roles/aiplatform.user | Vertex AI API呼び出し |

### github-actions-deployer

CI/CDパイプラインが使用するサービスアカウント。

```
github-actions-deployer@sanwa-appsheet-vertex.iam.gserviceaccount.com
```

| ロール | 用途 |
|---|---|
| roles/artifactregistry.writer | Dockerイメージのプッシュ |
| roles/run.admin | Cloud Runデプロイ |
| roles/iam.serviceAccountUser | ai-processorの使用 |

## Workload Identity Federation

<div class="mermaid">
flowchart LR
    subgraph GitHub["GitHub Actions"]
        GA[ワークフロー]
        OIDC[OIDC Token]
    end

    subgraph GCP["Google Cloud"]
        WIP[Workload Identity Pool<br/>github-actions-pool]
        PROV[Provider<br/>github-actions-provider]
        SA[Service Account<br/>github-actions-deployer]
    end

    GA -->|id-token: write| OIDC
    OIDC -->|認証| PROV
    PROV -->|検証| WIP
    WIP -->|偽装許可| SA
    SA -->|アクセストークン| GA
</div>

## ファイル構成

```
sanwa-appsheet-vertex-processor/
├── .github/
│   └── workflows/
│       ├── deploy.yml      # Cloud Runデプロイ
│       └── pages.yml       # GitHub Pagesデプロイ
├── docs/                   # ドキュメント（GitHub Pages）
├── src/
│   ├── main.py             # Flaskエントリーポイント
│   ├── config.py           # 環境変数管理
│   ├── auth.py             # Webhook認証
│   ├── vertex_ai.py        # Vertex AI連携
│   └── sheets.py           # Sheets API連携
├── deploy/
│   └── setup.sh            # GCPセットアップスクリプト
├── Dockerfile
├── requirements.txt
└── README.md
```

<script>
  mermaid.initialize({ startOnLoad: true, theme: 'default' });
</script>
