#!/usr/bin/env python3
"""
SharePoint側のディレクトリ構造確認
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv('.env', override=False)
sys.path.insert(0, 'src')
from transfer import GraphTransferClient

def debug_sharepoint_structure():
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    SITE_ID = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
    DRIVE_ID = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')

    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)
    
    print("=== SharePoint TEST-Sharepoint 配下の構造確認 ===")
    
    # API呼び出しで直接フォルダ構造を取得
    import requests
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/TEST-Sharepoint:/children"
    headers = client._headers()
    
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        
        folders = []
        files = []
        
        for item in data.get('value', []):
            if item.get('folder'):
                folders.append(item['name'])
            else:
                files.append(item['name'])
        
        print(f"📁 フォルダ数: {len(folders)}")
        for folder in folders[:5]:  # 最初の5つのフォルダを表示
            print(f"  📁 {folder}")
        if len(folders) > 5:
            print(f"  ... (他 {len(folders) - 5} 個のフォルダ)")
            
        print(f"📄 ファイル数: {len(files)}")
        for file in files[:5]:  # 最初の5つのファイルを表示
            print(f"  📄 {file}")
        if len(files) > 5:
            print(f"  ... (他 {len(files) - 5} 個のファイル)")
            
        print(f"\n総アイテム数: {len(data.get('value', []))}")
        
    else:
        print(f"エラー: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    debug_sharepoint_structure()
