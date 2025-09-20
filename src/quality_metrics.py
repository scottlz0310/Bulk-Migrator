#!/usr/bin/env python3
"""
品質メトリクス収集システム

カバレッジ、リンティングエラー、セキュリティ脆弱性の自動収集機能を提供
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class QualityMetrics:
    """品質メトリクス データクラス"""

    timestamp: datetime
    coverage_percentage: float
    lint_errors: int
    type_errors: int
    security_vulnerabilities: int
    test_count: int
    failed_tests: int

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "coverage": self.coverage_percentage,
            "lint_errors": self.lint_errors,
            "type_errors": self.type_errors,
            "security_issues": self.security_vulnerabilities,
            "tests": {
                "total": self.test_count,
                "failed": self.failed_tests,
                "success_rate": (self.test_count - self.failed_tests) / self.test_count
                if self.test_count > 0
                else 0,
            },
        }

    def to_json(self) -> str:
        """JSON形式に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class PhaseProgress:
    """フェーズ進捗 データクラス"""

    phase_name: str
    completion_percentage: float
    completed_tasks: list[str]
    remaining_tasks: list[str]
    target_completion_date: datetime
    actual_completion_date: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "phase_name": self.phase_name,
            "completion_percentage": self.completion_percentage,
            "completed_tasks": self.completed_tasks,
            "remaining_tasks": self.remaining_tasks,
            "target_completion_date": self.target_completion_date.isoformat(),
            "actual_completion_date": self.actual_completion_date.isoformat()
            if self.actual_completion_date
            else None,
        }


