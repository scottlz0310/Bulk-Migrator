#!/usr/bin/env python3
"""
スキップリストとSharePoint現状ファイルの差分・重複・漏れを検証するスクリプト。

【目的】
  - SharePoint現状ファイルとスキップリストの一致・差分を確認
【使い方】
  $ python utils/verify_skiplist_vs_sharepoint.py
  （logs/sharepoint_current_files.json, logs/skip_list.json を比較）
"""

import json
import os
from pathlib import Path


def load_config():
    """config/config.jsonと.envから必要なルート名を取得"""
    import json

    from dotenv import load_dotenv

    # プロジェクトルートを基準にパス解決
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "config" / "config.json"
    env_path = root_dir / ".env"
    # config.json
    with open(config_path, encoding="utf-8") as f:
        json.load(f)
    # .env
    if env_path.exists():
        load_dotenv(env_path)
    # OneDrive/SharePointのルート名
    onedrive_root = os.getenv("SOURCE_ONEDRIVE_FOLDER_PATH", "TEST-Onedrive")
    sharepoint_root = os.getenv("DESTINATION_SHAREPOINT_DOCLIB", "TEST-Sharepoint")
    return onedrive_root, sharepoint_root


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize_path(path, root):
    """先頭のroot部分を除去し、スラッシュを正規化"""
    # 先頭にrootがあれば除去
    if path.startswith(root):
        norm = path[len(root) :]
        # 先頭の/を除去
        if norm.startswith("/"):
            norm = norm[1:]
    else:
        norm = path
    # OS依存しないようスラッシュ統一
    return norm.replace("\\", "/").strip()


def main():
    sharepoint_path = Path("logs/sharepoint_current_files.json")
    skiplist_path = Path("logs/skip_list.json")

    onedrive_root, sharepoint_root = load_config()

    sharepoint = load_json(sharepoint_path)
    skiplist = load_json(skiplist_path)

    # 各pathからルート名を除去して比較キーを生成（パスのみ）
    sharepoint_set = set(normalize_path(f["path"], sharepoint_root) for f in sharepoint)
    skiplist_set = set(normalize_path(f["path"], onedrive_root) for f in skiplist)

    only_in_sharepoint = sharepoint_set - skiplist_set
    only_in_skiplist = skiplist_set - sharepoint_set

    if only_in_sharepoint:
        for _p in list(only_in_sharepoint)[:10]:
            pass
    if only_in_skiplist:
        for _p in list(only_in_skiplist)[:10]:
            pass


if __name__ == "__main__":
    main()
