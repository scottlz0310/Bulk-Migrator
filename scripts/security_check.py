#!/usr/bin/env python3
"""
セキュリティチェックスクリプト
実行前の環境検証とセキュリティ状態の確認
"""

# ruff: noqa: E402

import json
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.secrets_manager import SecretsManager
from src.security_integration import SecurityIntegration

console = Console()


def _display_env_security(result: dict[str, Any]) -> bool:
    status = result.get("status")
    if status == "SECURE":
        console.print("✅ 環境変数: セキュア", style="green")
        return True

    console.print("❌ 環境変数: 問題あり", style="red")
    for issue in result.get("issues", []):
        console.print(f"   - {issue}", style="red")
    return False


def _display_file_permissions(entries: dict[str, Any]) -> bool:
    is_secure = True
    for file_path, outcome in entries.items():
        if outcome.get("status") == "SECURE":
            console.print(f"✅ {file_path}: セキュア", style="green")
            continue

        console.print(f"❌ {file_path}: {outcome.get('status')}", style="red")
        if outcome.get("auto_fixed"):
            console.print("   🔧 自動修正済み", style="yellow")
        is_secure = False
    return is_secure


def _display_secrets_scan(scan: dict[str, Any]) -> bool:
    if scan.get("status") == "CLEAN":
        console.print("✅ 機密情報露出: なし", style="green")
        return True

    console.print("❌ 機密情報露出: 検出", style="red")
    for exposure in scan.get("exposed_secrets", []):
        console.print(
            f"   - {exposure['file']}: {exposure['matches_count']} 件",
            style="red",
        )
    return False


def _display_integrity(integrity: dict[str, Any]) -> bool:
    alerts = integrity.get("alerts", [])
    if not alerts:
        console.print("✅ ファイル整合性: 正常", style="green")
        return True

    console.print("❌ ファイル整合性: 問題あり", style="red")
    for alert in alerts:
        console.print(f"   - {alert}", style="red")
    return False


def _persist_report(data: dict[str, Any]) -> Path:
    report_path = Path("security_reports/security_check_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report_path


def main() -> int:
    """メインのセキュリティチェック"""
    console.print(Panel("🔒 Bulk-Migrator セキュリティチェック", style="bold blue"))

    security = SecurityIntegration()
    secrets_manager = SecretsManager()

    # 1. 環境変数の検証
    console.print("\n📋 環境変数セキュリティ検証...", style="bold")
    env_check = secrets_manager.validate_env_security()
    env_secure = _display_env_security(env_check)

    # 2. ファイル権限チェック
    console.print("\n🔐 ファイル権限チェック...", style="bold")
    validation = security.validate_environment()
    permissions_ok = _display_file_permissions(validation["file_permissions"])

    # 3. 機密情報露出スキャン
    console.print("\n🔍 機密情報露出スキャン...", style="bold")
    secrets_clean = _display_secrets_scan(validation["secrets_exposure"])

    # 4. 整合性チェック
    console.print("\n🛡️ ファイル整合性チェック...", style="bold")
    integrity_ok = _display_integrity(validation["integrity"])

    # 5. 総合判定
    console.print("\n" + "=" * 50)

    all_secure = all((env_secure, permissions_ok, secrets_clean, integrity_ok))

    if all_secure:
        console.print("🎉 セキュリティチェック: 全て正常", style="bold green")
        console.print("✅ 転送処理を安全に実行できます", style="green")
        return 0

    console.print("⚠️  セキュリティチェック: 問題が検出されました", style="bold red")
    console.print("❌ 問題を解決してから転送処理を実行してください", style="red")

    report_path = _persist_report(validation)
    console.print(f"📄 詳細レポート: {report_path}", style="blue")
    return 1


if __name__ == "__main__":
    sys.exit(main())
