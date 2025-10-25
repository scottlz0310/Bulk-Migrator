#!/usr/bin/env python3
"""
セキュリティチェックスクリプト
実行前の環境検証とセキュリティ状態の確認
"""

import json
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.secrets_manager import SecretsManager
from src.security_integration import SecurityIntegration

console = Console()


def main():
    """メインのセキュリティチェック"""
    console.print(Panel("🔒 Bulk-Migrator セキュリティチェック", style="bold blue"))

    security = SecurityIntegration()
    secrets_manager = SecretsManager()

    # 1. 環境変数の検証
    console.print("\n📋 環境変数セキュリティ検証...", style="bold")
    env_check = secrets_manager.validate_env_security()

    if env_check["status"] == "SECURE":
        console.print("✅ 環境変数: セキュア", style="green")
    else:
        console.print("❌ 環境変数: 問題あり", style="red")
        for issue in env_check["issues"]:
            console.print(f"   - {issue}", style="red")

    # 2. ファイル権限チェック
    console.print("\n🔐 ファイル権限チェック...", style="bold")
    validation = security.validate_environment()

    permissions_ok = True
    for file_path, result in validation["file_permissions"].items():
        if result["status"] == "SECURE":
            console.print(f"✅ {file_path}: セキュア", style="green")
        else:
            console.print(f"❌ {file_path}: {result['status']}", style="red")
            if result.get("auto_fixed"):
                console.print("   🔧 自動修正済み", style="yellow")
            permissions_ok = False

    # 3. 機密情報露出スキャン
    console.print("\n🔍 機密情報露出スキャン...", style="bold")
    secrets_scan = validation["secrets_exposure"]

    if secrets_scan["status"] == "CLEAN":
        console.print("✅ 機密情報露出: なし", style="green")
    else:
        console.print("❌ 機密情報露出: 検出", style="red")
        for exposure in secrets_scan["exposed_secrets"]:
            console.print(f"   - {exposure['file']}: {exposure['matches_count']} 件", style="red")

    # 4. 整合性チェック
    console.print("\n🛡️ ファイル整合性チェック...", style="bold")
    integrity = validation["integrity"]

    if not integrity["alerts"]:
        console.print("✅ ファイル整合性: 正常", style="green")
    else:
        console.print("❌ ファイル整合性: 問題あり", style="red")
        for alert in integrity["alerts"]:
            console.print(f"   - {alert}", style="red")

    # 5. 総合判定
    console.print("\n" + "=" * 50)

    all_secure = (
        env_check["status"] == "SECURE"
        and permissions_ok
        and secrets_scan["status"] == "CLEAN"
        and not integrity["alerts"]
    )

    if all_secure:
        console.print("🎉 セキュリティチェック: 全て正常", style="bold green")
        console.print("✅ 転送処理を安全に実行できます", style="green")
        return 0
    else:
        console.print("⚠️  セキュリティチェック: 問題が検出されました", style="bold red")
        console.print("❌ 問題を解決してから転送処理を実行してください", style="red")

        # 詳細レポートを保存
        report_path = "security_reports/security_check_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(validation, f, indent=2, ensure_ascii=False)

        console.print(f"📄 詳細レポート: {report_path}", style="blue")
        return 1


if __name__ == "__main__":
    sys.exit(main())
