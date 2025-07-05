#!/usr/bin/env python3
"""
OneDrive現状ファイル一覧（onedrive_files.json）とサクセスログ（transfer.log）を突き合わせ、
- 上書き転送されたファイル数
- 新規転送されたファイル数
- サクセスログの総件数
を集計・可視化するスクリプト。

【使い方】
  $ python utils/collect_transfer_success_stats_v2.py

※ transfer.logは1行ごとに[INFO] SUCCESS: <パス> ... の形式
"""
import json
import re
from pathlib import Path

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def extract_success_paths(log_path):
    pattern = re.compile(r'SUCCESS: (.+?)(?: \[|$)')
    paths = []
    with open(log_path, encoding='utf-8') as f:
        for line in f:
            m = pattern.search(line)
            if m:
                paths.append(m.group(1).strip())
    return paths

def main():
    onedrive_path = Path('logs/onedrive_files.json')
    transfer_log_path = Path('logs/transfer.log')

    onedrive = load_json(onedrive_path)
    onedrive_paths = set(e['path'] for e in onedrive)
    success_paths = extract_success_paths(transfer_log_path)

    overwritten = [p for p in success_paths if p in onedrive_paths]
    newly_created = [p for p in success_paths if p not in onedrive_paths]

    print(f"サクセスログ(SUCCESS)件数: {len(success_paths)}")
    print(f"上書き転送されたファイル数: {len(overwritten)}")
    print(f"新規転送されたファイル数: {len(newly_created)}")

    if overwritten:
        print("\n--- 上書き転送例（最大5件）---")
        for p in overwritten[:5]:
            print(p)
    if newly_created:
        print("\n--- 新規転送例（最大5件）---")
        for p in newly_created[:5]:
            print(p)

if __name__ == '__main__':
    main()
