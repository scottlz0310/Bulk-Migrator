# 🌙 夜間バッチ運用実装案

**作成日**: 2025年6月29日  
**対象**: OneDrive to SharePoint Migration Tool - 夜間バッチ運用

---

## 🎯 夜間バッチ運用の目標

- **無人運用**: 人的介入なしで安定稼働
- **エラー自動復旧**: 一時的な障害からの自動回復
- **監視・通知**: 処理状況とエラーの自動通知
- **スケーラビリティ**: 大量ファイル処理への対応

---

## 🏗️ バッチ運用アーキテクチャ

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  スケジューラ    │───▶│  メインバッチ     │───▶│  監視・通知      │
│  (Task Scheduler)│    │  (main_batch.py) │    │  (monitor.py)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │      処理フロー           │
                    │                          │
                    │ 1. 前処理・検証           │
                    │ 2. OneDriveクロール       │
                    │ 3. ファイルダウンロード    │
                    │ 4. SharePointアップロード │
                    │ 5. 失敗ファイル再送       │
                    │ 6. ログ整理・通知         │
                    └──────────────────────────┘
```

---

## 📝 新規実装が必要なファイル

### 1. `main_batch.py` - メインバッチ制御

**責務**: 全処理の統合制御と監視

```python
#!/usr/bin/env python3
"""
夜間バッチメイン制御スクリプト
- 全処理フローの統合実行
- エラーハンドリング・リトライ制御
- 実行時間監視・タイムアウト制御
"""

import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 設定
BATCH_TIMEOUT = 6 * 60 * 60  # 6時間でタイムアウト
MAX_RETRY_COUNT = 3
RETRY_INTERVAL = 30 * 60  # 30分間隔

class BatchController:
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.setup_logging()
        
    def run_batch(self):
        """メインバッチ実行"""
        try:
            self.pre_check()           # 前処理・検証
            self.crawl_phase()         # OneDriveクロール
            self.download_phase()      # ダウンロード
            self.upload_phase()        # アップロード
            self.retry_phase()         # 失敗再送
            self.post_process()        # 後処理
            
        except Exception as e:
            self.handle_critical_error(e)
            
    def pre_check(self):
        """実行前チェック"""
        # 設定ファイル検証
        # 認証トークン確認
        # ディスク容量チェック
        # 前回実行状況確認
        
    def handle_critical_error(self, error):
        """重要エラーの処理"""
        logging.critical(f"バッチ処理で重要エラー: {error}")
        self.send_alert(f"バッチ処理停止: {error}")
        sys.exit(1)
```

### 2. `batch_scheduler.py` - スケジュール管理

**責務**: 実行タイミング制御と重複実行防止

```python
#!/usr/bin/env python3
"""
バッチスケジュール管理
- 実行時間制御
- 重複実行防止（ロックファイル）
- 実行履歴管理
"""

import os
import sys
import fcntl
from datetime import datetime

class BatchScheduler:
    def __init__(self):
        self.lock_file = "batch.lock"
        self.history_file = "batch_history.log"
        
    def acquire_lock(self):
        """排他制御 - 重複実行防止"""
        try:
            self.lock_handle = open(self.lock_file, 'w')
            fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_handle.write(f"{os.getpid()}\n{datetime.utcnow()}\n")
            self.lock_handle.flush()
            return True
        except IOError:
            return False
            
    def release_lock(self):
        """ロック解放"""
        if hasattr(self, 'lock_handle'):
            fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_UN)
            self.lock_handle.close()
            os.remove(self.lock_file)
```

### 3. `batch_monitor.py` - 監視・通知

**責務**: 処理状況監視と通知

```python
#!/usr/bin/env python3
"""
バッチ監視・通知システム
- 処理進捗監視
- エラー通知
- 処理完了レポート
"""

