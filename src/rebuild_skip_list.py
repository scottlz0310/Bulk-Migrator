#!/usr/bin/env python3
"""
SharePointクロールとスキップリスト再構築ツール
"""

import json
import os
import sys

from dotenv import load_dotenv

# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path, override=False)

# パス調整を最初に実行
sys.path.insert(0, os.path.dirname(__file__))

# ローカルモジュールのインポート
from structured_logger import get_structured_logger  # noqa: E402
from transfer import GraphTransferClient  # noqa: E402


def crawl_sharepoint():
    """SharePointの指定フォルダ配下をクロールしてファイルリストを生成"""
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    TENANT_ID = os.getenv("TENANT_ID")
    SITE_ID = os.getenv("DESTINATION_SHAREPOINT_SITE_ID")
    DRIVE_ID = os.getenv("DESTINATION_SHAREPOINT_DRIVE_ID")

    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)

    # 環境変数からSharePointフォルダパスを取得
    sharepoint_folder = os.getenv("DESTINATION_SHAREPOINT_DOCLIB", "TEST-Sharepoint")
    structured_logger = get_structured_logger("rebuild_skip_list")
    structured_logger.info("SharePointクロール開始", folder=sharepoint_folder)

    # SharePoint側のファイルリストを取得（既存のlist_drive_itemsを使用）
    sharepoint_files = client.list_drive_items(sharepoint_folder)

    # ファイル情報を整理してフルパスを生成
    sharepoint_file_list = []
    for _i, item in enumerate(sharepoint_files):
        # SharePoint側のパス情報を再構築
        file_path = item.get("parentReference", {}).get("path", "")

        # パスから指定フォルダ以降を抽出
        if f"/{sharepoint_folder}" in file_path:
            relative_path = file_path.split(f"/{sharepoint_folder}")[1]
            if relative_path.startswith("/"):
                relative_path = relative_path[1:]
            full_path = (
                os.path.join(sharepoint_folder, relative_path, item["name"]).replace("\\", "/")
                if relative_path
                else f"{sharepoint_folder}/{item['name']}"
            )
        else:
            full_path = f"{sharepoint_folder}/{item['name']}"

        sharepoint_file_list.append(
            {
                "name": item["name"],
                "path": full_path,
                "size": item.get("size"),
                "lastModifiedDateTime": item.get("lastModifiedDateTime"),
                "id": item.get("id"),
            }
        )

        # 1000件ごとに進捗ログを出力
        if len(sharepoint_file_list) % 1000 == 0:
            from src.logger import logger

            logger.info(f"SharePointクロール進捗: {len(sharepoint_file_list)}ファイル処理済み")

    # SharePointファイルリストを保存
    os.makedirs("logs", exist_ok=True)
    try:
        from src.config_manager import get_sharepoint_current_files_path

        sharepoint_files_path = get_sharepoint_current_files_path()
    except ImportError:
        sharepoint_files_path = "logs/sharepoint_current_files.json"

    with open(sharepoint_files_path, "w", encoding="utf-8") as f:
        json.dump(sharepoint_file_list, f, ensure_ascii=False, indent=2)

    structured_logger.info("SharePointクロール完了", file_count=len(sharepoint_file_list))
    return sharepoint_file_list


def crawl_onedrive():
    """OneDriveの指定フォルダをクロールしてファイルリストを生成"""
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    TENANT_ID = os.getenv("TENANT_ID")
    SITE_ID = os.getenv("DESTINATION_SHAREPOINT_SITE_ID")
    DRIVE_ID = os.getenv("DESTINATION_SHAREPOINT_DRIVE_ID")
    USER_PRINCIPAL_NAME = os.getenv("SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME")

    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)

    # 環境変数からOneDriveフォルダパスを取得
    onedrive_folder = os.getenv("SOURCE_ONEDRIVE_FOLDER_PATH", "TEST-Onedrive")
    structured_logger = get_structured_logger("rebuild_skip_list")
    structured_logger.info("OneDriveクロール開始", folder=onedrive_folder)

    file_targets = client.collect_file_targets_from_onedrive(
        folder_path=onedrive_folder,
        user_principal_name=USER_PRINCIPAL_NAME,
        drive_id=None,
    )

    # OneDriveファイルリストを保存
    try:
        from src.config_manager import get_onedrive_files_path

        onedrive_files_path = get_onedrive_files_path()
    except ImportError:
        onedrive_files_path = "logs/onedrive_files.json"

    with open(onedrive_files_path, "w", encoding="utf-8") as f:
        json.dump(file_targets, f, ensure_ascii=False, indent=2)

    structured_logger.info("OneDriveクロール完了", file_count=len(file_targets))
    return file_targets


def create_skip_list_from_sharepoint(onedrive_files, sharepoint_files):
    """SharePointの転送済みファイルからスキップリストを構築"""
    structured_logger = get_structured_logger("rebuild_skip_list")
    structured_logger.info("スキップリスト再構築開始")

    # 環境変数からフォルダパスを取得
    onedrive_folder = os.getenv("SOURCE_ONEDRIVE_FOLDER_PATH", "TEST-Onedrive")
    sharepoint_folder = os.getenv("DESTINATION_SHAREPOINT_DOCLIB", "TEST-Sharepoint")

    # SharePointファイルの名前とパスのみでマッピング作成（サイズ・メタデータ無視）
    sharepoint_map = {}
    for sp_file in sharepoint_files:
        # SharePointフォルダをOneDriveフォルダに変換したパスを作成
        converted_path = sp_file["path"].replace(sharepoint_folder, onedrive_folder)
        key = (sp_file["name"], converted_path)
        sharepoint_map[key] = sp_file

    skip_list = []
    matched_count = 0

    for od_file in onedrive_files:
        # OneDriveファイルに対応するSharePointファイルを検索（サイズ・メタデータ無視）
        key = (od_file["name"], od_file["path"])
        if key in sharepoint_map:
            skip_list.append(od_file)
            matched_count += 1
            structured_logger.debug("ファイルマッチ", file_path=od_file["path"])

    # スキップリストを保存
    # スキップリストを保存
    try:
        from src.config_manager import get_skip_list_path

        skip_list_path = get_skip_list_path()
    except ImportError:
        skip_list_path = "logs/skip_list.json"

    with open(skip_list_path, "w", encoding="utf-8") as f:
        json.dump(skip_list, f, ensure_ascii=False, indent=2)

    structured_logger.info(
        "スキップリスト構築完了",
        matched_count=matched_count,
        total_onedrive_files=len(onedrive_files),
        pending_transfer=len(onedrive_files) - matched_count,
    )

    return skip_list


if __name__ == "__main__":
    # 1. SharePointをクロール
    sharepoint_files = crawl_sharepoint()

    # 2. OneDriveをクロール
    onedrive_files = crawl_onedrive()

    # 3. スキップリストを構築
    skip_list = create_skip_list_from_sharepoint(onedrive_files, sharepoint_files)
