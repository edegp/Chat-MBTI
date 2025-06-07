from pydantic import BaseModel
from typing import List
from ..usecase.type import Message


class UserRequest(BaseModel):
    messages: List[Message]


class OptionsRequest(BaseModel):
    # user_id: uuid.UUID
    retry: bool = False


class QuestionResponse(BaseModel):
    question: str


class OptionsResponse(BaseModel):
    options: List[str]
