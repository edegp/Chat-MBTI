"""
ワークフローゲートウェイのテスト
"""

import pytest
from unittest.mock import Mock, patch
from src.gateway.workflow_gateway import WorkflowGateway
from src.driver.langgraph_driver import LangGraphDriver


class Test_ワークフローゲートウェイ:
    """ワークフローゲートウェイのテストクラス"""

    @pytest.fixture
    def mock_langgraph_driver(self):
        """LangGraphDriverのモック"""
        return Mock(spec=LangGraphDriver)

    @pytest.fixture
    def workflow_gateway(self, mock_langgraph_driver):
        """ワークフローゲートウェイのインスタンス"""
        return WorkflowGateway(mock_langgraph_driver)

    def test_会話フローの実行_成功(self, workflow_gateway, mock_langgraph_driver):
        """会話フローが正常に実行されることをテスト"""
        # Arrange
        user_input = "こんにちは"
        session_id = "test_session"
        user_id = "test_user"
        expected_result = {"status": "success"}
        mock_langgraph_driver.run_workflow.return_value = expected_result

        # Act
        result = workflow_gateway.execute_conversation_flow(
            user_input, session_id, user_id
        )

        # Assert
        assert result == expected_result
        mock_langgraph_driver.run_workflow.assert_called_once_with(
            user_input, session_id, user_id
        )

    def test_会話フローの実行_例外処理(self, workflow_gateway, mock_langgraph_driver):
        """会話フロー実行時の例外処理をテスト"""
        # Arrange
        user_input = "テスト入力"
        session_id = "test_session"
        user_id = "test_user"
        mock_langgraph_driver.run_workflow.side_effect = Exception("Driver error")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to execute conversation flow"):
            workflow_gateway.execute_conversation_flow(user_input, session_id, user_id)

    def test_会話状態の取得_成功(self, workflow_gateway, mock_langgraph_driver):
        """会話状態が正常に取得されることをテスト"""
        # Arrange
        session_id = "test_session"
        expected_state = {"messages": [], "next_display_order": 0}
        mock_langgraph_driver.get_state.return_value = expected_state

        # Act
        result = workflow_gateway.get_conversation_state(session_id)

        # Assert
        assert result == expected_state
        mock_langgraph_driver.get_state.assert_called_once_with(session_id)

    def test_会話状態の取得_例外処理(self, workflow_gateway, mock_langgraph_driver):
        """会話状態取得時の例外処理をテスト"""
        # Arrange
        session_id = "test_session"
        mock_langgraph_driver.get_state.side_effect = Exception("State error")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to get conversation state"):
            workflow_gateway.get_conversation_state(session_id)

    def test_会話オプションの取得_成功(self, workflow_gateway, mock_langgraph_driver):
        """会話オプションが正常に取得されることをテスト"""
        # Arrange
        session_id = "test_session"
        expected_options = ["オプション1", "オプション2", "オプション3"]
        mock_langgraph_driver.get_options.return_value = expected_options

        # Act
        result = workflow_gateway.get_conversation_options(session_id)

        # Assert
        assert result == expected_options
        mock_langgraph_driver.get_options.assert_called_once_with(session_id)

    def test_会話オプションの取得_例外処理(
        self, workflow_gateway, mock_langgraph_driver
    ):
        """会話オプション取得時の例外処理をテスト"""
        # Arrange
        session_id = "test_session"
        mock_langgraph_driver.get_options.side_effect = Exception("Options error")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to get conversation options"):
            workflow_gateway.get_conversation_options(session_id)


class Test_ワークフローゲートウェイ_統合:
    """ワークフローゲートウェイの統合テスト"""

    def test_エラーメッセージの一貫性(self):
        """エラーメッセージが適切にラップされていることをテスト"""
        # Arrange
        mock_driver = Mock(spec=LangGraphDriver)
        mock_driver.run_workflow.side_effect = ValueError("原因エラー")
        gateway = WorkflowGateway(mock_driver)

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            gateway.execute_conversation_flow("test", "session", "user")

        assert "Failed to execute conversation flow" in str(exc_info.value)
        assert "原因エラー" in str(exc_info.value)

    def test_初期化_正常(self):
        """ワークフローゲートウェイが正常に初期化されることをテスト"""
        # Arrange
        mock_driver = Mock(spec=LangGraphDriver)

        # Act
        gateway = WorkflowGateway(mock_driver)

        # Assert
        assert gateway.driver == mock_driver
