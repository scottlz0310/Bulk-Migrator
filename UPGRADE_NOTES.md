# アップグレードノート

## Python 3.13 & 並列テスト実行への更新

### 変更内容

#### 1. Python バージョンアップグレード
- **Python 3.12** → **Python 3.13** に更新
- 最新の Python 機能とパフォーマンス改善を活用

#### 2. 並列テスト実行の導入
- `pytest-xdist` を追加してテストの並列実行を有効化
- テスト実行時間の大幅な短縮を実現

### 更新されたファイル

1. **pyproject.toml**
   - `requires-python = ">=3.13"`
   - `pytest-xdist>=3.6.0` を依存関係に追加
   - pytest の `addopts` に `-n=auto` を追加

2. **.python-version**
   - `3.13` に更新

3. **Makefile**
   - テストコマンドに `-n auto` オプションを追加

4. **GitHub Actions (.github/workflows/quality-check.yml)**
   - 並列テスト実行を有効化

5. **run_tests.py**
   - 並列実行オプションを追加

### 移行手順

#### 既存環境からの移行

1. **Python 3.13 のインストール**
   ```bash
   # Windows (winget)
   winget install Python.Python.3.13
   
   # macOS (Homebrew)
   brew install python@3.13
   
   # Linux (Ubuntu/Debian)
   sudo apt update
   sudo apt install python3.13 python3.13-venv
   ```

2. **仮想環境の再作成**
   ```bash
   # 既存の仮想環境を削除
   rm -rf .venv  # Linux/macOS
   rmdir /s .venv  # Windows
   
   # 新しい仮想環境を作成
   uv venv --python 3.13
   uv sync
   ```

3. **動作確認**
   ```bash
   # 並列テスト実行の確認
   python test_parallel.py
   
   # 通常のテスト実行
   make test
   
   # カバレッジ付きテスト
   make cov
   ```

### パフォーマンス改善

#### テスト実行時間の短縮
- **並列実行**: CPU コア数に応じて自動的にワーカープロセスを起動
- **期待される効果**: 2-4倍の速度向上（テスト数とCPUコア数に依存）

#### Python 3.13 の新機能
- **JIT コンパイラ**: 実行時パフォーマンスの向上
- **改善されたエラーメッセージ**: デバッグ効率の向上
- **メモリ使用量の最適化**: より効率的なメモリ管理

### 注意事項

#### 並列テスト実行の制限
1. **共有リソース**: ファイルやデータベースを共有するテストは注意が必要
2. **テスト分離**: テスト間の依存関係がないことを確認
3. **ランダム性**: 並列実行により実行順序が変わる可能性

#### 対応策
- テストの独立性を保つ
- 一時ファイルには一意な名前を使用
- 共有リソースへのアクセスは適切に同期化

### トラブルシューティング

#### よくある問題

1. **仮想環境の作成に失敗**
   ```bash
   # 権限の問題の場合
   uv venv --python 3.13 --clear
   ```

2. **並列テストでエラーが発生**
   ```bash
   # シーケンシャル実行に戻す
   pytest tests/ -v  # -n auto を除く
   ```

3. **Python 3.13 が見つからない**
   ```bash
   # インストール確認
   python3.13 --version
   
   # パスの確認
   which python3.13  # Linux/macOS
   where python  # Windows
   ```

### 検証方法

#### 並列テスト実行の確認
```bash
# 専用テストスクリプトで検証
python test_parallel.py

# 手動での確認
pytest tests/unit/ -v -n auto  # 並列実行
pytest tests/unit/ -v         # シーケンシャル実行
```

#### パフォーマンス測定
```bash
# 時間測定付きテスト実行
time make test

# 詳細なプロファイリング
pytest tests/ --durations=10 -n auto
```

### 今後の計画

1. **Python 3.14 対応**: リリース後の対応準備
2. **テスト最適化**: 並列実行に最適化されたテスト構造への改善
3. **CI/CD 最適化**: GitHub Actions での並列実行の最適化

---

## 関連リンク

- [Python 3.13 リリースノート](https://docs.python.org/3.13/whatsnew/3.13.html)
- [pytest-xdist ドキュメント](https://pytest-xdist.readthedocs.io/)
- [uv ドキュメント](https://docs.astral.sh/uv/)

---

**更新日**: 2025-01-27
**バージョン**: 1.0.0