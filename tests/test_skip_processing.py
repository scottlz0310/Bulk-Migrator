#!/usr/bin/env python3
"""
複数ファイルのスキップ処理テスト
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

# ファイルリストを取得
file_targets = client.collect_file_targets_from_onedrive(
    folder_path="TEST-Onedrive",
    user_principal_name=USER_PRINCIPAL_NAME,
    drive_id=None
)

print(f"総ファイル数: {len(file_targets)}")

# スキップリストを確認
skip_list = load_skip_list('logs/skip_list.json')
print(f"スキップ済みファイル数: {len(skip_list)}")

# 転送対象（スキップされていない）ファイルを確認
pending_files = [f for f in file_targets if not is_skipped(f, skip_list)]
print(f"転送対象ファイル数: {len(pending_files)}")

if pending_files:
    print("\n転送対象ファイル（最初の5つ）:")
    for i, f in enumerate(pending_files[:5]):
        print(f"  {i+1}. {f['path']}")
    
    # 3つのファイルを追加で転送してスキップリストに追加
    print(f"\n3ファイルを転送してスキップリストに追加します...")
    for i, target_file in enumerate(pending_files[:3]):
        try:
            print(f"\n[{i+1}/3] 転送: {target_file['name']}")
            result = client.upload_file_to_sharepoint(
                target_file,
                src_root="TEST-Onedrive",
                dst_root="TEST-Sharepoint",
                timeout=10
            )
            add_to_skip_list(target_file, 'logs/skip_list.json')
            print(f"✅ 成功")
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    # 更新後のスキップリスト確認
    skip_list_updated = load_skip_list('logs/skip_list.json')
    print(f"\n更新後のスキップ済みファイル数: {len(skip_list_updated)}")
    
else:
    print("✅ 全ファイルがスキップ済みです！")
