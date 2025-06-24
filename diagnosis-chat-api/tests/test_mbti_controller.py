"""
MBTIコントローラーのテスト
"""

import pytest
from unittest.mock import Mock
from src.controller.mbti_controller import MBTIController
from src.controller.type import StartConversationRequest, ProcessUserResponseRequest


class Test_MBTIコントローラー:
    """MBTIコントローラーのテスト"""

    def setup_method(self):
        """テストフィクスチャのセットアップ"""
        self.mock_service = Mock()
        self.controller = MBTIController(self.mock_service)

    @pytest.mark.asyncio
    async def test_start_conversation_success(self):
        """会話開始が正常に動作することをテスト"""
        # 準備
        request = StartConversationRequest(user_id="test_user_123")

        expected_response = {
            "status": "success",
            "messages": [
                {"content": "Let's start your MBTI assessment!", "role": "assistant"}
            ],
            "conversation_state": "active",
        }

        self.mock_service.start_conversation = Mock(return_value=expected_response)

        # 実行
        result = await self.controller.start_conversation(request)

        # 検証
        assert result == expected_response
        self.mock_service.start_conversation.assert_called_once_with("test_user_123")

    @pytest.mark.asyncio
    async def test_process_user_response_success(self):
        """ユーザー応答処理が正常に動作することをテスト"""
        # 準備
        request = ProcessUserResponseRequest(
            user_input="I prefer working alone", user_id="test_user_123"
        )

        expected_response = {
            "status": "success",
            "messages": [{"content": "Next question here", "role": "assistant"}],
            "conversation_state": "active",
        }

        self.mock_service.process_user_response = Mock(return_value=expected_response)

        # 実行
        result = await self.controller.process_user_response(request)

        # 検証
        assert result == expected_response
        self.mock_service.process_user_response.assert_called_once_with(
            "I prefer working alone", "test_user_123"
        )

    @pytest.mark.asyncio
    async def test_service_exception_handling(self):
        """サービス層からの例外が適切に処理されることをテスト"""
        # 準備
        request = StartConversationRequest(user_id="test_user_123")

        self.mock_service.start_conversation = Mock(
            side_effect=Exception("Service error")
        )

        # 実行・検証
        result = await self.controller.start_conversation(request)

        # Controller should handle exceptions and return error response
        assert result["status"] == "error"
        assert "message" in result

    @pytest.mark.asyncio
    async def test_invalid_user_id_handling(self):
        """無効なユーザーIDの処理をテスト"""
        # 準備
        request = StartConversationRequest(user_id="")

        # 実行
        result = await self.controller.start_conversation(request)

        # 検証
        assert result["status"] == "error"
        assert result["message"] == "User ID is required"

    @pytest.mark.asyncio
    async def test_empty_user_input_handling(self):
        """空のユーザー入力の処理をテスト"""
        # 準備
        request = ProcessUserResponseRequest(user_input="", user_id="test_user_123")

        # 実行
        result = await self.controller.process_user_response(request)

        # 検証
        assert result["status"] == "error"
        assert result["message"] == "User input is required"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
