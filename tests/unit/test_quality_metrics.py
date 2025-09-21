"""
品質メトリクス収集システムのテスト
"""

import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.quality_metrics import PhaseProgress, QualityMetrics, QualityMetricsCollector


class TestQualityMetrics:
    """QualityMetrics データクラスのテスト"""

    @pytest.fixture
    def sample_metrics(self):
        """テスト用メトリクスデータ"""
        # 検証対象: QualityMetrics データクラス
        # 目的: テスト用のメトリクスインスタンスを作成
        return QualityMetrics(
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            coverage_percentage=85.5,
            lint_errors=2,
            type_errors=1,
            security_vulnerabilities=0,
            test_count=50,
            failed_tests=1,
        )

    def test_quality_metrics_to_dict(self, sample_metrics):
        """QualityMetrics の辞書変換テスト"""
        # 検証対象: QualityMetrics.to_dict()
        # 目的: メトリクスが正しく辞書形式に変換されることを確認

        result = sample_metrics.to_dict()

        assert result["timestamp"] == "2024-01-01T12:00:00+00:00"
        assert result["coverage"] == 85.5
        assert result["lint_errors"] == 2
        assert result["type_errors"] == 1
        assert result["security_issues"] == 0
        assert result["tests"]["total"] == 50
        assert result["tests"]["failed"] == 1
        assert result["tests"]["success_rate"] == 0.98  # (50-1)/50

    def test_quality_metrics_to_json(self, sample_metrics):
        """QualityMetrics の JSON 変換テスト"""
        # 検証対象: QualityMetrics.to_json()
        # 目的: メトリクスが正しくJSON形式に変換されることを確認

        json_str = sample_metrics.to_json()
        parsed = json.loads(json_str)

        assert parsed["coverage"] == 85.5
        assert parsed["tests"]["success_rate"] == 0.98

    def test_quality_metrics_zero_tests(self):
        """テスト数が0の場合の成功率計算テスト"""
        # 検証対象: QualityMetrics.to_dict() のゼロ除算対応
        # 目的: テスト数が0の場合でもエラーが発生しないことを確認

        metrics = QualityMetrics(
            timestamp=datetime.now(UTC),
            coverage_percentage=0.0,
            lint_errors=0,
            type_errors=0,
            security_vulnerabilities=0,
            test_count=0,
            failed_tests=0,
        )

        result = metrics.to_dict()
        assert result["tests"]["success_rate"] == 0


class TestPhaseProgress:
    """PhaseProgress データクラスのテスト"""

    def test_phase_progress_to_dict(self):
        """PhaseProgress の辞書変換テスト"""
        # 検証対象: PhaseProgress.to_dict()
        # 目的: フェーズ進捗が正しく辞書形式に変換されることを確認

        progress = PhaseProgress(
            phase_name="Phase 5",
            completion_percentage=75.0,
            completed_tasks=["task1", "task2"],
            remaining_tasks=["task3"],
            target_completion_date=datetime(2024, 2, 1, tzinfo=UTC),
            actual_completion_date=None,
        )

        result = progress.to_dict()

        assert result["phase_name"] == "Phase 5"
        assert result["completion_percentage"] == 75.0
        assert result["completed_tasks"] == ["task1", "task2"]
        assert result["remaining_tasks"] == ["task3"]
        assert result["actual_completion_date"] is None


