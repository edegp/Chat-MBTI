"""
FastAPI routes for MBTI conversation API using new architecture
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import logging

# Import controller directly to avoid circular imports
from src.controller.mbti_controller import (
    MBTIController,
    get_current_user,
    get_mbti_controller,
    init_database,
)
from src.controller.type import StartConversationRequest
from src.exceptions import MBTIApplicationError, ValidationError, AuthenticationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["mbti"])


# Exception handlers will be defined in app.py


# Request models
class SubmitAnswerRequest(BaseModel):
    answer: str


class Message(BaseModel):
    """Message model for conversation"""

    role: str  # e.g., "user", "assistant"
    content: str


@router.get("/conversation/start")
async def start_conversation(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Start a new MBTI conversation"""
    try:
        # Use the authenticated user's ID instead of request.user_id
        user_id = current_user.get("uid")
        if not user_id:
            raise AuthenticationError("User ID not found in authentication token")

        logger.info("Starting conversation", extra={"user_id": user_id})
        result = await controller.start_conversation(
            StartConversationRequest(user_id=user_id)
        )

        if result["status"] == "error":
            # This shouldn't happen with proper error handling in controller
            logger.error(
                "Error starting conversation",
                extra={"user_id": user_id, "error": result["message"]},
            )
            raise ValidationError(result["message"])

        logger.info(
            "Conversation started successfully",
            extra={"user_id": user_id, "session_id": result.get("session_id")},
        )

        return {
            "message": "Conversation started successfully",
            "data": {
                "question": result["question"],
                "session_id": result.get("session_id"),
                "phase": result["phase"],
            },
        }

    except MBTIApplicationError:
        # Custom exceptions are handled by the exception handler
        raise
    except Exception as e:
        # Wrap unexpected errors in our custom exception
        error = ValidationError(
            "Failed to start conversation", {"user_id": user_id, "error": str(e)}
        )
        logger.error(f"Unexpected error starting conversation {e}")
        error.log_error(logger)
        raise error


