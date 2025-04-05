from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime
from enum import Enum

class SpeakerType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    session_id: str
    speaker: SpeakerType
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = Field(default_factory=dict)

    @field_validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip() 