from unittest.mock import patch

from src.config_manager import (
    get_chunk_size_mb,
    get_config,
    get_large_file_threshold_mb,
)


class TestConfigManager:
    """config_managerモジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前処理"""
        self.test_config = {
            "log_level": "DEBUG",
            "chunk_size_mb": 10,
            "large_file_threshold_mb": 8,
            "max_parallel_transfers": 6,
            "retry_count": 5,
            "timeout_sec": 15,
        }

    @patch("src.config_manager.config_manager")
    def test_get_config_with_default(self, mock_config_manager):
        """デフォルト値付きの設定取得テスト"""
        mock_config_manager.get.return_value = "DEBUG"
        result = get_config("log_level", "INFO")
        assert result == "DEBUG"
        mock_config_manager.get.assert_called_once_with("log_level", "INFO", None)

    @patch("src.config_manager.config_manager")
    def test_get_config_with_missing_key(self, mock_config_manager):
        """存在しないキーの場合のデフォルト値テスト"""
        mock_config_manager.get.return_value = "default_value"
        result = get_config("non_existent_key", "default_value")
        assert result == "default_value"

    @patch("src.config_manager.config_manager")
    def test_get_config_with_missing_file(self, mock_config_manager):
        """設定ファイルが存在しない場合のテスト"""
        mock_config_manager.get.return_value = "INFO"
        result = get_config("log_level", "INFO")
        assert result == "INFO"

    @patch("src.config_manager.config_manager")
    def test_get_chunk_size_mb(self, mock_config_manager):
        """チャンクサイズ取得テスト"""
        mock_config_manager.get.return_value = 10
        result = get_chunk_size_mb()
        assert result == 10

    @patch("src.config_manager.config_manager")
    def test_get_large_file_threshold_mb(self, mock_config_manager):
        """大容量ファイル閾値取得テスト"""
        mock_config_manager.get.return_value = 8
        result = get_large_file_threshold_mb()
        assert result == 8

    @patch("src.config_manager.config_manager")
    def test_get_config_with_invalid_json(self, mock_config_manager):
        """無効なJSONファイルの場合のテスト"""
        mock_config_manager.get.return_value = "INFO"
        result = get_config("log_level", "INFO")
        assert result == "INFO"
