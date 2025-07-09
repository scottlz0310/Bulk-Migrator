#!/usr/bin/env python3
"""
転送の進捗と完了時刻を予測するスクリプト

【目的】
  - フリーズ・中断時間を排除した実稼働時間を集計
  - 進捗率と平均処理速度から完了時刻を予測
  
【使い方】
  $ python utils/predict_completion.py
  
【出力例】
  実稼働時間: 5時間32分
  転送済み: 15,000件 / 50,000件 (30.0%)
  平均処理速度: 2.7件/分
  予測残り時間: 21時間15分
  完了予測時刻: 2025-07-10 18:30:00
"""

import sys
import os
import json
import glob
import re
from datetime import datetime, timedelta
from pathlib import Path

# src/の設定管理を使用
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
try:
    from config_manager import get_transfer_log_path, get_skip_list_path, get_onedrive_files_path
except ImportError:
    def get_transfer_log_path():
        return 'logs/transfer_start_success_error.log'
    def get_skip_list_path():
        return 'logs/skip_list.json'
    def get_onedrive_files_path():
        return 'logs/onedrive_files.json'

def parse_timestamp(line):
    """ログ行からタイムスタンプを抽出"""
    match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+\]', line)
    if match:
        return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
    return None

def calculate_active_runtime(log_files, max_gap_minutes=10):
    """
    ログファイルから実稼働時間を計算
    max_gap_minutes以上の間隔は中断とみなして除外
    """
    all_lines = []
    
    # 全ログファイルを時系列でマージ
    for log_file in sorted(log_files):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    timestamp = parse_timestamp(line)
                    if timestamp:
                        all_lines.append((timestamp, line.strip()))
        except Exception as e:
            print(f"警告: {log_file} の読み込みエラー: {e}")
    
    # 時系列順にソート
    all_lines.sort(key=lambda x: x[0])
    
    if len(all_lines) < 2:
        return timedelta(0), 0, 0
    
    total_runtime = timedelta(0)
    success_count = 0
    error_count = 0
    max_gap = timedelta(minutes=max_gap_minutes)
    
    for i in range(1, len(all_lines)):
        prev_time, prev_line = all_lines[i-1]
        curr_time, curr_line = all_lines[i]
        
        gap = curr_time - prev_time
        
        # 10分以内の間隔のみ実稼働時間に加算
        if gap <= max_gap:
            total_runtime += gap
        
        # SUCCESS/ERRORをカウント
        if 'SUCCESS:' in curr_line:
            success_count += 1
        elif 'ERROR:' in curr_line:
            error_count += 1
    
    return total_runtime, success_count, error_count

def load_file_counts():
    """OneDriveファイル数とスキップリスト件数を取得"""
    onedrive_path = Path(get_onedrive_files_path())
    skiplist_path = Path(get_skip_list_path())
    
    onedrive_count = 0
    skiplist_count = 0
    
    # OneDriveファイル数
    if onedrive_path.exists():
        try:
            with open(onedrive_path, 'r', encoding='utf-8') as f:
                onedrive_files = json.load(f)
                onedrive_count = len(onedrive_files)
        except Exception as e:
            print(f"警告: {onedrive_path} の読み込みエラー: {e}")
    
    # スキップリスト件数
    if skiplist_path.exists():
        try:
            with open(skiplist_path, 'r', encoding='utf-8') as f:
                skiplist = json.load(f)
                skiplist_count = len(skiplist)
        except Exception as e:
            print(f"警告: {skiplist_path} の読み込みエラー: {e}")
    
    return onedrive_count, skiplist_count

def format_timedelta(td):
    """timedeltalを読みやすい形式でフォーマット"""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}時間{minutes}分"
    elif minutes > 0:
        return f"{minutes}分{seconds}秒"
    else:
        return f"{seconds}秒"

def main():
    # ログファイルを取得
    log_pattern = get_transfer_log_path() + '*'
    log_files = glob.glob(log_pattern)
    
    if not log_files:
        print(f"ログファイルが見つかりません: {log_pattern}")
        return
    
    # 実稼働時間と転送件数を計算
    print("ログを解析中...")
    runtime, success_count, error_count = calculate_active_runtime(log_files)
    transferred_count = success_count + error_count
    
    # ファイル数を取得
    onedrive_count, skiplist_count = load_file_counts()
    
    # 進捗率を計算
    if onedrive_count > 0:
        progress_rate = (transferred_count / onedrive_count) * 100
    else:
        progress_rate = 0
    
    # 平均処理速度（件/分）
    runtime_minutes = runtime.total_seconds() / 60
    if runtime_minutes > 0:
        avg_speed = transferred_count / runtime_minutes
    else:
        avg_speed = 0
    
    # 残り件数と予測時間
    remaining_count = max(0, onedrive_count - transferred_count)
    if avg_speed > 0:
        predicted_remaining_minutes = remaining_count / avg_speed
        predicted_remaining = timedelta(minutes=predicted_remaining_minutes)
        completion_time = datetime.now() + predicted_remaining
    else:
        predicted_remaining = timedelta(0)
        completion_time = None
    
    # 結果を表示
    print("\n=== 転送進捗・完了予測 ===")
    print(f"実稼働時間: {format_timedelta(runtime)}")
    print(f"転送済み: {transferred_count:,}件 (SUCCESS: {success_count:,}, ERROR: {error_count:,})")
    print(f"OneDrive総ファイル数: {onedrive_count:,}件")
    print(f"スキップリスト: {skiplist_count:,}件")
    print(f"進捗率: {progress_rate:.1f}%")
    
    if avg_speed > 0:
        print(f"平均処理速度: {avg_speed:.1f}件/分")
        print(f"残り件数: {remaining_count:,}件")
        print(f"予測残り時間: {format_timedelta(predicted_remaining)}")
        if completion_time:
            print(f"完了予測時刻: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("処理速度の計算ができません（実稼働時間が不足）")
    
    # 成功率
    if transferred_count > 0:
        success_rate = (success_count / transferred_count) * 100
        print(f"成功率: {success_rate:.1f}%")

if __name__ == "__main__":
    main()
