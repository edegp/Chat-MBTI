"""
APIコントローラー層のエラーハンドリングテスト

TDDアプローチでコントローラー層の包括的なエラーハンドリングをテストします。
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.controller.mbti_controller import MBTIController
from src.exceptions import (
    MBTIApplicationError,
    ValidationError,
    InvalidInputError,
    SessionNotFoundError,
    AssessmentIncompleteError,
    DatabaseError,
    WorkflowError,
    create_error_response,
)


class TestMBTIControllerErrorHandling:
    """MBTIControllerのエラーハンドリングテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_service = Mock()
        self.controller = MBTIController(self.mock_service)

    @pytest.mark.asyncio
    async def test_start_conversation_missing_user_id(self):
        """会話開始時のユーザーID不足エラーテスト"""
        # Given: ユーザーIDが不足したリクエスト
        request = Mock()
        request.user_id = None

        # When: 会話開始を試行
        result = await self.controller.start_conversation(request)

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User ID is required" in result["message"]

    @pytest.mark.asyncio
    async def test_start_conversation_service_error(self):
        """会話開始時のサービスエラーテスト"""
        # Given: サービスがカスタム例外を発生させる
        request = Mock()
        request.user_id = "user123"
        self.mock_service.start_conversation.side_effect = SessionNotFoundError(
            "Session not found", details={"user_id": "user123"}
        )

        # When: 会話開始を試行
        result = await self.controller.start_conversation(request)

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "SessionNotFoundError"
        assert "Session not found" in result["message"]
        assert result["details"]["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_start_conversation_unexpected_error(self):
        """会話開始時の予期しないエラーテスト"""
        # Given: サービスが予期しない例外を発生させる
        request = Mock()
        request.user_id = "user123"
        self.mock_service.start_conversation.side_effect = ValueError(
            "Unexpected error"
        )

        # When: 会話開始を試行
        result = await self.controller.start_conversation(request)

        # Then: 汎用的なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "MBTIApplicationError"
        assert "Internal server error" in result["message"]

    @pytest.mark.asyncio
    async def test_process_user_response_missing_user_id(self):
        """レスポンス処理時のユーザーID不足エラーテスト"""
        # Given: ユーザーIDが不足したリクエスト
        request = Mock()
        request.user_id = None
        request.user_input = "test input"

        # When: レスポンス処理を試行
        result = await self.controller.process_user_response(request)

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User ID is required" in result["message"]

    @pytest.mark.asyncio
    async def test_process_user_response_missing_input(self):
        """レスポンス処理時の入力不足エラーテスト"""
        # Given: 入力が不足したリクエスト
        request = Mock()
        request.user_id = "user123"
        request.user_input = ""

        # When: レスポンス処理を試行
        result = await self.controller.process_user_response(request)

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User input is required" in result["message"]

    @pytest.mark.asyncio
    async def test_process_user_response_whitespace_input(self):
        """レスポンス処理時の空白文字入力エラーテスト"""
        # Given: 空白文字のみの入力
        request = Mock()
        request.user_id = "user123"
        request.user_input = "   "

        # When: レスポンス処理を試行
        result = await self.controller.process_user_response(request)

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User input is required" in result["message"]

    @pytest.mark.asyncio
    async def test_process_user_response_database_error(self):
        """レスポンス処理時のデータベースエラーテスト"""
        # Given: サービスがデータベースエラーを発生させる
        request = Mock()
        request.user_id = "user123"
        request.user_input = "test input"
        self.mock_service.process_user_response.side_effect = DatabaseError(
            "Database connection failed"
        )

        # When: レスポンス処理を試行
        result = await self.controller.process_user_response(request)

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "DatabaseError"
        assert "Database connection failed" in result["message"]

    @pytest.mark.asyncio
    async def test_get_user_session_service_error(self):
        """ユーザーセッション取得時のサービスエラーテスト"""
        # Given: サービスがセッションエラーを発生させる
        self.mock_service.get_user_session.side_effect = SessionNotFoundError(
            "Session not found"
        )

        # When: ユーザーセッション取得を試行
        result = await self.controller.get_user_session()

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "SessionNotFoundError"
        assert "Session not found" in result["message"]

    @pytest.mark.asyncio
    async def test_submit_answer_missing_user_id(self):
        """回答送信時のユーザーID不足エラーテスト"""
        # When: ユーザーIDなしで回答送信を試行
        result = await self.controller.submit_answer("", "test answer")

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User ID is required" in result["message"]

    @pytest.mark.asyncio
    async def test_submit_answer_missing_answer(self):
        """回答送信時の回答不足エラーテスト"""
        # When: 回答なしで送信を試行
        result = await self.controller.submit_answer("user123", "")

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "Answer is required" in result["message"]

    @pytest.mark.asyncio
    async def test_submit_answer_workflow_error(self):
        """回答送信時のワークフローエラーテスト"""
        # Given: サービスがワークフローエラーを発生させる
        self.mock_service.process_user_response.side_effect = WorkflowError(
            "Workflow execution failed"
        )

        # When: 回答送信を試行
        result = await self.controller.submit_answer("user123", "test answer")

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "WorkflowError"
        assert "Workflow execution failed" in result["message"]

    @pytest.mark.asyncio
    async def test_get_options_missing_user_id(self):
        """オプション取得時のユーザーID不足エラーテスト"""
        # When: ユーザーIDなしでオプション取得を試行
        result = await self.controller.get_options("")

        # Then: 適切なエラーレスポンスが返される（optionsフィールド付き）
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User ID is required" in result["message"]
        assert "options" in result
        assert result["options"] == []

    @pytest.mark.asyncio
    async def test_get_options_service_error(self):
        """オプション取得時のサービスエラーテスト"""
        # Given: サービスがエラーを発生させる
        self.mock_service.get_answer_options.side_effect = AssessmentIncompleteError(
            "Assessment not complete"
        )

        # When: オプション取得を試行
        result = await self.controller.get_options("user123")

        # Then: 適切なエラーレスポンスが返される（optionsフィールド付き）
        assert result["status"] == "error"
        assert result["error_type"] == "AssessmentIncompleteError"
        assert "Assessment not complete" in result["message"]
        assert "options" in result
        assert result["options"] == []

    @pytest.mark.asyncio
    async def test_get_progress_missing_user_id(self):
        """進捗取得時のユーザーID不足エラーテスト"""
        # When: ユーザーIDなしで進捗取得を試行
        result = await self.controller.get_progress("")

        # Then: 適切なエラーレスポンスが返される（progressフィールド付き）
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User ID is required" in result["message"]
        assert "progress" in result
        assert result["progress"] == 0.0

    @pytest.mark.asyncio
    async def test_get_progress_service_error(self):
        """進捗取得時のサービスエラーテスト"""
        # Given: サービスがエラーを発生させる
        self.mock_service.get_conversation_progress.side_effect = SessionNotFoundError(
            "Session not found"
        )

        # When: 進捗取得を試行
        result = await self.controller.get_progress("user123")

        # Then: 適切なエラーレスポンスが返される（progressフィールド付き）
        assert result["status"] == "error"
        assert result["error_type"] == "SessionNotFoundError"
        assert "Session not found" in result["message"]
        assert "progress" in result
        assert result["progress"] == 0.0

    @pytest.mark.asyncio
    async def test_complete_assessment_missing_user_id(self):
        """診断完了時のユーザーID不足エラーテスト"""
        # When: ユーザーIDなしで診断完了を試行
        result = await self.controller.complete_assessment("")

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User ID is required" in result["message"]

    @pytest.mark.asyncio
    async def test_complete_assessment_incomplete_error(self):
        """診断完了時の診断未完了エラーテスト"""
        # Given: サービスが診断未完了エラーを発生させる
        self.mock_service.complete_assessment.side_effect = AssessmentIncompleteError(
            "Assessment is not complete yet"
        )

        # When: 診断完了を試行
        result = await self.controller.complete_assessment("user123")

        # Then: 適切なエラーレスポンスが返される
        assert result["status"] == "error"
        assert result["error_type"] == "AssessmentIncompleteError"
        assert "Assessment is not complete yet" in result["message"]

    @pytest.mark.asyncio
    async def test_get_conversation_history_missing_user_id(self):
        """会話履歴取得時のユーザーID不足エラーテスト"""
        # When: ユーザーIDなしで会話履歴取得を試行
        result = await self.controller.get_conversation_history("")

        # Then: 適切なエラーレスポンスが返される（historyフィールド付き）
        assert result["status"] == "error"
        assert result["error_type"] == "InvalidInputError"
        assert "User ID is required" in result["message"]
        assert "history" in result
        assert result["history"] == []

    @pytest.mark.asyncio
    async def test_get_conversation_history_service_error(self):
        """会話履歴取得時のサービスエラーテスト"""
        # Given: サービスがデータベースエラーを発生させる
        self.mock_service.get_conversation_history.side_effect = DatabaseError(
            "Failed to retrieve history"
        )

        # When: 会話履歴取得を試行
        result = await self.controller.get_conversation_history("user123")

        # Then: 適切なエラーレスポンスが返される（historyフィールド付き）
        assert result["status"] == "error"
        assert result["error_type"] == "DatabaseError"
        assert "Failed to retrieve history" in result["message"]
        assert "history" in result
        assert result["history"] == []

    @pytest.mark.asyncio
    async def test_successful_operations_logging(self):
        """成功時の情報ログ出力テスト"""
        # Given: サービスが正常な結果を返す
        request = Mock()
        request.user_id = "user123"
        request.user_input = "test input"
        expected_result = {"status": "success", "data": "test"}
        self.mock_service.start_conversation.return_value = expected_result
        self.mock_service.process_user_response.return_value = expected_result

        # When: 各操作を実行
        start_result = await self.controller.start_conversation(request)
        process_result = await self.controller.process_user_response(request)

        # Then: 成功結果が返される
        assert start_result == expected_result
        assert process_result == expected_result
        # 注：ログ出力の確認は実際のテスト環境では別途モックを使用
