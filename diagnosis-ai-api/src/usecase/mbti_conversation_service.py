"""
MBTI Conversation Service - Pure Business Logic
This service contains the core business rules for MBTI conversations
without dependencies on external frameworks or infrastructure.
"""

import logging
from typing import Dict, Any, List
from ..port.ports import (
    WorkflowPort,
    QuestionRepositoryPort,
    SessionRepositoryPort,
    ElementRepositoryPort,
)
from .type import Message
from ..exceptions import (
    SessionNotFoundError,
    SessionError,
    AssessmentError,
    AssessmentIncompleteError,
    InvalidResponseError,
    WorkflowError,
)

logger = logging.getLogger(__name__)


class MBTIConversationService:
    """Service for managing MBTI conversation business logic"""

    def __init__(
        self,
        workflow_port: WorkflowPort,
        question_repository: QuestionRepositoryPort,
        session_repository: SessionRepositoryPort,
        elements_repository: ElementRepositoryPort,
    ):
        self.workflow = workflow_port
        self.question_repository = question_repository
        self.session_repository = session_repository
        self.elements_repository = elements_repository

    def start_conversation(self, user_id: str) -> Dict[str, Any]:
        """Start a new MBTI conversation"""
        try:
            logger.info("Starting conversation", extra={"user_id": user_id})
            existing_session = self.session_repository.get_session_by_user(user_id)
            if existing_session:
                # 既存のセッションがあれば、最新の質問を返す
                session_id = existing_session
                logger.info(
                    "Resuming existing session",
                    extra={"session_id": session_id, "user_id": user_id},
                )
                state = self.workflow.get_conversation_state(session_id)
                messages = state.get("messages", [])
                if not messages:
                    raise InvalidResponseError(
                        "No messages in session",
                        {"user_id": user_id, "session_id": session_id},
                    )
                last = messages[-1]
                question = (
                    last.content
                    if hasattr(last, "content")
                    else last.get("content", "")
                )
                return {
                    "phase": "question",
                    "question": question,
                    "session_id": session_id,
                    "status": "success",
                }
            # 新規 or 再開を問わず、最初は空履歴でワークフローを実行して質問とオプションを生成
            session_id = (
                self.session_repository.create_session(user_id)
                if not existing_session
                else existing_session
            )
            result = self.workflow.execute_conversation_flow("", session_id, user_id)
            last_msg = result.get("messages", [])[-1]
            question = (
                last_msg.content
                if hasattr(last_msg, "content")
                else last_msg.get("content", "")
            )
            options = result.get("options", [])
            return {
                "phase": "question",
                "question": question,
                "options": options,
                "session_id": session_id,
                "status": "success",
            }
        except (
            SessionNotFoundError,
            AssessmentError,
            WorkflowError,
            InvalidResponseError,
        ):
            # 既知のカスタム例外は再発生
            raise
        except Exception as e:
            error = AssessmentError(
                "Failed to start conversation due to unexpected error",
                {"user_id": user_id, "error": str(e), "error_type": type(e).__name__},
            )
            logger.debug(
                f"Error starting conversation for user {user_id}: {e}",
            )
            error.log_error(logger)
            raise error

    def process_user_response(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Process user response and generate next question or complete assessment"""
        try:
            logger.info(
                "Processing user response",
                extra={
                    "user_id": user_id,
                    "input_preview": user_input[:100] + "..."
                    if len(user_input) > 100
                    else user_input,
                },
            )

            # Business rule: User must have an active session
            session_id = self.session_repository.get_session_by_user(user_id)
            if not session_id:
                raise SessionNotFoundError(
                    "No active session found for user", {"user_id": user_id}
                )

            # Get current conversation state to check progress
            current_state = self.workflow.get_conversation_state(session_id)
            next_order = current_state.get("next_display_order", 0)
            logger.debug(
                "Current conversation state retrieved",
                extra={"session_id": session_id, "next_display_order": next_order},
            )

            # Business rule: Check if we have enough questions (MBTI typically needs 20+ questions)
            if next_order >= 20:
                logger.info(
                    "Assessment complete",
                    extra={"session_id": session_id, "questions_completed": next_order},
                )
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

            # Get updated conversation state after processing user response
            current_state = self.workflow.get_conversation_state(session_id)
            next_order = current_state.get("next_display_order", 0)

            # Extract results
            if "messages" in result and len(result["messages"]) > 0:
                last_message = result["messages"][-1]
                # Handle both Message objects and dict formats
                if hasattr(last_message, "content"):
                    question = last_message.content
                else:
                    question = last_message.get("content", "")

                if not question:
                    raise InvalidResponseError(
                        "Empty question generated from workflow",
                        {"user_id": user_id, "session_id": session_id},
                    )

                # Progress calculation: completed questions / total questions
                # Adjust question index since next_order reflects next_display_order after generation
                question_index = max(next_order, 0)
                completed_questions = question_index
                progress = min(completed_questions / 20.0, 1.0)
                # Question number to display for the upcoming question
                current_question_number = min(max(next_order, 1), 20)

                logger.info(
                    "User response processed successfully",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "progress": progress,
                        "question_number": current_question_number,
                        "completed_questions": completed_questions,
                    },
                )

                return {
                    "phase": "question",
                    "question": question,
                    "session_id": session_id,
                    "progress": progress,
                    "question_number": current_question_number,
                    "total_questions": 20,
                    "status": "success",
                }
            else:
                raise InvalidResponseError(
                    "No question generated from workflow",
                    {
                        "user_id": user_id,
                        "session_id": session_id,
                        "result": str(result),
                    },
                )

        except (
            SessionNotFoundError,
            AssessmentError,
            WorkflowError,
            InvalidResponseError,
        ):
            # 既知のカスタム例外は再発生
            raise
        except Exception as e:
            error = AssessmentError(
                "Failed to process user response due to unexpected error",
                {"user_id": user_id, "error": str(e), "error_type": type(e).__name__},
            )
            error.log_error(logger)
            raise error

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
            logger.info("Completing assessment", extra={"user_id": user_id})

            session_id = self.session_repository.get_session_by_user(user_id)
            if not session_id:
                raise SessionNotFoundError(
                    "No active session found for user", {"user_id": user_id}
                )

            # Business rule: Check if enough questions were answered
            current_state = self.workflow.get_conversation_state(session_id)
            answered_questions = current_state.get("next_display_order", 0)

            if answered_questions < 20:
                raise AssessmentIncompleteError(
                    f"Assessment incomplete. Only {answered_questions}/20 questions answered.",
                    {
                        "user_id": user_id,
                        "session_id": session_id,
                        "answered_questions": answered_questions,
                        "required_questions": 20,
                    },
                )

            # Close the session
            self.session_repository.close_session(session_id)

            logger.info(
                "Assessment completed successfully",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "total_questions_answered": answered_questions,
                },
            )

            return {
                "message": "Assessment completed successfully",
                "total_questions_answered": answered_questions,
                "session_id": session_id,
                "status": "success",
            }

        except (SessionNotFoundError, AssessmentIncompleteError):
            # 既知のカスタム例外は再発生
            raise
        except Exception as e:
            error = AssessmentError(
                "Failed to complete assessment due to unexpected error",
                {"user_id": user_id, "error": str(e), "error_type": type(e).__name__},
            )
            error.log_error(logger)
            raise error

    def get_conversation_progress(self, user_id: str) -> Dict[str, Any]:
        """Get current progress of the conversation"""
        try:
            session_id = self.session_repository.get_session_by_user(user_id)
            if not session_id:
                return {
                    "progress": 0.0,
                    "question_number": 1,
                    "total_questions": 20,
                    "session_id": None,
                    "status": "error",
                    "message": "No active session found",
                }

            current_state = self.workflow.get_conversation_state(session_id)
            next_order = current_state.get("next_display_order", 0)
            # Completed questions count
            completed_questions = next_order
            progress = min(completed_questions / 20.0, 1.0)
            # Next question number (1-based, max 20)
            current_question_number = min(max(next_order, 1), 20)

            logger.info(
                f"GET Progress: next_order={next_order}, completed_questions={completed_questions}, progress={progress}, question_number={current_question_number}"
            )

            return {
                "progress": progress,
                "question_number": current_question_number,
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

    def get_conversation_history(self, user_id: str) -> Dict[str, Any]:
        """Get conversation history for session restoration"""
        try:
            session_id = self.session_repository.get_session_by_user(user_id)
            if not session_id:
                return {
                    "history": [],
                    "message": "No active session found",
                    "status": "error",
                }

            current_state = self.workflow.get_conversation_state(session_id)
            messages = current_state.get("messages", [])

            # Format messages for frontend consumption
            formatted_history = []
            for msg in messages:
                if hasattr(msg, "role") and hasattr(msg, "content"):
                    # Handle Message objects
                    formatted_history.append(
                        {
                            "type": "question" if msg.role == "assistant" else "answer",
                            "text": msg.content,
                            "role": msg.role,
                        }
                    )
                elif isinstance(msg, dict) and "role" in msg and "content" in msg:
                    # Handle dict format
                    formatted_history.append(
                        {
                            "type": "question"
                            if msg["role"] == "assistant"
                            else "answer",
                            "text": msg["content"],
                            "role": msg["role"],
                        }
                    )

            return {
                "history": formatted_history,
                "session_id": session_id,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Failed to get conversation history for user {user_id}: {e}")
            return {
                "history": [],
                "message": f"Failed to get conversation history: {str(e)}",
                "status": "error",
            }
