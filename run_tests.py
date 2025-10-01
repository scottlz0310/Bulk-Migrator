#!/usr/bin/env python3
"""
ローカルテスト実行スクリプト
テストカバレッジの測定とレポート生成を行います
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """テストを実行し、カバレッジレポートを生成"""

    # テスト実行コマンド（並列実行）
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=src",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-fail-under=15",
        "-v",
        "-n",
        "auto",
        "tests/",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.stderr:
            pass

        if result.returncode == 0:
            pass
        else:
            return False

    except Exception:
        return False

    return True


def check_coverage():
    """カバレッジレポートの確認"""
    coverage_file = Path("htmlcov/index.html")
    if coverage_file.exists():
        return True
    else:
        return False


def check_dependencies():
    """依存関係の確認"""
    import importlib.util

    # pytest-cov は coverage を使用するため確認
    if importlib.util.find_spec("coverage") is None:
        return False
    if importlib.util.find_spec("pytest") is None:
        return False

    return True


def main():
    """メイン関数"""

    # 依存関係の確認
    if not check_dependencies():
        return False

    # テスト実行
    success = run_tests()

    if success:
        # カバレッジレポート確認
        check_coverage()

    else:
        pass

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
