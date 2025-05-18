from fastapi import FastAPI
from src.controller import generate_qa
from src.usecase.generate_qa import llm

# Add configuration for CORS if needed
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MBTI Chatbot API")
app.include_router(generate_qa.router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Verify the API is properly configured on startup"""
    try:
        # Test the LLM with a simple prompt
        test_response = llm.invoke("Hello")
        print("LLM initialized successfully")
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        raise


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
