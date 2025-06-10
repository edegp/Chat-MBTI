"""
Gateway implementation for workflow operations.
This layer adapts the LangGraph driver to the workflow port interface.
"""

from typing import Dict, Any, List
from ..port.ports import WorkflowPort
from ..driver.langgraph_driver import LangGraphDriver


class WorkflowGateway(WorkflowPort):
    """Gateway implementation for workflow orchestration"""

    def __init__(self, langgraph_driver: LangGraphDriver):
        self.driver = langgraph_driver

    def execute_conversation_flow(
        self, user_input: str, session_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Execute the conversation workflow and return results"""
        try:
            return self.driver.run_workflow(user_input, session_id, user_id)
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
