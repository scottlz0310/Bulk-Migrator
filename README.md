# Bulk-Migration

組織用 OneDrive から SharePoint への大容量ファイル転送自動化スクリプト

## 概要
- OneDrive上の大量ファイルをSharePoint Onlineへ安全・効率的に移行するバッチツール
- ディレクトリ構造を保持したまま数百GB規模のファイルを安全・効率的に転送
- Microsoft Graph API を利用し、4MB以上の大容量ファイルはチャンクアップロード対応
- ログ・インデックス・スキップリストによる堅牢な運用に加え転送失敗時の自動リトライ・進捗監視・自動再起動（watchdog）機能あり
- 利用対象者：SharepontサイトとOndriveを同じ組織上で運用してる管理者またはその権限を有する方

---

## 主な機能

- OneDrive/SharePoint間のファイル・フォルダ構造を再帰的に転送
- 4MB以上のファイルはアップロードセッションによる分割転送
- 転送失敗時の自動リトライ・スキップリスト管理
- 転送進捗・エラー・成功ログの出力
- watchdogによるフリーズ検知＆自動再起動
- 転送漏れ検証用のrebuild/verifyバッチ

---

## 使い方

1. Python 3.8 以上をインストール
2. 仮想環境を作成
   ```bash
   python -m venv venv
   ```
3. 仮想環境を有効化
   - Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - Windows:
     ```cmd
     venv\Scripts\activate
     ```
4. 依存関係をインストール
   ```bash
   pip install -r requirements.txt
   ```
5. `.env` にMicrosoft Graph API認証情報・転送元/先情報を記載※SETUPGUIDE.md参照
6. 必要に応じて `config/config.json` で詳細設定
7. キャッシュ情報の消去と再構築※キャッシュ情報やログをを初期化したくなったとき以外はこの項をスキップして通常運用を実行して良い。初回起動を含め設定変更を認識したときやキャッシュが存在しないときは自動でクロールを開始するが、明示的に再構築をしたいときは推奨
   ```bash
   python -m src.main --reset
   ```
8. 通常運用（監視付き）  
   ```bash
   python src/watchdog.py
   ```

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
