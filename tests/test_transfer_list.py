import os
from dotenv import load_dotenv
# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=False)
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from transfer import GraphTransferClient

CLIENT_ID = os.getenv('CLIENT_ID').strip('"')
CLIENT_SECRET = os.getenv('CLIENT_SECRET').strip('"')
TENANT_ID = os.getenv('TENANT_ID').strip('"')
DRIVE_ID = os.getenv('SOURCE_ONEDRIVE_DRIVE_ID', '').strip('"')
SITE_ID = os.getenv('DESTINATION_SHAREPOINT_SITE_ID', '').strip('"')
USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME', '').strip('"')


def test_list_drive_items():
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        print("必要な環境変数が不足しています。.envを確認してください。")
        print(f"CLIENT_ID={CLIENT_ID}")
        print(f"CLIENT_SECRET={'***' if CLIENT_SECRET else ''}")
        print(f"TENANT_ID={TENANT_ID}")
        return
    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)
    # SharePoint TEST-Sharepoint フォルダ配下
    if SITE_ID and DRIVE_ID:
        try:
            print("[SharePoint] TEST-Sharepoint フォルダ直下のアイテムを再帰取得...")
            items = client.list_drive_items("TEST-Sharepoint")
            print(f"取得件数: {len(items)}")
            file_targets = client.collect_file_targets(items, parent_path="TEST-Sharepoint")
            print(f"[SharePoint] 転送対象ファイル数: {len(file_targets)}")
            for f in file_targets[:10]:
                print(f"{f['path']} (size={f['size']}, lastModified={f['lastModifiedDateTime']})")
            # 保存
            client.save_file_targets(file_targets, "logs/sharepoint_transfer_targets.json")
            print("[SharePoint] 転送対象リストを logs/sharepoint_transfer_targets.json に保存しました")
        except Exception as e:
            print(f"[SharePoint] エラー: {e}")
    # OneDrive TEST-Onedrive フォルダ配下
    if USER_PRINCIPAL_NAME or DRIVE_ID:
        try:
            print("[OneDrive] TEST-Onedrive フォルダ直下のアイテムを再帰取得...")
            items = client.list_onedrive_items(user_principal_name=USER_PRINCIPAL_NAME or None, drive_id=DRIVE_ID or None, folder_path="TEST-Onedrive")
            print(f"取得件数: {len(items)}")
            file_targets = client.collect_file_targets(items, parent_path="TEST-Onedrive")
            print(f"[OneDrive] 転送対象ファイル数: {len(file_targets)}")
            for f in file_targets[:10]:
                print(f"{f['path']} (size={f['size']}, lastModified={f['lastModifiedDateTime']})")
            # 保存
            client.save_file_targets(file_targets, "logs/onedrive_transfer_targets.json")
            print("[OneDrive] 転送対象リストを logs/onedrive_transfer_targets.json に保存しました")
        except Exception as e:
            print(f"[OneDrive] エラー: {e}")

if __name__ == "__main__":
    test_list_drive_items()
