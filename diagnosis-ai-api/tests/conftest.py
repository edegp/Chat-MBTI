"""
Test configuration for pytest

This file configures the test environment and sets up necessary environment variables
and mocks to prevent tests from requiring actual external services.
"""

import os
import pytest
from unittest.mock import patch, Mock

# Set up environment variables for testing before any imports
os.environ.setdefault("GEMINI_API_KEY", "test-api-key-for-testing")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("DB_APP_USER", "postgres")
os.environ.setdefault("DB_APP_PASS", "postgres")
os.environ.setdefault("DB_ADMIN_USER", "postgres")
os.environ.setdefault("DB_ADMIN_PASS", "postgres")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables and configurations"""
    # Ensure environment variables are set for the entire test session
    os.environ["GEMINI_API_KEY"] = "test-api-key-for-testing"
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"

    # Mock external services to prevent real API calls during testing
    with (
        patch("google.generativeai.configure"),
        patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_llm,
    ):
        # Configure mock LLM to return predictable responses
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = "Mock LLM response"
        mock_llm.return_value = mock_llm_instance

        yield


@pytest.fixture
def mock_llm():
    """Provide a mock LLM for tests that need it"""
    mock = Mock()
    mock.invoke.return_value = "Mock LLM response"
    mock.generate.return_value = "Mock generated content"
    return mock


@pytest.fixture
def mock_database():
    """Provide mock database connections for tests"""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()

        # Set up cursor context manager
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_context

        mock_connect.return_value = mock_conn
        yield mock_conn, mock_cursor
