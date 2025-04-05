class MockOpenAIService:
    async def generate_response(self, system_prompt: str, context: dict) -> str:
        """Mock response generation"""
        return "This is a mock response from the AI assistant."

    async def generate_section_content(self, section_type: str, context: dict) -> str:
        """Mock section content generation"""
        return f"Mock content for section type: {section_type}" 