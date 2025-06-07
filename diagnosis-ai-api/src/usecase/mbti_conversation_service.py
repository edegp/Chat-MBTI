"""
MBTI Conversation Service - Pure Business Logic
This service contains the core business rules for MBTI conversations
without dependencies on external frameworks or infrastructure.
"""

import logging
from typing import Dict, Any
from ..port.ports import WorkflowPort, QuestionRepositoryPort, SessionRepositoryPort

logger = logging.getLogger(__name__)


class MBTIConversationService:
    """Service for managing MBTI conversation business logic"""

    def __init__(
        self,
        workflow_port: WorkflowPort,
        question_repository: QuestionRepositoryPort,
        session_repository: SessionRepositoryPort,
    ):
        self.workflow = workflow_port
        self.question_repository = question_repository
        self.session_repository = session_repository

    def start_conversation(self, user_id: str) -> Dict[str, Any]:
        """Start a new MBTI conversation"""
        try:
            # Business rule: Check if user already has an active session
            existing_session = self.session_repository.get_session_by_user(user_id)

            if existing_session:
                # Continue existing conversation
                session_id = existing_session
                logger.info(
                    f"Continuing existing session {session_id} for user {user_id}"
                )
            else:
                # Create new session
                session_id = self.session_repository.create_session(user_id)
                logger.info(f"Created new session {session_id} for user {user_id}")

            # Start conversation flow with initial message
            initial_message = "Let's start your MBTI assessment!"
            result = self.workflow.execute_conversation_flow(
                initial_message, session_id, user_id
            )

            # Extract the generated question
            if "messages" in result and len(result["messages"]) > 0:
                last_message = result["messages"][-1]
                # Handle both Message objects and dict formats
                if hasattr(last_message, "content"):
                    question = last_message.content
                else:
                    question = last_message.get("content", "")

                return {
                    "phase": "question",
                    "question": question,
                    "session_id": session_id,
                    "status": "success",
                }
            else:
                raise ValueError("No question generated from workflow")

        except Exception as e:
            logger.error(f"Failed to start conversation for user {user_id}: {e}")
            return {
                "phase": "error",
                "message": f"Failed to start conversation: {str(e)}",
                "status": "error",
            }

    def process_user_response(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Process user response and generate next question or complete assessment"""
        try:
            # Business rule: User must have an active session
            session_id = self.session_repository.get_session_by_user(user_id)
            if not session_id:
                return {
                    "phase": "error",
                    "message": "No active session found. Please start a new conversation.",
                    "status": "error",
                }

            # Get current conversation state to check progress
            current_state = self.workflow.get_conversation_state(session_id)
            current_order = current_state.get("next_display_order", 0)

            # Business rule: Check if we have enough questions (MBTI typically needs 20+ questions)
            if current_order >= 20:
                return {
                    "phase": "diagnosis",
                    "message": "Assessment complete! Ready for MBTI diagnosis.",
                    "session_id": session_id,
                    "status": "success",
                }

            # Execute workflow with user response
            result = self.workflow.execute_conversation_flow(
                user_input, session_id, user_id
            )

            # Extract results
            if "messages" in result and len(result["messages"]) > 0:
                last_message = result["messages"][-1]
                # Handle both Message objects and dict formats
                if hasattr(last_message, "content"):
                    question = last_message.content
                else:
                    question = last_message.get("content", "")

                progress = min(current_order / 20.0, 1.0)  # Progress as percentage

                return {
                    "phase": "question",
                    "question": question,
                    "session_id": session_id,
                    "progress": progress,
                    "question_number": current_order + 1,
                    "total_questions": 20,
                    "status": "success",
                }
            else:
                raise ValueError("No question generated from workflow")

        except Exception as e:
            logger.error(f"Failed to process user response for user {user_id}: {e}")
            return {
                "phase": "error",
                "message": f"Failed to process response: {str(e)}",
                "status": "error",
            }

    def get_answer_options(self, user_id: str) -> Dict[str, Any]:
        """Get available answer options for current question"""
        try:
            session_id = self.session_repository.get_session_by_user(user_id)
            if not session_id:
                return {
                    "options": [],
                    "message": "No active session found",
                    "status": "error",
                }

            options = self.workflow.get_conversation_options(session_id)

            return {"options": options, "session_id": session_id, "status": "success"}

        except Exception as e:
            logger.error(f"Failed to get options for user {user_id}: {e}")
            return {
                "options": [],
                "message": f"Failed to get options: {str(e)}",
                "status": "error",
            }

    def complete_assessment(self, user_id: str) -> Dict[str, Any]:
        """Complete the MBTI assessment and close session"""
        try:
            session_id = self.session_repository.get_session_by_user(user_id)
            if not session_id:
                return {"message": "No active session found", "status": "error"}

            # Business rule: Check if enough questions were answered
            current_state = self.workflow.get_conversation_state(session_id)
            answered_questions = current_state.get("next_display_order", 0)

            if answered_questions < 20:
                return {
                    "message": f"Assessment incomplete. Only {answered_questions}/20 questions answered.",
                    "status": "error",
                }

            # Close the session
            self.session_repository.close_session(session_id)

            return {
                "message": "Assessment completed successfully",
                "total_questions_answered": answered_questions,
                "session_id": session_id,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Failed to complete assessment for user {user_id}: {e}")
            return {
                "message": f"Failed to complete assessment: {str(e)}",
                "status": "error",
            }

    def get_conversation_progress(self, user_id: str) -> Dict[str, Any]:
        """Get current progress of the conversation"""
        try:
            session_id = self.session_repository.get_session_by_user(user_id)
            if not session_id:
                return {
                    "progress": 0.0,
                    "message": "No active session found",
                    "status": "error",
                }

            current_state = self.workflow.get_conversation_state(session_id)
            current_order = current_state.get("next_display_order", 0)
            progress = min(current_order / 20.0, 1.0)

            return {
                "progress": progress,
                "question_number": current_order,
                "total_questions": 20,
                "session_id": session_id,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Failed to get progress for user {user_id}: {e}")
            return {
                "progress": 0.0,
                "message": f"Failed to get progress: {str(e)}",
                "status": "error",
            }