class TestQualityMetricsCollector:
    """QualityMetricsCollector クラスのテスト"""

    @pytest.fixture
    def temp_project_root(self):
        """テスト用の一時プロジェクトルート"""
        # 検証対象: QualityMetricsCollector の初期化
        # 目的: テスト用の一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def collector(self, temp_project_root):
        """テスト用コレクターインスタンス"""
        # 検証対象: QualityMetricsCollector.__init__()
        # 目的: テスト用のコレクターインスタンスを作成
        return QualityMetricsCollector(temp_project_root)

    def test_collector_initialization(self, collector, temp_project_root):
        """コレクターの初期化テスト"""
        # 検証対象: QualityMetricsCollector.__init__()
        # 目的: コレクターが正しく初期化されることを確認

        assert collector.project_root == temp_project_root
        assert collector.metrics_dir.exists()
        assert collector.metrics_dir.name == "quality_reports"

    @patch("subprocess.run")
    def test_collect_coverage_metrics_success(
        self, mock_run, collector, temp_project_root
    ):
        """カバレッジメトリクス収集成功テスト"""
        # 検証対象: QualityMetricsCollector.collect_coverage_metrics()
        # 目的: カバレッジが正常に収集されることを確認

        # subprocess.runのモック設定
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # coverage.jsonファイルを作成
        coverage_file = temp_project_root / "coverage.json"
        coverage_data = {"totals": {"percent_covered": 85.5}}
        with open(coverage_file, "w") as f:
            json.dump(coverage_data, f)

        result = collector.collect_coverage_metrics()

        assert result == 85.5
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_collect_coverage_metrics_failure(self, mock_run, collector):
        """カバレッジメトリクス収集失敗テスト"""
        # 検証対象: QualityMetricsCollector.collect_coverage_metrics()
        # のエラーハンドリング
        # 目的: コマンド実行失敗時に0.0が返されることを確認

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

        result = collector.collect_coverage_metrics()

        assert result == 0.0

    @patch("subprocess.run")
    def test_collect_coverage_metrics_timeout(self, mock_run, collector):
        """カバレッジメトリクス収集タイムアウトテスト"""
        # 検証対象: QualityMetricsCollector.collect_coverage_metrics()
        # のタイムアウト例外処理
        # 目的: タイムアウト時に0.0が返されることを確認

        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 30)

        result = collector.collect_coverage_metrics()

        assert result == 0.0

    @patch("subprocess.run")
    def test_collect_coverage_metrics_subprocess_error(self, mock_run, collector):
        """カバレッジメトリクス収集サブプロセスエラーテスト"""
        # 検証対象: QualityMetricsCollector.collect_coverage_metrics()
        # のサブプロセス例外処理
        # 目的: サブプロセスエラー時に0.0が返されることを確認

        mock_run.side_effect = subprocess.SubprocessError("Process failed")

        result = collector.collect_coverage_metrics()

        assert result == 0.0

    @patch("subprocess.run")
    def test_collect_coverage_metrics_file_not_found(self, mock_run, collector):
        """カバレッジメトリクス収集ファイル未存在テスト"""
        # 検証対象: QualityMetricsCollector.collect_coverage_metrics()
        # のファイル未存在例外処理
        # 目的: ファイル未存在時に0.0が返されることを確認

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = collector.collect_coverage_metrics()

        assert result == 0.0

    @patch("subprocess.run")
    def test_collect_coverage_metrics_json_decode_error(
        self, mock_run, collector, temp_project_root
    ):
        """カバレッジメトリクス収集JSON解析エラーテスト"""
        # 検証対象: QualityMetricsCollector.collect_coverage_metrics()
        # のJSON解析例外処理
        # 目的: JSON解析エラー時に0.0が返されることを確認

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # 不正なJSONファイルを作成
        coverage_file = temp_project_root / "coverage.json"
        with open(coverage_file, "w") as f:
            f.write("invalid json content")

        result = collector.collect_coverage_metrics()

        assert result == 0.0

    @patch("subprocess.run")
    def test_collect_lint_metrics(self, mock_run, collector):
        """リンティングメトリクス収集テスト"""
        # 検証対象: QualityMetricsCollector.collect_lint_metrics()
        # 目的: リンティングエラー数が正常に収集されることを確認

        # ruffの出力をモック
        lint_output = json.dumps(
            [
                {"code": "E501", "message": "line too long"},
                {"code": "F401", "message": "unused import"},
            ]
        )
        mock_run.return_value = MagicMock(returncode=1, stdout=lint_output, stderr="")

        result = collector.collect_lint_metrics()

        assert result == 2

    @patch("subprocess.run")
    def test_collect_lint_metrics_timeout(self, mock_run, collector):
        """リンティングメトリクス収集タイムアウトテスト"""
        # 検証対象: QualityMetricsCollector.collect_lint_metrics()
        # のタイムアウト例外処理
        # 目的: タイムアウト時に0が返されることを確認

        mock_run.side_effect = subprocess.TimeoutExpired("ruff", 30)

        result = collector.collect_lint_metrics()

        assert result == 0

    @patch("subprocess.run")
    def test_collect_lint_metrics_json_error(self, mock_run, collector):
        """リンティングメトリクス収集JSON解析エラーテスト"""
        # 検証対象: QualityMetricsCollector.collect_lint_metrics()
        # のJSON解析例外処理
        # 目的: JSON解析エラー時に0が返されることを確認

        mock_run.return_value = MagicMock(
            returncode=1, stdout="invalid json", stderr=""
        )

        result = collector.collect_lint_metrics()

        assert result == 0

    @patch("subprocess.run")
    def test_collect_type_check_metrics_timeout(self, mock_run, collector):
        """型チェックメトリクス収集タイムアウトテスト"""
        # 検証対象: QualityMetricsCollector.collect_type_check_metrics()
        # のタイムアウト例外処理
        # 目的: タイムアウト時に0が返されることを確認

        mock_run.side_effect = subprocess.TimeoutExpired("mypy", 30)

        result = collector.collect_type_check_metrics()

        assert result == 0

    @patch("subprocess.run")
    def test_collect_security_metrics_timeout(self, mock_run, collector):
        """セキュリティメトリクス収集タイムアウトテスト"""
        # 検証対象: QualityMetricsCollector.collect_security_metrics()
        # のタイムアウト例外処理
        # 目的: タイムアウト時に0が返されることを確認

        mock_run.side_effect = subprocess.TimeoutExpired("bandit", 30)

        result = collector.collect_security_metrics()

        assert result == 0

    @patch("subprocess.run")
    def test_collect_security_metrics_json_error(self, mock_run, collector):
        """セキュリティメトリクス収集JSON解析エラーテスト"""
        # 検証対象: QualityMetricsCollector.collect_security_metrics()
        # のJSON解析例外処理
        # 目的: JSON解析エラー時に0が返されることを確認

        mock_run.return_value = MagicMock(
            returncode=1, stdout="invalid json", stderr=""
        )

        result = collector.collect_security_metrics()

        assert result == 0

    @patch("subprocess.run")
    def test_collect_test_metrics_timeout(self, mock_run, collector):
        """テストメトリクス収集タイムアウトテスト"""
        # 検証対象: QualityMetricsCollector.collect_test_metrics()
        # のタイムアウト例外処理
        # 目的: タイムアウト時に(0, 0)が返されることを確認

        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 30)

        total, failed = collector.collect_test_metrics()

        assert total == 0
        assert failed == 0

    @patch("subprocess.run")
    def test_collect_test_metrics_no_match(self, mock_run, collector):
        """テストメトリクス収集パターン不一致テスト"""
        # 検証対象: QualityMetricsCollector.collect_test_metrics()
        # のパターン不一致処理
        # 目的: パターンが一致しない場合に(0, 0)が返されることを確認

        mock_run.return_value = MagicMock(
            returncode=0, stdout="no test results", stderr=""
        )

        total, failed = collector.collect_test_metrics()

        assert total == 0
        assert failed == 0

    @patch("subprocess.run")
    def test_collect_type_check_metrics(self, mock_run, collector):
        """型チェックメトリクス収集テスト"""
        # 検証対象: QualityMetricsCollector.collect_type_check_metrics()
        # 目的: 型チェックエラー数が正常に収集されることを確認

        # mypyの出力をモック
        mypy_output = (
            "src/test.py:10: error: Incompatible types\n"
            "src/test.py:15: error: Missing return"
        )
        mock_run.return_value = MagicMock(returncode=1, stdout=mypy_output, stderr="")

        result = collector.collect_type_check_metrics()

        assert result == 2

    @patch("subprocess.run")
    def test_collect_security_metrics(self, mock_run, collector):
        """セキュリティメトリクス収集テスト"""
        # 検証対象: QualityMetricsCollector.collect_security_metrics()
        # 目的: セキュリティ脆弱性数が正常に収集されることを確認

        # banditの出力をモック
        bandit_output = json.dumps(
            {
                "results": [
                    {"issue_severity": "HIGH", "issue_text": "Hardcoded password"},
                    {"issue_severity": "MEDIUM", "issue_text": "SQL injection"},
                ]
            }
        )
        mock_run.return_value = MagicMock(returncode=1, stdout=bandit_output, stderr="")

        result = collector.collect_security_metrics()

        assert result == 2

    @patch("subprocess.run")
    def test_collect_test_metrics(self, mock_run, collector):
        """テストメトリクス収集テスト"""
        # 検証対象: QualityMetricsCollector.collect_test_metrics()
        # 目的: テスト数と失敗数が正常に収集されることを確認

        # pytestの出力をモック
        pytest_output = "10 passed, 2 failed in 0.5s"
        mock_run.return_value = MagicMock(returncode=1, stdout=pytest_output, stderr="")

        total, failed = collector.collect_test_metrics()

        assert total == 12  # 10 + 2
        assert failed == 2

    def test_save_and_load_metrics(self, collector):
        """メトリクス保存・読み込みテスト"""
        # 検証対象: QualityMetricsCollector.save_metrics(), load_metrics()
        # 目的: メトリクスが正しく保存・読み込みされることを確認

        metrics = QualityMetrics(
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            coverage_percentage=85.5,
            lint_errors=2,
            type_errors=1,
            security_vulnerabilities=0,
            test_count=50,
            failed_tests=1,
        )

        # 保存
        filepath = collector.save_metrics(metrics, "test_metrics.json")
        assert filepath.exists()

        # 読み込み
        loaded_metrics = collector.load_metrics("test_metrics.json")

        assert loaded_metrics is not None
        assert loaded_metrics.coverage_percentage == 85.5
        assert loaded_metrics.lint_errors == 2
        assert loaded_metrics.timestamp == metrics.timestamp

    def test_compare_metrics_improvement(self, collector):
        """メトリクス比較（改善）テスト"""
        # 検証対象: QualityMetricsCollector.compare_metrics()
        # 目的: メトリクスの改善が正しく検出されることを確認

        previous = QualityMetrics(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            coverage_percentage=80.0,
            lint_errors=5,
            type_errors=3,
            security_vulnerabilities=2,
            test_count=45,
            failed_tests=2,
        )

        current = QualityMetrics(
            timestamp=datetime(2024, 1, 2, tzinfo=UTC),
            coverage_percentage=85.0,
            lint_errors=2,
            type_errors=1,
            security_vulnerabilities=0,
            test_count=50,
            failed_tests=1,
        )

        comparison = collector.compare_metrics(current, previous)

        assert comparison["status"] == "比較完了"
        assert comparison["changes"]["coverage"] == 5.0
        assert comparison["changes"]["lint_errors"] == -3
        assert len(comparison["improvements"]) > 0
        assert comparison["overall_trend"] == "改善"

    def test_compare_metrics_first_time(self, collector):
        """メトリクス比較（初回）テスト"""
        # 検証対象: QualityMetricsCollector.compare_metrics() の初回測定対応
        # 目的: 初回測定時に適切なメッセージが返されることを確認

        current = QualityMetrics(
            timestamp=datetime.now(UTC),
            coverage_percentage=85.0,
            lint_errors=2,
            type_errors=1,
            security_vulnerabilities=0,
            test_count=50,
            failed_tests=1,
        )

        comparison = collector.compare_metrics(current, None)

        assert comparison["status"] == "初回測定"
        assert comparison["changes"] == {}

    @patch.object(QualityMetricsCollector, "collect_coverage_metrics")
    @patch.object(QualityMetricsCollector, "collect_lint_metrics")
    @patch.object(QualityMetricsCollector, "collect_type_check_metrics")
    @patch.object(QualityMetricsCollector, "collect_security_metrics")
    @patch.object(QualityMetricsCollector, "collect_test_metrics")
    def test_collect_all_metrics(
        self, mock_test, mock_security, mock_type, mock_lint, mock_coverage, collector
    ):
        """全メトリクス収集テスト"""
        # 検証対象: QualityMetricsCollector.collect_all_metrics()
        # 目的: 全てのメトリクスが正常に収集されることを確認

        mock_coverage.return_value = 85.0
        mock_lint.return_value = 2
        mock_type.return_value = 1
        mock_security.return_value = 0
        mock_test.return_value = (50, 1)

        metrics = collector.collect_all_metrics()

        assert metrics.coverage_percentage == 85.0
        assert metrics.lint_errors == 2
        assert metrics.type_errors == 1
        assert metrics.security_vulnerabilities == 0
        assert metrics.test_count == 50
        assert metrics.failed_tests == 1
        assert isinstance(metrics.timestamp, datetime)

    def test_load_metrics_file_not_found(self, collector):
        """メトリクス読み込みファイル未存在テスト"""
        # 検証対象: QualityMetricsCollector.load_metrics()
        # のファイル未存在処理
        # 目的: ファイルが存在しない場合にNoneが返されることを確認

        result = collector.load_metrics("nonexistent_file.json")

        assert result is None

    def test_load_metrics_json_error(self, collector, temp_project_root):
        """メトリクス読み込みJSON解析エラーテスト"""
        # 検証対象: QualityMetricsCollector.load_metrics()
        # のJSON解析例外処理
        # 目的: JSON解析エラー時にNoneが返されることを確認

        # 不正なJSONファイルを作成
        metrics_dir = temp_project_root / "quality_reports"
        metrics_dir.mkdir(exist_ok=True)
        invalid_file = metrics_dir / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write("invalid json content")

        result = collector.load_metrics("invalid.json")

        assert result is None

    def test_compare_metrics_degradation(self, collector):
        """メトリクス比較（劣化）テスト"""
        # 検証対象: QualityMetricsCollector.compare_metrics()
        # 目的: メトリクスの劣化が正しく検出されることを確認

        previous = QualityMetrics(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            coverage_percentage=90.0,
            lint_errors=0,
            type_errors=0,
            security_vulnerabilities=0,
            test_count=50,
            failed_tests=0,
        )

        current = QualityMetrics(
            timestamp=datetime(2024, 1, 2, tzinfo=UTC),
            coverage_percentage=75.0,
            lint_errors=5,
            type_errors=3,
            security_vulnerabilities=2,
            test_count=45,
            failed_tests=3,
        )

        comparison = collector.compare_metrics(current, previous)

        assert comparison["status"] == "比較完了"
        assert comparison["changes"]["coverage"] == -15.0
        assert comparison["changes"]["lint_errors"] == 5
        assert len(comparison["regressions"]) > 0
        assert comparison["overall_trend"] == "悪化"
