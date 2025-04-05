from fastapi.testclient import TestClient
from app.main import app
import pytest

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
            "content": msg
        }
        response = client.post("/message", json=message)
        assert response.status_code == 200
        assert response.json()["speaker"] == "system"
    
    # 3. Verify chat history
    session_response = client.get(f"/session/{session_id}")
    assert session_response.status_code == 200
    chat_history = session_response.json()["chat_history"]
    
    # Should have 6 messages (3 user messages + 3 system responses)
    assert len(chat_history) == 6
    
    # Verify message order and content
    for i, msg in enumerate(messages):
        assert chat_history[i*2]["content"] == msg
        assert chat_history[i*2]["speaker"] == "user"
        assert chat_history[i*2+1]["speaker"] == "system" 