import os
from dotenv import load_dotenv
# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=False)
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from skiplist import load_skip_list, is_skipped

# ファイルパス
SHAREPOINT_TARGETS = os.path.join(os.path.dirname(__file__), '../logs/sharepoint_transfer_targets.json')
ONEDRIVE_TARGETS = os.path.join(os.path.dirname(__file__), '../logs/onedrive_transfer_targets.json')
SKIP_LIST = os.path.join(os.path.dirname(__file__), '../logs/skip_list.json')

def load_targets(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def main():
    skip_list = load_skip_list(SKIP_LIST)
    sharepoint_targets = load_targets(SHAREPOINT_TARGETS)
    onedrive_targets = load_targets(ONEDRIVE_TARGETS)

    # SharePoint側のファイルがスキップリストに含まれるか判定
    skipped = []
    not_skipped = []
    for t in sharepoint_targets:
        if is_skipped(t, skip_list):
            skipped.append(t)
        else:
            not_skipped.append(t)
    print(f"[SharePoint] skip_list.jsonでスキップされるファイル: {len(skipped)} 件")
    print(f"[SharePoint] スキップされないファイル: {len(not_skipped)} 件")
    if not_skipped:
        print("例: スキップされないファイル")
        for t in not_skipped[:5]:
            print(f"  {t['path']} ({t['name']}, size={t['size']}, lastModified={t['lastModifiedDateTime']})")

    # OneDrive側も同様に判定（参考）
    skipped_od = []
    not_skipped_od = []
    for t in onedrive_targets:
        if is_skipped(t, skip_list):
            skipped_od.append(t)
        else:
            not_skipped_od.append(t)
    print(f"[OneDrive] skip_list.jsonでスキップされるファイル: {len(skipped_od)} 件")
    print(f"[OneDrive] スキップされないファイル: {len(not_skipped_od)} 件")
    if not_skipped_od:
        print("例: スキップされないファイル")
        for t in not_skipped_od[:5]:
            print(f"  {t['path']} ({t['name']}, size={t['size']}, lastModified={t['lastModifiedDateTime']})")

if __name__ == '__main__':
    main()
