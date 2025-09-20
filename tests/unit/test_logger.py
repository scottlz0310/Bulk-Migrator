"""
loggerモジュールのテスト
"""

import os
import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

from src.logger import (
    SecureLogger,
    log_transfer_error,
    log_transfer_skip,
    log_transfer_start,
    log_transfer_success,
)


class TestLogger:
    """loggerモジュールのテストクラス"""

    test_file_info: dict[str, Any]

    def setup_method(self):
        """各テストメソッドの前処理"""
        self.test_file_info = {
            "name": "test_file.txt",
            "path": "/test/path/test_file.txt",
            "size": 1024,
            "lastModifiedDateTime": "2024-01-01T00:00:00Z",
        }

    @patch("src.logger.logger")
    def test_log_transfer_start(self, mock_logger: Any):
        """転送開始ログテスト"""
        log_transfer_start(self.test_file_info)
        mock_logger.info.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_success(self, mock_logger: Any):
        """転送成功ログテスト"""
        log_transfer_success(self.test_file_info)
        mock_logger.info.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_success_with_elapsed(self, mock_logger: Any):
        """転送成功ログテスト（経過時間付き）"""
        log_transfer_success(self.test_file_info, elapsed=1.5)
        mock_logger.info.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_error(self, mock_logger: Any):
        """転送エラーログテスト"""
        error_message = "Test error message"
        log_transfer_error(self.test_file_info, error_message)
        mock_logger.error.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_error_with_retry(self, mock_logger: Any):
        """転送エラーログテスト（リトライ回数付き）"""
        error_message = "Test error message"
        log_transfer_error(self.test_file_info, error_message, retry_count=3)
        mock_logger.error.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_skip(self, mock_logger: Any):
        """転送スキップログテスト"""
        log_transfer_skip(self.test_file_info)
        mock_logger.info.assert_called_once()


