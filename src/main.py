import sys
import os
import argparse
from dotenv import load_dotenv
# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path, override=False)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from transfer import GraphTransferClient
from skiplist import load_skip_list, is_skipped, add_to_skip_list
from logger import log_transfer_start, log_transfer_success, log_transfer_error, log_transfer_skip
from rebuild_skip_list import crawl_sharepoint, create_skip_list_from_sharepoint

# 設定読み込み
with open('config/config.json', encoding='utf-8') as f:
    config = json.load(f)

def get_current_config_hash():
    """現在の設定のハッシュ値を計算"""
    import hashlib
    
    # 重要な環境変数と設定を文字列として結合
    config_string = f"{os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')}|{os.getenv('SOURCE_ONEDRIVE_FOLDER_PATH')}|{os.getenv('DESTINATION_SHAREPOINT_SITE_ID')}|{os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')}|{os.getenv('DESTINATION_SHAREPOINT_DOCLIB')}"
    
    return hashlib.md5(config_string.encode()).hexdigest()

def check_config_changed():
    """設定が変更されたかチェック"""
    config_hash_file = 'logs/config_hash.txt'
    current_hash = get_current_config_hash()
    
    if not os.path.exists(config_hash_file):
        # 初回実行時はハッシュファイルを作成
        os.makedirs('logs', exist_ok=True)
        with open(config_hash_file, 'w') as f:
            f.write(current_hash)
        return False
    
    with open(config_hash_file, 'r') as f:
        saved_hash = f.read().strip()
    
    if current_hash != saved_hash:
        print("=== 設定変更を検出 ===")
        print("フォルダ設定またはアカウント設定が変更されています")
        return True
    
    return False

