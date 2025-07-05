# 🌙 OneDrive to SharePoint Bulk Migration Tool v2.1

**ログクリーンナップ機能追加版** - OneDrive上のファイル群をSharePointへ大容量・高速転送するPythonスクリプト群

## 📋 概要

このツールは、OneDrive上の指定ユーザー配下にあるファイル群をクロール・ダウンロードし、バッチ的にSharePointへ転送する処理系です。**冪等性と耐障害性**を重視し、**ログ主導の制御**と**並列処理による高速化**、**夜間バッチ運用**を設計方針としています。

### 🎯 主な特徴

- ✅ **夜間バッチ運用**: Windows Task Schedulerによる自動実行
- ✅ **冪等性**: 処理の中断・再開が可能
- ✅ **耐障害性**: エラー時の自動リトライ機能
- ✅ **大容量対応**: チャンクアップロードによる大容量ファイル対応
- ✅ **並列処理**: 高速な大量ファイル処理
- ✅ **監視・通知**: Microsoft Teams/メール通知
- ✅ **セキュリティ**: 環境変数による機密情報管理
- ✅ **ログクリーンナップ**: 設定変更時の自動ログ整理 🆕 v2.1

### 🆕 v2.1 新機能ハイライト

- 🧹 **インテリジェントログクリーンナップ**: 設定変更を自動検出
- 🤝 **対話式確認**: ユーザーフレンドリーな選択インターフェース
- 💾 **安全なバックアップ**: 既存ログを自動保護
- 📊 **ログ統計表示**: 処理済みファイル数や実行履歴の確認

## 🏗️ システム構成

```
OneDrive → クロール → ローカル一時保存 → SharePointアップロード
     ↓           ↓              ↓
   index.json  temp_dir/    logs/upload_log.csv
                                ↓
                      [監視・通知システム]
                          ↓
                    Teams/メール通知
```

## 📁 ファイル構成

```
bulk-safe-copy/
├── main_batch.py              # メインバッチ制御
├── batch_config.py            # 設定管理
├── batch_logger.py            # ログ管理
├── batch_monitor.py           # 監視・通知
├── batch_scheduler.py         # スケジュール管理
├── auth_helper.py             # 認証処理
├── onedrive_crawler.py        # OneDriveクローラー
├── file_downloader.py         # ファイルダウンローダー
├── sharepoint_uploader.py     # SharePointアップローダー
├── log_manager.py             # CSVログ管理
├── graph_api_helper.py        # Graph API共通処理 ⭐NEW
├── interactive_setup.py       # 対話型セットアップ ⭐NEW
├── log_cleanup_helper.py      # ログクリーンナップ ⭐NEW v2.1
├── config.json                # 設定ファイル
├── run_batch.bat             # バッチ実行スクリプト
├── setup_scheduler.ps1       # スケジューラー設定
├── setup_environment.ps1     # 環境変数設定
├── SETUP_GUIDE.md            # 対話型セットアップガイド ⭐NEW
├── GRAPH_API_GUIDE.md        # Graph API情報取得ガイド ⭐NEW
├── requirements.txt          # Python依存関係
├── doc/                      # ドキュメント
│   ├── README.md
│   ├── ISSUES.md
│   ├── BATCH_OPERATION_PLAN.md
│   ├── GRAPH_API_INTEGRATION_REPORT.md  ⭐NEW
│   └── システム全体の目的.md
├── Ver0.2/                   # 旧バージョン
├── logs/                     # ログファイル
└── temp_downloads/           # 一時ダウンロード
```

## 🔧 セットアップ

### 🚀 簡単セットアップ（推奨）

**対話型セットアップスクリプト**を使用することで、Graph Explorerと連携して必要な情報を自動取得できます：

```bash
# 1. 依存関係のインストール
pip install -r requirements.txt

# 2. 対話型セットアップ実行
python interactive_setup.py
```

#### 対話型セットアップの特徴
- 🌐 **Graph Explorer自動連携**: ブラウザが自動で開き、必要なクエリを表示
- 🔍 **ID自動取得ガイド**: ユーザーID、サイトID、ドライブIDを段階的に取得
- 🔐 **セキュリティ配慮**: 機密情報は環境変数で安全管理
- 📝 **設定ファイル自動生成**: config.jsonと環境変数スクリプトを自動作成
- ✅ **設定検証**: 入力内容の妥当性を自動チェック

