# Bulk-Migration

組織用 OneDrive から SharePoint への大容量ファイル転送自動化スクリプト

## 概要
- ディレクトリ構造を保持したまま数百GB規模のファイルを安全・効率的に転送
- Microsoft Graph API を利用
- ログ・インデックス・スキップリストによる堅牢な運用

## セットアップ
1. Python 3.8 以上をインストール
2. `requirements.txt` で依存パッケージをインストール
3. `.env` を作成し認証情報を記入
4. `config/config.json` を編集

## 実行例
```bash
# 仮想環境を有効化（初回や新しいターミナルの場合は必須）
source venv/bin/activate
python -m src.main
```

## 大容量ファイル対応
- 4MB以上のファイルは自動的にアップロードセッション（分割アップロード）を使用
- チャンクサイズは `config/config.json` で設定可能（デフォルト: 5MB）
- 従来の単純PUTでは転送できなかった数百MB～GBクラスのファイルも安全に転送

## 詳細は `Bulk-Migration-PLOT.txt` を参照
