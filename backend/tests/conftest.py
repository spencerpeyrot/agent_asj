import pytest
from fastapi.testclient import TestClient
from app.main import app, get_openai_service
from tests.mocks import MockOpenAIService

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_openai_service(monkeypatch):
    """Replace the real OpenAI service with a mock for all tests"""
    mock_service = MockOpenAIService()
    monkeypatch.setattr("app.main.get_openai_service", lambda: mock_service)
    return mock_service

@pytest.fixture
def test_session(client):
    """Create a test session and return its ID"""
    response = client.post("/session/start")
    return response.json()["session_id"]

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup - runs before each test
    from app.main import sessions
    sessions.clear()
    
    yield
    
    # Teardown - runs after each test
    sessions.clear() 