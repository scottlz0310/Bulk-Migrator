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
    print("🧪 テスト実行を開始します...")
    
    # テスト実行コマンド
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=src",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-fail-under=15",
        "-v",
        "tests/"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("📊 テスト結果:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  警告・エラー:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ テストが正常に完了しました")
            print("📁 カバレッジレポート: htmlcov/index.html")
        else:
            print("❌ テストが失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        return False
    
    return True


def check_coverage():
    """カバレッジレポートの確認"""
    coverage_file = Path("htmlcov/index.html")
    if coverage_file.exists():
        print(f"📈 カバレッジレポートが生成されました: {coverage_file.absolute()}")
        return True
    else:
        print("❌ カバレッジレポートが生成されませんでした")
        return False


def check_dependencies():
    """依存関係の確認"""
    try:
        import pytest
        import coverage  # pytest-cov は coverage を使用
        print("✅ 必要な依存関係がインストールされています")
        return True
    except ImportError as e:
        print(f"❌ 必要な依存関係が不足しています: {e}")
        print("以下のコマンドでインストールしてください:")
        print("pip install pytest pytest-cov pytest-mock")
        return False


def main():
    """メイン関数"""
    print("🚀 Bulk-Migrator ローカルテスト実行")
    print("=" * 50)
    
    # 依存関係の確認
    if not check_dependencies():
        return False
    
    # テスト実行
    success = run_tests()
    
    if success:
        # カバレッジレポート確認
        check_coverage()
        
        print("\n🎉 テスト実行完了!")
        print("📋 次のステップ:")
        print("1. htmlcov/index.html をブラウザで開いてカバレッジを確認")
        print("2. テストが失敗した場合は、エラーメッセージを確認して修正")
        print("3. カバレッジが70%未満の場合は、テストケースを追加")
    else:
        print("\n💡 改善提案:")
        print("1. テストが失敗した原因を特定")
        print("2. 必要なモックやフィクスチャを追加")
        print("3. テストケースの見直し")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 