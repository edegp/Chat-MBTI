from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

# Add configuration for CORS if needed
from fastapi.middleware.cors import CORSMiddleware

from .router import router
from src.exceptions import (
    MBTIApplicationError,
    AuthenticationError,
    AuthorizationError,
    SessionNotFoundError,
    LLMError,
    DatabaseError,
    create_error_response,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="MBTI Chatbot API")
app.include_router(router)


# Exception handlers
@app.exception_handler(MBTIApplicationError)
async def mbti_exception_handler(request, exc: MBTIApplicationError):
    """Handle MBTI application errors"""
    exc.log_error(logger)
    response = create_error_response(exc)

    # Map specific error types to HTTP status codes
    status_code = 400  # Default bad request
    if isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, AuthorizationError):
        status_code = 403
    elif isinstance(exc, SessionNotFoundError):
        status_code = 404
    elif isinstance(exc, DatabaseError):
        status_code = 500
    elif isinstance(exc, LLMError):
        status_code = 503  # Service unavailable

    return JSONResponse(status_code=status_code, content=response)


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "error_type": "InternalServerError",
            "details": {},
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
