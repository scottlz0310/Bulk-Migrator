## [2.3.5] - 2025-10-21



---


## [2.3.6] - 2025-10-21

### 変更内容

- fix: リリース自動化の自動トリガーにPAT対応を追加 (a43b7a9)
- docs: update documentation for v2.3.5 (e41acfe)

**完全な変更履歴**: https://github.com/scottlz0310/Bulk-Migrator/compare/v2.3.5...v2.3.5




---


## [2.3.5] - 2025-10-21

### 変更内容

- chore(deps): bump actions/setup-python from 5 to 6 (#6) (2bb4c46)
- chore(deps): bump actions/checkout from 4 to 5 (#3) (8dd547f)
- chore(deps): bump astral-sh/setup-uv from 1 to 7 (#4) (9434320)
- chore(deps): bump github/codeql-action from 3 to 4 (#5) (2256c08)
- chore(deps): bump dorny/test-reporter from 1 to 2 (#2) (a433bac)
- feat: Dependabot自動更新とオートマージを追加 (afae542)
- docs: update documentation for vmain (9636b98)

**完全な変更履歴**: https://github.com/scottlz0310/Bulk-Migrator/compare/v2.3.4...main




---


## [2.3.4] - 2025-10-21

### 変更内容

- fix: Windows PowerShell互換性のため複数行コマンドを修正 (a10b97d)
- fix: 無効なmetadata権限を削除 (5f2ff8f)
- fix: yamllintエラーを修正（長い行の分割、末尾空白削除、括弧修正） (3ce0044)
- feat: yamllintをpre-commitに追加、YAML品質チェックを強化 (ca2bdc6)
- fix: Python要件を3.11+に変更してCI互換性を確保 (6fddffc)
- fix: Windows環境でのuv venv問題を修正、uv syncに--pythonオプションを追加 (3aad3be)
- refactor: コードの可読性向上のため、コマンドリストのフォーマットを修正 (340e844)
- chore: .amazonq/をgit除外、.amazonq/rules/のみ追跡対象に設定 (53a555e)
- refactor: 不要な出力を削除し、コードをクリーンアップ (8f036eb)
- Merge branch 'main' of https://github.com/scottlz0310/Bulk-Migrator (d01b803)
- feat: Python 3.13へのアップグレードと並列テスト実行の導入 - Pythonバージョンを3.12から3.13に更新 - `pytest-xdist`を追加し、テストの並列実行を有効化 - GitHub ActionsおよびMakefileで並列実行オプションを追加 - READMEとアップグレードノートを更新 (e4e7ff4)
- feat: .gitignoreにテンプレートからの自動生成エントリを追加 (cb085a9)
- Merge branch 'main' of github.com:scottlz0310/Bulk-Migrator (9b0b997)
- Add VSCode related entries to .gitignore (b9b03b6)
- fix: リリース準備ワークフローのタグプッシュ問題を修正 (a7782b8)


## [2.3.3] - 2025-09-21

### 変更内容

- feat: CodeQLを手動実行のみに変更してパフォーマンス最適化 (380b2e0)
- feat: pre-commitでfail_fast設定を追加 (dd2cfce)
- fix: CodeQL Docker権限問題を修正し並行処理を最適化 (10a7d73)
- feat: CodeQLスキャニングスクリプトにWSLサポートを追加し、エラー処理を強化 (f4b4e81)
- feat: add CodeQL pre-commit hook with Docker support (942360a)


## [2.3.2] - 2025-09-21

### 変更内容

- chore: update changelog for v2.3.1 (b3f532b)
- fix: update prepare-release workflow to use Python 3.13 (804dadc)
- docs: update documentation for v2.3.1 (c40b1ad)

**完全な変更履歴**: https://github.com/scottlz0310/Bulk-Migrator/compare/v2.3.1...v2.3.1




---

**完全な変更履歴**: https://github.com/scottlz0310/Bulk-Migrator/compare/v2.3.0...v2.3.0


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0]

### Added
- CI/CD パイプラインの構築
- GitHub Actions による品質チェック自動化
- セキュリティスキャンの統合
- リリース自動化とバージョン管理

### Changed
- pytest 設定に JUnit XML 出力を追加
- pyproject.toml にセキュリティツールの依存関係を追加

### Security
- CodeQL セキュリティスキャンの導入
- Bandit による Python セキュリティ脆弱性検出
- pip-audit による依存関係脆弱性チェック
- TruffleHog による秘密情報スキャン
- SBOM (Software Bill of Materials) 生成

## [0.1.0] - 2025-01-20

### Added
- 初期リリース
- OneDrive から SharePoint への大容量ファイル転送機能
- Microsoft Graph API 統合
- 構造化ログシステム
- テストスイートとカバレッジ測定
- コード品質管理 (ruff, mypy)
