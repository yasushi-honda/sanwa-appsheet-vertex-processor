---
layout: default
title: Home
---

# AppSheet AI Processor

AppSheetアプリケーションからユーザーが選択した行データに対して、GCP上のCloud Runサービス経由でVertex AI（Gemini）による処理を実行し、結果をGoogleスプレッドシートに書き戻すシステムです。

## 特徴

- **Workload Identity認証** - サービスアカウントキー不要のセキュアな認証
- **サーバーレス** - Cloud Runによる自動スケーリング
- **AI処理** - Vertex AI (Gemini) による高度なテキスト処理
- **リアルタイム連携** - AppSheet Webhookによる即座のデータ処理

## システム構成

<div class="mermaid">
flowchart TB
    subgraph AppSheet["AppSheet"]
        A[ユーザー操作]
    end

    subgraph CloudRun["Cloud Run"]
        B[appsheet-ai-processor]
    end

    subgraph GCP["Google Cloud Platform"]
        C[Vertex AI<br/>Gemini]
        D[Google Sheets API]
    end

    subgraph Data["Data Store"]
        E[Google スプレッドシート]
    end

    A -->|Webhook POST| B
    B -->|AI処理リクエスト| C
    C -->|処理結果| B
    B -->|結果書き込み| D
    D -->|更新| E
    E -->|データソース| A
</div>

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
| ドキュメント | GitHub Pages |

## クイックリンク

- [システム構成](./architecture) - アーキテクチャ詳細とMermaid図
- [API仕様](./api-spec) - エンドポイント仕様とリクエスト/レスポンス形式
- [セットアップガイド](./setup-guide) - 環境構築手順
- [CI/CD](./ci-cd) - GitHub Actionsによる自動デプロイ
- [GCPセットアップ](./gcp-setup) - GCPリソース設定詳細

## リポジトリ

- GitHub: [yasushi-honda/sanwa-appsheet-vertex-processor](https://github.com/yasushi-honda/sanwa-appsheet-vertex-processor)

<script>
  mermaid.initialize({ startOnLoad: true, theme: 'default' });
</script>
