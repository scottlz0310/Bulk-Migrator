#!/usr/bin/env python3
"""
GitHub Actions 実行状況確認スクリプト

このスクリプトはGitHub APIを使用してワークフローの実行状況を確認します。
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

import requests

# ロガーの設定
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class GitHubActionsChecker:
    """GitHub Actions の実行状況をチェックするクラス"""

    def __init__(self, repo_owner: str, repo_name: str, token: str | None = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"

        if not self.token:
            msg = (
                "⚠️  GITHUB_TOKEN が設定されていません。"
                "API制限により一部機能が制限される可能性があります。"
            )
            logger.warning(msg)

    def _make_request(self, endpoint: str) -> dict[str, Any] | None:
        """GitHub API リクエストを実行"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/{endpoint}"
        headers = {"Accept": "application/vnd.github.v3+json"}

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API リクエストエラー: {e}")
            return None

    def get_workflow_runs(
        self, workflow_name: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """ワークフロー実行履歴を取得"""
        logger.info(f"🔍 ワークフロー実行履歴を取得中... (最新{limit}件)")

        endpoint = f"actions/runs?per_page={limit}"
        if workflow_name:
            endpoint += f"&workflow={workflow_name}"

        data = self._make_request(endpoint)
        if not data:
            return []

        return data.get("workflow_runs", [])

    def get_workflow_status(self, workflow_name: str) -> dict[str, Any]:
        """特定のワークフローの最新実行状況を取得"""
        logger.info(f"📊 ワークフロー '{workflow_name}' の状況を確認中...")

        # 全実行履歴を取得してワークフロー名でフィルタ
        all_runs = self.get_workflow_runs(limit=20)

        # 指定されたワークフローの実行のみを抽出
        workflow_runs = [
            run for run in all_runs if run.get("path", "").endswith(workflow_name)
        ]

        if not workflow_runs:
            return {
                "status": "not_found",
                "message": f"ワークフロー '{workflow_name}' が見つかりません",
            }

        latest_run = workflow_runs[0]
        head_sha = latest_run.get("head_sha")
        return {
            "status": latest_run.get("status"),
            "conclusion": latest_run.get("conclusion"),
            "created_at": latest_run.get("created_at"),
            "updated_at": latest_run.get("updated_at"),
            "html_url": latest_run.get("html_url"),
            "head_branch": latest_run.get("head_branch"),
            "head_sha": head_sha[:8] if head_sha else None,
            "run_number": latest_run.get("run_number"),
            "event": latest_run.get("event"),
        }

    def get_security_scan_status(self) -> dict[str, Any]:
        """セキュリティスキャンワークフローの状況を取得"""
        return self.get_workflow_status("security-scan.yml")

    def get_quality_check_status(self) -> dict[str, Any]:
        """品質チェックワークフローの状況を取得"""
        return self.get_workflow_status("quality-check.yml")

    def get_all_workflow_status(self) -> dict[str, dict[str, Any]]:
        """全ワークフローの状況を取得"""
        logger.info("📋 全ワークフローの状況を確認中...")

        workflows = [
            "quality-check.yml",
            "security-scan.yml",
            "pr-quality-gate.yml",
            "prepare-release.yml",
            "release.yml",
        ]

        status_summary = {}
        for workflow in workflows:
            status_summary[workflow] = self.get_workflow_status(workflow)

        return status_summary

    def display_workflow_status(self, workflow_name: str, status: dict[str, Any]):
        """ワークフロー状況を表示"""
        if status.get("status") == "not_found":
            logger.info(f"❓ {workflow_name}: {status.get('message')}")
            return

        conclusion = status.get("conclusion")
        run_status = status.get("status")

        # ステータスアイコンを決定
        if conclusion == "success":
            icon = "✅"
        elif conclusion == "failure":
            icon = "❌"
        elif conclusion == "cancelled":
            icon = "⚠️"
        elif run_status == "in_progress":
            icon = "🔄"
        elif run_status == "queued":
            icon = "⏳"
        else:
            icon = "❓"

        # 実行時刻をフォーマット
        updated_at = status.get("updated_at")
        if updated_at:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            time_str = "不明"

        logger.info(f"{icon} {workflow_name}")
        logger.info(f"   ステータス: {run_status} / {conclusion}")
        logger.info(f"   実行番号: #{status.get('run_number', 'N/A')}")
        logger.info(f"   ブランチ: {status.get('head_branch', 'N/A')}")
        logger.info(f"   コミット: {status.get('head_sha', 'N/A')}")
        logger.info(f"   更新日時: {time_str}")
        if status.get("html_url"):
            logger.info(f"   詳細: {status.get('html_url')}")
        logger.info("")

    def generate_status_report(self) -> dict[str, Any]:
        """ステータスレポートを生成"""
        logger.info("📊 GitHub Actions ステータスレポートを生成中...")

        all_status = self.get_all_workflow_status()

        # サマリー情報を生成
        summary: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "repository": f"{self.repo_owner}/{self.repo_name}",
            "workflows": all_status,
            "summary": {
                "total_workflows": len(all_status),
                "successful": 0,
                "failed": 0,
                "in_progress": 0,
                "other": 0,
            },
        }

        # 各ワークフローの状況を集計
        for _, status in all_status.items():
            conclusion = status.get("conclusion")
            run_status = status.get("status")

            if conclusion == "success":
                summary["summary"]["successful"] = summary["summary"]["successful"] + 1
            elif conclusion == "failure":
                summary["summary"]["failed"] = summary["summary"]["failed"] + 1
            elif run_status == "in_progress":
                summary["summary"]["in_progress"] = (
                    summary["summary"]["in_progress"] + 1
                )
            else:
                summary["summary"]["other"] = summary["summary"]["other"] + 1

        return summary


