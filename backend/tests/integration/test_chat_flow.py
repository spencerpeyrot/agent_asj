from fastapi.testclient import TestClient
from app.main import app
import pytest
from datetime import datetime

client = TestClient(app)

def test_complete_chat_flow():
    # 1. Start new session
    session_response = client.post("/session/start")
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]
    
    # 2. Send multiple messages
    messages = [
        "Hello, I want to create a newsletter",
        "The topic is AI and Machine Learning",
        "Please add a section about recent developments"
    ]
    
    for msg in messages:
        message = {
            "session_id": session_id,
            "speaker": "user",
            "content": msg,
            "timestamp": datetime.now().isoformat()
        }
        response = client.post("/message", json=message)
        assert response.status_code == 200
        assert response.json()["speaker"] == "assistant"
    
    # 3. Verify chat history
    session_response = client.get(f"/session/{session_id}")
    assert session_response.status_code == 200
    message_history = session_response.json()["messages"]
    
    # Should have 6 messages (3 user messages + 3 system responses)
    assert len(message_history) == 6
    
    # Verify message order and content
    for i, msg in enumerate(messages):
        assert message_history[i*2]["content"] == msg
        assert message_history[i*2]["speaker"] == "user"
        assert message_history[i*2+1]["speaker"] == "assistant" 