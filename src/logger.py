import logging
import os
import re
from logging.handlers import RotatingFileHandler
from typing import Any

# 設定値管理を使用（テストでpatchしやすいように同名シンボルを公開）
try:  # pragma: no cover - 実行環境により分岐
    from src.config_manager import get_config, get_transfer_log_path
except ImportError:  # pragma: no cover - 実行環境により分岐
    get_config = None  # type: ignore[assignment]
    get_transfer_log_path = None  # type: ignore[assignment]

if get_transfer_log_path is not None:
    _log_path = get_transfer_log_path()
    _log_level = get_config("log_level", "INFO", "LOG_LEVEL") if get_config is not None else "INFO"
else:
    # フォールバック（直接実行時など）
    _log_path = os.environ.get(
        "TRANSFER_LOG_PATH",
        "logs/transfer_start_success_error.log",
    )
    _log_level = os.environ.get("LOG_LEVEL", "INFO")

LOG_PATH: str = _log_path
LOG_LEVEL: str = _log_level

# ロガー初期化
logger = logging.getLogger("bulk_migrator")
logger.setLevel(LOG_LEVEL)
if not logger.handlers:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    handler = RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 標準出力にも出す
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(console)


def log_transfer_start(file_info: dict[str, Any]) -> None:
    logger.info(
        "START: %s (size=%s, lastModified=%s)",
        file_info["path"],
        file_info["size"],
        file_info["lastModifiedDateTime"],
    )


def log_transfer_success(
    file_info: dict[str, Any],
    elapsed: float | None = None,
) -> None:
    if elapsed is not None:
        logger.info("SUCCESS: %s [elapsed: %.2fs]", file_info["path"], elapsed)
    else:
        logger.info("SUCCESS: %s", file_info["path"])


def log_transfer_error(
    file_info: dict[str, Any],
    error: Any,
    retry_count: int = 0,
) -> None:
    logger.error(
        "ERROR: %s [retry=%d] %s",
        file_info["path"],
        retry_count,
        error,
    )


def log_transfer_skip(file_info: dict[str, Any]) -> None:
    logger.info("SKIP: %s", file_info["path"])


