"""
pytest共通設定とフィクスチャ
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_config_file():
    """一時的な設定ファイルを作成"""
    config_data = {
        "log_level": "DEBUG",
        "chunk_size_mb": 5,
        "large_file_threshold_mb": 4,
        "max_parallel_transfers": 4,
        "retry_count": 3,
        "timeout_sec": 10,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # クリーンアップ
    os.unlink(temp_path)


@pytest.fixture
def mock_env_vars():
    """環境変数のモック"""
    env_vars = {
        "CLIENT_ID": "test_client_id",
        "CLIENT_SECRET": "test_client_secret",
        "TENANT_ID": "test_tenant_id",
        "SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME": "test@example.com",
        "SOURCE_ONEDRIVE_FOLDER_PATH": "test_folder",
        "SOURCE_ONEDRIVE_DRIVE_ID": "test_drive_id",
        "DESTINATION_SHAREPOINT_SITE_ID": "test_site_id",
        "DESTINATION_SHAREPOINT_DRIVE_ID": "test_drive_id",
        "DESTINATION_SHAREPOINT_HOST_NAME": "test.sharepoint.com",
        "DESTINATION_SHAREPOINT_SITE_PATH": "sites/test",
        "DESTINATION_SHAREPOINT_DOCLIB": "test_doclib",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_file_info():
    """サンプルファイル情報"""
    return {
        "id": "test_file_id",
        "name": "test_file.txt",
        "path": "/test/path/test_file.txt",
        "size": 1024,
        "lastModifiedDateTime": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_skip_list():
    """サンプルスキップリスト"""
    return [
        {
            "id": "skipped_file_id",
            "name": "skipped_file.txt",
            "path": "/test/path/skipped_file.txt",
            "size": 2048,
            "reason": "already_exists",
        }
    ]


@pytest.fixture
def mock_graph_client():
    """Microsoft Graph API クライアントのモック"""
    with patch("src.transfer.GraphTransferClient") as mock:
        # 標準的なレスポンスを設定
        mock.return_value.upload_file_to_sharepoint.return_value = {
            "id": "test_upload_id",
            "name": "test_file.txt",
            "size": 1024,
            "lastModifiedDateTime": "2024-01-01T00:00:00Z",
        }

        mock.return_value.list_drive_items.return_value = [
            {
                "id": "file1_id",
                "name": "file1.txt",
                "size": 1024,
                "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                "folder": None,
                "parentReference": {"path": "/drive/root:/test"},
            },
            {
                "id": "folder1_id",
                "name": "folder1",
                "folder": {"childCount": 2},
                "parentReference": {"path": "/drive/root:/test"},
            },
        ]

        mock.return_value.create_folder.return_value = {
            "id": "new_folder_id",
            "name": "new_folder",
            "folder": {"childCount": 0},
        }

        mock.return_value.ensure_sharepoint_folder.return_value = None

        yield mock


@pytest.fixture
def mock_auth():
    """認証コンポーネントのモック"""
    with patch("src.auth.GraphAuthenticator") as mock:
        mock.return_value.get_access_token.return_value = "mock_access_token_12345"
        yield mock


@pytest.fixture
def mock_graph_response():
    """Microsoft Graph API レスポンスのモック"""
    return {
        "id": "test_file_id",
        "name": "test_file.txt",
        "size": 1024,
        "lastModifiedDateTime": "2024-01-01T00:00:00Z",
        "createdDateTime": "2024-01-01T00:00:00Z",
        "parentReference": {"path": "/drive/root:/test", "driveId": "test_drive_id"},
        "file": {"mimeType": "text/plain", "hashes": {"sha1Hash": "test_hash"}},
    }


@pytest.fixture
def mock_error_response():
    """Microsoft Graph API エラーレスポンスのモック"""
    return {
        "error": {
            "code": "itemNotFound",
            "message": "The resource could not be found.",
            "innerError": {
                "date": "2024-01-01T00:00:00",
                "request-id": "test-request-id",
            },
        }
    }


@pytest.fixture
def mock_upload_session_response():
    """アップロードセッションレスポンスのモック"""
    return {
        "uploadUrl": "https://graph.microsoft.com/v1.0/drives/test/items/test/uploadSession",
        "expirationDateTime": "2024-01-01T01:00:00Z",
        "nextExpectedRanges": ["0-"],
    }


@pytest.fixture
def mock_requests_get():
    """requests.get のモック"""
    with patch("requests.get") as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {"value": []}
        mock.return_value.iter_content = lambda chunk_size: [b"test_content"]
        mock.return_value.headers = {"content-length": "1024"}
        yield mock


@pytest.fixture
def mock_requests_post():
    """requests.post のモック"""
    with patch("requests.post") as mock:
        mock.return_value.status_code = 201
        mock.return_value.json.return_value = {"id": "test_id", "name": "test_file.txt"}
        yield mock


@pytest.fixture
def mock_requests_put():
    """requests.put のモック"""
    with patch("requests.put") as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {"id": "test_id", "name": "test_file.txt"}
        yield mock
