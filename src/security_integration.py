"""
既存システムへのセキュリティ統合
"""

import logging
import os
from typing import Any

from .secrets_manager import SecretsManager, SecureLogFormatter
from .security_audit import AccessController, SecurityAuditor


class SecurityIntegration:
    """セキュリティ機能の統合管理"""

    def __init__(self):
        self.secrets_manager = SecretsManager()
        self.auditor = SecurityAuditor()
        self.access_controller = AccessController()

    def setup_secure_logging(
        self, logger_name: str = "bulk-migration"
    ) -> logging.Logger:
        """セキュアなロガーの設定"""
        logger = logging.getLogger(logger_name)

        # 既存ハンドラーをクリア
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # セキュアフォーマッターを適用
        handler = logging.FileHandler("logs/secure_transfer.log")
        handler.setFormatter(
            SecureLogFormatter(
                "%(asctime)s UTC - %(levelname)s - %(name)s - %(message)s"
            )
        )

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        return logger

    def validate_environment(self) -> dict[str, Any]:
        """環境のセキュリティ検証"""
        validation_results = {
            "env_security": self.secrets_manager.validate_env_security(),
            "file_permissions": self._check_critical_files(),
            "secrets_exposure": self.auditor.scan_for_secrets_exposure(),
            "timestamp": self.secrets_manager._get_timestamp(),
        }

        # 重要ファイルの整合性チェック
        critical_files = [".env", "config/config.json", "src/main.py"]
        validation_results["integrity"] = self.auditor.check_file_integrity(
            critical_files
        )

        return validation_results

    def _check_critical_files(self) -> dict[str, Any]:
        """重要ファイルの権限チェック"""
        critical_files = [".env", "config/config.json"]
        results = {}

        for file_path in critical_files:
            if os.path.exists(file_path):
                results[file_path] = self.access_controller.check_file_permissions(
                    file_path
                )

                # 権限が不適切な場合は自動修正
                if results[file_path]["status"] == "INSECURE_PERMISSIONS":
                    if self.access_controller.secure_file_permissions(file_path):
                        results[file_path]["auto_fixed"] = True

        return results

    def audit_transfer_operation(self, operation: str, file_path: str, success: bool):
        """転送操作の監査"""
        self.auditor.audit_file_access(file_path, operation)

        if not success:
            self.auditor.audit_logger.error(
                f"TRANSFER_FAILURE - Operation: {operation}, "
                f"File: {self.auditor._mask_path(file_path)}"
            )


# グローバルインスタンス
security_integration = SecurityIntegration()
