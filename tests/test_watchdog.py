"""
src/watchdog.py のテスト
"""

import json
import subprocess
from unittest.mock import Mock, mock_open, patch

from src.watchdog import (
    _handle_freeze_detection,
    _handle_keyboard_interrupt,
    _handle_process_termination,
    _monitor_process,
    _start_main_process,
    format_time_diff,
    get_log_mtime,
    get_tail_lines,
    is_transfer_remaining,
    log_watchdog,
    main,
)


class TestLogWatchdog:
    """log_watchdog 関数のテスト"""

    @patch("src.watchdog.get_structured_logger")
    @patch("os.makedirs")
    def test_log_watchdog(self, mock_makedirs, mock_get_logger):
        """検証対象: log_watchdog() 目的: ログ出力の動作確認"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("src.watchdog.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = (
                    "2024-01-01 12:00:00"
                )
                log_watchdog("test message")

        mock_get_logger.assert_called_once_with("watchdog")
        mock_logger.info.assert_called_once_with(
            "test message", timestamp="2024-01-01 12:00:00"
        )
        mock_makedirs.assert_called_once_with("logs", exist_ok=True)
        mock_file.assert_called_once_with("logs/watchdog.log", "a", encoding="utf-8")


class TestGetLogMtime:
    """get_log_mtime 関数のテスト"""

    @patch("os.path.getmtime")
    def test_get_log_mtime_file_exists(self, mock_getmtime):
        """検証対象: get_log_mtime() 目的: ファイル存在時の更新時刻取得確認"""
        mock_getmtime.return_value = 1234567890.0

        result = get_log_mtime()

        assert result == 1234567890.0
        mock_getmtime.assert_called_once_with("logs/transfer_start_success_error.log")

    @patch("os.path.getmtime")
    def test_get_log_mtime_file_not_found(self, mock_getmtime):
        """検証対象: get_log_mtime() 目的: ファイル未存在時の0返却確認"""
        mock_getmtime.side_effect = FileNotFoundError()

        result = get_log_mtime()

        assert result == 0


class TestGetTailLines:
    """get_tail_lines 関数のテスト"""

    def test_get_tail_lines_sufficient_lines(self):
        """検証対象: get_tail_lines() 目的: 十分な行数がある場合の末尾取得確認"""
        file_content = "line1\nline2\nline3\nline4\nline5\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_tail_lines("test.log", 3)

        assert result == ["line3\n", "line4\n", "line5\n"]

    def test_get_tail_lines_insufficient_lines(self):
        """検証対象: get_tail_lines() 目的: 行数不足時の全行返却確認"""
        file_content = "line1\nline2\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_tail_lines("test.log", 5)

        assert result == ["line1\n", "line2\n"]

    def test_get_tail_lines_file_not_found(self):
        """検証対象: get_tail_lines() 目的: ファイル未存在時の空リスト返却確認"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = get_tail_lines("nonexistent.log", 3)

        assert result == []


class TestFormatTimeDiff:
    """format_time_diff 関数のテスト"""

    def test_format_time_diff_seconds(self):
        """検証対象: format_time_diff() 目的: 秒単位の時間フォーマット確認"""
        assert format_time_diff(30) == "30秒"
        assert format_time_diff(59.9) == "59秒"

    def test_format_time_diff_minutes(self):
        """検証対象: format_time_diff() 目的: 分単位の時間フォーマット確認"""
        assert format_time_diff(60) == "1分0秒"
        assert format_time_diff(125) == "2分5秒"
        assert format_time_diff(3599) == "59分59秒"

    def test_format_time_diff_hours(self):
        """検証対象: format_time_diff() 目的: 時間単位の時間フォーマット確認"""
        assert format_time_diff(3600) == "1時間0分"
        assert format_time_diff(3665) == "1時間1分"
        assert format_time_diff(7325) == "2時間2分"


