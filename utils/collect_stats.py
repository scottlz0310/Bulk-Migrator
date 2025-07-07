#!/usr/bin/env python3
"""
転送ログ・SharePoint現状・スキップリストの統計情報を集計するスクリプト。

【目的】
  - 転送成功数・エラー数・スキップ数・成功率などを集計
  - SharePoint現状ファイル数・スキップリスト件数も表示
【使い方】
  $ python utils/collect_stats.py
  （logs/transfer_start_success_error.log, logs/sharepoint_current_files.json, logs/skip_list.json を集計）
"""
import json
import re
import sys
import os
from pathlib import Path

# src/の設定管理を使用
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
try:
    from config_manager import get_transfer_log_path, get_sharepoint_current_files_path, get_skip_list_path
except ImportError:
    # フォールバック
    def get_transfer_log_path():
        return 'logs/transfer_start_success_error.log'
    def get_sharepoint_current_files_path():
        return 'logs/sharepoint_current_files.json'
    def get_skip_list_path():
        return 'logs/skip_list.json'

def main():
    log_path = Path(get_transfer_log_path())
    sharepoint_path = Path(get_sharepoint_current_files_path())
    skiplist_path = Path(get_skip_list_path())

    # 転送ログ
    if log_path.exists():
        with open(log_path, encoding='utf-8') as f:
            lines = f.readlines()
        success = sum(1 for l in lines if 'SUCCESS:' in l)
        error = sum(1 for l in lines if 'ERROR:' in l)
        total = success + error
        print(f"SUCCESS: {success}")
        print(f"ERROR: {error}")
        print(f"合計: {total}")
        if total:
            print(f"成功率: {success/total*100:.2f}%")
    else:
        print(f"{log_path} が見つかりません (SUCCESS/ERROR/合計/成功率: 0)")

    # SharePoint現状
    if sharepoint_path.exists():
        with open(sharepoint_path, encoding='utf-8') as f:
            sharepoint = json.load(f)
        print(f"SharePoint現状ファイル数: {len(sharepoint)}")
    else:
        print(f"{sharepoint_path} が見つかりません (SharePoint現状ファイル数: 0)")

    # スキップリスト
    if skiplist_path.exists():
        with open(skiplist_path, encoding='utf-8') as f:
            skiplist = json.load(f)
        print(f"スキップリスト件数: {len(skiplist)}")
    else:
        print(f"{skiplist_path} が見つかりません (スキップリスト件数: 0)")

if __name__ == "__main__":
    main()
