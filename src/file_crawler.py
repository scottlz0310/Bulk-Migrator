import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from src.transfer import GraphTransferClient
from src.skiplist import save_skip_list

# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path, override=False)

def load_config() -> dict:
    """
    設定ファイルと環境変数を読み込む
    """
    # load_dotenv()はグローバルで一度だけ呼ぶ
    config_path = 'config/config.json'
    if os.path.exists(config_path):
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    return config

def create_transfer_client() -> GraphTransferClient:
    """
    GraphTransferClientのインスタンスを作成
    """
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    SITE_ID = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
    DRIVE_ID = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')
    
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID]):
        raise ValueError("必要な環境変数が設定されていません")
    
    # 型チェック後のassertionで安全性を担保
    assert CLIENT_ID is not None
    assert CLIENT_SECRET is not None
    assert TENANT_ID is not None
    assert SITE_ID is not None
    assert DRIVE_ID is not None
    
    return GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)

def crawl_onedrive_files(root_folder: str = "TEST-Onedrive", user_principal_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    OneDrive側のファイルを再帰的にクロールし、重複排除済みファイルリストを返す
    
    Args:
        root_folder: OneDriveのルートフォルダ名
        user_principal_name: OneDriveのユーザープリンシパル名（None時は環境変数から取得）
    
    Returns:
        重複排除済みファイルリスト
    """
    client = create_transfer_client()
    
    if user_principal_name is None:
        user_principal_name = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')
        if not user_principal_name:
            raise ValueError("user_principal_nameまたは環境変数SOURCE_ONEDRIVE_USER_PRINCIPAL_NAMEが必要です")
    
    print(f"OneDrive側({root_folder})をクロール中...")
    items = client.list_onedrive_items(user_principal_name=user_principal_name, folder_path=root_folder)
    file_targets = client.collect_file_targets(items, parent_path=root_folder, user_principal_name=user_principal_name)
    
    print(f"OneDriveクロール完了: {len(file_targets)}件")
    return file_targets

def crawl_sharepoint_files(root_folder: str = "TEST-Sharepoint") -> List[Dict[str, Any]]:
    """
    SharePoint側のファイルを再帰的にクロールし、重複排除済みファイルリストを返す
    
    Args:
        root_folder: SharePointのルートフォルダ名
    
    Returns:
        重複排除済みファイルリスト
    """
    client = create_transfer_client()
    
    print(f"SharePoint側({root_folder})をクロール中...")
    items = client.list_drive_items(folder_path=root_folder)
    file_targets = client.collect_file_targets(items, parent_path=root_folder)
    
    print(f"SharePointクロール完了: {len(file_targets)}件")
    return file_targets

def save_file_list(file_targets: List[Dict[str, Any]], save_path: str) -> None:
    """
    ファイルリストをJSONで保存
    
    Args:
        file_targets: ファイルリスト
        save_path: 保存先パス
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(file_targets, f, ensure_ascii=False, indent=2)
    print(f"ファイルリストを {save_path} に保存しました")

def load_file_list(file_path: str) -> List[Dict[str, Any]]:
    """
    JSONファイルからファイルリストを読み込む
    
    Args:
        file_path: ファイルリストのJSONパス
    
    Returns:
        ファイルリスト
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルリストが見つかりません: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        file_targets = json.load(f)
    
    print(f"ファイルリストを読み込みました: {file_path} ({len(file_targets)}件)")
    return file_targets

def build_skiplist_from_filelist(file_targets: List[Dict[str, Any]], skip_list_path: str) -> None:
    """
    ファイルリストからスキップリストを生成・保存
    
    Args:
        file_targets: ファイルリスト
        skip_list_path: スキップリスト保存先パス
    """
    save_skip_list(file_targets, skip_list_path)
    print(f"スキップリストを生成しました: {skip_list_path} ({len(file_targets)}件)")

def build_skiplist_from_sharepoint(root_folder: Optional[str] = None, skip_list_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    SharePoint側をクロールしてスキップリストを生成・保存
    
    Args:
        root_folder: SharePointのルートフォルダ名（None時は設定ファイルから取得）
        skip_list_path: スキップリスト保存先パス（None時は設定ファイルから取得）
    
    Returns:
        クロールしたファイルリスト
    """
    config = load_config()
    
    if root_folder is None:
        root_folder = config.get('sharepoint_root', 'TEST-Sharepoint')
    
    if skip_list_path is None:
        skip_list_path = config.get('skip_list_path', 'logs/skip_list.json')
    
    # 型チェック後のassertionで安全性を担保
    assert root_folder is not None
    assert skip_list_path is not None
    
    # SharePoint側をクロール
    file_targets = crawl_sharepoint_files(root_folder)
    
    # スキップリスト形式で保存
    build_skiplist_from_filelist(file_targets, skip_list_path)
    
    print(f"SharePoint側スキップリスト再構築完了: {skip_list_path} ({len(file_targets)}件)")
    return file_targets

def compare_file_counts(onedrive_count: int, sharepoint_count: int, expected_count: Optional[int] = None) -> None:
    """
    ファイル数の比較と検証結果を出力
    
    Args:
        onedrive_count: OneDrive側のファイル数
        sharepoint_count: SharePoint側のファイル数
        expected_count: 期待されるファイル数（指定時のみチェック）
    """
    print(f"\n=== ファイル数比較 ===")
    print(f"OneDrive側: {onedrive_count}件")
    print(f"SharePoint側: {sharepoint_count}件")
    
    if expected_count:
        print(f"期待値: {expected_count}件")
        if onedrive_count == expected_count:
            print("✓ OneDrive側のファイル数は期待値と一致")
        else:
            print(f"✗ OneDrive側のファイル数が期待値と不一致（差分: {onedrive_count - expected_count}）")
    
    transfer_needed = onedrive_count - sharepoint_count
    if transfer_needed > 0:
        print(f"転送が必要なファイル: 約{transfer_needed}件")
    elif transfer_needed == 0:
        print("✓ すべてのファイルが転送済みです")
    else:
        print(f"注意: SharePoint側にOneDriveより多いファイルがあります（差分: {abs(transfer_needed)}件）")

def rebuild_skiplist_interactive() -> None:
    """
    対話形式でスキップリストを再構築
    """
    print("=== スキップリスト再構築ツール ===")
    print("1. SharePoint側をクロールして再構築")
    print("2. 既存のファイルリストから再構築")
    
    choice = input("選択してください (1 or 2): ").strip()
    
    if choice == "1":
        root_folder = input("SharePointルートフォルダ名 (デフォルト: config設定値): ").strip()
        skip_list_path = input("スキップリスト保存先 (デフォルト: config設定値): ").strip()
        
        # ディレクトリ名だけが指定された場合、デフォルトファイル名を追加
        if skip_list_path and not skip_list_path.endswith('.json'):
            if skip_list_path.endswith('/') or skip_list_path.endswith('\\'):
                skip_list_path += 'skip_list.json'
            else:
                skip_list_path += '/skip_list.json'
        
        try:
            build_skiplist_from_sharepoint(
                root_folder if root_folder else None,
                skip_list_path if skip_list_path else None
            )
        except ValueError as e:
            print(f"エラー: {e}")
            print("環境変数の設定を確認してください。")
            print("必要な環境変数: CLIENT_ID, CLIENT_SECRET, TENANT_ID, DESTINATION_SHAREPOINT_SITE_ID, DESTINATION_SHAREPOINT_DRIVE_ID")
        except Exception as e:
            print(f"予期しないエラー: {e}")
        
    elif choice == "2":
        file_list_path = input("ファイルリストのパスを入力: ").strip()
        if not file_list_path:
            print("エラー: ファイルリストのパスが必要です")
            return
        
        config = load_config()
        skip_list_path = input("スキップリスト保存先 (デフォルト: config設定値): ").strip()
        if not skip_list_path:
            skip_list_path = config.get('skip_list_path', 'logs/skip_list.json')
        elif not skip_list_path.endswith('.json'):
            if skip_list_path.endswith('/') or skip_list_path.endswith('\\'):
                skip_list_path += 'skip_list.json'
            else:
                skip_list_path += '/skip_list.json'
        
        try:
            file_targets = load_file_list(file_list_path)
            build_skiplist_from_filelist(file_targets, skip_list_path)
        except FileNotFoundError as e:
            print(f"エラー: {e}")
        except Exception as e:
            print(f"予期しないエラー: {e}")
        
    else:
        print("無効な選択です")
