#!/usr/bin/env python3
"""
品質アラートシステム

品質メトリクスが閾値を下回った場合の自動アラート機能と
定期レビュー用のレポート生成機能を提供
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# オプショナルなメール機能のインポート
try:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

try:
    from src.quality_metrics import QualityMetrics, QualityMetricsCollector
except ImportError:
    from quality_metrics import QualityMetrics, QualityMetricsCollector  # type: ignore


@dataclass
class QualityThresholds:
    """品質閾値設定"""

    coverage_minimum: float = 60.0  # staging目標
    max_lint_errors: int = 0
    max_type_errors: int = 0
    max_security_vulnerabilities: int = 0
    max_failed_tests: int = 0

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)


@dataclass
class QualityAlert:
    """品質アラート"""

    alert_type: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    message: str
    current_value: Any
    threshold_value: Any
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ReviewReport:
    """レビューレポート"""

    report_type: str  # "monthly", "quarterly", "semi-annual"
    period_start: datetime
    period_end: datetime
    metrics_summary: dict[str, Any]
    trends: dict[str, Any]
    recommendations: list[str]
    generated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "report_type": self.report_type,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "metrics_summary": self.metrics_summary,
            "trends": self.trends,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat(),
        }

    def to_json(self) -> str:
        """JSON形式に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class QualityAlertSystem:
    """品質アラートシステム"""

    def __init__(
        self,
        project_root: Path | None = None,
        thresholds: QualityThresholds | None = None,
    ):
        self.project_root = project_root or Path.cwd()
        self.thresholds = thresholds or QualityThresholds()
        self.alerts_dir = self.project_root / "quality_reports" / "alerts"
        self.reports_dir = self.project_root / "quality_reports" / "reports"

        # ディレクトリを作成
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.collector = QualityMetricsCollector(project_root)

    def check_quality_thresholds(self, metrics: QualityMetrics) -> list[QualityAlert]:
        """品質閾値をチェックしてアラートを生成"""
        alerts = []

        # カバレッジチェック
        if metrics.coverage_percentage < self.thresholds.coverage_minimum:
            alerts.append(
                QualityAlert(
                    alert_type="coverage",
                    severity="HIGH",
                    message=(
                        f"カバレッジが閾値を下回りました: "
                        f"{metrics.coverage_percentage:.1f}% < "
                        f"{self.thresholds.coverage_minimum}%"
                    ),
                    current_value=metrics.coverage_percentage,
                    threshold_value=self.thresholds.coverage_minimum,
                    timestamp=metrics.timestamp,
                )
            )

        # リンティングエラーチェック
        if metrics.lint_errors > self.thresholds.max_lint_errors:
            alerts.append(
                QualityAlert(
                    alert_type="lint_errors",
                    severity="MEDIUM",
                    message=(
                        f"リンティングエラーが閾値を超えました: "
                        f"{metrics.lint_errors}件 > "
                        f"{self.thresholds.max_lint_errors}件"
                    ),
                    current_value=metrics.lint_errors,
                    threshold_value=self.thresholds.max_lint_errors,
                    timestamp=metrics.timestamp,
                )
            )

        # 型チェックエラーチェック
        if metrics.type_errors > self.thresholds.max_type_errors:
            alerts.append(
                QualityAlert(
                    alert_type="type_errors",
                    severity="MEDIUM",
                    message=(
                        f"型チェックエラーが閾値を超えました: "
                        f"{metrics.type_errors}件 > "
                        f"{self.thresholds.max_type_errors}件"
                    ),
                    current_value=metrics.type_errors,
                    threshold_value=self.thresholds.max_type_errors,
                    timestamp=metrics.timestamp,
                )
            )

        # セキュリティ脆弱性チェック
        if metrics.security_vulnerabilities > self.thresholds.max_security_vulnerabilities:
            alerts.append(
                QualityAlert(
                    alert_type="security_vulnerabilities",
                    severity="HIGH",
                    message=(
                        f"セキュリティ脆弱性が検出されました: "
                        f"{metrics.security_vulnerabilities}件 > "
                        f"{self.thresholds.max_security_vulnerabilities}件"
                    ),
                    current_value=metrics.security_vulnerabilities,
                    threshold_value=self.thresholds.max_security_vulnerabilities,
                    timestamp=metrics.timestamp,
                )
            )

        # テスト失敗チェック
        if metrics.failed_tests > self.thresholds.max_failed_tests:
            alerts.append(
                QualityAlert(
                    alert_type="failed_tests",
                    severity="HIGH",
                    message=(
                        f"テスト失敗が発生しました: {metrics.failed_tests}件 > {self.thresholds.max_failed_tests}件"
                    ),
                    current_value=metrics.failed_tests,
                    threshold_value=self.thresholds.max_failed_tests,
                    timestamp=metrics.timestamp,
                )
            )

        return alerts

    def save_alerts(self, alerts: list[QualityAlert]) -> Path | None:
        """アラートをファイルに保存"""
        if not alerts:
            return None

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"quality_alerts_{timestamp}.json"
        filepath = self.alerts_dir / filename

        alerts_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "alert_count": len(alerts),
            "alerts": [alert.to_dict() for alert in alerts],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(alerts_data, f, ensure_ascii=False, indent=2)

        logger = logging.getLogger(__name__)
        logger.info(f"アラートを保存しました: {filepath}")
        return filepath

    def send_alert_notification(self, alerts: list[QualityAlert], email_config: dict[str, str] | None = None) -> bool:
        """アラート通知を送信（メール）"""
        if not alerts or not email_config or not EMAIL_AVAILABLE:
            if not EMAIL_AVAILABLE:
                logger = logging.getLogger(__name__)
                logger.warning("メール機能が利用できません。アラートはファイルに保存されました。")
            return False

        try:
            # メール内容を作成
            subject = f"品質アラート: {len(alerts)}件の問題が検出されました"
            body = self._create_alert_email_body(alerts)

            # メール送信（実装例 - 実際の設定に応じて調整）
            msg = MIMEMultipart()
            msg["From"] = email_config.get("from_email", "quality-system@example.com")
            msg["To"] = email_config.get("to_email", "dev-team@example.com")
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # SMTP設定（実際の環境に応じて設定）
            if email_config.get("smtp_server"):
                smtp_port = email_config.get("smtp_port", 587)
                if isinstance(smtp_port, str):
                    smtp_port = int(smtp_port)
                with smtplib.SMTP(email_config["smtp_server"], smtp_port) as server:
                    if email_config.get("smtp_username"):
                        server.starttls()
                        server.login(email_config["smtp_username"], email_config["smtp_password"])
                    server.send_message(msg)

                logger = logging.getLogger(__name__)
                logger.info("アラート通知メールを送信しました")
                return True
            else:
                logger = logging.getLogger(__name__)
                logger.warning("メール設定が不完全です。アラートはファイルに保存されました。")
                return False

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"アラート通知の送信に失敗しました: {e}")
            return False

    def _create_alert_email_body(self, alerts: list[QualityAlert]) -> str:
        """アラートメールの本文を作成"""
        body = "品質アラート通知\n"
        body += "=" * 50 + "\n\n"
        body += f"検出時刻: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        body += f"アラート数: {len(alerts)}件\n\n"

        # 重要度別にグループ化
        high_alerts = [a for a in alerts if a.severity == "HIGH"]
        medium_alerts = [a for a in alerts if a.severity == "MEDIUM"]
        low_alerts = [a for a in alerts if a.severity == "LOW"]

        if high_alerts:
            body += "🚨 高重要度アラート:\n"
            for alert in high_alerts:
                body += f"  - {alert.message}\n"
            body += "\n"

        if medium_alerts:
            body += "⚠️  中重要度アラート:\n"
            for alert in medium_alerts:
                body += f"  - {alert.message}\n"
            body += "\n"

        if low_alerts:
            body += "ℹ️  低重要度アラート:\n"
            for alert in low_alerts:
                body += f"  - {alert.message}\n"
            body += "\n"

        body += "詳細は品質レポートを確認してください。\n"
        return body

    def generate_monthly_report(self, target_month: datetime | None = None) -> ReviewReport:
        """月次レビューレポートを生成"""
        if target_month is None:
            target_month = datetime.now(UTC).replace(day=1)

        # 期間設定
        period_start = target_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1) - timedelta(seconds=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1) - timedelta(seconds=1)

        return self._generate_report("monthly", period_start, period_end)

    def generate_quarterly_report(self, target_quarter: tuple[int, int] | None = None) -> ReviewReport:
        """四半期レビューレポートを生成"""
        if target_quarter is None:
            now = datetime.now(UTC)
            quarter = (now.month - 1) // 3 + 1
            target_quarter = (now.year, quarter)

        year, quarter = target_quarter
        start_month = (quarter - 1) * 3 + 1

        period_start = datetime(year, start_month, 1, tzinfo=UTC)
        if start_month + 2 == 12:
            period_end = datetime(year + 1, 1, 1, tzinfo=UTC) - timedelta(seconds=1)
        else:
            period_end = datetime(year, start_month + 3, 1, tzinfo=UTC) - timedelta(seconds=1)

        return self._generate_report("quarterly", period_start, period_end)

    def generate_semi_annual_report(self, target_half: tuple[int, int] | None = None) -> ReviewReport:
        """半年レビューレポートを生成"""
        if target_half is None:
            now = datetime.now(UTC)
            half = 1 if now.month <= 6 else 2
            target_half = (now.year, half)

        year, half = target_half
        start_month = 1 if half == 1 else 7
        end_month = 7 if half == 1 else 1
        end_year = year if half == 1 else year + 1

        period_start = datetime(year, start_month, 1, tzinfo=UTC)
        period_end = datetime(end_year, end_month, 1, tzinfo=UTC) - timedelta(seconds=1)

        return self._generate_report("semi-annual", period_start, period_end)

    def _generate_report(self, report_type: str, period_start: datetime, period_end: datetime) -> ReviewReport:
        """レポートを生成"""
        # メトリクスファイルを収集
        metrics_files = list((self.project_root / "quality_reports").glob("quality_metrics_*.json"))
        period_metrics = []

        for file in metrics_files:
            try:
                with open(file, encoding="utf-8") as f:
                    data = json.load(f)

                timestamp = datetime.fromisoformat(data["timestamp"])
                if period_start <= timestamp <= period_end:
                    period_metrics.append(data)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        # メトリクス集計
        if not period_metrics:
            metrics_summary = {
                "data_points": 0,
                "message": "期間内にデータが見つかりませんでした",
            }
            trends = {}
            recommendations = ["定期的な品質メトリクス収集を開始してください"]
        else:
            metrics_summary = self._calculate_metrics_summary(period_metrics)
            trends = self._calculate_trends(period_metrics)
            recommendations = self._generate_recommendations(metrics_summary, trends)

        return ReviewReport(
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            metrics_summary=metrics_summary,
            trends=trends,
            recommendations=recommendations,
            generated_at=datetime.now(UTC),
        )

    def _calculate_metrics_summary(self, metrics_data: list[dict[str, Any]]) -> dict[str, Any]:
        """メトリクスサマリーを計算"""
        if not metrics_data:
            return {}

        coverages = [m["coverage"] for m in metrics_data]
        lint_errors = [m["lint_errors"] for m in metrics_data]
        type_errors = [m["type_errors"] for m in metrics_data]
        security_issues = [m["security_issues"] for m in metrics_data]

        return {
            "data_points": len(metrics_data),
            "coverage": {
                "average": sum(coverages) / len(coverages),
                "min": min(coverages),
                "max": max(coverages),
                "latest": coverages[-1],
            },
            "lint_errors": {
                "average": sum(lint_errors) / len(lint_errors),
                "min": min(lint_errors),
                "max": max(lint_errors),
                "latest": lint_errors[-1],
            },
            "type_errors": {
                "average": sum(type_errors) / len(type_errors),
                "min": min(type_errors),
                "max": max(type_errors),
                "latest": type_errors[-1],
            },
            "security_issues": {
                "average": sum(security_issues) / len(security_issues),
                "min": min(security_issues),
                "max": max(security_issues),
                "latest": security_issues[-1],
            },
        }

    def _calculate_trends(self, metrics_data: list[dict[str, Any]]) -> dict[str, Any]:
        """トレンドを計算"""
        if len(metrics_data) < 2:
            return {"message": "トレンド分析には最低2つのデータポイントが必要です"}

        first = metrics_data[0]
        last = metrics_data[-1]

        return {
            "coverage_trend": last["coverage"] - first["coverage"],
            "lint_errors_trend": last["lint_errors"] - first["lint_errors"],
            "type_errors_trend": last["type_errors"] - first["type_errors"],
            "security_issues_trend": last["security_issues"] - first["security_issues"],
        }

    def _generate_recommendations(self, summary: dict[str, Any], trends: dict[str, Any]) -> list[str]:
        """推奨事項を生成"""
        recommendations = []

        if "coverage" in summary:
            if summary["coverage"]["latest"] < 60:
                recommendations.append(
                    "カバレッジが目標値（60%）を下回っています。テストケースの追加を検討してください。"
                )

            if trends.get("coverage_trend", 0) < 0:
                recommendations.append("カバレッジが低下傾向にあります。新機能のテスト追加を確認してください。")

        if "lint_errors" in summary and summary["lint_errors"]["latest"] > 0:
            recommendations.append("リンティングエラーが残っています。コード品質の改善を実施してください。")

        if "type_errors" in summary and summary["type_errors"]["latest"] > 0:
            recommendations.append("型チェックエラーが残っています。型ヒントの追加・修正を実施してください。")

        if "security_issues" in summary and summary["security_issues"]["latest"] > 0:
            recommendations.append("セキュリティ問題が検出されています。緊急対応が必要です。")

        if not recommendations:
            recommendations.append("品質指標は良好です。現在の品質レベルを維持してください。")

        return recommendations

    def save_report(self, report: ReviewReport) -> Path:
        """レポートをファイルに保存"""
        timestamp = report.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{report.report_type}_report_{timestamp}.json"
        filepath = self.reports_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report.to_json())

        logger = logging.getLogger(__name__)
        logger.info(f"{report.report_type}レポートを保存しました: {filepath}")
        return filepath


