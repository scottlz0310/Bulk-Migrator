.PHONY: bootstrap lint format typecheck test cov security build clean help

# デフォルトターゲット
help:
	@echo "Available targets:"
	@echo "  bootstrap  - 開発環境のセットアップ"
	@echo "  lint       - リンティング実行"
	@echo "  format     - コードフォーマット"
	@echo "  typecheck  - 型チェック"
	@echo "  test       - テスト実行（カバレッジなし）"
	@echo "  cov        - カバレッジ付きテスト実行"
	@echo "  security   - セキュリティスキャン"
	@echo "  quality    - 全品質チェック実行"
	@echo "  clean      - キャッシュファイル削除"

bootstrap:
	uv venv --python 3.13
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src/

test:
	uv run python -m pytest -p xdist -q -n auto

cov:
	uv run python -m pytest -p pytest_cov -p xdist --cov=src --cov-report=html:htmlcov --cov-report=term-missing --cov-fail-under=60 -n auto

security:
	uv run bandit -r src/ -f json -o security-report.json || echo "Security scan completed"

quality: lint typecheck test
	@echo "All quality checks completed"

clean:
	if exist .venv rmdir /s /q .venv
	if exist .cache rmdir /s /q .cache
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .ruff_cache rmdir /s /q .ruff_cache
	if exist .mypy_cache rmdir /s /q .mypy_cache
	if exist htmlcov rmdir /s /q htmlcov
	if exist dist rmdir /s /q dist
	if exist build rmdir /s /q build
	del /q .coverage 2>nul || echo ""
	del /q pytest-results.xml 2>nul || echo ""
	del /q security-report.json 2>nul || echo ""