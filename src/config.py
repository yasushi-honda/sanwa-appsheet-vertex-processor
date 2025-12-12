"""環境変数の読み込みと設定管理"""

import os
import logging
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Config:
    """アプリケーション設定"""

    # 必須環境変数
    project_id: str
    spreadsheet_id: str
    sheet_name: str
    pk_column: str
    target_column: str
    result_column: str
    webhook_secret: str

    # オプション環境変数
    vertex_ai_location: str = "asia-northeast1"
    vertex_ai_model: str = "gemini-1.5-flash"
    log_level: str = "INFO"
    port: int = 8080


def load_config() -> Config:
    """環境変数から設定を読み込む

    Returns:
        Config: アプリケーション設定

    Raises:
        ValueError: 必須環境変数が設定されていない場合
    """
    required_vars = [
        "PROJECT_ID",
        "SPREADSHEET_ID",
        "SHEET_NAME",
        "PK_COLUMN",
        "TARGET_COLUMN",
        "RESULT_COLUMN",
        "WEBHOOK_SECRET",
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"必須環境変数が設定されていません: {', '.join(missing_vars)}")

    return Config(
        project_id=os.environ["PROJECT_ID"],
        spreadsheet_id=os.environ["SPREADSHEET_ID"],
        sheet_name=os.environ["SHEET_NAME"],
        pk_column=os.environ["PK_COLUMN"],
        target_column=os.environ["TARGET_COLUMN"],
        result_column=os.environ["RESULT_COLUMN"],
        webhook_secret=os.environ["WEBHOOK_SECRET"],
        vertex_ai_location=os.environ.get("VERTEX_AI_LOCATION", "asia-northeast1"),
        vertex_ai_model=os.environ.get("VERTEX_AI_MODEL", "gemini-1.5-flash"),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        port=int(os.environ.get("PORT", "8080")),
    )


def setup_logging(log_level: str) -> None:
    """ロギングの設定

    Args:
        log_level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
