"""
MBTI Controller - Clean API Layer
This controller handles HTTP requests and delegates business logic to the usecase layer.
"""

import logging
from typing import Dict, Any
from ..usecase.mbti_conversation_service import MBTIConversationService
from ..usecase.data_collection_service import DataCollectionService
from ..gateway.llm_gateway import LLMGateway
from ..gateway.repository_gateway import (
    QuestionRepositoryGateway,
    SessionRepositoryGateway,
    ElementRepositoryGateway,
    DataCollectionRepositoryGateway,
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
from .type import (
    StartConversationRequest,
    ProcessUserResponseRequest,
)

from ..type import DataCollectionUploadRequest

logger = logging.getLogger(__name__)

security = HTTPBearer()


class MBTIController:
    """Controller for MBTI conversation API endpoints"""

    def __init__(
        self,
        mbti_service: MBTIConversationService,
        data_collection_service: DataCollectionService = None,
    ):
        self.mbti_service = mbti_service
        self.data_collection_service = data_collection_service

    async def start_conversation(
        self, request: StartConversationRequest
    ) -> Dict[str, Any]:
        """Start MBTI conversation endpoint"""
        user_id = request.user_id
        element_id = getattr(request, "element_id", None)

        logger.info(
            f"Starting conversation for user: {user_id}, element_id: {element_id}"
        )

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            return create_error_response(error)

        try:
            # Pass element_id only if provided
            if element_id is None:
                result = self.mbti_service.start_conversation(user_id)
            else:
                result = self.mbti_service.start_conversation(
                    user_id, element_id=element_id
                )
            logger.info(
                f"Conversation started successfully for user: {user_id}, element_id: {element_id}"
            )
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

    async def undo_last_answer(self, user_id: str) -> Dict[str, Any]:
        """Undo the last answer for data collection"""
        logger.info(f"Undoing last answer for user: {user_id}")

        if not user_id:
            error = InvalidInputError("User ID is required")
            error.log_error(logger)
            return create_error_response(error)

        try:
            result = self.mbti_service.undo_last_answer(user_id)
            logger.info(f"Last answer undone successfully for user: {user_id}")
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            return create_error_response(e)
        except Exception as e:
            logger.error(
                f"Unexpected error while undoing last answer for user {user_id}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            return create_error_response(error)

    async def upload_data_collection_csv(
        self, request: DataCollectionUploadRequest
    ) -> Dict[str, Any]:
        """Upload data collection CSV to GCS"""
        logger.info(
            f"Uploading data collection CSV for user: {request.participant_name}"
        )

        if not request.participant_name:
            error = InvalidInputError("Participant name is required")
            error.log_error(logger)
            return create_error_response(error)

        try:
            result = self.data_collection_service.upload_data_collection_csv(
                participant_name=request.participant_name,
                personality_code=request.personality_code,
                csv_content=request.csv_content,
                element_id=request.element_id,
                cycle_number=request.cycle_number,
            )
            logger.info(
                f"Data collection CSV uploaded successfully for user: {request.participant_name}"
            )
            return result
        except MBTIApplicationError as e:
            e.log_error(logger)
            return create_error_response(e)
        except Exception as e:
            logger.error(
                f"Unexpected error while uploading data collection CSV for user {request.participant_name}: {e}"
            )
            error = MBTIApplicationError("Internal server error")
            return create_error_response(error)


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
    data_collection_repo = DataCollectionRepositoryGateway()

    # Create service
    mbti_service = MBTIConversationService(
        workflow_port=workflow_gateway,
        question_repository=question_repo,
        session_repository=session_repo,
        elements_repository=elements_repo,
        data_collection_repository=data_collection_repo,
    )
    data_collection_service = DataCollectionService(
        data_collection_repository=data_collection_repo,
    )

    # Create controller
    return MBTIController(mbti_service, data_collection_service)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Get the current user from the request context"""
    user = await get_firebase_user(credentials)
    return user


def init_database():
    init_postgres()