def main():
    """メイン関数 - コマンドライン実行用"""
    import argparse

    parser = argparse.ArgumentParser(description="品質アラートシステム")
    parser.add_argument(
        "--check",
        action="store_true",
        help="現在のメトリクスをチェックしてアラートを生成",
    )
    parser.add_argument("--monthly", action="store_true", help="月次レポートを生成")
    parser.add_argument("--quarterly", action="store_true", help="四半期レポートを生成")
    parser.add_argument("--semi-annual", action="store_true", help="半年レポートを生成")

    args = parser.parse_args()

    alert_system = QualityAlertSystem()

    if args.check:
        # 最新のメトリクスを取得してアラートチェック
        latest_metrics = alert_system.collector.get_latest_metrics()
        if latest_metrics:
            alerts = alert_system.check_quality_thresholds(latest_metrics)
            if alerts:
                alert_system.save_alerts(alerts)
                logger = logging.getLogger(__name__)
                logger.info(f"{len(alerts)}件のアラートが生成されました")
            else:
                logger = logging.getLogger(__name__)
                logger.info("品質閾値内です。アラートはありません。")
        else:
            logger = logging.getLogger(__name__)
            logger.warning("メトリクスデータが見つかりません。先に品質メトリクスを収集してください。")

    if args.monthly:
        report = alert_system.generate_monthly_report()
        alert_system.save_report(report)

    if args.quarterly:
        report = alert_system.generate_quarterly_report()
        alert_system.save_report(report)

    if args.semi_annual:
        report = alert_system.generate_semi_annual_report()
        alert_system.save_report(report)

    if not any([args.check, args.monthly, args.quarterly, args.semi_annual]):
        logger = logging.getLogger(__name__)
        logger.info("使用方法: python src/quality_alerts.py [--check] [--monthly] [--quarterly] [--semi-annual]")


if __name__ == "__main__":
    main()
