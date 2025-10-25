# セキュリティ運用手順書

## 実行前チェックリスト

### 1. 環境セキュリティ検証
```bash
# セキュリティチェック実行
uv run python scripts/security_check.py

# 問題がある場合は修正後に再実行
```

### 2. 認証情報の確認
- [ ] `.env` ファイルの権限が 600 に設定されている
- [ ] `CLIENT_SECRET` が32文字以上の強力な値である
- [ ] 不要な認証情報が削除されている
- [ ] 本番環境では環境変数を使用している

### 3. ファイル権限の設定
```bash
# Windows (PowerShell)
icacls .env /inheritance:r /grant:r "%USERNAME%:F"

# Linux/macOS
chmod 600 .env
chmod 600 *.key
chmod 644 config/config.json
```

## 実行時セキュリティ

### 1. セキュアログの有効化
```python
from src.security_integration import security_integration

# セキュアロガーの設定
logger = security_integration.setup_secure_logging()

# 転送操作の監査
security_integration.audit_transfer_operation("upload", file_path, success)
```

### 2. 機密情報のマスキング
- ログ出力時に自動的に機密情報がマスキングされる
- UUIDやBase64エンコードされた値も自動検出・マスキング
- メールアドレスなどのPII情報も保護

### 3. API呼び出しの監査
- すべてのGraph API呼び出しが監査ログに記録される
- 失敗した認証試行が追跡される
- 異常なアクセスパターンが検出される

## 事後確認

### 1. セキュリティ監査ログの確認
```bash
# 監査ログの確認
tail -f logs/security_audit.log

# 異常なアクセスの検索
grep "FAILURE\|CRITICAL\|WARNING" logs/security_audit.log
```

### 2. 整合性チェック
```bash
# 重要ファイルの整合性確認
uv run python -c "
from src.security_audit import SecurityAuditor
auditor = SecurityAuditor()
result = auditor.check_file_integrity(['.env', 'config/config.json'])
print(result)
"
```

### 3. 機密情報露出スキャン
```bash
# 定期的な機密情報スキャン
uv run python -c "
from src.security_audit import SecurityAuditor
auditor = SecurityAuditor()
result = auditor.scan_for_secrets_exposure()
if result['status'] != 'CLEAN':
    print('WARNING: 機密情報の露出が検出されました')
    print(result)
"
```

## インシデント対応

### 1. 機密情報漏洩の疑い
1. 即座に該当する認証情報を無効化
2. Azure AD でアプリケーションのシークレットをローテーション
3. 監査ログで影響範囲を特定
4. 必要に応じてアクセス権限を一時停止

### 2. 不正アクセスの検出
1. `logs/security_audit.log` で詳細を確認
2. 該当するセッション・IPアドレスを特定
3. 必要に応じて条件付きアクセスポリシーを適用
4. パスワード・シークレットの強制リセット

### 3. ファイル改ざんの検出
1. 整合性チェックで変更されたファイルを特定
2. バックアップから復元するか、変更内容を検証
3. 改ざんの原因を調査（マルウェア、内部脅威等）
4. 必要に応じてシステム全体のスキャンを実行

## 定期メンテナンス

### 週次
- [ ] セキュリティ監査ログの確認
- [ ] 機密情報露出スキャンの実行
- [ ] ファイル権限の確認

### 月次
- [ ] 認証情報のローテーション検討
- [ ] セキュリティポリシーの見直し
- [ ] 脆弱性スキャンの実行

### 四半期
- [ ] セキュリティ設定の全面見直し
- [ ] インシデント対応手順の訓練
- [ ] アクセス権限の棚卸し

## 緊急連絡先

- セキュリティ担当者: [連絡先]
- システム管理者: [連絡先]
- Microsoft サポート: [契約に応じて]

## 参考資料

- [Microsoft Graph セキュリティベストプラクティス](https://docs.microsoft.com/graph/security-best-practices)
- [Azure AD アプリケーションセキュリティ](https://docs.microsoft.com/azure/active-directory/develop/security-best-practices)
- [OWASP セキュアコーディング](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)