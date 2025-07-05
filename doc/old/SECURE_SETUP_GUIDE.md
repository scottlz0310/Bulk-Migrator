# 🔐 セキュアな環境変数設定ガイド
作成日: 2025-06-30 23:26:54

## 🎯 設定方法

### Windows PowerShell (管理者権限で実行)
```powershell
# 以下のコマンドを実行してください
[Environment]::SetEnvironmentVariable("CLIENT_ID", "YOUR_CLIENT_ID_HERE", "Machine")
[Environment]::SetEnvironmentVariable("TENANT_ID", "YOUR_TENANT_ID_HERE", "Machine") 
[Environment]::SetEnvironmentVariable("CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE", "Machine")
```

### Windows コマンドプロンプト (管理者権限で実行)
```cmd
setx CLIENT_ID "YOUR_CLIENT_ID_HERE" /M
setx TENANT_ID "YOUR_TENANT_ID_HERE" /M
setx CLIENT_SECRET "YOUR_CLIENT_SECRET_HERE" /M
```

## 📋 設定する値

### CLIENT_ID
```
test-client-id
```

### TENANT_ID  
```
test-tenant-id
```

### CLIENT_SECRET
```
⚠️  このファイルには保存されていません
Azure Portal の「証明書とシークレット」から値をコピーしてください
```

## ✅ 設定確認

設定後、新しいコマンドプロンプト/PowerShellで以下のコマンドで確認：

```cmd
echo %CLIENT_ID%
echo %TENANT_ID%
echo %CLIENT_SECRET%
```

## 🛡️ セキュリティノート

- このファイルには CLIENT_SECRET は保存されていません
- Azure Portal から直接コピー・ペーストしてください  
- 設定完了後、このファイルは削除しても構いません
- バージョン管理には絶対に含めないでください

---
**作成者**: OneDrive→SharePoint移行ツール セキュアセットアップ
