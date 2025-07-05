#!/usr/bin/env python3
"""
転送後の検証スクリプト
OneDriveとSharePointのファイル数・整合性を確認
"""
import sys
import os
from dotenv import load_dotenv

# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=False)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.transfer import GraphTransferClient

def main():
    # 環境変数から設定を読み込み
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    SITE_ID = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
    DRIVE_ID = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')
    USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')

    print("=== 転送後の検証 ===")
    print(f"CLIENT_ID: {CLIENT_ID[:10]}...")
    print(f"TENANT_ID: {TENANT_ID[:10]}...")
    print(f"USER_PRINCIPAL_NAME: {USER_PRINCIPAL_NAME}")
    
    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)
    
    # OneDriveファイル数
    try:
        onedrive_items = client.list_onedrive_items(user_principal_name=USER_PRINCIPAL_NAME, folder_path="TEST-Onedrive")
        onedrive_files = client.collect_file_targets(
            onedrive_items,
            parent_path="TEST-Onedrive",
            user_principal_name=USER_PRINCIPAL_NAME,
            drive_id=None
        )
        print(f"OneDriveファイル数: {len(onedrive_files)}")
    except Exception as e:
        print(f"OneDrive取得エラー: {e}")
    
    # SharePointファイル数
    try:
        sharepoint_items = client.list_drive_items("TEST-Sharepoint")
        print(f"SharePointファイル数: {len(sharepoint_items)}")
    except Exception as e:
        print(f"SharePoint取得エラー: {e}")
    
    # スキップリストファイル数
    try:
        import json
        with open('logs/skip_list.json', 'r', encoding='utf-8') as f:
            skip_list = json.load(f)
        print(f"スキップリストファイル数: {len(skip_list)}")
    except Exception as e:
        print(f"スキップリスト読み込みエラー: {e}")

if __name__ == "__main__":
    main()
