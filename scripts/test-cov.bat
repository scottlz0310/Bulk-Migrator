@echo off
REM Windows用カバレッジ付きテスト実行スクリプト

echo Testing with coverage...
uv run pytest --cov=src --cov-report=html:htmlcov --cov-report=term-missing --cov-fail-under=60

if %ERRORLEVEL% neq 0 (
    echo Tests with coverage failed!
    exit /b 1
)

echo All tests passed with coverage!