class QualityMetricsCollector:
    """品質メトリクス収集クラス"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.metrics_dir = self.project_root / "quality_reports"
        self.metrics_dir.mkdir(exist_ok=True)

    def collect_coverage_metrics(self) -> float:
        """カバレッジメトリクスを収集"""
        try:
            # pytest-covを実行してカバレッジを取得
            result = subprocess.run(
                ["uv", "run", "pytest", "--cov=src", "--cov-report=json", "--quiet"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                # coverage.jsonファイルからカバレッジを読み取り
                coverage_file = self.project_root / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                    return coverage_data.get("totals", {}).get("percent_covered", 0.0)

            return 0.0
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
            json.JSONDecodeError,
        ):
            return 0.0

    def collect_lint_metrics(self) -> int:
        """リンティングエラー数を収集"""
        try:
            # ruffを実行してエラー数を取得
            result = subprocess.run(
                ["uv", "run", "ruff", "check", ".", "--output-format=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                lint_results = json.loads(result.stdout)
                return len(lint_results)

            return 0
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
            json.JSONDecodeError,
        ):
            return 0

    def collect_type_check_metrics(self) -> int:
        """型チェックエラー数を収集"""
        try:
            # mypyを実行してエラー数を取得
            result = subprocess.run(
                ["uv", "run", "mypy", ".", "--no-error-summary"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # mypyのエラー出力から行数をカウント
            if result.stdout:
                error_lines = [
                    line
                    for line in result.stdout.split("\n")
                    if line.strip() and ":" in line
                ]
                return len(error_lines)

            return 0
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ):
            return 0

    def collect_security_metrics(self) -> int:
        """セキュリティ脆弱性数を収集"""
        try:
            # banditを実行してセキュリティ問題を取得
            result = subprocess.run(
                ["uv", "run", "bandit", "-r", "src", "-f", "json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.stdout:
                bandit_results = json.loads(result.stdout)
                return len(bandit_results.get("results", []))

            return 0
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
            json.JSONDecodeError,
        ):
            return 0

    def collect_test_metrics(self) -> tuple[int, int]:
        """テストメトリクス（総数、失敗数）を収集"""
        try:
            # pytestを実行してテスト結果を取得
            result = subprocess.run(
                ["uv", "run", "pytest", "--tb=no", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # pytest出力からテスト数を解析
            output = result.stdout
            if "passed" in output or "failed" in output:
                # 例: "10 passed, 2 failed in 0.5s" のような出力を解析
                import re

                passed_match = re.search(r"(\d+) passed", output)
                failed_match = re.search(r"(\d+) failed", output)

                passed = int(passed_match.group(1)) if passed_match else 0
                failed = int(failed_match.group(1)) if failed_match else 0

                return passed + failed, failed

            return 0, 0
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ):
            return 0, 0

    def collect_all_metrics(self) -> QualityMetrics:
        """全ての品質メトリクスを収集"""
        print("品質メトリクスを収集中...")

        coverage = self.collect_coverage_metrics()
        print(f"カバレッジ: {coverage:.1f}%")

        lint_errors = self.collect_lint_metrics()
        print(f"リンティングエラー: {lint_errors}件")

        type_errors = self.collect_type_check_metrics()
        print(f"型チェックエラー: {type_errors}件")

        security_vulnerabilities = self.collect_security_metrics()
        print(f"セキュリティ脆弱性: {security_vulnerabilities}件")

        test_count, failed_tests = self.collect_test_metrics()
        print(f"テスト: {test_count}件中{failed_tests}件失敗")

        metrics = QualityMetrics(
            timestamp=datetime.now(UTC),
            coverage_percentage=coverage,
            lint_errors=lint_errors,
            type_errors=type_errors,
            security_vulnerabilities=security_vulnerabilities,
            test_count=test_count,
            failed_tests=failed_tests,
        )

        return metrics

    def save_metrics(
        self, metrics: QualityMetrics, filename: str | None = None
    ) -> Path:
        """メトリクスをファイルに保存"""
        if filename is None:
            timestamp = metrics.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"quality_metrics_{timestamp}.json"

        filepath = self.metrics_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(metrics.to_json())

        print(f"品質メトリクスを保存しました: {filepath}")
        return filepath

    def load_metrics(self, filename: str) -> QualityMetrics | None:
        """保存されたメトリクスを読み込み"""
        filepath = self.metrics_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            return QualityMetrics(
                timestamp=datetime.fromisoformat(data["timestamp"]),
                coverage_percentage=data["coverage"],
                lint_errors=data["lint_errors"],
                type_errors=data["type_errors"],
                security_vulnerabilities=data["security_issues"],
                test_count=data["tests"]["total"],
                failed_tests=data["tests"]["failed"],
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def get_latest_metrics(self) -> QualityMetrics | None:
        """最新のメトリクスを取得"""
        metrics_files = list(self.metrics_dir.glob("quality_metrics_*.json"))

        if not metrics_files:
            return None

        # ファイル名でソートして最新を取得
        latest_file = sorted(metrics_files)[-1]
        return self.load_metrics(latest_file.name)

    def compare_metrics(
        self, current: QualityMetrics, previous: QualityMetrics | None
    ) -> dict[str, Any]:
        """メトリクスの比較結果を生成"""
        if previous is None:
            return {"status": "初回測定", "changes": {}}

        changes = {
            "coverage": current.coverage_percentage - previous.coverage_percentage,
            "lint_errors": current.lint_errors - previous.lint_errors,
            "type_errors": current.type_errors - previous.type_errors,
            "security_vulnerabilities": current.security_vulnerabilities
            - previous.security_vulnerabilities,
            "test_count": current.test_count - previous.test_count,
            "failed_tests": current.failed_tests - previous.failed_tests,
        }

        # 改善/悪化の判定
        improvements = []
        regressions = []

        if changes["coverage"] > 0:
            improvements.append(f"カバレッジが{changes['coverage']:.1f}%向上")
        elif changes["coverage"] < 0:
            regressions.append(f"カバレッジが{abs(changes['coverage']):.1f}%低下")

        if changes["lint_errors"] < 0:
            improvements.append(
                f"リンティングエラーが{abs(changes['lint_errors'])}件減少"
            )
        elif changes["lint_errors"] > 0:
            regressions.append(f"リンティングエラーが{changes['lint_errors']}件増加")

        if changes["type_errors"] < 0:
            improvements.append(
                f"型チェックエラーが{abs(changes['type_errors'])}件減少"
            )
        elif changes["type_errors"] > 0:
            regressions.append(f"型チェックエラーが{changes['type_errors']}件増加")

        if changes["security_vulnerabilities"] < 0:
            improvements.append(
                f"セキュリティ脆弱性が{abs(changes['security_vulnerabilities'])}件減少"
            )
        elif changes["security_vulnerabilities"] > 0:
            regressions.append(
                f"セキュリティ脆弱性が{changes['security_vulnerabilities']}件増加"
            )

        return {
            "status": "比較完了",
            "changes": changes,
            "improvements": improvements,
            "regressions": regressions,
            "overall_trend": "改善"
            if len(improvements) > len(regressions)
            else "悪化"
            if len(regressions) > len(improvements)
            else "変化なし",
        }


def main():
    """メイン関数 - コマンドライン実行用"""
    collector = QualityMetricsCollector()

    # 現在のメトリクスを収集
    current_metrics = collector.collect_all_metrics()

    # 前回のメトリクスと比較
    previous_metrics = collector.get_latest_metrics()
    comparison = collector.compare_metrics(current_metrics, previous_metrics)

    # 結果を保存
    filepath = collector.save_metrics(current_metrics)

    # 結果を表示
    print("\n=== 品質メトリクス レポート ===")
    print(f"測定日時: {current_metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"カバレッジ: {current_metrics.coverage_percentage:.1f}%")
    print(f"リンティングエラー: {current_metrics.lint_errors}件")
    print(f"型チェックエラー: {current_metrics.type_errors}件")
    print(f"セキュリティ脆弱性: {current_metrics.security_vulnerabilities}件")
    print(
        f"テスト: {current_metrics.test_count}件中{current_metrics.failed_tests}件失敗"
    )

    if comparison.get("improvements"):
        print("\n改善点:")
        for improvement in comparison["improvements"]:
            print(f"  ✅ {improvement}")

    if comparison.get("regressions"):
        print("\n悪化点:")
        for regression in comparison["regressions"]:
            print(f"  ❌ {regression}")

    if "overall_trend" in comparison:
        print(f"\n全体的な傾向: {comparison['overall_trend']}")
    else:
        print(f"\n状態: {comparison['status']}")
    print(f"レポート保存先: {filepath}")


if __name__ == "__main__":
    main()
