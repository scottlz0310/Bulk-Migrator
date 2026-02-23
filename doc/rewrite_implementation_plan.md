# Bulk-Migrator リライト実装計画書（新規リポジトリ）

## 1. 目的

本計画書は、現行 Python 実装の仕様を欠落なく引き継ぎつつ、**並列実行に強い言語（C#/.NET）**で新規リポジトリへリライトするための実装計画を定義する。

- 対象: OneDrive → SharePoint の大容量移行ツール群
- 方針: 仕様互換を最優先し、段階的に置換する
- 成果物: 新規リポジトリ（.NET 実装、CI、運用ドキュメント、移行手順）

---

## 2. 採用技術（リライト先）

### 2.1 言語・実行基盤
- **C# / .NET 8 LTS（.NET 10 互換方針）**
- 採用理由:
  - `Parallel.ForEachAsync` による上限付き並列処理
  - `System.Threading.Channels` による背圧制御（有界キュー）
  - Microsoft Graph SDK の大容量アップロード支援（再開・進捗）
  - 単一配布（self-contained）と運用性の高さ

### 2.2 推奨ライブラリ
- CLI: `System.CommandLine`
- 設定: `Microsoft.Extensions.Configuration`（env > file > default）
- 構造化ログ: `Microsoft.Extensions.Logging` + JSON sink（Serilog等）
- HTTP: `HttpClient` / `SocketsHttpHandler`
- Graph: Microsoft Graph SDK（LargeFileUploadTask, RetryHandler）
- テスト: `xUnit` / `NUnit` + `FluentAssertions` + `Moq`

### 2.3 計画見直し提案の採否（2026-02-23）

| 項目 | 判定 | 理由 |
|---|---|---|
| Go→.NET への方針転換 | 採用 | 現行スコープが Graph 中心で、SDK活用により実装リスクを下げられるため |
| Channels + Parallel.ForEachAsync | 採用 | 背圧と上限付き並列を標準機能で実装できるため |
| Graph Retry-After 厳守 | 採用 | 429/一時障害への運用要件と整合するため |
| Native AOT を必須化 | 条件付き採用 | 効果は高いが、トリミング制約の検証完了後に有効化するため |
| Dropbox 先行フェーズ化 | 現フェーズ不採用（将来採用） | 現行要件外のため先行実装はしないが、拡張点を先に固定して手戻りを抑制する |

### 2.4 将来 Dropbox 拡張の手戻り最小化方針

- ストレージ実装は `IStorageProvider`（仮称）で抽象化し、Graph 実装はその1実装として構築する。
- 設定は `providers.graph.*` / `providers.dropbox.*` の名前空間で分離し、クラウド別のチャンク/DoP/リトライを初期から表現可能にする。
- セッション再開情報・転送マニフェストは provider フィールドを含む共通フォーマットで永続化する。
- 受入テストは provider 共通テスト + provider 固有テストの2層構成にし、Dropbox 追加時の回帰を最小化する。

---

## 3. 仕様網羅チェックリスト（現行互換要件）

以下は新実装で必ず互換維持する仕様。実装時は ID 単位で受入テストを作成する。

### 3.1 コア機能仕様（必須）

| ID | 仕様 |
|---|---|
| FR-01 | Microsoft Graph (client credentials) 認証、トークン有効期限前の再取得 |
| FR-02 | OneDrive 指定ルートの再帰クロール（重複排除、path/name/id/size/更新日時保持） |
| FR-03 | SharePoint ドキュメントライブラリ配下の再帰クロール |
| FR-04 | 4MB未満ファイル: 単純 PUT アップロード |
| FR-05 | 4MB以上ファイル: Upload Session + チャンクアップロード |
| FR-06 | 転送先フォルダ自動作成（階層を順次作成） |
| FR-07 | スキップリスト管理（判定キー: **path + name**、サイズ/時刻は判定に使わない） |
| FR-08 | 転送成功後に skip_list へ原子的追加（排他制御あり） |
| FR-09 | OneDrive/SharePoint クロール結果のキャッシュファイル化 |
| FR-10 | 設定変更検知（設定ハッシュ）とキャッシュ・ログのクリア |
| FR-11 | `--reset`: 再構築のみ実施（転送なし） |
| FR-12 | `--full-rebuild`: キャッシュ再作成 + 再構築 + 転送実行 |
| FR-13 | 通常実行: skip_list 不在時は自動再構築後に転送 |
| FR-14 | 並列転送（現行 max_parallel_transfers 相当） |
| FR-15 | ネットワーク失敗時リトライ（ConnectionError/一時障害） |
| FR-16 | watchdog によるフリーズ監視（ログ無更新10分で再起動） |
| FR-17 | 転送残ありで main 正常終了時に watchdog が再起動継続 |
| FR-18 | file_crawler CLI（onedrive/sharepoint/skiplist/compare/validate/explore） |

