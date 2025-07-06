#!/usr/bin/env python3
"""
転送ログ・SharePoint現状・スキップリストの統計情報を集計するスクリプト。

【目的】
  - 転送成功数・エラー数・スキップ数・成功率などを集計
  - SharePoint現状ファイル数・スキップリスト件数も表示
【使い方】
  $ python utils/collect_stats.py
  （logs/transfer.log, logs/sharepoint_current_files.json, logs/skip_list.json を集計）
"""
import json
import re
from pathlib import Path

def main():
    log_path = Path('logs/transfer_start_success_error.log')
    sharepoint_path = Path('logs/sharepoint_current_files.json')
    skiplist_path = Path('logs/skip_list.json')

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
        print("logs/transfer.log が見つかりません (SUCCESS/ERROR/合計/成功率: 0)")

    # SharePoint現状
    if sharepoint_path.exists():
        with open(sharepoint_path, encoding='utf-8') as f:
            sharepoint = json.load(f)
        print(f"SharePoint現状ファイル数: {len(sharepoint)}")
    else:
        print("logs/sharepoint_current_files.json が見つかりません (SharePoint現状ファイル数: 0)")

    # スキップリスト
    if skiplist_path.exists():
        with open(skiplist_path, encoding='utf-8') as f:
            skiplist = json.load(f)
        print(f"スキップリスト件数: {len(skiplist)}")
    else:
        print("logs/skip_list.json が見つかりません (スキップリスト件数: 0)")

if __name__ == "__main__":
    main()