def get_repo_info() -> tuple[str, str]:
    """Gitリポジトリから所有者とリポジトリ名を取得"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )

        remote_url = result.stdout.strip()

        # GitHub URL からリポジトリ情報を抽出
        if "github.com" in remote_url:
            if remote_url.startswith("https://"):
                # https://github.com/owner/repo.git
                parts = (
                    remote_url.replace("https://github.com/", "")
                    .replace(".git", "")
                    .split("/")
                )
            elif remote_url.startswith("git@"):
                # git@github.com:owner/repo.git
                parts = (
                    remote_url.replace("git@github.com:", "")
                    .replace(".git", "")
                    .split("/")
                )
            else:
                raise ValueError("不明なGitHub URL形式")

            if len(parts) >= 2:
                return parts[0], parts[1]

        raise ValueError("GitHub リポジトリではありません")

    except subprocess.CalledProcessError as e:
        raise ValueError("Git リポジトリではありません") from e
    except Exception as e:
        raise ValueError(f"リポジトリ情報の取得に失敗: {e}") from e


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="GitHub Actions 実行状況を確認")
    parser.add_argument(
        "--workflow", help="特定のワークフローのみ確認 (例: security-scan.yml)"
    )
    parser.add_argument("--output", help="結果をJSONファイルに出力")
    parser.add_argument(
        "--token",
        help="GitHub Personal Access Token (環境変数 GITHUB_TOKEN でも設定可能)",
    )

    args = parser.parse_args()

    try:
        # リポジトリ情報を取得
        repo_owner, repo_name = get_repo_info()
        logger.info(f"📁 リポジトリ: {repo_owner}/{repo_name}")
        logger.info("")

        # GitHub Actions チェッカーを初期化
        checker = GitHubActionsChecker(repo_owner, repo_name, args.token)

        if args.workflow:
            # 特定のワークフローのみ確認
            status = checker.get_workflow_status(args.workflow)
            checker.display_workflow_status(args.workflow, status)

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump({args.workflow: status}, f, indent=2, ensure_ascii=False)
                logger.info(f"📄 結果を {args.output} に保存しました")
        else:
            # 全ワークフローの状況を確認
            report = checker.generate_status_report()

            # 結果を表示
            logger.info("=" * 60)
            logger.info("📋 GitHub Actions ステータス一覧")
            logger.info("=" * 60)

            for workflow_name, status in report["workflows"].items():
                checker.display_workflow_status(workflow_name, status)

            # サマリーを表示
            summary = report["summary"]
            logger.info("📊 サマリー:")
            logger.info(f"   総ワークフロー数: {summary['total_workflows']}")
            logger.info(f"   成功: {summary['successful']}")
            logger.info(f"   失敗: {summary['failed']}")
            logger.info(f"   実行中: {summary['in_progress']}")
            logger.info(f"   その他: {summary['other']}")

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                logger.info(f"📄 詳細レポートを {args.output} に保存しました")

        logger.info("✅ GitHub Actions 状況確認が完了しました")

    except ValueError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
