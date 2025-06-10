"""
Tests for Usecase Utils
"""

import pytest
from src.usecase.utils import _organize_chat_history


class TestUsecaseUtils:
    """Test cases for usecase utility functions"""

    def test_organize_chat_history_empty(self):
        """Test organizing empty chat history"""
        # Arrange
        messages = []

        # Act
        result = _organize_chat_history(messages)

        # Assert
        assert result == ""

    def test_organize_chat_history_single_message(self):
        """Test organizing single message"""
        # Arrange
        messages = [{"role": "assistant", "content": "Hello! What's your name?"}]

        # Act
        result = _organize_chat_history(messages)

        # Assert
        assert "assistant: Hello! What's your name?" in result

    def test_organize_chat_history_conversation(self):
        """Test organizing full conversation"""
        # Arrange
        messages = [
            {"role": "assistant", "content": "What's your favorite activity?"},
            {"role": "user", "content": "I like reading books"},
            {"role": "assistant", "content": "Do you prefer fiction or non-fiction?"},
            {"role": "user", "content": "I prefer fiction"},
        ]

        # Act
        result = _organize_chat_history(messages)

        # Assert
        expected_lines = [
            "assistant: What's your favorite activity?",
            "user: I like reading books",
            "assistant: Do you prefer fiction or non-fiction?",
            "user: I prefer fiction",
        ]

        for line in expected_lines:
            assert line in result

    def test_organize_chat_history_with_system_message(self):
        """Test organizing chat history with system message"""
        # Arrange
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "assistant", "content": "How can I help you?"},
            {"role": "user", "content": "Tell me a joke"},
        ]

        # Act
        result = _organize_chat_history(messages)

        # Assert
        assert "system: You are a helpful assistant" in result
        assert "assistant: How can I help you?" in result
        assert "user: Tell me a joke" in result

    def test_organize_chat_history_preserves_order(self):
        """Test that chat history preserves message order"""
        # Arrange
        messages = [
            {"role": "assistant", "content": "First message"},
            {"role": "user", "content": "Second message"},
            {"role": "assistant", "content": "Third message"},
        ]

        # Act
        result = _organize_chat_history(messages)

        # Assert
        lines = result.split("\n")
        lines = [line for line in lines if line.strip()]  # Remove empty lines

        assert "First message" in lines[0]
        assert "Second message" in lines[1]
        assert "Third message" in lines[2]

    def test_organize_chat_history_handles_none_content(self):
        """Test organizing chat history with None content"""
        # Arrange
        messages = [
            {"role": "assistant", "content": None},
            {"role": "user", "content": "Valid message"},
        ]

        # Act
        result = _organize_chat_history(messages)

        # Assert
        # Should handle None gracefully and not crash
        assert "user: Valid message" in result

    def test_organize_chat_history_handles_missing_fields(self):
        """Test organizing chat history with missing fields"""
        # Arrange
        messages = [
            {"role": "assistant"},  # Missing content
            {"content": "Message without role"},  # Missing role
            {"role": "user", "content": "Complete message"},
        ]

        # Act
        result = _organize_chat_history(messages)

        # Assert
        # Should handle incomplete messages gracefully
        assert "user: Complete message" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
