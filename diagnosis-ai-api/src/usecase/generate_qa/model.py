import os

from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Configure Google API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=1,
    max_tokens=256,
    timeout=None,
    max_retries=2,
    api_key=GEMINI_API_KEY,
)