### 3.2 品質・監視仕様（必須）

| ID | 仕様 |
|---|---|
| NFR-01 | 構造化 JSON ログ（timestamp UTC ISO8601, level, event, message, logger, module, trace_id, span_id, request_id） |
| NFR-02 | 機密情報マスキング（secret/token/password/api_key/メール等） |
| NFR-03 | 転送ログ・watchdogログ・監査ログの分離 |
| NFR-04 | 品質メトリクス収集（coverage/lint/type/security/tests） |
| NFR-05 | 品質アラート（coverage<60, lint>0, type>0, security>0, failed_tests>0） |
| NFR-06 | 月次/四半期/半年レポート生成 |
| NFR-07 | セキュリティスキャン（bandit/pip-audit 相当）と統合サマリ出力 |

### 3.3 設定・運用仕様（必須）

| ID | 仕様 |
|---|---|
| OPS-01 | 設定優先順位: **環境変数 > config file > default** |
| OPS-02 | 現行 `.env` キー互換（Graph資格情報、OneDrive/SharePoint ID群） |
| OPS-03 | `config/config.json` 相当（chunk_size_mb, large_file_threshold_mb, max_parallel_transfers, retry_count, timeout_sec, paths） |
| OPS-04 | ログ/レポート/キャッシュ出力先の外部設定可能化 |
| OPS-05 | CLI サブコマンド互換（transfer/rebuild-skiplist/watchdog/quality-metrics/quality-alerts/security-scan/file-crawler） |
| OPS-06 | CI 品質ゲート互換（lint/format/type/test+coverage/security） |
| OPS-07 | Renovate/依存更新運用の維持 |

---

## 4. 新規リポジトリアーキテクチャ案（.NET）

```text
bulk-migrator-dotnet/
├─ src/
│  ├─ BulkMigrator.Cli/            # メインCLI
│  ├─ BulkMigrator.Core/           # ドメイン・ユースケース
│  ├─ BulkMigrator.Providers.Abstractions/ # IStorageProvider等の契約
│  ├─ BulkMigrator.Providers.Graph/        # Graph認証/転送
│  ├─ BulkMigrator.Providers.Dropbox/      # 将来拡張（初期は実装スケルトンのみ）
│  ├─ BulkMigrator.Observability/  # 構造化ログ・メトリクス
│  └─ BulkMigrator.Testing/        # テスト共通
├─ configs/
│  └─ config.json
├─ docs/
├─ tools/
├─ test/
│  ├─ unit/
│  ├─ integration/
│  └─ e2e/
└─ .github/workflows/
```

---

## 5. 並列実行設計（.NETでの強化ポイント）

1. **有界キュー（背圧）**
   - `Channel.CreateBounded<TransferJob>(capacity)` を使用
   - クロール側と転送側を分離しつつ、メモリ上限を維持

2. **上限付き並列転送**
   - `Parallel.ForEachAsync` と `MaxDegreeOfParallelism` で制御
   - `CancellationToken` により安全停止

3. **大容量ファイル転送**
   - Graph SDK の `LargeFileUploadTask` を優先採用
   - チャンク送信・進捗・再開を SDK 標準で実現

4. **再試行ポリシー**
   - Graph は `Retry-After` 準拠の再試行を適用
   - その他一時障害は指数バックオフ＋ジッターで統一

---

## 6. 実装フェーズ（新規リポジトリ）

