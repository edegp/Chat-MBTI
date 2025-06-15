"""
Gateway implementations for repository operations.
This layer adapts the driver layer to the port interfaces.
"""

import os
from typing import Dict, Any, Optional, List
from ..port.ports import (
    QuestionRepositoryPort,
    SessionRepositoryPort,
    ElementRepositoryPort,
)
from ..driver.db import GeneratedQuestionDriver, UserAnswerDriver, ChatSessionDriver
from ..driver.env import ElementsDriver
from ..driver.gcs import GCSDriver


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


class ElementRepositoryGateway(ElementRepositoryPort):
    """Gateway implementation for personality element operations"""

    def __init__(self):
        self.element_driver = ElementsDriver()

    def get_element_info(self, element_id: int) -> Dict[str, Any]:
        """Get personality element information by ID"""
        try:
            return self.element_driver.get_element_info(element_id)
        except Exception as e:
            raise RuntimeError(f"Failed to get element info: {str(e)}")

    def get_elements(self) -> List[Dict[str, Any]]:
        """Get all personality elements"""
        try:
            return self.element_driver.get_elements()
        except Exception as e:
            raise RuntimeError(f"Failed to get elements: {str(e)}")

    def get_initial_question(self, element_id: int = 1) -> str:
        """Get initial question for personality element"""
        try:
            return self.element_driver.get_initial_question(element_id)
        except Exception as e:
            raise RuntimeError(f"Failed to get initial question: {str(e)}")


class DataCollectionRepositoryGateway:
    """Gateway implementation for data collection operations"""

    def __init__(self):
        # Placeholder for actual upload logic
        bucket_name = os.getenv("GCS_BUCKET_NAME", "your-default-bucket")
        # プロジェクトIDを環境変数またはquota_project_idから取得
        project_id = (
            os.getenv("GCP_PROJECT")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCLOUD_PROJECT")
            or "chat-mbti-458210"
        )
        self.gcs_driver = GCSDriver(bucket_name=bucket_name, project_id=project_id)

    def upload_data(self, file_name, csv_content) -> str:
        """Upload data to Google Cloud Storage"""
        try:
            uploaded_blob = self.gcs_driver.upload_blob(
                blob_name=file_name, content=csv_content
            )
            return uploaded_blob
        except Exception as e:
            raise RuntimeError(f"Failed to upload data: {str(e)}")
