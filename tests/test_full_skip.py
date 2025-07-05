#!/usr/bin/env python3
"""
全ファイルスキップテスト用ツール
"""
import sys
import os
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=False)

sys.path.insert(0, 'src')
from transfer import GraphTransferClient

def create_full_skip_list():
    """全ファイルをスキップリストに追加"""
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    SITE_ID = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
    DRIVE_ID = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')
    USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')

    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)

    # 全ファイルリストを取得
    file_targets = client.collect_file_targets_from_onedrive(
        folder_path="TEST-Onedrive",
        user_principal_name=USER_PRINCIPAL_NAME,
        drive_id=None
    )
    
    # 全ファイルをスキップリストに保存
    with open('logs/skip_list_full.json', 'w', encoding='utf-8') as f:
        json.dump(file_targets, f, ensure_ascii=False, indent=2)
    
    print(f"全ファイルスキップリスト作成完了: {len(file_targets)}ファイル")
    return len(file_targets)

def restore_partial_skip_list():
    """部分的なスキップリストに戻す"""
    import shutil
    shutil.copy('logs/skip_list.json', 'logs/skip_list_partial.json')
    print("部分的なスキップリストをバックアップしました")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "full":
        create_full_skip_list()
    elif len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_partial_skip_list()
    else:
        print("使用方法:")
        print("  python test_full_skip.py full     # 全ファイルスキップリスト作成")
        print("  python test_full_skip.py restore  # 部分スキップリストのバックアップ")
