#!/usr/bin/env python3
"""
構造化ログ出力モジュール

JSON形式の構造化ログを出力し、機密情報の自動マスキング機能を提供
"""

import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any


class StructuredLogger:
    """構造化ログ出力クラス"""

    # 機密情報パターン
    SENSITIVE_PATTERNS = [
        r"client_secret=[\w-]+",
        r"access_token=[\w.-]+",
        r"tenant_id=[\w-]+",
        r"CLIENT_SECRET[\s]*=[\s]*[\w-]+",
        r"ACCESS_TOKEN[\s]*=[\s]*[\w.-]+",
        r"TENANT_ID[\s]*=[\s]*[\w-]+",
    ]

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.setup_json_formatter()

    def setup_json_formatter(self) -> None:
        """JSON形式のフォーマッターを設定"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def generate_trace_id(self) -> str:
        """トレースIDを生成"""
        return str(uuid.uuid4())

    def mask_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """機密情報をマスクする"""
        masked_data = data.copy()

        # メッセージ内の機密情報をマスク
        if "message" in masked_data and isinstance(masked_data["message"], str):
            message = masked_data["message"]
            for pattern in self.SENSITIVE_PATTERNS:
                message = re.sub(pattern, "[MASKED]", message, flags=re.IGNORECASE)
            masked_data["message"] = message

        # その他のフィールドも再帰的にマスク
        for key, value in masked_data.items():
            if isinstance(value, str):
                for pattern in self.SENSITIVE_PATTERNS:
                    value = re.sub(pattern, "[MASKED]", value, flags=re.IGNORECASE)
                masked_data[key] = value
            elif isinstance(value, dict):
                masked_data[key] = self.mask_sensitive_data(value)

        return masked_data

    def log_structured(
        self,
        level: str,
        event: str,
        message: str,
        trace_id: str | None = None,
        **kwargs,
    ) -> None:
        """構造化ログを出力"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "event": event,
            "message": message,
            "logger": self.logger.name,
            "trace_id": trace_id or self.generate_trace_id(),
            **kwargs,
        }

        # 機密情報のマスキング
        log_data = self.mask_sensitive_data(log_data)

        # JSON形式で出力
        json_message = json.dumps(log_data, ensure_ascii=False)

        # ログレベルに応じて出力
        if level.upper() == "DEBUG":
            self.logger.debug(json_message)
        elif level.upper() == "INFO":
            self.logger.info(json_message)
        elif level.upper() == "WARNING":
            self.logger.warning(json_message)
        elif level.upper() == "ERROR":
            self.logger.error(json_message)
        else:
            self.logger.info(json_message)

    def log_transfer_event(
        self,
        event: str,
        file_info: dict[str, Any],
        trace_id: str | None = None,
        **kwargs,
    ) -> None:
        """転送イベントの構造化ログ出力"""
        self.log_structured(
            level="INFO",
            event=event,
            message=f"File transfer {event}",
            module="transfer",
            trace_id=trace_id,
            file_name=file_info.get("name"),
            file_size=file_info.get("size"),
            file_path=file_info.get("path"),
            **kwargs,
        )

    def info(self, message: str, **kwargs) -> None:
        """INFO レベルのログ出力"""
        self.log_structured("INFO", "general", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """WARNING レベルのログ出力"""
        self.log_structured("WARNING", "general", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """ERROR レベルのログ出力"""
        self.log_structured("ERROR", "general", message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """DEBUG レベルのログ出力"""
        self.log_structured("DEBUG", "general", message, **kwargs)


# グローバルインスタンス
structured_logger = StructuredLogger("bulk-migration")


# 便利関数
def get_structured_logger(name: str = "bulk-migration") -> StructuredLogger:
    """構造化ログインスタンスを取得"""
    return StructuredLogger(name)
