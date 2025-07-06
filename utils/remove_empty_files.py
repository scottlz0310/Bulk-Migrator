#!/usr/bin/env python3
"""
空ファイル（サイズ0バイト）を検索・削除するスクリプト

【使い方】
  # 空ファイルを検索のみ（削除しない）
  $ python utils/remove_empty_files.py

  # 空ファイルを検索して削除
  $ python utils/remove_empty_files.py --delete

  # 特定フォルダ内の空ファイルを検索
  $ python utils/remove_empty_files.py --path src/

  # 特定の拡張子のみ対象（例：.pyファイルのみ）
  $ python utils/remove_empty_files.py --extensions .py,.txt

  # 特定のフォルダを除外して検索
  $ python utils/remove_empty_files.py --exclude logs,tests

  # .gitignoreや隠しファイルも含めて検索
  $ python utils/remove_empty_files.py --include-hidden

  # 特定フォルダを除外（カンマ区切りで複数指定可能）
  $ python utils/remove_empty_files.py --exclude logs,temp,venv

【注意事項】
  - デフォルトでは検索のみで削除は行いません
  - --delete オプション使用時は十分注意してください
  - .git/ フォルダ内は自動で除外されます
"""

import os
import argparse
from pathlib import Path
import fnmatch

def should_exclude_path(path, include_hidden=False, exclude_dirs=None):
    """除外すべきパスかどうかを判定"""
    path_str = str(path)
    
    # .git フォルダは常に除外
    if '/.git/' in path_str or path_str.endswith('/.git'):
        return True
    
    # 指定された除外ディレクトリをチェック
    if exclude_dirs:
        path_parts = path.parts
        for exclude_dir in exclude_dirs:
            if exclude_dir in path_parts:
                return True
            # パスの一部にマッチするかチェック
            for part in path_parts:
                if exclude_dir == part:
                    return True
    
    # 隠しファイル/フォルダの処理
    if not include_hidden:
        parts = path.parts
        for part in parts:
            if part.startswith('.') and part not in ['.', '..']:
                return True
    
    return False

def find_empty_files(search_path='.', extensions=None, include_hidden=False, exclude_dirs=None):
    """空ファイルを検索"""
    empty_files = []
    search_path = Path(search_path)
    
    print(f"検索対象パス: {search_path.absolute()}")
    if extensions:
        print(f"対象拡張子: {extensions}")
    if exclude_dirs:
        print(f"除外ディレクトリ: {exclude_dirs}")
    print(f"隠しファイル含む: {include_hidden}")
    print("-" * 50)
    
    for root, dirs, files in os.walk(search_path):
        root_path = Path(root)
        
        # 除外すべきディレクトリを削除（os.walkの動作を制御）
        dirs[:] = [d for d in dirs if not should_exclude_path(root_path / d, include_hidden, exclude_dirs)]
        
        for file in files:
            file_path = root_path / file
            
            # パスの除外チェック
            if should_exclude_path(file_path, include_hidden, exclude_dirs):
                continue
            
            # 拡張子フィルタ
            if extensions:
                if not any(file.endswith(ext) for ext in extensions):
                    continue
            
            try:
                # ファイルサイズチェック
                if file_path.stat().st_size == 0:
                    empty_files.append(file_path)
                    print(f"空ファイル発見: {file_path}")
            except (OSError, PermissionError) as e:
                print(f"アクセスエラー: {file_path} - {e}")
    
    return empty_files

def delete_files(files, dry_run=True):
    """ファイルを削除"""
    if not files:
        print("削除対象のファイルはありません。")
        return
    
    print(f"\n削除対象ファイル数: {len(files)}")
    print("-" * 50)
    
    if dry_run:
        print("【プレビューモード】以下のファイルが削除対象です:")
        for file_path in files:
            print(f"  {file_path}")
        print("\n実際に削除するには --delete オプションを使用してください。")
        return
    
    # 確認プロンプト
    print("以下のファイルを削除します:")
    for file_path in files:
        print(f"  {file_path}")
    
    confirm = input(f"\n{len(files)}個のファイルを削除しますか？ (y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("削除をキャンセルしました。")
        return
    
    # 削除実行
    deleted_count = 0
    for file_path in files:
        try:
            file_path.unlink()
            print(f"削除完了: {file_path}")
            deleted_count += 1
        except Exception as e:
            print(f"削除失敗: {file_path} - {e}")
    
    print(f"\n削除完了: {deleted_count}/{len(files)} ファイル")

def main():
    parser = argparse.ArgumentParser(
        description="空ファイル（サイズ0バイト）を検索・削除するスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python utils/remove_empty_files.py                    # 検索のみ
  python utils/remove_empty_files.py --delete           # 検索して削除
  python utils/remove_empty_files.py --path src/        # srcフォルダ内を検索
  python utils/remove_empty_files.py --extensions .py,.txt  # 特定拡張子のみ
        """
    )
    
    parser.add_argument(
        '--path', 
        default='.', 
        help='検索対象パス (デフォルト: カレントディレクトリ)'
    )
    
    parser.add_argument(
        '--delete', 
        action='store_true', 
        help='空ファイルを実際に削除する'
    )
    
    parser.add_argument(
        '--extensions', 
        help='対象とする拡張子をカンマ区切りで指定 (例: .py,.txt,.log)'
    )
    
    parser.add_argument(
        '--include-hidden', 
        action='store_true', 
        help='隠しファイル・隠しフォルダも検索対象に含める'
    )
    
    parser.add_argument(
        '--exclude', 
        help='除外するディレクトリ名をカンマ区切りで指定 (例: logs,temp,venv)'
    )
    
    args = parser.parse_args()
    
    # 拡張子の処理
    extensions = None
    if args.extensions:
        extensions = [ext.strip() for ext in args.extensions.split(',')]
        # 先頭に . がない場合は追加
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    
    # 除外ディレクトリの処理
    exclude_dirs = None
    if args.exclude:
        exclude_dirs = [dir_name.strip() for dir_name in args.exclude.split(',')]
    
    # 空ファイル検索
    empty_files = find_empty_files(
        search_path=args.path,
        extensions=extensions,
        include_hidden=args.include_hidden,
        exclude_dirs=exclude_dirs
    )
    
    # 削除処理
    delete_files(empty_files, dry_run=not args.delete)

if __name__ == '__main__':
    main()
