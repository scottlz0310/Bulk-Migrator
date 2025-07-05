#!/usr/bin/env python3
"""
OneDriveのファイルIDを使った直接アクセステスト
"""

import os
import sys
import json
from dotenv import load_dotenv

# プロジェクトルートの.envを読み込む
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=False)

# パス調整
sys.path.insert(0, os.path.dirname(__file__))

from src.auth import GraphAuthenticator
import requests

def test_onedrive_file_access():
    """OneDriveファイルのアクセス方法をテストする"""
    try:
        # ファイルリストを読み込み
        with open('logs/onedrive_filelist.json', 'r', encoding='utf-8') as f:
            file_list = json.load(f)
        
        if not file_list:
            print("ファイルリストが空です")
            return
            
        # 最初のファイルでテスト
        test_file = file_list[0]
        print(f"テストファイル: {test_file['name']}")
        print(f"パス: {test_file['path']}")
        print(f"ファイルID: {test_file['id']}")
        
        # 認証取得
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET') 
        tenant_id = os.getenv('TENANT_ID')
        auth = GraphAuthenticator(client_id, client_secret, tenant_id)
        token = auth.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        onedrive_drive_id = os.getenv('SOURCE_ONEDRIVE_DRIVE_ID')
        print(f"OneDriveドライブID: {onedrive_drive_id}")
        
        # 方法1: ファイルIDを使った直接アクセス
        print("\n=== 方法1: ファイルIDを使った直接アクセス ===")
        file_id_url = f"https://graph.microsoft.com/v1.0/drives/{onedrive_drive_id}/items/{test_file['id']}"
        resp = requests.get(file_id_url, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✓ ファイルIDでのアクセス成功")
            data = resp.json()
            print(f"ファイル名: {data.get('name')}")
            print(f"サイズ: {data.get('size')}")
            
            # ダウンロードURLを取得
            download_url = data.get('@microsoft.graph.downloadUrl')
            if download_url:
                print(f"ダウンロードURL: {download_url[:100]}...")
                # 実際にダウンロードできるかテスト
                download_resp = requests.head(download_url)
                print(f"ダウンロード可能: {download_resp.status_code == 200}")
        else:
            print(f"✗ ファイルIDでのアクセス失敗: {resp.text}")
        
        # 方法2: パスベースアクセス（現在の方法）
        print("\n=== 方法2: パスベースアクセス（現在の方法） ===")
        import urllib.parse
        src_path = test_file['path']
        encoded_path = '/'.join([urllib.parse.quote(part) for part in src_path.split('/')])
        path_url = f"https://graph.microsoft.com/v1.0/drives/{onedrive_drive_id}/root:/{encoded_path}:/content"
        print(f"URL: {path_url}")
        resp = requests.head(path_url, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✓ パスベースアクセス成功")
        else:
            print(f"✗ パスベースアクセス失敗")
            
        # 方法3: ルートフォルダを確認
        print("\n=== 方法3: ルートフォルダの確認 ===")
        root_url = f"https://graph.microsoft.com/v1.0/drives/{onedrive_drive_id}/root/children"
        resp = requests.get(root_url, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('value', [])
            print(f"ルートディレクトリ内のアイテム数: {len(items)}")
            
            # TEST-Onedriveフォルダを探す
            test_folder = None
            for item in items:
                print(f"  - {item.get('name')} ({item.get('id')})")
                if item.get('name') == 'TEST-Onedrive':
                    test_folder = item
                    
            if test_folder:
                print(f"\nTEST-Onedriveフォルダ発見: {test_folder['id']}")
                # TEST-Onedriveフォルダの中身を確認
                folder_url = f"https://graph.microsoft.com/v1.0/drives/{onedrive_drive_id}/items/{test_folder['id']}/children"
                folder_resp = requests.get(folder_url, headers=headers)
                if folder_resp.status_code == 200:
                    folder_data = folder_resp.json()
                    folder_items = folder_data.get('value', [])
                    print(f"TEST-Onedriveフォルダ内のアイテム数: {len(folder_items)}")
                    
                    # テストファイルを探す
                    for item in folder_items[:5]:  # 最初の5個だけ表示
                        print(f"  - {item.get('name')} (ID: {item.get('id')})")
                        if item.get('name') == test_file['name']:
                            print(f"    ✓ テストファイルが見つかりました!")
                            print(f"    リストID: {test_file['id']}")
                            print(f"    実際ID: {item.get('id')}")
                            if test_file['id'] != item.get('id'):
                                print(f"    ⚠️ IDが一致しません!")
                        
                        # Musicフォルダがあれば中身も確認
                        if item.get('name') == 'Music' and 'folder' in item:
                            print(f"\n=== Musicフォルダの中身確認 ===")
                            music_url = f"https://graph.microsoft.com/v1.0/drives/{onedrive_drive_id}/items/{item['id']}/children"
                            music_resp = requests.get(music_url, headers=headers)
                            if music_resp.status_code == 200:
                                music_data = music_resp.json()
                                music_items = music_data.get('value', [])
                                print(f"Musicフォルダ内のアイテム数: {len(music_items)}")
                                
                                # 最初の5個のファイルを表示
                                for music_item in music_items[:5]:
                                    print(f"  - {music_item.get('name')} (ID: {music_item.get('id')})")
                                    if music_item.get('name') == test_file['name']:
                                        print(f"    ✓ テストファイルがMusicフォルダ内で見つかりました!")
                                        print(f"    リストID: {test_file['id']}")
                                        print(f"    実際ID: {music_item.get('id')}")
                                        if test_file['id'] == music_item.get('id'):
                                            print(f"    ✓ IDが一致します!")
                                        else:
                                            print(f"    ⚠️ IDが一致しません!")
                            else:
                                print(f"Musicフォルダアクセス失敗: {music_resp.status_code}")
            else:
                print("✗ TEST-Onedriveフォルダが見つかりません")
        else:
            print(f"✗ ルートフォルダアクセス失敗: {resp.text}")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_onedrive_file_access()
