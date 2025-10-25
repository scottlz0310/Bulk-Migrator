"""
セキュリティ監査とアクセス制御
"""

import hashlib
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any


class SecurityAuditor:
    """セキュリティ監査機能"""

    def __init__(self, audit_log_path: str = "logs/security_audit.log"):
        self.audit_log_path = audit_log_path
        self._setup_audit_logger()
        self.sensitive_files = {
            ".env",
            "config.json",
            "*.key",
            "*.pem",
            "*.p12",
        }

    def _setup_audit_logger(self):
        """監査ログの設定"""
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)

        self.audit_logger = logging.getLogger("security_audit")
        self.audit_logger.setLevel(logging.INFO)

        if not self.audit_logger.handlers:
            handler = logging.FileHandler(self.audit_log_path)
            formatter = logging.Formatter(
                "%(asctime)s UTC - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)

    def audit_file_access(
        self,
        file_path: str,
        operation: str,
        user: str | None = None,
    ) -> None:
        """ファイルアクセスの監査ログ"""
        user = user or os.getenv("USERNAME", "unknown")

        # 機密ファイルへのアクセスを記録
        patterns = [".env", "secret", "key", "credential"]
        if any(pattern in file_path.lower() for pattern in patterns):
            self.audit_logger.warning(
                ("SENSITIVE_FILE_ACCESS - User: %s, Operation: %s, File: %s, PID: %s"),
                user,
                operation,
                self._mask_path(file_path),
                os.getpid(),
            )
        else:
            self.audit_logger.info(
                "FILE_ACCESS - User: %s, Operation: %s, File: %s",
                user,
                operation,
                self._mask_path(file_path),
            )

    def audit_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int | None = None,
    ) -> None:
        """API呼び出しの監査"""
        self.audit_logger.info(
            "API_CALL - Endpoint: %s, Method: %s, Status: %s",
            self._mask_endpoint(endpoint),
            method,
            status_code or "N/A",
        )

    def audit_authentication(
        self,
        success: bool,
        user: str | None = None,
        details: str | None = None,
    ) -> None:
        """認証イベントの監査"""
        user = user or os.getenv("USERNAME", "unknown")
        status = "SUCCESS" if success else "FAILURE"

        self.audit_logger.warning(
            "AUTH_%s - User: %s, Details: %s, Timestamp: %s",
            status,
            user,
            details or "N/A",
            datetime.now(UTC).isoformat(),
        )

    def check_file_integrity(
        self,
        critical_files: list[str],
    ) -> dict[str, Any]:
        """重要ファイルの整合性チェック"""
        files: dict[str, dict[str, Any]] = {}
        alerts: list[str] = []
        timestamp = datetime.now(UTC).isoformat()

        for file_path in critical_files:
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    content = f.read()
                    file_hash = hashlib.sha256(content).hexdigest()

                files[file_path] = {
                    "hash": file_hash,
                    "size": len(content),
                    "modified": os.path.getmtime(file_path),
                }

                # 前回のハッシュと比較
                hash_file = f"{file_path}.hash"
                if os.path.exists(hash_file):
                    with open(hash_file, encoding="utf-8") as hf:
                        stored_hash = hf.read().strip()

                    if stored_hash != file_hash:
                        alert = f"INTEGRITY_VIOLATION: {file_path} has been modified"
                        alerts.append(alert)
                        self.audit_logger.critical(alert)

                # 新しいハッシュを保存
                with open(hash_file, "w", encoding="utf-8") as hf:
                    hf.write(file_hash)
                os.chmod(hash_file, 0o600)

        return {"timestamp": timestamp, "files": files, "alerts": alerts}

    def scan_for_secrets_exposure(
        self,
        directory: str = ".",
    ) -> dict[str, Any]:
        """機密情報の露出スキャン"""
        exposed_secrets: list[dict[str, Any]] = []

        # 危険なパターン
        secret_patterns = [
            r'CLIENT_SECRET\s*=\s*["\'][^"\']+["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r"[A-Za-z0-9+/]{40,}={0,2}",  # Base64
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        ]

        for root, dirs, files in os.walk(directory):
            # .git, __pycache__ などをスキップ
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

            for file in files:
                if file.endswith((".py", ".json", ".txt", ".md", ".yml", ".yaml")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path,
                            encoding="utf-8",
                            errors="ignore",
                        ) as f:
                            content = f.read()

                        for pattern in secret_patterns:
                            matches = re.findall(
                                pattern,
                                content,
                                re.IGNORECASE,
                            )
                            if matches:
                                exposed_secrets.append(
                                    {
                                        "file": file_path,
                                        "pattern": pattern,
                                        "matches_count": len(matches),
                                    }
                                )
                    except (OSError, UnicodeDecodeError):
                        continue

        if exposed_secrets:
            msg = f"SECRETS_EXPOSURE_DETECTED: {len(exposed_secrets)} files"
            self.audit_logger.critical(msg)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "exposed_secrets": exposed_secrets,
            "status": "CLEAN" if not exposed_secrets else "SECRETS_FOUND",
        }

    def _mask_path(self, path: str) -> str:
        """パスの機密部分をマスキング"""
        # ユーザー名やドライブ文字をマスキング
        path = re.sub(r"[A-Z]:\\Users\\[^\\]+", r"C:\Users\***", path)
        path = re.sub(r"/home/[^/]+", r"/home/***", path)
        return path

    def _mask_endpoint(self, endpoint: str) -> str:
        """エンドポイントの機密部分をマスキング"""
        # UUIDやIDをマスキング
        endpoint = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/***-***-***-***",
            endpoint,
            flags=re.IGNORECASE,
        )
        return endpoint


class AccessController:
    """アクセス制御機能"""

    def __init__(self):
        self.allowed_operations = {
            "read": ["logs", "config"],
            "write": ["logs"],
            "execute": ["src"],
        }

    def check_file_permissions(self, file_path: str) -> dict[str, Any]:
        """ファイル権限の確認"""
        if not os.path.exists(file_path):
            return {"status": "FILE_NOT_FOUND", "path": file_path}

        stat = os.stat(file_path)
        permissions = oct(stat.st_mode)[-3:]

        # 機密ファイルの権限チェック
        if any(sensitive in file_path.lower() for sensitive in [".env", "secret", "key"]):
            if int(permissions[1:]) > 0:  # グループ・その他に権限がある
                return {
                    "status": "INSECURE_PERMISSIONS",
                    "path": file_path,
                    "permissions": permissions,
                    "recommendation": "chmod 600",
                }

        return {
            "status": "SECURE",
            "path": file_path,
            "permissions": permissions,
        }

    def secure_file_permissions(self, file_path: str) -> bool:
        """ファイル権限の安全化"""
        try:
            if any(sensitive in file_path.lower() for sensitive in [".env", "secret", "key"]):
                os.chmod(file_path, 0o600)  # 所有者のみ読み書き
            else:
                os.chmod(file_path, 0o644)  # 標準権限
            return True
        except OSError:
            return False
