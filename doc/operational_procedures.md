# 運用手順書

## 概要

Bulk-Migration プロジェクトの運用担当者向けの監視・アラート対応手順書です。品質向上機能の導入により、システムの健全性を継続的に監視し、問題発生時に迅速に対応するための手順を定義します。

## 日常運用手順

### 1. 日次チェック項目

#### 1.1 システム稼働状況確認

```bash
# アプリケーションの稼働確認
ps aux | grep python | grep -E "(main|watchdog)"

# ログファイルの確認
tail -f logs/transfer_start_success_error.log
tail -f logs/watchdog.log
```

#### 1.2 品質メトリクス確認

```bash
# 品質メトリクス収集
uv run python src/quality_metrics.py

# 品質アラートチェック
uv run python src/quality_alerts.py --check
```

**確認項目:**

- [ ] テストカバレッジが50%以上
- [ ] リンティングエラーが0件
- [ ] セキュリティ脆弱性が0件
- [ ] テスト失敗が0件

#### 1.3 転送状況確認

```bash
# 転送統計の確認
uv run python utils/collect_stats.py

# スキップリストの状況確認
ls -la logs/skip_list.json
wc -l logs/skip_list.json
```

### 2. 週次チェック項目

#### 2.1 セキュリティスキャン

```bash
# セキュリティスキャン実行
uv run python scripts/security_scan.py

# 結果確認
cat security_reports/bandit_report.json
cat security_reports/sbom.json
```

#### 2.2 依存関係更新確認

```bash
# 依存関係の脆弱性チェック
uv sync --upgrade

# テスト実行で動作確認
uv run pytest
```

### 3. 月次チェック項目

#### 3.1 月次レポート生成

```bash
# 月次品質レポート生成
uv run python src/quality_alerts.py --monthly

# レポート確認
ls -la quality_reports/reports/
```

#### 3.2 ログローテーション

```bash
# 古いログファイルのアーカイブ
mkdir -p logs/archive/$(date +%Y%m)
mv logs/*.log.* logs/archive/$(date +%Y%m)/ 2>/dev/null || true
```

## アラート対応手順

### 1. 品質アラート対応

#### 1.1 カバレッジ低下アラート

**症状:** テストカバレッジが閾値を下回る

**対応手順:**

1. **原因調査**

   ```bash
   # カバレッジレポート確認
   uv run pytest --cov=src --cov-report=html
   open htmlcov/index.html  # ブラウザでレポート確認
   ```

2. **未カバー行の特定**

   ```bash
   # 詳細なカバレッジレポート
   uv run pytest --cov=src --cov-report=term-missing
   ```

3. **対応策**
   - 新規追加コードのテスト作成
   - 既存テストの拡張
   - 不要コードの削除

#### 1.2 リンティングエラーアラート

**症状:** コード品質チェックでエラーが検出される

**対応手順:**

1. **エラー確認**

   ```bash
   uv run ruff check .
   ```

2. **自動修正の試行**

   ```bash
   uv run ruff check . --fix
   ```

3. **手動修正**
   - エラー内容に応じて手動でコード修正
   - 修正後にテスト実行で動作確認

#### 1.3 セキュリティ脆弱性アラート

**症状:** セキュリティスキャンで脆弱性が検出される

**対応手順:**

1. **緊急度判定**

   ```bash
   # セキュリティレポート確認
   cat security_reports/bandit_report.json | jq '.results[] | select(.issue_severity == "HIGH")'
   ```

2. **Critical/High レベルの場合**
   - 即座にシステム停止を検討
   - セキュリティチームに報告
   - 修正版の緊急リリース準備

3. **Medium/Low レベルの場合**
   - 次回定期メンテナンスで修正
   - 修正計画の策定

### 2. システムアラート対応

#### 2.1 転送エラー急増

**症状:** 転送エラー率が異常に高い

**対応手順:**

1. **エラーログ確認**

   ```bash
   grep "ERROR:" logs/transfer_start_success_error.log | tail -20
   ```

2. **API制限チェック**
   - Microsoft Graph API の制限状況確認
   - レート制限の調整検討

3. **ネットワーク状況確認**
   - インターネット接続の確認
   - 帯域使用状況の確認

#### 2.2 Watchdog 再起動頻発

**症状:** Watchdog が頻繁に再起動している

**対応手順:**

1. **ログ確認**

   ```bash
   tail -50 logs/watchdog.log
   ```

2. **リソース使用状況確認**

   ```bash
   top
   df -h
   free -h
   ```

3. **設定調整**
   - `config/config.json` のタイムアウト値調整
   - 並列処理数の調整

## 監視項目と閾値

### 1. 品質メトリクス

