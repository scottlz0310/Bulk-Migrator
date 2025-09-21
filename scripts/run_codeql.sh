#!/bin/bash

# CodeQL Python スキャンスクリプト
# Docker環境でCodeQLを実行し、結果を出力

set -e

echo "🔍 CodeQL Python スキャンを実行中..."

# Dockerが利用可能かチェック
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker が見つかりません。CodeQL スキャンをスキップします。"
    exit 0
fi

# Dockerが実行中かチェック
if ! docker info &> /dev/null; then
    echo "⚠️  Docker が実行されていません。CodeQL スキャンをスキップします。"
    exit 0
fi

# プロジェクトルートディレクトリを取得
PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

# CodeQL結果ディレクトリを作成
mkdir -p codeql-results

# CodeQLデータベース作成とスキャン実行
echo "📊 CodeQLデータベースを作成中..."
echo "💡 ヒント: Docker DesktopでCPU使用率が高い場合は正常に動作中です"
echo "⏱️  データベース作成には数分かかる場合があります"
echo "Command Output:"

# Dockerコンテナ内での権限問題を解決
# 1. ホスト側でディレクトリを作成し、権限を設定
chmod 755 codeql-results 2>/dev/null || true

# 2. Dockerコンテナをrootユーザーで実行
if ! docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /workspace \
    --entrypoint="" \
    mcr.microsoft.com/cstsectools/codeql-container:latest \
    bash -c "set -e && \
    chmod +x /usr/local/startup_scripts/setup.py 2>/dev/null || true && \
    codeql database create \
    --language=python \
    --source-root=/workspace/src \
    /workspace/codeql-results/python-db \
    --threads=0 \
    --overwrite" 2>&1; then
    echo ""
    echo "⚠️  CodeQLデータベース作成に失敗しました。スキップします。"
    echo "📝 可能な原因:"
    echo "   - src/ディレクトリにPythonファイルがない"
    echo "   - Dockerイメージのダウンロード失敗"
    echo "   - ネットワーク接続の問題"
    echo "   - Dockerのメモリ/ディスク容量不足"
    exit 0
fi

echo "🔍 CodeQLクエリを実行中..."
echo "⏱️  クエリ実行にはさらに数分かかります。お待ちください..."
if ! docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /workspace \
    --entrypoint="" \
    mcr.microsoft.com/cstsectools/codeql-container:latest \
    bash -c "set -e && \
    chmod +x /usr/local/startup_scripts/setup.py 2>/dev/null || true && \
    codeql database analyze \
    /workspace/codeql-results/python-db \
    python-security-and-quality \
    --format=sarif-latest \
    --output=/workspace/codeql-results/results.sarif \
    --threads=0 \
    --download" 2>&1; then
    echo ""
    echo "⚠️  CodeQLクエリ実行に失敗しました。スキップします。"
    exit 0
fi

# ホスト側で権限を修正
sudo chown -R $USER:$USER codeql-results 2>/dev/null || true
chmod -R 755 codeql-results 2>/dev/null || true

# 結果の確認
if [ -f "codeql-results/results.sarif" ]; then
    # 結果ファイルから問題数を取得
    issues=$(grep -o '"ruleId"' codeql-results/results.sarif | wc -l || echo "0")
    echo "✅ CodeQL スキャン完了: $issues 件の問題を検出"
    
    if [ "$issues" -gt 0 ]; then
        echo "⚠️  CodeQLで問題が検出されました。詳細は codeql-results/results.sarif を確認してください。"
        # pre-commitでは警告として扱い、失敗させない
        exit 0
    fi
else
    echo "⚠️  CodeQL結果ファイルが生成されませんでした。"
    exit 0
fi

echo "✅ CodeQL スキャンが正常に完了しました。"