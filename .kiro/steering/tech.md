# 技術スタック

## ビルドシステム・パッケージ管理
- **パッケージマネージャー**: `uv`（必須） - モダンな Python パッケージマネージャー
- **Python バージョン**: 3.13+ （pyproject.toml で指定）
- **ロックファイル**: `uv.lock` （コミット必須）
- **仮想環境**: `.venv` （`uv venv` で作成）

## 主要依存関係
- **msal**: Graph API 認証用 Microsoft Authentication Library
- **requests**: API 呼び出し用 HTTP クライアント
- **python-dotenv**: .env ファイルからの環境変数管理
- **pytest**: カバレッジレポート付きテストフレームワーク
- **pytest-cov**: カバレッジプラグイン
- **pytest-mock**: モック用ユーティリティ

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

### テスト
```bash
# カバレッジ付き全テスト実行
uv run pytest

# 特定のテストカテゴリ実行
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m auth
```

## アーキテクチャパターン
- **設定管理**: 環境変数オーバーライド付き集約設定
- **エラーハンドリング**: ネットワーク操作の指数バックオフリトライ
- **ログ**: 転送追跡付き構造化ログ
- **キャッシュ**: OneDrive/SharePoint クロール結果のファイルベースキャッシュ
- **並行処理**: 並列ファイル転送用 ThreadPoolExecutor
- **状態管理**: 完了転送追跡用スキップリスト