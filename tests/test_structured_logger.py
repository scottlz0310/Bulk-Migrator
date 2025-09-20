"""
構造化ログ機能のテスト
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from src.structured_logger import StructuredLogger, get_structured_logger


class TestStructuredLogger:
    """StructuredLogger クラスのテスト"""

    @pytest.fixture
    def fixed_utc_time(self):
        """UTC時刻を固定するフィクスチャ"""
        # 検証対象: 時刻依存処理のテスト
        # 目的: UTC時刻を固定して再現可能なテストを実現
        return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

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
        
        with patch('src.structured_logger.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_utc_time.replace(tzinfo=None)
            
            with patch.object(structured_logger.logger, 'info') as mock_info:
                structured_logger.log_structured("INFO", "test_event", "Test message", test_field="test_value")
                
                # ログが呼ばれたことを確認
                mock_info.assert_called_once()
                
                # ログデータの内容を確認
                log_call_args = mock_info.call_args[0][0]
                log_data = json.loads(log_call_args)
                
                assert log_data["timestamp"] == "2024-01-01T12:00:00Z"
                assert log_data["level"] == "INFO"
                assert log_data["event"] == "test_event"
                assert log_data["message"] == "Test message"
                assert log_data["test_field"] == "test_value"

    def test_mask_sensitive_data(self, structured_logger):
        """機密情報マスキングテスト"""
        # 検証対象: StructuredLogger.mask_sensitive_data()
        # 目的: 機密情報が適切にマスクされることを確認
        
        test_data = {
            "message": "client_secret=secret123 and access_token=token456",
            "normal_field": "normal_value"
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
        
        file_info = {
            "name": "test_file.txt",
            "size": 1024,
            "path": "/test/path"
        }
        
        with patch('src.structured_logger.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_utc_time.replace(tzinfo=None)
            
            with patch.object(structured_logger.logger, 'info') as mock_info:
                structured_logger.log_transfer_event(
                    "upload_start", 
                    file_info, 
                    trace_id="test-trace-123"
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
        
        with patch.object(structured_logger.logger, 'info') as mock_info:
            structured_logger.log_structured(
                "INFO", 
                "test_event", 
                "Test message",
                none_field=None,
                valid_field="valid_value"
            )
            
            # ログが呼ばれたことを確認
            mock_info.assert_called_once()
            
            # ログデータにNone値も含まれることを確認
            log_call_args = mock_info.call_args[0][0]
            log_data = json.loads(log_call_args)
            
            assert log_data["none_field"] is None
            assert log_data["valid_field"] == "valid_value"