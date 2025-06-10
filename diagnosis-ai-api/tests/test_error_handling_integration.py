"""
エラーハンドリング統合テスト

TDDで実装されたエラーハンドリングが正しく動作することを確認します。
"""

import pytest
from unittest.mock import Mock
import sys
import os

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.exceptions import (
    MBTIApplicationError,
    ValidationError,
    AuthenticationError,
    DatabaseError,
    LLMError,
    create_error_response,
)


class TestErrorHandlingIntegration:
    """エラーハンドリング統合テスト"""

    def test_custom_exception_creation_and_logging(self):
        """カスタム例外の作成とログ出力テスト"""
        # Arrange
        mock_logger = Mock()
        error_message = "テストエラーメッセージ"
        error_details = {"user_id": "test_123", "operation": "test_op"}

        # Act
        error = ValidationError(error_message, error_details)
        error.log_error(mock_logger)

        # Assert
        assert error.message == error_message
        assert error.details == error_details
        mock_logger.error.assert_called_once()

    def test_error_response_creation(self):
        """エラーレスポンス生成テスト"""
        # Arrange
        error = DatabaseError(
            "データベース接続エラー", {"host": "localhost", "port": 5432}
        )

        # Act
        response = create_error_response(error)

        # Assert
        assert response["status"] == "error"
        assert response["message"] == "データベース接続エラー"
        assert response["error_type"] == "DatabaseError"
        assert response["details"]["host"] == "localhost"
        assert response["details"]["port"] == 5432

    def test_exception_hierarchy(self):
        """例外階層のテスト"""
        # Arrange & Act
        auth_error = AuthenticationError("認証失敗")
        db_error = DatabaseError("DB接続失敗")
        llm_error = LLMError("LLM呼び出し失敗")

        # Assert
        assert isinstance(auth_error, MBTIApplicationError)
        assert isinstance(db_error, MBTIApplicationError)
        assert isinstance(llm_error, MBTIApplicationError)

    def test_error_logging_with_structured_data(self):
        """構造化データ付きエラーログのテスト"""
        # Arrange
        mock_logger = Mock()
        error = LLMError(
            "レート制限に到達しました",
            {"model": "gemini-2.0-flash", "requests_per_minute": 60, "retry_after": 30},
        )

        # Act
        error.log_error(mock_logger)

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "LLMError: レート制限に到達しました" in call_args[0][0]
        assert call_args[1]["extra"]["details"]["model"] == "gemini-2.0-flash"
        assert call_args[1]["extra"]["details"]["requests_per_minute"] == 60

    def test_error_details_optional(self):
        """エラー詳細が省略可能であることをテスト"""
        # Act
        error = ValidationError("シンプルなエラー")

        # Assert
        assert error.message == "シンプルなエラー"
        assert error.details == {}

    def test_error_message_in_str_representation(self):
        """文字列表現でエラーメッセージが含まれることをテスト"""
        # Arrange
        error_message = "テスト用エラーメッセージ"
        error = ValidationError(error_message)

        # Act & Assert
        assert str(error) == error_message


class TestErrorHandlingInRealScenarios:
    """実際のシナリオでのエラーハンドリングテスト"""

    def test_database_connection_failure_scenario(self):
        """データベース接続失敗シナリオ"""
        # Arrange
        mock_logger = Mock()

        # Act
        try:
            # データベース接続失敗をシミュレート
            raise DatabaseError(
                "PostgreSQL接続に失敗しました",
                {
                    "host": "localhost",
                    "port": 5432,
                    "database": "diagnosis_ai",
                    "error_code": "08006",
                },
            )
        except DatabaseError as e:
            e.log_error(mock_logger)
            response = create_error_response(e)

        # Assert
        assert response["error_type"] == "DatabaseError"
        assert "PostgreSQL接続に失敗しました" in response["message"]
        assert response["details"]["error_code"] == "08006"
        mock_logger.error.assert_called_once()

    def test_llm_rate_limit_scenario(self):
        """LLMレート制限シナリオ"""
        # Arrange
        mock_logger = Mock()

        # Act
        try:
            # LLMレート制限をシミュレート
            raise LLMError(
                "Gemini APIのレート制限に到達しました",
                {
                    "service": "gemini",
                    "limit_type": "requests_per_minute",
                    "current_usage": 60,
                    "limit": 60,
                    "reset_time": "2024-01-01T10:05:00Z",
                },
            )
        except LLMError as e:
            e.log_error(mock_logger)
            response = create_error_response(e)

        # Assert
        assert response["error_type"] == "LLMError"
        assert "レート制限" in response["message"]
        assert response["details"]["service"] == "gemini"
        assert response["details"]["current_usage"] == 60
        mock_logger.error.assert_called_once()

    def test_validation_error_scenario(self):
        """入力バリデーションエラーシナリオ"""
        # Arrange
        mock_logger = Mock()

        # Act
        try:
            # 入力バリデーション失敗をシミュレート
            raise ValidationError(
                "回答が空です",
                {
                    "field": "answer",
                    "value": "",
                    "constraint": "not_empty",
                    "user_id": "user_123",
                },
            )
        except ValidationError as e:
            e.log_error(mock_logger)
            response = create_error_response(e)

        # Assert
        assert response["error_type"] == "ValidationError"
        assert "回答が空です" in response["message"]
        assert response["details"]["field"] == "answer"
        assert response["details"]["constraint"] == "not_empty"
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
