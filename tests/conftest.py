"""
pytest共通設定とフィクスチャ
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch


@pytest.fixture
def temp_config_file():
    """一時的な設定ファイルを作成"""
    config_data = {
        "log_level": "DEBUG",
        "chunk_size_mb": 5,
        "large_file_threshold_mb": 4,
        "max_parallel_transfers": 4,
        "retry_count": 3,
        "timeout_sec": 10
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # クリーンアップ
    os.unlink(temp_path)


@pytest.fixture
def mock_env_vars():
    """環境変数のモック"""
    env_vars = {
        'CLIENT_ID': 'test_client_id',
        'CLIENT_SECRET': 'test_client_secret',
        'TENANT_ID': 'test_tenant_id',
        'SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME': 'test@example.com',
        'SOURCE_ONEDRIVE_FOLDER_PATH': 'test_folder',
        'SOURCE_ONEDRIVE_DRIVE_ID': 'test_drive_id',
        'DESTINATION_SHAREPOINT_SITE_ID': 'test_site_id',
        'DESTINATION_SHAREPOINT_DRIVE_ID': 'test_drive_id',
        'DESTINATION_SHAREPOINT_HOST_NAME': 'test.sharepoint.com',
        'DESTINATION_SHAREPOINT_SITE_PATH': 'sites/test',
        'DESTINATION_SHAREPOINT_DOCLIB': 'test_doclib'
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
        "lastModifiedDateTime": "2024-01-01T00:00:00Z"
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
            "reason": "already_exists"
        }
    ] 