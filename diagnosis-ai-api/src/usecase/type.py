from typing import List, Dict, Optional, Literal
from typing_extensions import TypedDict, Annotated
from pydantic import BaseModel


class Message(BaseModel):
    """Message class for chat conversations"""

    role: str  # "user" or "assistant"
    content: str


# Define state management (from your notebook)
def add_messages(messages, new_messages):
    return messages + new_messages


class ChatState(TypedDict):
    # --- メタ ---
    user_id: str
    session_id: str
    phase: Literal["ask", "diagnosis", "consult"]

    # --- LLM や会話履歴 ---
    messages: Annotated[List[Message], add_messages]
    answers: Dict[int, str]
    personality_element_id: Literal[1, 2, 3, 4]

    # --- 質問管理 ---
    next_display_order: int
    pending_question: Optional[str]
    pending_question_meta: Optional[dict]
    options: List[str]


def get_initial_state(
    user_id: str,
    session_id: str,
    messages: List[Message] = None,
) -> ChatState:
    """Initialize a new chat state"""
    if messages is None:
        messages = []

    return ChatState(
        user_id=user_id,
        session_id=session_id,
        phase="ask",
        messages=messages,
        answers={},
        personality_element_id=1,
        next_display_order=0,
        pending_question=None,
        pending_question_meta=None,
        options=[],
    )
