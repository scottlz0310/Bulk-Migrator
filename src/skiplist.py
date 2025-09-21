import json
import os
from typing import Any

from src.filelock import FileLock

# 設定値管理を使用
try:
    from src.config_manager import get_skip_list_path

    SKIP_LIST_PATH = get_skip_list_path()
except ImportError:
    # フォールバック（直接実行時など）
    SKIP_LIST_PATH = os.path.join("logs", "skip_list.json")

LOCK_PATH = SKIP_LIST_PATH + ".lock"


def load_skip_list(path: str = SKIP_LIST_PATH) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_skip_list(skip_list: list[dict[str, Any]], path: str = SKIP_LIST_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(skip_list, f, ensure_ascii=False, indent=2)


def is_skipped(file_info: dict[str, Any], skip_list: list[dict[str, Any]]) -> bool:
    for item in skip_list:
        # パス＋ファイル名のみでスキップ判定（サイズ・タイムスタンプは無視）
        if item.get("path") == file_info.get("path") and item.get(
            "name"
        ) == file_info.get("name"):
            return True
    return False


def add_to_skip_list(
    file_info: dict[str, Any], path: str = SKIP_LIST_PATH, lock_path: str = LOCK_PATH
):
    with FileLock(lock_path, timeout=10):
        skip_list = load_skip_list(path)
        if not is_skipped(file_info, skip_list):
            skip_list.append(file_info)
            save_skip_list(skip_list, path)