class TestIsTransferRemaining:
    """is_transfer_remaining 関数のテスト"""

    @patch("src.watchdog.log_watchdog")
    def test_is_transfer_remaining_true(self, mock_log):
        """検証対象: is_transfer_remaining() 目的: 転送残あり時のTrue返却確認"""
        onedrive_data = [{"name": "file1"}, {"name": "file2"}, {"name": "file3"}]
        skiplist_data = [{"name": "file1"}]

        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(onedrive_data)).return_value,
                mock_open(read_data=json.dumps(skiplist_data)).return_value,
            ]

            result = is_transfer_remaining()

        assert result is True
        mock_log.assert_called_with(
            "転送残判定: OneDrive=3件, スキップリスト=1件, 残り=2件"
        )

    @patch("src.watchdog.log_watchdog")
    def test_is_transfer_remaining_false(self, mock_log):
        """検証対象: is_transfer_remaining() 目的: 転送残なし時のFalse返却確認"""
        onedrive_data = [{"name": "file1"}]
        skiplist_data = [{"name": "file1"}]

        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(onedrive_data)).return_value,
                mock_open(read_data=json.dumps(skiplist_data)).return_value,
            ]

            result = is_transfer_remaining()

        assert result is False
        mock_log.assert_called_with(
            "転送残判定: OneDrive=1件, スキップリスト=1件, 残り=0件"
        )

    @patch("src.watchdog.log_watchdog")
    def test_is_transfer_remaining_error(self, mock_log):
        """検証対象: is_transfer_remaining() 目的: エラー時のTrue返却確認"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = is_transfer_remaining()

        assert result is True
        mock_log.assert_called()
        assert "転送残判定エラー" in mock_log.call_args[0][0]


class TestHandleProcessTermination:
    """_handle_process_termination 関数のテスト"""

    @patch("src.watchdog.is_transfer_remaining")
    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    def test_handle_process_termination_success_with_remaining(
        self, mock_time, mock_log, mock_remaining
    ):
        """検証対象: _handle_process_termination()
        目的: 正常終了・転送残あり時のrestart返却確認"""
        mock_time.return_value = 1000.0
        mock_remaining.return_value = True

        mock_proc = Mock()
        mock_proc.returncode = 0

        result = _handle_process_termination(mock_proc, start_time=900.0)

        assert result == "restart"
        mock_log.assert_any_call(
            "src.mainが自然終了しました (稼働時間: 1分40秒, 終了コード: 0)"
        )
        mock_log.assert_any_call("転送対象が残っているため、src.mainを再起動します")

    @patch("src.watchdog.is_transfer_remaining")
    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    def test_handle_process_termination_success_complete(
        self, mock_time, mock_log, mock_remaining
    ):
        """検証対象: _handle_process_termination()
        目的: 正常終了・転送完了時のcomplete返却確認"""
        mock_time.return_value = 1000.0
        mock_remaining.return_value = False

        mock_proc = Mock()
        mock_proc.returncode = 0

        result = _handle_process_termination(mock_proc, start_time=900.0)

        assert result == "complete"
        mock_log.assert_any_call("=== 監視終了（全転送完了） ===")

    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    def test_handle_process_termination_error(self, mock_time, mock_log):
        """検証対象: _handle_process_termination()
        目的: エラー終了時のrestart返却確認"""
        mock_time.return_value = 1000.0

        mock_proc = Mock()
        mock_proc.returncode = 1

        result = _handle_process_termination(mock_proc, start_time=900.0)

        assert result == "restart"
        mock_log.assert_called_with(
            "src.mainが自然終了しました (稼働時間: 1分40秒, 終了コード: 1)"
        )


class TestHandleFreezeDetection:
    """_handle_freeze_detection 関数のテスト"""

    @patch("src.watchdog.get_tail_lines")
    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    def test_handle_freeze_detection_with_logs(self, mock_time, mock_log, mock_tail):
        """検証対象: _handle_freeze_detection() 目的: フリーズ検出時の処理確認"""
        mock_time.return_value = 2000.0
        mock_tail.return_value = ["log line 1\n", "log line 2\n"]

        mock_proc = Mock()
        mock_proc.pid = 12345
        mock_proc.wait.return_value = None

        _handle_freeze_detection(mock_proc, start_time=1500.0, idle_time=300.0)

        mock_log.assert_any_call(
            "!!! フリーズ検出 !!! (稼働時間: 8分20秒, 無応答時間: 5分0秒)"
        )
        mock_log.assert_any_call("=== 直前のログ ===")
        mock_log.assert_any_call("  log line 1")
        mock_log.assert_any_call("  log line 2")
        mock_log.assert_any_call("=== 直前のログ終了 ===")
        mock_log.assert_any_call("src.main強制終了中... (PID: 12345)")
        mock_log.assert_any_call("src.main正常終了")

        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_with(timeout=10)

    @patch("src.watchdog.get_tail_lines")
    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    def test_handle_freeze_detection_timeout_kill(self, mock_time, mock_log, mock_tail):
        """検証対象: _handle_freeze_detection()
        目的: 終了タイムアウト時のKILL処理確認"""
        mock_time.return_value = 2000.0
        mock_tail.return_value = []

        mock_proc = Mock()
        mock_proc.pid = 12345
        mock_proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 10), None]

        _handle_freeze_detection(mock_proc, start_time=1500.0, idle_time=300.0)

        mock_log.assert_any_call("強制終了タイムアウト、KILL送信")
        mock_log.assert_any_call("src.mainをKILLしました")

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
        assert mock_proc.wait.call_count == 2


class TestStartMainProcess:
    """_start_main_process 関数のテスト"""

    @patch("subprocess.Popen")
    @patch("os.makedirs")
    @patch("src.watchdog.log_watchdog")
    def test_start_main_process(self, mock_log, mock_makedirs, mock_popen):
        """検証対象: _start_main_process() 目的: プロセス起動の動作確認"""
        mock_proc = Mock()
        mock_proc.pid = 12345
        mock_popen.return_value = mock_proc

        with patch("builtins.open", mock_open()):
            result = _start_main_process()

        assert result == mock_proc
        mock_makedirs.assert_called_once_with("logs", exist_ok=True)
        mock_log.assert_called_with("src.main起動完了 (PID: 12345)")
        mock_popen.assert_called_once()


class TestMonitorProcess:
    """_monitor_process 関数のテスト"""

    @patch("src.watchdog.get_log_mtime")
    @patch("time.sleep")
    @patch("time.time")
    def test_monitor_process_natural_termination(
        self, mock_time, mock_sleep, mock_mtime
    ):
        """検証対象: _monitor_process() 目的: プロセス自然終了時の検出確認"""
        mock_proc = Mock()
        mock_proc.poll.side_effect = [None, 0]  # 1回目は実行中、2回目は終了
        mock_mtime.return_value = 1000.0
        mock_time.return_value = 2000.0

        with patch(
            "src.watchdog._handle_process_termination", return_value="complete"
        ) as mock_handle:
            result = _monitor_process(mock_proc, start_time=1500.0)

        assert result == "complete"
        mock_handle.assert_called_once_with(mock_proc, 1500.0)

    @patch("src.watchdog.get_log_mtime")
    @patch("time.sleep")
    @patch("time.time")
    def test_monitor_process_log_update(self, mock_time, mock_sleep, mock_mtime):
        """検証対象: _monitor_process() 目的: ログ更新時の監視継続確認"""
        mock_proc = Mock()
        mock_proc.poll.side_effect = [None, None, 0]  # 2回実行中、3回目で終了
        mock_mtime.side_effect = [
            1000.0,
            1000.0,
            1100.0,
        ]  # 初期値、1回目チェック、2回目でログ更新
        mock_time.side_effect = [2000.0, 2030.0, 2060.0]

        with patch("src.watchdog._handle_process_termination", return_value="complete"):
            result = _monitor_process(mock_proc, start_time=1500.0)

        assert result == "complete"
        assert mock_sleep.call_count >= 2

    @patch("src.watchdog.get_log_mtime")
    @patch("time.sleep")
    @patch("time.time")
    def test_monitor_process_timeout(self, mock_time, mock_sleep, mock_mtime):
        """検証対象: _monitor_process() 目的: タイムアウト時のフリーズ検出確認"""
        mock_proc = Mock()
        mock_proc.poll.side_effect = [None, None]  # 常に実行中
        mock_mtime.return_value = 1000.0  # ログ更新なし
        mock_time.side_effect = [2000.0, 2030.0, 2700.0]  # 10分以上経過

        with patch("src.watchdog._handle_freeze_detection") as mock_handle:
            result = _monitor_process(mock_proc, start_time=1500.0)

        assert result == "restart"
        mock_handle.assert_called_once()


class TestHandleKeyboardInterrupt:
    """_handle_keyboard_interrupt 関数のテスト"""

    @patch("src.watchdog.log_watchdog")
    def test_handle_keyboard_interrupt_with_running_process(self, mock_log):
        """検証対象: _handle_keyboard_interrupt() 目的: 実行中プロセスの停止処理確認"""
        mock_proc = Mock()
        mock_proc.poll.return_value = None  # 実行中
        mock_proc.wait.return_value = None

        _handle_keyboard_interrupt(mock_proc)

        mock_log.assert_any_call("監視停止要求を受信")
        mock_log.assert_any_call("src.mainを停止中...")
        mock_log.assert_any_call("=== 監視終了 ===")
        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once_with(timeout=10)

    @patch("src.watchdog.log_watchdog")
    def test_handle_keyboard_interrupt_with_terminated_process(self, mock_log):
        """検証対象: _handle_keyboard_interrupt() 目的: 終了済みプロセスの処理確認"""
        mock_proc = Mock()
        mock_proc.poll.return_value = 0  # 既に終了

        _handle_keyboard_interrupt(mock_proc)

        mock_log.assert_any_call("監視停止要求を受信")
        mock_log.assert_any_call("=== 監視終了 ===")
        mock_proc.terminate.assert_not_called()

    @patch("src.watchdog.log_watchdog")
    def test_handle_keyboard_interrupt_timeout_kill(self, mock_log):
        """検証対象: _handle_keyboard_interrupt()
        目的: 停止タイムアウト時のKILL処理確認"""
        mock_proc = Mock()
        mock_proc.poll.return_value = None
        mock_proc.wait.side_effect = subprocess.TimeoutExpired("cmd", 10)

        _handle_keyboard_interrupt(mock_proc)

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()


class TestMain:
    """main 関数のテスト"""

    @patch("src.watchdog._start_main_process")
    @patch("src.watchdog._monitor_process")
    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    def test_main_complete_on_first_run(
        self, mock_time, mock_log, mock_monitor, mock_start
    ):
        """検証対象: main() 目的: 初回実行で完了時の動作確認"""
        mock_time.return_value = 1000.0
        mock_proc = Mock()
        mock_start.return_value = mock_proc
        mock_monitor.return_value = "complete"

        main()

        mock_log.assert_any_call("=== 監視開始 ===")
        mock_start.assert_called_once()
        mock_monitor.assert_called_once_with(mock_proc, 1000.0)

    @patch("src.watchdog._start_main_process")
    @patch("src.watchdog._monitor_process")
    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    @patch("time.sleep")
    def test_main_restart_cycle(
        self, mock_sleep, mock_time, mock_log, mock_monitor, mock_start
    ):
        """検証対象: main() 目的: 再起動サイクルの動作確認"""
        mock_time.side_effect = [1000.0, 1100.0, 1200.0]  # start times
        mock_proc1 = Mock()
        mock_proc2 = Mock()
        mock_start.side_effect = [mock_proc1, mock_proc2]
        mock_monitor.side_effect = ["restart", "complete"]

        main()

        assert mock_start.call_count == 2
        assert mock_monitor.call_count == 2
        mock_log.assert_any_call("自動再起動準備中... (累計再起動回数: 1)")

    @patch("src.watchdog._start_main_process")
    @patch("src.watchdog._monitor_process")
    @patch("src.watchdog._handle_keyboard_interrupt")
    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    def test_main_keyboard_interrupt(
        self, mock_time, mock_log, mock_handle_interrupt, mock_monitor, mock_start
    ):
        """検証対象: main() 目的: キーボード割り込み時の処理確認"""
        mock_time.return_value = 1000.0
        mock_proc = Mock()
        mock_start.return_value = mock_proc
        mock_monitor.side_effect = KeyboardInterrupt()

        main()

        mock_handle_interrupt.assert_called_once_with(mock_proc)

    @patch("src.watchdog._start_main_process")
    @patch("src.watchdog._monitor_process")
    @patch("src.watchdog.log_watchdog")
    @patch("time.time")
    @patch("time.sleep")
    def test_main_short_runtime_delay(
        self, mock_sleep, mock_time, mock_log, mock_monitor, mock_start
    ):
        """検証対象: main() 目的: 短時間終了時の待機処理確認"""
        mock_time.side_effect = [1000.0, 1030.0, 1100.0]  # 30秒で終了、次回起動
        mock_proc1 = Mock()
        mock_proc2 = Mock()
        mock_start.side_effect = [mock_proc1, mock_proc2]
        mock_monitor.side_effect = ["restart", "complete"]

        main()

        mock_log.assert_any_call("短時間終了検出、5秒待機してから再起動")
        mock_sleep.assert_called_with(5)
