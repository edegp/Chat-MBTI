"""
Gateway implementation for workflow operations.
This layer adapts the LangGraph driver to the workflow port interface.
"""

from typing import Dict, Any, List
from ..port.ports import WorkflowPort
from ..driver.langgraph_driver import LangGraphDriver
from ..usecase.type import Message


class WorkflowGateway(WorkflowPort):
    """Gateway implementation for workflow orchestration"""

    def __init__(self, langgraph_driver: LangGraphDriver):
        self.driver = langgraph_driver

    def execute_conversation_flow(
        self,
        user_input: str,
        session_id: str,
        user_id: str,
        personality_element_id: int = None,
    ) -> Dict[str, Any]:
        """Execute the conversation workflow and return results"""
        try:
            # wrap raw user input into a single Message for the workflow
            messages = [Message(role="user", content=user_input)]
            # Call run_workflow without element_id when None (tests expect 3 args)
            if personality_element_id is None:
                return self.driver.run_workflow(
                    messages,
                    session_id,
                    user_id,
                )
            else:
                return self.driver.run_workflow(
                    messages,
                    session_id,
                    user_id,
                    personality_element_id,
                )
        except Exception as e:
            raise RuntimeError(f"Failed to execute conversation flow: {str(e)}")

    def get_conversation_state(self, session_id: str) -> Dict[str, Any]:
        """Get current state of conversation"""
        try:
            return self.driver.get_state(session_id)
        except Exception as e:
            raise RuntimeError(f"Failed to get conversation state: {str(e)}")

    def get_conversation_options(self, session_id: str) -> List[str]:
        """Get available options for current question"""
        try:
            return self.driver.get_options(session_id)
        except Exception as e:
            raise RuntimeError(f"Failed to get conversation options: {str(e)}")
