import json
import os
from typing import Any

import requests
from dotenv import load_dotenv

from src.skiplist import save_skip_list
from src.transfer import GraphTransferClient

# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path, override=False)


def load_config() -> dict:
    """
    設定ファイルと環境変数を読み込む
    """
    # load_dotenv()はグローバルで一度だけ呼ぶ
    config_path = "config/config.json"
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}
    return config


def create_transfer_client() -> GraphTransferClient:
    """
    GraphTransferClientのインスタンスを作成
    """
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    TENANT_ID = os.getenv("TENANT_ID")
    SITE_ID = os.getenv("DESTINATION_SHAREPOINT_SITE_ID")
    DRIVE_ID = os.getenv("DESTINATION_SHAREPOINT_DRIVE_ID")

    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID]):
        raise ValueError("必要な環境変数が設定されていません")

    # 型チェック後のassertionで安全性を担保
    assert CLIENT_ID is not None
    assert CLIENT_SECRET is not None
    assert TENANT_ID is not None
    assert SITE_ID is not None
    assert DRIVE_ID is not None

    return GraphTransferClient(CLIENT_ID, CLIENT_SECRET, TENANT_ID, SITE_ID, DRIVE_ID)


def crawl_onedrive_files(
    root_folder: str = "TEST-Onedrive", user_principal_name: str | None = None
) -> list[dict[str, Any]]:
    """
    OneDrive側のファイルを再帰的にクロールし、重複排除済みファイルリストを返す

    Args:
        root_folder: OneDriveのルートフォルダ名
        user_principal_name: OneDriveのユーザープリンシパル名
            （None時は環境変数から取得）

    Returns:
        重複排除済みファイルリスト
    """
    client = create_transfer_client()

    if user_principal_name is None:
        user_principal_name = os.getenv("SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME")
        if not user_principal_name:
            raise ValueError("user_principal_nameまたは環境変数SOURCE_ONEDRIVE_USER_PRINCIPAL_NAMEが必要です")

    file_targets = client.collect_file_targets_from_onedrive(
        folder_path=root_folder, user_principal_name=user_principal_name
    )

    return file_targets


def crawl_sharepoint_files(
    root_folder: str = "TEST-Sharepoint",
) -> list[dict[str, Any]]:
    """
    SharePoint側のファイルを再帰的にクロールし、重複排除済みファイルリストを返す

    Args:
        root_folder: SharePointのルートフォルダ名

    Returns:
        重複排除済みファイルリスト
    """
    client = create_transfer_client()

    # Get SharePoint items and convert to file targets format
    items = client.list_drive_items(folder_path=root_folder)
    # Convert items to file targets format (items already have the right structure)
    file_targets = [item for item in items if item.get("file")]

    return file_targets


def save_file_list(file_targets: list[dict[str, Any]], save_path: str) -> None:
    """
    ファイルリストをJSONで保存

    Args:
        file_targets: ファイルリスト
        save_path: 保存先パス
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(file_targets, f, ensure_ascii=False, indent=2)


def load_file_list(file_path: str) -> list[dict[str, Any]]:
    """
    JSONファイルからファイルリストを読み込む

    Args:
        file_path: ファイルリストのJSONパス

    Returns:
        ファイルリスト
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルリストが見つかりません: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        file_targets = json.load(f)

    return file_targets


def build_skiplist_from_filelist(file_targets: list[dict[str, Any]], skip_list_path: str) -> None:
    """
    ファイルリストからスキップリストを生成・保存

    Args:
        file_targets: ファイルリスト
        skip_list_path: スキップリスト保存先パス
    """
    save_skip_list(file_targets, skip_list_path)


def build_skiplist_from_sharepoint(
    root_folder: str | None = None, skip_list_path: str | None = None
) -> list[dict[str, Any]]:
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
        # .envのDESTINATION_SHAREPOINT_DOCLIBを参照
        import os

        root_folder = os.getenv("DESTINATION_SHAREPOINT_DOCLIB", "TEST-Sharepoint")

    if skip_list_path is None:
        skip_list_path = config.get("skip_list_path", "logs/skip_list.json")

    # 型チェック後のassertionで安全性を担保
    assert root_folder is not None
    assert skip_list_path is not None

    # SharePoint側をクロール
    file_targets = crawl_sharepoint_files(root_folder)

    # スキップリスト形式で保存
    build_skiplist_from_filelist(file_targets, skip_list_path)

    return file_targets


def compare_file_counts(onedrive_count: int, sharepoint_count: int, expected_count: int | None = None) -> None:
    """
    ファイル数の比較と検証結果を出力

    Args:
        onedrive_count: OneDrive側のファイル数
        sharepoint_count: SharePoint側のファイル数
        expected_count: 期待されるファイル数（指定時のみチェック）
    """

    if expected_count:
        if onedrive_count == expected_count:
            pass
        else:
            pass

    transfer_needed = onedrive_count - sharepoint_count
    if transfer_needed > 0:
        pass
    elif transfer_needed == 0:
        pass
    else:
        pass


