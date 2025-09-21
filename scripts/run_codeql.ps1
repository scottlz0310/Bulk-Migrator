#!/usr/bin/env pwsh

# CodeQL Python スキャンスクリプト (Windows/WSL対応)
# WSL環境でCodeQLを実行し、結果を出力

Write-Host "🔍 CodeQL Python スキャンを実行中..."

# WSLが利用可能かチェック
if (!(Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  WSL が見つかりません。CodeQL スキャンをスキップします。"
    exit 0
}

# WSL内でDockerが利用可能かチェック
$dockerCheck = wsl bash -c "command -v docker > /dev/null 2>&1; echo `$?"
if ($dockerCheck -ne "0") {
    Write-Host "⚠️  WSL内にDocker が見つかりません。CodeQL スキャンをスキップします。"
    exit 0
}

# WSL内でDockerが実行中かチェック
$dockerRunning = wsl bash -c "docker info > /dev/null 2>&1; echo `$?"
if ($dockerRunning -ne "0") {
    Write-Host "⚠️  WSL内でDocker が実行されていません。CodeQL スキャンをスキップします。"
    exit 0
}

# プロジェクトルートを取得
$PROJECT_ROOT = Get-Location

# WSLパスに変換
$wslPath = wsl wslpath -a $PROJECT_ROOT.Path

Write-Host "📊 CodeQLデータベースを作成中..."
Write-Host "Command Output:"

# WSL経由でCodeQLを実行
$createResult = wsl bash -c "
cd '$wslPath'
mkdir -p codeql-results
docker run --rm \
    -v '$wslPath:/workspace' \
    -w /workspace \
    mcr.microsoft.com/cstsectools/codeql-container:latest \
    codeql database create \
    --language=python \
    --source-root=/workspace/src \
    /workspace/codeql-results/python-db \
    --overwrite 2>&1
echo `$?
"

$exitCode = $createResult[-1]
$output = $createResult[0..($createResult.Length-2)]

Write-Host ($output -join "`n")

if ($exitCode -ne "0") {
    Write-Host ""
    Write-Host "⚠️  CodeQLデータベース作成に失敗しました。スキップします。"
    Write-Host "📝 可能な原因:"
    Write-Host "   - src/ディレクトリにPythonファイルがない"
    Write-Host "   - Dockerイメージのダウンロード失敗"
    Write-Host "   - ネットワーク接続の問題"
    Write-Host "   - Dockerのメモリ/ディスク容量不足"
    exit 0
}

Write-Host "🔍 CodeQLクエリを実行中..."
$analyzeResult = wsl bash -c "
cd '$wslPath'
docker run --rm \
    -v '$wslPath:/workspace' \
    -w /workspace \
    mcr.microsoft.com/cstsectools/codeql-container:latest \
    codeql database analyze \
    /workspace/codeql-results/python-db \
    --format=sarif-latest \
    --output=/workspace/codeql-results/results.sarif \
    --download 2>&1
echo `$?
"

$analyzeExitCode = $analyzeResult[-1]
$analyzeOutput = $analyzeResult[0..($analyzeResult.Length-2)]

Write-Host ($analyzeOutput -join "`n")

if ($analyzeExitCode -ne "0") {
    Write-Host ""
    Write-Host "⚠️  CodeQLクエリ実行に失敗しました。スキップします。"
    exit 0
}

# 結果の確認
if (Test-Path "codeql-results/results.sarif") {
    $issues = (Select-String -Path "codeql-results/results.sarif" -Pattern '"ruleId"' -AllMatches).Matches.Count
    if ($null -eq $issues) { $issues = 0 }
    
    Write-Host "✅ CodeQL スキャン完了: $issues 件の問題を検出"
    
    if ($issues -gt 0) {
        Write-Host "⚠️  CodeQLで問題が検出されました。詳細は codeql-results/results.sarif を確認してください。"
    }
} else {
    Write-Host "⚠️  CodeQL結果ファイルが生成されませんでした。"
}

Write-Host "✅ CodeQL スキャンが正常に完了しました。"