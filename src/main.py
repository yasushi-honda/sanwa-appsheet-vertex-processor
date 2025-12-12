"""Flaskエントリーポイント、エンドポイント定義"""

import logging
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from config import Config, load_config, setup_logging
from auth import verify_webhook_secret, validate_request_body
from vertex_ai import process_with_gemini
from sheets import update_sheet_row

# アプリケーション設定
config: Config = None
app = Flask(__name__)
logger = logging.getLogger(__name__)

VERSION = "1.0.0"


@app.route("/health", methods=["GET"])
def health():
    """ヘルスチェックエンドポイント"""
    return jsonify({"status": "healthy", "version": VERSION})


@app.route("/process", methods=["POST"])
def process():
    """AI処理エンドポイント

    AppSheet Webhookからのリクエストを受け付け、
    Vertex AI (Gemini) で処理し、結果をスプレッドシートに書き戻す
    """
    # Webhook認証
    request_secret = request.headers.get("X-AppSheet-Secret")
    if not request_secret:
        logger.warning("X-AppSheet-Secret ヘッダーが存在しません")
        return jsonify({"error": "認証ヘッダーがありません"}), 403

    import hmac
    if not hmac.compare_digest(request_secret, config.webhook_secret):
        logger.warning("X-AppSheet-Secret の検証に失敗しました")
        return jsonify({"error": "認証に失敗しました"}), 403

    # リクエストボディの取得
    try:
        data = request.get_json()
    except Exception as e:
        logger.error(f"JSONパースエラー: {e}")
        return jsonify({"error": "無効なJSONフォーマットです"}), 400

    # 必須フィールドの検証
    required_fields = [config.pk_column, config.target_column]
    is_valid, error_message = validate_request_body(data, required_fields)
    if not is_valid:
        logger.warning(f"リクエスト検証エラー: {error_message}")
        return jsonify({"error": error_message}), 400

    row_id = data[config.pk_column]
    target_text = data[config.target_column]

    logger.info(f"処理開始: row_id={row_id}")

    # Vertex AI (Gemini) による処理
    try:
        ai_result = process_with_gemini(
            text=target_text,
            project_id=config.project_id,
            location=config.vertex_ai_location,
            model_name=config.vertex_ai_model,
        )
    except Exception as e:
        logger.error(f"Vertex AI処理エラー: {e}")
        return jsonify({"error": "AI処理中にエラーが発生しました"}), 500

    # 処理日時
    processed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # スプレッドシートへの書き込み
    try:
        update_sheet_row(
            spreadsheet_id=config.spreadsheet_id,
            sheet_name=config.sheet_name,
            pk_column=config.pk_column,
            pk_value=row_id,
            result_column=config.result_column,
            result_value=ai_result,
            processed_at=processed_at,
        )
    except Exception as e:
        logger.error(f"スプレッドシート書き込みエラー: {e}")
        return jsonify({"error": "スプレッドシートへの書き込み中にエラーが発生しました"}), 500

    logger.info(f"処理完了: row_id={row_id}")

    return jsonify({
        "status": "success",
        "row_id": row_id,
        "ai_result": ai_result,
        "processed_at": processed_at,
    })


def create_app() -> Flask:
    """Flaskアプリケーションを作成する

    Returns:
        Flask: 設定済みのFlaskアプリケーション
    """
    global config

    # 設定の読み込み
    config = load_config()

    # ロギングの設定
    setup_logging(config.log_level)

    logger.info(f"アプリケーション起動: version={VERSION}")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=config.port, debug=False)
