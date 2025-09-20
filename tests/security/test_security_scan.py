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
    def test_run_pip_audit_success(self, mock_subprocess):
        """pip-auditスキャン成功テスト"""
        # 検証対象: SecurityScanner.run_pip_audit()
        # 目的: pip-auditスキャンが正常に実行されることを確認

        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        # テスト用のauditレポートを作成
        audit_report = {
            "vulnerabilities": [
                {
                    "package": "test-package",
                    "vulnerability_id": "CVE-2023-1234",
                    "severity": "HIGH",
                }
            ]
        }

        audit_report_path = self.scanner.reports_dir / "pip_audit_report.json"
        with open(audit_report_path, "w") as f:
            json.dump(audit_report, f)

        result = self.scanner.run_pip_audit()

        assert result["status"] == "success"
        assert result["vulnerabilities_count"] == 1
        assert "pip_audit_report.json" in result["report_path"]

    @patch("subprocess.run")
    def test_run_pip_audit_error(self, mock_subprocess):
        """pip-auditスキャンエラーテスト"""
        # 検証対象: SecurityScanner.run_pip_audit()
        # 目的: pip-auditスキャンでエラーが発生した場合の処理を確認

        mock_subprocess.return_value = MagicMock(returncode=1, stderr="audit error")

        result = self.scanner.run_pip_audit()

        assert result["status"] == "error"
        assert "audit error" in result["message"]

    @patch("subprocess.run")
    def test_generate_sbom_success(self, mock_subprocess):
        """SBOM生成成功テスト"""
        # 検証対象: SecurityScanner.generate_sbom()
        # 目的: SBOMが正常に生成されることを確認

        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        # テスト用のSBOMを作成
        sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "components": [
                {"type": "library", "name": "test-package", "version": "1.0.0"}
            ],
        }

        sbom_report_path = self.scanner.reports_dir / "sbom.json"
        with open(sbom_report_path, "w") as f:
            json.dump(sbom_data, f)

        result = self.scanner.generate_sbom()

        assert result["status"] == "success"
        assert result["components_count"] == 1
        assert "sbom.json" in result["report_path"]

    @patch("subprocess.run")
    def test_generate_sbom_error(self, mock_subprocess):
        """SBOM生成エラーテスト"""
        # 検証対象: SecurityScanner.generate_sbom()
        # 目的: SBOM生成でエラーが発生した場合の処理を確認

        mock_subprocess.return_value = MagicMock(returncode=1, stderr="sbom error")

        result = self.scanner.generate_sbom()

        assert result["status"] == "error"
        assert "sbom error" in result["message"]

    def test_generate_summary_report(self):
        """統合レポート生成テスト"""
        # 検証対象: SecurityScanner.generate_summary_report()
        # 目的: 統合レポートが正常に生成されることを確認

        bandit_result = {"status": "success", "issues_count": 2}
        audit_result = {"status": "success", "vulnerabilities_count": 1}
        sbom_result = {"status": "success", "components_count": 10}

        summary = self.scanner.generate_summary_report(
            bandit_result, audit_result, sbom_result
        )

        assert summary["overall_status"] == "success"
        assert summary["scan_results"]["bandit"] == bandit_result
        assert summary["scan_results"]["pip_audit"] == audit_result
        assert summary["scan_results"]["sbom"] == sbom_result
        assert len(summary["recommendations"]) > 0

        # 統合レポートファイルが作成されることを確認
        summary_path = self.scanner.reports_dir / "security_summary.json"
        assert summary_path.exists()

    def test_generate_summary_report_with_errors(self):
        """エラーありの統合レポート生成テスト"""
        # 検証対象: SecurityScanner.generate_summary_report()
        # 目的: エラーがある場合の統合レポート生成を確認

        bandit_result = {"status": "error", "message": "bandit failed"}
        audit_result = {"status": "success", "vulnerabilities_count": 0}
        sbom_result = {"status": "success", "components_count": 10}

        summary = self.scanner.generate_summary_report(
            bandit_result, audit_result, sbom_result
        )

        assert summary["overall_status"] == "error"

    def test_generate_summary_report_with_warnings(self):
        """警告ありの統合レポート生成テスト"""
        # 検証対象: SecurityScanner.generate_summary_report()
        # 目的: 警告がある場合の統合レポート生成を確認

        bandit_result = {"status": "warning", "message": "bandit warning"}
        audit_result = {"status": "success", "vulnerabilities_count": 0}
        sbom_result = {"status": "success", "components_count": 10}

        summary = self.scanner.generate_summary_report(
            bandit_result, audit_result, sbom_result
        )

        assert summary["overall_status"] == "warning"

    @patch.object(SecurityScanner, "run_bandit_scan")
    @patch.object(SecurityScanner, "run_pip_audit")
    @patch.object(SecurityScanner, "generate_sbom")
    @patch.object(SecurityScanner, "generate_summary_report")
    def test_run_full_scan(self, mock_summary, mock_sbom, mock_audit, mock_bandit):
        """フルスキャン実行テスト"""
        # 検証対象: SecurityScanner.run_full_scan()
        # 目的: フルスキャンが正常に実行されることを確認

        # モックの設定
        mock_bandit.return_value = {"status": "success", "issues_count": 0}
        mock_audit.return_value = {"status": "success", "vulnerabilities_count": 0}
        mock_sbom.return_value = {"status": "success", "components_count": 10}
        mock_summary.return_value = {
            "overall_status": "success",
            "recommendations": ["テストの推奨事項"],
        }

        result = self.scanner.run_full_scan()

        # 各スキャンが呼び出されることを確認
        mock_bandit.assert_called_once()
        mock_audit.assert_called_once()
        mock_sbom.assert_called_once()
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
