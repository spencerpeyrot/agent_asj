from openai import AsyncOpenAI, OpenAIError
from typing import Optional, Dict
import os
from datetime import datetime
from templates.prompts import PROMPT_TEMPLATES
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors"""
    pass

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIServiceError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_section_content(
        self,
        section_type: str,
        context: Dict[str, str]
    ) -> str:
        """
        Generate content for a newsletter section using OpenAI.
        
        Args:
            section_type: Type of section to generate
            context: Dictionary containing context variables for the prompt
        
        Returns:
            Generated content as a string
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Validate section type first
        template = PROMPT_TEMPLATES.get(section_type)
        if not template:
            raise ValueError(f"No template found for section type: {section_type}")

        # Validate context
        try:
            prompt = template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing required context key: {str(e)}")

        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional financial newsletter writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()

        except OpenAIError as e:
            raise OpenAIServiceError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise OpenAIServiceError(f"Unexpected error: {str(e)}")

    async def generate_response(self, system_prompt: str, context: dict) -> str:
        """
        Generate a response using OpenAI's chat completion.
        
        Args:
            system_prompt: The system message to set the AI's role
            context: Dictionary containing previous messages and current message
        
        Returns:
            Generated response as a string
        """
        if not self.api_key:
            raise OpenAIServiceError("OPENAI_API_KEY environment variable is not set")

        try:
            formatted_system_prompt = f"""
            {system_prompt}
            
            Format your responses as follows:
            - Use '# ' for main headings
            - Use '## ' for subheadings
            - Use '### ' for section titles
            - Use bullet points with '- ' for lists
            - Structure your response like a professional report with clear sections
            """
            
            messages = [
                {"role": "system", "content": formatted_system_prompt}
            ]
            
            # Add previous messages for context
            if "previous_messages" in context:
                for msg in context["previous_messages"]:
                    messages.append({
                        "role": "user" if msg["speaker"] == "user" else "assistant",
                        "content": msg["content"]
                    })
            
            # Add current message
            if "current_message" in context:
                messages.append({"role": "user", "content": context["current_message"]})
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return f"I'm sorry, I encountered an error: {str(e)}" 