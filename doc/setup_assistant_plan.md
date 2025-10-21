# Setup Assistant Implementation Plan (v2.4.0)

## 目的
- Microsoft Graph 設定の初期セットアップを CLI で支援し、`.env` を対話的に自動生成できるようにする。
- Azure アプリ登録済み/未登録の両ケースに対応し、途中中断・再開が容易なフローを提供する。
- 既存ドキュメント（README, SETUPGUIDE）と整合したオンボーディング体験を実現する。

## スコープ
- 新 CLI (`scripts/setup_assistant.py`) と関連モジュールの実装。
- Device Code Flow を使用した管理者認証、Graph API 呼び出し、必要 ID の取得。
- `.env` 更新の自動化、バックアップ、検証。
- ドキュメント/テスト/Makefile の最小限の更新。

## 優先度
1. CLI 基盤・認証・Graph API 連携。
2. `.env` 自動生成と検証。
3. ドキュメント整備と統合テスト。

## 想定ユーザーとユースケース
- **管理者**: Graph Explorer を使わずに CLI でセットアップを完了したい。
- **開発者**: ステージング環境で `.env` を短時間で再構築したい。
- **CI**: 非対話モードで構成検証のみ走らせたい。

## 機能要件
### CLI 概要
- `uv run python scripts/setup_assistant.py env [--existing-app|--create-app|--non-interactive]`
- サブコマンド例:
  - `env`: `.env` の生成・更新。
  - `validate`: 作成済み `.env` と Graph API 権限の整合性チェック。
  - 将来拡張用に `export` や `audit` を予約。

### フロー詳細
1. **認証**
   - Device Code Flow (MSAL) で管理者ログイン。
   - 必要スコープ: `offline_access`, `User.Read.All`, `Sites.Read.All`, `Application.Read.All`, `Application.ReadWrite.All`（`--create-app` 時）。
   - 認証状態とトークンのキャッシュは `logs/setup_token_cache.json` に保存。
2. **テナント情報取得**
   - `GET /organization` で `TENANT_ID`, `displayName` を収集。
   - 取得結果をユーザーに確認させる。
3. **アプリ登録フロー**
   - `--existing-app`:
     - `CLIENT_ID` を入力 → `/applications/{id}` で存在確認。
     - `client secret` が不明な場合は再作成の手順を提示。
   - `--create-app`:
     - `POST /applications` で新規アプリを生成し、必要な API 権限を設定。
     - `POST /applications/{id}/addPassword` で client secret を取得。
     - 結果を `.env` に保持し、秘密情報は再表示しない旨を通知。
4. **OneDrive 情報**
   - 個人用 / 組織用 (共有ライブラリ) を選択できるよう制御フローを分岐。
     - **個人用 (Personal OneDrive)**:
       - ユーザー UPN を入力または `GET /users?$filter=` で候補表示。
       - `GET /users/{UPN}/drive` で `SOURCE_ONEDRIVE_DRIVE_ID` を取得。
     - **組織用 (SharePoint/Shared Library)**:
       - サイト選択と共通化し、`GET /sites/{hostname}:/sites/{path}` → `GET /sites/{id}/drives` で該当ドライブを選択。
       - 選択結果を OneDrive 設定として扱えるよう `.env` キー (`SOURCE_ONEDRIVE_DRIVE_ID`, `SOURCE_ONEDRIVE_USER_PRINCIPAL_NAME` など) に適切に反映。
   - 対象フォルダは手入力 + API から上位フォルダ一覧を提示。種類に応じて API パスを切り替える。
5. **SharePoint 情報**
   - サイト検索 (`GET /sites?search=`) または `GET /sites/{hostname}:/sites/{path}`。
   - ドライブ一覧 (`GET /sites/{id}/drives`) からライブラリを選択。
   - `DESTINATION_SHAREPOINT_SITE_ID`, `DRIVE_ID`, `DOCLIB`, `HOST_NAME`, `SITE_PATH` を抽出。
