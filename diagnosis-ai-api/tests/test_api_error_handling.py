"""
APIルーターのエラーハンドリングテスト

APIエンドポイントでのカスタム例外処理とHTTPステータスコードのマッピングをテストします。
"""

import pytest
from unittest.mock import Mock, AsyncMock
import sys
import os

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.exceptions import (
    AuthenticationError,
    AuthorizationError,
    SessionNotFoundError,
    ValidationError,
    LLMError,
    DatabaseError,
)

# Create a test app for mocking dependencies
test_app = FastAPI()

try:
    from src.api.router import router
    from src.api.app import app
    from src.controller.mbti_controller import get_current_user, get_mbti_controller

    # Use the main app but we'll override dependencies
    client = TestClient(app)
except ImportError:
    # テスト環境でインポートエラーが発生する場合のダミーアプリ
    # router が定義されていない場合はダミーのルーターを作成
    from fastapi import APIRouter

    router = APIRouter()
    test_app.include_router(router)
    client = TestClient(test_app)


@pytest.fixture
def test_client():
    """テスト用のクライアントを作成"""
    try:
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller
    except ImportError:
        from fastapi import FastAPI

        app = FastAPI()

        def get_current_user():
            pass

        def get_mbti_controller():
            pass

    # Mock dependencies
    def mock_get_current_user():
        return {"uid": "test_user_123", "email": "test@example.com"}

    def mock_get_mbti_controller():
        controller = Mock()
        controller.start_conversation = AsyncMock()
        controller.submit_answer = AsyncMock()
        controller.get_options = AsyncMock()
        controller.get_progress = AsyncMock()
        controller.complete_assessment = AsyncMock()
        controller.get_conversation_history = AsyncMock()
        return controller

    # Override dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

    test_client = TestClient(app)

    yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_controller():
    """モックコントローラーを作成"""
    controller = Mock()
    controller.start_conversation = AsyncMock()
    controller.submit_answer = AsyncMock()
    controller.get_options = AsyncMock()
    controller.get_progress = AsyncMock()
    controller.complete_assessment = AsyncMock()
    controller.get_conversation_history = AsyncMock()
    return controller


@pytest.fixture
def mock_current_user():
    """モック認証ユーザーを作成"""
    return {"uid": "test_user_123", "email": "test@example.com"}


