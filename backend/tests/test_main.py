import pytest
from fastapi.testclient import TestClient
from app.main import app, Message, Session, SpeakerType
from datetime import datetime

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Newsletter Builder API"}

class TestSessionManagement:
    def test_start_session(self):
        response = client.post("/session/start")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert isinstance(data["session_id"], str)

    def test_get_session(self, test_session):
        response = client.get(f"/session/{test_session}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == test_session
        assert "chat_history" in data
        assert "created_at" in data

    def test_get_nonexistent_session(self):
        response = client.get("/session/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

class TestMessageHandling:
    def test_send_message(self, test_session):
        message = {
            "session_id": test_session,
            "speaker": "user",
            "content": "Test message"
        }
        response = client.post("/message", json=message)
        assert response.status_code == 200
        data = response.json()
        assert data["speaker"] == "system"
        assert "Received: Test message" in data["content"]

    def test_send_message_invalid_session(self):
        message = {
            "session_id": "nonexistent",
            "speaker": "user",
            "content": "Test message"
        }
        response = client.post("/message", json=message)
        assert response.status_code == 404

    def test_send_empty_message(self, test_session):
        message = {
            "session_id": test_session,
            "speaker": "user",
            "content": ""
        }
        response = client.post("/message", json=message)
        assert response.status_code == 400