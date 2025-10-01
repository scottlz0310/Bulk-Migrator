#!/usr/bin/env python3
"""
転送ログ・SharePoint現状・スキップリストの統計情報を集計するスクリプト。

【目的】
  - 転送成功数・エラー数・スキップ数・成功率などを集計
  - SharePoint現状ファイル数・スキップリスト件数も表示
【使い方】
  $ python utils/collect_stats.py
  （logs/transfer_start_success_error.log*,
   logs/sharepoint_current_files.json, logs/skip_list.json を集計）
"""

import json
import os
import sys
from pathlib import Path

# src/の設定管理を使用
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
try:
    from config_manager import (
        get_sharepoint_current_files_path,
        get_skip_list_path,
        get_transfer_log_path,
    )
except ImportError:
    # フォールバック
    def get_transfer_log_path():
        return "logs/transfer_start_success_error.log"

    def get_sharepoint_current_files_path():
        return "logs/sharepoint_current_files.json"

    def get_skip_list_path():
        return "logs/skip_list.json"


def main():
    import glob

    log_pattern = get_transfer_log_path() + "*"
    log_files = glob.glob(log_pattern)
    sharepoint_path = Path(get_sharepoint_current_files_path())
    skiplist_path = Path(get_skip_list_path())

    # 転送ログ（複数ファイル対応）
    total_success = 0
    total_error = 0
    if log_files:
        for log_file in log_files:
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()
            success = sum(1 for line in lines if "SUCCESS:" in line)
            error = sum(1 for line in lines if "ERROR:" in line)
            total = success + error
            (success / total * 100) if total else 0
            total_success += success
            total_error += error
        grand_total = total_success + total_error
        (total_success / grand_total * 100) if grand_total else 0
    else:
        pass

    # SharePoint現状
    if sharepoint_path.exists():
        with open(sharepoint_path, encoding="utf-8") as f:
            json.load(f)
    else:
        pass

    # スキップリスト
    if skiplist_path.exists():
        with open(skiplist_path, encoding="utf-8") as f:
            json.load(f)
    else:
        pass


if __name__ == "__main__":
    main()
