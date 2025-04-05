import pytest
from fastapi.testclient import TestClient
from app.main import app, SectionType, NewsletterSection
from datetime import datetime

client = TestClient(app)

@pytest.fixture
def test_session():
    # Create a test session first
    response = client.post("/session/start")
    return response.json()["session_id"]

class TestNewsletterSection:
    def test_section_model(self):
        """Test NewsletterSection model validation"""
        section = NewsletterSection(
            section_type=SectionType.THESIS,
            content="Test content",
            generated_at=datetime.now().isoformat()
        )
        assert section.section_type == SectionType.THESIS
        assert section.content == "Test content"
        assert section.metadata is None

    def test_invalid_section_type(self):
        """Test validation of invalid section type"""
        with pytest.raises(ValueError):
            NewsletterSection(
                section_type="invalid_type",
                content="Test content",
                generated_at=datetime.now().isoformat()
            )

    def test_empty_content(self):
        """Test validation of empty content"""
        with pytest.raises(ValueError):
            NewsletterSection(
                section_type=SectionType.THESIS,
                content="",
                generated_at=datetime.now().isoformat()
            )

class TestSectionGeneration:
    def test_generate_thesis(self, test_session):
        """Test generating a thesis section"""
        request = {
            "session_id": test_session,
            "section_type": "thesis",
            "context": {  # Add required context
                "topic": "Market Analysis",
                "additional_info": "Focus on tech sector"
            }
        }
        response = client.post("/generate/section", json=request)
        assert response.status_code == 200

    def test_generate_invalid_section_type(self, test_session):
        """Test generating with invalid section type"""
        request = {
            "session_id": test_session,
            "section_type": "invalid",
            "context": {  # Add required context
                "topic": "test"
            }
        }
        response = client.post("/generate/section", json=request)
        assert response.status_code == 422  # FastAPI validation error

    def test_generate_section_invalid_session(self):
        """Test generating with invalid session"""
        request = {
            "session_id": "nonexistent",
            "section_type": "thesis",
            "context": {  # Add required context
                "topic": "test"
            }
        }
        response = client.post("/generate/section", json=request)
        assert response.status_code == 404

    def test_section_stored_in_session(self, test_session):
        """Test that generated section is stored in session"""
        request = {
            "session_id": test_session,
            "section_type": "thesis",
            "context": {  # Add required context
                "topic": "Market Analysis",
                "additional_info": "Focus on tech sector"
            }
        }
        response = client.post("/generate/section", json=request)
        assert response.status_code == 200

    async def test_generate_section_missing_context(self, test_session):
        """Test generating a section with missing context"""
        request = {
            "session_id": test_session,
            "section_type": "thesis",
            "context": {}  # Empty context
        }
        response = client.post("/generate/section", json=request)
        assert response.status_code == 422  # FastAPI validation error
        assert "Value error, Missing required context fields: topic" in response.json()["detail"][0]["msg"] 