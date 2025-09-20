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

security: ## セキュリティスキャンを実行
	uv run python scripts/security_scan.py --scan-type=all

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

ci-check: quality-check security ## CI 環境での品質チェック
	@echo "CI 品質チェックが完了しました"

release-check: ## リリース前の最終チェック
	@echo "リリース前チェックを実行中..."
	$(MAKE) quality-check
	uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=60
	@echo "リリース前チェックが完了しました"

sbom: ## SBOM (Software Bill of Materials) を生成
	uv run python scripts/security_scan.py --scan-type=sbom

security-strict: ## セキュリティスキャンを実行（問題検出時に失敗）
	uv run python scripts/security_scan.py --scan-type=all --fail-on-issues

bandit: ## bandit セキュリティスキャンのみ実行
	uv run python scripts/security_scan.py --scan-type=bandit

audit: ## pip-audit 脆弱性チェックのみ実行
	uv run python scripts/security_scan.py --scan-type=audit

metrics: ## 品質メトリクスを収集・表示
	uv run python src/quality_metrics.py

metrics-report: ## 品質メトリクスレポートを生成
	@echo "品質メトリクスレポートを生成中..."
	uv run python src/quality_metrics.py
	@echo "品質メトリクスレポートが quality_reports/ に保存されました"

alerts-check: ## 品質アラートをチェック
	uv run python src/quality_alerts.py --check

monthly-report: ## 月次品質レポートを生成
	uv run python src/quality_alerts.py --monthly

quarterly-report: ## 四半期品質レポートを生成
	uv run python src/quality_alerts.py --quarterly

semi-annual-report: ## 半年品質レポートを生成
	uv run python src/quality_alerts.py --semi-annual

quality-dashboard: ## 品質ダッシュボード（メトリクス収集 + アラートチェック）
	@echo "品質ダッシュボードを実行中..."
	uv run python src/quality_metrics.py
	uv run python src/quality_alerts.py --check
	@echo "品質ダッシュボードが完了しました"
