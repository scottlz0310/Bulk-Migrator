#!/usr/bin/env python3
"""
転送ログ（SUCCESS/ERROR/SKIP）とスキップリストの突き合わせ検証スクリプト。

【目的】
  - 転送成功ファイルがスキップリストに正しく登録されているか検証
【使い方】
  $ python utils/verify_transfer_log.py
  （logs/transfer.log, logs/skip_list.json を比較）
"""
import re
import json
from pathlib import Path
import sys
import os

# src/の設定管理を使用
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
try:
    from config_manager import get_transfer_log_path, get_skip_list_path
except ImportError:
    def get_transfer_log_path():
        return 'logs/transfer_start_success_error.log'
    def get_skip_list_path():
        return 'logs/skip_list.json'

def load_skiplist(path):
    with open(path, encoding='utf-8') as f:
        return set((f['path'], f.get('id')) for f in json.load(f))

def main():
    log_path = Path(get_transfer_log_path())
    skiplist_path = Path(get_skip_list_path())
    if not log_path.exists():
        print(f"{log_path} が見つかりません")
        return
    if not skiplist_path.exists():
        print(f"{skiplist_path} が見つかりません")
        return
    skiplist = load_skiplist(skiplist_path)
    
    success_files = set()
    with open(log_path, encoding='utf-8') as f:
        for line in f:
            m = re.search(r'SUCCESS: (.+?) \[', line)
            if m:
                path = m.group(1)
                success_files.add(path)
    
    print(f"SUCCESSログ件数: {len(success_files)}")
    # スキップリストに含まれていない成功ファイル
    not_in_skiplist = [p for p in success_files if not any(p == s[0] for s in skiplist)]
    print(f"スキップリスト未登録のSUCCESS: {len(not_in_skiplist)} 件")
    if not_in_skiplist:
        print("例:")
        for p in not_in_skiplist[:10]:
            print(f"  {p}")

if __name__ == "__main__":
    main()
