#!/usr/bin/env python3
"""
Test element switching logic in data collection workflow
"""


class DummyRepo:
    pass


def test_langgraph_element_calculation():
    """Test LangGraphDriver element calculation logic"""
    questions_per_phase = 10

    print("=== LangGraphDriver Element Calculation Test ===")

    for current_order in [0, 10, 20, 30, 40, 50]:
        is_first_question_of_phase = current_order == 0 or (
            current_order % questions_per_phase == 0
        )

        if is_first_question_of_phase and questions_per_phase == 10:
            element_id = ((current_order // questions_per_phase) % 4) + 1
            print(
                f"current_order={current_order}: is_first={is_first_question_of_phase}, element_id={element_id}"
            )
        else:
            print(
                f"current_order={current_order}: is_first={is_first_question_of_phase}, use_state_element"
            )


def test_data_collection_service_calculation():
    """Test DataCollectionService element calculation"""
    from src.usecase.data_collection_service import DataCollectionService

    print("\n=== DataCollectionService Element Calculation Test ===")

    dc_service = DataCollectionService(data_collection_repository=DummyRepo())

    for question_num in [1, 10, 11, 20, 21, 30, 31, 40, 41, 50]:
        element_id = dc_service.calculate_personality_element_id(question_num)
        is_first = dc_service.is_first_question_of_element_set(question_num)
        print(
            f"question_num={question_num}: element_id={element_id}, is_first={is_first}"
        )


def test_workflow_order_mapping():
    """Test workflow order vs question number mapping"""
    print("\n=== Workflow Order vs Question Number Mapping ===")

    # In workflow: current_order is 0-based
    # In data collection: question_number is 1-based

    for current_order in range(0, 11):
        question_number = current_order + 1

        # LangGraph logic
        is_first_phase = current_order == 0 or (current_order % 10 == 0)
        if is_first_phase:
            lg_element_id = ((current_order // 10) % 4) + 1
        else:
            lg_element_id = "state"

        # DataCollection logic
        from src.usecase.data_collection_service import DataCollectionService

        dc_service = DataCollectionService(data_collection_repository=DummyRepo())
        dc_element_id = dc_service.calculate_personality_element_id(question_number)
        dc_is_first = dc_service.is_first_question_of_element_set(question_number)

        print(f"current_order={current_order}, question_num={question_number}")
        print(f"  LangGraph: is_first={is_first_phase}, element_id={lg_element_id}")
        print(f"  DataCollection: is_first={dc_is_first}, element_id={dc_element_id}")
        print()


if __name__ == "__main__":
    test_langgraph_element_calculation()
    test_data_collection_service_calculation()
    test_workflow_order_mapping()
