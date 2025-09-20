"""
src/main.py のテスト
"""

import json
import os
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
import requests

from src.main import (
    check_config_changed,
    clear_logs_and_update_config,
    get_current_config_hash,
    get_onedrive_files,
    main,
    rebuild_skip_list,
    retry_with_backoff,
    run_transfer,
    transfer_file,
)


class TestRetryWithBackoff:
    """retry_with_backoff 関数のテスト"""

    def test_success_on_first_attempt(self):
        """検証対象: retry_with_backoff() 目的: 初回成功時の動作確認"""
        mock_func = Mock(return_value="success")
        result = retry_with_backoff(mock_func, max_retries=3, wait_sec=1, arg1="test")

        assert result == "success"
        mock_func.assert_called_once_with(arg1="test")

    def test_success_after_retries(self):
        """検証対象: retry_with_backoff() 目的: リトライ後成功時の動作確認"""
        mock_func = Mock(
            side_effect=[
                requests.exceptions.ConnectionError("network error"),
                "success",
            ]
        )

        with patch("time.sleep") as mock_sleep:
            result = retry_with_backoff(mock_func, max_retries=3, wait_sec=2)

        assert result == "success"
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once_with(2)

    def test_max_retries_exceeded(self):
        """検証対象: retry_with_backoff() 目的: 最大リトライ回数超過時の例外発生確認"""
        mock_func = Mock(
            side_effect=requests.exceptions.ConnectionError("persistent error")
        )

        with patch("time.sleep"):
            with pytest.raises(
                requests.exceptions.ConnectionError, match="persistent error"
            ):
                retry_with_backoff(mock_func, max_retries=2, wait_sec=1)

        assert mock_func.call_count == 2

    def test_non_retryable_exception(self):
        """検証対象: retry_with_backoff() 目的: リトライ対象外例外の即座な再発生確認"""
        mock_func = Mock(side_effect=ValueError("not retryable"))

        with pytest.raises(ValueError, match="not retryable"):
            retry_with_backoff(mock_func, max_retries=3, wait_sec=1)

        mock_func.assert_called_once()


class TestConfigHash:
    """設定ハッシュ関連のテスト"""

    @patch.dict(
        os.environ,
        {
            "SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME": "test@example.com",
            "SOURCE_ONEDRIVE_FOLDER_PATH": "test_folder",
            "DESTINATION_SHAREPOINT_SITE_ID": "site123",
            "DESTINATION_SHAREPOINT_DRIVE_ID": "drive456",
            "DESTINATION_SHAREPOINT_DOCLIB": "doclib789",
        },
    )
    def test_get_current_config_hash(self):
        """検証対象: get_current_config_hash() 目的: 設定ハッシュ値の生成確認"""
        hash_value = get_current_config_hash()

        assert isinstance(hash_value, str)
        assert len(hash_value) == 32  # MD5ハッシュの長さ

        # 同じ設定で再実行すると同じハッシュが生成される
        hash_value2 = get_current_config_hash()
        assert hash_value == hash_value2

    @patch.dict(os.environ, {})
    def test_get_current_config_hash_with_none_values(self):
        """検証対象: get_current_config_hash() 目的: 環境変数未設定時のハッシュ生成確認"""
        hash_value = get_current_config_hash()

        assert isinstance(hash_value, str)
        assert len(hash_value) == 32

    @patch("os.path.exists")
    def test_check_config_changed_no_hash_file(self, mock_exists):
        """検証対象: check_config_changed() 目的: ハッシュファイル未存在時の初回作成確認"""
        mock_exists.return_value = False

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs") as mock_makedirs:
                result = check_config_changed()

        assert result is False
        mock_makedirs.assert_called_once_with("logs", exist_ok=True)
        mock_file.assert_called_once_with("logs/config_hash.txt", "w")

    @patch("os.path.exists")
    def test_check_config_changed_same_hash(self, mock_exists):
        """検証対象: check_config_changed() 目的: 設定未変更時の動作確認"""
        mock_exists.return_value = True
        current_hash = get_current_config_hash()

        with patch("builtins.open", mock_open(read_data=current_hash)):
            result = check_config_changed()

        assert result is False

    @patch("os.path.exists")
    def test_check_config_changed_different_hash(self, mock_exists):
        """検証対象: check_config_changed() 目的: 設定変更検出時の動作確認"""
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data="old_hash_value")):
            result = check_config_changed()

        assert result is True


