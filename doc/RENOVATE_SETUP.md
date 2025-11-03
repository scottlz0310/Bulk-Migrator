# Renovate セルフホストセットアップガイド

このガイドでは、Dockerを使用したRenovateのセルフホスト環境のセットアップ手順を説明します。

## 概要

- **Renovate**: 依存関係の自動更新ツール
- **セルフホスト方式**: Docker Composeを使用してローカルまたは自社サーバーで実行
- **対象リポジトリ**: プライベートリポジトリ（無料で利用可能）

## 前提条件

- Docker および Docker Compose がインストールされている
- GitHubアカウントとプライベートリポジトリへのアクセス権
- GitHub Personal Access Token（PAT）の作成権限

## セットアップ手順

### 1. GitHub Personal Access Token の作成

プライベートリポジトリにアクセスするため、適切な権限を持つトークンを作成します。

1. GitHubにログイン
2. **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
3. **Generate new token (classic)** をクリック
4. 以下の権限（スコープ）を選択:
   - ✅ `repo` (フルコントロール)
   - ✅ `workflow` (ワークフロー更新用)
   - ✅ `read:org` (組織情報の読み取り、オプション)
5. トークンを生成し、**必ず安全に保存**してください

### 2. 環境設定ファイルの作成

```bash
# サンプルファイルをコピー
cp .env.renovate.example .env.renovate

# エディタで編集
nano .env.renovate
```

最低限、以下の設定が必要です:

```bash
GITHUB_TOKEN=ghp_your_actual_token_here
GITHUB_REPOSITORY=scottlz0310/Bulk-Migrator
GIT_AUTHOR_NAME=Renovate Bot
GIT_AUTHOR_EMAIL=renovate@example.com
```

### 3. 初回実行（ドライラン）

実際の変更を行う前に、ドライランモードでテストします。

```bash
# ドライランで実行（変更は適用されません）
docker-compose -f docker-compose.renovate.yml --env-file .env.renovate up
```

**確認事項:**
- エラーが発生していないか
- リポジトリへの接続が成功しているか
- 検出された依存関係が正しいか

### 4. 本番実行

ドライランで問題がなければ、`.env.renovate`ファイルを編集:

```bash
DRY_RUN=false
```

そして実行:

```bash
docker-compose -f docker-compose.renovate.yml --env-file .env.renovate up
```

### 5. 定期実行の設定（推奨）

#### Option A: Cron（Linux/macOS）

```bash
# crontabを編集
crontab -e

# 毎日午前2時に実行
0 2 * * * cd /path/to/Bulk-Migrator && docker-compose -f docker-compose.renovate.yml --env-file .env.renovate up --abort-on-container-exit >> /var/log/renovate.log 2>&1
```

#### Option B: systemd タイマー（Linux）

`/etc/systemd/system/renovate.service` を作成:

```ini
[Unit]
Description=Renovate Dependency Updates
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/path/to/Bulk-Migrator
ExecStart=/usr/bin/docker-compose -f docker-compose.renovate.yml --env-file .env.renovate up --abort-on-container-exit
User=your-username
StandardOutput=journal
StandardError=journal
```

`/etc/systemd/system/renovate.timer` を作成:

```ini
[Unit]
Description=Run Renovate daily

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

有効化:

```bash
sudo systemctl daemon-reload
sudo systemctl enable renovate.timer
sudo systemctl start renovate.timer
```

#### Option C: GitHub Actions（代替案）

自社サーバーがない場合、GitHub Actionsでも実行可能です。

`.github/workflows/renovate.yml`:

```yaml
name: Renovate

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  renovate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Renovate
        uses: renovatebot/github-action@v40
        with:
          configurationFile: renovate.json
          token: ${{ secrets.RENOVATE_TOKEN }}
```

## Renovate 設定のカスタマイズ

`renovate.json` ファイルで動作をカスタマイズできます。

### 主要な設定項目

#### スケジュール設定

```json
{
  "schedule": [
    "after 10pm every weekday",
    "before 5am every weekday",
    "every weekend"
  ]
}
```

#### 自動マージ設定

```json
{
  "packageRules": [
    {
      "matchUpdateTypes": ["patch", "minor"],
      "automerge": true
    }
  ]
}
```

#### グループ化

```json
{
  "packageRules": [
    {
      "matchPackageNames": ["pytest", "pytest-cov", "mypy"],
      "groupName": "test dependencies"
    }
  ]
}
```

## トラブルシューティング

### 問題: トークン認証エラー

**原因**: トークンが無効または権限不足

**解決策**:
1. トークンの有効期限を確認
2. 必要な権限（`repo`, `workflow`）が付与されているか確認
3. 新しいトークンを生成して再試行

### 問題: リポジトリが見つからない

**原因**: リポジトリ名が正しくない

**解決策**:
```bash
GITHUB_REPOSITORY=owner/repo-name
```
形式が正しいか確認

### 問題: Dockerイメージのダウンロード失敗

**原因**: ネットワーク問題またはDocker Hubの制限

**解決策**:
```bash
# イメージを手動でプル
docker pull renovate/renovate:latest

# 再実行
docker-compose -f docker-compose.renovate.yml --env-file .env.renovate up
```

### 問題: 依存関係が検出されない

**原因**: Pythonの設定ファイルが認識されていない

**解決策**:
`renovate.json`に以下を追加:

```json
{
  "pip_requirements": {
    "fileMatch": ["(^|/)requirements\\.txt$", "(^|/)pyproject\\.toml$"]
  }
}
```

## セキュリティ考慮事項

### トークン管理

- ✅ `.env.renovate`ファイルは`.gitignore`に追加
- ✅ トークンは定期的にローテーション
- ✅ 最小権限の原則に従う

### Docker セキュリティ

- ✅ 公式イメージを使用（`renovate/renovate:latest`）
- ✅ リソース制限を設定（メモリ、CPU）
- ✅ 不要なコマンド実行を無効化

```yaml
environment:
  - RENOVATE_ALLOWED_POST_UPGRADE_COMMANDS=[]
```

## モニタリング

### ログの確認

```bash
# リアルタイムログ
docker-compose -f docker-compose.renovate.yml --env-file .env.renovate logs -f

# ログファイル（設定済みの場合）
tail -f logs/renovate/*.log
```

### 実行履歴の確認

GitHub リポジトリの Pull Requests タブで、Renovate が作成した PR を確認できます。

## メンテナンス

### イメージの更新

```bash
# 最新イメージを取得
docker pull renovate/renovate:latest

# 古いイメージを削除
docker image prune -f
```

### キャッシュのクリア

```bash
# キャッシュボリュームを削除
docker volume rm bulk-migrator_renovate-cache

# 次回実行時に再構築されます
```

## 参考リソース

- [Renovate 公式ドキュメント](https://docs.renovatebot.com/)
- [セルフホストガイド](https://docs.renovatebot.com/self-hosting/)
- [設定オプション](https://docs.renovatebot.com/configuration-options/)
- [Docker Hub - Renovate](https://hub.docker.com/r/renovate/renovate)

## サポート

問題が発生した場合:
1. このドキュメントのトラブルシューティングセクションを確認
2. Renovateのログを詳細モード（`LOG_LEVEL=debug`）で確認
3. [Renovate Discussions](https://github.com/renovatebot/renovate/discussions)でコミュニティに質問

## 次のステップ

Renovateのセットアップが完了したら:

1. ✅ Dependabot設定の削除（必要に応じて）
2. ✅ 定期実行の設定
3. ✅ チームメンバーへの通知設定
4. ✅ 自動マージルールの調整
