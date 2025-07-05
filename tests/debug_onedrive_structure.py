#!/usr/bin/env python3
"""
OneDriveの構造を確認するデバッグスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# プロジェクトルートの.envを読み込む
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=False)

# パス調整
sys.path.insert(0, os.path.dirname(__file__))

from src.file_crawler import create_transfer_client
import requests

def explore_onedrive_structure():
    """OneDriveの構造を探索する"""
    try:
        client = create_transfer_client()
        token = client.auth.get_access_token()
        
        # OneDriveユーザーのルートディレクトリ内容を取得
        user_principal_name = os.getenv('ONEDRIVE_USER_PRINCIPAL_NAME')
        print(f"OneDrive User: {user_principal_name}")
        
        # ルートディレクトリの内容を取得
        url = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}/drive/root/children"
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"リクエストURL: {url}")
        resp = requests.get(url, headers=headers)
        
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('value', [])
            print(f"ルートディレクトリ内のアイテム数: {len(items)}")
            
            for item in items:
                name = item.get('name', 'N/A')
                item_type = 'folder' if 'folder' in item else 'file'
                size = item.get('size', 0) if item_type == 'file' else '-'
                print(f"  {name} ({item_type}, size={size})")
                
                # TEST-Onedriveフォルダが見つかったら、その中身も確認
                if name == 'TEST-Onedrive' and item_type == 'folder':
                    print(f"\n=== TEST-Onedriveフォルダの中身 ===")
                    test_url = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}/drive/root:/TEST-Onedrive:/children"
                    test_resp = requests.get(test_url, headers=headers)
                    
                    if test_resp.status_code == 200:
                        test_data = test_resp.json()
                        test_items = test_data.get('value', [])
                        print(f"TEST-Onedriveフォルダ内のアイテム数: {len(test_items)}")
                        
                        for test_item in test_items[:10]:  # 最初の10個だけ表示
                            test_name = test_item.get('name', 'N/A')
                            test_type = 'folder' if 'folder' in test_item else 'file'
                            test_size = test_item.get('size', 0) if test_type == 'file' else '-'
                            print(f"    {test_name} ({test_type}, size={test_size})")
                    else:
                        print(f"TEST-Onedriveフォルダアクセスエラー: {test_resp.status_code} - {test_resp.text}")
        else:
            print(f"エラー: {resp.text}")
            
        # 実際のファイルアクセスを試してみる
        print(f"\n=== ファイルアクセステスト ===")
        test_file_path = "TEST-Onedrive/5D1D16873657D2D1-3C285FB0ED3F9DA3.itc2"
        file_url = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}/drive/root:/{test_file_path}"
        file_resp = requests.get(file_url, headers=headers)
        print(f"ファイル情報取得: {file_url}")
        print(f"Status: {file_resp.status_code}")
        if file_resp.status_code != 200:
            print(f"エラー詳細: {file_resp.text}")
        else:
            file_data = file_resp.json()
            print(f"ファイル名: {file_data.get('name')}")
            print(f"サイズ: {file_data.get('size')}")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    explore_onedrive_structure()
