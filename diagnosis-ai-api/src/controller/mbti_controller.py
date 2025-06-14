"""
MBTI Controller - Clean API Layer
This controller handles HTTP requests and delegates business logic to the usecase layer.
"""

import logging
from typing import Dict, Any
from ..usecase.mbti_conversation_service import MBTIConversationService
from ..gateway.llm_gateway import LLMGateway
from ..gateway.repository_gateway import (
    QuestionRepositoryGateway,
    SessionRepositoryGateway,
    ElementRepositoryGateway,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends


from ..gateway.workflow_gateway import WorkflowGateway
from ..driver.langgraph_driver import LangGraphDriver
from ..driver.auth import get_firebase_user
from ..driver.db import init_postgres
from ..exceptions import (
    MBTIApplicationError,
    ValidationError,
    InvalidInputError,
    create_error_response,
)
from .type import StartConversationRequest, ProcessUserResponseRequest

logger = logging.getLogger(__name__)

security = HTTPBearer()


class MBTIController:
    """Controller for MBTI conversation API endpoints"""

    def __init__(self, mbti_service: MBTIConversationService):
        self.mbti_service = mbti_service

    async def start_conversation(
        self, request: StartConversationRequest
    ) -> Dict[str, Any]:
        """Start MBTI conversation endpoint"""
        user_id = request.user_id

        logger.info(f"Starting conversation for user: {user_id}")

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            return create_error_response(error)

        try:
            result = self.mbti_service.start_conversation(user_id)
            logger.info(f"Conversation started successfully for user: {user_id}")
            return result
        except MBTIApplicationError as e:
            logger.error(
                f"MBTIApplicationError while starting conversation for user {user_id}: {e}"
            )
            e.log_error(logger)
            return create_error_response(e)
        except Exception as e:
            logger.error(
                f"Unexpected error while starting conversation for user {user_id}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            return create_error_response(error)

    async def process_user_response(
        self, request: ProcessUserResponseRequest
    ) -> Dict[str, Any]:
        """Process user response endpoint"""
        # Extract fields from request
        user_input = request.user_input
        user_id = request.user_id
        logger.info(f"Processing response for user: {user_id}")

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            return create_error_response(error)

        if not user_input or not user_input.strip():
            error = InvalidInputError("User input is required")
            error.log_error(logger)
            return create_error_response(error)

        try:
            result = self.mbti_service.process_user_response(
                user_input.strip(), user_id
            )
            logger.info(f"Response processed successfully for user: {user_id}")
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            return create_error_response(e)
        except Exception as e:
            logger.error(
                f"Unexpected error while processing response for user {user_id}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            return create_error_response(error)

    async def get_user_session(self) -> Dict[str, Any]:
        """Get current user session endpoint"""
        # This would typically get user from auth context
        # For testing purposes, we'll implement a basic version
        try:
            # In real implementation, this would get user from authentication context
            user = {"uid": "test_user"}  # Placeholder
            if not user:
                from fastapi import HTTPException, status

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )

            result = self.mbti_service.get_user_session(user["uid"])
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            return create_error_response(e)
        except Exception as e:
            logger.error(f"Unexpected error while getting user session: {e}")
            error = MBTIApplicationError("Internal server error")
            return create_error_response(error)

    async def submit_answer(self, user_id: str, answer: str) -> Dict[str, Any]:
        """Submit user answer endpoint"""
        logger.info(f"Processing answer for user: {user_id}")

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            return create_error_response(error)

        if not answer or not answer.strip():
            error = InvalidInputError("Answer is required")
            error.log_error(logger)
            return create_error_response(error)

        try:
            result = self.mbti_service.process_user_response(answer.strip(), user_id)
            logger.info(f"Answer processed successfully for user: {user_id}")
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            return create_error_response(e)
        except Exception as e:
            logger.error(
                f"Unexpected error while processing answer for user {user_id}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            return create_error_response(error)

    async def get_options(self, user_id: str) -> Dict[str, Any]:
        """Get answer options endpoint"""
        logger.info(f"Getting options for user: {user_id}")

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            error_response = create_error_response(error)
            error_response["options"] = []  # 追加フィールド
            return error_response

        try:
            result = self.mbti_service.get_answer_options(user_id)
            logger.info(f"Options retrieved successfully for user: {user_id}")
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            error_response = create_error_response(e)
            error_response["options"] = []  # 追加フィールド
            return error_response
        except Exception as e:
            logger.error(
                f"Unexpected error while getting options for user {user_id}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            error_response = create_error_response(error)
            error_response["options"] = []  # 追加フィールド
            return error_response

    async def get_progress(self, user_id: str) -> Dict[str, Any]:
        """Get conversation progress endpoint"""
        logger.info(f"Getting progress for user: {user_id}")

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            error_response = create_error_response(error)
            error_response["progress"] = 0.0  # 追加フィールド
            return error_response

        try:
            result = self.mbti_service.get_conversation_progress(user_id)
            logger.info(f"Progress retrieved successfully for user: {user_id}")
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            error_response = create_error_response(e)
            error_response["progress"] = 0.0  # 追加フィールド
            return error_response
        except Exception as e:
            logger.error(
                f"Unexpected error while getting progress for user {user_id}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            error_response = create_error_response(error)
            error_response["progress"] = 0.0  # 追加フィールド
            return error_response

    async def complete_assessment(self, user_id: str) -> Dict[str, Any]:
        """Complete MBTI assessment endpoint"""
        logger.info(f"Completing assessment for user: {user_id}")

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            return create_error_response(error)

        try:
            result = self.mbti_service.complete_assessment(user_id)
            logger.info(f"Assessment completed successfully for user: {user_id}")
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            return create_error_response(e)
        except Exception as e:
            logger.error(
                f"Unexpected error while completing assessment for user {user_id}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            return create_error_response(error)

    async def get_conversation_history(self, user_id: str) -> Dict[str, Any]:
        """Get conversation history endpoint"""
        logger.info(f"Getting conversation history for user: {user_id}")

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            error_response = create_error_response(error)
            error_response["history"] = []  # 追加フィールド
            return error_response

        try:
            result = self.mbti_service.get_conversation_history(user_id)
            logger.info(
                f"Conversation history retrieved successfully for user: {user_id}"
            )
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            error_response = create_error_response(e)
            error_response["history"] = []  # 追加フィールド
            return error_response
        except Exception as e:
            logger.error(
                f"Unexpected error while getting conversation history for user {user_id}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            error_response = create_error_response(error)
            error_response["history"] = []  # 追加フィールド
            return error_response


def get_mbti_controller() -> MBTIController:
    """Dependency injection for MBTIController"""
    # Create dependencies
    llm_gateway = LLMGateway()
    question_repo = QuestionRepositoryGateway()
    session_repo = SessionRepositoryGateway()
    elements_repo = ElementRepositoryGateway()

    langgraph_driver = LangGraphDriver(llm_gateway, question_repo, elements_repo)
    # Create workflow gateway
    workflow_gateway = WorkflowGateway(langgraph_driver)

    # Create service
    mbti_service = MBTIConversationService(
        workflow_port=workflow_gateway,
        question_repository=question_repo,
        session_repository=session_repo,
        elements_repository=elements_repo,
    )

    # Create controller
    return MBTIController(mbti_service)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Get the current user from the request context"""
    user = await get_firebase_user(credentials)
    return user


def init_database():
    init_postgres()
