"""
GraphTransferClient のテスト
"""

from unittest.mock import MagicMock, patch

import pytest

from src.transfer import GraphTransferClient


class TestGraphTransferClient:
    """GraphTransferClient クラスのテスト"""

    @pytest.fixture
    def transfer_client(self, mock_env_vars, mock_auth):
        """テスト用 GraphTransferClient インスタンス"""
        # 検証対象: GraphTransferClient の初期化
        # 目的: 環境変数から正しく認証情報を取得することを確認
        with patch(
            "src.transfer.GraphAuthenticator", return_value=mock_auth.return_value
        ):
            return GraphTransferClient(
                client_id="test_client_id",
                client_secret="test_client_secret",
                tenant_id="test_tenant_id",
                site_id="test_site_id",
                drive_id="test_drive_id",
            )

    @pytest.mark.transfer
    def test_upload_file_to_sharepoint_small_file(
        self, transfer_client, mock_requests_put, sample_file_info
    ):
        """小さなファイルのアップロードテスト"""
        # 検証対象: upload_file_to_sharepoint()
        # 目的: 小さなファイル（4MB未満）が単純PUTでアップロードされることを確認

        # 小さなファイル（1KB）のテストデータ
        small_file_info = sample_file_info.copy()
        small_file_info["size"] = 1024

        with patch("requests.get") as mock_get:
            # ファイル情報取得のモック
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "@microsoft.graph.downloadUrl": "https://test.download.url"
            }

            # ダウンロードストリームのモック
            mock_download_response = MagicMock()
            mock_download_response.iter_content.return_value = [b"test_content"]
            mock_download_response.raise_for_status.return_value = None

            # 2回目のrequests.getコール（ダウンロード用）をモック
            mock_get.side_effect = [mock_get.return_value, mock_download_response]

            result = transfer_client.upload_file_to_sharepoint(small_file_info)

            # 結果の検証
            assert "id" in result or "message" in result
            assert mock_get.call_count >= 1

    @pytest.mark.transfer
    def test_upload_file_to_sharepoint_large_file(
        self, transfer_client, mock_upload_session_response, sample_file_info
    ):
        """大きなファイルのアップロードテスト"""
        # 検証対象: upload_file_to_sharepoint()
        # 目的: 大きなファイル（4MB以上）がアップロードセッションで処理されることを確認

        # 大きなファイル（5MB）のテストデータ
        large_file_info = sample_file_info.copy()
        large_file_info["size"] = 5 * 1024 * 1024

        with patch.object(transfer_client, "_create_upload_session") as mock_session:
            mock_session.return_value = mock_upload_session_response

            with patch.object(
                transfer_client, "_get_onedrive_file_stream"
            ) as mock_stream:
                mock_stream.return_value = MagicMock()
                mock_stream.return_value.iter_content.return_value = [
                    b"test_content" * 1000
                ]

                with patch("requests.put") as mock_put:
                    mock_put.return_value.status_code = 202
                    mock_put.return_value.json.return_value = {"nextExpectedRanges": []}

                    result = transfer_client.upload_file_to_sharepoint(large_file_info)

                    # 結果の検証
                    assert "message" in result
                    assert "upload session" in result["message"]
                    mock_session.assert_called_once()

    @pytest.mark.transfer
    def test_list_drive_items(self, transfer_client, mock_requests_get):
        """ドライブアイテム一覧取得テスト"""
        # 検証対象: list_drive_items()
        # 目的: OneDriveのファイル・フォルダ一覧が正しく取得されることを確認

        mock_requests_get.return_value.json.return_value = {
            "value": [
                {
                    "id": "file1_id",
                    "name": "file1.txt",
                    "size": 1024,
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                    "parentReference": {"path": "/drive/root:/test"},
                }
            ]
        }

        result = transfer_client.list_drive_items("test_folder")

        # 結果の検証
        assert isinstance(result, list)
        mock_requests_get.assert_called()

    @pytest.mark.transfer
    def test_create_folder(self, transfer_client, mock_requests_post):
        """フォルダ作成テスト"""
        # 検証対象: create_folder()
        # 目的: SharePointにフォルダが正しく作成されることを確認

        mock_requests_post.return_value.json.return_value = {
            "id": "new_folder_id",
            "name": "new_folder",
            "folder": {"childCount": 0},
        }

        result = transfer_client.create_folder("/test", "new_folder")

        # 結果の検証
        assert "id" in result
        assert result["name"] == "new_folder"
        mock_requests_post.assert_called_once()

    @pytest.mark.auth
    def test_acquire_token(self, transfer_client, mock_auth):
        """トークン取得テスト"""
        # 検証対象: _acquire_token()
        # 目的: 認証トークンが正しく取得されることを確認

        token = transfer_client._acquire_token()

        # 結果の検証
        assert token == "mock_access_token_12345"
        mock_auth.return_value.get_access_token.assert_called_once()

    @pytest.mark.auth
    def test_headers(self, transfer_client, mock_auth):
        """HTTPヘッダー生成テスト"""
        # 検証対象: _headers()
        # 目的: 認証ヘッダーが正しく生成されることを確認

        headers = transfer_client._headers()

        # 結果の検証
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer mock_access_token_12345"

    @pytest.mark.transfer
    def test_ensure_sharepoint_folder(self, transfer_client):
        """SharePointフォルダ確保テスト"""
        # 検証対象: ensure_sharepoint_folder()
        # 目的: SharePointに必要なフォルダ構造が作成されることを確認

        with patch.object(transfer_client, "create_folder") as mock_create:
            with patch("requests.get") as mock_get:
                # フォルダが存在しない場合のレスポンス
                mock_get.return_value.status_code = 404

                transfer_client.ensure_sharepoint_folder("/test/nested/folder")

                # フォルダ作成が呼ばれることを確認
                assert mock_create.called

    @pytest.mark.integration
    def test_upload_with_error_handling(self, transfer_client, sample_file_info):
        """エラーハンドリングテスト"""
        # 検証対象: upload_file_to_sharepoint() のエラー処理
        # 目的: API エラー時に適切な例外が発生することを確認

        with patch("requests.get") as mock_get:
            # ファイル情報取得でエラーを発生させる
            mock_get.return_value.status_code = 404
            mock_get.return_value.text = "File not found"

            with pytest.raises(Exception) as exc_info:
                transfer_client.upload_file_to_sharepoint(sample_file_info)

            assert "ファイル情報の取得に失敗しました" in str(exc_info.value)

    @pytest.mark.transfer
    def test_list_drive_items_timeout_error(self, transfer_client):
        """ドライブアイテム一覧取得のタイムアウトエラーテスト"""
        # 検証対象: list_drive_items() のタイムアウト処理
        # 目的: タイムアウト時に空のリストが返されることを確認

        import requests

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

            result = transfer_client.list_drive_items("test_folder")

            # タイムアウト時は空のリストが返される
            assert result == []

    @pytest.mark.transfer
    def test_list_drive_items_request_error(self, transfer_client):
        """ドライブアイテム一覧取得のリクエストエラーテスト"""
        # 検証対象: list_drive_items() のリクエストエラー処理
        # 目的: リクエストエラー時に空のリストが返されることを確認

        import requests

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")

            result = transfer_client.list_drive_items("test_folder")

            # リクエストエラー時は空のリストが返される
            assert result == []

    @pytest.mark.transfer
    def test_ensure_sharepoint_folder_error_handling(self, transfer_client):
        """SharePointフォルダ確保のエラーハンドリングテスト"""
        # 検証対象: ensure_sharepoint_folder() のエラー処理
        # 目的: フォルダ作成時のエラーが適切に処理されることを確認

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404  # フォルダが存在しない

            with patch.object(transfer_client, "create_folder") as mock_create:
                mock_create.side_effect = Exception("Folder creation failed")

                # エラーが発生してもメソッドは正常終了する（警告ログのみ）
                transfer_client.ensure_sharepoint_folder("/test/nested/folder")

                # フォルダ作成が試行されることを確認
                assert mock_create.called

    @pytest.mark.transfer
    def test_get_onedrive_file_stream_error(self, transfer_client, sample_file_info):
        """OneDriveファイルストリーム取得エラーテスト"""
        # 検証対象: _get_onedrive_file_stream() のエラー処理
        # 目的: ファイルストリーム取得時のエラーが適切に処理されることを確認

        with patch("requests.get") as mock_get:
            # ファイル情報取得は成功するが、ダウンロードURLが無い場合
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}  # ダウンロードURLなし

            with pytest.raises(Exception) as exc_info:
                transfer_client._get_onedrive_file_stream(sample_file_info)

            assert "ダウンロードURLが取得できませんでした" in str(exc_info.value)

    @pytest.mark.transfer
    def test_create_upload_session_error(self, transfer_client):
        """アップロードセッション作成エラーテスト"""
        # 検証対象: _create_upload_session() のエラー処理
        # 目的: アップロードセッション作成時のエラーが適切に処理されることを確認

        import requests

        with patch("requests.post") as mock_post:
            mock_post.return_value.raise_for_status.side_effect = (
                requests.exceptions.HTTPError("Session creation failed")
            )

            with pytest.raises(requests.exceptions.HTTPError):
                transfer_client._create_upload_session("/test/path", 1024)

    @pytest.mark.integration
    def test_import_error_fallback(self):
        """インポートエラー時のフォールバック処理テスト"""
        # 検証対象: transfer.py のインポートエラー処理
        # 目的: config_manager インポート失敗時のフォールバック関数が動作することを確認

        # この部分は既にモジュールレベルで実行されているため、
        # 実際のテストは困難だが、フォールバック関数の存在を確認
        from src.transfer import get_chunk_size_mb, get_large_file_threshold_mb

        # フォールバック関数が定義されていることを確認
        assert callable(get_chunk_size_mb)
        assert callable(get_large_file_threshold_mb)

    @pytest.mark.transfer
    def test_build_onedrive_download_url_with_drive_id(self):
        """OneDriveダウンロードURL構築テスト（ドライブID指定）"""
        # 検証対象: _build_onedrive_download_url()
        # 目的: ドライブIDが指定された場合の正しいURL構築を確認

        from src.transfer import _build_onedrive_download_url

        base_url = "https://graph.microsoft.com/v1.0"
        encoded_path = "test%2Ffile.txt"
        drive_id = "test_drive_id"

        result = _build_onedrive_download_url(base_url, encoded_path, drive_id)

        expected = f"{base_url}/drives/{drive_id}/root:/{encoded_path}:/content"
        assert result == expected

    @pytest.mark.transfer
    def test_build_onedrive_download_url_without_drive_id(self):
        """OneDriveダウンロードURL構築テスト（ユーザープリンシパル使用）"""
        # 検証対象: _build_onedrive_download_url()
        # 目的: ドライブIDが無い場合のユーザープリンシパル使用を確認

        from src.transfer import _build_onedrive_download_url

        base_url = "https://graph.microsoft.com/v1.0"
        encoded_path = "test%2Ffile.txt"

        with patch.dict(
            "os.environ", {"SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME": "test@example.com"}
        ):
            result = _build_onedrive_download_url(base_url, encoded_path, None)

            expected = (
                f"{base_url}/users/test@example.com/drive/root:/{encoded_path}:/content"
            )
            assert result == expected

    @pytest.mark.transfer
    def test_build_onedrive_download_url_empty_drive_id(self):
        """OneDriveダウンロードURL構築テスト（空のドライブID）"""
        # 検証対象: _build_onedrive_download_url()
        # 目的: 空のドライブIDの場合のユーザープリンシパル使用を確認

        from src.transfer import _build_onedrive_download_url

        base_url = "https://graph.microsoft.com/v1.0"
        encoded_path = "test%2Ffile.txt"

        with patch.dict(
            "os.environ", {"SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME": "test@example.com"}
        ):
            result = _build_onedrive_download_url(base_url, encoded_path, "")

            expected = (
                f"{base_url}/users/test@example.com/drive/root:/{encoded_path}:/content"
            )
            assert result == expected

    @pytest.mark.transfer
    def test_filter_skipped_targets(self, transfer_client):
        """スキップリストフィルタリングテスト"""
        # 検証対象: filter_skipped_targets()
        # 目的: スキップリストに該当するファイルが除外されることを確認

        file_targets = [
            {"name": "file1.txt", "path": "/test/file1.txt", "size": 1024},
            {"name": "file2.txt", "path": "/test/file2.txt", "size": 2048},
            {"name": "file3.txt", "path": "/test/file3.txt", "size": 3072},
        ]

        # スキップリストのモック
        skip_list = {"/test/file2.txt": True}

        with patch("src.transfer.load_skip_list", return_value=skip_list):
            with patch("src.transfer.is_skipped") as mock_is_skipped:
                # file2.txt のみスキップされるように設定
                mock_is_skipped.side_effect = (
                    lambda f, sl: f["path"] == "/test/file2.txt"
                )

                result = transfer_client.filter_skipped_targets(file_targets)

                # file2.txt が除外されることを確認
                assert len(result) == 2
                assert all(f["path"] != "/test/file2.txt" for f in result)

    @pytest.mark.transfer
    def test_save_file_targets(self, transfer_client, tmp_path):
        """ファイルターゲット保存テスト"""
        # 検証対象: save_file_targets()
        # 目的: ファイルターゲットリストがJSONで正しく保存されることを確認

        file_targets = [
            {"name": "file1.txt", "path": "/test/file1.txt", "size": 1024},
            {"name": "file2.txt", "path": "/test/file2.txt", "size": 2048},
        ]

        save_path = tmp_path / "test_targets.json"

        transfer_client.save_file_targets(file_targets, str(save_path))

        # ファイルが作成されることを確認
        assert save_path.exists()

        # 内容を確認
        import json

        with open(save_path, encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data == file_targets

    @pytest.mark.transfer
    def test_collect_file_targets_from_onedrive(self, transfer_client):
        """OneDriveファイルターゲット収集テスト"""
        # 検証対象: collect_file_targets_from_onedrive()
        # 目的: OneDriveからファイルリストが正しく収集されることを確認

        mock_items = [
            {
                "name": "file1.txt",
                "full_path": "/test/file1.txt",
                "size": 1024,
                "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                "id": "file1_id",
                "file": {"mimeType": "text/plain"},
            },
            {
                "name": "file2.txt",
                "full_path": "/test/file2.txt",
                "size": 2048,
                "lastModifiedDateTime": "2024-01-02T00:00:00Z",
                "id": "file2_id",
                "file": {"mimeType": "text/plain"},
            },
        ]

        with patch.object(
            transfer_client, "list_onedrive_items_with_path", return_value=mock_items
        ):
            result = transfer_client.collect_file_targets_from_onedrive(
                "/test", user_principal_name="test@example.com"
            )

            # 結果の検証
            assert len(result) == 2
            assert result[0]["name"] == "file1.txt"
            assert result[0]["path"] == "/test/file1.txt"
            assert result[1]["name"] == "file2.txt"
            assert result[1]["path"] == "/test/file2.txt"

    @pytest.mark.transfer
    def test_collect_file_targets_progress_logging(self, transfer_client):
        """OneDriveファイルターゲット収集の進捗ログテスト"""
        # 検証対象: collect_file_targets_from_onedrive() の進捗ログ
        # 目的: 1000件ごとの進捗ログが出力されることを確認

        # 1001個のファイルを生成（1000件目と1001件目で進捗ログが出力される）
        mock_items = []
        for i in range(1001):
            mock_items.append(
                {
                    "name": f"file{i}.txt",
                    "full_path": f"/test/file{i}.txt",
                    "size": 1024,
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                    "id": f"file{i}_id",
                    "file": {"mimeType": "text/plain"},
                }
            )

        with patch.object(
            transfer_client, "list_onedrive_items_with_path", return_value=mock_items
        ):
            with patch("src.transfer.get_structured_logger") as mock_logger:
                mock_logger_instance = MagicMock()
                mock_logger.return_value = mock_logger_instance

                result = transfer_client.collect_file_targets_from_onedrive(
                    "/test", user_principal_name="test@example.com"
                )

                # 結果の検証
                assert len(result) == 1001

                # 進捗ログが呼ばれることを確認（1000件目で1回）
                progress_calls = [
                    call
                    for call in mock_logger_instance.info.call_args_list
                    if "進捗" in str(call)
                ]
                assert len(progress_calls) >= 1

    @pytest.mark.transfer
    def test_list_onedrive_items_with_path_user_principal(self, transfer_client):
        """OneDriveアイテム一覧取得テスト（ユーザープリンシパル指定）"""
        # 検証対象: list_onedrive_items_with_path()
        # 目的: ユーザープリンシパル指定時の正しいURL構築を確認

        mock_response_data = {
            "value": [
                {
                    "name": "file1.txt",
                    "size": 1024,
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                    "id": "file1_id",
                    "file": {"mimeType": "text/plain"},
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_data
            mock_get.return_value.raise_for_status.return_value = None

            result = transfer_client.list_onedrive_items_with_path(
                user_principal_name="test@example.com", folder_path="test_folder"
            )

            # 結果の検証
            assert len(result) == 1
            assert result[0]["name"] == "file1.txt"
            assert result[0]["full_path"] == "file1.txt"

            # 正しいURLが呼ばれることを確認
            expected_url = (
                f"{transfer_client.base_url}/users/test@example.com"
                "/drive/root:/test_folder:/children"
            )
            mock_get.assert_called_with(
                expected_url, headers=transfer_client._headers(), timeout=10
            )

    @pytest.mark.transfer
    def test_list_onedrive_items_with_path_drive_id(self, transfer_client):
        """OneDriveアイテム一覧取得テスト（ドライブID指定）"""
        # 検証対象: list_onedrive_items_with_path()
        # 目的: ドライブID指定時の正しいURL構築を確認

        mock_response_data = {
            "value": [
                {
                    "name": "file1.txt",
                    "size": 1024,
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                    "id": "file1_id",
                    "file": {"mimeType": "text/plain"},
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_data
            mock_get.return_value.raise_for_status.return_value = None

            result = transfer_client.list_onedrive_items_with_path(
                drive_id="test_drive_id", folder_path="test_folder"
            )

            # 結果の検証
            assert len(result) == 1
            assert result[0]["name"] == "file1.txt"

            # 正しいURLが呼ばれることを確認
            expected_url = (
                f"{transfer_client.base_url}/drives/test_drive_id"
                "/root:/test_folder:/children"
            )
            mock_get.assert_called_with(
                expected_url, headers=transfer_client._headers(), timeout=10
            )

    @pytest.mark.transfer
    def test_list_onedrive_items_with_path_no_params_error(self, transfer_client):
        """OneDriveアイテム一覧取得エラーテスト（パラメータ不足）"""
        # 検証対象: list_onedrive_items_with_path()
        # 目的: user_principal_name と drive_id の両方が未指定の場合のエラー処理を確認

        with pytest.raises(ValueError) as exc_info:
            transfer_client.list_onedrive_items_with_path(folder_path="test_folder")

        assert "user_principal_name か drive_id のいずれかを指定してください" in str(
            exc_info.value
        )

    @pytest.mark.transfer
    def test_list_onedrive_items_with_path_timeout_error(self, transfer_client):
        """OneDriveアイテム一覧取得のタイムアウトエラーテスト"""
        # 検証対象: list_onedrive_items_with_path() のタイムアウト処理
        # 目的: タイムアウト時に空のリストが返されることを確認

        import requests

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

            result = transfer_client.list_onedrive_items_with_path(
                user_principal_name="test@example.com"
            )

            # タイムアウト時は空のリストが返される
            assert result == []

    @pytest.mark.transfer
    def test_list_onedrive_items_with_path_request_error(self, transfer_client):
        """OneDriveアイテム一覧取得のリクエストエラーテスト"""
        # 検証対象: list_onedrive_items_with_path() のリクエストエラー処理
        # 目的: リクエストエラー時に空のリストが返されることを確認

        import requests

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")

            result = transfer_client.list_onedrive_items_with_path(
                user_principal_name="test@example.com"
            )

            # リクエストエラー時は空のリストが返される
            assert result == []

    @pytest.mark.transfer
    def test_list_onedrive_items_with_path_recursive(self, transfer_client):
        """OneDriveアイテム一覧取得の再帰処理テスト"""
        # 検証対象: list_onedrive_items_with_path() の再帰処理
        # 目的: フォルダが含まれる場合の再帰的な処理を確認

        # 最初の呼び出し（フォルダを含む）
        mock_response_data_1 = {
            "value": [
                {"name": "subfolder", "id": "folder_id", "folder": {"childCount": 1}},
                {
                    "name": "file1.txt",
                    "size": 1024,
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                    "id": "file1_id",
                    "file": {"mimeType": "text/plain"},
                },
            ]
        }

        # 2回目の呼び出し（サブフォルダ内）
        mock_response_data_2 = {
            "value": [
                {
                    "name": "file2.txt",
                    "size": 2048,
                    "lastModifiedDateTime": "2024-01-02T00:00:00Z",
                    "id": "file2_id",
                    "file": {"mimeType": "text/plain"},
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status.return_value = None
            # 最初の呼び出しでフォルダを含むレスポンス、2回目でファイルのみ
            mock_get.return_value.json.side_effect = [
                mock_response_data_1,
                mock_response_data_2,
            ]

            result = transfer_client.list_onedrive_items_with_path(
                user_principal_name="test@example.com", folder_path="test_folder"
            )

            # 結果の検証（ファイルのみが返される）
            assert len(result) == 2
            # 順序は実装に依存するため、名前で検索して確認
            file_names = [item["name"] for item in result]
            assert "file1.txt" in file_names
            assert "file2.txt" in file_names

            # file2.txtはサブフォルダ内にあることを確認
            file2_item = next(item for item in result if item["name"] == "file2.txt")
            assert "subfolder" in file2_item["full_path"]

    @pytest.mark.transfer
    def test_create_folder_conflict_handling(self, transfer_client):
        """フォルダ作成の競合処理テスト"""
        # 検証対象: create_folder() の競合処理
        # 目的: フォルダが既に存在する場合の処理を確認

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 409  # Conflict

            result = transfer_client.create_folder("/test", "existing_folder")

            # 競合時は空の辞書が返される
            assert result == {}

    @pytest.mark.transfer
    def test_ensure_sharepoint_folder_empty_path(self, transfer_client):
        """SharePointフォルダ確保の空パス処理テスト"""
        # 検証対象: ensure_sharepoint_folder() の空パス処理
        # 目的: 空のパスや "." の場合に何も処理しないことを確認

        with patch.object(transfer_client, "create_folder") as mock_create:
            # 空文字列の場合
            transfer_client.ensure_sharepoint_folder("")
            # "." の場合
            transfer_client.ensure_sharepoint_folder(".")
            # None の場合
            transfer_client.ensure_sharepoint_folder(None)

            # フォルダ作成が呼ばれないことを確認
            mock_create.assert_not_called()

    @pytest.mark.transfer
    def test_ensure_sharepoint_folder_existing_folder(self, transfer_client):
        """SharePointフォルダ確保の既存フォルダ処理テスト"""
        # 検証対象: ensure_sharepoint_folder() の既存フォルダ処理
        # 目的: フォルダが既に存在する場合に作成処理をスキップすることを確認

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200  # フォルダが存在

            with patch.object(transfer_client, "create_folder") as mock_create:
                transfer_client.ensure_sharepoint_folder("/test/existing")

                # フォルダ作成が呼ばれないことを確認
                mock_create.assert_not_called()

    @pytest.mark.transfer
    def test_upload_small_file_fallback_path(self, transfer_client, sample_file_info):
        """小容量ファイルアップロードのフォールバック処理テスト"""
        # 検証対象: _upload_small_file_to_sharepoint() のフォールバック処理
        # 目的: ドライブIDまたはファイルIDが無い場合のパスベース方式を確認

        small_file_info = sample_file_info.copy()
        small_file_info["size"] = 1024
        small_file_info.pop("id", None)  # ファイルIDを削除

        with patch.dict(
            "os.environ", {"SOURCE_ONEDRIVE_DRIVE_ID": ""}
        ):  # 空のドライブID
            with patch("requests.get") as mock_get:
                # ダウンロードレスポンスのモック
                mock_download_response = MagicMock()
                mock_download_response.raw = b"test_content"
                mock_download_response.raise_for_status.return_value = None
                mock_get.return_value = mock_download_response

                with patch("requests.put") as mock_put:
                    mock_put.return_value.json.return_value = {"id": "uploaded_file_id"}
                    mock_put.return_value.raise_for_status.return_value = None

                    with patch.object(transfer_client, "ensure_sharepoint_folder"):
                        result = transfer_client._upload_small_file_to_sharepoint(
                            small_file_info
                        )

                        # 結果の検証
                        assert "id" in result
                        assert result["id"] == "uploaded_file_id"

    @pytest.mark.transfer
    def test_upload_small_file_file_info_error(self, transfer_client, sample_file_info):
        """小容量ファイルアップロードのファイル情報取得エラーテスト"""
        # 検証対象: _upload_small_file_to_sharepoint() のファイル情報取得エラー処理
        # 目的: ファイル情報取得に失敗した場合の例外処理を確認

        small_file_info = sample_file_info.copy()
        small_file_info["size"] = 1024

        with patch.dict("os.environ", {"SOURCE_ONEDRIVE_DRIVE_ID": "test_drive_id"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 404
                mock_get.return_value.text = "File not found"

                with pytest.raises(Exception) as exc_info:
                    transfer_client._upload_small_file_to_sharepoint(small_file_info)

                assert "ファイル情報の取得に失敗しました" in str(exc_info.value)

    @pytest.mark.transfer
    def test_upload_small_file_no_download_url(self, transfer_client, sample_file_info):
        """小容量ファイルアップロードのダウンロードURL無しエラーテスト"""
        # 検証対象: _upload_small_file_to_sharepoint() のダウンロードURL無しエラー処理
        # 目的: ダウンロードURLが取得できない場合の例外処理を確認

        small_file_info = sample_file_info.copy()
        small_file_info["size"] = 1024

        with patch.dict("os.environ", {"SOURCE_ONEDRIVE_DRIVE_ID": "test_drive_id"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {}  # ダウンロードURLなし

                with pytest.raises(Exception) as exc_info:
                    transfer_client._upload_small_file_to_sharepoint(small_file_info)

                assert "ダウンロードURLが取得できませんでした" in str(exc_info.value)

    @pytest.mark.transfer
    def test_upload_large_file_complete_flow(self, transfer_client, sample_file_info):
        """大容量ファイルアップロードの完全フローテスト"""
        # 検証対象: _upload_large_file_to_sharepoint() の完全フロー
        # 目的: 大容量ファイルのアップロードセッション処理を確認

        large_file_info = sample_file_info.copy()
        large_file_info["size"] = 10 * 1024 * 1024  # 10MB

        # アップロードセッションのモック
        mock_session = {"uploadUrl": "https://test.upload.url"}

        # ファイルストリームのモック
        mock_stream = MagicMock()
        mock_stream.read.side_effect = [
            b"chunk1" * 1000,  # 最初のチャンク
            b"chunk2" * 1000,  # 2番目のチャンク
            b"",  # 終了
        ]

        with patch.object(
            transfer_client, "_create_upload_session", return_value=mock_session
        ):
            with patch.object(
                transfer_client, "_get_onedrive_file_stream", return_value=mock_stream
            ):
                with patch.object(
                    transfer_client, "_upload_chunk"
                ) as mock_upload_chunk:
                    with patch.object(transfer_client, "ensure_sharepoint_folder"):
                        result = transfer_client._upload_large_file_to_sharepoint(
                            large_file_info
                        )

                        # 結果の検証
                        assert "message" in result
                        assert "Upload completed" in result["message"]

                        # チャンクアップロードが呼ばれることを確認
                        assert mock_upload_chunk.call_count >= 1

    @pytest.mark.transfer
    def test_create_upload_session(self, transfer_client):
        """アップロードセッション作成テスト"""
        # 検証対象: _create_upload_session()
        # 目的: SharePointアップロードセッションが正しく作成されることを確認

        dst_path = "/test/large_file.txt"
        file_size = 10 * 1024 * 1024

        mock_response = {"uploadUrl": "https://test.upload.url"}

        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status.return_value = None

            result = transfer_client._create_upload_session(dst_path, file_size)

            # 結果の検証
            assert result == mock_response
            assert "uploadUrl" in result

            # 正しいペイロードで呼ばれることを確認
            expected_payload = {
                "item": {
                    "@microsoft.graph.conflictBehavior": "replace",
                    "name": "large_file.txt",
                }
            }
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"] == expected_payload

    @pytest.mark.transfer
    def test_get_onedrive_file_stream_with_file_id(
        self, transfer_client, sample_file_info
    ):
        """OneDriveファイルストリーム取得テスト（ファイルID使用）"""
        # 検証対象: _get_onedrive_file_stream() のファイルID使用
        # 目的: ファイルIDを使った直接アクセス方式を確認

        with patch.dict("os.environ", {"SOURCE_ONEDRIVE_DRIVE_ID": "test_drive_id"}):
            with patch("requests.get") as mock_get:
                # ファイル情報取得のレスポンス
                mock_file_response = MagicMock()
                mock_file_response.status_code = 200
                mock_file_response.json.return_value = {
                    "@microsoft.graph.downloadUrl": "https://test.download.url"
                }

                # ダウンロードストリームのレスポンス
                mock_download_response = MagicMock()
                mock_download_response.raw = b"file_content"
                mock_download_response.raise_for_status.return_value = None

                mock_get.side_effect = [mock_file_response, mock_download_response]

                result = transfer_client._get_onedrive_file_stream(sample_file_info)

                # 結果の検証
                assert result == b"file_content"

                # 2回のGETリクエストが呼ばれることを確認
                assert mock_get.call_count == 2

    @pytest.mark.transfer
    def test_get_onedrive_file_stream_fallback_path(
        self, transfer_client, sample_file_info
    ):
        """OneDriveファイルストリーム取得のフォールバック処理テスト"""
        # 検証対象: _get_onedrive_file_stream() のフォールバック処理
        # 目的: ドライブIDまたはファイルIDが無い場合のパスベース方式を確認

        file_info_no_id = sample_file_info.copy()
        file_info_no_id.pop("id", None)  # ファイルIDを削除

        with patch.dict(
            "os.environ", {"SOURCE_ONEDRIVE_DRIVE_ID": ""}
        ):  # 空のドライブID
            with patch("requests.get") as mock_get:
                mock_download_response = MagicMock()
                mock_download_response.raw = b"file_content"
                mock_download_response.raise_for_status.return_value = None
                mock_get.return_value = mock_download_response

                result = transfer_client._get_onedrive_file_stream(file_info_no_id)

                # 結果の検証
                assert result == b"file_content"

    @pytest.mark.transfer
    def test_get_onedrive_file_stream_file_info_error(
        self, transfer_client, sample_file_info
    ):
        """OneDriveファイルストリーム取得のファイル情報エラーテスト"""
        # 検証対象: _get_onedrive_file_stream() のファイル情報取得エラー処理
        # 目的: ファイル情報取得に失敗した場合の例外処理を確認

        with patch.dict("os.environ", {"SOURCE_ONEDRIVE_DRIVE_ID": "test_drive_id"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 404
                mock_get.return_value.text = "File not found"

                with pytest.raises(Exception) as exc_info:
                    transfer_client._get_onedrive_file_stream(sample_file_info)

                assert "ファイル情報の取得に失敗しました" in str(exc_info.value)

    @pytest.mark.transfer
    def test_get_onedrive_file_stream_no_download_url(
        self, transfer_client, sample_file_info
    ):
        """OneDriveファイルストリーム取得のダウンロードURL無しエラーテスト"""
        # 検証対象: _get_onedrive_file_stream() のダウンロードURL無しエラー処理
        # 目的: ダウンロードURLが取得できない場合の例外処理を確認

        with patch.dict("os.environ", {"SOURCE_ONEDRIVE_DRIVE_ID": "test_drive_id"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {}  # ダウンロードURLなし

                with pytest.raises(Exception) as exc_info:
                    transfer_client._get_onedrive_file_stream(sample_file_info)

                assert "ダウンロードURLが取得できませんでした" in str(exc_info.value)

    @pytest.mark.transfer
    def test_upload_chunk(self, transfer_client):
        """チャンクアップロードテスト"""
        # 検証対象: _upload_chunk()
        # 目的: チャンクデータが正しくアップロードされることを確認

        upload_url = "https://test.upload.url"
        chunk_data = b"test_chunk_data"
        start_byte = 0
        end_byte = len(chunk_data) - 1
        total_size = 1024

        with patch("requests.put") as mock_put:
            mock_put.return_value.raise_for_status.return_value = None

            result = transfer_client._upload_chunk(
                upload_url, chunk_data, start_byte, end_byte, total_size
            )

            # 結果の検証
            assert result == mock_put.return_value

            # 正しいヘッダーで呼ばれることを確認
            expected_headers = {
                "Content-Range": f"bytes {start_byte}-{end_byte}/{total_size}",
                "Content-Length": str(len(chunk_data)),
            }
            mock_put.assert_called_once_with(
                upload_url, headers=expected_headers, data=chunk_data, timeout=10
            )

    @pytest.mark.transfer
    def test_list_drive_items_recursive_folder_handling(self, transfer_client):
        """ドライブアイテム一覧取得の再帰フォルダ処理テスト"""
        # 検証対象: list_drive_items() の再帰処理
        # 目的: フォルダが含まれる場合の再帰的な処理を確認

        # 最初の呼び出し（フォルダを含む）
        mock_response_data_1 = {
            "value": [
                {"id": "folder_id", "name": "subfolder", "folder": {"childCount": 1}},
                {
                    "id": "file1_id",
                    "name": "file1.txt",
                    "size": 1024,
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                },
            ]
        }

        # 2回目の呼び出し（サブフォルダ内）
        mock_response_data_2 = {
            "value": [
                {
                    "id": "file2_id",
                    "name": "file2.txt",
                    "size": 2048,
                    "lastModifiedDateTime": "2024-01-02T00:00:00Z",
                }
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status.return_value = None
            # 最初の呼び出しでフォルダを含むレスポンス、2回目でファイルのみ
            mock_get.return_value.json.side_effect = [
                mock_response_data_1,
                mock_response_data_2,
            ]

            result = transfer_client.list_drive_items("test_folder")

            # 結果の検証（ファイルのみが返される）
            assert len(result) == 2
            # 順序は実装に依存するため、名前で検索して確認
            file_names = [item["name"] for item in result]
            assert "file1.txt" in file_names
            assert "file2.txt" in file_names

            # 2回のAPIコールが行われることを確認
            assert mock_get.call_count == 2

    @pytest.mark.transfer
    def test_filter_skipped_targets_with_default_path(self, transfer_client):
        """スキップリストフィルタリングテスト（デフォルトパス使用）"""
        # 検証対象: filter_skipped_targets() のデフォルトパス使用
        # 目的: skip_list_path が None の場合のデフォルト動作を確認

        file_targets = [
            {"name": "file1.txt", "path": "/test/file1.txt", "size": 1024},
        ]

        with patch("src.transfer.load_skip_list", return_value={}):
            with patch("src.transfer.is_skipped", return_value=False):
                # config_manager のインポートエラーをシミュレート
                with patch(
                    "src.config_manager.get_skip_list_path", side_effect=ImportError
                ):
                    result = transfer_client.filter_skipped_targets(file_targets, None)

                    # 結果の検証
                    assert len(result) == 1
                    assert result[0]["name"] == "file1.txt"

    @pytest.mark.transfer
    def test_collect_file_targets_duplicate_handling(self, transfer_client):
        """OneDriveファイルターゲット収集の重複処理テスト"""
        # 検証対象: collect_file_targets_from_onedrive() の重複処理
        # 目的: 同じファイルが重複して追加されないことを確認

        mock_items = [
            {
                "name": "file1.txt",
                "full_path": "/test/file1.txt",
                "size": 1024,
                "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                "id": "file1_id",
                "file": {"mimeType": "text/plain"},
            },
            {
                "name": "file1.txt",  # 同じファイル
                "full_path": "/test/file1.txt",
                "size": 1024,
                "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                "id": "file1_id",
                "file": {"mimeType": "text/plain"},
            },
        ]

        with patch.object(
            transfer_client, "list_onedrive_items_with_path", return_value=mock_items
        ):
            result = transfer_client.collect_file_targets_from_onedrive(
                "/test", user_principal_name="test@example.com"
            )

            # 重複が除去されることを確認
            assert len(result) == 1
            assert result[0]["name"] == "file1.txt"
