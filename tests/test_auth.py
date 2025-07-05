import os
from dotenv import load_dotenv
import msal
import requests

# .envとOS環境変数の両対応
# OS環境変数が優先され、未設定の場合のみ.envが使われる
# .envの値で強制的に上書きしたい場合は override=True に変更可能
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=False)

REQUIRED_VARS = [
    'CLIENT_ID',
    'CLIENT_SECRET',
    'TENANT_ID',
    'SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME',
    'SOURCE_ONEDRIVE_FOLDER_PATH',
    'SOURCE_ONEDRIVE_DRIVE_ID',
    'DESTINATION_SHAREPOINT_SITE_ID',
    'DESTINATION_SHAREPOINT_DRIVE_ID',
    'DESTINATION_SHAREPOINT_HOST_NAME',
    'DESTINATION_SHAREPOINT_SITE_PATH',
    'DESTINATION_SHAREPOINT_DOCLIB',
]

def check_env_vars():
    print("【環境変数チェック】")
    missing = []
    for var in REQUIRED_VARS:
        val = os.getenv(var)
        if val is None or val.strip() == "":
            print(f"[NG] {var} : 未設定")
            missing.append(var)
        else:
            print(f"[OK] {var} = {val}")
    if missing:
        print(f"\n未設定の環境変数があります: {missing}")
        return False
    print("\n全ての必須環境変数が設定されています。\n")
    return True

def test_msal_auth():
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    SCOPE = ["https://graph.microsoft.com/.default"]
    print("【MSAL認証テスト】")
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        print("[NG] 認証に必要な環境変数(CLIENT_ID, CLIENT_SECRET, TENANT_ID)が未設定です")
        assert False, "認証に必要な環境変数が未設定です"
        return
    if CLIENT_ID:
        CLIENT_ID = CLIENT_ID.strip('"')
    if CLIENT_SECRET:
        CLIENT_SECRET = CLIENT_SECRET.strip('"')
    if TENANT_ID:
        TENANT_ID = TENANT_ID.strip('"')
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if result and isinstance(result, dict) and 'access_token' in result:
        print("認証成功: アクセストークン取得")
    else:
        err = result.get('error_description', result) if isinstance(result, dict) else str(result)
        print(f"認証失敗: {err}")
        assert False, f"認証失敗: {err}"

def get_access_token():
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    SCOPE = ["https://graph.microsoft.com/.default"]
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if result and isinstance(result, dict) and 'access_token' in result:
        return result['access_token']
    raise RuntimeError(f"アクセストークン取得失敗: {result}")

def test_onedrive_user_and_drive():
    print("\n【OneDriveユーザー/ドライブIDの有効性テスト】")
    access_token = get_access_token()
    user = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')
    drive_id = os.getenv('SOURCE_ONEDRIVE_DRIVE_ID')
    headers = {"Authorization": f"Bearer {access_token}"}

    # ユーザーのOneDrive取得
    url_user = f"https://graph.microsoft.com/v1.0/users/{user}/drive"
    resp_user = requests.get(url_user, headers=headers)
    print(f"[OneDriveユーザーDrive] {url_user} -> {resp_user.status_code}")
    print(resp_user.json())
    assert resp_user.status_code == 200, "ユーザーのOneDrive取得に失敗"

    # drive-idで取得
    url_drive = f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
    resp_drive = requests.get(url_drive, headers=headers)
    print(f"[Drive ID] {url_drive} -> {resp_drive.status_code}")
    print(resp_drive.json())
    assert resp_drive.status_code == 200, "drive-idでの取得に失敗"

def test_sharepoint_site_and_drive():
    print("\n【SharePoint Site/Drive IDの有効性テスト】")
    access_token = get_access_token()
    site_id = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
    drive_id = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')
    headers = {"Authorization": f"Bearer {access_token}"}

    # サイト情報
    url_site = f"https://graph.microsoft.com/v1.0/sites/{site_id}"
    resp_site = requests.get(url_site, headers=headers)
    print(f"[SharePoint Site] {url_site} -> {resp_site.status_code}")
    print(resp_site.json())
    assert resp_site.status_code == 200, "サイトIDでの取得に失敗"

    # ドライブ情報
    url_drive = f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
    resp_drive = requests.get(url_drive, headers=headers)
    print(f"[SharePoint Drive] {url_drive} -> {resp_drive.status_code}")
    print(resp_drive.json())
    assert resp_drive.status_code == 200, "SharePointドライブIDでの取得に失敗"

if __name__ == "__main__":
    ok = check_env_vars()
    if ok:
        test_msal_auth()
        test_onedrive_user_and_drive()
        test_sharepoint_site_and_drive()
