import os
from dotenv import load_dotenv
# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=False)
import sys
import json
import shutil
import tempfile
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from skiplist import load_skip_list, save_skip_list, is_skipped, add_to_skip_list

# テスト用一時ディレクトリとスキップリストファイルを作成
TMP_DIR = tempfile.mkdtemp()
SKIP_PATH = os.path.join(TMP_DIR, 'skip_list.json')

def setup_skiplist():
    # 既存のlogs/skip_list.jsonをコピーしてテスト用に利用
    src = os.path.join(os.path.dirname(__file__), '../logs/skip_list.json')
    if os.path.exists(src):
        shutil.copy(src, SKIP_PATH)
    else:
        save_skip_list([], SKIP_PATH)

def test_is_skipped():
    setup_skiplist()
    skip_list = load_skip_list(SKIP_PATH)
    # 既存スキップリストから1件取得
    if not skip_list:
        print('skip_list.jsonが空です')
        return
    base = skip_list[0]
    # 完全一致
    assert is_skipped(base, skip_list), '完全一致はTrueになるべき'
    # pathだけ違う
    test1 = dict(base)
    test1['path'] = base['path'] + '_diff'
    assert not is_skipped(test1, skip_list), 'path違いはFalseになるべき'
    # nameだけ違う
    test2 = dict(base)
    test2['name'] = base['name'] + '_diff'
    assert not is_skipped(test2, skip_list), 'name違いはFalseになるべき'
    # sizeだけ違う
    test3 = dict(base)
    test3['size'] = (base['size'] or 0) + 1
    assert not is_skipped(test3, skip_list), 'size違いはFalseになるべき'
    # lastModifiedDateTimeだけ違う
    test4 = dict(base)
    test4['lastModifiedDateTime'] = '2099-01-01T00:00:00Z'
    assert not is_skipped(test4, skip_list), 'lastModifiedDateTime違いはFalseになるべき'
    print('is_skipped属性判定テスト: OK')

def test_add_to_skip_list():
    setup_skiplist()
    skip_list = load_skip_list(SKIP_PATH)
    base = {'path': 'dummy/path', 'name': 'dummy.txt', 'size': 123, 'lastModifiedDateTime': '2025-01-01T00:00:00Z'}
    add_to_skip_list(base, SKIP_PATH)
    skip_list2 = load_skip_list(SKIP_PATH)
    assert is_skipped(base, skip_list2), '追加後はTrueになるべき'
    # 重複追加されない
    add_to_skip_list(base, SKIP_PATH)
    skip_list3 = load_skip_list(SKIP_PATH)
    assert skip_list2 == skip_list3, '重複追加されないべき'
    print('add_to_skip_listテスト: OK')

def cleanup():
    shutil.rmtree(TMP_DIR)

if __name__ == '__main__':
    test_is_skipped()
    test_add_to_skip_list()
    cleanup()
