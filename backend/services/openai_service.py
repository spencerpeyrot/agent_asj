from openai import AsyncOpenAI, OpenAIError
from typing import Optional, Dict, List, Any
import os
from datetime import datetime
from templates.prompts import PROMPT_TEMPLATES
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors"""
    pass

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIServiceError("OPENAI_API_KEY not found in environment variables")
        
        logger.debug("Initializing AsyncOpenAI client")
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

    async def generate_response(self, messages: List[Dict[str, str]], context: Dict[str, Any]) -> str:
        try:
            logger.debug(f"Generating response with context: {context}")
            logger.debug(f"Messages being sent to OpenAI: {messages}")

            # Format messages for the API
            formatted_messages = []
            
            # Add system message
            formatted_messages.append({
                "role": "system",
                "content": "You are a helpful AI assistant specializing in financial analysis and newsletter writing."
            })
            
            # Add conversation history
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            logger.debug(f"Formatted messages for OpenAI: {formatted_messages}")

            # Make the API call
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # or your preferred model
                    messages=formatted_messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                logger.debug(f"Raw OpenAI response: {response}")
                
                if not response.choices or not response.choices[0].message:
                    raise OpenAIServiceError("No response received from OpenAI")
                
                return response.choices[0].message.content

            except Exception as e:
                logger.error(f"OpenAI API call failed: {str(e)}", exc_info=True)
                raise OpenAIServiceError(f"OpenAI API call failed: {str(e)}")

        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}", exc_info=True)
            raise OpenAIServiceError(f"Failed to generate response: {str(e)}") 