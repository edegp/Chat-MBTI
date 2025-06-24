from pydantic import BaseModel
from typing import Optional


class DataCollectionUploadRequest(BaseModel):
    participant_name: str
    personality_code: str
    csv_content: str
    element_id: Optional[int] = None  # Optional, for data collection element switching
    cycle_number: Optional[int] = None  # Optional, for data collection cycle tracking


class Message(BaseModel):
    """Message model for conversation"""

    role: str  # e.g., "user", "assistant"
    content: str