#### セットアップフロー
1. **Azure AD情報入力**: テナントID、クライアントID、クライアントシークレット
2. **Graph Explorer連携**: OneDriveユーザー情報とSharePointサイト情報の取得
3. **詳細設定**: パフォーマンス設定と通知設定（オプション）
4. **設定保存**: config.jsonと環境変数スクリプトの自動生成
5. **設定テスト**: 認証と接続の動作確認

詳細な手順は [🚀 対話型セットアップ クイックスタートガイド](SETUP_GUIDE.md) を参照してください。

---

### 🔧 手動セットアップ（上級者向け）

対話型セットアップを使わない場合の手動設定手順：

#### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

#### 2. Azure AD アプリケーションの設定

1. [Azure Portal](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) でアプリケーション登録
2. API権限設定:
   - `Files.ReadWrite.All` (アプリケーション)
   - `Sites.ReadWrite.All` (アプリケーション)
   - `User.Read.All` (アプリケーション)
3. 管理者の同意を付与
4. クライアントシークレット生成

#### 3. Graph Explorerでの情報取得

必要なID情報を取得するため、Graph Explorerを使用します。

詳細な手順は **[🌐 Graph API 情報取得ガイド](GRAPH_API_GUIDE.md)** を参照してください。

**取得が必要な情報:**
- テナントID（組織のディレクトリID）
- ユーザーID（OneDriveの対象ユーザー）
- サイトID（SharePointサイト識別子）
- ドライブID（ドキュメントライブラリID）

#### 4. 環境変数の設定

**管理者権限のPowerShellで実行:**

```powershell
.\setup_environment.ps1 -ClientId "your_client_id" -TenantId "your_tenant_id" -ClientSecret "your_client_secret" -TeamsWebhookUrl "your_webhook_url"
```

#### 5. 設定ファイルの編集

`config.json`を編集し、SharePointとOneDriveの設定を記入：

```json
{
  "target_site_hostname": "yourcompany.sharepoint.com",
  "target_site_path": "/sites/yoursite",
  "target_drive_id": "b!AbCdEfGhIjKlMnOpQrStUvWxYz",
  "target_root_path": "音楽",
  "onedrive_user_id": "12345678-abcd-efgh-ijkl-123456789012",
  "source_onedrive_path": "Music"
}
```

#### 6. Windows Task Schedulerの設定

**管理者権限のPowerShellで実行:**

```powershell
.\setup_scheduler.ps1
```

## 🚀 使用方法

### 🧪 セットアップ確認（初回必須）

対話型セットアップ完了後、以下のコマンドで動作確認：

```bash
# 設定ファイル読み込みテスト
python test_config_loading.py

# 認証テスト
python test_simple_auth.py

# Graph API接続テスト  
python test_graph_api_integration.py
```

### 手動実行（テスト用）

```bash
# バッチファイルで実行
run_batch.bat

# または直接Python実行
python main_batch.py
```

### 夜間バッチ実行

Windows Task Schedulerにより毎日午前2時に自動実行されます。

### ログ確認

```bash
# メインログ
type logs\batch_main.log

# エラーログ
type logs\batch_error.log

# 処理状況（CSV）
type logs\upload_log.csv
```

## 📊 ログ仕様

`logs/upload_log.csv`は処理全体をドライブする"真実の情報源"として機能：

| カラム名 | 内容 |
|---------|------|
| `relative_path` | OneDrive/SharePoint上のファイル相対パス |
| `file_name` | ファイル名 |
| `file_size_bytes` | バイト単位のサイズ |
| `status` | `PENDING`/`LOCAL`/`SUCCESS`/`FAILED` |
| `timestamp` | 最終状態更新日時 |
| `comment` | エラー情報・補足 |

### ステータスの意味

- **PENDING**: ダウンロード待ち
- **LOCAL**: ローカルにダウンロード済み
- **SUCCESS**: アップロード完了
- **FAILED**: 処理失敗

## 🔔 監視・通知

### Microsoft Teams通知

Webhook URLを設定することで以下の通知を受信：

- バッチ処理開始/完了通知
- エラー発生時の即座通知
- 日次処理サマリー

### メール通知

SMTP設定により同様の通知をメールで受信可能。

## 🛠️ トラブルシューティング

### よくある問題

#### 1. 認証エラー

```
❌ トークン取得失敗
```

**解決方法:**
- 環境変数の設定確認: `echo %CLIENT_SECRET%`
- Azure ADアプリケーションの権限確認
- クライアントシークレットの有効期限確認

#### 2. バッチ実行エラー