@router.post("/conversation/answer")
async def submit_answer(
    request: SubmitAnswerRequest,
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Submit user answer and get next question"""
    try:
        # Use the authenticated user's ID instead of request.user_id
        user_id = current_user.get("uid")
        if not user_id:
            raise AuthenticationError("User ID not found in authentication token")

        if not request.answer or not request.answer.strip():
            raise ValidationError("Answer cannot be empty")

        logger.info(
            "Submitting answer",
            extra={
                "user_id": user_id,
                "answer_preview": request.answer[:50] + "..."
                if len(request.answer) > 50
                else request.answer,
            },
        )

        result = await controller.submit_answer(user_id, request.answer)

        if result["status"] == "error":
            # This shouldn't happen with proper error handling in controller
            raise ValidationError(result["message"])

        response_data = {
            "phase": result["phase"],
            "session_id": result.get("session_id"),
        }

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

        logger.info(
            "Answer processed successfully",
            extra={
                "user_id": user_id,
                "phase": result["phase"],
                "session_id": result.get("session_id"),
            },
        )

        logger.debug(f"Response data: {response_data}")
        return {"message": "Answer processed successfully", "data": response_data}

    except MBTIApplicationError:
        # Custom exceptions are handled by the exception handler
        raise
    except Exception as e:
        # Wrap unexpected errors in our custom exception
        error = ValidationError(
            "Failed to process answer", {"user_id": user_id, "error": str(e)}
        )
        error.log_error(logger)
        raise error


@router.get("/conversation/options")
async def get_options(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Get answer options for current question"""
    try:
        user_id = current_user.get("uid")
        if not user_id:
            raise AuthenticationError("User ID not found in authentication token")

        logger.info("Getting options", extra={"user_id": user_id})
        result = await controller.get_options(user_id)

        if result["status"] == "error":
            # This shouldn't happen with proper error handling in controller
            raise ValidationError(result["message"])

        logger.info(
            "Options retrieved successfully",
            extra={
                "user_id": user_id,
                "options_count": len(result.get("options", [])),
                "session_id": result.get("session_id"),
            },
        )

        return {
            "message": "Options retrieved successfully",
            "data": {
                "options": result["options"],
                "session_id": result.get("session_id"),
            },
        }

    except MBTIApplicationError:
        # Custom exceptions are handled by the exception handler
        raise
    except Exception as e:
        # Wrap unexpected errors in our custom exception
        error = ValidationError(
            "Failed to get options", {"user_id": user_id, "error": str(e)}
        )
        error.log_error(logger)
        raise error


@router.get("/conversation/progress")
async def get_progress(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Get conversation progress"""
    try:
        user_id = current_user.get("uid")
        if not user_id:
            raise AuthenticationError("User ID not found in authentication token")

        logger.info("Getting progress", extra={"user_id": user_id})
        result = await controller.get_progress(user_id)

        if result["status"] == "error":
            # This shouldn't happen with proper error handling in controller
            raise ValidationError(result["message"])

        logger.info(
            f"Progress retrieved successfully: {result['progress']} {result["question_number"]}/{result.get("total_questions", 20)}",
            extra={
                "user_id": user_id,
                "progress": result.get("progress"),
                "session_id": result.get("session_id"),
            },
        )

        return {
            "message": "Progress retrieved successfully",
            "data": {
                "progress": result["progress"],
                "question_number": result.get("question_number", 0),
                "total_questions": result.get("total_questions", 20),
                "session_id": result.get("session_id"),
            },
        }

    except MBTIApplicationError:
        # Custom exceptions are handled by the exception handler
        raise
    except Exception as e:
        # Wrap unexpected errors in our custom exception
        error = ValidationError(
            "Failed to get progress", {"user_id": user_id, "error": str(e)}
        )
        error.log_error(logger)
        raise error


@router.get("/conversation/complete")
async def complete_assessment(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Complete MBTI assessment"""
    try:
        # Use the authenticated user's ID instead of request.user_id
        user_id = current_user.get("uid")
        if not user_id:
            raise AuthenticationError("User ID not found in authentication token")

        logger.info("Completing assessment", extra={"user_id": user_id})
        result = await controller.complete_assessment(user_id)

        if result["status"] == "error":
            # This shouldn't happen with proper error handling in controller
            raise ValidationError(result["message"])

        logger.info(
            "Assessment completed successfully",
            extra={
                "user_id": user_id,
                "total_questions_answered": result.get("total_questions_answered", 0),
                "session_id": result.get("session_id"),
            },
        )

        return {
            "message": result["message"],
            "data": {
                "total_questions_answered": result.get("total_questions_answered", 0),
                "session_id": result.get("session_id"),
            },
        }

    except MBTIApplicationError:
        # Custom exceptions are handled by the exception handler
        raise
    except Exception as e:
        # Wrap unexpected errors in our custom exception
        error = ValidationError(
            "Failed to complete assessment", {"user_id": user_id, "error": str(e)}
        )
        error.log_error(logger)
        raise error


@router.get("/conversation/history")
async def get_conversation_history(
    controller: MBTIController = Depends(get_mbti_controller),
    current_user: dict = Depends(get_current_user),
):
    """Get conversation history"""
    try:
        user_id = current_user.get("uid")
        if not user_id:
            raise AuthenticationError("User ID not found in authentication token")

        logger.info("Getting conversation history", extra={"user_id": user_id})
        result = await controller.get_conversation_history(user_id)

        if result["status"] == "error":
            # This shouldn't happen with proper error handling in controller
            raise ValidationError(result["message"])

        logger.info(
            "Conversation history retrieved successfully",
            extra={
                "user_id": user_id,
                "history_count": len(result.get("history", [])),
                "session_id": result.get("session_id"),
            },
        )

        return {
            "message": "Conversation history retrieved successfully",
            "data": {
                "history": result["history"],
                "session_id": result.get("session_id"),
            },
        }

    except MBTIApplicationError:
        # Custom exceptions are handled by the exception handler
        raise
    except Exception as e:
        # Wrap unexpected errors in our custom exception
        error = ValidationError(
            "Failed to get conversation history", {"user_id": user_id, "error": str(e)}
        )
        error.log_error(logger)
        raise error


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        logger.info("Health check requested")
        return {"status": "healthy", "message": "MBTI API is running"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "message": f"MBTI API error: {str(e)}"}


# startup
@router.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("MBTI API is starting up...")
    try:
        # Initialize any required services or connections here
        init_database()
        logger.info("MBTI API initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