| 項目 | 正常範囲 | 警告閾値 | 危険閾値 | 対応レベル |
|------|----------|----------|----------|------------|
| テストカバレッジ | 60%以上 | 50-59% | 50%未満 | Medium/High |
| リンティングエラー | 0件 | 1-5件 | 6件以上 | Low/Medium |
| 型チェックエラー | 0件 | 1-3件 | 4件以上 | Low/Medium |
| セキュリティ脆弱性 | 0件 | 1件(Low) | 1件以上(High) | Medium/Critical |
| テスト失敗 | 0件 | 1件 | 2件以上 | Medium/High |

### 2. システムメトリクス

| 項目 | 正常範囲 | 警告閾値 | 危険閾値 | 対応レベル |
|------|----------|----------|----------|------------|
| CPU使用率 | 80%未満 | 80-90% | 90%以上 | Medium/High |
| メモリ使用率 | 80%未満 | 80-90% | 90%以上 | Medium/High |
| ディスク使用率 | 80%未満 | 80-90% | 90%以上 | Medium/High |
| 転送成功率 | 95%以上 | 90-94% | 90%未満 | Medium/High |

## エスカレーション手順

### 1. 対応レベル定義

#### Level 1: Low（情報）

- **対応時間:** 24時間以内
- **対応者:** 運用担当者
- **例:** 軽微なリンティングエラー、低レベルセキュリティ警告

#### Level 2: Medium（注意）

- **対応時間:** 4時間以内
- **対応者:** 開発チーム
- **例:** カバレッジ低下、中レベルセキュリティ脆弱性

#### Level 3: High（緊急）

- **対応時間:** 1時間以内
- **対応者:** 開発チームリーダー
- **例:** テスト失敗、転送成功率低下

#### Level 4: Critical（重大）

- **対応時間:** 30分以内
- **対応者:** プロジェクトマネージャー
- **例:** 高レベルセキュリティ脆弱性、システム停止

### 2. 連絡先

```
Level 1-2: 運用チーム Slack #bulk-migration-ops
Level 3: 開発チーム Slack #bulk-migration-dev
Level 4: 緊急連絡先（電話・SMS）
```

## 定期メンテナンス

### 1. 月次メンテナンス

#### 第1営業日

- [ ] 月次品質レポート生成・確認
- [ ] セキュリティスキャン実行
- [ ] 依存関係更新確認

#### 第2営業日

- [ ] ログファイルのアーカイブ
- [ ] ディスク容量の確認・クリーンアップ
- [ ] バックアップの確認

### 2. 四半期メンテナンス

#### 品質レビュー

- [ ] 四半期品質レポート生成
- [ ] 品質閾値の見直し
- [ ] テスト戦略の見直し

#### セキュリティ監査

- [ ] 包括的セキュリティスキャン
- [ ] 依存関係の全面更新
- [ ] アクセス権限の見直し

### 3. 半年メンテナンス

#### システム全体見直し

- [ ] 半年品質レポート生成
- [ ] 運用手順書の更新
- [ ] 監視項目・閾値の見直し

## トラブルシューティング

### 1. よくある問題と解決方法

#### 問題: 品質メトリクス収集が失敗する

**解決方法:**

```bash
# 権限確認
ls -la quality_reports/
chmod 755 quality_reports/

# 依存関係確認
uv sync
```

#### 問題: アラート通知が届かない

**解決方法:**

```bash
# メール設定確認
cat .env | grep EMAIL

# SMTP接続テスト
python -c "import smtplib; print('SMTP available')"
```

#### 問題: セキュリティスキャンが異常終了する

**解決方法:**

```bash
# bandit の再インストール
uv add bandit

# 手動実行でエラー確認
uv run bandit -r src/ -f json
```

### 2. ログファイル一覧

| ファイル | 内容 | 確認頻度 |
|----------|------|----------|
| `logs/transfer_start_success_error.log` | 転送処理ログ | 日次 |
| `logs/watchdog.log` | 監視プロセスログ | 日次 |
| `quality_reports/quality_metrics_*.json` | 品質メトリクス | 週次 |
| `quality_reports/alerts/quality_alerts_*.json` | 品質アラート | 日次 |
| `security_reports/bandit_report.json` | セキュリティスキャン結果 | 週次 |

## 緊急時対応

### 1. システム停止手順

```bash
# Watchdog プロセス停止
pkill -f watchdog.py

# メインプロセス停止
pkill -f "python.*main.py"

# プロセス確認
ps aux | grep python
```

### 2. 緊急復旧手順

```bash
# 最新の安定版に戻す
git checkout main
git pull origin main

# 依存関係再インストール
uv sync

# 動作確認
uv run pytest --tb=short

# サービス再開
uv run python src/watchdog.py &
```

### 3. データバックアップ

```bash
# 重要ファイルのバックアップ
cp logs/skip_list.json logs/skip_list.json.backup.$(date +%Y%m%d_%H%M%S)
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
cp config/config.json config/config.json.backup.$(date +%Y%m%d_%H%M%S)
```

## まとめ

この運用手順書に従って日常的な監視と定期メンテナンスを実施することで、Bulk-Migration システムの安定稼働と品質維持を実現できます。問題発生時は適切なエスカレーション手順に従って迅速に対応してください。
