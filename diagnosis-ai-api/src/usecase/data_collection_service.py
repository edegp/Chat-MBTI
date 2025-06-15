"""
Data collection specific business logic service.
This handles the 10 questions × 5 sets cycle for data collection.
"""

import os
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from ..exceptions import ValidationError
from ..port import DataCollectionRepositoryPort

logger = logging.getLogger(__name__)


class DataCollectionService:
    """Service for managing data collection specific business logic"""

    # Data collection configuration
    QUESTIONS_PER_SET = 10
    TOTAL_SETS = 5
    TOTAL_QUESTIONS = QUESTIONS_PER_SET * TOTAL_SETS  # 50 questions total
    ELEMENT_COUNT = 4  # Energy, Mind, Nature, Tactics

    def __init__(self, data_collection_repository: DataCollectionRepositoryPort):
        self.data_collection_repository = data_collection_repository

    def calculate_personality_element_id(self, question_number: int) -> int:
        """
        Calculate personality element ID based on question number for data collection.
        Data collection cycles through 4 elements every 10 questions:
        - Questions 1-10: Element 1 (Energy)
        - Questions 11-20: Element 2 (Mind)
        - Questions 21-30: Element 3 (Nature)
        - Questions 31-40: Element 4 (Tactics)
        - Questions 41-50: Element 1 (Energy) again
        """
        if question_number <= 0:
            return 1

        # Calculate which element (1-4) based on 10-question cycles
        element_id = (
            (question_number - 1) // self.QUESTIONS_PER_SET
        ) % self.ELEMENT_COUNT + 1

        logger.debug(
            f"Question {question_number} -> Element {element_id}",
            extra={
                "question_number": question_number,
                "element_id": element_id,
                "set_number": ((question_number - 1) // self.QUESTIONS_PER_SET) + 1,
            },
        )

        return element_id

    def get_current_set_number(self, question_number: int) -> int:
        """Get current set number (1-5) based on question number"""
        if question_number <= 0:
            return 1
        return ((question_number - 1) // self.QUESTIONS_PER_SET) + 1

    def get_question_in_set(self, question_number: int) -> int:
        """Get question position within current set (1-10)"""
        if question_number <= 0:
            return 1
        return ((question_number - 1) % self.QUESTIONS_PER_SET) + 1

    def is_set_complete(self, question_number: int) -> bool:
        """Check if current set is complete (just finished 10th question)"""
        return question_number > 0 and (question_number % self.QUESTIONS_PER_SET) == 0

    def is_element_switching(self, question_number: int) -> bool:
        """Check if we're switching to a new element (every 10 questions)"""
        return self.is_set_complete(question_number)

    def get_element_type_name(self, element_id: int) -> str:
        """Get human-readable element type name"""
        element_names = {
            1: "Energy (I/E)",
            2: "Mind (N/S)",
            3: "Nature (T/F)",
            4: "Tactics (J/P)",
        }
        return element_names.get(element_id, f"Element {element_id}")

    def is_data_collection_complete(self, question_number: int) -> bool:
        """Check if all data collection is complete"""
        return question_number >= self.TOTAL_QUESTIONS

    def get_progress_info(self, question_number: int) -> Dict[str, Any]:
        """Get comprehensive progress information"""
        current_set = self.get_current_set_number(question_number)
        question_in_set = self.get_question_in_set(question_number)
        element_id = self.calculate_personality_element_id(question_number)
        element_name = self.get_element_type_name(element_id)

        return {
            "current_set": current_set,
            "total_sets": self.TOTAL_SETS,
            "question_in_set": question_in_set,
            "questions_per_set": self.QUESTIONS_PER_SET,
            "overall_question_number": question_number,
            "total_questions": self.TOTAL_QUESTIONS,
            "element_id": element_id,
            "element_name": element_name,
            "is_set_complete": self.is_set_complete(question_number),
            "is_element_switching": self.is_element_switching(question_number),
            "is_complete": self.is_data_collection_complete(question_number),
            "progress_percentage": min(
                (question_number / self.TOTAL_QUESTIONS) * 100, 100
            ),
        }

    def validate_question_number(self, question_number: int) -> None:
        """Validate question number is within acceptable range"""
        if question_number < 0:
            raise ValidationError(
                f"Question number cannot be negative: {question_number}"
            )

        if question_number > self.TOTAL_QUESTIONS:
            logger.warning(
                f"Question number {question_number} exceeds total questions {self.TOTAL_QUESTIONS}"
            )

    def is_first_question_of_element_set(self, question_number: int) -> bool:
        """
        Check if this is the first question of an element set.
        These questions should be selected from initial_questions in element.yaml.

        Returns True for questions: 1, 11, 21, 31, 41 (first of each 10-question set)
        """
        if question_number <= 0:
            return True  # Question 0 or negative should be treated as first

        # First question of each set (1, 11, 21, 31, 41)
        return ((question_number - 1) % self.QUESTIONS_PER_SET) == 0

    def upload_data_collection_csv(
        self,
        participant_name: str,
        personality_code: str,
        csv_content: str,
        element_id: Optional[int] = None,
        cycle_number: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        Upload data collection CSV data.
        This method should handle the logic to save the CSV data to the database or file system.
        """
        try:
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Build safe directory path including personality code
            safe_name = participant_name.replace("/", "_")
            safe_code = personality_code.replace("/", "_")
            directory = Path("mbti_data") / f"{safe_name}_{safe_code}"

            # Construct file name path under directory
            if element_id and cycle_number:
                path = directory / str(element_id)
                file_name = (
                    path
                    / f"{safe_name}_{safe_code}_element_{element_id}_cycle_{cycle_number}_{now}.csv"
                )
            else:
                file_name = directory / f"{safe_name}_{safe_code}_all_data_{now}.csv"

            # Convert Path to string for upload
            file_name = str(file_name)
            uploaded_name = self.data_collection_repository.upload_data(
                file_name, csv_content
            )
            logger.info(f"Data collection CSV uploaded to {uploaded_name}")
            return {
                "file_name": uploaded_name,
            }
        except Exception as e:
            logger.error(f"Failed to upload data collection CSV: {str(e)}")
            raise RuntimeError(f"Data upload failed: {str(e)}")
