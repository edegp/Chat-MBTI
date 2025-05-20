from pydantic import BaseModel
from typing import List
import uuid


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class UserRequest(BaseModel):
    user_id: uuid.UUID
    messages: List[Message]


class OptionsRequest(BaseModel):
    user_id: uuid.UUID
    retry: bool = False


class QuestionResponse(BaseModel):
    question: str


class OptionsResponse(BaseModel):
    options: List[str]
