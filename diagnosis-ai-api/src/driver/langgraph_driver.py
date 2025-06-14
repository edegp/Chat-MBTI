"""
LangGraph workflow driver.
This isolates LangGraph complexity from business logic.
"""

import logging
import time
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..port.ports import LLMPort, QuestionRepositoryPort, ElementRepositoryPort
from ..usecase.type import ChatState, Message
from ..usecase.utils import _organize_chat_history
from ..driver.db import create_checkpointer
from ..exceptions import (
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    WorkflowError,
    QuestionGenerationError,
    InvalidResponseError,
)

logger = logging.getLogger(__name__)

# リトライ設定
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # 秒
BACKOFF_MULTIPLIER = 2.0


def retry_on_llm_error(func):
    """LLMエラーに対するリトライデコレータ"""

    def wrapper(*args, **kwargs):
        last_exception = None
        delay = RETRY_DELAY

        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except LLMRateLimitError as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})",
                        extra={"delay": delay, "attempt": attempt + 1},
                    )
                    time.sleep(delay)
                    delay *= BACKOFF_MULTIPLIER
                else:
                    logger.error("Max retries exceeded for rate limit")
                    raise
            except LLMTimeoutError as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"Timeout occurred, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})",
                        extra={"delay": delay, "attempt": attempt + 1},
                    )
                    time.sleep(delay)
                    delay *= BACKOFF_MULTIPLIER
                else:
                    logger.error("Max retries exceeded for timeout")
                    raise
            except LLMError as e:
                # 他のLLMエラーは即座に失敗
                logger.error(
                    "LLM error occurred, not retrying", extra={"error": str(e)}
                )
                raise

        # このポイントに到達することはないはずですが、安全のため
        raise last_exception

    return wrapper


