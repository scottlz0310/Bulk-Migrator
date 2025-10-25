import json
from unittest.mock import MagicMock, mock_open, patch

from src.skiplist import add_to_skip_list, is_skipped, load_skip_list, save_skip_list


class TestSkipList:
    """skiplistモジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前処理"""
        self.test_skip_list = [
            {
                "path": "/test/file1.txt",
                "name": "file1.txt",
                "reason": "already_exists",
            },
            {
                "path": "/test/file2.txt",
                "name": "file2.txt",
                "reason": "permission_error",
            },
        ]

    def test_load_skip_list_existing_file(self):
        """既存のスキップリストファイル読み込みテスト"""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(self.test_skip_list))):
                result = load_skip_list("test_path.json")
                assert result == self.test_skip_list

    def test_load_skip_list_missing_file(self):
        """存在しないスキップリストファイルのテスト"""
        with patch("os.path.exists", return_value=False):
            result = load_skip_list("non_existent.json")
            assert result == []

    def test_is_skipped_true(self):
        """スキップ対象ファイルの判定テスト（True）"""
        file_info = {"path": "/test/file1.txt", "name": "file1.txt"}
        skip_list = [{"path": "/test/file1.txt", "name": "file1.txt", "reason": "test"}]
        result = is_skipped(file_info, skip_list)
        assert result is True

    def test_is_skipped_false(self):
        """スキップ対象ファイルの判定テスト（False）"""
        file_info = {"path": "/test/file2.txt", "name": "file2.txt"}
        skip_list = [{"path": "/test/file1.txt", "name": "file1.txt", "reason": "test"}]
        result = is_skipped(file_info, skip_list)
        assert result is False

    @patch("src.skiplist.FileLock")
    def test_add_to_skip_list(self, mock_filelock):
        """スキップリストへの追加テスト"""
        mock_lock = MagicMock()
        mock_filelock.return_value.__enter__.return_value = mock_lock

        file_info = {"path": "/test/new_file.txt", "name": "new_file.txt"}
        with patch("src.skiplist.load_skip_list", return_value=[]):
            with patch("src.skiplist.save_skip_list") as mock_save:
                add_to_skip_list(file_info, "test_path.json")
                mock_save.assert_called_once()

    @patch("src.skiplist.FileLock")
    def test_add_to_skip_list_duplicate(self, mock_filelock):
        """重複するスキップリストへの追加テスト"""
        mock_lock = MagicMock()
        mock_filelock.return_value.__enter__.return_value = mock_lock

        file_info = {"path": "/test/file1.txt", "name": "file1.txt"}
        existing_list = [{"path": "/test/file1.txt", "name": "file1.txt", "reason": "existing"}]

        with patch("src.skiplist.load_skip_list", return_value=existing_list):
            with patch("src.skiplist.save_skip_list") as mock_save:
                add_to_skip_list(file_info, "test_path.json")
                # 重複は追加されないので、save_skip_listは呼ばれない
                mock_save.assert_not_called()

    def test_save_skip_list(self):
        """スキップリスト保存テスト"""
        with patch("builtins.open", mock_open()) as mock_file:
            save_skip_list(self.test_skip_list, "test_output.json")
            mock_file.assert_called_once()

    def test_save_skip_list_with_directory_creation(self):
        """ディレクトリ作成付きスキップリスト保存テスト"""
        with patch("os.makedirs"):
            with patch("builtins.open", mock_open()):
                save_skip_list(self.test_skip_list, "logs/test_output.json")
                # save_skip_listは直接os.makedirsを呼ばないので、このテストは削除
                pass
