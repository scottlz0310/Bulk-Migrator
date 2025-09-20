#!/usr/bin/env python3
"""
セキュリティスキャンスクリプト

このスクリプトは以下のセキュリティチェックを実行します：
1. bandit による Python セキュリティ脆弱性スキャン
2. pip-audit による依存関係の脆弱性チェック
3. SBOM (Software Bill of Materials) の生成
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ロガーの設定
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class SecurityScanner:
    """セキュリティスキャンを実行するクラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "security_reports"
        self.reports_dir.mkdir(exist_ok=True)

    def run_bandit_scan(self) -> dict[str, Any]:
        """bandit によるセキュリティスキャンを実行"""
        logger.info("🔍 bandit セキュリティスキャンを実行中...")

        bandit_report_path = self.reports_dir / "bandit_report.json"

        try:
            # bandit を JSON 形式で実行
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "bandit",
                    "-r",
                    "src/",
                    "-f",
                    "json",
                    "-o",
                    str(bandit_report_path),
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # bandit は脆弱性が見つかった場合に非ゼロの終了コードを返す
            if result.returncode != 0 and result.returncode != 1:
                logger.info(f"❌ bandit 実行エラー: {result.stderr}")
                return {"status": "error", "message": result.stderr}

            # レポートファイルを読み込み
            if bandit_report_path.exists():
                with open(bandit_report_path, encoding="utf-8") as f:
                    bandit_data = json.load(f)

                issues_count = len(bandit_data.get("results", []))
                logger.info(f"✅ bandit スキャン完了: {issues_count} 件の問題を検出")

                return {
                    "status": "success",
                    "issues_count": issues_count,
                    "report_path": str(bandit_report_path),
                    "data": bandit_data,
                }
            else:
                logger.info("⚠️  bandit レポートファイルが生成されませんでした")
                return {
                    "status": "warning",
                    "message": "レポートファイルが生成されませんでした",
                }

        except FileNotFoundError:
            logger.info(
                "❌ bandit が見つかりません。依存関係をインストールしてください。"
            )
            return {"status": "error", "message": "bandit が見つかりません"}
        except Exception as e:
            logger.info(f"❌ bandit 実行中にエラーが発生しました: {e}")
            return {"status": "error", "message": str(e)}

    def run_pip_audit(self) -> dict[str, Any]:
        """pip-audit による依存関係の脆弱性チェックを実行"""
        logger.info("🔍 pip-audit 依存関係脆弱性チェックを実行中...")

        audit_report_path = self.reports_dir / "pip_audit_report.json"

        try:
            # pip-audit を JSON 形式で実行
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "pip-audit",
                    "--format",
                    "json",
                    "--output",
                    str(audit_report_path),
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                logger.info(f"❌ pip-audit 実行エラー: {result.stderr}")
                return {"status": "error", "message": result.stderr}

            # レポートファイルを読み込み
            if audit_report_path.exists():
                with open(audit_report_path, encoding="utf-8") as f:
                    audit_data = json.load(f)

                vulnerabilities_count = len(audit_data.get("vulnerabilities", []))
                logger.info(
                    f"✅ pip-audit チェック完了: {vulnerabilities_count} 件の"
                    "脆弱性を検出"
                )

                return {
                    "status": "success",
                    "vulnerabilities_count": vulnerabilities_count,
                    "report_path": str(audit_report_path),
                    "data": audit_data,
                }
            else:
                logger.info("⚠️  pip-audit レポートファイルが生成されませんでした")
                return {
                    "status": "warning",
                    "message": "レポートファイルが生成されませんでした",
                }

        except FileNotFoundError:
            logger.info(
                "❌ pip-audit が見つかりません。依存関係をインストールしてください。"
            )
            return {"status": "error", "message": "pip-audit が見つかりません"}
        except Exception as e:
            logger.info(f"❌ pip-audit 実行中にエラーが発生しました: {e}")
            return {"status": "error", "message": str(e)}

    def generate_sbom(self) -> dict[str, Any]:
        """SBOM (Software Bill of Materials) を生成"""
        logger.info("📋 SBOM (Software Bill of Materials) を生成中...")

        sbom_report_path = self.reports_dir / "sbom.json"

        try:
            # cyclonedx-bom を使用して SBOM を生成
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "cyclonedx-py",
                    "environment",
                    "--output-format",
                    "json",
                    "--output-file",
                    str(sbom_report_path),
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                logger.info(f"❌ SBOM 生成エラー: {result.stderr}")
                return {"status": "error", "message": result.stderr}

            if sbom_report_path.exists():
                with open(sbom_report_path, encoding="utf-8") as f:
                    sbom_data = json.load(f)

                components_count = len(sbom_data.get("components", []))
                logger.info(
                    f"✅ SBOM 生成完了: {components_count} 個のコンポーネントを記録"
                )

                return {
                    "status": "success",
                    "components_count": components_count,
                    "report_path": str(sbom_report_path),
                    "data": sbom_data,
                }
            else:
                logger.info("⚠️  SBOM ファイルが生成されませんでした")
                return {
                    "status": "warning",
                    "message": "SBOM ファイルが生成されませんでした",
                }

        except FileNotFoundError:
            logger.info(
                "❌ cyclonedx-py が見つかりません。依存関係をインストールしてください。"
            )
            return {"status": "error", "message": "cyclonedx-py が見つかりません"}
        except Exception as e:
            logger.info(f"❌ SBOM 生成中にエラーが発生しました: {e}")
            return {"status": "error", "message": str(e)}

    def generate_summary_report(
        self,
        bandit_result: dict[str, Any],
        audit_result: dict[str, Any],
        sbom_result: dict[str, Any],
    ) -> dict[str, Any]:
        """セキュリティスキャンの統合レポートを生成"""
        logger.info("📊 統合セキュリティレポートを生成中...")

        summary: dict[str, Any] = {
            "scan_timestamp": datetime.now(UTC).isoformat(),
            "project_name": "bulk-migrator",
            "scan_results": {
                "bandit": bandit_result,
                "pip_audit": audit_result,
                "sbom": sbom_result,
            },
            "overall_status": "success",
            "recommendations": [],
        }

        # 全体的なステータスを判定
        if any(
            result.get("status") == "error"
            for result in [bandit_result, audit_result, sbom_result]
        ):
            summary["overall_status"] = "error"
        elif any(
            result.get("status") == "warning"
            for result in [bandit_result, audit_result, sbom_result]
        ):
            summary["overall_status"] = "warning"

        # 推奨事項を生成
        if bandit_result.get("issues_count", 0) > 0:
            summary["recommendations"].append(
                f"bandit で {bandit_result['issues_count']} 件の"
                "セキュリティ問題が検出されました。修正を検討してください。"
            )

        if audit_result.get("vulnerabilities_count", 0) > 0:
            summary["recommendations"].append(
                f"pip-audit で {audit_result['vulnerabilities_count']} 件の"
                "依存関係脆弱性が検出されました。依存関係の更新を検討してください。"
            )

        if not summary["recommendations"]:
            summary["recommendations"].append(
                "セキュリティスキャンで問題は検出されませんでした。"
            )

        # 統合レポートを保存
        summary_report_path = self.reports_dir / "security_summary.json"
        with open(summary_report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 統合レポートを保存しました: {summary_report_path}")

        return summary

    def run_full_scan(self) -> dict[str, Any]:
        """全セキュリティスキャンを実行"""
        logger.info("🚀 セキュリティスキャンを開始します...")
        logger.info(f"📁 レポート保存先: {self.reports_dir}")

        # 各スキャンを実行
        bandit_result = self.run_bandit_scan()
        audit_result = self.run_pip_audit()
        sbom_result = self.generate_sbom()

        # 統合レポートを生成
        summary = self.generate_summary_report(bandit_result, audit_result, sbom_result)

        logger.info("\n" + "=" * 60)
        logger.info("📋 セキュリティスキャン結果サマリー")
        logger.info("=" * 60)
        logger.info(f"全体ステータス: {summary['overall_status']}")
        logger.info(f"bandit 問題数: {bandit_result.get('issues_count', 'N/A')}")
        logger.info(
            f"pip-audit 脆弱性数: {audit_result.get('vulnerabilities_count', 'N/A')}"
        )
        logger.info(
            f"SBOM コンポーネント数: {sbom_result.get('components_count', 'N/A')}"
        )
        logger.info("\n推奨事項:")
        for recommendation in summary["recommendations"]:
            logger.info(f"  • {recommendation}")
        logger.info("=" * 60)

        return summary


def handle_full_scan(scanner, args):
    """全スキャンの処理"""
    summary = scanner.run_full_scan()
    if args.fail_on_issues:
        bandit_issues = summary["scan_results"]["bandit"].get("issues_count", 0)
        audit_vulnerabilities = summary["scan_results"]["pip_audit"].get(
            "vulnerabilities_count", 0
        )
        if bandit_issues > 0 or audit_vulnerabilities > 0:
            logger.info(
                "\n❌ セキュリティ問題が検出されました。終了コード 1 で終了します。"
            )
            sys.exit(1)


def handle_single_scan(scanner, args):
    """単一スキャンの処理"""
    if args.scan_type == "bandit":
        result = scanner.run_bandit_scan()
        if args.fail_on_issues and result.get("issues_count", 0) > 0:
            sys.exit(1)
    elif args.scan_type == "audit":
        result = scanner.run_pip_audit()
        if args.fail_on_issues and result.get("vulnerabilities_count", 0) > 0:
            sys.exit(1)
    elif args.scan_type == "sbom":
        scanner.generate_sbom()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="セキュリティスキャンを実行")
    parser.add_argument(
        "--scan-type",
        choices=["all", "bandit", "audit", "sbom"],
        default="all",
        help="実行するスキャンの種類",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="問題が検出された場合に非ゼロの終了コードで終了",
    )

    args = parser.parse_args()
    project_root = Path(__file__).parent.parent
    scanner = SecurityScanner(project_root)

    try:
        if args.scan_type == "all":
            handle_full_scan(scanner, args)
        else:
            handle_single_scan(scanner, args)

        logger.info("\n✅ セキュリティスキャンが完了しました。")

    except KeyboardInterrupt:
        logger.info("\n⚠️  スキャンが中断されました。")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
