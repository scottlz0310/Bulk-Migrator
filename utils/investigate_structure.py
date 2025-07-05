#!/usr/bin/env python3
"""
OneDriveの詳細なディレクトリ構造を調査
"""
import sys
import os
from dotenv import load_dotenv
import requests

load_dotenv('.env', override=False)
sys.path.insert(0, 'src')
from src.auth import GraphAuthenticator

def investigate_onedrive_structure():
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')

    auth = GraphAuthenticator(CLIENT_ID, CLIENT_SECRET, TENANT_ID)
    headers = {"Authorization": f"Bearer {auth.get_access_token()}"}
    
    def explore_folder(folder_path="", indent=""):
        """再帰的にフォルダ構造を探索"""
        if folder_path:
            url = f"https://graph.microsoft.com/v1.0/users/{USER_PRINCIPAL_NAME}/drive/root:/{folder_path}:/children"
        else:
            url = f"https://graph.microsoft.com/v1.0/users/{USER_PRINCIPAL_NAME}/drive/root/children"
        
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"{indent}❌ エラー: {resp.status_code}")
            return
            
        data = resp.json()
        items = data.get('value', [])
        
        for item in items:
            if item.get('folder'):
                print(f"{indent}📁 {item['name']}/ (子: {item.get('folder', {}).get('childCount', 0)})")
                # サブフォルダを再帰探索
                sub_path = os.path.join(folder_path, item['name']).replace("\\", "/") if folder_path else item['name']
                explore_folder(sub_path, indent + "  ")
            else:
                size = item.get('size', 0)
                print(f"{indent}📄 {item['name']} ({size} bytes)")
    
    print("=== OneDriveルート配下の完全な構造 ===")
    explore_folder()
    
    print("\n=== TEST-Onedrive 配下の詳細構造 ===")
    explore_folder("TEST-Onedrive")

if __name__ == "__main__":
    investigate_onedrive_structure()