class TestClearLogsAndUpdateConfig:
    """ログクリア・設定更新のテスト"""

    @patch("src.main.get_config")
    @patch("src.main.get_onedrive_files_path")
    @patch("src.main.get_sharepoint_current_files_path")
    @patch("src.main.get_skip_list_path")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_clear_logs_and_update_config(
        self,
        mock_remove,
        mock_exists,
        mock_skip_list_path,
        mock_sharepoint_path,
        mock_onedrive_path,
        mock_get_config,
    ):
        """検証対象: clear_logs_and_update_config() 目的: ログファイル削除と設定更新確認"""
        # モックの設定
        mock_onedrive_path.return_value = "logs/onedrive_files.json"
        mock_sharepoint_path.return_value = "logs/sharepoint_files.json"
        mock_skip_list_path.return_value = "logs/skip_list.json"
        mock_get_config.return_value = "logs/transfer.log"
        mock_exists.return_value = True

        with patch("builtins.open", mock_open()) as mock_file:
            clear_logs_and_update_config()

        # ファイル削除の確認
        expected_files = [
            "logs/onedrive_files.json",
            "logs/sharepoint_files.json",
            "logs/skip_list.json",
            "logs/transfer.log",
        ]

        for file_path in expected_files:
            mock_remove.assert_any_call(file_path)

        # 設定ハッシュファイルの更新確認
        mock_file.assert_called_with("logs/config_hash.txt", "w")


