"""
src/filelock.py のテスト
"""

import errno
import os
import tempfile
from unittest.mock import patch

import pytest

from src.filelock import FileLock


class TestFileLock:
    """FileLock クラスのテスト"""

    def test_init(self):
        """検証対象: FileLock.__init__() 目的: 初期化の動作確認"""
        lock = FileLock("test.lock", timeout=5)

        assert lock.lockfile == "test.lock"
        assert lock.timeout == 5
        assert lock.fd is None

    def test_init_default_timeout(self):
        """検証対象: FileLock.__init__() 目的: デフォルトタイムアウトの確認"""
        lock = FileLock("test.lock")

        assert lock.timeout == 10

    @patch("os.open")
    @patch("os.write")
    @patch("os.getpid")
    def test_acquire_success(self, mock_getpid, mock_write, mock_open):
        """検証対象: FileLock.acquire() 目的: ロック取得成功時の動作確認"""
        mock_getpid.return_value = 12345
        mock_open.return_value = 42

        lock = FileLock("test.lock")
        lock.acquire()

        assert lock.fd == 42
        mock_open.assert_called_once_with(
            "test.lock", os.O_CREAT | os.O_EXCL | os.O_RDWR
        )
        mock_write.assert_called_once_with(42, b"12345")

    @patch("os.open")
    @patch("time.time")
    @patch("time.sleep")
    def test_acquire_timeout(self, mock_sleep, mock_time, mock_open):
        """検証対象: FileLock.acquire() 目的: タイムアウト時の例外発生確認"""
        # ファイルが既に存在するエラーを模擬
        mock_open.side_effect = OSError(errno.EEXIST, "File exists")
        mock_time.side_effect = [100.0, 105.0, 112.0]  # start, check, timeout

        lock = FileLock("test.lock", timeout=10)

        with pytest.raises(TimeoutError, match="Timeout waiting for lock: test.lock"):
            lock.acquire()

        assert mock_sleep.call_count >= 1

    @patch("os.open")
    @patch("time.time")
    @patch("time.sleep")
    @patch("os.write")
    @patch("os.getpid")
    def test_acquire_retry_then_success(
        self, mock_getpid, mock_write, mock_sleep, mock_time, mock_open
    ):
        """検証対象: FileLock.acquire() 目的: リトライ後成功時の動作確認"""
        mock_getpid.return_value = 12345
        mock_time.side_effect = [100.0, 105.0, 107.0]  # start, first check, success
        mock_open.side_effect = [
            OSError(errno.EEXIST, "File exists"),  # 1回目失敗
            42,  # 2回目成功
        ]

        lock = FileLock("test.lock", timeout=10)
        lock.acquire()

        assert lock.fd == 42
        assert mock_open.call_count == 2
        mock_sleep.assert_called_with(0.1)
        mock_write.assert_called_once_with(42, b"12345")

    @patch("os.open")
    def test_acquire_non_eexist_error(self, mock_open):
        """検証対象: FileLock.acquire() 目的: EEXIST以外のOSError時の例外再発生確認"""
        mock_open.side_effect = OSError(errno.EACCES, "Permission denied")

        lock = FileLock("test.lock")

        with pytest.raises(OSError) as exc_info:
            lock.acquire()

        assert exc_info.value.errno == errno.EACCES

    @patch("os.close")
    @patch("os.unlink")
    def test_release_with_fd(self, mock_unlink, mock_close):
        """検証対象: FileLock.release() 目的: ファイルディスクリプタありでの解放確認"""
        lock = FileLock("test.lock")
        lock.fd = 42

        lock.release()

        mock_close.assert_called_once_with(42)
        mock_unlink.assert_called_once_with("test.lock")
        assert lock.fd is None

    @patch("os.close")
    @patch("os.unlink")
    def test_release_without_fd(self, mock_unlink, mock_close):
        """検証対象: FileLock.release() 目的: ファイルディスクリプタなしでの解放確認"""
        lock = FileLock("test.lock")
        lock.fd = None

        lock.release()

        mock_close.assert_not_called()
        mock_unlink.assert_not_called()

    @patch("os.open")
    @patch("os.write")
    @patch("os.getpid")
    @patch("os.close")
    @patch("os.unlink")
    def test_context_manager_success(
        self, mock_unlink, mock_close, mock_getpid, mock_write, mock_open
    ):
        """検証対象: FileLock context manager 目的: with文での正常動作確認"""
        mock_getpid.return_value = 12345
        mock_open.return_value = 42

        lock = FileLock("test.lock")

        with lock as context_lock:
            assert context_lock is lock
            assert lock.fd == 42

        mock_close.assert_called_once_with(42)
        mock_unlink.assert_called_once_with("test.lock")
        assert lock.fd is None

    @patch("os.open")
    @patch("os.write")
    @patch("os.getpid")
    @patch("os.close")
    @patch("os.unlink")
    def test_context_manager_with_exception(
        self, mock_unlink, mock_close, mock_getpid, mock_write, mock_open
    ):
        """検証対象: FileLock context manager 目的: 例外発生時の適切な解放確認"""
        mock_open.return_value = 42
        mock_getpid.return_value = 12345

        lock = FileLock("test.lock")

        with pytest.raises(ValueError):
            with lock:
                raise ValueError("test exception")

        mock_close.assert_called_once_with(42)
        mock_unlink.assert_called_once_with("test.lock")
        assert lock.fd is None

    def test_integration_with_real_files(self):
        """検証対象: FileLock integration 目的: 実ファイルでの統合テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile = os.path.join(temp_dir, "test.lock")

            # 1つ目のロック取得
            lock1 = FileLock(lockfile, timeout=1)
            lock1.acquire()

            try:
                # 2つ目のロック取得（タイムアウトするはず）
                lock2 = FileLock(lockfile, timeout=1)
                with pytest.raises(TimeoutError):
                    lock2.acquire()

                # ロックファイルが存在することを確認
                assert os.path.exists(lockfile)

                # PIDが書き込まれていることを確認
                with open(lockfile, "rb") as f:
                    content = f.read()
                    assert content == str(os.getpid()).encode()

            finally:
                lock1.release()

            # ロックファイルが削除されていることを確認
            assert not os.path.exists(lockfile)

    def test_integration_context_manager_with_real_files(self):
        """検証対象: FileLock context manager integration
        目的: 実ファイルでのwith文統合テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile = os.path.join(temp_dir, "test.lock")

            with FileLock(lockfile, timeout=1):
                # ロックファイルが存在することを確認
                assert os.path.exists(lockfile)

                # 別のロックが取得できないことを確認
                lock2 = FileLock(lockfile, timeout=1)
                with pytest.raises(TimeoutError):
                    lock2.acquire()

            # with文を抜けた後、ロックファイルが削除されていることを確認
            assert not os.path.exists(lockfile)

    def test_multiple_locks_different_files(self):
        """検証対象: FileLock multiple instances
        目的: 異なるファイルでの複数ロック確認"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile1 = os.path.join(temp_dir, "test1.lock")
            lockfile2 = os.path.join(temp_dir, "test2.lock")

            with FileLock(lockfile1, timeout=1) as lock1:
                with FileLock(lockfile2, timeout=1) as lock2:
                    # 両方のロックファイルが存在することを確認
                    assert os.path.exists(lockfile1)
                    assert os.path.exists(lockfile2)
                    assert lock1.fd != lock2.fd

            # 両方のロックファイルが削除されていることを確認
            assert not os.path.exists(lockfile1)
            assert not os.path.exists(lockfile2)
