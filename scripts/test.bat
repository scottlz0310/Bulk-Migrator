@echo off
REM Windows用テスト実行スクリプト

echo Testing without coverage...
uv run pytest -q

if %ERRORLEVEL% neq 0 (
    echo Tests failed!
    exit /b 1
)

echo All tests passed!