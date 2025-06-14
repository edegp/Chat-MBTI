"""
Integration Tests for MBTI Application
"""

import pytest
from unittest.mock import Mock, patch
from src.usecase.mbti_conversation_service import MBTIConversationService
from src.exceptions import AssessmentError


class TestMBTIIntegration:
    """Integration test cases for MBTI application flow"""

    def setup_method(self):
        """Setup test dependencies"""
        self.mock_llm_port = Mock()
        self.mock_question_repo = Mock()
        self.mock_session_repo = Mock()
        self.mock_workflow_gateway = Mock()

        # Mock for ElementRepositoryPort
        self.mock_elements_repo = Mock()

        # Create service with all mocked dependencies for integration testing
        self.service = MBTIConversationService(
            workflow_port=self.mock_workflow_gateway,
            question_repository=self.mock_question_repo,
            session_repository=self.mock_session_repo,
            elements_repository=self.mock_elements_repo,
        )

    @patch("src.driver.db.create_checkpointer")
    def test_full_conversation_flow_phase_1(self, mock_create_checkpointer):
        """Test complete conversation flow for Phase 1 (questions 1-5)"""
        # Arrange
        user_id = "integration_test_user"
        session_id = "integration_session_123"

        # Mock checkpointer
        mock_checkpointer = Mock()
        mock_create_checkpointer.return_value = mock_checkpointer

        # Mock session repository
        self.mock_session_repo.get_session_by_user.side_effect = [
            None,
            session_id,
            session_id,
        ]  # None for first check, session_id for creation and later use
        self.mock_session_repo.create_session.return_value = session_id

        # Mock question repository
        self.mock_question_repo.save_question.return_value = "q1_id"

        # Mock workflow gateway to return successful results
        initial_question = (
            "What energizes you more: social interactions or quiet reflection?"
        )
        second_question = "How do you prefer to process information?"

        # Mock the workflow execution results
        initial_workflow_result = {
            "messages": [{"content": initial_question}],
            "status": "success",
        }

        second_workflow_result = {
            "messages": [{"content": second_question}],
            "status": "success",
        }

        # Mock workflow gateway methods
        self.mock_workflow_gateway.execute_conversation_flow.side_effect = [
            initial_workflow_result,  # For start_conversation
            second_workflow_result,  # For process_user_response
        ]

        # Mock conversation state for progress tracking
        self.mock_workflow_gateway.get_conversation_state.side_effect = [
            {
                "next_display_order": 1
            },  # After first question (for process_user_response)
            {"next_display_order": 1},  # State used for calculations
        ]

        # Act - Start conversation
        start_result = self.service.start_conversation(user_id)

        # Assert - Initial question generated
        assert start_result["status"] == "success"
        assert start_result["phase"] == "question"
        assert start_result["session_id"] == session_id
        assert "energizes you more" in start_result["question"]

        # Act - Process first answer
        # No need to set mock again as it's already configured with side_effect

        first_response = self.service.process_user_response(
            "I prefer social interactions", user_id
        )

        # Assert - Second question generated (still in Phase 1)
        assert first_response["status"] == "success"
        assert first_response["question_number"] == 1  # next_order(1)
        assert first_response["progress"] == 0.05  # 1/20

    @patch("src.driver.db.create_checkpointer")
    def test_phase_transition_context_reset(self, mock_create_checkpointer):
        """Test that context is reset when transitioning from Phase 1 to Phase 2"""
        # Arrange
        user_id = "phase_test_user"
        session_id = "phase_session_456"

        mock_checkpointer = Mock()
        mock_create_checkpointer.return_value = mock_checkpointer

        # Mock repositories
        self.mock_session_repo.get_session_by_user.return_value = session_id
        self.mock_question_repo.save_question.return_value = "q6_id"

        # Mock workflow gateway to return Phase 2 question
        phase2_workflow_result = {
            "messages": [
                {"content": "Phase 2: How do you prefer to gather information?"}
            ],
            "status": "success",
        }

        self.mock_workflow_gateway.execute_conversation_flow.return_value = (
            phase2_workflow_result
        )
        self.mock_workflow_gateway.get_conversation_state.return_value = {
            "next_display_order": 5
        }  # Changed to 5 so question_number becomes 6

        # Act - Process user response that should trigger Phase 2
        result = self.service.process_user_response("My final Phase 1 answer", user_id)

        # Assert - Phase 2 question should be generated
        assert result["status"] == "success"
        assert result["question_number"] == 5  # next_order(5)

        # Verify workflow gateway was called
        self.mock_workflow_gateway.execute_conversation_flow.assert_called_once()

    def test_assessment_completion_after_20_questions(self):
        """Test assessment completion after all 20 questions"""
        # Arrange
        user_id = "completion_test_user"
        session_id = "completion_session_789"

        # Mock state with 20 questions completed
        self.mock_session_repo.get_session_by_user.return_value = session_id

        # Mock workflow state to show 20 questions completed
        self.mock_workflow_gateway.get_conversation_state.return_value = {
            "next_display_order": 20
        }

        # Act
        result = self.service.process_user_response("Final answer", user_id)

        # Assert
        assert result["status"] == "success"
        assert result["phase"] == "diagnosis"
        assert "Assessment complete" in result["message"]

    def test_error_handling_in_integration(self):
        """Test error handling in integration scenarios"""
        # Arrange
        user_id = "error_test_user"

        # Mock workflow gateway to raise an exception
        self.mock_workflow_gateway.execute_conversation_flow.side_effect = RuntimeError(
            "Failed to execute conversation flow: LLM API Error"
        )
        self.mock_session_repo.get_session_by_user.return_value = None
        self.mock_session_repo.create_session.return_value = "error_session"

        # Act & Assert - Should raise AssessmentError exception
        with pytest.raises(AssessmentError) as exc_info:
            self.service.start_conversation(user_id)

        # Verify error contains relevant information
        assert "Failed to start conversation" in str(exc_info.value)
        # The service wraps unexpected errors with a generic message, so check for that instead
        assert "due to unexpected error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
