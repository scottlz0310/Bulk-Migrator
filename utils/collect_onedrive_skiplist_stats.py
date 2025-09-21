#!/usr/bin/env python3
"""
OneDrive現状ファイル一覧（onedrive_files.json）とスキップリスト（skip_list.json）の件数・重複・差分を集計・可視化するスクリプト。

【使い方】
  $ python utils/collect_onedrive_skiplist_stats.py
"""

import json
from pathlib import Path

onedrive_path = Path("logs/onedrive_files.json")
skiplist_path = Path("logs/skip_list.json")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    onedrive = load_json(onedrive_path)
    skiplist = load_json(skiplist_path)

    # パスの集合
    onedrive_paths = set(e["path"] for e in onedrive)
    skiplist_paths = set(e["path"] for e in skiplist)

    # 完全一致
    onedrive_paths & skiplist_paths
    only_onedrive = onedrive_paths - skiplist_paths
    only_skiplist = skiplist_paths - onedrive_paths

    # 例として先頭5件だけ表示
    if only_onedrive:
        for _p in list(only_onedrive)[:5]:
            pass
    if only_skiplist:
        for _p in list(only_skiplist)[:5]:
            pass

    # name重複チェック
    [e["name"] for e in onedrive]
    [e["name"] for e in skiplist]


if __name__ == "__main__":
    main()
