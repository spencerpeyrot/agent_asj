import pytest
from fastapi.testclient import TestClient
from app.main import app, get_openai_service
from tests.mocks import MockOpenAIService

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_openai_service():
    # Store the original get_openai_service function
    original_get_service = getattr(get_openai_service, "_instance", None)
    
    # Replace with mock service
    get_openai_service._instance = MockOpenAIService()
    
    yield
    
    # Restore original service if it existed
    if original_get_service:
        get_openai_service._instance = original_get_service
    else:
        delattr(get_openai_service, "_instance")

@pytest.fixture
def test_session(client):
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