# OneDrive to SharePoint Bulk Migration Tool

🚀 OneDrive上のファイル群をSharePointへ大容量・高速転送するPythonスクリプト群

## 📋 概要

このツールは、OneDrive上の指定ユーザー配下にある音源・ファイル群をクロール・ダウンロードし、バッチ的にSharePointへ転送・再送する処理系です。**冪等性と耐障害性**を重視し、**ログ主導の制御**と**並列処理による高速化**を設計方針としています。

### 🎯 主な特徴

- ✅ **冪等性**: 処理の中断・再開が可能
- ✅ **耐障害性**: エラー時の自動リトライ機能
- ✅ **大容量対応**: チャンクアップロードによる大容量ファイル対応
- ✅ **並列処理**: 高速な大量ファイル処理
- ✅ **ログ主導**: 処理状況の完全な追跡・管理

## 🏗️ システム構成

```
OneDrive → クロール → ローカル一時保存 → SharePointアップロード
     ↓           ↓              ↓
   index.json  temp_dir/    upload_log.csv
```

## 📁 モジュール構成

| ファイル名 | 責務 |
|-----------|------|
| `auth_helper_app.py` | client_credentials認証・トークン管理 |
| `crawl_onedrive_files.py` | OneDriveファイル走査・index.json出力 |
| `logger_preprocessor.py` | ログのバックアップ・SUCCESS削除 |
| `logger_writer.py` | ログ記録・更新（排他制御対応） |
| `logger_reader.py` | 過去ログからSUCCESSファイル取得 |
| `prepare_pending_files.py` | 未成功ファイルのダウンロード |
| `onedrive_download.py` | OneDrive→ローカルDL処理 |
| `upload_file_to_sharepoint.py` | チャンクアップロード機能 |
| `sharepoint_folder.py` | SharePointフォルダ構造作成 |
| `batch_sync_app.py` | メインアップロード処理 |
| `retry_failed_uploads.py` | 失敗ファイルの再送処理 |

## 🔧 セットアップ

### 1. 必要な依存関係をインストール

```bash
pip install requests msal python-dotenv
```

### 2. 設定ファイルの作成

`config.json`を作成し、以下の設定を記入：

```json
{
  "client_id": "あなたのクライアントID",
  "tenant_id": "あなたのテナントID", 
  "client_secret": "あなたのクライアントシークレット",
  "scopes": ["https://graph.microsoft.com/.default"],
  
  "target_site_hostname": "yourcompany.sharepoint.com",
  "target_site_path": "/sites/yoursite",
  "target_drive_name": "ドキュメント",
  "target_root_path": "音楽",
  
  "onedrive_user_id": "user@yourcompany.onmicrosoft.com",
  "source_onedrive_path": "Music",
  
  "log_file_path": "upload_log.csv",
  "temp_dir": "temp_downloads",
  "max_chunk_size_mb": 4
}
```

### 3. Azure AD アプリケーションの設定

1. Azure Portalでアプリケーション登録
2. API権限設定:
   - `Files.ReadWrite.All`
   - `Sites.ReadWrite.All`
   - `User.Read.All`
3. クライアントシークレット生成

## 🚀 使用方法

### 基本的な実行フロー

```bash
# 1. OneDriveファイルのクロール
python crawl_onedrive_files.py

# 2. 未処理ファイルの準備（ダウンロード）
python prepare_pending_files.py

# 3. SharePointへのアップロード
python batch_sync_app.py

# 4. 失敗ファイルの再送（必要に応じて）
python retry_failed_uploads.py
```

### 認証テスト

```bash
python test_auth_context.py
```

## 📊 ログ仕様

`upload_log.csv`は処理全体をドライブする"真実の情報源"として機能：

| カラム名 | 内容 |
|---------|------|
| `relative_path` | OneDrive/SharePoint上のファイル相対パス |
| `file_name` | ファイル名 |
| `file_size_bytes` | バイト単位のサイズ |
| `status` | `PENDING`/`LOCAL`/`DUPE`/`SUCCESS` |
| `timestamp` | 最終状態更新日時 |
| `comment` | エラー情報・補足（任意） |

### ステータスの意味

- **PENDING**: ダウンロード待ち
- **LOCAL**: ローカルにダウンロード済み
- **DUPE**: SharePointで重複検出
- **SUCCESS**: アップロード完了

## 🔐 セキュリティ設定

### 環境変数の使用（推奨）

機密情報は環境変数で管理することを推奨：

```bash
export CLIENT_SECRET="your_client_secret"
export CLIENT_ID="your_client_id"
export TENANT_ID="your_tenant_id"
```

`.env`ファイルでの管理も可能：

```env
CLIENT_SECRET=your_client_secret
CLIENT_ID=your_client_id
TENANT_ID=your_tenant_id
```

## 🛠️ トラブルシューティング

### よくある問題

#### 1. 認証エラー
```
❌ トークン取得失敗
```
- Azure ADアプリケーションの権限設定を確認
- クライアントシークレットの有効期限を確認

#### 2. アップロード失敗
```
❌ チャンク失敗
```
- ネットワーク接続を確認
- チャンクサイズを小さく設定（`max_chunk_size_mb`）

#### 3. フォルダ作成エラー
```
❌ フォルダ作成失敗
```
- SharePoint側の権限を確認
- パス名に使用禁止文字がないか確認

### ログの確認

処理状況は`upload_log.csv`で確認できます：

```bash
# 成功したファイル数をカウント
grep "SUCCESS" upload_log.csv | wc -l

# 失敗したファイルを確認
grep -v "SUCCESS" upload_log.csv
```

## 🔄 復旧手順

処理が中断された場合の復旧手順：

1. **ログファイルの確認**: `upload_log.csv`で処理済みファイルを確認
2. **再実行**: 各スクリプトは冪等性があるため、そのまま再実行可能
3. **失敗ファイルの再送**: `retry_failed_uploads.py`で個別再送

## 📈 パフォーマンス調整

### 並列処理の設定

```python
# prepare_pending_files.py での並列数調整
with ThreadPoolExecutor(max_workers=4) as executor:  # 4 → 8に変更で高速化
```

### チャンクサイズの調整

```json
{
  "max_chunk_size_mb": 8  // 4MB → 8MBで高速化（ネットワーク環境による）
}
```

## 🧪 テスト

### 小規模テスト

```bash
# 少数のファイルでテスト実行
python batch_sync.py  # Ver0.1のシンプル版
```

### 認証テスト

```bash
python test_auth_context.py
```

## 📝 開発・カスタマイズ

### 新しいログステータスの追加

1. `logger_writer.py`でステータス定義を追加
2. 各処理スクリプトでステータス更新処理を追加

### カスタムフィルタの追加

`crawl_onedrive_files.py`でファイル種別フィルタを実装可能。

## 🤝 貢献・サポート

問題が発生した場合は、以下の情報と共にIssueを作成してください：

- エラーメッセージ
- `upload_log.csv`の関連行
- 実行環境（Python版本、OS等）

---

## 📚 関連ドキュメント

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [SharePoint REST API Reference](https://docs.microsoft.com/en-us/sharepoint/dev/sp-add-ins/sharepoint-rest-api)

---

**💡 Tips**: 大量のファイル処理前には、必ず小規模テストを実行することをお勧めします。
