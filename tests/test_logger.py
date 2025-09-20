"""
loggerモジュールのテスト
"""

from unittest.mock import patch

from src.logger import (
    log_transfer_error,
    log_transfer_skip,
    log_transfer_start,
    log_transfer_success,
)


class TestLogger:
    """loggerモジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前処理"""
        self.test_file_info = {
            "name": "test_file.txt",
            "path": "/test/path/test_file.txt",
            "size": 1024,
            "lastModifiedDateTime": "2024-01-01T00:00:00Z",
        }

    @patch("src.logger.logger")
    def test_log_transfer_start(self, mock_logger):
        """転送開始ログテスト"""
        log_transfer_start(self.test_file_info)
        mock_logger.info.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_success(self, mock_logger):
        """転送成功ログテスト"""
        log_transfer_success(self.test_file_info)
        mock_logger.info.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_success_with_elapsed(self, mock_logger):
        """転送成功ログテスト（経過時間付き）"""
        log_transfer_success(self.test_file_info, elapsed=1.5)
        mock_logger.info.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_error(self, mock_logger):
        """転送エラーログテスト"""
        error_message = "Test error message"
        log_transfer_error(self.test_file_info, error_message)
        mock_logger.error.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_error_with_retry(self, mock_logger):
        """転送エラーログテスト（リトライ回数付き）"""
        error_message = "Test error message"
        log_transfer_error(self.test_file_info, error_message, retry_count=3)
        mock_logger.error.assert_called_once()

    @patch("src.logger.logger")
    def test_log_transfer_skip(self, mock_logger):
        """転送スキップログテスト"""
        log_transfer_skip(self.test_file_info)
        mock_logger.info.assert_called_once()
