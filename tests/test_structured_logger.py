"""
構造化ログ機能のテスト
"""

import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.structured_logger import StructuredLogger, get_structured_logger


class TestStructuredLogger:
    """StructuredLogger クラスのテスト"""

    @pytest.fixture
    def fixed_utc_time(self):
        """UTC時刻を固定するフィクスチャ"""
        # 検証対象: 時刻依存処理のテスト
        # 目的: UTC時刻を固定して再現可能なテストを実現
        return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    @pytest.fixture
    def structured_logger(self):
        """テスト用 StructuredLogger インスタンス"""
        # 検証対象: StructuredLogger の初期化
        # 目的: テスト用のロガーインスタンスを作成
        return StructuredLogger("test_logger")

    def test_structured_logger_initialization(self, structured_logger):
        """構造化ロガーの初期化テスト"""
        # 検証対象: StructuredLogger.__init__()
        # 目的: ロガーが正しく初期化されることを確認
        assert structured_logger.logger.name == "test_logger"
        assert structured_logger.SENSITIVE_PATTERNS is not None

    def test_log_with_fixed_utc_time(self, structured_logger, fixed_utc_time):
        """UTC時刻固定でのログ出力テスト"""
        # 検証対象: StructuredLogger.log_structured() の時刻処理
        # 目的: UTC時刻が固定された状態でログが正しく出力されることを確認

        with patch("src.structured_logger.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_utc_time

            with patch.object(structured_logger.logger, "info") as mock_info:
                structured_logger.log_structured(
                    "INFO", "test_event", "Test message", test_field="test_value"
                )

                # ログが呼ばれたことを確認
                mock_info.assert_called_once()

                # ログデータの内容を確認
                log_call_args = mock_info.call_args[0][0]
                log_data = json.loads(log_call_args)

                assert log_data["timestamp"] == "2024-01-01T12:00:00Z"
                assert log_data["level"] == "INFO"
                assert log_data["event"] == "test_event"
                assert log_data["message"] == "Test message"
                assert log_data["module"] == "general"
                assert "trace_id" in log_data
                assert "span_id" in log_data
                assert log_data["test_field"] == "test_value"

    def test_mask_sensitive_data(self, structured_logger):
        """機密情報マスキングテスト"""
        # 検証対象: StructuredLogger.mask_sensitive_data()
        # 目的: 機密情報が適切にマスクされることを確認

        test_data = {
            "message": "client_secret=secret123 and access_token=token456",
            "normal_field": "normal_value",
        }

        masked_data = structured_logger.mask_sensitive_data(test_data)

        assert "[MASKED]" in masked_data["message"]
        assert "secret123" not in masked_data["message"]
        assert "token456" not in masked_data["message"]
        assert masked_data["normal_field"] == "normal_value"

    def test_generate_trace_id(self, structured_logger):
        """トレースID生成テスト"""
        # 検証対象: StructuredLogger.generate_trace_id()
        # 目的: ユニークなトレースIDが生成されることを確認

        trace_id1 = structured_logger.generate_trace_id()
        trace_id2 = structured_logger.generate_trace_id()

        assert trace_id1 != trace_id2
        assert len(trace_id1) > 0
        assert len(trace_id2) > 0

    def test_get_structured_logger_function(self):
        """get_structured_logger関数のテスト"""
        # 検証対象: get_structured_logger()
        # 目的: ファクトリ関数が正しくロガーインスタンスを返すことを確認

        logger = get_structured_logger("test_module")

        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "test_module"

    def test_log_transfer_event_with_utc_time(self, structured_logger, fixed_utc_time):
        """転送イベントログのUTC時刻テスト"""
        # 検証対象: StructuredLogger.log_transfer_event() の時刻処理
        # 目的: 転送イベントログでUTC時刻が正しく記録されることを確認

        file_info = {"name": "test_file.txt", "size": 1024, "path": "/test/path"}

        with patch("src.structured_logger.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_utc_time

            with patch.object(structured_logger.logger, "info") as mock_info:
                structured_logger.log_transfer_event(
                    "upload_start", file_info, trace_id="test-trace-123"
                )

                # ログが呼ばれたことを確認
                mock_info.assert_called_once()

                # ログデータの内容を確認
                log_call_args = mock_info.call_args[0][0]
                log_data = json.loads(log_call_args)

                assert log_data["timestamp"] == "2024-01-01T12:00:00Z"
                assert log_data["event"] == "upload_start"
                assert log_data["trace_id"] == "test-trace-123"
                assert log_data["file_name"] == "test_file.txt"
                assert log_data["file_size"] == 1024

    def test_log_with_none_values(self, structured_logger):
        """None値を含むログのテスト"""
        # 検証対象: StructuredLogger.log_structured() のNone値処理
        # 目的: None値が含まれていてもログが正常に出力されることを確認

        with patch.object(structured_logger.logger, "info") as mock_info:
            structured_logger.log_structured(
                "INFO",
                "test_event",
                "Test message",
                none_field=None,
                valid_field="valid_value",
            )

            # ログが呼ばれたことを確認
            mock_info.assert_called_once()

            # ログデータにNone値も含まれることを確認
            log_call_args = mock_info.call_args[0][0]
            log_data = json.loads(log_call_args)

            assert log_data["none_field"] is None
            assert log_data["valid_field"] == "valid_value"

    def test_required_fields_present(self, structured_logger):
        """必須フィールドの存在確認テスト"""
        # 検証対象: StructuredLogger.log_structured() の必須フィールド
        # 目的: 品質ルールで定義された必須フィールドが全て含まれることを確認

        with patch.object(structured_logger.logger, "info") as mock_info:
            structured_logger.log_structured(
                "INFO",
                "test_event",
                "Test message",
                user_id="test_user",
                request_id="req_123",
            )

            log_call_args = mock_info.call_args[0][0]
            log_data = json.loads(log_call_args)

            # 必須フィールドの確認
            required_fields = [
                "timestamp",
                "level",
                "event",
                "message",
                "logger",
                "module",
                "trace_id",
                "span_id",
            ]
            for field in required_fields:
                assert field in log_data, f"必須フィールド '{field}' が見つかりません"

            # オプショナルフィールドの確認
            assert log_data["user_id"] == "test_user"
            assert log_data["request_id"] == "req_123"

    def test_pii_masking(self, structured_logger):
        """PII情報マスキングテスト"""
        # 検証対象: StructuredLogger.mask_sensitive_data() のPII対応
        # 目的: メールアドレス等のPII情報が適切にマスクされることを確認

        test_data = {
            "message": "User email is user@example.com and password=secret123",
            "email_field": "admin@company.com",
        }

        masked_data = structured_logger.mask_sensitive_data(test_data)

        assert "user@example.com" not in masked_data["message"]
        assert "admin@company.com" not in masked_data["email_field"]
        assert "[MASKED]" in masked_data["message"]
        assert "[MASKED]" in masked_data["email_field"]

    def test_span_id_generation(self, structured_logger):
        """スパンID生成テスト"""
        # 検証対象: StructuredLogger.generate_span_id()
        # 目的: ユニークなスパンIDが生成されることを確認

        span_id1 = structured_logger.generate_span_id()
        span_id2 = structured_logger.generate_span_id()

        assert span_id1 != span_id2
        assert len(span_id1) > 0
        assert len(span_id2) > 0
