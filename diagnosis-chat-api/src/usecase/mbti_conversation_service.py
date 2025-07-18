from ..gateway.repository_gateway import MBTIReportRepositoryGateway

"""
MBTI Conversation Service - Pure Business Logic
This service contains the core business rules for MBTI conversations
without dependencies on external frameworks or infrastructure.
"""

import logging
from typing import Dict, Any, List, TypedDict
from langchain_core.messages import RemoveMessage

from ..port.ports import (
    MBTIReportRepositoryPort,
    WorkflowPort,
    QuestionRepositoryPort,
    AnswerRepositoryPort,
    SessionRepositoryPort,
    ElementRepositoryPort,
)
from .data_collection_service import DataCollectionService
from ..exceptions import (
    SessionNotFoundError,
    AssessmentError,
    AssessmentIncompleteError,
    InvalidResponseError,
    WorkflowError,
)

logger = logging.getLogger(__name__)


class Message(TypedDict):
    """TypedDict for message structure"""

    role: str  # 'user' or 'assistant'
    content: str  # Message content


class MBTIConversationService:
    """Service for managing MBTI conversation business logic"""

    # Configurable question/phase counts for standard MBTI
    QUESTIONS_PER_PHASE = 8  # Example: 5 questions per phase (can be changed)
    NUM_PHASES = 4  # Example: 4 phases (can be changed)
    TOTAL_QUESTIONS = QUESTIONS_PER_PHASE * NUM_PHASES

    def __init__(
        self,
        workflow_port: WorkflowPort,
        question_repository: QuestionRepositoryPort,
        answer_repository: AnswerRepositoryPort,
        session_repository: SessionRepositoryPort,
        elements_repository: ElementRepositoryPort,
        mbti_report_repository: MBTIReportRepositoryPort,
        data_collection_workflow_port: WorkflowPort = None,
        data_collection_repository: QuestionRepositoryPort = None,
    ):
        self.workflow = workflow_port
        self.question_repository = question_repository
        self.answer_repository = answer_repository
        self.session_repository = session_repository
        self.elements_repository = elements_repository
        self.data_collection_service = DataCollectionService(data_collection_repository)
        self.data_collection_workflow = data_collection_workflow_port or workflow_port
        self.mbti_report_repository = mbti_report_repository
        self.QUESTIONS_PER_PHASE = elements_repository.get_question_per_phase()
        self.TOTAL_QUESTIONS = self.QUESTIONS_PER_PHASE * self.NUM_PHASES

    async def restore_report(self, user_id: str, element_id: int) -> Dict[str, Any]:
        """Restore MBTI report from the database."""
        db_user_id = self.session_repository.get_or_create_user_id(user_id)
        report = self.mbti_report_repository.get_reports_by_user(db_user_id)
        if not report:
            return {"status": "error", "message": "No report found for this user."}
        return [r for r in report if r["element_id"] == element_id][0]

    async def save_report(
        self,
        user_id: str,
        element_id: int,
        report: str,
        pred_label: str = None,
        gemma_judge: str = None,
        gemma_success: bool = None,
    ) -> str:
        """Save MBTI report to the database."""
        db_user_id = self.session_repository.get_or_create_user_id(user_id)
        return self.mbti_report_repository.save_report(
            db_user_id, element_id, report, pred_label, gemma_judge, gemma_success
        )

    def start_conversation(
        self, user_id: str, element_id: int = None
    ) -> Dict[str, Any]:
        """Start a new MBTI conversation"""
        try:
            logger.info(
                "Starting conversation",
                extra={"user_id": user_id, "element_id": element_id},
            )

            # Check if this is data collection mode
            is_data_collection = user_id == "data_collection_user"

            # Select appropriate workflow
            workflow = (
                self.data_collection_workflow if is_data_collection else self.workflow
            )

            existing_sessions = self.session_repository.get_sessions_by_user(
                user_id, status="in_progress"
            )
            existing_session = existing_sessions[0] if existing_sessions else None
            if existing_session:
                if is_data_collection:
                    logger.info(
                        "Closing existing data collection session to start fresh",
                        extra={"session_id": existing_session, "user_id": user_id},
                    )
                    self.session_repository.close_session(existing_session)
                    session_id = self.session_repository.create_session(user_id)
                    logger.info(
                        "Created new data collection session",
                        extra={"session_id": session_id, "user_id": user_id},
                    )
                else:
                    session_id = existing_session
                    logger.info(
                        "Resuming existing session",
                        extra={"session_id": session_id, "user_id": user_id},
                    )
                    state = workflow.get_conversation_state(session_id)
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

                    response_data = {
                        "phase": "question",
                        "question": question,
                        "session_id": session_id,
                        "status": "success",
                    }

                    if is_data_collection:
                        next_order = state.get("next_display_order", 0)
                        progress_info = self.data_collection_service.get_progress_info(
                            next_order
                        )
                        response_data["progress_info"] = progress_info

                    return response_data
            else:
                session_id = self.session_repository.create_session(user_id)

            # For data collection, initialize with proper element ID
            if is_data_collection:
                initial_element_id = element_id if element_id is not None else 1
                logger.info(
                    f"Starting data collection with element_id: {initial_element_id}",
                    extra={"user_id": user_id, "element_id": initial_element_id},
                )
                result = workflow.execute_conversation_flow(
                    "", session_id, user_id, personality_element_id=initial_element_id
                )
            else:
                result = workflow.execute_conversation_flow("", session_id, user_id)
            last_msg = result.get("messages", [])[-1]
            question = (
                last_msg.content
                if hasattr(last_msg, "content")
                else last_msg.get("content", "")
            )
            options = result.get("options", [])

            response_data = {
                "phase": "question",
                "question": question,
                "options": options,
                "session_id": session_id,
                "status": "success",
            }

            if is_data_collection:
                progress_info = self.data_collection_service.get_progress_info(0)
                response_data["progress_info"] = progress_info

            return response_data
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
            session_ids = self.session_repository.get_sessions_by_user(
                user_id, status="in_progress"
            )
            session_id = session_ids[0] if session_ids else None
            if not session_id:
                raise SessionNotFoundError(
                    "No active session found for user", {"user_id": user_id}
                )

            # Check if this is data collection mode
            is_data_collection = user_id == "data_collection_user"

            # Select appropriate workflow
            workflow = (
                self.data_collection_workflow if is_data_collection else self.workflow
            )

            # Get current conversation state to check progress
            current_state = workflow.get_conversation_state(session_id)
            next_order = current_state.get("next_display_order", 0)
            logger.debug(
                "Current conversation state retrieved",
                extra={"session_id": session_id, "next_display_order": next_order},
            )

            if is_data_collection:
                # Use data collection business logic
                progress_info = self.data_collection_service.get_progress_info(
                    next_order
                )

                # Calculate personality_element_id using business logic
                # For the next question (current_order), calculate which element it should be
                new_element_id = (
                    self.data_collection_service.calculate_personality_element_id(
                        next_order  # Use next_order directly, not next_order + 1
                    )
                )

                # Update state with correct element ID before workflow execution
                current_state["personality_element_id"] = new_element_id

                # Check if data collection is complete
                if self.data_collection_service.is_data_collection_complete(next_order):
                    logger.info(
                        "Data collection complete",
                        extra={
                            "session_id": session_id,
                            "questions_completed": next_order,
                        },
                    )
                    return {
                        "phase": "diagnosis",
                        "message": "Data collection complete! All 50 questions answered.",
                        "session_id": session_id,
                        "status": "success",
                        "progress_info": progress_info,
                    }

                total_questions = self.data_collection_service.TOTAL_QUESTIONS
            else:
                # Standard MBTI logic (configurable total questions)
                if next_order >= self.TOTAL_QUESTIONS:
                    logger.info(
                        "Assessment complete",
                        extra={
                            "session_id": session_id,
                            "questions_completed": next_order,
                        },
                    )
                    return {
                        "phase": "diagnosis",
                        "message": "Assessment complete! Ready for MBTI diagnosis.",
                        "session_id": session_id,
                        "status": "success",
                    }
                total_questions = self.TOTAL_QUESTIONS

            # Execute workflow with user response
            result = workflow.execute_conversation_flow(user_input, session_id, user_id)

            # Get updated conversation state after processing user response
            current_state = workflow.get_conversation_state(session_id)
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
                progress = min(completed_questions / total_questions, 1.0)
                # Question number to display for the upcoming question
                current_question_number = min(max(next_order, 1), total_questions)

                response_data = {
                    "phase": "question",
                    "question": question,
                    "session_id": session_id,
                    "progress": progress,
                    "question_number": current_question_number,
                    "total_questions": total_questions,
                    "status": "success",
                }

                # Add data collection specific info if applicable
                if is_data_collection:
                    response_data["progress_info"] = progress_info
                    response_data["element_switching"] = (
                        self.data_collection_service.is_element_switching(next_order)
                    )

                logger.info(
                    "User response processed successfully",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "progress": progress,
                        "question_number": current_question_number,
                        "completed_questions": completed_questions,
                        "is_data_collection": is_data_collection,
                    },
                )

                return response_data
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
            session_id = self.session_repository.get_sessions_by_user(
                user_id, status="in_progress"
            )[0]
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

    def complete_assessment(self, user_id: str, force: bool = False) -> Dict[str, Any]:
        """Complete the MBTI assessment and close session"""
        try:
            logger.info("Completing assessment", extra={"user_id": user_id})

            session_id = self.session_repository.get_sessions_by_user(
                user_id, status="in_progress"
            )[0]
            if not session_id:
                raise SessionNotFoundError(
                    "No active session found for user", {"user_id": user_id}
                )

            # Check if this is data collection mode
            is_data_collection = user_id == "data_collection_user"

            # Business rule: Check if enough questions were answered
            current_state = self.workflow.get_conversation_state(session_id)
            answered_questions = current_state.get("next_display_order", 0)

            if is_data_collection:
                # For data collection, always allow completion to enable fresh start
                logger.info(
                    "Completing data collection session",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "answered_questions": answered_questions,
                        "force_complete": True,
                    },
                )
            else:
                # Standard MBTI assessment requires all questions answered
                if not force and answered_questions < self.TOTAL_QUESTIONS:
                    logger.warning(
                        f"{force} {answered_questions} < {self.TOTAL_QUESTIONS}"
                    )
                    raise AssessmentIncompleteError(
                        f"Assessment incomplete. Only {answered_questions}/{self.TOTAL_QUESTIONS} questions answered.",
                        {
                            "user_id": user_id,
                            "session_id": session_id,
                            "answered_questions": answered_questions,
                            "required_questions": self.TOTAL_QUESTIONS,
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
            session_id = self.session_repository.get_sessions_by_user(
                user_id, status="in_progress"
            )[0]
            if not session_id:
                return {
                    "progress": 0.0,
                    "question_number": 1,
                    "total_questions": self.TOTAL_QUESTIONS,
                    "session_id": None,
                    "status": "error",
                    "message": "No active session found",
                }

            current_state = self.workflow.get_conversation_state(session_id)
            next_order = current_state.get("next_display_order", 0)
            # Completed questions count
            completed_questions = next_order
            progress = min(completed_questions / self.TOTAL_QUESTIONS, 1.0)
            # Next question number (1-based, max TOTAL_QUESTIONS)
            current_question_number = min(max(next_order, 1), self.TOTAL_QUESTIONS)

            logger.info(
                f"GET Progress: next_order={next_order}, completed_questions={completed_questions}, progress={progress}, question_number={current_question_number}"
            )

            return {
                "progress": progress,
                "question_number": current_question_number,
                "total_questions": self.TOTAL_QUESTIONS,
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

    def undo_last_answer(self, user_id: str, steps: int = 1) -> Dict[str, Any]:
        """Undo the last answer(s) by removing messages from conversation history"""
        try:
            logger.info(f"Undoing {steps} step(s)", extra={"user_id": user_id})

            session_id = self.session_repository.get_sessions_by_user(
                user_id, status="in_progress"
            )[0]
            if not session_id:
                raise SessionNotFoundError(
                    "No active session found for user", {"user_id": user_id}
                )

            # Check if this is data collection mode
            is_data_collection = user_id == "data_collection_user"

            # Select appropriate workflow
            workflow = (
                self.data_collection_workflow if is_data_collection else self.workflow
            )

            # Get current conversation state
            current_state = workflow.get_conversation_state(session_id)
            next_order = current_state.get("next_display_order", 0)

            if next_order < steps:
                raise InvalidResponseError(
                    f"Cannot undo {steps} step(s): only {next_order} answers available",
                    {
                        "user_id": user_id,
                        "session_id": session_id,
                        "next_order": next_order,
                        "requested_steps": steps,
                    },
                )

            # Calculate messages to remove (2 messages per step: user answer + assistant question)
            messages_to_remove = steps * 2
            messages = current_state.get("messages", [])
            original_message_count = len(messages)

            # Remove the specified number of messages if they exist
            actual_messages_to_remove = min(messages_to_remove, len(messages))
            if actual_messages_to_remove > 0:
                current_state["messages"] = [
                    RemoveMessage(id=msg.id)
                    for msg in messages[-actual_messages_to_remove:]
                ]
                logger.info(
                    f"Removed last {actual_messages_to_remove} messages from conversation history for {steps} step(s)",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "original_count": original_message_count,
                        "removed_count": actual_messages_to_remove,
                        "steps": steps,
                    },
                )

            # Decrement next_display_order by the number of steps
            new_next_order = next_order - steps
            current_state["next_display_order"] = new_next_order

            # Update the workflow state
            workflow.update_conversation_state(session_id, current_state)

            logger.info(
                f"Last {steps} answer(s) undone successfully",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "new_next_order": new_next_order,
                    "messages_remaining": len(messages) - actual_messages_to_remove,
                    "steps_undone": steps,
                },
            )

            return {
                "status": "success",
                "message": f"Last {steps} answer(s) undone successfully",
                "session_id": session_id,
                "next_display_order": new_next_order,
                "steps_undone": steps,
                "messages_removed": actual_messages_to_remove,
            }

        except (SessionNotFoundError, InvalidResponseError):
            # Known custom exceptions are re-raised
            raise
        except Exception as e:
            error = AssessmentError(
                "Failed to undo last answer due to unexpected error",
                {"user_id": user_id, "error": str(e), "error_type": type(e).__name__},
            )
            error.log_error(logger)
            raise error

    def get_conversation_history(self, user_id: str) -> Dict[str, Any]:
        """Get conversation history for session restoration"""
        try:
            session_id = self.session_repository.get_sessions_by_user(
                user_id, status="in_progress"
            )[0]
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

    def get_conversation_histories(
        self, user_id: str
    ) -> Dict[str, List[List[Message]]]:
        """Get complete conversation history for session restoration"""
        try:
            session_ids = self.session_repository.get_sessions_by_user(user_id)
            if not session_ids:
                logger.warning(
                    f"No complete sessions found for user {user_id}, returning empty history"
                )
                return {
                    "history": [],
                    "message": "No complete sessions found",
                    "status": "error",
                }
            session_questions_list = [
                self.question_repository.find_questions_by_session_id(session_id)
                for session_id in session_ids
            ]
            logger.debug(
                f"Retrieved {session_questions_list} session question lists for user {user_id}"
            )
            logger.info(
                f"Found {len(session_questions_list)} complete sessions for user {user_id}"
            )
            session_messages = {}
            for questions in session_questions_list:
                # groupby personality element
                if not questions:
                    continue
                if len(questions) < 5:
                    logger.warning(
                        f"Session {session_ids} has less than 5 questions, skipping"
                    )
                    continue
                # groupby personality element
                for question in questions:
                    question_id = question[0]
                    session_id = question[1]
                    if session_id not in session_messages:
                        session_messages[session_id] = [[], [], [], []]
                    logger.debug(
                        f"Processing question {question_id} for session {session_id}"
                    )
                    answer = self.answer_repository.get_answer_by_question_id(
                        question_id
                    )
                    if answer is None:
                        logger.warning(
                            f"No answer found for question {question_id} in session {session_id}"
                        )
                        continue
                    user_answer_text = answer[2]
                    question_text = question[4]
                    if (
                        type(question_text) is not str
                        or type(user_answer_text) is not str
                    ):
                        logger.warning(
                            f"Invalid question format for question {question_id} in session {session_id} - {question_text}, {user_answer_text}"
                        )

                        continue
                    message_pair = [
                        {"role": "assistant", "content": question_text},
                        {"role": "user", "content": user_answer_text},
                    ]
                    if question[2] == 1:
                        session_messages[session_id][0].extend(message_pair)
                    elif question[2] == 2:
                        session_messages[session_id][1].extend(message_pair)
                    elif question[2] == 3:
                        session_messages[session_id][2].extend(message_pair)
                    elif question[2] == 4:
                        session_messages[session_id][3].extend(message_pair)

            return session_messages

        except Exception as e:
            logger.error(
                f"Failed to get complete conversation history for user {user_id}: {e}"
            )
            return {
                "history": [],
                "message": f"Failed to get complete conversation history: {str(e)}",
                "status": "error",
            }
