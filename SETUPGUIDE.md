# SETUPGUIDE.md

## Microsoft Graph API 利用のためのセットアップ手順

---

### 1. Azureポータルでアプリ登録（クライアントID/シークレット取得）

1. [Azure Portal](https://portal.azure.com/) に管理者アカウントでログイン
2. 「Azure Active Directory」→「アプリの登録」→「新規登録」
3. 名前を入力し、リダイレクトURIは空欄でOK
4. 登録後「アプリケーション(クライアント)ID」をコピー → `.env` の `CLIENT_ID` に貼り付け
5. 「証明書とシークレット」→「新しいクライアント シークレット」→説明と有効期限を設定し「追加」
6. 生成された値をコピー → `.env` の `CLIENT_SECRET` に貼り付け（再表示不可なので注意）
7. 「ディレクトリ(テナント)ID」もコピー → `.env` の `TENANT_ID` に貼り付け

---

### 2. API権限の付与

1. 「APIのアクセス許可」→「Microsoft Graph」→「委任されたアクセス許可」または「アプリケーションのアクセス許可」
2. 必要な権限例：
   - `Files.Read.All`
   - `Files.ReadWrite.All`
   - `Sites.Read.All`
   - `Sites.ReadWrite.All`
   - `User.Read`
3. 追加後、「管理者の同意を与える」を必ず実行

---

### 3. Graph ExplorerでID情報を確認

1. [Microsoft Graph Explorer](https://developer.microsoft.com/ja-jp/graph/graph-explorer)
2. サインインし、以下のAPIで各種IDを取得

#### OneDriveのDrive ID取得
```
GET /me/drive
または
GET /users/{userPrincipalName}/drive
```
- レスポンスの`id` → `.env` の `SOURCE_ONEDRIVE_DRIVE_ID` に

#### SharePointのSite ID/Drive ID取得
```
GET /sites/{domain}.sharepoint.com:/sites/{site-path}
```
- レスポンスの`id` → `.env` の `DESTINATION_SHAREPOINT_SITE_ID` に

```
GET /sites/{site-id}/drives
```
- レスポンスの`id` → `.env` の `DESTINATION_SHAREPOINT_DRIVE_ID` に

#### ドキュメントライブラリ名（ルートフォルダ名）
- SharePointサイトの「ドキュメント」ライブラリ名を確認し、`.env` の `DESTINATION_SHAREPOINT_DOCLIB` に

---

### 4. .envファイルへの記入例

```ini
CLIENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
CLIENT_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TENANT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME="user@domain.onmicrosoft.com"
SOURCE_ONEDRIVE_FOLDER_PATH="Documents/サンプル"
SOURCE_ONEDRIVE_DRIVE_ID="b!xxxx..."
DESTINATION_SHAREPOINT_SITE_ID="xxxx..."
DESTINATION_SHAREPOINT_DRIVE_ID="b!xxxx..."
DESTINATION_SHAREPOINT_HOST_NAME="yourdomain.sharepoint.com"
DESTINATION_SHAREPOINT_SITE_PATH="sites/your-site"
DESTINATION_SHAREPOINT_DOCLIB="ドキュメント"
```

---

### 5. 注意事項
- シークレットやIDは漏洩厳禁。`.env`は必ずgit管理対象外に
- 権限不足やID間違いの場合、APIエラーとなるので注意
- 詳細はMicrosoft公式ドキュメントも参照

---

