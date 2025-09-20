.PHONY: bootstrap lint format typecheck test cov security build clean help

help: ## このヘルプメッセージを表示
	@echo "利用可能なコマンド:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

bootstrap: ## 開発環境をセットアップ
	uv venv --python 3.13
	uv sync
	uv run pre-commit install

lint: ## ruff によるリンティングを実行
	uv run ruff check .

format: ## ruff による自動フォーマットを実行
	uv run ruff format .

typecheck: ## mypy による型チェックを実行
	uv run mypy .

test: ## pytest によるテストを実行
	uv run pytest -q

cov: ## カバレッジ付きテストを実行
	uv run pytest --cov=src --cov-report=term-missing

security: ## セキュリティスキャンを実行（将来の拡張用）
	@echo "セキュリティスキャンは CI で実行されます"

build: ## プロジェクトをビルド
	uv build

clean: ## キャッシュファイルを削除
	rm -rf .venv .cache .pytest_cache .ruff_cache .mypy_cache dist build htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 開発用コマンド
dev-setup: bootstrap ## 開発環境の完全セットアップ
	@echo "開発環境のセットアップが完了しました"

quality-check: lint typecheck test ## 品質チェックを一括実行
	@echo "品質チェックが完了しました"