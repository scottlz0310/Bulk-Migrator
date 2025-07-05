#!/usr/bin/env python3
import os
from pathlib import Path

# プロジェクトルートの.envファイルを読み込み
project_root = Path(__file__).parent
env_path = project_root / '.env'

print(f"Project root: {project_root}")
print(f"Env file path: {env_path}")
print(f"Env file exists: {env_path.exists()}")

try:
    from dotenv import load_dotenv
    print("dotenv imported successfully")
    
    result = load_dotenv(env_path, override=True)
    print(f"load_dotenv result: {result}")
    
    # 環境変数の確認
    client_id = os.getenv('CLIENT_ID')
    print(f"CLIENT_ID: {client_id}")
    
    tenant_id = os.getenv('TENANT_ID')
    print(f"TENANT_ID: {tenant_id}")
    
    source_user = os.getenv('SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME')
    print(f"SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME: {source_user}")
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
