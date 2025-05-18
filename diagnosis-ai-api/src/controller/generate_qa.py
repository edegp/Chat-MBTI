from fastapi import HTTPException, APIRouter
import time
import traceback
import logging

from .type import (
    UserRequest,
    QuestionResponse,
    OptionsRequest,
    OptionsResponse,
)
from src.usecase.generate_qa import graph_builder
from src.driver.checkpointer_factory import create_checkpointer

logger = logging.getLogger(__name__)

router = APIRouter()

# Example for maintaining state across API calls
thread_states = {}  # Simple in-memory store for demonstration


# API Endpoints
@router.post("/generate_qa/question", response_model=QuestionResponse)
async def generate_mbti_question(request: UserRequest):
    """Generate a new MBTI-related question based on previous conversation"""
    try:
        user_id = request.user_id  # Assuming you have user ID in the request

        # Get or create thread ID for this user
        thread_id = thread_states.get(user_id)

        # Convert request messages
        messages = [{"role": "user", "content": request.message}]
        with create_checkpointer() as checkpointer:
            checkpointer.setup()

            graph_with_memory = graph_builder.compile(checkpointer=checkpointer)
            if thread_id:
                # Continue from previous state
                result = graph_with_memory.invoke(
                    {"messages": messages, "options": []},
                    config={"configurable": {"thread_id": thread_id}},
                )
            else:
                # Create new thread
                thread_id = f"thread_{user_id}_{int(time.time())}"
                thread_states[user_id] = thread_id

                result = graph_with_memory.invoke(
                    {"messages": messages, "options": []},
                    config={"configurable": {"thread_id": thread_id}},
                )
            return {"question": result["messages"][-1]["content"]}

    except Exception as e:
        logger.debug(e.__str__())
        traceback.print_exc()

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate_qa/options", response_model=OptionsResponse)
async def generate_mbti_answer_options(request: OptionsRequest):
    """Generate answer options for the current question"""
    try:
        user_id = request.user_id
        thread_id = thread_states.get(user_id)
        with create_checkpointer() as checkpointer:
            checkpointer.setup()

            graph_with_memory = graph_builder.compile(checkpointer=checkpointer)
            result = graph_with_memory.invoke(
                {"messages": [], "options": []},
                config={"configurable": {"thread_id": thread_id}},
            )
        # Return the generated options
        if result["options"] and len(result["options"]) > 0:
            return {"options": result["options"][0]}
        else:
            raise HTTPException(status_code=500, detail="No options were generated")
    except Exception as e:
        print(f"Graph invoke error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
