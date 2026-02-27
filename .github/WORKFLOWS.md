# CI/CD パイプライン設定

このディレクトリには、Bulk-Migration プロジェクトの CI/CD パイプライン設定が含まれています。

## ワークフロー概要

### 1. 品質チェック (`quality-check.yml`)
- **トリガー**: push (main, develop), pull_request, 定期実行 (毎日午前2時)
- **対象**: マルチプラットフォーム (Ubuntu, Windows, macOS) × Python (3.11, 3.12, 3.13)
- **実行内容**:
  - リンティング (ruff check)
  - フォーマットチェック (ruff format --check)
  - 型チェック (mypy)
  - テスト実行とカバレッジ測定 (pytest, 60%閾値)
  - カバレッジレポートのアップロード

### 2. プルリクエスト品質ゲート (`pr-quality-gate.yml`)
- **トリガー**: pull_request (opened, synchronize, reopened)
- **実行内容**:
  - 品質チェックの実行
  - 結果のPRコメント自動投稿
  - 品質基準未達時のマージブロック

### 3. セキュリティスキャン (`security-scan.yml`)
- **トリガー**: push (main, develop), pull_request (main, develop), 手動実行 (`workflow_dispatch`)
- **実行内容**:
  - CodeQL セキュリティ分析
  - 依存関係脆弱性スキャン (pip-audit)
  - Python セキュリティスキャン (bandit)
  - 秘密情報スキャン (TruffleHog)
  - SBOM (Software Bill of Materials) 生成

### 4. リリース準備 (`prepare-release.yml`)
- **トリガー**: 手動実行のみ
- **実行内容**:
  - 品質チェックの実行
  - セマンティックバージョニング
  - pyproject.toml のバージョン更新
  - CHANGELOG.md の自動更新
  - リリースタグの作成とプッシュ

### 5. リリース自動化 (`release.yml`)
- **トリガー**: タグプッシュ (`v*`), 手動実行
- **実行内容**:
  - GitHub Release の自動作成
  - リリースノートの自動生成

## 品質ゲート基準

### 必須条件 (全て通過が必要)
- ✅ ruff check でエラー 0
- ✅ ruff format でフォーマット準拠
- ✅ mypy で型エラー 0
- ✅ pytest でテストカバレッジ 60% 以上
- ✅ セキュリティスキャンで高レベル脆弱性 0

### セキュリティ基準
- CodeQL による静的解析通過
- 依存関係に既知の脆弱性なし
- Bandit による高レベルセキュリティ問題なし
- 秘密情報の漏洩なし

## 使用方法

### ローカル開発
```bash
# 開発環境セットアップ
make bootstrap

# 品質チェック実行
make quality-check

# セキュリティスキャン実行
make security

# リリース前チェック
make release-check
```

### プルリクエスト
1. プルリクエスト作成時に自動で品質チェックが実行されます
2. 品質基準を満たさない場合、マージがブロックされます
3. 修正後、再度プッシュすると自動で再チェックされます

### リリース
1. GitHub Actions の「リリース準備」ワークフローを手動実行します
2. リリースタイプ (patch/minor/major) を選択します
3. ワークフローが品質チェック、バージョン更新、タグ作成を自動実行します
4. タグプッシュにより「リリース自動化」ワークフローが自動実行され、GitHub Release が作成されます

#### リリース手順
1. GitHub の Actions タブから「リリース準備」を選択
2. 「Run workflow」をクリック
3. リリースタイプを選択して実行
4. 完了後、自動的にリリースが作成されます

## Conventional Commits 規約

- `feat:` - 新機能 (minor バージョンアップ)
- `fix:` - バグ修正 (patch バージョンアップ)
- `docs:` - ドキュメント変更
- `style:` - コードスタイル変更
- `refactor:` - リファクタリング
- `test:` - テスト追加・修正
- `chore:` - その他の変更
- `BREAKING CHANGE:` - 破壊的変更 (major バージョンアップ)

## 設定ファイル

### pyproject.toml
- pytest 設定 (JUnit XML 出力含む)
- bandit セキュリティスキャン設定

### Makefile
- 開発用コマンドの統一インターフェース
- CI/CD で使用されるコマンドと同等の機能

## トラブルシューティング

### 品質チェック失敗時
1. ローカルで `make quality-check` を実行
2. エラー内容を確認し修正
3. 修正後にコミット・プッシュ

### セキュリティスキャン失敗時
1. 脆弱性レポートを確認
2. 依存関係の更新または代替パッケージの検討
3. 必要に応じてセキュリティ例外の申請

### リリース失敗時
1. リリース前チェックをローカルで実行
2. 品質基準を満たしているか確認
3. バージョン番号の整合性を確認
