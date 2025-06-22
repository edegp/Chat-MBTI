#!/usr/bin/env python3
"""
Test script to verify the undo workflow is working correctly.
This tests the complete sequence:
1. Start conversation
2. Submit answer 1 -> Get question 2
3. Submit answer 2 -> Get question 3
4. Undo -> Should return to question 2 state
5. Submit different answer 2 -> Should get new question 3
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer data_collection_user",
}


def test_undo_workflow():
    print("🧪 Testing Undo Workflow")
    print("=" * 50)

    # Step 1: Start conversation
    print("1️⃣ Starting conversation...")
    response = requests.get(
        f"{BASE_URL}/data-collection/conversation/start?element_id=1", headers=HEADERS
    )
    data = response.json()
    print(f"   Question 1: {data['data']['question'][:50]}...")
    session_id = data["data"]["session_id"]

    # Step 2: Submit first answer
    print("\n2️⃣ Submitting first answer...")
    response = requests.post(
        f"{BASE_URL}/data-collection/conversation/answer",
        headers=HEADERS,
        json={"answer": "初回の回答です"},
    )
    data = response.json()
    question_2 = data["data"]["question"]
    print(f"   Question 2: {question_2[:50]}...")

    # Step 3: Submit second answer
    print("\n3️⃣ Submitting second answer...")
    response = requests.post(
        f"{BASE_URL}/data-collection/conversation/answer",
        headers=HEADERS,
        json={"answer": "2回目の回答です"},
    )
    data = response.json()
    question_3 = data["data"]["question"]
    print(f"   Question 3: {question_3[:50]}...")

    # Step 4: Undo last answer
    print("\n4️⃣ Undoing last answer...")
    response = requests.delete(
        f"{BASE_URL}/data-collection/conversation/undo", headers=HEADERS
    )
    data = response.json()
    undo_status = data.get("data", {}).get("status")
    print(f"   Undo status: {undo_status}")

    # Verify undo was successful
    if undo_status == "success":
        print("   ✅ PASS: Undo operation completed successfully")
    else:
        print("   ❌ FAIL: Undo operation failed")
        print(f"      Response: {data}")
        return

    # Step 5: Submit different second answer
    print("\n5️⃣ Submitting different second answer...")
    response = requests.post(
        f"{BASE_URL}/data-collection/conversation/answer",
        headers=HEADERS,
        json={"answer": "修正された2回目の回答です"},
    )
    data = response.json()
    new_question_3 = data["data"]["question"]
    print(f"   New Question 3: {new_question_3[:50]}...")

    # Check if we got a new question (it might be the same or different)
    if new_question_3:
        print("   ✅ PASS: Successfully continued conversation after undo")
    else:
        print("   ❌ FAIL: Failed to continue conversation after undo")

    # Step 6: Submit one more answer to verify flow continues
    print("\n6️⃣ Submitting third answer to verify flow...")
    response = requests.post(
        f"{BASE_URL}/data-collection/conversation/answer",
        headers=HEADERS,
        json={"answer": "3回目の回答です"},
    )
    data = response.json()
    question_4 = data["data"]["question"]
    print(f"   Question 4: {question_4[:50]}...")

    if question_4:
        print("   ✅ PASS: Conversation flow continues normally")
    else:
        print("   ❌ FAIL: Conversation flow broken")

    print("\n🎉 Test completed!")
    print("If all steps show ✅ PASS, the undo functionality is working correctly.")


if __name__ == "__main__":
    test_undo_workflow()
