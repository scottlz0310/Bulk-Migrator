# プロジェクト構造

## ルートレベル
- `main.py` - エントリーポイントラッパー（src/main.py に委譲）
- `pyproject.toml` - プロジェクトメタデータと依存関係
- `uv.lock` - ロックされた依存関係バージョン（コミット必須）
- `pytest.ini` - カバレッジ設定付きテスト設定
- `run_tests.py` - テスト実行スクリプト
- `sample.env` - 環境変数テンプレート（`.env` にコピーして使用）
- `.env` - 実際の環境変数（コミット対象外）

## ソースコード (`src/`)
主要アプリケーションモジュール:
- `main.py` - メインアプリケーションロジックと CLI インターフェース
- `transfer.py` - Microsoft Graph API 経由のファイル転送操作
- `auth.py` - Microsoft Graph API 認証
- `config_manager.py` - 優先度システム付き設定管理
- `logger.py` - 転送操作用構造化ログ
- `skiplist.py` - 完了転送用スキップリスト管理
- `rebuild_skip_list.py` - SharePoint クロールからのスキップリスト再構築
- `watchdog.py` - プロセス監視と自動再起動機能
- `filelock.py` - ファイルロックユーティリティ

### ユーティリティ (`src/utils/`)
- `find_and_delete_renamed_folders.py` - クリーンアップユーティリティ

## 設定 (`config/`)
- `config.json` - ランタイム設定（チャンクサイズ、タイムアウト、パスなど）

## テスト (`tests/`)
- `conftest.py` - Pytest 設定とフィクスチャ
- `test_*.py` - 各モジュールの単体テスト
- テストマーカー: `unit`, `integration`, `auth`, `transfer`, `config`

## ユーティリティ (`utils/`)
独立ユーティリティスクリプト:
- `collect_stats.py` - 転送統計収集
- `collect_onedrive_skiplist_stats.py` - OneDrive スキップリスト分析
- `predict_completion.py` - 転送完了予測
- `verify_*.py` - 各種検証ユーティリティ

## ドキュメント (`doc/`)
- `implementation-rules.md` - 開発ガイドラインと AI 実装ルール
- `PROJECT_STRUCTURE_STATUS.md` - 現在のプロジェクト状況
- `old/` - アーカイブされたドキュメントとレポート

## ログ (`logs/`)
ランタイム生成ファイル（コミット対象外）:
- `transfer_start_success_error.log` - 転送操作ログ
- `onedrive_files.json` - キャッシュされた OneDrive ファイル一覧
- `sharepoint_current_files.json` - キャッシュされた SharePoint ファイル一覧
- `skip_list.json` - 転送済みファイル（スキップリスト）
- `config_hash.txt` - 設定変更検出

## 命名規則
- **モジュール**: スネークケース（例: `config_manager.py`）
- **クラス**: パスカルケース（例: `GraphTransferClient`）
- **関数**: スネークケース（例: `get_onedrive_files`）
- **定数**: 大文字スネークケース（例: `CLIENT_ID`）
- **ログファイル**: `.log` または `.json` 拡張子付きの説明的な名前

## インポートパターン
- `src` パッケージからの絶対インポートを使用
- 設定モジュールではモジュールレベルでの環境読み込み
- try/except ブロックによるオプショナルインポートの優雅なフォールバック

## ファイル組織原則
- `src/` にコアビジネスロジック
- `config/` に設定を集約
- 目的別ユーティリティ分離（テスト vs 運用ユーティリティ）
- `logs/` に生成ファイルを分離
- 対象者と目的別に構造化されたドキュメント