"""
Unit tests for the new MBTI architecture
"""

import pytest
from unittest.mock import Mock
from src.usecase.mbti_conversation_service import MBTIConversationService
from src.port.ports import WorkflowPort, QuestionRepositoryPort, SessionRepositoryPort


class TestMBTIConversationService:
    """Test cases for MBTI Conversation Service"""

    def setup_method(self):
        """Setup test dependencies"""
        self.mock_workflow = Mock(spec=WorkflowPort)
        self.mock_question_repo = Mock(spec=QuestionRepositoryPort)
        self.mock_session_repo = Mock(spec=SessionRepositoryPort)

        self.service = MBTIConversationService(
            workflow_port=self.mock_workflow,
            question_repository=self.mock_question_repo,
            session_repository=self.mock_session_repo,
        )

    def test_start_conversation_new_user(self):
        """Test starting conversation for new user"""
        # Arrange
        user_id = "test_user_123"
        session_id = "session_456"

        self.mock_session_repo.get_session_by_user.return_value = None
        self.mock_session_repo.create_session.return_value = session_id
        self.mock_workflow.execute_conversation_flow.return_value = {
            "messages": [
                {"content": "What's your favorite activity?", "role": "assistant"}
            ]
        }

        # Act
        result = self.service.start_conversation(user_id)

        # Assert
        assert result["status"] == "success"
        assert result["phase"] == "question"
        assert "What's your favorite activity?" in result["question"]
        assert result["session_id"] == session_id

        self.mock_session_repo.create_session.assert_called_once_with(user_id)
        self.mock_workflow.execute_conversation_flow.assert_called_once()

    def test_start_conversation_existing_user(self):
        """Test starting conversation for user with existing session"""
        # Arrange
        user_id = "test_user_123"
        existing_session_id = "existing_session_789"

        self.mock_session_repo.get_session_by_user.return_value = existing_session_id
        self.mock_workflow.execute_conversation_flow.return_value = {
            "messages": [
                {"content": "Let's continue where we left off.", "role": "assistant"}
            ]
        }

        # Act
        result = self.service.start_conversation(user_id)

        # Assert
        assert result["status"] == "success"
        assert result["session_id"] == existing_session_id

        # Should not create new session
        self.mock_session_repo.create_session.assert_not_called()

    def test_process_user_response_normal_flow(self):
        """Test processing user response in normal conversation flow"""
        # Arrange
        user_id = "test_user_123"
        session_id = "session_456"
        user_input = "I prefer outdoor activities"

        self.mock_session_repo.get_session_by_user.return_value = session_id
        self.mock_workflow.get_conversation_state.return_value = {
            "next_display_order": 5
        }
        self.mock_workflow.execute_conversation_flow.return_value = {
            "messages": [
                {
                    "content": "That's interesting! Do you prefer group activities?",
                    "role": "assistant",
                }
            ]
        }

        # Act
        result = self.service.process_user_response(user_input, user_id)

        # Assert
        assert result["status"] == "success"
        assert result["phase"] == "question"
        assert result["question_number"] == 6  # 5 + 1
        assert result["progress"] == 0.25  # 5/20

        self.mock_workflow.execute_conversation_flow.assert_called_once_with(
            user_input, session_id, user_id
        )

    def test_process_user_response_assessment_complete(self):
        """Test processing user response when assessment is complete"""
        # Arrange
        user_id = "test_user_123"
        session_id = "session_456"
        user_input = "Yes, I agree"

        self.mock_session_repo.get_session_by_user.return_value = session_id
        self.mock_workflow.get_conversation_state.return_value = {
            "next_display_order": 20  # Assessment complete
        }

        # Act
        result = self.service.process_user_response(user_input, user_id)

        # Assert
        assert result["status"] == "success"
        assert result["phase"] == "diagnosis"
        assert "Assessment complete" in result["message"]

        # Should not call workflow since assessment is complete
        self.mock_workflow.execute_conversation_flow.assert_not_called()

    def test_process_user_response_no_active_session(self):
        """Test processing user response when no active session exists"""
        # Arrange
        user_id = "test_user_123"
        user_input = "Hello"

        self.mock_session_repo.get_session_by_user.return_value = None

        # Act
        result = self.service.process_user_response(user_input, user_id)

        # Assert
        assert result["status"] == "error"
        assert result["phase"] == "error"
        assert "No active session found" in result["message"]

    def test_complete_assessment_success(self):
        """Test successful assessment completion"""
        # Arrange
        user_id = "test_user_123"
        session_id = "session_456"

        self.mock_session_repo.get_session_by_user.return_value = session_id
        self.mock_workflow.get_conversation_state.return_value = {
            "next_display_order": 20
        }

        # Act
        result = self.service.complete_assessment(user_id)

        # Assert
        assert result["status"] == "success"
        assert result["total_questions_answered"] == 20

        self.mock_session_repo.close_session.assert_called_once_with(session_id)

    def test_complete_assessment_insufficient_questions(self):
        """Test assessment completion with insufficient questions"""
        # Arrange
        user_id = "test_user_123"
        session_id = "session_456"

        self.mock_session_repo.get_session_by_user.return_value = session_id
        self.mock_workflow.get_conversation_state.return_value = {
            "next_display_order": 10  # Only 10 questions answered
        }

        # Act
        result = self.service.complete_assessment(user_id)

        # Assert
        assert result["status"] == "error"
        assert "Only 10/20 questions answered" in result["message"]

        # Should not close session
        self.mock_session_repo.close_session.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
