#!/usr/bin/env python3
"""
OneDrive現状ファイル一覧（onedrive_files.json）とサクセスログ（transfer.log）を突き合わせ、
- 上書き転送されたファイル数
- 新規転送されたファイル数
- サクセスログの総件数
を集計・可視化するスクリプト。

【使い方】
  $ python utils/collect_transfer_success_stats.py

※ transfer.logは1行1エントリのJSONまたはパス文字列を想定（必要に応じて調整）
"""
import json
from pathlib import Path

onedrive_path = Path('logs/onedrive_files.json')
transfer_log_path = Path('logs/transfer.log')

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_transfer_log(path):
    """
    1行1エントリのJSONまたはパス文字列をサポート
    """
    entries = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and 'path' in obj:
                    entries.append(obj['path'])
                elif isinstance(obj, str):
                    entries.append(obj)
            except Exception:
                entries.append(line)
    return entries

def main():
    onedrive = load_json(onedrive_path)
    onedrive_paths = set(e['path'] for e in onedrive)
    transfer_paths = load_transfer_log(transfer_log_path)

    transfer_paths_set = set(transfer_paths)

    # 上書き: 既に存在していたパス
    overwritten = [p for p in transfer_paths if p in onedrive_paths]
    # 新規: onedrive_files.jsonに存在しなかったパス
    newly_created = [p for p in transfer_paths if p not in onedrive_paths]

    print(f"サクセスログ件数: {len(transfer_paths)}")
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
