"""
Gateway implementations for repository operations.
This layer adapts the driver layer to the port interfaces.
"""

from typing import Dict, Any, Optional
from ..port.ports import QuestionRepositoryPort, SessionRepositoryPort
from ..driver.db import GeneratedQuestionDriver, UserAnswerDriver, ChatSessionDriver


class QuestionRepositoryGateway(QuestionRepositoryPort):
    """Gateway implementation for question repository operations"""

    def __init__(self):
        self.question_driver = GeneratedQuestionDriver()
        self.answer_driver = UserAnswerDriver()

    def save_question(self, question_data: Dict[str, Any]) -> str:
        """Save generated question and return question ID"""
        try:
            qid = self.question_driver.post_question(
                session_id=question_data["session_id"],
                personality_element_id=question_data.get("personality_element_id", 1),
                display_order=question_data["display_order"],
                question=question_data["question"],
                model_version=question_data.get("model_version", "gemini-2.0-flash"),
            )
            return qid
        except Exception as e:
            raise RuntimeError(f"Failed to save question: {str(e)}")

    def get_question_by_session(
        self, session_id: str, order: int
    ) -> Optional[Dict[str, Any]]:
        """Get question by session ID and display order"""
        try:
            qid = self.question_driver.get_id(session_id=session_id, order=order)
            if qid:
                return {"question_id": qid}
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to get question: {str(e)}")

    def save_answer(self, question_id: str, answer_text: str) -> None:
        """Save user answer to question"""
        try:
            self.answer_driver.post_answer(
                question_id=question_id, answer_text=answer_text
            )
        except Exception as e:
            raise RuntimeError(f"Failed to save answer: {str(e)}")


class SessionRepositoryGateway(SessionRepositoryPort):
    """Gateway implementation for session management operations"""

    def __init__(self):
        self.session_driver = ChatSessionDriver()

    def create_session(self, user_id: str) -> str:
        """Create new chat session and return session ID"""
        try:
            # First get or create user with Firebase UID
            db_user_id = self.session_driver.get_or_create_user(user_id)
            return self.session_driver.create_session(db_user_id)
        except Exception as e:
            raise RuntimeError(f"Failed to create session: {str(e)}")

    def get_session_by_user(self, user_id: str) -> Optional[str]:
        """Get active session ID for user"""
        try:
            # First get or create user with Firebase UID
            db_user_id = self.session_driver.get_or_create_user(user_id)
            return self.session_driver.get_session_by_user_id(db_user_id)
        except Exception as e:
            raise RuntimeError(f"Failed to get session: {str(e)}")

    def close_session(self, session_id: str) -> None:
        """Close chat session"""
        try:
            self.session_driver.close_session(session_id)
        except Exception as e:
            raise RuntimeError(f"Failed to close session: {str(e)}")
