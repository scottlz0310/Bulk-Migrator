# Bulk-Migrator

![Version](https://img.shields.io/badge/version-2.3.6-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-Private-red)

Microsoft 365 環境で OneDrive から SharePoint Online へ大容量コンテンツを安全に移行するためのバッチ／ツール群。Microsoft Graph API を利用し、フォルダ階層と再開性を維持した移行を支援します。

## 概要
- 転送対象を OneDrive から再帰的に収集し、SharePoint のドキュメント ライブラリへストリーミング転送。
- 4 MB 以上のファイルは自動的にアップロード セッションで分割し、並列転送・再試行・タイムアウトを構成可能。
- スキップリスト、キャッシュ、構造化ログを使って長時間ジョブでも安全に再開・検証できるよう設計。
- Watchdog、品質メトリクス、セキュリティ スキャンなどの保守用ユーティリティを付属。

## 主な機能

- `src/main.py`: 転送フロー全体を制御し、`python main.py transfer [--reset|--full-rebuild] [--verbose]` から実行。
- `src/transfer.py`: Graph API を呼び出してファイル一覧取得とチャンク アップロードを実行。並列転送とバックオフリトライを提供。
- `src/rebuild_skip_list.py`: SharePoint 側をクロールしてスキップリストを生成し、`python main.py rebuild-skiplist` で実行可能。
- `src/watchdog.py`: ログを監視し、一定時間更新が止まった場合に `src.main` を自動再起動。`python main.py watchdog` で起動。
- `src/quality_metrics.py` / `src/quality_alerts.py`: 品質メトリクス収集とアラートの生成。`python main.py quality-metrics` / `python main.py quality-alerts` で実行。
- `scripts/security_scan.py`: bandit・pip-audit・SBOM 生成を一括で実行。`python main.py security-scan` で起動。
- `utils/` 配下: クロール CLI、統計算出、検証ツールなどの補助スクリプト。`python main.py file-crawler` からヘルプ確認。

## CLI ランチャー

Typer ベースのランチャーで主要コマンドにアクセスできます。仮想環境を有効化した状態で以下を実行してください。

```bash
python main.py
```

メニューが表示されるので、数字を選ぶだけで主な処理を実行できます。直接サブコマンドを呼び出す場合は次の通りです。

- `python main.py transfer [--reset|--full-rebuild] [--verbose]`
- `python main.py rebuild-skiplist`
- `python main.py watchdog`
- `python main.py quality-metrics`
- `python main.py quality-alerts`
- `python main.py security-scan`
- `python main.py file-crawler`

## ディレクトリ構成

```text
Bulk-Migrator/
├── src/
│   ├── main.py
│   ├── transfer.py
│   ├── rebuild_skip_list.py
│   ├── watchdog.py
│   ├── quality_metrics.py
│   ├── quality_alerts.py
│   ├── config_manager.py
│   ├── logger.py
│   ├── structured_logger.py
│   ├── skiplist.py
│   ├── auth.py
│   └── utils/
│       └── find_and_delete_renamed_folders.py
├── utils/
│   ├── file_crawler.py
│   ├── file_crawler_cli.py
│   ├── collect_onedrive_skiplist_stats.py
│   ├── collect_stats.py
│   ├── collect_transfer_success_stats_v2.py
│   ├── compare_entry_detail.py
│   ├── predict_completion.py
│   ├── remove_empty_files.py
│   ├── verify_skiplist_vs_sharepoint.py
│   └── verify_transfer_log.py
├── scripts/security_scan.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── security/
├── config/config.json
├── sample.env
├── SETUPGUIDE.md
├── doc/
└── Makefile
```

## セットアップ

### 前提

- Python 3.11 以上（開発・CI では 3.13 を想定）
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー
- Microsoft Graph API にアクセスできる Azure AD アプリ登録済み

### 手順

1. uv をインストールし、仮想環境を作成します（Windows は PowerShell 相当のコマンドを使用）。

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv venv --python 3.13
   source .venv/bin/activate
   ```

2. 依存関係を同期します。

   ```bash
   uv sync
   ```

3. 環境変数ファイルを作成し、Microsoft Graph の認証情報と転送設定を記入します。

   ```bash
   cp sample.env .env
   # 必要なキーは SETUPGUIDE.md を参照して編集
   ```


### 環境変数 (.env)

- `CLIENT_ID` / `CLIENT_SECRET` / `TENANT_ID`: Azure AD アプリの認証情報。
- `SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME`: 転送元ユーザーの UPN。
- `SOURCE_ONEDRIVE_FOLDER_PATH`: クロールを開始する OneDrive 上のルートフォルダ。
- `SOURCE_ONEDRIVE_DRIVE_ID`: OneDrive ドライブ ID（UPN でアクセスできない場合に必須）。
- `DESTINATION_SHAREPOINT_SITE_ID` / `DESTINATION_SHAREPOINT_DRIVE_ID`: SharePoint サイトとドキュメントライブラリの ID。
- `DESTINATION_SHAREPOINT_DOCLIB`: 転送先ドキュメントライブラリのルートフォルダ名。
- `DESTINATION_SHAREPOINT_HOST_NAME` / `DESTINATION_SHAREPOINT_SITE_PATH`: 一部ユーティリティで利用する SharePoint ホスト情報。

### config/config.json

- `chunk_size_mb`: チャンクアップロード時の分割サイズ（MB）。
- `large_file_threshold_mb`: セッションアップロードに切り替えるファイルサイズ（MB）。
- `max_parallel_transfers`: 同時転送数。
- `retry_count`: 転送リトライ回数。
- `timeout_sec`: HTTP タイムアウト。
- `onedrive_files_path` / `sharepoint_current_files_path` / `skip_list_path`: 各種キャッシュファイル保存先。
- `transfer_log_path`: 転送ログの出力先。
- その他のキーは `config/config.json` と `config_manager.py` を参照してください。

## 基本的な運用フロー

1. 初回または設定・環境変数を変更した場合はキャッシュを再生成します。  
   `uv run python -m src.main --reset`
2. 通常運用では OneDrive キャッシュとスキップリストを参照しつつ転送を実行します。  
   `uv run python -m src.main`
3. SharePoint 側を含めて強制再クロールしたい場合はフルリビルドを使用します。  
   `uv run python -m src.main --full-rebuild`
4. ログは `logs/transfer_start_success_error.log` に出力され、`logs/onedrive_files.json` / `logs/sharepoint_current_files.json` / `logs/skip_list.json` にキャッシュが保存されます。

## 監視と保守支援ツール

- `uv run python -m src.watchdog`: 転送ログの更新を監視し、一定時間無反応の場合に `src.main` を再起動。
- `uv run python -m src.rebuild_skip_list`: SharePoint をクロールしてスキップリストを再構築。
- `uv run python utils/file_crawler_cli.py onedrive --save logs/onedrive_files.json`: OneDrive 側の最新リストを収集。
- `uv run python utils/file_crawler_cli.py sharepoint --save logs/sharepoint_current_files.json`: SharePoint の現在の状態を取得。
- `uv run python utils/file_crawler_cli.py skiplist --root DEST_LIB --save logs/skip_list.json`: SharePoint から直接スキップリストを生成。
- `uv run python utils/predict_completion.py`: 転送ログから残作業時間を推定。

## 品質・テスト・セキュリティ

- `uv run pytest`: すべてのテスト（`tests/unit`, `tests/integration`, `tests/security`）を実行。
- `uv run pytest -m unit` / `-m integration` / `-m security`: マーカ別テスト実行。
- `uv run pytest --cov=src --cov-report=term-missing`: カバレッジ測定。
- `uv run ruff check .` / `uv run ruff format --check .`: コードスタイルと静的解析。
- `uv run mypy src/`: 型チェック。
- `uv run python src/quality_metrics.py`: 品質メトリクスの収集と `quality_reports/metrics_*.json` への保存。
- `uv run python src/quality_alerts.py --check`: 閾値チェックとアラート生成（`quality_reports/alerts/`）。
- `uv run python scripts/security_scan.py`: bandit・pip-audit・SBOM の一括実行（`security_reports/`）。
- `make lint` / `make test` / `make quality`: uv コマンドをまとめて実行するショートカット。

## ログと生成物

- `logs/transfer_start_success_error.log`: ローテーション付き転送ログ。
- `logs/onedrive_files.json`: OneDrive 側の最新ファイルリストキャッシュ。
- `logs/sharepoint_current_files.json`: SharePoint 側のキャッシュ。
- `logs/skip_list.json`: 転送済みと判定されたファイルのスキップリスト。
- `logs/config_hash.txt`: 直近に使用した設定ハッシュ。変更検知に利用。
- `quality_reports/`: 品質メトリクス、アラート、定期レポート。
- `security_reports/`: セキュリティスキャン結果と SBOM。
- `pytest-results.xml`, `htmlcov/`: テスト結果やカバレッジレポート（必要に応じて生成）。

## 既知の制限・注意事項

- Graph API の仕様上、4 MB 以上のファイルはアップロードセッションでの分割が必須です。
- SharePoint へ転送後はメタデータやタイムスタンプが変化する場合があり、`verify` 系スクリプトはファイル名とパスの一致のみを検証します。
- API レート制限に達した場合は自動リトライされますが、大量転送時は追加の待機時間が発生します。
- `DESTINATION_SHAREPOINT_DOCLIB` はドキュメントライブラリ直下の 1 階層のみ指定可能です。サブフォルダ構成は OneDrive 側の階層で調整してください。
- Windows 環境での長時間運用時はウイルス対策ソフトやスリープ設定によりログ更新が止まる場合があるため、watchdog の導入を推奨します。

## ドキュメント

- `SETUPGUIDE.md`: Azure アプリ登録、Graph Explorer での ID 取得手順。
- `doc/operational_procedures.md`: 定常運用フローと対応手順。
- `doc/quality_checklist.md`: 品質ゲートと確認項目。
- `doc/rollback_plan.md`: 転送失敗時のロールバック計画。
- `UPGRADE_NOTES.md`: バージョンアップ時の変更点。

## ライセンス・問い合わせ

- 本リポジトリは社内利用限定のプライベートプロジェクトです。
- 不具合や質問はプロジェクト管理者までご連絡ください。
