#!/usr/bin/env python3
"""
設定値管理モジュール

優先順位：
1. 環境変数（.env）
2. config/config.json
3. デフォルト値
"""

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path, override=False)


class ConfigManager:
    def __init__(self):
        self._config_cache = None
        self._load_config()

    def _load_config(self):
        """config/config.jsonを読み込む"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
        try:
            with open(config_path, encoding="utf-8") as f:
                self._config_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config_cache = {}

    def get(self, key: str, default: Any = None, env_key: str | None = None) -> Any:
        """
        設定値を優先順位に従って取得

        Args:
            key: config.jsonのキー
            default: デフォルト値
            env_key: 環境変数のキー（Noneの場合はkeyを大文字化して使用）

        Returns:
            設定値
        """
        # 1. 環境変数から取得を試行
        if env_key is None:
            env_key = key.upper()

        env_value = os.getenv(env_key)
        if env_value is not None and env_value != "":
            return env_value

        # 2. config.jsonから取得を試行
        if self._config_cache and key in self._config_cache:
            config_value = self._config_cache[key]
            if config_value is not None and config_value != "":
                return config_value

        # 3. デフォルト値
        return default


# グローバルインスタンス
config_manager = ConfigManager()


def get_config(key: str, default: Any = None, env_key: str | None = None) -> Any:
    """設定値取得のショートカット関数"""
    return config_manager.get(key, default, env_key)


# 頻繁に使用される設定値のショートカット関数
def get_transfer_log_path() -> str:
    return get_config(
        "transfer_log_path",
        "logs/transfer_start_success_error.log",
        "TRANSFER_LOG_PATH",
    )


def get_skip_list_path() -> str:
    return get_config("skip_list_path", "logs/skip_list.json", "SKIP_LIST_PATH")


def get_onedrive_files_path() -> str:
    return get_config("onedrive_files_path", "logs/onedrive_files.json", "ONEDRIVE_FILES_PATH")


def get_sharepoint_current_files_path() -> str:
    return get_config(
        "sharepoint_current_files_path",
        "logs/sharepoint_current_files.json",
        "SHAREPOINT_CURRENT_FILES_PATH",
    )


def get_checksum_report_path() -> str:
    return get_config("checksum_report_path", "logs/checksum_report.json", "CHECKSUM_REPORT_PATH")


def get_source_onedrive_folder_path() -> str:
    return get_config("source_onedrive_user", "TEST-Onedrive", "SOURCE_ONEDRIVE_FOLDER_PATH")


def get_destination_sharepoint_doclib() -> str:
    return get_config(
        "destination_sharepoint_doclib",
        "TEST-Sharepoint",
        "DESTINATION_SHAREPOINT_DOCLIB",
    )


def get_chunk_size_mb() -> int:
    return get_config("chunk_size_mb", 5, "CHUNK_SIZE_MB")


def get_large_file_threshold_mb() -> int:
    return get_config("large_file_threshold_mb", 4, "LARGE_FILE_THRESHOLD_MB")


class SecureConfigManager(ConfigManager):
    """セキュリティ強化された設定管理クラス"""

    # 機密情報として扱うキーのパターン
    SENSITIVE_KEYS = {
        "CLIENT_SECRET",
        "TENANT_ID",
        "ACCESS_TOKEN",
        "REFRESH_TOKEN",
        "API_KEY",
        "PASSWORD",
        "SECRET",
        "TOKEN",
        "KEY",
    }

    # 機密情報パターン（正規表現）
    SENSITIVE_PATTERNS = [
        r'client_secret[=:]\s*["\']?([^"\'\s]+)["\']?',
        r'access_token[=:]\s*["\']?([^"\'\s]+)["\']?',
        r'tenant_id[=:]\s*["\']?([^"\'\s]+)["\']?',
        r'api_key[=:]\s*["\']?([^"\'\s]+)["\']?',
        r'password[=:]\s*["\']?([^"\'\s]+)["\']?',
    ]

    def __init__(self):
        super().__init__()

    def is_sensitive_key(self, key: str) -> bool:
        """キーが機密情報かどうかを判定"""
        key_upper = key.upper()
        return any(sensitive in key_upper for sensitive in self.SENSITIVE_KEYS)

    def mask_value(self, value: Any) -> str | None:
        """値をマスクする"""
        if value is None:
            return None

        value_str = str(value)
        if len(value_str) <= 4:
            return "***"
        elif len(value_str) <= 8:
            return value_str[:2] + "***"
        else:
            return value_str[:3] + "***" + value_str[-2:]

    def get_masked_config(self) -> dict[str, Any]:
        """機密情報をマスクした設定を返す"""
        config = {}

        # 環境変数から取得
        for key, value in os.environ.items():
            if self.is_sensitive_key(key):
                config[key] = self.mask_value(value)
            else:
                config[key] = value

        # config.jsonから取得
        if self._config_cache:
            for key, value in self._config_cache.items():
                if self.is_sensitive_key(key):
                    config[key] = self.mask_value(value)
                else:
                    config[key] = value

        return config

    def get_all_config(self) -> dict[str, Any]:
        """全設定を取得（機密情報含む）- 内部使用のみ"""
        config = {}

        # 環境変数から取得
        for key, value in os.environ.items():
            config[key] = value

        # config.jsonから取得
        if self._config_cache:
            for key, value in self._config_cache.items():
                config[key] = value

        return config

    def mask_sensitive_data(self, text: str) -> str:
        """テキスト内の機密情報をマスクする"""
        if not text:
            return text

        masked_text = text
        for pattern in self.SENSITIVE_PATTERNS:
            masked_text = re.sub(
                pattern,
                lambda m: (
                    f"{m.group(0).split('=')[0]}=[MASKED]"
                    if "=" in m.group(0)
                    else f"{m.group(0).split(':')[0]}:[MASKED]"
                ),
                masked_text,
                flags=re.IGNORECASE,
            )

        return masked_text

    def validate_env_file_security(self) -> dict[str, Any]:
        """環境ファイルのセキュリティ設定を検証"""
        results: dict[str, Any] = {
            "env_in_gitignore": False,
            "sample_env_exists": False,
            "sensitive_keys_found": [],
            "recommendations": [],
        }

        # .gitignoreの確認
        gitignore_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, encoding="utf-8") as f:
                gitignore_content = f.read()
                if ".env" in gitignore_content:
                    results["env_in_gitignore"] = True

        # sample.envの確認
        sample_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample.env")
        results["sample_env_exists"] = os.path.exists(sample_env_path)

        # 機密情報キーの確認
        for key in os.environ.keys():
            if self.is_sensitive_key(key):
                results["sensitive_keys_found"].append(key)

        # 推奨事項の生成
        if not results["env_in_gitignore"]:
            results["recommendations"].append(".envファイルを.gitignoreに追加してください")

        if not results["sample_env_exists"]:
            results["recommendations"].append("sample.envファイルを作成してください")

        if not results["sensitive_keys_found"]:
            results["recommendations"].append("必要な機密情報の環境変数が設定されていません")

        return results


# セキュアな設定管理インスタンス
secure_config_manager = SecureConfigManager()