def _normalize_skip_list_path(path: str) -> str:
    """スキップリストパスを正規化"""
    if not path.endswith(".json"):
        if path.endswith("/") or path.endswith("\\"):
            return path + "skip_list.json"
        else:
            return path + "/skip_list.json"
    return path


def _handle_sharepoint_rebuild():
    """SharePointからのスキップリスト再構築を処理"""
    root_folder = input("SharePointルートフォルダ名 (デフォルト: config設定値): ").strip()
    skip_list_path = input("スキップリスト保存先 (デフォルト: config設定値): ").strip()

    if skip_list_path:
        skip_list_path = _normalize_skip_list_path(skip_list_path)

    try:
        build_skiplist_from_sharepoint(
            root_folder if root_folder else None,
            skip_list_path if skip_list_path else None,
        )
    except (ValueError, Exception):
        pass


def _handle_filelist_rebuild():
    """ファイルリストからのスキップリスト再構築を処理"""
    file_list_path = input("ファイルリストのパスを入力: ").strip()
    if not file_list_path:
        return

    config = load_config()
    skip_list_path = input("スキップリスト保存先 (デフォルト: config設定値): ").strip()

    if not skip_list_path:
        skip_list_path = config.get("skip_list_path", "logs/skip_list.json")
    else:
        skip_list_path = _normalize_skip_list_path(skip_list_path)

    try:
        file_targets = load_file_list(file_list_path)
        build_skiplist_from_filelist(file_targets, skip_list_path)
    except (FileNotFoundError, Exception):
        pass


def rebuild_skiplist_interactive() -> None:
    """
    対話形式でスキップリストを再構築
    """
    choice = input("選択してください (1 or 2): ").strip()

    if choice == "1":
        _handle_sharepoint_rebuild()
    elif choice == "2":
        _handle_filelist_rebuild()
    else:
        pass


def _check_graph_endpoint(label: str, url: str, headers: dict[str, str]) -> tuple[bool, str]:
    """Graph API エンドポイントの疎通確認を実行"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as exc:  # リクエスト系の例外のみ捕捉
        return False, f"[ERROR] {label}: {exc}"

    if response.ok:
        return True, f"[OK] {label}"

    detail = response.text.strip().replace("\n", " ")
    if len(detail) > 120:
        detail = detail[:120] + "..."
    return False, f"[ERROR] {label}: HTTP {response.status_code} {detail}"


def validate_configuration() -> tuple[bool, list[str]]:
    """環境変数とMicrosoft Graph疎通を確認"""
    messages: list[str] = []
    success = True

    required_env = [
        "CLIENT_ID",
        "CLIENT_SECRET",
        "TENANT_ID",
        "DESTINATION_SHAREPOINT_SITE_ID",
        "DESTINATION_SHAREPOINT_DRIVE_ID",
    ]

    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        messages.append("[ERROR] Missing environment variables: " + ", ".join(sorted(missing)))
        return False, messages

    try:
        client = create_transfer_client()
    except ValueError as exc:
        messages.append(f"[ERROR] {exc}")
        return False, messages
    except Exception as exc:  # noqa: BLE001 - 予期せぬ例外をそのまま表示したい
        messages.append(f"[ERROR] Failed to initialize GraphTransferClient: {exc}")
        return False, messages

    messages.append("[OK] Required environment variables are set.")

    try:
        token = client.auth.get_access_token()
    except Exception as exc:  # noqa: BLE001 - 認証例外をそのまま返す
        messages.append(f"[ERROR] Failed to acquire access token: {exc}")
        return False, messages

    messages.append("[OK] Access token acquired.")
    headers = {"Authorization": f"Bearer {token}"}

    sharepoint_url = f"{client.base_url}/sites/{client.site_id}/drives/{client.drive_id}"
    sharepoint_ok, sharepoint_msg = _check_graph_endpoint("SharePoint drive access", sharepoint_url, headers)
    messages.append(sharepoint_msg)
    success &= sharepoint_ok

    onedrive_drive_id = os.getenv("SOURCE_ONEDRIVE_DRIVE_ID")
    if onedrive_drive_id:
        onedrive_url = f"{client.base_url}/drives/{onedrive_drive_id}"
        drive_ok, drive_msg = _check_graph_endpoint("OneDrive drive access", onedrive_url, headers)
        messages.append(drive_msg)
        success &= drive_ok
    else:
        user_principal_name = os.getenv("SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME")
        if user_principal_name:
            user_url = f"{client.base_url}/users/{user_principal_name}"
            user_ok, user_msg = _check_graph_endpoint("OneDrive user lookup", user_url, headers)
            messages.append(user_msg)
            success &= user_ok
        else:
            messages.append("[WARN] SOURCE_ONEDRIVE_DRIVE_ID と SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME が未設定です。")

    return bool(success), messages
