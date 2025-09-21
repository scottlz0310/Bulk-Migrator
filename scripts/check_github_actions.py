#!/usr/bin/env python3
"""GitHub Actions ワークフロー状況確認スクリプト"""

import json
import logging
import subprocess
import sys
from datetime import datetime

# ロガーの設定
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def run_command(cmd: list[str]) -> tuple[str, str, int]:
    """コマンドを実行して結果を返す"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def check_github_actions():
    """GitHub Actions の状況をチェック"""
    logger.info("GitHub Actions ワークフロー状況確認中...")

    # GitHub CLI が利用可能かチェック
    stdout, stderr, code = run_command(["gh", "--version"])
    if code != 0:
        logger.error("エラー: GitHub CLI (gh) がインストールされていません")
        logger.info("インストール方法: https://cli.github.com/")
        return False

    # 最新のワークフロー実行状況を取得
    stdout, stderr, code = run_command(
        [
            "gh",
            "run",
            "list",
            "--limit",
            "10",
            "--json",
            "status,conclusion,name,createdAt,url,workflowName",
        ]
    )

    if code != 0:
        logger.error(f"エラー: GitHub Actions の情報取得に失敗: {stderr}")
        return False

    try:
        runs = json.loads(stdout)
    except json.JSONDecodeError:
        logger.error("エラー: GitHub Actions の応答を解析できません")
        return False

    if not runs:
        logger.info("ワークフロー実行履歴が見つかりません")
        return True

    logger.info(f"\n最新のワークフロー実行状況 (最新{len(runs)}件):")
    logger.info("-" * 80)

    failed_runs = []
    for run in runs:
        status = run.get("status", "unknown")
        conclusion = run.get("conclusion", "unknown")
        name = run.get("workflowName", "unknown")
        created = run.get("createdAt", "")
        url = run.get("url", "")

        # 日時をフォーマット
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            created_str = created

        # ステータス表示
        status_icon = {
            "completed": "✅" if conclusion == "success" else "❌",
            "in_progress": "🔄",
            "queued": "⏳",
        }.get(status, "❓")

        logger.info(f"{status_icon} {name}")
        logger.info(f"   ステータス: {status} / {conclusion}")
        logger.info(f"   実行日時: {created_str}")
        logger.info(f"   URL: {url}")
        logger.info("")

        # 失敗したワークフローを記録
        if status == "completed" and conclusion == "failure":
            failed_runs.append({"name": name, "url": url, "created": created_str})

    # 失敗したワークフローの詳細を表示
    if failed_runs:
        logger.warning("🚨 失敗したワークフロー:")
        logger.info("-" * 40)
        for run in failed_runs:
            logger.error(f"❌ {run['name']} ({run['created']})")
            logger.info(f"   詳細: {run['url']}")

        logger.warning("\n修正が必要なワークフローがあります。")
        return False
    else:
        logger.info("✅ すべてのワークフローが正常に完了しています。")
        return True


def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("GitHub Actions ワークフロー確認スクリプト")
    logger.info("=" * 60)

    success = check_github_actions()

    if not success:
        logger.info("\n推奨アクション:")
        logger.info("1. 失敗したワークフローのログを確認")
        logger.info("2. エラーの原因を特定")
        logger.info("3. 必要に応じてワークフローファイルを修正")
        logger.info("4. 修正後に再度プッシュして確認")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
