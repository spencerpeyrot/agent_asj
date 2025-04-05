import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.openai_service import OpenAIService, OpenAIServiceError
from app.main import SectionType
from openai import OpenAIError
import os

@pytest.fixture
def mock_openai():
    with patch('openai.OpenAI') as mock:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def service(mock_openai):
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        service = OpenAIService()
        service.client = mock_openai
        return service

class TestOpenAIService:
    async def test_generate_section_content(self, service, mock_openai):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_openai.chat.completions.create.return_value = mock_response

        context = {
            "topic": "Market Analysis",
            "additional_info": "Focus on tech sector"
        }

        content = await service.generate_section_content(
            SectionType.THESIS.value,
            context
        )

        assert content == "Generated content"
        mock_openai.chat.completions.create.assert_called_once()

    async def test_missing_context(self, service):
        with pytest.raises(ValueError) as exc:
            await service.generate_section_content(
                SectionType.THESIS.value,
                {}  # Empty context
            )
        assert "Missing required context key: 'topic'" in str(exc.value)

    async def test_invalid_section_type(self, service):
        with pytest.raises(ValueError) as exc:
            await service.generate_section_content(
                "invalid_type",
                {"topic": "test"}
            )
        assert "No template found for section type" in str(exc.value)

    async def test_api_error(self, service, mock_openai):
        mock_openai.chat.completions.create.side_effect = OpenAIError("API Error")
        
        with pytest.raises(OpenAIServiceError) as exc:
            await service.generate_section_content(
                SectionType.THESIS.value,
                {"topic": "test", "additional_info": "test"}
            )
        assert "OpenAI API error" in str(exc.value) 