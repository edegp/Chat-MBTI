from fastapi import FastAPI
from src.controller.mbti_routes import router as mbti_router

# Add configuration for CORS if needed
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MBTI Chatbot API",
    description="AI-powered MBTI personality assessment chatbot using LangGraph",
    version="1.0.0",
)

# Include new architecture routes
app.include_router(mbti_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
