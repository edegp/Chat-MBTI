from pydantic import BaseModel
from typing import List
from ..type import Message


class StartConversationRequest(BaseModel):
    user_id: str
    element_id: int = None  # Optional, for data collection element switching


class ProcessUserResponseRequest(BaseModel):
    user_input: str
    user_id: str


class UserRequest(BaseModel):
    messages: List[Message]


class OptionsRequest(BaseModel):
    # user_id: uuid.UUID
    retry: bool = False


class QuestionResponse(BaseModel):
    question: str


class OptionsResponse(BaseModel):
    options: List[str]
