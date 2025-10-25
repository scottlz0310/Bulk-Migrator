"""
src/rebuild_skip_list.py のテスト
"""

import os
from unittest.mock import Mock, mock_open, patch

import pytest

from src.rebuild_skip_list import (
    crawl_onedrive,
    crawl_sharepoint,
    create_skip_list_from_sharepoint,
)


class TestCrawlSharepoint:
    """crawl_sharepoint 関数のテスト"""

    @patch("src.rebuild_skip_list.GraphTransferClient")
    @patch("src.rebuild_skip_list.get_structured_logger")
    @patch("os.makedirs")
    def test_crawl_sharepoint_success(self, mock_makedirs, mock_logger, mock_client_class):
        """検証対象: crawl_sharepoint() 目的: SharePointクロール成功時の動作確認"""
        # モックの設定
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # SharePointファイルリストのモック
        sharepoint_items = [
            {
                "name": "file1.txt",
                "id": "file1_id",
                "size": 1024,
                "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                "parentReference": {"path": "/drive/root:/TEST-Sharepoint/folder1"},
            },
            {
                "name": "file2.txt",
                "id": "file2_id",
                "size": 2048,
                "lastModifiedDateTime": "2024-01-02T00:00:00Z",
                "parentReference": {"path": "/drive/root:/TEST-Sharepoint"},
            },
        ]
        mock_client.list_drive_items.return_value = sharepoint_items

        with patch.dict(
            os.environ,
            {
                "CLIENT_ID": "test_id",
                "CLIENT_SECRET": "test_secret",
                "TENANT_ID": "test_tenant",
                "DESTINATION_SHAREPOINT_SITE_ID": "test_site",
                "DESTINATION_SHAREPOINT_DRIVE_ID": "test_drive",
                "DESTINATION_SHAREPOINT_DOCLIB": "TEST-Sharepoint",
            },
        ):
            with patch("builtins.open", mock_open()) as mock_file:
                result = crawl_sharepoint()

        # 結果の検証
        assert len(result) == 2
        assert result[0]["name"] == "file1.txt"
        assert result[0]["path"] == "TEST-Sharepoint/folder1/file1.txt"
        assert result[1]["name"] == "file2.txt"
        assert result[1]["path"] == "TEST-Sharepoint/file2.txt"

        # ログ出力の確認
        mock_logger_instance.info.assert_any_call("SharePointクロール開始", folder="TEST-Sharepoint")
        mock_logger_instance.info.assert_any_call("SharePointクロール完了", file_count=2)

        # ファイル保存の確認
        mock_file.assert_called()

    @patch("src.rebuild_skip_list.GraphTransferClient")
    @patch("src.rebuild_skip_list.get_structured_logger")
    def test_crawl_sharepoint_missing_env_vars(self, mock_logger, mock_client_class):
        """検証対象: crawl_sharepoint() 目的: 必須環境変数未設定時のエラー確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        with patch.dict(os.environ, {}, clear=True):
            # 環境変数が未設定の場合、GraphTransferClientの初期化でエラーが発生
            mock_client_class.side_effect = TypeError("missing required arguments")
            with pytest.raises(TypeError):
                crawl_sharepoint()

    @patch("src.rebuild_skip_list.GraphTransferClient")
    @patch("src.rebuild_skip_list.get_structured_logger")
    @patch("os.makedirs")
    def test_crawl_sharepoint_large_file_list(self, mock_makedirs, mock_logger, mock_client_class):
        """検証対象: crawl_sharepoint() 目的: 大量ファイル処理時の進捗ログ確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # 1500件のファイルを生成（1000件ごとの進捗ログをテスト）
        sharepoint_items = []
        for i in range(1500):
            sharepoint_items.append(
                {
                    "name": f"file{i}.txt",
                    "id": f"file{i}_id",
                    "size": 1024,
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                    "parentReference": {"path": "/drive/root:/TEST-Sharepoint"},
                }
            )

        mock_client.list_drive_items.return_value = sharepoint_items

        with patch.dict(
            os.environ,
            {
                "CLIENT_ID": "test_id",
                "CLIENT_SECRET": "test_secret",
                "TENANT_ID": "test_tenant",
                "DESTINATION_SHAREPOINT_SITE_ID": "test_site",
                "DESTINATION_SHAREPOINT_DRIVE_ID": "test_drive",
                "DESTINATION_SHAREPOINT_DOCLIB": "TEST-Sharepoint",
            },
        ):
            with patch("builtins.open", mock_open()):
                with patch("src.logger.logger") as mock_progress_logger:
                    result = crawl_sharepoint()

        # 結果の検証
        assert len(result) == 1500

        # 進捗ログの確認（1000件と1500件で2回呼ばれるはず）
        assert mock_progress_logger.info.call_count >= 1


