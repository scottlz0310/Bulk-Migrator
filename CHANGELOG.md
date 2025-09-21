## [2.3.1] - 2025-09-21



---

**完全な変更履歴**: https://github.com/scottlz0310/Bulk-Migrator/compare/v2.3.1...v2.3.1




---

**完全な変更履歴**: https://github.com/scottlz0310/Bulk-Migrator/compare/v2.3.0...v2.3.0


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
