"""
LangGraph workflow driver.
This isolates LangGraph complexity from business logic.
"""

import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..port.ports import LLMPort, QuestionRepositoryPort
from ..usecase.type import ChatState, Message
from ..usecase.utils import _organize_chat_history
from ..driver.db import create_checkpointer

logger = logging.getLogger(__name__)


class LangGraphDriver:
    """Driver for LangGraph workflow orchestration"""

    def __init__(self, llm_port: LLMPort, question_repository: QuestionRepositoryPort):
        self.llm_port = llm_port
        self.question_repository = question_repository
        self.graph_builder = self._create_graph()

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
        try:
            messages = [m.dict() for m in state["messages"]]
            order = state["next_display_order"]

            # Save previous answer if exists
            if len(state["messages"]) > 0 and order > 0:
                answer_text = state["messages"][-1].content
                state["answers"][order] = answer_text

            chat_history = _organize_chat_history(messages)

            # Generate question through port interface
            question = self.llm_port.generate_question(
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

            return {
                "messages": [new_message],
                "pending_question": question,
                "pending_question_meta": {"model_version": "gemini-2.0-flash"},
                "session_id": state["session_id"],
                "personality_element_id": state["next_display_order"] // 4 + 1,
                "next_display_order": state["next_display_order"] + 1,
            }

        except Exception as e:
            logger.error(f"Error in question generation node: {e}")
            raise

    def _generate_options_node(self, state: ChatState) -> ChatState:
        """LangGraph node for options generation"""
        try:
            messages_text = _organize_chat_history(
                [m.dict() for m in state["messages"]]
            )
            num_options = 3
            options_list = []

            # Generate options through port interface
            for i in range(num_options):
                new_option = self.llm_port.generate_options(messages_text, options_list)
                options_list.append(new_option)
                logger.debug(f"Generated option {i + 1}: {new_option}")

            return {"options": [options_list]}

        except Exception as e:
            logger.error(f"Error in options generation node: {e}")
            raise

    def run_workflow(
        self, user_input: str, session_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Execute the LangGraph workflow"""
        try:
            checkpointer = create_checkpointer()
            config = {"configurable": {"thread_id": session_id}}

            # Create initial state
            messages = [Message(role="user", content=user_input)] if user_input else []
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

            if isinstance(checkpointer, MemorySaver):
                graph_with_memory = self.graph_builder.compile(
                    checkpointer=checkpointer
                )
                result = graph_with_memory.invoke(state, config=config)
                return result
            else:
                with checkpointer as cp:
                    try:
                        cp.get(config)
                    except Exception:
                        cp.setup()

                    graph_with_memory = self.graph_builder.compile(checkpointer=cp)
                    result = graph_with_memory.invoke(state, config=config)
                    return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise RuntimeError(f"Failed to execute workflow: {str(e)}")

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
