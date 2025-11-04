"""
セキュリティスキャンスクリプトのテスト
"""

import json

# テスト対象のモジュールをインポート
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))

from security_scan import SecurityScanner


class TestSecurityScanner:
    """SecurityScannerクラスのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.scanner = SecurityScanner(self.project_root)

    def teardown_method(self):
        """各テストメソッドの後処理"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_run_bandit_scan_success(self, mock_subprocess):
        """banditスキャン成功テスト"""
        # 検証対象: SecurityScanner.run_bandit_scan()
        # 目的: banditスキャンが正常に実行されることを確認

        # モックの設定
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        # テスト用のbanditレポートを作成
        bandit_report = {
            "results": [
                {
                    "filename": "test.py",
                    "issue_severity": "MEDIUM",
                    "issue_text": "Test issue",
                }
            ]
        }

        bandit_report_path = self.scanner.reports_dir / "bandit_report.json"
        with open(bandit_report_path, "w") as f:
            json.dump(bandit_report, f)

        result = self.scanner.run_bandit_scan()

        assert result["status"] == "success"
        assert result["issues_count"] == 1
        assert "bandit_report.json" in result["report_path"]

    @patch("subprocess.run")
    def test_run_bandit_scan_error(self, mock_subprocess):
        """banditスキャンエラーテスト"""
        # 検証対象: SecurityScanner.run_bandit_scan()
        # 目的: banditスキャンでエラーが発生した場合の処理を確認

        mock_subprocess.return_value = MagicMock(returncode=2, stderr="bandit error")

        result = self.scanner.run_bandit_scan()

        assert result["status"] == "error"
        assert "bandit error" in result["message"]

    @patch("subprocess.run")
    def test_run_safety_check_success(self, mock_subprocess):
        """safetyスキャン成功テスト"""
        # 検証対象: SecurityScanner.run_safety_check()
        # 目的: safetyスキャンが正常に実行されることを確認

        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        # テスト用のsafetyレポートを作成
        safety_report = [
            {
                "package": "test-package",
                "vulnerability_id": "CVE-2023-1234",
                "severity": "HIGH",
            }
        ]

        safety_report_path = self.scanner.reports_dir / "safety_report.json"
        with open(safety_report_path, "w") as f:
            json.dump(safety_report, f)

        result = self.scanner.run_safety_check()

        assert result["status"] == "success"
        assert result["vulnerabilities_count"] == 1
        assert "safety_report.json" in result["report_path"]

    @patch("subprocess.run")
    def test_run_safety_check_error(self, mock_subprocess):
        """safetyスキャンエラーテスト"""
        # 検証対象: SecurityScanner.run_safety_check()
        # 目的: safetyスキャンでエラーが発生した場合の処理を確認

        # 終了コード 2 以上でエラーとして処理される
        mock_subprocess.return_value = MagicMock(returncode=2, stderr="safety error")

        result = self.scanner.run_safety_check()

        assert result["status"] == "error"
        assert "safety error" in result["message"]

    def test_generate_summary_report(self):
        """統合レポート生成テスト"""
        # 検証対象: SecurityScanner.generate_summary_report()
        # 目的: 統合レポートが正常に生成されることを確認

        bandit_result = {"status": "success", "issues_count": 2}
        safety_result = {"status": "success", "vulnerabilities_count": 1}

        summary = self.scanner.generate_summary_report(bandit_result, safety_result)

        assert summary["overall_status"] == "success"
        assert summary["scan_results"]["bandit"] == bandit_result
        assert summary["scan_results"]["safety"] == safety_result
        assert len(summary["recommendations"]) > 0

        # 統合レポートファイルが作成されることを確認
        summary_path = self.scanner.reports_dir / "security_summary.json"
        assert summary_path.exists()

    def test_generate_summary_report_with_errors(self):
        """エラーありの統合レポート生成テスト"""
        # 検証対象: SecurityScanner.generate_summary_report()
        # 目的: エラーがある場合の統合レポート生成を確認

        bandit_result = {"status": "error", "message": "bandit failed"}
        safety_result = {"status": "success", "vulnerabilities_count": 0}

        summary = self.scanner.generate_summary_report(bandit_result, safety_result)

        assert summary["overall_status"] == "error"

    def test_generate_summary_report_with_warnings(self):
        """警告ありの統合レポート生成テスト"""
        # 検証対象: SecurityScanner.generate_summary_report()
        # 目的: 警告がある場合の統合レポート生成を確認

        bandit_result = {"status": "warning", "message": "bandit warning"}
        safety_result = {"status": "success", "vulnerabilities_count": 0}

        summary = self.scanner.generate_summary_report(bandit_result, safety_result)

        assert summary["overall_status"] == "warning"

    @patch.object(SecurityScanner, "run_bandit_scan")
    @patch.object(SecurityScanner, "run_safety_check")
    @patch.object(SecurityScanner, "generate_summary_report")
    def test_run_full_scan(self, mock_summary, mock_safety, mock_bandit):
        """フルスキャン実行テスト"""
        # 検証対象: SecurityScanner.run_full_scan()
        # 目的: フルスキャンが正常に実行されることを確認

        # モックの設定
        mock_bandit.return_value = {"status": "success", "issues_count": 0}
        mock_safety.return_value = {
            "status": "success",
            "vulnerabilities_count": 0,
        }
        mock_summary.return_value = {
            "overall_status": "success",
            "recommendations": ["テストの推奨事項"],
        }

        result = self.scanner.run_full_scan()

        # 各スキャンが呼び出されることを確認
        mock_bandit.assert_called_once()
        mock_safety.assert_called_once()
        mock_summary.assert_called_once()

        assert result["overall_status"] == "success"

    def test_reports_directory_creation(self):
        """レポートディレクトリ作成テスト"""
        # 検証対象: SecurityScanner.__init__()
        # 目的: レポートディレクトリが正常に作成されることを確認

        assert self.scanner.reports_dir.exists()
        assert self.scanner.reports_dir.is_dir()
        assert self.scanner.reports_dir.name == "security_reports"

    @patch("subprocess.run")
    def test_file_not_found_error_handling(self, mock_subprocess):
        """FileNotFoundErrorのハンドリングテスト"""
        # 検証対象: SecurityScanner.run_bandit_scan()
        # 目的: コマンドが見つからない場合のエラーハンドリングを確認

        mock_subprocess.side_effect = FileNotFoundError("bandit not found")

        result = self.scanner.run_bandit_scan()

        assert result["status"] == "error"
        assert "bandit が見つかりません" in result["message"]

    @patch("subprocess.run")
    def test_general_exception_handling(self, mock_subprocess):
        """一般的な例外のハンドリングテスト"""
        # 検証対象: SecurityScanner.run_bandit_scan()
        # 目的: 一般的な例外が適切にハンドリングされることを確認

        mock_subprocess.side_effect = Exception("Unexpected error")

        result = self.scanner.run_bandit_scan()

        assert result["status"] == "error"
        assert "Unexpected error" in result["message"]
