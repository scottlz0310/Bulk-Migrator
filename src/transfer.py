from src.skiplist import load_skip_list, is_skipped, add_to_skip_list

import os
from dotenv import load_dotenv
import requests
from src.auth import GraphAuthenticator
from typing import List, Dict, Any, Optional
import io
import math

# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path, override=False)


# 絶対インポートに修正
try:
    from src.config_manager import get_chunk_size_mb, get_large_file_threshold_mb
except ImportError:
    def get_chunk_size_mb():
        return 5
    def get_large_file_threshold_mb():
        return 4

# OneDrive/SharePoint ディレクトリ再帰取得・転送ロジック雛形

class GraphTransferClient:

    def upload_file_to_sharepoint(self, file_info, src_root="TEST-Onedrive", dst_root="TEST-Sharepoint", timeout=10):
        """
        OneDriveからSharePointへファイルをストリーミング転送する
        ファイルサイズに応じて単純PUT or アップロードセッションを選択
        """
        file_size = file_info.get('size', 0)
        threshold_mb = get_large_file_threshold_mb()
        threshold_bytes = threshold_mb * 1024 * 1024
        
        if file_size >= threshold_bytes:
            print(f"[INFO] 大容量ファイル検出({file_size} bytes) - アップロードセッション使用")
            return self._upload_large_file_to_sharepoint(file_info, src_root, dst_root, timeout)
        else:
            print(f"[INFO] 小容量ファイル({file_size} bytes) - 単純PUT使用")
            return self._upload_small_file_to_sharepoint(file_info, src_root, dst_root, timeout)

    def _upload_small_file_to_sharepoint(self, file_info, src_root="TEST-Onedrive", dst_root="TEST-Sharepoint", timeout=10):
        """
        小容量ファイル用の従来の単純PUTアップロード
        """
        # OneDriveからファイルをダウンロード
        src_path = file_info['path']  # src_pathを最初に定義

        # OneDriveファイルIDを使った直接アクセス方式に変更
        onedrive_drive_id = os.getenv('SOURCE_ONEDRIVE_DRIVE_ID')
        file_id = file_info.get('id')
        
        if onedrive_drive_id and file_id:
            # 方法1: ファイルIDを使って直接ダウンロードURL取得
            file_url = f"{self.base_url}/drives/{onedrive_drive_id}/items/{file_id}"
            file_resp = requests.get(file_url, headers=self._headers())
            
            if file_resp.status_code == 200:
                file_data = file_resp.json()
                download_url = file_data.get('@microsoft.graph.downloadUrl')
                
                if download_url:
                    resp = requests.get(download_url, stream=True, timeout=timeout)
                    resp.raise_for_status()
                else:
                    raise Exception(f"ダウンロードURLが取得できませんでした: {file_info['name']}")
            else:
                raise Exception(f"ファイル情報の取得に失敗しました: {file_resp.status_code} - {file_resp.text}")
        else:
            # フォールバック: 従来のパスベース方式
            import urllib.parse
            encoded_path = '/'.join([urllib.parse.quote(part) for part in src_path.split('/')])
            
            if onedrive_drive_id:
                download_url = f"{self.base_url}/drives/{onedrive_drive_id}/root:/{encoded_path}:/content"
            else:
                download_url = f"{self.base_url}/users/{os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')}/drive/root:/{encoded_path}:/content"
            
            print(f"[DEBUG] OneDrive download_url: {download_url}")
            resp = requests.get(download_url, headers=self._headers(), stream=True, timeout=timeout)
            resp.raise_for_status()

        # SharePoint側のアップロード先パスを生成
        rel_path = os.path.relpath(src_path, src_root)
        dst_path = os.path.join(dst_root, rel_path).replace("\\", "/")
        
        # ディレクトリ部分を抽出してフォルダを事前作成
        dst_dir = os.path.dirname(dst_path)
        if dst_dir and dst_dir != dst_root:
            self.ensure_sharepoint_folder(dst_dir)
        
        upload_url = f"{self.base_url}/sites/{self.site_id}/drives/{self.drive_id}/root:/{dst_path}:/content"

        # PUTでストリーミングアップロード
        put_resp = requests.put(upload_url, headers=self._headers(), data=resp.raw, timeout=timeout)
        put_resp.raise_for_status()
        return put_resp.json()
    def filter_skipped_targets(self, file_targets: list, skip_list_path: Optional[str] = None) -> list:
        """
        スキップリストに該当するファイルを除外したリストを返す
        """
        if skip_list_path is None:
            try:
                from src.config_manager import get_skip_list_path
                skip_list_path = get_skip_list_path()
            except ImportError:
                skip_list_path = 'logs/skip_list.json'
        
        skip_list = load_skip_list(skip_list_path)
        return [f for f in file_targets if not is_skipped(f, skip_list)]
    def save_file_targets(self, file_targets: list, save_path: str) -> None:
        """
        転送対象ファイルリストをJSONで保存
        """
        import json
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(file_targets, f, ensure_ascii=False, indent=2)
    def collect_file_targets_from_onedrive(self, folder_path: str, user_principal_name: Optional[str] = None, drive_id: Optional[str] = None) -> list:
        """
        OneDriveから指定フォルダ配下のファイルリストを取得（ディレクトリ構造保持）
        """
        print(f"[INFO] OneDriveクロール開始: {folder_path}")
        items = self.list_onedrive_items_with_path(
            user_principal_name=user_principal_name,
            drive_id=drive_id,
            folder_path=folder_path,
            _parent_path=folder_path  # ルートパスを設定
        )
        
        file_targets = []
        seen = set()
        
        for i, item in enumerate(items):
            if 'file' in item:
                file_key = (item['full_path'], item.get('id'))
                if file_key not in seen:
                    seen.add(file_key)
                    file_targets.append({
                        'name': item['name'],
                        'path': item['full_path'],
                        'size': item.get('size'),
                        'lastModifiedDateTime': item.get('lastModifiedDateTime'),
                        'id': item.get('id'),
                    })
                    
                    # 1000件ごとに進捗ログを出力
                    if len(file_targets) % 1000 == 0:
                        from src.logger import logger
                        logger.info(f"OneDriveクロール進捗: {len(file_targets)}ファイル処理済み")
                        
        print(f"[INFO] OneDriveクロール完了: {len(file_targets)}ファイル")
        return file_targets

    def __init__(self, client_id: str, client_secret: str, tenant_id: str, site_id: str, drive_id: str):
        self.site_id = site_id
        self.drive_id = drive_id
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.auth = GraphAuthenticator(client_id, client_secret, tenant_id)


    def _acquire_token(self) -> str:
        return self.auth.get_access_token()

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._acquire_token()}"}

    def list_drive_items(self, folder_path: str = "") -> List[Dict[str, Any]]:
        """
        指定フォルダ配下のアイテム（ファイル・フォルダ）を再帰的に取得
        タイムアウト・エラー内容も出力
        """
        items = []
        url = f"{self.base_url}/sites/{self.site_id}/drives/{self.drive_id}/root"
        if folder_path:
            url += f":/{folder_path}:"
        url += "/children"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            print(f"[Timeout] API応答がありません: {url}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[RequestException] {e}\nレスポンス: {getattr(e.response, 'text', '')}")
            return []
        data = resp.json()
        for item in data.get('value', []):
            if item.get('folder'):
                # フォルダは再帰のみ、itemsには追加しない（二重再帰バグ修正）
                sub_path = os.path.join(folder_path, item['name']) if folder_path else item['name']
                items.extend(self.list_drive_items(sub_path))
            else:
                # ファイルのみitemsに追加
                items.append(item)
        return items

    def list_onedrive_items_with_path(self, user_principal_name: Optional[str] = None, drive_id: Optional[str] = None, folder_path: str = "", _parent_path: str = "") -> List[Dict[str, Any]]:
        """
        OneDrive個人用のアイテム一覧取得（パス情報付き・再帰対応）
        folder_path: API呼び出し用のパス
        _parent_path: 内部的に使用する親パス（再帰用）
        """
        items = []
        if user_principal_name:
            url = f"{self.base_url}/users/{user_principal_name}/drive/root"
        elif drive_id:
            url = f"{self.base_url}/drives/{drive_id}/root"
        else:
            raise ValueError("user_principal_name か drive_id のいずれかを指定してください")
        if folder_path:
            url += f":/{folder_path}:"
        url += "/children"
        
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            print(f"[Timeout] API応答がありません: {url}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[RequestException] {e}\nレスポンス: {getattr(e.response, 'text', '')}")
            return []
        data = resp.json()
        for item in data.get('value', []):
            # フルパスを構築
            current_path = os.path.join(_parent_path, item['name']) if _parent_path else item['name']
            current_path = current_path.replace("\\", "/")
            
            # アイテムにパス情報を追加
            item_with_path = item.copy()
            item_with_path['full_path'] = current_path
            
            if item.get('folder'):
                # フォルダの場合は再帰的に取得
                sub_folder_path = os.path.join(folder_path, item['name']) if folder_path else item['name']
                sub_folder_path = sub_folder_path.replace("\\", "/")
                items.extend(self.list_onedrive_items_with_path(
                    user_principal_name=user_principal_name, 
                    drive_id=drive_id, 
                    folder_path=sub_folder_path,
                    _parent_path=current_path
                ))
            else:
                # ファイルの場合はリストに追加
                items.append(item_with_path)
        return items

    def create_folder(self, parent_path: str, folder_name: str) -> Dict[str, Any]:
        """
        指定パス配下に新しいフォルダを作成
        """
        url = f"{self.base_url}/sites/{self.site_id}/drives/{self.drive_id}/root"
        if parent_path:
            url += f":/{parent_path}:"
        url += "/children"
        payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"
        }
        resp = requests.post(url, headers=self._headers(), json=payload)
        if resp.status_code == 409:
            # 既に存在する場合は何もしない（正常終了扱い）
            print(f"[INFO] フォルダ既存: {os.path.join(parent_path, folder_name)}")
            return {}
        resp.raise_for_status()
        return resp.json()
    def ensure_sharepoint_folder(self, folder_path: str) -> None:
        """
        SharePoint側で指定されたフォルダパスが存在しない場合、再帰的に作成する
        """
        if not folder_path or folder_path == ".":
            return
            
        # パスを正規化
        folder_path = folder_path.replace("\\", "/").strip("/")
        if not folder_path:
            return
            
        # 親ディレクトリから順に作成
        path_parts = folder_path.split("/")
        current_path = ""
        
        for part in path_parts:
            parent_path = current_path
            current_path = os.path.join(current_path, part).replace("\\", "/") if current_path else part
            
            # フォルダの存在確認
            check_url = f"{self.base_url}/sites/{self.site_id}/drives/{self.drive_id}/root:/{current_path}"
            try:
                resp = requests.get(check_url, headers=self._headers())
                if resp.status_code == 404:
                    # フォルダが存在しないので作成
                    print(f"[INFO] フォルダを作成: {current_path}")
                    self.create_folder(parent_path, part)
            except Exception as e:
                print(f"[WARNING] フォルダ確認/作成エラー: {current_path} - {e}")
                # エラーが発生しても処理を続行

    def _upload_large_file_to_sharepoint(self, file_info, src_root="TEST-Onedrive", dst_root="TEST-Sharepoint", timeout=10):
        """
        大容量ファイル用のアップロードセッション + 分割アップロード
        """
        src_path = file_info['path']
        file_size = file_info.get('size', 0)
        
        # SharePoint側のアップロード先パスを生成
        rel_path = os.path.relpath(src_path, src_root)
        dst_path = os.path.join(dst_root, rel_path).replace("\\", "/")
        
        # ディレクトリ部分を抽出してフォルダを事前作成
        dst_dir = os.path.dirname(dst_path)
        if dst_dir and dst_dir != dst_root:
            self.ensure_sharepoint_folder(dst_dir)
        
        # 1. アップロードセッションを作成
        upload_session = self._create_upload_session(dst_path, file_size)
        upload_url = upload_session['uploadUrl']
        
        # 2. OneDriveからファイルをダウンロード（ストリーム）
        download_stream = self._get_onedrive_file_stream(file_info, timeout)
        
        # 3. チャンク分割アップロード
        chunk_size = get_chunk_size_mb() * 1024 * 1024  # MBをバイトに変換
        total_chunks = math.ceil(file_size / chunk_size)
        
        for chunk_index in range(total_chunks):
            start_byte = chunk_index * chunk_size
            end_byte = min(start_byte + chunk_size - 1, file_size - 1)
            chunk_data = download_stream.read(chunk_size)
            
            if not chunk_data:
                break
                
            print(f"[INFO] チャンク {chunk_index + 1}/{total_chunks} アップロード中 ({start_byte}-{end_byte})")
            
            # チャンクをアップロード
            self._upload_chunk(upload_url, chunk_data, start_byte, end_byte, file_size, timeout)
        
        print(f"[INFO] アップロード完了: {dst_path}")
        return {"message": "Upload completed via upload session"}
    
    def _create_upload_session(self, dst_path: str, file_size: int) -> Dict[str, Any]:
        """
        SharePointアップロードセッションを作成
        """
        session_url = f"{self.base_url}/sites/{self.site_id}/drives/{self.drive_id}/root:/{dst_path}:/createUploadSession"
        
        payload = {
            "item": {
                "@microsoft.graph.conflictBehavior": "replace",
                "name": os.path.basename(dst_path)
            }
        }
        
        response = requests.post(session_url, headers=self._headers(), json=payload)
        response.raise_for_status()
        return response.json()
    
    def _get_onedrive_file_stream(self, file_info, timeout=10):
        """
        OneDriveからファイルのダウンロードストリームを取得
        """
        # OneDriveファイルIDを使った直接アクセス方式
        onedrive_drive_id = os.getenv('SOURCE_ONEDRIVE_DRIVE_ID')
        file_id = file_info.get('id')
        
        if onedrive_drive_id and file_id:
            # ファイルIDを使って直接ダウンロードURL取得
            file_url = f"{self.base_url}/drives/{onedrive_drive_id}/items/{file_id}"
            file_resp = requests.get(file_url, headers=self._headers())
            
            if file_resp.status_code == 200:
                file_data = file_resp.json()
                download_url = file_data.get('@microsoft.graph.downloadUrl')
                
                if download_url:
                    resp = requests.get(download_url, stream=True, timeout=timeout)
                    resp.raise_for_status()
                    return resp.raw
                else:
                    raise Exception(f"ダウンロードURLが取得できませんでした: {file_info['name']}")
            else:
                raise Exception(f"ファイル情報の取得に失敗しました: {file_resp.status_code} - {file_resp.text}")
        else:
            # フォールバック: 従来のパスベース方式
            src_path = file_info['path']
            import urllib.parse
            encoded_path = '/'.join([urllib.parse.quote(part) for part in src_path.split('/')])
            
            if onedrive_drive_id:
                download_url = f"{self.base_url}/drives/{onedrive_drive_id}/root:/{encoded_path}:/content"
            else:
                download_url = f"{self.base_url}/users/{os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')}/drive/root:/{encoded_path}:/content"
            
            resp = requests.get(download_url, headers=self._headers(), stream=True, timeout=timeout)
            resp.raise_for_status()
            return resp.raw
    
    def _upload_chunk(self, upload_url: str, chunk_data: bytes, start_byte: int, end_byte: int, total_size: int, timeout=10):
        """
        チャンクデータをアップロードセッションURLにアップロード
        """
        headers = {
            'Content-Range': f'bytes {start_byte}-{end_byte}/{total_size}',
            'Content-Length': str(len(chunk_data))
        }
        
        response = requests.put(upload_url, headers=headers, data=chunk_data, timeout=timeout)
        response.raise_for_status()
        return response
