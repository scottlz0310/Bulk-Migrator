# ワークフロー設定ガイド

## リリース自動化の設定

リリース準備ワークフローからリリース自動化を自動トリガーするには、Personal Access Token (PAT) が必要です。

### PAT設定手順

1. **PATの作成**
   - GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - "Generate new token (classic)" をクリック
   - 必要な権限:
     - `repo` (Full control of private repositories)
     - `workflow` (Update GitHub Action workflows)

2. **リポジトリシークレットに追加**
   - Repository Settings → Secrets and variables → Actions
   - "New repository secret" をクリック
   - Name: `PAT_TOKEN`
   - Secret: 作成したPATを貼り付け

### 動作

- **PAT設定済み**: タグプッシュ時にリリース自動化が自動発火
- **PAT未設定**: GITHUB_TOKENを使用（リリース自動化は手動実行が必要）

### なぜPATが必要か

GitHub Actionsの仕様により、`GITHUB_TOKEN`を使ったワークフロー内からのプッシュは、
他のワークフローをトリガーしません（無限ループ防止のため）。

PATを使用することで、この制限を回避できます。
