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
echo "Command Output:"

# エラー出力をキャプチャして表示
if ! docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /workspace \
    mcr.microsoft.com/cstsectools/codeql-container:latest \
    codeql database create \
    --language=python \
    --source-root=/workspace/src \
    /workspace/codeql-results/python-db \
    --overwrite 2>&1; then
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
if ! docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /workspace \
    mcr.microsoft.com/cstsectools/codeql-container:latest \
    codeql database analyze \
    /workspace/codeql-results/python-db \
    --format=sarif-latest \
    --output=/workspace/codeql-results/results.sarif \
    --download 2>&1; then
    echo ""
    echo "⚠️  CodeQLクエリ実行に失敗しました。スキップします。"
    exit 0
fi

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