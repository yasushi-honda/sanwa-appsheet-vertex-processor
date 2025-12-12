"""Vertex AI (Gemini) 連携処理"""

import logging

import google.auth
import vertexai
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)

# Vertex AI初期化フラグ
_initialized = False


def _initialize_vertex_ai(project_id: str, location: str) -> None:
    """Vertex AIを初期化する（Workload Identity使用）

    Args:
        project_id: GCPプロジェクトID
        location: Vertex AIリージョン
    """
    global _initialized

    if _initialized:
        return

    # Workload Identityによる自動認証
    # google.auth.default() が Cloud Run 環境で自動的に認証情報を取得
    credentials, project = google.auth.default()

    vertexai.init(
        project=project_id,
        location=location,
        credentials=credentials,
    )

    _initialized = True
    logger.info(f"Vertex AI初期化完了: project={project_id}, location={location}")


def process_with_gemini(
    text: str,
    project_id: str,
    location: str,
    model_name: str,
    timeout: int = 60,
) -> str:
    """Geminiモデルでテキストを処理する

    Args:
        text: 処理対象のテキスト
        project_id: GCPプロジェクトID
        location: Vertex AIリージョン
        model_name: 使用するモデル名
        timeout: タイムアウト秒数

    Returns:
        AIによる処理結果テキスト

    Raises:
        Exception: Vertex AI API呼び出しでエラーが発生した場合
    """
    # Vertex AIの初期化
    _initialize_vertex_ai(project_id, location)

    logger.info(f"Gemini処理開始: model={model_name}, text_length={len(text)}")

    try:
        # モデルの取得
        model = GenerativeModel(model_name)

        # プロンプトの構築
        prompt = f"""以下のテキストを分析し、要約・整理してください。

テキスト:
{text}

回答:"""

        # 生成の実行
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.2,
            },
        )

        result = response.text
        logger.info(f"Gemini処理完了: result_length={len(result)}")

        return result

    except Exception as e:
        logger.error(f"Gemini処理エラー: {e}")
        raise
