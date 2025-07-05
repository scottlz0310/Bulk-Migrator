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
    log_path = Path('logs/transfer.log')
    sharepoint_path = Path('logs/sharepoint_current_files.json')
    skiplist_path = Path('logs/skip_list.json')
    
    with open(log_path, encoding='utf-8') as f:
        lines = f.readlines()
    success = sum(1 for l in lines if 'SUCCESS:' in l)
    error = sum(1 for l in lines if 'ERROR:' in l)
    skip = sum(1 for l in lines if 'SKIP:' in l)
    total = success + error + skip
    print(f"SUCCESS: {success}")
    print(f"ERROR: {error}")
    print(f"SKIP: {skip}")
    print(f"合計: {total}")
    if total:
        print(f"成功率: {success/total*100:.2f}%")
    
    with open(sharepoint_path, encoding='utf-8') as f:
        sharepoint = json.load(f)
    with open(skiplist_path, encoding='utf-8') as f:
        skiplist = json.load(f)
    print(f"SharePoint現状ファイル数: {len(sharepoint)}")
    print(f"スキップリスト件数: {len(skiplist)}")

if __name__ == "__main__":
    main()
