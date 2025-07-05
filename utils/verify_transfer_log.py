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

def load_skiplist(path):
    with open(path, encoding='utf-8') as f:
        return set((f['path'], f.get('id')) for f in json.load(f))

def main():
    log_path = Path('logs/transfer.log')
    skiplist_path = Path('logs/skip_list.json')
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
