#!/usr/bin/env python3
"""
ファイル名を入力して、onedrive_files.jsonとskip_list.jsonの両方から該当エントリを詳細比較するスクリプト。

【目的】
  - OneDrive現状ファイルとスキップリストの差異を個別に比較・検証
【使い方】
  $ python utils/compare_entry_detail.py
  → ファイル名を入力すると両リストから該当エントリを抽出・表示
"""

import json
from pathlib import Path

onedrive_path = Path("logs/onedrive_files.json")
skiplist_path = Path("logs/skip_list.json")

with open(onedrive_path, encoding="utf-8") as f:
    onedrive = json.load(f)
with open(skiplist_path, encoding="utf-8") as f:
    skiplist = json.load(f)

filename = input("検索したいファイル名（部分一致OK）を入力してください: ").strip()

found = False
for entry in onedrive:
    if filename in entry.get("name", "") or filename in entry.get("path", ""):
        found = True
if not found:
    pass

found = False
for entry in skiplist:
    if filename in entry.get("name", "") or filename in entry.get("path", ""):
        found = True
if not found:
    pass
