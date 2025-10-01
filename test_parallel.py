#!/usr/bin/env python3
"""
並列テスト実行の検証スクリプト
pytest-xdist が正しく動作するかテストします
"""

import subprocess
import sys
import time
from pathlib import Path


def run_test_with_timing(parallel=False):
    """テストを実行し、実行時間を測定"""
    
    cmd = [
        sys.executable,
        "-m", 
        "pytest",
        "tests/unit/",
        "-v",
        "--tb=short"
    ]
    
    if parallel:
        cmd.extend(["-n", "auto"])
        print("🔄 並列テスト実行中...")
    else:
        print("🔄 シーケンシャルテスト実行中...")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ テスト成功 - 実行時間: {execution_time:.2f}秒")
            return execution_time, True
        else:
            print(f"❌ テスト失敗 - 実行時間: {execution_time:.2f}秒")
            print("STDERR:", result.stderr)
            return execution_time, False
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return 0, False


def main():
    """メイン関数"""
    print("🧪 並列テスト実行の検証を開始します\n")
    
    # シーケンシャル実行
    print("=" * 50)
    sequential_time, sequential_success = run_test_with_timing(parallel=False)
    
    print("\n" + "=" * 50)
    # 並列実行
    parallel_time, parallel_success = run_test_with_timing(parallel=True)
    
    print("\n" + "=" * 50)
    print("📊 結果サマリー:")
    print(f"  シーケンシャル実行: {sequential_time:.2f}秒 ({'成功' if sequential_success else '失敗'})")
    print(f"  並列実行: {parallel_time:.2f}秒 ({'成功' if parallel_success else '失敗'})")
    
    if sequential_success and parallel_success and sequential_time > 0:
        speedup = sequential_time / parallel_time
        print(f"  🚀 速度向上: {speedup:.2f}倍")
        
        if speedup > 1.2:
            print("  ✅ 並列実行による有意な速度向上が確認されました！")
        else:
            print("  ⚠️  並列実行の効果は限定的です（テスト数が少ない可能性）")
    else:
        print("  ⚠️  比較できませんでした")
    
    return sequential_success and parallel_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)