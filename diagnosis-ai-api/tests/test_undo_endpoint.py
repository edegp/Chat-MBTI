#!/usr/bin/env python3
"""
Test undo endpoint functionality
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.api.app import app


class TestUndoEndpoint:
    """Test class for undo endpoint"""

    def setup_method(self):
        """Setup test fixtures"""
        self.client = TestClient(app)

    @patch("src.controller.mbti_controller.get_mbti_controller")
    def test_undo_last_answer_success(self, mock_get_controller):
        """Test successful undo of last answer"""
        # Setup mock controller
        mock_controller = Mock()
        mock_controller.undo_last_answer.return_value = {
            "status": "success",
            "question": "What is your preferred work environment?",
            "session_id": "test_session_123",
        }
        mock_get_controller.return_value = mock_controller

        # Make request
        response = self.client.delete("/api/v1/data-collection/conversation/undo")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Last answer undone successfully"
        assert data["data"]["question"] == "What is your preferred work environment?"
        assert data["data"]["session_id"] == "test_session_123"
        assert data["data"]["status"] == "success"

    @patch("src.controller.mbti_controller.get_mbti_controller")
    def test_undo_last_answer_error(self, mock_get_controller):
        """Test undo endpoint with error"""
        # Setup mock controller
        mock_controller = Mock()
        mock_controller.undo_last_answer.return_value = {
            "status": "error",
            "message": "No previous answers to undo",
        }
        mock_get_controller.return_value = mock_controller

        # Make request
        response = self.client.delete("/api/v1/data-collection/conversation/undo")

        # Should still return 422 for validation error
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
