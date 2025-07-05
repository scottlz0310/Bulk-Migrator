#!/usr/bin/env python3
"""
OneDrive現状ファイル一覧（onedrive_files.json）とスキップリスト（skip_list.json）の件数・重複・差分を集計・可視化するスクリプト。

【使い方】
  $ python utils/collect_onedrive_skiplist_stats.py
"""
import json
from pathlib import Path
from collections import Counter

onedrive_path = Path('logs/onedrive_files.json')
skiplist_path = Path('logs/skip_list.json')

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def main():
    onedrive = load_json(onedrive_path)
    skiplist = load_json(skiplist_path)

    print(f"OneDrive現状ファイル数: {len(onedrive)}")
    print(f"スキップリスト件数: {len(skiplist)}")

    # パスの集合
    onedrive_paths = set(e['path'] for e in onedrive)
    skiplist_paths = set(e['path'] for e in skiplist)

    # 完全一致
    matched = onedrive_paths & skiplist_paths
    only_onedrive = onedrive_paths - skiplist_paths
    only_skiplist = skiplist_paths - onedrive_paths

    print(f"\n=== 完全一致（両方に存在）: {len(matched)} 件 ===")
    print(f"=== OneDriveのみに存在: {len(only_onedrive)} 件 ===")
    print(f"=== スキップリストのみに存在: {len(only_skiplist)} 件 ===")

    # 例として先頭5件だけ表示
    if only_onedrive:
        print("\n--- OneDriveのみに存在する例 ---")
        for p in list(only_onedrive)[:5]:
            print(p)
    if only_skiplist:
        print("\n--- スキップリストのみに存在する例 ---")
        for p in list(only_skiplist)[:5]:
            print(p)

    # name重複チェック
    onedrive_names = [e['name'] for e in onedrive]
    skiplist_names = [e['name'] for e in skiplist]
    print(f"\nOneDrive内のファイル名重複数: {sum(c>1 for c in Counter(onedrive_names).values())}")
    print(f"スキップリスト内のファイル名重複数: {sum(c>1 for c in Counter(skiplist_names).values())}")

if __name__ == '__main__':
    main()
