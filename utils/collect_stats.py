#!/usr/bin/env python3
"""
転送ログ・SharePoint現状・スキップリストの統計情報を集計するスクリプト。

【目的】
  - 転送成功数・エラー数・スキップ数・成功率などを集計
  - SharePoint現状ファイル数・スキップリスト件数も表示
【使い方】
  $ python utils/collect_stats.py
  （logs/transfer_start_success_error.log*, logs/sharepoint_current_files.json, logs/skip_list.json を集計）
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
    import glob
    log_pattern = get_transfer_log_path() + '*'
    log_files = glob.glob(log_pattern)
    sharepoint_path = Path(get_sharepoint_current_files_path())
    skiplist_path = Path(get_skip_list_path())

    # 転送ログ（複数ファイル対応）
    total_success = 0
    total_error = 0
    if log_files:
        for log_file in log_files:
            with open(log_file, encoding='utf-8') as f:
                lines = f.readlines()
            success = sum(1 for l in lines if 'SUCCESS:' in l)
            error = sum(1 for l in lines if 'ERROR:' in l)
            total = success + error
            rate = (success / total * 100) if total else 0
            print(f"{log_file}: SUCCESS={success}, ERROR={error}, 合計={total}, 成功率={rate:.2f}%")
            total_success += success
            total_error += error
        grand_total = total_success + total_error
        grand_rate = (total_success / grand_total * 100) if grand_total else 0
        print(f"Total SUCCESS: {total_success}, ERROR: {total_error}, 合計: {grand_total}, 成功率: {grand_rate:.2f}%")
    else:
        print(f"{log_pattern} が見つかりません (SUCCESS/ERROR/合計/成功率: 0)")

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
