#!/usr/bin/env python3
"""
OneDriveの実際の構造を詳細確認
"""
import sys
import os
from dotenv import load_dotenv
import requests

load_dotenv('.env', override=False)
sys.path.insert(0, 'src')
from auth import GraphAuthenticator

def check_onedrive_actual_structure():
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')

    auth = GraphAuthenticator(CLIENT_ID, CLIENT_SECRET, TENANT_ID)
    headers = {"Authorization": f"Bearer {auth.get_access_token()}"}
    
    print("=== OneDrive TEST-Onedrive 直下の詳細構造 ===")
    
    # TEST-Onedrive直下のアイテム取得
    url = f"https://graph.microsoft.com/v1.0/users/{USER_PRINCIPAL_NAME}/drive/root:/TEST-Onedrive:/children"
    
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        
        folders = []
        files = []
        
        for item in data.get('value', []):
            if item.get('folder'):
                folders.append({
                    'name': item['name'],
                    'id': item['id'],
                    'childCount': item.get('folder', {}).get('childCount', 0)
                })
            else:
                files.append({
                    'name': item['name'],
                    'id': item['id'],
                    'size': item.get('size', 0)
                })
        
        print(f"📁 サブフォルダ数: {len(folders)}")
        for folder in folders:
            print(f"  📁 {folder['name']} (子アイテム: {folder['childCount']})")
            
        print(f"📄 ファイル数: {len(files)}")
        for file in files[:10]:  # 最初の10ファイルのみ表示
            print(f"  📄 {file['name']} ({file['size']} bytes)")
        if len(files) > 10:
            print(f"  ... (他 {len(files) - 10} ファイル)")
            
        print(f"\n総アイテム数: {len(data.get('value', []))}")
        
        # もしサブフォルダがあれば、その中身も確認
        if folders:
            print("\n=== サブフォルダの内容 ===")
            for folder in folders[:3]:  # 最初の3フォルダのみ
                sub_url = f"https://graph.microsoft.com/v1.0/users/{USER_PRINCIPAL_NAME}/drive/root:/TEST-Onedrive/{folder['name']}:/children"
                sub_resp = requests.get(sub_url, headers=headers)
                if sub_resp.status_code == 200:
                    sub_data = sub_resp.json()
                    print(f"📁 {folder['name']} 配下:")
                    for sub_item in sub_data.get('value', [])[:5]:
                        item_type = "📁" if sub_item.get('folder') else "📄"
                        print(f"    {item_type} {sub_item['name']}")
                    if len(sub_data.get('value', [])) > 5:
                        print(f"    ... (他 {len(sub_data.get('value', [])) - 5} アイテム)")
        
    else:
        print(f"エラー: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    check_onedrive_actual_structure()
