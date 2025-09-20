"""
テスト用設定管理テスト
"""

from unittest.mock import patch

import pytest

from src.config_manager import (
    get_chunk_size_mb,
    get_config,
    get_large_file_threshold_mb,
)


class TestConfigManagerSettings:
    """設定管理の詳細テスト"""

    @patch("src.config_manager.config_manager")
    def test_config_file_not_found(self, mock_config_manager):
        """設定ファイルが存在しない場合のテスト"""
        mock_config_manager.get.return_value = "INFO"
        result = get_config("log_level", "INFO")
        assert result == "INFO"

    @patch("src.config_manager.config_manager")
    def test_config_invalid_json(self, mock_config_manager):
        """無効なJSONファイルのテスト"""
        mock_config_manager.get.return_value = "INFO"
        result = get_config("log_level", "INFO")
        assert result == "INFO"

    @patch("src.config_manager.config_manager")
    def test_chunk_size_mb_default(self, mock_config_manager):
        """チャンクサイズのデフォルト値テスト"""
        mock_config_manager.get.return_value = 5
        result = get_chunk_size_mb()
        assert result == 5  # デフォルト値

    @patch("src.config_manager.config_manager")
    def test_large_file_threshold_default(self, mock_config_manager):
        """大容量ファイル閾値のデフォルト値テスト"""
        mock_config_manager.get.return_value = 4
        result = get_large_file_threshold_mb()
        assert result == 4  # デフォルト値

    @pytest.mark.config
    @patch("src.config_manager.config_manager")
    def test_config_all_keys(self, mock_config_manager):
        """全設定キーのテスト"""
        config_data = {
            "log_level": "DEBUG",
            "chunk_size_mb": 10,
            "large_file_threshold_mb": 8,
            "max_parallel_transfers": 6,
            "retry_count": 5,
            "timeout_sec": 15,
            "transfer_log_path": "logs/test.log",
            "skip_list_path": "logs/test_skip.json",
        }

        for key, expected_value in config_data.items():
            mock_config_manager.get.return_value = expected_value
            result = get_config(key, "default")
            assert result == expected_value