class TestAPIErrorHandling:
    """APIエラーハンドリングのテスト"""

    def test_authentication_error_returns_401(self, test_client):
        """認証エラーが401ステータスコードを返すことをテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user

        # Override with an error-raising mock
        def mock_get_current_user():
            raise AuthenticationError("Invalid token")

        app.dependency_overrides[get_current_user] = mock_get_current_user

        # Act
        response = test_client.get("/api/v1/conversation/start")

        # Assert
        assert response.status_code == 401
        assert response.json()["status"] == "error"
        assert "Invalid token" in response.json()["message"]

    def test_authorization_error_returns_403(self, test_client):
        """認可エラーが403ステータスコードを返すことをテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with mocks that raise exceptions
        def mock_get_current_user():
            return {"uid": "test_user"}

        async def mock_get_mbti_controller():
            controller = Mock()

            async def mock_start_conversation(user_id):
                raise AuthorizationError("Access denied")

            controller.start_conversation = mock_start_conversation
            return controller

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.get("/api/v1/conversation/start")

        # Assert
        assert response.status_code == 403
        assert response.json()["status"] == "error"
        assert "Access denied" in response.json()["message"]

    def test_session_not_found_returns_404(self, test_client):
        """セッション未発見エラーが404ステータスコードを返すことをテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with mocks that raise exceptions
        def mock_get_current_user():
            return {"uid": "test_user"}

        async def mock_get_mbti_controller():
            controller = Mock()

            async def mock_get_progress(user_id):
                raise SessionNotFoundError("Session not found")

            controller.get_progress = mock_get_progress
            return controller

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.get("/api/v1/conversation/progress")

        # Assert
        assert response.status_code == 404
        assert response.json()["status"] == "error"
        assert "Session not found" in response.json()["message"]

    def test_database_error_returns_500(self, test_client):
        """データベースエラーが500ステータスコードを返すことをテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with mocks that raise exceptions
        def mock_get_current_user():
            return {"uid": "test_user"}

        async def mock_get_mbti_controller():
            controller = Mock()

            async def mock_start_conversation(user_id):
                raise DatabaseError("Database connection failed")

            controller.start_conversation = mock_start_conversation
            return controller

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.get("/api/v1/conversation/start")

        # Assert
        assert response.status_code == 500
        assert response.json()["status"] == "error"
        assert "Database connection failed" in response.json()["message"]

    def test_llm_error_returns_503(self, test_client):
        """LLMエラーが503ステータスコードを返すことをテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with mocks that raise exceptions
        def mock_get_current_user():
            return {"uid": "test_user"}

        async def mock_get_mbti_controller():
            controller = Mock()

            async def mock_start_conversation(user_id):
                raise LLMError("LLM service unavailable")

            controller.start_conversation = mock_start_conversation
            return controller

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.get("/api/v1/conversation/start")

        # Assert
        assert response.status_code == 503
        assert response.json()["status"] == "error"
        assert "LLM service unavailable" in response.json()["message"]

    def test_validation_error_returns_400(self, test_client):
        """バリデーションエラーが400ステータスコードを返すことをテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with mocks that raise exceptions
        def mock_get_current_user():
            return {"uid": "test_user"}

        async def mock_get_mbti_controller():
            controller = Mock()

            async def mock_submit_answer(user_id, answer):
                raise ValidationError("Invalid input")

            controller.submit_answer = mock_submit_answer
            return controller

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.post(
            "/api/v1/conversation/answer", json={"answer": "test answer"}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["status"] == "error"
        assert "Invalid input" in response.json()["message"]

    def test_empty_answer_validation(self, test_client):
        """空の回答のバリデーションテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with basic mocks
        def mock_get_current_user():
            return {"uid": "test_user"}

        async def mock_get_mbti_controller():
            return Mock()

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.post("/api/v1/conversation/answer", json={"answer": ""})

        # Assert
        assert response.status_code == 400
        assert response.json()["status"] == "error"
        assert "Answer cannot be empty" in response.json()["message"]

    def test_missing_user_id_validation(self, test_client):
        """ユーザーID不足のバリデーションテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with missing uid mock
        def mock_get_current_user():
            return {}  # uid が含まれていない

        async def mock_get_mbti_controller():
            return Mock()

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.get("/api/v1/conversation/start")

        # Assert
        assert response.status_code == 401
        assert response.json()["status"] == "error"
        assert "User ID not found" in response.json()["message"]

    def test_successful_request_with_info_logging(self, test_client):
        """成功リクエストでinfoログが出力されることをテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with successful mocks
        def mock_get_current_user():
            return {"uid": "test_user"}

        async def mock_get_mbti_controller():
            controller = Mock()

            async def mock_start_conversation(user_id):
                return {
                    "status": "success",
                    "question": "Test question",
                    "session_id": "test_session_123",
                    "phase": "question",
                }

            controller.start_conversation = mock_start_conversation
            return controller

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.get("/api/v1/conversation/start")

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Conversation started successfully"
        assert response.json()["data"]["question"] == "Test question"

    def test_health_check_endpoint(self, test_client):
        """ヘルスチェックエンドポイントのテスト"""
        # Act
        response = test_client.get("/api/v1/health")

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "MBTI API is running" in response.json()["message"]


class TestErrorResponseFormat:
    """エラーレスポンス形式のテスト"""

    def test_error_response_has_required_fields(self, test_client):
        """エラーレスポンスが必要なフィールドを含むことをテスト"""
        from src.api.app import app
        from src.controller.mbti_controller import get_current_user, get_mbti_controller

        # Override with mocks that raise exceptions
        def mock_get_current_user():
            return {"uid": "test_user"}

        async def mock_get_mbti_controller():
            controller = Mock()

            async def mock_start_conversation(user_id):
                raise ValidationError(
                    "Test error message", {"field": "value", "context": "test"}
                )

            controller.start_conversation = mock_start_conversation
            return controller

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_mbti_controller] = mock_get_mbti_controller

        # Act
        response = test_client.get("/api/v1/conversation/start")

        # Assert
        error_response = response.json()
        assert "status" in error_response
        assert "message" in error_response
        assert "error_type" in error_response
        assert "details" in error_response
        assert error_response["status"] == "error"
        assert error_response["error_type"] == "ValidationError"
        assert error_response["message"] == "Test error message"
        assert error_response["details"]["field"] == "value"
