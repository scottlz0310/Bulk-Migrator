# 🚀 対話型セットアップ クイックスタートガイド

OneDrive→SharePoint移行ツールの設定を簡単に行うための対話型セットアップツールです。

## 📋 事前準備

### 1. 必要なPythonライブラリのインストール
```bash
pip install requests
```

### 2. Azure AD アプリケーション登録（未実施の場合）
1. [Azure Portal](https://portal.azure.com) にアクセス
2. **Azure Active Directory** > **アプリの登録** > **新規登録**
3. アプリケーション名を入力して登録
4. **API のアクセス許可** で以下を追加：
   - `Files.ReadWrite.All` (アプリケーション)
   - `Sites.ReadWrite.All` (アプリケーション) 
   - `User.Read.All` (アプリケーション)
5. **管理者の同意を付与**
6. **証明書とシークレット** でクライアントシークレットを作成

## 🔧 セットアップ実行

```bash
python interactive_setup.py
```

## 📝 セットアップフロー

### Step 1: Azure AD アプリケーション情報
- **テナント ID**: Azure AD のディレクトリ ID
- **アプリケーション ID**: 登録したアプリのクライアント ID  
- **クライアントシークレット**: 作成したシークレット値

### Step 2: Graph Explorer 連携
スクリプトが Graph Explorer を自動で開き、必要なクエリを表示します。

**詳細な手順については [🌐 Graph API 情報取得ガイド](GRAPH_API_GUIDE.md) を参照してください。**

#### 主な取得情報
- **ユーザーID**: OneDriveの対象ユーザー識別子
- **サイトID**: SharePointサイトの識別子  
- **ドライブID**: ドキュメントライブラリの識別子

#### 基本的なクエリ例
```http
# ユーザー情報取得
GET https://graph.microsoft.com/v1.0/users/{email}

# サイト情報取得
GET https://graph.microsoft.com/v1.0/sites/{hostname}:/{sitepath}

# ドライブ情報取得
GET https://graph.microsoft.com/v1.0/sites/{site-id}/drives
```

### Step 3: 詳細設定（オプション）
- チャンクサイズ調整（4-16MB推奨）
- 並列処理数設定
- Teams通知設定

### Step 4: 設定保存
- `config.json` 自動生成（機密情報除外）
- 環境変数設定スクリプト生成
- 自動環境変数設定

### Step 5: 設定テスト
- 環境変数確認
- Azure AD 認証テスト
- Graph API 接続テスト
- OneDrive/SharePoint アクセステスト

## 📁 生成されるファイル

| ファイル | 内容 |
|----------|------|
| `config.json` | システム設定（機密情報除外） |
| `setup_environment.ps1` | PowerShell環境変数設定スクリプト |
| `setup_environment.bat` | バッチ環境変数設定スクリプト |

## 🔐 セキュリティ

- 機密情報（クライアントシークレット等）は環境変数に保存
- `config.json` には機密情報を含めない
- 設定スクリプトは実行後に削除を推奨

## ⚡ クイック実行例

```bash
# 1. セットアップ実行
python interactive_setup.py

# 2. 動作確認
python test_environment_setup.py

# 3. メインバッチ実行
python main_batch.py
```

## 🛠️ トラブルシューティング

### 認証エラーが発生する場合
1. Azure AD アプリの権限設定を確認
2. 管理者同意が付与されているか確認
3. テナント ID、アプリケーション ID が正しいか確認

### Graph API でデータが取得できない場合
1. Graph Explorer でログインしているアカウントを確認
2. 必要な権限が付与されているか確認
3. ユーザー ID、サイト ID が正しいか確認

### 環境変数が設定されない場合
1. 管理者権限でコマンドプロンプト/PowerShellを実行
2. 手動でsetxコマンドを実行：
   ```cmd
   setx CLIENT_ID "your-client-id" /M
   setx TENANT_ID "your-tenant-id" /M  
   setx CLIENT_SECRET "your-client-secret" /M
   ```

## 📞 サポート

設定で困った場合は、生成された設定ファイルと以下の情報を確認してください：

- Azure AD アプリケーションの権限設定
- Graph Explorer での API レスポンス
- 環境変数の設定状況
- エラーメッセージの詳細
