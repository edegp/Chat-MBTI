"""
MBTI Controller - Clean API Layer
This controller handles HTTP requests and delegates business logic to the usecase layer.
"""

import logging
from typing import Dict, Any
from ..usecase.mbti_conversation_service import MBTIConversationService

logger = logging.getLogger(__name__)


class MBTIController:
    """Controller for MBTI conversation API endpoints"""

    def __init__(self, mbti_service: MBTIConversationService):
        self.mbti_service = mbti_service

    async def start_conversation(self, user_id: str) -> Dict[str, Any]:
        """Start MBTI conversation endpoint"""
        logger.info(f"Starting conversation for user: {user_id}")

        if not user_id:
            return {"status": "error", "message": "User ID is required"}

        try:
            result = self.mbti_service.start_conversation(user_id)
            logger.info(f"Conversation started successfully for user: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to start conversation for user {user_id}: {e}")
            return {"status": "error", "message": "Internal server error"}

    async def submit_answer(self, user_id: str, answer: str) -> Dict[str, Any]:
        """Submit user answer endpoint"""
        logger.info(f"Processing answer for user: {user_id}")

        if not user_id:
            return {"status": "error", "message": "User ID is required"}

        if not answer or not answer.strip():
            return {"status": "error", "message": "Answer is required"}

        try:
            result = self.mbti_service.process_user_response(answer.strip(), user_id)
            logger.info(f"Answer processed successfully for user: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to process answer for user {user_id}: {e}")
            return {"status": "error", "message": "Internal server error"}

    async def get_options(self, user_id: str) -> Dict[str, Any]:
        """Get answer options endpoint"""
        logger.info(f"Getting options for user: {user_id}")

        if not user_id:
            return {"status": "error", "message": "User ID is required", "options": []}

        try:
            result = self.mbti_service.get_answer_options(user_id)
            logger.info(f"Options retrieved successfully for user: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get options for user {user_id}: {e}")
            return {
                "status": "error",
                "message": "Internal server error",
                "options": [],
            }

    async def get_progress(self, user_id: str) -> Dict[str, Any]:
        """Get conversation progress endpoint"""
        logger.info(f"Getting progress for user: {user_id}")

        if not user_id:
            return {
                "status": "error",
                "message": "User ID is required",
                "progress": 0.0,
            }

        try:
            result = self.mbti_service.get_conversation_progress(user_id)
            logger.info(f"Progress retrieved successfully for user: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get progress for user {user_id}: {e}")
            return {
                "status": "error",
                "message": "Internal server error",
                "progress": 0.0,
            }

    async def complete_assessment(self, user_id: str) -> Dict[str, Any]:
        """Complete MBTI assessment endpoint"""
        logger.info(f"Completing assessment for user: {user_id}")

        if not user_id:
            return {"status": "error", "message": "User ID is required"}

        try:
            result = self.mbti_service.complete_assessment(user_id)
            logger.info(f"Assessment completed successfully for user: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to complete assessment for user {user_id}: {e}")
            return {"status": "error", "message": "Internal server error"}
