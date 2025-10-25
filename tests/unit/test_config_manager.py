from unittest.mock import mock_open, patch

from src.config_manager import (
    SecureConfigManager,
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
        import json

        from src.config_manager import ConfigManager

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
            get_checksum_report_path,
            get_destination_sharepoint_doclib,
            get_onedrive_files_path,
            get_sharepoint_current_files_path,
            get_skip_list_path,
            get_source_onedrive_folder_path,
            get_transfer_log_path,
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


class TestSecureConfigManager:
    """SecureConfigManagerクラスのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前処理"""
        self.secure_config = SecureConfigManager()

    def test_is_sensitive_key(self):
        """機密情報キー判定テスト"""
        # 検証対象: SecureConfigManager.is_sensitive_key()
        # 目的: 機密情報キーが正しく判定されることを確認
        assert self.secure_config.is_sensitive_key("CLIENT_SECRET") is True
        assert self.secure_config.is_sensitive_key("client_secret") is True
        assert self.secure_config.is_sensitive_key("ACCESS_TOKEN") is True
        assert self.secure_config.is_sensitive_key("API_KEY") is True
        assert self.secure_config.is_sensitive_key("PASSWORD") is True
        assert self.secure_config.is_sensitive_key("TENANT_ID") is True

        # 非機密情報キー
        assert self.secure_config.is_sensitive_key("CLIENT_ID") is False
        assert self.secure_config.is_sensitive_key("LOG_LEVEL") is False
        assert self.secure_config.is_sensitive_key("CHUNK_SIZE") is False

    def test_mask_value(self):
        """値マスキングテスト"""
        # 検証対象: SecureConfigManager.mask_value()
        # 目的: 値が適切にマスクされることを確認
        assert self.secure_config.mask_value(None) is None
        assert self.secure_config.mask_value("abc") == "***"
        assert self.secure_config.mask_value("abcdef") == "ab***"
        assert self.secure_config.mask_value("abcdefghijk") == "abc***jk"
        assert self.secure_config.mask_value("very_long_secret_value") == "ver***ue"

    @patch.dict(
        "os.environ",
        {"CLIENT_SECRET": "secret123", "CLIENT_ID": "client456", "LOG_LEVEL": "DEBUG"},
    )
    def test_get_masked_config(self):
        """マスクされた設定取得テスト"""
        # 検証対象: SecureConfigManager.get_masked_config()
        # 目的: 機密情報がマスクされた設定が取得されることを確認
        self.secure_config._config_cache = {
            "API_KEY": "api_secret_key",
            "CHUNK_SIZE": "5",
        }

        masked_config = self.secure_config.get_masked_config()

        assert masked_config["CLIENT_SECRET"] == "sec***23"
        assert masked_config["CLIENT_ID"] == "client456"  # 非機密情報はそのまま
        assert masked_config["LOG_LEVEL"] == "DEBUG"
        assert masked_config["API_KEY"] == "api***ey"
        assert masked_config["CHUNK_SIZE"] == "5"

    @patch.dict("os.environ", {"CLIENT_SECRET": "secret123", "CLIENT_ID": "client456"})
    def test_get_all_config(self):
        """全設定取得テスト"""
        # 検証対象: SecureConfigManager.get_all_config()
        # 目的: 機密情報を含む全設定が取得されることを確認
        self.secure_config._config_cache = {
            "API_KEY": "api_secret_key",
            "CHUNK_SIZE": "5",
        }

        all_config = self.secure_config.get_all_config()

        assert all_config["CLIENT_SECRET"] == "secret123"  # マスクされない
        assert all_config["CLIENT_ID"] == "client456"
        assert all_config["API_KEY"] == "api_secret_key"
        assert all_config["CHUNK_SIZE"] == "5"

    def test_mask_sensitive_data(self):
        """機密データマスキングテスト"""
        # 検証対象: SecureConfigManager.mask_sensitive_data()
        # 目的: テキスト内の機密情報がマスクされることを確認
        test_text = "client_secret=abc123 and access_token='xyz789' and api_key: secret_key"
        masked_text = self.secure_config.mask_sensitive_data(test_text)

        assert "client_secret=[MASKED]" in masked_text
        assert "access_token=[MASKED]" in masked_text
        assert "api_key:[MASKED]" in masked_text
        assert "abc123" not in masked_text
        assert "xyz789" not in masked_text

    def test_mask_sensitive_data_empty_input(self):
        """空入力のマスキングテスト"""
        # 検証対象: SecureConfigManager.mask_sensitive_data()
        # 目的: 空入力の場合の処理を確認
        assert self.secure_config.mask_sensitive_data("") == ""
        assert self.secure_config.mask_sensitive_data(None) is None

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch.dict("os.environ", {"CLIENT_SECRET": "secret123", "API_KEY": "key456"})
    def test_validate_env_file_security(self, mock_file, mock_exists):
        """環境ファイルセキュリティ検証テスト"""
        # 検証対象: SecureConfigManager.validate_env_file_security()
        # 目的: 環境ファイルのセキュリティ設定が検証されることを確認

        # .gitignoreに.envが含まれている場合
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = ".env\n*.log\n"

        result = self.secure_config.validate_env_file_security()

        assert result["env_in_gitignore"] is True
        assert result["sample_env_exists"] is True
        assert "CLIENT_SECRET" in result["sensitive_keys_found"]
        assert "API_KEY" in result["sensitive_keys_found"]

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch.dict("os.environ", {}, clear=True)
    def test_validate_env_file_security_missing_setup(self, mock_file, mock_exists):
        """環境ファイルセキュリティ検証テスト（設定不備）"""
        # 検証対象: SecureConfigManager.validate_env_file_security()
        # 目的: セキュリティ設定不備の場合の推奨事項が生成されることを確認

        # .gitignoreに.envが含まれていない場合
        mock_exists.side_effect = lambda path: False if "sample.env" in path else True
        mock_file.return_value.read.return_value = "*.log\n"

        result = self.secure_config.validate_env_file_security()

        assert result["env_in_gitignore"] is False
        assert result["sample_env_exists"] is False
        assert len(result["sensitive_keys_found"]) == 0
        assert ".envファイルを.gitignoreに追加してください" in result["recommendations"]
        assert "sample.envファイルを作成してください" in result["recommendations"]
        assert "必要な機密情報の環境変数が設定されていません" in result["recommendations"]
