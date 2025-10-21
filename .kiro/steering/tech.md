# 技術スタック

## 必須スタック
- **Python**: 3.11+ （pyproject.toml: `requires-python = ">=3.11"`）
- **パッケージマネージャー**: `uv`（必須）
- **ビルドバックエンド**: Hatchling（pyproject.toml で指定）
- **リント・フォーマット**: `ruff`
- **型チェック**: `mypy`
- **ロックファイル**: `uv.lock` （CIでも自動生成、git除外）
- **仮想環境**: `.venv` （`uv venv` で作成）

## CLI スタック（該当する場合）
本プロジェクトは現在 CLI フレームワークを使用していませんが、将来的に以下を採用可能：
- **Typer**: CLIフレームワーク
- **Rich**: 出力・進捗表示
- **pydantic-settings**: 設定管理

## 主要依存関係
- **msal**: Graph API 認証用 Microsoft Authentication Library
- **requests**: API 呼び出し用 HTTP クライアント
- **python-dotenv**: .env ファイルからの環境変数管理
- **pytest**: テストフレームワーク
- **pytest-cov**: カバレッジプラグイン
- **pytest-mock**: モック用ユーティリティ
- **pytest-xdist**: 並列テスト実行
- **bandit**: セキュリティ静的解析
- **pip-audit**: 依存関係脆弱性スキャン
- **cyclonedx-bom**: SBOM 生成

## 設定管理
- **環境変数**: `.env` ファイル（コミット対象外、`sample.env` をテンプレートとして使用）
- **アプリケーション設定**: `config/config.json` でランタイム設定
- **優先順位**: 環境変数 → config.json → デフォルト値

## 共通コマンド

### セットアップ
```bash
# uv のインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成
uv venv --python 3.13

# 依存関係のインストール
uv sync

# 環境変数テンプレートのコピー
cp sample.env .env
# .env を編集して Microsoft Graph API 認証情報を設定
```

### 開発
```bash
# テストの実行
uv run python run_tests.py
# または
uv run pytest

# メインアプリケーションの実行
uv run python src/main.py

# watchdog 付き実行（本番モード）
uv run python src/watchdog.py

# リセットとキャッシュ再構築
uv run python src/main.py --reset

# 転送付きフル再構築
uv run python src/main.py --full-rebuild
```

### 品質チェック
```bash
# リント・フォーマットチェック
uv run ruff check .
uv run ruff format --check .

# 型チェック
uv run mypy src/

# カバレッジ付き全テスト実行
uv run pytest --cov=src --cov-report=term-missing

# 特定のテストカテゴリ実行
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m auth

# セキュリティスキャン
uv run python scripts/security_scan.py
```

## アーキテクチャパターン
- **設定管理**: 環境変数オーバーライド付き集約設定
- **エラーハンドリング**: ネットワーク操作の指数バックオフリトライ
- **ログ**: 転送追跡付き構造化ログ
- **キャッシュ**: OneDrive/SharePoint クロール結果のファイルベースキャッシュ
- **並行処理**: 並列ファイル転送用 ThreadPoolExecutor
- **状態管理**: 完了転送追跡用スキップリスト