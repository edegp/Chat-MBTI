import os

from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Configure Google API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # Check if we're in a test environment
    if os.environ.get("PYTEST_CURRENT_TEST"):
        GEMINI_API_KEY = "test-api-key-for-testing"
    else:
        raise ValueError("GEMINI_API_KEY environment variable not set")

# Only configure genai if not in test environment
if not os.environ.get("PYTEST_CURRENT_TEST"):
    genai.configure(api_key=GEMINI_API_KEY)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=1,
    max_tokens=256,
    timeout=None,
    max_retries=2,
    api_key=GEMINI_API_KEY,
)