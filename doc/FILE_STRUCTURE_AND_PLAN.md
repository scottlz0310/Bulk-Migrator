# Bulk-Migration ファイル構成・実装計画

## 1. ディレクトリ・ファイル構成（案）

```
Bulk-Migration/
├── src/                  # メインスクリプト群
│   ├── main.py           # エントリポイント・並列転送バッチ
│   ├── auth.py           # GraphAPI認証処理
│   ├── transfer.py       # 転送ロジック・ファイルリスト生成
│   ├── logger.py         # ログ出力
│   ├── skiplist.py       # スキップリスト管理
│   ├── filelock.py       # ファイルロック・排他制御
│   ├── file_crawler.py   # クロール・リスト生成共通関数【本番運用】
│   └── file_crawler_cli.py # CLIインターフェース【本番運用ツール】
├── tests/                # テストスクリプト群
│   ├── test_auth.py      # 認証テスト
│   ├── test_skiplist.py  # スキップリストテスト
│   ├── rebuild_skiplist_from_sharepoint.py # スキップリスト再構築
│   ├── compare_transfer_targets.py         # ファイルリスト比較
│   ├── generate_onedrive_filelist.py       # OneDriveリスト生成
│   └── テスト手順書.md    # テスト実行手順
├── config/
│   └── config.json       # 設定ファイル
├── logs/                 # ログ・スキップリスト・ファイルリスト等
│   ├── transfer.log      # 転送ログ
│   ├── skip_list.json    # スキップリスト
│   ├── onedrive_transfer_targets.json  # OneDriveファイルリスト
│   └── sharepoint_transfer_targets.json # SharePointファイルリスト
├── .env                  # 環境変数（Graph API認証情報等）
├── .env.example          # 環境変数サンプル
├── requirements.txt      # 依存パッケージ
├── README.md             # 概要・使い方
└── doc/                  # 詳細ドキュメント
    ├── FILE_STRUCTURE_AND_PLAN.md   # 本ファイル
    ├── IMPLEMENTATION_ORDER.md      # 実装順序
    └── problem_analysis.md          # 問題分析・修正履歴
```

## 2. 実装計画（フェーズ分割）

### フェーズ1：基盤構築
- ディレクトリ・初期ファイル作成
- 認証（GraphAPI/MSAL）基盤の実装
- 設定ファイル・環境変数の読み込み
- ログ出力の仕組み

### フェーズ2：転送ロジックの実装
- OneDrive/SharePointのディレクトリ再帰取得
- ファイル転送（URL取得→PUTリクエスト）
- スキップリスト・重複防止
- 転送状況のログ化

### フェーズ3：堅牢化・異常時対応
- 途中再開・リトライ機構
- ログ破損時の復旧
- ファイル名規則差異への対応
- 標準出力・ログ粒度の調整

### フェーズ4：整合性・削除・レポート
- ハッシュ値比較による整合性チェック
- 転送元削除・削除ログ
- チェックサムレポート生成

### フェーズ5：セキュリティ・運用性
- 機密情報の安全な管理（環境変数・config柔軟化）
- セットアップスクリプト
- ドキュメント整備

---

## 3. 補足
- 各フェーズごとにテスト・レビューを実施
- 詳細設計・API仕様は `doc/` 配下に随時追加
- 実装優先度や分担は進捗・要望に応じて調整

---

（このドキュメントは随時更新）
