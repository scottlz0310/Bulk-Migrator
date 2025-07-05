import json
import os
from typing import List, Dict, Any
from src.filelock import FileLock

SKIP_LIST_PATH = os.path.join('logs', 'skip_list.json')
LOCK_PATH = SKIP_LIST_PATH + '.lock'

def load_skip_list(path: str = SKIP_LIST_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def save_skip_list(skip_list: List[Dict[str, Any]], path: str = SKIP_LIST_PATH):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(skip_list, f, ensure_ascii=False, indent=2)

def is_skipped(file_info: Dict[str, Any], skip_list: List[Dict[str, Any]]) -> bool:
    for item in skip_list:
        if (item.get('path') == file_info.get('path') and
            item.get('name') == file_info.get('name') and
            item.get('size') == file_info.get('size') and
            item.get('lastModifiedDateTime') == file_info.get('lastModifiedDateTime')):
            return True
    return False

def add_to_skip_list(file_info: Dict[str, Any], path: str = SKIP_LIST_PATH, lock_path: str = LOCK_PATH):
    with FileLock(lock_path, timeout=10):
        skip_list = load_skip_list(path)
        if not is_skipped(file_info, skip_list):
            skip_list.append(file_info)
            save_skip_list(skip_list, path)
