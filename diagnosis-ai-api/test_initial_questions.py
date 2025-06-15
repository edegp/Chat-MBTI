#!/usr/bin/env python3
"""
Test script to verify the initial question selection logic for data collection.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.usecase.data_collection_service import DataCollectionService
from src.driver.env import ElementsDriver


def test_initial_question_logic():
    """Test the logic for when to use initial_questions"""
    service = DataCollectionService()

    print("Testing initial question selection logic:")
    print("=" * 50)

    # Test the first question of each 10-question set
    test_questions = [0, 1, 11, 21, 31, 41, 2, 12, 22, 32, 42, 10, 20, 30, 40, 50]

    for q_num in test_questions:
        is_first = service.is_first_question_of_element_set(q_num)
        element_id = service.calculate_personality_element_id(q_num if q_num > 0 else 1)
        progress = service.get_progress_info(q_num if q_num > 0 else 1)

        print(
            f"Question {q_num:2d}: Element {element_id} - "
            + f"{'USE initial_questions' if is_first else 'Generate with LLM'} - "
            + f"Set {progress['current_set']}, Q{progress['question_in_set']}"
        )


def test_element_driver():
    """Test ElementsDriver initial question selection"""
    print("\nTesting ElementsDriver initial question selection:")
    print("=" * 50)

    try:
        elements_driver = ElementsDriver()

        for element_id in [1, 2, 3, 4]:
            print(f"\nElement {element_id}:")
            # Get 3 random selections to show variety
            for i in range(3):
                question = elements_driver.get_initial_question(element_id)
                print(f"  Sample {i+1}: {question}")

    except Exception as e:
        print(f"Error testing ElementsDriver: {e}")


if __name__ == "__main__":
    test_initial_question_logic()
    test_element_driver()
