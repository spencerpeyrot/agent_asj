from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid
from .database import Base

# Enum for speaker types
class SpeakerType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

def generate_uuid():
    return str(uuid.uuid4())

# SQLAlchemy models
class DBSession(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("DBMessage", back_populates="session", cascade="all, delete-orphan")

class DBMessage(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"))
    speaker = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    content = Column(String)
    message_metadata = Column(JSON, default={})
    
    session = relationship("DBSession", back_populates="messages") 