def clear_logs_and_update_config():
    """ログをクリアして設定ハッシュを更新"""
    print("=== ログクリア・設定更新 ===")
    
    # ログファイルを削除
    log_files = [
        'logs/onedrive_files.json',
        'logs/sharepoint_current_files.json', 
        'logs/skip_list.json',
        'logs/transfer.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            os.remove(log_file)
            print(f"削除: {log_file}")
    
    # 設定ハッシュを更新
    current_hash = get_current_config_hash()
    with open('logs/config_hash.txt', 'w') as f:
        f.write(current_hash)
    
    print("キャッシュクリア完了")

def get_onedrive_files(force_crawl=False):
    """OneDriveファイルリストを取得（キャッシュ機能付き）"""
    # キャッシュファイルの存在確認
    cache_file = 'logs/onedrive_files.json'
    
    if not force_crawl and os.path.exists(cache_file):
        try:
            # キャッシュから読み込み
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_files = json.load(f)
            print(f"=== OneDriveファイルリスト（キャッシュ利用）: {len(cached_files)}件 ===")
            return cached_files
        except (json.JSONDecodeError, IOError):
            print("キャッシュファイルが破損しています。再クロールします。")
    
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET') 
    TENANT_ID = os.getenv('TENANT_ID')
    SITE_ID = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
    DRIVE_ID = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')
    USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')

    # 環境変数の検証
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID, USER_PRINCIPAL_NAME]):
        print("エラー: 必要な環境変数が設定されていません")
        return []

    assert CLIENT_ID is not None
    assert CLIENT_SECRET is not None  
    assert TENANT_ID is not None
    assert SITE_ID is not None
    assert DRIVE_ID is not None
    assert USER_PRINCIPAL_NAME is not None
    
    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)
    
    print("=== OneDriveファイルリスト取得（新規クロール）===")
    
    # 環境変数からフォルダパスを取得
    source_folder = os.getenv('SOURCE_ONEDRIVE_FOLDER_PATH', 'TEST-Onedrive')
    
    file_targets = client.collect_file_targets_from_onedrive(
        folder_path=source_folder,
        user_principal_name=USER_PRINCIPAL_NAME,
        drive_id=None
    )
    
    # ファイルリストをキャッシュとして保存
    os.makedirs('logs', exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(file_targets, f, ensure_ascii=False, indent=2)
    
    print(f"OneDriveファイル数: {len(file_targets)}")
    return file_targets

def rebuild_skip_list(onedrive_files=None, force_crawl=False):
    """スキップリストを再構築する"""
    print("=== スキップリスト再構築開始 ===")
    
    # OneDriveファイルリストが提供されていない場合は取得
    if onedrive_files is None:
        onedrive_files = get_onedrive_files(force_crawl)
    
    # SharePointをクロール（force_crawlの場合は強制的に新規クロール）
    if force_crawl:
        sharepoint_files = crawl_sharepoint()
    else:
        # SharePointキャッシュの確認
        sharepoint_cache_file = 'logs/sharepoint_current_files.json'
        if os.path.exists(sharepoint_cache_file):
            try:
                with open(sharepoint_cache_file, 'r', encoding='utf-8') as f:
                    sharepoint_files = json.load(f)
                print(f"=== SharePointファイルリスト（キャッシュ利用）: {len(sharepoint_files)}件 ===")
            except (json.JSONDecodeError, IOError):
                print("SharePointキャッシュが破損しています。再クロールします。")
                sharepoint_files = crawl_sharepoint()
        else:
            sharepoint_files = crawl_sharepoint()
    
    # スキップリストを構築
    skip_list = create_skip_list_from_sharepoint(onedrive_files, sharepoint_files)
    
    print("\n=== スキップリスト再構築完了 ===")
    print(f"OneDriveファイル数: {len(onedrive_files)}")
    print(f"SharePoint転送済み: {len(sharepoint_files)}")
    print(f"スキップリスト: {len(skip_list)}")
    print(f"転送待ち: {len(onedrive_files) - len(skip_list)}")
    
    return len(onedrive_files) - len(skip_list)

def transfer_file(file_info, client, retry_count, timeout):
    """ファイル転送処理"""
    # 環境変数からフォルダパスを取得
    src_root = os.getenv('SOURCE_ONEDRIVE_FOLDER_PATH', 'TEST-Onedrive')
    dst_root = os.getenv('DESTINATION_SHAREPOINT_DOCLIB', 'TEST-Sharepoint')
    
    for attempt in range(1, retry_count + 1):
        try:
            log_transfer_start(file_info)
            start = time.time()
            client.upload_file_to_sharepoint(
                file_info,
                src_root=src_root,
                dst_root=dst_root,
                timeout=timeout
            )
            elapsed = time.time() - start
            log_transfer_success(file_info, elapsed=elapsed)
            add_to_skip_list(file_info, config["skip_list_path"])
            return True
        except Exception as e:
            log_transfer_error(file_info, str(e), retry_count=attempt)
            if attempt == retry_count:
                return False
            time.sleep(1)
    return False

def run_transfer(onedrive_files=None):
    """転送処理を実行"""
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    SITE_ID = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
    DRIVE_ID = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')
    USER_PRINCIPAL_NAME = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')

    # 環境変数の検証
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID, USER_PRINCIPAL_NAME]):
        print("エラー: 必要な環境変数が設定されていません")
        print("CLIENT_ID, CLIENT_SECRET, TENANT_ID, DESTINATION_SHAREPOINT_SITE_ID, DESTINATION_SHAREPOINT_DRIVE_ID, SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME")
        return

    # 転送クライアント初期化
    # 型チェッカー用のassert（実際の検証は上で済んでいる）
    assert CLIENT_ID is not None
    assert CLIENT_SECRET is not None  
    assert TENANT_ID is not None
    assert SITE_ID is not None
    assert DRIVE_ID is not None
    assert USER_PRINCIPAL_NAME is not None
    
    client = GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)

    # OneDriveファイルリストが提供されていない場合は取得
    if onedrive_files is None:
        onedrive_files = get_onedrive_files()

    # スキップリスト適用
    skip_list = load_skip_list(config["skip_list_path"])
    targets = [f for f in onedrive_files if not is_skipped(f, skip_list)]

    # 並列転送
    max_workers = config.get("max_parallel_transfers", 4)
    retry_count = config.get("retry_count", 3)
    timeout = config.get("timeout_sec", 10)

    print(f"転送対象: {len(targets)} 件 (スキップ済み除外)")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(transfer_file, f, client, retry_count, timeout): f for f in targets}
        for future in as_completed(futures):
            f = futures[future]
            try:
                future.result()
            except Exception as e:
                log_transfer_error(f, str(e))

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='OneDrive to SharePoint 転送ツール')
    parser.add_argument('--rebuild-skip', action='store_true', 
                       help='スキップリストを再構築する（SharePointから転送済みファイルを検出）')
    parser.add_argument('--clear-and-rebuild', action='store_true',
                       help='スキップリストをクリアして再構築する')
    parser.add_argument('--force-crawl', action='store_true',
                       help='キャッシュを無視して強制的に全クロールする')
    
    args = parser.parse_args()
    
    # 設定変更をチェック
    config_changed = check_config_changed()
    force_crawl = args.force_crawl or config_changed
    
    if config_changed:
        print("フォルダ設定またはアカウント設定の変更を検出しました。")
        print("ログをクリアして全クロールを実行します。")
        clear_logs_and_update_config()
    
    # OneDriveファイルリストを一度だけ取得（全モードで共有）
    onedrive_files = None
    
    if args.clear_and_rebuild:
        print("=== スキップリストクリア・再構築モード ===")
        # スキップリストファイルを削除
        skip_list_path = config["skip_list_path"]
        if os.path.exists(skip_list_path):
            os.remove(skip_list_path)
            print(f"スキップリスト削除: {skip_list_path}")
        
        # OneDriveクロール（1回のみ）
        onedrive_files = get_onedrive_files(force_crawl=True)  # クリア・再構築は常に強制クロール
        
        # 再構築
        remaining_files = rebuild_skip_list(onedrive_files, force_crawl=True)
        print(f"\n転送待ちファイル: {remaining_files}件")
        
    elif args.rebuild_skip:
        print("=== スキップリスト再構築モード ===")
        # OneDriveクロール（1回のみ）
        onedrive_files = get_onedrive_files(force_crawl)
        
        remaining_files = rebuild_skip_list(onedrive_files, force_crawl)
        print(f"\n転送待ちファイル: {remaining_files}件")
        
    else:
        print("=== 通常転送モード ===")
        # OneDriveクロール（1回のみ）
        onedrive_files = get_onedrive_files(force_crawl)
        
        run_transfer(onedrive_files)

if __name__ == "__main__":
    main()
