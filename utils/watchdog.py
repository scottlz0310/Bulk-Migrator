#!/usr/bin/env python3
"""
フリーズ対策用監視・自動再起動スクリプト（親プロセス）

設計方針：
- src.mainを子プロセスとして起動・監視
- このスクリプトを使用する場合は先にpython -m src.main --resetを実行しておくと早くログが出力されるので失敗しにくいでしょう
- ログファイルの更新時刻を監視し、指定時間更新されなければ自動再起動
- 最低限の監視ログを記録（時刻・進行状況・再起動履歴）
usage:
  $ python utils/watchdog.py
  （src.mainが正常に動作しているか監視し、フリーズ時は自動再起動します）
- ログファイルのパスやタイムアウト時間は設定値として定義
- 監視ログはlogs/watchdog.logに出力
- src.mainの起動はsubprocessを使用し、標準出力・エラー出力をキャプチャ
- タイムアウト時間は設定値で調整
- 監視間隔は設定値で調整
- 再起動時は直前のログを記録し、監視ログに出力
- 短時間での連続再起動を防ぐため、再起動後は一定時間待機
- キーボード割り込み（Ctrl+C）で監視を停止し、
- src.mainが実行中の場合は正常に終了させる

"""

import subprocess
import time
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# 設定値
MAIN_LOG_PATH = "logs/transfer_start_success_error.log"
WATCHDOG_LOG_PATH = "logs/watchdog.log"
TIMEOUT_MINUTES = 10  # 10分間ログ更新がなければ再起動
CHECK_INTERVAL_SEC = 30  # 30秒ごとに監視
TAIL_LINES = 5  # 再起動時に記録する直前ログの行数

def log_watchdog(message):
    """監視ログに出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    # ログファイルにも記録
    os.makedirs(os.path.dirname(WATCHDOG_LOG_PATH), exist_ok=True)
    with open(WATCHDOG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def get_log_mtime():
    """メインログファイルの最終更新時刻を取得"""
    try:
        return os.path.getmtime(MAIN_LOG_PATH)
    except FileNotFoundError:
        return 0

def get_tail_lines(file_path, n_lines):
    """ファイルの末尾n行を取得"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return lines[-n_lines:] if len(lines) >= n_lines else lines
    except FileNotFoundError:
        return []

def format_time_diff(seconds):
    """秒数を読みやすい形式に変換"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        return f"{int(seconds/60)}分{int(seconds%60)}秒"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}時間{minutes}分"

def main():
    """メイン監視ループ"""
    log_watchdog("=== 監視開始 ===")
    log_watchdog(f"監視対象ログ: {MAIN_LOG_PATH}")
    log_watchdog(f"タイムアウト設定: {TIMEOUT_MINUTES}分")
    log_watchdog(f"監視間隔: {CHECK_INTERVAL_SEC}秒")
    
    restart_count = 0
    
    try:
        while True:
            # src.mainを子プロセスとして起動（標準出力・エラーをファイルにリダイレクト）
            start_time = time.time()
            log_watchdog(f"src.main起動中... (起動回数: {restart_count + 1})")

            os.makedirs("logs", exist_ok=True)
            with open("logs/src_main_stdout.log", "a", encoding="utf-8") as out, open("logs/src_main_stderr.log", "a", encoding="utf-8") as err:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "src.main"],
                    stdout=out,
                    stderr=err
                )
                log_watchdog(f"src.main起動完了 (PID: {proc.pid})")
                last_mtime = get_log_mtime()
                last_check_time = time.time()

                # 監視ループ
                while True:
                    time.sleep(CHECK_INTERVAL_SEC)

                    # プロセスが自然終了していないかチェック
                    if proc.poll() is not None:
                        elapsed = format_time_diff(time.time() - start_time)
                        log_watchdog(f"src.mainが自然終了しました (稼働時間: {elapsed}, 終了コード: {proc.returncode})")
                        # 正常終了（終了コード0）ならwatchdogも終了
                        if proc.returncode == 0:
                            log_watchdog("=== 監視終了（src.main正常終了） ===")
                            return
                        break

                    # ログファイルの更新チェック
                    current_mtime = get_log_mtime()
                    current_time = time.time()

                    if current_mtime > last_mtime:
                        # ログが更新された
                        last_mtime = current_mtime
                        last_check_time = current_time
                        continue

                    # タイムアウトチェック
                    idle_time = current_time - last_check_time
                    if idle_time > (TIMEOUT_MINUTES * 60):
                        elapsed = format_time_diff(time.time() - start_time)
                        idle_formatted = format_time_diff(idle_time)

                        log_watchdog(f"!!! フリーズ検出 !!! (稼働時間: {elapsed}, 無応答時間: {idle_formatted})")

                        # 直前のログを記録
                        tail_lines = get_tail_lines(MAIN_LOG_PATH, TAIL_LINES)
                        if tail_lines:
                            log_watchdog("=== 直前のログ ===")
                            for line in tail_lines:
                                log_watchdog(f"  {line.rstrip()}")
                            log_watchdog("=== 直前のログ終了 ===")

                        # プロセス強制終了
                        log_watchdog(f"src.main強制終了中... (PID: {proc.pid})")
                        proc.terminate()

                        try:
                            proc.wait(timeout=10)
                            log_watchdog("src.main正常終了")
                        except subprocess.TimeoutExpired:
                            log_watchdog("強制終了タイムアウト、KILL送信")
                            proc.kill()
                            proc.wait()
                            log_watchdog("src.mainをKILLしました")

                        restart_count += 1
                        log_watchdog(f"自動再起動準備中... (累計再起動回数: {restart_count})")
                        break

            # 短時間での連続再起動を防ぐ
            if time.time() - start_time < 60:
                log_watchdog("短時間終了検出、5秒待機してから再起動")
                time.sleep(5)

    except KeyboardInterrupt:
        log_watchdog("監視停止要求を受信")
        if 'proc' in locals() and proc.poll() is None:
            log_watchdog("src.mainを停止中...")
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        log_watchdog("=== 監視終了 ===")

if __name__ == "__main__":
    main()
