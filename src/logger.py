import logging
import os
from logging.handlers import RotatingFileHandler

# 設定値管理を使用
try:
    from src.config_manager import get_transfer_log_path, get_config
    LOG_PATH = get_transfer_log_path()
    LOG_LEVEL = get_config("log_level", "INFO", "LOG_LEVEL")
except ImportError:
    # フォールバック（直接実行時など）
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path, override=False)
    LOG_PATH = os.environ.get('TRANSFER_LOG_PATH', 'logs/transfer_start_success_error.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# ロガー初期化
logger = logging.getLogger('bulk_migrator')
logger.setLevel(LOG_LEVEL)
if not logger.handlers:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    handler = RotatingFileHandler(LOG_PATH, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 標準出力にも出す
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console)

def log_transfer_start(file_info):
    logger.info(f"START: {file_info['path']} (size={file_info['size']}, lastModified={file_info['lastModifiedDateTime']})")

def log_transfer_success(file_info, elapsed=None):
    msg = f"SUCCESS: {file_info['path']}"
    if elapsed is not None:
        msg += f" [elapsed: {elapsed:.2f}s]"
    logger.info(msg)

def log_transfer_error(file_info, error, retry_count=0):
    logger.error(f"ERROR: {file_info['path']} [retry={retry_count}] {error}")

def log_transfer_skip(file_info):
    logger.info(f"SKIP: {file_info['path']}")