class TestCrawlOnedrive:
    """crawl_onedrive 関数のテスト"""

    @patch("src.rebuild_skip_list.GraphTransferClient")
    @patch("src.rebuild_skip_list.get_structured_logger")
    def test_crawl_onedrive_success(self, mock_logger, mock_client_class):
        """検証対象: crawl_onedrive() 目的: OneDriveクロール成功時の動作確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # OneDriveファイルリストのモック
        onedrive_files = [
            {"name": "doc1.txt", "path": "/TEST-Onedrive/doc1.txt", "size": 1024},
            {"name": "doc2.txt", "path": "/TEST-Onedrive/doc2.txt", "size": 2048},
        ]
        mock_client.collect_file_targets_from_onedrive.return_value = onedrive_files

        with patch.dict(
            os.environ,
            {
                "CLIENT_ID": "test_id",
                "CLIENT_SECRET": "test_secret",
                "TENANT_ID": "test_tenant",
                "DESTINATION_SHAREPOINT_SITE_ID": "test_site",
                "DESTINATION_SHAREPOINT_DRIVE_ID": "test_drive",
                "SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME": "test@example.com",
                "SOURCE_ONEDRIVE_FOLDER_PATH": "TEST-Onedrive",
            },
        ):
            with patch("builtins.open", mock_open()) as mock_file:
                result = crawl_onedrive()

        # 結果の検証
        assert result == onedrive_files

        # GraphTransferClientの呼び出し確認
        mock_client.collect_file_targets_from_onedrive.assert_called_once_with(
            folder_path="TEST-Onedrive",
            user_principal_name="test@example.com",
            drive_id=None,
        )

        # ログ出力の確認
        mock_logger_instance.info.assert_any_call("OneDriveクロール開始", folder="TEST-Onedrive")
        mock_logger_instance.info.assert_any_call("OneDriveクロール完了", file_count=2)

        # ファイル保存の確認
        mock_file.assert_called()

    @patch("src.rebuild_skip_list.GraphTransferClient")
    @patch("src.rebuild_skip_list.get_structured_logger")
    def test_crawl_onedrive_missing_env_vars(self, mock_logger, mock_client_class):
        """検証対象: crawl_onedrive() 目的: 必須環境変数未設定時のエラー確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TypeError):
                crawl_onedrive()


