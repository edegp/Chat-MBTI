"""
FastAPI routes for MBTI conversation API using new architecture
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# Import controller directly to avoid circular imports
from .mbti_controller import MBTIController
from ..driver.auth import get_current_user
from ..gateway.llm_gateway import LLMGateway
from ..gateway.repository_gateway import (
    QuestionRepositoryGateway,
    SessionRepositoryGateway,
)
from ..gateway.workflow_gateway import WorkflowGateway
from ..driver.langgraph_driver import LangGraphDriver
from ..usecase.mbti_conversation_service import MBTIConversationService

router = APIRouter(prefix="/api/v1", tags=["mbti"])


# Request models
class SubmitAnswerRequest(BaseModel):
    answer: str


def get_mbti_controller() -> MBTIController:
    """Dependency injection for MBTIController"""
    # Create dependencies
    llm_gateway = LLMGateway()
    question_repo = QuestionRepositoryGateway()
    session_repo = SessionRepositoryGateway()

    # Create LangGraph driver
    langgraph_driver = LangGraphDriver(llm_gateway, question_repo)

    # Create workflow gateway
    workflow_gateway = WorkflowGateway(langgraph_driver)

    # Create service
    mbti_service = MBTIConversationService(
        workflow_port=workflow_gateway,
        question_repository=question_repo,
        session_repository=session_repo,
    )

    # Create controller
    return MBTIController(mbti_service)


@router.get("/conversation/start")
async def start_conversation(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Start a new MBTI conversation"""
    # Use the authenticated user's ID instead of request.user_id
    user_id = current_user.get("uid")
    result = await controller.start_conversation(user_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "message": "Conversation started successfully",
        "data": {
            "question": result["question"],
            "session_id": result.get("session_id"),
            "phase": result["phase"],
        },
    }


@router.post("/conversation/answer")
async def submit_answer(
    request: SubmitAnswerRequest,
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Submit user answer and get next question"""
    # Use the authenticated user's ID instead of request.user_id
    user_id = current_user.get("uid")
    result = await controller.submit_answer(user_id, request.answer)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    response_data = {"phase": result["phase"], "session_id": result.get("session_id")}

    if result["phase"] == "question":
        response_data.update(
            {
                "question": result["question"],
                "progress": result.get("progress", 0.0),
                "question_number": result.get("question_number", 1),
                "total_questions": result.get("total_questions", 20),
            }
        )
    elif result["phase"] == "diagnosis":
        response_data["message"] = result["message"]

    return {"message": "Answer processed successfully", "data": response_data}


@router.get("/conversation/options")
async def get_options(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Get answer options for current question"""
    user_id = current_user.get("uid")
    result = await controller.get_options(user_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "message": "Options retrieved successfully",
        "data": {"options": result["options"], "session_id": result.get("session_id")},
    }


@router.get("/conversation/progress")
async def get_progress(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Get conversation progress"""
    user_id = current_user.get("uid")
    result = await controller.get_progress(user_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "message": "Progress retrieved successfully",
        "data": {
            "progress": result["progress"],
            "question_number": result.get("question_number", 0),
            "total_questions": result.get("total_questions", 20),
            "session_id": result.get("session_id"),
        },
    }


@router.get("/conversation/complete")
async def complete_assessment(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Complete MBTI assessment"""
    # Use the authenticated user's ID instead of request.user_id
    user_id = current_user.get("uid")
    result = await controller.complete_assessment(user_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "message": result["message"],
        "data": {
            "total_questions_answered": result.get("total_questions_answered", 0),
            "session_id": result.get("session_id"),
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "MBTI API is running"}
