"""
品質アラートシステムのテスト
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.quality_alerts import (
    QualityAlert,
    QualityAlertSystem,
    QualityThresholds,
    ReviewReport,
)
from src.quality_metrics import QualityMetrics


class TestQualityThresholds:
    """QualityThresholds データクラスのテスト"""

    def test_quality_thresholds_default(self):
        """デフォルト閾値のテスト"""
        # 検証対象: QualityThresholds のデフォルト値
        # 目的: デフォルト閾値が適切に設定されることを確認

        thresholds = QualityThresholds()

        assert thresholds.coverage_minimum == 60.0
        assert thresholds.max_lint_errors == 0
        assert thresholds.max_type_errors == 0
        assert thresholds.max_security_vulnerabilities == 0
        assert thresholds.max_failed_tests == 0

    def test_quality_thresholds_custom(self):
        """カスタム閾値のテスト"""
        # 検証対象: QualityThresholds のカスタム設定
        # 目的: カスタム閾値が正しく設定されることを確認

        thresholds = QualityThresholds(
            coverage_minimum=80.0, max_lint_errors=5, max_type_errors=3
        )

        assert thresholds.coverage_minimum == 80.0
        assert thresholds.max_lint_errors == 5
        assert thresholds.max_type_errors == 3

    def test_quality_thresholds_to_dict(self):
        """閾値の辞書変換テスト"""
        # 検証対象: QualityThresholds.to_dict()
        # 目的: 閾値が正しく辞書形式に変換されることを確認

        thresholds = QualityThresholds(coverage_minimum=75.0)
        result = thresholds.to_dict()

        assert result["coverage_minimum"] == 75.0
        assert "max_lint_errors" in result


class TestQualityAlert:
    """QualityAlert データクラスのテスト"""

    def test_quality_alert_creation(self):
        """アラート作成のテスト"""
        # 検証対象: QualityAlert の作成
        # 目的: アラートが正しく作成されることを確認

        timestamp = datetime.now(UTC)
        alert = QualityAlert(
            alert_type="coverage",
            severity="HIGH",
            message="カバレッジが低下しました",
            current_value=45.0,
            threshold_value=60.0,
            timestamp=timestamp,
        )

        assert alert.alert_type == "coverage"
        assert alert.severity == "HIGH"
        assert alert.current_value == 45.0
        assert alert.threshold_value == 60.0

    def test_quality_alert_to_dict(self):
        """アラートの辞書変換テスト"""
        # 検証対象: QualityAlert.to_dict()
        # 目的: アラートが正しく辞書形式に変換されることを確認

        timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        alert = QualityAlert(
            alert_type="coverage",
            severity="HIGH",
            message="テストメッセージ",
            current_value=45.0,
            threshold_value=60.0,
            timestamp=timestamp,
        )

        result = alert.to_dict()

        assert result["alert_type"] == "coverage"
        assert result["severity"] == "HIGH"
        assert result["timestamp"] == "2024-01-01T12:00:00+00:00"


class TestReviewReport:
    """ReviewReport データクラスのテスト"""

    def test_review_report_creation(self):
        """レビューレポート作成のテスト"""
        # 検証対象: ReviewReport の作成
        # 目的: レビューレポートが正しく作成されることを確認

        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        end_date = datetime(2024, 1, 31, tzinfo=UTC)
        generated_at = datetime.now(UTC)

        report = ReviewReport(
            report_type="monthly",
            period_start=start_date,
            period_end=end_date,
            metrics_summary={"coverage": 85.0},
            trends={"coverage_trend": 5.0},
            recommendations=["テストを追加してください"],
            generated_at=generated_at,
        )

        assert report.report_type == "monthly"
        assert report.metrics_summary["coverage"] == 85.0
        assert len(report.recommendations) == 1

    def test_review_report_to_json(self):
        """レビューレポートのJSON変換テスト"""
        # 検証対象: ReviewReport.to_json()
        # 目的: レビューレポートが正しくJSON形式に変換されることを確認

        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        end_date = datetime(2024, 1, 31, tzinfo=UTC)
        generated_at = datetime(2024, 2, 1, tzinfo=UTC)

        report = ReviewReport(
            report_type="monthly",
            period_start=start_date,
            period_end=end_date,
            metrics_summary={"test": "value"},
            trends={"trend": "up"},
            recommendations=["recommendation"],
            generated_at=generated_at,
        )

        json_str = report.to_json()
        parsed = json.loads(json_str)

        assert parsed["report_type"] == "monthly"
        assert parsed["metrics_summary"]["test"] == "value"


class TestQualityAlertSystem:
    """QualityAlertSystem クラスのテスト"""

    @pytest.fixture
    def temp_project_root(self):
        """テスト用の一時プロジェクトルート"""
        # 検証対象: QualityAlertSystem の初期化
        # 目的: テスト用の一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def alert_system(self, temp_project_root):
        """テスト用アラートシステムインスタンス"""
        # 検証対象: QualityAlertSystem.__init__()
        # 目的: テスト用のアラートシステムインスタンスを作成
        return QualityAlertSystem(temp_project_root)

    def test_alert_system_initialization(self, alert_system, temp_project_root):
        """アラートシステムの初期化テスト"""
        # 検証対象: QualityAlertSystem.__init__()
        # 目的: アラートシステムが正しく初期化されることを確認

        assert alert_system.project_root == temp_project_root
        assert alert_system.alerts_dir.exists()
        assert alert_system.reports_dir.exists()
        assert isinstance(alert_system.thresholds, QualityThresholds)

    def test_check_quality_thresholds_no_alerts(self, alert_system):
        """品質閾値チェック（アラートなし）のテスト"""
        # 検証対象: QualityAlertSystem.check_quality_thresholds()
        # 目的: 閾値内の場合にアラートが生成されないことを確認

        good_metrics = QualityMetrics(
            timestamp=datetime.now(UTC),
            coverage_percentage=85.0,
            lint_errors=0,
            type_errors=0,
            security_vulnerabilities=0,
            test_count=50,
            failed_tests=0,
        )

        alerts = alert_system.check_quality_thresholds(good_metrics)

        assert len(alerts) == 0

    def test_check_quality_thresholds_with_alerts(self, alert_system):
        """品質閾値チェック（アラートあり）のテスト"""
        # 検証対象: QualityAlertSystem.check_quality_thresholds()
        # 目的: 閾値を超えた場合にアラートが生成されることを確認

        bad_metrics = QualityMetrics(
            timestamp=datetime.now(UTC),
            coverage_percentage=45.0,  # 60%未満
            lint_errors=5,  # 0より大きい
            type_errors=3,  # 0より大きい
            security_vulnerabilities=2,  # 0より大きい
            test_count=50,
            failed_tests=1,  # 0より大きい
        )

        alerts = alert_system.check_quality_thresholds(bad_metrics)

        assert len(alerts) == 5  # 全ての閾値を超過

        # アラートタイプの確認
        alert_types = [alert.alert_type for alert in alerts]
        assert "coverage" in alert_types
        assert "lint_errors" in alert_types
        assert "type_errors" in alert_types
        assert "security_vulnerabilities" in alert_types
        assert "failed_tests" in alert_types

    def test_save_alerts(self, alert_system):
        """アラート保存のテスト"""
        # 検証対象: QualityAlertSystem.save_alerts()
        # 目的: アラートが正しくファイルに保存されることを確認

        alerts = [
            QualityAlert(
                alert_type="coverage",
                severity="HIGH",
                message="テストアラート",
                current_value=45.0,
                threshold_value=60.0,
                timestamp=datetime.now(UTC),
            )
        ]

        filepath = alert_system.save_alerts(alerts)

        assert filepath is not None
        assert filepath.exists()

        # ファイル内容の確認
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert data["alert_count"] == 1
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["alert_type"] == "coverage"

    def test_save_alerts_empty(self, alert_system):
        """空のアラート保存のテスト"""
        # 検証対象: QualityAlertSystem.save_alerts() の空リスト処理
        # 目的: 空のアラートリストの場合にNoneが返されることを確認

        result = alert_system.save_alerts([])

        assert result is None

    def test_generate_monthly_report(self, alert_system, temp_project_root):
        """月次レポート生成のテスト"""
        # 検証対象: QualityAlertSystem.generate_monthly_report()
        # 目的: 月次レポートが正しく生成されることを確認

        # テスト用メトリクスファイルを作成
        quality_reports_dir = temp_project_root / "quality_reports"
        quality_reports_dir.mkdir(exist_ok=True)

        test_metrics = {
            "timestamp": "2024-01-15T12:00:00+00:00",
            "coverage": 85.0,
            "lint_errors": 2,
            "type_errors": 1,
            "security_issues": 0,
        }

        with open(
            quality_reports_dir / "quality_metrics_20240115_120000.json", "w"
        ) as f:
            json.dump(test_metrics, f)

        # 2024年1月のレポートを生成
        target_month = datetime(2024, 1, 1, tzinfo=UTC)
        report = alert_system.generate_monthly_report(target_month)

        assert report.report_type == "monthly"
        assert report.period_start.month == 1
        assert report.period_end.month == 1
        assert report.metrics_summary["data_points"] == 1

    def test_create_alert_email_body(self, alert_system):
        """アラートメール本文作成のテスト"""
        # 検証対象: QualityAlertSystem._create_alert_email_body()
        # 目的: アラートメールの本文が正しく作成されることを確認

        alerts = [
            QualityAlert(
                alert_type="coverage",
                severity="HIGH",
                message="カバレッジが低下しました",
                current_value=45.0,
                threshold_value=60.0,
                timestamp=datetime.now(UTC),
            ),
            QualityAlert(
                alert_type="lint_errors",
                severity="MEDIUM",
                message="リンティングエラーが増加しました",
                current_value=5,
                threshold_value=0,
                timestamp=datetime.now(UTC),
            ),
        ]

        body = alert_system._create_alert_email_body(alerts)

        assert "品質アラート通知" in body
        assert "🚨 高重要度アラート:" in body
        assert "⚠️  中重要度アラート:" in body
        assert "カバレッジが低下しました" in body
        assert "リンティングエラーが増加しました" in body

    def test_generate_recommendations(self, alert_system):
        """推奨事項生成のテスト"""
        # 検証対象: QualityAlertSystem._generate_recommendations()
        # 目的: 適切な推奨事項が生成されることを確認

        summary = {
            "coverage": {"latest": 45.0},
            "lint_errors": {"latest": 5},
            "type_errors": {"latest": 0},
            "security_issues": {"latest": 0},
        }

        trends = {"coverage_trend": -5.0, "lint_errors_trend": 3}

        recommendations = alert_system._generate_recommendations(summary, trends)

        assert len(recommendations) > 0
        assert any("カバレッジ" in rec for rec in recommendations)
        assert any("リンティング" in rec for rec in recommendations)

    def test_save_report(self, alert_system):
        """レポート保存のテスト"""
        # 検証対象: QualityAlertSystem.save_report()
        # 目的: レポートが正しくファイルに保存されることを確認

        report = ReviewReport(
            report_type="monthly",
            period_start=datetime(2024, 1, 1, tzinfo=UTC),
            period_end=datetime(2024, 1, 31, tzinfo=UTC),
            metrics_summary={"test": "data"},
            trends={"test": "trend"},
            recommendations=["test recommendation"],
            generated_at=datetime.now(UTC),
        )

        filepath = alert_system.save_report(report)

        assert filepath.exists()
        assert "monthly_report_" in filepath.name

        # ファイル内容の確認
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert data["report_type"] == "monthly"
        assert data["metrics_summary"]["test"] == "data"
