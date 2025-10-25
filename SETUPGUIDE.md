# SETUPGUIDE.md

## Microsoft Graph API 利用のためのセットアップ手順

**所要時間：15-30分**（初回の場合）

このガイドに従えば、技術者でなくても設定できます。
分からない箇所があれば、scott.lz0310@gmail.com までお気軽にお問い合わせください。

---

> ℹ️ 2023年以降、Azure Active Directory は **Microsoft Entra ID** に名称変更されています。
> ポータル内の一部メニューでは旧名称が表示される場合がありますが、本ガイドでは最新の名称を使用します。

## 📋 セットアップの全体像

1. ✅ Azureポータルでアプリ登録（10分）
2. ✅ API権限の付与（5分）
3. ✅ Graph ExplorerでID情報を取得（10分）
4. ✅ .envファイルに記入（5分）

---

## 1. Azureポータルでアプリ登録

### 手順

1. [Azure Portal](https://portal.azure.com/) に**管理者アカウント**でログイン
   - ⚠️ 注意：一般ユーザーではなく、Microsoft Entra ID の管理者権限が必要です

2. 左メニューから「**Microsoft Entra ID**」（旧 Azure Active Directory）を選択
   - 見つからない場合：画面上部の検索ボックスで「Entra ID」または「Azure Active Directory」と検索

3. 「**アプリの登録**」→「**新規登録**」をクリック

4. 以下を入力：
   - **名前**：`BulkMigrator-YourCompany`（分かりやすい名前）
   - **サポートされているアカウントの種類**：「この組織ディレクトリのみ」を選択
   - **リダイレクトURI**：空欄のままでOK

5. 「**登録**」をクリック

6. 登録後、以下の情報をコピー：
```
   アプリケーション(クライアント)ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ディレクトリ(テナント)ID:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```
   
7. 左メニューから「**証明書とシークレット**」を選択

8. 「**新しいクライアント シークレット**」をクリック
   - **説明**：`BulkMigrator Secret`
   - **有効期限**：24ヶ月（推奨）
   - 「**追加**」をクリック

9. **重要：** 生成された「値」を今すぐコピー
```
   シークレット値: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
   - ⚠️ このページを離れると二度と表示されません
   - コピーし忘れた場合は、新しいシークレットを作成してください

### 取得した値を.envに記入
```ini
CLIENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
CLIENT_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TENANT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

---

## 2. API権限の付与

### 手順

1. アプリ登録画面の左メニューから「**APIのアクセス許可**」を選択

2. 「**アクセス許可の追加**」をクリック

3. 「**Microsoft Graph**」を選択

4. 「**アプリケーションのアクセス許可**」を選択
   - ⚠️ 注意：「委任されたアクセス許可」ではなく「アプリケーションのアクセス許可」

5. 以下の権限を検索して追加：
```
   ✓ Files.Read.All
   ✓ Files.ReadWrite.All
   ✓ Sites.Read.All
   ✓ Sites.ReadWrite.All
   ✓ User.Read.All
```

6. **最重要：** 「**（組織名）に管理者の同意を与えます**」をクリック
   - ⚠️ これを忘れると権限が有効になりません
   - 確認ダイアログで「はい」をクリック
   - 「状態」列がすべて緑のチェックマークになることを確認

### なぜこれらの権限が必要？
```
Files.Read.All / Files.ReadWrite.All
→ OneDriveとSharePointのファイルを読み書きするため

Sites.Read.All / Sites.ReadWrite.All
→ SharePointサイトにアクセスするため

User.Read.All
→ ユーザー情報とOneDrive情報を取得するため
```

---

## 3. Graph ExplorerでID情報を取得

[Microsoft Graph Explorer](https://developer.microsoft.com/ja-jp/graph/graph-explorer) を使って、
必要なIDを取得します。

### 3.1 OneDriveのDrive ID取得

1. Graph Explorerにアクセスし、「**サインイン**」
   - 先ほど権限を付与したアカウントでサインインします。
2. 画面左上で HTTP メソッドに **GET**、バージョンドロップダウンに **v1.0** を選択します。
3. アドレス欄に次の URL を入力し、`{userPrincipalName}` を実際のメールアドレスに置き換えます。

   ```http
   https://graph.microsoft.com/v1.0/users/{userPrincipalName}/drive
   ```

   例：`https://graph.microsoft.com/v1.0/users/tanaka@yourcompany.onmicrosoft.com/drive`

4. 「**Run query**」（▷）をクリックします。
5. レスポンスから `id` をコピーします。

   ```json
   {
     "id": "b!xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
     ...
   }
   ```

6. 以下を `.env` に記入します。

   ```ini
   SOURCE_ONEDRIVE_DRIVE_ID="b!xxxxxxxxxx..."
   SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME="tanaka@yourcompany.onmicrosoft.com"
   ```

### 3.2 SharePointのSite ID取得

1. Graph Explorerでサインイン済みであることを確認し、HTTP メソッドを **GET**、バージョンを **v1.0** に設定します。
2. アドレス欄に次の URL を入力し、`{domain}` と `{site-path}` を自社環境に合わせて置き換えます。

   ```http
   https://graph.microsoft.com/v1.0/sites/{domain}.sharepoint.com:/sites/{site-path}
   ```

   例：`https://graph.microsoft.com/v1.0/sites/yourcompany.sharepoint.com:/sites/ProjectA`

3. 「**Run query**」（▷）をクリックします。
4. レスポンスから `id` をコピーし、以下を `.env` に記入します。

   ```ini
   DESTINATION_SHAREPOINT_SITE_ID="xxxxxxxxxx..."
   DESTINATION_SHAREPOINT_HOST_NAME="yourcompany.sharepoint.com"
   DESTINATION_SHAREPOINT_SITE_PATH="sites/ProjectA"
   ```

### 3.3 SharePointのDrive ID取得

1. Graph Explorerで HTTP メソッドを **GET**、バージョンを **v1.0** に設定します。
2. アドレス欄に次の URL を入力し、`{site-id}` を前のステップで取得した値に置き換えます。

   ```http
   https://graph.microsoft.com/v1.0/sites/{site-id}/drives
   ```

3. 「**Run query**」（▷）をクリックします。
4. レスポンスから目的のドキュメントライブラリの `id` をコピーし、以下を `.env` に記入します。

   ```ini
   DESTINATION_SHAREPOINT_DRIVE_ID="b!xxxxxxxxxx..."
   DESTINATION_SHAREPOINT_DOCLIB="ドキュメント"
   ```

---

## 4. .envファイルへの記入

### 完成例

```ini
# Microsoft Entra ID App（旧 Azure AD）
CLIENT_ID="12345678-1234-1234-1234-123456789abc"
CLIENT_SECRET="abcdefghijklmnopqrstuvwxyz123456"
# Source (OneDrive)
SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME="tanaka@yourcompany.onmicrosoft.com"
SOURCE_ONEDRIVE_FOLDER_PATH="Documents/移行対象フォルダ"
SOURCE_ONEDRIVE_DRIVE_ID="b!xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Destination (SharePoint)
DESTINATION_SHAREPOINT_SITE_ID="yourcompany.sharepoint.com,xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx,yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
DESTINATION_SHAREPOINT_DRIVE_ID="b!zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
DESTINATION_SHAREPOINT_HOST_NAME="yourcompany.sharepoint.com"
DESTINATION_SHAREPOINT_SITE_PATH="sites/ProjectA"
DESTINATION_SHAREPOINT_DOCLIB="ドキュメント"
DESTINATION_SHAREPOINT_FOLDER_PATH="移行先フォルダ"
```

---

## 5. 設定の確認

### テスト実行

```bash
# 設定が正しいか確認
uv run python -m utils.file_crawler_cli validate

# 問題なければ、ドライラン（実際にはコピーしない）
uv run python -m utils.file_crawler_cli migrate --dry-run
```

---

## ❓ よくある問題とトラブルシューティング

### エラー: `Insufficient privileges to complete the operation`

**原因：** API権限の管理者同意が完了していない

**解決策：**

1. Azure Portalのアプリ登録画面へ
2. 「APIのアクセス許可」を確認
3. 「管理者の同意を与える」を再度クリック
4. すべての権限の「状態」が緑のチェックマークになっているか確認

---

### エラー: `Resource not found for the segment 'drive'`

**原因：** Drive IDが間違っている、またはユーザーにOneDriveが割り当てられていない

**解決策：**

1. Graph Explorerで`GET /users/{UPN}/drive`を再実行
2. エラーが出る場合、該当ユーザーにOneDriveライセンスが割り当てられているか確認
3. UPNが正しいか確認（メールアドレスと同じとは限らない）

---

### エラー: `Invalid client secret provided`

**原因：** CLIENT_SECRETが間違っている、または期限切れ

**解決策：**

1. Azure Portalで新しいクライアントシークレットを作成
2. 生成された値を.envに貼り付け
3. **重要：** 前後に余分なスペースがないか確認

---

### Drive IDの探し方が分からない

**簡単な方法：**

1. OneDriveまたはSharePointをブラウザで開く
2. URLをコピー
3. サポート（<mailto:scott.lz0310@gmail.com>）にURLを送信
4. Drive IDを調べてお伝えします（無料）

---

## 📞 サポート

分からないことがあれば、お気軽にお問い合わせください：

- Email: <mailto:scott.lz0310@gmail.com>
- 対応時間：平日 9:00-18:00（日本時間）
- 初回セットアップサポートは無料

---

## ⚠️ セキュリティに関する注意

```text
🔒 絶対に守ること：
- .envファイルをGitにコミットしない
- CLIENT_SECRETを他人に教えない
- スクリーンショットにCLIENT_SECRETを含めない

✓ 安全な保管：
- .envは必ず.gitignoreに追加
- CLIENT_SECRETは定期的に更新（推奨：6ヶ月ごと）
```

---

## 🎯 次のステップ

セットアップが完了したら：

1. [README.md](README.md) で使い方を確認
2. 小規模なテスト移行から開始（1-5GB推奨）
3. 問題なければ本番移行へ

---