### Phase 0: 仕様凍結
- 本書の FR/NFR/OPS ID を仕様ベースライン化
- 旧ドキュメントとの差分（`doc/`, `doc/old/`）を一覧化

### Phase 1: プロジェクト基盤
- .NET solution / project 初期化
- Lint/Format/Test/CI 雛形
- 設定ローダ（env > json > default）
- provider 抽象契約（IStorageProvider）と共通転送モデルを確定

### Phase 2: 認証・Graph基盤
- client credentials 認証
- Graph API クライアント共通化（retry, timeout, rate-limit対応）
- LargeFileUploadTask を利用した大容量アップロード PoC
- provider 契約に沿って Graph 実装を接続（将来Dropbox差替え可能な形を維持）

### Phase 3: クロール + スキップリスト
- OneDrive/SharePoint 再帰クロール
- skip_list 読み書き、ロック制御、判定規約（path+name）

### Phase 4: 転送エンジン
- small/large upload 実装（SDK優先）
- 失敗リトライ、フォルダ自動作成、並列転送
- セッション再開と部分再送の永続化

### Phase 5: 実行モード互換
- `--reset`, `--full-rebuild`, 通常実行の互換動作
- 設定変更ハッシュ検知とキャッシュ再生成

### Phase 6: 監視・品質・セキュリティ
- watchdog
- 品質メトリクス/アラート/定期レポート
- セキュリティスキャン統合

### Phase 7: 補助CLI・運用機能
- file_crawler 系サブコマンド
- validate/explore/compare
- 既存運用 Runbook を .NET 版へ移植
- Dropbox 拡張用の空実装テンプレートと開発ガイドを整備（機能実装は範囲外）

### Phase 8: E2E・性能検証・切替
- 実データに近い E2E
- 並列数・チャンクサイズ最適化
- 本番切替計画（段階的カットオーバー）

---

## 7. 並行開発ワークストリーム

- **WS-A（Platform）**: repo/CI/config/logging
- **WS-B（Graph/Auth）**: 認証・Graph client
- **WS-C（Core Transfer）**: crawl/skiplist/transfer engine
- **WS-D（Ops & Reliability）**: watchdog/quality/security/reporting
- **WS-E（CLI & Docs）**: command UX, setup/運用ドキュメント

依存関係:
- WS-B 完了後に WS-C 本格化
- WS-C 完了後に WS-D の E2E を実施

---

## 8. テスト計画（仕様IDトレーサビリティ）

1. **単体テスト**
   - FR-01〜FR-18 の関数単位検証
2. **統合テスト**
   - クロール→スキップ生成→転送→再実行の連続シナリオ
3. **E2Eテスト**
   - 実 Graph API かステージング環境での通し確認
4. **回帰テスト**
   - 現行 Python 出力（ログ/skip_list/cache）との比較
5. **性能テスト**
   - 並列数別の throughput / failure rate / retry rate 計測

---

## 9. リリースと移行

1. 新リポジトリで v0 系を段階リリース
2. 既存 Python 実装と並行稼働（同一入力で比較）
3. 主要ジョブを .NET 版へ段階切替
4. watchdog/監視系を最後に切替
5. 旧実装を read-only 化し保守モードへ

---

## 10. リスクと対策

- Graph API のレート制限/一時エラー  
  → 指数バックオフ + ジッター + 上限付き再試行
- Native AOT のトリミング/Reflection 制約  
  → AOT 検証ジョブを CI に追加し、非互換依存を段階除去
- 仕様取りこぼし  
  → FR/NFR/OPS ID ごとの受入テストを必須化
- ログ互換崩れ  
  → JSON schema と必須フィールド検証を CI で強制
- 大容量時のメモリ増大  
  → ストリーミング + bounded queue + profiler 監視

---

## 11. 完了条件（Definition of Done）

- FR/NFR/OPS の全 ID に対するテストが green
- 既存運用コマンドに対応する .NET CLI が提供済み
- 既存品質ゲート（lint/type/test/security/coverage）を新リポジトリで再現
- 本番想定データでの転送成功率・再実行安全性・監視挙動を確認
- 運用手順書（セットアップ、日次運用、障害対応、ロールバック）を更新済み

