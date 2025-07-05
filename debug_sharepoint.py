#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートの.envを読み込み
project_root = Path(__file__).parent
env_path = project_root / '.env'
load_dotenv(env_path, override=True)

# srcディレクトリをパスに追加
sys.path.insert(0, str(project_root / 'src'))

from transfer import GraphTransferClient

def check_sharepoint_structure():
    """SharePointの構造を確認"""
    try:
        site_id = os.getenv('DESTINATION_SHAREPOINT_SITE_ID')
        drive_id = os.getenv('DESTINATION_SHAREPOINT_DRIVE_ID')
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        tenant_id = os.getenv('TENANT_ID')
        
        client = GraphTransferClient(
            client_id=client_id,
            client_secret=client_secret, 
            tenant_id=tenant_id,
            site_id=site_id,
            drive_id=drive_id
        )
        
        print(f"=== SharePoint構造確認 ===")
        print(f"Site ID: {site_id}")
        print(f"Drive ID: {drive_id}")
        
        # 1. ドライブのルートを確認
        print("\n=== ドライブルート確認 ===")
        try:
            root_url = f"/sites/{site_id}/drives/{drive_id}/root/children"
            response = client.graph_client.get(root_url)
            if response and 'value' in response:
                print(f"ルート直下のアイテム数: {len(response['value'])}")
                for item in response['value'][:10]:  # 最初の10件
                    item_type = "📁" if item.get('folder') else "📄"
                    print(f"  {item_type} {item.get('name')}")
                if len(response['value']) > 10:
                    print(f"  ... および {len(response['value']) - 10} 件のその他のアイテム")
            else:
                print("ルートアイテムなし")
        except Exception as e:
            print(f"ルート確認エラー: {e}")
        
        # 2. 「ドキュメント」フォルダを確認
        print("\n=== 'ドキュメント' フォルダ確認 ===")
        try:
            docs_url = f"/sites/{site_id}/drives/{drive_id}/root:/ドキュメント:/children"
            response = client.graph_client.get(docs_url)
            if response and 'value' in response:
                print(f"ドキュメント配下のアイテム数: {len(response['value'])}")
                for item in response['value'][:10]:
                    item_type = "📁" if item.get('folder') else "📄"
                    print(f"  {item_type} {item.get('name')}")
            else:
                print("ドキュメントフォルダなしまたは空")
        except Exception as e:
            print(f"ドキュメント確認エラー: {e}")
        
        # 3. 「LargeScaleTest」フォルダを確認
        print("\n=== 'LargeScaleTest' フォルダ確認 ===")
        try:
            test_url = f"/sites/{site_id}/drives/{drive_id}/root:/ドキュメント/LargeScaleTest:/children"
            response = client.graph_client.get(test_url)
            if response and 'value' in response:
                print(f"LargeScaleTest配下のファイル数: {len(response['value'])}")
                print("✅ LargeScaleTestフォルダが存在し、アクセス可能")
            else:
                print("❌ LargeScaleTestフォルダなしまたは空")
        except Exception as e:
            print(f"❌ LargeScaleTest確認エラー: {e}")
            # フォルダが存在しない場合は作成を提案
            print("\n=== フォルダ作成の提案 ===")
            print("LargeScaleTestフォルダが存在しません。")
            print("手動で作成するか、別のフォルダ名を使用してください。")
        
    except Exception as e:
        print(f"SharePoint接続エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_sharepoint_structure()