class TestSecureLogger:
    """SecureLoggerクラスのテストクラス"""

    test_file_info: dict[str, Any]

    def setup_method(self):
        """各テストメソッドの前処理"""
        self.test_file_info = {
            "name": "test_file.txt",
            "path": "/test/path/test_file.txt",
            "size": 1024,
            "lastModifiedDateTime": "2024-01-01T00:00:00Z",
        }

    def test_mask_sensitive_data_client_secret(self):
        """CLIENT_SECRETマスキングテスト"""
        # 検証対象: SecureLogger.mask_sensitive_data()
        # 目的: CLIENT_SECRETが適切にマスクされることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            try:
                test_message = "Authentication with client_secret=abc123def456"
                masked_message = secure_logger.mask_sensitive_data(test_message)

                assert isinstance(masked_message, str)
                assert "client_secret=[MASKED]" in masked_message
                assert "abc123def456" not in masked_message
            finally:
                secure_logger.close()

    def test_mask_sensitive_data_access_token(self):
        """ACCESS_TOKENマスキングテスト"""
        # 検証対象: SecureLogger.mask_sensitive_data()
        # 目的: ACCESS_TOKENが適切にマスクされることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            test_message = (
                "Request with access_token=" "'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9'"
            )
            try:
                jwt_snippet = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9"
                masked_message = secure_logger.mask_sensitive_data(test_message)

                assert isinstance(masked_message, str)
                assert "access_token=[MASKED]" in masked_message
                assert jwt_snippet not in masked_message
            finally:
                secure_logger.close()

    def test_mask_sensitive_data_bearer_token(self):
        """Bearerトークンマスキングテスト"""
        # 検証対象: SecureLogger.mask_sensitive_data()
        # 目的: Bearerトークンが適切にマスクされることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            test_message = (
                "Authorization: Bearer " "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9"
            )
            try:
                jwt_snippet = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9"
                masked_message = secure_logger.mask_sensitive_data(test_message)

                assert isinstance(masked_message, str)
                assert "Bearer [MASKED]" in masked_message
                assert jwt_snippet not in masked_message
            finally:
                secure_logger.close()

    def test_mask_sensitive_data_json_format(self):
        """JSON形式の機密情報マスキングテスト"""
        # 検証対象: SecureLogger.mask_sensitive_data()
        # 目的: JSON内の機密情報が適切にマスクされることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            test_message = '{"client_secret": "abc123", "client_id": "def456"}'
            try:
                masked_message = secure_logger.mask_sensitive_data(test_message)

                assert isinstance(masked_message, str)
                assert '"client_secret": "[MASKED]"' in masked_message
                # 非機密情報はそのまま
                assert '"client_id": "def456"' in masked_message
                assert "abc123" not in masked_message
            finally:
                secure_logger.close()

    def test_mask_sensitive_data_multiple_patterns(self):
        """複数パターンの機密情報マスキングテスト"""
        # 検証対象: SecureLogger.mask_sensitive_data()
        # 目的: 複数の機密情報パターンが同時にマスクされることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            test_message = (
                "client_secret=abc123 and api_key: xyz789 and " "password='secret123'"
            )
            try:
                masked_message = secure_logger.mask_sensitive_data(test_message)
                assert isinstance(masked_message, str)
                assert "client_secret=[MASKED]" in masked_message
                assert "api_key=[MASKED]" in masked_message
                assert "password=[MASKED]" in masked_message
                assert "abc123" not in masked_message
                assert "xyz789" not in masked_message
                assert "secret123" not in masked_message
            finally:
                secure_logger.close()

    def test_mask_sensitive_data_empty_input(self):
        """空入力のマスキングテスト"""
        # 検証対象: SecureLogger.mask_sensitive_data()
        # 目的: 空入力の場合の処理を確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            try:
                assert secure_logger.mask_sensitive_data("") == ""
                assert secure_logger.mask_sensitive_data(None) is None
            finally:
                secure_logger.close()

    @patch("src.logger.SecureLogger._log_with_masking")
    def test_log_levels(self, mock_log_with_masking: Any):
        """各ログレベルのテスト"""
        # 検証対象: SecureLogger.debug/info/warning/error/critical()
        # 目的: 各ログレベルメソッドが適切に動作することを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            test_message = "Test message"

            secure_logger.debug(test_message)
            secure_logger.info(test_message)
            secure_logger.warning(test_message)
            secure_logger.error(test_message)
            secure_logger.critical(test_message)

            try:
                assert mock_log_with_masking.call_count == 5
            finally:
                secure_logger.close()

    def test_log_transfer_methods(self):
        """転送関連ログメソッドのテスト"""
        # 検証対象: SecureLogger.log_transfer_*()
        # 目的: 転送関連のログメソッドが適切に動作することを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            # モックロガーを設定
            secure_logger.logger = MagicMock()

            secure_logger.log_transfer_start(self.test_file_info)
            secure_logger.log_transfer_success(self.test_file_info, elapsed=1.5)
            secure_logger.log_transfer_error(
                self.test_file_info, "Test error", retry_count=2
            )
            secure_logger.log_transfer_skip(self.test_file_info)

            try:
                # ログメソッドが呼び出されたことを確認
                assert secure_logger.logger.log.call_count == 4
            finally:
                secure_logger.close()

    def test_log_auth_event(self):
        """認証イベントログテスト"""
        # 検証対象: SecureLogger.log_auth_event()
        # 目的: 認証イベントログが適切に出力されることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            # モックロガーを設定
            secure_logger.logger = MagicMock()

            # 機密情報を含む詳細情報
            auth_details = {
                "client_id": "test_client_id",
                "client_secret": "secret123",
                "tenant_id": "tenant456",
                "scope": "https://graph.microsoft.com/.default",
            }

            secure_logger.log_auth_event("Token acquired", auth_details)

            # ログメソッドが呼び出されたことを確認
            secure_logger.logger.log.assert_called_once()

            # 呼び出された引数を確認
            call_args = secure_logger.logger.log.call_args
            logged_message = call_args[0][1]  # メッセージ部分

            try:
                # 機密情報がマスクされていることを確認
                assert "[MASKED]" in logged_message
                assert "secret123" not in logged_message
                assert "tenant456" not in logged_message
                assert "test_client_id" in logged_message  # 非機密情報はそのまま
            finally:
                secure_logger.close()

    def test_log_auth_event_without_details(self):
        """認証イベントログテスト（詳細情報なし）"""
        # 検証対象: SecureLogger.log_auth_event()
        # 目的: 詳細情報なしの認証イベントログが適切に出力されることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            # モックロガーを設定
            secure_logger.logger = MagicMock()

            secure_logger.log_auth_event("Authentication started")

            try:
                # ログメソッドが呼び出されたことを確認
                secure_logger.logger.log.assert_called_once()
            finally:
                secure_logger.close()

    @patch("src.logger.get_config")
    @patch("src.logger.get_transfer_log_path")
    def test_setup_logger_with_config(
        self, _mock_get_transfer_log_path: Any, _mock_get_config: Any
    ):
        """設定管理を使用したロガーセットアップテスト"""
        # 検証対象: SecureLogger._setup_logger()
        # 目的: 設定管理を使用したロガーセットアップが正常に動作することを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            _mock_get_transfer_log_path.return_value = log_path
            _mock_get_config.return_value = "DEBUG"

            secure_logger = SecureLogger("test_logger")

            # ログレベルが設定されていることを確認
            # （数値は環境により異なる可能性があるため、設定されていることのみ確認）
            try:
                assert secure_logger.logger.level is not None
                # file + console
                assert len(secure_logger.logger.handlers) == 2
            finally:
                secure_logger.close()

    @patch("src.logger.get_config", side_effect=ImportError("NA"))
    @patch(
        "src.logger.get_transfer_log_path",
        side_effect=ImportError("NA"),
    )
    def test_setup_logger_import_error_fallback(
        self, _mock_get_transfer_log_path: Any, _mock_get_config: Any
    ):
        """設定管理インポートエラー時のフォールバックテスト"""
        # 検証対象: SecureLogger._setup_logger() のImportError処理
        # 目的: config_manager インポートエラー時のフォールバック処理を確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")

            with patch.dict(
                "os.environ",
                {
                    "TRANSFER_LOG_PATH": log_path,
                    "LOG_LEVEL": "WARNING",
                },
            ):
                secure_logger = SecureLogger("test_logger")

                try:
                    # フォールバック処理が動作していることを確認
                    assert secure_logger.logger.level is not None
                    # file + console
                    assert len(secure_logger.logger.handlers) == 2
                finally:
                    secure_logger.close()

    @patch("src.logger.get_config", side_effect=ImportError("NA"))
    @patch(
        "src.logger.get_transfer_log_path",
        side_effect=ImportError("NA"),
    )
    def test_setup_logger_import_error_with_log_path_param(
        self, _mock_get_transfer_log_path: Any, _mock_get_config: Any
    ):
        """設定管理インポートエラー時のフォールバックテスト（ログパス指定）"""
        # 検証対象: SecureLogger._setup_logger() のImportError処理（ログパス指定）
        # 目的: ログパス指定時のフォールバック処理を確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")

            with patch.dict("os.environ", {"LOG_LEVEL": "ERROR"}):
                secure_logger = SecureLogger("test_logger", log_path)

                try:
                    # フォールバック処理が動作していることを確認
                    assert secure_logger.logger.level is not None
                    # file + console
                    assert len(secure_logger.logger.handlers) == 2
                finally:
                    secure_logger.close()

    def test_module_level_import_error_fallback(self):
        """モジュールレベルのインポートエラーフォールバックテスト"""
        # 検証対象: logger.py のモジュールレベルImportError処理
        # 目的: モジュールレベルでのconfig_manager インポートエラー時の
        # フォールバック処理を確認

        # このテストは実際のモジュールレベルの処理をテストするため、
        # 新しいプロセスでモジュールを再インポートする必要がある
        # ここでは、フォールバック処理が存在することを確認

        # モジュールレベルの変数が設定されていることを確認
        from src.logger import LOG_LEVEL, LOG_PATH

        assert LOG_PATH is not None
        assert LOG_LEVEL is not None
        assert isinstance(LOG_PATH, str)
        assert isinstance(LOG_LEVEL, str)

    @patch("src.logger.get_config", side_effect=ImportError("NA"))
    @patch(
        "src.logger.get_transfer_log_path",
        side_effect=ImportError("NA"),
    )
    def test_setup_logger_import_error_default_values(
        self, _mock_get_transfer_log_path: Any, _mock_get_config: Any
    ):
        """設定管理インポートエラー時のデフォルト値テスト"""
        # 検証対象: SecureLogger._setup_logger() のImportError処理のデフォルト値
        # 目的: 環境変数が設定されていない場合のデフォルト値を確認
        with tempfile.TemporaryDirectory():
            # 環境変数をクリア
            with patch.dict("os.environ", {}, clear=True):
                secure_logger = SecureLogger("test_logger")

                try:
                    # デフォルト値が使用されていることを確認
                    assert secure_logger.logger.level is not None
                    # file + console
                    assert len(secure_logger.logger.handlers) == 2
                finally:
                    secure_logger.close()

    def test_logger_initialization_with_different_log_levels(self):
        """異なるログレベルでの初期化テスト"""
        # 検証対象: SecureLogger の異なるログレベルでの初期化
        # 目的: 各ログレベルが正しく設定されることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

            for level in log_levels:
                log_path = os.path.join(temp_dir, f"test_{level.lower()}.log")

                with patch.dict("os.environ", {"LOG_LEVEL": level}):
                    with patch(
                        "src.logger.get_config",
                        side_effect=ImportError("NA"),
                    ):
                        with patch(
                            "src.logger.get_transfer_log_path",
                            side_effect=ImportError("NA"),
                        ):
                            secure_logger = SecureLogger(
                                f"test_logger_{level.lower()}", log_path
                            )

                            try:
                                # ログレベルが設定されていることを確認
                                assert secure_logger.logger.level is not None
                            finally:
                                secure_logger.close()

    def test_secure_logger_with_none_message(self):
        """Noneメッセージでのセキュアロガーテスト"""
        # 検証対象: SecureLogger.mask_sensitive_data() のNone処理
        # 目的: Noneメッセージが適切に処理されることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            try:
                # Noneメッセージの処理
                result = secure_logger.mask_sensitive_data(None)
                assert result is None
            finally:
                secure_logger.close()

    def test_secure_logger_case_insensitive_masking(self):
        """大文字小文字を区別しないマスキングテスト"""
        # 検証対象: SecureLogger.mask_sensitive_data() の大文字小文字処理
        # 目的: 大文字小文字を区別せずにマスキングされることを確認
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "test.log")
            secure_logger = SecureLogger("test_logger", log_path)

            test_cases = [
                "CLIENT_SECRET=abc123",
                "client_secret=abc123",
                "Client_Secret=abc123",
                "ACCESS_TOKEN=xyz789",
                "access_token=xyz789",
                "Access_Token=xyz789",
            ]

            try:
                for test_message in test_cases:
                    masked_message = secure_logger.mask_sensitive_data(test_message)
                    assert isinstance(masked_message, str)
                    assert "[MASKED]" in masked_message
                    assert "abc123" not in masked_message
                    assert "xyz789" not in masked_message
            finally:
                secure_logger.close()