class TestGetOneDriveFiles:
    """OneDriveファイル取得のテスト"""

    @patch("src.main.GraphTransferClient")
    @patch("os.path.exists")
    def test_get_onedrive_files_from_cache(self, mock_exists, mock_client):
        """検証対象: get_onedrive_files() 目的: キャッシュからのファイル読み込み確認"""
        mock_exists.return_value = True
        cached_files = [{"name": "test.txt", "path": "/test.txt"}]

        with patch("builtins.open", mock_open(read_data=json.dumps(cached_files))):
            result = get_onedrive_files(force_crawl=False)

        assert result == cached_files
        mock_client.assert_not_called()

    @patch("src.main.GraphTransferClient")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_get_onedrive_files_force_crawl(
        self, mock_makedirs, mock_exists, mock_client
    ):
        """検証対象: get_onedrive_files() 目的: 強制クロール時の新規取得確認"""
        mock_exists.return_value = True
        mock_files = [{"name": "new.txt", "path": "/new.txt"}]

        # GraphTransferClientのモック設定
        mock_instance = Mock()
        mock_instance.collect_file_targets_from_onedrive.return_value = mock_files
        mock_client.return_value = mock_instance

        with patch.dict(
            os.environ,
            {
                "CLIENT_ID": "test_id",
                "CLIENT_SECRET": "test_secret",
                "TENANT_ID": "test_tenant",
                "DESTINATION_SHAREPOINT_SITE_ID": "test_site",
                "DESTINATION_SHAREPOINT_DRIVE_ID": "test_drive",
                "SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME": "test@example.com",
            },
        ):
            with patch("builtins.open", mock_open()) as mock_file:
                result = get_onedrive_files(force_crawl=True)

        assert result == mock_files
        mock_instance.collect_file_targets_from_onedrive.assert_called_once()
        mock_file.assert_called()

    @patch("src.main.GraphTransferClient")
    def test_get_onedrive_files_missing_env_vars(self, mock_client):
        """検証対象: get_onedrive_files() 目的: 必須環境変数未設定時の空リスト返却確認"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_onedrive_files()

        assert result == []
        mock_client.assert_not_called()


class TestRebuildSkipList:
    """スキップリスト再構築のテスト"""

    @patch("src.main.create_skip_list_from_sharepoint")
    @patch("src.main.crawl_sharepoint")
    @patch("src.main.get_onedrive_files")
    @patch("os.path.exists")
    def test_rebuild_skip_list_with_provided_files(
        self,
        mock_exists,
        mock_get_onedrive,
        mock_crawl_sharepoint,
        mock_create_skip_list,
    ):
        """検証対象: rebuild_skip_list() 目的: 提供されたファイルリストでの再構築確認"""
        onedrive_files = [{"name": "file1.txt"}, {"name": "file2.txt"}]
        sharepoint_files = [{"name": "file1.txt"}]
        skip_list = [{"name": "file1.txt"}]

        # SharePointキャッシュファイルが存在しない場合をシミュレート
        mock_exists.return_value = False
        mock_crawl_sharepoint.return_value = sharepoint_files
        mock_create_skip_list.return_value = skip_list

        result = rebuild_skip_list(onedrive_files=onedrive_files)

        assert result == 1  # 2 - 1 = 1 (pending transfer count)
        mock_get_onedrive.assert_not_called()
        mock_crawl_sharepoint.assert_called_once()
        mock_create_skip_list.assert_called_once_with(onedrive_files, sharepoint_files)

    @patch("src.main.create_skip_list_from_sharepoint")
    @patch("src.main.crawl_sharepoint")
    @patch("src.main.get_onedrive_files")
    def test_rebuild_skip_list_without_provided_files(
        self, mock_get_onedrive, mock_crawl_sharepoint, mock_create_skip_list
    ):
        """検証対象: rebuild_skip_list() 目的: ファイルリスト未提供時の自動取得確認"""
        onedrive_files = [{"name": "file1.txt"}]
        sharepoint_files = []
        skip_list = []

        mock_get_onedrive.return_value = onedrive_files
        mock_crawl_sharepoint.return_value = sharepoint_files
        mock_create_skip_list.return_value = skip_list

        result = rebuild_skip_list()

        assert result == 1
        mock_get_onedrive.assert_called_once()


class TestTransferFile:
    """ファイル転送のテスト"""

    @patch("src.main.add_to_skip_list")
    @patch("src.main.log_transfer_success")
    @patch("src.main.log_transfer_start")
    @patch("src.main.get_skip_list_path")
    @patch("time.time")
    def test_transfer_file_success(
        self,
        mock_time,
        mock_skip_list_path,
        mock_log_start,
        mock_log_success,
        mock_add_skip,
    ):
        """検証対象: transfer_file() 目的: ファイル転送成功時の動作確認"""
        file_info = {"name": "test.txt", "path": "/test.txt"}
        mock_client = Mock()
        mock_client.upload_file_to_sharepoint.return_value = None
        mock_time.side_effect = [100.0, 105.0]  # start, end
        mock_skip_list_path.return_value = "logs/skip_list.json"

        with patch.dict(
            os.environ,
            {
                "SOURCE_ONEDRIVE_FOLDER_PATH": "source",
                "DESTINATION_SHAREPOINT_DOCLIB": "dest",
            },
        ):
            result = transfer_file(file_info, mock_client, retry_count=3, timeout=10)

        assert result is True
        mock_log_start.assert_called_once_with(file_info)
        mock_log_success.assert_called_once_with(file_info, elapsed=5.0)
        mock_add_skip.assert_called_once_with(file_info, "logs/skip_list.json")

    @patch("src.main.log_transfer_error")
    @patch("src.main.log_transfer_start")
    @patch("time.sleep")
    def test_transfer_file_failure_with_retries(
        self, mock_sleep, mock_log_start, mock_log_error
    ):
        """検証対象: transfer_file() 目的: 転送失敗時のリトライ動作確認"""
        file_info = {"name": "test.txt", "path": "/test.txt"}
        mock_client = Mock()
        mock_client.upload_file_to_sharepoint.side_effect = Exception("upload failed")

        with patch.dict(
            os.environ,
            {
                "SOURCE_ONEDRIVE_FOLDER_PATH": "source",
                "DESTINATION_SHAREPOINT_DOCLIB": "dest",
            },
        ):
            result = transfer_file(file_info, mock_client, retry_count=2, timeout=10)

        assert result is False
        assert mock_log_start.call_count == 2
        assert mock_log_error.call_count == 2
        mock_sleep.assert_called_once_with(1)


class TestRunTransfer:
    """転送実行のテスト"""

    @patch("src.main.ThreadPoolExecutor")
    @patch("src.main.load_skip_list")
    @patch("src.main.is_skipped")
    @patch("src.main.get_onedrive_files")
    @patch("src.main.GraphTransferClient")
    @patch("src.main.get_config")
    def test_run_transfer_success(
        self,
        mock_get_config,
        mock_client_class,
        mock_get_onedrive,
        mock_is_skipped,
        mock_load_skip,
        mock_executor_class,
    ):
        """検証対象: run_transfer() 目的: 転送処理の正常実行確認"""
        # モックの設定
        onedrive_files = [{"name": "file1.txt"}, {"name": "file2.txt"}]
        skip_list = [{"name": "file1.txt"}]

        mock_get_onedrive.return_value = onedrive_files
        mock_load_skip.return_value = skip_list
        mock_is_skipped.side_effect = lambda f, sl: f["name"] == "file1.txt"
        mock_get_config.side_effect = lambda key, default: {
            "max_parallel_transfers": 4,
            "retry_count": 3,
            "timeout_sec": 10,
        }.get(key, default)

        # ThreadPoolExecutorのモック
        mock_executor = MagicMock()
        mock_future = Mock()
        mock_future.result.return_value = True
        mock_executor.submit.return_value = mock_future
        mock_executor.__enter__.return_value = mock_executor
        mock_executor.__exit__.return_value = None
        mock_executor_class.return_value = mock_executor

        # as_completedのモック
        with patch("src.main.as_completed", return_value=[mock_future]):
            with patch.dict(
                os.environ,
                {
                    "CLIENT_ID": "test_id",
                    "CLIENT_SECRET": "test_secret",
                    "TENANT_ID": "test_tenant",
                    "DESTINATION_SHAREPOINT_SITE_ID": "test_site",
                    "DESTINATION_SHAREPOINT_DRIVE_ID": "test_drive",
                    "SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME": "test@example.com",
                },
            ):
                run_transfer(onedrive_files)

        # 1つのファイルのみが転送対象（file2.txt）
        mock_executor.submit.assert_called_once()

    def test_run_transfer_missing_env_vars(self):
        """検証対象: run_transfer() 目的: 必須環境変数未設定時のエラーハンドリング確認"""
        with patch.dict(os.environ, {}, clear=True):
            # エラーログが出力されるが例外は発生しない
            run_transfer()


class TestMain:
    """メイン関数のテスト"""

    @patch("src.main.rebuild_skip_list")
    @patch("src.main.get_onedrive_files")
    @patch("src.main.clear_logs_and_update_config")
    @patch("sys.argv", ["main.py", "--reset"])
    def test_main_reset_option(self, mock_clear_logs, mock_get_onedrive, mock_rebuild):
        """検証対象: main() 目的: --resetオプション時の動作確認"""
        mock_get_onedrive.return_value = [{"name": "test.txt"}]
        mock_rebuild.return_value = 5

        main()

        mock_clear_logs.assert_called_once()
        mock_get_onedrive.assert_called_once_with(force_crawl=True)
        mock_rebuild.assert_called_once()

    @patch("src.main.run_transfer")
    @patch("src.main.rebuild_skip_list")
    @patch("src.main.get_onedrive_files")
    @patch("src.main.clear_logs_and_update_config")
    @patch("sys.argv", ["main.py", "--full-rebuild"])
    def test_main_full_rebuild_option(
        self, mock_clear_logs, mock_get_onedrive, mock_rebuild, mock_run_transfer
    ):
        """検証対象: main() 目的: --full-rebuildオプション時の動作確認"""
        mock_get_onedrive.return_value = [{"name": "test.txt"}]
        mock_rebuild.return_value = 5

        main()

        mock_clear_logs.assert_called_once()
        mock_get_onedrive.assert_called_once_with(force_crawl=True)
        mock_rebuild.assert_called_once()
        mock_run_transfer.assert_called_once()

    @patch("src.main.run_transfer")
    @patch("src.main.rebuild_skip_list")
    @patch("src.main.get_onedrive_files")
    @patch("src.main.check_config_changed")
    @patch("os.path.exists")
    @patch("sys.argv", ["main.py"])
    def test_main_default_with_skip_list_exists(
        self,
        mock_exists,
        mock_config_changed,
        mock_get_onedrive,
        mock_rebuild,
        mock_run_transfer,
    ):
        """検証対象: main() 目的: デフォルト実行時（スキップリスト存在）の動作確認"""
        mock_config_changed.return_value = False
        mock_exists.return_value = True  # skip_list.json exists
        mock_get_onedrive.return_value = [{"name": "test.txt"}]

        main()

        mock_get_onedrive.assert_called_once_with()
        mock_rebuild.assert_not_called()  # スキップリストが存在するので再構築しない
        mock_run_transfer.assert_called_once()

    @patch("src.main.run_transfer")
    @patch("src.main.rebuild_skip_list")
    @patch("src.main.get_onedrive_files")
    @patch("src.main.check_config_changed")
    @patch("os.path.exists")
    @patch("sys.argv", ["main.py"])
    def test_main_default_without_skip_list(
        self,
        mock_exists,
        mock_config_changed,
        mock_get_onedrive,
        mock_rebuild,
        mock_run_transfer,
    ):
        """検証対象: main() 目的: デフォルト実行時（スキップリスト未存在）の動作確認"""
        mock_config_changed.return_value = False
        mock_exists.return_value = False  # skip_list.json does not exist
        mock_get_onedrive.return_value = [{"name": "test.txt"}]
        mock_rebuild.return_value = 5

        main()

        mock_get_onedrive.assert_called_once_with()
        mock_rebuild.assert_called_once()  # スキップリストが存在しないので自動再構築
        mock_run_transfer.assert_called_once()

    @patch("src.main.run_transfer")
    @patch("src.main.rebuild_skip_list")
    @patch("src.main.get_onedrive_files")
    @patch("src.main.clear_logs_and_update_config")
    @patch("src.main.check_config_changed")
    @patch("sys.argv", ["main.py"])
    def test_main_config_changed(
        self,
        mock_config_changed,
        mock_clear_logs,
        mock_get_onedrive,
        mock_rebuild,
        mock_run_transfer,
    ):
        """検証対象: main() 目的: 設定変更検出時の自動フルリビルド確認"""
        mock_config_changed.return_value = True
        mock_get_onedrive.return_value = [{"name": "test.txt"}]
        mock_rebuild.return_value = 5

        main()

        mock_clear_logs.assert_called_once()
        mock_get_onedrive.assert_called_once_with(force_crawl=True)
        mock_rebuild.assert_called_once()
        mock_run_transfer.assert_called_once()