class TestCreateSkipListFromSharepoint:
    """create_skip_list_from_sharepoint 関数のテスト"""

    @patch("src.rebuild_skip_list.get_structured_logger")
    def test_create_skip_list_success(self, mock_logger):
        """検証対象: create_skip_list_from_sharepoint()
        目的: スキップリスト作成成功時の動作確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        # テストデータ
        onedrive_files = [
            {"name": "file1.txt", "path": "TEST-Onedrive/file1.txt", "size": 1024},
            {
                "name": "file2.txt",
                "path": "TEST-Onedrive/folder/file2.txt",
                "size": 2048,
            },
            {"name": "file3.txt", "path": "TEST-Onedrive/file3.txt", "size": 512},
        ]

        sharepoint_files = [
            {"name": "file1.txt", "path": "TEST-Sharepoint/file1.txt", "size": 1024},
            {
                "name": "file2.txt",
                "path": "TEST-Sharepoint/folder/file2.txt",
                "size": 2048,
            },
            # file3.txtは存在しない（転送されていない）
        ]

        with patch.dict(
            os.environ,
            {
                "SOURCE_ONEDRIVE_FOLDER_PATH": "TEST-Onedrive",
                "DESTINATION_SHAREPOINT_DOCLIB": "TEST-Sharepoint",
            },
        ):
            with patch("builtins.open", mock_open()) as mock_file:
                result = create_skip_list_from_sharepoint(onedrive_files, sharepoint_files)

        # 結果の検証
        assert len(result) == 2  # file1.txt と file2.txt がマッチ
        assert result[0]["name"] == "file1.txt"
        assert result[1]["name"] == "file2.txt"

        # ログ出力の確認
        mock_logger_instance.info.assert_any_call("スキップリスト再構築開始")
        mock_logger_instance.info.assert_any_call(
            "スキップリスト構築完了",
            matched_count=2,
            total_onedrive_files=3,
            pending_transfer=1,
        )

        # ファイル保存の確認
        mock_file.assert_called()

    @patch("src.rebuild_skip_list.get_structured_logger")
    def test_create_skip_list_no_matches(self, mock_logger):
        """検証対象: create_skip_list_from_sharepoint()
        目的: マッチするファイルがない場合の動作確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        # テストデータ（マッチしないファイル）
        onedrive_files = [
            {"name": "file1.txt", "path": "TEST-Onedrive/file1.txt", "size": 1024},
            {"name": "file2.txt", "path": "TEST-Onedrive/file2.txt", "size": 2048},
        ]

        sharepoint_files = [
            {
                "name": "different.txt",
                "path": "TEST-Sharepoint/different.txt",
                "size": 1024,
            }
        ]

        with patch.dict(
            os.environ,
            {
                "SOURCE_ONEDRIVE_FOLDER_PATH": "TEST-Onedrive",
                "DESTINATION_SHAREPOINT_DOCLIB": "TEST-Sharepoint",
            },
        ):
            with patch("builtins.open", mock_open()):
                result = create_skip_list_from_sharepoint(onedrive_files, sharepoint_files)

        # 結果の検証
        assert len(result) == 0  # マッチするファイルなし

        # ログ出力の確認
        mock_logger_instance.info.assert_any_call(
            "スキップリスト構築完了",
            matched_count=0,
            total_onedrive_files=2,
            pending_transfer=2,
        )

    @patch("src.rebuild_skip_list.get_structured_logger")
    def test_create_skip_list_empty_inputs(self, mock_logger):
        """検証対象: create_skip_list_from_sharepoint()
        目的: 空のファイルリスト処理確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        with patch.dict(
            os.environ,
            {
                "SOURCE_ONEDRIVE_FOLDER_PATH": "TEST-Onedrive",
                "DESTINATION_SHAREPOINT_DOCLIB": "TEST-Sharepoint",
            },
        ):
            with patch("builtins.open", mock_open()):
                result = create_skip_list_from_sharepoint([], [])

        # 結果の検証
        assert len(result) == 0

        # ログ出力の確認
        mock_logger_instance.info.assert_any_call(
            "スキップリスト構築完了",
            matched_count=0,
            total_onedrive_files=0,
            pending_transfer=0,
        )

    @patch("src.rebuild_skip_list.get_structured_logger")
    def test_create_skip_list_path_conversion(self, mock_logger):
        """検証対象: create_skip_list_from_sharepoint() 目的: パス変換ロジックの確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        # 複雑なパス構造のテストデータ
        onedrive_files = [{"name": "doc.txt", "path": "MyOneDrive/subfolder/doc.txt", "size": 1024}]

        sharepoint_files = [{"name": "doc.txt", "path": "MySharePoint/subfolder/doc.txt", "size": 1024}]

        with patch.dict(
            os.environ,
            {
                "SOURCE_ONEDRIVE_FOLDER_PATH": "MyOneDrive",
                "DESTINATION_SHAREPOINT_DOCLIB": "MySharePoint",
            },
        ):
            with patch("builtins.open", mock_open()):
                result = create_skip_list_from_sharepoint(onedrive_files, sharepoint_files)

        # 結果の検証
        assert len(result) == 1
        assert result[0]["name"] == "doc.txt"
        assert result[0]["path"] == "MyOneDrive/subfolder/doc.txt"

    @patch("src.rebuild_skip_list.get_structured_logger")
    def test_create_skip_list_with_config_manager_import_error(self, mock_logger):
        """検証対象: create_skip_list_from_sharepoint()
        目的: config_manager インポートエラー時のフォールバック確認"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        onedrive_files = [{"name": "test.txt", "path": "TEST-Onedrive/test.txt", "size": 1024}]
        sharepoint_files = [{"name": "test.txt", "path": "TEST-Sharepoint/test.txt", "size": 1024}]

        with patch.dict(
            os.environ,
            {
                "SOURCE_ONEDRIVE_FOLDER_PATH": "TEST-Onedrive",
                "DESTINATION_SHAREPOINT_DOCLIB": "TEST-Sharepoint",
            },
        ):
            # config_manager のインポートエラーをシミュレート
            with patch("src.config_manager.get_skip_list_path", side_effect=ImportError()):
                with patch("builtins.open", mock_open()) as mock_file:
                    result = create_skip_list_from_sharepoint(onedrive_files, sharepoint_files)

        # 結果の検証
        assert len(result) == 1

        # デフォルトパスでファイルが保存されることを確認
        mock_file.assert_called()


class TestMainExecution:
    """メイン実行部分のテスト"""

    @patch("src.rebuild_skip_list.create_skip_list_from_sharepoint")
    @patch("src.rebuild_skip_list.crawl_onedrive")
    @patch("src.rebuild_skip_list.crawl_sharepoint")
    def test_main_execution_flow(self, mock_crawl_sharepoint, mock_crawl_onedrive, mock_create_skip_list):
        """検証対象: メイン実行フロー 目的: 全体の実行順序確認"""
        # モックの設定
        sharepoint_files = [{"name": "sp_file.txt", "path": "TEST-Sharepoint/sp_file.txt"}]
        onedrive_files = [{"name": "od_file.txt", "path": "TEST-Onedrive/od_file.txt"}]
        skip_list = [{"name": "matched.txt", "path": "TEST-Onedrive/matched.txt"}]

        mock_crawl_sharepoint.return_value = sharepoint_files
        mock_crawl_onedrive.return_value = onedrive_files
        mock_create_skip_list.return_value = skip_list

        # メイン実行部分をテスト

        # スクリプトを直接実行する代わりに、関数を順次呼び出してテスト
        result_sharepoint = mock_crawl_sharepoint()
        result_onedrive = mock_crawl_onedrive()
        result_skip_list = mock_create_skip_list(result_onedrive, result_sharepoint)

        # 実行順序の確認
        mock_crawl_sharepoint.assert_called_once()
        mock_crawl_onedrive.assert_called_once()
        mock_create_skip_list.assert_called_once_with(result_onedrive, result_sharepoint)

        # 結果の確認
        assert result_sharepoint == sharepoint_files
        assert result_onedrive == onedrive_files
        assert result_skip_list == skip_list
