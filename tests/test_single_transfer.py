#!/usr/bin/env python3
"""
1ファイルのみのテスト転送（パス確認用）
"""
import sys
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=False)

sys.path.insert(0, 'src')
from transfer import GraphTransferClient
from skiplist import load_skip_list, is_skipped, add_to_skip_list

# 設定読み込み
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
SITE_ID = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
DRIVE_ID = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')
USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')

client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)

# 1つのファイルだけを転送対象にする
file_targets = client.collect_file_targets_from_onedrive(
    folder_path="TEST-Onedrive",
    user_principal_name=USER_PRINCIPAL_NAME,
    drive_id=None
)

# スキップリストに未登録の最初のファイルを選択
skip_list = load_skip_list('logs/skip_list.json')
target_file = None
for f in file_targets:
    if not is_skipped(f, skip_list):
        target_file = f
        break

if target_file:
    print(f"=== テスト転送: {target_file['name']} ===")
    print(f"パス: {target_file['path']}")
    try:
        result = client.upload_file_to_sharepoint(
            target_file,
            src_root="TEST-Onedrive",
            dst_root="TEST-Sharepoint",
            timeout=10
        )
        print("転送成功！")
        
        # スキップリストに追加
        add_to_skip_list(target_file, 'logs/skip_list.json')
        print("スキップリストに追加完了")
    except Exception as e:
        print(f"転送エラー: {e}")
else:
    print("転送対象ファイルが見つかりません（全てスキップ済み）")
