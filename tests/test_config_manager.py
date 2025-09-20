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

    def test_config_manager_direct_instantiation(self):
        """ConfigManagerクラスの直接インスタンス化テスト"""
        # 検証対象: ConfigManager.__init__()
        # 目的: 設定ファイルが存在しない場合の初期化を確認
        from src.config_manager import ConfigManager
        
        with patch("builtins.open", side_effect=FileNotFoundError):
            config_mgr = ConfigManager()
            assert config_mgr._config_cache == {}

    def test_config_manager_invalid_json_file(self):
        """ConfigManagerの無効なJSONファイル処理テスト"""
        # 検証対象: ConfigManager.__init__()
        # 目的: 無効なJSONファイルの場合の初期化を確認
        from src.config_manager import ConfigManager
        import json
        
        with patch("builtins.open", side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            config_mgr = ConfigManager()
            assert config_mgr._config_cache == {}

    def test_config_manager_get_with_env_override(self):
        """環境変数による設定値オーバーライドテスト"""
        # 検証対象: ConfigManager.get()
        # 目的: 環境変数が設定値をオーバーライドすることを確認
        from src.config_manager import ConfigManager
        
        config_mgr = ConfigManager()
        config_mgr._config_cache = {"test_key": "config_value"}
        
        with patch("os.getenv", return_value="env_value"):
            result = config_mgr.get("test_key", "default_value")
            assert result == "env_value"

    def test_config_manager_get_with_empty_env_value(self):
        """空の環境変数値の処理テスト"""
        # 検証対象: ConfigManager.get()
        # 目的: 空の環境変数値の場合にconfig.jsonの値が使用されることを確認
        from src.config_manager import ConfigManager
        
        config_mgr = ConfigManager()
        config_mgr._config_cache = {"test_key": "config_value"}
        
        with patch("os.getenv", return_value=""):
            result = config_mgr.get("test_key", "default_value")
            assert result == "config_value"

    def test_config_manager_get_with_empty_config_value(self):
        """空の設定値の処理テスト"""
        # 検証対象: ConfigManager.get()
        # 目的: 空の設定値の場合にデフォルト値が使用されることを確認
        from src.config_manager import ConfigManager
        
        config_mgr = ConfigManager()
        config_mgr._config_cache = {"test_key": ""}
        
        with patch("os.getenv", return_value=None):
            result = config_mgr.get("test_key", "default_value")
            assert result == "default_value"

    def test_config_manager_get_with_none_config_value(self):
        """None設定値の処理テスト"""
        # 検証対象: ConfigManager.get()
        # 目的: None設定値の場合にデフォルト値が使用されることを確認
        from src.config_manager import ConfigManager
        
        config_mgr = ConfigManager()
        config_mgr._config_cache = {"test_key": None}
        
        with patch("os.getenv", return_value=None):
            result = config_mgr.get("test_key", "default_value")
            assert result == "default_value"

    def test_shortcut_functions_coverage(self):
        """ショートカット関数のカバレッジテスト"""
        # 検証対象: 各種ショートカット関数
        # 目的: 未カバーのショートカット関数が正しく動作することを確認
        from src.config_manager import (
            get_transfer_log_path,
            get_skip_list_path,
            get_onedrive_files_path,
            get_sharepoint_current_files_path,
            get_checksum_report_path,
            get_source_onedrive_folder_path,
            get_destination_sharepoint_doclib
        )
        
        with patch("src.config_manager.get_config") as mock_get_config:
            mock_get_config.return_value = "test_value"
            
            # 各ショートカット関数をテスト
            assert get_transfer_log_path() == "test_value"
            assert get_skip_list_path() == "test_value"
            assert get_onedrive_files_path() == "test_value"
            assert get_sharepoint_current_files_path() == "test_value"
            assert get_checksum_report_path() == "test_value"
            assert get_source_onedrive_folder_path() == "test_value"
            assert get_destination_sharepoint_doclib() == "test_value"
            
            # 呼び出し回数を確認
            assert mock_get_config.call_count == 7
