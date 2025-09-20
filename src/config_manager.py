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
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "config.json"
        )
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
    return get_config(
        "onedrive_files_path", "logs/onedrive_files.json", "ONEDRIVE_FILES_PATH"
    )


def get_sharepoint_current_files_path() -> str:
    return get_config(
        "sharepoint_current_files_path",
        "logs/sharepoint_current_files.json",
        "SHAREPOINT_CURRENT_FILES_PATH",
    )


def get_checksum_report_path() -> str:
    return get_config(
        "checksum_report_path", "logs/checksum_report.json", "CHECKSUM_REPORT_PATH"
    )


def get_source_onedrive_folder_path() -> str:
    return get_config(
        "source_onedrive_user", "TEST-Onedrive", "SOURCE_ONEDRIVE_FOLDER_PATH"
    )


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
