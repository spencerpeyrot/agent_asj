class MockOpenAIService:
    async def generate_section_content(self, section_type: str, context: dict) -> str:
        return f"Mock content for {section_type}" 