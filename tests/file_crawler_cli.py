#!/usr/bin/env python3
"""
ファイルクローラーのコマンドラインインターフェース

使用例:
1. OneDriveクロール + ファイルリスト保存:
   python src/file_crawler_cli.py onedrive --root "TEST-Onedrive" --save "logs/onedrive_filelist.json"

2. SharePointクロール + ファイルリスト保存:
   python src/file_crawler_cli.py sharepoint --root "TEST-Sharepoint" --save "logs/sharepoint_filelist.json"

3. SharePointクロール + スキップリスト生成:
   python src/file_crawler_cli.py skiplist --root "TEST-Sharepoint" --save "logs/skip_list.json"

4. ファイル数比較:
   python src/file_crawler_cli.py compare --onedrive "logs/onedrive_filelist.json" --sharepoint "logs/sharepoint_filelist.json"
"""

import sys
import os
from dotenv import load_dotenv
# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path, override=False)
import argparse

# srcディレクトリから実行する場合のパス調整
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

from src.file_crawler import (
    crawl_onedrive_files, 
    crawl_sharepoint_files, 
    save_file_list, 
    load_file_list,
    build_skiplist_from_sharepoint,
    build_skiplist_from_filelist,
    compare_file_counts,
    rebuild_skiplist_interactive
)

def cmd_onedrive(args):
    """OneDriveクロール実行"""
    try:
        file_targets = crawl_onedrive_files(
            root_folder=args.root,
            user_principal_name=args.user
        )
        
        if args.save:
            save_file_list(file_targets, args.save)
        
        return file_targets
        
    except Exception as e:
        print(f"エラー: OneDriveクロールに失敗しました - {e}")
        return None

def cmd_sharepoint(args):
    """SharePointクロール実行"""
    try:
        file_targets = crawl_sharepoint_files(root_folder=args.root)
        
        if args.save:
            save_file_list(file_targets, args.save)
        
        return file_targets
        
    except Exception as e:
        print(f"エラー: SharePointクロールに失敗しました - {e}")
        return None

def cmd_skiplist(args):
    """スキップリスト生成実行"""
    try:
        if args.from_file:
            # 既存のファイルリストからスキップリスト生成
            file_targets = load_file_list(args.from_file)
            build_skiplist_from_filelist(file_targets, args.save)
        else:
            # SharePointクロール→スキップリスト生成
            build_skiplist_from_sharepoint(
                root_folder=args.root,
                skip_list_path=args.save
            )
        
    except Exception as e:
        print(f"エラー: スキップリスト生成に失敗しました - {e}")

def cmd_compare(args):
    """ファイル数比較実行"""
    try:
        onedrive_targets = load_file_list(args.onedrive)
        sharepoint_targets = load_file_list(args.sharepoint)
        
        compare_file_counts(
            onedrive_count=len(onedrive_targets),
            sharepoint_count=len(sharepoint_targets),
            expected_count=args.expected
        )
        
    except Exception as e:
        print(f"エラー: ファイル数比較に失敗しました - {e}")

def cmd_interactive(args):
    """対話型スキップリスト再構築実行"""
    rebuild_skiplist_interactive()

def cmd_explore(args):
    """SharePointドライブの構造を探索"""
    try:
        from src.file_crawler import create_transfer_client
        import requests
        
        client = create_transfer_client()
        token = client.auth.get_access_token()
        drive_id = client.drive_id
        
        # 探索するパス（省略時はルート）
        explore_path = args.path if args.path else ""
        
        if explore_path:
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{explore_path}:/children"
            print(f"探索中: /{explore_path}")
        else:
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
            print("探索中: / (ルート)")
            
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers)
        
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('value', [])
            print(f"アイテム数: {len(items)}")
            
            for item in items:
                name = item.get('name', 'N/A')
                item_type = 'folder' if 'folder' in item else 'file'
                size = item.get('size', 0) if item_type == 'file' else '-'
                print(f"  {name} ({item_type}, size={size})")
        else:
            print(f"エラー: {resp.text}")
            
    except Exception as e:
        print(f"エラー: SharePoint探索に失敗しました - {e}")

def main():
    parser = argparse.ArgumentParser(
        description="OneDrive/SharePointファイルクローラー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # OneDriveクロールコマンド
    parser_onedrive = subparsers.add_parser('onedrive', help='OneDriveをクロール')
    parser_onedrive.add_argument('--root', default='TEST-Onedrive', help='OneDriveルートフォルダ名')
    parser_onedrive.add_argument('--user', help='OneDriveユーザープリンシパル名（省略時は環境変数から取得）')
    parser_onedrive.add_argument('--save', help='ファイルリスト保存先パス')
    parser_onedrive.set_defaults(func=cmd_onedrive)
    
    # SharePointクロールコマンド
    parser_sharepoint = subparsers.add_parser('sharepoint', help='SharePointをクロール')
    parser_sharepoint.add_argument('--root', default='TEST-Sharepoint', help='SharePointルートフォルダ名')
    parser_sharepoint.add_argument('--save', help='ファイルリスト保存先パス')
    parser_sharepoint.set_defaults(func=cmd_sharepoint)
    
    # 探索コマンド【新規追加】
    parser_explore = subparsers.add_parser('explore', help='SharePointドライブの構造を探索')
    parser_explore.add_argument('--path', help='探索するパス（省略時はルート）')
    parser_explore.set_defaults(func=cmd_explore)
    
    # スキップリスト生成コマンド
    parser_skiplist = subparsers.add_parser('skiplist', help='スキップリストを生成')
    parser_skiplist.add_argument('--root', help='SharePointルートフォルダ名（--from-file指定時は無視）')
    parser_skiplist.add_argument('--save', default='logs/skip_list.json', help='スキップリスト保存先パス')
    parser_skiplist.add_argument('--from-file', help='既存のファイルリストJSONからスキップリスト生成')
    parser_skiplist.set_defaults(func=cmd_skiplist)
    
    # ファイル数比較コマンド
    parser_compare = subparsers.add_parser('compare', help='ファイル数を比較')
    parser_compare.add_argument('--onedrive', required=True, help='OneDriveファイルリストJSONパス')
    parser_compare.add_argument('--sharepoint', required=True, help='SharePointファイルリストJSONパス')
    parser_compare.add_argument('--expected', type=int, help='期待されるファイル数')
    parser_compare.set_defaults(func=cmd_compare)
    
    # 対話型コマンド
    parser_interactive = subparsers.add_parser('interactive', help='対話型スキップリスト再構築')
    parser_interactive.set_defaults(func=cmd_interactive)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # コマンド実行
    args.func(args)

if __name__ == "__main__":
    main()