def _filter_messages_by_phase(messages: list, current_question_number: int) -> list:
    """Filter messages to only include those from the current phase (5 questions per phase)"""
    if current_question_number <= 0:
        return []

    # Calculate current phase (1-based)
    current_phase = ((current_question_number - 1) // 5) + 1

    # Calculate phase boundaries
    phase_start_question = (current_phase - 1) * 5 + 1  # 1, 6, 11, 16
    phase_end_question = current_phase * 5  # 5, 10, 15, 20

    logger.info(
        f"Filtering messages for phase {current_phase}: questions {phase_start_question}-{phase_end_question}"
    )
    logger.debug(f"Current question number: {current_question_number}")

    # Filter messages to only include current phase
    # Count questions to determine which phase each message belongs to
    question_count = 0
    filtered_messages = []

    for msg in messages:
        if msg.get("role") == "assistant":
            question_count += 1
            # Include question if it's in current phase AND we haven't reached the current question being generated
            if phase_start_question <= question_count <= current_question_number:
                filtered_messages.append(msg)
        elif (
            msg.get("role") == "user"
            and len(filtered_messages) > 0
            and filtered_messages[-1].get("role") == "assistant"
        ):
            # Include user answer if we included the corresponding question
            filtered_messages.append(msg)

    logger.debug(
        f"Filtered {len(messages)} messages to {len(filtered_messages)} for current phase"
    )
    return filtered_messages


class LangGraphDriver:
    """Driver for LangGraph workflow orchestration"""

    def __init__(
        self,
        llm_port: LLMPort,
        question_repository: QuestionRepositoryPort,
        elements_repository: ElementRepositoryPort,
    ):
        self.llm_port = llm_port
        self.question_repository = question_repository
        self.elements_repository = elements_repository
        try:
            self.graph_builder = self._create_graph()
            logger.info("LangGraphDriver initialized successfully")
        except Exception as e:
            error = WorkflowError(
                "Failed to initialize LangGraphDriver", {"error": str(e)}
            )
            error.log_error(logger)
            raise error

    def _create_graph(self) -> StateGraph:
        """Create LangGraph StateGraph with nodes and edges"""
        sg = StateGraph(ChatState)

        # Register nodes
        sg.add_node("generate_question", self._generate_question_node)
        sg.add_node("generate_options", self._generate_options_node)

        # Define edges
        sg.add_edge(START, "generate_question")
        sg.add_edge("generate_question", "generate_options")
        sg.add_edge("generate_options", END)

        return sg

    def _generate_question_node(self, state: ChatState) -> ChatState:
        """LangGraph node for question generation"""
        logger.debug(
            f"Entering question generation node with state: {state}",
        )
        # 初回のみリポジトリから質問を取得して返す
        if state.get("next_display_order", 0) == 0:
            question = self.elements_repository.get_initial_question(
                state.get("personality_element_id", 1)
            )
            qid = self.question_repository.save_question(
                {
                    "session_id": state.get("session_id"),
                    "display_order": 0,
                    "question": question,
                }
            )
            new_message = Message(role="assistant", content=question)
            return {
                "messages": [new_message],
                "pending_question": question,
                "pending_question_meta": {},
                "session_id": state.get("session_id"),
                "personality_element_id": state.get("personality_element_id", 1),
                "next_display_order": 1,
            }
        try:
            logger.info(
                "Starting question generation",
                extra={
                    "session_id": state.get("session_id"),
                    "next_display_order": state.get("next_display_order"),
                    "personality_element_id": state.get("personality_element_id"),
                },
            )

            messages = [
                m.model_dump() if hasattr(m, "model_dump") else m
                for m in state["messages"]
            ]
            order = state["next_display_order"]

            # Save previous answer if exists
            if len(state["messages"]) > 0 and order > 0:
                answer_text = state["messages"][-1].content
                state["answers"][order] = answer_text

            # Filter messages to only include current phase context (every 5 questions)
            current_question_number = order + 1  # next question number
            filtered_messages = _filter_messages_by_phase(
                messages, current_question_number
            )
            chat_history = _organize_chat_history(filtered_messages)

            # Generate question through port interface with retry
            question = self._generate_question_with_retry(
                chat_history,
                {
                    "personality_element_id": state["personality_element_id"],
                    "next_display_order": state["next_display_order"],
                },
            )

            # Save question to repository through port
            qid = self.question_repository.save_question(
                {
                    "session_id": state["session_id"],
                    "personality_element_id": state["personality_element_id"],
                    "display_order": state["next_display_order"],
                    "question": question,
                    "model_version": "gemini-2.0-flash",
                }
            )

            # Save answer if we have one
            if len(state["messages"]) > 0 and order > 0:
                answer_text = state["messages"][-1].content
                self.question_repository.save_answer(qid, answer_text)

            # Create new message
            new_message = Message(role="assistant", content=question)

            logger.info(
                "Question generation completed successfully",
                extra={
                    "session_id": state.get("session_id"),
                    "question_id": str(qid),
                    "next_display_order": state.get("next_display_order"),
                },
            )
            logger.debug(f"{new_message.role} message generated: {new_message.content}")

            return {
                "messages": [new_message],
                "pending_question": question,
                "pending_question_meta": {"model_version": "gemini-2.0-flash"},
                "session_id": state["session_id"],
                "personality_element_id": state["next_display_order"] // 4 + 1,
                "next_display_order": state["next_display_order"] + 1,
            }

        except Exception as e:
            error = QuestionGenerationError(
                "Failed to generate question in workflow node",
                {
                    "session_id": state.get("session_id"),
                    "next_display_order": state.get("next_display_order"),
                    "error": str(e),
                },
            )
            logger.error(
                f"Error during question generation {state.get("next_display_order")}: {e}"
            )
            error.log_error(logger)
            raise error

    @retry_on_llm_error
    def _generate_question_with_retry(
        self, chat_history: str, context: Dict[str, Any]
    ) -> str:
        """質問生成をリトライ機能付きで実行"""
        try:
            return self.llm_port.generate_question(chat_history, context)
        except Exception as e:
            # LLMポートからの例外を適切なカスタム例外に変換
            if "rate limit" in str(e).lower():
                raise LLMRateLimitError(
                    "Rate limit exceeded during question generation", {"error": str(e)}
                )
            elif "timeout" in str(e).lower():
                raise LLMTimeoutError(
                    "Timeout during question generation", {"error": str(e)}
                )
            else:
                logger.error(
                    f"LLM error during question generation {context.get('next_display_order')}: {e}"
                )
                raise LLMError(
                    "LLM error during question generation", {"error": str(e)}
                )

    def _generate_options_node(self, state: ChatState) -> ChatState:
        """LangGraph node for options generation"""
        try:
            logger.info(
                "Starting options generation",
                extra={
                    "session_id": state.get("session_id"),
                    "next_display_order": state.get("next_display_order"),
                },
            )

            # Filter messages to only include current phase context
            current_question_number = state["next_display_order"]
            messages = [
                m.model_dump() if hasattr(m, "model_dump") else m
                for m in state["messages"]
            ]
            logger.debug(
                f"Messages before filtering: {messages}",
                extra={
                    "session_id": state.get("session_id"),
                    "next_display_order": state.get("next_display_order"),
                },
            )
            filtered_messages = _filter_messages_by_phase(
                messages, current_question_number
            )
            messages_text = _organize_chat_history(filtered_messages)
            num_options = 3
            options_list = []

            logger.debug(
                f"Filtered messages for options generation: {filtered_messages}",
                extra={
                    "session_id": state.get("session_id"),
                    "next_display_order": state.get("next_display_order"),
                },
            )

            # Generate options through port interface with retry
            for i in range(num_options):
                new_option = self._generate_option_with_retry(
                    messages_text, options_list
                )
                options_list.append(new_option)
                logger.debug(f"Generated option {i + 1}: {new_option}")

            logger.info(
                "Options generation completed successfully",
                extra={
                    "session_id": state.get("session_id"),
                    "options_count": len(options_list),
                },
            )

            return {"options": [options_list]}

        except Exception as e:
            error = QuestionGenerationError(
                "Failed to generate options in workflow node",
                {
                    "session_id": state.get("session_id"),
                    "next_display_order": state.get("next_display_order"),
                    "error": str(e),
                },
            )
            error.log_error(logger)
            raise error

    @retry_on_llm_error
    def _generate_option_with_retry(
        self, messages_text: str, existing_options: List[str]
    ) -> str:
        """選択肢生成をリトライ機能付きで実行"""
        try:
            return self.llm_port.generate_options(messages_text, existing_options)
        except Exception as e:
            # LLMポートからの例外を適切なカスタム例外に変換
            if "rate limit" in str(e).lower():
                raise LLMRateLimitError(
                    "Rate limit exceeded during options generation", {"error": str(e)}
                )
            elif "timeout" in str(e).lower():
                raise LLMTimeoutError(
                    "Timeout during options generation", {"error": str(e)}
                )
            else:
                raise LLMError("LLM error during options generation", {"error": str(e)})

    def run_workflow(
        self, user_messages: List[Message], session_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Execute the LangGraph workflow"""
        try:
            logger.info(
                "Starting workflow execution",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "has_user_input": bool(user_messages),
                },
            )

            checkpointer = create_checkpointer()
            config = {"configurable": {"thread_id": session_id}}

            # Try to get existing state first
            existing_state = None
            try:
                existing_state = self.get_state(session_id)
                if existing_state:
                    logger.info(
                        "Retrieved existing workflow state",
                        extra={
                            "session_id": session_id,
                            "next_display_order": existing_state.get(
                                "next_display_order", 0
                            ),
                        },
                    )
            except Exception as e:
                logger.info(
                    "No existing state found, creating new workflow",
                    extra={"session_id": session_id, "reason": str(e)},
                )

            # Create initial state or continue from existing state
            messages = [msg for msg in user_messages if msg.content != ""]
            logging.debug(
                f"User messages for workflow: {messages}",
                extra={"session_id": session_id, "user_id": user_id},
            )
            if existing_state and "next_display_order" in existing_state:
                # Continue from existing state
                current_next_order = existing_state.get("next_display_order", 0)
                logger.info(
                    f"Continuing from existing state: next_display_order={current_next_order}"
                )

                # Check if we're starting a new phase (every 5 questions)
                current_phase = (
                    ((current_next_order - 1) // 5) + 1 if current_next_order > 0 else 1
                )
                question_number_in_phase = (
                    ((current_next_order - 1) % 5) + 1 if current_next_order > 0 else 1
                )

                # If this is the first question of a new phase, clear phase-specific context
                existing_messages = existing_state.get("messages", [])
                if question_number_in_phase == 1 and current_next_order > 0:
                    logger.info(
                        f"Starting new phase {current_phase}, filtering messages for phase context"
                    )
                    # Keep only messages from current phase for context
                    filtered_existing_messages = _filter_messages_by_phase(
                        [
                            m.model_dump() if hasattr(m, "model_dump") else m
                            for m in existing_messages
                        ],
                        current_next_order,
                    )
                    existing_messages = [
                        Message(**msg) if isinstance(msg, dict) else msg
                        for msg in filtered_existing_messages
                    ]

                state = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "messages": messages,  # use only new user messages
                    "options": existing_state.get("options", []),
                    "next_display_order": current_next_order,
                    "personality_element_id": existing_state.get(
                        "personality_element_id", 1
                    ),
                    "answers": existing_state.get("answers", {}),
                    "phase": existing_state.get("phase", "ask"),
                    "pending_question": existing_state.get("pending_question"),
                    "pending_question_meta": existing_state.get(
                        "pending_question_meta", {}
                    ),
                }

            else:
                # Create fresh state for new conversation
                logger.info("Creating new conversation state")
                state = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "messages": messages,
                    "options": [],
                    "next_display_order": 0,
                    "personality_element_id": 1,
                    "answers": {},
                    "phase": "ask",
                    "pending_question": None,
                    "pending_question_meta": {},
                }

            # Execute workflow
            if isinstance(checkpointer, MemorySaver):
                graph_with_memory = self.graph_builder.compile(
                    checkpointer=checkpointer
                )
                result = graph_with_memory.invoke(state, config=config)
            else:
                with checkpointer as cp:
                    try:
                        cp.get(config)
                    except Exception:
                        cp.setup()

                    graph_with_memory = self.graph_builder.compile(checkpointer=cp)
                    result = graph_with_memory.invoke(state, config=config)

            logger.info(
                "Workflow execution completed successfully",
                extra={"session_id": session_id, "result_type": type(result).__name__},
            )
            return result

        except (LLMError, QuestionGenerationError, WorkflowError):
            # 既知のカスタム例外は再発生
            raise
        except Exception as e:
            error = WorkflowError(
                "Workflow execution failed with unexpected error",
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            logger.debug(f"Unexpected error during workflow execution {e}")
            error.log_error(logger)
            raise error

    def get_state(self, session_id: str) -> Dict[str, Any]:
        """Get current workflow state"""
        try:
            checkpointer = create_checkpointer()
            config = {"configurable": {"thread_id": session_id}}

            if isinstance(checkpointer, MemorySaver):
                graph_with_memory = self.graph_builder.compile(
                    checkpointer=checkpointer
                )
                state_result = graph_with_memory.get_state(config)
                return state_result.values if state_result else {}
            else:
                with checkpointer as cp:
                    cp.setup()
                    graph_with_memory = self.graph_builder.compile(checkpointer=cp)
                    state_result = graph_with_memory.get_state(config)
                    return state_result.values if state_result else {}

        except Exception as e:
            logger.error(f"Failed to get workflow state: {e}")
            raise RuntimeError(f"Failed to get state: {str(e)}")

    def get_options(self, session_id: str) -> List[str]:
        """Get available options for current question"""
        try:
            state = self.get_state(session_id)
            if state and "options" in state and len(state["options"]) > 0:
                return state["options"][0]
            return []
        except Exception as e:
            logger.error(f"Failed to get options: {e}")
            raise RuntimeError(f"Failed to get options: {str(e)}")
