from fastapi import HTTPException, APIRouter, Depends
import logging

from .type import (
    UserRequest,
    QuestionResponse,
    OptionsRequest,
    OptionsResponse,
)
from ..usecase.graph import Graph
from ..driver.auth import get_current_user
from ..driver.db import init_db
from ..driver.llm import llm


logger = logging.getLogger(__name__)

router = APIRouter()

# Example for maintaining state across API calls
thread_states = {}  # Simple in-memory store for demonstration

graph = Graph()


# Startup event
@router.on_event("startup")
async def startup_event():
    """Verify the API is properly configured on startup"""
    try:
        init_db()
        llm.invoke("You are a helpful assistant.")

        print("LLM initialized successfully")
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        raise


# API Endpoints
@router.post("/generate_qa/question", response_model=QuestionResponse)
async def generate_mbti_question(
    request: UserRequest, firebase_user: dict = Depends(get_current_user)
):
    """Generate a new MBTI-related question based on previous conversation"""
    user_id = graph.chat_session_driver.get_or_create_user(
        firebase_uid=firebase_user["uid"]
    )

    messages = request.messages

    try:
        question = graph.get_question(messages, user_id)
    except ValueError as e:
        # Handle business rule exceptions
        if "No active session" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected exceptions
        logger.error(f"Error generating question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"question": question}


@router.get("/generate_qa/options", response_model=OptionsResponse)
async def generate_mbti_answer_options(firebase_user: dict = Depends(get_current_user)):
    """選択肢を生成する"""
    user_id = graph.chat_session_driver.get_or_create_user(
        firebase_uid=firebase_user["uid"]
    )

    try:
        options = graph.get_options(user_id=user_id)
        return {"options": options}
    except ValueError as e:
        # ビジネスルールに関する例外
        if "No active session" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # その他の予期しない例外
        logger.error(f"Error generating options: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/generate_qa/close_chat")
async def close_chat(
    request: OptionsRequest, firebase_user: dict = Depends(get_current_user)
):
    """Finish the chat session and clean up resources"""
    user_id = graph.chat_session_driver.get_or_create_user(
        firebase_uid=firebase_user["uid"]
    )
    try:
        # Close the chat session
        graph.close_chat(user_id)
    except ValueError as e:
        # Handle business rule exceptions
        if "No active session" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected exceptions
        logger.error(f"Error closing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"message": "Chat session closed successfully."}
