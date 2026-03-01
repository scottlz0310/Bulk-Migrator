# Copilot Instructions

## 言語規約
**すべてのコード、コメント、ドキュメント、AIとの対話は日本語で行う。** 技術的な固有名詞（クラス名、API名等）は英語併記可。

## プロジェクト概要
OneDrive から SharePoint Online への大容量ファイル移行を自動化するバッチツール。Microsoft Graph API を使用し、4MB 超のファイルはチャンクアップロードセッションで転送する。

## ビルド・テスト・品質チェック

```bash
# セットアップ
make bootstrap          # uv venv --python 3.13 && uv sync

# 品質チェック（ローカル最小ループ）
make lint               # ruff check .
make format             # ruff format .
make typecheck          # mypy src/
make test               # pytest -n auto（カバレッジなし）
make cov                # pytest --cov=src（閾値60%）
make quality            # lint + typecheck + test

# 特定テストの実行
uv run pytest tests/unit/test_transfer.py          # 単一ファイル
uv run pytest -m unit                              # マーカー指定
uv run pytest -m "auth or transfer"                # 複数マーカー
uv run pytest tests/unit/test_config_manager.py -k "test_get" # キーワード

# アプリ実行
uv run python src/main.py                          # 通常実行
uv run python src/watchdog.py                      # watchdog付き本番実行
uv run python src/main.py --reset                  # キャッシュリセット
uv run python src/main.py --full-rebuild           # 転送付き完全再構築
```

## アーキテクチャ

```
root/main.py        → src/main.py へ委譲するエントリーポイント
src/
  main.py           → ThreadPoolExecutor で並列転送、retry_with_backoff でリトライ
  auth.py           → GraphAuthenticator（MSAL、トークン自動更新）
  transfer.py       → GraphTransferClient（4MB超はチャンクアップロードセッション）
  config_manager.py → 設定優先順位: 環境変数 > config/config.json > デフォルト値
  skiplist.py       → 転送済みファイルのスキップリスト（logs/skip_list.json）
  watchdog.py       → フリーズ検知・自動再起動
  logger.py         → 転送開始/成功/エラーのログ関数
  structured_logger.py → JSON構造化ログ（UTC ISO 8601必須）
  rebuild_skip_list.py → SharePoint クロールからスキップリスト再構築

config/config.json  → チャンクサイズ、タイムアウト等のランタイム設定
logs/               → 実行時生成ファイル（コミット禁止）
  skip_list.json, onedrive_files.json, sharepoint_current_files.json
```

## 重要な規約

### パッケージ管理
`uv` のみ使用（pip/poetry 禁止）。`uv.lock` は必ずコミット。

### インポートパターン
`src/` 内のモジュールは相互に相対的なインポートを使用する（`from src.` ではなく `from config_manager import ...`）。`src/` 外からは `from src.transfer import GraphTransferClient` のように絶対インポート。

### 設定管理
`config_manager.get(key, default, env_key)` で設定取得。機密キー（CLIENT_SECRET, TOKEN, PASSWORD 等）は `SecureConfigManager` でマスク処理される。設定のショートカット関数（`get_chunk_size_mb()` 等）が用意されているため新規追加時も同パターンに従う。

### ネットワーク操作
`retry_with_backoff(func, max_retries, wait_sec, ...)` を使用し、`ConnectionError`/`MaxRetryError` を自動リトライ。

### ログ
全ログは UTC タイムゾーン付きで記録。`structured_logger.py` の `get_structured_logger(module_name)` を使い JSON 出力。PII をログに含めない。

### テスト規約
- テストマーカー: `unit`, `integration`, `auth`, `transfer`, `config`
- カバレッジ閾値: 60%（`--cov-fail-under=60`）
- 既存 `test_*.py` にテストを追加（`test_*_expanded.py` 等の重複ファイル作成禁止）
- 各テストに目的コメントを付与: `# 検証対象: foo()  # 目的: 無効入力で例外を確認`
- Mock は外部依存・破壊的変更・非決定的処理・エッジケース再現時のみ使用
- Windows/Linux/macOS 依存のテストは SKIP 処理で対応（Mock による代替禁止）

### シークレット管理
`.env`（コミット禁止）を使用。`sample.env` をテンプレートとして提供。`.env` には Microsoft Graph API 認証情報（`CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`）を設定。

### コミット規約
Conventional Commits 準拠: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`, `perf:`。PR サイズは ~300 行を目安とする。

### セキュリティ
`bandit` の B101（assert\_used）は `tests/` で除外済み。新規コードでの `assert` 使用は `tests/` 内のみ。セキュリティスキャン: `make security`（bandit）、CI では CodeQL + pip-audit + TruffleHog + SBOM も実行。
