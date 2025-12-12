"""Google Sheets API 連携処理"""

import logging
from typing import Optional

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Sheets APIサービスのキャッシュ
_sheets_service = None


def _get_sheets_service():
    """Sheets APIサービスを取得する（Workload Identity使用）

    Returns:
        Google Sheets APIサービスオブジェクト
    """
    global _sheets_service

    if _sheets_service is not None:
        return _sheets_service

    # Workload Identityによる自動認証
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    _sheets_service = build("sheets", "v4", credentials=credentials)
    logger.info("Google Sheets APIサービス初期化完了")

    return _sheets_service


def _get_column_index(sheet_name: str, spreadsheet_id: str, column_name: str) -> int:
    """カラム名からカラムインデックス（0始まり）を取得する

    Args:
        sheet_name: シート名
        spreadsheet_id: スプレッドシートID
        column_name: カラム名

    Returns:
        カラムインデックス（0始まり）

    Raises:
        ValueError: カラムが見つからない場合
    """
    service = _get_sheets_service()

    # ヘッダー行を取得
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!1:1",
    ).execute()

    headers = result.get("values", [[]])[0]

    try:
        return headers.index(column_name)
    except ValueError:
        raise ValueError(f"カラム '{column_name}' が見つかりません")


def _column_index_to_letter(index: int) -> str:
    """カラムインデックス（0始まり）をアルファベット表記に変換する

    Args:
        index: カラムインデックス（0始まり）

    Returns:
        カラムのアルファベット表記（例: A, B, ..., Z, AA, AB, ...）
    """
    result = ""
    while index >= 0:
        result = chr(index % 26 + ord("A")) + result
        index = index // 26 - 1
    return result


def _find_row_by_pk(
    spreadsheet_id: str,
    sheet_name: str,
    pk_column_index: int,
    pk_value: str,
) -> Optional[int]:
    """主キーで行番号を検索する

    Args:
        spreadsheet_id: スプレッドシートID
        sheet_name: シート名
        pk_column_index: 主キーカラムのインデックス（0始まり）
        pk_value: 検索する主キーの値

    Returns:
        行番号（1始まり）、見つからない場合はNone
    """
    service = _get_sheets_service()
    pk_column_letter = _column_index_to_letter(pk_column_index)

    # 主キーカラム全体を取得
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!{pk_column_letter}:{pk_column_letter}",
    ).execute()

    values = result.get("values", [])

    for i, row in enumerate(values):
        if row and str(row[0]) == str(pk_value):
            return i + 1  # 1始まりの行番号

    return None


def update_sheet_row(
    spreadsheet_id: str,
    sheet_name: str,
    pk_column: str,
    pk_value: str,
    result_column: str,
    result_value: str,
    processed_at: str,
) -> None:
    """スプレッドシートの該当行を更新する

    Args:
        spreadsheet_id: スプレッドシートID
        sheet_name: シート名
        pk_column: 主キーカラム名
        pk_value: 主キーの値
        result_column: 結果を書き込むカラム名
        result_value: 書き込む結果値
        processed_at: 処理日時

    Raises:
        ValueError: 行が見つからない場合
        HttpError: API呼び出しでエラーが発生した場合
    """
    service = _get_sheets_service()

    logger.info(f"スプレッドシート更新開始: pk={pk_value}")

    try:
        # カラムインデックスの取得
        pk_column_index = _get_column_index(sheet_name, spreadsheet_id, pk_column)
        result_column_index = _get_column_index(sheet_name, spreadsheet_id, result_column)

        # 処理日時カラムのインデックス（結果カラムの次と仮定）
        # 実際の運用では環境変数で設定可能にすることを推奨
        processed_at_column_index = result_column_index + 1

        # 主キーで行を検索
        row_number = _find_row_by_pk(spreadsheet_id, sheet_name, pk_column_index, pk_value)
        if row_number is None:
            raise ValueError(f"主キー '{pk_value}' に該当する行が見つかりません")

        # 結果カラムのレター表記
        result_column_letter = _column_index_to_letter(result_column_index)
        processed_at_column_letter = _column_index_to_letter(processed_at_column_index)

        # バッチ更新用のデータ
        data = [
            {
                "range": f"{sheet_name}!{result_column_letter}{row_number}",
                "values": [[result_value]],
            },
            {
                "range": f"{sheet_name}!{processed_at_column_letter}{row_number}",
                "values": [[processed_at]],
            },
        ]

        # バッチ更新の実行
        body = {"valueInputOption": "RAW", "data": data}
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body,
        ).execute()

        logger.info(f"スプレッドシート更新完了: row={row_number}")

    except HttpError as e:
        logger.error(f"Google Sheets API エラー: {e}")
        raise
    except Exception as e:
        logger.error(f"スプレッドシート更新エラー: {e}")
        raise
