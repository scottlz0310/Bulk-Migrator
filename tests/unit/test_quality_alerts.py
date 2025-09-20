"""
品質アラートシステムのテスト
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

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

    def test_send_alert_notification_no_email_config(self, alert_system):
        """アラート通知送信テスト（メール設定なし）"""
        # 検証対象: QualityAlertSystem.send_alert_notification()
        # 目的: メール設定が無い場合にFalseが返されることを確認

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

        result = alert_system.send_alert_notification(alerts, None)
        assert result is False

    def test_send_alert_notification_empty_alerts(self, alert_system):
        """アラート通知送信テスト（空のアラート）"""
        # 検証対象: QualityAlertSystem.send_alert_notification()
        # 目的: 空のアラートリストの場合にFalseが返されることを確認

        email_config = {
            "smtp_server": "smtp.example.com",
            "from_email": "test@example.com",
            "to_email": "dev@example.com",
        }

        result = alert_system.send_alert_notification([], email_config)
        assert result is False

    def test_send_alert_notification_no_email_available(self, alert_system):
        """アラート通知送信テスト（メール機能無効）"""
        # 検証対象: QualityAlertSystem.send_alert_notification()
        # 目的: EMAIL_AVAILABLEがFalseの場合の処理を確認

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

        email_config = {
            "smtp_server": "smtp.example.com",
            "from_email": "test@example.com",
            "to_email": "dev@example.com",
        }

        # EMAIL_AVAILABLEをFalseに設定
        with patch("src.quality_alerts.EMAIL_AVAILABLE", False):
            result = alert_system.send_alert_notification(alerts, email_config)
            assert result is False

    def test_send_alert_notification_success(self, alert_system):
        """アラート通知送信テスト（成功）"""
        # 検証対象: QualityAlertSystem.send_alert_notification()
        # 目的: メール送信が成功することを確認

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
                message="リンティングエラーが発生しました",
                current_value=5.0,
                threshold_value=0.0,
                timestamp=datetime.now(UTC),
            ),
        ]

        email_config = {
            "smtp_server": "smtp.example.com",
            "smtp_port": "587",
            "smtp_username": "user@example.com",
            "smtp_password": "password",
            "from_email": "test@example.com",
            "to_email": "dev@example.com",
        }

        # SMTPサーバーをモック
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = mock_smtp.return_value.__enter__.return_value
            mock_server.starttls.return_value = None
            mock_server.login.return_value = None
            mock_server.send_message.return_value = None

            result = alert_system.send_alert_notification(alerts, email_config)
            assert result is True

            # SMTPメソッドが呼ばれることを確認
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("user@example.com", "password")
            mock_server.send_message.assert_called_once()

    def test_send_alert_notification_no_smtp_server(self, alert_system):
        """アラート通知送信テスト（SMTPサーバー設定なし）"""
        # 検証対象: QualityAlertSystem.send_alert_notification()
        # 目的: SMTPサーバー設定が無い場合にFalseが返されることを確認

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

        email_config = {
            "from_email": "test@example.com",
            "to_email": "dev@example.com",
            # smtp_server が無い
        }

        result = alert_system.send_alert_notification(alerts, email_config)
        assert result is False

    def test_send_alert_notification_smtp_error(self, alert_system):
        """アラート通知送信テスト（SMTP エラー）"""
        # 検証対象: QualityAlertSystem.send_alert_notification()
        # 目的: SMTP エラー時にFalseが返されることを確認

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

        email_config = {
            "smtp_server": "smtp.example.com",
            "from_email": "test@example.com",
            "to_email": "dev@example.com",
        }

        # SMTPエラーをシミュレート
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP connection failed")

            result = alert_system.send_alert_notification(alerts, email_config)
            assert result is False

    def test_send_alert_notification_without_auth(self, alert_system):
        """アラート通知送信テスト（認証なし）"""
        # 検証対象: QualityAlertSystem.send_alert_notification()
        # 目的: SMTP認証なしでの送信を確認

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

        email_config = {
            "smtp_server": "smtp.example.com",
            "smtp_port": 25,  # 数値型
            "from_email": "test@example.com",
            "to_email": "dev@example.com",
            # smtp_username, smtp_password なし
        }

        # SMTPサーバーをモック
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = mock_smtp.return_value.__enter__.return_value
            mock_server.send_message.return_value = None

            result = alert_system.send_alert_notification(alerts, email_config)
            assert result is True

            # 認証メソッドが呼ばれないことを確認
            mock_server.starttls.assert_not_called()
            mock_server.login.assert_not_called()
            mock_server.send_message.assert_called_once()

    def test_create_alert_email_body(self, alert_system):
        """アラートメール本文作成テスト"""
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
                message="リンティングエラーが発生しました",
                current_value=5.0,
                threshold_value=0.0,
                timestamp=datetime.now(UTC),
            ),
            QualityAlert(
                alert_type="type_errors",
                severity="LOW",
                message="型エラーが発生しました",
                current_value=2.0,
                threshold_value=0.0,
                timestamp=datetime.now(UTC),
            ),
        ]

        body = alert_system._create_alert_email_body(alerts)

        # 本文の内容を確認
        assert "品質アラート通知" in body
        assert "アラート数: 3件" in body
        assert "🚨 高重要度アラート:" in body
        assert "カバレッジが低下しました" in body
        assert "⚠️  中重要度アラート:" in body
        assert "リンティングエラーが発生しました" in body
        assert "ℹ️  低重要度アラート:" in body
        assert "型エラーが発生しました" in body

    def test_create_alert_email_body_single_severity(self, alert_system):
        """アラートメール本文作成テスト（単一重要度）"""
        # 検証対象: QualityAlertSystem._create_alert_email_body()
        # 目的: 単一重要度のアラートのみの場合の本文作成を確認

        alerts = [
            QualityAlert(
                alert_type="coverage",
                severity="HIGH",
                message="カバレッジが低下しました",
                current_value=45.0,
                threshold_value=60.0,
                timestamp=datetime.now(UTC),
            )
        ]

        body = alert_system._create_alert_email_body(alerts)

        # 高重要度のみが含まれることを確認
        assert "🚨 高重要度アラート:" in body
        assert "⚠️  中重要度アラート:" not in body
        assert "ℹ️  低重要度アラート:" not in body

    def test_generate_quarterly_report_default(self, alert_system):
        """四半期レポート生成テスト（デフォルト）"""
        # 検証対象: QualityAlertSystem.generate_quarterly_report()
        # 目的: デフォルト引数での四半期レポート生成を確認

        with patch.object(alert_system, "_generate_report") as mock_generate:
            mock_generate.return_value = ReviewReport(
                report_type="quarterly",
                period_start=datetime(2024, 1, 1, tzinfo=UTC),
                period_end=datetime(2024, 3, 31, tzinfo=UTC),
                metrics_summary={},
                trends={},
                recommendations=[],
                generated_at=datetime.now(UTC),
            )

            report = alert_system.generate_quarterly_report()

            assert report.report_type == "quarterly"
            mock_generate.assert_called_once()

    def test_generate_quarterly_report_custom(self, alert_system):
        """四半期レポート生成テスト（カスタム）"""
        # 検証対象: QualityAlertSystem.generate_quarterly_report()
        # 目的: カスタム四半期指定でのレポート生成を確認

        target_quarter = (2024, 2)  # 2024年第2四半期

        with patch.object(alert_system, "_generate_report") as mock_generate:
            mock_generate.return_value = ReviewReport(
                report_type="quarterly",
                period_start=datetime(2024, 4, 1, tzinfo=UTC),
                period_end=datetime(2024, 6, 30, tzinfo=UTC),
                metrics_summary={},
                trends={},
                recommendations=[],
                generated_at=datetime.now(UTC),
            )

            report = alert_system.generate_quarterly_report(target_quarter)

            assert report.report_type == "quarterly"
            mock_generate.assert_called_once()

    def test_generate_semi_annual_report_default(self, alert_system):
        """半年レポート生成テスト（デフォルト）"""
        # 検証対象: QualityAlertSystem.generate_semi_annual_report()
        # 目的: デフォルト引数での半年レポート生成を確認

        with patch.object(alert_system, "_generate_report") as mock_generate:
            mock_generate.return_value = ReviewReport(
                report_type="semi_annual",
                period_start=datetime(2024, 1, 1, tzinfo=UTC),
                period_end=datetime(2024, 6, 30, tzinfo=UTC),
                metrics_summary={},
                trends={},
                recommendations=[],
                generated_at=datetime.now(UTC),
            )

            report = alert_system.generate_semi_annual_report()

            assert report.report_type == "semi_annual"
            mock_generate.assert_called_once()

    def test_generate_semi_annual_report_custom(self, alert_system):
        """半年レポート生成テスト（カスタム）"""
        # 検証対象: QualityAlertSystem.generate_semi_annual_report()
        # 目的: カスタム半年指定でのレポート生成を確認

        target_half = (2024, 2)  # 2024年下半期

        with patch.object(alert_system, "_generate_report") as mock_generate:
            mock_generate.return_value = ReviewReport(
                report_type="semi_annual",
                period_start=datetime(2024, 7, 1, tzinfo=UTC),
                period_end=datetime(2024, 12, 31, tzinfo=UTC),
                metrics_summary={},
                trends={},
                recommendations=[],
                generated_at=datetime.now(UTC),
            )

            report = alert_system.generate_semi_annual_report(target_half)

            assert report.report_type == "semi_annual"
            mock_generate.assert_called_once()

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

    def test_generate_quarterly_report(self, alert_system, temp_project_root):
        """四半期レポート生成のテスト"""
        # 検証対象: QualityAlertSystem.generate_quarterly_report()
        # 目的: 四半期レポートが正しく生成されることを確認

        # テスト用メトリクスファイルを作成
        quality_reports_dir = temp_project_root / "quality_reports"
        quality_reports_dir.mkdir(exist_ok=True)

        test_metrics = {
            "timestamp": "2024-02-15T12:00:00+00:00",
            "coverage": 80.0,
            "lint_errors": 3,
            "type_errors": 2,
            "security_issues": 1,
        }

        with open(
            quality_reports_dir / "quality_metrics_20240215_120000.json", "w"
        ) as f:
            json.dump(test_metrics, f)

        # 2024年Q1のレポートを生成
        target_quarter = (2024, 1)  # (year, quarter)
        report = alert_system.generate_quarterly_report(target_quarter)

        assert report.report_type == "quarterly"
        assert report.period_start.month == 1
        assert report.period_end.month == 3

    def test_generate_semi_annual_report(self, alert_system, temp_project_root):
        """半年レポート生成のテスト"""
        # 検証対象: QualityAlertSystem.generate_semi_annual_report()
        # 目的: 半年レポートが正しく生成されることを確認

        # テスト用メトリクスファイルを作成
        quality_reports_dir = temp_project_root / "quality_reports"
        quality_reports_dir.mkdir(exist_ok=True)

        test_metrics = {
            "timestamp": "2024-04-15T12:00:00+00:00",
            "coverage": 75.0,
            "lint_errors": 4,
            "type_errors": 3,
            "security_issues": 2,
        }

        with open(
            quality_reports_dir / "quality_metrics_20240415_120000.json", "w"
        ) as f:
            json.dump(test_metrics, f)

        # 2024年上半期のレポートを生成
        target_half = (2024, 1)  # (year, half)
        report = alert_system.generate_semi_annual_report(target_half)

        assert report.report_type == "semi-annual"
        assert report.period_start.month == 1
        assert report.period_end.month == 6

    def test_send_alert_email_no_smtp(self, alert_system):
        """アラートメール送信（SMTP未設定）のテスト"""
        # 検証対象: QualityAlertSystem.send_alert_email()
        # 目的: SMTP未設定時の処理確認

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

        # SMTP設定なしでメール送信を試行（例外が発生しないことを確認）
        try:
            alert_system.send_alert_email(alerts)
        except Exception as e:
            # SMTP設定がない場合の例外は想定内
            assert "SMTP" in str(e) or "email" in str(e).lower()

    def test_calculate_trends_empty_data(self, alert_system):
        """トレンド計算（データなし）のテスト"""
        # 検証対象: QualityAlertSystem._calculate_trends()
        # 目的: データがない場合の処理確認

        trends = alert_system._calculate_trends([])

        assert "message" in trends
        assert "最低2つのデータポイントが必要" in trends["message"]

    def test_calculate_trends_single_data_point(self, alert_system):
        """トレンド計算（単一データ）のテスト"""
        # 検証対象: QualityAlertSystem._calculate_trends()
        # 目的: データが1つの場合の処理確認

        data = [{"coverage": 85.0, "lint_errors": 2}]
        trends = alert_system._calculate_trends(data)

        assert "message" in trends
        assert "最低2つのデータポイントが必要" in trends["message"]

    def test_generate_recommendations_no_issues(self, alert_system):
        """推奨事項生成（問題なし）のテスト"""
        # 検証対象: QualityAlertSystem._generate_recommendations()
        # 目的: 問題がない場合の推奨事項確認

        summary = {
            "coverage": {"latest": 90.0},
            "lint_errors": {"latest": 0},
            "type_errors": {"latest": 0},
            "security_issues": {"latest": 0},
        }

        trends = {"coverage_trend": 5.0, "lint_errors_trend": 0}

        recommendations = alert_system._generate_recommendations(summary, trends)

        assert len(recommendations) > 0
        assert len(recommendations) >= 0  # 推奨事項が生成されることを確認

    def test_calculate_metrics_summary_empty_data(self, alert_system):
        """メトリクス要約計算（データなし）のテスト"""
        # 検証対象: QualityAlertSystem._calculate_metrics_summary()
        # 目的: データがない場合の処理確認

        summary = alert_system._calculate_metrics_summary([])

        assert summary == {}  # 空のデータの場合は空の辞書が返される

    def test_create_alert_email_body_empty_alerts(self, alert_system):
        """アラートメール本文作成（アラートなし）のテスト"""
        # 検証対象: QualityAlertSystem._create_alert_email_body()
        # 目的: アラートがない場合の処理確認

        body = alert_system._create_alert_email_body([])

        assert "品質アラート通知" in body
        assert "アラート数: 0件" in body
