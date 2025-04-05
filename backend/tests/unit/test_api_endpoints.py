from fastapi.testclient import TestClient
from app.main import app
import pytest
from datetime import datetime

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Newsletter Builder API"}

def test_start_session():
    response = client.post("/session/start")
    assert response.status_code == 200
    assert "session_id" in response.json()
    session_id = response.json()["session_id"]
    assert isinstance(session_id, str)

def test_get_session():
    # Create session
    create_response = client.post("/session/start")
    session_id = create_response.json()["session_id"]
    
    # Get session
    response = client.get(f"/session/{session_id}")
    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    
    # Test non-existent session
    response = client.get("/session/non-existent")
    assert response.status_code == 404

def test_create_message():
    # Create session
    create_response = client.post("/session/start")
    session_id = create_response.json()["session_id"]

    # Send message
    message = {
        "session_id": session_id,
        "speaker": "user",
        "content": "Test message",
        "timestamp": datetime.now().isoformat()
    }
    response = client.post("/message", json=message)
    assert response.status_code == 200
    
    # Test invalid session
    message["session_id"] = "non-existent"
    response = client.post("/message", json=message)
    assert response.status_code == 404 