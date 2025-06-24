"""
Dependency Injection Container
This module wires up all the dependencies according to the Port & Adapter pattern.
"""

from src.port.ports import (
    LLMPort,
    WorkflowPort,
    QuestionRepositoryPort,
    SessionRepositoryPort,
    ElementRepositoryPort,
)
from src.gateway.llm_gateway import LLMGateway
from src.gateway.repository_gateway import (
    QuestionRepositoryGateway,
    SessionRepositoryGateway,
    ElementRepositoryGateway,
)
from src.gateway.workflow_gateway import WorkflowGateway
from src.driver.langgraph_driver import LangGraphDriver
from src.usecase.mbti_conversation_service import MBTIConversationService
from src.controller.mbti_controller import MBTIController


class DIContainer:
    """Dependency Injection Container for the MBTI application"""

    def __init__(self):
        self._instances = {}

    def get_llm_port(self) -> LLMPort:
        """Get LLM port instance"""
        if "llm_port" not in self._instances:
            self._instances["llm_port"] = LLMGateway()
        return self._instances["llm_port"]

    def get_question_repository_port(self) -> QuestionRepositoryPort:
        """Get question repository port instance"""
        if "question_repository_port" not in self._instances:
            self._instances["question_repository_port"] = QuestionRepositoryGateway()
        return self._instances["question_repository_port"]

    def get_session_repository_port(self) -> SessionRepositoryPort:
        """Get session repository port instance"""
        if "session_repository_port" not in self._instances:
            self._instances["session_repository_port"] = SessionRepositoryGateway()
        return self._instances["session_repository_port"]

    def get_elements_repository_port(self) -> ElementRepositoryPort:
        """Get elements repository port instance"""
        if "elements_repository_port" not in self._instances:
            self._instances["elements_repository_port"] = ElementRepositoryGateway()
        return self._instances["elements_repository_port"]

    def get_langgraph_driver(self, questions_per_phase: int = 5) -> LangGraphDriver:
        """Get LangGraph driver instance with configurable questions per phase"""
        cache_key = f"langgraph_driver_{questions_per_phase}"
        if cache_key not in self._instances:
            self._instances[cache_key] = LangGraphDriver(
                llm_port=self.get_llm_port(),
                question_repository=self.get_question_repository_port(),
                elements_repository=self.get_elements_repository_port(),
                questions_per_phase=questions_per_phase,
            )
        return self._instances[cache_key]

    def get_data_collection_langgraph_driver(self) -> LangGraphDriver:
        """Get LangGraph driver instance configured for data collection (10 questions per phase)"""
        return self.get_langgraph_driver(questions_per_phase=10)

    def get_workflow_port(self) -> WorkflowPort:
        """Get workflow port instance"""
        if "workflow_port" not in self._instances:
            self._instances["workflow_port"] = WorkflowGateway(
                langgraph_driver=self.get_langgraph_driver()
            )
        return self._instances["workflow_port"]

    def get_data_collection_workflow_port(self) -> WorkflowPort:
        """Get workflow port instance configured for data collection"""
        if "data_collection_workflow_port" not in self._instances:
            self._instances["data_collection_workflow_port"] = WorkflowGateway(
                langgraph_driver=self.get_data_collection_langgraph_driver()
            )
        return self._instances["data_collection_workflow_port"]

    def get_mbti_service(self) -> MBTIConversationService:
        """Get MBTI conversation service instance"""
        if "mbti_service" not in self._instances:
            self._instances["mbti_service"] = MBTIConversationService(
                workflow_port=self.get_workflow_port(),
                question_repository=self.get_question_repository_port(),
                session_repository=self.get_session_repository_port(),
                elements_repository=self.get_elements_repository_port(),
                data_collection_workflow_port=self.get_data_collection_workflow_port(),
            )
        return self._instances["mbti_service"]

    def get_mbti_controller(self) -> MBTIController:
        """Get MBTI controller instance"""
        if "mbti_controller" not in self._instances:
            self._instances["mbti_controller"] = MBTIController(
                mbti_service=self.get_mbti_service()
            )
        return self._instances["mbti_controller"]


# Global container instance
container = DIContainer()
