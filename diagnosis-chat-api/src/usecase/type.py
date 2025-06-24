from typing import List, Dict, Optional, Literal
from pydantic import Field
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class Message(BaseMessage):
    """Message class for chat conversations"""

    id: Optional[str] = None
    role: str  # "user" or "assistant"
    type: Optional[Literal["human", "ai"]] = None

    def __post_init__(self):
        """Set type based on role after initialization"""
        if hasattr(self, "role") and self.role:
            self.type = "human" if self.role == "user" else "ai"


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
    personality_element_id: int = 1,
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
        personality_element_id=personality_element_id,
        next_display_order=0,
        pending_question=None,
        pending_question_meta=None,
        options=[],
    )
