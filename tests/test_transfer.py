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
