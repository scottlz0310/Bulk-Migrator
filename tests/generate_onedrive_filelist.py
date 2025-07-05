import os
from dotenv import load_dotenv

# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=False)

import sys
import json

# プロジェクトルートをsys.pathに追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from src.transfer import GraphTransferClient

# .envとconfigの読み込み
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')

# OneDriveクライアント初期化（site_id, drive_idは空文字でOK）
client = GraphTransferClient(CLIENT_ID or "", CLIENT_SECRET or "", TENANT_ID or "", site_id="", drive_id="")

# OneDriveのファイルリストを取得
items = client.list_onedrive_items(user_principal_name=USER_PRINCIPAL_NAME, folder_path="TEST-Onedrive")
file_targets = client.collect_file_targets(items, parent_path="TEST-Onedrive", user_principal_name=USER_PRINCIPAL_NAME)

# 保存
os.makedirs("logs", exist_ok=True)
with open("logs/onedrive_transfer_targets.json", "w", encoding="utf-8") as f:
    json.dump(file_targets, f, ensure_ascii=False, indent=2)

print(f"ファイルリストを logs/onedrive_transfer_targets.json に保存しました。件数: {len(file_targets)}")
