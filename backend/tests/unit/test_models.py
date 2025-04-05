import pytest
from datetime import datetime
from pydantic import ValidationError
from app.main import Message, Session, SpeakerType

def test_message_model():
    # Test valid message creation
    message = Message(
        session_id="test-session",
        speaker=SpeakerType.USER,
        timestamp=datetime.now().isoformat(),
        content="Test message"
    )
    assert message.session_id == "test-session"
    assert message.speaker == SpeakerType.USER
    assert message.content == "Test message"
    assert message.metadata is None

    # Test invalid speaker
    with pytest.raises(ValidationError):
        Message(
            session_id="test-session",
            speaker="invalid_speaker",
            timestamp=datetime.now().isoformat(),
            content="Test message"
        )

def test_session_model():
    session_id = "test-session"
    created_at = datetime.now().isoformat()
    
    # Test session creation
    session = Session(
        session_id=session_id,
        created_at=created_at
    )
    assert session.session_id == session_id
    assert session.created_at == created_at
    assert session.chat_history == []
    assert session.newsletter_sections == {}

    # Test adding message to session
    message = Message(
        session_id=session_id,
        speaker=SpeakerType.USER,
        timestamp=datetime.now().isoformat(),
        content="Test message"
    )
    session.chat_history.append(message)
    assert len(session.chat_history) == 1 

def test_message_metadata():
    # Test message with metadata
    metadata = {"key": "value"}
    message = Message(
        session_id="test-session",
        speaker=SpeakerType.SYSTEM,
        timestamp=datetime.now().isoformat(),
        content="Test message",
        metadata=metadata
    )
    assert message.metadata == metadata

def test_message_validation():
    """Test various validation cases for the Message model"""
    
    # Test invalid speaker
    with pytest.raises(ValidationError):
        Message(
            session_id="test-session",
            speaker="invalid",
            timestamp=datetime.now().isoformat(),
            content="Test message"
        )

    # Test invalid timestamp
    with pytest.raises(ValidationError):
        Message(
            session_id="test-session",
            speaker=SpeakerType.USER,
            timestamp="invalid-timestamp",
            content="Test message"
        )

    # Test empty content
    with pytest.raises(ValidationError):
        Message(
            session_id="test-session",
            speaker=SpeakerType.USER,
            timestamp=datetime.now().isoformat(),
            content=""
        )

    # Test whitespace-only content
    with pytest.raises(ValidationError) as exc_info:
        Message(
            session_id="test-session",
            speaker=SpeakerType.USER,
            timestamp=datetime.now().isoformat(),
            content="   "
        )
    assert "content" in str(exc_info.value) 