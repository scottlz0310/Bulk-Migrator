import sys
import os
from dotenv import load_dotenv

# プロジェクトルートの.envを必ず読み込む（OS環境変数優先、なければ.env）
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=False)

# パス調整: testsディレクトリから実行する場合
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.file_crawler import build_skiplist_from_sharepoint, rebuild_skiplist_interactive

def main():
    """
    SharePoint側をクロールしてスキップリストを再構築するメインスクリプト
    """
    print("=== SharePoint側スキップリスト再構築 ===")
    print("1. 設定ファイルの値で自動実行")
    print("2. 対話形式で実行")
    
    choice = input("選択してください (1 or 2, デフォルト: 1): ").strip()
    
    if choice == "2":
        rebuild_skiplist_interactive()
    else:
        # 設定ファイルの値で自動実行
        print("設定ファイルの値で自動実行します...")
        build_skiplist_from_sharepoint()

if __name__ == "__main__":
    main()
