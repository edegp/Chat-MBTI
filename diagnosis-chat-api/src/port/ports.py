"""
Port interfaces for MBTI conversation AI system.
These abstract interfaces define contracts between layers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMPort(ABC):
    """Abstract interface for LLM operations"""

    @abstractmethod
    def generate_question(self, chat_history: str, context: Dict[str, Any]) -> str:
        """Generate MBTI question based on conversation history"""
        pass

    @abstractmethod
    def generate_options(self, messages: str, existing_options: List[str]) -> str:
        """Generate answer options for current question"""
        pass


class WorkflowPort(ABC):
    """Abstract interface for AI workflow orchestration"""

    @abstractmethod
    def execute_conversation_flow(
        self, user_input: str, session_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Execute the conversation workflow and return results"""
        pass

    @abstractmethod
    def get_conversation_state(self, session_id: str) -> Dict[str, Any]:
        """Get current state of conversation"""
        pass

    @abstractmethod
    def update_conversation_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Update conversation state"""
        pass

    @abstractmethod
    def get_conversation_options(self, session_id: str) -> List[str]:
        """Get available options for current question"""
        pass


class QuestionRepositoryPort(ABC):
    """Abstract interface for question data operations"""

    @abstractmethod
    def save_question(self, question_data: Dict[str, Any]) -> str:
        """Save generated question and return question ID"""
        pass

    @abstractmethod
    def get_question_by_session(
        self, session_id: str, order: int
    ) -> Optional[Dict[str, Any]]:
        """Get question by session ID and display order"""
        pass

    def find_questions_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Find questions by session ID and display order"""
        pass


class AnswerRepositoryPort(ABC):
    """Abstract interface for user answer operations"""

    @abstractmethod
    def save_answer(self, question_id: str, answer_text: str) -> None:
        """Save user answer to question"""
        pass

    @abstractmethod
    def get_answer_by_question_id(self, question_id: str) -> Optional[str]:
        """Get user answer by question ID"""
        pass


class SessionRepositoryPort(ABC):
    """Abstract interface for session management"""

    @abstractmethod
    def get_or_create_user_id(self, firebase_uid: str) -> str:
        """Get or create user with Firebase UID and return database user ID"""
        pass

    @abstractmethod
    def create_session(self, user_id: str) -> str:
        """Create new chat session and return session ID

        Args:
            user_id: Firebase UID of the authenticated user
        """
        pass

    @abstractmethod
    def get_sessions_by_user(self, user_id: str, status: str = None) -> Optional[str]:
        """Get active session ID for user

        Args:
            user_id: Firebase UID of the authenticated user
        """
        pass

    @abstractmethod
    def close_session(self, session_id: str) -> None:
        """Close chat session"""
        pass


class ElementRepositoryPort(ABC):
    """Abstract interface for element data operations"""

    @abstractmethod
    def get_element_info(self, element_id: str) -> Dict[str, Any]:
        """Get information about a personality element"""
        pass

    @abstractmethod
    def get_question_per_phase(self) -> int:
        """Get number of questions per phase"""
        pass

    @abstractmethod
    def get_elements(self) -> List[Dict[str, Any]]:
        """Get all personality elements"""
        pass

    @abstractmethod
    def get_initial_question(self, element_id: str) -> Dict[str, Any]:
        """Get initial question for a personality element"""
        pass


class DataCollectionRepositoryPort(ABC):
    """Abstract interface for data collection operations"""

    @abstractmethod
    def upload_data_collection(self, user_id: str, data: Dict[str, Any]) -> None:
        """Upload data collection for a user"""
        pass


class MBTIReportRepositoryPort(ABC):
    """Abstract interface for report data operations"""

    @abstractmethod
    def save_report(
        self, user_id: str, element_id: int, report: str, pred_label: str = None
    ) -> None:
        """Save MBTI report for a user"""
        pass

    @abstractmethod
    def get_reports_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch all MBTI reports for a user"""
        pass


__all__ = [
    "LLMPort",
    "WorkflowPort",
    "QuestionRepositoryPort",
    "SessionRepositoryPort",
    "ElementRepositoryPort",
    "DataCollectionRepositoryPort",
    "MBTIReportRepositoryPort",
]
