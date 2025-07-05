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
from pathlib import Path

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def main():
    sharepoint_path = Path('logs/sharepoint_current_files.json')
    skiplist_path = Path('logs/skip_list.json')
    
    sharepoint = load_json(sharepoint_path)
    skiplist = load_json(skiplist_path)
    
    sharepoint_set = set((f['path'], f.get('id')) for f in sharepoint)
    skiplist_set = set((f['path'], f.get('id')) for f in skiplist)
    
    only_in_sharepoint = sharepoint_set - skiplist_set
    only_in_skiplist = skiplist_set - sharepoint_set
    
    print(f"SharePoint現状ファイル数: {len(sharepoint_set)}")
    print(f"スキップリスト件数: {len(skiplist_set)}")
    print(f"SharePointにしかない: {len(only_in_sharepoint)} 件")
    print(f"スキップリストにしかない: {len(only_in_skiplist)} 件")
    
    if only_in_sharepoint:
        print("\n--- SharePointにしかないファイル例 ---")
        for p, _ in list(only_in_sharepoint)[:10]:
            print(f"  {p}")
    if only_in_skiplist:
        print("\n--- スキップリストにしかないファイル例 ---")
        for p, _ in list(only_in_skiplist)[:10]:
            print(f"  {p}")

if __name__ == "__main__":
    main()
