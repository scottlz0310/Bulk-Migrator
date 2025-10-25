#!/usr/bin/env python3
"""
GitHub CLI を使用した Actions 実行状況確認スクリプト

GitHub CLI (gh) を使用してワークフローの実行状況を確認します。
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from typing import Any

# ロガーの設定
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class GitHubCLIChecker:
    """GitHub CLI を使用した Actions チェッカー"""

    def __init__(self):
        self.check_gh_cli()

    def check_gh_cli(self):
        """GitHub CLI の存在確認"""
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True, check=True)
            version = result.stdout.strip().split()[2]
            logger.info(f"✅ GitHub CLI が利用可能です: {version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ GitHub CLI (gh) がインストールされていません")
            logger.error("   インストール方法: https://cli.github.com/")
            sys.exit(1)

    def run_gh_command(self, args: list[str]) -> dict[str, Any] | None:
        """GitHub CLI コマンドを実行"""
        try:
            result = subprocess.run(["gh"] + args, capture_output=True, text=True, check=True)

            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"output": result.stdout.strip()}
            return None

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ GitHub CLI コマンドエラー: {e.stderr}")
            return None

    def get_workflow_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """ワークフロー実行履歴を取得"""
        logger.info(f"🔍 ワークフロー実行履歴を取得中... (最新{limit}件)")

        result = self.run_gh_command(
            [
                "run",
                "list",
                "--limit",
                str(limit),
                "--json",
                (
                    "databaseId,displayTitle,status,conclusion,createdAt,"
                    "updatedAt,url,headBranch,headSha,number,event,workflowName"
                ),
            ]
        )

        if result and isinstance(result, list):
            return result
        return []

    def get_workflow_status_summary(self) -> dict[str, Any]:
        """ワークフロー実行状況のサマリーを取得"""
        logger.info("📊 ワークフロー実行状況サマリーを生成中...")

        runs = self.get_workflow_runs(20)  # 最新20件を取得

        if not runs:
            return {"error": "ワークフロー実行履歴を取得できませんでした"}

        # ワークフロー別の最新状況を集計
        workflow_status = {}
        summary: dict[str, Any] = {
            "total_runs": len(runs),
            "successful": 0,
            "failed": 0,
            "in_progress": 0,
            "cancelled": 0,
            "other": 0,
            "workflows": {},
        }

        for run in runs:
            workflow_name = run.get("workflowName", "unknown")
            conclusion = run.get("conclusion")
            status = run.get("status")

            # ワークフロー別の最新実行を記録
            if workflow_name not in workflow_status:
                workflow_status[workflow_name] = run

            # 全体サマリーを集計
            if conclusion == "success":
                summary["successful"] = summary["successful"] + 1
            elif conclusion == "failure":
                summary["failed"] = summary["failed"] + 1
            elif conclusion == "cancelled":
                summary["cancelled"] = summary["cancelled"] + 1
            elif status == "in_progress":
                summary["in_progress"] = summary["in_progress"] + 1
            else:
                summary["other"] = summary["other"] + 1

        summary["workflows"] = workflow_status
        return summary

    def display_run_status(self, run: dict[str, Any]):
        """実行状況を表示"""
        workflow_name = run.get("workflowName", "Unknown")
        conclusion = run.get("conclusion")
        status = run.get("status")

        # ステータスアイコンを決定
        if conclusion == "success":
            icon = "✅"
        elif conclusion == "failure":
            icon = "❌"
        elif conclusion == "cancelled":
            icon = "⚠️"
        elif status == "in_progress":
            icon = "🔄"
        elif status == "queued":
            icon = "⏳"
        else:
            icon = "❓"

        # 実行時刻をフォーマット
        updated_at = run.get("updatedAt")
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except ValueError:
                time_str = updated_at
        else:
            time_str = "不明"

        logger.info(f"{icon} {workflow_name}")
        logger.info(f"   ステータス: {status} / {conclusion or 'N/A'}")
        logger.info(f"   実行番号: #{run.get('number', 'N/A')}")
        logger.info(f"   ブランチ: {run.get('headBranch', 'N/A')}")
        head_sha = run.get("headSha")
        commit_short = head_sha[:8] if head_sha else "N/A"
        logger.info(f"   コミット: {commit_short}")
        logger.info(f"   更新日時: {time_str}")
        logger.info(f"   詳細: {run.get('url', 'N/A')}")
        logger.info("")

    def check_security_status(self) -> dict[str, Any]:
        """セキュリティ関連ワークフローの状況をチェック"""
        logger.info("🔒 セキュリティ関連ワークフローの状況を確認中...")

        summary = self.get_workflow_status_summary()
        if "error" in summary:
            return summary

        security_workflows = {}
        for workflow_name, run in summary["workflows"].items():
            if "security" in workflow_name.lower() or "scan" in workflow_name.lower():
                security_workflows[workflow_name] = run

        return {
            "security_workflows": security_workflows,
            "total_security_workflows": len(security_workflows),
            "summary": summary,
        }

    def check_quality_status(self) -> dict[str, Any]:
        """品質チェック関連ワークフローの状況をチェック"""
        logger.info("🎯 品質チェック関連ワークフローの状況を確認中...")

        summary = self.get_workflow_status_summary()
        if "error" in summary:
            return summary

        quality_workflows = {}
        for workflow_name, run in summary["workflows"].items():
            keywords = ["quality", "test", "lint", "check"]
            if any(keyword in workflow_name.lower() for keyword in keywords):
                quality_workflows[workflow_name] = run

        return {
            "quality_workflows": quality_workflows,
            "total_quality_workflows": len(quality_workflows),
            "summary": summary,
        }

    def generate_status_report(self) -> dict[str, Any]:
        """総合ステータスレポートを生成"""
        logger.info("📋 総合ステータスレポートを生成中...")

        summary = self.get_workflow_status_summary()
        if "error" in summary:
            return summary

        # セキュリティと品質の分類
        security_workflows = {}
        quality_workflows = {}
        other_workflows = {}

        for workflow_name, run in summary["workflows"].items():
            if "security" in workflow_name.lower() or "scan" in workflow_name.lower():
                security_workflows[workflow_name] = run
            elif any(keyword in workflow_name.lower() for keyword in ["quality", "test", "lint", "check"]):
                quality_workflows[workflow_name] = run
            else:
                other_workflows[workflow_name] = run

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "security_workflows": security_workflows,
            "quality_workflows": quality_workflows,
            "other_workflows": other_workflows,
            "recommendations": self._generate_recommendations(security_workflows, quality_workflows),
        }

    def _generate_recommendations(
        self, security_workflows: dict[str, Any], quality_workflows: dict[str, Any]
    ) -> list[str]:
        """推奨事項を生成"""
        recommendations = []

        # セキュリティワークフローの確認
        security_failed = any(run.get("conclusion") == "failure" for run in security_workflows.values())
        if security_failed:
            msg = "❌ セキュリティスキャンで問題が検出されています。修正が必要です。"
            recommendations.append(msg)
        elif security_workflows:
            recommendations.append("✅ セキュリティスキャンは正常に完了しています。")
        else:
            msg = "⚠️  セキュリティスキャンワークフローが見つかりません。"
            recommendations.append(msg)

        # 品質チェックワークフローの確認
        quality_failed = any(run.get("conclusion") == "failure" for run in quality_workflows.values())
        if quality_failed:
            msg = "❌ 品質チェックで問題が検出されています。修正が必要です。"
            recommendations.append(msg)
        elif quality_workflows:
            recommendations.append("✅ 品質チェックは正常に完了しています。")
        else:
            recommendations.append("⚠️  品質チェックワークフローが見つかりません。")

        return recommendations


def _handle_security_check(checker: GitHubCLIChecker) -> dict[str, Any]:
    """セキュリティチェックを処理"""
    result = checker.check_security_status()

    logger.info("=" * 60)
    logger.info("🔒 セキュリティワークフロー状況")
    logger.info("=" * 60)

    if "error" in result:
        logger.error(f"❌ {result['error']}")
    else:
        for _, run in result["security_workflows"].items():
            checker.display_run_status(run)

        count = result["total_security_workflows"]
        logger.info(f"📊 セキュリティワークフロー数: {count}")

    return result


def _handle_quality_check(checker: GitHubCLIChecker) -> dict[str, Any]:
    """品質チェックを処理"""
    result = checker.check_quality_status()

    logger.info("=" * 60)
    logger.info("🎯 品質チェックワークフロー状況")
    logger.info("=" * 60)

    if "error" in result:
        logger.error(f"❌ {result['error']}")
    else:
        for _, run in result["quality_workflows"].items():
            checker.display_run_status(run)

        count = result["total_quality_workflows"]
        logger.info(f"📊 品質チェックワークフロー数: {count}")

    return result


def _handle_all_check(checker: GitHubCLIChecker) -> dict[str, Any]:
    """全チェックを処理"""
    result = checker.generate_status_report()

    if "error" in result:
        logger.error(f"❌ {result['error']}")
        return result

    logger.info("=" * 60)
    logger.info("📋 GitHub Actions 総合ステータス")
    logger.info("=" * 60)

    # セキュリティワークフロー
    if result["security_workflows"]:
        logger.info("🔒 セキュリティワークフロー:")
        for _, run in result["security_workflows"].items():
            checker.display_run_status(run)

    # 品質チェックワークフロー
    if result["quality_workflows"]:
        logger.info("🎯 品質チェックワークフロー:")
        for _, run in result["quality_workflows"].items():
            checker.display_run_status(run)

    # その他のワークフロー
    if result["other_workflows"]:
        logger.info("📦 その他のワークフロー:")
        for _, run in result["other_workflows"].items():
            checker.display_run_status(run)

    # サマリー
    summary = result["summary"]
    logger.info("📊 サマリー:")
    logger.info(f"   総実行数: {summary['total_runs']}")
    logger.info(f"   成功: {summary['successful']}")
    logger.info(f"   失敗: {summary['failed']}")
    logger.info(f"   実行中: {summary['in_progress']}")
    logger.info(f"   キャンセル: {summary['cancelled']}")
    logger.info(f"   その他: {summary['other']}")

    # 推奨事項
    logger.info("\n💡 推奨事項:")
    for recommendation in result["recommendations"]:
        logger.info(f"   {recommendation}")

    return result


def main() -> None:
    """メイン関数"""
    parser = argparse.ArgumentParser(description="GitHub Actions 実行状況を確認 (GitHub CLI使用)")
    parser.add_argument(
        "--type",
        choices=["all", "security", "quality"],
        default="all",
        help="確認するワークフローの種類",
    )
    parser.add_argument("--output", help="結果をJSONファイルに出力")
    parser.add_argument("--limit", type=int, default=10, help="取得する実行履歴の件数")

    args = parser.parse_args()

    try:
        checker = GitHubCLIChecker()

        if args.type == "security":
            result = _handle_security_check(checker)
        elif args.type == "quality":
            result = _handle_quality_check(checker)
        else:  # all
            result = _handle_all_check(checker)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 詳細レポートを {args.output} に保存しました")

        logger.info("\n✅ GitHub Actions 状況確認が完了しました")

    except KeyboardInterrupt:
        logger.info("\n⚠️  処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