class SecureLogger:
    """セキュリティ対応ログ出力クラス"""

    # 機密情報パターン（正規表現）
    SENSITIVE_PATTERNS = [
        # Microsoft Graph API関連
        (
            r'client_secret[=:]\s*["\']?([^"\'\s&]+)["\']?',
            "client_secret=[MASKED]",
        ),
        (
            r'access_token[=:]\s*["\']?([^"\'\s&]+)["\']?',
            "access_token=[MASKED]",
        ),
        (
            r'refresh_token[=:]\s*["\']?([^"\'\s&]+)["\']?',
            "refresh_token=[MASKED]",
        ),
        (r'tenant_id[=:]\s*["\']?([^"\'\s&]+)["\']?', "tenant_id=[MASKED]"),
        # 一般的な機密情報
        (r'api_key[=:]\s*["\']?([^"\'\s&]+)["\']?', "api_key=[MASKED]"),
        (r'password[=:]\s*["\']?([^"\'\s&]+)["\']?', "password=[MASKED]"),
        (r'secret[=:]\s*["\']?([^"\'\s&]+)["\']?', "secret=[MASKED]"),
        (r'token[=:]\s*["\']?([^"\'\s&]+)["\']?', "token=[MASKED]"),
        # Bearer トークン
        (r"Bearer\s+([A-Za-z0-9\-._~+/]+=*)", "Bearer [MASKED]"),
        # URL内の機密情報
        (r"(https?://[^/]*/)([^@]+@)", r"\1[MASKED]@"),
        # JSON内の機密情報
        (
            r'"(client_secret|access_token|refresh_token|api_key|password|' r'secret|token)"\s*:\s*"([^"]+)"',
            r'"\1": "[MASKED]"',
        ),
    ]

    def __init__(self, name: str, log_path: str | None = None):
        """
        SecureLoggerの初期化

        Args:
            name: ロガー名
            log_path: ログファイルパス（Noneの場合はデフォルト設定を使用）
        """
        self.logger = logging.getLogger(name)
        self.name = name
        self._setup_logger(log_path)

    def _setup_logger(self, log_path: str | None = None):
        """ロガーのセットアップ"""
        # 既存ハンドラをクリーンアップ（Windowsのファイルロック対策）
        for h in self.logger.handlers[:]:
            try:
                h.close()
            finally:
                self.logger.removeHandler(h)
        if get_transfer_log_path is not None and not log_path:
            try:
                actual_log_path = get_transfer_log_path()
            except ImportError:
                actual_log_path = os.environ.get(
                    "TRANSFER_LOG_PATH",
                    "logs/transfer_start_success_error.log",
                )

            if get_config is not None:
                try:
                    log_level = get_config("log_level", "INFO", "LOG_LEVEL")
                except ImportError:
                    log_level = os.environ.get("LOG_LEVEL", "INFO")
            else:
                log_level = os.environ.get("LOG_LEVEL", "INFO")
        else:
            actual_log_path = log_path or os.environ.get(
                "TRANSFER_LOG_PATH",
                "logs/transfer_start_success_error.log",
            )
            log_level = os.environ.get("LOG_LEVEL", "INFO")

        self.logger.setLevel(log_level)

        # ファイルハンドラー
        os.makedirs(os.path.dirname(actual_log_path), exist_ok=True)
        file_handler = RotatingFileHandler(
            actual_log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # ルートへの伝播を抑止
        self.logger.propagate = False

    def mask_sensitive_data(self, message: str | None) -> str | None:
        """
        メッセージ内の機密情報をマスクする

        Args:
            message: 元のメッセージ

        Returns:
            マスクされたメッセージ
        """
        if not message:
            return message

        masked_message = message
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            masked_message = re.sub(pattern, replacement, masked_message, flags=re.IGNORECASE)

        return masked_message

    def close(self) -> None:
        """ロガーのハンドラを全てクローズして解放する"""
        for h in self.logger.handlers[:]:
            try:
                h.close()
            finally:
                self.logger.removeHandler(h)

    def _log_with_masking(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """機密情報をマスクしてログ出力"""
        masked_message = self.mask_sensitive_data(message)
        self.logger.log(level, masked_message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """DEBUGレベルでログ出力（機密情報マスク付き）"""
        self._log_with_masking(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """INFOレベルでログ出力（機密情報マスク付き）"""
        self._log_with_masking(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """WARNINGレベルでログ出力（機密情報マスク付き）"""
        self._log_with_masking(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """ERRORレベルでログ出力（機密情報マスク付き）"""
        self._log_with_masking(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """CRITICALレベルでログ出力（機密情報マスク付き）"""
        self._log_with_masking(logging.CRITICAL, message, *args, **kwargs)

    def log_transfer_start(self, file_info: dict[str, Any]):
        """転送開始ログ（セキュア版）"""
        message = (
            f"START: {file_info['path']} (size={file_info['size']}, lastModified={file_info['lastModifiedDateTime']})"
        )
        self.info(message)

    def log_transfer_success(self, file_info: dict[str, Any], elapsed: float | None = None):
        """転送成功ログ（セキュア版）"""
        message = f"SUCCESS: {file_info['path']}"
        if elapsed is not None:
            message += f" [elapsed: {elapsed:.2f}s]"
        self.info(message)

    def log_transfer_error(self, file_info: dict[str, Any], error: str, retry_count: int = 0):
        """転送エラーログ（セキュア版）"""
        message = f"ERROR: {file_info['path']} [retry={retry_count}] {error}"
        self.error(message)

    def log_transfer_skip(self, file_info: dict[str, Any]):
        """転送スキップログ（セキュア版）"""
        message = f"SKIP: {file_info['path']}"
        self.info(message)

    def log_auth_event(
        self,
        event: str,
        details: dict[str, Any] | None = None,
    ):
        """認証イベントログ（セキュア版）"""
        message = f"AUTH: {event}"
        if details:
            # 機密情報を含む可能性があるdetailsをマスク
            safe_details = {}
            for key, value in details.items():
                if any(
                    sensitive in key.lower()
                    for sensitive in [
                        "secret",
                        "token",
                        "password",
                        "key",
                        "tenant",
                    ]
                ):
                    safe_details[key] = "[MASKED]"
                else:
                    safe_details[key] = value
            message += f" - {safe_details}"
        self.info(message)


# セキュアロガーのグローバルインスタンス
secure_logger = SecureLogger("bulk_migrator_secure")
