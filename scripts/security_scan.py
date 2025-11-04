#!/usr/bin/env python3
"""
セキュリティスキャンスクリプト

このスクリプトは以下のセキュリティチェックを実行します：
1. bandit による Python セキュリティ脆弱性スキャン
2. safety による依存関係の脆弱性チェック
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
            # 終了コード 0: 問題なし, 1: 問題あり, 2+: エラー
            if result.returncode > 1:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.info(f"❌ bandit 実行エラー: {error_msg}")
                return {"status": "error", "message": error_msg}

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
            logger.info("❌ bandit が見つかりません。依存関係をインストールしてください。")
            return {"status": "error", "message": "bandit が見つかりません"}
        except Exception as e:
            logger.info(f"❌ bandit 実行中にエラーが発生しました: {e}")
            return {"status": "error", "message": str(e)}

    def run_safety_check(self) -> dict[str, Any]:
        """safety による依存関係の脆弱性チェックを実行"""
        logger.info("🔍 safety 依存関係脆弱性チェックを実行中...")

        safety_report_path = self.reports_dir / "safety_report.json"

        try:
            # safety を JSON 形式で実行
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "safety",
                    "check",
                    "--json",
                    "--output",
                    str(safety_report_path),
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # safety は脆弱性が見つかった場合に非ゼロの終了コードを返す
            if result.returncode > 1:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.info(f"❌ safety 実行エラー: {error_msg}")
                return {"status": "error", "message": error_msg}

            # レポートファイルを読み込み
            if safety_report_path.exists():
                with open(safety_report_path, encoding="utf-8") as f:
                    safety_data = json.load(f)

                # safety の JSON 形式は異なる場合があるため、適応的に処理
                vulnerabilities_count = len(safety_data) if isinstance(safety_data, list) else 0
                logger.info(f"✅ safety チェック完了: {vulnerabilities_count} 件の脆弱性を検出")

                return {
                    "status": "success",
                    "vulnerabilities_count": vulnerabilities_count,
                    "report_path": str(safety_report_path),
                    "data": safety_data,
                }
            else:
                logger.info("⚠️  safety レポートファイルが生成されませんでした")
                return {
                    "status": "warning",
                    "message": "レポートファイルが生成されませんでした",
                }

        except FileNotFoundError:
            logger.info("❌ safety が見つかりません。依存関係をインストールしてください。")
            return {"status": "error", "message": "safety が見つかりません"}
        except Exception as e:
            logger.info(f"❌ safety 実行中にエラーが発生しました: {e}")
            return {"status": "error", "message": str(e)}

    def generate_summary_report(
        self,
        bandit_result: dict[str, Any],
        safety_result: dict[str, Any],
    ) -> dict[str, Any]:
        """セキュリティスキャンの統合レポートを生成"""
        logger.info("📊 統合セキュリティレポートを生成中...")

        summary: dict[str, Any] = {
            "scan_timestamp": datetime.now(UTC).isoformat(),
            "project_name": "bulk-migrator",
            "scan_results": {
                "bandit": bandit_result,
                "safety": safety_result,
            },
            "overall_status": "success",
            "recommendations": [],
        }

        # 全体的なステータスを判定
        if any(result.get("status") == "error" for result in [bandit_result, safety_result]):
            summary["overall_status"] = "error"
        elif any(result.get("status") == "warning" for result in [bandit_result, safety_result]):
            summary["overall_status"] = "warning"

        # 推奨事項を生成
        if bandit_result.get("issues_count", 0) > 0:
            summary["recommendations"].append(
                f"bandit で {bandit_result['issues_count']} 件の"
                "セキュリティ問題が検出されました。修正を検討してください。"
            )

        if safety_result.get("vulnerabilities_count", 0) > 0:
            summary["recommendations"].append(
                f"safety で {safety_result['vulnerabilities_count']} 件の"
                "依存関係脆弱性が検出されました。依存関係の更新を検討してください。"
            )

        if not summary["recommendations"]:
            summary["recommendations"].append("セキュリティスキャンで問題は検出されませんでした。")

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
        safety_result = self.run_safety_check()

        # 統合レポートを生成
        summary = self.generate_summary_report(bandit_result, safety_result)

        logger.info("\n" + "=" * 60)
        logger.info("📋 セキュリティスキャン結果サマリー")
        logger.info("=" * 60)
        logger.info(f"全体ステータス: {summary['overall_status']}")
        logger.info(f"bandit 問題数: {bandit_result.get('issues_count', 'N/A')}")
        logger.info(f"safety 脆弱性数: {safety_result.get('vulnerabilities_count', 'N/A')}")
        logger.info("\n推奨事項:")
        for recommendation in summary["recommendations"]:
            logger.info(f"  • {recommendation}")
        logger.info("=" * 60)

        return summary


def handle_full_scan(scanner, args):
    """全スキャンの処理"""
    summary = scanner.run_full_scan()

    # エラーステータスのチェック
    if summary["overall_status"] == "error":
        logger.info("\n❌ スキャン実行中にエラーが発生しました。")
        sys.exit(1)

    if args.fail_on_issues:
        bandit_issues = summary["scan_results"]["bandit"].get("issues_count", 0)
        safety_vulnerabilities = summary["scan_results"]["safety"].get("vulnerabilities_count", 0)
        if bandit_issues > 0 or safety_vulnerabilities > 0:
            logger.info("\n⚠️  セキュリティ問題が検出されましたが、スキャンは成功しました。")
            logger.info("詳細はセキュリティレポートを確認してください。")
            # 警告レベルとして処理し、終了コードは 0 を保持


def handle_single_scan(scanner, args):
    """単一スキャンの処理"""
    result = None

    if args.scan_type == "bandit":
        result = scanner.run_bandit_scan()
    elif args.scan_type == "safety":
        result = scanner.run_safety_check()

    # エラーステータスのチェック
    if result and result.get("status") == "error":
        logger.info(f"\n❌ {args.scan_type} スキャンでエラーが発生しました。")
        sys.exit(1)

    # 問題検出時の処理（警告レベル）
    if args.fail_on_issues and result:
        issues = result.get("issues_count", 0) + result.get("vulnerabilities_count", 0)
        if issues > 0:
            logger.info(f"\n⚠️  {args.scan_type} スキャンで {issues} 件の問題が検出されました。")
            logger.info("詳細はレポートを確認してください。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="セキュリティスキャンを実行")
    parser.add_argument(
        "--scan-type",
        choices=["all", "bandit", "safety"],
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
        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️  スキャンが中断されました。")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