```
❌ 別のバッチプロセスが実行中
```

**解決方法:**
- ロックファイル削除: `del batch.lock`
- プロセス確認: `tasklist | findstr python`

#### 3. ディスク容量不足

```
❌ ディスク容量不足
```

**解決方法:**
- 一時ファイル削除: `rd /s temp_downloads`
- 古いログ削除: PowerShellで `Get-ChildItem logs\*.log | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item`

### ログの確認方法

```bash
# 成功したファイル数
findstr "SUCCESS" logs\upload_log.csv | find /c /v ""

# 失敗したファイル一覧
findstr "FAILED" logs\upload_log.csv

# 最新の実行ログ
Get-Content logs\batch_main.log -Tail 50
```

## 🔄 復旧手順

処理が中断された場合：

1. **ログファイル確認**: `logs/upload_log.csv`で処理済みファイルを確認
2. **ロックファイル削除**: `batch.lock`が残っている場合は削除
3. **再実行**: `run_batch.bat`で再実行（冪等性により安全）

## 📈 パフォーマンス調整

### 並列処理数の調整

`config.json`で調整：

```json
{
  "batch_settings": {
    "max_workers_download": 8,    // ダウンロード並列数
    "max_workers_upload": 4,      // アップロード並列数
    "max_retry_count": 5,         // リトライ回数
    "batch_timeout_hours": 8      // タイムアウト時間
  }
}
```

### チャンクサイズの調整

```json
{
  "max_chunk_size_mb": 8  // 4MB → 8MBで高速化
}
```

## 🛡️ セキュリティ

### 🔐 機密情報管理（v2.1.1 セキュリティ強化）

- ✅ **環境変数による機密情報管理**: CLIENT_SECRET等は環境変数で管理
- ✅ **平文保存の完全防止**: 設定ファイルやスクリプトに機密情報を平文保存しない
- ✅ **セキュアセットアップ**: 機密情報を含まない手動設定ガイド方式
- ✅ **自動クリーンアップ**: 危険なファイルの自動検出・削除機能
- ✅ **.gitignore保護**: 機密情報ファイルのバージョン管理除外
- ✅ **ログ内アクセストークンのマスキング**: ログ出力時の機密情報保護

### 🚨 セキュリティ重要事項

⚠️ **絶対に避けること**:
- ❌ `setup_environment.bat`や`.ps1`ファイルに機密情報を保存
- ❌ 設定ファイルに`CLIENT_SECRET`を平文で記録
- ❌ 機密情報を含むファイルのバージョン管理への追加

✅ **推奨される安全な方法**:
1. **セキュア方式**: `python interactive_setup.py`でセキュア方式を選択
2. **手動設定**: 生成されたガイドを参照してAzure Portalから手動コピー
3. **環境変数**: PowerShellで直接システム環境変数に設定
4. **定期的清掃**: `python secure_setup_helper.py`で危険ファイルを確認

### 📋 セキュリティチェックリスト

**導入時**:
- [ ] セキュア方式でのセットアップ実行
- [ ] 機密情報の平文ファイル保存なし確認  
- [ ] 環境変数設定の完了確認
- [ ] 危険ファイルの存在チェック

**運用時**:
- [ ] 定期的なセキュリティファイルスキャン
- [ ] ログファイルの機密情報混入チェック
- [ ] バックアップ時の機密情報除外確認

詳細は **[🔐 セキュリティ強化レポート](SECURITY_ENHANCEMENT_REPORT.md)** を参照してください。

### アクセス制御

- Windows Task SchedulerでSYSTEMアカウント実行
- 適切なファイル権限設定

## 📋 運用チェックリスト

### 導入時
- [ ] **対話型セットアップ実行**: `python interactive_setup.py` 完了
- [ ] **設定確認テスト**: `python test_config_loading.py` 成功
- [ ] **認証テスト**: `python test_simple_auth.py` 成功
- [ ] **Graph API接続テスト**: `python test_graph_api_integration.py` 成功
- [ ] **ログクリーンナップテスト**: 設定変更後の動作確認 🆕 v2.1
- [ ] Windows Task Scheduler設定完了
- [ ] 小規模テスト実行成功

### 日次確認
- [ ] バッチ処理成功通知確認
- [ ] エラー通知の有無確認
- [ ] ディスク容量確認

### 週次確認
- [ ] ログファイルサイズ確認
- [ ] 処理性能トレンド確認
- [ ] 失敗ファイルパターン分析

