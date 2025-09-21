import time

from msal import ConfidentialClientApplication


class GraphAuthenticator:
    def __init__(self, client_id, client_secret, tenant_id, scope=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.scope = scope or ["https://graph.microsoft.com/.default"]
        self._token = None
        self._expires_at = 0
        self._app = ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret,
        )

    def get_access_token(self):
        now = time.time()
        # 有効期限の10分（600秒）前に再認証
        if not self._token or now > self._expires_at - 600:
            result = self._app.acquire_token_for_client(scopes=self.scope)
            if "access_token" not in result:
                raise Exception(f"認証失敗: {result.get('error_description', result)}")
            self._token = result["access_token"]
            self._expires_at = now + int(result.get("expires_in", 3600))
        return self._token
