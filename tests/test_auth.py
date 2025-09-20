from unittest.mock import MagicMock, patch

import pytest

from src.auth import GraphAuthenticator


class TestGraphAuthenticator:
    """GraphAuthenticatorクラスのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前処理"""
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.tenant_id = "test_tenant_id"

    @patch("src.auth.ConfidentialClientApplication")
    def test_init(self, mock_msal):
        """初期化テスト"""
        mock_app = MagicMock()
        mock_msal.return_value = mock_app

        auth = GraphAuthenticator(self.client_id, self.client_secret, self.tenant_id)

        assert auth.client_id == self.client_id
        assert auth.client_secret == self.client_secret
        assert auth.tenant_id == self.tenant_id
        mock_msal.assert_called_once()

    @patch("src.auth.ConfidentialClientApplication")
    def test_get_access_token_success(self, mock_msal):
        """トークン取得成功テスト"""
        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        mock_msal.return_value = mock_app

        auth = GraphAuthenticator(self.client_id, self.client_secret, self.tenant_id)

        token = auth.get_access_token()
        assert token == "test_token"
        mock_app.acquire_token_for_client.assert_called_once()

    @patch("src.auth.ConfidentialClientApplication")
    def test_get_access_token_failure(self, mock_msal):
        """トークン取得失敗テスト"""
        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "Test error",
        }
        mock_msal.return_value = mock_app

        auth = GraphAuthenticator(self.client_id, self.client_secret, self.tenant_id)

        with pytest.raises(Exception) as exc_info:
            auth.get_access_token()

        assert "認証失敗" in str(exc_info.value)

    @patch("src.auth.ConfidentialClientApplication")
    def test_get_access_token_no_token(self, mock_msal):
        """トークンが含まれていない場合のテスト"""
        mock_app = MagicMock()
        mock_app.acquire_token_for_client.return_value = {"expires_in": 3600}
        mock_msal.return_value = mock_app

        auth = GraphAuthenticator(self.client_id, self.client_secret, self.tenant_id)

        with pytest.raises(Exception) as exc_info:
            auth.get_access_token()

        assert "認証失敗" in str(exc_info.value)
