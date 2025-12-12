"""X-AppSheet-Secretによるリクエスト検証"""

import hmac
import logging
from functools import wraps
from typing import Callable

from flask import Request, jsonify, request

logger = logging.getLogger(__name__)


def verify_webhook_secret(webhook_secret: str) -> Callable:
    """Webhook認証デコレータを生成する

    Args:
        webhook_secret: 検証に使用するシークレット文字列

    Returns:
        デコレータ関数
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # X-AppSheet-Secret ヘッダーを取得
            request_secret = request.headers.get("X-AppSheet-Secret")

            if not request_secret:
                logger.warning("X-AppSheet-Secret ヘッダーが存在しません")
                return jsonify({"error": "認証ヘッダーがありません"}), 403

            # タイミング攻撃を防ぐため、hmac.compare_digest を使用
            if not hmac.compare_digest(request_secret, webhook_secret):
                logger.warning("X-AppSheet-Secret の検証に失敗しました")
                return jsonify({"error": "認証に失敗しました"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_request_body(data: dict, required_fields: list[str]) -> tuple[bool, str]:
    """リクエストボディの必須フィールドを検証する

    Args:
        data: リクエストボディ（JSON）
        required_fields: 必須フィールドのリスト

    Returns:
        (検証結果, エラーメッセージ)
    """
    if not data:
        return False, "リクエストボディが空です"

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"必須フィールドがありません: {', '.join(missing_fields)}"

    return True, ""
