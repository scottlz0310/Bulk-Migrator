#!/usr/bin/env python3
"""

初回クロール時のSharePoint現状ファイル一覧（sharepoint_current_files.json）とサクセスログ（transfer.log）を突き合わせ、
- 上書き転送されたファイル数
- 新規転送されたファイル数
- サクセスログの総件数
を集計・可視化するスクリプト。

【使い方】
  $ python utils/collect_transfer_success_stats_v2.py

※ transfer.logは1行ごとに[INFO] SUCCESS: <パス> ... の形式
"""

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

# src/の設定管理を使用
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
try:
    from config_manager import get_sharepoint_current_files_path, get_transfer_log_path
except ImportError:
    # フォールバック
    def get_transfer_log_path():
        return "logs/transfer_start_success_error.log"

    def get_sharepoint_current_files_path():
        return "logs/sharepoint_current_files.json"


def normalize_path(path, root):
    """
    指定したroot部分をパスから除去し、先頭の/を除いた相対パスに正規化
    """
    if path.startswith(root):
        path = path[len(root) :]
    return path.lstrip("/\\")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_success_paths(log_path):
    pattern = re.compile(r"SUCCESS: (.+?)(?: \[|$)")
    paths = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                paths.append(m.group(1).strip())
    return paths


def main():
    # .envからルート名を取得
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(dotenv_path, override=False)
    os.getenv("SOURCE_ONEDRIVE_FOLDER_PATH", "")
    sharepoint_root = os.getenv("DESTINATION_SHAREPOINT_DOCLIB", "")

    sharepoint_path = Path(get_sharepoint_current_files_path())
    transfer_log_path = Path(get_transfer_log_path())

    if not sharepoint_path.exists():
        return
    if not transfer_log_path.exists():
        return

    sharepoint = load_json(sharepoint_path)
    # SharePoint側のパスを正規化
    sharepoint_paths = set(
        normalize_path(e["path"], sharepoint_root) for e in sharepoint
    )
    success_paths = [
        normalize_path(p, sharepoint_root)
        for p in extract_success_paths(transfer_log_path)
    ]

    overwritten = [p for p in success_paths if p in sharepoint_paths]
    newly_created = [p for p in success_paths if p not in sharepoint_paths]

    if overwritten:
        for _p in overwritten[:5]:
            pass
    if newly_created:
        for _p in newly_created[:5]:
            pass


if __name__ == "__main__":
    main()
