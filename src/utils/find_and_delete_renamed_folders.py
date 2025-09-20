#!/usr/bin/env python3
"""
SharePoint上のリネーム（例: 'XXXXX 1', 'XXXXX 2'）フォルダを抽出し、
リスト出力またはAPIで削除するユーティリティ。

デフォルト: リネームフォルダ一覧を出力
--delete オプション: APIで実際に削除を実行

使い方:
  # プロジェクトルートで実行（推奨）
  $ python -m src.utils.find_and_delete_renamed_folders
  $ python -m src.utils.find_and_delete_renamed_folders --delete

  # 旧: src/utils/から直接実行したい場合はimport修正が必要
  # $ python src/utils/find_and_delete_renamed_folders.py
"""

import argparse
import json
import os
import re
import sys

from dotenv import load_dotenv

# プロジェクトルートをimportパスに追加（srcをimportルートにする）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from src.transfer import GraphTransferClient

# .env読み込み
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path, override=False)

# SharePoint API認証情報
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
SITE_ID = os.getenv("DESTINATION_SHAREPOINT_SITE_ID")
DRIVE_ID = os.getenv("DESTINATION_SHAREPOINT_DRIVE_ID")
SHAREPOINT_ROOT = os.getenv("DESTINATION_SHAREPOINT_DOCLIB", "TEST-Sharepoint")

# リネームパターン: 末尾に半角スペース＋数字
RENAME_PATTERN = re.compile(r".+ \d+$")


def load_sharepoint_filelist(path=None):
    # プロジェクトルート基準でlogs/を参照
    if path is None:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        path = os.path.join(root, "logs/sharepoint_current_files.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_renamed_folders(filelist):
    # フォルダのみ、かつリネームパターンに一致
    return [
        f
        for f in filelist
        if f.get("folder")
        or f.get("isFolder")
        or f.get("is_folder")
        and RENAME_PATTERN.match(f["name"])
    ]


def main():
    parser = argparse.ArgumentParser(
        description="SharePointリネームフォルダ抽出・削除ツール"
    )
    parser.add_argument(
        "--delete", action="store_true", help="APIで該当フォルダを削除する"
    )
    parser.add_argument("--verbose", action="store_true", help="詳細情報を表示する")
    args = parser.parse_args()

    filelist = load_sharepoint_filelist()
    renamed_folders = [
        f
        for f in filelist
        if RENAME_PATTERN.match(f["name"])
        and (f.get("folder") or f.get("isFolder") or f.get("is_folder"))
    ]

    if not args.delete:
        for f in renamed_folders:
            if args.verbose:
                pass
        return

    # 削除実行
    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)
    for f in renamed_folders:
        try:
            client.delete_sharepoint_item(f["id"])
            if args.verbose:
                pass
        except Exception:
            if args.verbose:
                pass


if __name__ == "__main__":
    main()