import smtplib
import requests
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class BatchMonitor:
    def __init__(self, config):
        self.config = config
        self.webhook_url = config.get("teams_webhook_url")
        self.email_config = config.get("email_config", {})
        
    def send_teams_notification(self, message, is_error=False):
        """Microsoft Teams通知"""
        color = "FF0000" if is_error else "00FF00"
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": "バッチ処理通知",
            "sections": [{
                "activityTitle": "OneDrive to SharePoint Migration",
                "activitySubtitle": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "text": message
            }]
        }
        
        requests.post(self.webhook_url, json=payload)
        
    def send_email_report(self, subject, body):
        """メール通知"""
        msg = MimeMultipart()
        msg['From'] = self.email_config['from']
        msg['To'] = self.email_config['to']
        msg['Subject'] = subject
        msg.attach(MimeText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP(self.email_config['smtp_server']) as server:
            server.send_message(msg)
            
    def generate_daily_report(self):
        """日次レポート生成"""
        # upload_log.csvから統計情報を生成
        # 成功件数、失敗件数、処理時間等
        pass
```

### 4. `batch_config.py` - 設定管理強化

**責務**: 環境別設定とバリデーション

```python
#!/usr/bin/env python3
"""
バッチ運用設定管理
- 環境変数からの設定読み込み
- 設定値検証
- 環境別設定切り替え
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

class BatchConfig:
    def __init__(self, env="production"):
        self.env = env
        self.config = self.load_config()
        self.validate_config()
        
    def load_config(self) -> Dict[str, Any]:
        """設定読み込み（環境変数優先）"""
        # 基本設定をファイルから読み込み
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            
        # 機密情報は環境変数から上書き
        config["client_secret"] = os.getenv("CLIENT_SECRET", config.get("client_secret"))
        config["tenant_id"] = os.getenv("TENANT_ID", config.get("tenant_id"))
        
        # 環境別設定
        if self.env == "production":
            config["max_workers"] = 8
            config["retry_count"] = 5
        elif self.env == "development":
            config["max_workers"] = 2
            config["retry_count"] = 2
            
        return config
        
    def validate_config(self):
        """設定値検証"""
        required_keys = [
            "client_id", "tenant_id", "client_secret",
            "target_site_hostname", "onedrive_user_id"
        ]
        
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"必須設定項目が不足: {key}")
                
        # 値の妥当性チェック
        if self.config.get("max_chunk_size_mb", 0) <= 0:
            raise ValueError("max_chunk_size_mb は正の数値である必要があります")
```

---

## 🔧 既存ファイルの改修

### 1. `auth_helper_app.py` の改修

**改修内容**: バッチ運用に適したエラーハンドリング

```python
# 追加：リトライ機能付きトークン取得
def get_token_with_retry(conf, max_retry=3):
    """リトライ機能付きトークン取得"""
    for attempt in range(max_retry):
        try:
            return get_token(conf)
        except Exception as e:
            if attempt == max_retry - 1:
                raise
            logging.warning(f"トークン取得失敗 (試行 {attempt + 1}/{max_retry}): {e}")
            time.sleep(30)  # 30秒待機
```

### 2. ログ機能の統合・強化

**新規ファイル**: `batch_logger.py`

```python
#!/usr/bin/env python3
"""
バッチ運用向けログ管理
- 構造化ログ
- ログローテーション
- 統計情報記録
"""

import logging
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from threading import Lock

class BatchLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.setup_logger()
        self._stats_lock = Lock()
        self.stats = {
            "files_processed": 0,
            "files_success": 0,
            "files_failed": 0,
            "bytes_transferred": 0
        }
        
    def setup_logger(self):
        """ログ設定"""
        # メインログ
        main_handler = RotatingFileHandler(
            self.log_dir / "batch_main.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=30
        )
        
        # エラーログ
        error_handler = RotatingFileHandler(
            self.log_dir / "batch_error.log",
            maxBytes=5*1024*1024,   # 5MB
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        
        # フォーマット
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        main_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        # ロガー設定
        self.logger = logging.getLogger("batch")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        
    def update_stats(self, **kwargs):
        """統計情報更新"""
        with self._stats_lock:
            for key, value in kwargs.items():
                if key in self.stats:
                    self.stats[key] += value
                    
    def get_stats_summary(self):
        """統計サマリー取得"""
        with self._stats_lock:
            return self.stats.copy()
```

---

## ⚙️ Windows Task Scheduler 設定

### PowerShell設定スクリプト

**新規ファイル**: `setup_scheduler.ps1`

```powershell
# Windows Task Scheduler設定
$TaskName = "OneDriveToSharePointBatch"
$ScriptPath = "C:\Repository\bulk-safe-copy\main_batch.py"
$PythonPath = "C:\Python\python.exe"

# タスク作成
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath
$Trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal
```

### バッチファイル

**新規ファイル**: `run_batch.bat`

```batch
@echo off
cd /d "C:\Repository\bulk-safe-copy"

REM 環境変数設定
set CLIENT_SECRET=%BATCH_CLIENT_SECRET%
set TENANT_ID=%BATCH_TENANT_ID%

REM Python実行
python main_batch.py

REM 終了コード確認
if %ERRORLEVEL% neq 0 (
    echo バッチ処理でエラーが発生しました: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo バッチ処理が正常に完了しました
```

---

## 📊 監視・アラート設定

### 1. 処理時間監視

```python
# main_batch.py内で実装
def monitor_execution_time(self):
    """実行時間監視"""
    elapsed = datetime.utcnow() - self.start_time
    if elapsed > timedelta(hours=5):  # 5時間超過でアラート
        self.send_alert(f"バッチ処理時間が長時間実行中: {elapsed}")
```

### 2. ディスク容量監視

```python
def check_disk_space(self, path, min_gb=10):
    """ディスク容量チェック"""
    import shutil
    free_gb = shutil.disk_usage(path).free / (1024**3)
    if free_gb < min_gb:
        raise RuntimeError(f"ディスク容量不足: {free_gb:.1f}GB < {min_gb}GB")
```

### 3. Microsoft Teams通知設定

**Webhook URL設定例**:
```json
{
  "teams_webhook_url": "https://outlook.office.com/webhook/xxx",
  "notification_settings": {
    "send_on_start": true,
    "send_on_success": true,
    "send_on_error": true,
    "send_daily_summary": true
  }
}
```

---

## 🔄 エラー回復戦略

### 1. 自動リトライ設定

```python
class RetryStrategy:
    def __init__(self):
        self.retry_configs = {
            "network_error": {"max_retry": 5, "delay": 60},
            "auth_error": {"max_retry": 3, "delay": 300},
            "rate_limit": {"max_retry": 10, "delay": 900}
        }
        
    def should_retry(self, error_type, attempt):
        config = self.retry_configs.get(error_type, {"max_retry": 1, "delay": 0})
        return attempt < config["max_retry"]
```

### 2. 部分実行継続

```python
def resume_from_checkpoint(self):
    """チェックポイントからの再開"""
    checkpoint_file = "batch_checkpoint.json"
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
            return checkpoint.get("last_processed_file")
    return None
```

---

## 📈 性能最適化

### 1. 並列処理設定

```python
# main_batch.py
OPTIMAL_WORKERS = {
    "download": 4,    # ダウンロード並列数
    "upload": 2,      # アップロード並列数（SharePoint制限考慮）
    "crawl": 1        # クロールは単一スレッド
}
```

### 2. バッチサイズ調整

```python
BATCH_SIZES = {
    "small_files": 100,    # 1MB未満
    "medium_files": 50,    # 1-10MB
    "large_files": 10      # 10MB以上
}
```

---

## 🛡️ セキュリティ強化

### 1. 機密情報管理

```powershell
# 環境変数設定（システム管理者権限で実行）
[Environment]::SetEnvironmentVariable("BATCH_CLIENT_SECRET", "機密情報", "Machine")
[Environment]::SetEnvironmentVariable("BATCH_TENANT_ID", "機密情報", "Machine")
```

### 2. ログ保護

```python
# 機密情報のマスキング
def mask_sensitive_data(log_message):
    """機密情報のマスキング"""
    import re
    # アクセストークンをマスク
    log_message = re.sub(r'Bearer [A-Za-z0-9+/=]{100,}', 'Bearer ***MASKED***', log_message)
    return log_message
```

---

## 📋 運用チェックリスト

### 導入前チェック
- [ ] Windows Task Scheduler設定完了
- [ ] 環境変数設定完了
- [ ] ログディレクトリ作成・権限設定
- [ ] 通知設定（Teams/Email）テスト
- [ ] 小規模データでのテスト実行
- [ ] エラー処理のテスト

### 運用開始後の定期チェック
- [ ] 日次処理結果確認
- [ ] ログファイルサイズ監視
- [ ] ディスク容量監視
- [ ] 処理時間トレンド確認
- [ ] エラー発生パターン分析

### 月次メンテナンス
- [ ] 古いログファイルの整理
- [ ] 設定ファイルの見直し
- [ ] 処理性能の評価・改善
- [ ] セキュリティパッチ適用確認

---

## 🚀 段階的導入計画

### Phase 1: 基盤構築（1週間）
1. `main_batch.py`の実装
2. `batch_config.py`の実装
3. 基本的な監視機能

### Phase 2: 運用機能追加（2週間）
1. `batch_monitor.py`の実装
2. Windows Task Scheduler設定
3. 通知機能の実装

### Phase 3: 最適化・安定化（1週間）
1. 性能チューニング
2. エラー処理の強化
3. 運用ドキュメント整備

**総実装期間**: 約4週間

---

**⚠️ 重要**: 本格運用開始前に、必ずテスト環境での十分な検証を実施してください。