6. **確認 & 編集**
   - CLI 内で収集値を一覧表示し、修正があれば個別に再入力。
   - 途中状態は `logs/setup_session.json` に保存し、再開時に読み込む。
7. **.env 書き込み**
   - 既存 `.env` があればバックアップ (`.env.backup-YYYYmmddHHMM`)、差分表示。
   - `sample.env` の順序・コメントを反映しつつ、未設定キーは空欄のまま保持。
8. **検証**
   - `.env` 読み込み後に Graph API でシンプルな疎通テストを実施。
   - 成功/失敗を表示し、失敗時の診断（HTTP エラー、権限不足など）を提示。

## 非機能要件
- 対話操作はキャンセル可能で、途中再開を考慮。
- CLI 実行ログを `logs/setup_assistant.log` に出力。
- 秘密情報は画面に再表示しない。保存先は `.env` のみ。
- コードは既存スタイル（type hints, structured logging）に準拠。

## 実装タスク
1. **設計/セットアップ**
   - `src/setup/` ディレクトリ新設。
   - `scripts/setup_assistant.py` の CLI スケルトン作成（argparse 予定）。
2. **MS Graph クライアント**
   - `src/setup/ms_graph_client.py`: Device Code Flow、Graph API 呼び出しユーティリティ。
   - 検証用のモック/インタフェースを用意。
3. **プロンプト/バリデーション**
   - `src/setup/prompts.py`: ユーザー入力、再入力、 yes/no 確認などの共通処理。
   - UPN、URL、GUID のバリデータ追加。
4. **セッション管理**
   - `src/setup/session_store.py`: `logs/setup_session.json` への保存/読み込み。
   - 途中中断時に再開できるよう CLI 起動時にセッションを読み込み。
5. **.env 書き込み**
   - `src/setup/env_writer.py`: バックアップ、差分表示、安全な書き込み。
   - `sample.env` を読み込み順序を維持する仕組み。
6. **CLI フロー統合**
   - `scripts/setup_assistant.py`: 上記モジュールを組み合わせ、`env` コマンドを完成。
   - `validate` サブコマンド（.env を読み込み Graph API で疎通チェック）。
7. **既存ツール連携**
   - `utils/file_crawler_cli.py` に `setup` コマンドを追加、setup assistant を呼び出す。
   - `Makefile` に `setup-env` ターゲットを追加。
8. **テスト**
   - 単体テスト (`tests/unit/setup/`) を追加。
   - 非対話モードの統合テスト (`tests/integration/test_setup_assistant.py`) を追加。
9. **ドキュメント**
   - README のセットアップ手順に CLI の案内を追加。
   - SETUPGUIDE を整理し、CLI 手順とトラブルシューティングを追加。
   - `sample.env` に CLI で自動生成可能な旨のコメントを追記。

## タイムライン（案）
1. 週1: 設計整理・CLI スケルトン・セッション保存まで。
2. 週2: Graph API 連携（existing-app フロー）と `.env` 書き込み実装。
3. 週3: create-app フロー、非対話モード、テスト整備。
4. 週4: ドキュメント更新、総合テスト、レビュー・調整。

## リスクと対策
- **Graph API 権限不足**: CLI でエラーメッセージに必要スコープと手動手順を表示。
- **Device Code Flow 失敗**: リトライ機能、タイムアウト時の再試行ガイド。
- **.env 上書き事故**: 常にバックアップ&差分確認を行い、ユーザー確認後に確定。
- **セッションデータ破損**: 読み込み時に検証し、破損時は再生成とユーザー通知。

## 成果物
- `scripts/setup_assistant.py`
- `src/setup/` 配下の新モジュール
- 新テストケース
- 更新された README.md, SETUPGUIDE.md, sample.env
- ログ/セッションデータ保存仕様

---

この計画に基づき、実装を段階的に進める。進捗・仕様変更は本ドキュメントに追記する。
