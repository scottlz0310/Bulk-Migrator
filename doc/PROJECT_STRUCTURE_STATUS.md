# プロジェクト構造整理状況レポート

## 整理完了日
2024年12月現在

## プロジェクト構造

### ディレクトリ構成
```
Bulk-Migrator/
├── README.md                     # プロジェクト概要
├── requirements.txt              # Python依存関係
├── .env                         # 環境変数（未追跡）
├── .env.example                 # 環境変数テンプレート
├── .gitignore                   # Git除外設定
├── config/
│   └── config.json              # アプリケーション設定
├── doc/                         # ドキュメント
│   ├── Bulk-Migration-1stPLOT.md
│   ├── FILE_STRUCTURE_AND_PLAN.md
│   ├── IMPLEMENTATION_ORDER.md
│   ├── PROJECT_STRUCTURE_STATUS.md
│   └── old/                     # 旧ドキュメント保管
├── logs/                        # ログ・データファイル
│   ├── onedrive_files.json      # OneDriveファイルリスト
│   ├── sharepoint_current_files.json # SharePointファイルリスト
│   ├── skip_list.json           # スキップリスト
│   └── transfer.log             # 転送ログ
├── src/                         # メインソースコード
│   ├── __init__.py              # パッケージ初期化
│   ├── auth.py                  # Graph API認証
│   ├── transfer.py              # ファイル転送・クロール
│   ├── file_crawler.py          # ファイルクロール機能
│   ├── file_crawler_cli.py      # CLIツール
│   ├── main.py                  # メイン実行スクリプト
│   ├── skiplist.py              # スキップリスト管理
│   ├── rebuild_skip_list.py     # スキップリスト再構築
│   ├── logger.py                # ログ機能
│   └── filelock.py              # ファイルロック機能
├── tests/                       # テスト・デバッグスクリプト
│   ├── test_auth.py             # 認証テスト
│   ├── test_single_transfer.py  # 単体転送テスト
│   ├── test_skip_processing.py  # スキップ処理テスト
│   ├── test_full_skip.py        # 全スキップテスト
│   ├── test_skiplist.py         # スキップリストテスト
│   ├── test_transfer_list.py    # 転送リストテスト
│   ├── test_skiplist_vs_targets.py # スキップリスト比較テスト
│   ├── compare_filelist_vs_log.py   # ファイルリスト比較
│   ├── compare_transfer_targets.py # 転送対象比較
│   ├── analyze_single_file_log.py  # ログ分析
│   ├── generate_onedrive_filelist.py # OneDriveリスト生成
│   ├── rebuild_skiplist_from_sharepoint.py # スキップリスト再構築
│   ├── debug_file_access.py     # ファイルアクセスデバッグ
│   ├── debug_onedrive_actual.py # OneDriveデバッグ
│   ├── debug_onedrive_structure.py # OneDrive構造デバッグ
│   ├── debug_sharepoint_structure.py # SharePoint構造デバッグ
│   └── テスト手順書.md          # テスト手順書
└── utils/                       # ユーティリティツール
    ├── investigate_structure.py # 構造調査ツール
    └── verify_transfer.py       # 転送検証ツール
```

## 機能別ファイル分類

### コア機能（src/）
- **認証**: `auth.py`
- **転送・クロール**: `transfer.py`, `file_crawler.py`
- **CLI**: `file_crawler_cli.py`
- **メイン実行**: `main.py`
- **スキップリスト**: `skiplist.py`, `rebuild_skip_list.py`
- **ログ・ファイルロック**: `logger.py`, `filelock.py`

### テスト・デバッグ（tests/）
- **単体テスト**: `test_*.py`
- **デバッグツール**: `debug_*.py`
- **比較・分析ツール**: `compare_*.py`, `analyze_*.py`
- **データ生成**: `generate_*.py`, `rebuild_skiplist_from_sharepoint.py`

### ユーティリティ（utils/）
- **構造調査**: `investigate_structure.py`
- **転送検証**: `verify_transfer.py`

## 整理実施内容

### 完了項目
1. ✅ tests/ディレクトリから重複するfile_crawler_cli.pyを削除
2. ✅ src/、tests/、utils/ディレクトリへの適切な分類完了
3. ✅ ルート直下のクリーンアップ完了
4. ✅ プロジェクト構造の文書化

### 現在の状態
- 全てのPythonスクリプトが適切なディレクトリに配置済み
- 機能別の分類が明確
- 重複ファイルの除去完了
- ドキュメント整理完了

## 主要スクリプトの役割

### 本体スクリプト
- `src/main.py`: バッチ転送の実行
- `src/file_crawler_cli.py`: コマンドライン操作
- `src/rebuild_skip_list.py`: スキップリスト再構築

### 主要テストスクリプト
- `tests/test_auth.py`: 認証機能の総合テスト
- `tests/test_single_transfer.py`: 単体ファイル転送テスト
- `tests/test_full_skip.py`: 全スキップ動作テスト

### 主要ユーティリティ
- `utils/verify_transfer.py`: 転送結果の検証
- `utils/investigate_structure.py`: ディレクトリ構造調査

## 運用における推奨パス

### 日常的な転送実行
```bash
# メイン転送実行
python -m src.main

# CLIでの操作
python -m src.file_crawler_cli explore
python -m src.file_crawler_cli crawl onedrive
python -m src.file_crawler_cli crawl sharepoint
```

### テスト・検証
```bash
# 認証テスト
python tests/test_auth.py

# 転送テスト
python tests/test_single_transfer.py

# 検証ツール
python utils/verify_transfer.py
```

### トラブル時の対応
```bash
# スキップリスト再構築
python -m src.rebuild_skip_list

# 構造調査
python utils/investigate_structure.py

# デバッグ
python tests/debug_onedrive_structure.py
python tests/debug_sharepoint_structure.py
```

## 保守性確保事項

1. **明確な責任分離**: 機能別ディレクトリ分割
2. **テスト体系**: 充実したテストスクリプト群
3. **ドキュメント整備**: 各機能の説明文書
4. **ユーティリティ完備**: 検証・調査ツール
5. **設定の分離**: 環境変数とconfigファイル

## 結論

プロジェクト内のスクリプト整理が完全に完了し、以下の状態になりました：

- **構造の明確化**: 機能別の適切な分類
- **保守性の向上**: テスト・ユーティリティの体系化
- **運用性の確保**: 明確な実行パス
- **拡張性の準備**: 新機能追加時の指針確立

このプロジェクト構造により、OneDriveとSharePoint間の大容量ファイル転送システムの本格運用と保守が効率的に行えます。
