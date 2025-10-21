# Bulk-Migration

![Version](https://img.shields.io/badge/version-main-blue)
![Python](https://img.shields.io/badge/python-3.13+-green)
![License](https://img.shields.io/badge/license-Private-red)

組織用 OneDrive から SharePoint への大容量ファイル転送自動化スクリプト

## 概要
- OneDrive上の大量ファイルをSharePoint Onlineへ安全・効率的に移行するバッチツール
- ディレクトリ構造を保持したまま数百GB規模のファイルを安全・効率的に転送
- Microsoft Graph API を利用し、4MB以上の大容量ファイルはチャンクアップロード対応
- ログ・インデックス・スキップリストによる堅牢な運用に加え転送失敗時の自動リトライ・進捗監視・自動再起動（watchdog）機能あり
- **品質向上機能**: 自動リンティング、テストカバレッジ、セキュリティスキャン、構造化ログ対応
- 利用対象者：SharepontサイトとOndriveを同じ組織上で運用してる管理者またはその権限を有する方

---

## 主な機能

- OneDrive/SharePoint間のファイル・フォルダ構造を再帰的に転送
- 4MB以上のファイルはアップロードセッションによる分割転送
- 転送失敗時の自動リトライ・スキップリスト管理
- 転送進捗・エラー・成功ログの出力
- watchdogによるフリーズ検知＆自動再起動(完了時に未転送ファイルのリトライを含む)
- 転送漏れ検証用のrebuild/verifyバッチ

---

## 使い方

### 基本セットアップ

1. **Python 3.13 以上をインストール**
2. **uv パッケージマネージャーのインストール**
   ```bash
   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
3. **プロジェクトのセットアップ**
   ```bash
   # 仮想環境の作成
   uv venv --python 3.13

   # 依存関係のインストール
   uv sync

   # 環境変数テンプレートのコピー
   cp sample.env .env
   # .env を編集して Microsoft Graph API 認証情報を設定
   ```

### 開発・品質チェック

4. **テストの実行（推奨）**
   ```bash
   # 全テスト実行
   uv run pytest

   # カバレッジ付きテスト実行
   uv run pytest --cov=src --cov-report=html

   # 品質チェック
   uv run ruff check .
   uv run mypy src/
   ```

### アプリケーション実行

5. **設定ファイルの準備**
   - `.env` にMicrosoft Graph API認証情報・転送元/先情報を記載（SETUPGUIDE.md参照）
   - 必要に応じて `config/config.json` で詳細設定

6. **キャッシュ情報の消去と再構築**（初回または設定変更時）
   ```bash
   uv run python src/main.py --reset
   ```

7. **通常運用（監視付き）**
   ```bash
   uv run python src/watchdog.py
   ```

### 品質管理・監視

8. **品質メトリクスの収集**
   ```bash
   # 品質メトリクス収集
   uv run python src/quality_metrics.py

   # 品質アラートチェック
   uv run python src/quality_alerts.py --check

   # 月次レポート生成
   uv run python src/quality_alerts.py --monthly
   ```

9. **セキュリティスキャン**
   ```bash
   # セキュリティスキャン実行
   uv run python scripts/security_scan.py
   ```

---

## 品質向上機能

### 自動品質チェック

本プロジェクトでは以下の品質向上機能が導入されています：

#### コード品質
- **リンティング**: ruff による自動コードフォーマットと静的解析
- **型チェック**: mypy による型安全性の確保
- **テストカバレッジ**: pytest-cov による包括的なテストカバレッジ測定

#### セキュリティ
- **セキュリティスキャン**: bandit による Python セキュリティ脆弱性の自動検出
- **秘密情報管理**: 機密情報の自動マスキングとログ保護
- **依存関係監査**: 既知の脆弱性を持つパッケージの検出

#### 監視・ログ
- **構造化ログ**: JSON 形式による構造化ログ出力
- **品質メトリクス**: カバレッジ、リンティングエラー、セキュリティ脆弱性の自動収集
- **アラート機能**: 品質閾値を下回った場合の自動通知

### 開発者向けコマンド

```bash
# 開発環境のセットアップ
make bootstrap

# コード品質チェック
make lint          # リンティング実行
make format        # コードフォーマット
make typecheck     # 型チェック
make test          # テスト実行
make cov           # カバレッジ付きテスト

# セキュリティチェック
make security      # セキュリティスキャン

# 全体的な品質チェック
make quality       # 全ての品質チェックを実行
```

### CI/CD パイプライン

GitHub Actions により以下が自動実行されます：
- プルリクエスト時の品質チェック
- マルチプラットフォーム（Ubuntu/Windows/macOS）でのテスト
- セキュリティスキャンと脆弱性検出
- カバレッジレポートの生成

---

## 設定ファイル

- `.env` … 認証情報・転送元/先パス等（**必須。`sample.env`を参考に作成。詳細はSETUPGUIDE.md参照**）
- `config/config.json` … チャンクサイズ・並列数・ログパス等（**任意。未設定時はデフォルト値で動作**）
- `sample.env` … 配布用の.envテンプレート。**本番運用時は必ず値を記入し`.env`として保存**
- `SETUPGUIDE.md` … Graph APIキー取得・権限付与・ID確認方法などのセットアップ手順書

---

## 既知の制限・注意事項

- OneDrive/SharePointのAPI仕様上、4MB以上のファイルはチャンクアップロード必須
- すべてのファイルはAPI経由でリモートファイルをクロールしている為、走査時間が長くかかるが、ローカルディスクを圧迫しない
- ファイル名・パス長・属性の差異に注意
- 大量ファイル・大容量ファイルの転送には十分な時間・帯域が必要
- 検証（verify）は転送完了後に--full-rebuildオプションで起動して再走査すれば転送漏れ等はチェックできるがパス＋ファイル名の照合のみである(Sharepointの仕様によりメタデータの付加、タイムスタンプの変更が伴ってしまう)

---


## トラブルシューティング・FAQ

- **Q. `DESTINATION_SHAREPOINT_DOCLIB` で複数階層を指定したい**
  - A. SharePointのドキュメントライブラリ名（`DESTINATION_SHAREPOINT_DOCLIB`）は「トップディレクトリ直下の一階層のみ」指定可能です。`folder1/folder2` のような複数階層は指定できません。サブフォルダを作成したい場合は、転送元OneDrive側のディレクトリ構造をそのまま維持してください。

- **Q. Graph ExplorerでIDや情報がうまく見つからない**
  - A. Graph Explorerは直感的でない部分が多いですが、以下のキーワード・APIパスが特に有用です：
    - `me/drive` … 自分のOneDrive情報
    - `users/{userPrincipalName}/drive` … 指定ユーザーのOneDrive
    - `sites/{domain}.sharepoint.com:/sites/{site-path}` … SharePointサイトID取得
    - `sites/{site-id}/drives` … ドキュメントライブラリ一覧
    - `sites/{site-id}/drives/{drive-id}/root/children` … ルート配下のファイル・フォルダ一覧
  - 検索ワード例：「drive id」「site id」「sharepoint document library id」「graph api list files」など
  - レスポンスの`id`や`name`を.envに転記してください。

- **Q. .envやconfig.jsonの値が反映されない/エラーになる**
  - A. パスやID、シークレットのコピペミス・全角/半角・余計な空白に注意してください。特にダブルクォートや改行の混入に注意。

- **Q. 転送が途中で止まる・watchdogが再起動を繰り返す**
  - A. ネットワークやAPI制限、ファイル名の禁則文字、権限不足などが原因の場合があります。`logs/watchdog.log`や`logs/src_main_stdout.log`を確認し、該当ファイルやエラー内容を特定してください。

---

## 今後の改善予定

- verify機能の強化
- ドキュメント・運用手順のさらなる充実

---

## ライセンス・問い合わせ

- 本リポジトリは非公開・社内利用限定
- ご質問・不具合報告は管理者まで