## 🆕 Ver2.0の新機能

- 🌙 **夜間バッチ運用対応**
- 🔔 **Teams/メール通知システム**
- 🔒 **セキュリティ強化**（環境変数管理）
- 📊 **詳細ログ・統計機能**
- ⚡ **並列処理最適化**
- 🛡️ **エラー回復機能強化**
- 🔗 **Graph API統合処理** ⭐NEW
- 🚀 **対話型セットアップツール** ⭐NEW
- 📝 **包括的な運用ドキュメント**

## 📚 関連ドキュメント

- [🚀 対話型セットアップ クイックスタートガイド](SETUP_GUIDE.md) - 簡単セットアップ手順 ⭐NEW
- [🌐 Graph API 情報取得ガイド](GRAPH_API_GUIDE.md) - 必要ID取得の詳細手順 ⭐NEW
- [📝 リリースノート](RELEASE_NOTES.md) - バージョン履歴と更新内容 🆕 v2.1
- [問題点分析レポート](doc/ISSUES.md) - ✅ 全問題解決済み
- [夜間バッチ運用実装案](doc/BATCH_OPERATION_PLAN.md)
- [Graph API統合リファクタリング報告](doc/GRAPH_API_INTEGRATION_REPORT.md)
- [システム整理完了レポート](doc/SYSTEM_CLEANUP_COMPLETE_REPORT.md) ⭐NEW
- [システム全体の目的](doc/システム全体の目的.md)

---

## 📞 サポート

問題が発生した場合は、以下の情報と共に報告してください：

- エラーメッセージ
- `logs/batch_error.log`の関連行
- `logs/upload_log.csv`の関連行
- 実行環境（Windows版本、Python版本等）

---

**💡 Tips**: 本格運用前には、必ず少量のテストデータで動作確認を行ってください。

## 🧹 ログクリーンナップ機能 (v2.1)

v2.1では、設定変更時のログ管理を自動化する**インテリジェントログクリーンナップ機能**を追加しました。

### 📋 機能概要

設定を変更（移行元/先パスの変更、ユーザー変更など）すると、過去のログが新しい移行タスクと混在して以下の問題が発生する可能性があります：

- ❌ **重複チェックの誤作動**: 異なる設定での成功ファイルが「処理済み」として誤認識
- ❌ **統計情報の混在**: 複数のタスクの結果が混在し、正確な統計が取れない
- ❌ **デバッグの困難**: トラブル発生時にどの設定での実行か特定困難

### 🎯 自動解決メカニズム

```
1. 設定変更の自動検出
   ├─ 前回実行時の設定と比較
   ├─ 重要パラメータの変更をチェック
   └─ 初回実行か継続実行かを判定

2. 対話式確認プロンプト
   ├─ [y] クリーンナップ実行（推奨）
   ├─ [n] 既存ログに追記
   └─ [v] ログ内容確認

3. 安全なバックアップ
   ├─ logs/backup/YYYYMMDD_HHMMSS/ に既存ログを移動
   ├─ 設定履歴も保存
   └─ 新しいログファイルで実行開始
```

### 💡 使用例

```bash
# 設定を変更後、バッチ実行時
python main_batch.py

# 出力例:
# 🔍 設定変更が検出されました:
# 📝 OneDrive移行元パス: Music → Photos
# 📝 SharePoint移行先パス: 音楽 → 写真
# 
# ❓ ログファイルをクリーンナップしますか？
#    [y] はい（推奨）- 古いログをバックアップして新規開始
#    [n] いいえ - 既存ログに追記
#    [v] 表示 - 既存ログの内容を確認
# 
# 選択してください [y/n/v]: y
# 📁 ログを logs/backup/20250630_120000 にバックアップしました
# 🚀 ログクリーンナップ完了。新規実行を開始します。
```

### 🗂️ バックアップ管理

- **自動タイムスタンプ**: `logs/backup/YYYYMMDD_HHMMSS/`形式
- **全ログ保持**: upload_log.csv, batch_main.log, batch_error.log等
- **設定履歴**: last_run_config.jsonも併せて保存
- **手動復元**: 必要に応じてバックアップから復元可能

### ⚙️ 対象設定項目

以下の設定変更時にクリーンナップが提案されます：

- `source_onedrive_path`: OneDrive移行元パス
- `target_root_path`: SharePoint移行先パス  
- `onedrive_user_id`: 対象ユーザーID
- `target_drive_id`: 移行先ドライブID

---
